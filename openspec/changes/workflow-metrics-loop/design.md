## Context

**现状**：评审系统三层（grill / spec-review / code-review），后两层是 fan-out 多镜（领域/对抗/接地或历史 + outside-voice + Step1 广审）。唯一度量是 sdflow-code-review 的 `voice分桶`——只覆盖 outside-voice、且写成报告里的自由 prose 行（`voice分桶: codex 采纳3/裁掉0/defer0`）。要回答「哪镜/哪层值不值得留」，现在只能靠 n≈小的口头「实测」。

**ROADMAP 容器**：`workflow-metrics-loop`（暂名，⚪待开）已列——「聚合各层评审报告数据…每 N 个 change 汇总一份，为『哪层值不值得留』供数」，**独立可开**（只读报告产物）。

**预设硬约束（ROADMAP line 21 / adr/0006(b)，materialize 时 MUST 写进 proposal）**：步序/记录用**确定性台账（锚行/脚本判）**，SKILL.md prose 只管每步内部判断——否则是「用 prose 协议治 prose 协议」。这条直接否掉「延续 prose 分桶」的省事路径。

**约束/纪律**：规则改动落 `sdflow-init/assets/workflow/`（bundle 权威源）+ 两 SKILL 源，`sdflow-init update` 推下游；本仓 dogfood 走 propose→review→done。

## Goals / Non-Goals

**Goals：**
- 每轮 spec-review / code-review 的每镜**价值**（findings/裁决/独立/严重度）**结构化落锚**、跨 change **只读可聚合**。
- 复用已验证的 v1 锚行机制（行级 grep、盘面即状态），零新持久态。
- 泛化现有「10 次采纳率复评」到 per-镜，**供数驱动**评审架构调整（人决）。

**Non-Goals：**
- 不测 grill 层（异构，留 open sub-item）；不产合成价值分；不自动砍镜；不建持久聚合文件；不改评审判定逻辑。
- 〔grill-amendment〕**不含成本维度**——原 T29（时长/成本）从本 change 撤出另立（per-镜 dur_s 无诚实数据源，见 ADR-3）；token/usage 同样不测。

## 数据流（本能力一张图）

```
  [镜子代理 domain/adversarial/grounding/history]  [outside-voice codex/fallback]  [Step1 广审]
        │ findings（去重前自报数）                        │ findings                    │ findings
        └──────────────┬─────────────────────────────────┴─────────────────────────────┘
                       ▼  合并池
              主 session Step3：去重(记每条命中镜集合) + 对抗裁决(采纳/裁掉/defer)
                       │  ← 独立 = 只此镜单抓且被采纳〔grill-amendment: dur_s 已砍，见 ADR-3〕
                       ▼  每镜一行
        <!-- sdflow:lens-metric v1 layer=… lens=… runner=… findings=… 采纳=… 裁掉=… defer=… 独立=… sev=… -->
                       ▼  写进 {change_dir}/*-review-report.md，随归档入库
        ────────────────────────────────────────────────────────────
        只读聚合脚本  grep 所有 archive/**/*-review-report.md 的锚 → 多列可排序表（可重生 view，不落新持久态）
                       ▼
        人读表 → per-镜采纳率+独立率双列 → 10 轮节奏复评 → 保留/降采样/收紧触发/淘汰（人决）
```

## `sdflow:lens-metric v1` 锚契约（核心，P0）

一行一镜一轮，主 session 在 Step3 裁决完写入对应 review 报告。字段与取值域：

| 字段 | 取值域 | 语义 | 来源 |
|---|---|---|---|
| `layer` | `spec-review` \| `code-review` | 评审层 | 编排 skill 自知 |
| `lens` | `domain` \| `adversarial` \| `grounding` \| `history` \| `outside-voice` \| `broad` | 镜别 **canonical 投影**（非 `源` 逐字，映射规则见 ADR-2；grounding 仅 spec-review 且含完整性镜；history 仅 code-review；broad=Step1 广审/autoplan/gstack 整体） | 规划镜头时已定，写锚时按 ADR-2 折叠 |
| `runner` | `claude` \| `codex` \| `claude-fallback` | 执行模型（镜=claude；outside-voice=codex/fallback） | fan-out 时已定 |
| `findings` | int≥0 | 该镜**去重前**自报条数 | 子代理返回计数 |
| `采纳` `裁掉` `defer` | int≥0 | 该镜所报 finding 的裁决分桶（**共抓的 finding 记入每个命中镜**） | Step3 裁决 |
| `独立` | int≥0 | 该镜**单独抓到且被采纳**、无其他镜共抓的条数（非冗余真值） | Step3 去重共现导出 |
| `sev` | `致N/高N/中N/低N` | **被采纳** findings 的严重度分布（裁掉的严重度无意义不计） | Step3 |

