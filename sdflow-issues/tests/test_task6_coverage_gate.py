"""Task 6.2 — CLI subcommand 覆盖闭包门（SC-R3 / R5）。**留存**门。

argparse **自身**枚举的每个 subcommand（core 三薄入口 + issues.py top-level + batch 二级）
MUST 逐一被行为等价 harness（`test_task6_cli_equivalence_harness`）触达。枚举让 argparse
自己回答（`build_parser` 的 subparser choices + invalid-choice 的 usage `{...}`），非手搓
subcommand 名单（CLAUDE.md 基准 5：让工具自己回答）。守的是「新增 CLI subcommand 必被 harness
覆盖」这个当前系统不变量。

注：本 change 一次性的 **migration 零回归门**（pre-migration node baseline 逐 node 比对 +
冻结契约 sha256）已随 `dedupe-issues-scripts-shared-layer` 归档一并退役——baseline 是迁移前
的历史快照，migration 完成后它不对应任何当前不变量，只会随测试正常演进（合理增删）误报。
留存下来的是 CLI 行为契约（本门 + harness），锚的是当前 issues CLI 该有的外部行为。
"""
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "scripts"


# ── 全 argparse subcommand 触达门（argparse 自己枚举，非手搓名单）──────────────
def _core_subcommands():
    sys.path.insert(0, str(SCRIPTS))
    import sdflow_issues_core as core
    parser = core.build_parser(core.POOL_SPEC["bug"], core.BUG_STRATEGY)
    choices = set()
    for action in parser._subparsers._group_actions:
        choices.update(action.choices.keys())
    return {f"core:{name}" for name in choices}


_USAGE_CHOICES_RE = re.compile(r"\{([^}]+)\}")


def _argparse_choices(argv):
    """跑一次 invalid-choice，让 argparse 自己在 usage 行吐出 `{a,b,c}` 枚举。"""
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "issues.py"), "--root", ".", *argv, "__invalid__"],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired as exc:  # fail-closed，非静默 hang
        raise AssertionError(f"argparse usage 子进程超时（>120s）: {exc}") from exc
    text = proc.stdout + proc.stderr
    m = _USAGE_CHOICES_RE.search(text)
    assert m, f"未从 argparse usage 解析出 subcommand 枚举: {text!r}"
    return [c.strip() for c in m.group(1).split(",")]


def _issues_subcommands():
    top = _argparse_choices([])  # {reindex, batch, sweep}
    labels = set()
    for name in top:
        if name == "batch":
            for action in _argparse_choices(["batch"]):  # {add,set-status,rename,lint}
                labels.add(f"issues:batch:{action}")
        else:
            labels.add(f"issues:{name}")
    return labels


def test_every_argparse_subcommand_is_touched_by_equivalence_harness():
    sys.path.insert(0, str(Path(__file__).parent))
    from test_task6_cli_equivalence_harness import COVERED_SUBCOMMANDS

    enumerated = _core_subcommands() | _issues_subcommands()
    assert enumerated, "未枚举出任何 subcommand"

    uncovered = sorted(enumerated - COVERED_SUBCOMMANDS)
    assert not uncovered, (
        "以下 argparse subcommand 未被行为等价 harness 触达（CLI 覆盖缺口）：\n"
        f"  {uncovered}\n"
        f"  argparse 枚举: {sorted(enumerated)}\n"
        f"  harness 覆盖: {sorted(COVERED_SUBCOMMANDS)}"
    )
