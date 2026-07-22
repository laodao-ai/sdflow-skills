"""POOL_SPEC 封闭 schema + 关系正确性守卫（dedupe-issues-scripts-shared-layer Task 1）。

守护对象（design AD-3 / spec `determinism-guards` DG-M1「POOL_SPEC 封闭 schema 完备 +
关系正确性守」）：

- **封闭 schema**：`POOL_SPEC` 为封闭 dataclass 集合，required 维 = 类型字段全集。
  新增差异维必须改 schema（`PoolSpec` 字段 + `POOL_SPEC_FIELDS` 注册表两处），
  不得从后门（硬编码常量 / argparse default / callable）漏进 core。字段注册表漂移即红。
- **fail-closed keys**：`POOL_SPEC.keys() == {"bug","todo"}`，额外/缺失 pool key 即红。
- **关系正确性**：`terminal_set ⊆ status_values`（per pool）。
- **值正确性（外部字面锚）**：固定契约维（前缀 / scan 键 / 目录 / legacy glob / 粒度 / 文件干）
  按 design AD-3 表**钉死字面值**（`EXPECTED_CONTRACT` / `test_fixed_contract_dims_match_design_table`）
  ——**这是值正确性的真外部锚**（POOL_SPEC 之外独立的 design-table 常量，改错值即红）。

> **诚实修正（Task 4 复核·DG-M1 诚实边界）**：`RECORDER_POOL_CONFIG` / `TERMINAL_STATUSES` 自 Task 2
> 起已**从 POOL_SPEC 派生**（单一源，见 core `__init__.py:227-233`）。故
> `test_specific_field_and_enums_match_recorder_config` / `test_terminal_set_matches_recorder_terminal_statuses`
> 现为 **POOL_SPEC 自比其派生物 = 同源**——它们守的是「派生接线正确」（RECORDER_POOL_CONFIG 确实
> 由 POOL_SPEC 生成、投影没接错），**不再是独立的漂移捕获**（同源、护力对「值填错」为零）。
> 值正确性的真护力**全在** `EXPECTED_CONTRACT`（外部 design-table 字面锚）与 `test_required_dims_all_present`。
> 不 overclaim「对照三脚本权威常量抓漂移」。

诚实边界：本守卫是 POOL_SPEC **数据面**的封闭性（keys/schema/关系 fail-closed 充要）+ **外部字面锚**
值正确性守。「core 源码无 pool 条件分支」是**另一条**守（AST 级 best-effort，`test_determinism_guards.py`）
——不在本文件口径内。

加载策略（AD-1 / SC-R3）：本测试把 `sdflow-issues/scripts/` 插入 `sys.path` 后
`import sdflow_issues_core`（package-aware 加载）；唯一命名避 `sys.modules["core"]` 碰撞。
`RECORDER_POOL_CONFIG` 对照源经 `importlib.spec_from_file_location` 按文件加载 `issues.py`，
不额外污染 sys.path。
"""

import dataclasses
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import sdflow_issues_core as core  # noqa: E402


