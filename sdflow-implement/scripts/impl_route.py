#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""impl_route.py — sdflow-implement tickets 调度 helper（stdlib-only + 外部 yq 二进制，只读、零副作用）

本文件是 tickets 管线（唯一实现管线，见 adr/0042）的调度基础设施，提供三个子命令：
    `frontier`     —— 按 Blocked-by 拓扑算 next-ready ticket 号
    `task-text`    —— 机械抠出单张 Task 段原文落盘，供 dispatch prompt 引用文件路径
                       （替代编排层手抄 Task N 段落全文——手抄=转录风险）
    `suite-scope`  —— 按 diff 路径归域求值收尾票测试层集合（`adr/0045`；design.md 决策 §2）
`frontier`/`task-text` 共用同一份 `parse_blocked_by` 拓扑解析（Blocked-by 依赖图单一源，
基准 5：无界语法禁手搓）。

[scope-aggregate-suite-by-diff-domain Task 1] `suite-scope` 重新内联 `_yq()`（骨架同
`sdflow-init/assets/workflow/tools/anchor_lint.py`，不引 `ship_gate.GateIndeterminate`——
本文件失败一律走 `SuiteScopeError`/`RuntimeError`，由 `_cmd_suite_scope` 统一转译成
stderr `problem/cause/fix` + `EXIT_ROUTE_STOP`）。`_yq()` 消费点计数见
`hack/tests/test_yq_wrapper_consistency.py` 的 `TARGETS`（份数不写死，以实际枚举为准）。

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
import json
import re
import shutil
import subprocess
import sys
import tempfile  # [impl-review-fix F3]

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
# suite-scope：按 diff 路径归域求值收尾票测试层集合（adr/0045，design.md §2）
# ---------------------------------------------------------------------------

class SuiteScopeError(Exception):
    """`suite-scope` 判定失败（坏配置 / git 命令失败 / --base·--head 非法）——一律 fail-loud，
    携带 problem/cause/fix 三段人读诊断，由 `_cmd_suite_scope` 统一格式化到 stderr + 退出 6。"""

    def __init__(self, problem: str, cause: str, fix: str) -> None:
        super().__init__(problem)
        self.problem = problem
        self.cause = cause
        self.fix = fix


# [scope-aggregate-suite-by-diff-domain Task 1] `_yq()` 内联封装，骨架同
# `sdflow-init/assets/workflow/tools/anchor_lint.py`（shutil.which 探测 + `--version` 身份
# 校验 + 进程内缓存 + fail-loud；design.md §1「不跨脚本共享」决定）。本文件不引
# `ship_gate.GateIndeterminate`——yq 缺失/身份不对/解析失败统一 raise `_YqError`，
# 由 `_cmd_suite_scope` 转译为 `SuiteScopeError` 同构的 problem/cause/fix（Global
# Constraints：「yq 缺失或身份不对同路径」= 与坏配置同路径退出 6）。仅接受 `file=` 路径参数
# （本文件唯一消费点读磁盘上的 `openspec/config.yaml`，不需要 `ship_gate.py`/`sad_schema.py`
# 的 `text=` stdin 变体）。
_yq_bin = None  # 进程内缓存

_YQ_INSTALL_FIX = (
    "  macOS:   brew install yq\n"
    "  Windows: winget install --id MikeFarah.yq\n"
    "  Linux:   snap install yq")


class _YqError(RuntimeError):
    """[closeout-suite-scope-leftovers T304] `_yq()` 五种失败成因的载体——按成因携带
    专属 problem/fix（design.md Decisions「六成因表」），不再统一「yq 调用失败」四字。
    `super().__init__(message)`（只传 message，MUST NOT 把 fix 一并传给基类）⇒
    `str(e)` 就是 cause 文案；`_cmd_suite_scope` 的 `except RuntimeError` 原样捕获本类
    （子类被父类 except 捕获），`getattr(e, "problem"/"fix", 默认值)` 取专属诊断。"""

    def __init__(self, problem: str, message: str, fix: str) -> None:
        super().__init__(message)
        self.problem = problem
        self.fix = fix



def _first_line(text):
    """取多行输出的首行（无输出时空串）——`_yq` 探针/身份两条诊断分支共用（T306）。"""
    lines = (text or "").strip().splitlines()[:1]
    return lines[0] if lines else ""

