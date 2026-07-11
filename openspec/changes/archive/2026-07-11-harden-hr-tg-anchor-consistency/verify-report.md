---
ship-gate:
  verify: PASS
---

# Verify Report — harden-hr-tg-anchor-consistency

日期：2026-07-11 · change：`harden-hr-tg-anchor-consistency`

**结论：PASS**

Do-Not-Trust 冷核：不信复选框/既有报告，每条 ✅ 均附机验锚点（测试名 / 文件:行）。
全套件 `python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -v` → **235 passed**。

## 逐需求核对表

### R1 出锚侧 hr_tg_intersect（§1 / M3 + M-new）

| 需求/任务 | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| 1.1 parse_tg_set 删静默过滤，空 cell/前后/连续逗号→EmitError；仅空串表空集 | `hr_tg_intersect.py:131-143`；`test_tg_set_empty_cell_fail_closed`、`test_tg_set_empty_string_is_empty_set` | ✅ |
| 1.2 成员抽取词边界严格，`TG-04x`→EmitError，不宽松正规化 | `_parse_member_tokens:58-70`（`_TG_STRICT_RE` fullmatch）；`test_member_strict_token_rejects_malformed`、`test_malformed_tg_token_fail_closed` | ✅ |
| 1.3 M-new catalog 全 TG 集解析，declared/hit 每 TG ∈ 全集，`TG-99`/`TG-1`→EmitError | `load_all_tg_set:105-128` + `main:185-188`；`test_mnew_token_fullmatch_rejects_residue`、CLI 存在性测试 | ✅ |
| 1.4 pytest 覆盖畸形/空串/不存在 TG | `test_hr_tg_intersect.py`（多条，见上）| ✅ |
| F5 single_source_mutability 重设计（全集内非 HR-TG 成员证行为变化） | `test_single_source_mutability:102` | ✅ |
| F7 catalog 内部一致 HR-TG ⊆ 全集，越界→fail-closed | `load_hr_tg_subset:99-101`；`test_f7_hr_tg_must_subset_full_set` | ✅ |
| F8 全集只取 `## 三` 段表行 + token fullmatch 拒残留（`TG-04.0`） | `load_all_tg_set` + `_TABLE_TG_RE:21`；`test_mnew_token_fullmatch_rejects_residue` | ✅ |
| fence-aware 段/成员/表行解析先剔围栏 | `fence_outside_lines:30-44`，各 loader 先过滤 | ✅ |
| 段定位 fail-closed（恰 1，歧义 raise） | `_locate_unique_h12:47-55` | ✅ |

### R2 校验侧 anchor_lint（§2 / M1+M2+M4+M-new + 必需 catalog）

| 需求/任务 | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| 2.1 `--trigger-catalog` 必需（argparse required），缺→fail-closed exit2，不 WARN | `main:438-439`、`:463-469`；`test_anchor_lint_missing_catalog_fail_closed` | ✅ |
| 2.2 M1 declared= 硬必填，缺→`missing-field`，无 grace/`--allow-legacy` | `HR_TG_REQUIRED_FIELDS:174` + `check_hr_tg:347-349`；`test_hr_tg_missing_declared_violation`、`test_hr_tg_missing_declared_exit1` | ✅ |
| 2.3 M2 重算 declared∩HR-TG 逐元素同序，不一致→`hit-declared-mismatch` | `check_hr_tg:391-396`；`test_m2_hit_recompute_mismatch_violation` | ✅ |
| 2.4 M4 hit≠none ⟹ evidence= strip 后非空 | `check_hr_tg:397-400`；`test_m4_evidence_missing_when_hit`、`test_m4_evidence_present_when_hit_ok` | ✅ |
| 2.5 M-new declared/hit 每 TG ∈ catalog 全集 | `check_hr_tg:367-369`、`:386-388`；`test_mnew_lint_tg_not_in_catalog`、`test_mnew_lint_hit_tg_not_in_catalog` | ✅ |
| 2.6 诚实边界 docstring（M2 非 tamper-proof、declared 正确性属语义残余） | `check_hr_tg` docstring `:329-333` | ✅ |
| 2.7 测试反转：`hit="whatever"` 应违规（非旧 `[]`） | `test_hr_tg_malformed_csv_collect_not_raise:207-213` | ✅ |
| 2.8 SKILL 接线补 `--trigger-catalog` | `sdflow-spec-review/SKILL.md:78`、`sdflow-code-review/SKILL.md:127` | ✅ |
| 2.9 pytest 全覆盖（无 catalog/缺 declared/M2/M4/M-new + 诚实负例） | `test_anchor_lint.py` 多条 | ✅ |

