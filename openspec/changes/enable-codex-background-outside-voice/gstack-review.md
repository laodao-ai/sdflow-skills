<!-- sdflow:step1-broad-review v1 mode="native" -->

# gstack-review（广审）— enable-codex-background-outside-voice

> 原生执行佐证：主 session 按 `autoplan` 的 CEO → Eng → DX 顺序完成广审，UI scope 不命中；已建立 restore point。双声侧真实调用 Claude `opus`，在旧同步路径以 `rc=124`、stdout=0 结束，随后按协议由 fresh Codex 子代理完成同族 fallback。该 timeout 是本变更目标问题的复现，不伪装成跨模型成功。

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" host="codex" runner="codex" reason_code="timeout" findings="3" truncated="false" -->

## 结论

问题与目标匹配：现有 Codex-host → Claude voice 在真实负载上 5/5 timeout，本轮又复现一次 `rc=124`；把现有 `outside-voice.sh exec` 放到 Claude supervisor，而不是延长同步等待，是最直接的目标态。方案继续复用已有 FRAME、secret scan、四旗与 rc 语义，避免重建安全核心。

```text
CURRENT                         THIS CHANGE                         12-MONTH IDEAL
Codex 同步等 300s → timeout  → supervisor 托管 + 可信 collect  → 双宿主均异步、可审计、按真实终态裁决
```

## 方案对照与自动决策

| 方案 | 完整度 | 系统/用户/开发循环后果 | 裁决 |
|---|---:|---|---|
| A. `claude --bg --exec` 托管现有 helper | 9/10 | 最少复制安全逻辑；快返；新增 job 生命周期 | **采用** |
| B. 交互式 `claude --bg '<prompt>'` | 6/10 | 公开入口，但结果依赖 transcript/log，结构化终态弱 | 弃选 |
| C. 自建 daemon/launchd/systemd | 10/10 | 可完全控生命周期，但安装、跨平台、维护面显著放大 | 暂不采用 |
| D. 同步 900 秒 | 4/10 | 可能提高成功率，但继续阻塞关键路径且保留回收风险 | 弃选 |

主次判定：先实现可信终态与真实第二意见；不为 research-preview 的所有边角自建 daemon。

## Findings

### G1 — 真实 efficacy 缺少可机读的模型、effort 与时长证据（high，高置信）

- 证据：`proposal.md:7-9`、`tasks.md:46-48` 要求证明 `opus` + `high` 且自然耗时 `>300s`；但 `design.md:54-68` 的 `job.json` 没有 `runner/model/effort`，也没有 terminal/collect 时间或 duration。
- 风险：实现可真实跑通，却无法用现有盘面证明关 T162 的关键条件；最终只能靠散文/终端回忆，release gate 假绿或永远无法关闭。
- 建议：把 `runner/model/effort` 写入不可变 job metadata；`collect` 结构化返回 dispatch/terminal/collect UTC 与 duration，真实 smoke 把这些字段落报告。

### G2 — `shlex.quote` 不能承载仓库现有 Windows 安装面（high，高置信）

- 证据：`design.md:207` 指定用 `shlex.quote` 生成 background shell command；`setup.sh:5,17,45` 与 `README.md:77` 明确支持 Windows copy 模式。Python 官方文档明确 `shlex.quote` 只保证 Unix shell，Windows/non-POSIX shell 可能产生命令注入风险。
- 风险：Windows supervisor 使用的 shell grammar 与 POSIX 不同，路径空格/单引号可导致 dispatch 失败或注入；安全要求与跨平台安装面冲突。
- 建议：把命令编码契约改为按目标 shell 显式分支并测试；POSIX 可用 `shlex.join`，Windows 必须使用经过 golden/注入用例验证的 PowerShell argv bridge。MUST NOT 用一套 `shlex.quote` 声称跨平台安全。

### G3 — 同 site 并发 dispatch 的“先查后派”仍有双计费窗口（high，高置信）

- 证据：`design.md:95-106` 写了 `validate+reserve` 与“独占创建”，但数据模型只有 dispatch 成功后才完整写出的 `<site>.job.json`；`tasks.md:4` 只要求 atomic 写 job.json。
- 风险：两个 dispatch 同时通过存在性检查后都能先启动外部 job，再争写 metadata；失败的一方已经产生模型成本，违反重复 dispatch 必须拒绝的目标态。
- 建议：在任何外部副作用前以 `O_CREAT|O_EXCL` 建立 `<site>.reserve`；成功发布 job.json 后释放。补并发竞态测试，并把 dispatch 后、metadata 前崩溃记为已知残余与清理指引。

