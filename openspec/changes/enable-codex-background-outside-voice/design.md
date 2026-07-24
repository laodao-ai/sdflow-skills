<!-- /autoplan restore point: ~/.gstack/projects/laodao-ai-sdflow-skills/feat-enable-codex-background-outside-voice-autoplan-restore-20260724-1203.md -->

## Context

当前 `sdflow-spec-review/SKILL.md` 与 `sdflow-code-review/SKILL.md` 的等值调度段在 `host=codex` 时同步调用 `outside-voice.sh exec --timeout 300`。helper 的 Claude 分支再运行 `claude -p --model "$SDFLOW_VOICE_MODEL" --tools "Read,Grep,Glob" --strict-mcp-config --add-dir "$repo_root" --settings "$OV_CLAUDE_READ_FENCE"`。`zhws_ops_api` 的 `optimize-device-access-authorization` 已提供 5/5 真实 rc124 证据；小且未截断 context 在关闭 customizations 后仍可撞 90 秒天花板，说明根因是“无界 agentic review × 同步固定天花板”，不是安装、context 截断或 hooks 单点故障。

旧 change `async-outside-voice` 的判断“Codex 无可用后台原语”在当时成立；当前本机 Claude Code `2.1.218` 已提供 `claude --bg --exec '<command>'`，该能力自 `2.1.154` 出现。实测 `claude --bg --exec 'printf SDFLOW_EXEC_BG_OK'` 在约 1 秒内返回 short id，发起 shell 结束后由 per-user supervisor 完成，`claude agents --all --json` 给出终态。官方 agent-view 文档亦声明 background session 由独立 supervisor 托管、无需终端保持打开。**[grill-amendment] 完整方案的最低版本不是 2.1.154，而是 2.1.169：该版本才同时具备本方案承重的 `--safe-mode` 与含 `--all`/`id`/`state` 的 agents JSON。**

本 change 命中：外部 CLI、job 数据对象与状态机、3+ 组件协作、复杂降级、新组件/codepath、并发、可用性、信任边界、测试计划、多需求、多利益相关方、未验证前提、合理方案竞争与外部 LLM 成本；不命中业务 backend/frontend/embedded 领域清单。

## Goals / Non-Goals

**Goals:**

- Codex-host Claude voice 用官方 supervisor 脱离发起 shell，dispatch ≤5 秒并与 fan-out 重叠。
- 保留现有 `outside-voice.sh exec` 的安全、prompt、stdout、退出码契约，终态成功才允许 findings 进池。
- 用 per-run/per-site 盘面证据关联 dispatch、await、collect、stop/cleanup；外层等待中断后可恢复而不重派。
- 将受支持能力下限、故障归约、900 秒天花板、并发边界与真实 smoke 做成可回归契约。

**Non-Goals:**

- 不保证 Claude 推理在 300 秒内完成；可证伪假设是 supervisor 托管 + 900 秒天花板足以覆盖目标真实负载，否则数据支持后另调上限。
- 不实现自有常驻 daemon/launchd/systemd 服务；可证伪假设是 Claude 官方 supervisor 在受支持版本上的存活与清理 smoke 全绿，否则回退重新评估外部 daemon。
- 不改变 Claude-host → Codex 的既有 harness background 路径；可证伪假设是其既有 async 测试与真实 reason_code=ok 继续成立。
- 不支持无界站点 fan-out；可证伪假设是两层评审的 producer 契约仍将每轮实际站点限制在 0..2，若新增第三层/动态站点则重新设计限流。

## Components

| 组件 | 职责 | 权威/边界 |
|---|---|---|
| `outside-voice.sh` | render、secret scan、四旗 Claude/Codex runner、同步 child 生命周期、最终 stdout/rc | 既有安全与执行契约单一源 |
| `outside-voice-job.py`（新增） | `preflight/dispatch/status/await/collect/cleanup/worker`；调用 `claude --bg --exec` 并管理 per-site 终态文件 | 只编排后台生命周期，不复制 prompt/scan |
| Claude Code supervisor | 在 Codex shell 退出后托管 `worker` | 外部 research-preview 依赖，**[grill-amendment] 最低 2.1.169** |
| 两份 review SKILL | 按 host 选择 harness async 或 supervisor async，在 Step3 barrier collect | marker 内段保持字节等值 |
| `.outside-voice/<run-id>/` | context、dispatch manifest、job metadata、stdout/stderr/rc | gitignored 单轮审计证据，非 workflow 进度真相 |

