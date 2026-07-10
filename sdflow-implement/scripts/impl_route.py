#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""impl_route.py — sdflow-implement 路由/拓扑 stdlib-only helper（只读、零副作用）

管线路由三跳（design F4/F12/F13，逐字见 matt-workflow-integration/superpowers-plan.md
Task 2 Interfaces）：
    ① openspec/config.yaml 顶层 `impl-pipeline:` 键（仅新出 ticket 首跳读一次）
    ② plan 文件头 frontmatter marker（在途只读，marker 存在即锁定，优先于 config）
    ③ 键/marker 缺席 → 一律 superpowers（缺省态，静默回退）
marker **存在但非法/重复/损坏** 一律停（RouteStop，UNKNOWN 语义），不静默回退——
防两管线混跑。

本文件不 import yaml（config.yaml 只做逐行文本解析，不做通用 YAML 解析）；
不读、不改 sdflow-ship/scripts/ship_gate.py（gate 零改动铁律，本文件与 gate 完全独立）；
subprocess 仅用于取 plan_sha（`git log -1 --format=%h`），取不到时输出 "-"。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

FRONT_DELIM = "---"
CONFIG_KEY = "impl-pipeline:"
LEGAL_PIPELINES = ("tickets", "superpowers")

TASK_HEADER_RE = re.compile(r"^###\s*Task\s+(\d+):", re.MULTILINE)
BLOCKED_BY_RE = re.compile(r"^\*{0,2}Blocked-by:\*{0,2}\s*(.*)$", re.MULTILINE)


class RouteStop(Exception):
    """管线 marker 存在但非法/重复/损坏——UNKNOWN 语义，停，不静默回退。"""


class TopoError(Exception):
    """Blocked-by 拓扑非法：环/自环/引用不存在的依赖号。"""


# ---------------------------------------------------------------------------
# 文本标量提取（config 与 marker frontmatter 共用：允许引号值、去行内注释）
# ---------------------------------------------------------------------------

def _extract_scalar(raw: str) -> str:
    s = raw.strip()
    if not s:
        return ""
    if s[0] in ("'", '"'):
        q = s[0]
        end = s.find(q, 1)
        if end != -1:
            return s[1:end]
        return s[1:]  # 未闭合引号，兜底去掉起始引号字符
    hash_idx = s.find("#")
    if hash_idx != -1:
        s = s[:hash_idx]
    return s.strip()


# ---------------------------------------------------------------------------
# ① config 键
# ---------------------------------------------------------------------------

def read_config_pipeline(root) -> Tuple[str, str]:
    """读 <root>/openspec/config.yaml 顶层 `impl-pipeline:` 行。

    返回 (pipeline, note)：
        缺失/空值      → ("superpowers", "absent")
        tickets/superpowers → (值, "ok")
        其他值         → ("superpowers", "unknown-value:<v>")（F12：非法值回显，区别于缺省）
    """
    config_path = Path(root) / "openspec" / "config.yaml"
    if not config_path.exists():
        return "superpowers", "absent"

    text = config_path.read_text(encoding="utf-8", errors="replace")
    raw_value: Optional[str] = None
    for line in text.splitlines():
        # 顶层键要求列 0 起始（排除注释行 `# impl-pipeline: ...` 与缩进内文本，
        # 如 `context: |` 块标量正文提及同名字样）。
        if line.startswith(CONFIG_KEY):
            raw_value = _extract_scalar(line[len(CONFIG_KEY):])
            break

    if not raw_value:
        return "superpowers", "absent"
    if raw_value in LEGAL_PIPELINES:
        return raw_value, "ok"
    return "superpowers", f"unknown-value:{raw_value}"


# ---------------------------------------------------------------------------
# ② plan frontmatter marker
# ---------------------------------------------------------------------------

