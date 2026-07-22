# impl-report — Task 4: determinism-guards 守法切换（镜像守退役 → 单一源新守法）

**R-ID:** DG-M1, DG-M2 | **状态:** DONE_WITH_CONCERNS（2 条已知代价，非阻断，见 §7）

## 1. 前序验证（4.1 / 4.3）

### 4.1 镜像守已删、无孤立 roster 残留 —— 已验证 ✅
- `find . -name test_mirror_consistency.py` → 无（T2 已删）。
- 全仓（排除 `archive/`）grep `test_mirror_consistency|THREE_WAY|TWO_WAY` → **唯一命中**是
  `sdflow_issues_core/__init__.py:274` 的一句注释（"# THREE_WAY 共享 helper…"），非对已删 roster
  测试的 import/引用。无孤立 roster。

### 4.3 POOL_SPEC 封闭 schema + 关系守已建、现状诚实 —— 已验证 ✅（并补诚实注记）
`test_pool_spec_schema.py`（15 用例，全绿）覆盖题面点名的三条：
- **keys≠{bug,todo}**：`test_pool_spec_keys_fail_closed` + `test_validate_reds_on_extra_pool_key`
  + `test_validate_reds_on_missing_pool_key`。
- **terminal⊄status**：`test_terminal_subset_of_status` + `test_validate_reds_on_terminal_not_subset`。
- **缺 required 维**：`test_required_dims_all_present` + `test_field_registry_matches_dataclass`
  + `test_validate_reds_on_registry_drift`（注册表漂移 fail-closed）。

**诚实现状确认（题面要求）**：T2 已把 `RECORDER_POOL_CONFIG` / `TERMINAL_STATUSES` 改为
**从 POOL_SPEC 派生**（core `__init__.py:227-233`）。故该文件里
`test_specific_field_and_enums_match_recorder_config` / `test_terminal_set_matches_recorder_terminal_statuses`
现为 **POOL_SPEC 自比其派生物 = 同源**——守「派生接线正确」而非「独立漂移捕获」（护力对「值填错」
为零）。**值正确性的真外部锚全在 `EXPECTED_CONTRACT`**（design AD-3 表字面，`test_fixed_contract_dims_match_design_table`）
+ `test_required_dims_all_present`——独立于 POOL_SPEC 的 design-table 常量，改错值即红。
我把此诚实边界**补写进该文件模块 docstring**（不改任何断言，同源检仍作派生完整性守保留），
以免它 overclaim「对照三脚本权威常量抓漂移」。

## 2. AST 无 pool 分支守（4.2）—— 新建 `test_determinism_guards.py`

**实现**：`scan_pool_branches(source)` 走 `ast.parse` → `ast.walk`，拦两类节点：
- `ast.Compare`（覆盖 `If`/`IfExp`/`while` 的 test——其 test 即嵌套 Compare 节点 + 裸比较）：
  任一操作数是**裸** pool 常量 `"bug"`/`"todo"` 且另一侧**不是整集** `{"bug","todo"}` → 拦。
- `ast.Match`（Python ≥3.10；`getattr(ast,"Match",None)` 版本安全）：`case "bug"`/`case "todo"` → 拦。

**放行**（AD-3 明确允许，机械区分）：
- 封闭 schema keys 断言 `set(spec) != {"bug","todo"}`——右操作数是**整集 Set**（`_is_full_pool_collection`），
  非裸单值，自动豁免。
- `POOL_SPEC = {"bug":…, "todo":…}` 数据字典、`for pool in ("bug","todo")`——非 Compare/Match 操作数。
- 注释 / docstring——不在 Compare/Match 节点内，AST 结构上不可见。

**只扫 core `.py`（基准 5 + gate 子串自指坑）**：`scan_pool_branches` 只喂 `CORE_DIR.glob("*.py")` 的源；
且它走 `ast.parse`——喂 prose/.md 会 `SyntaxError` 拒解析（`test_scanner_does_not_scan_prose` 机械证之），
**结构上不可能把文档当代码扫**（对比字面子串扫会假阳）。

