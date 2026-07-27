---
ship-gate:
  verify: PASS
  reviewed_sha: 91253fbd8f0ef8a54b89e0e29b3879d0dfbb237c
---

# `harden-sdflow-spec-followups` 验证报告

**结论：PASS**

- 日期：2026-07-27
- Change：`harden-sdflow-spec-followups`
- 被验证盘面：`91253fbd8f0ef8a54b89e0e29b3879d0dfbb237c`
- 验证口径：Do Not Trust the Report；逐条核对 delta、`tasks.md`、真实实现、测试与安装态。`tasks.md` 的勾选状态不作为完成证据。

## Delta requirements 逐条核对

| 需求 | 代码出处（文件:行 / 测试 / commit） | 状态 |
|---|---|---|
| FF-0 未判定路径不对错仓执法且留下非越权审计 | `sdflow-init/assets/hooks/ff0-branch-guard.py:85-106,212-230,249-279`；`sdflow-init/tests/test_ff0_branch_guard.py::test_direct_literal_variants_enter_the_protected_branch_guard`、`::test_non_direct_forms_emit_one_unverifiable_audit`、`::test_stacking_deny_precedes_cwd_ambiguity`；commit `b573c37f00073ff58cec9808bad6e1c781e05512` | ✅实现 |
| SA-01 单入口三相位与 Codex 诚实边界 | `sdflow-spec/SKILL.md:157-180,211-212`；`hack/tests/test_sdflow_spec_resident_contract.py::test_codex_claim_is_limited_to_observed_user_trigger`；commit `793f58309a88f175c0d16403a4f423c4e220d549` | ✅实现 |
| SA-06 终审以整个 change 目录追溯 | `sdflow-spec/SKILL.md:450-465`；`hack/tests/test_sdflow_spec_resident_contract.py::test_final_review_accepts_change_directory_traceability`；commit `793f58309a88f175c0d16403a4f423c4e220d549` | ✅实现 |
| SA-16 薄入口、按需 references 与 resident-contract 门 | `sdflow-spec/SKILL.md:171-180`（当前 Python Unicode 字符数 `16,972`）；`hack/tests/test_sdflow_spec_resident_contract.py:17-74,89-179`；`::test_entry_is_within_unicode_character_budget`、`::test_resident_contract_tokens_have_substantive_semantics`、`::test_three_on_demand_references_have_conditions_paths_and_content`；commits `793f58309a88f175c0d16403a4f423c4e220d549`、`564ae577ba7fc85868527e1b5e63b9eba79e9c30` | ✅实现 |
| SA-15 T132 A/B 输入契约分治且不实现 gate | `sdflow-spec/references/evolution-notes.md:19-29`；`hack/tests/test_harden_sdflow_spec_followup_closure.py::test_t132_remains_open_with_corrected_future_ab_contract`；台账 `openspec/issues/todolist/2026-07-todolist.md:94-104`（T132 OPEN、T239 PROPOSED）；commit `8875b5492228f1b8a0e9ab1b482713f49428f2b8` | ✅实现 |

## `tasks.md` 逐条核对

