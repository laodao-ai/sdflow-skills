# spec-review 报告 — mlh-p2-anchor-lint

> 阶段二设计评审。Step1 broad（simulated）+ Step2 多镜（领域BASE/对抗A/对抗B/接地）+ outside-voice(codex design-voice)，主 session 强档对抗裁决。
> **并行说明（T20）**：broad 与多镜同批派出、审同一 committed 四件套（broad 不产 artifact amendment，故 mirrors 无遗漏增量）。

## 命中范围
- 栈：Python 工具脚本 + markdown（无 backend·go/embedded/frontend 领域命中）→ 领域镜跑 BASE（spec-quality-base）。
- **HR-TG 判定 = none**：TG-04/06/07/08/09/16/17/26 均不命中（锚自检门错判最坏=评审报告假过/假阻，非运行期爆炸/数据损坏/安全泄漏）。
- 清单：BASE-01~29 + 对抗三角度 + 接地代码事实核验。

<!-- sdflow:hr-tg v1 hit="none" evidence="锚自检门错判最坏为评审报告假过/假阻，非运行期爆炸/数据损坏/安全泄漏，不入 HR-TG 子集" -->
<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="ok" findings="4" truncated="false" -->

---

## Findings（对抗裁决后）

### 致命 / 高

**H1 [三镜收敛：broad+对抗A+对抗B｜置信高] metrics 门控把「config 存在但无 `metrics:` 块」误判 ERROR → 100% 消费仓每轮评审假阻塞**
- 证据：design.md 决策2 + spec Scenario 只分「文件缺失→false」vs「匹配不到 `metrics:`块下 enabled→ERROR」两支，把「config 存在但从未声明 `metrics:` 段」（消费仓常态）归进 ERROR 分支。`sdflow-init` update 从不为已存在 config 注入新顶层键（只并 context/rules）。**对抗B 实测**：本机 4 消费仓（05-sarvelo/01-laodao/10-michi/11-michi-kb-build）`grep "^metrics:"` 全零命中。本仓 dogfood 测不出（本仓 config 有 `metrics: enabled: true` 掩盖）。
- 裁决：**采纳**。真四态：①文件不存在→false；②文件存在但无顶层 `^metrics:` 行→视同未配置→false（放行，同缺省）；③有 `metrics:` 行但块内解不出合法 `enabled: true|false`→ERROR(2)。**精化 grill Q1**（保留「真坏→ERROR」精神，把「坏」收窄到「块在值非法」）。补一份无 metrics 段的真实 config fixture 测试。

**H2 [codex outside-voice｜置信高] `--layer` 不校验行内 `layer` == CLI `--layer`**
- 证据：design 只写字段 `layer ∈ {spec-review,code-review}`，未要求 fence 外 lens-metric 的 `layer` 等于 CLI `--layer`。`anchor_lint --layer code-review` 会放过 `layer="spec-review"` 的错层锚（错贴的度量锚漏网）。
- 裁决：**采纳**。加规则+测试：fence 外 lens-metric 的 `layer` MUST == CLI `--layer`，否则 VIOLATION。

**H3 [领域镜 BASE-08｜置信高] design 决策1/4 与父 roadmap 正面矛盾未调和**
- 证据：本 change design「脚本内重实现 fence 核、不 import」vs roadmap `design.md:56`/`roadmap.md:61`「复用 parse_anchor/_fence_aware_lines、不重实现」（且 task-log F1 冷审已采纳）。
- 裁决：**采纳（我方向正确但须显式调和）**。跨 skill import 在**消费仓 break**（anchor_lint 经 bundle tools/ 跑，sdflow-retro/scripts 不在消费仓）——对抗A/B 读码确认。roadmap F1 实质=「用变长 KV 前缀匹配、不用 _line_scoped_hits 定长原语」，本 change 遵其**实质**，仅把「import」澄清为「脚本内重实现同款逻辑」。**须**：design 显式声明覆盖 + 理由；同步改 roadmap `design.md:56`/`roadmap.md:61` + task-log 注记。

**H4 [领域镜 BASE-29/TG-25｜置信高] 契约文档套件 scope-check 表缺失**
- 证据：动了 lens-metric-contract.md（加机读块）+ 新增消费者 anchor_lint，但 design 无 TG-25 scope-check 表（workflow-metrics-loop 先例有）。BASE-29：未列入比未完成更危险。
- 裁决：**采纳**。design 补 scope-check 表：契约文件 / anchor_lint(新消费者) / lens_metric_aggregate(既有硬编码消费者+本 change 加一致性测试) / 两 SKILL / spec-workflow delta，各标 改/不改+为何。

