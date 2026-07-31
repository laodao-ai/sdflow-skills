---
impl-pipeline: tickets
---

## Global Constraints

以下逐字摘自 design.md 的 MUST/MUST NOT/SHALL 硬约束与 Compliance 条款：

- **改动面仅 `sdflow-spec-review/SKILL.md` 一个文件**，三处条款改写，不涉及脚本/测试/其它 SKILL 文件
- 接地镜 MAY 与 Step1 autoplan 并行起跑（读当前盘面的 design/specs + 真实代码）
- 领域镜与对抗镜 MUST 仍等 Step1 checkpoint 完成后才 fan-out（它们依赖 autoplan amendment 对 design/specs 的修订）
- autoplan amendment 后 SHALL NOT 自动补跑接地镜（decision-memo D1；由 code-review 的 grounding/history 镜兜底）
- 零额外 token 成本（不补跑）
- MUST NOT 改 `sdflow-code-review`（无等价串行约束）
- MUST NOT 改 anchor/lens-metric 体系
- 能力探针时机前移但逻辑不变：接地镜提前 dispatch 前仍须过能力探针，探针结果对接地镜和领域/对抗镜共用（一次探针，不重复）

### Task 1: 串行纪律条款改写——分治接地镜与领域/对抗镜

**Blocked-by:** none
**R-ID:** R1

将 `sdflow-spec-review/SKILL.md` 第 197 行附近的串行纪律条款〔T20〕从「全部镜 MUST 等 Step1 完成」改为分治：
- 接地镜：MAY 与 Step1 并行起跑（读当前盘面的 design/specs + 真实代码核验代码事实）
- 领域/对抗镜：MUST 仍等 Step1 checkpoint 完成（它们依赖 autoplan amendment 对 design/specs 的修订）
- 删除该条款末尾的兜底条款「若历史运行已并行…Step3 须增量核对」——并行已是接地镜的默认行为，不再是需要额外注明的例外

验收标准：
- [x] 串行纪律条款明确区分接地镜（MAY 并行）与领域/对抗镜（MUST 等 checkpoint）
- [x] 兜底条款已删除
- [x] 条款措辞与 spec delta 的 Scenario「领域/对抗镜等待 autoplan 先行」和 Scenario「接地镜与 autoplan 并行」一致

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

### Task 4: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task4-verify-all.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

本 change 为纯 prose 条款改写，无脚本产物，预期：
- 单元测试：`pytest`（本仓有 pytest 测试，虽然本 change 不改脚本，跑一遍确认无回归）
- 集成测试：未覆盖（本仓无集成测试层）
- e2e 测试：未覆盖（本仓无 e2e 测试层）
- `openspec validate parallelize-grounding-mirror --strict --type change`（若 CLI 可用）

- [ ] 单元测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
