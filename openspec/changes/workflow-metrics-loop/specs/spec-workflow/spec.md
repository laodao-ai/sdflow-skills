## ADDED Requirements

### Requirement: 评审每镜落度量锚为生产者义务，取代 voice 分桶 prose

`sdflow-spec-review` 与 `sdflow-code-review` 编排器 SHALL 在 Step3 裁决后为每个参与镜（`domain`/`adversarial`/`grounding`（spec-review）/`history`（code-review）/`outside-voice`/**`broad`**）落一行 `sdflow:lens-metric v1` 锚（契约见 `workflow-metrics` 能力），其中 code-review 现有的 `voice分桶` 自由 prose 行 SHALL 被 outside-voice 镜的 `lens-metric` 锚**吸收取代**（grep 报告 MUST NOT 再有残留自由文本分桶）。度量锚 SHALL 为旁路记录：其有无 MUST NOT 改变 findings 的采纳与否或评审的推进/拒绝结论。

〔spec-review-amendment SR-L〕`broad` 行的 `findings/采纳/独立` 口径 = 主 session 汇总 `gstack-review.md` **去重后**计入（非各子声原始条数总和）；code-review 的 Step1 `gstack/review` 与 spec-review 的 Step1 autoplan 均折叠为 `layer=<层> lens=broad`。

〔spec-review-amendment SR-M〕**spec-review 度量锚在设计门拍板后最终化**：spec-review 的 `采纳/裁掉/defer` 因中置信项在设计 HARD-GATE 由人翻改，其 `lens-metric` 锚 SHALL 在**拍板回写协议**执行时（与 `<!-- ship-gate: design-approved -->` 同步）最终确定/重算，反映门后最终裁决，MUST NOT 用 Step3 pre-gate 的临时裁决充当最终采纳率（code-review 阶段三无人类门、Step3 即最终，无此步）。

#### Scenario: code-review 落锚并消除 voice 分桶 prose
- **WHEN** 一轮 code-review 完成裁决
- **THEN** 报告 SHALL 为 `domain`/`adversarial`/`history`/`outside-voice`/**`broad`(gstack/review)** 各落一行 `lens-metric` 锚，且 SHALL NOT 再含 `voice分桶: codex 采纳x/裁掉y...` 自由 prose 行〔spec-review-amendment SR-L：显式列 broad〕

#### Scenario: spec-review 落锚
- **WHEN** 一轮 spec-review 完成裁决
- **THEN** 报告 SHALL 为领域镜/对抗镜/接地镜/outside-voice/broad 各落一行 `lens-metric` 锚

#### Scenario: 度量锚为旁路不改判定
- **WHEN** 度量锚落锚失败或字段缺失被自检拦截
- **THEN** 拦截的是**报告完整性**（机械失职），SHALL NOT 反向改写已裁决 findings 的采纳结论——锚是旁路观测，非评审判定输入