```text
spec-review SKILL ─┐
                   ├─ host branch ─ Claude host → harness run_in_background ─┐
code-review SKILL ─┘             └ Codex host  → outside-voice-job.py ────────┤
                                                        │                    │
                                                        ▼                    │
                                              Claude supervisor --bg --exec  │
                                                        │                    │
                                                        ▼                    │
                                              outside-voice.sh exec           │
                                                        │                    │
                                                        ▼                    ▼
                                               per-site terminal files → Step3 barrier
```

## Data Model and Lifecycle

`<site>.job.json` 只存不可变 dispatch 事实：

```json
{
  "schema_version": 1,
  "run_id": "20260724T020000Z-Ab12Cd",
  "site": "design-voice",
  "repo_root": "/abs/repo",
  "short_id": "75d34378",
  "session_id": "uuid-or-null",
  "dispatched_at": "2026-07-24T02:00:00Z",
  "deadline_at": "2026-07-24T02:15:00Z",
  "timeout_seconds": 900,
  "command_sha256": "..."
}
```

不持久化可变 `status`。状态由 agent liveness 与终态文件派生：

```text
                 dispatch accepted
PREPARED ───────────────────────────▶ RUNNING
                                         │
                 ┌───────────────────────┼────────────────────────┐
                 │ rc=0 + stdout         │ rc=124                 │ other rc
                 ▼                       ▼                        ▼
             SUCCEEDED                TIMED_OUT                 FAILED

RUNNING ── agent terminal/missing 且 rc 缺席 ──▶ LOST(exec-error)
RUNNING ── deadline+30s 且 rc 缺席 ───────────▶ LOST(exec-error)+stop

任一 terminal ── collect ──▶ cleanup supervisor job（run-dir 审计证据保留）
```

worker 先写 `<site>.stdout`/`<site>.stderr`，child 退出后再将 rc 写入临时文件并 atomic rename 为 `<site>.rc`。collect 只在 rc 发布后读取 stdout，从而不把半成品误作成功。

## Sequence and Concurrency

```text
Codex main       job helper          Claude supervisor       worker/outside-voice     run dir
    | dispatch       |                      |                         |                    |
    |--------------->| validate+reserve     |                         |                    |
    |                 | --bg --exec-------->| spawn detached          |                    |
    |                 |<-- short id --------|------------------------>| exec helper        |
    |<-- job id ≤5s --| write job.json      |                         | stdout/stderr ----->|
    |                 |                      |                         | rc atomic --------->|
    | run other lenses/fan-out               |                         |                    |
    | await/collect -->| inspect rc/liveness |                         |                    |
    |<-- terminal + findings/status ---------|-------------------------|--------------------|
    | cleanup ------->| stop? / rm id ------>|                         |                    |
```

同 run 最多两个站点，各自只写 `<site>.*`，共享目录但不共享可变文件。`dispatch-manifest.tsv` 继续登记 `site ↔ short_id`；job helper 使用独占创建/atomic rename，重复 dispatch 同一 site 必须 fail-closed，避免双倍计费与结果竞态。

## Decision Flow

```text
host?
├─ unknown ───────────────────────────────▶ host-unknown（不派）
├─ claude
│  ├─ harness background + main confirmed ▶ 既有 async 900s
│  └─ unavailable                         ▶ sync 300s compatibility fallback
└─ codex
   ├─ Claude >=2.1.169 + bg-exec ready     ▶ supervisor async 900s  [grill-amendment]
   └─ unavailable/disabled/bad dispatch    ▶ immediate same-family fallback

Codex collect terminal?
├─ rc=0 + nonempty stdout ────────────────▶ ok
├─ rc=124 ────────────────────────────────▶ timeout
├─ other rc / terminal without rc ────────▶ exec-error
└─ running ───────────────────────────────▶ bounded await; never early timeout
```

## Decisions

### ADR-1: 用 `claude --bg --exec` 托管现有 helper，而不是交互式 background agent

