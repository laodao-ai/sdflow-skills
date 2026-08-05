## Purpose

简化 spec 工作流阶段一入口为唯一线性路径，删除双轨分支、wayfinder 衔接、embedded-test-sop 自动触发、sdflow-spec 手动限制，翻转 impl-pipeline 缺省为 tickets。

## MODIFIED Requirements

### Requirement: 阶段一入口为唯一线性路径，模型可自动触发

阶段一入口 SHALL 为唯一线性路径：`explore(条件) → sdflow-spec → /clear → sdflow-spec-review`。不再有分支 A/B 双轨选择。

- **`opsx:explore`**：条件前置步——问题模糊/方向未定时先 explore 发散；问题清晰时跳过。
- **`/sdflow-spec`**：唯一生成入口——澄清(A) → 拷问(B) → 生成(C) 三相位连续跑，产四件套 + `decision-memo.md`。
- **自动触发**：`sdflow-spec` MUST NOT 声明 `disable-model-invocation: true`。模型 SHALL 在以下情形自动 invoke `/sdflow-spec`：① explore 中人示意收敛（如「开搞」「做吧」「开 change」）；② 用户描述需求且需要开 change 时。模型 MUST NOT 自主判断「该开 change 了」——须有人的示意信号。
- **拷问不可省**：触发方式的变更 SHALL NOT 影响相位 B 的拷问协议。任何进入相位 C 的路径 SHALL 先产出非空 `decision-memo.md`。
- **FF-0 三分支判定**不受影响：保护分支建 / 已在 `feat/{本 change}` 跳过 / 在其它 feature 分支 halt 问人。

#### Scenario: 用户在 explore 中示意收敛

- **WHEN** 用户在 opsx:explore 中表达「开搞」「做吧」「开 change」等收敛信号
- **THEN** 模型自动 invoke `/sdflow-spec`，带入 explore 上下文

#### Scenario: 用户直接描述需求

- **WHEN** 用户说「做 X」且需要开 change，未指定入口
- **THEN** 模型直接 invoke `/sdflow-spec`

#### Scenario: 模型不自主触发

- **WHEN** explore 讨论仍在发散，用户未表达收敛信号
- **THEN** 模型 MUST NOT 自动 invoke `/sdflow-spec`

#### Scenario: 拷问协议不因触发方式改变

- **WHEN** sdflow-spec 由模型自动触发（而非用户手动敲）
- **THEN** 相位 B 的人机对话拷问（一次一问、承重约束逐条站稳、停止信号需证据锚）照常执行，MUST NOT 缩减或跳过

### Requirement: 阶段三编排不含 embedded-test-sop 自动触发

`sdflow-ship` 编排器的 gate 状态机 SHALL NOT 包含 `RUN_SOP` verdict。`embedded-test-sop` skill SHALL 不再作为流程内自动触发步存在——ship_gate.py MUST NOT 检测 TG-02 命中并输出 `RUN_SOP`。`embedded-test-sop` skill 目录 SHALL 从仓库删除。

#### Scenario: ship gate 不输出 RUN_SOP

- **WHEN** ship_gate.py 对一个 proposal 命中 TG-02 的 change 求值
- **THEN** 不输出 `RUN_SOP` verdict（该 verdict 不存在于契约表中）

#### Scenario: embedded-test-sop skill 不可安装

- **WHEN** 用户运行 `setup.sh`
- **THEN** `~/.claude/skills/` 下无 `embedded-test-sop` 链接（skill 目录已从源仓删除）

### Requirement: impl-pipeline 缺省为 tickets

`impl_route.py` 的 `route` 子命令 SHALL 在 `openspec/config.yaml` 无 `impl-pipeline` 键时默认路由到 `tickets` 管线（`sdflow-implement`）。显式 `impl-pipeline: superpowers` 仍路由到旧管线（`writing-plans → subagent-driven-development`）。

#### Scenario: 无 impl-pipeline 键默认走 tickets

- **WHEN** 项目 config.yaml 不含 `impl-pipeline` 键
- **THEN** `impl_route.py route` 输出 `pipeline=tickets`

#### Scenario: 显式 superpowers 不受影响

- **WHEN** 项目 config.yaml 含 `impl-pipeline: superpowers`
- **THEN** `impl_route.py route` 输出 `pipeline=superpowers`

## REMOVED Requirements

### Requirement: 阶段一讨论按雾量三段分流并约定 wayfinder→ff 衔接契约

本 Requirement 整段移除。阶段一不再有雾量三分（清晰/单session模糊/超单session）和 wayfinder→ff 衔接契约。入口由上方「阶段一入口为唯一线性路径」替代。

#### Scenario: 本 Requirement 不再存在

- **WHEN** archive 执行
- **THEN** 主 spec 中本 Requirement 被删除

### Requirement: grill 对上游已决分支瘦跑

本 Requirement 整段移除。grill-with-docs 不再是流程中的独立步骤。拷问功能由 sdflow-spec 相位 B 内建。

#### Scenario: 本 Requirement 不再存在

- **WHEN** archive 执行
- **THEN** 主 spec 中本 Requirement 被删除
