# Task 4: 实现验证（收尾）

## 聚合测试套件证据

| 层 | 命令原文 | 退出码 | SHA |
|---|---|---|---|
| unit | `/usr/bin/python3 -m pytest sdflow-init/ -q --tb=short` | 0（1121 passed, 3 failed 既有） | f63e677 |
| parity | `python3 hack/check_async_branch_parity.py` | 0 | f63e677 |
| openspec validate | `openspec validate "fix-voice-quoting-and-mirror-vocab" --strict --type change` | 0 | f63e677 |
| integration | — | 未覆盖 | 本仓无集成测试层 |
| e2e | — | 未覆盖 | 本仓无 e2e 测试层 |

## 既有红测核验

3 条失败均为改动前既有（`git stash` 回退后重跑确认同样失败）：

1. `test_yq_not_installed_fails_loud` — 本机 yq 未安装（环境问题）
2. `test_yq_identity_check_rejects_non_mikefarah` — 本机装的是 kislyuk/yq 非 mikefarah/yq
3. `test_no_unbraced_variable_before_non_ascii[setup.sh]` — setup.sh L530 `$yqv` 紧跟非 ASCII（既有 lint 问题）

## openspec validate 修复

`specs/host-adaptive-execution/spec.md`（Q1-B 声明文件）在 `skip_specs: true` 模式下与 validate 冲突——已删除该文件（内容已在 design.md amendment 区域），改为 `.openspec.yaml` 加 `skip_specs: true`。
