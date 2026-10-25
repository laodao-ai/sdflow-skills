# 子代理派发契约

适用于 `sdflow-spec-review`、`sdflow-code-review`、`sdflow-implement`、`sdflow-done` 与
`sdflow-roadmap`、`sdflow-adr`、`sdflow-architecture` 与 `sdflow-devenv`
已经决定派发子代理之后的调度和结果收集。本文件不决定未被某个 skill、全局规则或
用户指令要求的场景是否派发；各入口仍定义自己的任务角色、完整派发任务清单和失败策略。

## 每轮任务记录

派发前固定本轮完整派发任务清单。每项至少记录 `run_id`、`task_id`、角色、`requested_model`、
`requested_effort`、上下文模式、预期 `result_ref`、生命周期状态、截止时刻（派出时刻 + 该角色的时长上限，
见「子代理时长上限」节）和闹钟任务 ID（Claude 宿主，见「Claude 结果收集」节；Codex 宿主留空）。
容量只能改变批次与墙钟时间，
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

## 子代理时长上限

两宿主共用一张按角色定的时长上限表。子代理从派出起运行到上限仍未终态，即停止并记 `interrupted`。
本表是上限数值的唯一原文，「Claude 结果收集」「Codex 结果收集」两节与八个派发入口都引用这里。

| 角色 | 上限 |
|---|---|
| 评审镜、轴审、verify、adr sync/audit、architecture 走查、devenv 冷审、roadmap 广审镜、scope 审计、archive、outside-voice 同族 fallback 子代理 | 60 分钟 |
| implementer、fix | 180 分钟 |

- 入口 MAY 在自身收集段声明更长的上限。
- 超限判定只依据主 session 自己的计时（派出时刻与当前时刻的差），MUST NOT 依据子代理输出的内容、
  文件状态或模型的判断。
- 上限只用于控制，不产出任何 per-agent 时长度量。

## Claude 结果收集

适用于 Claude 宿主派发后台 Agent 子代理。子代理完成时 harness 推送通知唤醒主 session；本节在此之上
加一个闹钟，保证卡死的子代理不会让主 session 永远等下去。

1. **记截止时刻**：派发时在「每轮任务记录」里给每个任务记角色与截止时刻（派出时刻 + 该角色上限）。
   上下文压缩后靠这些字段继续。
2. **每入口一个闹钟**：以 `run_in_background` 起 `date +%s; sleep <秒>; date +%s`，
   秒数 = 在途任务中最早的截止时刻 − 当前时刻，差值不足 60 时取 60（防止已过截止的任务让秒数为负、闹钟立即异常退出并无限重起）；闹钟任务 ID 记进同一条记录。
   中途补派任务（容量分批、frontier 滚动、重派）使最早截止时刻提前时，`TaskStop` 旧闹钟，按新时刻重起。
   任何时候起新闹钟前都先 `TaskStop` 旧闹钟并更新记录里的闹钟任务 ID；任务 ID 与记录不符的闹钟通知
   一律忽略，保证每个入口只有一个有效闹钟。
3. **等通知**：结束回合，等通知。
4. **完成通知照常收集**：在途任务全部终态时，`TaskStop` 停掉闹钟，忽略停闹钟产生的通知。
5. **闹钟到点**：
   - 先处理已到达的完成通知，以完成为准。
   - 闹钟通知不是正常结束（被回收、被停、输出缺少结束时间戳，或实际耗时明显短于设定秒数）且不是本节
     主动停的：视为闹钟异常，不停止任何任务，按最早截止时刻重起闹钟，报告标注「闹钟异常重起」。
   - 闹钟输出的实际耗时比设定秒数多 120 秒以上：视为系统休眠，所有在途任务的截止时刻顺延
     （实际耗时 − 设定秒数），按新的最早截止时刻重起闹钟，不停止任何任务。
   - 其余已过截止时刻的未终态任务：`TaskStop`，记 `interrupted`，报告写「超过时长上限 N 分钟」与续跑方式，
     按入口既有失败路径处理。`TaskStop` 返回失败且原因不是「任务已结束」时，同样记 `interrupted`，
     并标注「未确认停止，可能仍在写入」。
     `TaskStop` 返回「任务已结束」时，该任务不再计入在途、不记 `interrupted`，等它的完成通知按第 7 条处理；
     重起闹钟只看其余在途任务。
   - 仍有在途任务时，按最早截止时刻重起闹钟，回到第 3 条。
6. **写入任务**：有写副作用的任务（implementer、fix、archive、adr sync）被停后，MUST NOT 重派、
   MUST NOT 撤销其改动，沿用 HAE-18 的写入任务规则。
7. **晚到的通知**：停止后才到达的完成通知，为成功且带结果正文时，以完成为准改记成功；否则保持 `interrupted`。
8. **记账丢失**：上下文压缩后记录也丢失时，从当次闹钟起按上限表中最长的一档重新计时，并在报告标注「记账丢失」。
9. **适用范围**：本节只管 Agent 子代理。outside-voice 的后台 Bash 有 helper 内层超时，不起闹钟。

### 权限确认被拒时

