### Task 5: 文档 sweep 与验收

**Blocked-by:** 1,2,3,4
**R-ID:** R-spec-workflow, R-workflow-metrics

全面文档 sweep + 验收 + 盲测:

1. 文档面 sweep:`openspec/CONTEXT.md`「镜」词条 autoplan 例句改述;`docs/workflow-skills/gstack-autoplan.md` 降级为非运行时参考;`docs/workflow-skills/sdflow-spec-review.md` 同步;`docs/external-dependencies.md` §5/§8;`WORKFLOW-GUIDE.md`(assets 权威源侧);README(如涉及);`docs/workflow-map.md`(:34 流程描述、:169 guard 工具行);`docs/workflow-overview.md`(:123 CP1 checkpoint 节点)。
2. 关闭 T268(resolved_by=absorb-gstack-autoplan)。
3. 归档盲测(逐声边际贡献):选 3-5 份含 broad 独家 findings 的归档 change,分别单独跑 strategy/plan-eng/design-voice 三声,测旧 broad 独家高危召回率与各声边际独家召回;盲测报告随 change 归档。
4. 最终验收:`grep -rn "autoplan\|gstack" sdflow-spec-review/SKILL.md sdflow-roadmap/SKILL.md sdflow-init/assets/workflow/`(排除 reference/)归零 + 读码确认两 SKILL 无条件调用 gstack 分支;全仓 pytest 绿。

- [ ] CONTEXT.md/docs/workflow-skills/WORKFLOW-GUIDE/external-dependencies/workflow-map/workflow-overview 全部 sweep 完成
- [ ] T268 已关闭
- [ ] 盲测报告落盘(3-5 份归档 change × 3 声)
- [ ] grep 验收归零
- [ ] 全仓 pytest 绿

