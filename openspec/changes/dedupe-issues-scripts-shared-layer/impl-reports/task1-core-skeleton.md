# impl-report — Task 1: 零回归基线 + core package 骨架 + 封闭 POOL_SPEC schema 与守卫

**R-ID:** SC-R2, SC-R3, DG-M1  |  **范畴:** FOUNDATION only（**不迁移任何 CLI 逻辑**）

## Seam 声明（守卫测试的公共接口边界）

TDD 在预定义 seam 上先红后绿。守卫测试 `sdflow-issues/tests/test_pool_spec_schema.py`
只依赖 `sdflow_issues_core` 的以下公共接口：

| 接口 | 类型 | 契约 |
|---|---|---|
| `sdflow_issues_core.PoolSpec` | frozen dataclass | 封闭 schema 类型；一个 pool 的全部差异维；无 `**kwargs`/dict 逃生口 |
| `sdflow_issues_core.POOL_SPEC` | `dict[str, PoolSpec]` | `{"bug": PoolSpec, "todo": PoolSpec}` |
| `sdflow_issues_core.POOL_SPEC_FIELDS` | `tuple[str, ...]` | **手写**差异维注册表（新增维必须两处同步的锚点） |
| `sdflow_issues_core.validate_pool_spec(spec=POOL_SPEC)` | `-> True \| raise` | 封闭性 + 关系正确性 fail-closed 校验，违规抛 `PoolSpecError` |
| `sdflow_issues_core.PoolSpecError` | `Exception` | 违规异常类型 |

红→绿证据：先建测试 → `pytest test_pool_spec_schema.py` = `ModuleNotFoundError: No module
named 'sdflow_issues_core'`（collection error，红）→ 实现 `__init__.py` → `15 passed`（绿）。

## 做了什么

1. **冻结零回归基线**（Task 0.1 / SC-R3）：`impl-reports/node-id-manifest.baseline.txt` —
   `/usr/bin/python3 -m pytest --collect-only -q`（仓根，pytest 8.4.2）冻结 **2093** 个
   pre-refactor node-id；头部注释显式标注 **7 个意图删除 node** =
   `sdflow-buglist/tests/test_mirror_consistency.py` 的 7 个测试（Task 4.1 删除时其消失不计回归）。
   `#` 开头为注释，其余为 node ID（Task 6.2 零回归门解析用）。

2. **唯一命名 package 骨架**（Task 1.1 / SC-R2）：`sdflow-issues/scripts/sdflow_issues_core/__init__.py`
   （**非**裸 `core.py`——避 `sys.modules["core"]` 碰撞）。`from sdflow_issues_core import ...`
   可解；薄入口 `sys.path.insert(0, dirname(__file__))` 后同目录 import（已用脚本模拟验证）。
   **本票未迁入任何 CLI 逻辑**——起步单 `__init__.py`，只承载 POOL_SPEC schema。

3. **封闭 POOL_SPEC schema**（Task 1.2 / SC-R2 / DG-M1）：`PoolSpec` = frozen dataclass，
   10 字段覆盖 design AD-3 表的 8 个 required 差异维；`POOL_SPEC_FIELDS` 手写注册表；
   import 时 `validate_pool_spec()` fail-closed 自校验。

4. **schema/关系守卫测试**（Task 4.3 的 schema 部分）：`test_pool_spec_schema.py`（15 用例），
   含 5 个 mutation 反红用例证明守卫非摆设。

## POOL_SPEC 维清单（PoolSpec 字段 → design AD-3 表 8 维映射）

| PoolSpec 字段 | 对应 required 维 | bug 值 | todo 值 |
|---|---|---|---|
| `date_granularity` | 文件粒度 | `"day"` | `"month"` |
| `file_stem` | 文件粒度（文件干/子目录叶） | `"buglist"` | `"todolist"` |
| `issues_dir` | 目录 | `openspec/issues/buglist` | `openspec/issues/todolist` |
| `legacy_dir_glob` | legacy dir glob | `openspec/buglists/*.md` | `openspec/todolists/*.md` |
| `specific_field` | 特定字段（字段名） | `"priority"` | `"type"` |
| `specific_values` | 特定字段（枚举，成对） | `{P0..P4}` | `{性能优化,可观测性,代码质量,功能增强,基础设施}` |
| `status_values` | 状态词表 | `{OPEN,VERIFIED,PROPOSED,IN_PROGRESS,FIXED,WONTFIX,BLOCKED}` | `{OPEN,PROPOSED,DONE,WONTDO}` |
| `terminal_set` | 终态集（⊆ 状态词表） | `{FIXED,WONTFIX}` | `{DONE,WONTDO}` |
| `default_prefix` | ID 前缀 | `"B"` | `"T"` |
| `scan_output_key` | scan 输出键 | `"bugs"` | `"items"` |

> `date_granularity` + `file_stem` 共同承载「文件粒度」一维（day/month + 文件名干），
> 均为独立 required 字段，缺任一即 schema 不完整。所有集合值用 `frozenset`（不可变）。

