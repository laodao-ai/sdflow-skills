## MODIFIED Requirements

### Requirement: outside-voice exec 的 dispatch 模式宿主自适应

**Requirement ID: HAE-08.** 编排评审 SKILL 调用 outside voice 的 **dispatch 模式 SHALL 按 `$SDFLOW_HOST` 自适应**（读 Step0 已解析值、MUST NOT 重判宿主，ADR-9 同源），使两宿主的跨模型 voice 均可离开同步关键路径并在真实评审负载下跑到终态：

- **`$SDFLOW_HOST=claude` ∧ harness 后台能力自探通过 ∧ 主 session 已确证**：SHALL 继续把 `outside-voice.sh exec` 通过 harness `run_in_background` 派出，dispatch 秒返，Step3 用既有完成通知 barrier collect。
- **`$SDFLOW_HOST=codex` ∧ Claude 2.1.169+ background-exec preflight ready**：SHALL 通过 `outside-voice-background-job` helper 调用本机验证过的 research-preview `claude --bg --exec` 执行形态，由 Claude per-user supervisor 托管现有 `outside-voice.sh exec`；dispatch 秒返，Step3 从 terminal sidecar await/collect。preflight SHALL 同时验证已安装 helper/data capability manifest 与受支持平台；真实 dispatch 是最终能力探针。**[grill-amendment] [spec-review-amendment]**
- 两条 async 路径的内层 timeout **SHALL** 使用 `outside-voice.async-timeout-seconds`（合法范围 1..3600，默认 900）。Claude-host harness 能力不可用时可保留 sync 300 秒降级；Codex-host background-exec 不可用时 **SHALL** 立即同族 fallback，MUST NOT 再走已知 efficacy=0 的同步 Claude 300 秒路径。**[grill-amendment] 该 Codex-host 快速降级是已拍板的兼容边界，不得以“尽力兼容旧版”为由恢复同步分支。**

#### Scenario: Claude 宿主既有 async 行为保持
- **WHEN** `$SDFLOW_HOST=claude` 且 harness background 可用、主 session 已确证
- **THEN** voice 经 `run_in_background` 跑到完成，dispatch 秒级返回，锚行按真实结果落 `reason_code="ok"` 或诚实降级

#### Scenario: Codex 宿主经 Claude supervisor 后台运行
- **WHEN** `$SDFLOW_HOST=codex`、Claude Code ≥2.1.169 且 background-exec preflight ready **[grill-amendment]**
- **THEN** `claude --bg --exec` SHALL 托管 `outside-voice.sh exec --timeout <async-timeout>`，Codex 发起 shell 5 秒内返回，任务跨 shell 生命周期继续运行，终态成功落 `host="codex" runner="claude" reason_code="ok"`

#### Scenario: 两宿主 dispatch 均不长阻塞
- **WHEN** 任一受支持宿主实际派发跨模型 voice
- **THEN** dispatch shell SHALL 在 5 秒内返回并允许主 session 继续 fan-out；总 barrier 可等待 voice 终态，但 MUST NOT 把整个模型运行塞在 dispatch 调用内

#### Scenario: Codex background-exec 不可用时快速降级
- **WHEN** `$SDFLOW_HOST=codex` 但 Claude CLI 版本过旧、agent view 被策略禁用、supervisor 启动失败或 job id 不可解析
- **THEN** SHALL 在 5 秒级走同族 fallback并落 `preflight-error`/`exec-error`，MUST NOT 同步调用 Claude 等待 300 秒，MUST NOT 假装跨模型成功 **[grill-amendment]**

#### Scenario: Claude harness 后台不可用则保留同步兼容降级
- **WHEN** `$SDFLOW_HOST=claude` 但 harness background 自探失败，或无法确证当前为主 session
- **THEN** SHALL 降级回 sync 300 秒、外层 ≥330 秒并显著标注同步降级，MUST NOT 沿用 async 900 秒导致假超时

### Requirement: async dispatch 不改变锚契约与诚实降级

**Requirement ID: HAE-09.** async dispatch SHALL 只改变执行时机与托管方——锚行契约、`reason_code` 枚举、`anchor_lint` 合法组合矩阵、outside-voice 的 FRAME/secret scan/200KB 截断与 Claude 四旗 MUST 保持语义不变。Claude-host collect **SHALL** 继续使用 harness 完成通知；Codex-host collect **SHALL** 使用 background job 的原子 terminal sidecar + 有界 await。两路径均须只按可信终态分支，MUST NOT 假绿。

