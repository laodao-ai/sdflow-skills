---
ship-gate:
  verify: PASS
  reviewed_sha: dc67af388a471acbe36d95a83ac7eab65948c304
---

# Verify Report · align-sdflow-spec-with-openspec-schema

日期：2026-07-31

## 结论

**PASS（含 2 项 Minor/过程证据缺口及 1 项用户批准的测试例外）**。

核心 schema、迁移、bundle 下发与 Phase C 载荷契约已在当前盘面独立核验。当前定向聚合为
`127 passed, 1 skipped`，真实 CLI 的 schema validate、change status、specs instructions、tasks
instructions 均退出 `0`，`openspec validate align-sdflow-spec-with-openspec-schema --strict` 退出 `0`。
全量 `pytest` 此前 90 秒超时退出 `124`，按用户明确批准停止等待并跳过；它**未通过，也未被记为绿色**。

## 逐任务核对

| 任务 | 代码 / 测试 / commit 证据锚 | 状态 |
|---|---|---|
| 1.1 fork schema | `sdflow-init/assets/schemas/sdflow-spec-driven/schema.yaml:1`；实现 checkpoint `916b203` | ✅ 实现 |
| 1.2 四产物委派区块 | `schema.yaml:10`、`:67`、`:236`、`:290`；`test_task5_schema_content_contract` | ✅ 实现 |
| 1.3 requires 两条边 | `schema.yaml:228-230`、`:346-349`；当前 `openspec schema validate sdflow-spec-driven` exit 0 | ✅ 实现 |
| 1.4 design 无条件 | `schema.yaml:240-242` | ✅ 实现 |
| 1.5 id/generates 保持兼容 | `schema.yaml:5-6`、`:62-63`、`:231-232`、`:285-286`；`test_task5_schema_content_contract` | ✅ 实现 |
| 1.6 schema validate | 当前真实 CLI：`openspec schema validate sdflow-spec-driven` exit 0 | ✅ 实现 |
| 2.1 CLI 数值版本门与 fail-closed | `sdflow-init/scripts/init.py:461-481`；`test_old_cli_does_not_deploy_schema_or_switch_config`、`test_semver_numeric_gate_accepts_1_10`、`test_missing_or_non_numeric_cli_fails_closed` | ✅ 实现 |
| 2.2 仅迁移在途 change、幂等 | `init.py:484-507`；`test_migration_only_in_progress_and_idempotent`、`test_stray_directory_without_proposal_is_ignored` | ✅ 实现 |
| 2.3 先补写后切 config、失败中止 | `init.py:1040-1050`、`:1069`；`test_migration_failure_stops_before_schema_and_config_switch`、`test_task5_migration_runs_before_config_switch` | ✅ 实现 |
| 2.4 managed fork 整删重拷 | `init.py:261-270`；`test_schema_bundle_prunes_orphans`、`test_schema_bundle_preserves_sibling_schemas` | ✅ 实现 |
| 2.5 config template 指向 fork | `sdflow-init/assets/workflow/config.template.yaml:17` | ✅ 实现 |
| 2.6 两项结论进汇总 | `init.py:1037-1048` | ✅ 实现 |
| 2.7 update 窄改 schema | `init.py:386-424`、`:441-458`；`test_update_changes_only_schema_line`、`test_update_rewrites_bom_crlf_schema_once_and_preserves_other_bytes`、`test_update_inserts_schema_after_yaml_directives_and_document_start` | ✅ 实现 |
| 3.1 委派段先剥离 | `sdflow-spec/SKILL.md:438-439`；`test_phase_c_strips_delegation_before_applying_instruction` | ✅ 实现 |
| 3.2 无标记 no-op / 畸形 fail-closed | `sdflow-spec/SKILL.md:439`；`test_phase_c_strips_delegation_before_applying_instruction` | ✅ 实现 |
| 3.3 glob 与 existingOutputPaths | `sdflow-spec/SKILL.md:440`；`test_phase_c_handles_glob_existing_outputs_and_skipped_status` | ✅ 实现 |
| 3.4 对具体路径净化 | `sdflow-spec/SKILL.md:442-446`；`test_phase_c_handles_glob_existing_outputs_and_skipped_status` | ✅ 实现 |
| 3.5 skipped 不创建文件 | `sdflow-spec/SKILL.md:441`；`test_phase_c_handles_glob_existing_outputs_and_skipped_status` | ✅ 实现 |
| 3.6 requires 优先、图不足 fallback | `sdflow-spec/SKILL.md:412-423`；`test_phase_c_consumes_dependency_objects_and_has_schema_fallback` | ✅ 实现 |
| 3.7 dependencies 对象列表断言 | `sdflow-spec/SKILL.md:431-437`；`test_phase_c_consumes_dependency_objects_and_has_schema_fallback` | ✅ 实现 |
| 3.8 终审措辞降级 | `sdflow-spec/SKILL.md:468-474` 已写“判断层兜底”，但未明写“schema 已切换”前提 | ⚠️ Minor 文案缺口，tasks 保持未勾 |
| 4.1 切换前快照 | `impl-reports/task4-dogfood-zero-regression-fix1.md:9-22`；checkpoint `602b243` | ✅ 历史操作有提交锚 |
| 4.2 本仓切换 | `openspec/config.yaml:1`；canonical 与 dogfood schema 树当前 `git diff --no-index` exit 0 | ✅ 实现 |
| 4.3 切换后逐 artifact 零回归 | `task4-dogfood-zero-regression-fix1.md:43-49`；checkpoint `602b243` | ✅ 历史操作有提交锚 |
| 4.4 一次性 change 依赖载荷 | `task4-dogfood-zero-regression-fix1.md:51-75`；schema 依赖边 `schema.yaml:228-230`、`:346-349` | ✅ 实现 |
| 5.1 版本门测试 | `test_old_cli_does_not_deploy_schema_or_switch_config`、`test_semver_numeric_gate_accepts_1_10`、`test_task5_schema_gate_fails_closed_for_unusable_cli` | ✅ 实现 |
| 5.2 迁移测试 | `test_migration_only_in_progress_and_idempotent`、`test_stray_directory_without_proposal_is_ignored`、`test_update_accepts_existing_fork_bound_change` | ✅ 实现 |
| 5.3 顺序与失败测试 | `test_task5_migration_runs_before_config_switch`、`test_migration_failure_stops_before_schema_and_config_switch` | ✅ 实现 |
| 5.4 bundle 收敛测试 | `test_install_refresh_is_authoritative_and_prunes_only_its_schema_orphans`、`test_schema_bundle_prunes_orphans` | ✅ 实现 |
| 5.5 schema 内容契约 | `test_task5_schema_content_contract`；当前真实 schema validate exit 0 | ✅ 实现 |
| 5.6 每条新增测试先 mutation-red | 仅 `task5-regression-install-refresh.md:15-20` 留有孤儿清理用例 red/green；无每条用例的可机验历史锚 | ⚠️ 过程证据不足，tasks 保持未勾 |
| 5.7 全仓 pytest 绿 | 历史命令 90 秒超时 exit 124；用户批准跳过。当前仅定向 `127 passed, 1 skipped` | ⚠️ 未通过，tasks 保持未勾 |
| 5.8 update byte-identical 测试 | `test_update_changes_only_schema_line`、`test_update_preserves_schema_inline_comment_and_suffix_bytes`、`test_update_preserves_schema_key_spacing_before_colon` | ✅ 实现 |
| 6.1 人读入口文档 | `AGENTS.md:113-115`、`CLAUDE.md:217-219`；`test_two_human_carriers_are_verbatim_identical` | ✅ 实现 |
| 6.2 roadmap P1 | `openspec/roadmaps/openspec-1.7.0-followup/roadmap.md:49`、`:60` | ✅ 实现 |
| 6.3 fork 漂移 todo | `openspec/issues/todolist/2026-07-todolist.md:2675`；issues 批次 `align-sdflow-spec-with-openspec-schema` | ✅ 实现 |
| 6.4 安装刷新 | `task5-regression-install-refresh.md:29-32` 记录 Git Bash setup exit 0；canonical/dogfood schema 与 generation-process 当前字节一致 | ✅ 完成，保留后续重跑超时 caveat |

