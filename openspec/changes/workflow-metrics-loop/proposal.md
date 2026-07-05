## Why

评审系统（spec-review / code-review 各多镜 + outside-voice）目前**无法回答「哪一镜/哪一层值不值得留」**——现有依据是 n≈小的口头「实测」（如 P3c 断言 sdflow-code-review 值得每次全跑），以及唯一一颗窄度量苗子（sdflow-code-review 的 `voice分桶` 只测 outside-voice，且记为**报告里的自由 prose**，跨 change 聚合须 parse 自由文本、措辞一漂就腐坏——正是 F1-T2「naive split」那类脆弱）。ROADMAP 早已列出 `workflow-metrics-loop`（⚪待开）作为容器，本 change 将其落地：让每一轮评审的价值与成本**可被结构化记录、跨 change 聚合、数据驱动决定评审架构**（保留 / 降采样 / 收紧触发 / 淘汰低价值镜）。

## What Changes

- **新增结构化度量锚行 `sdflow:lens-metric v1`**：spec-review / code-review 每镜每轮落一行机读锚，携带 `layer / lens / runner / findings / 采纳 / 裁掉 / defer / 独立 / sev`。**吸收并取代**现有 `voice分桶` prose 行（M4 现状顺带修——把自由文本升级为行级可 grep 的锚）。
- **新增只读聚合脚本**：grep 所有归档报告的 `lens-metric` 锚 → 输出**多列可排序**的「各镜价值表」，每 N change 或按需生成。**不落新持久态**（锚行本身即 state，表是可重生 view——守「盘面即状态」红线）。
- **泛化反馈回路**：把现有「累计 10 次后按采纳率复评是否降采样为 HR-only」从「仅 outside-voice」**泛化到 per-镜**，判据升为**采纳率 + 独立贡献率双列**；动作**仍人决**（回路只供数不供裁决，不自动砍镜）。
- 〔grill-amendment〕**成本维度（原 T29）撤出另立**：grill 接地推翻「harness 给子代理 duration_ms」前提（全仓零捕获 + 并行 fan-out 无法按镜掐墙钟 + 自报不可靠），per-镜 `dur_s` 无诚实数据源 → 从 v1 锚砍除；本 change 做**纯价值度量**，成本另开时先解决阶段级 checkpoint 时间戳数据源（见 design ADR-3 + grill T29 调研）。
- **grill 层暂不纳入**：grill 是对话式 human-in-loop、无 fan-out 镜、无 findings 台账，硬套「findings 分桶」测不了；其「amendment 下游存活率」度量作为**显式 open sub-item 留档**，不在本次实现。
- **NOT（明确不做）**：合成价值分（供数非供裁决，避免焊死未验证权重）、per-finding 锚（塌进 per-镜汇总）、成本/时长（撤出另立 T29）、token/usage。

## Capabilities

### New Capabilities
- `workflow-metrics`: 评审**价值**度量回路——结构化度量锚契约（`sdflow:lens-metric v1`）、只读跨 change 聚合、per-镜数据驱动反馈（人决）；covers 记录形态、聚合脚本、反馈判据、grill 留档边界。〔grill-amendment：成本维度撤出另立 T29〕

### Modified Capabilities
- `spec-workflow`: 评审编排规则新增「每镜落度量锚」义务（spec-review / code-review 两 SKILL 的产出契约变化——现 `voice分桶` prose → `lens-metric` 锚；独立贡献在 Step3 去重时导出）。

## 需求优先级（TG-19）

- **P0**：`lens-metric v1` 锚契约（字段/取值域/落点）+ spec-review·code-review 两 SKILL 落锚 + 现有 voice分桶吸收。度量的地基，无它其余无数据。
- **P1**：只读聚合脚本（多列可排序表）+ 独立贡献去重导出规则。有数据后才谈聚合与「独立」这一真轴。
- **P2**：反馈回路泛化（per-镜双列判据、人复评节奏）。回路闭合，但可在锚+聚合稳定后叠加。〔grill-amendment：原含镜级 dur_s + 阶段级成本汇总，已随成本维度撤出另立 T29〕

## Success Metrics

- 一轮 spec-review + 一轮 code-review 跑完，机械 grep 能取到**每镜一行** `lens-metric v1` 锚，字段齐全、`findings=N` 与合并池实收数一致。
- 〔spec-review-amendment SR-H〕**本 change 验收 = pytest fixture**（合成 ≥2 份带锚报告，验聚合/去重导出/fence-aware 解析逻辑正确、独立列非空）——现有归档报告**零** `lens-metric` 锚，故「对真实归档 change 跑出非空表」是**部署后观察项**（须本 change ship 后再有 ≥2 个后续 change 走完全流程才满足），MUST NOT 作本 change 的 verify 门槛（否则 verify 拿不出机验锚点、被自造的「未来时」指标卡死）。
- 现有 `voice分桶` prose 行在 code-review 报告中**已被锚取代**（grep 无残留自由文本分桶）。

## Non-Goals

- 不测 grill 层（其 amendment 存活率度量留 open sub-item）。
- 不产合成价值分 / 不做自动砍镜（人决保留）。
- 〔grill-amendment〕不含成本/时长维度（原 T29 撤出另立，per-镜 dur_s 无诚实数据源）；不测 token/usage。
- 不新建持久化聚合文件 / 数据库（盘面即状态，聚合是可重生 view）。
- 不改评审的**判定逻辑**（只加旁路记录，锚的有无不改 findings 采纳与否）。

## Compliance

- **ROADMAP 硬约束（line 21 / adr/0006(b)）**：记录用**确定性锚行 + 脚本判**，SKILL.md prose 只管每步内部判断——**禁用 prose 协议治 prose 协议**。本设计（B 结构化锚 + 只读聚合脚本）已合规，design 将显式声明并对每处落点核验。
- **bundle 权威源纪律**：规则改动落 `sdflow-init/assets/workflow/`（唯一权威源）+ 两 SKILL 源，经 `sdflow-init update` 推下游；禁只改下游副本。

## Impact

- **改**：`sdflow-code-review/SKILL.md`（Step2半/裁决分桶/报告格式台账）、`sdflow-spec-review/SKILL.md`（Step3 裁决/报告）——落 `lens-metric` 锚、独立贡献去重导出、voice分桶吸收。
- **新增**：`sdflow-init/assets/workflow/` 下 metric 锚契约规范 + `workflow/tools/` 只读聚合脚本；`openspec/specs/workflow-metrics/spec.md` 新能力 spec + `spec-workflow` delta。
- **依赖**：现有 v1 锚行机制（复用其行级 fence-aware grep 契约）。〔grill-amendment：原列 harness `duration_ms` 依赖已删——该源不存在，见 ADR-3〕
- **TG 命中**：TG-19（多需求，已标优先级）· TG-23（记录形态 A/B/C 等≥2 方案 → design ADR + 三镜）· TG-25（`lens-metric v1` 是跨多文件版本化契约 → design 加 scope-check 表 BASE-29）。技术栈为 Markdown+Python，不命中 backend/embedded/frontend 领域清单。
