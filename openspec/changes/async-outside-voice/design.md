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

### ADR-3〔grill; spec-review-amendment(F-A,F-B,F-D)〕：async 天花板 = 调大 `--timeout`（**仅 async 分支**）；collect 是**通知驱动 barrier**（非轮询）；按**结构化**退出码分支
- **天花板（F-B 执行模式矩阵）**：`--timeout` 是 caller flag（脚本不改）。**仅 `$SDFLOW_HOST=claude` 的 async 分支**用 config 默认 **900s**——backgrounding 解除外层阻塞压力，**spike 实证**（2026-07-18：后台任务跑满 660s、跨过 Bash 外层 600000ms 上限、exit 0、ppid 稳定不 reparent）天花板可达。**Codex 同步分支 + claude 自探失败降级同步分支**保留 **300s 内层 / 外层 ≥330s**（这两条仍同步阻塞，套 900s 会假超时、或不再是「同步现状」）。始终机械满足 **外层 ≥ 内层+30s**。900s 是「worst-case 愿等多久」的 max-耐心天花板、非 T_voice 估计（任务方差大、单发无意义），做成 `config.yaml` 键（默认 900s，仓库可覆盖）。
- **collect 是通知驱动（F-A，非「轮询」）**：本 harness 的 `run_in_background` 是**完成推送通知**（"you will be notified — do not poll"；长 sleep 被 block），**不是**可主动轮询的状态查询。∴ dispatch 记 `站点↔task_id`；完成通知**异步到达**（可能早于 Step3）→ 主 session 接住即暂存该站点结果；Step3 是 **barrier**：每个「实际 dispatch 过的站点」结果 MUST 已在手（已 collect）或已按退出码降级，**MUST NOT** 单次长 sleep 等待、MUST NOT 自造轮询循环。
- **退出码结构化传输（F-D）**：按 helper 退出码分支（`0`=ok / `124`=timeout / `1`=exec-error / `3`=secret-hit / **`2`=用法错·context 不可读→并入 exec-error**，reason_code 枚举不新增）。退出码 MUST 由**可信结构化 envelope** 取得（后台命令末行固定 `EXEC_EXIT=<rc>`、与 voice 正文分隔），**MUST NOT** 从 voice 正文推断。**未知/丢失退出码 / task lookup 失败 → 保守 `exec-error` 降级**，MUST NOT 读作 `ok`。
- **弃**：① 新造 dispatch/collect 子命令+jobdir（多余，ADR-1）；② Step3 到「镜子跑完+小 grace」即回落同族（否：早回落把长尾还给 efficacy=0，max 耐心=天花板）；③ 900s 套同步分支（F-B：假超时/毁同步现状）。
- **理由**：voice 与 fan-out 镜重叠 ⇒ 多数任务镜子跑完前就绪（免费），慢任务落长尾多等（「慢但真」，整轮墙钟 ≈天花板，但 collect 靠通知/暂存非单条长 Bash ∴ 无 ≥330s 单次阻塞）。锚 reason_code 契约完全不变；不假绿。

### ADR-4：host 分支复用 Step0 已解析的 `$SDFLOW_HOST`，不重判
- 承 ADR-9 同源约束：async/sync 分支读 Step0 export 的 `$SDFLOW_HOST`，MUST NOT 各自重判宿主（防信号跨调用点漂移）。

### ADR-5〔grill; spec-review-amendment(F-M,F-O/Q4)〕：async 分支两 SKILL 各改一份 + **机械等值门**守一致；返修轮 MUST 出候选 marker 文本证可行
- **选**：spec-review（line 263 节）+ code-review（line 261 节）各加 host 分支；两处 async **host 调度段**（站点无关逻辑）用 `<!-- sdflow:async-branch:start/end -->` marker 圈定，加 `hack/check_async_branch_parity.py` 断言两段**字节相同**、挂进 `setup.sh` + `hack/tests/`（沿用 `sync_principles.py --check` idiom）。**领域镜已实证**两 SKILL 该节当前就字节相同（除 `site=` 行）→ 圈得干净可行、非空承诺。
- **F-O 闭环（Q4 拍板）**：返修/实现轮 **MUST 先写出候选 marker 文本 + 建 check 脚本**（不 defer）——把「站点无关段能否圈干净」从主张变实证，收窄基准5「圈太小没守住 / 圈太大永红」风险。collect 通知/退出码逻辑（站点无关）进 marker；站点枚举 / context 构造 / reuse-guard 门控留 marker 外。
- **弃**：① 人工 scope-check（低于 `一致性机械化优先` 基准 adr/0006(b)）；② 现在抽单一源运行时注入（要新建 include 机制=越 scope）。`--check` 无 `--apply` 单一源是**已知次优**〔F-O/对抗2-3b〕——`--apply` 式单一源注入留 DRY todo（tasks §5.2）。
- **理由**：async 两分支必须逐字一致，否则一宿主路径静默行为分叉（load-bearing 正确性）——机械等值门一次封死漂移面（面治优先于点补），属「async 正确落地」的一部分（related+低成本→fold）。

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
 dispatch(run_in_bg) ─▶ RUNNING ─┬─ exit 0 ───────────▶ DONE  → findings 进池, reason_code=ok
                                 ├─ exit 124 ─────────▶ 同族 fallback → reason_code=timeout
                                 ├─ exit 1 ───────────▶ 同族 fallback → reason_code=exec-error
                                 ├─ exit 2(context不可读)─▶ 同族 fallback → reason_code=exec-error〔F-D:2 不在旧枚举、并入 exec-error〕
                                 ├─ exit 3(secret) ───▶ 拒发不 fallback → reason_code=secret-hit, findings=0
                                 └─ 未知/丢失退出码·task lookup 失败 ─▶ 保守同族 fallback → reason_code=exec-error〔F-D，MUST NOT 读作 ok〕
 collect = 通知驱动 barrier@Step3（F-A）：完成推送异步到达即暂存该站点；Step3 每「实际 dispatch 站点」结果 MUST 在手或已按上表降级。
   deadline = terminal 可 collect（非裸墙钟；`timeout -k 10` 终止后 10s 宽限，撞天花板即 exit124）〔F-D/HV5〕
 Codex 宿主：无 RUNNING 态（同步阻塞≤330s），分支同上但无 dispatch/collect
 never-collected(评审中止)：无锚 ⇒ 读作 voice 缺席；per-site 完整性由机械核守（见并发节 F-C），非纯 prose
