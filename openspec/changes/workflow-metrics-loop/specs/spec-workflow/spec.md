## ADDED Requirements

### Requirement: 评审每镜落度量锚为生产者义务，取代 voice 分桶 prose

`sdflow-spec-review` 与 `sdflow-code-review` 编排器 SHALL 在 Step3 裁决后为每个参与镜落一行 `sdflow:lens-metric v1` 锚（契约见 `workflow-metrics` 能力），其中 code-review 现有的 `voice分桶` 自由 prose 行 SHALL 被 outside-voice 镜的 `lens-metric` 锚**吸收取代**（grep 报告 MUST NOT 再有残留自由文本分桶）。度量锚 SHALL 为旁路记录：其有无 MUST NOT 改变 findings 的采纳与否或评审的推进/拒绝结论。

#### Scenario: code-review 落锚并消除 voice 分桶 prose
- **WHEN** 一轮 code-review 完成裁决
- **THEN** 报告 SHALL 为每镜（含 outside-voice）各落一行 `lens-metric` 锚，且 SHALL NOT 再含 `voice分桶: codex 采纳x/裁掉y...` 自由 prose 行

#### Scenario: spec-review 落锚
- **WHEN** 一轮 spec-review 完成裁决
- **THEN** 报告 SHALL 为领域镜/对抗镜/接地镜/outside-voice/broad 各落一行 `lens-metric` 锚

#### Scenario: 度量锚为旁路不改判定
- **WHEN** 度量锚落锚失败或字段缺失被自检拦截
- **THEN** 拦截的是**报告完整性**（机械失职），SHALL NOT 反向改写已裁决 findings 的采纳结论——锚是旁路观测，非评审判定输入
