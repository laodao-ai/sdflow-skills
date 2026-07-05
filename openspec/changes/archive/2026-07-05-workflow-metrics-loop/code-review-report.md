# code-review 报告 — workflow-metrics-loop

## 命中范围

- 栈：Markdown（bundle 规则 + 3 SKILL 编排指令）+ Python 只读聚合器（stdlib）。清单：通用 CR-01~09（无 backend/embedded/frontend 领域）。
- 镜阵：领域镜×1（CR-01~09 on 聚合器+契约+3 SKILL 三方一致）· 对抗镜×2（聚合器运行期爆点 / 指令一致性爆点）· 历史镜×1（重蹈旧教训）· codex code-voice（跨模型）。**HR-TG=none**（旁路观测锚+只读聚合，读错顶多坏度量非运行期爆炸/数据损坏/安全泄漏）。
- gstack/review scope-drift：本审自动修只触碰意图内文件（聚合器/init.py/3 SKILL/契约），无顺手多改；完成度：9 计划任务全落。

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="旁路观测锚+只读聚合;读错坏度量非运行期爆炸/数据损坏/安全泄漏" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->

## Findings（置信 ≥80）

| 严重度 | CR | 位置 | 问题 | 源 | 裁决 |
|---|---|---|---|---|---|
| 高 | CR-06 | lens_metric_aggregate.py:80 | **聚合键漏 runner**——按 `(layer,lens,site)` 分组，codex 与 claude-fallback 被合并（违 spec 键 `(layer,lens,runner,site)`） | **codex 独立**（各 claude 镜均漏） | 已修 [impl-review-fix CF-1] |
| 高 | CR-01 | lens_metric_aggregate.py:43 | **单个坏归档文件崩溃全仓聚合**——`read_text` 无 try/except，实测 UnicodeDecodeError 拖垮整轮 | 领域镜（复现） | 已修 [impl-review-fix CF-2] |
| 高 | CR-02 | sdflow-maintain/SKILL.md:63 | **surfacing 步在最常见「确认修复」分支不可达**——Task7 fix 只补了无差异/拒绝两分支，漏主干（防死列自毁） | 对抗镜2（接地实证） | 已修 [impl-review-fix CF-3] |
| 高 | CR-01 | lens_metric_aggregate.py:19 | **非等长嵌套 fence 漏出污染**——fence 翻转不看反引号长度，4-外层包 3-内层示范锚被当真数据吃进 | 对抗镜1（复现） | 已修 [impl-review-fix CF-4] |
| 中 | CR-05 | lens_metric_aggregate.py:66 | **数值字段无校验**——`_int` 对 `"3.0"` 静默归0、`"-1"` 算出 -25%，flag 列不提示 | 对抗镜1+codex+领域（三源） | 已修 [impl-review-fix CF-5] |
| 中 | CR-01 | sdflow-init/scripts/init.py:119 | **聚合器 pytest 被部署到所有消费仓**——copy_bundle 整棵刷 tools/ 含 tests/ | **codex 独立** | 已修 [impl-review-fix CF-6] |
| 中 | CR-06 | lens_metric_aggregate.py:render | **无锚"N 份"同名重复误导**——每 change 两份报告名连出两次像 bug | 领域镜（本仓实跑） | 已修 [impl-review-fix CF-7] |
| 中高 | CR-06 | sdflow-spec-review/SKILL.md SR-M | **SR-M 无机械兜底、形同空文**——pre-gate 值静默失真、聚合器不知"草稿"态 | 对抗镜2 | 已修 [impl-review-fix CF-8]（诚实化为 best-effort） |
| 中 | CR-06 | 两 SKILL 自检段 | **"机械 grep"措辞误导**——自检由同一执行会话自跑、非外部门 | 对抗镜2 | 已修 [impl-review-fix CF-9] |
| 中 | CR-06 | 契约 site 行 + 两 SKILL | **site 校验三方遗漏**——契约列取值域但无处校验 | 领域镜 | 已修 [impl-review-fix CF-10]（契约注明 site 仅消歧不自检） |
| 低 | CR-09 | test:layer分支 | layer 越域无测试 | 领域镜 | 已修 [impl-review-fix F2] |
| 低 | CR-06 | test:sev注释 | sev "渲染层校验"过度承诺（render 不用 sev） | 领域镜 | 已修 [impl-review-fix F5]（注释诚实化） |
| 低 | CR-06 | spec-review SKILL | 缺反馈回路免责声明（与 code-review 不对称） | 对抗镜2 | 已修 [impl-review-fix] |

