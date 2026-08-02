## Why

tickets 管线（`sdflow-implement`）的执行模式强制严格串行——`next_ready()` 返回多个无阻塞候选时仍逐个派发。一个 5 票 change（T1 → T2/T3/T4 → T5 收尾）的墙钟 = 5 票之和，而 T2/T3/T4 之间无依赖、本可并行。串行是首版红线（design D4/Non-Goal），Phase A 试点已判赢（6 change 无熔断），现在可以放开。

## What Changes

- **出票模式**（`mode=tickets-plan`）：加「并行安全」生成约束——对同一 `Blocked-by` 层级的 ticket，出票时须确认行为边界不重叠、产出不互为输入，有疑问时保守声明依赖；收尾节点唯一约束
- **执行模式**（`mode=tickets-exec`）：宿主条件化受限并行——Claude 宿主 `next_ready` 返回多个候选时用 `isolation: "worktree"` 并行派发 implementer 子代理，Codex 宿主退化为串行；所有 implementer 返回后逐票 merge 回主分支 + 串行双轴审 + checkpoint commit
- **执行模式 review-package 生成**：并行批次用 merge commit 天然隔离（`merge_parent1..merge_commit`），无需文件过滤

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `impl-orchestration`: 执行模式 frontier 从严格串行放宽为受限并行；出票模式加并行安全生成约束

## Impact

- **代码**：仅 `sdflow-implement/SKILL.md` 一个文件的 prose 条款（出票段 + 执行段）
- **不改**：`impl_route.py`（`next_ready` 已支持多候选返回）、`ship_gate.py`（gate 完成窗口零改动，`done_task_ids` 穿透 merge commit）、`sdflow-ship/SKILL.md`（链序零改动）
- **向后兼容**：① 依赖图为线性链的 change 退化为串行；② Codex 宿主退化为串行（行为与改动前完全一致）

## Success Metrics

- [spec-review-amendment] Claude 宿主：依赖图稀疏的 change（如 T1 → T2/T3/T4 → T5）impl 阶段墙钟 ≈ T1 + max(impl T2,T3,T4) + sum(merge+审, all tickets) + impl T5；Codex 宿主：行为与改动前一致（退化串行，无回归）
- gate 行为零回归（`done_task_ids` 穿透 merge commit，checkpoint 标签可见性、完成集计算、失鲜判据均不受影响）
- 出票模式产出的 `Blocked-by` 声明在并行场景下语义正确（不遗漏数据流依赖）

## Non-Goals

- 双轴审并行（不同票之间）——留后续优化（变异 race condition 需改审 dispatch prompt，scope 加大）
- 文件路径声明/机械冲突检测——违反 ticket 不预写文件路径的设计取向（`SKILL.md:260`）
- `impl_route.py` / `ship_gate.py` 代码改动——不需要

[spec-review-amendment] ~~每 ticket 开子分支/worktree 隔离~~：已升级为 Goal（Claude 宿主使用 `isolation: "worktree"`）。gate 契约零改动（已验证 `done_task_ids` 穿透 merge commit）。

## Compliance

N/A
