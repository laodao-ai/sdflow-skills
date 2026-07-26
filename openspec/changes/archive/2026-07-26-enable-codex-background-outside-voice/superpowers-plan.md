---
impl-pipeline: tickets
---

## Global Constraints

以下为逐字摘自本 change `design.md` 的硬约束与 Compliance 条款（非转述），对每张 ticket 的
implementer 与两轴审 reviewer 同等生效。

**数据模型与发布门（design.md · Data Model and Lifecycle）**

- `<site>.reserve` 必须在任何外部 dispatch 前以 `O_CREAT|O_EXCL` 原子建立；`<site>.job.json` 只存不可变 dispatch 事实。
- worker 启动后原子发布 `<site>.started.json`（`started_at`、可验证的 worker/process-tree identity、attempt nonce），终态发布 `<site>.terminal.json`（`terminal_at`、stdout digest、attempt nonce）后再发布 `.rc`；collect 结构化返回 `dispatched_at/started_at/terminal_at/collected_at/duration_seconds/runner/model/effort`。这些 sidecar 只证明本轮执行与发布门，不承载 workflow 完成状态。outer supervisor 的 short id 仅是定位线索；任何 `status/stop/rm` 在破坏性操作前都必须重新核验 canonical id、repo、site 与 attempt identity，核验失败只能告警，不能猜目标。
- worker 先把自身及 child stdout/stderr 直接重定向到 0600 的 `<site>.stdout`/`<site>.stderr`，避免原始输出进入可被 `claude logs` 读取的 outer supervisor transcript；child 退出后写 terminal witness，再将 rc 写入临时文件并 atomic rename 为 `<site>.rc`。collect 只在 rc 发布后读取 stdout，从而不把半成品误作成功。

**并发与恢复（design.md · Sequence and Concurrency）**

- 同 run 最多两个站点，各自只写 `<site>.*`，共享目录但不共享可变文件。reservation 在外部副作用前同时机械核验同 site 唯一性与本 run 两个 slot 上限；第三个不同 site 也 fail-closed。`dispatch-manifest.tsv` 继续登记 `site ↔ short_id`。若进程在 dispatch accepted 与 job metadata 发布之间崩溃，残留 reserve 进入 `unknown-cost`：后续只允许 reconcile/人工 cleanup，禁止再次 dispatch 或立即 fallback，避免双倍计费。外层 await 子进程中断时，主评审 session 保留显式 run-dir 并从相同 metadata collect；若整个评审 session 已丢失，新评审不得扫描“最新目录”猜测恢复目标，只能用显式 `reconcile --run-dir` 处理 abandoned run 后新开 run。

**非功能约束（design.md · Non-Functional Requirements）**

- dispatch p95（本机集成 smoke）≤5 秒；单次 status/collect 查询 ≤5 秒，不含 barrier 等待。
- 默认 worker timeout=900 秒，可配范围 1..3600；await grace 固定 30 秒。
- 每轮每层实际 background voice 站点上限为 2；同 site 重复 dispatch=硬失败。
- job metadata/rc 原子发布；terminal rc 后 collect 幂等，重复 collect 输出/分类一致。
- 任何 pending/lost/corrupt 组合产生 `reason_code="ok"` 的数量必须为 0。
- 5 秒 dispatch 使用 monotonic deadline；超时必须回收 spawn 进程树并清理尚未产生外部 job 的 reserve。worker 的 900 秒 deadline 从可信 `started_at` 起算，另设独立 startup deadline，不能用 dispatch 时刻误杀排队中的合法 worker。
- helper 对第三个不同 site 原子拒绝；每个成功 smoke 必须可机读证明 model、effort 与自然运行时长。

**安全与数据保护（design.md · Security and Data Protection）**

