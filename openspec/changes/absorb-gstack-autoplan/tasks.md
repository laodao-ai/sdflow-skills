## 1. Bundle 机械层同步(P0)

- [ ] 1.1 `lens-metric-contract.md` fold 块:`autoplan-ceo/design/eng/dx: broad` 四行替换为 `strategy: broad` + `plan-eng: broad`(直接替换不共存)〔Req: workflow-metrics·度量锚契约〕
- [ ] 1.2 `anchor_lint` golden 测试补用例:spec-review 报告 `mirrors=` 含 `broad` token、`step1-broad-review` 锚 `mode="subagent|main-session"` 两枚举(枚举常量零改动,只补用例证既有文法覆盖新形态)〔Req: host-adaptive-execution·子代理不可用时镜数如实降级〕
- [ ] 1.3 `sdflow-retro` 步类型解析:`checkpoint(spec-review-autoplan)` 历史标签保留识别、新轮次不再要求;调整 `tests/test_retro_report.py` 相应断言〔Req: spec-workflow·REMOVED 阶段二产出单一合并报告 之 Migration〕
- [ ] 1.4 bundle 规则文档行为面改写:`spec-review.md`(L2 表 autoplan 行、瘦跑注记)、`workflow.md` 阶段二步骤表、`reference/quality-layering.md`——广审载体改述为自持双镜〔Req: spec-workflow·阶段二自持广审并单批 dispatch 产出单一合并报告〕

## 2. sdflow-spec-review SKILL 重写(P0)

- [ ] 2.1 Step1/Step2 合并为单批 dispatch:删两段 dispatch 时序图与 T20 分治条款,新镜表加 strategy/plan-eng 行(职责清单=base R 项划分,见 design DD2),删「与 autoplan 的分工」表与「防重叠 1.4」条款(由 base/domains 分工线替代)〔Req: spec-workflow·阶段二自持广审并单批 dispatch 产出单一合并报告〕
- [ ] 2.2 `step1-broad-review` 锚 mode 枚举换 `subagent|main-session`,`subagents="unavailable"` 时广审主 session 亲做(恒跑守卫,`mirrors=` 计入 broad)〔Req: host-adaptive-execution·子代理不可用时镜数如实降级〕
- [ ] 2.3 Step1 的 autoplan 原生执行/gstack-review.md 落盘/outside_voice_guard 调用/checkpoint(spec-review-autoplan) 四环节删除;design-voice 恒自跑(回落路径转正);`guard=` 字段从 outside-voice 锚文法移除〔Req: spec-workflow·REMOVED outside-voice 复用挂反静默守卫〕
- [ ] 2.4 lens-metric 落锚指引同步:roster 行键 raw 名 strategy/plan-eng(折叠 broad),报告模版段落更新〔Req: workflow-metrics·度量锚契约〕

## 3. 守卫脚本退役(P0,任务组 1/2 完成且 pytest 绿后执行)

- [ ] 3.1 删除 `sdflow-init/assets/workflow/tools/outside_voice_guard.py` 及其 tests;全仓 `/usr/bin/python3 -m pytest` 绿〔Req: spec-workflow·REMOVED outside-voice 复用挂反静默守卫〕

## 4. DX 吸收(P1)

- [ ] 4.1 `trigger-catalog.md` 新增 TG-28(developer-facing 交付面:CLI/公共 API/SDK/skill/配置面/错误信息;领域列 `devex`,spec-review-only;不入 HR-TG)〔design DD6〕
- [ ] 4.2 新建 `spec-checklists/domains/devex.md`:TTHW 分档基准、错误信息 problem+cause+fix、命名可猜性/默认值/渐进式披露、升级路径、Claude Code Skill DX 清单(收/不收判据见 design DD6)〔design DD6〕
- [ ] 4.3 `openspec/INDEX.md` 同步新增的 bundle 规则文件(devex.md)〔CLAUDE.md·INDEX 同步〕

## 5. sdflow-roadmap 侧(P1)

- [ ] 5.1 review 节重写:判定点②(商业化分档)删除、判定留痕总则三判定点改两判定点、恒跑 strategy/plan-eng 双镜(镜职责同源引用 spec-review SKILL,不复制)、失败处置改述(未审待恢复语义不变)〔Req: roadmap-planning·review 恒跑自持双镜与跨模型声〕
- [ ] 5.2 sync-only outside voice 接入:site=`roadmap-voice`,context=design.md Decisions+roadmap.md(>200KB 收敛),run 目录 `openspec/roadmaps/{name}/.outside-voice/<run-id>/`,前台 `--timeout 300` 外层 ≥330000ms,⑦ 表映射,失败同族 fallback,task-log 一行 runner/reason_code 留痕〔Req: roadmap-planning·review 恒跑自持双镜与跨模型声〕

## 6. 文档 sweep 与验收(P2 + 收尾)

- [ ] 6.1 `spec-checklists/domains/frontend.md` 增补 design 镜 litmus/AI-slop 精华 R 项(P2)〔design DD6〕
- [ ] 6.2 文档面 sweep:`openspec/CONTEXT.md`「镜」词条 autoplan 例句、`docs/workflow-skills/gstack-autoplan.md` 降级为非运行时参考、`docs/workflow-skills/sdflow-spec-review.md`、`docs/external-dependencies.md` §5/§8、`WORKFLOW-GUIDE.md`(assets 权威源侧)、README(如涉及)〔proposal·What Changes 文档 sweep〕
- [ ] 6.3 关闭 T268(resolved_by=absorb-gstack-autoplan)+ 若拷问/实现期发现新边角按 fold-vs-defer 处置〔proposal·Why〕
- [ ] 6.4 验收:`grep -rn "autoplan\|gstack" sdflow-spec-review/SKILL.md sdflow-roadmap/SKILL.md` 归零;全仓 pytest 绿;dogfood 本 change 评审报告产出 strategy/plan-eng raw 名 broad 行 + 新 mode 锚且 anchor_lint 通过〔proposal·Success Metrics〕

## 测试覆盖注记(TG-18)

| code path | 测试类型 |
|---|---|
| fold 表新 raw 名折叠 / 旧名 fail-closed | `lens_metric_emit` 既有单测 + golden fixture 更新(1.1) |
| anchor_lint mirrors broad / 新 mode 锚 | golden 用例(1.2) |
| retro 标签历史识别 | `test_retro_report.py` 断言调整(1.3) |
| guard 退役无残留引用 | 全仓 pytest + grep 验收(3.1/6.4) |
| SKILL 指令层(单批 dispatch/voice 转正/roadmap 双镜) | 无机械测试面——dogfood 评审实跑核验(6.4),诚实边界:指令层靠执行方自报 |