### 中

**M1 [对抗A+对抗B+broad 收敛｜置信中] aggregator 一致性测试 + fence 核为双份独立实现 → 假绿风险**
- 证据：一致性测试「自带极简契约块解析、不跨 skill import anchor_lint」→ 守的是「测试自己的解析 == aggregator」而非「anchor_lint 运行时解析 == aggregator」；fence 核同理两份（R3 已承认）。两解析器边界处理分歧则假绿。
- 裁决：**采纳**。测试对同一真实契约 fixture **交叉断言**（两解析路径输出相等，非仅各自终集）；design R3/R4 补显式风险声明。

**M2 [对抗B｜置信中] SR-M 拍板回写在 anchor_lint 保护范围外（新缺口）**
- 证据：spec-review SKILL 的 SR-M 在设计门拍板时「原地更新」lens-metric 锚，发生在 Step3 anchor_lint 自检**之后**，自承「best-effort 无机械兜底」。design Risks 未提。
- 裁决：**采纳（仅记录，不本 change 修）**。design Risks 补记此已知缺口，避免误传「全流程锚格式已机械保证」。

**M3 [codex｜置信中] 计数字段不校验 int≥0**
- 证据：`findings/采纳/裁掉/defer/独立` 契约=int≥0，anchor_lint 只查字段存在+sev 格式，坏值（负/浮点/空/中文数字）漏进聚合。
- 裁决：**采纳**。anchor_lint 硬校验五计数字段为十进制非负整数，补失败样本。

### 低

**L1 [接地镜 F9｜置信高] 测试落点路径错**：design/tasks 写 `sdflow-retro/tests/`，实际现有测试在 `sdflow-retro/scripts/tests/test_lens_metric_aggregate.py`。→ **采纳**订正。
**L2 [对抗B｜置信中] `read_metrics_enabled` 块边界算法**：需先定位 `metrics:` 起点再限范围（防未来多段 config 误配对）。→ **采纳**补多段 config 测试。
**L3 [领域镜 BASE-07｜置信中] 决策1 重复论证块**（grill 编辑残留）→ **采纳**去重。
**L4 [领域镜 BASE-13/12｜置信低] Non-Goals 无可证伪断言 + 决策缺三镜框架**（镜自降置信，姊妹 change P1 亦无）→ **采纳（轻）**：决策1 补三镜一句 + Non-Goals 加可证伪判据。

---

## 已裁掉（反静默压制·可审计）

**X1 [接地镜 F10/F11/F12] 「anchor_lint.py/test 不存在、SKILL 未接、开发 0% → 不应过门」**
- 裁掉理由：接地镜**误判阶段**。这是设计门（阶段二），实现本就未开工——anchor_lint 在设计门通过后的 SDD 阶段才建。spec/design **未声称**脚本已存在（描述的是待建交付物）。「实现未开工」是阶段二的正常盘面，非缺陷。接地镜的代码事实核验价值在 F1-F9（已存在的复用源/先例/契约），F10-12 属越界。

**X2 [对抗B 低] site 豁免下游分类漂移**：非 outside-voice 锚误填 site 只多一分组行、不报错——契约 CF-补2 历史已拍板接受，仅记录不改。

---

## 决策登记区

```
┌────────────────────────────────────────────────────────────────────┐
│ [自动决策] 已采纳并将 [spec-review-amendment] 回写（gate 前）：       │
│   A1  metrics 真四态（H1）      A2  layer==--layer（H2）             │
│   A3  int≥0 校验（M3）          A4  roadmap 覆盖调和+同步（H3）       │
│   A5  scope-check 表（H4）      A6  一致性测试交叉断言（M1）          │
│   A7  测试路径订正 scripts/tests（L1）  A8  块边界多段测试（L2）      │
│   A9  决策1去重（L3）           A10 SR-M/Risks 记录（M2）+三镜/可证伪（L4）│
│                                                                      │
│ [需拍板] Q1  本地 pin 消费仓契约陈旧（对抗A H·边缘）——修法二选一      │
│ [需拍板] Q2  metrics 开时 per-lens 度量行完整性（codex F3 M）——三档   │
└────────────────────────────────────────────────────────────────────┘
```