def read_plan_marker(plan_path) -> Optional[str]:
    """读 plan 文件头 frontmatter 的 `impl-pipeline` marker。

    文件缺            → None
    无 frontmatter / 无键 → "superpowers"（旧管线产物，不嗅探正文内容）
    首块 frontmatter 含 impl-pipeline: tickets|superpowers 单值 → 该值
    键重复 / 值非法 / frontmatter 未闭合 → raise RouteStop（UNKNOWN 语义，停）
    """
    p = Path(plan_path)
    if not p.exists():
        return None

    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONT_DELIM:
        return "superpowers"  # 无 frontmatter

    close_idx: Optional[int] = None
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONT_DELIM:
            close_idx = i
            break
    if close_idx is None:
        raise RouteStop(f"plan frontmatter 未闭合: {p}")

    values: List[str] = []
    for line in lines[1:close_idx]:
        if line.startswith(CONFIG_KEY):
            values.append(_extract_scalar(line[len(CONFIG_KEY):]))

    if not values:
        return "superpowers"  # frontmatter 在，但无 impl-pipeline 键
    if len(values) > 1:
        raise RouteStop(f"plan frontmatter impl-pipeline 键重复: {p}")

    val = values[0]
    if val not in LEGAL_PIPELINES:
        raise RouteStop(f"plan frontmatter impl-pipeline 值非法: {val!r} ({p})")
    return val


# ---------------------------------------------------------------------------
# 路由合成：marker 存在（非 None）优先（在途锁定）；marker 为 None（plan 缺）→ 用 config（首跳）
# ---------------------------------------------------------------------------

def resolve_pipeline(config_pipeline: str, marker: Optional[str]) -> str:
    if marker is None:
        return config_pipeline
    return marker


# ---------------------------------------------------------------------------
# Blocked-by 拓扑
# ---------------------------------------------------------------------------

def parse_blocked_by(plan_text: str) -> Dict[int, Set[int]]:
    """按 `### Task N:` 分段解析 `Blocked-by:`（`none` 或逗号号列）。

    环 / 自环 / 引用不存在的依赖号 → raise TopoError（结构校验，与 done 集无关）。
    """
    headers = list(TASK_HEADER_RE.finditer(plan_text))
    if not headers:
        return {}

    task_ids: Set[int] = set()
    segments: List[Tuple[int, str]] = []
    for i, m in enumerate(headers):
        tid = int(m.group(1))
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(plan_text)
        segments.append((tid, plan_text[start:end]))
        task_ids.add(tid)

    deps: Dict[int, Set[int]] = {}
    for tid, seg in segments:
        bm = BLOCKED_BY_RE.search(seg)
        dep_set: Set[int] = set()
        if bm is not None:
            raw = bm.group(1).strip()
            if raw and raw.lower() != "none":
                for part in raw.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    if not part.isdigit():
                        raise TopoError(
                            f"Task {tid} Blocked-by 含非法号: {part!r}")
                    dep_set.add(int(part))
        deps[tid] = dep_set

    # 结构校验：自环 / 引用不存在的依赖号
    for tid, dep_set in deps.items():
        if tid in dep_set:
            raise TopoError(f"Task {tid} 自环依赖自身")
        missing = dep_set - task_ids
        if missing:
            raise TopoError(
                f"Task {tid} 引用不存在的依赖号: {sorted(missing)}")

    _detect_cycle(deps)
    return deps


def _detect_cycle(deps: Dict[int, Set[int]]) -> None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {tid: WHITE for tid in deps}

    def visit(tid: int, path: List[int]) -> None:
        color[tid] = GRAY
        for dep in deps.get(tid, ()):
            if color.get(dep) == GRAY:
                chain = " -> ".join(str(x) for x in path + [dep])
                raise TopoError(f"Blocked-by 依赖环: {chain}")
            if color.get(dep) == WHITE:
                visit(dep, path + [dep])
        color[tid] = BLACK

    for tid in deps:
        if color[tid] == WHITE:
            visit(tid, [tid])


