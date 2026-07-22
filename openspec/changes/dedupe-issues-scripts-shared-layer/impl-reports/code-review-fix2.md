# code-review-fix2 — dedupe-issues-scripts-shared-layer 冷代码审 hr-tg voice 两洞修复

标记：所有改动处标 `[impl-review-fix]`。未动 proposal/design/specs/tasks，未勾复选框/打完成标签。

---

## V2·中 — `validate_pool_spec` fail-closed 补漏 + 外部锚补字段

### 1. validator 补 fail-closed（core `sdflow_issues_core/__init__.py`，loop 内）

保持既有断言（keys 恰为 {bug,todo}、注册表 vs schema、isinstance PoolSpec、terminal_set⊆status）不动，
在 `for pool, value in spec.items()` 循环内增补以下逐条 raise `PoolSpecError`（带可诊断消息）：

| 新增断言 | 堵的 fail-open 洞 |
|---|---|
| `value.pool == pool` | 实例装错桶（key 与内嵌 pool 身份漂移） |
| `issues_dir` / `file_stem` / `default_prefix` / `legacy_dir_glob` / `specific_field` **非空串** | 空目录/空前缀静默落错位置 |
| `specific_values` / `status_values` / `terminal_set` **非空集** | 空枚举令一切值合法或一切非法 |

### 2. 外部锚补字段（test `test_pool_spec_schema.py`）

新增 `EXPECTED_ENUMS` 字面锚（design AD-3 表取值，与现 POOL_SPEC 核对无误），补齐此前
EXPECTED_CONTRACT 漏掉、且 T2 后逐值对照已成 tautology（RECORDER_POOL_CONFIG 派生自 POOL_SPEC）
的字段——**这是这些值正确性的唯一真外部锚**：

```
bug : pool=bug,  requires_block=True,  specific_values={P0,P1,P2,P3,P4},
      status={OPEN,VERIFIED,PROPOSED,IN_PROGRESS,FIXED,WONTFIX,BLOCKED}, terminal={FIXED,WONTFIX}
todo: pool=todo, requires_block=False, specific_values={性能优化,代码质量,功能增强,基础设施,可观测性},
      status={OPEN,PROPOSED,DONE,WONTDO}, terminal={DONE,WONTDO}
```

新增断言测试：
- `test_pool_identity_and_flag_match_design_table` — pool/requires_block 用相等。
- `test_enums_match_external_design_table` — 枚举/状态/终态用集合比较。

Mutation 反红（证 validator 对新洞有效）：
- `test_validate_reds_on_pool_identity_mismatch` — `pool="todo"` 塞进 bug 桶 → 反红。
- `test_validate_reds_on_empty_string_dim` — `issues_dir=""` → 反红。
- `test_validate_reds_on_empty_collection_dim` — `specific_values=frozenset()` → 反红。

现状 POOL_SPEC 满足全部新断言，正例 `test_validate_pool_spec_passes_on_canonical` 仍绿。

---

## V3·中 — `specific_values` 双真相源 → **选：单一源化**

**选单一源化，非一致性守卫 test。**

**理由**：CLAUDE.md 分析基准 1「一致性机械化优先 / 单一源」——结构上消除漂移 >> 事后检测漂移。
任务给的首选形（`POOL_SPEC.specific_values` 由 `strategy.specific_values_ordered` 派生）**结构上被阻断**：
POOL_SPEC 定义在 :104（RECORDER_POOL_CONFIG 于 :229 即依赖它、core 全程用），而两 STRATEGY 定义在
:1838+（依赖大量后置函数），无法前移让 POOL_SPEC 引用。∴ 采**共用上游有序 tuple 常量**这一等价单一源形：

在 POOL_SPEC 之前引入：
```python
BUG_SPECIFIC_VALUES_ORDERED  = ("P0", "P1", "P2", "P3", "P4")
TODO_SPECIFIC_VALUES_ORDERED = ("性能优化", "可观测性", "代码质量", "功能增强", "基础设施")
```
- `POOL_SPEC["bug"].specific_values = frozenset(BUG_SPECIFIC_VALUES_ORDERED)`（todo 同）——集合从有序源派生。
- `BUG_STRATEGY.specific_values_ordered = BUG_SPECIFIC_VALUES_ORDERED`（todo 同）——有序源即常量本体。

有序 tuple 为唯一源（frozenset 无序、给人看的提示需有序，∴ tuple 承源）。cmd_add:1928 判合法用
`spec.specific_values`、:1930 提示用 `strat.specific_values_ordered`，二者现同源派生，**结构上不可能
「add 收但 lint 拒 / 提示与规则不一致」**。`issues.py:56 PRIORITIES` 亦经 strategy 间接共用同源。

守此接线不被后续改回双源：`test_specific_values_single_source_no_drift` 断言二者 `is` 同一常量 +
POOL_SPEC 集合 == `frozenset(常量)`。

---

## 等价 oracle：全套件

```
/usr/bin/python3 -m pytest -q   （仓根）
2143 passed, 8 skipped, 3 xfailed in 149.31s
```
基线 2137 → 2143（+6 新测试）。无值变更，现状全绿。
targeted：`test_pool_spec_schema.py` 21 passed。