> 〔grill-amendment〕**`dur_s` 已从 v1 砍除**——接地证实本 harness 不向主 session 暴露子代理 `duration_ms`（全仓零捕获），并行 fan-out 亦无法按镜掐墙钟，子代理自报不可靠。成本维度（原 T29）另立，见 ADR-3。

**归属规则（钉死，防歧义）**：`findings/采纳/裁掉/defer` 按「哪些镜**报过**该条」归属（共抓则每镜各记一次，反映「此镜确实surface了真问题」）；`独立`只在「**唯一**报过 ∧ 被采纳」时 +1（隔离非冗余贡献）。二者并存回答两个不同问题：采纳率=精度，独立率=不可替代性。

## Decisions（ADR，TG-23 每条按三镜 + 主次）

### ADR-1 记录形态 = B 结构化锚（vs A prose 延续 / C 独立 JSONL 台账）
- **选 B**。A（现状 prose）被 ROADMAP 硬约束直接否（prose 治 prose）；C 造新状态源 + 写副作用，与「盘面即状态/零副作用」拧、且要管文件生命周期。
- **三镜**：系统镜——锚机制已存在已验证，扩词汇 << 造新台账，grep 即聚合、零歧义；用户镜——无差别（机器消费）；开发循环镜（**主**）——B 一举消解 ROADMAP 标红的坑，把窄 prose 分桶升级为通用锚（顺带修 M4 现状），C 反而多一层要治的状态。
- **主次**：开发循环镜主导 → B。C 待锚跑出量、真需脱离报告独立查询时再说（现在造 JSONL 是过早基建）。

### ADR-2 独立贡献 = Step3 去重共现导出，塌进 per-镜锚（vs per-finding 锚 / 不测）
- **选「去重导出 + 塌进汇总」**。Step3 去重时主 session 已知每条命中镜集合，`独立=N` 天然可导；per-finding 锚是过度插桩（N 锚/轮），不测则丢掉「淘汰哪镜」的唯一真轴。**接地确认**：现有报告的「源（多源=高置信）」列早已逐条记命中镜集合（spec-review/code-review 皆有，如「四源：领域镜+对抗镜1+gstack-adv+codex(hr-tg)」），前提成立。
- **三镜**：系统镜——共现数据在去重那步免费产生，只需持久化为 per-镜标量；用户镜——无差别；开发循环镜（**主**）——采纳率单独会误留「100%采纳但全冗余」的镜，独立率才是砍镜依据；代价是给热评审路径加一道「记每条命中镜集合」的账（轻，非零）。
- **主次**：开发循环镜主导 → 收，接受去重记账负担。
- **〔grill-amendment 1〕`lens` 字段 = 规范投影（canonical taxonomy），非 `源` 逐字**。接地揭出真实词表比 6 值 enum 又乱又富（`对抗镜1/2/3`、`镜1/3`、`完整性镜`、`CEO/Eng/DX-Claude`、`gstack-adv`、`codex(hr-tg/CV/design-voice)`）。主 session 写锚时按下表映射，`独立` 在**折叠到类型之后**计（对抗镜1、2 都抓、别类型没抓 → 仍算 adversarial 独立）：

  | 真实报告标签 | canonical `lens` |
  |---|---|
  | 领域镜 | `domain` |
  | 对抗镜1/2/3（编号仅并行实例） | `adversarial`（折叠到类型） |
  | 接地镜 / 完整性镜（报告写「完整性/接地镜」连体） | `grounding` |
  | 历史镜（code-review 专有） | `history` |
  | codex(任何 site) / claude-fallback | `outside-voice` |
  | autoplan 的 CEO/Eng/DX/design 子声 + gstack-adv | `broad`（enum 粒度=**可砍单元**：autoplan 是整体外调 skill，砍只能砍「跑不跑广审」，砍不了内部子声） |

