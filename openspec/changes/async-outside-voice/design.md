## Context

两个评审 SKILL 各有一份「outside-voice helper 调用协议」节（`sdflow-spec-review/SKILL.md` line 263 · `sdflow-code-review/SKILL.md` line 261）。voice `exec` 是**主 session 的一次 Bash 调用**（`$HELPER exec --context-file <f>`），协议明写外层 Bash 超时由**调用方**设 ≥330000ms（`outside-voice.sh` 内部 `timeout -k 10` 默认 300s + grace）。真实评审负载下 voice 推理时长 >300s → 被外层超时杀 → 降级同族 fallback，efficacy=0。

**spike 实证（2026-07-18，本机 darwin + codex-cli 0.144.5）：**
- Claude 宿主：`run_in_background`（及 `nohup`）后台进程**跨 Bash tool call 存活**、跑到完成、结果后续可取。
- Codex 宿主：每条 shell 命令返回即**回收该命令 spawn 的一切本地进程**（`nohup` + `setsid` 新会话皆秒死，按 sandbox 域回收非按 pgid）；codex **无生产可用后台原语**（`deferred_executor` under-dev+默认关；cloud/exec-server/app-server/multi_agent 只跑 codex 自己）。

**约束**：`outside-voice.sh` = 契约单一源 + 四旗承重墙（不碰）；锚行契约 + `anchor_lint` 合法组合矩阵（不碰）；`$SDFLOW_HOST` 每轮 Step0 解析一次已在环境（ADR-9 同源）。

## Goals / Non-Goals

**Goals:**
- Claude 宿主把 voice exec 移出关键路径（harness `run_in_background`），voice 跑到完成、恢复跨模型 efficacy。
- Codex 宿主保持同步 + 既有诚实降级（超时→同族 fallback），明牌接受边界。

**Non-Goals:**
- 不改 `outside-voice.sh`（脚本本体 / 四旗承重墙 / 出境安全三件套）。
- 不解 Codex 宿主方向的 efficacy=0（架构性无解，另立项）。
- 不改锚行契约 / `anchor_lint` 合法组合矩阵。

## Decisions

### ADR-1（核心）：用 harness `run_in_background`（SKILL 编排层），不在 outside-voice.sh 加 dispatch/collect
- **选**：主 session 对 `$HELPER exec` 调用设 `run_in_background`，harness 托管后台生命周期 + 完成通知；Step3 收结果。
- **弃**：outside-voice.sh 自加 `dispatch`/`collect` 子命令 + caller-owned jobdir + TTL sweep（探索初期骨架）。
- **理由**：harness 托管生命周期 ⇒ jobdir 孤儿清理、TTL、出境 scan 窗口变宽这些难点**全消失**；outside-voice.sh 契约脚本 + 四旗承重墙**零触碰**（高危面归零）；outside-voice.sh 内部 `mktemp`+`trap` 在其自身进程完成时正常触发（run_in_background 只把整个 exec 后台化，不改脚本内部同步语义）。**代价**：async 编排逻辑进 model-driven SKILL（指令非机械门），靠 grill/spec-review 压。

### ADR-2：Claude-宿主-only async，Codex 保持同步
- **选**：`$SDFLOW_HOST=claude` → async；`$SDFLOW_HOST=codex` → 同步现状。
- **弃**：① 一套 `nohup` 打通双宿主（spike 证 Codex 秒杀 → 作废）；② Codex 用外部 claude daemon（重、脆、超 skills 仓范畴）。
- **理由**：spike 实证 Codex 架构性不可后台化。目标态导向——不为 Codex 一个宿主拖垮 Claude 宿主的可行优化；Codex 方向 efficacy=0 另立项。

