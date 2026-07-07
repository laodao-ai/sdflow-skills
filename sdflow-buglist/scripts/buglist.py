#!/usr/bin/env python3
"""buglist.py — 自动记录/回写/扫描 buglist 的确定性兜底脚本。

skill `sdflow-buglist` 的执行核心。把"判断"留给模型（现象 vs 根因、定优先级、
是否值得记录），把"确定性且易错"的部分交给本脚本：
  - 全局 ID 扫描自增（跨文件不撞号）
  - 今日文件/目录定位与创建（缺则建 + 写头部）
  - 状态总览表 ↔ 详细块 的双写一致（增、改都两处同步）
  - 状态回写的门禁（FIXED 必须有根因 + 证据；WONTFIX 必须有理由）
  - 扫描列表 + 表↔块一致性自检

文件布局（约定，自包含，不依赖外部 rule）：
  <root>/openspec/issues/buglist/YYYY-MM-DD-buglist.md
  结构 = 头部元信息 → ## 状态总览（表）→ 各 bug 的 --- 分隔详细块

用法见 `python buglist.py --help`。所有写操作都是追加式，不删历史；落盘经 atomic_write
（tempfile 同目录 + os.replace），中途异常不会截断原文件。
"""

import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter


def atomic_write(path, text):
    """原子写：同目录临时文件写完整内容 → os.replace 原子换入。
    中途任何异常（含 os.replace 本身失败）都不会截断/损坏原文件——旧内容原样保留，
    临时文件在 finally 里清理，不留残留 .tmp。

    tempfile.mkstemp 固定以 0600 创建临时文件；os.replace 是纯 rename，目标会
    继承临时文件的权限。覆写已存在文件前必须把临时文件权限对齐回原文件的权限，
    否则已存在文件的权限会被静默从（例如）0644 收紧到 0600（对 group/other 变
    不可读）。原文件不存在（首次创建）时用 0o644 兜底。"""
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

STATUS_CODES = ["OPEN", "VERIFIED", "PROPOSED", "IN_PROGRESS", "FIXED", "WONTFIX", "BLOCKED"]
PRIORITIES = ["P0", "P1", "P2", "P3", "P4"]
DEFAULT_PREFIX = "B"
ID_RE = re.compile(r"\b([A-Z])(\d+)\b")


# ── 路径与文件 ───────────────────────────────────────────────────────────────

def repo_root(start="."):
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return os.path.abspath(start)


BRANCH_PREFIX_RE = re.compile(r"^[a-z]+/")


def detect_change(root):
    """自动探测当前所处 OpenSpec change 名，供 add 时记录来源（可被 --json 里的 change 覆盖）。
    优先级：openspec/changes/ 下唯一未归档目录 → git branch 名去前缀 → 空字符串（多 change 并行/
    无法判断时交给模型显式传 change，不瞎猜）。"""
    changes_dir = os.path.join(root, "openspec", "changes")
    dirs = []
    if os.path.isdir(changes_dir):
        dirs = sorted(
            d for d in os.listdir(changes_dir)
            if d != "archive" and os.path.isdir(os.path.join(changes_dir, d))
        )
    if len(dirs) == 1:
        return dirs[0]
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root, capture_output=True, text=True, check=True,
        )
        branch = out.stdout.strip()
    except Exception:
        branch = ""
    candidate = BRANCH_PREFIX_RE.sub("", branch) if branch else ""
    if candidate and (not dirs or candidate in dirs):
        return candidate
    return ""


# ── 关联文档 doc ─────────────────────────────────────────────────────────────

def normalize_doc_paths(doc):
    """把 add 时传入的 doc 字段（str / list[str] / 空）归一化为 list[str]，
    每项保证以 'openspec/' 开头（缺前缀则补）。不强制要求 .md 结尾——
    非 .md 路径仍会被记录，只是不会被 review 工具的 linkify 正则识别为可点击链接
    （该正则只认 `openspec/...同.md` 结尾的反引号内联代码）。"""
    if not doc:
        return []
    items = [doc] if isinstance(doc, str) else list(doc)
    out = []
    for item in items:
        item = (item or "").strip()
        if not item:
            continue
        if not item.startswith("openspec/"):
            item = "openspec/" + item.lstrip("/")
        out.append(item)
    return out