- `outside-voice.sh` 继续负责入境/出境 secret scan、FRAME、截断与四旗，job helper 不接触/重组 prompt 正文。
- background worker 命令参数只携带受校验的绝对路径、runner/model 与 timeout；v1 仅在已验证的 POSIX shell 上用 `shlex.join`/等价 quoting 生成唯一 shell command，拒绝换行/NUL、越出 repo/run-dir 的路径；未验证的平台/shell preflight fail-closed。
- `<site>.stdout/.stderr/.rc/.job.json` 创建权限 0600，父目录沿 `.outside-voice` gitignore；tracked 报告不转录 stderr/context。
- outer worker 在执行任何可携带 payload 的代码前完成文件重定向；supervisor logs/state 不得包含 context、child stdout/stderr 或 secret canary。清理必须按 `stop → 核验 worker/子树终止 → rm`，无法核验时保留 orphan warning，禁止自动 fallback 叠加费用。
- safe mode 禁 ambient hooks/plugins/skills/memory，`--no-session-persistence` 禁 inner `claude -p` transcript；显式 read-fence 已用无敏感内容的 `/etc/hosts` deny 探针真机验明，仍须补自动回归防未来 CLI 漂移。
- `claude --bg --exec` supervisor 是本机同用户信任域，不声称提供 OS 沙箱；安全边界仍由 inner helper 的只读工具与应用层 read deny-list 承担。

**效能门（design.md · Test Coverage）**

- 真实 efficacy 门只要求在 `zhws_ops_api` 完成一层 spec-review 或 code-review，但该层所有 declared/dispatch 站点必须可信 collect 且 reason_code=ok，并至少有一个 `opus` + `high` 推理自然耗时 >300 秒；sleep/shim、无模型或短调用只能证明编排，不能替代 efficacy 证明。

**Compliance（design.md · Compliance）**

- D-1：文中的 helper argv、SKILL marker、setup 安装模式、Claude 版本与 `--bg --exec` 均已从当前仓库/本机 CLI/changelog 核验；`--exec` 只按本机验证的 research-preview 形态陈述，不升级为公开契约。
- D-3：所有 Non-Goals 均附可证伪假设。
- D-4：外部 Claude supervisor 的 5 秒 dispatch/status、900 秒 worker timeout、30 秒 grace 与 stop/rm 回滚路径已明确。
- D-6：核对 `openspec/CONTEXT.md` 的盘面即状态、反静默、宿主/机队与自包含重写边界；runtime job metadata 不承载工作流完成真相，最终仍以报告锚为准。
- canonical-first：只改本仓 source assets/SKILL，再经 setup/update 分发；不直接修下游 workflow 副本。

### Task 1: 后台派发落地——preflight 无副作用 + dispatch ≤5 秒 + worker 跨 shell 存活

**Blocked-by:** none
**R-ID:** OVBG-01, OVBG-02

Codex 宿主发起一次 Claude outside voice 后台派发：先做无副作用的能力 preflight（Claude Code
最低版本、`claude agents --all --json` 顶层结构、已安装 helper/data 的同代 capability manifest、
受支持的 POSIX shell），通过后在 monotonic 5 秒 deadline 内拿到可审计的 canonical job id 并返回；
发起的 shell 退出后，worker 仍由 per-user supervisor 托管，跑完既有 outside-voice exec 并按
started → terminal → rc 的顺序原子发布本轮证据。能力不满足或 dispatch 失败一律快速诚实降级，
不伪造后台成功。

- [x] preflight 在旧版本、agent view 被策略禁用、非 POSIX 平台三种情形下 fail-closed，stderr 给 actionable 升级/解禁提示
- [x] 负向 golden 证明 preflight 不执行 `--bg --exec 'true'`、不创建任何 dummy job、无任何外部副作用
- [x] 任何外部副作用之前先以 `O_CREAT|O_EXCL` 建立 reservation；同 site 重复派发与本 run 第三个不同 site 均在外部副作用前原子拒绝
- [x] dispatch 在 monotonic 5 秒 deadline 内返回并核验唯一 canonical job id；超时回收 spawn 进程树，并清理尚未产生外部 job 的 reserve
- [x] job metadata 以临时文件 + atomic rename 写入，字段含 schema version、run id、site、repo root、attempt nonce、runner、model、effort、platform、canonical job id、session id、dispatch UTC、timeout 秒数、命令摘要
- [x] 发起 shell 退出后 worker 仍跑到终态（可由无模型 job 证明跨 shell 存活），worker 第一动作发布 started/process-tree identity，终态发布 terminal witness 后再 atomic rename 出纯十进制 rc
- [x] dispatch accepted 与 metadata 发布之间崩溃留下的残留 reserve 判定 `unknown-cost`，禁止自动重派、禁止立即 fallback

