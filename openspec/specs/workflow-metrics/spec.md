# workflow-metrics Specification

## Purpose
TBD - created by archiving change workflow-metrics-loop. Update Purpose after archive.
## Requirements
### Requirement: 度量锚契约 sdflow:lens-metric v1 为结构化行级机读锚

评审**价值** SHALL 以结构化锚行 `sdflow:lens-metric v1` 记录，一行对应一（层, 镜, **宿主**, runner, 轮）**五**元组〔add-codex-host-support：原四元组不含 host，导致 Codex 宿主的自审轮次与 Claude 宿主的真跨模型轮次**无法区分**〕，MUST NOT 以自由 prose 承载（否则跨 change 聚合须 parse 自由文本，措辞漂移即腐坏——ROADMAP adr/0006(b) 禁「prose 治 prose」）。契约字段与取值域 SHALL 由 `sdflow-init/assets/workflow/` 下的**单一权威规范**定义，各生产者 SKILL 引用而 MUST NOT 复制字段清单。

字段：`layer`（`spec-review`|`code-review`）、`lens`（`domain`|`adversarial`|`grounding`|`history`|`outside-voice`|`broad`）、**`host`（`claude`|`codex`|`unknown`——谁在跑这次评审，由 `resolve-models.sh` 按正信号判定，见能力 `host-adaptive-execution`）**、`runner`（`claude`|`codex`|`none`|`unknown`——**谁执行了这个镜，只记机队家族**；`none` = 该轮无执行〔D6：host-unknown/secret-hit/fallback-unavailable 用之，伴 `findings=0`〕；`unknown` = host=unknown 时普通镜的主审机队〔spec-review-r3 codex#1，**仅合法于非-outside-voice 普通镜行 ∧ host=unknown**；outside-voice 锚 runner 恒 ∈{claude,codex,none}，受合法组合矩阵约束不取 unknown〕）、`site`（**可选消歧**：`code-voice`|`hr-tg`|`design-voice`|`—`，**仅 `outside-voice` 用、不进 `lens` enum**——消同轮多次 voice 调用的撞键，保 hr-tg 定向复核 vs 泛检信号区分〔SR-D 决策门 Q1=A〕）、`findings`（int≥0，去重前自报数）、`采纳`/`裁掉`/`defer`（int≥0）、`独立`（int≥0）、`sev`（`致N/高N/中N/低N`，仅采纳项）。〔grill-amendment：原含 `dur_s`，因无诚实数据源砍除，成本另立 T29——见 design ADR-3〕

**「跨模型性」SHALL 为派生量、由能力 `host-adaptive-execution` 的合法组合矩阵机械判定（`host,runner 均∈{claude,codex} ∧ runner≠host ∧ reason_code="ok"`），MUST NOT 编码进 `runner` 枚举值、亦 MUST NOT 简写为裸 `runner ≠ host`**〔add-codex-host-support · spec-review-r2 C1：裸 `runner≠host` 被 `runner="none"`（`none≠host` 恒真）击穿〕。`claude-fallback` **枚举值废弃**——它把"跨模型性"藏进了枚举值，在 Codex 宿主下必然说谎。矩阵三态：跨模型第二意见（上式）/ 同族 fallback（`runner==host`）/ 无执行（`runner="none" ∧ findings=0`，非跨模型）。

`lens` 字段 SHALL 为 **canonical 投影**（非报告「源」列逐字）：按规范映射折叠——完整性镜并入 `grounding`、编号对抗镜（对抗镜1/2/3）折叠到 `adversarial`、autoplan/gstack 各子声折叠到 `broad`、**任一 runner 的 outside voice 折叠到 `outside-voice`**（映射表见契约 `lens-metric-fold` 机读块）。`独立` SHALL 在**折叠到类型之后**计算。

**归属规则 MUST 钉死**：`findings/采纳/裁掉/defer` 按「哪些镜报过该 finding」归属，共抓则每命中镜各记一次；`独立` 仅在「唯一报过 ∧ 被采纳」时 +1。`sev` 子格式 MUST 钉死为 `致N/高N/中N/低N` 四级**定序、零也写 0、分隔符恒 `/`**（禁省略某级或改序，防自由子格式脆弱——F1-T2 类）〔spec-review-amendment SR-I〕。

