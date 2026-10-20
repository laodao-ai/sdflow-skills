# 子代理派发契约

适用于 `sdflow-spec-review`、`sdflow-code-review`、`sdflow-implement`、`sdflow-done` 与
`sdflow-roadmap`、`sdflow-adr`、`sdflow-architecture` 与 `sdflow-devenv` 已经决定派发子代理之后的调度和结果收集。本文件不决定未被某个 skill、全局规则或
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

## Codex 结果收集

适用于 Codex 宿主。Claude 宿主等完成通知，不适用本节。各入口可在自身收集段声明其他时长上限。

1. **同回合收齐**：派发一批后，在同一回合内循环调 `wait_agent`（`timeout_ms` 取 60000–300000）；
   返回后用 `list_agents` 刷新各任务状态；进入终态的任务按宿主实际提供的方式取结果正文
   （`list_agents`、邮箱通知或 `result_ref`）。本契约不锁定 `wait_agent` 返回值的字段名。
   MUST NOT 结束回合去等通知。
2. **单子代理计时**：每个子代理从派出起单独计时，循环持续到本批全部终态，或某个子代理超过时长上限。
   缺省上限 30 分钟；`sdflow-implement` 声明 60 分钟（implementer 要跑测试）。派出时跑一次
   `date -u +%s` 记该任务起点，每次 `wait_agent` 返回后再取一次，差值即该任务已用时长。
3. **超限处置**：工具集有 `interrupt_agent` 就调用，再用 `list_agents` 确认它已停下，确认后记
   `interrupted`；没有该工具或确认不了，记 `interrupted` 并在报告标注「未确认停止，可能仍在写入」。
   `interrupt_agent` 只停当前回合，不关闭子代理、不保证释放名额。报告列出任务名与续跑方式（新回合继续
   `wait_agent`，或新开会话重跑该入口），并按入口既有失败路径处理。有写副作用的任务在确认停下之前，
   MUST NOT 重派、MUST NOT 撤销其改动。
4. **名额**：在途数不超过 `N - 1 - A`（同「容量分批」）；本批跑完后名额回收，再派下一批。
   不给已进入终态的子代理发 `send_message` / `followup_task`：给已完成的子代理留下未取走的消息，
   会让它一直占着名额。工具集有 `close_agent` 时逐个关闭已收集的子代理，没有则不尝试。
5. **`thread limit reached`**：
   - 本批仍有子代理在跑：等它们进入终态后重试一次。
   - 本批已全部终态仍报满：名额没被回收，不再重试，直接报告「需新开会话」，列出已完成与未派出的任务，
     停在该入口既有阻塞路径。

## Codex 派发的 task_name

Codex 宿主派发子代理时，`spawn_agent` 的 `task_name` 即该派发项的角色 id：格式
`<skill>_<role>[_<n>]`，字符集仅 `[a-z0-9_]`，同批派发内唯一（如 `spec_review_strategy`、
`spec_review_adversarial_1`、`implement_task3`）。宿主把它落为子线程元数据
`agent_path=/root/<task_name>`，token 快照的 `role` 字段原样记录该值；不符合约定的值照原样记录，
不映射、不猜测角色。

## Codex effort 回退与门禁

Codex 派发使用本轮 resolver 的 model、`reasoning_effort` 与 `fork_turns: "none"`。Claude 派发同样 MUST 传本轮 resolver 的 model，并以 `subagent_type: sdflow-effort-<档位>` 选 effort（effort agent 定义为 `model: inherit`，漏传 model 即继承主 session 模型）；本契约不把主 session 的模型切换交给 resolver，也不以子代理的 strong
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

## 通则承载与前缀文件

适用于全部子代理派发。outside-voice 不走本节：它的通则由 `outside-voice.sh` 的 FRAME 机械注入。

每个子代理 MUST 拿到四条通则全文。派发 prompt MUST NOT 内联通则原文，也 MUST NOT 内联前缀正文。承载方二选一。

### 承载判定

对本次派发所带的 `subagent_type`（只有 `host=claude` 会带）逐个判定：`~/.claude/agents/<subagent_type>.md`
是软链，且 `readlink` 指向 `sdflow-spec/agents/` 下的同名文件。

```bash
case "$(readlink "$HOME/.claude/agents/<subagent_type>.md")" in
  */sdflow-spec/agents/<subagent_type>.md) echo carried ;;
  *) echo not-carried ;;
esac
```

- `carried`：通则由 agent 定义承载（定义正文由 `sync_principles.py` 注入）。
- 其余一律 `not-carried`：未跑 setup、Windows、同名文件属于别的插件、Codex 宿主（不带 `subagent_type`）、
  effort 为空。
- 入口在第零步解析档位之后、首次派发之前判完，结果写进任务记录。MUST NOT 在派发失败后补判。

### 变体选用

| 任务 | `carried` | `not-carried` |
|---|---|---|
| 评审镜（spec-review、code-review 的领域、对抗、接地、历史镜） | 读 `prefix-<layer>-np.md` | 读 `prefix-<layer>.md` |
| 其余子代理（广审镜、scope 审计、implementer、两轴审、fix、verify、archive、adr、architecture、devenv、roadmap） | prompt 不带通则、不读文件、无回执 | 读 `prefix-principles.md` |

`sdflow-spec` 的三个角色定义只经 agent 定义派发，没有 `not-carried` 分支：定义不可用时由主 session 亲做
（SA-07），MUST NOT 改派通用子代理去读文件。

### run 目录

每个入口在第零步、首次派发之前创建本轮 run 目录。父目录：