## RECORDER_POOL_CONFIG 对照结论

对照源 = `sdflow-issues/scripts/issues.py`（合并后幸存脚本）的 `RECORDER_POOL_CONFIG`
（`:73-78`）与 `TERMINAL_STATUSES`（`:1522-1525`）。守卫 `importlib.spec_from_file_location`
按文件加载 issues.py 取权威常量，逐值比对（**非只 non-None**）：

- `RECORDER_POOL_CONFIG[pool]` = `(specific_field, specific_values, status_values)` 三元
  → 与 `POOL_SPEC[pool].specific_field / specific_values / status_values` **逐值一致**（绿）。
- `TERMINAL_STATUSES[pool]` → 与 `POOL_SPEC[pool].terminal_set` **逐值一致**（绿）。
- 三脚本（buglist/todolist/issues）的 `RECORDER_POOL_CONFIG` 现值相同（pre-refactor 由
  `test_mirror_consistency.py::test_frontmatter_constant_consistency` 守 `BUG==TODO==ISS`）；
  取 issues.py 为对照源与另两份等价。
- 固定契约维（粒度/文件干/目录/legacy glob/前缀/scan 键）按 design AD-3 表钉死字面值断言。

> **迁移期语义**（CLAUDE.md 基准 2）：此对照把新 POOL_SPEC 钉在 pre-refactor 权威真相上，
> 是等价锚。将来 Task 2/4 若把 `RECORDER_POOL_CONFIG` 派生/移入 core，该对照测试由那批
> 任务同步演进——本票不动 issues.py 的 `RECORDER_POOL_CONFIG`。

## 跑了哪些测试（实际输出）

- 守卫测试（隔离）：`pytest sdflow-issues/tests/test_pool_spec_schema.py -q` → **`15 passed in 0.01s`**
- 红态证据（实现前）：`ModuleNotFoundError: No module named 'sdflow_issues_core'`（collection error）
- 全套件（仓根，SC-R3 零回归确认）：`pytest -q` → **`2098 passed, 8 skipped, 3 xfailed in 148.69s`**，exit 0
- node-id 差异核对（`--collect-only` vs baseline）：
  - baseline pure nodes = **2093**；current = **2109**
  - 差 16 = 我新增 15 个 `test_pool_spec_schema.py` node + 1 个既有 `test_patch_discipline.py`
    的参数化守卫自动覆盖新测试文件（`...[test_pool_spec_schema.py]`，通过——我的测试文件无
    `subprocess.run` 补桩，trivially 满足 gate A）
  - `comm` 双向 diff：**无 baseline node 消失、无其他意外新 node** → 零回归确认

## 验收标准逐条自评（**未勾框，由编排器双轴审后补打**）

- [x] 冻结 pre-refactor node-id manifest 作 allowlist 基线，标注 7 个意图删除 node
- [x] 唯一命名 package `sdflow_issues_core` 建立且 `from sdflow_issues_core import ...` 可解
- [x] `POOL_SPEC` 封闭 dataclass，含全部 8 required 维；新增维不改 schema 即报错
      （手写 `POOL_SPEC_FIELDS` 注册表 + 非派生，drift → import fail-closed，mutation 用例证实）
- [x] schema 守卫红于：缺 pool key / 额外 pool key / `terminal_set ⊄ 状态词表` / 非 PoolSpec 值 /
      注册表漂移；值与 `RECORDER_POOL_CONFIG`·`TERMINAL_STATUSES` 逐值一致

## Concerns

无阻断项。以下为交接给后续任务的边界说明（非本票缺陷）：

1. **本票 FOUNDATION 边界**：`sdflow_issues_core` 目前**只有** POOL_SPEC schema，未迁入任何
   共享 helper / 镜像逻辑（Task 1.3/1.4）、未重写 pool 分支（Task 1.5）、三薄入口未壳化
   （Task 2）。三个现存脚本（buglist/todolist/issues）**保持原状、行为不变**，全套件绿即证。
2. **`RECORDER_POOL_CONFIG` 对照测试的演进依赖**：`test_specific_field_and_enums_match_recorder_config`
   / `test_terminal_set_matches_recorder_terminal_statuses` 读 `issues.py` 的
   `RECORDER_POOL_CONFIG`/`TERMINAL_STATUSES`。当 Task 2/4 把这些常量移入/派生自 core 时，
   这两个测试的对照源需同步更新（属那批任务的守法切换范畴，本票不预改）。
3. **AST 无 pool 分支守未落**：DG-M1 的「core 无 pool 条件分支（AST 级 best-effort）」是
   Task 4.2 的守，本票范畴外——因 core 此刻尚无任何逻辑可扫。本票只落 POOL_SPEC **数据面**
   的封闭性/关系/值正确性守（fail-closed 充要）。
4. **解释器**：本机默认 `python3`（`~/.local/bin`）无 pytest；用 `/usr/bin/python3`
   （pytest 8.4.2）跑测试，满足仓根 `pytest.ini` 的 `minversion=8.0`。