#### Scenario: 锚契约与矩阵不变
- **WHEN** 本 change 落地后跑 `anchor_lint` 的 host×runner×reason_code×findings 全笛卡尔 golden
- **THEN** 结果 SHALL 与本 change 前逐条一致，跨模型成功仍只允许 `host≠runner ∧ reason_code="ok"` 的合法组合

#### Scenario: 两类 async 路径按各自可信终态 collect
- **WHEN** Claude-host harness 或 Codex-host supervisor job 到达终态
- **THEN** 前者按 harness task 终态、后者按 worker 原子 `.rc` sidecar 分支；成功 stdout 才进 findings，MUST NOT 从自由文本、agent summary 或未完成输出推断状态

#### Scenario: 撞天花板或异常退出诚实降级
- **WHEN** worker 实际 rc=124、rc=1/2/其他非零、terminal job 无 rc、job lookup 失败或 collect 读取失败
- **THEN** 124 SHALL 映射 `timeout`；其他非零/未知/丢失 SHALL 映射 `exec-error`；MUST NOT 静默当 `ok`、MUST NOT 落零锚

#### Scenario: 起了没收不得读作成功
- **WHEN** background voice 已 dispatch 但评审中止、尚未 collect 或 terminal sidecar 不完整
- **THEN** 该站点 SHALL 无 `reason_code="ok"` 锚，MUST NOT 因“起过一次”或 agent summary 看似完成而假绿

#### Scenario: barrier 时 RUNNING 不得早退落 timeout
- **WHEN** Step3 barrier 时某 dispatch 站点仍 RUNNING 且未撞内层 timeout
- **THEN** Claude-host SHALL 等完成通知，Codex-host SHALL 进入有界 await；两者均 MUST NOT 提前落 `timeout`，`reason_code="timeout"` 只允许由实际 rc=124 产生

#### Scenario: 外层等待被回收后可恢复 collect
- **WHEN** Codex-host await shell 被外层回收但 supervisor worker 仍在运行
- **THEN** 同一主评审 session SHALL 按保留的显式 job id/run dir 恢复 collect，MUST NOT 重派；若整个 session 已丢失，新评审只能通过显式 `reconcile --run-dir` 处理 abandoned run，MUST NOT 扫描“最新 run”猜测恢复目标；若 worker/job 已丢失且无 rc且子树已确认退出则诚实判 `exec-error` **[spec-review-amendment]**

#### Scenario: 退出码不可被 runner 伪造
- **WHEN** voice stdout 含退出码样式文本或恶意指令
- **THEN** Claude-host 继续读 runner 不可写的 wrapper sidecar；Codex-host 读 supervisor worker 在 child 结束后原子发布的 rc sidecar。runner 仅有只读工具，不能写这些文件；文件缺失/坏格式 SHALL 判 `exec-error`，MUST NOT 从 stdout 解析退出码

#### Scenario: per-site 完整性机械可审
- **WHEN** 任一宿主同轮 dispatch 2 个站点，其一未 collect、另一正常落锚
- **THEN** `declared-sites` 与实落 outside-voice 锚集合核 SHALL 报错，MUST NOT 因家族级“至少一行”而判 CLEAN

#### Scenario: 复用态不假红
- **WHEN** spec-review 复用已有 `design-voice` 产出而未重新 dispatch
- **THEN** declared 仍按“应有锚”站点集计算并包含 `design-voice`，MUST NOT 改成按 job dispatch 集计算，MUST NOT 解析站点语义不同的 `guard=` 承重

#### Scenario: 错误 stderr 不当 findings
- **WHEN** 任一后台 runner 非零退出并产生未过出境 scan 的 stderr
- **THEN** collect SHALL 只记录结构化退出状态与 stderr 行数/字节数，MUST NOT 把 stderr 原文当 findings 或写入 tracked 报告

#### Scenario: outer supervisor logs 不成为第二出境面 **[spec-review-amendment]**
- **WHEN** background worker 或 inner helper 产生 context、partial stdout、stderr 或 secret canary
- **THEN** 原始内容 SHALL 只写入 0600 run-dir 文件，`claude logs`/supervisor state 只能出现固定结构化状态；negative smoke 失败 SHALL 阻塞 Codex background transport

#### Scenario: helper 安全核心复用且隔离项可加固
- **WHEN** Codex-host background worker 执行 Claude voice
- **THEN** SHALL 调用同一 `outside-voice.sh exec`，FRAME、secret scan、截断与四旗保持同源；Claude runner SHALL 使用单一源解析的 strong 模型（目标仓为 `opus`）与 `--effort high --safe-mode --no-session-persistence`，但 MUST NOT 复制第二份 prompt/safety/model-tier 实现 **[grill-amendment]**
