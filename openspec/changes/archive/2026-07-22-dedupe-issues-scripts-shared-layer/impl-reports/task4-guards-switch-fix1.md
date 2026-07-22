# Task 4 双轴审 fix1 — `_legacy_block_range` 承重重复消除 + 守卫两处清理

修 Task 4 双轴审 3 处发现：Important-A（`_legacy_block_range` 逐行相同的承重重复）+
Minor-B（`scan_pool_branches` 死参数）+ Minor-C（误导注释）。全套件 2110 passed 保持。

## Important-A：扫描算法收敛为唯一命名单一源

**逐行比对确认**：`issues.py::_legacy_block_range(document, raw_id)` 与
`sdflow_issues_core::_legacy_block_range(document, raw_id, path)` 是**逐行相同**的块边界扫描
（同 `##\s+([A-Z][0-9]+)\s*:` regex + `_legacy_semantic_id_key` 比对 + start/end 扫描 +
marker collision 循环）。唯一差异：(1) path 取参 vs 读 `document['path']`；(2) 错误发射
（issues 抛英文 rename `ValueError`、core 抛中文 `_frontmatter_error`）。无本质语义差异，可安全合并。

### 抽取的 core 单一源

```python
class LegacyBlockError(Exception):
    def __init__(self, kind, raw_id, *, candidates=None, line=None): ...
    # kind ∈ {"ambiguous","collision"}; 只携结构化数据，无 caller-facing prose

def _scan_legacy_block_range(document, raw_id) -> (start, end):
    # pool-agnostic 单一源；ambiguous → raise LegacyBlockError("ambiguous", raw_id, candidates=n)
    #                       collision → raise LegacyBlockError("collision", raw_id, line=i+1)
```

`_scan_legacy_block_range` **pool-agnostic**（无 pool 分支、无 prose），满足 AD-3/Q2。

### 两 caller 各自 catch + 格式化

- **core** `_legacy_block_range(document, raw_id, path)`：`try _scan… except LegacyBlockError`
  → `_frontmatter_error(...)` 中文，文案逐字不变。
- **issues** 新增 `_rename_legacy_block_range(document, raw_id)`：`try _scan… except LegacyBlockError`
  → `ValueError` 英文（"rerun the original batch rename command"），文案逐字不变；两 rename caller
  （`_body_with_legacy_bug_markers` :124、`_reject_target_document_problems` :191）改调它。
- **删除** issues.py 原 `_legacy_block_range` 独立副本（29 行算法 → 0；扫描不再有第二份）。

## 守卫更新（determinism-guards thinness 守）

- `ALLOWED_DISTINCT` 中 `("issues","_legacy_block_range")` **移除**，`ALLOWED_DISTINCT = set()`
  （放行注记改写为 dedup 收敛说明）。
- `_scan_legacy_block_range` **纳入 TWO_WAY_ROSTER**（新的扫描单一源）——issues 经显式 import
  暴露之，thinness 守正面核验 `issues._scan_legacy_block_range.__module__ == 'sdflow_issues_core'`。
- `issues.py` 显式 import 三符号：`_scan_legacy_block_range`（wrapper 调用）、`LegacyBlockError`
  （wrapper catch）、`_legacy_block_range`（re-export core 的中文 sibling，令 roster 既有条目亦解析到
  core；本文件不调）。
- `test_patch_discipline.py`：**无** `_legacy_block_range` allowlist 条目（其 allowlist 只管
  subprocess.run 补桩），无需改动。

## Minor-B / Minor-C

- **B**：`scan_pool_branches(source, filename=...)` 的 `filename` body 全程未引用；4 处调用各自已持
  源文件名（offenders 以 `path.name` 为键、mutation/prose 传字面 label）→ 删该参数 + 4 处调用去实参。
- **C**：mutation 测试注释「减去 clean 基线」与代码（仅 `assert findings`）不符 → 改写为「clean=0 由
  `test_core_has_no_pool_value_branches` 独立保证，故只需断言 findings 非空」。

## 错误文案不变的证据

- **英文（issues rename）**：新增 `test_rename_legacy_block_range_emits_exact_english_fix_text`
  直调 `_rename_legacy_block_range`，byte-exact 断言两分支全文（ambiguous + collision）。
- **中文（core）**：既有 `test_task3_frontmatter_writer.py::test_legacy_promotion_rejects_*`、
  `test_task4_rename_snapshot.py::test_pure_legacy_marker_collision_cli_...` 断言 `marker collision`
  / `id=` / `line=` 子串，全绿。
- CLI 零回归：rename preflight / set-status / add 路径全套件保持等价。

## 全套件输出

```
2110 passed, 9 skipped, 3 xfailed in 143.78s
```

（`/usr/bin/python3 -m pytest -q`，从仓根跑，EXIT=0；与 T4 后基线 2110 passed 一致。）

## diff 规模

`issues.py` +29 −30（删 29 行算法副本，加薄 wrapper + 3 import）· `sdflow_issues_core/__init__.py`
+47 −10（加 sentinel + scan + 薄格式化器）· `test_determinism_guards.py`（roster/allowlist/死参数/注释）·
`test_task4_rename_snapshot.py`（+29 锁测试）。共 5 文件（含本报告）。
