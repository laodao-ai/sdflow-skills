## 1. Bundle 机械层同步(P0)

- [ ] 1.1 `lens-metric-contract.md` fold 块:`autoplan-ceo/design/eng/dx: broad` 四行替换为 `strategy: broad` + `plan-eng: broad`(直接替换不共存)〔Req: workflow-metrics·度量锚契约〕
- [ ] 1.2 `anchor_lint` golden 测试补用例:spec-review 报告 `mirrors=` 含 `broad` token、`step1-broad-review` 锚 `mode="subagent|main-session"` 两枚举(枚举常量零改动,只补用例证既有文法覆盖新形态)〔Req: host-adaptive-execution·子代理不可用时镜数如实降级〕
- [ ] 1.3 `sdflow-retro` 步类型解析:**确认**既有前缀规则(`_STAGE_RULES` 的 `("spec-review","spec-review")` startswith 匹配)与既有断言 `tests/test_retro_report.py:129` 已覆盖历史标签识别——**勿新增冗余规则/断言**(评审已实跑核验现绿)[spec-review-amendment M14:原任务按字面为 no-op,防执行期造无用功]〔Req: spec-workflow·REMOVED 阶段二产出单一合并报告 之 Migration〕
- [ ] 1.4 bundle 规则文档行为面改写:`spec-review.md`(L2 表 autoplan 行、瘦跑注记)、`workflow.md` 阶段二步骤表、`reference/quality-layering.md`——广审载体改述为自持双镜〔Req: spec-workflow·阶段二自持广审并单批 dispatch 产出单一合并报告〕
- [ ] 1.5 `lens-metric-contract.md` 散文同步:「跨模型性」段与 fold 注记中「anchor_lint 与 outside_voice_guard 各自本地重实现/双实现」表述改为 anchor_lint 单实现(:19 附近、:44 附近 fold prose 的 autoplan 例名一并换新 raw 名)[spec-review-amendment M1]〔Req: host-adaptive-execution·锚行合法组合矩阵(MODIFIED)〕
- [ ] 1.6 `anchor_lint.py` `_MIRRORS_UPGRADE_HINT`(:680 附近)失效修复指引 `sdflow-init update` → 「回运行 checkout 跑 `bash setup.sh`」(与 lens_metric_emit 既有正确文案对齐)[spec-review-amendment M3/K-1,fold-vs-defer:相关且低改动量,并入本 change]〔Req: spec-workflow·workflow bundle 改在权威源(MODIFIED)〕

## 2. sdflow-spec-review SKILL 重写(P0)

- [ ] 2.1 Step1/Step2 合并为单批 dispatch:删两段 dispatch 时序图与 T20 分治条款,新镜表加 strategy/plan-eng 行(职责清单=base R 项划分,见 design DD2),删「与 autoplan 的分工」表与「防重叠 1.4」条款(由 base/domains 分工线替代)〔Req: spec-workflow·阶段二自持广审并单批 dispatch 产出单一合并报告〕
- [ ] 2.2 `step1-broad-review` 锚 mode 枚举换 `subagent|main-session`,`subagents="unavailable"` 时广审主 session 亲做(恒跑守卫,`mirrors=` 计入 broad)〔Req: host-adaptive-execution·子代理不可用时镜数如实降级〕
- [ ] 2.3 Step1 的 autoplan 原生执行/gstack-review.md 落盘/outside_voice_guard 调用/checkpoint(spec-review-autoplan) 四环节删除;design-voice 恒自跑(回落路径转正);`guard=` 字段从 outside-voice 锚文法移除〔Req: spec-workflow·REMOVED outside-voice 复用挂反静默守卫〕
- [ ] 2.4 lens-metric 落锚指引同步:**roster 恒一行 `lens="broad"`(canonical——emitter roster 校验拒收 raw 名);两广审镜 findings 各自以 `hits[].raw="strategy"/"plan-eng"` 进入 emitter 输入、由 fold 表折叠归属到该唯一 broad 行**;报告模版段落更新 [spec-review-amendment M4:原「roster 行键 raw 名」按 emitter 契约 schema-invalid]〔Req: workflow-metrics·度量锚契约〕

## 3. 守卫脚本退役(P0,任务组 1/2 完成且 pytest 绿后执行)

- [ ] 3.1 删除 `sdflow-init/assets/workflow/tools/outside_voice_guard.py` 及其 tests;全仓 `/usr/bin/python3 -m pytest` 绿〔Req: outside-voice-reuse-guard·REMOVED(全三条)+ spec-workflow·REMOVED outside-voice 复用挂反静默守卫〕
- [ ] 3.2 矩阵 golden 迁移:原 `test_outside_voice_guard.py` Step 5 跨工具全笛卡尔用例改造为 anchor_lint 单工具矩阵自测(枚举域仍读契约机读块,分类逐条断言符合矩阵定义),**在 3.1 删除前迁移、MUST NOT 随文件删除静默丢覆盖面** [spec-review-amendment M1]〔Req: host-adaptive-execution·锚行合法组合矩阵(MODIFIED)〕