- **[grill-amendment] 拍板**：确认采用该架构。真实接缝探针已验证 supervisor 后台环境不继承 `CLAUDECODE=1`，且后台 shell 能成功运行带 `--safe-mode --no-session-persistence` 的嵌套 `claude -p`；因此这里不是以 `printf` smoke 代替模型链路证明。
- **决策**：新增 job helper，将 `outside-voice.sh exec` 作为 background shell session 托管。
- **系统镜**：复用现有 stdout/rc/secret-scan 契约；不依赖私有 transcript 路径或 TUI logs 解析。代价是依赖 research-preview supervisor 与 `--exec` 能力。
- **用户镜**：dispatch 快返，最终仍拿到真实 Claude findings；不会多套一层 Claude agent 或产生双重模型调用。
- **开发循环镜**：新增一个状态编排脚本与测试矩阵，但安全核心不复制，维护面小于外部 daemon。
- **主次判定**：结构化结果与最小新增机制优先，选择 `--bg --exec`。
- **弃选**：`claude --bg '<prompt>'`（结果只能经 agent transcript/logs 收，schema 私有且 TUI 难解析）；launchd/systemd daemon（跨平台重、生命周期与安装面扩大）；同步 900 秒（成功率可能提高但关键路径阻塞且仍受外层回收）。

### ADR-2: `.rc` 是终态发布点，Claude job state 只提供 liveness

- **[grill-amendment] 拍板**：确认以 worker 原子发布的 `<site>.rc` 为唯一终态发布点；真机反例表明 `exit 7` 与 `exit 124` 在 supervisor JSON 中都只归为 `failed`，且作业退出后 logs control socket 可能已不可读，故 supervisor 信号无权决定 `ok` 或 `timeout`。
- **决策**：worker 原子发布 rc；status 不持久化，按 rc + `claude agents --all --json` 派生。
- **系统镜**：模型无写工具，不能伪造 rc；agent state schema 漂移时仍可凭 rc 收成功。代价是 worker 在 child 结束与 rc rename 间崩溃会落 LOST。
- **用户镜**：不会把“Completed”摘要或半截输出误判成第二意见。
- **开发循环镜**：测试可以机械覆盖每个状态组合，避免模型读 prose 猜状态。
- **主次判定**：防假绿优先于极窄崩溃窗的自动恢复；LOST 诚实 fallback。

### ADR-3: Codex-host 不保留同步 300 秒兼容路径

- **[grill-amendment] 拍板**：确认 background 能力不满足或 dispatch 失败时在 5 秒级立即同族 fallback，彻底删除 Codex-host 的同步 Claude 300 秒分支；`zhws_ops_api` 五个真实站点均为 rc124，已证明该路径在目标负载上只有等待成本、没有跨模型产出。
- **决策**：background 能力不可用时立即同族 fallback；只有 Claude-host 保留原 sync compatibility branch。
- **系统镜**：Codex 真实基准 5/5 timeout，继续同步只增加时延和费用而没有跨模型价值。
- **用户镜**：失败更快、更可操作（升级 Claude/解除策略），不再每站点白等 300 秒。
- **开发循环镜**：分支更少；代价是旧 Claude 版本不再“尽力”跑反向 voice。
- **主次判定**：真实 efficacy 证据优先于名义兼容，快速诚实降级。

### ADR-4: safe mode 是隔离加固，不是完成保证

- **[grill-amendment] 拍板**：确认 Outside Voice 主动隔离项目/user customizations；真机 deny 探针已证明 `--safe-mode` 下显式 `--settings` permissions 仍生效。`--effort` 不属于隔离边界，见 D-5。
- **决策**：Claude runner 加 `--safe-mode --no-session-persistence`，显式四旗与 read-fence 保留。
- **系统镜**：减少 hooks/plugins/memory 污染和无关 token；90 秒对照仍超时，故完成保证来自后台生命周期而非 isolation。
- **用户镜**：outside voice 更独立，减少项目自定义规则把第二意见同化。
- **开发循环镜**：需增加 safe-mode 下 read-fence 与四旗真机回归；无项目配置清理前置。
- **主次判定**：安全/独立性加固保留，但不据此缩短 900 秒天花板。

### D-5: Claude strong（目标仓解析为 opus）+ high effort + async 900 秒

