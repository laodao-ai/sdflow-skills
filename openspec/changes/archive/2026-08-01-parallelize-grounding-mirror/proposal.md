## Why

`sdflow-spec-review` 的 Step2 fan-out 被串行纪律〔T20〕强制等 Step1（autoplan）完成后才能起跑——包括不依赖 autoplan 产出的接地镜。接地镜核的是代码事实（函数名/字段/API 路径是否存在），与 autoplan 的设计判断无关。这段串行等待是纯浪费的墙钟：autoplan 持续数分钟，接地镜在此期间无事可做。

放松串行纪律仅对接地镜——让它与 autoplan 并行起跑——是 roadmap `workflow-cost-optimization` P3（Leg 2 接地镜流水线）的交付。前置条件 P2（档位矩阵）已闭合。

## What Changes

- `sdflow-spec-review/SKILL.md` 的串行纪律条款（`:197`）从「全部镜 MUST 等 Step1 完成」改为「领域/对抗镜 MUST 等 Step1 完成；接地镜可与 Step1 并行起跑」
- Step2 的 fan-out 编排逻辑拆为两段：接地镜在 Step1 启动时即 dispatch，领域/对抗镜在 Step1 checkpoint 后 dispatch
- Step3 合并逻辑不变——接地镜 findings 与其它镜 findings 同池合并裁决
- 不补跑：autoplan amendment 后不重跑接地镜（decision-memo D1），由 code-review 接地镜兜底

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-workflow`: 设计评审的接地镜串行纪律放松为与 autoplan 并行

## Impact

- **代码**：仅 `sdflow-spec-review/SKILL.md` 一个文件的 prose 条款
- **收益**：设计评审墙钟降低 ≈ autoplan 持续时间（接地镜从串行等待变为并行）
- **代价**：autoplan amendment 新增代码事实引用时，接地镜对该部分漏覆盖——由 `sdflow-code-review` 的 grounding/history 镜兜底（已有机制，不新增）
- **不改**：`sdflow-code-review`（无等价串行约束）、anchor 体系、lens-metric 体系
