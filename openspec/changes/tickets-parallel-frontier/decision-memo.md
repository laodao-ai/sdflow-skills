---
schema_version: 1
change: tickets-parallel-frontier
branch: feat/tickets-parallel-frontier
generated_at: 2026-08-02T11:30:38+08:00
decision_hash: 4d69b0210011
---

# 决策纪要 · tickets-parallel-frontier

## 目标态

tickets 管线依赖图无阻塞边的 ticket 并行执行，缩短多票 change 的墙钟。

## 拍板决策

- **D3 并行模式下 review-package 用逐 ticket 文件范围隔离 diff** — 依据：并行 implementer 的 commit 在 git 历史上交错，`BASE..HEAD` 会包含所有 ticket 的变更；**做法**：编排层记录 `PARALLEL_BASE`，审 T2 时用 `git diff PARALLEL_BASE..HEAD -- $(git diff --name-only <T2 commits>)` 隔离 T2 的文件；**砍掉的候选**：按 commit SHA 范围切（交错 commit 下 `T2_first^..T2_last` 会包含 T3 的 commit，不可靠）
- **D2 并行 implementer 的 dispatch prompt 必须要求按文件名 `git add`** — 依据：并行 implementer 共享工作树，`git add .` / `git add -A` 会暂存别人的改动；**砍掉的候选**：无（串行模式下也是好习惯，并行模式下是硬约束）
- **D1 并行 implementer + 串行双轴审** — 依据：impl 通常是每票墙钟大头，并行 impl 已拿到主要收益；双轴审并行需改审的 dispatch prompt（变异须在 scratchpad 做，memory `parallel-reviewers-mutate-same-worktree`），scope 加大但增量收益小；**砍掉的候选**：双轴审也并行（增量收益小、改动面大、变异 race condition 风险，④ 简化留后续优化）

## 承重约束

- **C1 同分支方案下 gate 完成窗口零改动** — 验证方式：读 `ship_gate.py` 的窗口算法 + checkpoint 标签后置纪律；**证据锚**：`ship_gate.py:1797-1800`（`done_task_ids` + `checkbox_done_ids` 并集在 `[plan_first_sha, HEAD]` 窗口内扫）、`sdflow-implement/SKILL.md:547`（implementer 实现期 MUST NOT 带完成标签，标签由执行模式审后补打 ⇒ 并行 implementer 不产生标签竞争）
- **C3 并行 implementer 异常处理 = 等全部返回后逐个处理** — 验证方式：Agent tool 无中途取消能力（harness 约束）；白跑成本 = 个别 implementer token（BLOCKED 罕见，pilot-log 样本 #1：5 票 0 BLOCKED）；**证据锚**：`tickets-pilot-log.md` 样本 #1（5 票全 DONE）；harness 行为（并行 Agent 调用等全部返回）
- **C2 并行安全保证是语义层约束，非机械门** — 验证方式：ticket 不写文件路径（`SKILL.md:260` "MUST NOT 预写实现代码或具体文件路径"），出票时无确定性信号可判文件重叠；**证据锚**：`SKILL.md:260`；**诚实边界**：出票模型判断 + 执行时 `git add` 冲突 fail-loud 兜底，人 2026-08-02 明确接受

## 接受的边角

- 并行 implementer 中某个 BLOCKED 时其余已白跑 — 概率：低（pilot-log 5 票 0 BLOCKED）；影响：token 浪费（系统镜），无代码副作用（普通 commit 可 revert）；完美成本：需 harness 支持取消正在运行的子代理（不存在该能力）；**为何接受**：成本天花板 = 2-3 个 implementer 的 token，远低于重新手动管理的成本
- 并行 implementer 碰同一文件（C2 的边角失败模式） — 概率：低（vertical-slice 设计 + 出票语义约束）；影响：git add 冲突 fail-loud、需人介入（开发循环镜）；完美成本：需 ticket 声明文件路径（违反 SKILL.md:260 的设计取向）；**为何接受**：fail-loud 兜底确保不静默损坏，出票约束在上游减少概率

## 三镜代价

本次无 TG-23 命中。
