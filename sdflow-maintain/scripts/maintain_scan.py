#!/usr/bin/env python3
"""maintain_scan.py — sdflow-maintain 的确定性只读差异报告核心。

扫 openspec/specs|rules ↔ INDEX.md（托管块外）双向 set-diff、CLAUDE.md 过时引用、
workflow bundle 陈旧遮蔽，产出四类分节只读报告。纯读、fail-closed、零写文件。
判断（归组/是否修复）留 SKILL 步骤 4；判据 canonical 见 init.py，本文件保自包含副本
+ 一致性守卫测试机验（见 tests/test_marker_consistency.py）。
"""
import argparse
import os
import re
import sys


class MaintainScanError(Exception):
    """坏输入 / 无法可靠完成扫描。main() 捕获 → stderr → 非零退出（fail-closed）。"""


def find_repo_root(start):
    """从 start 向上找含 .git 的目录，返回其绝对路径；找不到 raise MaintainScanError。"""
    cur = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            raise MaintainScanError(f"未找到 git 仓根（从 {start} 向上）")
        cur = parent


def run_scan(root):
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="sdflow-maintain 确定性只读差异报告（fail-closed）")
    ap.add_argument("--root", default=None, help="仓根，缺省自动探测 git 根")
    args = ap.parse_args(argv)
    try:
        root = args.root or find_repo_root(os.getcwd())
        report = run_scan(root)
    except MaintainScanError as e:
        print(f"[maintain_scan] ERROR {e}", file=sys.stderr)
        return 2
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