**〔mlh-p4-lens-metric-emit〕计数归约由确定性 emitter 执行、非手数**：上述折叠（原始镜名 → canonical `lens`）+ 归属（`findings/采纳/裁掉/defer` 每命中**行键**各记一次）+ `独立`（唯一报过 ∧ 被采纳、折叠到**行键**后计）+ `sev` rollup（仅采纳项）SHALL 由 `lens_metric_emit.py` 对**主 session 给的结构化 findings + 本轮行键 roster**确定性归约产出，MUST NOT 再由主 session 手折叠手数手写锚。**行键 SHALL 为 `(lens, host, runner, site)`**〔add-codex-host-support：由 `(lens,runner,site)` 升维，与锚唯一键对齐〕。折叠映射 SHALL 由契约 `lens-metric-fold` 机读块**单一源**承载、`fold(raw)=raw if∈lens_enum elif fold_map else fail-closed`〔spec-review-amendment ADR-7 恒等 pass-through〕；`load_fold` 后 SHALL 自校验 codomain⊆`lens-enum`〔spec-review-amendment C3〕。emitter **门控外置、不读 config**（关时 SKILL 不调 emitter）〔spec-review-amendment ADR-10〕；layer 单一源=`--layer`、无 per-finding layer〔ADR-9〕。emitter 详细契约见能力 `lens-metric-emit`。**去重（是否同一 finding）+ 对抗裁决 + 严重度定级** SHALL 保留给模型（产出结构化输入），emitter 只做机械归约、MUST NOT 越权做判断。

〔spec-review-amendment SR-E〕**enum 扩展治理**：新增镜类型（6 值 `lens` 枚举未列的）MUST 先升契约版本号至 `v2` 并更新折叠表，**MUST NOT 静默塞入 `broad`**（`broad` 是低区分度兜底桶，新镜价值信号被广审噪声稀释 = 反噬「数据驱动优化评审架构」本命题）。**新增宿主（第三个机队）MUST 扩 `host`/`runner` 枚举**，MUST NOT 复用 `unknown` 承载已知的第三方宿主〔add-codex-host-support：`unknown` 的语义是"判不出"，不是"其他"〕。

〔spec-review-amendment SR-D · 决策门 Q1=A 已定〕**同轮多次 outside-voice 调用以 `site` 消歧**：`outside-voice` 同轮的 `code-voice`/`hr-tg`（或 `design-voice`/`hr-tg`）各落**独立一行**、以 `site` 区分（唯一性键为 `(layer,lens,host,runner,site,轮)`），MUST NOT 加总成一行抹掉 hr-tg vs 泛检的区分。非 outside-voice 镜 `site=—`。

#### Scenario: 每镜落一行合规锚
- **WHEN** 一轮 spec-review 或 code-review 的 Step3 裁决完成
- **THEN** 每个参与镜 SHALL 在对应 review 报告落一行 `sdflow:lens-metric v1` 锚，字段齐全（**含 `host`**）、取值在域内，且 `findings` 与该镜合并池实收数一致

#### Scenario: 锚字段缺失或取值越域被自检阻塞
- **WHEN** 出报告后机械核验发现某镜锚缺必填字段（如漏 `独立` 或**漏 `host`**），**或 `layer`/`lens`/`host`/`runner`/`sev` 取值不在枚举域/子格式内**（如 `lens=对抗镜1` 未折叠成 `adversarial`，或 `runner=claude-fallback` 用了已废弃的值）
- **THEN** 本步 SHALL 报错阻塞（复用现有锚存在性自检机制扩一类，**含枚举域 + sev 子格式校验**），MUST NOT 静默放行

#### Scenario: 自审锚行被自检阻塞〔add-codex-host-support · spec-review-amendment D1/D2〕
- **WHEN** 某 **`sdflow:outside-voice` 锚**（**非 lens-metric 锚**——只有 outside-voice 锚同时承载 `runner`/`host`/`reason_code`；绑到无 `reason_code` 的 lens-metric 锚会使红线静默永不触发）的 `runner == host` 且 `reason_code ∉ {not-installed, preflight-error, timeout, exec-error}`（即非合法同族降级、却声称拿到跨模型第二意见）
- **THEN** `anchor_lint` SHALL 报错阻塞——`runner == host` 的 voice 依定义**不是**跨模型，MUST NOT 作为跨模型证据落账（此即**合法组合矩阵**同族行子句，spec-review-r2 C1）。**合法降级码集 SHALL 钉死为 `{not-installed, preflight-error, timeout, exec-error}`**〔D2：grill G5 初钉漏了 `preflight-error`；`missing-deps` 现定死归约入 `preflight-error`（D7），不留实现期裁量〕；成功跨模型路径 `reason_code="ok"`（D5，非 none）；`anchor_lint` SHALL **新增 outside-voice 锚的 KV 字段解析**（现状零字段解析）；此校验 **MUST always-on、独立成函数、不受 `metrics.enabled` 门控**（D7/D11：读真实性信号）

