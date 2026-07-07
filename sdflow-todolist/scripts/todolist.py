#!/usr/bin/env python3
"""todolist.py — 自动记录/回写/扫描 todolist 的确定性兜底脚本。

skill `sdflow-todolist` 的执行核心。收集优化想法/技术债/改进等**非缺陷**项，
作为后续排期的收集池。与 buglist 的差异：每月一文件、T 前缀、按类型而非优先级、
详细块可选（轻量优先）、无根因/修复方案、状态码 OPEN/PROPOSED/DONE/WONTDO。

把"判断"留给模型（值不值得记、归哪类、要不要写动机/思路），把"确定性且易错"的部分
交给本脚本：全局 T-ID 自增、当月文件定位/创建、总览表 ↔ 详细块一致、DONE 门禁
（必带 change/commit 证据）、WONTDO 门禁（必带理由）、扫描 + 一致性自检。

文件布局（约定，自包含，不依赖外部 rule）：
  <root>/openspec/issues/todolist/YYYY-MM-todolist.md
  结构 = 头部 → ## 状态总览（表）→ 各项的 --- 分隔详细块（可选）

用法见 `python todolist.py --help`。写操作追加式，不删历史；落盘经 atomic_write
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

STATUS_CODES = ["OPEN", "PROPOSED", "DONE", "WONTDO"]
TYPE_TAGS = ["性能优化", "可观测性", "代码质量", "功能增强", "基础设施"]
DEFAULT_PREFIX = "T"
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


def todolists_dir(root):
    return os.path.join(root, "openspec", "issues", "todolist")


def legacy_todolists_dir(root):
    return os.path.join(root, "openspec", "todolists")


def _dated_dirs(root):
    """新在前（写落新），旧只读兼容——过渡期 dual-read 两目录（Phase B Q1 加固，镜像 buglist）。
    下游只 update 未迁移旧数据时，若 next_id 只看新目录会从 T1 重数、撞旧目录已有的号；
    扫两目录取并集 max+1 规避这个撞号风险。"""
    return [todolists_dir(root), legacy_todolists_dir(root)]


def list_files(root):
    out = []
    for d in _dated_dirs(root):  # 新在前（目录序），不可对拼接后的全路径整体 sorted
        if os.path.isdir(d):
            files = [
                os.path.join(d, f) for f in os.listdir(d)
                if re.match(r"\d{4}-\d{2}-todolist\.md$", f)
            ]
            out += sorted(files)  # 各目录内部按文件名（=月份）排序
    return out


def this_month(override=None):
    if override:
        return override
    return datetime.date.today().strftime("%Y-%m")


def file_for_month(root, month):
    return os.path.join(todolists_dir(root), f"{month}-todolist.md")


HEADER_TMPL = """# {month} TODO

> 项目：{project}

## 状态总览