### [需拍板] Q1：本地 pin 消费仓契约陈旧 → 永久 fail-closed（对抗A R-MRF-1）
- 盘面：本地 pin 消费仓（手动冻结全规则集：workflow.md+spec-checklists+code-checklists）RULES_ROOT 落本地 pin；`update` 刷 tools/anchor_lint.py（要机读块）但**不刷** sibling lens-metric-contract.md（pin 冻结）→ 块缺 → 每轮 ERROR(2)。**严重度=边缘**（对抗B 反证：pin 检测不认 tools-only，本机 4 消费仓全非 pin、常态走 canonical 全树无此问题；local-pin 可能零现存用户）。
- **三面后果**：系统镜——机读契约已成 tools/ 运行时依赖，理应同批刷新；用户镜——pin 用户（若有）静默假阻、报错不指真因；开发循环镜——(a) 改 copy_bundle 是 init.py 小改+测试。
- 选项：
  - **(a) copy_bundle 刷 tools/ 时一并刷 lens-metric-contract.md〔推荐·fold〕**：契约=机读依赖、与 tools 锁版本。小改 init.py+测试。轻微改变 pin 语义（契约随刷，但枚举极少变、且是机读必需）。
  - (b) 仅加 stale-shadow 告警：init.py 检测 pin + 契约无块 → 告警「须同步契约」。不根治，surface。
  - (c) 文档化已知限制 + defer：design 声明「local-pin 消费仓须手动同步契约」，本 change 不改 init.py。scope 最小。
- **主次判定**：推荐 (a)——正确性根治且成本小；若嫌扩 init.py scope 则 (c) 文档化 defer（边缘、零现用户，可后续补）。

### [需拍板] Q2：metrics 开时 per-lens 度量行完整性（codex F3）
- 盘面：SKILL 要求各参与镜（domain/adversarial/grounding/outside-voice/broad）各落一行 lens-metric；anchor_lint 现只查「≥1 条 lens-metric 存在+字段合法」，发现不了某镜漏落行。「本轮跑了哪些镜」是主 session 动态知识、报告本身机读不出。
- **三面后果**：系统镜——全 per-lens 完整性须报告显式声明参与镜清单才机验，增复杂度；用户镜——漏落行=度量召回缺口，但非门禁正确性；开发循环镜——min-required（broad+outside-voice 恒跑）是廉价钉法。
- 选项：
  - **(a) 钉最小必有行 broad+outside-voice〔推荐·部分〕**：metrics 开时这两行 MUST 存在（两者恒跑），其余动态 per-lens 完整性仍属主 session 信任边界。廉价、堵住最常见漏落。
  - (b) 报告显式声明参与镜清单 + anchor_lint 核对：全完整性机验，但要改报告格式+两 SKILL，复杂度高。
  - (c) 全 defer：per-lens 完整性纯属主 session 信任边界（与数值一致性同口径），anchor_lint 不管。
- **主次判定**：推荐 (a) 部分——钉 broad+outside-voice 廉价高价值；动态 per-lens 完整性 defer（(b) 过重，(c) 太松）。

---

## 度量锚（lens-metric，metrics.enabled=true·pre-gate 草稿值，SR-M 拍板时最终化）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="—" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="5" sev="致0/高2/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="6" 采纳="5" 裁掉="1" defer="0" 独立="3" sev="致0/高1/中2/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="4" 采纳="1" 裁掉="3" defer="0" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="2" sev="致0/高2/中1/低0" -->

---

## 结论
- 冷镜抓出 2 条我设计漏的高危（H1 metrics 100% 消费仓假阻、H3 roadmap 未调和）+ 多条紧固——**冷层 load-bearing 再次兑现**。
- 12 项自动采纳（[spec-review-amendment] 已回写）+ 2 项需拍板（Q1/Q2）。

## 设计门拍板记录（2026-07-07）
- **Q1 = (a)** copy_bundle 一并刷契约（fold init.py + 测试，防本地 pin 部署错配）。
- **Q2 = (a)** metrics 开时钉 `broad`+`outside-voice` 最小必有行；动态 per-lens 完整性留主 session 信任边界。
- 全部 12 自动采纳 + Q1(a)/Q2(a) 已 [spec-review-amendment] 回写 design/specs/tasks/proposal，validate ✓。
- 用户预授权「spec-review → ship」+ 答毕 Q1/Q2 = **过设计 HARD-GATE**，进 SDD。

<!-- ship-gate: design-approved -->
