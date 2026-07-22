"""Task 6.2 — 覆盖判据零回归门（SC-R3 / R5）。**留存**门，非一次性脚本。

**MUST NOT 用 `通过数 ≥ N` 魔数**——design 明确：该魔数被本 change 删除的 7 个 mirror 测试
证伪（删测试后总数下降，魔数会误判为回归，或被下调掩盖真回归）。正解 = 与冻结的 pre-refactor
node-id manifest **逐 node 比对**：

  1. **零回归 node 门**：baseline 每个 node（除 allowlist 的 7 个 `test_mirror_consistency.py`）
     在 migration 后仍存在且 collect 得到。三脚本合一把 `sdflow-buglist/tests/`·`sdflow-todolist/tests/`
     的测试文件迁进 `sdflow-issues/tests/`，故 baseline 里旧目录路径的 node 经 **RENAME-MAP**
     （旧 tests 目录 → `sdflow-issues/tests/`）重定位后须命中当前 collection。消失的 node **只允许**
     是那 7 个 allowlist；其它 node 消失 = 回归（红）。新增 node 允许。
  2. **全 subcommand 触达门**：argparse **自身**枚举的每个 subcommand（core 三薄入口 + issues.py
     top-level + batch 二级）migration 后逐一被行为等价 harness（`test_task6_cli_equivalence_harness`）
     触达。枚举让 argparse 自己回答（`build_parser` 的 subparser choices + `--help`/invalid-choice
     的 usage `{...}`），非手搓 subcommand 名单（CLAUDE.md 基准 5：让工具自己回答）。
  3. **无 FAILED / 无重构导致的 skip**：当前 collection 干净可跑（本门只做 collect-only 对账；
     实际 pass/fail 由全套件 run 保证，pre-existing 环境/平台 skip 不算回归）。
"""
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = Path(__file__).parent.parent / "scripts"
BASELINE = (
    REPO_ROOT
    / "openspec" / "changes" / "dedupe-issues-scripts-shared-layer"
    / "impl-reports" / "node-id-manifest.baseline.txt"
)

# 三脚本合一：旧两 skill 目录整体并入 sdflow-issues。node id 里旧名有两类出现——
#   ① 测试文件路径前缀：`sdflow-{buglist,todolist}/tests/*`  → `sdflow-issues/tests/*`
#   ② param 括号内的**被测脚本路径**：`sdflow-{buglist,todolist}/scripts/{buglist,todolist}.py`
#      （如 `test_...[sdflow-buglist/scripts/buglist.py]`）→ `sdflow-issues/scripts/*`
# 二者都是「文件搬家、测试不删」的 migration 事实，故按目录前缀做**全串替换**（非仅 node 头部）。
# baseline 已核实：旧名在 node id 中**仅**以上述 tests/·scripts/ 路径出现（无 legacy-name 数据
# param），故全串替换不会误改本应保留旧名的 param。消失 node 只允许是 7 个 allowlist。
RENAME_MAP = {
    "sdflow-buglist/tests/": "sdflow-issues/tests/",
    "sdflow-todolist/tests/": "sdflow-issues/tests/",
    "sdflow-buglist/scripts/": "sdflow-issues/scripts/",
    "sdflow-todolist/scripts/": "sdflow-issues/scripts/",
}

# 允许消失的 node（design/tasks 4.1：镜像 AST 守单一物理源后无对象，整文件删除）。
ALLOWLIST_DELETED = frozenset(
    f"sdflow-buglist/tests/test_mirror_consistency.py::{t}"
    for t in (
        "test_docstring_diff_ok",
        "test_frontmatter_constant_consistency",
        "test_helper_deletion_is_not_silently_swallowed",
        "test_logic_drift_is_caught",
        "test_priorities_constant_consistency",
        "test_three_way_mirror_consistency",
        "test_two_way_mirror_consistency",
    )
)


def _load_baseline_nodes():
    nodes = []
    for raw in BASELINE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        nodes.append(line)
    return nodes


def _apply_rename(node):
    for old, new in RENAME_MAP.items():
        node = node.replace(old, new)
    return node


def _collect_current_nodes():
    """pytest --collect-only 从仓根 collect 全部 node id（让 pytest 自己回答，非静态推断）。"""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"collect-only 失败:\n{proc.stdout}\n{proc.stderr}"
    nodes = set()
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if "::" in line and not line.startswith(("=", "_", "warnings", "no tests")):
            nodes.add(line)
    assert nodes, "collect-only 未解析出任何 node id"
    return nodes


# ── 门 1：零回归 node 门（逐 node 比对，非计数魔数）──────────────────────────────
def test_zero_regression_every_baseline_node_survives():
    baseline = _load_baseline_nodes()
    current = _collect_current_nodes()

    missing = []
    for node in baseline:
        if node in ALLOWLIST_DELETED:
            continue
        relocated = _apply_rename(node)
        if relocated not in current:
            missing.append((node, relocated))

    assert not missing, (
        "零回归门失败——以下 baseline node 在 migration 后消失（非 allowlist）：\n"
        + "\n".join(f"  baseline: {n}\n  期望(重定位后): {r}" for n, r in missing)
    )


def test_allowlist_deleted_nodes_are_actually_gone():
    """反向：7 个 intended-delete node 确已消失（防 test_mirror_consistency 残留导致守法未切换）。"""
    current = _collect_current_nodes()
    still_present = [n for n in ALLOWLIST_DELETED if n in current]
    # 迁移后旧路径也不该出现在 sdflow-issues/tests/ 下
    relocated_present = [
        _apply_rename(n) for n in ALLOWLIST_DELETED if _apply_rename(n) in current
    ]
    assert not still_present and not relocated_present, (
        f"intended-delete mirror node 仍存在: {still_present + relocated_present}"
    )


def test_baseline_is_frozen_and_nonempty():
    """基线自身完整性：非空 + 恰含 7 个 allowlist node（防基线被误改削弱门）。"""
    baseline = set(_load_baseline_nodes())
    assert len(baseline) >= 2000, f"baseline node 数异常偏少: {len(baseline)}"
    assert ALLOWLIST_DELETED <= baseline, "baseline 应含 7 个 intended-delete node"


# ── 门 2：全 argparse subcommand 触达门（argparse 自己枚举，非手搓名单）──────────
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
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "issues.py"), "--root", ".", *argv, "__invalid__"],
        capture_output=True, text=True,
    )
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
        "以下 argparse subcommand 未被行为等价 harness 触达（migration 覆盖缺口）：\n"
        f"  {uncovered}\n"
        f"  argparse 枚举: {sorted(enumerated)}\n"
        f"  harness 覆盖: {sorted(COVERED_SUBCOMMANDS)}"
    )
