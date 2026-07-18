## Why

评审工作流的跨模型 outside-voice 用 `outside-voice.sh exec` **同步阻塞主 session**（外层 Bash 超时须 ≥330s）。真实评审负载下 voice（`claude -p` / `codex exec`）推理时长 >300s，被外层超时杀 → 降级同族 fallback，跨模型第二意见 **efficacy=0**（`add-codex-host-support/codex-e2e-efficacy-report.md` 实测 Codex 宿主 3/3 timeout；Claude 宿主调 codex 方向亦经用户实证超时）。根因经 spike 实证**不是 timeout 设太小**（默认 300s、2.5× smoke 仍系统超时），而是 voice 真实推理时长本身超过任何可接受的同步阻塞窗口——∴ 同步阻塞模型本身错。

## What Changes

- 评审 SKILL（`sdflow-spec-review`、`sdflow-code-review`）的 outside-voice exec 改为**宿主自适应 dispatch 模式**：
  - **Claude 宿主**：主 session 用 harness 原生 `run_in_background` 派 voice exec（秒返），继续 fan-out 镜等其余评审工作，Step3 综合时 collect。voice 后台跑到完成、与镜工作重叠，不再被外层超时杀。**赢的是 efficacy（拿到真跨模型第二意见），不是速度。**
  - **Codex 宿主**：保持同步现状（后台化在 Codex 上架构性不可行——spike 实证 codex 每条 shell 命令返回即回收该命令 spawn 的一切本地进程，`nohup` + `setsid` 新会话皆秒死；且 codex 无生产可用后台原语）。超时仍→同族 fallback，明牌接受边界。
- collect 是**通知驱动 barrier**（非轮询，F-A）：完成推送异步到达即暂存该站点，Step3 每 dispatch 站点结果按**结构化退出码** envelope 分支（撞天花板 exit124/未完 → 同族 fallback `reason_code="timeout"`）。天花板 = 调大既有 `--timeout`（**仅 async 分支** 900s，Codex/降级同步保留 300s，F-B），caller flag、脚本不改。**锚行/reason_code 契约完全不变**，`anchor_lint` 矩阵零改动；per-site 完整性由 declared-sites 机械核守（F-C）。
- `outside-voice.sh` 脚本本体、四旗承重墙、出境安全三件套**一字不改**（后台生命周期交给 harness，非脚本自管）。

## Capabilities

### New Capabilities
（无——本 change 不引入新能力，是既有能力的行为增补。）

### Modified Capabilities
- `host-adaptive-execution`: ADD 一条需求——outside-voice exec 的 **dispatch 模式 SHALL 宿主自适应**（Claude=off-critical-path 后台、Codex=同步），MUST NOT 改变锚行契约与出境安全不变式；voice 未按 deadline 完成时 SHALL 保持既有诚实降级（同族 fallback、`reason_code="timeout"`），MUST NOT 假绿。

## Impact

- **改**：`sdflow-spec-review/SKILL.md` + `sdflow-code-review/SKILL.md` 的「outside-voice helper 调用协议」节（编排层，纯 Markdown）。
- **不改**：`sdflow-init/assets/hack/outside-voice.sh`（契约脚本 + 四旗承重墙）、`anchor_lint`/`outside_voice_guard`/`lens_metric_emit`（锚契约不变）。
- **新机制**：仓内首次使用 harness `run_in_background`（此前无先例）。
- **新增**：`hack/check_async_branch_parity.py` + `hack/tests/`（async 段字节等值机械门，ADR-5/F-O）、`setup.sh` 挂该检查；**per-site declared-sites 机械核**（补 anchor_lint 家族级盲区，F-C；declared = 该层「**应有锚**站点集」非「应 dispatch 集」，**优先实现为 `anchor_lint` 附加校验**并复用其 `fence_outside_lines` 口径，G1/G4）；**per-run 不可变 context 路径** `.outside-voice/<run-id>/<site>-context.md`（F-G，父目录须留在 `.outside-voice/` 下以承既有 gitignore 覆盖，G5）；collect 天花板 config 键（async 900s / sync 300s，**SKILL 直读 config.yaml** 沿 metrics.enabled 先例 + 正整数校验，F-B/F-N/F-F）。
- **并发面（TG-26）**：Claude 宿主下多个 voice（design-voice、hr-tg）+ fan-out 镜后台并发；共享状态按站点分文件（`.outside-voice/<site>-context.md`）+ 按任务分后台输出，collect/merge 在单一主 session Step3——需 design 显式论证无数据竞争。

## Success Metrics

- Claude 宿主跑一次真实评审，outside-voice 锚 `reason_code="ok"`（真跨模型 findings 进池），**而非** `reason_code="timeout"`（降级同族）——efficacy 从 0 恢复到非零。
- 主 session 不再有 ≥330s 的单次阻塞 Bash 调用（dispatch <1s 返回）。
- 锚契约回归：`anchor_lint` 全笛卡尔 golden 不变即绿（本 change 不碰矩阵）。
- **负向断言（F-K）**：Codex 宿主方向 `reason_code` **仍是 `timeout`（efficacy 仍 0）**——非回归、是已知未解范围（Non-Goals）；本 change 只恢复 Claude 宿主方向。
- **近天花板（F-J）**：smoke MUST 覆盖 voice 时长逼近 900s 场景（验后台过 600000ms 外层上限存活），非侥幸 <600s 完成即判绿。