#### Scenario: fan-out 机制死却报多镜被一致性 lint 阻塞（always-on，判据读 mirrors=）〔add-codex-host-support · spec-review-amendment Q1 · adr/0023 · spec-review-r2 C2〕
- **WHEN** 会话级 `sdflow:fanout-capability` 锚记 `subagents="unavailable"`，而**同锚 `mirrors=`** 清单中 `∈ {domain,adversarial,grounding,history}`（**按值去重**）的计数 > 1
- **THEN** `anchor_lint` SHALL 报错阻塞（违规类型 `dead-fanout-multi-mirror`）——这是**锚行自身的自相矛盾**（机制死却报多镜），**不是伪造拦截**（主 session 写 `subagents="available"` 或只列 1 镜即绕过）；判据 **MUST 读 `fanout-capability` 锚的 `mirrors=`、MUST NOT 数 lens-metric 行**〔spec-review-r2 C2 纠正首轮致命洞：lens-metric 行在生产端受 `metrics.enabled` 门控，默认消费仓 metrics=false ⇒ 零行 ⇒ lint 空转；`mirrors=` 由 SKILL 直接落、不受该门控〕；此校验及其判据数据 **MUST always-on、与 `metrics.enabled` 解耦**。MUST NOT 声称「头号假绿事前拦截」——只拦机制死变体，机制活+偷懒自代变体留语义层

#### Scenario: 宿主分组可事后区分真跨模型与自审轮次〔add-codex-host-support〕
- **WHEN** 复盘聚合器读取跨 change 的 lens-metric 锚
- **THEN** SHALL 可按 `host` 分组统计，使 Codex 宿主轮次与 Claude 宿主轮次的采纳率/独立率分别可见，MUST NOT 混算（混算会让一方的自审数据污染另一方的真跨模型信号）

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

聚合 SHALL 由只读脚本 grep 所有归档 review 报告的 `lens-metric` 锚产出，输出**多列可排序**的各镜价值表；锚行本身 SHALL 为 state 真相源，聚合表 SHALL 为可随时重跑的 view，MUST NOT 写入新持久化聚合文件/数据库（守盘面即状态、避免双写不一致）。字段提取解析器**是净新路径**（现有 `_line_scoped_hits` 仅做固定字符串存在性检测、提不了字段），MUST 沿用同一 **fence-aware 行级纪律**（跳 fenced block、锚独占行前缀匹配、受限 kv 解析、**禁裸 `split`/substring**），SHALL 在聚合器内重实现 fence 核而 MUST NOT 跨 skill import `ship_gate`（避免 bundle→sdflow-ship 反向依赖）。**〔sdflow-retro SR-K 修订〕聚合器落 `sdflow-retro/scripts/`**（skill 独占——改后唯一运行时消费者 = `/sdflow-retro`，全局安装即用），MUST NOT 再落 bundle `sdflow-init/assets/workflow/tools/`、MUST NOT 再随 `sdflow-init update` 派生到消费仓 `openspec/workflow/tools/`（消费仓不再背此工具；原派生逻辑由本 change 一并撤除。**注：init.py 的 `ignore_patterns("tests")` 通用 tools/tests 排除 MUST 保留——它非聚合器专属，仍护 `trivial_shape.py` 部署**）。

#### Scenario: 聚合表可重生且标注无锚样本
- **WHEN** 聚合脚本对 ≥2 个归档 change 运行
- **THEN** 输出一张多列可排序表、各镜 `独立` 列非空；对无 `lens-metric` 锚的老报告 SHALL 显式计「无锚样本 N，不纳入」，MUST NOT 静默跳过

