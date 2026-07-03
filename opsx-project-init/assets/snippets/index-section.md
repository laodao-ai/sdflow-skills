## OpenSpec 工作流规则（opsx-project-init 维护）

> 本区块由 `opsx-project-init` 维护——`openspec/workflow/` bundle 的规则索引。
> 新增/删 workflow 规则后重跑 `opsx-project-init update`，或手动同步本表。

| 名称 | 文件 | 作用 |
|---|---|---|
| `workflow` | [workflow/workflow.md](./workflow/workflow.md) | 端到端流程总览（三阶段连续化）：生成(ff+grill)→设计审(spec-review 编排器)→设计 GATE→实现+代码审+收尾(subagent-dev→impl-review→opsx-done)；去 /clear、连续跑到 merge |
| `trigger-catalog` | [workflow/trigger-catalog.md](./workflow/trigger-catalog.md) | 「按内容条件触发」单一权威源 TG-01~24，驱动 约束/领域清单/画图/必填槽 四层 |
| `ff-generation-constraints` | [workflow/ff-generation-constraints.md](./workflow/ff-generation-constraints.md) | `opsx:ff` 起手强制：FF-0 开分支 + 生成硬约束 D-1~D-6 |
| `generation-process` | [workflow/generation-process.md](./workflow/generation-process.md) | 生成过程三相位：发散(explore)/收敛(brainstorming)/对抗压测(grill) |
| `design-diagrams` | [workflow/design-diagrams.md](./workflow/design-diagrams.md) | 设计/spec 阶段画哪些图、何时画、什么形态（C4 + 行为图，触发条件化） |
| `spec-review` | [workflow/spec-review.md](./workflow/spec-review.md) | spec 评审（Detection 层）：只做 prevention 残差，trigger 驱动 + 独立 + 读码核验 |

代码审规则集（`/impl-review` 用）：[workflow/code-checklists/](./workflow/code-checklists/)（base CR-01~09 + domains）。
说明类（可删不影响执行）：[workflow/reference/](./workflow/reference/)。