- **〔grill-amendment 2〕`独立` 对 dedup 合并粒度敏感（诚实声明）**：「同一问题多镜命中合并」是判断、**无 ground truth**——合并激进则 `独立` 偏低、保守则偏高。故 `独立` 是 **N 轮噪声 flag、非单轮自动砍镜依据**，决策仍人决（与 ADR-5 一致）。

### ADR-3〔grill-amendment〕成本维度暂不纳入本能力，另立 T29——per-镜 dur_s 无诚实数据源（vs 硬撑镜级 dur_s / 阶段级留本 change）
- **前提被接地推翻**：原设计立论「镜级 dur_s = harness `duration_ms`，直接给」。grill 接地核实**三条数据源全断**：① 本 harness 的 Agent 工具只回子代理最终文本，不暴露结构化 `duration_ms`（全仓 grep 零捕获，从没人取到过）；② 镜是一条消息内并行 fan-out，一次 start/一次 end 整批返回，无法按镜隔离墙钟；③ 子代理自报耗时不可靠（不含排队、掐不准起点、可造假）。**填不出的字段会变成永远 `unknown` 的死列或假数据**。
- **决定**：`workflow-metrics` 本能力做**纯价值度量**（findings/采纳/裁掉/defer/独立/sev），`dur_s` 从 v1 锚砍除；成本维度（原 T29）**重新拆出另立**，另开时先解决诚实数据源（阶段级 checkpoint 时间戳差 + 人类门剔除——该数据源真实存在，见 grill T29 调研结论）。
- **三镜**：系统镜——填不出的字段是负债（死列/假数据污染聚合），砍掉比硬撑健康；用户镜——无差别；开发循环镜（**主**）——「该不该留这镜」的决策**本就由价值驱动**（某镜 N 轮 `独立=0` 即可砍，与它多快无关），成本只是分母的锦上添花，无诚实成本不阻塞核心回路。
- **主次**：开发循环镜主导 → 砍 dur_s、价值内核先做扎实，T29 成本另立用真实数据源。这也修正了「全景落地」的原始 scope（那是在错误的「harness 给 duration」前提下选的）。

### ADR-4 层覆盖 = 仅 spec-review + code-review，grill 留 open sub-item（vs 三层全测 / 硬套 grill）
- **选两层**。grill 对话式 human-in-loop、无 fan-out 镜、无 findings 台账，产出是 `[grill-amendment]`/ADR 修正；硬套「findings 分桶」测不了它。
- **三镜**：系统镜——grill 与两评审层的产出模型异构，同锚会污染语义；用户镜——无差别；开发循环镜（**主**）——两评审层同构、锚合身、立刻能落；grill 需另立「amendment 下游存活率」口径，是独立子问题，本轮硬塞会拖慢。
- **主次**：开发循环镜主导 → 两层先落，grill 度量作 Open Questions 显式留档，不静默丢。
- **〔grill-amendment〕排除的诚实性**：grill 恰是**人类时间最贵、价值最不确定**的一层，而「该不该留哪层」正是本系统立命题——排除它 = 最该被数据审视的一层只能靠轶事辩护。**但其度量口径确实未定义**（非逃避）：`[grill-amendment]` 标记**无 ID、无结构化链接**，「amendment 下游存活率」需把具体某条 grill 修正链到具体 spec-review 动作，**无 ground truth 关联** → 需**自己的 explore** 才能落，非本 change 实现范畴。**裸数 amendment 条数是误导指标**（多≠好，无采纳/存活分母）故不采。记一句：grill 价值本 session 有强轶事证据（连揭 dur_s 幻影 / 独立镜词表 / 解析器复用假 3 处），**排除 = 未测 ≠ 无价值**；升级为与 T29 并列的 workflow-metrics-loop 伞下独立 deferred item（口径未定义，先 explore）。