def _load_issues_module():
    """按文件加载 issues.py 取其权威常量（RECORDER_POOL_CONFIG / TERMINAL_STATUSES）作对照源。

    issues.py 是合并后的幸存脚本，本 change Task 1 阶段其 RECORDER_POOL_CONFIG / TERMINAL_STATUSES
    仍是 pool 特定值的权威真相源——POOL_SPEC 的对应维 MUST 与之逐值一致（迁移期等价锚）。
    """
    path = SCRIPTS_DIR / "issues.py"
    spec = importlib.util.spec_from_file_location("_issues_for_pool_spec_check", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ISSUES = _load_issues_module()


# ── design AD-3 表的固定契约维（钉死字面值——POOL_SPEC 错值即红）────────────────
EXPECTED_CONTRACT = {
    "bug": {
        "date_granularity": "day",
        "file_stem": "buglist",
        "issues_dir": "openspec/issues/buglist",
        "legacy_dir_glob": "openspec/buglists/*.md",
        "specific_field": "priority",
        "default_prefix": "B",
        "scan_output_key": "bugs",
    },
    "todo": {
        "date_granularity": "month",
        "file_stem": "todolist",
        "issues_dir": "openspec/issues/todolist",
        "legacy_dir_glob": "openspec/todolists/*.md",
        "specific_field": "type",
        "default_prefix": "T",
        "scan_output_key": "items",
    },
}


# ── 封闭 schema ─────────────────────────────────────────────────────────────
def test_pool_spec_keys_fail_closed():
    """POOL_SPEC.keys() 必须恰为 {"bug","todo"}——额外/缺失 pool key 即红。"""
    assert set(core.POOL_SPEC) == {"bug", "todo"}


def test_pool_spec_is_closed_dataclass():
    """每个 pool 的 spec 是 frozen dataclass 实例（非裸 dict——封闭 schema，无处硬塞新维）。"""
    for pool, spec in core.POOL_SPEC.items():
        assert dataclasses.is_dataclass(spec), f"{pool} spec 非 dataclass"
        params = spec.__dataclass_params__
        assert params.frozen, f"{pool} spec 非 frozen（可变 = 差异可从后门被改写）"


def test_field_registry_matches_dataclass():
    """POOL_SPEC_FIELDS 注册表 == PoolSpec 实际字段全集（顺序无关）。

    这是「新增维必须改 schema」的机械化：给 PoolSpec 加字段而不同步 POOL_SPEC_FIELDS
    （或反之）即红——强制差异维的引入是一次自觉的两处编辑，堵「作者没想到的差异被
    硬编码进 core」的后门（design AD-3 / 对抗A NEW-2）。
    """
    actual = {f.name for f in dataclasses.fields(core.PoolSpec)}
    assert set(core.POOL_SPEC_FIELDS) == actual
    # 且注册表无重复
    assert len(core.POOL_SPEC_FIELDS) == len(set(core.POOL_SPEC_FIELDS))


def test_required_dims_all_present():
    """design/tasks 点名的 8 个 required 差异维在 schema 中都有对应字段。

    「特定字段」拆为 specific_field（字段名）+ specific_values（枚举，成对）⇒ 字段级 9 项。
    """
    required_dims = {
        "date_granularity",   # 文件粒度（日/月）
        "issues_dir",         # 目录
        "legacy_dir_glob",    # legacy dir glob
        "specific_field",     # 特定字段（字段名）
        "specific_values",    # 特定字段（枚举，与字段名成对）
        "status_values",      # 状态词表
        "terminal_set",       # 终态集
        "default_prefix",     # ID 前缀 B/T
        "scan_output_key",    # scan 输出键 bugs/items
    }
    fields_ = {f.name for f in dataclasses.fields(core.PoolSpec)}
    missing = required_dims - fields_
    assert not missing, f"schema 缺 required 维: {missing}"


# ── 关系正确性 ───────────────────────────────────────────────────────────────
def test_terminal_subset_of_status():
    """终态集 ⊆ 状态词表（hr-tg H2）——终态若不在词表内是无意义/永不可达的死值。"""
    for pool, spec in core.POOL_SPEC.items():
        assert spec.terminal_set <= spec.status_values, (
            f"{pool}: terminal_set {spec.terminal_set} ⊄ status_values {spec.status_values}"
        )


# ── 值正确性：与 issues.py 权威常量逐值一致（非只 non-None）─────────────────────
def test_specific_field_and_enums_match_recorder_config():
    """特定字段名 + 枚举 + 状态词表 与 issues.RECORDER_POOL_CONFIG 逐值一致。"""
    for pool, spec in core.POOL_SPEC.items():
        field, values, statuses = ISSUES.RECORDER_POOL_CONFIG[pool]
        assert spec.specific_field == field
        assert set(spec.specific_values) == set(values)
        assert set(spec.status_values) == set(statuses)


def test_terminal_set_matches_recorder_terminal_statuses():
    """终态集与 issues.TERMINAL_STATUSES 逐值一致。"""
    for pool, spec in core.POOL_SPEC.items():
        assert set(spec.terminal_set) == set(ISSUES.TERMINAL_STATUSES[pool])


def test_fixed_contract_dims_match_design_table():
    """固定契约维（粒度/文件干/目录/legacy glob/字段名/前缀/scan 键）钉死 design AD-3 表字面值。"""
    for pool, expected in EXPECTED_CONTRACT.items():
        spec = core.POOL_SPEC[pool]
        for dim, want in expected.items():
            assert getattr(spec, dim) == want, f"{pool}.{dim}: got {getattr(spec, dim)!r}, want {want!r}"


# ── validator 本体：正例绿 + 对违规 fail-closed（mutation 反红证明守卫有效）──────
def test_validate_pool_spec_passes_on_canonical():
    """规范 POOL_SPEC 通过 validate_pool_spec（不抛）。"""
    assert core.validate_pool_spec(core.POOL_SPEC) is True


def test_validate_reds_on_extra_pool_key():
    """额外 pool key → PoolSpecError（keys 必须恰为 {"bug","todo"}）。"""
    mutated = dict(core.POOL_SPEC)
    mutated["chore"] = core.POOL_SPEC["bug"]
    with pytest.raises(core.PoolSpecError):
        core.validate_pool_spec(mutated)


def test_validate_reds_on_missing_pool_key():
    """缺 pool key → PoolSpecError。"""
    mutated = {"bug": core.POOL_SPEC["bug"]}
    with pytest.raises(core.PoolSpecError):
        core.validate_pool_spec(mutated)


def test_validate_reds_on_terminal_not_subset():
    """terminal_set ⊄ status_values → PoolSpecError。"""
    bad = dataclasses.replace(
        core.POOL_SPEC["bug"],
        terminal_set=frozenset(core.POOL_SPEC["bug"].terminal_set | {"NOT_A_STATUS"}),
    )
    mutated = dict(core.POOL_SPEC)
    mutated["bug"] = bad
    with pytest.raises(core.PoolSpecError):
        core.validate_pool_spec(mutated)


def test_validate_reds_on_non_pool_spec_value():
    """pool 值不是 PoolSpec（如裸 dict——差异从后门塞进）→ PoolSpecError。"""
    mutated = dict(core.POOL_SPEC)
    mutated["todo"] = {"specific_field": "type"}  # 裸 dict 逃生口
    with pytest.raises(core.PoolSpecError):
        core.validate_pool_spec(mutated)


def test_validate_reds_on_registry_drift(monkeypatch):
    """POOL_SPEC_FIELDS 注册表与 PoolSpec 字段全集漂移 → PoolSpecError。

    证明手写注册表不是摆设：漏改一处（此处模拟少一维）即被 validate_pool_spec 拦红。
    """
    drifted = tuple(f for f in core.POOL_SPEC_FIELDS if f != "scan_output_key")
    monkeypatch.setattr(core, "POOL_SPEC_FIELDS", drifted)
    with pytest.raises(core.PoolSpecError):
        core.validate_pool_spec(core.POOL_SPEC)


def test_pool_spec_frozen_rejects_mutation():
    """frozen dataclass 拒绝字段赋值（差异不可被运行期改写）。"""
    with pytest.raises(dataclasses.FrozenInstanceError):
        core.POOL_SPEC["bug"].default_prefix = "X"
