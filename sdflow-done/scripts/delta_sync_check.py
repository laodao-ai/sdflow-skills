#!/usr/bin/env python3
"""delta_sync_check.py — sdflow-done 归档后核对 delta 已同步进主 spec.

对归档目录 `specs/<cap>/spec.md` 里的每条 delta，按名字核对 `openspec/specs/<cap>/spec.md`：
  ADDED / MODIFIED  主 spec 里恰好一条同名 Requirement（缺 = 漏同步；多 = 追加而非替换）
  REMOVED           主 spec 里已不存在
  RENAMED           旧名不存在、新名恰好一条
只比名字、不比正文：归档子代理按代码实况改写正文是允许的，名字是确定性信号。
只在刚归档时有意义——之后的 change 合法地改名、删除都会让历史归档「不符」。

退出码：0 全部同步；1 有缺口（逐条打印）；2 用法错误或归档目录不可读。
stdlib-only，确定性，fail-closed。
"""
import argparse
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from pathlib import Path

REQ_PREFIX = "### Requirement:"
SECTION_RE = re.compile(r"^## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements\b")
RENAME_RE = re.compile(r"^-\s*(FROM|TO):\s*`?" + re.escape(REQ_PREFIX) + r"\s*(.+?)`?\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _lines_outside_fences(text):
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield line


def parse_delta(text):
    """→ {"ADDED": [...], "MODIFIED": [...], "REMOVED": [...], "RENAMED": [(from, to), ...]}"""
    out = {"ADDED": [], "MODIFIED": [], "REMOVED": [], "RENAMED": []}
    section = None
    pending_from = None
    for line in _lines_outside_fences(text):
        if line.startswith("## "):
            m = SECTION_RE.match(line)
            section = m.group(1) if m else None
            pending_from = None
            continue
        if section is None:
            continue
        if section == "RENAMED":
            m = RENAME_RE.match(line.strip())
            if not m:
                continue
            if m.group(1) == "FROM":
                pending_from = m.group(2).strip()
            elif pending_from is not None:
                out["RENAMED"].append((pending_from, m.group(2).strip()))
                pending_from = None
        elif line.startswith(REQ_PREFIX):
            out[section].append(line[len(REQ_PREFIX):].strip())
    return out


def main_requirement_names(text):
    return [line[len(REQ_PREFIX):].strip()
            for line in _lines_outside_fences(text) if line.startswith(REQ_PREFIX)]


def check(archive_dir, specs_root):
    """→ 缺口列表（每项一行人读描述）。"""
    problems = []
    delta_files = sorted((archive_dir / "specs").glob("*/spec.md"))
    for delta_path in delta_files:
        cap = delta_path.parent.name
        delta = parse_delta(delta_path.read_text(encoding="utf-8"))
        main_path = specs_root / cap / "spec.md"
        names = (main_requirement_names(main_path.read_text(encoding="utf-8"))
                 if main_path.is_file() else [])
        if not main_path.is_file() and (delta["ADDED"] or delta["MODIFIED"] or delta["RENAMED"]):
            problems.append(f"{cap}: 主 spec 不存在（{main_path}），delta 一条都没同步")
            continue
        for kind in ("ADDED", "MODIFIED"):
            for name in delta[kind]:
                n = names.count(name)
                if n == 0:
                    problems.append(f"{cap}: {kind} 未同步：{name}")
                elif n > 1:
                    problems.append(f"{cap}: {kind} 在主 spec 出现 {n} 次（应替换而非追加）：{name}")
        for name in delta["REMOVED"]:
            if name in names:
                problems.append(f"{cap}: REMOVED 仍在主 spec：{name}")
        for old, new in delta["RENAMED"]:
            if old in names:
                problems.append(f"{cap}: RENAMED 旧名仍在主 spec：{old}")
            if names.count(new) != 1:
                problems.append(f"{cap}: RENAMED 新名在主 spec 出现 {names.count(new)} 次：{new}")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="核对归档 change 的 delta 已同步进主 spec")
    ap.add_argument("--archive-dir", required=True,
                    help="归档目录，如 openspec/changes/archive/2026-10-21-foo")
    ap.add_argument("--specs-root", default=None,
                    help="主 spec 根目录，缺省为归档目录向上推出的 openspec/specs")
    args = ap.parse_args(argv)

    archive_dir = Path(args.archive_dir)
    if not archive_dir.is_dir():
        print(f"delta_sync_check: 归档目录不存在：{archive_dir}", file=sys.stderr)
        return 2
    specs_root = Path(args.specs_root) if args.specs_root else archive_dir.resolve().parents[2] / "specs"
    if not specs_root.is_dir():
        print(f"delta_sync_check: 主 spec 根目录不存在：{specs_root}（用 --specs-root 指定）",
              file=sys.stderr)
        return 2

    problems = check(archive_dir, specs_root)
    if problems:
        print(f"delta_sync_check: ✗ {len(problems)} 处 delta 未同步进主 spec（{archive_dir.name}）")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"delta_sync_check: ✓ delta 已全部同步（{archive_dir.name}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