def validate_doc_paths(root, docs):
    """软校验：文档路径（相对 root）不存在只打 stderr 警告，不阻断记录——
    这个功能的目的是鼓励关联文档，不是做门禁。"""
    for d in docs:
        if not os.path.isfile(os.path.join(root, d)):
            print(f"WARNING: 关联文档路径不存在：{d}", file=sys.stderr)


def auto_default_doc(root, change):
    """change 已知但显式 doc 为空时，尽力探测关联文档，按优先级：
    1) openspec/changes/{change}/design.md
    2) openspec/changes/{change}/proposal.md
    3) openspec/changes/archive/*-{change}/design.md（glob，归档目录名前缀是不可预测的日期）
    4) 同上但 proposal.md
    归档层的歧义检查只做一次、在“目录”这一级：先看 `*-{change}` 这个 glob 命中几个归档目录——
    不是恰好 1 个就整层跳过（design.md/proposal.md 都不试），不能因为其中一个目录碰巧只有
    proposal.md 就把它当成唯一匹配悄悄采用（那样目录本身仍是歧义的）。只有 glob 恰好命中 1 个
    目录时，才在该目录内按 design.md → proposal.md 的优先级取值。
    全部落空则返回 []（best-effort，不是必须项）。仅在调用方没有显式传 doc 时才应调用本函数，
    不覆盖显式值。"""
    if not change:
        return []
    for name in ("design.md", "proposal.md"):
        candidate = os.path.join("openspec", "changes", change, name)
        if os.path.isfile(os.path.join(root, candidate)):
            return [candidate.replace(os.sep, "/")]
    archive_pattern = os.path.join(root, "openspec", "changes", "archive", f"*-{change}")
    archive_dirs = [d for d in glob.glob(archive_pattern) if os.path.isdir(d)]
    if len(archive_dirs) == 1:
        archive_dir = archive_dirs[0]
        for name in ("design.md", "proposal.md"):
            candidate = os.path.join(archive_dir, name)
            if os.path.isfile(candidate):
                rel = os.path.relpath(candidate, root)
                return [rel.replace(os.sep, "/")]
    return []


def render_doc_block(docs):
    """渲染详细块里的『关联文档』行；docs 为空则返回空串（不插入该行）。"""
    if not docs:
        return ""
    return "\n**关联文档**：" + "、".join(f"`{d}`" for d in docs) + "\n"


def buglists_dir(root):
    return os.path.join(root, "openspec", "issues", "buglist")


def legacy_buglists_dir(root):
    return os.path.join(root, "openspec", "buglists")


def _dated_dirs(root):
    """新在前（写落新），旧只读兼容——过渡期 dual-read 两目录（Phase B Q1 加固）。
    下游只 update 未迁移旧数据时，若 next_id 只看新目录会从 B1 重数、撞旧目录已有的号；
    扫两目录取并集 max+1 规避这个撞号风险。"""
    return [buglists_dir(root), legacy_buglists_dir(root)]


def list_files(root):
    out = []
    for d in _dated_dirs(root):  # 新在前（目录序），不可对拼接后的全路径整体 sorted
        if os.path.isdir(d):
            files = [
                os.path.join(d, f) for f in os.listdir(d)
                if re.match(r"\d{4}-\d{2}-\d{2}-buglist\.md$", f)
            ]
            out += sorted(files)  # 各目录内部按文件名（=日期）排序
    return out


def today_str(override=None):
    if override:
        return override
    return datetime.date.today().isoformat()


def file_for_date(root, date):
    return os.path.join(buglists_dir(root), f"{date}-buglist.md")


