"""CLI subcommand 覆盖闭包门（SC-R3 / R5）。**留存**门。

（issues-v2-single-file-model · Task 3 改造）v1 时代本门比对「argparse 自身枚举的 subcommand」
与「行为等价 harness 覆盖清单」（`test_task6_cli_equivalence_harness.COVERED_SUBCOMMANDS`）——
三薄入口（buglist.py/todolist.py/issues.py）之间需要互相等价，才有「equivalence harness」这个
概念。v2 单文件模型下三薄入口合一为 `issues_v2.py`，不再有跨脚本等价性要问题；对应的
`test_task6_cli_equivalence_harness.py` 已随本次改造删除。

留存的不变量改为更直接的形态：`issues_v2.py` argparse **自身**枚举的每个 subcommand
（`add`/`set-status`/`scan`/`reindex`/`next-id`/`migrate`）MUST 逐一被 `test_issues_v2.py`
的 CLI 集成测试**触达**（即该测试文件的源码里，对 `SCRIPT` 发起的子进程调用含该 subcommand
字面量）。枚举让 argparse 自己回答（invalid-choice 的 usage `{...}` 行），非手搓 subcommand
名单（CLAUDE.md 基准 5：让工具自己回答）。守的是「新增 CLI subcommand 必被
`test_issues_v2.py` 覆盖」这个当前系统不变量。

注：v1 的 **migration 零回归门**（pre-migration node baseline 逐 node 比对 + 冻结契约
sha256）已随 `dedupe-issues-scripts-shared-layer` 归档一并退役——baseline 是迁移前的历史
快照，migration 完成后它不对应任何当前不变量，只会随测试正常演进（合理增删）误报。
"""
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "scripts"
TESTS_DIR = Path(__file__).parent
SCRIPT = str(SCRIPTS / "issues_v2.py")

_USAGE_CHOICES_RE = re.compile(r"\{([^}]+)\}")


def _argparse_subcommands():
    """跑一次 invalid-choice，让 argparse 自己在 usage 行吐出 `{a,b,c}` 枚举。"""
    try:
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", ".", "__invalid__"],
            capture_output=True, text=True, timeout=120,

            encoding="utf-8",
            errors="replace",)
    except subprocess.TimeoutExpired as exc:  # fail-closed，非静默 hang
        raise AssertionError(f"argparse usage 子进程超时（>120s）: {exc}") from exc
    text = proc.stdout + proc.stderr
    m = _USAGE_CHOICES_RE.search(text)
    assert m, f"未从 argparse usage 解析出 subcommand 枚举: {text!r}"
    return {c.strip().strip("'\"") for c in m.group(1).split(",")}


def test_every_argparse_subcommand_is_touched_by_issues_v2_tests():
    enumerated = _argparse_subcommands()
    assert enumerated, "未枚举出任何 subcommand"

    source = (TESTS_DIR / "test_issues_v2.py").read_text(encoding="utf-8")
    uncovered = sorted(
        name for name in enumerated
        if f'"{name}"' not in source
    )
    assert not uncovered, (
        "以下 argparse subcommand 未在 test_issues_v2.py 里被任何子进程调用触达（CLI 覆盖"
        "缺口）：\n"
        f"  {uncovered}\n"
        f"  argparse 枚举: {sorted(enumerated)}"
    )
