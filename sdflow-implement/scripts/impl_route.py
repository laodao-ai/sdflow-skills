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
**不改** sdflow-ship/scripts/ship_gate.py（gate 零改动铁律：本文件不影响 gate 任何判定）；
subprocess 仅用于取 plan_sha（`git log -1 --format=%h`），取不到时输出 "-"。

[impl-review-fix F4] 唯一例外：**fenced code block 的围栏词法**从 ship_gate 引入
（`FenceTracker`，只读纯函数）。原先此处手抄 `line.lstrip().startswith("```")` 并在注释里
声称「口径与 ship_gate._parse_plan 一致」——gate 侧已收敛到 FenceTracker（同种 + 长度 ≥ 开启符
+ 尾部校验），手抄副本没跟上，那句注释成了假话，两个解析器对同一 plan 给出不同段落边界
（仓内实证：archive/2026-07-03-sdflow-ship/superpowers-plan.md 的 ```markdown 块内嵌 ```bash
示例，旧口径被内层 ``` 提前关掉围栏 ⇒ 多认了 2 个复选框）。后果：`Blocked-by` 依赖图与
完成判据基于两套边界，被隐藏的行若恰是唯一未勾项 ⇒ 完成判据侧假 ✅。
⇒ 改为**单一源** import。引不到 ⇒ parse_blocked_by 直接 TopoError（fail-closed），
MUST NOT 回退手抄副本——那正是本条要根治的漂移面。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

FRONT_DELIM = "---"
LEGAL_PIPELINES = ("tickets", "superpowers")

# [impl-review-fix F4] 围栏词法单一源 = ship_gate.FenceTracker。
# 定位方式：本文件在 <root>/sdflow-implement/scripts/ 下，gate 在同级 <root>/sdflow-ship/scripts/。
# 两种安装形态都成立——symlink 安装时 Path(__file__).resolve() 落回仓内；Windows copy 安装时
# 两个 skill 目录在 ~/.claude/skills/ 下互为兄弟。抽第三个共享模块反而两种形态都找不到
# （它没有 SKILL.md，setup.sh 不装它），故取 sibling import。
_GATE_SCRIPTS = Path(__file__).resolve().parents[2] / "sdflow-ship" / "scripts"
try:
    if str(_GATE_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_GATE_SCRIPTS))
    from ship_gate import FenceTracker as _FenceTracker  # type: ignore
except Exception:                                        # noqa: BLE001
    _FenceTracker = None                                 # fail-closed，见 parse_blocked_by

# [impl-review-fix] 语义对齐 ship_gate.EXIT_UNKNOWN=6（设计禁 import gate，手动同步；
# gate 侧字面见 ship_gate.py:137 `EXIT_OK, EXIT_REFUSE, EXIT_BLOCKED, EXIT_VFAIL, EXIT_UNKNOWN
# = 0, 3, 4, 5, 6`）。
EXIT_ROUTE_STOP = 6

# [impl-review-fix] 列 0 锚定 + 冒号前容忍空白（`impl-pipeline : tickets` 一类变体也命中），
# 相比旧版 `line.startswith("impl-pipeline:")` 不再要求冒号紧跟键名。捕获组=冒号后原文（未 strip）。
KEY_RE = re.compile(r"^impl-pipeline\s*:(.*)$")

# [impl-review-fix] 与 ship_gate.TASK_TITLE_RE 逐字一致（^### Task (\d+):，单空格、无 M 标志——
# 本模块逐行扫描不需要 MULTILINE）。排版漂移（`###Task 1:`/`### Task  1:`）不计任务，行为与
# gate 一致（sdflow-ship/scripts/ship_gate.py:483 TASK_TITLE_RE）。
TASK_HEADER_RE = re.compile(r"^### Task (\d+):")
BLOCKED_BY_RE = re.compile(r"\*{0,2}Blocked-by:\*{0,2}\s*(.*)$")
# [impl-review-fix] 疑似变体检测（大小写不同 / 全角冒号），case-insensitive、半角全角冒号皆认；
# 仅当某行未被 BLOCKED_BY_RE 命中时才检查此正则，命中即判「疑似声明格式不识别」。
BLOCKED_BY_VARIANT_RE = re.compile(r"(?i)\*{0,2}blocked-by\*{0,2}\s*[:：]")


class RouteStop(Exception):
    """管线 marker 存在但非法/重复/损坏——UNKNOWN 语义，停，不静默回退。"""