### §3 冷层 fold（spec-review-amendment F1/F2/F3/F9 等）

| 需求/任务 | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| F1 sentinel：`declared="none"`/`hit=""`→违规 | `check_hr_tg:359-360`、`:376-377`；`test_f1_declared_none_literal_is_violation`、`test_f1_hit_empty_string_is_violation` | ✅ |
| F2 整行严格解析拒重复键 + 未闭合 + 残留 | `parse_kv_strict:92-103` + `_HR_TG_ANCHOR_FULL_RE:294` + `check_hr_tg:339-346`；`test_f2_duplicate_key_violation`、`test_parse_kv_strict_detects_dup` | ✅ |
| F3 跨文件一致性 golden（emit hit ⟺ lint 重算逐元素等 + numeric 同序） | `test_hr_tg_cross_tool.py`（3 断言线、参数化）| ✅ |
| F-E numeric 序 + 重复元素独立 violation | `_check_order_and_dup:306-314`；`test_fe_hit_duplicate_violation`、`test_fe_normal_canonical_order_ok` | ✅ |
| F-F declared/hit 侧独立收集，一侧畸形不吞另一侧 | `check_hr_tg:354-389`；`test_ff_declared_and_hit_violations_both_collected_independently` | ✅ |
| F9 collect-not-raise（畸形转 violation dict，不 raise、stdout 仍合法 JSON） | `check_hr_tg:364-365`、`:383-384`；`test_hr_tg_malformed_csv_collect_not_raise` | ✅ |
| F-C fence-aware catalog 解析 | `test_fc_fence_aware_catalog_parsing_anchor_lint` | ✅ |
| F6 缺参撞码假绿防护（断言 stderr/reason 码非只 returncode） | `test_missing_report_error_exit2`、`test_catalog_bad_exit2_reason` | ✅ |
| F12 docs 同步 anchor_lint 调用串补 `--trigger-catalog` | `docs/workflow-skills/sdflow-code-review.md:74`（全命令串含 catalog）| ⚠️ Minor |

### §4 bundle 回灌 + delta

| 需求/任务 | 核验 | 状态 |
|---|---|---|
| 两工具落权威源 + canonical 同步（下游一致） | `diff` 两文件 → **IDENTICAL**（权威源 `sdflow-init/assets/…` == 下游 `openspec/workflow/tools/…`） | ✅ |
| delta spec:550 回灌 3 字段 canonical | delta `specs/spec-workflow/spec.md:7`：锚行 SHALL `hit="…|none" declared="…" evidence="…"`，declared= canonical、hit≠none 时 evidence 非空 | ✅ |
| S1 诚实边界负例在场（M2 未加强成 tamper-proof） | `test_m2_consistent_but_wrong_still_passes:223-227` 断言 `hit="none" declared=""` → `== []`（过）| ✅ |

## 缺口清单

**核心缺口（FAIL）**：无。

**Minor 缺口（可接受）**：
- F12：`docs/workflow-map.md` 与 `docs/workflow-skills/sdflow-spec-review.md` 中的 anchor_lint 引用为 prose 简写（`--layer spec-review`），非可复制的完整命令串，未逐处补 `--trigger-catalog`。运行时真相源（两个 SKILL.md）与 `sdflow-code-review.md` 的完整命令串均已含 `--trigger-catalog`；此为 view-only 文档的简写，不影响行为，判可接受。

PASS