### ADR-3〔grill-amendment〕：deadline = 调大既有 `--timeout` 天花板（脚本不改），Step3 轮询到 voice 终止、按现有 exit-code 契约分支
- **选**：dispatch @Step1/2（context 就绪即派），`--timeout` 由 sync 默认 300s **调大到 config 默认 900s**——backgrounding 解除了「外层阻塞主 session」这个当初压小内层 timeout 的唯一理由；collect @Step3 轮询后台任务**到它自己终止**（≤天花板保证终止：exit 0=跑完 / exit 124=撞内层 timeout 自杀），按**现有** exit-code 分支（exit0→findings 进池 `reason_code=ok`；exit124→同族 fallback `reason_code=timeout`）。
- **弃**：① 新造 dispatch/collect deadline 机制（多余——既有 `--timeout` 就是机械天花板）；② Step3 到「镜子跑完 + 小 grace」即放弃回落同族（**否**：async 存在的全部理由就是拿到真 voice，早回落把长尾又还给 efficacy=0 ⇒ max 耐心 = 天花板）。
- **理由**：deadline **不是 T_voice 的估计值**（任务间方差大、单发采样无意义），而是「worst-case 愿等多久」的 max-耐心天花板，天生 task-independent；voice 与 fan-out 镜重叠 ⇒ 绝大多数任务在镜子跑完前就绪（免费），慢任务落长尾多等（「慢但真」代价，整轮墙钟升至 ≈天花板，但 collect 是轮询非单条长 Bash ∴ 无 ≥330s 单次阻塞）。天花板 = 既有 `--timeout` **caller flag**（脚本一字不改，符 ADR-1），做成 `config.yaml` 键（默认 900s，仓库可覆盖）——这是「任务时长不一」的诚实解：发 sane 默认 + 给旋钮，不假装预测 per-task。锚契约完全不变（exit124 分支既有）；不假绿。

### ADR-4：host 分支复用 Step0 已解析的 `$SDFLOW_HOST`，不重判
- 承 ADR-9 同源约束：async/sync 分支读 Step0 export 的 `$SDFLOW_HOST`，MUST NOT 各自重判宿主（防信号跨调用点漂移）。

### ADR-5〔grill-amendment〕：async 分支两 SKILL 各改一份 + **机械等值门**守一致（非人工 scope-check），全抽取留 Q3 todo
- **选**：spec-review（line 263 节）+ code-review（line 261 节）各加 host 分支；两处 async **host 调度段**（站点无关逻辑）用 `<!-- sdflow:async-branch:start/end -->` marker 圈定，加 `hack/check_async_branch_parity.py` 断言两段**字节相同**、挂进 `setup.sh` + `hack/tests/`——漂了当场红（沿用 `sync_principles.py --check` 既有 idiom）。
- **弃**：① 人工 scope-check 表（低于本仓 `一致性机械化优先` 基准 adr/0006(b)「凡机械 prose MUST 脚本化」——人工守正是该被脚本化的机械 prose）；② 现在就抽单一源运行时注入（SKILL 是独立 symlink 目录、无运行时 include 机制，抽取要新建机制 = 越 scope）。
- **理由**：两 SKILL 本就各有一份 helper 协议（既有重复），本 change 循既有形态最小改动。async 两分支必须逐字一致，否则一个宿主路径静默行为分叉（load-bearing 正确性）——∴ 用机械等值门一次封死漂移面（面治优先于点补），而非再添一份靠人守。等值门属「async 正确落地」的一部分（related + 低成本 → fold）；长期全抽取（单一源注入）超 scope，留 Open Q3 todo（tasks §5.2）。

