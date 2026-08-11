#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""impl_route.py — sdflow-implement tickets 调度 helper（stdlib-only，只读、零副作用）

本文件是 tickets 管线（唯一实现管线，见 adr/0042）的调度基础设施，提供两个子命令：
    `frontier`   —— 按 Blocked-by 拓扑算 next-ready ticket 号
    `task-text`  —— 机械抠出单张 Task 段原文落盘，供 dispatch prompt 引用文件路径
                     （替代编排层手抄 Task N 段落全文——手抄=转录风险）
两者共用同一份 `parse_blocked_by` 拓扑解析（Blocked-by 依赖图单一源，基准 5：无界语法禁手搓）。

[remove-superpowers-pipeline] 本文件原含「管线路由三跳」（config 键 → plan frontmatter marker →
缺省，二选一派发 tickets/superpowers）——tickets 成为唯一管线后，route 子命令与全部路由函数
（`read_config_pipeline` / `read_plan_marker` / `resolve_pipeline` / `RouteStop` / `_get_plan_sha`
/ `_yq`）已整体切除（design.md 决策，adr/0042 supersede adr/0033）。保留半场（`frontier` /
`task-text` 子命令、`parse_blocked_by`、`_detect_cycle`、`next_ready`、`extract_task_text`、
`TopoError`、`BLOCKED_BY_RE`）接口与行为逐字不变——`sdflow-ship/scripts/ship_gate.py` 经既有
sibling-import 消费 `parse_blocked_by`/`TopoError`（收尾票 Blocked-by 校验单一源），本次切除
对其零感知。

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
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

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
except Exception as _e:                                  # noqa: BLE001
    _FenceTracker = None                                 # fail-closed，见 parse_blocked_by
    # [impl-review-fix] 记下失败原因串：fail-closed 本身对，但吞掉原因会让
    # 「装歪了 vs 语法错 vs 版本不符」三种情况在诊断上无法区分。
    _FENCE_IMPORT_ERR = f"{type(_e).__name__}: {_e}"
else:
    _FENCE_IMPORT_ERR = ""

# [impl-review-fix] 语义对齐 ship_gate.EXIT_UNKNOWN=6（设计禁 import gate，手动同步；
# gate 侧字面见 ship_gate.py:137 `EXIT_OK, EXIT_REFUSE, EXIT_BLOCKED, EXIT_VFAIL, EXIT_UNKNOWN
# = 0, 3, 4, 5, 6`）。
EXIT_ROUTE_STOP = 6

# [impl-review-fix] 与 ship_gate.TASK_TITLE_RE 逐字一致（^### Task (\d+):，单空格、无 M 标志——
# 本模块逐行扫描不需要 MULTILINE）。排版漂移（`###Task 1:`/`### Task  1:`）不计任务，行为与
# gate 一致（sdflow-ship/scripts/ship_gate.py:483 TASK_TITLE_RE）。
TASK_HEADER_RE = re.compile(r"^### Task (\d+):")
BLOCKED_BY_RE = re.compile(r"\*{0,2}Blocked-by:\*{0,2}\s*(.*)$")
# [impl-review-fix] 疑似变体检测（大小写不同 / 全角冒号），case-insensitive、半角全角冒号皆认；
# 仅当某行未被 BLOCKED_BY_RE 命中时才检查此正则，命中即判「疑似声明格式不识别」。
BLOCKED_BY_VARIANT_RE = re.compile(r"(?i)\*{0,2}blocked-by\*{0,2}\s*[:：]")


class TopoError(Exception):
    """Blocked-by 拓扑非法：环/自环/引用不存在的依赖号。"""


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
        raise TopoError(
            "无法加载围栏词法单一源 ship_gate.FenceTracker，拒绝以分叉口径解析 plan"
            + (f"（import 失败原因：{_FENCE_IMPORT_ERR}）" if _FENCE_IMPORT_ERR else "")
        )

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
# 单张 Task 原文机械抠取（仿 matt to-tickets 的 task-brief 脚本），
# 供 dispatch prompt 引用文件路径，不再要求编排层手抄 Task N 段落全文
# （手抄=转录风险；此前 SKILL.md 编辑本身就撞过 old_string 对不上的坑）。
# ---------------------------------------------------------------------------