def next_ready(deps: Dict[int, Set[int]], done: Iterable[int]) -> List[int]:
    """已验证的 deps + 已完成号集 → 下一批 next-ready 号（升序）。"""
    done_set = set(done)
    ready = [tid for tid, dep_set in deps.items()
             if tid not in done_set and dep_set <= done_set]
    return sorted(ready)


# ---------------------------------------------------------------------------
# plan_sha（唯一 subprocess 用途）
# ---------------------------------------------------------------------------

def _get_plan_sha(root: Path, plan_path: Path) -> str:
    if not plan_path.exists():
        return "-"
    try:
        rel = plan_path.relative_to(root)
        target = str(rel)
    except ValueError:
        target = str(plan_path)
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--format=%h", "--", target],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return "-"
    if result.returncode != 0:
        return "-"
    sha = result.stdout.strip()
    return sha if sha else "-"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_route(args: argparse.Namespace) -> int:
    root = Path(args.root)
    change = args.change
    plan_path = root / "openspec" / "changes" / change / "superpowers-plan.md"

    config_pipeline, config_note = read_config_pipeline(root)

    try:
        marker = read_plan_marker(plan_path)
    except RouteStop as e:
        print(str(e), file=sys.stderr)
        return 6

    pipeline = resolve_pipeline(config_pipeline, marker)

    if config_note == "absent":
        config_display = "absent"
    elif config_note == "ok":
        config_display = config_pipeline
    elif config_note.startswith("unknown-value:"):
        config_display = config_note[len("unknown-value:"):]
    else:  # pragma: no cover - 防御性兜底，理论不可达
        config_display = config_note

    if marker is None:
        marker_display = "absent"
    elif marker == "superpowers":
        # 无法区分"显式声明 superpowers"与"无 frontmatter/无键的隐式缺省"——两者
        # read_plan_marker 返回值相同，且路由行为等价（均不锁 tickets），统一显示 none。
        marker_display = "none"
    else:
        marker_display = marker

    plan_sha = _get_plan_sha(root, plan_path)

    print(f"PIPELINE_RECEIPT change={change} config={config_display} "
          f"marker={marker_display} pipeline={pipeline} plan_sha={plan_sha}")
    return 0


def _cmd_frontier(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"plan 文件不存在: {plan_path}", file=sys.stderr)
        return 6

    text = plan_path.read_text(encoding="utf-8", errors="replace")

    done_arg = args.done.strip()
    if done_arg.lower() == "none" or not done_arg:
        done: Set[int] = set()
    else:
        done = set()
        for part in done_arg.split(","):
            part = part.strip()
            if not part:
                continue
            if not part.isdigit():
                print(f"--done 含非法号: {part!r}", file=sys.stderr)
                return 6
            done.add(int(part))

    try:
        deps = parse_blocked_by(text)
        ready = next_ready(deps, done)
    except TopoError as e:
        print(str(e), file=sys.stderr)
        return 6

    print(" ".join(str(x) for x in ready))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="sdflow-implement 路由/拓扑 stdlib helper（只读，不改 ship_gate.py）")
    sub = p.add_subparsers(dest="cmd", required=True)

    route_p = sub.add_parser("route", help="计算实现管线路由（config → marker → 缺省）")
    route_p.add_argument("--root", required=True, help="仓根路径")
    route_p.add_argument("--change", required=True, help="change 名")

    frontier_p = sub.add_parser("frontier", help="按 Blocked-by 拓扑算 next-ready ticket 号")
    frontier_p.add_argument("--plan", required=True, help="plan 文件路径")
    frontier_p.add_argument("--done", required=True, help="逗号分隔已完成号列，或 none")

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "route":
        return _cmd_route(args)
    if args.cmd == "frontier":
        return _cmd_frontier(args)
    parser.error(f"未知子命令: {args.cmd}")  # pragma: no cover
    return 2


if __name__ == "__main__":
    sys.exit(main())
