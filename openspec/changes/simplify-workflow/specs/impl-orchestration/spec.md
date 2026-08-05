## Purpose

同步 impl-orchestration 能力，翻转 impl-pipeline 缺省路由。[spec-review-amendment]

## MODIFIED Requirements

### Requirement: impl-pipeline 路由（缺省翻转）

修改：`impl_route.py` 的 `route` 子命令 SHALL 在 `openspec/config.yaml` 无 `impl-pipeline` 键时默认路由到 `tickets` 管线（原为 `superpowers`）。

不变：显式 `impl-pipeline: superpowers` 仍路由到旧管线；已有 plan 文件的 marker 锁定优先于 config 缺省。

#### Scenario: 无 impl-pipeline 键默认走 tickets

- **WHEN** 项目 config.yaml 不含 `impl-pipeline` 键
- **THEN** `impl_route.py route` 输出 `pipeline=tickets`

#### Scenario: 非法值/YAML 损坏回退

- **WHEN** 项目 config.yaml 的 `impl-pipeline` 值不识别或 YAML 损坏
- **THEN** `impl_route.py route` 回退到 `tickets`（新缺省），并在 stderr 报告诊断信息