## Non-Goals

- **不改** `outside-voice.sh` 脚本本体（骨架里 dispatch/collect + jobdir 生命周期 + TTL sweep 因 harness 托管而全不需要）。
- **不解** Codex 宿主方向的 efficacy=0（架构性无解，另记 todo：等 codex `deferred_executor` 稳定 / 或建外部 claude daemon 再议）。
- **不改**锚行契约 / `anchor_lint` 合法组合矩阵 / 出境安全三件套。
- 归档勘误已在 commit `88c56d3` 完成，非本 change。

## Open Questions

（TG-21，负责人/截止在 grill/spec-review 收敛）
1. **collect barrier 语义**〔grill 已决 + spec-review/接缝复审校正，见 design ADR-3〕：deadline = 调大既有 `--timeout` 天花板（**仅 async 分支** config 默认 900s、Codex/降级同步保留 300s（F-B）、脚本不改）；Step3 以**通知驱动 barrier**（**非轮询**，F-A）collect、按**结构化哨兵 envelope** 取退出码分支（G2），站点仍 RUNNING 则让出轮次等终态通知、`timeout` 只由**实测 exit 124** 产生（G3）；不新造 deadline 机制、不设 early-grace 回落（early 回落把长尾还给 efficacy=0）。
2. **run_in_background 在 ship 路径可用性**〔grill 已解，见 design ADR-6〕：读 ship 机制——ship 是主 session 编排器（line 96「不直接派子代理」）、`RUN_CODE_REVIEW→/sdflow-code-review` 为主 session inline 调用，code-review 跑在主 session（其 fan-out 镜才是子代理），∴ voice exec = 主 session Bash 调用 = A1 spike 已证 run_in_background 存活的同一上下文（**F-E 校正**：line 101 那句 inline 绑的是 tickets-plan、非 `RUN_CODE_REVIEW`，结论靠 line 96/80 通用陈述推出）。∴ 读码**强提示**、A2 大概率成立；task 1.3 自探是**当前验证 A2 的实际防线**（非兜底冗余），不假绿。
3. **DRY**〔grill 已决，见 design ADR-5〕：两份副本 + **机械等值门**（marker + `hack/` 字节等值检查，沿用 sync_principles idiom）守一致；长期全抽取（单一源注入）超 scope，留 todo（tasks §5.2）。

## Assumptions

（TG-22，失效影响）
- **A1**：Claude 主 session 的 `run_in_background` 后台进程跨 tool call 存活、可 collect、**且能存活过 Bash 外层 600000ms 上限到 900s 量级**。**已 spike 实证**（2026-07-18：① 进程跨 tool call 存活跑完；② **边界 spike——后台任务跑满 660s、跨 600000ms 外层上限、exit 0、ppid 稳定不 reparent**，证 600ms 上限不管后台、900s 可达、harness 托管生命周期）。**残余待 impl 验（F-L）**：harness 后台**输出文件**的 TTL/权限/清理归属（A1 验的是进程存活、非输出文件生命周期）。失效影响：async 不可行、回落同步——方向已验，风险低。
- **A2**：`sdflow-code-review` 经 `sdflow-ship` 调用时其执行上下文也有 `run_in_background`。**已解**（grill：ship `SKILL.md` line 96/101 证 code-review 跑主 session inline、非子代理 → 与 A1 同上下文，run_in_background 存活由构造成立；见 design ADR-6）。task 1.3 自探兜底未来若 ship 改子代理派发的漂移；不假绿。
- **A3**：Codex 宿主后台化不可行是稳定事实。**已 spike 实证**（codex 每命令回收进程组，nohup+setsid 皆死）。失效影响：若未来 codex 改变此行为，Codex 方向可另立项救，不影响本 change。

## Cost

（TG-24 轻量）voice 跑到完成消耗完整 token（对比被 330s 杀的部分消耗）——恢复 efficacy 的**预期代价**，非新增计费；每轮多等一个后台 voice 墙钟、与镜工作重叠不叠加。**async 新增两项已知代价（F-H，登记非消除）**：① 孤儿 voice（评审中止 dispatch 后未 collect）跑完的完整 token 浪费；② `outside-voice.sh` 的 `trap` 仅 EXIT、不含 INT/TERM → SIGKILL 泄漏 workdir（含 prompt.md）在 /tmp，900s 天花板三倍化该窗——既有缺口、async 放大，不改脚本（Non-Goal），per-run 路径 + harness 托管缩小实际暴露。

## Compliance

N/A（本 change 不涉及数据合规 / 跨产品边界 / 外部法规）。
