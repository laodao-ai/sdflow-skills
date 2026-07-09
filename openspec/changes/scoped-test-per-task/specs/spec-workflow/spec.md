## ADDED Requirements

### Requirement: 阶段三 subagent-dev 派发注入测试范围纪律

阶段三派发 `subagent-driven-development` 执行 plan 时，MUST 注入统一测试范围纪律：每个任务的实现子代理 MUST 只运行覆盖本任务改动的 scoped test（named test files）确认无 warning；全量 `-race` / 回归套件 MUST 仅在 final whole-branch 终审前运行一次，SHALL NOT 逐任务运行全量回归。

该纪律 MUST 由 workflow bundle 的 `workflow.md`（步骤 6/7）承载为**单一源**；`sdflow-ship` 的 RUN_PLAN 分支 MUST **引用**该单一源注入、SHALL NOT 复述完整规则文本，且 MUST NOT 改动 checkpoint 主锚契约措辞。

此纪律 SHALL NOT 改变 ship_gate 完成判据——gate 只认 checkpoint 命名空间标签，不解析测试范围文本。

#### Scenario: 逐任务实现只跑 scoped test

- **WHEN** 阶段三 subagent-dev 派发某任务的实现子代理，该任务改动有对应覆盖测试文件
- **THEN** 实现子代理 MUST 只运行覆盖本任务的 named test files 确认通过且无 warning，MUST NOT 运行全量 `-race`/回归套件

#### Scenario: 全量回归仅 final whole-branch 终审一次

- **WHEN** 阶段三所有任务实现完成、进入 final whole-branch 终审
- **THEN** 全量 `-race`/回归套件 MUST 在此运行一次，且此前逐任务阶段 SHALL NOT 运行过全量回归

#### Scenario: 纪律以 workflow.md 为单一源、sdflow-ship 引用而非复述

- **WHEN** `sdflow-ship` 的 RUN_PLAN 分支派发 subagent-dev
- **THEN** 测试范围纪律 MUST 以 `workflow.md` 步骤 6/7 为承载单一源，RUN_PLAN MUST 引用而非复述该规则文本，且 MUST NOT 改动 checkpoint 主锚契约措辞

#### Scenario: 措辞变更不扰动 gate 判据

- **WHEN** 测试范围纪律措辞变更后重跑 `sdflow-ship/tests/`
- **THEN** ship_gate 的 verdict 判据（RUN_PLAN / CONTINUE_IMPL / RERUN 等）MUST 无回归——gate 只认 checkpoint 标签、不解析测试范围文本
