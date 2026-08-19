## OpenSpec 工作流规则（sdflow-init 维护）

> 本区块由 `sdflow-init` 维护——`openspec/workflow/` bundle 的规则索引。
> 新增/删 workflow 规则后重跑 `sdflow-init update`，或手动同步本表。

> 无本地规则副本的仓：下表文件位于全局 canonical `~/.sdflow/workflow/`，相对链接不可点，以文件名为准。

| 名称 | 文件 | 作用 |
|---|---|---|
| `workflow` | [workflow/workflow.md](./workflow/workflow.md) | 端到端流程总览（三阶段连续化）：/sdflow-spec 生成→设计审(sdflow-spec-review 编排器)→设计 GATE→实现(sdflow-implement)+代码审(sdflow-code-review)+收尾(sdflow-done)；阶段内部不用 /clear，仅两处阶段交界用（G1），连续跑到 merge |
| `trigger-catalog` | [workflow/trigger-catalog.md](./workflow/trigger-catalog.md) | 「按内容条件触发」单一权威源 TG-NN，驱动 约束/领域清单/画图/必填槽 四层 |
| `ff-generation-constraints` | [workflow/ff-generation-constraints.md](./workflow/ff-generation-constraints.md) | 生成起手强制：FF-0 开分支 + 生成硬约束 D-1~D-6（`/sdflow-spec` 调用，或 `opsx:ff` 直呼） |
| `generation-process` | [workflow/generation-process.md](./workflow/generation-process.md) | 生成过程：发散(explore) + `/sdflow-spec`（澄清→拷问→生成三相位） |
| `design-diagrams` | [workflow/design-diagrams.md](./workflow/design-diagrams.md) | 设计/spec 阶段画哪些图、何时画、什么形态（C4 + 行为图，触发条件化） |
| `spec-review` | [workflow/spec-review.md](./workflow/spec-review.md) | spec 评审（Detection 层）：只做 prevention 残差，trigger 驱动 + 独立 + 读码核验 |
| `model-tiers` | [workflow/model-tiers.md](./workflow/model-tiers.md) | 模型档位映射（强/中/弱职责 + canonical 缺省 + config 覆盖语义） |

设计审规则集（`/sdflow-spec-review` 用）：[workflow/spec-checklists/](./workflow/spec-checklists/)（base BASE-NN + domains，含 devex、frontend(+frontend-react)）。
代码审规则集（`/sdflow-code-review` 用）：[workflow/code-checklists/](./workflow/code-checklists/)（base CR-NN + domains，含 frontend(+frontend-react)）。
多为说明类（可删不影响执行），另含 change 拆分标准单一源（`change-decomposition-standard.md`，被
三处 SKILL 引为执行必需的规范文本，详见目录内 README）：[workflow/reference/](./workflow/reference/)。
人读概念指南（原理 / 设计思想 / 实战用法）：`~/.sdflow/workflow/sdflow-guide.html`（自包含 HTML，浏览器直接打开；随 bundle 全局分发，不入消费仓）。