| ID | 模块 | 描述 | 类型 | 状态 | 时间 | 关联Change | 批次 |
|----|------|------|------|------|------|------------|------|
"""


def ensure_file(root, month, project):
    path = file_for_month(root, month)
    if not os.path.exists(path):
        atomic_write(path, HEADER_TMPL.format(month=month, project=project or "<未注明>"))
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
    """跨路径 ID 冲突检测（Phase B Q1 加固，镜像 buglist）：同一 ID 若同时出现在新
    `openspec/issues/todolist/` 和旧 `openspec/todolists/` 两处，说明过渡期内新旧数据可能已经
    手工/脚本各自分配过号，存在撞号风险。只读、不阻断——调用方（CLI）自行决定打印警告还是忽略。"""
    new_dir, old_dir = todolists_dir(root), legacy_todolists_dir(root)
    new_files = [p for p in list_files(root) if os.path.dirname(p) == new_dir]
    old_files = [p for p in list_files(root) if os.path.dirname(p) == old_dir]
    new_ids = set(_ids_in_files(new_files))
    old_ids = set(_ids_in_files(old_files))
    return sorted(new_ids & old_ids, key=_id_sort_key)


# ── 表 / 块 解析 ─────────────────────────────────────────────────────────────

def split_sections(lines):
    table_hdr = None
    for i, ln in enumerate(lines):
        if re.match(r"\|\s*ID\s*\|", ln):
            table_hdr = i
            break
    if table_hdr is None:
        return None
    rows_start = table_hdr + 2  # 跳过表头 + 分隔行
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
    out = {}
    starts = [(i, m.group(1)) for i, ln in enumerate(lines)
              if (m := re.match(r"##\s+([A-Z]\d+)\s*:", ln))]
    for i, bid in starts:
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == "---" or re.match(r"##\s+[A-Z]\d+\s*:", lines[j]):
                end = j
                break
        out[bid] = (i, end)
    return out


def _find_row_file(root, item_id):
    """定位含 item_id 的状态总览表行所在的月度文件（T5：从 `cmd_set_status`/
    `cmd_triage` 抽出——两处遍历 `list_files` 找含该 ID 表行的逻辑逐字相同，
    镜像 buglist.py 的同名 helper，各自模块内抽、不跨 recorder 共享，D4）。
    返回 (path, lines, sec, rows)；找不到则 `_die` 退出（沿用两处原有的错误文案），
    调用方无需再自行判空。"""
    for path in list_files(root):
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        sec = split_sections(lines)
        rows = parse_table_rows(lines, sec) if sec else {}
        if item_id in rows:
            return path, lines, sec, rows
    _die(f"未找到 ID：{item_id}")


def cmd_next_id(args):
    root = repo_root(args.root)
    conflicts = id_conflicts(root)
    if conflicts:
        print(
            f"WARNING: 检测到跨路径 ID 冲突（新 openspec/issues/todolist/ 与旧 openspec/todolists/ "
            f"都存在）：{', '.join(conflicts)}——建议尽快把旧路径数据迁移到新路径",
            file=sys.stderr,
        )
    print(next_id(root, args.prefix))


# ── add ──────────────────────────────────────────────────────────────────────

def cmd_add(args):
    root = repo_root(args.root)
    data = _load_json(args.json)
    for req in ("module", "summary", "type"):
        if not data.get(req):
            _die(f"缺少必填字段：{req}")
    if data["type"] not in TYPE_TAGS:
        _die(f"类型非法：{data['type']}（应为 {'/'.join(TYPE_TAGS)}）")
    status = data.get("status", "OPEN")
    if status not in STATUS_CODES:
        _die(f"状态码非法：{status}")

    month = this_month(args.month)
    tid = data.get("id") or next_id(root, args.prefix)
    # OV-3 守卫（镜像 buglist.py）：显式传 id 时才校验（next_id 自动生成的号必然合法、必然
    # 不重，不需要重复查）。语法用单字母前缀 `[A-Z]\d+` 全量 fullmatch，不借用带 `\b` 的 ID_RE。
    # 必须是单字母前缀（不是 `[A-Z]+\d+`）：代码库对 ID 的识别全部只认单字母——
    # `_ids_in_files` 的 `\| *([A-Z]\d+) *\|`、`ID_RE = \b([A-Z])(\d+)\b`、block_ranges 均如此，
    # 若语法校验放行多字母前缀（如 "TT12"），all_ids() 根本认不出它，查重形同虚设
    # （两次 add 同一个 "TT12" 都会静默通过），且它会破坏 block_ranges 的正则匹配。
    # 先判 isinstance(str)：id 若是 JSON 数字等非字符串，直接 fullmatch 会抛裸 TypeError，
    # 破坏 _die 的 ERROR: 契约，须在此优雅拒绝。
    # 查重用 all_ids(root)：此刻新文件/新行还未落盘（ensure_file 在下面），all_ids 看到的是
    # 落盘前的既有全集，不会把本次正在 add 的 id 算进去，语义正确。
    if data.get("id"):
        if not (isinstance(tid, str) and re.fullmatch(r"[A-Z]\d+", tid)):
            _die(f"显式 id 语法非法（应形如 T12，单字母前缀）：{tid!r}")
        if tid in all_ids(root):
            _die(f"显式 id 与既有重复（会静默丢行）：{tid}")
    time_str = args.time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    change = data.get("change") or detect_change(root)

    # T2 守卫：挂原始用户参数（写盘前），不是 join 后的行字符串——顺序上必须在
    # ensure_file（会落盘建头部文件）之前，拒绝时不留任何新文件/新行残留。
    _reject_cell_unsafe(data["module"], "module")
    _reject_cell_unsafe(data["summary"], "summary")
    _reject_cell_unsafe(change, "change")
    _reject_cell_unsafe(data.get("batch"), "batch")
    _reject_cell_unsafe(time_str, "time")

    path = ensure_file(root, month, data.get("project"))

    explicit_docs = normalize_doc_paths(data.get("doc"))
    docs = explicit_docs
    if not docs:
        docs = auto_default_doc(root, change)  # 显式 doc 优先；仅在为空时才尝试自动关联
    validate_doc_paths(root, docs)

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    sec = split_sections(lines)
    if sec is None:
        _die("文件结构异常：找不到状态总览表")

    row = (f"| {tid} | `{data['module']}` | {data['summary']} | {data['type']} | "
           f"{status} | {time_str} | {change or '-'} | {data.get('batch', '')} |\n")
    lines.insert(sec["rows_end"], row)

    # 详细块可选：给了 动机/思路/备注，或显式传了关联文档，才写（轻量优先）。
    # auto-default 探测到的 doc 本身不触发建块——只用来丰富一个本来就会建的块。
    block = _build_block(tid, data, status, docs, explicit_docs)
    if block:
        lines.append(block)

    atomic_write(path, "".join(lines))
    print(json.dumps({"id": tid, "file": os.path.relpath(path, root), "status": status,
                      "block": bool(block), "time": time_str, "change": change or None},
                     ensure_ascii=False))


def _build_block(tid, data, status, docs=None, explicit_docs=None):
    """是否建块 只看：motivation/approach/note 任一非空，或调用方显式传了 doc
    （explicit_docs 非空）。auto-default 探测到的 doc（docs 里有、explicit_docs 里没有）不参与这个
    判断——它只在块因为其它理由已经要建时，用来丰富该块的『关联文档』行；如果块本不该建，
    auto-default 的结果在这里被静默丢弃，条目仍保持轻量（只记一行）。"""
    docs = docs or []
    explicit_docs = explicit_docs or []
    parts = {k: data.get(k, "").strip() for k in ("motivation", "approach", "note")}
    if not any(parts.values()) and not explicit_docs:
        return ""  # 简单项：不建块（auto-default 的 doc 不单独触发建块）
    title = data.get("title") or data["summary"]
    b = f"\n---\n\n## {tid}: {title}\n\n"
    b += "| 属性 | 值 |\n|------|------|\n"
    b += f"| 模块 | `{data['module']}` |\n| 类型 | {data['type']} |\n| 状态 | {status} |\n"
    if docs:
        b += "\n**关联文档**：" + "、".join(f"`{d}`" for d in docs) + "\n"
    if parts["motivation"]:
        b += f"\n**动机**：{parts['motivation']}\n"
    if parts["approach"]:
        b += f"\n**思路**：{parts['approach']}\n"
    if parts["note"]:
        b += f"\n**备注**：{parts['note']}\n"
    return b


# ── set-status ───────────────────────────────────────────────────────────────

def cmd_set_status(args):
    root = repo_root(args.root)
    new = args.to
    if new not in STATUS_CODES:
        _die(f"状态码非法：{new}")

    path, lines, sec, rows = _find_row_file(root, args.id)

    # 门禁
    if new == "DONE" and not args.evidence:
        _die("置为 DONE 必须提供 --evidence（关联的 change 名或 commit hash）")
    if new == "WONTDO" and not args.reason:
        _die("置为 WONTDO 必须提供 --reason（放弃的理由）")

    old = rows[args.id]["cells"][4]
    cells = rows[args.id]["cells"]
    cells[4] = new
    lines[rows[args.id]["line"]] = "| " + " | ".join(cells) + " |\n"

    note = args.evidence or args.reason or ""
    hist = f"> {this_month(args.month)} 状态：{old} → {new}" + (f"（{note}）" if note else "") + "\n"

    blocks = block_ranges(lines)
    if args.id in blocks:
        # 有块：更新块状态 + 追加历史
        b_start, b_end = blocks[args.id]
        for i in range(b_start, b_end):
            if re.match(r"\|\s*状态\s*\|", lines[i]):
                lines[i] = f"| 状态 | {new} |\n"
                break
        insert_at = b_end
        while insert_at > b_start and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        lines.insert(insert_at, hist)
    elif note:
        # 无块但有证据/理由：补一个最小块留痕（DONE/WONTDO 走这条）
        lines.append(_minimal_block(args.id, cells, new, hist))

    atomic_write(path, "".join(lines))
    print(json.dumps({"id": args.id, "old": old, "new": new,
                      "file": os.path.relpath(path, root)}, ensure_ascii=False))


def _minimal_block(tid, cells, status, hist):
    title = cells[2]
    return (f"\n---\n\n## {tid}: {title}\n\n"
            f"| 属性 | 值 |\n|------|------|\n"
            f"| 模块 | {cells[1]} |\n| 类型 | {cells[3]} |\n| 状态 | {status} |\n\n{hist}")


# ── triage ───────────────────────────────────────────────────────────────────

def cmd_triage(args):
    """给指定 item 赋批次 + 把状态从『未分诊开放态』推进到 PROPOSED（幂等，D7）。
    镜像 buglist.py 的 cmd_triage；差异只在 todolist 自己的 STATUS_CODES（终态 DONE/WONTDO）。

    定位 item：复用 set-status 的查找逻辑（遍历 list_files 找含该 ID 的表行）。
    状态处理（推导自 STATUS_CODES，不硬编码字面集合，镜像 cmd_scan 的 nonterminal 推导）：
      - 未分诊开放态 = STATUS_CODES 减 {PROPOSED} 减终态{DONE, WONTDO} → 即 {OPEN} → 置 PROPOSED。
      - 已是 PROPOSED → 不改状态（no-op，幂等）。
      - 已是终态（DONE/WONTDO）→ 不改状态（不把终态倒回 PROPOSED）。
    批次列（表行末列，第 8 列 / cells[7]）无条件写入，与 status 是否变化无关；
    旧格式行（无批次列）先补齐到 8 列再写，不越界。不报错（除 ID 未找到，沿用 set-status 的门禁）。
    块可选：状态若变化且块存在则同步块的『状态』行；块不存在不强制建块（triage 不写批次/历史进块）。
    """
    root = repo_root(args.root)
    batch = getattr(args, "批次")

    path, lines, sec, rows = _find_row_file(root, args.id)

    cells = rows[args.id]["cells"]
    old_status = cells[4]
    open_untriaged = set(STATUS_CODES) - {"DONE", "WONTDO", "PROPOSED"}
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
    items, problems = [], []
    for path in list_files(root):
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        sec = split_sections(lines)
        rows = parse_table_rows(lines, sec) if sec else {}
        blocks = block_ranges(lines)
        rel = os.path.relpath(path, root)
        # OV-3：重复 ID 检测（镜像 buglist.py）——必须在 parse_table_rows 已经按 ID 建 dict
        # 丢行之前、从原始表行里数，否则重复的那一行早被静默吞掉，dict 视角里只剩 1 个 ID。
        if sec:
            raw_ids = [
                lines[i].strip().strip("|").split("|", 1)[0].strip()
                for i in range(sec["rows_start"], sec["rows_end"])
            ]
            for dup_id in sorted({rid for rid, cnt in Counter(raw_ids).items() if cnt > 1}):
                problems.append(f"{rel}: 重复 ID：{dup_id}（parse_table_rows 会静默丢行）")
        # OV-1：行 arity 检测（镜像 buglist.py）——无块坏行（如描述含裸 `|`）会把某数据行
        # 拆成多于/少于标准列数的 cells，`parse_table_rows` 只要求 `len(cells) >= 5` 就照单
        # 按固定列位读，列错位不会自己报错——必须显式核对每一原始数据行的列数，标准 8 列
        # （新格式，含批次列）/7 列（旧格式，无批次列）之外的一律判定 arity 异常。
        if sec:
            for i in range(sec["rows_start"], sec["rows_end"]):
                cells_raw = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if len(cells_raw) not in (7, 8):
                    rid = cells_raw[0] if cells_raw else "?"
                    problems.append(
                        f"{rel}: {rid} 行 arity 异常：{len(cells_raw)} 列（应 8/7）"
                    )
        # 块若存在必须有对应表行（块可选，故只单向查）
        for bid in blocks:
            if bid not in rows:
                problems.append(f"{rel}: 块有 {bid} 但缺总览表行")
        # 状态一致性（仅对有块的项）
        for bid, info in rows.items():
            if bid in blocks:
                bs, be = blocks[bid]
                bstatus = next((m.group(1) for i in range(bs, be)
                                if (m := re.match(r"\|\s*状态\s*\|\s*(\w+)", lines[i]))), None)
                if bstatus and bstatus != info["cells"][4]:
                    problems.append(f"{rel}: {bid} 状态不一致（表={info['cells'][4]} 块={bstatus}）")
            c = info["cells"]
            items.append({"id": bid, "module": c[1], "summary": c[2],
                          "type": c[3], "status": c[4],
                          "time": c[5] if len(c) > 5 else None,
                          "change": c[6] if len(c) > 6 and c[6] != "-" else None,
                          "batch": c[7] if len(c) > 7 and c[7] else None,
                          "file": rel})

    if args.status:
        items = [b for b in items if b["status"] == args.status]
    if args.type:
        items = [b for b in items if b["type"] == args.type]
    if args.change:
        items = [b for b in items if b["change"] == args.change]
    if getattr(args, "批次", None):
        items = [b for b in items if b.get("batch") == getattr(args, "批次")]
    if args.open_ungrouped:
        # todolist 的非终态集与 buglist 不同：STATUS_CODES 只有 OPEN/PROPOSED/DONE/WONTDO，
        # 终态是 DONE/WONTDO，不能硬套 buglist 的 5 值非终态集。
        nonterminal = set(STATUS_CODES) - {"DONE", "WONTDO"}
        items = [b for b in items if b["status"] in nonterminal and not b.get("batch")]
    if args.json:
        print(json.dumps({"items": items, "problems": problems}, ensure_ascii=False, indent=2))
        return
    if not items:
        print("（无匹配 TODO）")
    for b in sorted(items, key=lambda x: (x["status"], x["id"])):
        print(f"{b['id']:<5} {b['status']:<10} {b['type']:<8} {b['module']:<24} {b['summary']}")
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
    p = argparse.ArgumentParser(description="自动记录/回写/扫描 todolist")
    p.add_argument("--root", default=".", help="仓库根（默认自动探测 git 根）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("next-id", help="打印下一个全局 ID")
    s.add_argument("--prefix", default=DEFAULT_PREFIX)
    s.set_defaults(func=cmd_next_id)

    s = sub.add_parser("add", help="新增 TODO（JSON 输入，stdin 或 --json 文件）")
    s.add_argument("--json", help="JSON 文件路径；缺省读 stdin")
    s.add_argument("--prefix", default=DEFAULT_PREFIX)
    s.add_argument("--month", help="覆盖月份 YYYY-MM（默认本月）")
    s.add_argument("--time", help="覆盖记录时间 YYYY-MM-DD HH:MM（默认当前时刻）")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("set-status", help="回写状态（表写 + 门禁 + 有证据则补块留痕）")
    s.add_argument("--id", required=True)
    s.add_argument("--to", required=True, help="目标状态码")
    s.add_argument("--evidence", help="change 名 / commit hash（DONE 必填）")
    s.add_argument("--reason", help="WONTDO 理由（WONTDO 必填）")
    s.add_argument("--month", help="覆盖月份")
    s.set_defaults(func=cmd_set_status)

    s = sub.add_parser("triage", help="赋批次 + 未分诊开放态→PROPOSED（幂等，D7）")
    s.add_argument("--id", required=True)
    s.add_argument("--批次", dest="批次", required=True, help="批次名（清理 change 名）")
    s.set_defaults(func=cmd_triage)

    s = sub.add_parser("scan", help="列出 TODO + 表↔块一致性自检")
    s.add_argument("--status", help="按状态码过滤")
    s.add_argument("--type", help="按类型过滤")
    s.add_argument("--change", help="按关联 change（来源）过滤")
    s.add_argument("--批次", dest="批次", help="按批次过滤")
    s.add_argument("--open-ungrouped", dest="open_ungrouped", action="store_true",
                    help="非终态（STATUS_CODES 减 DONE/WONTDO）且未分批的 TODO")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_scan)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
