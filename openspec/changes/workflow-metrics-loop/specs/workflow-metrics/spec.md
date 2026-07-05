## ADDED Requirements

### Requirement: 度量锚契约 sdflow:lens-metric v1 为结构化行级机读锚

评审**价值** SHALL 以结构化锚行 `sdflow:lens-metric v1` 记录，一行对应一（层, 镜, runner, 轮）四元组，MUST NOT 以自由 prose 承载（否则跨 change 聚合须 parse 自由文本，措辞漂移即腐坏——ROADMAP adr/0006(b) 禁「prose 治 prose」）。契约字段与取值域 SHALL 由 `sdflow-init/assets/workflow/` 下的**单一权威规范**定义，各生产者 SKILL 引用而 MUST NOT 复制字段清单。

字段：`layer`（`spec-review`|`code-review`）、`lens`（`domain`|`adversarial`|`grounding`|`history`|`outside-voice`|`broad`）、`runner`（`claude`|`codex`|`claude-fallback`）、`findings`（int≥0，去重前自报数）、`采纳`/`裁掉`/`defer`（int≥0）、`独立`（int≥0）、`sev`（`致N/高N/中N/低N`，仅采纳项）。〔grill-amendment：原含 `dur_s`，因无诚实数据源砍除，成本另立 T29——见 design ADR-3〕

`lens` 字段 SHALL 为 **canonical 投影**（非报告「源」列逐字）：主 session 写锚时按规范映射折叠——完整性镜并入 `grounding`、编号对抗镜（对抗镜1/2/3）折叠到 `adversarial`、autoplan/gstack 各子声折叠到 `broad`、codex/fallback 折叠到 `outside-voice`（映射表见 design ADR-2）。`独立` SHALL 在**折叠到类型之后**计算。

**归属规则 MUST 钉死**：`findings/采纳/裁掉/defer` 按「哪些镜报过该 finding」归属，共抓则每命中镜各记一次；`独立` 仅在「唯一报过 ∧ 被采纳」时 +1。

#### Scenario: 每镜落一行合规锚
- **WHEN** 一轮 spec-review 或 code-review 的 Step3 裁决完成
- **THEN** 每个参与镜 SHALL 在对应 review 报告落一行 `sdflow:lens-metric v1` 锚，字段齐全、取值在域内，且 `findings` 与该镜合并池实收数一致

#### Scenario: 锚字段缺失被自检阻塞
- **WHEN** 出报告后机械核验发现某镜锚缺必填字段（如漏 `独立`）
- **THEN** 本步 SHALL 报错阻塞（复用现有锚存在性自检机制扩一类），MUST NOT 静默放行


### Requirement: 独立贡献在 Step3 去重时导出，塌进 per-镜锚

主 session 在 Step3 去重（同一问题多镜命中合并）时 SHALL 记录每条 finding 的命中镜集合，据此为每（canonical）镜导出 `独立` 标量（该镜类型单独抓到且被采纳的条数），MUST NOT 要求 per-finding 独立锚（过度插桩）。`独立` 是「淘汰哪镜」的唯一非冗余真轴，与采纳率（精度）并存回答两个不同问题。`独立` 对 dedup 合并粒度敏感（「同一问题」无 ground truth，合并松紧影响计数），故 SHALL 作 **N 轮噪声 flag** 供人复评，MUST NOT 作单轮自动砍镜依据。

#### Scenario: 共抓 finding 不计入任一镜的独立
- **WHEN** 一条被采纳的 finding 由 `domain` 与 `outside-voice` 共同报出
- **THEN** 两镜的 `采纳` 各 +1，但两镜的 `独立` 均 SHALL NOT +1（非唯一贡献）

#### Scenario: 同类型多实例共抓仍算该类型独立
- **WHEN** 一条被采纳的 finding 由 `对抗镜1` 与 `对抗镜2` 报出、无其他类型镜报出
- **THEN** 折叠到类型后 `adversarial` 的 `独立` SHALL +1（编号实例是并行、非不同镜类型）

#### Scenario: 完整性镜折叠进 grounding
- **WHEN** 报告「源」列标为 `完整性镜` 或 `完整性/接地镜`
- **THEN** 写锚时 SHALL 折叠为 canonical `grounding`，MUST NOT 新增第 7 值

### Requirement: 跨 change 聚合为只读可重生 view，不落新持久态

聚合 SHALL 由只读脚本 grep 所有归档 review 报告的 `lens-metric` 锚产出，输出**多列可排序**的各镜价值表；锚行本身 SHALL 为 state 真相源，聚合表 SHALL 为可随时重跑的 view，MUST NOT 写入新持久化聚合文件/数据库（守盘面即状态、避免双写不一致）。字段提取解析器**是净新路径**（现有 `_line_scoped_hits` 仅做固定字符串存在性检测、提不了字段），MUST 沿用同一 **fence-aware 行级纪律**（跳 fenced block、锚独占行前缀匹配、受限 kv 解析、**禁裸 `split`/substring**），SHALL 在聚合器内重实现 fence 核而 MUST NOT 跨 skill import `ship_gate`（避免 bundle→sdflow-ship 反向依赖）。聚合器落 `workflow/tools/`（bundle，随 sdflow-init 推下游）。

#### Scenario: 聚合表可重生且标注无锚样本
- **WHEN** 聚合脚本对 ≥2 个归档 change 运行
- **THEN** 输出一张多列可排序表、各镜 `独立` 列非空；对无 `lens-metric` 锚的老报告 SHALL 显式计「无锚样本 N，不纳入」，MUST NOT 静默跳过

#### Scenario: 不产合成价值分
- **WHEN** 聚合输出评审价值维度
- **THEN** SHALL 保持描述性多列（采纳率、独立率、成本分列可排序），MUST NOT 产出单一合成价值分（避免焊死未验证权重、诱导自动砍镜）

### Requirement: 数据驱动反馈供数不供裁决，砍镜由人决

反馈回路 SHALL 把现有「累计 10 次后按采纳率复评是否降采样」从仅 outside-voice 泛化到 per-镜，判据升为**采纳率 + 独立贡献率双列**；保留 / 降采样 / 收紧触发 / 淘汰低价值镜的动作 MUST 由人决，回路 MUST NOT 依数据自动砍镜。

#### Scenario: per-镜累计触发人复评
- **WHEN** 某镜累计满复评窗口（默认 10 轮）
- **THEN** 回路 SHALL 呈现该镜采纳率+独立率供人复评是否降采样/淘汰，MUST NOT 自动执行降采样

### Requirement: grill 层不纳入本能力，amendment 度量显式留档

本能力 SHALL 仅覆盖 spec-review 与 code-review 两同构评审层；grill（对话式 human-in-loop、无 fan-out 镜、无 findings 台账）MUST NOT 被硬套 findings 分桶度量。grill 的「amendment 下游存活率」度量**口径未定义**（`[grill-amendment]` 无 ID/无结构化链接、无 ground truth 关联），SHALL 作为独立 deferred item 留档（记入 issues/todolist，声明需自己的 explore、非本能力实现），MUST NOT 静默丢弃，且 MUST NOT 以裸数 amendment 条数充当度量（多≠好、无采纳/存活分母，误导）。

#### Scenario: grill 不落 lens-metric 锚
- **WHEN** 一轮 grill 完成并产出 `[grill-amendment]`
- **THEN** grill SHALL NOT 落 `sdflow:lens-metric` 锚（层异构语义不符）；其度量口径作为 open sub-item 留档待另立
