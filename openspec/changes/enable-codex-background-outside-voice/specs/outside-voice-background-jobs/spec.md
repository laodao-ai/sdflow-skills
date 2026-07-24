## ADDED Requirements

### Requirement: Codex-host Claude voice 由官方 supervisor 托管

**Requirement ID: OVBG-01.** Codex 宿主的 Claude outside voice **SHALL** 通过 Claude Code `2.1.169+` 的 `claude --bg --exec '<command>'` 派发，由 per-user supervisor 托管现有 `outside-voice.sh exec` 命令；dispatch **MUST** 在 5 秒内返回可审计的短 job id，**MUST NOT** 把 review prompt 直接交给交互式 `claude --bg '<prompt>'`，亦 **MUST NOT** 依赖 `nohup`、`setsid` 或 Codex shell 子进程在命令返回后存活。**[grill-amendment] 2.1.169 是 `--bg --exec`、`--safe-mode` 与含 `--all`/`id`/`state` agents JSON 的共同能力下限。**

后台命令 **SHALL** 调用同一份已安装 `~/.sdflow/hack/outside-voice.sh exec`，使 prompt rendering、入境/出境 secret scan、context 截断、最终 stdout 与退出码继续由既有权威实现产生。

#### Scenario: dispatch 返回后 worker 继续运行
- **WHEN** Codex 宿主 dispatch 一个运行时间超过发起 shell 调用的 Claude voice job
- **THEN** dispatch 在 5 秒内返回 job id，发起 shell 已结束时 worker 仍由 Claude supervisor 托管，最终写出终态 sidecar

#### Scenario: 无副作用 preflight 通过后由真实 dispatch 最终核验 **[grill-amendment]**
- **WHEN** `claude --version` 为 `2.1.169` 或更高，且 `claude agents --all --json` 调用成功、顶层为可解析 JSON list
- **THEN** background-job preflight SHALL 返回 ready 且不得创建 dummy job；随后真实 worker dispatch SHALL 作为最终能力探针，负责取得并核验唯一 job id

#### Scenario: 旧版或被策略禁用时立即诚实降级
- **WHEN** Claude Code 低于 `2.1.169`、agents JSON 不可调用、`disableAgentView` 禁用 supervisor、或真实 dispatch 输出无法取得唯一 job id **[grill-amendment]**
- **THEN** 调用 SHALL 在 5 秒级失败为 `preflight-error`/`exec-error` 并走同族 fallback，MUST NOT 再同步等待 300 秒，MUST NOT 伪造后台成功 **[grill-amendment]**

### Requirement: job 关联与状态从不可变终态证据派生

**Requirement ID: OVBG-02.** 每个实际 dispatch 站点 **SHALL** 在本轮唯一 `.outside-voice/<run-id>/` 下产生独立的 `<site>.job.json`、`<site>.stdout`、`<site>.stderr` 与 `<site>.rc`。`job.json` **MUST** 至少记录 schema version、run id、site、repo root、Claude short id、session id（若 `claude agents --json` 可得）、dispatch UTC、deadline UTC、timeout 秒数和命令摘要；写入 **MUST** 使用临时文件 + atomic rename。

**[grill-amendment]** 运行状态 **SHALL** 从盘面派生而非另存可变 `status` 字段：`.rc` 不存在且 agent working = RUNNING；`.rc=0` 且 stdout 非空 = SUCCEEDED；`.rc=124` = TIMED_OUT；其他退出码或 terminal agent 无 `.rc` = FAILED/LOST。`claude agents` 的 `done/failed` 与 `claude logs` **MUST NOT** 决定 `ok`/`timeout`，只可提供 liveness；该 runtime metadata 只用于单轮关联与诊断，最终评审真相仍是报告锚，**MUST NOT** 演化为第二份工作流进度真相源。

#### Scenario: 同轮两站点不会互踩
- **WHEN** `design-voice` 与 `hr-tg` 在同一 run 并发 dispatch
- **THEN** 两站点拥有不同 job id 与独立 stdout/stderr/rc 文件，任一站点完成或失败均不覆盖另一站点证据

#### Scenario: rc 原子发布定义终态
- **WHEN** worker 仍在写 stdout 或 stderr
- **THEN** `<site>.rc` SHALL 不存在，collect MUST 视为 RUNNING；worker 结束后 SHALL 先完成输出写入，再以 temp+rename 原子发布纯十进制 rc

#### Scenario: 元数据损坏不得猜成功
- **WHEN** job JSON 缺字段、short id 不唯一、rc 非纯十进制、或 rc=0 但 stdout 为空
- **THEN** collect SHALL 判 `exec-error`，MUST NOT 从日志散文、agent summary 或半成品 stdout 猜测成功

### Requirement: barrier 有界等待并只认真实终态