HEADER_TMPL = """# {date} Buglist

> 来源：{source}
> 创建日期：{date}

## 状态总览

| ID | 模块 | 问题摘要 | 优先级 | 状态 | 时间 | 关联Change | 批次 |
|----|------|----------|--------|------|------|------------|------|
"""


def ensure_file(root, date, source):
    path = file_for_date(root, date)
    if not os.path.exists(path):
        atomic_write(path, HEADER_TMPL.format(date=date, source=source or "<未注明>"))
    return path


# ── ID 扫描 ──────────────────────────────────────────────────────────────────

def _ids_in_files(paths, prefix=None):
    ids = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for line in f:
                # 只认状态总览表里的行（以 | 开头且第二列是 ID）
                m = re.match(r"\|\s*([A-Z]\d+)\s*\|", line)
                if m:
                    pid = m.group(1)
                    if prefix is None or pid.startswith(prefix):
                        ids.append(pid)
    return ids


def all_ids(root, prefix=None):
    return _ids_in_files(list_files(root), prefix)


def next_id(root, prefix=DEFAULT_PREFIX):
    nums = [int(ID_RE.match(i).group(2)) for i in all_ids(root) if ID_RE.match(i)]
    n = (max(nums) + 1) if nums else 1
    return f"{prefix}{n}"


def _id_sort_key(pid):
    m = ID_RE.match(pid)
    return (m.group(1), int(m.group(2))) if m else (pid, 0)


def id_conflicts(root):
    """跨路径 ID 冲突检测（Phase B Q1 加固）：同一 ID 若同时出现在新 `openspec/issues/buglist/`
    和旧 `openspec/buglists/` 两处，说明过渡期内新旧数据可能已经手工/脚本各自分配过号，存在
    撞号风险。只读、不阻断——调用方（CLI）自行决定打印警告还是忽略。"""
    new_dir, old_dir = buglists_dir(root), legacy_buglists_dir(root)
    new_files = [p for p in list_files(root) if os.path.dirname(p) == new_dir]
    old_files = [p for p in list_files(root) if os.path.dirname(p) == old_dir]
    new_ids = set(_ids_in_files(new_files))
    old_ids = set(_ids_in_files(old_files))
    return sorted(new_ids & old_ids, key=_id_sort_key)


# ── 表 / 块 解析 ─────────────────────────────────────────────────────────────

def split_sections(lines):
    """返回 (head_end_idx, table_rows_range, body_start_idx)。
    head_end = 状态总览表分隔行后的位置；表行在 [rows_start, rows_end)。"""
    table_hdr = None
    for i, ln in enumerate(lines):
        if re.match(r"\|\s*ID\s*\|", ln):
            table_hdr = i
            break
    if table_hdr is None:
        return None
    sep = table_hdr + 1  # |----|----|
    rows_start = sep + 1
    rows_end = rows_start
    while rows_end < len(lines) and lines[rows_end].lstrip().startswith("|"):
        rows_end += 1
    return {"table_hdr": table_hdr, "rows_start": rows_start, "rows_end": rows_end}


def parse_table_rows(lines, sec):
    rows = {}
    for i in range(sec["rows_start"], sec["rows_end"]):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if len(cells) >= 5:
            rows[cells[0]] = {"line": i, "cells": cells}
    return rows


def block_ranges(lines):
    """返回 {id: (start, end)}，块从 '## {id}:' 到下一个 '---'/'## ' 或 EOF。"""
    out = {}
    starts = []
    for i, ln in enumerate(lines):
        m = re.match(r"##\s+([A-Z]\d+)\s*:", ln)
        if m:
            starts.append((i, m.group(1)))
    for idx, (i, bid) in enumerate(starts):
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == "---" or re.match(r"##\s+[A-Z]\d+\s*:", lines[j]):
                end = j
                break
        out[bid] = (i, end)
    return out