def extract_task_text(plan_text: str, task_id: int) -> Optional[str]:
    """按 `### Task N:` 分段抠出单张 ticket 的完整原文（含标题行，止于下一个 Task 标题或 EOF）。

    围栏词法（单一源 ship_gate.FenceTracker）只用于**标题识别**的豁免——fenced 示例里的
    `### Task N:` 字样不触发切段；一旦确认身处目标 Task 段内，段内所有行（含 fenced 内容，
    如出票规则允许内联的 prototype 决策性片段）原样收录、不做二次过滤——这是 ticket 的真实
    正文，不是需要滤掉的噪音（同 matt task-brief 脚本行为：fence 只挡标题误判，不挡正文收录；
    与 parse_blocked_by 整段跳过 fenced 行的口径**有意不同**，二者用途不同不可混用）。

    返回 None 表示 plan 里没有该编号的 Task 段。
    """
    if _FenceTracker is None:
        raise TopoError(
            "无法加载围栏词法单一源 ship_gate.FenceTracker，拒绝以分叉口径解析 plan"
            + (f"（import 失败原因：{_FENCE_IMPORT_ERR}）" if _FENCE_IMPORT_ERR else "")
        )
    # 扫描**全文到 EOF**（不因目标段已收完就提前退出）——与 parse_blocked_by 同一份
    # fail-closed 纪律对齐：目标段之后的悬空围栏一样代表"这份 plan 解析不可靠"，
    # 早退会让扫描停在悬空围栏产生之前、看不见它，把一个真实的解析风险静默放过。
    fence = _FenceTracker()
    cur_tid: Optional[int] = None
    out_lines: List[str] = []
    seen = False
    collecting = False
    for line in plan_text.splitlines():
        gated = fence.feed(line) or fence.inside
        if not gated:
            m = TASK_HEADER_RE.match(line)
            if m:
                new_tid = int(m.group(1))
                if collecting and new_tid != task_id:
                    collecting = False  # 目标段已收完，只停止收录，扫描仍继续到 EOF
                cur_tid = new_tid
                if cur_tid == task_id:
                    seen = True
                    collecting = True
        if collecting and cur_tid == task_id:
            out_lines.append(line)

    if fence.inside:
        raise TopoError("plan 存在未闭合的 fenced 代码块（```），解析不可靠")
    if not seen:
        return None
    return "\n".join(out_lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

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


def _cmd_task_text(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"plan 文件不存在: {plan_path}", file=sys.stderr)
        return EXIT_ROUTE_STOP

    text = plan_path.read_text(encoding="utf-8", errors="replace")
    try:
        extracted = extract_task_text(text, args.task)
    except TopoError as e:
        print(str(e), file=sys.stderr)
        return EXIT_ROUTE_STOP

    if extracted is None:
        print(f"Task {args.task} 在 {plan_path} 中不存在", file=sys.stderr)
        return EXIT_ROUTE_STOP

    if args.out:
        out_path = Path(args.out)
    else:
        # 默认落 {change_dir}/impl-reports/task<N>-brief.md——沿用 T125 既有的
        # report/review-package 文件命名惯例（plan_path.parent 即 change_dir）。
        out_path = plan_path.parent / "impl-reports" / f"task{args.task}-brief.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(extracted, encoding="utf-8")
    print(f"wrote {out_path}: {len(extracted.splitlines())} lines")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="sdflow-implement tickets 调度 stdlib helper（只读，不改 ship_gate.py）")
    sub = p.add_subparsers(dest="cmd", required=True)

    frontier_p = sub.add_parser("frontier", help="按 Blocked-by 拓扑算 next-ready ticket 号")
    frontier_p.add_argument("--plan", required=True, help="plan 文件路径")
    frontier_p.add_argument("--done", required=True, help="逗号分隔已完成号列，或 none")

    task_text_p = sub.add_parser(
        "task-text", help="机械抠出单张 Task 段原文落盘，供 dispatch prompt 引用路径而非手抄")
    task_text_p.add_argument("--plan", required=True, help="plan 文件路径")
    task_text_p.add_argument("--task", required=True, type=int, help="Task 号")
    task_text_p.add_argument(
        "--out", help="输出路径（默认 <change_dir>/impl-reports/task<N>-brief.md）")

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "frontier":
        return _cmd_frontier(args)
    if args.cmd == "task-text":
        return _cmd_task_text(args)
    parser.error(f"未知子命令: {args.cmd}")  # pragma: no cover
    return 2


if __name__ == "__main__":
    sys.exit(main())
