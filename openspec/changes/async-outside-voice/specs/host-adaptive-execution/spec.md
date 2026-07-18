## ADDED Requirements

### Requirement: outside-voice exec 的 dispatch 模式宿主自适应

编排评审 SKILL 调用 `outside-voice.sh exec` 的 **dispatch 模式 SHALL 按 `$SDFLOW_HOST` 自适应**（读 Step0 已解析值、MUST NOT 重判宿主，ADR-9 同源），使跨模型 voice 在真实评审负载下不被外层超时杀：

- **`$SDFLOW_HOST=claude`**：SHALL 将 voice exec 派为 **off-critical-path 后台执行**（harness `run_in_background`），dispatch 秒返、主 session 继续其余评审工作，综合阶段（Step3）再 collect；voice SHALL 得以跑到完成，MUST NOT 被外层 Bash 超时杀。内层 `--timeout` 天花板 SHALL 由 sync 默认 300s 调大（config 默认 900s、caller flag，脚本不改）——backgrounding 解除外层阻塞压力，故内层不必再压小。
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

#### Scenario: run_in_background 不可用则降级同步
- **WHEN** `$SDFLOW_HOST=claude` 但当前执行上下文无 `run_in_background` 能力（如经 `sdflow-ship` 调用的子代理上下文）
- **THEN** SHALL 自探并降级回同步执行，报告显式标注降级，MUST NOT 假装 async 成功、MUST NOT 静默失败

### Requirement: async dispatch 不改变锚契约与诚实降级

async dispatch SHALL 是**纯执行时机**的改变——锚行契约、`reason_code` 枚举、`anchor_lint` 合法组合矩阵、`outside-voice.sh` 出境安全三件套 MUST 逐字不变；voice 未按 collect deadline 完成时 SHALL 保持既有诚实降级，MUST NOT 假绿。

#### Scenario: 锚契约与矩阵不变
- **WHEN** 本 change 落地后跑 `anchor_lint` 的 host×runner×reason_code×findings 全笛卡尔 golden
- **THEN** 结果 SHALL 与本 change 前逐条一致（合法组合矩阵未被触碰）

#### Scenario: 撞 --timeout 天花板 → 诚实降级
- **WHEN** `$SDFLOW_HOST=claude` 的后台 voice 跑到既有 `--timeout` 天花板（config 默认 900s）仍未完成 → 脚本自杀 exit 124
- **THEN** collect SHALL 读到 exit 124、走既有同族 fallback 路径、锚行记 `reason_code="timeout"`，MUST NOT 静默当作 `ok`、MUST NOT 落零锚

#### Scenario: 起了没收不得读作成功
- **WHEN** 后台 voice 已 dispatch 但评审中止 / 未 collect
- **THEN** 该站点 SHALL 无 `reason_code="ok"` 锚（读作 voice 缺席），MUST NOT 因"起过一次"而假绿

#### Scenario: outside-voice.sh 零改动
- **WHEN** 审查本 change 的 diff
- **THEN** `outside-voice.sh` SHALL 零改动（四旗承重墙、`secret_scan`、FRAME、200KB 截断逐字不变）