**mutation 反证输出**（`test_scanner_reds_on_injected_pool_branches_mutation`，全绿）——往 core 源注入
五形态、逐一断言被捕获：
```
别名 ==          : if expected_pool == "bug":        → 捕获 ✅（题面必反红项）
subscript ==     : if document["pool"] == "bug":     → 捕获 ✅（题面必反红项）
三元 IfExp.test  : x = "bugs" if pool == "bug" ...   → 捕获 ✅
!= 裸常量        : if pool != "todo":                → 捕获 ✅
match case       : match pool: case "bug":           → 捕获 ✅（仅 Py≥3.10 跑；3.9 下 match 连 parse
                                                        都 SyntaxError，core 里结构上不可能）
```
`test_core_has_no_pool_value_branches`：干净 core（`__init__.py`）扫描 → **0 finding**，绿。

**诚实边界声明落点**：`test_determinism_guards.py` 模块 docstring 明写「此 AST 守是 **best-effort 代理、
非 fail-closed 充要保证**」；结构够不着的残余（dict-dispatch `{"bug":f,"todo":g}[pool]` 无法与合法数据
注册表 `POOL_SPEC`/`RECORDER_POOL_CONFIG` 机械区分）显式登记；「真正不变量由 AD-3 的 POOL_SPEC 封闭
schema 正面保证，本守只作辅助层，不 overclaim 机械充要」逐字写入。

## 3. 薄入口 thinness 同一性守（4.4）

**实现**：roster = THREE_WAY(37) + TWO_WAY(24) = **61**（逐字取自 T2 impl-report §2）。对
`buglist`/`todolist`/`issues` 三薄入口 × 61 helper：从薄入口 `getattr` 取对象，
断言 `__module__ == 'sdflow_issues_core'`（`test_thin_entry_does_not_shadow_core_helper`，参数化 3 入口，全绿）。

**分支处理**（护力真实、可 fail）：
- `__module__==core` → PASS（import 未改）；未在薄入口暴露（多为 underscore helper，`import *` 不带）
  → 未 shadow，跳过。
- **ALLOWED_POOL_BOUND**（`next_id`/`all_ids` × buglist/todolist，共 4 项）：T2 §5 的 pool-bound leaf 薄封装
  （绑定本池 spec 后暴露 root-only 签名供 tests 直调）。守卫对它们改验「**确为薄委派**」——AST 证 body 调
  `_core.<name>(...)`（`_wrapper_delegates_to_core`），若被换成重实现即红。
- **ALLOWED_DISTINCT**（`issues._legacy_block_range`，1 项）：见 §7 Concern-A（documented 已知近重复）。

**mutation 反证**：`test_thinness_identity_guard_reds_on_shadow` 把 `issues.canonical_id` 换成本地重实现，
断言 `__module__ != core` 且不在任何白名单 → 守卫会红。`test_allowlists_are_subset_of_roster` 防白名单
死配置/拼写错。

## 4. golden 诚实降级（4.5）

`test_direct_snapshot_matches_recorder_scan_contract_for_all_shapes_and_pools`（test_task4_rename_snapshot.py:582）
是 direct rename snapshot vs 薄入口 `scan --json` 的 golden。**该测试本体无 overclaim 断言可删**
（它只 `assert direct["items"] == expected`），降级动作 = **补写诚实 docstring 明确其守护语义**：

| 降级前 | 降级后（新 docstring） |
|---|---|
| 无 docstring；语义靠 spec 旧 Scenario 承载「任一方漏 rule → 失败」 | 明写「**同源两 code-path 的接线正确性守**（非 rule-omission 守）」 |
| — | 「两方跑同一 core parser（core 是 rule 单一源）⇒『一方漏 rule』结构上不可能、自比自己=tautology、**不再宣称抓 rule 遗漏**」 |
| — | 「守的是 envelope 组装/字段投影（`{**found,"pool":pool}`）逐字段一致=接线没接错；若要真 rule-完整性守须 core-parse vs **外部 golden fixture**」 |

## 5. 迁移守继续绿（4.6 / 4.7）

- **4.6** `validate_scan_envelope` fail-closed（test_task4_rename_snapshot.py 的 6 个
  `test_validate_scan_envelope_*`）+ `config.yaml` lint（sdflow-init/tests/test_config_lint.py）
  + `batches.md` lint（test_batch_lint.py）——全绿，不受本票影响。
