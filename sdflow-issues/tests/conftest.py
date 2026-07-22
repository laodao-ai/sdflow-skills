"""`sdflow-issues/tests/` 共用的 `subprocess.run` 补桩工具（**单一源**）。

## 为什么必须按 argv 分派、MUST NOT 整体替换

整体替换 `issues_mod.subprocess.run` 会连带劫持**被测函数之外**的一切子进程调用，
其中包括 `repo_root` 的 `git rev-parse --show-toplevel` 探测——于是 git 会"返回"
测试注入的载荷，root 解析在形状校验处先崩。此时用例看似通过（派生字节确实没变），
但那是因为被测逻辑**根本没访问过目标目录**，而不是因为不变量被保护住了。
这正是 `harden-repo-root-fail-closed` 要消灭的**假绿**形态。

∴ 补桩一律走本模块的 `dispatch_run`：命中判据的子进程返回替身，其余**透传真实行为**。

## 机械守

`test_patch_discipline.py` 用 `ast` 扫本目录所有测试文件，机械保证：
① 每个 `subprocess.run` 补桩站点要么走本模块的工厂、要么在显式白名单里（带理由）；
② 本模块工厂自身保留 `real_run` 透传分支（防「简化」回整体替换形态）。

注意：本文件**只服务 `sdflow-issues/tests/`**，与仓根 conftest 无关。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import issues as issues_mod  # noqa: E402
import sdflow_issues_core as _issues_core  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_recorder_delegation_globals():
    """[impl-review-fix] F1 防御：每个测试后无条件复位 core 的委派单例全局。

    core 是进程内单例模块全局；大量测试直调 read_pool/_scan_pool 绕过 main()，若某测试
    （或被测 main() 的错误路径）遗留脏 `_ACTIVE_RECORDER_TOKEN`/`_ACTIVE_RECORDER_CHAIN`，
    会按执行顺序污染同进程后续测试（RecorderLockError: delegation denied）。此 fixture
    消除「靠执行顺序侥幸绿」——不依赖任何被测代码正常复位。
    """
    yield
    _issues_core._ACTIVE_RECORDER_TOKEN = None
    _issues_core._ACTIVE_RECORDER_CHAIN = None


def is_recorder_scan(command):
    """命令是否为 recorder 的 `scan` 子进程（`[python, <script>, --root, R, scan, ...]`）。"""
    return isinstance(command, (list, tuple)) and len(command) > 1 and "scan" in command


def argv_contains(*tokens):
    """构造判据：argv 同时含全部 `tokens`（如 `argv_contains("batch", "add")`）。"""
    # 空 tokens 会让 `all([])` 恒真 ⇒ 分派静默退化成整体替换，而门 A/门 B 都看不见
    # （它们只检查调用形状与工厂本体，不检查判据的取值）。这正是本 change 要消灭的
    # 退化形态，故在构造期就拒绝，不留作"语义残余"。
    if not tokens:
        raise ValueError("argv_contains() 需至少一个 token：空判据恒真，等价于整体替换")

    def predicate(command):
        if not isinstance(command, (list, tuple)):
            return False
        return all(token in command for token in tokens)

    return predicate


def make_dispatch_run(predicate, handler):
    """按 argv 分派的 `subprocess.run` 替身：命中 `predicate` 的走 `handler(command)`，
    其余**透传** `real_run`（构造时捕获的真实实现）。

    签名一律 `(command, *args, **kwargs)` 全透传——写死关键字签名的话，将来若以
    位置方式传 `capture_output` 会 `TypeError`。
    """
    real_run = issues_mod.subprocess.run

    def run(command, *args, **kwargs):
        if predicate(command):
            return handler(command)
        return real_run(command, *args, **kwargs)

    return run


@pytest.fixture(name="argv_contains")
def argv_contains_fixture():
    """工厂 fixture：`argv_contains("batch", "add")` → 判据。"""
    return argv_contains


@pytest.fixture
def dispatch_run():
    """工厂 fixture：`dispatch_run(predicate, handler)` → 分派型 `subprocess.run` 替身。"""
    return make_dispatch_run


@pytest.fixture
def scan_only_run():
    """工厂 fixture：`scan_only_run(handler)` → 只拦 recorder `scan`、其余透传。"""

    def factory(handler):
        return make_dispatch_run(is_recorder_scan, handler)

    return factory
