---
ship-gate:
  design_approved: true
  reviewed_sha: 501e3c333dc37d7c4c94e348569dd9f85da79387
---

# spec-review-report — enable-codex-background-outside-voice

> 阶段二设计评审，宿主 `codex`，`metrics.enabled=true`。Step1 原生 autoplan 广审 → Step2 三个独立对抗镜 + 接地镜 + HR 高风险触发镜 → Step3 合并去重与对抗裁决。本 change 不命中 backend/frontend/embedded 领域清单，故无业务领域镜。
>
> **设计 HARD-GATE 已于 2026-07-24 由用户拍板批准。** 被批准盘面为 `501e3c333dc37d7c4c94e348569dd9f85da79387`；初始设计的 9 High + 3 Medium 目标态缺口均已回流四件套，门后 lens-metric 裁决与报告现值一致，无需翻改。

<!-- sdflow:step1-broad-review v1 mode="native" -->

## 执行真实性

- `design-voice`：同一 run 真实调用 Claude `opus`，旧同步 helper 在 300 秒天花板返回 `rc=124`、stdout 0 bytes；随后按协议以 fresh Codex 子代理完成同族 fallback，3 findings 中采纳 2、裁掉 1。
- `hr-tg`：同一 run 真实调用 Claude `opus`，同样 `rc=124`、stdout 0 bytes；随后同族 fallback 独立给出 5 findings，全部纳入裁决。
- 两次 timeout 都只证明本 change 所修的旧路径确实失效，**不计为跨模型成功**；stderr 原文未进入 tracked 报告，仅核验行数/字节数。
- fan-out 能力探针返回 `PROBE_OK`；三个对抗角度分别覆盖并发/身份、信任/出境、运维/发布门，另有一个接地镜逐项读码核验。

## 自动决策

| 决策 | 结论 | 主要依据 |
|---|---|---|
| D1 | 外部副作用前建立 `O_CREAT|O_EXCL` reservation，并机械限制同 run 最多两个站点 | 防同 site 并发与第三站点绕过造成重复计费 |
| D2 | 引入 started/terminal/collect 不可变执行证据，发布门由确定性 checker 核验 | 否则无法证明 `opus + high + >300s`，T162 不可审计关闭 |
| D3 | v1 background transport 只支持经验证的 POSIX shell，其他平台快速同族 fallback | Python `shlex` 只保证 Unix shell；未验证 Windows shell 时 fail-closed 比伪跨平台安全更诚实 |
| D4 | `--exec` 降格为 research-preview 上的本机验证形态，版本只作必要条件 | 公开 Agent View 文档与 help 未承诺该 flag，真实 dispatch 必须是最终 probe |
| D5 | outer logs 设零 payload negative gate；cleanup 增完整 identity 与子树终止见证 | supervisor transcript 与 orphan child 是原设计未覆盖的第二出境面/成本面 |
| D6 | 同一 session 可按 exact run-dir 恢复；session 丢失只允许显式 `reconcile --run-dir` | 不扫描“最新 run”，避免并发/历史 run 误关联和误删其他 Claude job |
| D7 | helper/shell/data 以同代 capability manifest 作为兼容快照安装 | 防新 job helper 搭旧 shell helper 静默丢失 isolation flags |

## Findings（合并去重）

### R1 High — 真实 efficacy 缺少可机读证据

命中：广审、对抗镜1/3、HR fallback。初始 `job.json` 无 runner/model/effort、started/terminal/collect 时刻和自然 duration，无法机械证明 T162 关闭条件。已回流：metadata 固化模型与 effort；started/terminal sidecar 原子发布；collect 返回结构化时刻、duration、digest；真实 smoke 由确定性 checker 判定。

### R2 High — dispatch 前没有原子 reservation

命中：广审、对抗镜1、HR fallback。先启动外部 job 再写 metadata 会在并发或崩溃窗产生双计费。已回流：任何 `claude --bg --exec` 前 `O_CREAT|O_EXCL` reserve；dispatch accepted 后 metadata 缺失进入 `unknown-cost`，禁止自动重派/fallback。

### R3 Medium — “最多两个站点”仅为 prose

命中：广审、对抗镜1/3、design/HR fallback。第三个不同 site 能绕过“同 site 重复”检查。已回流：reservation 阶段原子强制 run slot ≤2，并要求第三方并发拒绝测试。

### R4 Medium — `--bg --exec` 被过度表述为官方稳定契约

命中：广审、接地镜。本机 `2.1.218` 实测可用，但公开 CLI help 与 Agent View 文档未列 `--exec`。已回流：统一改为 research-preview 上的本机验证形态；version/preflight 只作必要条件，真实 dispatch 与升级后 smoke 作最终门。

### R5 Medium — 迁移 smoke 仍写 2.1.154+

命中：广审、接地镜、design fallback。共同承重能力下限已经是 2.1.169，旧迁移步骤会让缺能力版本过门。已统一为 2.1.169；2.1.154 只保留为历史观察值。

### R6 High — 分发链与同代安装协议不完整

命中：接地镜、对抗镜2/3。`sdflow-init update` 不安装全局 hack；逐文件 copy 还可能形成新 job helper + 旧 shell helper 混配。已回流：`setup.sh` 原子安装兼容快照并由 manifest/hash fail-closed；`sdflow-init update` 只刷新消费仓 workflow tools；smoke 必须从已安装路径运行。

### R7 High — outer supervisor transcript 是第二个出境面