def cmd_next_id(args):
    root = repo_root(args.root)
    conflicts = id_conflicts(root)
    if conflicts:
        print(
            f"WARNING: 检测到跨路径 ID 冲突（新 openspec/issues/buglist/ 与旧 openspec/buglists/ "
            f"都存在）：{', '.join(conflicts)}——建议尽快把旧路径数据迁移到新路径",
            file=sys.stderr,
        )
    print(next_id(root, args.prefix))


# ── add ──────────────────────────────────────────────────────────────────────

BLOCK_TMPL = """
---

## {id}: {title}

| 属性 | 值 |
|------|------|
| 模块 | `{module}` |
| 优先级 | {priority} |
| 状态 | {status} |
{doc_block}
**现象**：{phenomenon}

**根因**：{rootcause}

**修复方案**：
{fix}

**影响范围**：{impact}
"""


def cmd_add(args):
    root = repo_root(args.root)
    data = _load_json(args.json)
    for req in ("module", "summary", "priority", "phenomenon"):
        if not data.get(req):
            _die(f"缺少必填字段：{req}")
    if data["priority"] not in PRIORITIES:
        _die(f"优先级非法：{data['priority']}（应为 {'/'.join(PRIORITIES)}）")
    status = data.get("status", "OPEN")
    if status not in STATUS_CODES:
        _die(f"状态码非法：{status}")

    date = today_str(args.date)
    bid = data.get("id") or next_id(root, args.prefix)
    # OV-3 守卫：显式传 id 时才校验（next_id 自动生成的号必然合法、必然不重，不需要重复查）。
    # 语法用 `[A-Z]+\d+` 全量 fullmatch——不能借用带 `\b` 的 ID_RE.fullmatch，那个模式对
    # "B1" 这类无内部单词边界缺口的整串会拒绝匹配（\b 在两端本就满足，但 fullmatch 要求
    # 整串被两个捕获组精确覆盖，混用 \b 反而更脆），直接用不带 \b 的简单 fullmatch 更可靠。
    # 查重用 all_ids(root)：此刻新文件/新行还未落盘（ensure_file 在下面），all_ids 看到的是
    # 落盘前的既有全集，不会把本次正在 add 的 id 算进去，语义正确。
    if data.get("id"):
        if not re.fullmatch(r"[A-Z]+\d+", bid):
            _die(f"显式 id 语法非法（应形如 B12）：{bid!r}")
        if bid in all_ids(root):
            _die(f"显式 id 与既有重复（会静默丢行）：{bid}")
    time_str = args.time or datetime.datetime.now().strftime("%H:%M")
    change = data.get("change") or detect_change(root)

    # T2 守卫：挂原始用户参数（写盘前），不是 join 后的行字符串——顺序上必须在
    # ensure_file（会落盘建头部文件）之前，拒绝时不留任何新文件/新行残留。
    _reject_cell_unsafe(data["module"], "module")
    _reject_cell_unsafe(data["summary"], "summary")
    _reject_cell_unsafe(change, "change")
    _reject_cell_unsafe(data.get("batch"), "batch")
    _reject_cell_unsafe(time_str, "time")

    path = ensure_file(root, date, data.get("source"))

    docs = normalize_doc_paths(data.get("doc"))
    if not docs:
        docs = auto_default_doc(root, change)  # 显式 doc 优先；仅在为空时才尝试自动关联
    validate_doc_paths(root, docs)

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    sec = split_sections(lines)
    if sec is None:
        _die("文件结构异常：找不到状态总览表")

    row = (f"| {bid} | `{data['module']}` | {data['summary']} | {data['priority']} | "
           f"{status} | {time_str} | {change or '-'} | {data.get('batch', '')} |\n")
    lines.insert(sec["rows_end"], row)

    block = BLOCK_TMPL.format(
        id=bid, title=data.get("title") or data["summary"],
        module=data["module"], priority=data["priority"], status=status,
        doc_block=render_doc_block(docs),
        phenomenon=data["phenomenon"],
        rootcause=data.get("rootcause", "").strip() or "<待分析>",
        fix=_as_list(data.get("fix")), impact=data.get("impact", "<待评估>"),
    )
    extra = data.get("optional") or {}
    for k, v in extra.items():
        block += f"\n**{k}**：{v}\n"
    if not block.endswith("\n"):
        block += "\n"
    lines.append(block)

    atomic_write(path, "".join(lines))
    print(json.dumps({"id": bid, "file": os.path.relpath(path, root), "status": status,
                      "time": time_str, "change": change or None}, ensure_ascii=False))