### ADR-6〔grill-amendment; spec-review-amendment(F-E)〕：ship 路径下 code-review 跑在主 session，A2 强论证（非逐字实证）+ 自探是实际防线
- **证据强度校正〔spec-review F-E，三镜独立收敛〕**：ship line 101「主 session inline 执行」**绑在 `sdflow-implement mode=tickets-plan`**、**非** `RUN_CODE_REVIEW→/sdflow-code-review`（后者链序里是裸跳转、无 inline/子代理注记，接地镜 + 对抗镜2 + 广审 B2 独立核实）。∴「code-review 主 session 内联跑」的结论**成立**，但靠 line 96「本 skill 自身…不直接派子代理」+ line 80「meta-orchestrator：chain 现有 skill、不取代」两条**通用**陈述推出（ship 不 spawn 子代理 ⇒ 它 chain 的 /sdflow-code-review 在主 session 内联加载），**不是**一句逐字直接证据钉死。
- **推论（措辞降级）**：Q2 从「读码**已解**」改为「读码**强提示**，A2 大概率成立」——task 1.3/2.1 的 run_in_background 自探**不是「兜底未来漂移」的冗余保险，而是当前验证 A2 的实际防线**：无论 code-review 调用上下文如何演化（当前主 session、或未来若改子代理派发），自探不可用→降级同步、报告标注、不假绿——机制 fail-safe。

## 序列图（TG-10）：async dispatch / collect 流（Claude 宿主）

```
主 session          harness(bg)        outside-voice.sh        fallback 子代理
   │                    │                    │                      │
   │─Step0 resolve host─│                    │                      │
   │─写 <site>-context──▶                    │                      │
   │─exec(run_in_bg)───▶│─启后台进程────────▶│(mktemp+trap,同步跑)  │
   │  <1s 返回 task_id  │                    │  secret_scan/render  │
   │─继续 fan-out 镜、其余评审工作(重叠)──────┤  runner exec…        │
   │                    │                    │  出境 secret_scan    │
   │                    │◀───完成通知────────│(trap 清理 workdir)   │
   │─Step3 collect─────▶│  读 task 输出      │                      │
   │  exit0→findings进池 │                    │                      │
   │  exit124/1 或 到deadline未完 ────────────┼─render-prompt→派────▶│(同族只读)
   │  ← fallback findings + reason_code=timeout/exec-error          │
   │─落锚行(契约不变)、Step3 综合───────────────────────────────────┤
```

## 状态图（TG-09/12）：voice 单站点生命周期（锚 reason_code 不变）

```
 dispatch(run_in_bg) ─▶ RUNNING ─┬─ exit 0 ───────────▶ DONE     → findings 进池, reason_code=ok
                                 ├─ exit 124/1 ───────▶ 同族 fallback → reason_code=timeout/exec-error
                                 ├─ exit 3(secret) ───▶ 拒发不 fallback → reason_code=secret-hit, findings=0
                                 └─(collect@deadline 仍 RUNNING)─▶ 同族 fallback → reason_code=timeout
 Codex 宿主：无 RUNNING 态（同步阻塞≤330s），分支同上但无 dispatch/collect
 never-collected(评审中止)：无锚 ⇒ 读作 voice 缺席, MUST NOT 读作 ok
```

## 并发与共享状态访问策略（TG-26）

Claude 宿主并发实体：`design-voice` voice + `hr-tg` voice + N 个 fan-out 镜子代理，全后台/并行。
- **context 文件**：按站点固定命名（`.outside-voice/design-voice-context.md` / `hr-tg-context.md`，SKILL line 272-274），站点间**不共写** → 无竞争。
- **后台输出**：harness `run_in_background` 每任务独立输出文件 → 任务间不共写。
- **report 写**：单一主 session 在 Step3 顺序 collect + merge → 无并发写 report。

∴ **无数据竞争**：并发实体各写各的、汇聚点（Step3 主 session）单线程。唯一新增面 = 主 session 须记账「站点↔task_id」映射（model-driven 记账易错）→ SKILL 指令 MUST 显式列该映射，collect 时按站点逐一取。

