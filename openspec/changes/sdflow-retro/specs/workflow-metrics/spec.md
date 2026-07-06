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