### G4 — “每轮最多两个站点”未变成 helper 的机械上限（medium，高置信）

- 证据：`design.md:106,198-202` 声明上限 2；`tasks.md:4` 只测同 site 重派和两站点隔离，没有第三个不同 site 的拒绝用例。
- 风险：未来新增 producer 后无界增长不会被 helper 拦，成本/并发上界静默失效。
- 建议：reserve 时原子计数本 run 已保留站点，第三个不同 site fail-loud；补并发测试。

### G5 — Migration Plan 的最低版本仍写 2.1.154（medium，高置信）

- 证据：`design.md:5`、delta spec 与 tasks 已统一为 2.1.169；`design.md:233` 仍写 `2.1.154+`。
- 风险：实现按迁移步骤验证时会把缺 `safe-mode`/当前 agents JSON 契约的版本误作可用。
- 建议：统一为 2.1.169，并保留低版本快速降级负向 smoke。

### G6 — `--bg --exec` 是实测可用的 research-preview 执行形态，不是公开文档承诺（medium，高置信）

- 证据：本机 Claude Code 2.1.218 的 `claude --bg --exec 'printf …'` 约 1 秒返回、`agents --all --json` 终态为 `done`、logs 可取、rm 成功；但官方 agent-view 文档只公开 `claude --bg '<prompt>'`，公开 CLI help 也不列 `--exec`。
- 风险：把本机隐藏能力写成稳定“官方契约”会弱化版本漂移预期。
- 建议：文案改为“research-preview supervisor 上的本机实测 exec 形态”；版本 preflight 只做必要条件，真实 dispatch 继续作为最终能力探针。

## Error & Rescue Registry

| codepath | 失败 | 归约 | 用户/操作者看到 |
|---|---|---|---|
| preflight | 版本旧、agent view 禁用、JSON 形态坏 | preflight-error + 同族 fallback | actionable 升级/策略提示 |
| dispatch | 无唯一 id、超 5s、reserve 冲突 | exec-error + fallback | site + 结构化原因 |
| worker | rc=124 | timeout + fallback | 真实 timeout，不早退 |
| worker | 其他 rc、terminal 无 rc | exec-error + fallback | rc/行数/字节数，不转录 stderr |
| collect | rc=0 但 stdout 空/坏 metadata | exec-error + fallback | 结构化损坏原因 |
| cleanup | stop/rm 失败 | 不改既有裁决 | short id + cleanup warning |

## DX 与范围

- Persona：维护 sdflow 工作流、在 Codex/Claude 两宿主运行评审的工程师。
- TTHW：现状约 1 条 skill 命令，但 Codex 路径等待 300 秒后才失败；目标仍是一条命令，dispatch <5 秒、报告给出真实终态与修复指引。
- 不在范围：自建 daemon、无界站点队列、改变 Claude-host → Codex 既有路径、重做认证。
- 已复用：`outside-voice.sh`、`resolve-models.sh`、`dispatch-manifest.tsv`、`anchor_lint`、async marker parity gate。

## 自动决策与已裁掉

- **[自动决策] D1**：采纳 G1/G3/G4/G5/G6，回流 design/spec/tasks。
- **[自动决策] D2**：采纳 G2 的目标态要求，保持 Windows 安装面，不用“当前主要在 macOS”缩小目标；实现允许按 shell 分支。
- **[已裁掉] X1**：fallback 提议给 outer `claude --bg --exec` 叠 `--safe-mode --no-session-persistence`。本机反例直接输出 `--exec ignores --safe-mode --no-session-persistence (only --name composes)`；outer 是 raw exec 托管层，隔离旗应继续作用于 inner `claude -p`。保留 outer 无模型 hook-negative 测试即可，不落无效 flags。

## Broad Review Score

- CEO/scope：9/10；问题、替代与 non-goals 清晰。
- Engineering：7/10；终态语义强，但审计证据、并发 reserve 与 Windows quoting 尚需补齐。
- DX：8/10；快速诚实降级明确，需让 version/platform 诊断与真实 efficacy 证据可复制。
- UI：不命中。

〔gstack-amendment：G1-G6 纳入后续多镜合并池；本文件不直接替代 spec-review 的独立镜与最终裁决。〕
