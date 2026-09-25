#!/usr/bin/env python3
"""adr.py — `openspec/adr/` 下 ADR 的唯一确定性入口。

格式真相源见同 skill 的 `references/format.md`；本脚本只做机械检查与写入，
不判断 ADR 内容是否与代码一致（那是 sync / audit 的模型判断，见 SKILL.md）。

子命令：`next-id` / `new`（含 `--supersedes` / `--partial`）/ `lint` / `refs`。

退出码：0 成功；1 lint 有红项；2 用法错误 / IO 错误 / 文件不可读（fail-closed）。
"""

import argparse
import contextlib
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass


ADR_REL_DIR = "openspec/adr"
LOCK_REL = "openspec/adr/.lock"
LOCK_RETRIES = 20
LOCK_INTERVAL = 0.1
LOCK_STALE_SEC = 120

FILENAME_PREFIX_RE = re.compile(r"^\d{4}-")
FULL_FILENAME_RE = re.compile(r"^\d{4}-[a-z0-9][a-z0-9-]*\.md$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

H2_WHITELIST = ("Decision", "Considered Options", "Consequences", "附录：修订历史")

# Status 取值枚举（format.md）
_RANGE_ITEM = r"\d{4}（[^）]+）"
STATUS_ACCEPTED_RE = re.compile(r"^Accepted$")
STATUS_SUPERSEDED_SINGLE_RE = re.compile(r"^Superseded by (\d{4})$")
STATUS_SUPERSEDED_SPEC_RE = re.compile(r"^Superseded by `([^`]+)` spec$")
STATUS_PARTIALLY_RE = re.compile(r"^Partially superseded by ((?:%s、)*%s)$" % (_RANGE_ITEM, _RANGE_ITEM))
# 多目标 Superseded：Partially 件其余部分整体被取代时，末项新编号的范围可省
# （format.md 转换矩阵「<既有列表>、<新>（TEXT 可省）」）——new 不带 --partial 时正是产出这种形态。
STATUS_SUPERSEDED_MULTI_RE = re.compile(
    r"^Superseded by ((?:%s、)*%s|(?:%s、)+\d{4})$" % (_RANGE_ITEM, _RANGE_ITEM, _RANGE_ITEM))
# 取代者编号：紧跟在 `by ` 或上一项的 `）、` 之后的四位数字（范围文本里的数字不会被误取）
SUPERSEDER_NUMBER_RE = re.compile(r"(?:by |）、)(\d{4})")
STATUS_DEPRECATED_RE = re.compile(r"^Deprecated$")
STATUS_LINE_RE = re.compile(r"^\*\*Status: (.+?)\*\* · (.*)$")
RANGE_ITEM_RE = re.compile(r"(\d{4})（([^）]*)）")

FENCE_RE = re.compile(r"^(```+|~~~+)")

# Status 取值分类表（有序；首个匹配即为该值的 kind）。供 `_classify_target_status`
# 与 lint 的合法性判断 / L5 取代目标抽取 / is_frozen 判定四处共用，避免六路判别重复枚举。
STATUS_KIND_ORDER = (
    ("accepted", STATUS_ACCEPTED_RE),
    ("superseded_single", STATUS_SUPERSEDED_SINGLE_RE),
    ("superseded_spec", STATUS_SUPERSEDED_SPEC_RE),
    ("partially", STATUS_PARTIALLY_RE),
    ("superseded_multi", STATUS_SUPERSEDED_MULTI_RE),
    ("deprecated", STATUS_DEPRECATED_RE),
)
TERMINAL_KINDS = frozenset({"superseded_single", "superseded_spec", "superseded_multi", "deprecated"})


def _match_status_kind(status_value):
    """按 STATUS_KIND_ORDER 依次匹配，返回 (kind, match)；不在枚举内则 (None, None)。"""
    for kind, rx in STATUS_KIND_ORDER:
        m = rx.match(status_value)
        if m:
            return kind, m
    return None, None


def _find_h1_idx(lines):
    """返回 lines 中第一个非空行的下标（0-based，即 H1 行，无论是否真是合法 H1）；
    全空则 None。供 `_find_status_line` / `_rewrite_target_status` / `_lint_one` 共用。"""
    for i, line in enumerate(lines):
        if line.strip():
            return i
    return None


def _die(code, msg):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _read_or_die(path):
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        _die(2, f"adr: 无法读取 {path}: {e}")


def atomic_write(path, text):
    d = path.parent
    try:
        fd, tmpname = tempfile.mkstemp(dir=str(d), prefix=path.name + ".", suffix=".tmp-adr")
    except OSError as e:
        raise OSError(f"无法在 {d} 建临时文件: {e}") from e
    try:
        # newline=""：不做换行转换，text 里的 \r\n / \n 原样落盘
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmpname, str(path))
    except OSError:
        with contextlib.suppress(OSError):
            os.unlink(tmpname)
        raise


