## Context

tickets 管线首版（`matt-workflow-integration`）有意选择严格串行 frontier（design D4/Non-Goal），以降低首版复杂度。Phase A 试点 6 change 判赢后，受限并行的硬前置已解除。

当前改动面仅 `sdflow-implement/SKILL.md`——出票模式的生成约束段 + 执行模式的 frontier 编排段。`impl_route.py` 的 `next_ready()` 已支持一次返回多个无阻塞候选（纯集合运算 `dep_set <= done_set`），`ship_gate.py` 的完成窗口在同分支方案下零改动。

## Goals / Non-Goals

**Goals:**
- `next_ready` 返回多个候选时并行派发 implementer 子代理
- 出票时确保同层级 ticket 的行为边界不重叠
- review-package 在并行场景下正确隔离每票 diff

**Non-Goals:**
- 双轴审并行（留后续优化，见 decision-memo D1）
- 子分支/worktree 隔离（gate 契约重写成本过高）
- 文件路径声明或机械冲突检测

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。

## Risks / Trade-offs

- **并行 implementer 文件冲突**（C2 诚实边界）：语义约束非机械门，出票时模型判断 + 执行时 `git add` fail-loud 兜底。概率低（vertical-slice 设计），后果可控（fail-loud 不静默）
- **BLOCKED 白跑**（C3）：并行 implementer 某个 BLOCKED 时其余已跑完的 token 浪费。harness 无取消能力，成本天花板 = 2-3 个 implementer token

## Design

### 执行时序

```
串行（现状）：
  frontier(done=1) → [2] → impl T2 → 审 T2 → ckpt T2
  → frontier(done=1,2) → [3] → impl T3 → 审 T3 → ckpt T3
  → frontier(done=1,2,3) → [4] → impl T4 → 审 T4 → ckpt T4
  → frontier(done=1,2,3,4) → [5] → impl T5(收尾) → 审 T5 → ckpt T5
  墙钟 = sum(impl+审, all tickets)

并行（目标态）：
  frontier(done=1) → [2,3,4] → ┌ impl T2 ┐
                                 ├ impl T3 ├ 并行
                                 └ impl T4 ┘
  → 收集全部返回 →
  → 审 T2 → ckpt T2 → 审 T3 → ckpt T3 → 审 T4 → ckpt T4  （串行）
  → frontier(done=1,2,3,4) → [5] → impl T5(收尾) → 审 T5 → ckpt T5
  墙钟 = max(impl T2,T3,T4) + sum(审, all tickets) + impl T1 + impl T5
```

### 出票模式改动

在「产出：3–6 张 tracer-bullet 垂直切片」段末追加一条并行安全生成约束：

> 出票时，对 `Blocked-by` 声明使得 `next_ready` 可能同时返回的一组 ticket（即它们的 `Blocked-by` 集合是 `done` 集的子集时会同时出现在 ready 列表中），MUST 确认：
> - 它们的行为边界不重叠（不改同一模块的同一接口）
> - 一个的产出不是另一个的输入
> - 有疑问时保守声明依赖（宁可串行不可误并行）

### 执行模式改动

**frontier 段**：「严格串行」改为「受限并行」——

- `next_ready` 返回 1 个 → 串行派发（行为不变）
- `next_ready` 返回多个 → 并行派发全部（一条消息内多个 Agent 调用）
- 所有 implementer 返回后，逐票按号序串行：双轴审 → fix 循环（如有）→ checkpoint commit
- 收尾 ticket（`Blocked-by` = 全部功能票号）始终单独串行执行（`next_ready` 只返回它一个）

**dispatch prompt 新增约束**：

- implementer MUST 按文件名 `git add <具体文件>`，MUST NOT 用 `git add .` / `git add -A` / `git add -u`（并行 implementer 共享工作树，通配暂存会带入别人的改动）

**review-package 生成变化**：

- 串行票（`next_ready` 返回 1 个）：行为不变，`<before-sha>..<after-sha>` 同现有
- 并行批次：编排层在并行 dispatch 前记录 `PARALLEL_BASE = HEAD`，每个 implementer 返回后从 `git log` 识别其 commit。审第 N 票时：
  ```bash
  # 取该 implementer 改过的文件列表
  TICKET_FILES=$(git diff --name-only <ticket_commits>)
  # 用文件范围隔离 diff
  git diff PARALLEL_BASE..HEAD -- $TICKET_FILES
  ```
  review-package 头部仍写 `# Review package: PARALLEL_BASE..HEAD (scoped to Task N files)`

### gate 影响分析

无。同分支方案下：
- checkpoint 标签由编排层在串行审阶段补打（`SKILL.md:547`），不受 impl 并行影响
- `done_task_ids` 扫 `[plan_first_sha, HEAD]` 窗口内的 checkpoint 标签，全部可见
- `checkbox_done_ids` 扫 `tickets.md` 的复选框，与并行无关
- 失鲜判据的求值窗口不受影响（只在 RUN_SOP/RUN_PLAN/CONTINUE_IMPL 入口求值）

## Compliance

本次改动在 `sdflow-implement/SKILL.md` 的 prose 条款层面，不涉及脚本代码或测试变更。
