# workflow-retro delta — implement-workflow-optimization-2026-08-p2

## ADDED Requirements

### Requirement: 待复评镜处置记录消费与行内注记

retro 报告生成器 SHALL 消费处置记录文件 `openspec/retro/mirror-dispositions.yaml`（每条含镜匹配键 + `disposition ∈ {保留, 降采样, 淘汰, 不适用}` + 日期 + 依据，降采样条目另含派发条件原文；匹配键与 lens-metric 聚合分组键同构）：待复评区块中命中处置记录的镜行 SHALL 行内追加处置注记（处置结果 + 日期），未命中的照旧 flag。错误语义 SHALL 分治：文件缺失 = 合法零注记态（向后兼容，照旧全 flag）；文件存在但 yaml 不可解析或 `disposition` 取值非法 ⇒ fail-loud 非零退出（宁红勿静默）；文件内存在未命中任何锚组的键 ⇒ 告警不阻断（已淘汰镜的存量条目属合法形态）。处置记录 MUST NOT 影响出现轮数计数本身（注记是呈现层，计数口径不变）。

#### Scenario: 已处置镜行内注记
- **WHEN** 某待复评镜在处置文件中有 `disposition: 降采样` 条目
- **THEN** 再生报告中该镜行追加处置注记（含处置结果与日期），该镜不再以未处置形态裸 flag

#### Scenario: 处置文件缺失时照旧全量 flag
- **WHEN** `mirror-dispositions.yaml` 不存在
- **THEN** 报告生成正常完成，待复评区块行为与引入本能力前一致（全部达阈值镜裸 flag），无告警噪声

#### Scenario: 坏 yaml fail-loud
- **WHEN** 处置文件存在但 yaml 语法坏、或某条 `disposition` 不在合法枚举内
- **THEN** 生成器非零退出并报出坏条目定位；MUST NOT 静默跳过坏条目继续生成（半坏注记比无注记更误导）

#### Scenario: 未命中锚组的存量条目告警不阻断
- **WHEN** 处置文件含一条键未命中当前任何锚组（如已淘汰镜的历史条目）
- **THEN** 报告照常生成，该条目以一行告警呈现，MUST NOT 判为错误退出
