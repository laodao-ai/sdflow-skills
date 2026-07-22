#!/usr/bin/env python3
"""todolist.py — sdflow-issues 的 **todo 池薄入口**（dedupe-issues-scripts-shared-layer · adr/0027）。

todo 池的执行核心已上移唯一共享源 `sdflow_issues_core`；本文件只做薄入口：
解析 args → 注入 todo 的 `POOL_SPEC` + `PoolStrategy` → 调 `run_cli`。收集优化想法/技术债/
改进等**非缺陷**项，与 bug 的差异（每月一文件、T 前缀、按类型而非优先级、详细块可选、
状态码 OPEN/PROPOSED/DONE/WONTDO）全部经 `POOL_SPEC`/`PoolStrategy` 注入，本文件不持副本。

文件布局（约定不变）：`<root>/openspec/issues/todolist/YYYY-MM-todolist.md`。
用法见 `python todolist.py --help`。

薄入口顶部 `sys.path.insert(...)` 理由同 buglist.py（AD-1 / SC-R3）。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdflow_issues_core import *  # noqa: F401,F403  re-export 共享 helper（tests 按名 getattr 取用）
import sdflow_issues_core as _core

_SPEC = _core.POOL_SPEC["todo"]
_STRAT = _core.TODO_STRATEGY

# pool 特定常量（兼容测试按名访问；单一源仍是 POOL_SPEC）
STATUS_CODES = ["OPEN", "PROPOSED", "DONE", "WONTDO"]
TYPE_TAGS = list(_STRAT.specific_values_ordered)
DEFAULT_PREFIX = _SPEC.default_prefix


# pool-bound leaf API：绑定 todo POOL_SPEC 后暴露 root-only 签名（tests 直接调用）。
def next_id(root, prefix=DEFAULT_PREFIX, semantic=None):
    return _core.next_id(root, prefix, semantic)


def list_files(root):
    return _core.list_files(root, _SPEC)


def all_ids(root, prefix=None):
    return _core.all_ids(root, _SPEC, prefix)


def id_conflicts(root):
    return _core.id_conflicts(root, _SPEC)


def this_month(override=None):
    return _core._period_str(_SPEC, override)


def cmd_scan(args):
    return _core.cmd_scan(args, _SPEC, _STRAT)


def main():
    _core.run_cli(_SPEC, _STRAT)


if __name__ == "__main__":
    main()
