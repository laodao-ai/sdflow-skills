## ADDED Requirements

### Requirement: outside-voice exec 的 dispatch 模式宿主自适应

编排评审 SKILL 调用 `outside-voice.sh exec` 的 **dispatch 模式 SHALL 按 `$SDFLOW_HOST` 自适应**（读 Step0 已解析值、MUST NOT 重判宿主，ADR-9 同源），使跨模型 voice 在真实评审负载下不被外层超时杀：

- **`$SDFLOW_HOST=claude` ∧ 后台能力自探通过 ∧ 主 session 已确证**：SHALL 将 voice exec 派为 **off-critical-path 后台执行**（harness `run_in_background`；三个条件缺一即走 sync 分支），dispatch 秒返、主 session 继续其余评审工作，综合阶段（Step3）以**通知驱动 barrier** collect（完成推送异步到达即暂存，非轮询）；voice SHALL 得以跑到完成，MUST NOT 被外层 Bash 超时杀。**内层 `--timeout` 天花板仅此 async 分支** SHALL 由 sync 默认 300s 调大（config 默认 900s、caller flag、脚本不改；spike 证后台跨 Bash 外层 600000ms 上限可达）——**Codex 同步分支与 claude 自探失败降级同步分支保留 sync 300s 天花板 / 外层 ≥330s**，始终外层 ≥ 内层+30s。
- **`$SDFLOW_HOST=codex`**：SHALL 保持**同步执行**（外层超时 ≥330s）——Codex 宿主下后台进程在 shell 命令返回时被 sandbox 域回收，off-critical-path 架构性不可行；超时按既有语义降级。

#### Scenario: Claude 宿主 voice 跑到完成、efficacy 非零
- **WHEN** `$SDFLOW_HOST=claude` 且一次真实评审的 voice 推理时长 > 外层同步超时窗口
- **THEN** voice 经后台执行跑到完成，锚行记 `reason_code="ok"`（跨模型 findings 进合并池），**而非** `reason_code="timeout"` 降级同族

#### Scenario: 主 session 无长阻塞调用
- **WHEN** `$SDFLOW_HOST=claude` 派 voice
- **THEN** dispatch 的 Bash 调用 SHALL 秒级返回（不设 ≥330s 外层超时、不阻塞主 session），主 session 得以与 voice 并行推进 fan-out 镜

#### Scenario: Codex 宿主保持同步
- **WHEN** `$SDFLOW_HOST=codex` 派 voice
- **THEN** SHALL 同步执行（外层超时 ≥330s），MUST NOT 尝试后台化；超时（exit 124）→ 既有同族 fallback（`reason_code="timeout"`）

#### Scenario: 后台能力不可用【或无法确证主 session】则降级同步（保留 sync 天花板）
- **WHEN** `$SDFLOW_HOST=claude` 但当前执行上下文无 `run_in_background` 能力（自探失败），**或无法确证本次执行位于主 session**（子代理上下文在轮次终结时会整体回收在飞的后台任务，而自探对该模式结构性失明——它在同轮次内取回哨兵，故必报可用）
- **THEN** SHALL 降级回同步执行、**用 sync 300s 天花板 + 外层 ≥330s**（MUST NOT 沿用 async 900s——否则外层 330s 会假超时杀正常降级 voice），报告显式标注降级，MUST NOT 假装 async 成功、MUST NOT 静默失败

### Requirement: async dispatch 不改变锚契约与诚实降级

async dispatch SHALL 是**纯执行时机**的改变——锚行契约、`reason_code` 枚举、`anchor_lint` 合法组合矩阵、`outside-voice.sh` 出境安全三件套 MUST 逐字不变；collect SHALL **通知驱动（非轮询）**、按**结构化退出码 envelope** 分支，voice 未按天花板完成 / 退出码未知 / task lookup 失败时 SHALL 保守诚实降级（同族 fallback），MUST NOT 假绿；barrier 时站点仍 RUNNING SHALL 让出轮次等终态通知，`reason_code="timeout"` SHALL **只由实际观测到的 `exit 124`** 产生。

#### Scenario: 锚契约与矩阵不变
- **WHEN** 本 change 落地后跑 `anchor_lint` 的 host×runner×reason_code×findings 全笛卡尔 golden
- **THEN** 结果 SHALL 与本 change 前逐条一致（合法组合矩阵未被触碰）

#### Scenario: 撞天花板 / 退出码未知 → 诚实降级
- **WHEN** `$SDFLOW_HOST=claude` 后台 voice 撞 async `--timeout` 天花板（exit 124）、或结构化 envelope 取得退出码 `1/2`、或退出码丢失 / task lookup 失败
- **THEN** collect SHALL 走既有同族 fallback（124→`reason_code="timeout"`；`1/2`/未知/丢失→`exec-error`，reason_code 枚举不新增）；退出码 MUST 由结构化 envelope 取、MUST NOT 从 voice 正文推断；MUST NOT 静默当 `ok`、MUST NOT 落零锚

