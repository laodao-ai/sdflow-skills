# fix-workflow-bundle-staleness · Spec Review Report

- **change**: `openspec/changes/fix-workflow-bundle-staleness/`（`skip_specs: true`，四件套 = proposal / design / tasks + decision-memo）
- **日期**: 2026-08-13 · **host**: claude · **档位**: strong=opus / mid=sonnet / light=haiku · **effort**: high/medium/low
- **roster**: 广审双镜（strategy/plan-eng，fresh 子代理）+ devex 领域镜（TG-28）+ 对抗镜 ×2（隐藏假设 / 失败模式）+ 接地镜 ×1 + design-voice（codex `gpt-5.6-sol`，async·harness，`reason_code="ok"`，6 findings，OV_TRUNCATED=false）
- **TG 判定**: 命中 TG-22（Non-Goals 携假设）/ TG-25（契约文档套件，design 已含 scope-check 表）/ TG-28（devex：config.template context 默认内容 + bundle 交付面成员变更）；HR-TG ∩ = ∅（纯文档变更，无运行期爆炸面）
- **机械引用核**: 13 条入核——12 `pass` + 1 `uncheckable`（M1d 证据包，未经机械核直进裁决）+ 0 `fail`

---

## 拍板三问（人在设计 HARD-GATE 逐项勾选认/不认）

- **Q-scope 范围划界认不认？**
  自答：锚 proposal「Non-Goals」四条（不重构目录 / 不改 workflow.md 与机读块 / 不逐处改写 Methodology / 不触发消费仓 update）——评审后仍成立，但采纳项 A1-A6 把「同族面治」的枚举面扩到了 index-section :10-:19 全行、quality-layering:38、docs/sdflow-fable5:160、README:28（第 8 处 /review），均在「bundle 失鲜清零」原目标内，未加宽目标本身。 [ ] 认 [ ] 不认
- **Q-deps 依赖/顺序认不认？**
  自答：锚 tasks.md 四组线性任务（1 修正 → 2 收史 → 3 处置 → 4 收尾门），组间无并行依赖；唯一顺序敏感点 = 4.2 `init.py update` 必须在 index-section 修正**之后**跑（否则把失鲜行重新灌回 INDEX.md，plan-eng F1 已实证 INDEX.md:15 现有同款陈旧行）。 [ ] 认 [ ] 不认
- **Q-risk 风险赌注与对策认不认？**
  自答：锚 `sdflow:hr-tg` 判定 `hit="none"`（declared=TG-22,TG-25,TG-28，无高风险触发）+ design「Risks」5 条——对抗镜实证机械门覆盖面成立（无隐藏措辞测试锚、canonical 软链指向运行 checkout 无即时暴露窗口）；原 Q1/Q2 两个拍板项经二次调研升格为 spec 锚定失鲜修正（A11/A12），无剩余拍板项。 [ ] 认 [ ] 不认

<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->

## 决策登记区

### [自动决策]（高置信 → 默认采纳，四件套已按此修订，标 `[spec-review-amendment]`；可覆盖）

- **A1 · index-section.md 真实失鲜面与行号锚全面修正**〔M1a/M1b/M1c，高危，strategy+plan-eng+对抗镜2+voice 四路独立命中〕
  真实失鲜在 **:10**（`生成(ff+grill)`、`subagent-dev→sdflow-code-review→sdflow-done`、`去 /clear`）、**:12**（`opsx:ff` 起手 blurb，应随 D5 同步）、**:11/:18/:19**（TG-01~28 / BASE-01~30 / CR-01~09 号段）；memo D6/D9 与 tasks 3.4 引用的 `:13,15,16` 与真实文件错位（:15=spec-review 行、:16=model-tiers 行，主审 `cat -n` 亲验）。其中 :10 的「去 /clear」是被 `workflow.md:134` 明文否决的过度泛化——属**第三处正面矛盾**，且已传播进本仓 `openspec/INDEX.md:15`（与 :43 现行口径同文件自相矛盾）。tasks 3.4 已改为按内容定位 + 全行清单。
