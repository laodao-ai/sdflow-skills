#!/usr/bin/env python3
"""issues.py — 共享 issues 层脚本：跨 bug+todo 两池（Task 8：read + D9 冲突检测；
Task 9：reindex → issues/INDEX.md）。

背景（design.md §五 grill-amendment B-Q2）：`buglist.py`（sdflow-buglist）与
`todolist.py`（sdflow-todolist）是两个独立 skill 的独立脚本，各管自己一类
（add/scan/set-status/triage）。但 `reindex`/`batch` 是**跨 bug+todo**（join 两池 +
维护 `issues/INDEX.md`/`issues/batches.md`）——这类跨类型命令归本脚本独占，不塞进
per-type 脚本。

本文件现状：
  - `read_pool(root)`（Task 8）：子进程调 buglist.py/todolist.py 的 `scan --json`，
    join 成一份跨两池的 item 列表（每项打 `pool` 标记），join 后立即用
    `cross_pool_id_conflicts` 做 D9 防护网校验。
  - `cross_pool_id_conflicts(items)`（Task 8）：纯函数，检测同一 ID 是否跨池撞号。
  - `reindex`（Task 9 + Task 11）：`read_pool` → `generate_index_md` 纯函数重建
    `issues/INDEX.md`（首行 GENERATED banner + open item×批次物化板 + 已闭合摘要）
    → `atomic_write` 原子落盘。**禁读旧 INDEX**（D3，全量确定性重建）、**幂等**（D7）。
    随后 `sync_batches_md`（Task 11）拿同一份 item 池校验/回写 `issues/batches.md`
    的 `成员:`/`状态:` 两条生成行：D1 完成判据（成员数≥1 且全进各自 pool 终态集才
    判 DONE，0 成员显式排除、防 vacuous-truth 假 DONE）、Q3 不越权纠正（人标 DONE
    但成员未全终态 → 只追加 `⚠️ 不一致` 警告，不改人写的 `状态:` 值）、Q2 orphan
    报警（item 批次 tag 在 batches.md 无对应 key → stderr 报警，不新建 ghost 条目）。
  - `batch`（Task 10）：`issues/batches.md` 注册表 + `add`/`set-status`/`rename`
    三个子命令（Q2 grill-amendment）。`batches.md` 是**半手维护**注册表（Q3 字段级
    grammar）——`状态:`/`成员:` 是生成行（reindex/`batch set-status` 维护），
    `优先级:`/`计划:` 及其它是人写行，**解析/写入绝不覆写人写行**，只精确 patch
    目标生成行。`成员:` 行的内容同步（拿 item 池当 ground truth 填充）由 Task 11 的
    reindex 负责（见上），本任务的 `add` 只把它建成空占位、`set-status`/`rename` 都
    不碰它。`rename` 额外要把 item 池（bug+todo 两池）里所有 `批次==old` 的项同步改成
    `new`——直接精确 patch 对应 dated 文件的批次列（表末列 `cells[7]`），不经由
    per-type 脚本的 `triage` 子命令，因为 `triage` 有"未分诊开放态→PROPOSED"的状态
    推进副作用，rename 只该改标签本身、不该顺带推状态。
  - `atomic_write`：与 buglist.py/todolist.py 同款原子写 helper，供落盘
    `issues/INDEX.md`/`issues/batches.md`/dated 文件（rename 同步）用。

**并发假设边界（D8）**：本脚本假定单机单进程串行调用，不加锁、不做文件锁/乐观锁/CAS。
umbrella 设计认定"并发/共享可变状态"属 TG-26，但 TG-26 要 Phase C 才落地；Phase B（本
脚本所在阶段）显式声明串行假设、不实现锁——真需要并发调用本脚本，留给后续 change 补锁。
调用方（skill / CI / sdflow-done sweep 步）需自行保证不并发调用本脚本，也不与
buglist.py/todolist.py 的写操作并发交叉。

用法见 `python issues.py --help`。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile


# ── 兄弟脚本定位 ─────────────────────────────────────────────────────────────
# 按本脚本自身的文件位置（不是 --root / 目标项目根）定位 buglist.py/todolist.py：
# setup.sh 把仓库里的每个顶层 skill 目录（sdflow-buglist / sdflow-todolist /
# sdflow-issues ...）各自绝对 symlink 到 ~/.claude/skills/、~/.codex/skills/ 下，
# 三者在安装后仍是同级 sibling 目录，因此“sdflow-issues/scripts 的上两级”这个
# 相对关系在源码仓库和安装后的位置都成立。--root 是完全独立的另一个概念：它是
# *目标项目*（存 openspec/issues/... 的仓库）的根，两者不可混淆、不可互相替代。
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
BUGLIST_SCRIPT = os.path.join(SKILLS_ROOT, "sdflow-buglist", "scripts", "buglist.py")
TODOLIST_SCRIPT = os.path.join(SKILLS_ROOT, "sdflow-todolist", "scripts", "todolist.py")


def atomic_write(path, text):
    """原子写：同目录临时文件写完整内容 → os.replace 原子换入。
    中途任何异常（含 os.replace 本身失败）都不会截断/损坏原文件——旧内容原样保留，
    临时文件在 finally 里清理，不留残留 .tmp。

    tempfile.mkstemp 固定以 0600 创建临时文件；os.replace 是纯 rename，目标会
    继承临时文件的权限。覆写已存在文件前必须把临时文件权限对齐回原文件的权限，
    否则已存在文件的权限会被静默从（例如）0644 收紧到 0600（对 group/other 变
    不可读）。原文件不存在（首次创建）时用 0o644 兜底。

    与 buglist.py / todolist.py 的同名函数逐字同款（Phase B 3 个脚本各自独立、
    不互相 import，故各自内联一份，见模块 docstring "子进程解耦"）。"""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            mode = os.stat(path).st_mode & 0o777
        except FileNotFoundError:
            mode = 0o644
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# ── 路径与文件 ───────────────────────────────────────────────────────────────

def repo_root(start="."):
    """探测 git 仓库根；非 git 仓库（或 git 命令失败）退化为 `os.path.abspath(start)`。

    与 buglist.py / todolist.py 的同名函数逐字同款（Phase B 3 个脚本各自独立、不互相
    import，故各自内联一份，见模块 docstring "子进程解耦"）。修复 Critical fix carry-over：
    本脚本此前 4 个 cmd_* 直接用裸 `args.root`（默认 "."）拼路径，不像 buglist.py/todolist.py
    那样探测 git 根——从非仓库根的子目录调用时会把 `openspec/issues/...` 错误地写到 cwd 而非
    git 根，三脚本定位从此不一致。所有 cmd_* 现在统一先 `root = repo_root(args.root)` 再拼
    路径；`read_pool` 调 buglist.py/todolist.py 子进程时也把这个已 resolve 的 root 传下去
    （`--root`），保证跨三脚本落到同一个目录。"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return os.path.abspath(start)