| 入口 | 父目录 |
|---|---|
| spec-review、code-review、implement | `{change_dir}/.outside-voice/` |
| done | `openspec/.outside-voice/`（archive 会搬走 change 目录，放在外面才不失效） |
| roadmap | `openspec/roadmaps/<name>/.outside-voice/` |
| adr audit、adr 独立 sync | `openspec/adr/.outside-voice/`（被 done 调用的 sync 复用 done 的 run 目录） |
| architecture、devenv | `openspec/architecture/.outside-voice/` |

创建方式：

```bash
mkdir -p "<父目录>" && RUN_DIR="$(mktemp -d "<父目录>/$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")" && basename "$RUN_DIR"
```

同一次调用内用 `basename` 取回字面 run-id，后续一律代入字面值，不靠 shell 变量跨调用存活。
评审入口的 outside-voice 协议复用同一个 run 目录，不再另建。

写入 run 目录前跑 `git check-ignore -q "<父目录>/<run-id>"`。不被忽略 → fail-loud，不写文件、不派发：
problem=run 目录未被 git 忽略；cause=该仓 `.gitignore` 缺 `**/.outside-voice/`；
fix=在本仓跑 `sdflow-init update`。

### 前缀文件

```bash
~/.sdflow/hack/render-review-prefix.sh --layer principles --out-dir "<run 目录字面路径>"
```

stdout 是一行 JSON `{"path": …, "version": …, "bytes": …}`。用 `python3 -c` 解析取 `path`、`version`，
不手拼、不手抠。评审入口另渲染 `--layer <layer>` 与 `--layer <layer> --no-principles` 两个变体，共三个文件。
每个变体每轮只写一次，写后不改。

渲染器非零退出 → fail-loud 并转发 stderr 的 problem/cause/fix，不派发。未知参数 exit 64 表示渲染器旧于
SKILL，fix 是回运行 checkout 跑 `bash setup.sh`。

### 读文件指令与回执

`not-carried` 的派发，prompt 里的读文件指令固定为一句：

> 先完整读取 `<path>`；把该文件第一行原样作为你结果的第一行。

`<path>` 代入绝对路径。prompt MUST NOT 写出期望的 `prefix-version` 值：期望值只由主 session 持有，
子代理不读文件就拿不到正确首行。

子代理返回后，主 session 把结果首行与本轮文件首行（`<!-- prefix-version: <version> -->`）逐字比对，
比对通过后先剥掉回执行，再交给合并、解析或状态判断。

比对缺失或不符 → 记 `result-invalid-or-unattributed`：

- 只读任务（评审镜、scope 审计、两轴审、verify、adr audit、architecture 走查、devenv 冷审、roadmap 广审镜）：
  同一任务重派一次；再不符进入该入口既有失败路径。
- 有写副作用的任务（implementer、fix、archive、adr sync）：不重派，进入该入口既有失败或 BLOCKED 路径，
  报告标注「回执不符，产出未采信」。

回执只证明子代理读到了文件首行，不证明读完全文。

### 任务记录字段

任务记录在「每轮任务记录」所列字段之外增加 `prefix_path`、`prefix_version`。`carried` 分支两者为空。
上下文压缩后靠这两个字段继续比对。

## 运行诊断与恢复

所有入口将以下诊断写入本轮报告或既有状态产物。每条均保留原始错误；不得把非 effort、非容量错误改写为
另一类。

| 诊断 | problem | cause | fix | 可执行恢复动作 |
|---|---|---|---|---|
| `capacity-rejected` | 派发被容量拒绝。 | 宿主明确报告容量不足。 | 按容量规则刷新并有界重试。 | 刷新任务状态；有活动任务则等待终态，无活动任务只重试一次。 |
| `capacity-unknown` | 不能可靠计算可派发数。 | 总上限或活动状态不可得。 | 串行执行完整清单。 | 每批只派一个尚未处理的任务。 |
| `terminal-not-completed` | 子任务未形成可接受终态。 | 状态为 `failed`、`interrupted` 或 `cancelled`。 | 进入该入口既有失败路径。 | 保留状态与原错误，停止或按入口规则降级。 |
| `result-invalid-or-unattributed` | `completed` 但结果不能判成功。 | `result_ref` 缺失、结构无效或不属于本轮，或读文件分支的回执首行缺失、不符。 | 拒绝成功锚。 | 记录 `run_id/task_id` 核验失败，进入入口既有失败或降级路径。 |
| `effort-fallback` | 请求 effort 明确不受支持。 | 宿主拒绝 effort 参数或 model×effort 组合。 | 依次尝试 canonical 默认和省略 effort。 | 记录四个 effort 字段；保留同一任务、model 与 prompt。 |
| `dispatch-other-error` | 派发因非容量、非 effort 原因失败。 | 权限、网络、未知模型、坏 prompt 或其他原始错误。 | 不做错误分类转换。 | 保留原始错误并进入该入口既有失败路径。 |

## 发布与回退

开发树修改不会自动更新全局运行资产。只有完整新版本发布或该树已成为全局运行 checkout 后，才运行
`setup.sh` 刷新 canonical workflow、hack 与 skill；随后在消费仓运行 `sdflow-init update`。`init.py update`
自身不安装全局 helper，MUST NOT 在半代源码上执行全局安装。

回退以本 change 的提交为单位。canonical 与五个 skill 必须同批回退；只回退一侧会留下配置可写但无人
消费，或入口引用不存在的契约。真实全局安装窗口结束后，从目标运行 checkout 重跑 `setup.sh` 恢复同代快照。
