# Task 2 Spec 轴复审 · project-local schema 下发与迁移 · fix1

## 结论

**PASS**

本复审仅覆盖 `tickets.md` 的 Task 2（`R-ID: SW-SCHEMA`）及 fix1 变更；未修改生产代码或 `tickets.md`。fix1 已补齐旧 Spec/Standards review 指出的命令缺失、迁移补写失败保护和 stray 隔离证据。

## 输入与范围

- `impl-reports/task2-project-local-schema-fix1.md`
- `impl-reports/task2-project-local-schema.md`
- `impl-reports/task2-spec-review.md`
- `impl-reports/task2-standards-review.md`
- `impl-reports/task2-brief.md`
- `tickets.md` 的 Global Constraints 与 Task 2
- `design.md`
- `specs/spec-authoring/spec.md`
- `specs/spec-workflow/spec.md`
- 当前 diff：`sdflow-init/scripts/init.py`、`sdflow-init/tests/test_init.py`、`sdflow-init/assets/workflow/config.template.yaml`

## R-ID 与验收项逐项核对

| 验收项 | 当前实现与证据 | 判定 |
|---|---|---|
| CLI 版本按 semver 数值元组判断；`<1.7.0`、命令缺失、非数值输出均 fail-closed 并输出原因 | `init.py:_openspec_cli_version()` 用 `subprocess.run`、正则解析三元组并处理 `OSError`/非零退出/不可解析输出；`_schema_gate()` 数值比较并生成一行原因。`test_init.py` 覆盖 `1.6.9`、`1.10.0`、非数值输出和命令缺失。 | PASS |
| 仅扫描含 `proposal.md` 的在途 change；缺绑定补写，已有绑定 no-op，archive/stray 不迁移 | `migrate_changes()` 跳过 `archive`、非目录、无 `proposal.md` 和已有 `.openspec.yaml`；`test_migration_only_in_progress_and_idempotent`、`test_stray_directory_without_proposal_is_ignored` 提供机械证据。 | PASS |
| 任一补写失败终止本次 run，config 不切换，顺序有测试证据 | `run()` 在 `copy_bundle()` 与 `handle_config()` 前调用 `migrate_changes()`；补写异常向上传播。`test_migration_failure_stops_before_schema_and_config_switch` 注入 `.openspec.yaml` 写失败，断言 `SystemExit(1)`、config 字节不变、schema 未下发、marker 未残留。 | PASS |
| schema bundle 使用 rmtree-first 整删重拷 | `copy_bundle()` 对 `openspec/schemas` 先 `shutil.rmtree()` 再 `shutil.copytree()`；`test_schema_bundle_prunes_orphans` 断言 orphan 文件被清除。 | PASS |
| 版本门通过时模板与消费仓 config 指向 fork；update 只改 schema 行、其他字节保持不变 | `config.template.yaml` 指向 `sdflow-spec-driven`；`_set_schema_key()` 仅替换首个顶层 schema 行并原子写回；`test_update_changes_only_schema_line` 覆盖 byte-level 结果，版本门测试覆盖消费仓切换。 | PASS |
| 版本门与迁移结论进入既有 run 汇总 | `run()` 将 schema gate、迁移数量/跳过原因、bundle 和 config 结果写入 report，并沿既有输出路径返回。定点测试覆盖通过/拒绝路径。 | PASS |

## 旧 finding 复核

| 旧 finding | fix1 处理 | 结论 |
|---|---|---|
| 缺少命令缺失版本门测试 | 新增 `test_missing_cli_fails_closed`，注入 `OSError`，断言不部署 schema 且 config 保持 `spec-driven`。 | 已关闭 |
| 缺少迁移补写失败时 config 不切换测试 | 新增失败注入测试，覆盖异常、退出码、config 原字节、schema 未部署和 marker 未残留。 | 已关闭 |
| stray 目录缺少明确机械判据/独立测试 | `migrate_changes()` 明确定义无 `proposal.md` 为 stray 并跳过；新增独立测试。 | 已关闭 |

## 验证结果

- `pytest sdflow-init/tests/test_init.py -q -k 'ProjectLocalSchema'`：**9 passed**。
- fix1 实现报告记录的 `pytest sdflow-init/tests/test_init.py -q`：**53 passed, 1 skipped**。
- `git diff --check`：通过。
- `pytest sdflow-init/tests -q`：本次在 120 秒内无输出并超时，未宣称全量通过。该命令未提供新的失败断言；Task 2 直接受影响的 `test_init.py` 已有完整定点结果，故不构成当前 Spec 轴的阻断。

## Spec 轴裁决

Task 2 的 `SW-SCHEMA` 目标、Global Constraints 和六项验收要求均有当前实现与测试证据；fix1 已关闭两份旧 review 的阻断项。结论为 **PASS**，可进入下一步双轴/门禁流程。
