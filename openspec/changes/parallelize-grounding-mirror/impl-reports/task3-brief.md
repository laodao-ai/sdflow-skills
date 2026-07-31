### Task 3: 验证一致性

**Blocked-by:** 2
**R-ID:** R1

通读改写后的 `sdflow-spec-review/SKILL.md`，逐条对照 spec delta 的 4 个 Scenario 确认一致：
1. Scenario「阶段二收尾」：编排器输出一份已去重合并的报告
2. Scenario「领域/对抗镜等待 autoplan 先行」：MUST 等 checkpoint
3. Scenario「接地镜与 autoplan 并行」：MAY 同一时刻 dispatch
4. Scenario「amendment 后不补跑接地镜」：SHALL NOT 补跑

同时确认 anchor_lint / lens-metric / fanout-capability 锚语义不受影响（通读确认，无机械测试需新增）。

验收标准：
- [ ] 4 个 Scenario 逐条确认与 SKILL.md 条款一致
- [ ] anchor_lint 锚行语义不受影响（mirrors= 仍包含 grounding）
- [ ] lens-metric 体系不受影响（接地镜仍产 findings、仍被 emitter 归约）
- [ ] fanout-capability 锚行语义不受影响（记的是「跑了哪些镜」，不是「何时跑的」）