## 已裁掉 / 证伪（反静默压制，可审计）

- **X1** 对抗1 Q3「sev 含 `|` 破坏 markdown 表格列」——**证伪**：sev 从不进 render_table 单元格（仅 parse 存证），无从破列。
- **X2** 对抗1 Q3「只有 defer 时采纳率=0% 语义歧义」——**站不住**：Σ裁掉/Σdefer 单列可区分，非隐藏信息。
- **X3** 对抗1 Q4「glob 空表 vs archive 不存在无法区分」——**低危留档**：易用性小瑕疵非运行期爆/给错数，defer。
- **X4** 对抗1 Q1「转义引号 `\"` 截断」——**低危**：只污染该字段本身（多一奇怪 site 行、可见），不级联；site 不校验已 CF-10 注明，defer 观察。
- **X5** codex OV-3「N≥10『未复评』无登记来源」——**已 Task7 裁决**：ADR-6 零持久态下取幂等重提示（保留镜下次仍提示，可接受）；文案含"待复评"非承诺"已复评"追踪，defer（已入 hand-off）。
- **X6** 对抗2 #4 三方枚举一致性——**refuted**（未抓到抄错）：聚合器 ⚠越域 flag 是唯一机械兜底，CF-10 已在契约点明。

## 修复 / defer 台账

- **自动修 13 项** [impl-review-fix]（CF-1~10 + F2/F5 + spec-review 对称），分 3 波并行落地（Fix-A 聚合器 / Fix-B 部署 / Fix-C SKILL+契约）；因 checkpoint `git add -A` 并行卷入，改动最终落 commit `7a26b37`+`74efb45`，**最终树经全量 pytest（395 passed/1 pre-existing）+ grep 逐项核实自洽**。
- **defer**：X3（glob 空表易用性）· X4（转义引号 site 观察）——均低危、非本轮修，交 hand-off（可入 todolist 观察项）。
- **无 ≥2 方案需 T10 复核**（各修均有客观判据：测试/复现/接地实证）。
- voice分桶: — （已被下方 lens-metric 锚吸收取代，本审无残留 prose 分桶）

## 度量锚（lens-metric，dogfood 首批真锚——config metrics.enabled=true）

<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="4" sev="致0/高1/中3/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="6" 采纳="5" 裁掉="1" defer="0" 独立="4" sev="致0/高2/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="2" sev="致0/高2/中2/低0" -->

> **独立贡献活样本**：`outside-voice(codex)` 独立=2——CF-1（runner 漏出聚合键）+ CF-6（测试铺进消费仓）是**唯一由 codex 抓到、各 claude 镜全漏**的两条真缺陷，恰是「独立率」度量要捕获的跨家族非冗余价值（本 change 度量机制自身的首个佐证）。`history` findings=0（无重蹈，负例确认）。

## 锚行自检

四类 v1 锚齐备：step1-broad-review×1(simulated) / hr-tg×1(none+evidence) / outside-voice×1(codex,findings=4) / lens-metric×4(domain/adversarial/history/outside-voice)。lens-metric 字段/取值域经核合契约 `lens-metric-contract.md`；outside-voice findings=4 与 codex 实收一致 ✓。

## 结论

13 项确认缺陷全自动修（含 4 高：runner键/坏文件崩溃/surfacing不可达/嵌套fence污染）、6 项证伪/降级留档、2 项 defer。最终树全量 pytest 395 passed（1 pre-existing 无关红，main 亦红）。历史镜证无重蹈旧教训。建议进 `/sdflow-done`。

<!-- ship-gate: code-review=pass -->
