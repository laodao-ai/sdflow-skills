## MODIFIED Requirements

### Requirement: 执行模式宿主条件化受限并行工作 frontier 并以文件交接

[spec-review-amendment] 原「受限并行」升级为「宿主条件化受限并行 + per-ticket worktree 隔离」。

执行模式 SHALL 按 Blocked-by 拓扑计算工作 frontier（`next_ready` 返回所有前置已完成的 ticket 号集合）；行为按宿主分支（`$SDFLOW_HOST` 第零步已 resolve）：

- **`host=claude`**：`next_ready` 返回多个候选时 SHALL 并行派发 implementer 子代理，**每个 implementer SHALL 使用 `isolation: "worktree"`**（Agent tool 原生参数，harness 自动创建独立 git worktree）。所有 implementer 返回后，编排层 SHALL **逐票按号序串行** merge worktree 分支回主分支（`git merge --no-ff`）→ 双轴审 → fix 循环 → checkpoint commit。
- **`host=codex` / `host=unknown`**：`next_ready` 返回多个候选时 SHALL **按号序逐个派发**（退化为串行），行为与改动前完全一致。
- `next_ready` 返回单个候选时行为与串行模式一致（两宿主一致）。

**并行 dispatch 约束（Claude 宿主）**：

- 每个 implementer 在独立 worktree 中工作，有独立 `.git/index` 和工作树——不存在 index 竞态。
- implementer dispatch prompt MAY 建议按文件名 `git add <具体文件>`（最佳实践），但不再是 MUST——worktree 隔离下通配暂存不会带入别人的改动。
- 编排层 SHALL 在全部 implementer 返回后，逐票串行执行 `git merge --no-ff <worktree-branch>`。merge 冲突（两票改同一文件）由 git 原生冲突检测 fail-loud。
- 双轴审 SHALL 串行执行（不同票之间亦不并行）——反向变异共享工作树会交叉感染。
- 收尾 ticket（`Blocked-by` = 全部功能票号）`next_ready` 只返回它一个，始终单独串行执行。

**review-package 生成（并行批次，Claude 宿主）**：

merge 回主分支后，每个 merge commit 天然隔离各票改动。审第 N 票时：
- `before-sha` = merge commit 的第一父（merge 前主分支 HEAD）
- `after-sha` = merge commit 自身
- `git diff <merge_parent1>..<merge_commit> -U10` 天然只含该票改动，Commits/Stat/Diff 三段均自然收窄

串行票的 review-package 沿用既有 `<before-sha>..<after-sha>` 规则不变。fix 轮的 `<before-sha>` 沿用既有规则不变（fix commit 在串行审阶段单线程产生，无并发写入）。

其余契约不变：每 ticket 派发 fresh implementer 子代理，契约为 TDD at pre-agreed seams、定期 typecheck、**单元测试 + 本 ticket 声明的 e2e 场景 + 本 ticket `Blocked-by` 链上模块的集成测试**（MUST NOT 跑与本票无依赖关系的集成/e2e 套件）；implementer 状态词表四值处置不变；子代理产物以文件交接不变；cannot-verify-from-diff 编排层消解与预算上界不变；frontier next-ready 判定由确定性 helper 计算不变；halt envelope 五要素不变。

**异常处理**：并行 implementer 中某个返回 BLOCKED / NEEDS_CONTEXT 时，harness 无中途取消能力，编排层 SHALL 等全部返回后逐个处理状态。BLOCKED 票的 worktree 直接丢弃（不 merge 回主分支），无脏改动污染。完成态票据正常走完 merge+审+checkpoint，不因兄弟票 BLOCKED 而搁置。白跑成本为可接受边角。

#### Scenario: Claude 宿主 frontier 受限并行推进（worktree 隔离）

- **GIVEN** `$SDFLOW_HOST=claude`
- **WHEN** ticket 2、ticket 3 均 Blocked-by ticket 1 且 ticket 1 完成
- **THEN** 编排层并行派发 ticket 2 和 ticket 3 的 implementer（各自 `isolation: "worktree"`）；两者全部返回后，merge worktree-2 回主分支 → 审 ticket 2 → checkpoint，merge worktree-3 回主分支 → 审 ticket 3 → checkpoint

#### Scenario: Codex 宿主退化为串行

- **GIVEN** `$SDFLOW_HOST=codex`
- **WHEN** ticket 2、ticket 3 均 Blocked-by ticket 1 且 ticket 1 完成
- **THEN** 编排层按号序先派 ticket 2（无 worktree 隔离）→ 审 → checkpoint，再派 ticket 3 → 审 → checkpoint

#### Scenario: 依赖图为线性链时退化为串行

- **WHEN** 每 ticket 的 Blocked-by 严格指向前一 ticket（1→2→3→4→5）
- **THEN** `next_ready` 每次只返回一个候选，行为与改动前完全一致（两宿主一致）

#### Scenario: 并行 implementer 的 review-package 隔离（Claude 宿主）

- **WHEN** ticket 2 和 ticket 3 并行执行完毕（各在独立 worktree），编排层进入串行 merge+审
- **THEN** merge ticket 2 的 worktree 分支后，审 ticket 2 的 review-package diff = `merge_parent1..merge_commit`，天然只含 ticket 2 的改动

#### Scenario: 并行 implementer 某个 BLOCKED（Claude 宿主）

- **WHEN** ticket 2、ticket 3、ticket 4 并行派发（各自 worktree），ticket 3 返回 BLOCKED
- **THEN** 编排层等全部返回后，逐个处理：merge ticket 2 和 ticket 4 的 worktree 分支回主分支并正常进审+checkpoint；ticket 3 的 worktree 直接丢弃（不 merge），按 BLOCKED halt envelope 处理

#### Scenario: 并行 implementer 碰同一文件时 merge conflict fail-loud

- **WHEN** ticket 2 和 ticket 3 并行执行后各自改了同一文件的不同段
- **THEN** merge ticket 2 后无冲突；merge ticket 3 时 `git merge --no-ff` 报冲突，编排层 SHALL 上报人介入

### Requirement: 出 ticket 模式并行安全生成约束

出 ticket 模式 SHALL 在产出 ticket 时评估**并行安全性**：对 `Blocked-by` 声明使得 `next_ready` 可能同时返回的一组 ticket，出票方 SHALL 确认——

- 它们的行为边界不重叠（不改同一模块的同一接口）
- 一个的产出不是另一个的输入
- 有疑问时 SHALL 保守声明依赖（宁可串行不可误并行）
- [spec-review-amendment] 若产出多张 `Blocked-by` 覆盖全部其余票号的 ticket，SHALL 让后者追加声明对前者的 `Blocked-by`，确保收尾节点唯一

该约束为指令层语义约束（出票方的模型判断）。[spec-review-amendment] 兜底从"不存在的 git add fail-loud"升级为 worktree 隔离下的 `git merge` 原生冲突检测（真正的 fail-loud）。

#### Scenario: 并行安全的 ticket 不声明互相 Blocked-by

- **WHEN** 某 change 有 3 张功能 ticket，T2 改脚本 A，T3 改脚本 B，T4 改 SKILL.md 的不同段，三者均只 Blocked-by T1
- **THEN** 出票方判定三者行为边界不重叠、产出不互为输入，保留 `Blocked-by: 1` 不加互相依赖

#### Scenario: 有数据流依赖时保守声明串行

- **WHEN** T2 新增一个函数，T3 的验收标准调用该函数
- **THEN** 出票方 SHALL 让 T3 声明 `Blocked-by: 1,2`，确保 T3 在 T2 完成后才执行
