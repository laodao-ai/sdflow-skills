# spec-review-report — implement-workflow-optimization-2026-08-p1

- 评审日期：2026-08-10 · host=claude（强档主审 opus / 中档镜 sonnet / 接地镜 haiku）
- 盘面：单批 dispatch——广审双镜（strategy/plan-eng）+ devex 领域镜 + 对抗镜×3（隐藏假设/失败模式/乐观边界）+ 接地镜 + design-voice + hr-tg voice（codex/gpt-5.6-sol，跨模型）
- 修订已按裁决落盘四件套（标 `[spec-review-amendment]`），需拍板项见决策登记区

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="TG-09,TG-17" declared="TG-05,TG-09,TG-11,TG-14,TG-17,TG-18,TG-19,TG-20,TG-21,TG-22,TG-23,TG-28" evidence="reopen 新增 issue 生命周期唯一受控逆转换（TG-09）；token helper 读含完整对话的 transcript 并派生数据永久入库（TG-17）" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="5" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->

TG 命中（模型判定，交 `hr_tg_intersect.py` 机械交集）：TG-05/09/11/14/17/18/19/20/21/22/23/28；HR-TG ∩ = {TG-09, TG-17} ⇒ 单开 hr-tg 跨模型 voice。TG-01/02/03 不命中（纯 Python/Bash 工具栈）；TG-08 判不命中（transcript 为被动读本地文件、非服务依赖，漂移风险由假设 A-3 面覆盖）。

---

## 决策登记区

┌─────────────────────────────────────────────────────────────┐

### [自动决策]（高置信采纳，修订已落盘，设计门可覆盖）