## 4. DX 吸收(P1)

- [ ] 4.1 `trigger-catalog.md` 新增 TG-28(developer-facing 交付面:**新增/修改/重命名/废弃/删除** CLI 命令/flag/公共 API/SDK/skill 调用契约/配置面(消费方可见)/错误信息;领域列 `devex`,spec-review-only;不入 HR-TG——判定「否」显式记录)[spec-review-amendment M17 措辞同步]〔design DD6〕
- [ ] 4.2 新建 `spec-checklists/domains/devex.md`:**条目一律表式 `ID/触发条件/必需文本证据/PASS/FAIL/N.A`,无证据输出 `UNVERIFIABLE`**;TTHW 分档基准(附文本推导规则)、错误信息 problem+cause+fix、命名可猜性/默认值/渐进式披露、升级路径、Claude Code Skill DX 清单(sdflow 新作,非蒸馏)(收/不收判据见 design DD6)[spec-review-amendment M17]〔design DD6〕
- [ ] 4.3 `openspec/INDEX.md` 同步:新增 devex.md 行;**移除 `outside-voice-reuse-guard` capability 行(:54)与 `outside_voice_guard.py` 工具行** [spec-review-amendment M1]〔CLAUDE.md·INDEX 同步〕

## 5. sdflow-roadmap 侧(P1;**门:任务组 2 完成后执行**——DD7 引用/同源 spec-review SKILL 重写后的镜定义段,不可先行 [spec-review-amendment adv3-F4:原「独立可验」有隐藏顺序依赖])

- [ ] 5.1 review 节重写:判定点②(商业化分档)删除、判定留痕总则三判定点改两判定点、恒跑 strategy/plan-eng 双镜(镜职责同源引用 spec-review SKILL,不复制)、失败处置改述(未审待恢复语义不变)〔Req: roadmap-planning·review 恒跑自持双镜与跨模型声〕
- [ ] 5.2 sync-only outside voice 接入:site=`roadmap-voice`,context=design.md Decisions+roadmap.md(>200KB 收敛),run 目录 `openspec/roadmaps/{name}/.outside-voice/<run-id>/`,前台 `--timeout 300` 外层 ≥330000ms,⑦ 表映射,失败同族 fallback,task-log 一行 runner/reason_code 留痕〔Req: roadmap-planning·review 恒跑自持双镜与跨模型声〕

## 6. 文档 sweep 与验收(P2 + 收尾)

- [ ] 6.1 `spec-checklists/domains/frontend.md` 增补 design 镜 litmus/AI-slop 精华 R 项(P2)〔design DD6〕
- [ ] 6.2 文档面 sweep:`openspec/CONTEXT.md`「镜」词条 autoplan 例句、`docs/workflow-skills/gstack-autoplan.md` 降级为非运行时参考、`docs/workflow-skills/sdflow-spec-review.md`、`docs/external-dependencies.md` §5/§8、`WORKFLOW-GUIDE.md`(assets 权威源侧)、README(如涉及)、**`docs/workflow-map.md`(:34 流程描述、:169 guard 工具行)、`docs/workflow-overview.md`(:123 CP1 checkpoint 节点)** [spec-review-amendment M13/E2]〔proposal·What Changes 文档 sweep〕
- [ ] 6.3 关闭 T268(resolved_by=absorb-gstack-autoplan)+ 若拷问/实现期发现新边角按 fold-vs-defer 处置〔proposal·Why〕
- [ ] 6.4 验收(与 proposal Success Metrics 修订稿对齐 [spec-review-amendment M4/M7/M13]):`grep -rn "autoplan\|gstack" sdflow-spec-review/SKILL.md sdflow-roadmap/SKILL.md sdflow-init/assets/workflow/`(排除 `reference/`)归零 + 读码确认两 SKILL 无条件调用 gstack 分支;全仓 pytest 绿;dogfood 本 change 评审报告产出 `lens="broad"` 锚行(hits 含 raw strategy/plan-eng)+ mode 新枚举 step1 锚且 anchor_lint 通过〔proposal·Success Metrics〕

## 测试覆盖注记(TG-18)

| code path | 测试类型 |
|---|---|
| fold 表新 raw 名折叠 / 旧名 fail-closed | `lens_metric_emit` 既有单测 + golden fixture 更新(1.1) |
| anchor_lint mirrors broad / 新 mode 锚 | golden 用例(1.2) |
| retro 标签历史识别 | `test_retro_report.py` 断言调整(1.3) |
| guard 退役无残留引用 | 全仓 pytest + grep 验收(3.1/6.4) |
| SKILL 指令层(单批 dispatch/voice 转正/roadmap 双镜) | 无机械测试面——dogfood 评审实跑核验(6.4),诚实边界:指令层靠执行方自报 |