class CrossPoolIDConflict(RuntimeError):
    """D9 防护网触发：同一 ID 同时出现在 bug 池与 todo 池。"""


# ── 跨池 read ────────────────────────────────────────────────────────────────

def _scan_pool(script, root, pool):
    """子进程调 `{script} --root {root} scan --json`，给每项打 `pool` 标记后返回列表。

    推荐子进程而非 import（brief 明确要求）：buglist.py / todolist.py 是两个独立 skill
    各自的执行核心，子进程调用只依赖它们的 CLI 契约（`scan --json` 的输出结构），不依赖
    其内部函数签名——两边各自演进互不牵连，也不会把共享层的 issues.py 变成两个 per-type
    脚本的隐式反向依赖源。
    """
    proc = subprocess.run(
        [sys.executable, script, "--root", str(root), "scan", "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{os.path.basename(script)} scan --json 失败（exit={proc.returncode}）：{proc.stderr}"
        )
    data = json.loads(proc.stdout)
    # buglist.py 输出键是 "bugs"，todolist.py 输出键是 "items"（两脚本各自的命名，
    # 不统一——brief 明确提醒过这个坑，这里按 pool 分别取对应键）。
    raw_items = data.get("bugs" if pool == "bug" else "items") or []
    out = []
    for item in raw_items:
        merged = dict(item)
        merged["pool"] = pool
        out.append(merged)
    return out


def cross_pool_id_conflicts(items):
    """检测 `items`（含 `id`/`pool` 字段的 dict 列表）里同一 ID 是否跨池撞号
    （即同时出现在 pool == 'bug' 和 pool == 'todo' 的项里）。

    正常情况下 B(bug)/T(todo) 前缀互斥、不会天然撞号——D9 已把这条前缀互斥升为显式规范
    条款（recorder 约定段）。本函数是那条规范的**防护网**：万一有人为/历史数据用了非标准
    前缀（例如显式传自定义 `id` 绕开默认前缀），撞号也不能被静默 join 掉。

    纯函数、只读，不修改入参；返回按字典序排序的冲突 ID 列表，无冲突返回 `[]`。
    """
    bug_ids = {it["id"] for it in items if it.get("pool") == "bug"}
    todo_ids = {it["id"] for it in items if it.get("pool") == "todo"}
    return sorted(bug_ids & todo_ids)


def read_pool(root):
    """读跨两池（bug + todo）的 item 列表，join 结果里每项都带 `pool`（'bug' | 'todo'）
    标记，且至少含 `id`/`status`/`change`/`batch`/`pool` 五个字段（bug 池额外带
    priority/module/... 等 buglist 专属字段，todo 池额外带 type/module/... 等 todolist
    专属字段——字段是两边的并集，不做裁剪）。

    子进程调用 `buglist.py scan --json` + `todolist.py scan --json`（见 `_scan_pool`），
    两个结果 join 后立即跑 `cross_pool_id_conflicts` 做 D9 防护网校验：一旦检测到同一 ID
    跨池撞号，直接抛 `CrossPoolIDConflict`、**不静默 join**——调用方（reindex/batch，
    Task 9-11）不应该在数据已经撞号的情况下继续往下算 INDEX/batches。

    **并发假设边界（D8）**：本函数只读、不加锁。dated 文件本身靠 buglist.py/todolist.py
    的 atomic_write 保证不会读到半截内容，但两次 `scan --json` 子进程调用之间没有任何
    快照隔离——如果调用期间另一进程正并发 add/set-status，两池读到的"时刻"不保证一致。
    Phase B 显式假定单机单进程串行调用，不处理这类竞态（同模块 docstring D8）。
    """
    items = _scan_pool(BUGLIST_SCRIPT, root, "bug") + _scan_pool(TODOLIST_SCRIPT, root, "todo")
    conflicts = cross_pool_id_conflicts(items)
    if conflicts:
        raise CrossPoolIDConflict(
            "跨池 ID 冲突（D9 防护网触发，同一 ID 同时出现在 bug 池与 todo 池）："
            + ", ".join(conflicts)
        )
    return items


# ── reindex → issues/INDEX.md（Task 9） ─────────────────────────────────────
# 批次状态同步（`issues/batches.md` 的 `成员:`/`状态:` 生成行）见本文件靠后的
# 「reindex → batches.md 状态同步（Task 11）」一节；`issues/batches.md` 注册表
# 本身（`batch add`/`set-status`/`rename`）见 Task 10。本节只做「从 dated 文件
# 重建 INDEX.md」这一半。

INDEX_BANNER = "<!-- GENERATED by issues.py reindex — DO NOT EDIT -->"

# 各 recorder 的终态集（design.md §4.1 B-Q1）：进入即"这条债不再挂着"。
# per-recorder 判定，不写死字面 "DONE"（对 bug 池不成立）——两池状态词表不同。
TERMINAL_STATUSES = {
    "bug": {"FIXED", "WONTFIX"},
    "todo": {"DONE", "WONTDO"},
}


def _is_terminal(item):
    """item 是否已进入其所属 pool 的终态集（FIXED/WONTFIX 之于 bug，DONE/WONTDO 之于 todo）。"""
    return item.get("status") in TERMINAL_STATUSES.get(item.get("pool"), set())


def _render_item_table(items):
    """把一组 item 渲染成 markdown 表（ID | Pool | Status | 关联Change），按 id 升序。
    纯函数、确定性排序——供 generate_index_md 幂等（D7）用。"""
    lines = [
        "| ID | Pool | Status | 关联Change |",
        "|----|------|--------|------------|",
    ]
    for it in sorted(items, key=lambda x: x["id"]):
        change = it.get("change") or "-"
        lines.append(f"| {it['id']} | {it['pool']} | {it['status']} | {change} |")
    return "\n".join(lines)


def generate_index_md(items):
    """从 `read_pool` 返回的跨池 item 列表纯函数式生成 `issues/INDEX.md` 全文（含首行
    banner）。**禁读旧 INDEX**（D3）——只以 `items` 为唯一输入源，不看磁盘上已有内容。

    正文 = open item（非终态）× 批次的物化板：
      - 有批次的 open 项按批次分组（批次名升序），组内按 id 升序；
      - 批次为空的 open 项单列一组「未分组」，排在所有具名批次之后；
      - 已闭合（终态）项不逐条列出，只计数摘要（含 pool 拆分）。

    **幂等（D7）**：不写入时间戳/随机序等致每次不同的内容；分组键、组内排序全部确定性
    （批次名字典序、item id 字典序），故相同 `items` 两次调用逐字节输出相同。
    """
    open_items = [it for it in items if not _is_terminal(it)]
    closed_items = [it for it in items if _is_terminal(it)]

    groups = {}
    unbatched = []
    for it in open_items:
        batch = it.get("batch") or ""
        if batch:
            groups.setdefault(batch, []).append(it)
        else:
            unbatched.append(it)

    lines = [
        INDEX_BANNER,
        "",
        "# Issues Index",
        "",
        "> 本文件由 `issues.py reindex` 从 dated 文件"
        "（`issues/buglist/` + `issues/todolist/`）重建，请勿手改——"
        "手改内容会在下次 reindex 时被无条件覆盖。",
        "",
        "## Open 项（按批次）",
        "",
    ]

    if not groups and not unbatched:
        lines.append("（无 open 项）")
    else:
        for batch in sorted(groups):
            lines.append(f"### 批次：{batch}")
            lines.append("")
            lines.append(_render_item_table(groups[batch]))
            lines.append("")
        if unbatched:
            lines.append("### 未分组（批次为空）")
            lines.append("")
            lines.append(_render_item_table(unbatched))
            lines.append("")

    bug_closed = sum(1 for it in closed_items if it.get("pool") == "bug")
    todo_closed = sum(1 for it in closed_items if it.get("pool") == "todo")
    lines.append("## 已闭合（终态）摘要")
    lines.append("")
    lines.append(
        f"- 共 {len(closed_items)} 项已闭合（bug: {bug_closed}，todo: {todo_closed}）"
    )
    lines.append("")

    return "\n".join(lines)


def _die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def _reject_cell_unsafe(value, field):
    """总览管道表字段 fail-closed 守卫：含 ASCII | 或换行即拒（防列错位/行截断腐蚀盘面）。
    MUST 用于各命令入口的原始用户参数，勿用于 " | ".join(cells) 行拼接 sink。
    与 buglist.py / todolist.py 的同名函数逐字同款（三脚本各自独立、不互相 import，
    见模块 docstring "子进程解耦"）。挂在 `_retag_items_in_dated_files`（`batch rename`
    的跨池同步写路径，写 cells[7]）入口，守的是 `new_key` 原始参数。"""
    if value is None:
        return
    if "|" in str(value) or "\n" in str(value) or "\r" in str(value):
        _die(f"字段 {field} 含非法字符（| 或换行），会破坏总览表列对齐：{value!r}")


def _reject_batch_key_unsafe(key):
    """batches.md header slug 守卫（OV-2）：header 行是 `### {key} — {title}`
    （`_BATCH_HEADER_RE`，em dash U+2014 前后各一空格作分隔符）。`_reject_cell_unsafe`
    只挡 `|`/换行——不够，因为 key 本身若含 ` — ` 分隔符，会被 `_BATCH_HEADER_RE` 的
    非贪婪匹配切坏：例如 key="a — b" 写成 header 后，解析出的 key 变成 "a"、
    title 变成 "b"，原始完整 key 从此在 batches.md 里再也匹配不到——`_find_batch_entry_range`
    找不到它，等于这条注册从写入的那一刻起就是个读不回来的僵尸条目。首尾空白同理：
    `_BATCH_HEADER_RE` 用 `\\s*$` 吃掉尾部空白，写入时 key 有尾随空格、读回解析出的
    key 却没有，两次查找同一"逻辑 key"会得到不同结果。

    MUST 用于 `cmd_batch_add` 的 `key`、`cmd_batch_rename` 的 `new_key`（写 header 的
    唯一两处入口）。"""
    _reject_cell_unsafe(key, "batch key")
    if " — " in str(key) or str(key) != str(key).strip():
        _die(
            "batch key 非法（含 ' — ' em dash 分隔符，或首尾有空白），会破坏 "
            f"batches.md header（`### {{key}} — {{title}}`）解析：{key!r}"
        )


def cmd_reindex(args):
    """重建 `issues/INDEX.md` + 同步 `issues/batches.md` 状态（Task 9 + Task 11 两部分）。

    流程：`read_pool`（内含 D9 跨池 ID 冲突检测，冲突即抛 `CrossPoolIDConflict` 中止，
    不生成半截 INDEX、也不碰 batches.md）→ `generate_index_md` 纯函数重建全文 →
    `atomic_write` 原子落盘 INDEX.md → `sync_batches_md`（Task 11：拿同一份 `items`
    当 ground truth 同步 batches.md 每批的 `成员:`/`状态:` 生成行，含 D1 完成判据、
    Q3 不越权纠正、Q2 orphan 报警）。
    **禁读旧 INDEX.md**（D3）：全量确定性重建，不与磁盘上旧内容比较/合并。
    """
    root = repo_root(args.root)
    try:
        items = read_pool(root)
    except RuntimeError as e:
        _die(str(e))
        return  # pragma: no cover（_die 已 sys.exit(1)，此行只安抚静态分析）

    content = generate_index_md(items)
    index_path = os.path.join(root, "openspec", "issues", "INDEX.md")
    atomic_write(index_path, content)

    sync_batches_md(root, items)

    open_n = sum(1 for it in items if not _is_terminal(it))
    closed_n = len(items) - open_n
    print(f"reindex：已重建 {index_path}（open {open_n} 项，已闭合 {closed_n} 项）")


# ── issues/batches.md 注册表 + batch 命令（Task 10，Q2 rename / Q3 字段级 grammar） ──
#
# batches.md 每批一条，字段级 grammar（Q3 spec-review-amendment 裁决）：
#
#   ### {key} — {title}
#   状态: PLANNED            ← 生成行（reindex / `batch set-status` 维护）
#   成员: (生成) B1, T2      ← 生成行（`batch add` 建空占位；内容同步由 reindex 维护，见 Task 11）
#   优先级: P1               ← 人写行（reindex/batch 绝不覆写）
#   计划: 一句范围           ← 人写行（同上）
#
# 「生成行」= `状态:`/`成员:` 这两个固定前缀；「人写行」= 其它任意行（`优先级:`/`计划:`
# 只是本任务默认写入的两个人写字段，条目里额外追加的其它人写行同样原样保留——本节所有
# 解析/写入函数都按"整条 entry = 一段连续行"处理，只精确定位要 patch 的那一行，不touch
# 该 entry 范围内除目标行以外的任何字符。

BATCH_STATUSES = ["PLANNED", "IN_PROGRESS", "DONE"]
BATCH_PLACEHOLDER = "<待填>"  # 与 buglist.py `_has_rootcause` 的 <待分析> 同款占位符风格

# entry 头：`### {key} — {title}`（key/title 间用 em dash " — " 分隔，字面量，非正则元字符）
_BATCH_HEADER_RE = re.compile(r"^### (?P<key>.+?) — (?P<title>.+?)\s*$")
# 冒号兼容全角 `：`（Task 10 carry-over）：人手改 batches.md 很容易在中文输入法下敲成全角
# 冒号——若只认半角，解析会判定"整条目缺 状态: 行"，进而在别处插一条新的半角状态行，
# 把原来的全角行晾成永不会再被读到的僵尸行。放宽正则兼容两种冒号后，两者都能被找到、
# 定位、精确 patch（写回时统一改写成半角，起到顺手规范化的效果），不会产生僵尸行。
_BATCH_STATUS_LINE_RE = re.compile(r"^状态[:：]\s*(.*)$")
_BATCH_MEMBERS_LINE_RE = re.compile(r"^成员[:：]\s*(.*)$")
_BATCH_WARN_LINE_RE = re.compile(r"^⚠️ 不一致:.*$")

BATCHES_MD_HEADER = (
    "# Issues 批次注册表\n"
    "\n"
    "> 半手维护：`状态:`/`成员:` 由 `issues.py`（reindex / `batch set-status`）维护，"
    "其余字段（`优先级:`/`计划:` 等）人工填写——reindex/batch 只精确 patch 生成行，"
    "绝不覆写人写行（Q3）。\n"
    "\n"
)


def batches_md_path(root):
    return os.path.join(root, "openspec", "issues", "batches.md")


def _read_batches_lines(path):
    """batches.md 不存在时视为空注册表（`[]`），供 add 首次建文件时走同一套逻辑。

    规范化尾随换行（Critical fix）：`batches.md` 是半手维护文件，文件末尾缺尾随换行
    很常见——`readlines()` 会让最后一行不以 `\\n` 结尾。本文件下游多处对 `lines` 做
    `lines.insert(...)` 兜底插入（`_sync_one_entry` 的成员行/状态行/⚠️ 警告行缺失
    插入、`cmd_batch_set_status` 的状态行缺失插入），这些插入都假定“每一行都独立
    以 `\\n` 结尾”。若最后一行缺换行，插入的新行会在 `"".join()` 落盘时直接粘连到
    该行文本后面——不仅覆写/腐蚀人写行（违反 Q3 不覆写人写行），且粘连后的 ⚠️ 行不再
    以 `⚠️ 不一致:` 开头，`_BATCH_WARN_LINE_RE` 认不出它，导致下次 reindex 的“先剥旧
    ⚠️”识别不到、每跑一次 reindex 再插一条新 ⚠️——破幂等，数据腐蚀不自愈。

    所有下游函数（`_split_batches_entries`/`_find_batch_entry_range`/`sync_batches_md`/
    `cmd_batch_add`/`cmd_batch_set_status`/`cmd_batch_rename`）都经由本函数读取
    `batches.md`，故在此单点补齐是覆盖面最全、最不易遗漏未来新增插入点的实现：只有
    整个文件的最后一行可能缺换行（`readlines()` 对其余每一行都保证以 `\\n` 结尾），
    在此统一补上后，下游任何位置的 `lines.insert(...)` 都不会再粘连到前一行。
    """
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    if lines and not lines[-1].endswith("\n"):
        lines[-1] = lines[-1] + "\n"
    return lines


def _find_batch_entry_range(lines, key):
    """在 `lines`（batches.md 全文按行切片）里定位 `key` 对应 entry 的行范围。

    返回 `(header_idx, end_idx)`：entry 占 `lines[header_idx:end_idx]`（含 header 行，
    不含下一个 entry 的 header 行/EOF）。`key` 未找到返回 `None`。

    纯定位、不修改 `lines`——所有写操作都在调用方按需精确替换/插入某一行，其余行
    （含同一 entry 内的人写行、以及其它 entry 的全部内容）原样保留在 `lines` 里。
    """
    header_idx = None
    for i, line in enumerate(lines):
        m = _BATCH_HEADER_RE.match(line.rstrip("\n"))
        if m and m.group("key") == key:
            header_idx = i
            break
    if header_idx is None:
        return None
    end_idx = len(lines)
    for j in range(header_idx + 1, len(lines)):
        if _BATCH_HEADER_RE.match(lines[j].rstrip("\n")):
            end_idx = j
            break
    return header_idx, end_idx


def _batch_entry_exists(lines, key):
    return _find_batch_entry_range(lines, key) is not None


# ── reindex → batches.md 状态同步（Task 11） ─────────────────────────────────
# reindex 除了重建 issues/INDEX.md（Task 9），还拿 item 池当 ground truth 同步
# batches.md 每批的 `成员:`/`状态:` 两条生成行——这一节实现那一半（`sync_batches_md`，
# 被 `cmd_reindex` 调用）。

# 批次完成判据（D1）：成员数 ≥1 且全部进入各自 pool 的终态集（TERMINAL_STATUSES，
# 含 WONT* 是合法闭合）。0 成员显式被 `len(members) >= 1` 排除——对空集，"全部成员
# 都终态" 是全称量词的 vacuous truth（永真），若不显式排除会把刚建、还没人挂上去的
# 空批次误判成"已完成"，这正是 D1 要焊死的假 DONE。


def _split_batches_entries(lines):
    """把 batches.md 全文行切成 `(preamble_lines, entries)`；`entries` 是
    `[(key, entry_lines), ...]`（保持文件原有顺序），每个 `entry_lines` 含该条目的
    header 行 + 随后所有行（含尾部空行，直到下一个 entry header 或 EOF）。

    纯定位/切片，不修改 `lines`——与 `_find_batch_entry_range`（单 key 查找）同款
    定位逻辑，这里一次性切出全部条目，供 `sync_batches_md` 逐条 patch 用。
    """
    header_positions = [
        i for i, line in enumerate(lines) if _BATCH_HEADER_RE.match(line.rstrip("\n"))
    ]
    preamble = lines[: header_positions[0]] if header_positions else list(lines)
    entries = []
    for idx, hpos in enumerate(header_positions):
        end = header_positions[idx + 1] if idx + 1 < len(header_positions) else len(lines)
        key = _BATCH_HEADER_RE.match(lines[hpos].rstrip("\n")).group("key")
        entries.append((key, lines[hpos:end]))
    return preamble, entries


def _sync_one_entry(entry_lines, member_ids, is_complete):
    """纯函数：给定一个 batches.md 条目的原始行列表 + 该批当前成员 id 列表（按批次 tag
    从 item 池聚合而来）+ D1 完成判据结果，返回同步后的新行列表。

    只碰 `状态:`/`成员:` 两条生成行 + `⚠️ 不一致` 警告行，条目内其它任何人写行
    （`优先级:`/`计划:`/... 及 header 本身）原样保留、相对顺序不变（Q3 grammar）。

    - 先无条件剥掉旧的 `⚠️ 不一致` 行（若有）——下面按当前判据重新决定是否追加，
      两次调用同样输入必产生同样输出，不会累积重复警告（幂等）。
    - `成员:` 行整行重写为 `成员: (生成) id1, id2 ...`（id 升序；0 成员写
      `成员: (生成)` 不带尾巴）；缺失该行时插在 `状态:` 行之后（Task 10 的 `add`
      保证必有此行，这里只是防御式兜底，不代表预期路径）。
    - `状态:` 行：`is_complete` 为真 → 强制改写成 `DONE`——这是 reindex 唯一会写的
      值（PLANNED→IN_PROGRESS 是 `batch set-status` 的人工权限，reindex 只推
      →DONE，不碰其它值）。`is_complete` 为假时**绝不改这个值**，哪怕它当前就是
      `DONE`——那种"人标 DONE 但成员未全终态"的场景只触发下面的 ⚠️ 追加，不越权
      纠正（Q3）。
    """
    lines = [l for l in entry_lines if not _BATCH_WARN_LINE_RE.match(l.rstrip("\n"))]
    member_ids_sorted = sorted(member_ids)

    status_idx, status_val = None, None
    for i, l in enumerate(lines):
        m = _BATCH_STATUS_LINE_RE.match(l.rstrip("\n"))
        if m:
            status_idx, status_val = i, m.group(1).strip()
            break

    members_idx = None
    for i, l in enumerate(lines):
        if _BATCH_MEMBERS_LINE_RE.match(l.rstrip("\n")):
            members_idx = i
            break

    members_line = "成员: (生成)" + (
        (" " + ", ".join(member_ids_sorted)) if member_ids_sorted else ""
    ) + "\n"
    if members_idx is not None:
        lines[members_idx] = members_line
    else:
        lines.insert((status_idx + 1) if status_idx is not None else 1, members_line)

    need_warning = False
    if is_complete:
        if status_idx is not None:
            lines[status_idx] = "状态: DONE\n"
        else:
            lines.insert(1, "状态: DONE\n")
    elif status_val == "DONE":
        need_warning = True

    if need_warning:
        detail = ", ".join(member_ids_sorted) if member_ids_sorted else "0 名成员"
        warn_line = (
            f"⚠️ 不一致: 状态标记为 DONE，但成员未全部进入终态（当前成员：{detail}）——"
            "reindex 不会自动纠正 状态: 的值（不越权），请人工核实后用 `batch "
            "set-status` 改回或补完成员状态\n"
        )
        end = len(lines)
        while end > 0 and lines[end - 1].strip() == "":
            end -= 1
        lines.insert(end, warn_line)

    return lines


def sync_batches_md(root, items):
    """reindex 第二部分（Task 11）：拿 `items`（`read_pool` 结果）当 ground truth，
    同步 `issues/batches.md` 每批的 `成员:`/`状态:` 两条生成行。

    - 按批次 tag（`items` 里的 `batch` 字段，忽略空批次）聚合成员，重写每个已注册
      条目的 `成员:` 行。
    - D1 完成判据：成员数 ≥1 且全部进入各自 pool 终态集 → `状态:` 同步为 `DONE`；
      0 成员的批次显式排除在判据外（防 vacuous-truth 假 DONE），`状态:` 原样保留
      （reindex 不写 PLANNED/IN_PROGRESS，那是 `batch set-status` 的人工权限）。
    - Q3 不越权纠正：条目当前 `状态: DONE` 但成员未全终态 → 不改 `状态:` 值，只在
      条目尾部追加 `⚠️ 不一致` 警告（幂等：下次 reindex 会先移除旧警告再按当前
      判据重新决定是否追加，不累积）。
    - Q2/D5 orphan：item 的批次 tag 在 batches.md 里没有对应已注册 key → 不新建
      该 key 的 ghost 条目，只在 stderr 显式报警（`batches.md` 完全不存在时，
      所有带批次 tag 的 item 都会被判定 orphan）。

    该函数只在 batches.md 已有至少一条注册条目时才会写回文件（没有条目可 patch
    时不创建/改动 batches.md 本身——那是 `batch add` 的职责）；orphan 检测不受
    此限制，始终执行。
    """
    path = batches_md_path(root)
    lines = _read_batches_lines(path)
    preamble, entries = _split_batches_entries(lines) if lines else ([], [])
    known_keys = {key for key, _ in entries}

    by_batch = {}
    for it in items:
        batch = it.get("batch") or ""
        if batch:
            by_batch.setdefault(batch, []).append(it)

    for key in sorted(by_batch):
        if key not in known_keys:
            member_ids = sorted(it["id"] for it in by_batch[key])
            print(
                f"reindex: 警告（orphan，Q2）：批次 '{key}' 被 {len(member_ids)} 个 "
                f"item 引用（{', '.join(member_ids)}），但 issues/batches.md 未注册"
                "该 key——不会新建 ghost 条目，请用 `batch add` 补注册该 key，或修正"
                "对应 item 的批次 tag。",
                file=sys.stderr,
            )

    if not entries:
        return

    new_lines = list(preamble)
    for key, entry_lines in entries:
        members = by_batch.get(key, [])
        member_ids = [it["id"] for it in members]
        is_complete = len(members) >= 1 and all(_is_terminal(it) for it in members)
        new_lines.extend(_sync_one_entry(entry_lines, member_ids, is_complete))

    atomic_write(path, "".join(new_lines))


def cmd_batch_add(args):
    """`batch add {key}`：新建 PLANNED 条目，成员空；人写字段按参数写，缺省留占位
    （`BATCH_PLACEHOLDER`，不是空字符串——占位和"确实填了空值"要能区分）。

    已存在同 key → 报错（非 no-op）：add 是"新建"语义，撞号多半是误操作，报错比静默
    跳过更安全——静默 no-op 会让调用方以为参数（title/优先级/计划）已生效，实际全被
    忽略，是更隐蔽的坑。
    """
    root = repo_root(args.root)
    _reject_batch_key_unsafe(args.key)
    _reject_cell_unsafe(args.title, "title")
    path = batches_md_path(root)
    lines = _read_batches_lines(path)
    if _batch_entry_exists(lines, args.key):
        _die(f"批次 key 已存在：{args.key}（add 不覆写已有条目；改状态用 set-status，改名用 rename）")

    title = args.title or args.key
    priority = getattr(args, "优先级") or BATCH_PLACEHOLDER
    plan = getattr(args, "计划") or BATCH_PLACEHOLDER

    entry_lines = [
        f"### {args.key} — {title}\n",
        "状态: PLANNED\n",
        "成员: (生成)\n",
        f"优先级: {priority}\n",
        f"计划: {plan}\n",
    ]

    if not lines:
        lines = [BATCHES_MD_HEADER]
    elif lines[-1].strip() != "":
        lines.append("\n")
    lines.extend(entry_lines)
    lines.append("\n")

    atomic_write(path, "".join(lines))
    print(json.dumps({"key": args.key, "title": title, "status": "PLANNED"}, ensure_ascii=False))


def cmd_batch_set_status(args):
    """`batch set-status {key} {S}`：只改该条目的 `状态:` 生成行，绝不动人写行（Q3）
    或 `成员:` 生成行（那是 reindex/Task 11 的职责，本命令不碰）。
    """
    root = repo_root(args.root)
    if args.status not in BATCH_STATUSES:
        _die(f"批次状态非法：{args.status}（应为 {'/'.join(BATCH_STATUSES)}）")

    path = batches_md_path(root)
    lines = _read_batches_lines(path)
    rng = _find_batch_entry_range(lines, args.key)
    if rng is None:
        _die(f"未找到批次 key：{args.key}")
    header_idx, end_idx = rng

    status_idx = None
    for i in range(header_idx + 1, end_idx):
        if _BATCH_STATUS_LINE_RE.match(lines[i].rstrip("\n")):
            status_idx = i
            break

    old_status = None
    if status_idx is not None:
        old_status = _BATCH_STATUS_LINE_RE.match(lines[status_idx].rstrip("\n")).group(1).strip()
        lines[status_idx] = f"状态: {args.status}\n"
    else:
        # 防御式兜底：条目缺 `状态:` 生成行（理论上 add 必写，这里只防手造/损坏的 batches.md）。
        # 只在 header 后插一行，不碰任何既有人写行的位置。
        lines.insert(header_idx + 1, f"状态: {args.status}\n")

    atomic_write(path, "".join(lines))
    print(json.dumps(
        {"key": args.key, "old_status": old_status, "new_status": args.status}, ensure_ascii=False
    ))


def _retag_items_in_dated_files(root, items, old_key, new_key):
    """rename 的跨池同步半：把 `items`（`read_pool` 结果）里所有 `批次==old_key` 的项，
    在其各自 dated 文件里的批次列（表末列 `cells[7]`）精确改成 `new_key`。

    刻意不走 per-type 脚本的 `triage` 子命令：`triage` 除了写批次列，还会把「未分诊
    开放态」item 的状态顺带推进到 PROPOSED（见 buglist.py/todolist.py `cmd_triage`）——
    这是 rename 意料外的副作用（rename 只该改标签本身）。所以这里直接对 dated 文件的
    批次列做精确 patch（design §五允许的"直接改 dated 文件的批次列"路径），只改这一列，
    该行其它列 + 文件其它内容原样保留。

    每个受影响文件只读一次、原地改完全部命中行、写一次（`atomic_write`）——不会对同一
    文件重复打开写入。返回 `[{"pool", "id", "file"}, ...]`（改动了哪些项，供调用方汇报/测试）。
    """
    _reject_cell_unsafe(new_key, "new_key")
    targets = [it for it in items if it.get("batch") == old_key]
    by_file = {}
    for it in targets:
        rel_file = it.get("file")
        if not rel_file:
            continue  # 理论上 scan --json 每项都带 file；防御式跳过缺失的
        by_file.setdefault(rel_file, []).append(it)

    changed = []
    for rel_file, its in by_file.items():
        full_path = os.path.join(root, rel_file)
        with open(full_path, encoding="utf-8") as f:
            file_lines = f.readlines()
        wanted = {it["id"]: it for it in its}
        for i, line in enumerate(file_lines):
            m = re.match(r"\|\s*([A-Z]\d+)\s*\|", line)
            if not m or m.group(1) not in wanted:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            while len(cells) < 8:  # 旧格式（无批次列）行防御式补齐，不越界写 cells[7]
                cells.append("")
            cells[7] = new_key
            file_lines[i] = "| " + " | ".join(cells) + " |\n"
            changed.append({"pool": wanted[m.group(1)]["pool"], "id": m.group(1), "file": rel_file})
        atomic_write(full_path, "".join(file_lines))
    return changed


def cmd_batch_rename(args):
    """`batch rename {old} {new}`：改条目 key（`old`→`new`，标题文本不变）+ 同步 item 池
    （bug+todo 两池）里所有 `批次==old` 的 tag 一并改成 `new`（Q2：人真开 cleanup change
    用不同名时用这个命令，不做跨 change 主题聚类合并）。

    执行顺序（刻意）：先校验 batches.md 里 old 存在、new 不与既有条目撞号（不做静默合并）
    → 再 `read_pool`（这一步可能因跨池 ID 冲突/子进程失败抛错）→ 只有 `read_pool` 成功后
    才开始真正写盘：先改 dated 文件（item 池），最后才改 `batches.md` 的 key。这样任何一步
    失败都不会把 `batches.md` 改成指向一个内容对不上的新 key；`read_pool` 失败时更是连一个
    字节都不落盘。多文件写入本身无跨文件事务（D6 已知边界，靠"重跑收敛"），但至少不会因为
    校验类失败留下半吊子状态。
    """
    root = repo_root(args.root)
    old_key, new_key = args.old, args.new
    _reject_batch_key_unsafe(new_key)

    path = batches_md_path(root)
    lines = _read_batches_lines(path)
    rng = _find_batch_entry_range(lines, old_key)
    if rng is None:
        _die(f"未找到批次 key：{old_key}")
    if old_key != new_key and _batch_entry_exists(lines, new_key):
        _die(f"批次 key 已存在，rename 不做合并：{new_key}")

    try:
        items = read_pool(root)
    except RuntimeError as e:
        _die(str(e))
        return  # pragma: no cover（_die 已 sys.exit(1)，此行只安抚静态分析）

    changed = _retag_items_in_dated_files(root, items, old_key, new_key)

    header_idx, _end_idx = rng
    header_line = lines[header_idx].rstrip("\n")
    title = _BATCH_HEADER_RE.match(header_line).group("title")
    lines[header_idx] = f"### {new_key} — {title}\n"
    atomic_write(path, "".join(lines))

    print(json.dumps(
        {"old_key": old_key, "new_key": new_key, "items_changed": len(changed)}, ensure_ascii=False
    ))


def main():
    p = argparse.ArgumentParser(
        description="共享 issues 层：跨 bug+todo 的 reindex / batch"
    )
    p.add_argument("--root", default=".", help="目标项目根（存 openspec/issues/... 的仓库）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("reindex", help="重建 issues/INDEX.md（open×批次板）+ 同步 issues/batches.md 状态")
    s.set_defaults(func=cmd_reindex)

    batch_p = sub.add_parser("batch", help="issues/batches.md 注册表操作（add/set-status/rename）")
    batch_sub = batch_p.add_subparsers(dest="batch_action", required=True)

    sa = batch_sub.add_parser("add", help="新建批次条目（状态=PLANNED，成员空，人写字段按参数写/缺省留占位）")
    sa.add_argument("key")
    sa.add_argument("--title", help="批次标题（缺省=key）")
    sa.add_argument("--优先级", dest="优先级", help="人写字段，缺省留占位")
    sa.add_argument("--计划", dest="计划", help="人写字段（一句范围），缺省留占位")
    sa.set_defaults(func=cmd_batch_add)

    ss = batch_sub.add_parser("set-status", help="改批次状态（只精确 patch `状态:` 生成行，不动人写行）")
    ss.add_argument("key")
    ss.add_argument("status", choices=BATCH_STATUSES)
    ss.set_defaults(func=cmd_batch_set_status)

    sr = batch_sub.add_parser("rename", help="改批次 key + 同步 item 池（bug+todo 两池）批次 tag")
    sr.add_argument("old")
    sr.add_argument("new")
    sr.set_defaults(func=cmd_batch_rename)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
