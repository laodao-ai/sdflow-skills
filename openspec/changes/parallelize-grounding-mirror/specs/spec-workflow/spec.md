## MODIFIED Requirements

### Requirement: 阶段二产出单一合并报告

阶段二 SHALL 由 `sdflow-spec-review` 编排器串起 autoplan 与多镜评审并产出**单一** `spec-review-report.md`，MUST NOT 要求人工手动合并多份报告。**执行序按镜类分治**〔T20 修订〕：

- **领域镜 / 对抗镜** MUST 待 Step1 autoplan 完成并 checkpoint 之后 fan-out——它们的评审对象须包含 autoplan 的 `[gstack-amendment]` 改动（设计约束、scope 修订）。
- **接地镜** MAY 与 Step1 autoplan 并行起跑——它核的是代码事实（函数名/字段/API 路径是否真实存在），不依赖 autoplan 的设计判断产出。
- autoplan amendment 后 SHALL NOT 自动补跑接地镜——amendment 新增的代码事实引用由 `sdflow-code-review` 的 grounding/history 镜兜底覆盖。

#### Scenario: 阶段二收尾
- **WHEN** autoplan 与 spec-review 镜均完成
- **THEN** 编排器输出一份已去重合并、含决策登记区的 spec-review-report.md，供设计 HARD-GATE 人工一次性评审

#### Scenario: 领域/对抗镜等待 autoplan 先行
- **WHEN** sdflow-spec-review 执行 Step2 规划镜头时 Step1 autoplan 尚未 checkpoint
- **THEN** 领域镜与对抗镜 MUST 等待其完成后再 fan-out（评审对象须含 amendment）

#### Scenario: 接地镜与 autoplan 并行
- **WHEN** sdflow-spec-review 启动 Step1 autoplan
- **THEN** 接地镜 MAY 在同一时刻 dispatch，读当前盘面的 design/specs + 真实代码核验代码事实；其 findings 在 Step3 合并池与其它镜同等裁决

#### Scenario: amendment 后不补跑接地镜
- **WHEN** autoplan 产出 `[gstack-amendment]` 且 amendment 涉及新增代码事实引用
- **THEN** 接地镜 SHALL NOT 被要求补跑——该覆盖缺口由 sdflow-code-review 的 grounding 镜在实现完成后兜底