- **[grill-amendment] 拍板**：Claude voice 继续从 `resolve-models.sh` 取得 Claude 机队 `strong`，canonical 缺省和 `zhws_ops_api` 当前解析值均为 `opus`；调用显式使用 `--effort high`。async timeout 复用既有 `outside-voice.async-timeout-seconds`，默认 900 秒、合法范围 1..3600。
- **系统镜**：模型名仍由 model-tiers 单一源治理，不在 helper 复制 `opus`；显式 high 避免当前 Opus 默认值或 user 设置漂移。900 秒给强模型完整找漏窗口，同时保持硬上界。
- **用户镜**：优先拿到有质量的跨模型第二意见；最坏 barrier 等待与调用成本高于 medium，但 dispatch 仍 ≤5 秒且两个站点并发。
- **开发循环镜**：不新增 effort config；已有 timeout 配置继续承担仓级耐心调节，测试只需钉 resolver 输出与最终 argv。
- **主次判定**：评审质量优先于交互速度；成本由有界 timeout、站点上限和现有 model-tier 覆盖控制。

### D-6: preflight 无副作用，真实 dispatch 是最终能力探针

- **[grill-amendment] 拍板**：preflight 只校验 Claude Code ≥2.1.169 与 `claude agents --all --json` 可调用/顶层结构可解析，不创建 `claude --bg --exec 'true'` dummy job。实际 worker dispatch 在 5 秒内完成最终能力核验；失败或拿不到唯一 id 即快速同族 fallback。
- **系统镜**：不为每层制造额外 supervisor job、清理动作与 job-id 竞态；代价是策略禁用/冷启动故障到真实 dispatch 才暴露，但该阶段仍未发起内层模型推理。
- **用户镜**：失败时延仍为 5 秒级，不承担 dummy job 残留噪声。
- **开发循环镜**：preflight 测试只覆盖版本与 JSON 顶层；实际 dispatch 测试承担 id/schema/策略失败，职责不重叠。
- **主次判定**：最小副作用与单一真实探针优先。

## Failure Modes and Observability

| 失败模式 | 机械信号 | 去向 | 可观测性 |
|---|---|---|---|
| Claude <2.1.169 / agent view disabled | preflight/dispatch 非零，无唯一 id | preflight-error + 同族 fallback | stderr actionable 升级/策略提示 **[grill-amendment]** |
| supervisor 冷启动慢 | dispatch >5s 或非零 | exec-error，不假后台成功 | dispatch duration + 原始非敏感摘要 |
| helper 内层 900s timeout | `.rc=124` | timeout + fallback | job id、dispatch/deadline/terminal UTC |
| runner/helper 非零 | `.rc=1/2/3/...` | 既有映射 | 只记 rc、stderr lines/bytes |
| job failed/stopped/missing 且无 rc | agent terminal + rc absent | exec-error | short id + agent state |
| Codex await 被回收 | rc/job 仍存在 | 下轮恢复 collect | manifest/job.json 可重入 |
| 机器 sleep/shutdown | job stopped、rc absent | exec-error，不 auto-respawn | 明示需重跑 review/fallback |
| job 元数据/schema 损坏 | parse/shape fail | exec-error | fail-closed 字段名，不打印 context |
| cleanup 失败 | stop/rm 非零 | 已取结果不改判 | cleanup warning + short id |

## Non-Functional Requirements

- dispatch p95（本机集成 smoke）≤5 秒；单次 status/collect 查询 ≤5 秒，不含 barrier 等待。
- 默认 worker timeout=900 秒，可配范围 1..3600；await grace 固定 30 秒。
- 每轮每层实际 background voice 站点上限为 2；同 site 重复 dispatch=硬失败。
- job metadata/rc 原子发布；terminal rc 后 collect 幂等，重复 collect 输出/分类一致。
- 任何 pending/lost/corrupt 组合产生 `reason_code="ok"` 的数量必须为 0。

## Security and Data Protection

- `outside-voice.sh` 继续负责入境/出境 secret scan、FRAME、截断与四旗，job helper 不接触/重组 prompt 正文。
- background worker 命令参数只携带受校验的绝对路径、runner/model 与 timeout；用 argv + `shlex.quote` 生成唯一 shell command，拒绝换行/NUL、越出 repo/run-dir 的路径。
- `<site>.stdout/.stderr/.rc/.job.json` 创建权限 0600，父目录沿 `.outside-voice` gitignore；tracked 报告不转录 stderr/context。
- **[grill-amendment]** safe mode 禁 ambient hooks/plugins/skills/memory，`--no-session-persistence` 禁 inner `claude -p` transcript；显式 read-fence 已用无敏感内容的 `/etc/hosts` deny 探针真机验明，仍须补自动回归防未来 CLI 漂移。
- `claude --bg --exec` supervisor 是本机同用户信任域，不声称提供 OS 沙箱；安全边界仍由 inner helper 的只读工具与应用层 read deny-list 承担。

