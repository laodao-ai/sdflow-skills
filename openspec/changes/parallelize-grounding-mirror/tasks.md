## 1. 串行纪律条款改写

- [ ] 1.1 `sdflow-spec-review/SKILL.md:197` 串行纪律〔T20〕从「全部镜 MUST 等 Step1 完成」改为分治：接地镜 MAY 并行，领域/对抗镜 MUST 等 checkpoint
- [ ] 1.2 Step2 fan-out 编排段（:232 上方）拆为两段 dispatch 描述：接地镜在 Step1 启动时 dispatch、领域/对抗镜在 Step1 checkpoint 后 dispatch
- [ ] 1.3 删除 :197 末尾的兜底条款「若历史运行已并行…Step3 须增量核对」——并行已是默认行为，不再是例外

## 2. 能力探针时机适配

- [ ] 2.1 能力探针（:207-230）明确：接地镜提前 dispatch 前仍须过能力探针；探针结果对接地镜和领域/对抗镜共用（一次探针，不重复）

## 3. 验证

- [ ] 3.1 主 spec delta（`spec-workflow`）的 4 个 Scenario 逐条对照 SKILL.md 条款确认一致
- [ ] 3.2 `openspec validate parallelize-grounding-mirror --strict --type change` 绿
- [ ] 3.3 anchor_lint / lens-metric / fanout-capability 锚语义不受影响（通读确认，无机械测试需新增——改的是 prose 条款，不是脚本）

## 测试覆盖

| 任务 | 自动化测试 |
|---|---|
| 1.1–1.3 | 无（prose 条款改写，无脚本产物） |
| 2.1 | 无（prose 条款改写） |
| 3.1–3.3 | openspec validate（机械）+ 人读核对 |
