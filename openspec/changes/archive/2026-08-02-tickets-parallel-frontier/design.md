## Context

tickets 管线首版（`matt-workflow-integration`）有意选择严格串行 frontier（design D4/Non-Goal），以降低首版复杂度。Phase A 试点 6 change 判赢后，受限并行的硬前置已解除。

当前改动面仅 `sdflow-implement/SKILL.md`——出票模式的生成约束段 + 执行模式的 frontier 编排段。`impl_route.py` 的 `next_ready()` 已支持一次返回多个无阻塞候选（纯集合运算 `dep_set <= done_set`），`ship_gate.py` 的完成窗口在同分支方案下零改动。

## Goals / Non-Goals

**Goals:**
- `next_ready` 返回多个候选时并行派发 implementer 子代理（Claude 宿主用 worktree 隔离，Codex 宿主退化为串行）
- 出票时确保同层级 ticket 的行为边界不重叠
- review-package 在并行场景下正确隔离每票 diff

**Non-Goals:**
- 双轴审并行（留后续优化，见 decision-memo D1）
- 文件路径声明或机械冲突检测

[spec-review-amendment] ~~子分支/worktree 隔离~~：原 Non-Goal 已升级为 Goal——调研确认 `ship_gate.py` 的 `done_task_ids`（`git log sha..HEAD --no-merges`，无 `--first-parent`）能穿透 merge commit 看到被 merge 进来的分支上的 checkpoint 标签，gate 契约零改动。Claude Code 的 `isolation: "worktree"` 是 harness 原生能力，零脚本改动。Codex 无原生 worktree 能力且进程回收模型不兼容并行——退化为串行。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。

## Risks / Trade-offs

- **BLOCKED 白跑**（C3）：并行 implementer 某个 BLOCKED 时其余已跑完的 token 浪费。harness 无取消能力，成本天花板 = 2-3 个 implementer token
- **Codex 宿主无并行收益**：Codex 无原生 worktree 隔离且进程回收模型不兼容并行 → 退化为串行，行为与改动前一致，无风险但也无收益

[spec-review-amendment] ~~并行 implementer 文件冲突~~：原风险项（"语义约束 + git add fail-loud 兜底"）已被 worktree 隔离结构性消除。6 镜收敛确认"git add fail-loud"不是事务边界、不构成兜底——但 worktree 给每个 implementer 独立 `.git/index`，竞态不再存在。

## Design

### 执行时序

```
串行（现状 / Codex 宿主退化态）：
  frontier(done=1) → [2] → impl T2 → 审 T2 → ckpt T2
  → frontier(done=1,2) → [3] → impl T3 → 审 T3 → ckpt T3
  → frontier(done=1,2,3) → [4] → impl T4 → 审 T4 → ckpt T4
  → frontier(done=1,2,3,4) → [5] → impl T5(收尾) → 审 T5 → ckpt T5
  墙钟 = sum(impl+审, all tickets)

并行（Claude 宿主目标态，per-ticket worktree 隔离）：
  frontier(done=1) → [2,3,4] → ┌ impl T2 (worktree-2) ┐
                                 ├ impl T3 (worktree-3) ├ 并行，各自独立 .git/index
                                 └ impl T4 (worktree-4) ┘
  → 收集全部返回 →
  → merge worktree-2 回主分支 → 审 T2 → ckpt T2
  → merge worktree-3 回主分支 → 审 T3 → ckpt T3
  → merge worktree-4 回主分支 → 审 T4 → ckpt T4  （串行）
  → frontier(done=1,2,3,4) → [5] → impl T5(收尾) → 审 T5 → ckpt T5
  墙钟 = max(impl T2,T3,T4) + sum(merge+审, all tickets) + impl T1 + impl T5
```

### 出票模式改动

在「产出：3–6 张 tracer-bullet 垂直切片」段末追加一条并行安全生成约束：

> 出票时，对 `Blocked-by` 声明使得 `next_ready` 可能同时返回的一组 ticket（即它们的 `Blocked-by` 集合是 `done` 集的子集时会同时出现在 ready 列表中），MUST 确认：
> - 它们的行为边界不重叠（不改同一模块的同一接口）
> - 一个的产出不是另一个的输入
> - 有疑问时保守声明依赖（宁可串行不可误并行）

### 执行模式改动

**frontier 段**：「严格串行」改为「宿主条件化受限并行」——

- **宿主分支**（`$SDFLOW_HOST` 第零步已 resolve）：
  - `host=claude`：`next_ready` 返回多个 → 并行派发，每个 implementer 用 `isolation: "worktree"`（Agent tool 原生参数）
  - `host=codex` / `host=unknown`：退化为串行（`next_ready` 返回多个时仍按号序逐个派发），行为与改动前一致
- `next_ready` 返回 1 个 → 串行派发（行为不变，两宿主一致）
- 所有 implementer 返回后，编排层逐票按号序串行：merge worktree 分支回主分支（`git merge --no-ff`）→ 双轴审 → fix 循环（如有）→ checkpoint commit
- 收尾 ticket（`Blocked-by` = 全部功能票号）始终单独串行执行（`next_ready` 只返回它一个）

[spec-review-amendment] ~~dispatch prompt 的 `git add` 按文件名约束~~：worktree 隔离下每个 implementer 有独立 `.git/index`，不存在通配暂存带入别人改动的问题。该约束降为建议性最佳实践（非 MUST），dispatch prompt 不再强制。

**review-package 生成变化**：

- 串行票（`next_ready` 返回 1 个，或 Codex 退化串行）：行为不变，`<before-sha>..<after-sha>` 同现有
- 并行批次（Claude 宿主）：merge 回主分支后，每个 merge commit 清晰划分了各票的 commit 集。审第 N 票时：
  ```bash
  # merge commit 的第二父链即该票的 worktree 分支
  # before-sha = merge commit 的第一父（merge 前主分支 HEAD）
  # after-sha = merge commit 自身
  git diff <merge_parent1>..<merge_commit> -U10
  ```
  review-package 头部写 `# Review package: <merge_parent1>..<merge_commit> (Task N worktree merge)`
  Commits/Files-changed/Diff 三段均自然收窄到该票范围，无需额外文件过滤

### gate 影响分析

零改动。`done_task_ids`（`ship_gate.py:1478-1496`）使用 `git log sha..HEAD --no-merges --format=%s`：
- **无 `--first-parent`** → 遍历穿透 merge commit，看到被 merge 进来的 worktree 分支上的全部 commit
- **`--no-merges`** → 只跳过 merge commit 本身（其 subject 不含 checkpoint 标签），不影响遍历路径
- checkpoint 标签打在普通 commit 上 → **穿透 merge 正常识别**

[spec-review-amendment] 以上穿透性已由调研验证（读码 `ship_gate.py:1478-1496`），Non-Goal 2 原声称的"gate 契约重写成本过高"不成立。

其余不变：
- `checkbox_done_ids` 扫 `tickets.md` 的复选框，与并行/merge 无关
- 失鲜判据的求值窗口不受影响

## Compliance

本次改动在 `sdflow-implement/SKILL.md` 的 prose 条款层面，不涉及脚本代码或测试变更。