**dispatch 门控与条件性〔grill-amendment〕**：后台 voice 数**不定（0/1/2）**，记账须按「实际 dispatch 过的站点」列、非固定两个：
- `design-voice`（spec-review）**前置门控于 reuse-guard**：先同步跑 `outside_voice_guard.py`（快），仅 `reason_code≠none`（autoplan voice 不可复用）时才 dispatch design-voice；可复用则该站点整体不派（避免双 codex）。
- `hr-tg`（两 SKILL）**条件触发**：仅 HR-TG ∩ ≠ ∅ 时 dispatch；`code-voice`（code-review）always。
- **「起了没收」无孤儿危害**：Step3 轮询到 voice 终止（≤`--timeout` 天花板 = 脚本自杀点）⇒ 不存在「报告已出、voice 仍在后台跑」的状态，无需 kill-orphan 逻辑；评审中止残留的后台进程在 Claude 宿主 reparent PID1 自行跑完无害（A1 spike 证），无锚 = 读作 voice 缺席（状态图既有）。

## Security（TG-17）

`outside-voice.sh` 一字不改 ⇒ `secret_scan`（入/出境）、FRAME 三条通则注入、UNTRUSTED 硬分隔、四旗承重墙、200KB 截断**逐字不变**。`run_in_background` 只把整个 `exec` 后台化：outside-voice.sh 内部同步语义（mktemp workdir + trap 清理 + **出境 `secret_scan` 在 emit 前**）在其自身进程内正常完成——**后台化不引入新出境端点、不拉宽 scan 窗口**。新增落盘面仅 harness 托管的任务输出文件，其内容 = 已过出境 `secret_scan` 的 findings。∴ 安全面无回归。

## Scope-check 表（TG-25 / BASE-29）

| 文件 | helper 协议节 | 本 change 改动 |
|---|---|---|
| `sdflow-spec-review/SKILL.md` | line 263「outside-voice helper 调用协议」 | exec 步加 host 分支（claude=run_in_background dispatch / Step3 collect；codex=同步现状） |
| `sdflow-code-review/SKILL.md` | line 261 同名节 | 同上，措辞逐字对齐 |

守一致：两处 async host 调度段（marker 圈定、站点无关部分）MUST **字节相同**，由 `hack/check_async_branch_parity.py` 机械守（ADR-5，挂 setup.sh + hack/tests）——**非**人工 scope-check。

## Risks / Trade-offs

- [async 编排在 model-driven SKILL、非机械门] → grill/spec-review 压 + SKILL 指令显式列「站点↔task_id」映射 + 降级路径（不可用回同步）。
- [`run_in_background` 在 ship 调 code-review 时可能不可用（Open Q2）] → SKILL 自探能力、不可用回落同步（不假绿）。
- [两 SKILL 重复 helper 协议漂移] → scope-check 表 + 评审守当次一致；DRY 抽取另立 todo。
- [voice 跑到完成的墙钟/token 成本] → 预期代价（换 efficacy），与镜工作重叠不叠加。

## Migration Plan

- **部署**：改两 SKILL.md → `setup.sh` symlink 即时生效（无需重装；改的是 skill 源、非 hack 脚本）。
- **回滚**：`git revert` 本 change commit；两 SKILL 恢复同步现状，`outside-voice.sh` 从未变 → 零协同风险、无脏状态。

## Open Questions

grill（2026-07-18）三条均收敛，无未决：
1. collect deadline bound → **已决**：调大既有 `--timeout` 天花板（config 默认 900s）、Step3 轮询到终止（ADR-3）。
2. run_in_background@ship 可用性 → **已解**：读码，code-review 主 session inline，A2 由构造成立（ADR-6）。
3. DRY → **已决**：两份副本 + 机械等值门（ADR-5）；长期全抽取超 scope，留 todo（tasks §5.2）。

## Compliance

- 不碰 `sdflow:principles` 托管块、不碰 `outside-voice.sh` 契约、不碰 `anchor_lint` 矩阵——遵守。
- DOC-1（正文即最终态）：本设计正文即最终态，无考古层。
- 设计基准：机械化优先（锚契约仍机械守，async 编排是残余语义层，诚实登记）· 目标态导向（不拿 Codex 现状缩 Claude 优化）· 无界不手搓（不手搓进程管理，用 harness 原生后台）。
