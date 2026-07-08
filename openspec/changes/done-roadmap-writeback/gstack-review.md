<!-- sdflow:step1-broad-review v1 mode="simulated" -->
# 广审留档（Step1 · simulated）— done-roadmap-writeback

> mode="simulated"：子代理跑 CEO/design/eng/DX + 6 决策原则视角，未原生调 gstack autoplan skill（嵌套 spec-review 内不现实）。诚实标注降级，findings 已并入 spec-review-report.md 合并池。侧信道佐证：codex outside-voice（design-voice）另经 `~/.sdflow/hack/outside-voice.sh exec` 真实调用（exit 0，见 .outside-voice/ 调试留档与报告 outside-voice 锚行）。

## 广审 findings（CEO/design/eng/DX）〔gstack-amendment〕

- **[高]** 自动化可靠性最终系于「人记得写锚」——把"忘记勾复选框"换成"忘记写关联锚"，漏锚纯静默跳过。建议先零脚本"提醒式"版本观察漏填率是否真下降，再决定 6 件投入。→ 报告 Q1/Q3。
- **[高]** SKILL:195 误引：原文是"`/opsx:verify` 接 post-hook 校验 task-log Review 处置穷尽性"（校验≠写入、verify≠done），被过度泛化成"改 sdflow-roadmap 设计原意兑现"。→ 报告 D5。
- **[中]** 3.5 回写步未落"谁跑/什么档位"，含判断活却未定归属。建议折进第三步 archive 中档子代理。→ 报告 D6。
- **[中]** D-6 未区分"锚 name 打错字"——被当无关联静默吞，正是反静默最该抓的。→ 报告 D1/B3。
- **[中]** task 1.2"起手 MUST 带锚规范"改哪个文件不明；关联锚是 workflow 规则须改 sdflow-init/assets/workflow/（权威源）再 update 推下游（dogfooding 红线）。→ 报告 D7。
- **[中·CEO]** 6 件 scope 服务基数小（2 roadmap，1 高频），边际收益存疑。建议先只认新格式、旧 2 待需再迁。→ 报告 Q3。
- **[低]** roadmap-link P2 意味锚多半人手敲，格式错要等归档才 fail-closed，反馈回路长。建议 propose/spec-review 阶段校验锚格式。→ 报告 Q1/A。
- **[低]** 新"状态"enum 列与"就绪度"散文列语义相近、可能并存混淆。建议迁移时评估吸收/替代。→ 报告 D4/D-c。

**总评**：设计经 grill 认真纠偏（目标态/best-effort 两处范式修正站得住），机械/判断切分清楚，但主顾虑 = scope 与实际收益不成比例 + 核心可靠性系于"人会记得写锚"（正是原痛点本身）+ SKILL:195 误引。建议削最小可行版或补齐锚机械闭环 + 去误引 + 补 3.5 model 档位。