### Task 2: 终态派生的 status/await/collect——只认可信终态，不假绿

**Blocked-by:** 1
**R-ID:** OVBG-02, OVBG-03, HAE-09

调用方可以对一个已派发的站点做有界等待与结果收集：状态不持久化，全部由 rc 与 agent liveness
派生；未到终态不读 stdout；只有真实内层 timeout 才归 timeout，其余异常一律 exec-error。收集结果
是幂等的，并结构化返回可机读的时刻/时长/runner/model/effort 证据。

- [x] rc 维度（rc=0+非空 stdout / rc=124 / 其他 rc / 坏 rc / rc=0+空 stdout）× liveness 维度（agent working/done/failed/stopped/missing）× 元数据维度（完整 / 缺字段 / schema drift）逐组合有确定性归类，且终态前不读 stdout
- [x] 只有真实 124 归 timeout；terminal 无 rc、失联、元数据损坏一律 exec-error，不从 stdout 猜成功
- [x] 任何 pending/lost/corrupt 组合产生 `reason_code="ok"` 的数量为 0（机械断言）
- [x] startup deadline 独立于 worker deadline；worker 上界从可信 `started_at` 起算为 timeout + 30 秒 grace，排队中的合法 worker 不被误杀
- [x] 站点仍 RUNNING 时有界 await 不早退、不落 timeout
- [x] collect 幂等：重复收集的输出与分类一致，并返回 dispatched/started/terminal/collected 时刻、自然 duration、runner/model/effort 与 stdout digest
- [x] 超时上限复用既有 async timeout 配置项，默认 900 秒、合法范围 1..3600，越界值被拒绝

### Task 3: 中断恢复与 identity-safe 清理——不重派、不猜目标、不掩盖 orphan

**Blocked-by:** 2
**R-ID:** OVBG-03, OVBG-05

外层等待被回收、评审 session 中断、人工取消或任务失联时，结果不丢且成本不翻倍：同一评审 session
按保留的确切 job/run-dir 恢复收集；session 整体丢失只走显式 reconcile；一切破坏性清理先核验完整
identity，子树终止不可证时诚实落 orphan warning。

- [x] 外层 await 被回收后，同一主评审 session 用保留的 exact job/run-dir 恢复 collect，结果不丢且不重新派发
- [x] 评审 session 整体丢失时，禁止扫描“最新目录”猜恢复目标；只接受显式 `reconcile --run-dir` 处理 abandoned run
- [x] terminal 结果已 collect 后才清理 supervisor roster；`status/stop/rm` 前重新核验 canonical id、repo、site 与 attempt identity，核验失败只告警不猜目标
- [x] 取消/失联按 `stop → 核验 worker 与 inner child 子树已退出 → rm` 顺序执行；子树终止不可证时落 orphan warning 并抑制会叠加费用的自动 fallback
- [x] 清理失败不改写已取得的 rc、不删除本轮 run-dir 审计证据

### Task 4: runner 隔离加固与出境面封堵

**Blocked-by:** 1
**R-ID:** OVBG-04

Claude 反向 runner 主动隔离 ambient customizations 并显式声明推理档位，同时证明后台化没有开出第二
条出境面：原始 context、半截 stdout、stderr 与 secret canary 都不得进入 supervisor transcript/state，
本轮文件权限收紧，注入与越界输入不能改写命令或逃出本轮目录。

- [x] Claude 分支 argv golden 更新为显式 `--effort high --safe-mode --no-session-persistence`，模型仍只取 `SDFLOW_VOICE_MODEL`（Claude strong），helper 版本同步升级
- [x] 四旗（`--tools "Read,Grep,Glob"`、`--strict-mcp-config`、`--add-dir <repo_root>`、`--settings <read-fence>`）、共享 FRAME、两次 secret scan、200KB 截断保持同源语义不变，既有 golden 不回归
- [x] safe mode 下 SessionStart hooks/plugins/skills/memory 不执行，显式 read-fence 仍拒绝凭证路径，只读工具精确为 `Read,Grep,Glob`
- [x] worker 在执行任何可携带 payload 的代码前完成输出重定向；真实 `claude logs <id>` canary 回归证明 context、partial stdout、stderr、fake secret 均不进入 supervisor transcript/state
- [x] job 与输出文件权限为 0600；失败 stderr 只留在 gitignored run-dir，tracked 报告只写 rc/行数/字节数
- [x] 注入与越界攻击测试证明 NUL/换行、仓外路径、重复 site、shell 元字符不能改写命令或越出本轮目录；非 POSIX 平台 fail-closed