class TopoError(Exception):
    """Blocked-by 拓扑非法：环/自环/引用不存在的依赖号。"""


# ---------------------------------------------------------------------------
# 文本标量提取（config 与 marker frontmatter 共用：允许引号值、去行内注释）
# ---------------------------------------------------------------------------

def _extract_scalar(raw: str) -> Tuple[str, bool]:
    """返回 (value, damaged)。

    [impl-review-fix] 损坏标量 fail-closed 契约：未闭合引号、或闭合引号后跟非注释非空白
    字符（如 `"tickets" junk`）→ damaged=True，调用方各自 fail-closed（config→
    unknown-value 诊断值；marker→RouteStop），不再像旧版那样静默兜底成合法值绕过停机策略。
    """
    s = raw.strip()
    if not s:
        return "", False
    if s[0] in ("'", '"'):
        q = s[0]
        end = s.find(q, 1)
        if end == -1:
            return s[1:], True  # 未闭合引号 → 损坏
        rest = s[end + 1:].strip()
        if rest and not rest.startswith("#"):
            return s[1:end], True  # 闭合引号后跟非注释垃圾 → 损坏
        return s[1:end], False
    hash_idx = s.find("#")
    if hash_idx != -1:
        s = s[:hash_idx]
    return s.strip(), False


# ---------------------------------------------------------------------------
# ① config 键
# ---------------------------------------------------------------------------

def read_config_pipeline(root) -> Tuple[str, str]:
    """读 <root>/openspec/config.yaml 顶层 `impl-pipeline:` 行。

    返回 (pipeline, note)：
        缺失/空值      → ("superpowers", "absent")
        tickets/superpowers → (值, "ok")
        其他值/损坏标量 → ("superpowers", "unknown-value:<原文>")（F12：非法值回显，区别于缺省；
                          损坏标量同归此路径——fail 向旧管线，且原文回显可诊断）
    """
    config_path = Path(root) / "openspec" / "config.yaml"
    if not config_path.exists():
        return "superpowers", "absent"

    text = config_path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("﻿"):
        text = text[1:]  # [impl-review-fix] BOM 剥离，口径对齐 ship_gate.py:308

    raw_field: Optional[str] = None
    for line in text.splitlines():
        # 顶层键要求列 0 起始（排除注释行 `# impl-pipeline: ...` 与缩进内文本，
        # 如 `context: |` 块标量正文提及同名字样）；KEY_RE 容忍冒号前空白。
        m = KEY_RE.match(line)
        if m is not None:
            raw_field = m.group(1)
            break

    if raw_field is None:
        return "superpowers", "absent"

    raw_stripped = raw_field.strip()
    if not raw_stripped:
        return "superpowers", "absent"

    value, damaged = _extract_scalar(raw_field)
    if damaged:
        return "superpowers", f"unknown-value:{raw_stripped}"
    if not value:
        return "superpowers", "absent"
    if value in LEGAL_PIPELINES:
        return value, "ok"
    return "superpowers", f"unknown-value:{value}"


# ---------------------------------------------------------------------------
# ② plan frontmatter marker
# ---------------------------------------------------------------------------

