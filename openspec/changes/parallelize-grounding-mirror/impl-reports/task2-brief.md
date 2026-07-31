### Task 2: Step2 fan-out 编排拆为两段 dispatch

**Blocked-by:** 1
**R-ID:** R1

将 `sdflow-spec-review/SKILL.md` 第 232 行附近的 Step2 fan-out 编排段拆为两段 dispatch 描述：
- 接地镜在 Step1 启动时（能力探针通过后）即 dispatch，与 autoplan 并行
- 领域镜 + 对抗镜在 Step1 checkpoint 完成后 dispatch
- 能力探针明确：在 Step1 开始时即跑（而非 Step2 前），探针结果对所有镜共用（一次探针，不重复）
- Step3 合并逻辑不变——接地镜 findings 无论何时完成都进同一合并池

验收标准：
- [ ] fan-out 段清晰描述两段 dispatch 的时序关系
- [ ] 能力探针时机明确为 Step1 开始时（而非 Step2 前），一次探针共用
- [ ] 接地镜 dispatch 时序 = Step1 启动后（能力探针通过后）
- [ ] 领域/对抗镜 dispatch 时序 = Step1 checkpoint 后