# ══════════════════════════════════════════════════════════════════════════
# 仓级目录锁（形态照抄 sad_scaffold._repo_lock，不 import 该模块）
# ══════════════════════════════════════════════════════════════════════════

def _acquire_lock(root):
    import time
    lockp = root / LOCK_REL
    for _ in range(LOCK_RETRIES):
        try:
            fd = os.open(str(lockp), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(fd)
            return lockp
        except FileExistsError:
            try:
                age = time.time() - lockp.stat().st_mtime
            except OSError:
                age = 0
            if age > LOCK_STALE_SEC:
                _die(2, f"adr: 另一 new 操作进行中（锁 mtime 超 {LOCK_STALE_SEC}s，疑似残留）；"
                        f"若确认无并发进程，删除 {lockp} 后重试")
            time.sleep(LOCK_INTERVAL)
        except OSError as e:
            _die(2, f"adr: 无法创建锁文件 {lockp}: {e}")
    _die(2, f"adr: 另一 new 操作进行中；若确认无并发进程，删除 {lockp} 后重试")


def _release_lock(lockp):
    if lockp is not None:
        with contextlib.suppress(OSError):
            lockp.unlink()


@contextlib.contextmanager
def _repo_lock(root):
    lockp = _acquire_lock(root)
    try:
        yield
    finally:
        _release_lock(lockp)


# ══════════════════════════════════════════════════════════════════════════
# 目录扫描（next-id / new 共用）
# ══════════════════════════════════════════════════════════════════════════

def _scan_numbers_or_die(adr_dir):
    """扫描 adr_dir 下全部 .md 文件；文件名不匹配 `^\\d{4}-` 则 fail-closed 退出 2。
    返回已用编号的整数列表。"""
    numbers = []
    for p in sorted(adr_dir.glob("*.md")):
        if not FILENAME_PREFIX_RE.match(p.name):
            _die(2, f"adr: {ADR_REL_DIR}/{p.name} 不匹配 NNNN-<slug>.md；"
                    f"该目录只允许 ADR 文件；改名或移出后重跑")
        numbers.append(int(p.name[:4]))
    return numbers


def _resolve_adr_dir(root):
    adr_dir = root / ADR_REL_DIR
    if not adr_dir.is_dir():
        _die(2, f"adr: {ADR_REL_DIR} 不存在或不是目录")
    return adr_dir


# ══════════════════════════════════════════════════════════════════════════
# next-id
# ══════════════════════════════════════════════════════════════════════════

def cmd_next_id(args):
    root = Path(args.root).resolve()
    adr_dir = _resolve_adr_dir(root)
    numbers = _scan_numbers_or_die(adr_dir)
    nxt = (max(numbers) + 1) if numbers else 1
    print(f"{nxt:04d}")
    return 0


# ══════════════════════════════════════════════════════════════════════════
# new
# ══════════════════════════════════════════════════════════════════════════

def _classify_target_status(status_value):
    """返回 ('accepted' | 'partially' | 'terminal' | 'no-status-line' | 'invalid', existing_items)。
    existing_items 仅 'partially' 时有意义：[(nnnn, text), ...]。"""
    if status_value is None:
        return "no-status-line", []
    kind, _m = _match_status_kind(status_value)
    if kind == "accepted":
        return "accepted", []
    if kind == "partially":
        return "partially", _parse_range_items(status_value)
    if kind in TERMINAL_KINDS:
        return "terminal", []
    # 有 Status 行但取值不在枚举内：可能是写坏的终态，当 Accepted 处理会覆盖掉原取代关系，
    # 故拒绝转换（转换矩阵只授权 Accepted / 无 Status 行 / Partially 三类）
    return "invalid", []


def _parse_range_items(status_value):
    """从 `Partially superseded by 0044（决策 1、2）、0050（决策 3）` 中解析
    [('0044', '决策 1、2'), ('0050', '决策 3')]。"""
    return [(m.group(1), m.group(2)) for m in RANGE_ITEM_RE.finditer(status_value)]


def _find_status_line(text):
    """返回 (line_index, status_value, trailing_text) 或 (None, None, None)。
    line_index 是 H1 后第一个非空行的行号（0-based），无论是否匹配 Status 格式。"""
    lines = text.splitlines()
    h1_idx = _find_h1_idx(lines)
    if h1_idx is None:
        return None, None, None
    for i in range(h1_idx + 1, len(lines)):
        if lines[i].strip():
            m = STATUS_LINE_RE.match(lines[i])
            if m:
                return i, m.group(1), m.group(2)
            return i, None, None  # 有非空行但不是 Status 格式（旧格式，视为无 Status 行）
    return None, None, None


def _compose_new_status_line(kind, existing_items, nnnn, partial_text):
    """根据目标当前分类与转换矩阵，返回新的 Status 值（不含 `**Status: ` 包装）。"""
    if kind in ("accepted", "no-status-line"):
        if partial_text is None:
            value = f"Superseded by {nnnn}"
        else:
            value = f"Partially superseded by {nnnn}（{partial_text}）"
    elif kind == "partially":
        rendered = "、".join(f"{n}（{t}）" for n, t in existing_items)
        if partial_text is None:
            value = f"Superseded by {rendered}、{nnnn}"
        else:
            value = f"Partially superseded by {rendered}、{nnnn}（{partial_text}）"
    else:
        raise AssertionError(f"不可达：终态 {kind} 不应进入此函数")
    return value


def _supersedes_error_text(nnnn, status_display):
    return (f"adr: --supersedes {nnnn} 不存在（或 Status 为「{status_display}」，"
            f"终态不可再取代）；未创建新文件；核对编号，或对 Partially 件改用 --partial")


def _undo_new_file_and_die(new_path, reason):
    """补偿：删除本次创建的新 ADR 后以退出码 2 失败。删除本身失败时如实报告残留，
    不声称目录已恢复。"""
    try:
        new_path.unlink()
    except FileNotFoundError:
        pass
    except OSError as e:
        _die(2, f"adr: {reason}；删除本次创建的 {new_path} 也失败（{e}），该文件残留，"
                f"手工删除后重跑")
    _die(2, f"adr: {reason}；已删除本次创建的 {new_path}，目录回到调用前；修复权限或编码后重跑")


def _read_exact_or_die(path):
    """按原始换行读取（不做 CRLF→LF 转换），供改写旧 ADR 时保持 Status 行以外的字节不变。"""
    try:
        with path.open(encoding="utf-8", newline="") as f:
            return f.read()
    except (UnicodeDecodeError, OSError) as e:
        _die(2, f"adr: 无法读取 {path}: {e}")


def _validate_partial_or_die(partial_text, supersedes):
    if partial_text is None:
        return None
    if supersedes is None:
        _die(2, "adr: --partial 须与 --supersedes 同时使用；未创建新文件")
    text = partial_text.strip()
    # 空范围、换行、全角右括号都会写出 lint 不认的 Status 行
    if not text or "\n" in text or "\r" in text or "）" in text:
        _die(2, f"adr: --partial 须为非空单行、不含「）」的决策范围，得到 {partial_text!r}；未创建新文件")
    return text


def _plan_supersede(adr_dir, supersedes, nnnn, partial_text):
    """定位取代目标、按转换矩阵校验，返回 (目标路径, 改写后的目标全文)。只读不写；
    任何不合法情况以退出码 2 失败，此时尚未创建新文件。"""
    candidates = sorted(p for p in adr_dir.glob("*.md") if p.name.startswith(f"{supersedes}-"))
    if not candidates:
        _die(2, _supersedes_error_text(supersedes, "文件不存在"))
    if len(candidates) > 1:
        _die(2, f"adr: --supersedes {supersedes} 对应多个文件（{', '.join(p.name for p in candidates)}）；"
                f"未创建新文件；先修正重复编号")
    target_path = candidates[0]
    target_text = _read_exact_or_die(target_path)
    if _find_h1_idx(target_text.splitlines()) is None:
        _die(2, f"adr: --supersedes {supersedes} 的文件 {target_path} 为空；未创建新文件")
    idx, status_value, _trailing = _find_status_line(target_text)
    kind, existing_items = _classify_target_status(status_value)
    if kind == "terminal":
        _die(2, _supersedes_error_text(supersedes, status_value))
    if kind == "invalid":
        _die(2, f"adr: --supersedes {supersedes} 的 Status 取值 {status_value!r} 不在枚举内；"
                f"未创建新文件；先修正该 ADR 的 Status 行（adr.py lint 可定位）")
    new_status_value = _compose_new_status_line(kind, existing_items, nnnn, partial_text)
    new_target_text = _rewrite_target_status(target_text, idx, new_status_value, kind, nnnn, partial_text)
    return target_path, new_target_text


def cmd_new(args):
    root = Path(args.root).resolve()
    adr_dir = _resolve_adr_dir(root)

    if not SLUG_RE.match(args.slug):
        _die(2, f"adr: --slug 须匹配 [a-z0-9][a-z0-9-]*（ascii kebab），得到 {args.slug!r}")

    supersedes = args.supersedes
    if supersedes is not None and not re.fullmatch(r"\d{4}", supersedes):
        _die(2, f"adr: --supersedes 须为四位编号（如 0044），得到 {supersedes!r}；未创建新文件")
    partial_text = _validate_partial_or_die(args.partial, supersedes)

    with _repo_lock(root):
        numbers = _scan_numbers_or_die(adr_dir)

        nxt = (max(numbers) + 1) if numbers else 1
        nnnn = f"{nxt:04d}"
        new_path = adr_dir / f"{nnnn}-{args.slug}.md"

        # 全部校验与旧文件新内容的计算都在创建新文件之前完成：创建之后只剩原子写旧文件一步可能失败
        target_path, new_target_text = None, None
        if supersedes is not None:
            target_path, new_target_text = _plan_supersede(adr_dir, supersedes, nnnn, partial_text)

        existing_same_number = [p for p in adr_dir.glob(f"{nnnn}-*.md")]
        if existing_same_number:
            _die(2, f"adr: 编号 {nnnn} 已被 {existing_same_number[0]} 占用；"
                    f"扫号与创建之间有其他写入；重跑 new 即重新扫号")

        skeleton = _render_skeleton(args.title, args.source)
        try:
            fd = os.open(str(new_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except OSError:
            _die(2, f"adr: 编号 {nnnn} 已被 {new_path} 占用；"
                    f"扫号与创建之间有其他写入；重跑 new 即重新扫号")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(skeleton)
        except OSError as e:
            _undo_new_file_and_die(new_path, f"写入 {new_path} 失败：{e}")

        if supersedes is not None:
            try:
                atomic_write(target_path, new_target_text)
            except OSError as e:
                _undo_new_file_and_die(new_path, f"改写 {target_path} 失败：{e}")

        print(str(new_path))
        if supersedes is not None:
            print(str(target_path))
    return 0


def _render_skeleton(title, source):
    return (
        f"# {title}\n\n"
        f"**Status: Accepted** · {source}\n\n"
        f"TODO(adr)：背景段。\n\n"
        f"## Decision\n\n"
        f"TODO(adr)\n\n"
        f"## Considered Options\n\n"
        f"TODO(adr)\n\n"
        f"## Consequences\n\n"
        f"TODO(adr)\n"
    )


def _rewrite_target_status(text, status_line_idx, new_status_value, target_kind, nnnn, partial_text):
    """只替换 Status 行（或在 H1 下插入），其余行连同各自的换行符原样保留。
    splitlines(keepends=True) 与 _find_status_line 的 splitlines() 行下标一一对应。"""
    lines = text.splitlines(keepends=True)
    keep_trailing = target_kind in ("accepted", "partially")
    if keep_trailing and status_line_idx is not None:
        line = lines[status_line_idx]
        body = line.rstrip("\r\n")
        m = STATUS_LINE_RE.match(body)
        trailing = m.group(2) if m else ""
        lines[status_line_idx] = f"**Status: {new_status_value}** · {trailing}{line[len(body):]}"
    else:
        # no-status-line：插入到 H1 下一行，换行符沿用 H1 行的
        today = datetime.date.today().isoformat()
        trailing = f"由 {nnnn} 取代（{today}；迁移前无 Status 行）"
        h1_idx = _find_h1_idx(lines)
        h1_body = lines[h1_idx].rstrip("\r\n")
        eol = lines[h1_idx][len(h1_body):] or "\n"
        lines[h1_idx] = h1_body + eol
        new_line = f"**Status: {new_status_value}** · {trailing}{eol}"
        lines[h1_idx + 1:h1_idx + 1] = [eol, new_line]
    return "".join(lines)


# ══════════════════════════════════════════════════════════════════════════
# lint
# ══════════════════════════════════════════════════════════════════════════

def _strip_fenced_blocks(lines):
    """返回一份布尔掩码，True 表示该行在围栏代码块内（含围栏本身两行）。
    围栏：``` 或 ~~~，长度 >=3；闭合围栏长度 >= 开启围栏长度。"""
    in_fence = [False] * len(lines)
    fence_char = None
    fence_len = 0
    inside = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        m = FENCE_RE.match(stripped)
        if not inside:
            if m:
                inside = True
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                in_fence[i] = True
        else:
            in_fence[i] = True
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len:
                inside = False
    return in_fence


def _lint_one(path, root):
    """返回该文件的红项列表 [(line_no_1based, rule_id, msg), ...]。line_no 可为 None。"""
    text = _read_or_die(path)
    lines = text.splitlines()
    problems = []
    name = path.name

    # ADR-L1 文件名
    if not FULL_FILENAME_RE.match(name):
        problems.append((None, "ADR-L1", f"文件名 {name} 不匹配 ^\\d{{4}}-[a-z0-9][a-z0-9-]*\\.md$"))

    # H1
    h1_idx = _find_h1_idx(lines)
    if h1_idx is None:
        problems.append((1, "ADR-L3", "文件为空，缺少 H1"))
        return problems
    h1_line = lines[h1_idx]
    if not h1_line.startswith("# "):
        problems.append((h1_idx + 1, "ADR-L3", "第一个非空行不是 H1（缺少 `# ` 前缀）"))
    else:
        title = h1_line[2:].strip()
        if re.match(r"^ADR\s*\d+", title, re.IGNORECASE) or re.match(r"^\d{4}\s*[·:\-]", title):
            problems.append((h1_idx + 1, "ADR-L3", "H1 带编号前缀（NNNN 或 ADR+编号），应只写一句话结论"))

    # Status 行
    status_idx = None
    for i in range(h1_idx + 1, len(lines)):
        if lines[i].strip():
            status_idx = i
            break
    status_value = None
    status_kind = None
    status_match = None
    if status_idx is None:
        problems.append((h1_idx + 1, "ADR-L4", "缺少 Status 行"))
    else:
        m = STATUS_LINE_RE.match(lines[status_idx])
        if not m:
            problems.append((status_idx + 1, "ADR-L4", "H1 后第一个非空行不是 Status 行格式"))
        else:
            status_value, trailing = m.group(1), m.group(2)
            if not trailing.strip():
                problems.append((status_idx + 1, "ADR-L4", "Status 行 `·` 之后为空"))
            status_kind, status_match = _match_status_kind(status_value)
            if status_kind is None:
                problems.append((status_idx + 1, "ADR-L4", f"Status 取值 {status_value!r} 不在枚举内"))

    # ADR-L5 取代目标存在
    if status_value:
        if status_kind == "superseded_single":
            targets = [status_match.group(1)]
        elif status_kind in ("partially", "superseded_multi"):
            targets = SUPERSEDER_NUMBER_RE.findall(status_value)
        else:
            targets = []
        if status_kind == "superseded_spec":
            spec_name = status_match.group(1)
            spec_path = root / "openspec" / "specs" / spec_name / "spec.md"
            if not spec_path.is_file():
                problems.append((status_idx + 1, "ADR-L5", f"取代目标 spec `{spec_name}` 不存在"))
        for t in targets:
            if t == name[:4]:
                problems.append((status_idx + 1, "ADR-L5", f"取代目标 {t} 是自身"))
                continue
            matches = list((root / ADR_REL_DIR).glob(f"{t}-*.md"))
            if not matches:
                problems.append((status_idx + 1, "ADR-L5", f"取代目标 {t} 对应的文件不存在"))

    is_frozen = status_kind in TERMINAL_KINDS

    if not is_frozen:
        in_fence = _strip_fenced_blocks(lines)
        # H2 白名单与顺序
        h2s = []  # (line_idx, title)
        for i, line in enumerate(lines):
            if in_fence[i]:
                continue
            if line.startswith("## "):
                h2s.append((i, line[3:].strip()))
        seen = set()
        expected_order_idx = -1
        for i, title in h2s:
            if title not in H2_WHITELIST:
                problems.append((i + 1, "ADR-L6", f"H2 `{title}` 不在白名单内"))
                continue
            if title in seen:
                problems.append((i + 1, "ADR-L6", f"H2 `{title}` 重复出现"))
                continue
            seen.add(title)
            pos = H2_WHITELIST.index(title)
            if pos < expected_order_idx:
                problems.append((i + 1, "ADR-L6", f"H2 `{title}` 顺序错误"))
            else:
                expected_order_idx = pos

        # ADR-L8 背景段存在：Status 行与首个 H2 之间至少一个非空、非标题、非围栏行
        if status_idx is not None:
            first_h2_idx = h2s[0][0] if h2s else len(lines)
            has_body = False
            for i in range(status_idx + 1, first_h2_idx):
                if in_fence[i]:
                    continue
                stripped = lines[i].strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    continue
                has_body = True
                break
            if not has_body:
                problems.append((status_idx + 1, "ADR-L8", "Status 行与首个 H2 之间缺少背景段"))

    # ADR-L7 全文无 TODO(adr)
    for i, line in enumerate(lines):
        if "TODO(adr)" in line:
            problems.append((i + 1, "ADR-L7", "含未填写的 TODO(adr) 占位标记"))

    return problems


def cmd_lint(args):
    root = Path(args.root).resolve()
    adr_dir = _resolve_adr_dir(root)
    all_files = sorted(adr_dir.glob("*.md"))

    # ADR-L2：编号唯一性始终按全目录判定
    number_to_files = {}
    for p in all_files:
        m = re.match(r"^(\d{4})-", p.name)
        if m:
            number_to_files.setdefault(m.group(1), []).append(p)

    target_files = [Path(f).resolve() for f in args.files] if args.files else all_files

    exit_code = 0
    for p in target_files:
        problems = _lint_one(p, root)
        m = re.match(r"^(\d{4})-", p.name)
        if m and len(number_to_files.get(m.group(1), [])) > 1:
            others = ", ".join(f.name for f in number_to_files[m.group(1)] if f != p)
            problems.append((1, "ADR-L2", f"编号 {m.group(1)} 与 {others} 重复"))
        problems.sort(key=lambda t: (t[0] is None, t[0] or 0))
        for line_no, rule, msg in problems:
            loc = f"{p}:{line_no}" if line_no is not None else f"{p}"
            print(f"{loc}: {rule}: {msg}")
            exit_code = 1
    return exit_code


# ══════════════════════════════════════════════════════════════════════════
# refs（AM-7）
# ══════════════════════════════════════════════════════════════════════════

# 显式引用抽取：adr/NNNN、NNNN-<slug>.md、ADR-NNNN，恰好四位数字（负向前后瞻防误吃五位数）。
EXPLICIT_ADR_PATTERNS = (
    re.compile(r"(?<!\d)adr/(\d{4})(?!\d)"),
    re.compile(r"(?<!\d)(\d{4})-[a-z0-9][a-z0-9-]*\.md"),
    re.compile(r"(?<!\d)ADR-(\d{4})(?!\d)"),
)

REFS_EXCLUDED_PREFIXES = ("openspec/changes/", "openspec/adr/")


def _run_git_lines(args, cwd):
    """跑一条 git 子命令，返回非空行列表；失败（非零退出 / 无法执行）一律退出 2（AM-7）。"""
    sub = args[0] if args else ""
    try:
        r = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
    except OSError as e:
        _die(2, f"adr: git {sub} 退出 2：{e}；--base 引用不可达或不在仓内；在仓根运行并确认 REF 存在")
    if r.returncode != 0:
        stderr_lines = r.stderr.strip().splitlines()
        first_line = stderr_lines[0] if stderr_lines else "(无 stderr)"
        _die(2, f"adr: git {sub} 退出 {r.returncode}：{first_line}；"
                f"--base 引用不可达或不在仓内；在仓根运行并确认 REF 存在")
    return [line for line in r.stdout.splitlines() if line]


def _extract_explicit_numbers(files):
    """从 --explicit-from 指定的文件中提取显式 ADR 编号（四位）。文件不可读 fail-closed 退出 2。"""
    numbers = set()
    for f in files:
        text = _read_or_die(Path(f))
        for rx in EXPLICIT_ADR_PATTERNS:
            for m in rx.finditer(text):
                numbers.add(m.group(1))
    return numbers


def _build_match_words(diff_paths, union_basename_counts):
    """按 D9 规则为每条 diff 路径生成匹配词集合：完整路径；完整目录路径；
    文件名（仅并集中唯一）；去扩展名的文件名（仅文件名唯一且长度 >=4）。"""
    words = set()
    for p in diff_paths:
        pp = PurePosixPath(p)
        words.add(p)
        parent = str(pp.parent)
        if parent and parent != ".":
            words.add(parent)
        name = pp.name
        if union_basename_counts.get(name, 0) == 1:
            words.add(name)
            stem = pp.stem
            if len(stem) >= 4:
                words.add(stem)
    return words


def cmd_refs(args):
    root = Path(args.root).resolve()
    adr_dir = _resolve_adr_dir(root)

    diff_paths_raw = _run_git_lines(
        ["diff", "--name-only", "--no-renames", f"{args.base}...HEAD"], root)
    diff_paths = [p for p in diff_paths_raw if not p.startswith(REFS_EXCLUDED_PREFIXES)]

    ref_tree = _run_git_lines(["ls-tree", "-r", "--name-only", args.base], root)
    head_tree = _run_git_lines(["ls-tree", "-r", "--name-only", "HEAD"], root)
    union_basename_counts = Counter(
        PurePosixPath(p).name for p in set(ref_tree) | set(head_tree))

    match_words = _build_match_words(diff_paths, union_basename_counts)
    explicit_numbers = _extract_explicit_numbers(args.explicit_from or [])

    results = []
    for p in sorted(adr_dir.glob("*.md")):
        m = re.match(r"^(\d{4})-", p.name)
        if not m:
            continue  # 非 ADR 命名文件：next-id/lint 各自 fail-closed，refs 不重复判定
        nnnn = m.group(1)
        text = _read_or_die(p)
        _idx, status_value, _trailing = _find_status_line(text)
        hits = sorted(w for w in match_words if w in text)
        explicit = nnnn in explicit_numbers
        if hits or explicit:
            results.append({
                "adr": nnnn,
                "path": str(p),
                "status": status_value or "",
                "hits": hits,
                "explicit": explicit,
            })

    results.sort(key=lambda d: d["adr"])
    print(json.dumps(results, ensure_ascii=False))
    return 0


# ══════════════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════════════

def main(argv=None):
    p = argparse.ArgumentParser(prog="adr.py", description="ADR 唯一确定性入口")
    sub = p.add_subparsers(dest="cmd", required=True)

    sn = sub.add_parser("next-id", help="输出下一个可用编号")
    sn.add_argument("--root", required=True)
    sn.set_defaults(func=cmd_next_id)

    snew = sub.add_parser("new", help="新建 ADR，可选 --supersedes/--partial")
    snew.add_argument("--root", required=True)
    snew.add_argument("--title", required=True)
    snew.add_argument("--slug", required=True)
    snew.add_argument("--source", required=True)
    snew.add_argument("--supersedes", default=None)
    snew.add_argument("--partial", default=None)
    snew.set_defaults(func=cmd_new)

    sl = sub.add_parser("lint", help="机械检查 ADR-L1..L8")
    sl.add_argument("--root", required=True)
    sl.add_argument("files", nargs="*")
    sl.set_defaults(func=cmd_lint)

    sr = sub.add_parser("refs", help="按本次改动召回候选 ADR")
    sr.add_argument("--root", required=True)
    sr.add_argument("--base", required=True)
    sr.add_argument("--explicit-from", nargs="*", default=[])
    sr.set_defaults(func=cmd_refs)

    args = p.parse_args(argv)
    try:
        code = args.func(args)
    except SystemExit:
        raise
    raise SystemExit(code)


if __name__ == "__main__":
    main()
