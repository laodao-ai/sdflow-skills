## MODIFIED Requirements

### Requirement: 执行模式受限并行工作 frontier 并以文件交接

执行模式 SHALL 按 Blocked-by 拓扑计算工作 frontier（`next_ready` 返回所有前置已完成的 ticket 号集合）；**`next_ready` 返回多个候选时 SHALL 并行派发 implementer 子代理**（一条消息内多个 Agent 调用），所有 implementer 返回后**逐票按号序串行**进入双轴审 + fix 循环 + checkpoint commit。`next_ready` 返回单个候选时行为与串行模式一致。

**并行 dispatch 约束**：

- implementer dispatch prompt SHALL 要求按文件名 `git add <具体文件>`，MUST NOT 使用 `git add .` / `git add -A` / `git add -u`——并行 implementer 共享同一工作树，通配暂存会带入其他 ticket 的改动。
- 编排层 SHALL 在并行 dispatch 前记录 `PARALLEL_BASE = HEAD`。
- 并行 implementer 全部返回后，编排层 SHALL 从各 implementer 的 commit 列表提取其改过的文件，逐票审时的 review-package diff SHALL 用 `git diff PARALLEL_BASE..HEAD -- <该票文件列表>` 隔离，MUST NOT 用全局 `PARALLEL_BASE..HEAD`（会包含其他 ticket 的变更）。
- 双轴审 SHALL 串行执行（不同票之间亦不并行）——反向变异共享工作树会交叉感染。
- 收尾 ticket（`Blocked-by` = 全部功能票号）`next_ready` 只返回它一个，始终单独串行执行。

其余契约不变：每 ticket 派发 fresh implementer 子代理，契约为 TDD at pre-agreed seams、定期 typecheck、**单元测试 + 本 ticket 声明的 e2e 场景 + 本 ticket `Blocked-by` 链上模块的集成测试**（MUST NOT 跑与本票无依赖关系的集成/e2e 套件）；implementer 状态词表四值处置不变；子代理产物以文件交接不变；cannot-verify-from-diff 编排层消解与预算上界不变；frontier next-ready 判定由确定性 helper 计算不变；halt envelope 五要素不变。

**异常处理**：并行 implementer 中某个返回 BLOCKED / NEEDS_CONTEXT 时，harness 无中途取消能力，编排层 SHALL 等全部返回后逐个处理状态。已完成的 implementer 的普通 commit 无副作用（可 revert），白跑成本为可接受边角。

#### Scenario: frontier 受限并行推进

- **WHEN** ticket 2、ticket 3 均 Blocked-by ticket 1 且 ticket 1 完成
- **THEN** 编排层并行派发 ticket 2 和 ticket 3 的 implementer；两者全部返回后，按号序先审 ticket 2、再审 ticket 3

#### Scenario: 依赖图为线性链时退化为串行

- **WHEN** 每 ticket 的 Blocked-by 严格指向前一 ticket（1→2→3→4→5）
- **THEN** `next_ready` 每次只返回一个候选，行为与改动前完全一致

#### Scenario: 并行 implementer 的 review-package 隔离

- **WHEN** ticket 2 和 ticket 3 并行执行完毕，编排层进入串行审
- **THEN** 审 ticket 2 时的 review-package diff 仅含 ticket 2 改过的文件，不含 ticket 3 的变更

#### Scenario: 并行 implementer 某个 BLOCKED

- **WHEN** ticket 2、ticket 3、ticket 4 并行派发，ticket 3 返回 BLOCKED
- **THEN** 编排层等 ticket 2 和 ticket 4 也返回后，逐个处理：ticket 2 和 ticket 4 正常进审，ticket 3 按 BLOCKED halt envelope 处理

### Requirement: 出 ticket 模式并行安全生成约束

出 ticket 模式 SHALL 在产出 ticket 时评估**并行安全性**：对 `Blocked-by` 声明使得 `next_ready` 可能同时返回的一组 ticket，出票方 SHALL 确认——

- 它们的行为边界不重叠（不改同一模块的同一接口）
- 一个的产出不是另一个的输入
- 有疑问时 SHALL 保守声明依赖（宁可串行不可误并行）

该约束为指令层语义约束（出票方的模型判断），非机械门——ticket 不预写具体文件路径（`SKILL.md:260`），无确定性信号可机械判断文件重叠。执行时的 `git add` 冲突 fail-loud 为兜底防线。

#### Scenario: 并行安全的 ticket 不声明互相 Blocked-by

- **WHEN** 某 change 有 3 张功能 ticket，T2 改脚本 A，T3 改脚本 B，T4 改 SKILL.md 的不同段，三者均只 Blocked-by T1
- **THEN** 出票方判定三者行为边界不重叠、产出不互为输入，保留 `Blocked-by: 1` 不加互相依赖

#### Scenario: 有数据流依赖时保守声明串行

- **WHEN** T2 新增一个函数，T3 的验收标准调用该函数
- **THEN** 出票方 SHALL 让 T3 声明 `Blocked-by: 1,2`，确保 T3 在 T2 完成后才执行
