# 实现验收对账 · lens-metric-emit（Task 8 收尾）

> SDD 8 Task 实现完成后的验收对账。非四件套产物（不参与设计门新鲜度）。

## 测试全绿
- `pytest sdflow-init/` → **223 passed**
- `pytest -W error sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py` → **31 passed, 0 warning**
- `pytest sdflow-init/tests/test_init_contract_sync.py` → 1 passed（契约新增 fold 块无 drift）

## dogfood 端到端（经全局 bundle 路径）
- `bash setup.sh` → `~/.sdflow/workflow` 重指本 dev checkout（dogfood；**ship 收尾还原运行 checkout**）
- `python3 ~/.sdflow/workflow/tools/lens_metric_emit.py --layer spec-review --input …/fixtures/lens_metric_input.json` → **exit 0，6 行合规锚**
- emitter 输出过 `check_lens_metric` → **CLEAN**（ADR-4 产出↔校验闭环坐实）

## specs ↔ 测试锚点对账

| Requirement / Scenario | 测试锚点 | 类型 |
|---|---|---|
| R1 结构化归约出合规锚与计数 | test_reduce_single_accepted / test_golden_fixture | 机械 |
| R1 共抓每命中行各记但不计独立 | test_reduce_coreport_no_independent | 机械 |
| R1 同类型多实例折叠同行仍独立 | test_reduce_same_type_multi_instance | 机械 |
| R1 折叠恒等 pass-through + 非恒等映射 | test_fold_hit_identity/nonidentity/unknown | 机械 |
| R1 零-finding 行落全零行 | test_reduce_single_accepted（ov 全零断言） | 机械 |
| R1 finding 命中行∉roster fail-closed（C4） | test_reduce_finding_lens_not_in_roster | 机械 |
| R1 metrics 开强制 broad/outside-voice 行 | test_reduce_roster_missing_mandatory | 机械 |
| R2 越域枚举非零退出 | test_reduce_bad_verdict/layer + test_cli_bad_json | 机械 |
| R2 present-but-empty（hits:[]） | test_reduce_empty_hits | 机械 |
| R2 采纳缺 sev 条件必填 | test_reduce_accepted_missing_sev | 机械 |
| R2 site 注入 fail-closed | test_fold_hit_site_injection | 机械 |
| R2 all-or-nothing 不产部分锚 | test_cli_partial_fail_no_partial_anchor | 机械 |
| R2 roster/fold 重复键 fail-closed（C14） | test_reduce_roster_dup_key / test_load_fold_dup_key | 机械 |
| R2 契约枚举/折叠单一源读取 + codomain 自校验 | test_load_fold_codomain_out_of_enum / test_fold_codomain_subset | 机械 |
| R3 emitter 输出过 check_lens_metric | test_emit_then_check_lens_metric_clean | 机械 |
| R3 load_enums 等价性 | test_load_enums_equivalence | 机械 |
| R3 残余信任边界诚实声明 | design ADR-3 / spec R3 prose + SKILL 声明 | **文档保留** |
| workflow-metrics 计数机械化 | test_reduce_* + test_min_lens_rows_matches | 机械 |
| workflow-metrics 分类正确性为残余边界（C19 诚实账） | design Risks / spec prose | **文档保留** |

**单一源守卫**（C3/C10/C17/C23）：test_fold_codomain_subset_lens_enum / test_load_enums_equivalence / test_min_lens_rows_matches_anchor_lint / test_aggregator_enum_matches_contract —— 四方（emitter/anchor_lint/aggregator/契约）一致、无漂移。

## 结论
所有机械可验 Scenario 均有 pytest 锚点；文档保留类（残余信任边界诚实声明、C19 诚实账）为设计意图声明、非 pytest（X2：不当 verify 假绿）。无 Scenario 声称覆盖却缺锚点。
