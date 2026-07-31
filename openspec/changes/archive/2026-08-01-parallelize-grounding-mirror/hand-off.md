# Hand-off — parallelize-grounding-mirror

## ✅ 完成了什么

- 串行纪律〔T20〕分治：领域/对抗镜 MUST 等 Step1 checkpoint，接地镜 MAY 并行起跑（`sdflow-spec-review/SKILL.md:200`，`test_step2_serial_must_sentence` 绿）
- Step2 fan-out 编排拆为两段 dispatch + ASCII 时序图（`SKILL.md:235-247`，`test_both_skills_probe_precedes_fanout_dispatch` 绿）
- Step1 前向指针——提示执行者在进入 autoplan 的同时按 dispatch① 条款踢出接地镜（`SKILL.md:184-185`）
- 能力探针时机前移至 Step1 开始时，一次探针共用（`SKILL.md:210`）
- 旧兜底条款（「若历史运行已并行…增量核对」）已删除
- spec delta 内部措辞修正（Scenario 补 `/history`，与 Requirement 主文对齐）
- 测试更新：`test_serial_discipline` + `test_probe_precedes_fanout_dispatch` 适配新措辞
- `openspec validate` 绿

## ⏳ 未完成 / 延后

- 无 buglist / todolist 新增项（issues sweep: 0 项）
- 无延后的 ≥2 方案决策
- 无 verify Minor 缺口

## ▶ 下一阶段建议

本 change 为 roadmap `workflow-cost-optimization` P3 Leg 2（接地镜流水线）的交付。建议下一步：
- 在运行 checkout 跑 `/sdflow-upgrade` 激活新条款
- 观测接地镜并行运行效果（spec-review 墙钟是否降低）
- 二级文档 `docs/workflow-skills/sdflow-spec-review.md:81`（仍写"一条消息内全部派出"）在后续维护 change 中同步更新