命中：对抗镜2。inner helper 失败时会写 stderr，而 `claude logs` 可持久查看 outer session 输出；仅约束 run-dir 不足。已回流：worker 在执行 payload 前重定向自身/child 输出，outer 只准固定结构化状态；真实 canary negative smoke 失败即阻塞 transport。

### R8 High — cleanup 缺完整身份与子树退出证据

命中：对抗镜1/2。short id 不足以证明 stop/rm 目标，且 supervisor job 消失不等于 inner Claude child 已退出。已回流：持久化 attempt/process-tree identity；破坏性操作前核验 canonical id/repo/site/attempt；顺序固定为 stop → 证实子树退出 → rm，无法证明时落 orphan warning 并抑制自动 fallback。

### R9 High — worker deadline 错锚 dispatch 时刻

命中：对抗镜1。supervisor 排队/冷启动会吃掉 900 秒执行预算并误杀合法 worker。已回流：startup 使用独立上界；worker timeout 从可信 `started_at` 起算，测试覆盖延迟启动。

### R10 High — await 恢复/abandoned run 没有唯一入口

命中：对抗镜1/3。新评审每次 `mktemp`，扫描最新 run 会误关联并发/历史任务。已回流：同一主 session 保留 exact run-dir；session 丢失后只允许显式 `reconcile --run-dir`，且只处理 metadata 能完整核验的自有 job。

### R11 High — `shlex.quote` 与 Windows 安装面冲突

命中：广审、对抗镜2、HR fallback。`shlex.quote` 不保证 non-POSIX shell 安全，现有设计却没有 shell 契约。已回流最简安全边界：v1 仅启用已验证 POSIX transport；未验证平台 preflight fail-closed，后续若支持 Windows 必须先提供对应 argv bridge 与注入 golden。

### R12 Medium — 5 秒 dispatch 缺实现级 deadline/回收语义

命中：HR fallback。仅写“≤5 秒”不能阻止卡住的 CLI。已回流：monotonic 5 秒 deadline，超时回收 spawn process tree；未产生外部 job 才可清 reservation。

## 已裁掉 / 已核清

- **X1 裁掉**：给 outer `claude --bg --exec` 叠 `--safe-mode --no-session-persistence`。本机直接反证 outer exec 会忽略两旗；隔离旗只作用于 inner `claude -p`。
- **X2 核清**：不恢复 Codex-host 同步 300/900 秒兼容路径。已有 5/5 历史 timeout，加本轮 2 个真实 timeout；能力不可用时快速同族 fallback 才是已拍板目标态。
- **X3 核清**：stderr 不可作为 findings 或 tracked 诊断正文；只保留 rc、行数、字节数。
- **X4 裁掉**：不把最低版本抬到当前本机 `2.1.218`；保留共同能力下限 2.1.169，同时让真实 dispatch 承担最终探测。
- **X5 裁掉**：不在 `job.json` 回写可变 status；不可变 dispatch/started/terminal/collect sidecar 足够，避免第二份 workflow 进度真相。
- **X6 裁掉**：不为极窄 dispatch→metadata 崩溃窗自建 daemon。采用 reserve + `unknown-cost` + 禁自动重派的诚实止损边界。

## 回流结果

- `design.md`：补 research-preview 边界、reservation/slot、started/terminal evidence、deadline 起点、outer logs、identity-safe cleanup、reconcile、安装链和 POSIX v1 范围。
- `specs/outside-voice-background-jobs/spec.md`：把上述目标态改成 SHALL/MUST 与可执行 scenarios。
- `specs/host-adaptive-execution/spec.md`：补 preflight manifest、exact-run 恢复与 outer logs negative gate。
- `tasks.md`：补 TDD 项、并发/崩溃/延迟/日志/orphan/skew/platform 测试与确定性 efficacy checker。
- `proposal.md`：收紧成功指标、外部依赖、假设与两条分发链。

## 锚与度量

<!-- sdflow:hr-tg v1 hit="TG-08,TG-09,TG-16,TG-17,TG-26" declared="TG-05,TG-08,TG-09,TG-10,TG-12,TG-14,TG-15,TG-16,TG-17,TG-18,TG-19,TG-20,TG-22,TG-23,TG-24,TG-26" evidence="外部 Claude CLI 与 job 状态机 + 5s/900s NFR + secret/read-fence 信任边界 + 同 run 两站点并发" -->

<!-- sdflow:fanout-capability v1 host="codex" subagents="available" mirrors="adversarial,grounding" -->

<!-- sdflow:outside-voice v1 site="design-voice" guard="same-family" host="codex" runner="codex" reason_code="timeout" findings="3" truncated="false" -->

<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="codex" runner="codex" reason_code="timeout" findings="5" truncated="false" -->

<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="codex" runner="codex" site="—" findings="9" 采纳="9" 裁掉="0" defer="0" 独立="4" sev="致0/高8/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="codex" runner="codex" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="0" sev="致0/高3/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="codex" runner="codex" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="codex" runner="codex" site="design-voice" findings="3" 采纳="2" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="codex" runner="codex" site="hr-tg" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="1" sev="致0/高3/中2/低0" -->

## 收敛口

四件套已覆盖本轮发现的 blocker；无未处置 Critical/High，也无开放决策。用户已按修订后的 D1–D7 批准设计 HARD-GATE，阶段二闭环完成，可进入阶段三实现/`sdflow-ship`。
