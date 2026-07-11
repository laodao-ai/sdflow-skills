---
ship-gate:
  code_review: pass
---

## code-review 报告 — mlh-p4-reason-code-validators

> 阶段三独立冷层强制主审。每票循环内双轴审已全绿，本层承重墙职责 = 抓循环内被 controller 说服放过的真问题——**兑现价值**：抓出 2 条中危假绿（循环内每票单审只验了主解析路径，漏了次要路径）+ 5 条 hardening + codex 跨模型独家 1 项。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" declared="" evidence="纯 stdlib 校验器无 DB/API/并发/安全/外部依赖/多状态生命周期面，逐一比对 8 个 HR-TG 成员均不命中" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->

### 命中范围
- **栈**：Python stdlib CLI 工具（3 校验器 + anchor_lint + 3 处 SKILL.md 接线 + config 翻键）。无 DB/HTTP/嵌入式领域面。
- **清单**：通用 base CR-01~09。**F13 诚实降级**——`code-checklists/domains/` 下仅 backend(DB/HTTP)/embedded 系清单，均不适用（本变更无对应领域面），无领域 delta 可叠加，退 base；非漏审，属已知覆盖边界。
- **gstack/review Step1（native）**：scope-drift 无顺手多改（config 翻键 / CLAUDE·AGENTS 各 1 空行 / T135 均 in-scope）；完成度 5/5 票全建 + 每票双轴审通过，build=planned。
- **HR-TG**：命中集空（none），dogfood 自身 T81 校验器验证；不额外开领域 cross-model。
- **outside-voice code-voice（codex 跨模型）**：首跳 exec exit 1（context 非 UTF-8，reason_code=exec-error）→ 修净 context 重试 exit 0，产 4 findings、未截断。

### Findings（置信 ≥80）
| 严重度 | CR/类别 | 位置 | 问题 | 置信 | 处置 |
|---|---|---|---|---|---|
| 中 | CR-01 / adr0018 | outside_voice_guard.py parse_codex_findings/parse_mode | fence 内文档示例锚被全篇 finditer/search 灌数 → 真实 codex findings=0 却判 `none`(可复用) = outside-voice 层静默跳过（假绿）；与另两校验器 fence-aware 口径漂移 | 95 | ✅ 已修 [impl-review-fix] 6ef7d45 |
| 中 | adr0018 | review_disposition_check.py _has_entity_content | 空 code fence / 未闭合注释 → 误判 `section-ok`(假绿)；空判用 naive DOTALL 与 find_section_body 的 _annotate_lines 是两套注释模型 | 90 | ✅ 已修 [impl-review-fix] 8f455c8（弃贪婪初版→逐行 live/in_fence 正解） |
| 高 | codex-F2 | anchor_lint.py check_hr_tg | 只验 hit/declared 字段在场、不重算交集 → 手改报告写 `hit=none declared=TG-04` 可通过 lint、静默跳过必开的领域 cross-model | 85 | defer → T136 |
| 中 | 对抗B | config.yaml impl-pipeline | 翻键注释"首个试点(mlh-p4)"误导——mlh-p4 已由 plan marker 自锁，翻键实际卷入 scoped-test-per-task 及所有未来 change | 90 | defer → T137（⚠ 需人裁意图） |
| 中 | codex-F3 | hr_tg_intersect.py | 坏输入静默正规化：`TG-04,,TG-16`/单 `,` 过、catalog 成员宽松 `TG-\d+`(`TG-04x`→TG-04) | 80 | defer → T138 |
| 低 | codex-F1/对抗A | outside_voice_guard.py parse_mode | 双 step1 锚(native+simulated)静默取首、不校验数量/一致性 | 80 | defer → T139 |
| 低 | 对抗B | anchor_lint.py check_hr_tg | declared= 列为 hr-tg 锚必填，破坏性收紧无向后兼容（旧格式锚重 lint 会 exit1） | 80 | defer → T140 |

### 已裁掉（反静默压制·可审计）
- **X1 · 对抗A F1（review_disposition_check 单行 `<!-- x --> y -->` 判 section-ok = 假绿）→ 裁掉**：经查 CommonMark 下首个 `-->` 闭合注释、尾随 ` y -->` 是**可见渲染文本**，判 ok 正确（非假绿；用户写了会渲染的畸形注释）。真假绿是空 fence / 未闭合注释——已由 codex-F4 采纳修复（上表第 2 行）。逐行 live/in_fence 正解如实保留该单行为 ok，同时修真假绿，且不误伤 sandwich（真内容夹两注释间→ok）。
- **X2 · 对抗A（OVG 等值 mtime 判 fresh，low）→ 未立项**：需产物与源文件 mtime 撞同一时刻（粗粒度 fs / touch 无亚秒），构造性极低；且方向本身偏保守 fail-safe。留此备考不记 todolist。
- **<80 置信滤除**：无——本轮冷层 findings 均有具体复现命令 / file:line 证据，置信均 ≥80，无 nitpick/CI 可抓项混入。

### 修复 / defer 台账
- **自动修 2 项 [impl-review-fix]**：
  - BUG1 outside_voice_guard fence-aware（6ef7d45）——parse_codex_findings/parse_mode 只匹配 fence 外锚（D5 重实现不 import）。
  - BUG2 review_disposition_check（6ef7d45 初版贪婪 → **8f455c8 正解**）——初版贪婪去注释经复现证明吃掉 sandwich 真内容（新假阴回归），改为基于 `_annotate_lines` 逐行 live/in_fence 判定：空 fence→empty、未闭合注释→empty、sandwich→ok、单行畸形尾随文本→ok（CommonMark）。190 passed -W error 0 warning，下游逐字回灌一致。
- **defer 5 项 → todolist**（hand-off 引用）：T136(anchor_lint 重算 hr-tg 交集,高) / T137(config blast radius,需人裁意图) / T138(hr_tg 严格 CSV) / T139(OVG 双 step1 锚) / T140(declared 向后兼容)。
- **裁掉 1 项**：X1（CommonMark 尾随文本，非假绿）。
- **无 T10 复核项**：2 项采纳均有客观判据（复现负例测试红→绿）；5 项 defer 均 genuinely 需设计/用户意图决策，非"有把握自动选"。

### 度量锚（lens-metric，config metrics.enabled=true）
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="4" 采纳="0" 裁掉="1" defer="3" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="5" 采纳="2" 裁掉="0" defer="3" 独立="1" sev="致0/高0/中2/低0" -->

> 读法：outside-voice(codex 跨模型) 本轮 5 findings / 2 采纳 / 1 独立——独家抓出 review_disposition_check 空 fence·未闭合注释假绿（domain/adversarial 未报），佐证冷跨模型层承重价值。历史镜/broad 零 finding（历史镜实证系统复用旧教训、无重蹈）。

### 结论
- ☑ **建议进 /sdflow-done**——2 项中危假绿冷层已修复并回归验证（190 passed -W error）；5 项 hardening defer 入 todolist（T136-T140），hand-off 引用异步再入口。
- ⚠ **提请人注意 T137**：`config.yaml` 翻 `impl-pipeline: tickets` 的 blast radius 与注释不符——mlh-p4 已自锁，翻键实际使 `scoped-test-per-task` 及所有未来 change 被卷入 tickets 管线。需确认是否符合意图（仅 pilot → 撤回翻键；仓级前向切换 → 改注释）。