| 任务 | 机验证据锚 | 状态 |
|---|---|---|
| 1.1 单条 direct literal allowlist 与统一未判定审计 | `sdflow-init/assets/hooks/ff0-branch-guard.py:85-106,212-230,262-279`；focused 回归中的 `test_non_direct_forms_emit_one_unverifiable_audit`；commit `b573c37f00073ff58cec9808bad6e1c781e05512` | ✅实现 |
| 1.2 hook/canonical 回归矩阵 | `sdflow-init/tests/test_ff0_branch_guard.py:75-81,104-115,321-345,365-430`；`hack/tests/test_canonical_entry_sync.py::test_ff0_rule_and_sdflow_spec_entry_state_the_finite_grammar_boundary`；focused `496 passed` | ✅实现 |
| 1.3 canonical workflow 与入口文案 | `sdflow-init/assets/workflow/ff-generation-constraints.md:30-33`；`sdflow-spec/SKILL.md:287-291`；`hack/tests/test_canonical_entry_sync.py:305-313` | ✅实现 |
| 2.1 Codex 宿主证据边界 | `sdflow-spec/SKILL.md:211-212`；`hack/tests/test_sdflow_spec_resident_contract.py:159-163` | ✅实现 |
| 2.2 整个 change 目录追溯 | `sdflow-spec/SKILL.md:450-465`；`hack/tests/test_sdflow_spec_resident_contract.py:166-170` | ✅实现 |
| 2.3 T132/T234 A/B 契约订正、不实现 T132 | `sdflow-spec/references/evolution-notes.md:19-29`；`hack/tests/test_harden_sdflow_spec_followup_closure.py:254-266`；`openspec/issues/INDEX.md:334`（T132 OPEN） | ✅实现 |
| 2.4 未启用外派、诊断与演进依据按需外置 | `sdflow-spec/SKILL.md:171-180`；`sdflow-spec/references/delegation-protocol.md:1-60`；`sdflow-spec/references/degradation-ladder.md:1-83`；`sdflow-spec/references/evolution-notes.md:1-34`；`hack/tests/test_sdflow_spec_resident_contract.py::test_three_on_demand_references_have_conditions_paths_and_content` | ✅实现 |
| 2.5 字符预算与 resident-contract/reference 完整性门 | `hack/tests/test_sdflow_spec_resident_contract.py:17-74,89-179`；实测字符数 `16,972 <= 18,000`；focused `496 passed` | ✅实现 |
| 3.1 主规格与 closure matrix 台账同步 | `openspec/specs/spec-workflow/spec.md:1552-1572`；`openspec/specs/spec-authoring/spec.md:345-363`；`openspec/issues/todolist/2026-07-todolist.md:93-104`；`hack/tests/test_harden_sdflow_spec_followup_closure.py::test_archived_followup_is_done_only_with_real_artifact`、`::test_current_followup_is_done_only_with_implementation_evidence` | ✅实现 |
| 3.2 逐 ID 语义断言 | `hack/tests/test_harden_sdflow_spec_followup_closure.py:78-211,254-308`；`sdflow-issues/tests/test_task5_delivery_contract.py:151-163`；focused `496 passed` | ✅实现 |
| 4.1 focused pytest | 独立执行 `uv run --with pytest pytest -q`（FF-0、canonical、resident-contract、closure、init、outside-voice、issue projection 七组）：`496 passed in 108.03s`，无 skip/failure | ✅实现 |
| 4.2 通则同步、dogfood update、setup 与安装态 | 独立执行 `python3 hack/sync_principles.py --check`：`22` 个投放面一致；`python3 sdflow-init/scripts/init.py update --root . --dev` exit 0；`bash setup.sh` exit 0；`git diff --check` exit 0。安装态实测：Claude/Codex `sdflow-spec` symlink 均解析到本仓、`~/.sdflow/workflow` 解析到 canonical、FF-0 hook 与 outside-voice helper 字节一致、PreToolUse 注册存在。实现/回归锚：`sdflow-init/scripts/init.py:151-220`、`sdflow-init/tests/test_init.py:118-160,409-422`、`sdflow-init/assets/hack/outside-voice-job.py:422-445`、`sdflow-init/tests/test_outside_voice_job.py:392-417`；commits `310b0e283eb34f36897a1380343f370c7b97089f`、`656c5c164d304a6c36bec2bbbdf003ed3eb1a775` | ✅实现 |
| 4.3 全量 pytest | 独立执行 `uv run --with pytest pytest -q`：`2847 passed, 11 skipped, 3 xfailed in 283.68s`，exit 0。11 个条件 skip 与 3 个预期 xfail 不在上述 focused 验收集合；focused 集无 skip | ✅实现 |

## 缺口清单

### 核心缺口

无。

### Minor 缺口（可接受 / deferred）

- `T243` 保持 OPEN：`hack/tests/test_sdflow_spec_resident_contract.py` 的 reference 路由断言把非空链接标签格式收得过窄（台账锚：`openspec/issues/INDEX.md:358`）。当前 versioned reference 的加载条件、相对路径与实质内容均已由测试覆盖，故这是测试可维护性改进，不缺失 SA-16 目标能力，不阻断本 change。
- `update --dev` 会在 dogfood instance 生成 40 个未跟踪的完整 workflow bundle 文件；本次验证后已精确移除这些由验证命令生成的文件，最终工作树除本报告外无其它变更。该行为与 `--dev` 的“整刷 instance”契约一致，不属于交付缺口。

## 实际执行的验证命令

```text
openspec validate harden-sdflow-spec-followups --strict --type change
  -> Change 'harden-sdflow-spec-followups' is valid

uv run --with pytest pytest -q <七组 focused files>
  -> 496 passed in 108.03s

python3 hack/sync_principles.py --check
  -> 22 个投放面全部与真相源一致

python3 sdflow-init/scripts/init.py update --root . --dev
  -> exit 0；65 文件整刷；hook 已最新并已注册

bash setup.sh
  -> exit 0；Claude/Codex skills、agents、workflow、hack helpers 安装刷新成功

git diff --check
  -> exit 0

uv run --with pytest pytest -q
  -> 2847 passed, 11 skipped, 3 xfailed in 283.68s
```

PASS