- **A2 · quality-layering.md:38 `CR-01~09` 去上界**〔M1d 之 bundle 内部分，中危〕——D6 策略一致性：bundle 内号段全集面治，不留半治。
- **A3 · docs/sdflow-fable5/02-module-reference.md:160 `TG-01~26`**〔M2，中危，对抗镜1 独家〕——第三个漂移值（24/26/28 三版并存），事实性错误，一行修正并入同族面治。
- **A4 · `/review` 全集 = 8 处，非 7 处**〔M7，中危，接地镜独家〕——`code-checklists/README.md:28` 漏网（主审 grep 亲验 :3,13,28,53,68 共 5 处 + 其余 3 处）；tasks 1.5 已扩。对抗镜1 复扫声称 7 处全集成立，被证伪（见 X2）。
- **A5 · PRD_vs_Spec.md 深层失鲜**〔M5，中危，voice 独家〕——:33/37/68/70/79/97/113 以现行语气写 plan-ceo-review/autoplan/brainstorming 链路，只换 4 处 opsx:ff 会留半新半旧。处置 = D8 同款**顶部历史举例标注**（不逐处改写，通则④）；tasks 3.3 已并入。
- **A6 · Token_Saving_Strategies.md 移动时加历史横幅**〔M6，中危，voice 独家〕——:3 起通篇 superpowers 时代口径，裸移到 `docs/` 会以普通文档误导读者；git mv 时顶部加「个人历史笔记（superpowers 时代），不代表现行工作流」横幅；tasks 3.2 已并入。
- **A7 · memo C3 证据锚失实（勘误记录，memo 不回改）**〔M8，低，strategy 独家〕——「CLAUDE.md『历史参考（已退役）』段」不存在（grep 零命中）；writing-plans 退役的真实锚 = `openspec/changes/archive/2026-08-12-remove-superpowers-pipeline/`。memo 保持历史拍板记录原样，实现者以本条为准。
- **A8 · generation-process §二标题行同步**〔M9，低，strategy 独家〕——:21「## 二、③ = 三种对话相位 + 四个 skill」若不随正文改为两工具表会自相矛盾；tasks 2.1 已显式包含。
- **A9 · tasks 2.1「四短语」勘误**〔M10，低，对抗镜1 独家〕——`test_canonical_entry_sync.py` 实为**三对 presence 断言（六子串）**（「推荐流水线」+「唯一入口」、「模型 SHALL 在以下情形自动 invoke」+「/sdflow-spec」、「模型 MUST NOT 自主判断」+「该开 change 了」）；自检一律以 `pytest hack/tests/test_canonical_entry_sync.py` 为准，不靠记忆 grep。
- **A10 · bundle 外 `CR-01~09` 残留（SKILL.md ×4 / docs/workflow-skills ×2）不 fold，记 todo**〔M1d 之 bundle 外部分〕——当前值准确（CR 实到 09 未漂）、位于 skill 源与人读文档（非 bundle 分发面），fold 会加宽改动面；漂移仅在 CR 扩号时发生。三镜：系统镜 fold 增 blast-radius / 用户镜零现时影响 / 开发循环镜 todo 成本≈0——开发循环镜主导 ⇒ defer 记 **T282**。
- **A11 · generation-process §四流水线图补阶段二**〔M3，中危，voice 独家；原 Q1 升格〕——二次调研发现权威锚：`openspec/specs/spec-workflow/spec.md:1604` 的唯一线性路径字符串**本身含** `→ /clear → sdflow-spec-review`，而现图 `/sdflow-spec → HARD-GATE 批准`（:53-61）缺该环节 ⇒ 属 **bundle↔spec 分叉修正**（本 change 目标内失鲜），非 D4 拍板范围扩张。可行性亲验：`test_canonical_entry_sync.py` docstring 明文「不锚跨行 ASCII 图」，presence 六子串全在标题/散文行。修法：只插一行 `↓ /clear → /sdflow-spec-review（阶段二设计审）`，不重排其他行。人确认继续（2026-08-13 10:40）。
- **A12 · 自动触发规则 ② 删「判断」二字回归 spec 措辞**〔M4，中危，voice 独家；原 Q2/TENSION 升格〕——二次调研推翻双方原框架：② 是 simplify-workflow（2026-08-05 归档）拍板的**现行设计**（spec:1608 + :1617 专属 Scenario「用户直接描述需求 → 直接 invoke」），voice 的「自相矛盾」判定不成立；真问题是 bundle :72 比 spec 权威措辞（「② 用户描述需求且需要开 change 时」）**多「判断」二字**——正是这两个字制造「模型可自主判断」误读。修法 = bundle 回归 spec 措辞（删两字），纯 bundle↔spec 分叉修正，不撞 Non-Goals「不改规则语义」（语义权威在 spec）。主审原推荐（改写为「此即人的示意信号」）经复查**撤回**——会加深分叉，此推荐当时未亲验（教训已记 T283）。voice 的「删除②/加 absence 断言」不采（推翻现行设计 + 加宽）。人确认继续（2026-08-13 10:40）。

### [需拍板]（人工设计门勾选）

（无——原 Q1/Q2 经二次调研（用户 2026-08-13 10:22 触发）发现 spec 权威锚后升格为 A11/A12 失鲜修正，人已确认方向（10:40）；设计门只需过拍板三问与本报告整体。）

### [已裁掉]（反静默压制，原始发现 + 裁掉理由，供门上复核）

