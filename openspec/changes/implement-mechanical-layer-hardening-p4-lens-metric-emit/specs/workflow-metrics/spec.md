## MODIFIED Requirements

### Requirement: 度量锚契约 sdflow:lens-metric v1 为结构化行级机读锚

评审**价值** SHALL 以结构化锚行 `sdflow:lens-metric v1` 记录，一行对应一（层, 镜, runner, 轮）四元组，MUST NOT 以自由 prose 承载（否则跨 change 聚合须 parse 自由文本，措辞漂移即腐坏——ROADMAP adr/0006(b) 禁「prose 治 prose」）。契约字段与取值域 SHALL 由 `sdflow-init/assets/workflow/` 下的**单一权威规范**定义，各生产者 SKILL 引用而 MUST NOT 复制字段清单。

字段：`layer`（`spec-review`|`code-review`）、`lens`（`domain`|`adversarial`|`grounding`|`history`|`outside-voice`|`broad`）、`runner`（`claude`|`codex`|`claude-fallback`）、`site`（**可选消歧**：`code-voice`|`hr-tg`|`design-voice`|`—`，**仅 `outside-voice` 用、不进 `lens` enum**——消同轮多次 codex 调用的四元组撞键，保 hr-tg 定向复核 vs 泛检信号区分〔SR-D 决策门 Q1=A〕）、`findings`（int≥0，去重前自报数）、`采纳`/`裁掉`/`defer`（int≥0）、`独立`（int≥0）、`sev`（`致N/高N/中N/低N`，仅采纳项）。〔grill-amendment：原含 `dur_s`，因无诚实数据源砍除，成本另立 T29——见 design ADR-3〕

`lens` 字段 SHALL 为 **canonical 投影**（非报告「源」列逐字）：按规范映射折叠——完整性镜并入 `grounding`、编号对抗镜（对抗镜1/2/3）折叠到 `adversarial`、autoplan/gstack 各子声折叠到 `broad`、codex/fallback 折叠到 `outside-voice`（映射表见 design ADR-2）。`独立` SHALL 在**折叠到类型之后**计算。

**归属规则 MUST 钉死**：`findings/采纳/裁掉/defer` 按「哪些镜报过该 finding」归属，共抓则每命中镜各记一次；`独立` 仅在「唯一报过 ∧ 被采纳」时 +1。`sev` 子格式 MUST 钉死为 `致N/高N/中N/低N` 四级**定序、零也写 0、分隔符恒 `/`**（禁省略某级或改序，防自由子格式脆弱——F1-T2 类）〔spec-review-amendment SR-I〕。

**〔mlh-p4-lens-metric-emit〕计数归约由确定性 emitter 执行、非手数**：上述折叠（原始镜名 → canonical `lens`）+ 归属（`findings/采纳/裁掉/defer` 每命中镜各记一次）+ `独立`（唯一报过 ∧ 被采纳、折叠后计）+ `sev` rollup（仅采纳项）SHALL 由 `lens_metric_emit.py` 对**主 session 给的结构化 findings + 本轮 lens roster**〔grill-amendment：roster 补零-finding 镜的强制行〕确定性归约产出，MUST NOT 再由主 session 手折叠手数手写锚。折叠映射 SHALL 由契约 `lens-metric-fold` 机读块**单一源**承载〔grill-amendment：原折叠仅活在 prose ADR-2、无代码单一源，本 change 机读化根治〕。emitter 详细契约见新增能力 `lens-metric-emit`。**去重（是否同一 finding）+ 对抗裁决 + 严重度定级** SHALL 保留给模型（产出结构化输入），emitter 只做机械归约、MUST NOT 越权做判断。

〔spec-review-amendment SR-E〕**enum 扩展治理**：新增镜类型（6 值 `lens` 枚举未列的）MUST 先升契约版本号至 `v2` 并更新 ADR-2 折叠表，**MUST NOT 静默塞入 `broad`**（`broad` 是低区分度兜底桶，新镜价值信号被广审噪声稀释 = 反噬「数据驱动优化评审架构」本命题）。

〔spec-review-amendment SR-D · 决策门 Q1=A 已定〕**同轮多次 outside-voice 调用以 `site` 消歧**：`outside-voice` 同轮的 `code-voice`/`hr-tg`（或 `design-voice`/`hr-tg`）各落**独立一行**、以 `site` 区分（唯一性键升为 `(layer,lens,runner,site,轮)`），MUST NOT 加总成一行抹掉 hr-tg vs 泛检的区分。非 outside-voice 镜 `site=—`。

#### Scenario: 每镜落一行合规锚
- **WHEN** 一轮 spec-review 或 code-review 的 Step3 裁决完成
- **THEN** 每个参与镜 SHALL 在对应 review 报告落一行 `sdflow:lens-metric v1` 锚，字段齐全、取值在域内，且 `findings` 与该镜合并池实收数一致

#### Scenario: 锚字段缺失或取值越域被自检阻塞
- **WHEN** 出报告后机械核验发现某镜锚缺必填字段（如漏 `独立`），**或 `layer`/`lens`/`runner`/`sev` 取值不在枚举域/子格式内**（如 `lens=对抗镜1` 未折叠成 `adversarial`）〔spec-review-amendment SR-C〕
- **THEN** 本步 SHALL 报错阻塞（复用现有锚存在性自检机制扩一类，**含枚举域 + sev 子格式校验**），MUST NOT 静默放行

#### Scenario: 计数归约机械化，分类正确性为残余信任边界〔mlh-p4-lens-metric-emit 修订 SR-B〕
- **WHEN** 考察 `findings`/`采纳`/`裁掉`/`defer`/`独立` 计数的正确性
- **THEN** 「按归属规则把结构化 findings 折叠成 per-镜计数」SHALL 由 `lens_metric_emit` **确定性归约**（此环节不再是信任边界——脚本保证「计数是所给输入的正确归约」）；但「输入 findings 集是否忠实反映合并池（模型对每条 finding 的命中镜集/裁决/sev 分类是否正确）」SHALL 声明为**残余主 session 信任边界**（judgment，非机械可验），emitter/自检 MUST NOT 谎称能机械保证输入分类正确