# ── set-status ───────────────────────────────────────────────────────────────

def cmd_set_status(args):
    root = repo_root(args.root)
    new = args.to
    if new not in STATUS_CODES:
        _die(f"状态码非法：{new}")

    target = None
    for path in list_files(root):
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        sec = split_sections(lines)
        rows = parse_table_rows(lines, sec) if sec else {}
        if args.id in rows:
            target = (path, lines, sec, rows)
            break
    if not target:
        _die(f"未找到 ID：{args.id}")
    path, lines, sec, rows = target

    old = rows[args.id]["cells"][4]
    blocks = block_ranges(lines)
    if args.id not in blocks:
        _die(f"找到表行但缺详细块：{args.id}（表↔块不一致，请先修）")
    b_start, b_end = blocks[args.id]

    # 门禁
    if new == "FIXED":
        if not args.evidence:
            _die("置为 FIXED 必须提供 --evidence（commit hash 或 change 名）")
        if not _has_rootcause(lines, b_start, b_end):
            _die("置为 FIXED 前必须先补全『根因』（当前为空/占位符）")
    if new == "WONTFIX" and not args.reason:
        _die("置为 WONTFIX 必须提供 --reason（不修的理由）")

    # 1) 更新状态总览表的状态列
    cells = rows[args.id]["cells"]
    cells[4] = new
    lines[rows[args.id]["line"]] = "| " + " | ".join(cells) + " |\n"

    # 2) 更新详细块属性表的『状态』行
    for i in range(b_start, b_end):
        if re.match(r"\|\s*状态\s*\|", lines[i]):
            lines[i] = f"| 状态 | {new} |\n"
            break

    # 3) 追加状态变更历史（append-only，不删旧）
    note = args.evidence or args.reason or ""
    hist = f"> {today_str(args.date)} 状态：{old} → {new}" + (f"（{note}）" if note else "") + "\n"
    insert_at = b_end
    while insert_at > b_start and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    lines.insert(insert_at, hist)

    atomic_write(path, "".join(lines))
    print(json.dumps({"id": args.id, "old": old, "new": new,
                      "file": os.path.relpath(path, root)}, ensure_ascii=False))


def _has_rootcause(lines, start, end):
    for i in range(start, end):
        m = re.match(r"\*\*根因\*\*：(.*)", lines[i].strip())
        if m:
            val = m.group(1).strip()
            return bool(val) and not re.fullmatch(r"<.*>", val)
    return False


# ── triage ───────────────────────────────────────────────────────────────────

