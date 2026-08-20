wrote openspec/changes/sweep-pool-debt-2026-08/impl-reports/task3-brief.md: 12 lines
-ID:** IO1（impl-orchestration：切片偏离审计行 SHALL 被代码审 scope 审计对账消费）

给 `sdflow-code-review` 的 scope 审计接上 `planning-decisions.md` 切片偏离对账，使出票期申报的偏离在代码审阶段被机械核对。

> 执行说明（并行安全）：本票与票 1 均改 `sdflow-code-review/SKILL.md`（本票动 Step1 输入清单，票 1 动 impl-review 重锚协议段，两节相隔）。Claude 宿主各票独立 worktree，编排层按号序 merge，`git merge --no-ff` 对相隔两节 3-way 干净合并、真冲突则 fail-loud（并行安全约束兜底）。见 `impl-reports/planning-decisions.md`。

- [ ] `sdflow-code-review/SKILL.md` Step1 输入清单加 `impl-reports/planning-decisions.md` 切片偏离行
- [ ] 对账逻辑三分支：静默偏离上报 / 已申报核对 / 无输入降级不中断

