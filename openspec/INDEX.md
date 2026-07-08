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
| `workflow-metrics` | [specs/workflow-metrics/spec.md](./specs/workflow-metrics/spec.md) | 评审价值度量回路：`lens-metric v1` 结构化锚（layer/lens/runner/site 四元组）+ 只读可重生聚合（`sdflow-retro/scripts/lens_metric_aggregate.py`）+ per-镜数据驱动反馈，砍镜/降采样由人决不自动 |
| `lens-metric-emit` | [specs/lens-metric-emit/spec.md](./specs/lens-metric-emit/spec.md) | `lens_metric_emit.py`：从结构化 findings + 行键 roster 确定性归约出合规 `lens-metric` 锚行（折叠/归属/独立/sev-rollup 机械化，去重/裁决/定级仍归模型）；坏输入 fail-closed all-or-nothing，契约枚举/折叠单一源读取，不 import ship_gate/lens_metric_aggregate |
| `workflow-retro` | [specs/workflow-retro/spec.md](./specs/workflow-retro/spec.md) | `sdflow-retro` 只读再生全项目 change 成本×价值复盘：change 边界靠提交路径检测（非 tag 格式）、时间维仅到阶段级并诚实标注含人决策时间、价值维扫 active+archive 两源合并 spec/code 双报告锚、N≥10 待复评镜机械显著呈现、供数不供裁决 |
| `retro-report` | [retro/report.md](./retro/report.md)（`/sdflow-retro` 再生）| 全 change 成本×价值复盘活文档：git 提交阶段墙钟（成本维）+ lens-metric 锚聚合（价值维）合成 per-change 明细/阶段占比/成本双峰/per-镜价值表；view-only 再生，不做任何取舍决策 |
| `batch-triage` | [specs/batch-triage/spec.md](./specs/batch-triage/spec.md) | issues 池待处理项分诊三分类（相关合批/大扫除批/单开）：大扫除批硬边界（禁装逻辑面）+ issue 级 pre-diff fail-closed 判据（无自动兜底）+ 同类 Leg1 行为面路径守卫 + 聚合上限（MUST 有上限 + 生成物隔离）+ 一项一 commit 执行协议；本仓-local 不进 bundle |
| `determinism-guards` | [specs/determinism-guards/spec.md](./specs/determinism-guards/spec.md) | 机械层确定性守卫三件套：recorder 镜像 helper 剥-docstring-AST 等价一致性测试（3 向 3 个 + 2 向 14 个）、`init.py config-lint`（手写 stdlib、条件化放行、fail-closed）、`issues.py batch lint`（优先级/计划占位符豁免 + 前导 token 后缀不校验）；均只判机械可判的一致性/语法，不越权判内容 |
