## MODIFIED Requirements

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

### Requirement: 跨 change 聚合为只读可重生 view，不落新持久态

聚合 SHALL 由只读脚本 grep 所有归档 review 报告的 `lens-metric` 锚产出，输出**多列可排序**的各镜价值表；锚行本身 SHALL 为 state 真相源，聚合表 SHALL 为可随时重跑的 view，MUST NOT 写入新持久化聚合文件/数据库（守盘面即状态、避免双写不一致）。字段提取解析器**是净新路径**（现有 `_line_scoped_hits` 仅做固定字符串存在性检测、提不了字段），MUST 沿用同一 **fence-aware 行级纪律**（跳 fenced block、锚独占行前缀匹配、受限 kv 解析、**禁裸 `split`/substring**），SHALL 在聚合器内重实现 fence 核而 MUST NOT 跨 skill import `ship_gate`（避免反向依赖）。**〔sdflow-retro SR-K 修订〕聚合器落 `sdflow-retro/scripts/`**（skill 独占——改后唯一运行时消费者 = `/sdflow-retro`，全局安装即用），MUST NOT 再落 bundle `sdflow-init/assets/workflow/tools/`、MUST NOT 再随 `sdflow-init update` 派生到消费仓 `openspec/workflow/tools/`（消费仓不再背此工具；原派生逻辑由本 change 一并撤除）。

#### Scenario: 聚合表可重生且标注无锚样本
- **WHEN** 聚合脚本对 ≥2 个归档 change 运行
- **THEN** 输出一张多列可排序表、各镜 `独立` 列非空；对无 `lens-metric` 锚的老报告 SHALL 显式计「无锚样本 N，不纳入」，MUST NOT 静默跳过

#### Scenario: 聚合器随 skill 全局安装、不再派生消费仓
- **WHEN** 在任意仓运行 `/sdflow-retro`
- **THEN** 聚合器 SHALL 由 skill 自带（`sdflow-retro/scripts/`，setup.sh 全局安装）直接可用，MUST NOT 依赖消费仓 `openspec/workflow/tools/` 存在派生副本

#### Scenario: 不产合成价值分
- **WHEN** 聚合输出评审价值维度
- **THEN** SHALL 保持描述性多列（采纳率、独立率、findings/独立计数、出现轮数分列可排序），MUST NOT 产出单一合成价值分（避免焊死未验证权重、诱导自动砍镜）