def read_plan_marker(plan_path) -> Optional[str]:
    """读 plan 文件头 frontmatter 的 `impl-pipeline` marker。

    文件缺            → None
    无 frontmatter / 无键 → "superpowers"（旧管线产物，不嗅探正文内容）
    首块 frontmatter 含 impl-pipeline: tickets|superpowers 单值 → 该值
    键重复 / 值非法 / 值损坏（未闭合引号等）/ frontmatter 未闭合 → raise RouteStop（UNKNOWN 语义，停）
    """
    p = Path(plan_path)
    if not p.exists():
        return None

    text = p.read_text(encoding="utf-8", errors="replace")
    if text.startswith("﻿"):
        text = text[1:]  # [impl-review-fix] BOM 剥离，口径对齐 ship_gate.py:308
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

    raw_fields: List[str] = []
    for line in lines[1:close_idx]:
        m = KEY_RE.match(line)  # [impl-review-fix] 容忍冒号前空白
        if m is not None:
            raw_fields.append(m.group(1))

    if not raw_fields:
        return "superpowers"  # frontmatter 在，但无 impl-pipeline 键
    if len(raw_fields) > 1:
        raise RouteStop(f"plan frontmatter impl-pipeline 键重复: {p}")

    value, damaged = _extract_scalar(raw_fields[0])
    if damaged:
        raise RouteStop(
            f"plan frontmatter impl-pipeline 值损坏: {raw_fields[0].strip()!r} ({p})")
    if value not in LEGAL_PIPELINES:
        raise RouteStop(f"plan frontmatter impl-pipeline 值非法: {value!r} ({p})")
    return value


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

    [impl-review-fix F4] fence-aware：围栏内的行对标题与声明行均不可见，口径与
    ship_gate._parse_plan **同源**——直接复用 `ship_gate.FenceTracker`（`` ``` `` 与 `~~~`
    两族、闭合须同种且长度 ≥ 开启符、尾部只余空白），MUST NOT 再手抄
    `line.lstrip().startswith("```")`（旧手抄口径会被嵌套示例围栏的内层 ``` 提前关掉）。

    三态 fail-closed 契约（frontier 只服务 tickets plan，SKILL 契约要求每票显式声明依赖，
    不再对「段内无 Blocked-by 行」静默当无依赖）：
        每个 Task 段 MUST 恰好一条 canonical Blocked-by 行（`Blocked-by:` / `**Blocked-by:**`，
        允许行内前缀如 `R-ID: 1.1 · Blocked-by: none`）：
            0 条  → TopoError「Task N 缺 Blocked-by 声明」
            >1 条 → TopoError「Task N Blocked-by 声明重复」
        段内出现疑似变体（大小写不同如 `blocked-by:`、全角冒号 `Blocked-by：`）但未被
        canonical 正则命中同一行 → TopoError「Task N 疑似 Blocked-by 声明格式不识别」。

    环 / 自环 / 引用不存在的依赖号 → raise TopoError（结构校验，与 done 集无关）。
    EOF 时围栏未闭合（悬空 ```）→ raise TopoError（与 gate UNKNOWN 同向 fail-closed，防悬空
    围栏吞真实 Task 段/Blocked-by 行而假判「无依赖」）。
    """
    if _FenceTracker is None:
        # [impl-review-fix F4] 引不到单一源 ⇒ 停，MUST NOT 用手抄口径顶上（口径漂移
        # 正是本条要根治的病；假 ✅ 的方向比停下来贵得多）。
        raise TopoError("无法加载围栏词法单一源 ship_gate.FenceTracker，拒绝以分叉口径解析 plan")

    task_ids: Set[int] = set()
    segments: List[Tuple[int, List[str]]] = []
    cur_tid: Optional[int] = None
    cur_lines: List[str] = []
    fence = _FenceTracker()

    def _flush() -> None:
        if cur_tid is not None:
            segments.append((cur_tid, cur_lines))

    for line in plan_text.splitlines():
        if fence.feed(line) or fence.inside:
            continue
        m = TASK_HEADER_RE.match(line)
        if m:
            _flush()
            cur_tid = int(m.group(1))
            cur_lines = []
            task_ids.add(cur_tid)
            continue
        if cur_tid is not None:
            cur_lines.append(line)
    _flush()

    if fence.inside:
        raise TopoError("plan 存在未闭合的 fenced 代码块（```），解析不可靠")

    if not segments:
        return {}

    deps: Dict[int, Set[int]] = {}
    for tid, seg_lines in segments:
        canonical_hits: List[str] = []
        variant_hit = False
        for line in seg_lines:
            cm = BLOCKED_BY_RE.search(line)
            if cm is not None:
                canonical_hits.append(cm.group(1).strip())
                continue
            if BLOCKED_BY_VARIANT_RE.search(line):
                variant_hit = True
        if variant_hit:
            raise TopoError(f"Task {tid} 疑似 Blocked-by 声明格式不识别")
        if not canonical_hits:
            raise TopoError(f"Task {tid} 缺 Blocked-by 声明")
        if len(canonical_hits) > 1:
            raise TopoError(f"Task {tid} Blocked-by 声明重复")

        raw = canonical_hits[0]
        dep_set: Set[int] = set()
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
        return EXIT_ROUTE_STOP

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
        return EXIT_ROUTE_STOP

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
                return EXIT_ROUTE_STOP
            done.add(int(part))

    try:
        deps = parse_blocked_by(text)
        ready = next_ready(deps, done)
    except TopoError as e:
        print(str(e), file=sys.stderr)
        return EXIT_ROUTE_STOP

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