def cmd_triage(args):
    """给指定 item 赋批次 + 把状态从『未分诊开放态』推进到 PROPOSED（幂等，D7）。

    定位 item：复用 set-status 的查找逻辑（遍历 list_files 找含该 ID 的表行）。
    状态处理（推导自 STATUS_CODES，不硬编码字面集合，镜像 cmd_scan 的 nonterminal 推导）：
      - 未分诊开放态 = STATUS_CODES 减 {PROPOSED} 减终态{FIXED, WONTFIX}
        （即 OPEN/VERIFIED/IN_PROGRESS/BLOCKED）→ 置 PROPOSED。
      - 已是 PROPOSED → 不改状态（no-op，幂等）。
      - 已是终态（FIXED/WONTFIX）→ 不改状态（不把终态倒回 PROPOSED）。
    批次列（表行末列，第 8 列 / cells[7]）无条件写入，与 status 是否变化无关；
    旧格式行（无批次列）先补齐到 8 列再写，不越界。不报错（除 ID 未找到，沿用 set-status 的门禁）。
    """
    root = repo_root(args.root)
    batch = getattr(args, "批次")

    target = None
    for path in list_files(root):
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        sec = split_sections(lines)
        rows = parse_table_rows(lines, sec) if sec else {}
        if args.id in rows:
            target = (path, lines, sec, rows)
            break
    if not target:
        _die(f"未找到 ID：{args.id}")
    path, lines, sec, rows = target

    cells = rows[args.id]["cells"]
    old_status = cells[4]
    open_untriaged = set(STATUS_CODES) - {"FIXED", "WONTFIX", "PROPOSED"}
    new_status = "PROPOSED" if old_status in open_untriaged else old_status

    _reject_cell_unsafe(batch, "batch")
    cells[4] = new_status
    while len(cells) < 8:  # 旧格式（无批次列）行防御式补齐，不越界写 cells[7]
        cells.append("")
    cells[7] = batch
    lines[rows[args.id]["line"]] = "| " + " | ".join(cells) + " |\n"

    if new_status != old_status:
        blocks = block_ranges(lines)
        if args.id in blocks:
            b_start, b_end = blocks[args.id]
            for i in range(b_start, b_end):
                if re.match(r"\|\s*状态\s*\|", lines[i]):
                    lines[i] = f"| 状态 | {new_status} |\n"
                    break

    atomic_write(path, "".join(lines))
    print(json.dumps({"id": args.id, "old_status": old_status, "new_status": new_status,
                      "batch": batch, "file": os.path.relpath(path, root)}, ensure_ascii=False))


# ── scan ─────────────────────────────────────────────────────────────────────

def cmd_scan(args):
    root = repo_root(args.root)
    bugs = []
    problems = []
    for path in list_files(root):
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        sec = split_sections(lines)
        rows = parse_table_rows(lines, sec) if sec else {}
        blocks = block_ranges(lines)
        rel = os.path.relpath(path, root)
        # OV-3：重复 ID 检测——必须在 parse_table_rows 已经按 ID 建 dict 丢行之前、
        # 从原始表行里数，否则重复的那一行早被静默吞掉，dict 视角里只剩 1 个 ID，测不出来。
        if sec:
            raw_ids = [
                lines[i].strip().strip("|").split("|", 1)[0].strip()
                for i in range(sec["rows_start"], sec["rows_end"])
            ]
            for dup_id in sorted({rid for rid, cnt in Counter(raw_ids).items() if cnt > 1}):
                problems.append(f"{rel}: 重复 ID：{dup_id}（parse_table_rows 会静默丢行）")
        # 一致性：表↔块
        for bid in rows:
            if bid not in blocks:
                problems.append(f"{rel}: 表有 {bid} 但缺详细块")
        for bid in blocks:
            if bid not in rows:
                problems.append(f"{rel}: 块有 {bid} 但缺总览表行")
        # 状态一致性
        for bid, info in rows.items():
            if bid in blocks:
                bs, be = blocks[bid]
                block_status = None
                for i in range(bs, be):
                    m = re.match(r"\|\s*状态\s*\|\s*(\w+)", lines[i])
                    if m:
                        block_status = m.group(1)
                        break
                if block_status and block_status != info["cells"][4]:
                    problems.append(
                        f"{rel}: {bid} 状态不一致（表={info['cells'][4]} 块={block_status}）")
        for bid, info in rows.items():
            c = info["cells"]
            bugs.append({"id": bid, "module": c[1], "summary": c[2],
                         "priority": c[3], "status": c[4],
                         "time": c[5] if len(c) > 5 else None,
                         "change": c[6] if len(c) > 6 and c[6] != "-" else None,
                         "batch": c[7] if len(c) > 7 and c[7] else None,
                         "file": rel})

    if args.status:
        bugs = [b for b in bugs if b["status"] == args.status]
    if args.change:
        bugs = [b for b in bugs if b["change"] == args.change]
    if getattr(args, "批次", None):
        bugs = [b for b in bugs if b.get("batch") == getattr(args, "批次")]
    if args.open_ungrouped:
        nonterminal = set(STATUS_CODES) - {"FIXED", "WONTFIX"}
        bugs = [b for b in bugs if b["status"] in nonterminal and not b.get("batch")]
    if args.json:
        print(json.dumps({"bugs": bugs, "problems": problems}, ensure_ascii=False, indent=2))
        return
    if not bugs:
        print("（无匹配 bug）")
    for b in sorted(bugs, key=lambda x: (x["priority"], x["id"])):
        print(f"{b['id']:<5} {b['priority']} {b['status']:<12} {b['module']:<24} {b['summary']}")
    if problems:
        print("\n⚠️ 一致性问题：")
        for p in problems:
            print("  - " + p)
    else:
        print("\n✓ 表↔块一致")