## Delta Requirements 核对

| Requirement | 证据锚 | 状态 |
|---|---|---|
| SW-SCHEMA：project-local schema 下发、版本门、迁移前置 | `init.py:212-314`、`:461-507`、`:1019-1070`；`TestProjectLocalSchema`；当前真实 schema validate exit 0 | ✅ 实现 |
| SA-05：CLI 生成、依赖图/fallback、状态与校验分离 | `sdflow-spec/SKILL.md:392-464`；`test_phase_c_consumes_dependency_objects_and_has_schema_fallback`；当前 strict validate exit 0 | ✅ 核心实现；3.8 为 Minor 文案缺口 |
| SA-17：委派剥离、glob、skipped | `sdflow-spec/SKILL.md:425-446`；`test_phase_c_strips_delegation_before_applying_instruction`、`test_phase_c_handles_glob_existing_outputs_and_skipped_status` | ✅ 实现 |
| tickets 轨实现期聚合覆盖 | `tickets.md` frontmatter 为 `impl-pipeline: tickets`；`task7-implementation-verification.md:14-30` 各通过层锚在 `dc67af3`；当前 HEAD 另独立复跑 `127 passed, 1 skipped` | ✅ 实现期聚合证据成立 |

## 缺口与诚实边界

### 核心缺口

无。

### Minor / 已批准例外

1. Task 3.8 未明写“schema 已切换”这一降级前提；现有“判断层兜底”不影响运行行为，但文案契约未完整。
2. Task 5.6 只有一条 mutation red/green 历史证据，不能证明每条新增测试都先红。
3. Task 5.7 全量 `pytest` 未通过：历史超时 exit 124；按用户明确批准跳过，未假绿。
4. 自动化 e2e 未覆盖；当前仓无可发现的本 change e2e runner。真实 CLI 集成检查已通过，但不冒充 e2e。
5. 委派是否被模型遵守本来就是提示层、非机械保证（`proposal.md:61`、`:76`），本报告不宣称自动回流。

PASS