def _yq(expression, file, *, front_matter=False, in_place=False, default=None):
    """yq(mikefarah) subprocess 薄封装。exit≠0（解析失败/文件不可读）MUST raise，不吞——
    「键不存在」（exit 0 + stdout=null，走 default）与「解析失败」（exit≠0，走 raise）是
    两条不同分支（同 `yq-yaml-operations` spec R7）。"""
    global _yq_bin
    if _yq_bin is None:
        yq = shutil.which("yq")
        if not yq:
            raise _YqError(
                "yq 未安装",
                "PATH 上找不到 yq",
                "安装方式：\n" + _YQ_INSTALL_FIX)
        vr = subprocess.run([yq, "--version"], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        if vr.returncode != 0:
            raise _YqError(
                "yq 可执行文件损坏或不可执行",
                f"yq --version 退出码 {vr.returncode}：{_first_line(vr.stderr)}",
                "重装 mikefarah/yq：\n" + _YQ_INSTALL_FIX)
        if "mikefarah" not in vr.stdout:
            raise _YqError(
                "yq 实现不匹配",
                "检测到的 yq 不是 mikefarah/yq（可能是 kislyuk/yq）："
                f"{_first_line(vr.stdout)}",
                "卸载 kislyuk/yq 后安装 mikefarah/yq：\n" + _YQ_INSTALL_FIX)
        _yq_bin = yq
    cmd = [_yq_bin]
    if front_matter:
        cmd += [f"--front-matter={'process' if in_place else 'extract'}"]
    if in_place:
        cmd.append("-i")
    else:
        cmd += ["-o", "json"]
    cmd.append(expression)
    cmd.append(str(file))
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise _YqError(
            "openspec/config.yaml 无法解析",
            f"yq failed on {file}: {r.stderr.strip()}",
            "`openspec/config.yaml` YAML 语法错误或文件不可读——"
            "按 cause 里的 yq stderr 定位修正，不是 yq 安装问题")
    if in_place:
        return None
    raw = r.stdout.strip()
    if not raw or raw == "null":
        return default
    decoder = json.JSONDecoder()
    try:
        parsed, idx = decoder.raw_decode(raw)
    except json.JSONDecodeError as e:
        # [impl-review-fix A1] JSONDecodeError 是 ValueError 子类、不是 RuntimeError——不转译
        # 会逃过 _cmd_suite_scope 的 except RuntimeError 裸 traceback 退出 1，违反「退出 6 +
        # 三段诊断」契约。第六成因：yq 身份对、主调用 exit 0、stdout 却非 JSON。
        raise _YqError(
            "openspec/config.yaml 输出非合法 JSON",
            f"yq -o json 对 {file} 的输出无法解析为 JSON（{e}）: {raw[:200]!r}",
            "yq 对 `openspec/config.yaml` 输出了非 JSON 内容——按 cause 里的原始输出定位"
            "（yq 版本异常或配置含 yq 无法转 JSON 的值），不是 yq 安装问题")
    if raw[idx:].strip():
        raise _YqError(
            "openspec/config.yaml 含多文档",
            f"yq 输出多个 JSON 值（疑似多文档 YAML，不支持）: {raw[:200]!r}",
            "`openspec/config.yaml` 含多文档分隔 `---`，合并为单文档")
    return parsed


def _run_git_text(root: Path, args: List[str]) -> subprocess.CompletedProcess:
    """跑一条 text 模式 git 子命令（`errors="replace"`——诊断展示允许有损归一化）。
    [closeout-suite-scope-leftovers T300] 5 处逐字相同的样板收敛于此；`_run_git_z`
    是 bytes 模式 + `surrogateescape`（判定层字节保真，不做规范化），解码契约不同，
    不与本 helper 合并（Global Constraints）。"""
    return subprocess.run(["git", "-C", str(root)] + args,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _detect_default_branch(root: Path) -> str:
    """默认分支三段式检测——与 `sdflow-done/SKILL.md:175-187`「0.2 检测默认分支」**同口径
    重实现**（那是 SKILL prose 里的 bash，本函数是可 import 的 Python 版；两处无机械联动，
    改任一处 MUST 核对另一处，design.md §2 base 决策段落已记录此非机械同步风险）：
        1. `git symbolic-ref refs/remotes/origin/HEAD` 有值 → 取其短分支名
        2. 否则 `git rev-parse --verify origin/master` 成功 → "master"
        3. 否则 → "main"（不校验 main 是否真存在——与 bash 版的无条件 `|| echo main` 同构；
           若 main 实际不存在，失败会在随后的 `merge-base` 调用暴露，走同一条 fail-loud 路径）
    """
    r = _run_git_text(root, ["symbolic-ref", "refs/remotes/origin/HEAD"])
    if r.returncode == 0 and r.stdout.strip():
        ref = r.stdout.strip()
        prefix = "refs/remotes/origin/"
        return ref[len(prefix):] if ref.startswith(prefix) else ref
    r2 = _run_git_text(root, ["rev-parse", "--verify", "origin/master"])
    if r2.returncode == 0:
        return "master"
    return "main"


def _rev_parse(root: Path, ref: str) -> str:
    r = _run_git_text(root, ["rev-parse", "--verify", ref])
    if r.returncode != 0:
        raise SuiteScopeError(
            f"{ref!r} 不是仓内合法的 commit-ish",
            r.stderr.strip() or "git rev-parse --verify 非零退出",
            "确认传入的 --base/--head 值在本仓内存在")
    return r.stdout.strip()


def _merge_base(root: Path, default_branch: str) -> str:
    r = _run_git_text(root, ["merge-base", default_branch, "HEAD"])
    if r.returncode != 0:
        raise SuiteScopeError(
            f"git merge-base {default_branch} HEAD 失败",
            r.stderr.strip() or "退出码非零（默认分支不存在，或与 HEAD 无共同祖先）",
            f"确认默认分支 {default_branch!r} 在本仓存在，且与当前 HEAD 有共同祖先")
    return r.stdout.strip()


def _resolve_base(root: Path, base_arg: Optional[str]) -> str:
    if base_arg:
        return _rev_parse(root, base_arg)
    default_branch = _detect_default_branch(root)
    return _merge_base(root, default_branch)


def _run_git_z(root: Path, args: List[str]) -> List[str]:
    """跑一条 `-z` 输出的 git 子命令，NUL 分隔、字节保真（`surrogateescape` 解码，判定层
    不做规范化——Global Constraints「路径以 -z 读取、内部以 surrogateescape 解码后做归域」）。"""
    r = subprocess.run(["git", "-C", str(root)] + args, capture_output=True)
    if r.returncode != 0:
        raise SuiteScopeError(
            f"git {' '.join(args)} 失败",
            r.stderr.decode("utf-8", errors="replace").strip() or "退出码非零",
            "确认 base/head 在仓内合法、仓库未损坏")
    raw = r.stdout
    if not raw:
        return []
    return [p.decode("utf-8", errors="surrogateescape") for p in raw.split(b"\x00") if p]


def _collect_changed(root: Path, base: str, head_arg: Optional[str]) -> Tuple[str, Set[str]]:
    """changed 路径集合 + 实际使用的 head。`--head` 给出 ⇒ 提交范围模式（`git diff --name-only
    -z <base> <head>`，不含未跟踪文件）；否则 ⇒ 工作树模式（diff base 对工作树 ∪ 未跟踪文件）。
    两种模式均硬排除以 `openspec/` 开头的路径。"""
    if head_arg:
        head = _rev_parse(root, head_arg)
        changed = set(_run_git_z(root, ["diff", "--name-only", "-z", base, head]))
    else:
        head = _rev_parse(root, "HEAD")
        changed = set(_run_git_z(root, ["diff", "--name-only", "-z", base]))
        changed |= set(_run_git_z(root, ["ls-files", "--others", "--exclude-standard", "-z"]))
    changed = {p for p in changed if not p.startswith("openspec/")}
    return head, changed


def _normalize_layer_value(domain_name: str, layer_name: str, val):
    """层值 → `{quick, full}`（design.md §2：字符串两键同值；映射缺 quick ⇒ quick=full；缺
    full ⇒ full=quick；规则对全部层名一致，无 unit 特例）。"""
    if isinstance(val, str):
        return {"quick": val, "full": val}
    if isinstance(val, dict):
        allowed = {"quick", "full"}
        unknown = set(val.keys()) - allowed
        if unknown:
            raise SuiteScopeError(
                f"域 {domain_name!r} 层 {layer_name!r} 的值含未知键",
                f"未知键: {sorted(unknown)}（值={val!r}）",
                "层值映射只能含 quick/full 两键")
        for k, v in val.items():
            if not isinstance(v, str):
                raise SuiteScopeError(
                    f"域 {domain_name!r} 层 {layer_name!r} 的 {k} 值非字符串",
                    f"值={v!r}",
                    "quick/full 的值必须是命令字符串")
        quick, full = val.get("quick"), val.get("full")
        if quick is None and full is None:
            raise SuiteScopeError(
                f"域 {domain_name!r} 层 {layer_name!r} 的值是空映射",
                "既无 quick 也无 full，未声明任何命令",
                "至少给出 quick 或 full 其中一个")
        if quick is None:
            quick = full
        if full is None:
            full = quick
        return {"quick": quick, "full": full}
    raise SuiteScopeError(
        f"域 {domain_name!r} 层 {layer_name!r} 的值形状非法",
        f"值={val!r} 既非字符串也非 quick/full 映射",
        "层值须为字符串，或只含 quick/full 键（值为字符串）的映射")


def _validate_domains(domains_raw) -> Tuple[Dict[str, dict], str]:
    """校验 `test-suites.domains`（design.md §1 合法性全文）：非空映射；每域含 `paths`
    （字符串列表）与 `layers`（映射，`null`/`{}` 等价均合法）；恰一个域 `default: true`；
    每层值形状合法；同前缀不得跨域；同名层不得跨域（含默认域）。坏 ⇒ `SuiteScopeError`。
    返回 (规范化后的 domains 字典, default 域名)。"""
    if not isinstance(domains_raw, dict) or not domains_raw:
        raise SuiteScopeError(
            "test-suites.domains 非法",
            f"值 {domains_raw!r} 不是非空映射",
            "domains 必须是至少一个域的映射，每域含 paths 与 layers")

    seen_paths: Dict[str, str] = {}
    seen_layers: Dict[str, str] = {}
    validated: Dict[str, dict] = {}
    default_count = 0
    default_name: Optional[str] = None

    for name, spec in domains_raw.items():
        if not isinstance(spec, dict):
            raise SuiteScopeError(
                f"域 {name!r} 定义非法", f"值 {spec!r} 不是映射",
                "每个域须为含 paths/layers 的映射")
        if "paths" not in spec or "layers" not in spec:
            raise SuiteScopeError(
                f"域 {name!r} 缺必填字段",
                f"缺 {'paths' if 'paths' not in spec else 'layers'}",
                "补齐 paths（字符串列表）与 layers（映射，可为空/null）")

        paths = spec["paths"]
        if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
            raise SuiteScopeError(
                f"域 {name!r} 的 paths 非法", f"paths={paths!r} 不是字符串列表",
                "paths 必须是字符串列表（可为空列表）")

        layers_raw = spec.get("layers")
        if layers_raw is None:
            layers_raw = {}
        if not isinstance(layers_raw, dict):
            raise SuiteScopeError(
                f"域 {name!r} 的 layers 非法", f"layers={layers_raw!r} 不是映射",
                "layers 必须是映射（可为空映射或 null，两者等价）")

        layers_norm: Dict[str, dict] = {}
        for lname, lval in layers_raw.items():
            if lname in seen_layers:
                raise SuiteScopeError(
                    "跨域同名层",
                    f"层 {lname!r} 同时出现在域 {seen_layers[lname]!r} 与 {name!r}",
                    "层是「域 × 命令」，同名无合理合并语义——改名或合并域")
            seen_layers[lname] = name
            layers_norm[lname] = _normalize_layer_value(name, lname, lval)

        for p in paths:
            if p in seen_paths:
                if seen_paths[p] == name:
                    # [closeout-suite-scope-leftovers T302] 同域内部重复——不得表述为
                    # 「域 X 与 X」（自指），须指明「域 X 的 paths 内重复路径 p」。
                    raise SuiteScopeError(
                        "域内重复路径",
                        f"域 {name!r} 的 paths 内重复路径 {p!r}",
                        "去掉重复项")
                raise SuiteScopeError(
                    "同前缀双域",
                    f"路径 {p!r} 同时出现在域 {seen_paths[p]!r} 与 {name!r} 的 paths 中",
                    "同一前缀只能属于一个域")
            seen_paths[p] = name

        is_default = spec.get("default", False)
        if "default" in spec:
            if not isinstance(is_default, bool):
                raise SuiteScopeError(
                    f"域 {name!r} 的 default 值非布尔",
                    f"default={is_default!r}",
                    "default 只能省略、或写布尔 true/false")
            if is_default:
                default_count += 1
                default_name = name

        validated[name] = {"paths": paths, "layers": layers_norm}

    if default_count != 1:
        raise SuiteScopeError(
            "default 域数量非法",
            f"共 {default_count} 个域声明 default: true",
            "必须恰有一个域声明 default: true")

    return validated, default_name  # type: ignore[return-value]


def _match_domain(path: str, domains: Dict[str, dict], default_name: str
                   ) -> Tuple[str, Optional[str]]:
    """在全部域（含默认域）的 paths 中取最长匹配前缀；无匹配 ⇒ 默认域。以 `/` 结尾 = 目录
    前缀匹配（`path.startswith(prefix)`）；不以 `/` 结尾 = 精确路径相等。"""
    best_len = -1
    best_domain: Optional[str] = None
    best_prefix: Optional[str] = None
    for name, spec in domains.items():
        for p in spec["paths"]:
            matched = path.startswith(p) if p.endswith("/") else path == p
            if matched and len(p) > best_len:
                best_len = len(p)
                best_domain = name
                best_prefix = p
    if best_domain is None:
        return default_name, None
    return best_domain, best_prefix


def _classify_changed(changed: Set[str], domains: Dict[str, dict], default_name: str
                       ) -> Tuple[List[str], List[dict]]:
    mapping: List[dict] = []
    hit: Set[str] = set()
    for path in sorted(changed):
        domain, prefix = _match_domain(path, domains, default_name)
        hit.add(domain)
        mapping.append({"path": path, "domain": domain, "prefix": prefix})
    if not changed:
        hit = {default_name}
    return sorted(hit), mapping


def _aggregate_layers(domains: Dict[str, dict], hit_domains: List[str]
                       ) -> Tuple[Dict[str, dict], Dict[str, str]]:
    """|D|==1 ⇒ 该域 layers；|D|>1 ⇒ 命中域 layers 按层名并集（跨域同名层已在校验阶段
    fail-loud，并集无冲突可言）。未命中域的层名记入 skipped_layers（层名 → 域名）。"""
    hit_set = set(hit_domains)
    layers: Dict[str, dict] = {}
    skipped: Dict[str, str] = {}
    for name, spec in domains.items():
        if name in hit_set:
            layers.update(spec["layers"])
        else:
            for lname in spec["layers"]:
                skipped[lname] = name
    return layers, skipped


def _read_test_suites(config_path: Optional[Path]) -> dict:
    if config_path is None or not config_path.is_file():
        return {}
    ts = _yq(".test-suites", config_path, default={})
    return ts if isinstance(ts, dict) else {}


def _domains_key_present(config_path: Optional[Path]) -> bool:
    """[impl-review-fix F2] `test-suites.domains` 键**是否存在**（不是「值 is not None」）——
    区分「键真缺席」与「键存在但值为 null/非映射/空映射」：后者是 design.md §1 明写的
    「存在但坏」，MUST 走 `_validate_domains` 的坏配置分支退出 6，不能被 `domains_raw is
    not None` 这种弱判据误当缺席、静默降级到今日三层透传路径。"""
    if config_path is None or not config_path.is_file():
        return False
    return bool(_yq('.test-suites | has("domains")', config_path, default=False))


def _resolve_config_path(root: Path, head_arg: Optional[str], head: str
                          ) -> Tuple[Optional[Path], Optional[str]]:
    """[impl-review-fix F3] 提交范围模式（`--head` 给出）下 config 来源 MUST 是 head 快照
    （`git show <head>:openspec/config.yaml` 写到 tempfile 后交 `_yq`），不是工作树文件——
    否则 sdflow-done verify 在 code-review 修改 config 之后重跑同命令必假红（design.md §2）。
    head 快照无该文件 ⇒ 视同无 `test-suites`。工作树模式（`--head` 缺省）行为不变。
    返回 (config 文件路径或 None, 需在用完后清理的临时文件路径或 None)。"""
    if not head_arg:
        config_path = root / "openspec" / "config.yaml"
        return (config_path if config_path.is_file() else None), None
    r = _run_git_text(root, ["show", f"{head}:openspec/config.yaml"])
    if r.returncode != 0:
        return None, None
    fd, tmp = tempfile.mkstemp(suffix=".yaml")
    with open(fd, "w", encoding="utf-8") as f:
        f.write(r.stdout)
    return Path(tmp), tmp


def suite_scope(root: Path, base_arg: Optional[str], head_arg: Optional[str]) -> dict:
    """`suite-scope` 的纯函数核心（不含 CLI/打印），供子命令与测试共用。坏配置/git 失败
    统一 raise `SuiteScopeError`；yq 层的 `RuntimeError` 由调用方（`_cmd_suite_scope`）转译。"""
    base = _resolve_base(root, base_arg)
    head, changed = _collect_changed(root, base, head_arg)

    config_path, tmp_to_clean = _resolve_config_path(root, head_arg, head)
    try:
        test_suites = _read_test_suites(config_path)
        domains_raw = test_suites.get("domains") if isinstance(test_suites, dict) else None
        domains_configured = _domains_key_present(config_path)

        if domains_configured:
            conflict = [k for k in ("unit", "integration", "e2e") if k in test_suites]
            if conflict:
                raise SuiteScopeError(
                    "domains 与顶层三层键并存",
                    f"test-suites.domains 存在的同时，顶层键 {conflict} 仍残留",
                    "把这些层移入默认域的 layers（迁移期残留 MUST 清理，不静默忽略）")
            domains, default_name = _validate_domains(domains_raw)
            hit_domains, mapping = _classify_changed(changed, domains, default_name)
            layers, skipped_layers = _aggregate_layers(domains, hit_domains)
        else:
            hit_domains = []
            mapping = [{"path": p, "domain": None, "prefix": None} for p in sorted(changed)]
            # [impl-review-fix F1] 缺席路径也规范化：层集合仍逐字等同今日（只含配置里存在
            # 的层），但每层值统一走 `_normalize_layer_value`——分档语义单一源已从 SKILL
            # prose 迁到脚本（SKILL.md「聚合套件发现契约」第 2 条：消费方直接读
            # `layers[<层>].quick`/`.full`，规则对全部层名一致，无 unit 特例，design.md §2）。
            layers = {
                k: _normalize_layer_value("<legacy>", k, test_suites[k])
                for k in ("unit", "integration", "e2e") if k in test_suites
            }
            skipped_layers = {}
    finally:
        if tmp_to_clean:
            try:
                Path(tmp_to_clean).unlink()
            except OSError:
                pass

    return {
        "base": base,
        "head": head,
        "domains_configured": domains_configured,
        "hit_domains": hit_domains,
        "layers": layers,
        "skipped_layers": skipped_layers,
        "mapping": mapping,
    }


def _cmd_suite_scope(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    try:
        result = suite_scope(root, args.base, args.head)
    except SuiteScopeError as e:
        problem, cause, fix = e.problem, e.cause, e.fix
    except RuntimeError as e:
        # yq 未安装 / 版本探针非零退出 / 身份不对 / 解析失败 / 多文档 —— Global
        # Constraints「yq 缺失或身份不对同路径」= 与坏配置同路径退出 6。`_YqError`
        # 子类携带成因专属 problem/fix（design.md Decisions「六成因表」）；非 `_YqError`
        # 的裸 `RuntimeError`（理论上不应出现，兜底）落回旧的统一提示。
        problem, cause, fix = (
            getattr(e, "problem", "yq 调用失败"),
            str(e),
            getattr(e, "fix",
                    "确认已安装 mikefarah/yq（非 kislyuk/yq）且版本兼容：\n"
                    "  macOS:   brew install yq\n"
                    "  Windows: winget install --id MikeFarah.yq\n"
                    "  Linux:   snap install yq"))
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    print(f"problem: {problem}", file=sys.stderr)
    print(f"cause: {cause}", file=sys.stderr)
    print(f"fix: {fix}", file=sys.stderr)
    return EXIT_ROUTE_STOP


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

    suite_scope_p = sub.add_parser(
        "suite-scope", help="按 diff 路径归域求值收尾票测试层集合（adr/0045）")
    suite_scope_p.add_argument("--root", required=True, help="仓库根路径")
    suite_scope_p.add_argument(
        "--base", help="显式指定 base commit-ish（缺省 = 默认分支 merge-base）")
    suite_scope_p.add_argument(
        "--head",
        help="显式指定 head commit-ish（给出时走提交范围模式，不含未跟踪文件；"
             "缺省走工作树模式，含未跟踪文件）")

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "frontier":
        return _cmd_frontier(args)
    if args.cmd == "task-text":
        return _cmd_task_text(args)
    if args.cmd == "suite-scope":
        return _cmd_suite_scope(args)
    parser.error(f"未知子命令: {args.cmd}")  # pragma: no cover
    return 2


if __name__ == "__main__":
    sys.exit(main())