- **X1 · 接地镜断言「index-section.md:13/15/16 已包含需改内容（行号对得上）」**——裁掉理由：与主审 `cat -n` 亲验直接矛盾（:15 = spec-review 行、:16 = model-tiers 行，不含 ff+grill/subagent-dev/TG 号段）；三面镜（strategy/对抗镜2/voice）+ 主审共四路证据一致指向行号错位。接地镜该项核验结论错误。
- **X2 · 对抗镜1 断言「C4 的 `/review` 7 处全集经复扫成立」**——裁掉理由：主审 grep 亲验 `code-checklists/README.md` 实有 5 处（:3,13,**28**,53,68），第 8 处 :28 真实存在（接地镜正确）。
- **X3 · 对抗镜2 F2「ff-generation-constraints 标题改写无测试锚（低危记录项）」**——裁掉理由：该镜自证「未爆、无需改动」，无行动项，仅存档。

### 低置信一行带过（不静默滤除）

- strategy 镜注记：memo「三镜代价」自称无 TG-23 命中，但 D5/D6/D7/D8 均列了「砍掉的候选」——技术上触发「≥2 合理方案」文本；鉴于均为低风险纯文本选择且已附一行理由，判可接受从简（置信低，不构成 finding）。

---

## 各镜 findings 概览

| 镜 | 回传 | 采纳 | 裁掉 | defer | 要点 |
|---|---|---|---|---|---|
| strategy（broad） | 5 | 5 | 0 | 0 | SR-1/2/3 → A1/A2 族；SR-4 → A7；SR-5 → A8 |
| plan-eng（broad） | 1 | 1 | 0 | 0 | F1 → A1（独立命中 INDEX.md:15 已传播 + update 回灌路径） |
| devex 领域镜 | 0 | — | — | — | DX-01~05 全 N/A（含 DX-04 复核：Token_Saving 移出不属交付面变更——`index-section.md:20` 明示 reference/ 为「可删不影响执行」） |
| 对抗镜1（隐藏假设） | 1+7 未破 | 1(A3)+1(A9) | 1(X2) | 0 | 未破清单：行号漂移 / §三零外部引用（C5 成立）/ gen_workflow_guide 消费面（C6 成立）/ canonical 软链指向运行 checkout（无暴露窗口） |
| 对抗镜2（失败模式） | 2+4 未破 | 1(A1 加强：「去 /clear」第三矛盾) | 1(X3) | 0 | 未破清单：git mv 连锁（C7 成立）/ 全仓测试无隐藏措辞锚 / init.py update 副作用面 |
| 接地镜 | 2 不符 + 全量核验 | 1(A4) | 1(X1) | 0 | 其余全部 file:line 引用核验一致（含 test_canonical_entry_sync 断言、gen_workflow_guide 消费面、A1~A4/A5 未占用、39 md 计数） |
| design-voice（codex） | 6 | 6(A1c/A2 部分、A5、A6、A11、A12) | 0 | 0 | 独家贡献 A5/A6/A11/A12——6/6 全采纳（A11/A12 经二次调研以 spec 锚修正定性后升格），零裁掉 |

**镜间冲突裁决记录**：接地镜 vs 主审（X1，行号）、对抗镜1 vs 接地镜（X2，/review 计数）——两处均以主审亲跑命令的输出为准。

## 图验证（design-diagrams：只验存在/正确/未过时）

- design「改动面与门禁关系图」：在场，与 Migration Plan / 门禁清单一致（plan-eng 镜核验）✅。
- design「Scope-Check 表」（TG-25 → BASE-29）：在场且**全套枚举**；本轮 findings 恰证明其价值——漏的不是文件行（index-section 已标 ✓）而是行内枚举精度，已由 A1 修正。✅（修正后）

## 诚实边界声明

- 能力探针：host=claude 免探，`subagents="available"` 为机制事实；`mirrors=` 由本 skill 直写，无机械 spawn 证明。
- `findings=N` 与合并池实收数的数值一致性、lens-metric 分类/roster 完备性/誊写准确性 = 主 session 信任边界，emitter 只保证给定输入的确定性归约。
- lens-metric 锚已随 A11/A12 升格重算（emitter 重跑，非手拼）；门上若再翻改去向，SHOULD 随拍板回写同步重算（SR-M，best-effort 无机械兜底）。
- 「改动前全仓 2649 passed」未复跑核验（只读评审不跑全仓 pytest，收尾门 4.3 兜底）。

## 锚行区

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-22,TG-25,TG-28" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="6" truncated="false" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="7" 采纳="5" 裁掉="2" defer="0" 独立="2" sev="致0/高2/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="2" sev="致0/高2/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="8" 采纳="8" 裁掉="0" defer="0" 独立="4" sev="致0/高2/中6/低0" -->

## 收敛口

四件套已按 A1-A12 修订（标 `[spec-review-amendment]`；A10 记 T282，裁决纪律教训记 T283）。二次修订已按「拍板前二次修订」协议单独 checkpoint（见 git log `spec-review-amendment`）。**建议进设计 HARD-GATE**：人过本报告拍板三问即可（无剩余待拍板项）；批准后主审把 `design_approved: true` + 该 checkpoint 的 40 位 `reviewed_sha` 同次写入本文件头部 frontmatter，随后 `/clear` → `/sdflow-ship`。
