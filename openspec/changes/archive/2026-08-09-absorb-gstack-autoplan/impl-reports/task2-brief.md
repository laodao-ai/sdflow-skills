### Task 2: spec-review SKILL 重写与同源注入机制

**Blocked-by:** 1
**R-ID:** R-spec-workflow, R-host-adaptive-execution

spec-review SKILL 的 Step1/Step2 合并为单批 dispatch + 锚枚举换值 + guard 环节删除 + 同源注入机制建立:

1. `sdflow-spec-review/SKILL.md` 重写:删两段 dispatch 时序图与 T20 分治条款;新镜表加 strategy/plan-eng 行(职责清单=DD2 base R 项划分,含防重叠语义补句);删「与 autoplan 的分工」表与「防重叠 1.4」条款。
2. `step1-broad-review` 锚 mode 枚举 `native|simulated` → `subagent|main-session`;`subagents="unavailable"` 时广审主 session 亲做描述;mode 诚实边界声明。
3. Step1 的 autoplan 原生执行/gstack-review.md 落盘/outside_voice_guard 调用/checkpoint(spec-review-autoplan) 四环节删除;design-voice 恒自跑(回落路径转正);`guard=` 字段从 outside-voice 锚文法移除。
4. lens-metric 落锚指引同步:roster 恒一行 `lens="broad"`,两广审 hits raw=strategy/plan-eng 经 fold 折叠;报告模板段落更新。
5. 广审镜定义真相源:`sdflow-init/assets/snippets/broad-mirrors.md` 新建;`hack/sync_principles.py` 扩展(或同构小脚本)注入 `sdflow-spec-review/SKILL.md` 与 `sdflow-roadmap/SKILL.md` 的 `sdflow:broad-mirror-def` 托管块;`setup.sh --check` 门禁。
6. bundle 规则文档行为面改写:`spec-review.md`(L2 表 autoplan 行、瘦跑注记)、`workflow.md` 阶段二步骤表、`reference/quality-layering.md` 广审载体改述。

- [ ] spec-review SKILL 中 autoplan/gstack 引用归零(grep 验证)
- [ ] 单批 dispatch 结构(strategy/plan-eng/领域/对抗/接地一条消息并行)描述完整
- [ ] step1-broad-review 锚 mode 枚举为 subagent|main-session
- [ ] guard 调用/gstack-review.md/checkpoint(spec-review-autoplan) 环节已删
- [ ] broad-mirrors.md 真相源创建 + 注入脚本扩展 + setup.sh --check 门禁
- [ ] spec-review.md/workflow.md/quality-layering.md 规则文档同步
- [ ] lens-metric roster/模板更新