#### Scenario: 起了没收不得读作成功
- **WHEN** 后台 voice 已 dispatch 但评审中止 / 未 collect
- **THEN** 该站点 SHALL 无 `reason_code="ok"` 锚（读作 voice 缺席），MUST NOT 因"起过一次"而假绿

#### Scenario: barrier 时站点仍 RUNNING 不得早退落 timeout
- **WHEN** Step3 barrier 时某 dispatch 站点尚无终态退出码（后台 voice 仍在跑、未撞天花板）
- **THEN** 主 session SHALL 让出轮次等待该任务的完成/超时通知，MUST NOT 落 `reason_code="timeout"`；`timeout` SHALL 只由实际观测到的 `exit 124` 产生——早退假 timeout 会把「慢但会成功」的 voice 降级（即本 change 要消灭的 efficacy=0），且该假绿**逃过 per-site 站点集核**（站点仍在集合内）

#### Scenario: 退出码不可被 runner 伪造（经 runner 不可写的通道取得）
- **WHEN** voice 的 stdout 正文含退出码样式文本（本 change 自指场景下必然出现），或 wrapper 未能发出该文本（后台任务在轮次终结时被回收 ⇒ 写 stdout 的那步从未执行）
- **THEN** 退出码 SHALL 取自 **runner 不可写的旁路通道**（wrapper 在 runner 结束后写入 run 目录的 `<site>.rc` sidecar，主 session 独立读取）；**该通道之所以可信，是因为四旗承重墙只授予 runner 只读工具集（无 Write / 无 Bash）**。文件缺席 / 内容不匹配 `^[0-9]+$` / 读取失败 SHALL 判 `exec-error`（诚实降级）。
- **MUST NOT** 从 voice 的 stdout 推断退出码——无论用哨兵串、整行锚定还是子串匹配：**stdout 是 runner 能写的通道**。亦 **MUST NOT** 把「随机 run-id 拼进哨兵」当作认证——runner 被授予仓库读取能力，可枚举 `.outside-voice/` 直接取得该值，认证不能建立在模型读得到的字符串上。

#### Scenario: per-site 完整性机械可审（并发多站点漏收）
- **WHEN** Claude 宿主同轮并发 dispatch 2 个站点（design-voice + hr-tg），其一 dispatch 后未 collect、另一正常落锚
- **THEN** 机械核 SHALL 报错（`declared` 应**有锚**站点集 ≠ 实落 `outside-voice` 锚站点集）——MUST NOT 因 anchor_lint 家族级门（"outside-voice" 有 ≥1 行即过）而判 CLEAN，使「漏收」与「合法不派」机械可区分

#### Scenario: 复用态 MUST NOT 假红（declared 按「应有锚」而非「应 dispatch」）
- **WHEN** spec-review 复用 autoplan 的 codex voice（reuse-guard `reason_code=none` ⇒ **未** dispatch `design-voice`，但报告仍落 `site="design-voice"` 锚——归档实证 44 条）
- **THEN** 机械核 SHALL 判 CLEAN：`declared` SHALL 含 `design-voice`（该层**恒有锚**站点），MUST NOT 定义为「应 dispatch 的站点集」（否则在最常见路径上假红）；同理 `code-voice`（code-review，always）SHALL 恒在 declared 内
- **AND** 机械核 SHALL NOT 解析 `guard=` 字段——其语义**站点相关**（`design-voice` 上 `none`=复用·未派，`hr-tg` 上 `none`=填充值·已派），拿它承重即引入 site 特判

#### Scenario: 机械核不得自指假阳（fence 口径单一源）
- **WHEN** 报告正文含模版或示例锚行（讨论锚格式的 change 报告本身即是）
- **THEN** 机械核 SHALL 复用 `anchor_lint.py` 的 `fence_outside_lines` 口径统计真锚，MUST NOT 另起裸 grep 解析路径（否则模版/示例锚被计入 → 自指假阳，且形成 fence 口径二源）

#### Scenario: 错误路径未扫描 stderr 不当 findings
- **WHEN** 后台 voice `exit≠0`（helper 把未过出境 scan 的 runner stderr 写 stderr、落进 harness 后台输出文件）
- **THEN** collect SHALL 只把 exit0 的 stdout 当 findings 采信、按结构化状态判降级，MUST NOT 把后台文件原始 stderr 当 findings 进池（后台文件「内容=已过 scan」仅对 exit0 成立）

#### Scenario: outside-voice.sh 零改动
- **WHEN** 审查本 change 的 diff
- **THEN** `outside-voice.sh` SHALL 零改动（四旗承重墙、`secret_scan`、FRAME、200KB 截断逐字不变）