- **D1 · M1 fix-status 判定文法欠定（致命）**：`已修[impl-review-fix]` 并非「唯一形态」（裸串 257 处/57 份 vs 精确 needle 83 处/15 份，实存空格/加粗/全角/`采纳`/段落台账变体），且原管道「其余含 finding 特征→未修」把 67% 变体方向性判「未修」、压低实修率恰好污染砍留判据。**修订**：三态判定——含处置信号但不命中精确 needle → 未知桶 MUST NOT 判未修；spec 补两条 Scenario + tasks 2.3 变体用例 + tasks 2.0 真语料试算前置。
- **D2 · M2 lens 归属子串匹配无词边界（致命）**：真实语料实证假阳性（文件名 `outside-voice-reuse-guard` 误判给 voice 镜、「历史注释」误判给历史镜），且恰落「可判定」桶、现有安全网全拦不住。**修订**：匹配面收窄为有界来源记号（「来源」列 / `〔〕`/`【】` 标签）；`域` 别名限记号内。
- **D3 · M5 token helper 接线插入点消歧（致命，strategy 镜独家）**：插在判空 gate 之前会让 helper 弄脏干净树、「无变更静默跳过」契约永久失效（`sdflow-done` verify 依赖该 no-op 语义）。**修订**：design/spec/tasks 钉死「gate 之后、`git add -A` 之前」+ 干净树 no-op Scenario + 沙盒用例。
- **D4 · M6 token-log 坏行防护（致命）**：读侧无逐行防御则一行截断 JSON 拖垮整仓 retro 报告（`build_report` 主循环无 per-iteration try/except）；写侧无原子性契约是触发源。**修订**：spec 读侧「损坏行逐行跳过不中断整报」Scenario + 写侧「整行单次 O_APPEND 写」。
- **D5 · M3 计数失实**：design「83 处/63 份」实测为 83 处/**15 份** review-report（三镜独立复测一致；全仓宽口径 96/25）。已改，并连带修正「唯一形态」断言（见 D1）。
- **D6 · M11 `sdflow_issues_core` 引用失实（四路独立命中）**：该包已于 bad1f87 删除脱钩，`issues_v2.py` docstring 明言不 import；M-2 mechanics 全部内联。**修订**：proposal Impact / design 组件图 / tasks 1.1 三处改为「内联复用 `issues_v2.py` 自身 mechanics」。
- **D7 · M12 reopen 中断残留幂等恢复**：位置守卫不查 status ⇒ 中断重试会重复追加「原 closed_reason：null」误导历史行；`cmd_reindex` 照单渲染、「可被 reindex 检出」实际检不出。**修订**：守卫加中断残留分支（幂等续跑不重写历史行）+ reindex 对 closed/ 非终态输出 WARNING + 中断重试 Scenario 与用例。
- **D8 · M13 reindex 失败自愈提示**：`git mv` 后 reindex 失败时非零退出 ≠ 未发生变更；错误信息明示「重开已生效，重跑 reindex 即自愈」。已落 spec。
- **D9 · M10a TG-17 泄漏防护（hr-tg voice 独家）**：输出面封闭 schema（MUST NOT 透传 transcript 内容）+ usage 非负整数校验 + session-id 文法校验后才拼路径 + canary transcript 测试。已落 spec/design/tasks。
- **D10 · M9 helper 挂起防护**：`|| true` 只防非零退出防不住 hang，checkpoint 被编排流程同步调用。**修订**：helper 内部自设执行超时。
- **D11 · M4a 验收措辞对齐粒度诚实边界**：实修率粒度为 (layer,lens)（历史信号只到 lens 级，五元组不可回算）；「大面积『参考』」为合法诚实产出。proposal Success Metrics 已改。
- **D12 · M15 SKILL.md 文档面**：`sdflow-issues`/`sdflow-retro` 两处 SKILL.md 未随交付更新则新能力对使用者不可见。tasks 新增 5.3。
- **D13 · 小项打包采纳**：M7b tokens 列累计口径脚注（低）；M14 closed_reason 空值历史行文案（低）；M16 reopen 拒绝路径错误文案原文落 design（低）；M17 缩写 `cw`→`cc` 对照钉死（低）；M18 BASE-25 组件清单表补齐（低）；M19 D2 信号源收窄补显式标注（低）；M20 BASE-18 fold 判定确认——三域合并系继承 roadmap 1.B 阶段分解决策、非本 change 独立判断，设计门确认即可不拆分（低）；M21 「单人串行为主」论证措辞修正（低）。

### [需拍板]（设计门勾选，默认推荐已给）

- **Q1 · token 跨 change 双计数修法（M7，对抗镜C）**——「首行全额 + attribute-to-next」在 session 横跨两 change 时前段用量真实双计数；「与 stage_walltimes 同构」类比被读码证伪（walltime 是 delta-only、首提交贡献 0）。
  - 选项 A（**推荐**）：读侧全局按 session 跨 change 分组——retro 先扫全部 token-log，同 session 出现在多个 change 文件时，后一文件首行对前一文件末行差分，落行所在 change。依据：数据已在盘、纯读侧、彻底消双计数。代价：retro join 多一层全局分组。备选 B：首行归 0（与 walltime 严格同构，但单 session 单 change 的常见场景会整段漏计首段用量）。备选 C：维持现状 + 双计数 flag（数值仍失真）。
  - 三面后果：系统镜——A 零写侧改动、可回滚；用户镜——A 报告数值最真；开发循环镜——A 实现成本略高于 B/C 但一次做对。**主次判定：系统镜为主**（写侧契约不动，读侧口径可迭代）。
- **Q2 · change 收尾 token 不入账（M8，design-voice）**——最后一次 checkpoint 之后的 verify/archive/merge 用量对**每个** change 系统性缺失（sdflow-done 不走 checkpoint），非低概率边角。
  - 选项 A（**推荐**）：本 change 接受 + design 边角显式收录 + 记 roadmap todo（阶段 2 评估在 sdflow-done 加终态快照）。依据：不加宽本 change scope（proposal Impact 未含 sdflow-done）；尾段缺失是稳定同向偏差，趋势参考仍可用。备选 B：本 change 扩 scope 给 sdflow-done 加 done-archive 快照（交付更完整，但动第四个 skill、审面扩大）。
  - 三面后果：系统镜——A 零额外耦合；用户镜——token 列系统性偏低（可脚注）；开发循环镜——B 多一轮联动测试。**主次判定：系统镜为主**（scope 纪律优先，缺口显式记账）。
- **Q3 · 实修率判据密度大概率不足（M4b，design-voice + 对抗镜C 试算）**——57% 精确 needle 样本无 lens 记号、broad/grounding 单镜命中为 0，13 面镜大概率大面积落「参考」，阶段 2 可能仍拍不了板。
  - 选项 A（**推荐**）：接受本 change 交付 (layer,lens) 粒度 + 诚实三数呈现（tasks 2.0 试算先行确认密度；「判据密度不足」本身即有效决策输入，阶段 2 以独立率+人工复核为主）。备选 B：扩 scope 让未来报告 emitter 写结构化 per-finding resolution 锚（前向改善密度，属阶段 2+ 范围，本 change 不做、记 todo）。
  - 三面后果：系统镜——A 零新契约；用户镜——报告可能多数行标「参考」；开发循环镜——B 才能根治但跨 change。**主次判定：开发循环镜为主**（判据建设是本 change 目的，但历史密度是既成事实，前向改善另行立项）。
- **Q4 · session_id 明文入库 vs 哈希（M10c，hr-tg voice）**——原始 UUID 随仓库永久公开。
  - 推荐：**保留明文**。依据：session_id 是本机 transcript 文件名，知晓不构成访问能力、敏感度低；明文保留「错选 transcript 可事后甄别」的调试价值（纪要边角依赖）。备选：写哈希（丧失甄别能力，收益仅防跨记录关联——威胁模型弱）。

### [已裁掉]（反静默压制，原始发现 + 裁掉理由，供门上复核）

- **X1 · strategy F4：design.md `$CLAUDE_CODE_SESSION_ID` 括注违反 DOC-1**——裁掉理由：该括注正是本仓「偏离纪要必须显式标注」惯例的执行（strategy 自己的 F3 引同一括注为正例），删除反而断偏离追溯链；DOC-1 判据「只对读过上一版的人有意义」不成立——memo 与 design 是并存文档、非版本演进关系。
- **X2 · hr-tg voice 第 3 条的完美防御部分（realpath containment / O_NOFOLLOW / 全组件 symlink 拒绝）**——部分采纳（session-id 文法校验 + 输出封闭 schema 已入 D9），裁掉全套容器级防御：威胁模型是本机用户读自己的文件，攻击者=自己；五问——概率极低 / 影响中 / 完美成本高 / 简化方案（文法校验）已覆盖主要逃逸面。不因裁掉降低 canary 测试等级。

└─────────────────────────────────────────────────────────────┘

---

## 合并 findings 与裁决（26 条 canonical，多镜命中已去重）

| ID | 问题（一句） | 命中镜 | 裁决 | 严重度 |
|----|----|----|----|----|
| M1 | fix-status 文法欠定：needle 非唯一 + 默认判未修方向性偏差 | 对抗C · design-voice | 采纳→已修订 | 致命 |
| M2 | lens 关键词无边界子串匹配产假阳性入可判定桶 | 对抗A · 对抗C | 采纳→已修订 | 致命 |
| M3 | 「83 处/63 份」计数失实（实测 15 份 review-report） | plan-eng · 对抗C · 接地镜 | 采纳→已修订 | 高 |
| M4a | 「13 面镜可读」验收措辞越过 (layer,lens) 粒度诚实边界 | design-voice · 对抗C | 采纳→已修订 | 高 |
| M4b | 前向结构化 resolution 锚（改善未来密度） | design-voice | **defer→Q3** | — |
| M5 | helper 接线插入点未消歧，威胁干净树 no-op 契约 | strategy | 采纳→已修订 | 致命 |
| M6 | token-log 坏行可拖垮整仓报告 + 写侧无原子性 | 对抗B · plan-eng | 采纳→已修订 | 致命 |
| M7 | 跨 change session 首行全额 = 真实双计数 | 对抗C | **defer→Q1** | — |
| M7b | tickets 管线下差分少触发，需累计口径脚注 | 对抗B | 采纳→已修订 | 低 |
| M8 | change 收尾（verify/archive）token 系统性不入账 | design-voice | **defer→Q2** | — |
| M9 | helper 挂起无防护（`\|\| true` 不覆盖 hang） | 对抗B | 采纳→已修订 | 中 |
| M10a | TG-17 输出面无封闭 schema/canary 契约 | hr-tg voice | 采纳→已修订 | 高 |
| M10b | 容器级路径防御全套 | hr-tg voice | **裁掉→X2** | — |
| M10c | session_id 明文 vs 哈希 | hr-tg voice | **defer→Q4** | — |
| M11 | `sdflow_issues_core` 已删除，三份产物引用失实 | design-voice · plan-eng · devex · 对抗B | 采纳→已修订 | 高 |
| M12 | reopen 中断残留不可幂等恢复 + reindex 检出为虚 | hr-tg voice · 对抗B | 采纳→已修订 | 高 |
| M13 | reindex 失败窗口退出码语义误导 | design-voice · 对抗B | 采纳→已修订 | 中 |
| M14 | closed_reason 空值历史行呈现 | 对抗A | 采纳→已修订 | 低 |
| M15 | SKILL.md 文档面缺任务，交付面不可发现 | devex | 采纳→已修订 | 中 |
| M16 | reopen 拒绝路径错误文案无原文 | devex | 采纳→已修订 | 低 |
| M17 | `cw` 缩写与 `cache_creation` 字段名不对应 | devex | 采纳→已修订 | 低 |
| M18 | BASE-25 组件清单表缺失 | plan-eng | 采纳→已修订 | 低 |
| M19 | D2 信号源三类→一类收窄未显式标注 | strategy | 采纳→已修订 | 低 |
| M20 | BASE-18：三域合并 vs fold 判据（继承 roadmap 分解） | strategy | 采纳→门上确认 | 低 |
| M21 | 「单人串行为主」论证前提与并行子代理常态矛盾 | 对抗A | 采纳→已修订 | 低 |
| X1 | design 括注违反 DOC-1 | strategy | **裁掉→X1** | — |

**对抗裁决说明**：对抗镜 A/C 的两条致命项（M1/M2）均以真实语料实测复现（非推演），直接采信；对抗镜 B 对「git mv 脏写」「set -e 与 `|| true` 交互」「活跃 transcript 撕裂读」三方向的证伪结论采信为攻不破，未产生 finding。接地镜 11 条断言 10 条一致，唯一不符项（计数）并入 M3。低置信项无静默滤除：本轮各镜置信最低为「中」，全部入池裁决。

**各镜原始报告要点**（fresh 子代理返回，已按上表折叠）：strategy 4 条（M5/M20/M19/X1）；plan-eng 4 条（M3/M11/M18/M6-读侧）；devex 4 条（M16/M17/M15/M11-措辞）；对抗A 3 条（M2/M21/M14）+3 方向攻不破；对抗B 8 条（M6/M11/M12/M13/M9/M7b + 2 并入）+3 方向证伪；对抗C 6 条（M1/M3/M4a/M7/M2-别名/M1-规格根因）；接地镜 10✅/1❌；design-voice 5 条（M4a/M1-侧写/M8/M13/M11）；hr-tg voice 4 条（M12/M10a/M10b/M10c）。

---

## 图与既有一致性

- TG-14 组件图：存在，`sdflow_issues_core` 节点失实已修正 + 补 BASE-25 组件清单表。
- TG-11 数据流图：存在，随 fix-status 三态修订仍正确（未知桶分支语义已在 design 决策文字更新，图中「其余含 finding 特征→未修」一行以 D1 修订文字为准）。
- TG-09 状态机图：存在且与代码状态枚举一致（接地镜断言 11 核验）；reopen 幂等恢复分支为文字契约，不重画图。
- TG-18 测试覆盖图：存在，新增用例（no-op/canary/中断重试/坏行）已并入对应行落点，无新增测试落点目录。

## 收敛口

**建议进入设计 HARD-GATE**：4 条致命项与全部高危项均已修订落盘，剩余 Q1–Q4 为口径/取舍类拍板（均附推荐），无未修订的结构性缺陷。人工过本报告：勾 Q1–Q4 → 批准后按拍板回写协议落 `ship-gate.design_approved` frontmatter（若勾选结果引发四件套二次修订，先单独 checkpoint 再回写锚——ADR-7(b)）。

## lens-metric 度量锚（Step3 裁决草稿值，拍板回写时最终化〔SR-M〕）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="13" 采纳="12" 裁掉="0" defer="1" 独立="5" sev="致3/高4/中2/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="8" 采纳="7" 裁掉="1" defer="0" 独立="4" sev="致2/高2/中0/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="3" sev="致0/高1/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="6" 采纳="4" 裁掉="0" defer="2" 独立="0" sev="致1/高2/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="4" 采纳="2" 裁掉="1" defer="1" 独立="1" sev="致0/高2/中0/低0" -->

> 保留残余信任边界声明：分类正确性（finding 归哪个 lens）、roster 完备性、findings JSON 誊写准确仍是主 session 信任边界；emitter 只保证给定输入的确定性归约。`findings=N` 与合并池实收数的数值一致性同为主 session 信任边界、非机械可验。