- **4.7** 三薄入口经同目录 package `from sdflow_issues_core import`、无跨目录 import / sys.path 污染——
  由既有 `test_task5_delivery_contract.py::test_recorders_stay_self_contained_without_yaml_or_cross_skill_imports`
  守（AST 断三入口 import 名里除 `sdflow_issues_core` 外无 `sdflow_*`/`yaml`），绿。本票 thinness 守
  是其补充（同一性维度）。

## 6. 全套件输出

```
/usr/bin/python3 -m pytest -q   （仓根，pytest 8.4.2，Python 3.9.6）
2110 passed, 8 skipped, 3 xfailed in 148.53s   exit 0
```
T2 基线 2100 passed；本票净 +10（新 `test_determinism_guards.py` 9 用例：AST 守 4 + thinness 参数化 3
+ mutation/白名单 2；另 golden docstring 不新增 node）。无 FAILED、无因本票导致的 skip。

## 7. Concerns（2 条已知代价，非阻断——供双轴审裁）

### A. `issues._legacy_block_range` 同名近重复（thinness ALLOWED_DISTINCT）
issues.py 有一个**同名但语义相异**的 `_legacy_block_range(document, raw_id)`（2 参、读 `document['path']`、
抛 rename-path 专属 fix 文案「rerun the original batch rename command」，与 issues 批量改名错误族一致），
用于 issues **独占的 batch-rename 快照机制**（`_body_with_legacy_bug_markers`/`_reject_target_document_problems`
调用）——**非** pool CLI 路径对 core helper 的 shadow。其结构逻辑与 core 版
`_legacy_block_range(document, raw_id, path)`（3 参、`_frontmatter_error`）**近似**（找唯一 legacy block
+ 拒 marker 撞），属**已知近重复**。
- **为何 Task 4 放行而非当场 fold**：合并进 core 需把 rename 专属错误文案**注入 core**（caller-specific
  污染 core）或 catch-rewrap core 的 ValueError（脆）——属 **Task 2 单一源范畴 + 非低成本 fold**（基准 4
  的「唯一合理 defer」判据不完全适用，但 fold 代价确实压过收益）。故 thinness 守 **documented 放行 +
  本 Concern 登记**（对比 test_patch_discipline 的 allowlist-with-reason 惯例），未静默埋掉。
- **建议**：随 AD-7 的 god-module 拆子模块（rename 机制归 `ledger`/`rename` 子模块）时一并整合，
  或单记一条 todo。**本票未记 todo**（7.x 非本票 R-ID，避 recorder-add 误挂 change）——请编排层裁定是否
  正式登记。

### B. specs/determinism-guards/spec.md 内部两 Scenario 相互矛盾（spec 级，非我可改）
delta 同时含：
- `Scenario: direct↔scan golden 不再宣称抓 rule 遗漏`（:32-35，R6 降级后的新场景）；
- `Scenario: direct snapshot 与 scan 语义漂移`（:42-45），其 THEN 仍写
  **「任一方漏掉 lexical/marker/overlay/ID rule 时测试失败」**——**正是 R6/上一场景要删的宣称**。

二者直接冲突，疑似 amendment 加了新场景却漏删旧场景。**我 MUST NOT 改 specs**（本票约束），
故未动；但该 delta archive 时会同步进主 spec，矛盾会传播。**请编排层/设计门决定**是否删 :42-45 旧场景
（我的 golden test docstring 已按 R6 降级语义落地，与 :32-35 一致）。

## 8. 落点清单
- 新增 `sdflow-issues/tests/test_determinism_guards.py`（AST 守 + mutation + thinness 守）。
- 改 `sdflow-issues/tests/test_task4_rename_snapshot.py`：golden 降级 docstring（:582）。
- 改 `sdflow-issues/tests/test_pool_spec_schema.py`：模块 docstring 诚实注记（同源派生检 vs 外部锚）。
- **未打完成标签、未勾 superpowers-plan.md、未改 proposal/design/specs/tasks**（本票约束）。