Claude 宿主下 sdflow 子代理的权限确认可能被全局 hook 直接拒绝。被拒时按拒绝消息处理，改写不了就跳过该步。报告里写明跳过了什么、为什么，并把该步标为未完成。

## Codex 结果收集

适用于 Codex 宿主。Claude 宿主的收集见「Claude 结果收集」节。时长上限见「子代理时长上限」节，
各入口可在自身收集段声明更长的值。

1. **同回合收齐**：派发一批后，在同一回合内循环调 `wait_agent`（`timeout_ms` 取 60000–300000）；
   `timeout_ms` 同时不得超过在途任务中最早到期者的剩余时间（上限 − 已用时长，换成毫秒），
   剩余不足 60000 时取剩余值，但不低于宿主下限 10000。剩余为零或负数时不再等待，直接按第 3 条处置。
   返回后用 `list_agents` 刷新各任务状态；进入终态的任务按宿主实际提供的方式取结果正文
   （`list_agents`、邮箱通知或 `result_ref`）。本契约不锁定 `wait_agent` 返回值的字段名。
   MUST NOT 结束回合去等通知。
2. **单子代理计时**：每个子代理从派出起单独计时，循环持续到本批全部终态，或某个子代理超过时长上限。
   上限按「子代理时长上限」节的角色表。派出时跑一次
   `date -u +%s` 记该任务起点，每次 `wait_agent` 返回后再取一次，差值即该任务已用时长。
3. **超限处置**：工具集有 `interrupt_agent` 就调用，再用 `list_agents` 确认它已停下，确认后记
   `interrupted`；没有该工具或确认不了，记 `interrupted` 并在报告标注「未确认停止，可能仍在写入」。
   `interrupt_agent` 只停当前回合，不关闭子代理、不保证释放名额。报告列出任务名与续跑方式（新回合继续
   `wait_agent`，或新开会话重跑该入口），并按入口既有失败路径处理。有写副作用的任务在确认停下之前，
   MUST NOT 重派、MUST NOT 撤销其改动。
   - **同批其余在途任务一并中断**：先 `list_agents` 收一次已进终态的结果，再对本批仍未终态的任务逐个按本条
     中断并记 `interrupted`，报告标注「同批任务 X 超限，连带中断」。不继续等待它们：入口既有失败路径
     对任何非 `completed` 都要停下或阻塞，继续等只会让失败处置与在途写入交错。
   - **迟到结果不采信**：已记 `interrupted` 的任务，之后才出现的 `completed` 结果不采信、不改记成功，
     只在报告标注「迟到完成，未采信」。Claude 宿主第 7 条允许改记成功，Codex 不允许：
     此时失败处置已经开始。
4. **名额**：在途数不超过 `N - 1 - A`（同「容量分批」）；本批跑完后名额回收，再派下一批。
   A 包含已记 `interrupted` 但未确认关闭的子代理：中断不释放名额，这些子代理仍占着 A。
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

仅明确的 effort 参数或 model×effort 组合不支持，才可回退：先以同一 model、任务、prompt 和 runner 尝试该档
canonical 默认；请求值已经是默认值时跳过重复调用；默认值仍被明确拒绝时省略 `reasoning_effort` 继续。
不得猜相邻 effort，不得改变 model、任务、prompt、runner 或完整派发任务清单。其他错误不得走 effort 回退。

每次调用分别记录下列互不混写的字段：

| 字段 | 含义 |
|---|---|
| `requested_effort` | 配置意图。 |
| `accepted_request_evidence` | 本轮成功调用的参数和接口接受证据。 |
| `effective_effort` | 可信宿主实际元数据；没有时为 `unknown`。 |
| `fallback_reason` | 明确的 effort 不支持原因，或未回退。 |

成功返回只证明请求被接受，不能证明实际 effort。门禁子任务只有在 high+ 请求有本轮
`accepted_request_evidence`、任务 `completed`、结果有效且归属本轮、并完成最终主审核验时才能放行。
此时 `effective_effort=unknown` 可以放行，但必须显著披露实际值未获证明。省略 effort 后记录 `effective_effort=unknown`，不得写成已证明的 high；完成的任务继续
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
| `effort-fallback` | 请求 effort 明确不受支持。 | 宿主拒绝 effort 参数或 model×effort 组合。 | 依次尝试 canonical 默认和省略 effort。 | 记录四个 effort 字段；保留同一任务、model、prompt 与 runner。 |
| `dispatch-other-error` | 派发因非容量、非 effort 原因失败。 | 权限、网络、未知模型、坏 prompt 或其他原始错误。 | 不做错误分类转换。 | 保留原始错误并进入该入口既有失败路径。 |

## 发布与回退

开发树修改不会自动更新全局运行资产。只有完整新版本发布或该树已成为全局运行 checkout 后，才运行
`setup.sh` 刷新 canonical workflow、hack 与 skill；随后在消费仓运行 `sdflow-init update`。`init.py update`
自身不安装全局 helper，MUST NOT 在半代源码上执行全局安装。

回退以本 change 的提交为单位。canonical 与五个 skill 必须同批回退；只回退一侧会留下配置可写但无人
消费，或入口引用不存在的契约。真实全局安装窗口结束后，从目标运行 checkout 重跑 `setup.sh` 恢复同代快照。