### Task 5: 两份评审 SKILL 的宿主自适应调度切换与安装快照

**Blocked-by:** 3, 4
**R-ID:** HAE-08, HAE-09, OVBG-01

两份评审 SKILL 的等值调度段按宿主分流：Claude-host 保留既有 harness async；Codex-host 在 preflight
ready 时走后台 dispatch + Step3 有界 collect，不可用时 5 秒级同族 fallback，Codex 同步 300 秒兼容
分支彻底删除。同一批工具以带同代 capability manifest 的兼容快照原子安装到全局 home，任一 skew
preflight fail-closed。

- [x] 两 SKILL 的 async-branch 等值段同步修改，Codex sync 300 秒路径删除，负向 golden 证明 marker 段不再含该兼容分支
- [x] Codex dispatch 的 job id、site 与 attempt nonce 追加 dispatch manifest；Step3 barrier 使用有界 await/collect，逐站点按 rc 映射 `ok/timeout/exec-error/secret-hit`，RUNNING 不早退、外层 wait 回收后不重派、stderr 不进 findings/报告
- [x] 锚行契约、`reason_code` 枚举、anchor 合法组合矩阵与 `declared-sites` 公式保持不变
- [x] parity gate 证明两份 SKILL 的 marker 段逐字节一致
- [x] job helper、shell helper 与所需 data file 以同一 capability manifest/hash 作为兼容快照原子安装；执行权限/解释器、安装中断、新旧混配、stale copy 均有测试覆盖
- [x] 从临时全局 home 的已安装路径跑通完整 lifecycle（dispatch → collect → cleanup）的无模型集成 smoke；任一 manifest/hash skew 令 preflight fail-closed 并给出刷新指引
- [x] 使用说明写明最低 Claude Code 版本、agent view 被策略禁用的修法、`--exec` 为本机验证的 research-preview 形态、v1 POSIX 支持边界，以及全局 helper/SKILL 刷新与消费仓 workflow tools 刷新是两条不可互相替代的分发链

### Task 6: 真实 efficacy 证据与 T162 关闭

**Blocked-by:** 5
**R-ID:** OVBG-01, OVBG-03, HAE-08, HAE-09

在安装了新 canonical 工具之后，用 Codex 宿主对真实目标仓跑完整一层评审，拿到可机读的跨模型
efficacy 证据；只有全站点可信 `ok` 且至少一个自然耗时 >300 秒的强模型成功站点，才允许关闭 T162
并改写“Codex efficacy=0”的既有陈述，否则如实保留缺口。

- [ ] 以 Codex 宿主对 `zhws_ops_api` 跑至少一轮 `opus` + `high` 的真实 spec-review 或 code-review，该层全部 declared/dispatch 站点取得 `host="codex" runner="claude" reason_code="ok"`
- [ ] 该层至少含一个真实 Claude 推理自然耗时 >300 秒并成功的站点；sleep/shim、无模型命令或短调用不得替代
- [ ] 报告落不含 context/stderr 的结构化 efficacy 证据（runner/model/effort、dispatch/start/terminal/collect 时刻、自然 duration、stdout digest），并由确定性检查器判定通过
- [x] 仅当以上三条同时达标才关闭 T162 并更新 design/CONTEXT/hand-off 中的“Codex efficacy=0”陈述；任一未达标则保留 T162 并如实记录，不得以编排 smoke 假绿
- [x] 全量回归绿：既有 outside-voice 测试、async-branch parity 检查、通则同步 `--check`、`git diff --check` 与全量 pytest 全部通过
- [x] `openspec validate enable-codex-background-outside-voice --strict` 通过，且下游 `zhws_ops_api` 未被直接手改 canonical workflow 规则
