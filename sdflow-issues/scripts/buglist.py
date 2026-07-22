#!/usr/bin/env python3
"""buglist.py — sdflow-issues 的 **bug 池薄入口**（dedupe-issues-scripts-shared-layer · adr/0027）。

原 `sdflow-buglist` skill 的执行核心已上移唯一共享源 `sdflow_issues_core`；本文件只做薄入口：
解析 args → 注入 bug 的 `POOL_SPEC` + `PoolStrategy` → 调 `run_cli`。共享执行逻辑
（ID 扫描自增、canonical/overlay 写入、legacy 只读 promotion、状态门禁、扫描自检）全部
在 core，本文件不再持有任何副本。

文件布局（约定不变）：`<root>/openspec/issues/buglist/YYYY-MM-DD-buglist.md`。
用法见 `python buglist.py --help`。

薄入口顶部 `sys.path.insert(...)`（AD-1 / SC-R3）：多数测试用 `importlib.spec_from_file_location`
按文件加载本入口、不设 sys.path，故这里显式把入口所在目录插到 sys.path 前端，令
`from sdflow_issues_core import` 可解。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdflow_issues_core import *  # noqa: F401,F403  re-export 共享 helper（tests 按名 getattr 取用）
import sdflow_issues_core as _core

_SPEC = _core.POOL_SPEC["bug"]
_STRAT = _core.BUG_STRATEGY

# pool 特定常量（兼容测试按名访问；单一源仍是 POOL_SPEC，此处只是有序/列表投影）
STATUS_CODES = ["OPEN", "VERIFIED", "PROPOSED", "IN_PROGRESS", "FIXED", "WONTFIX", "BLOCKED"]
PRIORITIES = list(_STRAT.specific_values_ordered)
DEFAULT_PREFIX = _SPEC.default_prefix


# pool-bound leaf API：绑定 bug POOL_SPEC 后暴露 root-only 签名（tests 直接调用）。
def next_id(root, prefix=DEFAULT_PREFIX, semantic=None):
    return _core.next_id(root, prefix, semantic)


def list_files(root):
    return _core.list_files(root, _SPEC)


def all_ids(root, prefix=None):
    return _core.all_ids(root, _SPEC, prefix)


def id_conflicts(root):
    return _core.id_conflicts(root, _SPEC)


def today_str(override=None):
    return _core._period_str(_SPEC, override)


def cmd_scan(args):
    return _core.cmd_scan(args, _SPEC, _STRAT)


def main():
    _core.run_cli(_SPEC, _STRAT)


if __name__ == "__main__":
    main()
