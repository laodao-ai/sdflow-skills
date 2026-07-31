### Task 1: 串行纪律条款改写——分治接地镜与领域/对抗镜

**Blocked-by:** none
**R-ID:** R1

将 `sdflow-spec-review/SKILL.md` 第 197 行附近的串行纪律条款〔T20〕从「全部镜 MUST 等 Step1 完成」改为分治：
- 接地镜：MAY 与 Step1 并行起跑（读当前盘面的 design/specs + 真实代码核验代码事实）
- 领域/对抗镜：MUST 仍等 Step1 checkpoint 完成（它们依赖 autoplan amendment 对 design/specs 的修订）
- 删除该条款末尾的兜底条款「若历史运行已并行…Step3 须增量核对」——并行已是接地镜的默认行为，不再是需要额外注明的例外

验收标准：
- [ ] 串行纪律条款明确区分接地镜（MAY 并行）与领域/对抗镜（MUST 等 checkpoint）
- [ ] 兜底条款已删除
- [ ] 条款措辞与 spec delta 的 Scenario「领域/对抗镜等待 autoplan 先行」和 Scenario「接地镜与 autoplan 并行」一致

