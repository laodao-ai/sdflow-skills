# OpenSpec Index

本文件是当前仓库 OpenSpec 资产索引。

<!-- opsx-init:rules:start —— 由 sdflow-init 维护，勿手改本区块 -->
## OpenSpec 工作流规则（sdflow-init 维护）

> 本区块由 `sdflow-init` 维护——`openspec/workflow/` bundle 的规则索引。
> 新增/删 workflow 规则后重跑 `sdflow-init update`，或手动同步本表。

> 无本地规则副本的仓：下表文件位于全局 canonical `~/.sdflow/workflow/`，相对链接不可点，以文件名为准。

| 名称 | 文件 | 作用 |
|---|---|---|
| `workflow` | [workflow/workflow.md](./workflow/workflow.md) | 端到端流程总览（三阶段连续化）：生成(ff+grill)→设计审(sdflow-spec-review 编排器)→设计 GATE→实现+代码审+收尾(subagent-dev→sdflow-code-review→sdflow-done)；去 /clear、连续跑到 merge |
| `trigger-catalog` | [workflow/trigger-catalog.md](./workflow/trigger-catalog.md) | 「按内容条件触发」单一权威源 TG-01~24，驱动 约束/领域清单/画图/必填槽 四层 |
| `ff-generation-constraints` | [workflow/ff-generation-constraints.md](./workflow/ff-generation-constraints.md) | `opsx:ff` 起手强制：FF-0 开分支 + 生成硬约束 D-1~D-6 |
| `generation-process` | [workflow/generation-process.md](./workflow/generation-process.md) | 生成过程三相位：发散(explore)/收敛(brainstorming)/对抗压测(grill) |
| `design-diagrams` | [workflow/design-diagrams.md](./workflow/design-diagrams.md) | 设计/spec 阶段画哪些图、何时画、什么形态（C4 + 行为图，触发条件化） |
| `spec-review` | [workflow/spec-review.md](./workflow/spec-review.md) | spec 评审（Detection 层）：只做 prevention 残差，trigger 驱动 + 独立 + 读码核验 |
| `model-tiers` | [workflow/model-tiers.md](./workflow/model-tiers.md) | 模型档位映射（强/中/弱职责 + canonical 缺省 + config 覆盖语义） |

代码审规则集（`/sdflow-code-review` 用）：[workflow/code-checklists/](./workflow/code-checklists/)（base CR-01~09 + domains）。
说明类（可删不影响执行）：[workflow/reference/](./workflow/reference/)。
<!-- opsx-init:rules:end -->
### spec-workflow

| 名称 | 文件 | 主题 |
|---|---|---|
| `spec-workflow` | [specs/spec-workflow/spec.md](./specs/spec-workflow/spec.md) | spec 工作流三阶段（设计评审/代码评审/收尾归档）连续化的规范性行为：fresh 子代理替代 `/clear`、评审决策登记区、无人类门连续跑到 merge、verify 证据锚点、checkpoint 提交、bundle 权威源改动 |
| `workflow-metrics` | [specs/workflow-metrics/spec.md](./specs/workflow-metrics/spec.md) | 评审价值度量回路：`lens-metric v1` 结构化锚（layer/lens/runner/site 四元组）+ 只读可重生聚合（`lens_metric_aggregate.py`）+ per-镜数据驱动反馈，砍镜/降采样由人决不自动 |
