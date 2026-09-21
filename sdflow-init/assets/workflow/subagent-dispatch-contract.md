# 子代理派发契约

适用于 `sdflow-spec-review`、`sdflow-code-review`、`sdflow-implement`、`sdflow-done` 与
`sdflow-roadmap` 已经决定派发子代理之后的调度和结果收集。本文件不决定未被某个 skill、全局规则或
用户指令要求的场景是否派发；各入口仍定义自己的任务角色、完整派发任务清单和失败策略。

## 每轮任务记录

派发前固定本轮完整派发任务清单。每项至少记录 `run_id`、`task_id`、角色、`requested_model`、
`requested_effort`、上下文模式、预期 `result_ref` 和生命周期状态。容量只能改变批次与墙钟时间，
MUST NOT 删除任务、减少镜数，或让主 session 的结果冒充独立子代理结果。

生命周期只有 `pending`、`running`、`completed`、`failed`、`interrupted`、`cancelled` 六态。
`completed` 只是生命周期终态，不是业务成功：成功还要求 `result_ref` 存在、结构满足该 skill 的要求，
并且可由 `run_id/task_id` 或当前工具调用直接归属于本轮。旧轮结果、空结果、无效结构和无法归属的结果都
必须进入该入口的失败或降级路径，不得落成功锚。

## 容量分批

宿主报告会话总并发上限 `N` 时，它包含主 session。若当前有 `A` 个未终态子任务，新一批最多派发
`max(0, N - 1 - A)` 项。每批结束后刷新生命周期状态，再处理清单中尚未派发的项目。

容量或活动状态未知时，按串行方式每批派一项，直到完整派发任务清单处理完毕。MUST NOT 猜固定容量，
也不得把某次宿主或版本的上限写成跨宿主常量。

仅明确的容量拒绝可触发容量恢复：刷新状态；若仍有未终态任务，等待至少一项进入终态后重试；若没有
活动任务，只再重试一次。仍失败则进入入口既有阻塞、降级或硬停路径。权限、网络、未知模型、坏 prompt
及其他非容量错误保留原错误，MUST NOT 伪装成容量不足或进入容量重试。

## Codex 派发的 task_name

Codex 宿主派发子代理时，`spawn_agent` 的 `task_name` 即该派发项的角色 id：格式
`<skill>_<role>[_<n>]`，字符集仅 `[a-z0-9_]`，同批派发内唯一（如 `spec_review_strategy`、
`spec_review_adversarial_1`、`implement_task3`）。宿主把它落为子线程元数据
`agent_path=/root/<task_name>`，token 快照的 `role` 字段原样记录该值；不符合约定的值照原样记录，
不映射、不猜测角色。

## Codex effort 回退与门禁

Codex 派发使用本轮 resolver 的 model、`reasoning_effort` 与 `fork_turns: "none"`。Claude 使用其
既有 `subagent_type` 语义；本契约不把主 session 的模型切换交给 resolver，也不以子代理的 strong
档位冒充主 session 已满足门禁。

仅明确的 effort 参数或 model×effort 组合不支持，才可回退：先以同一 model、任务和 prompt 尝试该档
canonical 默认；请求值已经是默认值时跳过重复调用；默认值仍被明确拒绝时省略 `reasoning_effort` 继续。
不得猜相邻 effort，不得改变 model、任务、prompt 或完整派发任务清单。其他错误不得走 effort 回退。

每次调用分别记录下列互不混写的字段：

| 字段 | 含义 |
|---|---|
| `requested_effort` | 配置意图。 |
| `accepted_request_evidence` | 本轮成功调用的参数和接口接受证据。 |
| `effective_effort` | 可信宿主实际元数据；没有时为 `unknown`。 |
| `fallback_reason` | 明确的 effort 不支持原因，或未回退。 |

成功返回只证明请求被接受，不能证明实际 effort。门禁子任务只有在 high+ 请求有本轮
`accepted_request_evidence`、任务 `completed`、结果有效且归属本轮、并完成最终主审核验时才能放行。
此时 `effective_effort=unknown` 可以放行，但必须显著披露实际值未获证明。省略 effort 后完成的任务继续
执行，但最初被拒的 high 请求不得作为放行证据。可信元数据已知实际低于 high 时不得放行。

## 运行诊断与恢复

所有入口将以下诊断写入本轮报告或既有状态产物。每条均保留原始错误；不得把非 effort、非容量错误改写为
另一类。

| 诊断 | problem | cause | fix | 可执行恢复动作 |
|---|---|---|---|---|
| `capacity-rejected` | 派发被容量拒绝。 | 宿主明确报告容量不足。 | 按容量规则刷新并有界重试。 | 刷新任务状态；有活动任务则等待终态，无活动任务只重试一次。 |
| `capacity-unknown` | 不能可靠计算可派发数。 | 总上限或活动状态不可得。 | 串行执行完整清单。 | 每批只派一个尚未处理的任务。 |
| `terminal-not-completed` | 子任务未形成可接受终态。 | 状态为 `failed`、`interrupted` 或 `cancelled`。 | 进入该入口既有失败路径。 | 保留状态与原错误，停止或按入口规则降级。 |
| `result-invalid-or-unattributed` | `completed` 但结果不能判成功。 | `result_ref` 缺失、结构无效或不属于本轮。 | 拒绝成功锚。 | 记录 `run_id/task_id` 核验失败，进入入口既有失败或降级路径。 |
| `effort-fallback` | 请求 effort 明确不受支持。 | 宿主拒绝 effort 参数或 model×effort 组合。 | 依次尝试 canonical 默认和省略 effort。 | 记录四个 effort 字段；保留同一任务、model 与 prompt。 |
| `dispatch-other-error` | 派发因非容量、非 effort 原因失败。 | 权限、网络、未知模型、坏 prompt 或其他原始错误。 | 不做错误分类转换。 | 保留原始错误并进入该入口既有失败路径。 |

## 发布与回退

开发树修改不会自动更新全局运行资产。只有完整新版本发布或该树已成为全局运行 checkout 后，才运行
`setup.sh` 刷新 canonical workflow、hack 与 skill；随后在消费仓运行 `sdflow-init update`。`init.py update`
自身不安装全局 helper，MUST NOT 在半代源码上执行全局安装。

回退以本 change 的提交为单位。canonical 与五个 skill 必须同批回退；只回退一侧会留下配置可写但无人
消费，或入口引用不存在的契约。真实全局安装窗口结束后，从目标运行 checkout 重跑 `setup.sh` 恢复同代快照。