# ── 工具 ─────────────────────────────────────────────────────────────────────

def _load_json(src):
    if src in (None, "-"):
        return json.load(sys.stdin)
    with open(src, encoding="utf-8") as f:
        return json.load(f)


def _as_list(fix):
    if fix is None:
        return "- <待补充>"
    if isinstance(fix, list):
        return "\n".join(f"- {x}" for x in fix)
    return str(fix)


def _die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def _reject_cell_unsafe(value, field):
    """总览管道表字段 fail-closed 守卫：含 ASCII | 或换行即拒（防列错位/行截断腐蚀盘面）。
    MUST 用于各命令入口的原始用户参数，勿用于 " | ".join(cells) 行拼接 sink。"""
    if value is None:
        return
    if "|" in str(value) or "\n" in str(value) or "\r" in str(value):
        _die(f"字段 {field} 含非法字符（| 或换行），会破坏总览表列对齐：{value!r}")


def main():
    p = argparse.ArgumentParser(description="自动记录/回写/扫描 buglist")
    p.add_argument("--root", default=".", help="仓库根（默认自动探测 git 根）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("next-id", help="打印下一个全局 ID")
    s.add_argument("--prefix", default=DEFAULT_PREFIX)
    s.set_defaults(func=cmd_next_id)

    s = sub.add_parser("add", help="新增 bug（JSON 输入，stdin 或 --json 文件）")
    s.add_argument("--json", help="JSON 文件路径；缺省读 stdin")
    s.add_argument("--prefix", default=DEFAULT_PREFIX)
    s.add_argument("--date", help="覆盖日期 YYYY-MM-DD（默认今天）")
    s.add_argument("--time", help="覆盖记录时间 HH:MM（默认当前时刻）")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("set-status", help="回写状态（双写 + 门禁 + 追加历史）")
    s.add_argument("--id", required=True)
    s.add_argument("--to", required=True, help="目标状态码")
    s.add_argument("--evidence", help="commit hash / change 名（FIXED 必填）")
    s.add_argument("--reason", help="WONTFIX 理由（WONTFIX 必填）")
    s.add_argument("--date", help="覆盖日期")
    s.set_defaults(func=cmd_set_status)

    s = sub.add_parser("triage", help="赋批次 + 未分诊开放态→PROPOSED（幂等，D7）")
    s.add_argument("--id", required=True)
    s.add_argument("--批次", dest="批次", required=True, help="批次名（清理 change 名）")
    s.set_defaults(func=cmd_triage)

    s = sub.add_parser("scan", help="列出 bug + 表↔块一致性自检")
    s.add_argument("--status", help="按状态码过滤")
    s.add_argument("--change", help="按关联 change（来源）过滤")
    s.add_argument("--批次", dest="批次", help="按批次过滤")
    s.add_argument("--open-ungrouped", dest="open_ungrouped", action="store_true",
                    help="非终态（STATUS_CODES 减 FIXED/WONTFIX）且未分批的 bug")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_scan)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
