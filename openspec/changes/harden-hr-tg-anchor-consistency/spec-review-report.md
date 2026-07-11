## spec-review 报告 — harden-hr-tg-anchor-consistency

### 命中范围
栈：纯 Python stdlib 工具（无 python 领域清单 → 领域镜退 base，F13 诚实降级）。命中 TG：TG-18/19/22/23（∩ HR-TG = ∅）。
镜：广审（Step1，simulated）+ 对抗×2 + 接地×1 + codex outside-voice(design-voice)。**并发说明**〔T20〕：广审与多镜并发派发（本 change 无 autoplan 预写 amendment，广审只产 findings 不预改 spec，Step3 统一合并，无 diff 增量遗漏）。

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-18,TG-19,TG-22,TG-23" evidence="命中 TG-18(测试)/19(多需求)/22(假设)/23(≥2方案ADR)，∩HR-TG{04,06,07,08,09,16,17,26}=∅；纯 stdlib 校验器加固无运行期爆炸/数据损坏/安全泄漏面" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="none" findings="4" truncated="false" -->

### 决策登记区

**[自动决策] 全部 fold 进本 change（decomposition standard：相关即立即做，非 defer）**——冷层 5 源共识：完整性/scope/回灌口径**站得住**，但揪出 15 条"机械化还没做完整"，全为同片 hr-tg 一致性的更多确定性维度/回归，已落 [spec-review-amendment]（design 头部收敛块 + 两 delta spec + tasks §3）：

| ID | 发现 | 报告镜 | sev | 处置 |
|---|---|---|---|---|
| F1 | `declared="none"` 应为 `""`（我引入的 spec bug） | codex(独立) | 高 | 采纳·改 scenario + 测 |
| F2 | 跨消费者重复键分歧（lint 末值胜 vs retro 取首） | codex+对抗 | 高 | 采纳·整行严格解析拒重复键 |
| F3 | M2/M-new「非 import」双份重实现无跨文件一致性兜底 | 对抗A(独立) | 高 | 采纳·加 cross-tool golden 测试 |
| F4 | `_catalog()` fixture 缺 A–G 表→打崩 10+ 现有正例 | 对抗B(独立) | 高 | 采纳·retrofit fixture |
| F5 | `test_single_source_mutability` 的 TG-99 与 M-new 反例语义直撞 | 对抗B(独立) | 高 | 采纳·重设计该测试 |
| F6 | check_hr_tg 签名变+`_run()` 缺 catalog→argparse exit2 撞码假绿 | 对抗A+B | 高 | 采纳·补参+断言 stderr 原因 |
| F7 | catalog 内部一致（HR-TG⊆全集）未校验 | codex(独立) | 中 | 采纳·加载断言子集 |
| F8 | 全集解析边界未钉死（正文游离 TG 会被 blind-regex 纳入） | codex+对抗A | 中 | 采纳·钉死表行边界+fullmatch |
| F9 | 就地转 violation 不 raise（护 human+JSON 双输出） | 对抗A(独立) | 中 | 采纳·钉错误处理契约 |
| F10 | M4 `evidence="   "` 纯空白须 strip 判空 | 对抗B(独立) | 低 | 采纳·strip 后判空 |
| F11 | 部署 skew 描述过窄（下游消费仓双速率） | 广审(独立) | 中 | 采纳·design Risks 澄清 |
| F12 | docs/workflow-map + workflow-skills 调用串失真 | 广审(独立) | 低 | 采纳·tasks 补 docs 同步 |
| F14 | 新增-TG 类 change 自指评审顺序 | 广审(独立) | 低 | 采纳·design 注（fail-safe 可接受） |
| F15 | scoped-test-per-task 活跃旧格式报告中间态 | 对抗B(独立) | 中 | 采纳·design 注（全量重跑重 emit）+ship 前实测 |
| F16 | D2 诚实边界写成"绕过指南" | 对抗B(独立) | 低 | 采纳·补"S1 非可放松"声明 |

### 已裁掉 / 验证无问题（反静默压制，可审计）
- **无裁掉项**——所有 reviewer findings 均成立、已采纳。
- 冷层**验证无问题**（负向核验，非 finding）：① spec:550 回灌与 hr-tg-intersection-check 现存 Requirements 无重复/矛盾（对抗B，关注点分离）；② check_existence 家族存在性 vs hr-tg 字段级无结构冲突；③ `--trigger-catalog` 调用点仅 2 处、路径一致（对抗A+接地）；④ M1 硬必填不误伤别族锚（anchor_prefix 精确路由）；⑤ B3「无流程重 lint 归档报告」核验为真（ship_gate/outside_voice_guard/lens_metric_emit/sdflow-maintain 均不反调 anchor_lint；sdflow-retro 独立 `_HRTG_RE` 只抓 hit=、不受 declared= 影响）。

### 度量锚（lens-metric，config metrics.enabled=true）
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="10" 采纳="10" 裁掉="0" defer="0" 独立="8" sev="致0/高5/中3/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="3" sev="致0/高0/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="2" sev="致0/高2/中2/低0" -->

> 冷层承重实证：F1（热层引入的 spec bug）、F2/F3（热层漏的跨消费者/跨文件一致性）由冷层独家/交叉抓出——grill（热）+ 广审均漏，对抗+codex 补上。

### 结论
- 设计**方向站得住**（M1–M4+M-new 面治闭环、T137/T139 剥离有据、零妥协有 B3 支撑），15 条冷层发现**全为完整性/回归修复、非推翻决策**，已 fold 落 amendment。
- □ 建议进设计 HARD-GATE（人工过本报告拍板 → 过门后 /sdflow-ship）
- 拍板后主 session 写 `ship-gate.design_approved: true` 进本报告头部 frontmatter。