### ADR-5 反馈 = 描述性多列可排序表 + 人决，泛化 10 次复评（vs 合成价值分自动砍）
- **选描述性**。ROADMAP 原话「**供数**」= 供维度非供裁决；合成分焊死未验证权重（藏判断）、诱导照分自动砍。
- **三镜**：系统镜——多列表零权重假设、可加列不破坏既有；用户镜——无差别；开发循环镜（**主**）——保留人复评（沿用现有「10 次后人复评降采样 HR-only」模式），把判据从单一采纳率升为采纳率+独立率双列，砍哪镜仍人决。
- **主次**：开发循环镜主导 → 描述性表 + 人决；顶多给多列可排序辅助，不给单一分。
- **〔grill-amendment Q5〕复评节奏 = per-(layer,lens) 独立计数，计数派生进表（无新计数器）**：eval 单元 = per-(层,镜)（可砍单元；runner 于镜恒 claude，仅 outside-voice 按现有 M4 codex/fallback 细分）；「累计 10 次」由**聚合器从锚派生出「该(层,镜)出现轮数」列**（N≥10 标记待复评），**零新持久计数器**（呼应 ADR-6 view-only）；稀现镜自然推后/不评（低频=低成本，可接受）；surfacing 非自动。**否决全镜共享窗口**（稀现镜会被 n<10 误判）。

### ADR-6 聚合输出不落新持久态 = 可重生 view（盘面即状态 compliance）
- **选「脚本按需重生表，不写持久聚合文件」**。锚行（散在归档报告里）本身即 state 真相源；聚合表是 grep 出来的 view，随时可重跑。
- **三镜**：系统镜——不新增要维护/防漂移的持久态，聚合与真相零脱节风险；用户镜——无差别；开发循环镜（**主**）——守「盘面即状态」红线，避免又一个「总览表与详细块双写不一致」类 bug 面。
- **主次**：开发循环镜主导 → view-only 聚合。

## TG-25 契约文档套件 scope-check（BASE-29）

`lens-metric v1` 是跨多文件版本化契约，改一处牵连一组，落地/后续改版**须同步核**下表全部：

| 文件 | 角色 | 同步义务 |
|---|---|---|
| `sdflow-init/assets/workflow/` 下 metric 锚契约规范（新增） | **契约权威源**（字段/取值域/归属规则/版本号） | 改字段先改此处 |
| `sdflow-code-review/SKILL.md`（Step2半/裁决分桶/报告格式） | **生产者**（落锚 + voice分桶吸收） | 锚字段变更同步 |
| `sdflow-spec-review/SKILL.md`（Step3/报告） | **生产者**（落锚） | 锚字段变更同步 |
| `workflow/tools/` 聚合脚本（新增） | **消费者/解析器**（grep 锚、解析字段） | 字段/取值域变更同步解析 + 反例 |
| `openspec/specs/workflow-metrics/spec.md`（新增）+ `spec-workflow` delta | **规范** | 需求措辞与锚契约一致 |

> 〔grill-amendment〕**「复用」精确化**：`lens-metric` 是参数化锚（需**提取字段值**），与现有 `_line_scoped_hits`（`ship_gate.py:218`，只做**固定字符串存在性检测**，提不了字段）**不同职**；现有 outside-voice v1 锚从未被解析过字段（仅存在性自检 grep）。故聚合器的字段提取解析器**是净新路径**——可复用的是**fence-aware 行级纪律**（跳 fenced block、锚独占行前缀 `<!-- sdflow:lens-metric v1`、受限 kv 解析、**禁裸 `split("|")`/substring**，见记忆 gate-substring-detection-dogfood 坑），**在聚合器内重实现那 ~15 行 fence 核，不跨 skill import `ship_gate`**（避免 bundle→sdflow-ship 反向依赖）；配镜像 ship_gate fence 用例的反例测试。

## Risks / Trade-offs

- [去重记账负担压到热评审路径，主 session 忘记导出 `独立`] → 锚字段设为**必填**，出报告后锚存在性自检（现有 R1/R3/R5 自检机制扩一类）缺字段即报错阻塞。
- 〔grill-amendment〕[原「`broad` dur_s=unknown」风险随成本维度撤出而消解] → 成本另立 T29，本能力无成本列。
- [归属规则「共抓各记一次」使采纳数跨镜重复计，聚合总和 > 实际 finding 数] → 这是**特性非 bug**（度量的是「镜的贡献」非「finding 去重总量」）；聚合表注明「按镜计、含共抓重复」，另给一列去重后 finding 总数供对照。
- [naive parse 锚行遇措辞漂移腐坏（F1-T2 类）] → 消费脚本复用 fence-aware 行级锚解析口径 + 反例测试，禁裸 `split`。
- [两 SKILL 落锚措辞漂移，两生产者不一致] → 契约单一源（权威规范文件），SKILL 只引用不复制字段清单。