## Test Coverage

```text
                    outside-voice background jobs
                     /            |             \
            dispatch/lifecycle  integrity       security
             /      |      \      /   \          /    \
        fast-return survive 2site rc-matrix lost safe-mode four-flags
                                   |      |       |       |
                              0/124/other corrupt secret  no-write

                  host integration / real smoke
                   /                         \
         Claude-host existing async     Codex-host >300s job
```

**[grill-amendment]** 单测用 fake `claude`/fake helper 覆盖 version、dispatch 输出、agents JSON、状态笛卡尔、原子 rc、cleanup 与注入路径；集成测试用 `claude --bg --exec` 的无模型 shell job 证明跨 shell 存活。真实 efficacy 门只要求在 `zhws_ops_api` 完成一层 spec-review 或 code-review，但该层所有 declared/dispatch 站点必须可信 collect 且 reason_code=ok，并至少有一个 `opus` + `high` 推理自然耗时 >300 秒；sleep/shim、无模型或短调用只能证明编排，不能替代 efficacy 证明。

## Migration Plan

1. 新增 job helper、tests 与 `setup.sh` 的 `*.py` 安装路径；不切换 SKILL。
2. 加 Claude 2.1.154+ 无模型 `--bg --exec` smoke，验证 dispatch/status/await/cleanup。
3. 修改 `outside-voice.sh` Claude argv 的 isolation flags，并跑既有全套安全/child-lifecycle 测试。
4. 同步修改两份 review SKILL marker 段并跑 parity gate。
5. `bash setup.sh` 刷新 `~/.sdflow/hack/`，在 `zhws_ops_api` 跑真实 Codex-host spec/code review。
6. 真实锚全 ok 后关闭 T162；下游通过 `sdflow-init update` 获取规则/工具。

**Rollback**：先把两 SKILL 的 Codex branch 切回快速同族 fallback（不恢复已证低效的同步 300 秒），再移除 job helper 安装；`outside-voice.sh` isolation flags可独立保留或按真机回归回退。已 dispatch 的 job 按 manifest short id 执行 stop/rm，run-dir 审计证据保留。

## Risks / Trade-offs

- [Claude agent view 是 research preview，CLI/state 可能漂移] → 最低版本门 + `--bg --exec` 无模型 smoke + rc 盘面优先 + schema fail-closed；不解析私有 transcript。
- [机器睡眠/关机会停止本地 session] → 不自动 respawn（避免重复计费），归约 exec-error/fallback，报告显形。
- [900 秒提高单次额度上界] → 站点上限 2、helper 内 timeout、deadline cleanup；以成功结果替代失败+fallback 双耗。
- [worker 在 child 退出与 rc rename 间崩溃] → terminal agent 无 rc 判 LOST，不从 stdout 猜成功；低概率边角接受诚实降级。
- [外层 await 仍可能在 barrier 等待较久] → dispatch 与其余 lenses 重叠；await 被回收后 job 继续并可恢复，目标是结果不丢而非保证整轮瞬时完成。
- [safe mode 可能改变 repo 指令可见性] → outside voice 自带 FRAME/四通则，定位本就是独立找漏；真机对比 findings 质量，若显著退化可单独回退 safe mode而不回退后台架构。

## Open Questions

**[grill-amendment]** 无阻塞开放问题。已收敛：最低共同能力版本为 2.1.169；safe mode 下显式 read-fence 已真机 deny；真实 efficacy 门为一层完整评审全站点 `ok` 且至少一个自然 >300 秒的 `opus` + `high` 成功站点；preflight 无副作用，真实 dispatch 是最终能力探针。

## Compliance

- D-1：文中的 helper argv、SKILL marker、setup 安装模式、Claude 版本与 `--bg --exec` 均已从当前仓库/本机 CLI/changelog 核验。
- D-3：所有 Non-Goals 均附可证伪假设。
- D-4：外部 Claude supervisor 的 5 秒 dispatch/status、900 秒 worker timeout、30 秒 grace 与 stop/rm 回滚路径已明确。
- D-6：核对 `openspec/CONTEXT.md` 的盘面即状态、反静默、宿主/机队与自包含重写边界；runtime job metadata 不承载工作流完成真相，最终仍以报告锚为准。
- canonical-first：只改本仓 source assets/SKILL，再经 setup/update 分发；不直接修下游 workflow 副本。
