---
ship-gate:
  code_review: pass
  reviewed_sha: 916b203619f4818aa86dbec8e6f8da1886aeaf2d
---

# Task 2 Fix 1 Standards 轴复审

## 结论

PASS

## 复审范围

只读核验以下材料：

- `impl-reports/task2-project-local-schema-fix1.md`
- 旧报告 `impl-reports/task2-standards-review.md`、`impl-reports/task2-spec-review.md`
- `impl-reports/task2-brief.md`
- `tickets.md` 的 Global Constraints 与 Task 2
- `design.md`
- `specs/spec-workflow/spec.md`、`specs/spec-authoring/spec.md`
- 当前 `sdflow-init/scripts/init.py`、`sdflow-init/tests/test_init.py`、`config.template.yaml` diff

未修改生产代码，未修改 `tickets.md`。

## 旧阻断项复核

### 1. 命令缺失版本门：PASS

机械证据：

- `init.py:_openspec_cli_version()` 捕获 `OSError`，返回不可用原因；不可解析 semver、非零退出码同样 fail-closed。
- `init.py:_schema_gate()` 仅在可解析版本 `>= (1, 7, 0)` 时启用 project-local schema；否则保持内置 `spec-driven`。
- `test_missing_cli_fails_closed` 注入 `OSError("openspec: command not found")`，实际运行后断言：
  - `openspec/schemas/` 不存在；
  - `config.yaml` 仍以 `schema: spec-driven` 开头。
- 既有 `test_missing_or_non_numeric_cli_fails_closed` 继续覆盖非数字输出；`test_semver_numeric_gate_accepts_1_10` 覆盖数值比较而非字符串比较。

### 2. 迁移补写失败回滚：PASS

机械证据：

- `run()` 在 `copy_bundle()` 与 `handle_config()` 之前调用 `migrate_changes()`；迁移异常进入统一错误出口并以 `SystemExit(1)` 停止。
- `test_migration_failure_stops_before_schema_and_config_switch` 对 `.openspec.yaml` 的创建注入 `OSError`，实际断言：
  - `SystemExit.code == 1`；
  - `config.yaml` 字节与运行前完全相同；
  - `openspec/schemas/` 尚未部署；
  - 目标 change 未留下迁移 marker。
- 该测试证明失败不会继续进入 schema bundle 部署或 config schema 切换，而不只是证明正常路径顺序。

### 3. stray 目录隔离：PASS

机械证据：

- `migrate_changes()` 明确定义：`openspec/changes/` 下目录缺少 `proposal.md` 即为 stray；`archive` 另行显式排除。
- `test_stray_directory_without_proposal_is_ignored` 创建仅含 `notes.md` 的 stray 目录，并同时创建真实 active change；实际断言：
  - stray 不生成 `.openspec.yaml`；
  - active change 正常补写 `schema: spec-driven` marker。
- 因此测试同时证明了“隔离 stray”与“未误伤真实 change”，不是仅验证空目录被跳过。

## 验证结果

- `pytest sdflow-init/tests/test_init.py -q` → **53 passed, 1 skipped**
- `pytest sdflow-init/tests/test_init.py -q -k 'missing_cli or migration_failure_stops_before_schema_and_config_switch or stray_directory_without_proposal_is_ignored'` → **3 passed, 51 deselected**
- `git diff --check` → **通过**
- `tickets.md` 无 diff。

## Findings

无阻断项。三个旧 review 阻断点均已有代码级行为与独立测试机械锚点，建议进入后续实现流程。