〔spec-review-amendment 诚实声明补充〕
- [dedup 合并习惯**系统性漂移**（非 IID 噪声）→ 独立率跨轮趋势可能是合并松紧漂移伪影] → 聚合表旁 MUST 附一行免责：「独立率跨轮不保证同口径，复评时校验最近几轮合并尺度是否一致」；漂移非 N 轮可自动抵消（对抗镜1-2）。
- [普通 fan-out 镜（domain/adversarial/grounding/history）**子代理执行失败 vs 真 0 findings 无区分态**——失败会被写成 `findings=0` 污染分母] → pre-existing（本 change 首次让它载入决策数据）；本 change 不根治（补失败协议超 P0），Risks 显式记，defer 进 todolist（对抗镜1-3）。
- [自指坑残差：review 报告里引用/示范锚语法若未包 fence，聚合器 grep archive 可能误取] → 直白版已证伪（glob 仅 `*-review-report.md`、design.md 不命中；示例锚确在 fence 内）；残差闭合 = TG-25 契约加 MUST「review 报告中示范锚语法 MUST 包 ``` fence 内」〔SR-N〕（对抗镜2-1）。

## Migration Plan

- 纯新增旁路 + 一处 prose→锚 替换，**无数据迁移**。voice分桶吸收：老归档报告的 prose 行不回填（历史样本 n 小），新报告起用锚；聚合脚本只认锚、跳过无锚老报告（显式计「无锚样本 N，不纳入」，不静默）。
- 部署：改 `assets/workflow` 后**开发 checkout 跑 `bash setup.sh`** 让全局 canonical 生效才测得到；合并后运行 checkout `/sdflow-upgrade`。
- 回滚：锚是旁路、聚合是 view，撤下 SKILL 落锚指令即停产新锚，无残留状态。

## Open Questions

- 〔grill 定性 · defer〕**grill 层度量口径未定义 → 需自己的 explore**（非本 change）：`[grill-amendment]` 无 ID/无结构化链接，「amendment 下游存活率」无 ground truth 关联；裸数条数是误导指标故不采。与 T29 并列为 workflow-metrics-loop 伞下独立 deferred item，记入 todolist（见 task 4.2）。
- 〔grill Q3 已解决〕~~聚合脚本落点~~ → **定 `workflow/tools/`**（bundle，随 sdflow-init 推下游；消费仓同样用两评审 SKILL、可复用聚合器）。
- 〔grill Q5 已定〕10 轮复评节奏 = per-(层,镜) 独立计数、聚合器派生列（见 ADR-5）。
- 〔spec-review 决策门 Q1 · SR-D〕**同轮 outside-voice 多 site 撞键**：加可选 `site` 消歧字段（保 hr-tg vs 泛检信号，推荐）vs 钉死合并规则（求和/覆盖）。schema 层决策，实现前须定。
- 〔spec-review 决策门 Q2 · SR-G〕**消费仓 opt-out**：无条件 SHALL 落锚 + 缺字段阻塞随 bundle 推所有消费仓，低频小仓零收益期却背记账+硬阻塞。加 `config.yaml` 开关（默认源仓 on / 下游 off 或自检降软警告，推荐）vs 无条件全推（接受下游负担）。

## Compliance

- **ROADMAP line 21 / adr/0006(b)**：✅ 记录=结构化锚、判定=只读脚本，SKILL prose 不承载跨步状态——已合规，逐落点在 spec-review 接地核验。
- **盘面即状态 / 零副作用**：✅ 锚即 state、聚合即 view、不落新持久态（ADR-6）。
- **bundle 权威源纪律**：✅ 契约与规则落 `assets/workflow`，SKILL 引用不复制；改后 setup.sh 推 canonical。
- **不改评审判定逻辑**：✅ 锚为旁路，有无不影响 findings 采纳——design 与 spec 均声明。