#### Scenario: 聚合器随 skill 全局安装、不再派生消费仓
- **WHEN** 在任意仓运行 `/sdflow-retro`
- **THEN** 聚合器 SHALL 由 skill 自带（`sdflow-retro/scripts/`，setup.sh 全局安装）直接可用，MUST NOT 依赖消费仓 `openspec/workflow/tools/` 存在派生副本

#### Scenario: 不产合成价值分
- **WHEN** 聚合输出评审价值维度
- **THEN** SHALL 保持描述性多列（采纳率、独立率、findings/独立计数、出现轮数分列可排序），MUST NOT 产出单一合成价值分（避免焊死未验证权重、诱导自动砍镜）〔spec-review-amendment SR-J：删原「成本分列」——成本维度已撤出另立 T29〕

### Requirement: 数据驱动反馈供数不供裁决，砍镜由人决

反馈回路 SHALL 把现有「累计 10 次后按采纳率复评是否降采样」从仅 outside-voice 泛化到 per-镜，判据升为**采纳率 + 独立贡献率双列**；保留 / 降采样 / 收紧触发 / 淘汰低价值镜的动作 MUST 由人决，回路 MUST NOT 依数据自动砍镜。〔spec-review-amendment SR-A〕**主动 surfacing（防死列）**：`N≥10 未复评` 的镜 MUST 有一个**机械 surfacing 点**显著提示（只读聚合表、只提示不判断），MUST NOT 仅靠人记得手动跑聚合脚本（无主动提示的被动列 = 实践中等价永不被看见的死列，同 `grill-not-skippable` 教训：待办判定不埋进长消息、须显著呈现）。回路的立项理由正是「现状无人主动验证」，若聚合表同样无人主动开 = 同一失败模式换格式重演。

**〔sdflow-retro：surfacing 正主迁移〕** 该机械 surfacing 点的**正主** SHALL 为 `/sdflow-retro`（workflow 复盘评估的正主 skill，聚合镜价值 + 时间维成完整复盘），MUST NOT 再以 `/sdflow-maintain`（INDEX.md 维护 skill）为 surfacing 逻辑的承载者。`/sdflow-maintain` 收尾 SHALL 保留一个**薄指针**——归档后显著提示「跑 `/sdflow-retro` 看完整复盘（含 N≥10 待复评镜）」，以不丢"归档后自动提醒"的 cadence（策略 B）；该指针 MUST NOT 内联聚合逻辑（聚合单一真相源在 retro）。

#### Scenario: per-镜累计触发人复评
- **WHEN** 某镜累计满复评窗口（默认 10 轮）
- **THEN** 回路 SHALL 呈现该镜采纳率+独立率供人复评是否降采样/淘汰，MUST NOT 自动执行降采样

#### Scenario: N≥10 未复评项被机械显著提示〔surfacing 正主 = sdflow-retro〕
- **WHEN** `/sdflow-retro` 运行时聚合表存在某镜 `出现轮数≥10` 且未登记复评
- **THEN** SHALL 在复盘报告**显著**呈现该镜待复评（只提示不判断、不自动砍），MUST NOT 埋进长报告不显著呈现

#### Scenario: sdflow-maintain 保留薄指针不丢 cadence
- **WHEN** `/sdflow-maintain` 归档后运行、收尾
- **THEN** SHALL 显著提示"跑 `/sdflow-retro` 看完整复盘（含待复评镜）"，MUST NOT 内联聚合镜价值（聚合正主已迁 retro）、MUST NOT 静默省略该指针

### Requirement: grill 层不纳入本能力，amendment 度量显式留档

本能力 SHALL 仅覆盖 spec-review 与 code-review 两同构评审层；grill（对话式 human-in-loop、无 fan-out 镜、无 findings 台账）MUST NOT 被硬套 findings 分桶度量。grill 的「amendment 下游存活率」度量**口径未定义**（`[grill-amendment]` 无 ID/无结构化链接、无 ground truth 关联），SHALL 作为独立 deferred item 留档（记入 issues/todolist，声明需自己的 explore、非本能力实现），MUST NOT 静默丢弃，且 MUST NOT 以裸数 amendment 条数充当度量（多≠好、无采纳/存活分母，误导）。

#### Scenario: grill 不落 lens-metric 锚
- **WHEN** 一轮 grill 完成并产出 `[grill-amendment]`
- **THEN** grill SHALL NOT 落 `sdflow:lens-metric` 锚（层异构语义不符）；其度量口径作为 open sub-item 留档待另立

