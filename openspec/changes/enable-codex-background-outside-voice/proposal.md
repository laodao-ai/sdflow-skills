## Why

Codex 宿主当前把 Claude outside voice 当作同步 `claude -p` 命令执行，并在 300 秒硬天花板后回落同族评审；`optimize-device-access-authorization` 的 5 个真实站点全部以 `rc=124` 退出，导致反向跨模型评审 efficacy=0，同时每站点白白阻塞 300 秒。Claude Code 现已提供由独立 supervisor 托管的 background agent，具备补上该宿主能力缺口的条件，因此现在应关闭 T162，而不是继续扩大同步等待时间。

## Success Metrics

- **[grill-amendment]** Codex-host 真跨模型成功率 — `optimize-device-access-authorization` 同类真实负载基准 `0/5 reason_code=ok` → 在 `zhws_ops_api` 至少完成一层真实 spec-review 或 code-review，该层所有 declared/dispatch 站点均可信 collect 且取得 `reason_code="ok"`，其中至少一个 `opus` + `high` 推理自然耗时 >300 秒 — 通过报告锚与 dispatch/terminal/collect 记录核验，sleep/shim/无模型或短调用不得替代。
- 关键路径阻塞 — 每个 Claude voice 同步占用单条 shell 调用约 300 秒 → dispatch 命令 5 秒内返回，collect 单次状态查询 5 秒内返回 — 通过集成测试墙钟断言与真实 smoke 记录核验。
- 诚实与安全回归 — 现有四旗、secret scan、FRAME、200KB 截断及合法组合矩阵基准全绿 → 仍为 100% 通过，且 pending/timeout/损坏结果不得产生 `reason_code="ok"` — 通过既有测试套件与新增故障矩阵测试核验。

## What Changes

- **[grill-amendment]** 新增 Claude background-agent job 的 dispatch/status/collect/stop 生命周期：Codex shell 返回后任务仍由 Claude supervisor 运行，结果只通过 worker 原子发布的 stdout/rc sidecar 收集；不解析 transcript、TUI logs 或 agent summary。
- Codex-host outside voice 从同步 300 秒改为后台 dispatch，并复用 async 默认 900 秒耐心上限；Step3 barrier 只等待终态，不把仍运行的任务伪报为 timeout。
- background dispatch 默认隔离 Claude customizations，保留只读工具、MCP 隔离、仓根授权和凭证路径读围栏；现有 prompt 扫描与 framing 继续由同一权威实现产生。
- 增加 Claude Code background-agent 能力/version preflight、任务状态机、超时停止、损坏/缺失元数据 fail-closed、残留任务清理和 schema drift 降级测试。
- 同步更新两份评审 SKILL 的等值调度段、安装资产与使用说明，并以真实 Codex-host smoke 关闭 T162。

## Requirements Priority

- **P0**：后台任务跨 Codex shell 调用存活；dispatch/collect 可机械关联；终态成功才允许 `reason_code="ok"`；四旗与出境安全契约不回归。
- **P1**：900 秒天花板、超时停止、取消/异常退出清理、旧版 Claude CLI actionable preflight、两评审 SKILL 调度等值。
- **P2**：后台任务诊断可读性、完成任务的保留期与清理体验优化。

## Capabilities

### New Capabilities

- `outside-voice-background-jobs`：定义 Claude background agent 的 dispatch、状态、结果收集、天花板、取消清理、结果完整性与安全边界。

### Modified Capabilities

- `host-adaptive-execution`：Codex 宿主从同步 Claude voice 改为 background-agent dispatch/collect，并调整降级、barrier 与 timeout 行为。

## Stakeholders and External Dependencies

- **工作流维护者**：维护 `outside-voice` helper、两份 review SKILL、安装资产与回归测试。
- **Codex 宿主使用者**：获得真实 Claude 第二意见，不再每站点同步等待 300 秒后回落。
- **Claude 宿主使用者**：既有 Claude-host → Codex voice 路径保持兼容。
- **外部依赖**：Claude Code CLI 的 background agents、`claude agents --json` 和 per-user supervisor；目标环境需满足本 change 钉死的最低能力版本。

## Assumptions

- Claude Code background supervisor 会按官方契约脱离发起终端托管会话；若目标版本不提供该能力，preflight 必须 fail-loud 并诚实降级，不能尝试伪后台化。
- **[grill-amendment]** background session 的结构化状态只承担 liveness；结果与退出语义不依赖 transcript/log schema。若 agent JSON schema 漂移但可信 rc 已发布，仍可 collect；若 rc 缺席且 liveness 无法判定，则 fail-closed 为 `exec-error`，不得猜测最终文本。
- Codex 一轮最多并行少量 outside-voice 站点；若未来扩展为无界 fan-out，当前并发与成本上界失效，必须另加队列/限流设计。

## External Service Cost

不新增模型供应商或计费账户，继续使用现有 Claude Code 认证。单站点最坏运行窗口由 300 秒扩大到 900 秒，理论单次 Claude 推理消耗上界约为现状超时窗口的 3 倍；但成功结果将替代“300 秒失败调用 + 同族 fallback”的双重消耗。实现必须保留每轮有限站点集合、终态停止和超时清理，禁止无界后台 fan-out。

## Non-Goals

- 不缩短 Claude 对复杂仓库评审的模型推理时间；可证伪假设是后台化后即使自然耗时超过 300 秒，也不再因同步 shell 天花板丢失结果。
- 不重做 Claude Code 的认证、订阅额度或 supervisor 本身；可证伪假设是受支持版本的官方 background-agent 契约足以托管本地任务，若真机存活测试失败则本方案阻塞。
- 不改变 Claude-host → Codex outside voice 的既有 harness `run_in_background` 路径；可证伪假设是该方向现有真实 `reason_code="ok"` 证据继续成立且回归测试不退化。
- 不把项目级 plugins/hooks 清理当作正确性前提；可证伪假设是 safe-mode 隔离只负责减噪，任务是否成功由后台生命周期与终态收集保证。

## Impact

- 主要影响 `sdflow-init/assets/hack/` 下的 outside-voice 运行工具、`sdflow-spec-review/SKILL.md`、`sdflow-code-review/SKILL.md`、`setup.sh` 及对应 pytest/hack tests。
- 修改 canonical `host-adaptive-execution` requirement，并新增 `outside-voice-background-jobs` capability；归档后同步主 specs。
- 下游项目需经 `bash setup.sh` / `sdflow-init update` 获取新 helper 与 SKILL 指令；`zhws_ops_api` 用作真实回归样本，不直接在其 workflow 副本上修源代码。
- 不命中 backend、frontend、embedded 技术栈领域清单；涉及外部 CLI、后台状态机、跨组件协作、复杂降级、并发、可用性、信任边界、测试计划与外部 LLM 成本。

## Compliance

- 遵守 canonical-first：工具与规则先改 `04-sdflow-skills` 权威源，再分发下游，禁止只修 `zhws_ops_api` 副本。
- 保留并回归验证 outside-voice 四旗、secret scan、FRAME、context 截断、合法组合矩阵与 per-site 完整性门；任何豁免必须在 design 明示并阻塞评审。
- 本 change 不修改共享业务数据模型、数据库、业务 API 或受产品边界约束的 schema，D-2/D-6 不适用。