```

## 并发与共享状态访问策略（TG-26）

Claude 宿主并发实体：`design-voice` voice + `hr-tg` voice + N 个 fan-out 镜子代理，全后台/并行。
- **context 文件**：按站点固定命名（`.outside-voice/design-voice-context.md` / `hr-tg-context.md`，SKILL line 272-274），站点间**不共写** → 无竞争。
- **后台输出**：harness `run_in_background` 每任务独立输出文件 → 任务间不共写。
- **report 写**：单一主 session 在 Step3 顺序 collect + merge → 无并发写 report。

∴ **无数据竞争**：并发实体各写各的、汇聚点（Step3 主 session）单线程。**新增面 = 主 session 记账「站点↔task_id」映射**（model-driven 记账易错）——SKILL 指令 MUST 显式列该映射；**且 dispatch 时把 task_id 追加落盘**（写该站点 context 目录 manifest，F-I），使「是否真派发过」有落盘证据、脱离纯记忆。

**per-site 完整性机械核〔spec-review-amendment F-C·Q3 fold·基准①〕**：两个 dispatch 门控条件（reuse-guard `reason_code≠none`、HR-TG∩≠∅）在 Step1/2 **机械可算** ⇒「本轮应 dispatch 的站点集」是确定信号。anchor_lint 家族级门（"outside-voice" 有 ≥1 行即过、不核 per-site，`anchor_lint.py:154/595`）放过「并发 2 站点漏收一个」→ 返修轮 **fold 一个轻量机械核**：报告落 `declared-sites` 集（承 hr-tg 锚 `declared=` 先例 adr/0018），核「declared 应 dispatch 站点集 == 实落 `sdflow:outside-voice` 锚站点集」，不等即红（**additive 存在核**——独立小脚本 或 anchor_lint 附加校验，**MUST NOT 触碰 host/runner/reason_code 合法组合矩阵**，∴ 与「不改矩阵」Non-Goal 不冲突）。「无锚=缺席」的诚实由此**机械可审**、非纯 prose 兜底。

**dispatch 门控与条件性**：后台 voice 数**不定（0/1/2）**，记账/机械核按「实际 dispatch 过的站点」：
- `design-voice`（spec-review）前置门控于 reuse-guard：仅 `reason_code≠none`（autoplan voice 不可复用）才 dispatch；可复用则整体不派。
- `hr-tg`（两 SKILL）条件触发（仅 HR-TG∩≠∅）；`code-voice`（code-review）always。

**孤儿/泄漏〔spec-review-amendment F-G/F-H/HV5〕**：① **context 用 per-run 不可变路径** `<run-id>/<site>-context.md`（弃固定名+下轮覆盖）——闭掉「上轮孤儿 voice 未读完、下轮重写同路径」跨会话 TOCTOU（`outside-voice.sh` 的 scan@L153 与 cat@L164 是对 live 文件两次独立读，HV1 实证；per-run 路径令 scan+render 恒对同一快照）。② 评审中止：`run_in_background` 由 harness 托管（spike 证 **ppid 稳定、非 nohup-reparent-PID1**）→ 进程或跑完或被 harness 回收，无锚=缺席。但 `outside-voice.sh` 的 `trap … EXIT` **不含 INT/TERM**（L202）→ SIGKILL 泄漏 workdir（含全量 prompt.md）在 /tmp，900s 天花板三倍化该窗——**既有缺口、async 放大**，记 Cost、不改脚本（Non-Goal）。③ 孤儿跑完未 collect = 完整 token 浪费（记 Cost）。

## Security（TG-17）

`outside-voice.sh` 一字不改 ⇒ `secret_scan`（入/出境）、FRAME 三条通则注入、UNTRUSTED 硬分隔、四旗承重墙、200KB 截断**逐字不变**（接地镜逐字核）。`run_in_background` 只把整个 `exec` 后台化，脚本内部同步语义在其自身进程内正常完成。**但成功/错误路径须分别诚实登记〔spec-review-amendment DV4/HV2/1a〕**：
- **exit0**：出境 `secret_scan`（L246）在 emit 前跑 → stdout = 已扫描 findings，无新出境端点。
- **exit≠0（124/1/2）**：helper 把 runner **原始 stderr（L231/233）+ 未扫描 final-message 前 3 行（L235）** 写 stderr——**绕过** L246 出境 scan（**既有缺口**，同步态也有）。async 把这段落进 **harness 托管后台任务输出文件**（新持久化载体）→「后台文件内容=已过 scan」旧断言**在错误路径为假**。**缓解**：collect **只取结构化状态 + exit0 的 stdout findings**，MUST NOT 把后台文件原始 stderr 当 findings 采信；harness 输出文件 TTL/权限/清理归属为**残余待验**（impl 核 harness 捕获语义）〔F-L〕。
- **TOCTOU 已闭**：per-run 不可变 context 路径（并发节 F-G）消除固定路径跨会话覆盖窗。

∴ 安全面**主路径无回归**；错误路径未扫描 stderr 是既有缺口、async 换了持久化载体，已诚实登记 + 编排层不采信兜底。

## Scope-check 表（TG-25 / BASE-29）

| 文件 | helper 协议节 | 本 change 改动 |
|---|---|---|
| `sdflow-spec-review/SKILL.md` | line 263「outside-voice helper 调用协议」 | exec 步加 host 分支（claude=run_in_background dispatch / Step3 collect；codex=同步现状） |
| `sdflow-code-review/SKILL.md` | line 261 同名节 | 同上，措辞逐字对齐 |

守一致：两处 async host 调度段（marker 圈定、站点无关部分）MUST **字节相同**，由 `hack/check_async_branch_parity.py` 机械守（ADR-5，挂 setup.sh + hack/tests）——**非**人工 scope-check。

## Risks / Trade-offs

- [async 编排在 model-driven SKILL、非机械门] → grill/spec-review 压 + SKILL 指令显式列「站点↔task_id」映射 + 降级路径（不可用回同步）。
- [`run_in_background` 在 ship 调 code-review 时可能不可用（Open Q2）] → SKILL 自探能力、不可用回落同步（不假绿）。
- [两 SKILL 重复 helper 协议漂移] → **机械等值门**（ADR-5，非 scope-check 表）；`--apply` 单一源注入留 todo。
- [voice 跑到完成的墙钟/token 成本 + 孤儿跑完未 collect 的完整 token 浪费 + SIGKILL 泄漏 workdir（trap 仅 EXIT）] → 预期代价（换 efficacy），与镜工作重叠不叠加；泄漏是既有缺口 async 放大、记 Cost 不改脚本〔F-H〕。
- [config `--timeout` 无边界 → `--timeout 0` 破坏「≤天花板保证终止」] → 返修校验正整数 + harness 上界，0/负/越界/解析失败回落默认〔F-F〕。

## Migration Plan

- **部署**：改两 SKILL.md → `setup.sh` symlink 即时生效（无需重装；改的是 skill 源、非 hack 脚本）。
- **回滚**：`git revert` 本 change commit；两 SKILL 恢复同步现状，`outside-voice.sh` 从未变 → 零协同风险、无脏状态。

## Open Questions

grill + spec-review（2026-07-18）均收敛，无未决：
1. collect 天花板 → **已决 + spike 证**：async-only 900s（spike 证后台跨 600000ms 上限可达）；Codex/降级同步保留 300s（ADR-3 F-B 矩阵）。
2. run_in_background@ship → **已解（措辞校正 F-E）**：读码强提示 code-review 主 session inline、1.3 自探是实际防线（ADR-6）。
3. DRY → **已决**：两份副本 + 机械等值门（ADR-5）；`--apply` 单一源注入留 todo（tasks §5.2）。
4. collect 机制（F-A）→ **已决**：通知驱动 barrier、非轮询；退出码结构化 envelope（ADR-3）。
5. per-site 完整性（F-C）→ **已决 fold**：declared-sites 机械核（并发节）。
6. 安全错误路径 stderr（DV4）→ **已登记+缓解**：collect 不采信后台文件原始 stderr；harness 输出文件 TTL 残余待 impl 验（Security 节 F-L）。

## Compliance

- 不碰 `sdflow:principles` 托管块、不碰 `outside-voice.sh` 契约、不碰 `anchor_lint` 矩阵——遵守。
- DOC-1（正文即最终态）：本设计正文即最终态，无考古层。
- 设计基准：机械化优先（锚契约机械守 + **per-site 完整性 fold 进机械核 F-C**·declared-sites 门；async 编排残余仍 model-driven、诚实登记）· 目标态导向（不拿 Codex 现状缩 Claude 优化；F-A/B/C 锚目标态返修）· 无界不手搓（harness 原生后台、非手搓进程管理，spike 实证）。