**Requirement ID: OVBG-03.** Codex-host Step3 barrier **SHALL** 调用确定性的 `await/collect` helper 等待终态 sidecar；该 helper MAY 在内部以短间隔检查本地 sidecar，但主 session **MUST NOT** 自造无界 shell polling loop。await 的上界 **SHALL** 为 dispatch timeout + 30 秒 grace；后台 voice 复用 `outside-voice.async-timeout-seconds`，默认 timeout 为 900 秒、合法范围 1..3600。**[grill-amendment]**

`reason_code="timeout"` **MUST** 只由 worker 实际写出的 `.rc=124` 产生。deadline+grace 到达仍无 rc、agent 提前 failed/stopped/missing、机器睡眠/重启导致 job 停止等情形 **SHALL** 停止/移除已知 job 并归约为 `exec-error`，MUST NOT 冒充 timeout，MUST NOT 自动 respawn 造成重复计费。

#### Scenario: 真实内层 timeout 保持 124 语义
- **WHEN** `outside-voice.sh exec --timeout 900` 的内层 timeout 到达并返回 124
- **THEN** worker 原子写 `.rc=124`，collect 映射 `reason_code="timeout"` 并走同族 fallback

#### Scenario: supervisor/job 丢失不是 timeout
- **WHEN** deadline 前 `claude agents --all --json` 显示 job failed/stopped/missing 且 `.rc` 不存在
- **THEN** collect SHALL 立即判 `exec-error` 并 fallback，MUST NOT 等满 900 秒，MUST NOT 写 `reason_code="timeout"`

#### Scenario: 外层 collect 被回收不丢后台结果
- **WHEN** Codex 的 await shell 调用在 worker 完成前被外层回收
- **THEN** supervisor 托管的 worker SHALL 继续运行；下一次 collect 可从相同 job 元数据与终态 sidecar 恢复，MUST NOT 重派第二个 Claude job

### Requirement: background 路径保持只读与出境安全

**Requirement ID: OVBG-04.** **[grill-amendment]** background worker **SHALL** 原样复用 `outside-voice.sh exec` 的四旗（`--tools "Read,Grep,Glob"`、`--strict-mcp-config`、`--add-dir <repo_root>`、`--settings <read-fence>`）、共享 FRAME、入境/出境 secret scan 与 200KB 截断。Claude 反向 runner **SHALL** 使用 `resolve-models.sh` 解析出的 Claude `strong` 模型（canonical 缺省及目标仓当前值为 `opus`），并显式传 `--effort high --safe-mode --no-session-persistence`；显式 read-fence 与四旗仍须生效。

worker stdout 只有在 `.rc=0` 后才可进入 findings 池；stderr **MUST** 留在 gitignored run dir，仅允许向报告暴露退出码、行数和字节数，**MUST NOT** 逐字写入 tracked 报告。runner 无 Write/Bash 工具，因而不能伪造由 worker 发布的 rc sidecar。

#### Scenario: ambient customizations 不进入 outside voice
- **WHEN** 项目或 user settings 配置 SessionStart hooks、plugins、skills 与 memory
- **THEN** background Claude runner SHALL 在 safe mode 下运行，启动事件不得执行这些 customizations，同时显式只读四旗与 read-fence 仍生效

#### Scenario: secret 与失败 stderr 不进入报告
- **WHEN** 入境 context 或成功候选输出命中 secret scan，或 runner 非零退出并产生 stderr
- **THEN** secret 路径沿既有 exit 3 拒发；非零 stderr 不作为 findings、不被转录进报告，报告只记结构化降级字段

#### Scenario: background 命令不得扩大工具权限
- **WHEN** 检查 background worker 最终执行的 Claude runner argv
- **THEN** 工具集 SHALL 精确为 `Read,Grep,Glob` 且包含 strong model、high effort、MCP 隔离、仓根授权、read-fence、safe mode、no-session-persistence，MUST NOT 含 Write/Edit/Bash/WebFetch **[grill-amendment]**

### Requirement: 完成、失败与取消任务可清理

**Requirement ID: OVBG-05.** 每个 terminal job 在结果已 collect 后 **SHALL** 调用 `claude rm <id>` 清理 supervisor roster/job 状态；人工中止或 deadline+grace 失效 SHALL 先 `claude stop <id>`、再在进程终止后 `claude rm <id>`。清理失败 **MUST** 作为诊断告警可见，但不得删除 `.outside-voice/<run-id>/` 的本轮审计证据，也不得改写已经取得的 rc。

#### Scenario: 正常 collect 后无活动残留
- **WHEN** 一个 SUCCEEDED/TIMED_OUT/FAILED job 已完成 collect
- **THEN** `claude agents --cwd <repo> --json` 不再列出该活动 job，run dir 内 job 元数据与终态文件仍可供本轮审计

#### Scenario: stop/rm 失败显形
- **WHEN** Claude supervisor 不可达导致 stop 或 rm 失败
- **THEN** helper SHALL 返回/记录 cleanup warning 与 short id 供人工处理，MUST NOT 静默声称已清理，MUST NOT 因清理失败把已成功 findings 改判失败
