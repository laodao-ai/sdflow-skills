# Task 3 实现报告 — 中断恢复与 identity-safe 清理

**票**：Task 3（R-ID: OVBG-03, OVBG-05）· **Blocked-by**: 2（HEAD 起点 `7dd071e`）
**改动文件**：`sdflow-init/assets/hack/outside-voice-job.py`（+~530 行）·
`sdflow-init/tests/test_outside_voice_job.py`（+~520 行，245 → 283 条）

## 做了什么

在 Task 1/2 已有的盘面之上加两个子命令，并把 Task 2 双轴审留下的三条硬交接落地：

| 新增 | 角色 |
|---|---|
| `cleanup --run-dir --site [--cancel] [--subtree-wait]` | **单站点 identity-safe 清理**：四项 identity 重新核验 → 分支到 `rm` / `stop→子树核验→rm` / 拒绝 / orphan warning |
| `reconcile --run-dir <exact> [--site] [--subtree-wait]` | **abandoned run 的显式恢复入口**：站点只从本 run-dir 自己的 metadata 枚举，先 collect 落袋再决定清不清 |
| `probe_subtree` / `wait_subtree_exited` | worker + inner child 进程子树的**三值**核验（exited / alive / unverifiable） |
| `verify_identity` / `load_roster` | canonical id · repo · site · attempt 四项交叉核验（盘面 witness + roster 命令串两个独立信号源） |
| `_lost()` | LOST 的**唯一**构造口，三条产生路径共用 ⇒ `unknown_cost` / `orphan_warning` 不会漏翻某一条 |
| `run_collect()` | 从 `cmd_collect` 抽出的核心，CLI 与 reconcile 共用**同一条**实现路径（不长第二份） |

### 关键设计判断（含与 spec 的对照）

1. **`unknown_cost` 的翻转点放在纯派生层，子树探针放在 cleanup 层。**
   `derive_status` 保持「盘面 + liveness 纯派生」不变（不引入进程探针，笛卡尔表仍确定性）；
   LOST 的定义就是「rc 缺席 ⇒ 无 terminal witness」⇒ **纯派生阶段没有任何证据能证明子树已退出**
   ⇒ 一律 fail-closed 翻 `unknown_cost=true` + `orphan_warning`。**解闸的唯一途径**是
   `cleanup`/`reconcile` 真去探进程树，核验通过后返回 `fallback_allowed=true`。
   这与 OVBG-03 原文一一对应：「只有在 identity 与子树退出**均可核验**时才 SHALL 停止/移除
   已知 job 并归约为 exec-error；无法证明子树已退出时 SHALL 标记 unknown-cost/orphan-warning
   并抑制自动 fallback」。

2. **子树核验用「pid + 进程组 + terminal witness」三段，不改 worker 的 spawn 语义。**
   曾考虑让 worker `os.setsid()` 以保证 `pgid == pid`（让 killpg 永远是精确的子树信号）——
   **否掉了**：那会让 worker 脱离 supervisor 的进程组，`claude stop` 很可能就杀不到它，
   等于为了让核验好看而把 OVBG-05 的 stop 路径打断。改为**诚实三值**：组长时 killpg 是直接
   答案；非组长时退到 terminal witness（`subprocess.call` 同步 ⇒ 走到发布点意味着 child 已被
   wait 回收）；两者都没有 ⇒ `unverifiable`，落 orphan warning。**「不可证」不折算成「已退出」。**

3. **`verify_identity` 的判据是「有没有矛盾」，不是「有没有全部拿到肯定答案」。**
   真机上 `state="done"` 的 roster 条目**没有 `name` 字段**（Task 1 实测），若要求四项都
   positively verified，正常完成的 job 就永远 `rm` 不掉——那会把「不猜目标」写成「什么也别做」。
   故 `unavailable`（信号缺席）不阻塞，`fail`（信号相互矛盾）一票否决，且 `canonical-id`
   额外要求**唯一命中**才放行破坏性调用。

4. **`--run-dir` 是 `required=True`，全脚本没有任何「找最新 run」的代码路径。**
   站点枚举只走 `discover_sites()`（只 `os.listdir` 本 run-dir 的 `*.job.json` / `*.reserve`），
   **不**从 supervisor roster 反向取站点——那会碰到未持有 metadata 的他人 job。

5. **`probe_liveness` 加 repo 交叉核验（`expect_cwd`），矛盾时降级为 `unavailable` 而非 `missing`。**
   `missing` 属 `LIVENESS_TERMINAL`，会把还在飞的合法 worker 当场判 LOST；cwd 对不上只说明
   「这条探针没有判别力」，MUST NOT 拿它触发降级。

6. **清理闸门按 `PENDING_STATES` 划，不按 `!= LOST` 划**（实现中途自查改掉的一处）。
   终态但无可用 rc 的形态不止 LOST——rc 不可解析的 `CORRUPT` 同样永远等不到 rc。写成
   `!= LOST` 会把它报成「站点仍在飞」（一句假话），并让那个 job 被永久挂起：既不清理，
   也永远等不到终态。锚：`test_reconcile_treats_a_terminal_but_rc_less_corrupt_site_as_cleanup_not_pending`
   （反向变异回 `!= LOST` ⇒ **RED**）。

## 每条验收标准的机械锚

| # | 验收标准 | 机械锚 |
|---|---|---|
| 1 | 外层 await 被回收后，同一主评审 session 用保留的 exact job/run-dir 恢复 collect，结果不丢且不重新派发 | `test_reclaimed_await_recovers_by_collect_without_a_second_dispatch` —— 真 dispatch → `await --max-wait 0.3` 被回收（`terminal is False`）→ worker 继续跑到 rc → `collect` 拿到 SUCCEEDED + 真实 stdout；**锚 = `len(_bg_invocations(fake_claude)) == 1`**（fake `claude` 的调用日志，非实现自述） |
| 2 | 评审 session 整体丢失时禁止扫描「最新目录」，只接受显式 `reconcile --run-dir` | `test_reconcile_requires_an_explicit_run_dir`（无 `--run-dir` ⇒ exit 2）+ `test_reconcile_never_reaches_into_a_sibling_or_newer_run_dir`（两个同级 run，**站点名刻意不同**；断言 sites 列表、`_destructive` 只含旧 run 的 id、新 run 的 id 全日志零出现）+ `test_reconcile_ignores_supervisor_jobs_it_holds_no_metadata_for`（roster 3 个 job，只动持有 metadata 的那 1 个） |
| 3 | terminal 结果**已 collect 后**才清理 roster；`status/stop/rm` 前重新核验 canonical id / repo / site / attempt，核验失败只告警不猜目标 | 顺序：`test_cleanup_refuses_to_remove_a_terminal_site_before_it_was_collected`（`state="not-collected"` + `_destructive == []`）· `test_cleanup_removes_a_collected_terminal_site_from_the_roster`（`_destructive == [("rm","75d34378")]`）。identity：`test_cleanup_refuses_every_destructive_call_when_identity_does_not_verify` **5 参数化**（repo 不符 / id 不唯一 / 命令串 site 不符 / 命令串 nonce 不符 / 盘面 witness 属另一 attempt）—— **五格全断言 `_destructive(fake_claude) == []`**。status 侧：`test_status_liveness_probe_degrades_when_the_roster_entry_belongs_to_another_repo` + 正向对照 `..._accepts_a_roster_entry_whose_cwd_matches_repo_root` |
| 4 | 取消/失联按 `stop → 核验子树已退出 → rm`；不可证时落 orphan warning 并抑制自动 fallback | `test_cleanup_cancel_order_is_stop_then_subtree_verification_then_rm` —— **真起一个被 init 收养的进程**当 worker identity，fake `claude stop` 真把它杀掉；断言 `_destructive == [("stop", id), ("rm", id)]`（顺序）+ `subtree == "exited"` + `fallback_allowed is True`。负向三条：`..._when_the_subtree_survives_stop`（真活进程 ⇒ `orphan-warning` / `removed False` / `unknown_cost True` / `fallback_allowed False` / `_destructive == [("stop", id)]`）· `..._when_the_subtree_exit_cannot_be_proven`（无 started witness ⇒ `unverifiable`）· `test_cleanup_does_not_rm_when_stop_itself_failed` |
| 5 | 清理失败不改写已取得的 rc、不删除本轮 run-dir 审计证据 | `test_cleanup_failure_never_rewrites_the_rc_or_deletes_run_dir_evidence` —— `FAKE_CLAUDE_RM_MODE=fail`，断言 **run-dir 全部文件的字节内容逐一不变**（`after == before` 的 dict 比较），且清理失败后再 collect 仍是 `(True, "SUCCEEDED")`（已成功的 findings 不被改判） |

进程探针本身对**真内核**取答案：`test_pid_and_pgid_probes_answer_from_the_real_kernel`
（活进程 / 确定已死的 pid / 非法输入三值）+ `test_probe_subtree_*` 四条（alive / exited /
unverifiable-无 witness / 共用进程组两分支）。

## 三条硬交接的落地位置

| 交接（来自 `task2-review.md`） | 落地 |
|---|---|
| ① **LOST 路径 MUST 翻 `unknown_cost` / orphan-warning**，否则 Task 5 无可 gate 的字段 | `_lost()`（`outside-voice-job.py`，LOST 的唯一构造口）+ `_status_payload` 新增 `orphan_warning` 键。锚：`test_every_lost_verdict_flags_unknown_cost_and_an_orphan_warning`（**三条 LOST 产生路径逐条**：liveness 终态 / startup deadline / started+timeout+grace）+ 正向对照 `test_states_other_than_lost_and_reserved_never_raise_a_false_orphan_warning`（防「全都标 orphan」的假绿）。**Task 5 的 gate 字段 = `unknown_cost`**，模块 docstring 已把这条写进契约单一源 |
| ② `<site>.collected.json` 是第 6 个 sidecar，reconcile 需知其存在（terminal 已 collect 过可直接 `rm`） | `run_cleanup()` 用 `load_collected(...)[0] == "ok"` 作为 `rm` 的前置闸；已 collect ⇒ 直接 `rm`（不 stop）。锚：`test_cleanup_removes_a_collected_terminal_site_from_the_roster`（`stopped is False`, `removed is True`） |
| ③ 无 rc 的终态不再冻结 ⇒ **这正是留给 reconcile 修正的面** | `reconcile_site()` 的第一步就是「rc 已发布就 `run_collect`（幂等）」，先落袋再谈清理。锚：`test_reconcile_recovers_a_result_that_landed_after_a_lost_verdict` —— 先 collect 判 LOST（`collected.json` 不落盘），worker 随后真发布 rc=0，reconcile 拿到 `SUCCEEDED` 且落盘的 digest 等于**新** stdout 的 sha256 |

## 反向变异实测（判据不是「新增了测试」，是「改错了会不会红」）

在隔离副本上把实现改回错误形态逐条跑（仓内文件零残留，每轮跑完 `cp` 还原；脚本
`scratchpad/mut.py` / `mut2.py`）：

| # | 变异 | 结果 |
|---|---|---|
| M1 | `_lost` 不翻 `unknown_cost`/`orphan_warning` | **RED**（1 failed） |
| M2 | 子树「不可证」当「已退出」 | **RED**（3 failed） |
| M3 | `verify_identity` 的 `failed` 恒空（永远放行） | **RED**（4 failed / 1 passed，见下） |
| M4 | 未 collect 也 `rm` | **RED** |
| M5 | 子树仍存活也 `rm` | **RED** |
| M6 | `discover_sites` 顺带扫父目录（= 摸到「最新 run」） | 初版 **绿 → 已修测试** → **RED**（见下） |
| M7 | `probe_liveness` 忽略 repo 交叉核验 | **RED** |
| M8 | reconcile 跳过 collect 直接清理 | **RED**（2 failed） |
| M9 | 未到 deadline 的在飞站点也被 stop | **RED** |
| M10 | `stop` 失败后仍继续 `rm` | **RED** |
| M11 | `_status_payload` 默认 `unknown_cost=True`（「全标 orphan」的假绿形态） | **RED** |
| M12 | `probe_subtree` 恒返回 `unverifiable`（反方向） | **RED**（3 failed） |
| M13 | `discover_sites` 只返回第一个站点 | **RED** |
| M14 | 清理失败时删掉 `collected.json` 证据 | **RED** |
| M15 | roster 已无此 job 时仍走 `rm`（幂等路径消失） | **RED** |
| M16 | 清理闸门写回 `state != LOST`（CORRUPT 被报成「仍在飞」） | **RED** |

**M6 是本轮唯一真被照出来的测试缺陷**：初版 `test_reconcile_never_reaches_into_a_sibling_...`
把两个 run dir 的站点都写成 `design-voice` ⇒ 「扫了父目录」与「没扫」产出**同一份**站点集合
（`set` 去重），断言恒真。已改成 sibling 用 `hr-tg`，变异复跑 **RED**。测试 docstring 里
写明了这条陷阱，防后来者改回同名。

**M3 的那 1 个幸存者**是 `duplicate-id` 参数格：它被 `verify_identity` 的**第二道**闸
（`canonical-id` 必须唯一命中）挡住，属**冗余防御**而非漏洞——已单独 `-v` 复跑确认幸存者
就是它，另外 4 格全红。

## 测试结果

- 本文件：`/usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_job.py -q`
  → **283 passed in 82.01s**（基线 245，新增 38）
- 全量：`/usr/bin/python3 -m pytest -q`
  → **2433 passed, 8 skipped, 3 xfailed in 232.00s**
  （基线 2395 passed / 8 skipped / 3 xfailed，增量恰为新增的 38 条，**零回归**）

## 未做 / 降级项（如实报告）

1. **`status` 未接入完整的四项 identity 核验，只加了 repo 维度的交叉核验。**
   依据：`design.md` 原文是「任何 `status/stop/rm` 在**破坏性操作前**都必须重新核验」——
   `status` 不做任何破坏性操作，且它已在**每一次**派生里重新核验盘面 identity
   （`load_witness` 逐个核 site / run_id / attempt nonce，Task 2 已有锚）。本票补上的是
   缺失的 repo 维度（`probe_liveness(expect_cwd=…)`）。**若评审认为 spec 要求 `status`
   也走完整四项（含每次拉 roster 交叉核验 site/nonce），这是一处可判缺口**——代价是每次
   `status`/每轮 `await` 都多一次 `claude agents` 冷启动，与 Task 2 刚修的「liveness 探针
   独立节流」直接冲突，故没有自作主张扩大。
2. **`test_probe_subtree_reports_alive_when_the_group_still_holds_a_child` 用 monkeypatch，
   不是真进程。** 真实构造「组长已死但组内仍有活口」需要一个仍以死者 pid 为 pgid 的活进程，
   本机无法确定性摆出来。两个 syscall 探针本身对真内核有独立锚
   （`test_pid_and_pgid_probes_answer_from_the_real_kernel`），此处只钉判定逻辑。诚实降级。
3. **`_dead_pid()` 存在极低概率的 pid 回绕误差**（拿到的 pid 在断言前被系统复用）。已做
   `PermissionError → pytest.skip` 的兜底；进一步完美化（pid namespace / 进程句柄）成本
   远高于收益，按④简化不做。
4. **本票范围外未动**：`outside-voice.sh` 的 isolation flags 与 `claude logs` canary（Task 4）·
   `setup.sh` 安装快照与两份评审 SKILL 的调度段（Task 5）· 真实 efficacy（Task 6）。
   `superpowers-plan.md` 复选框**未勾**、未打 `task3-` 完成标签、`proposal/design/specs/tasks.md`
   **零改动**（`git status` 亲验：本次只改两个文件）。

## Concerns（交给编排层裁决）

- **C1（Task 5 必读）**：`unknown_cost=true` 现在会出现在**每一个** LOST 站点上，而 Task 2
  之前 LOST 是「直接 exec-error + 允许 fallback」。⇒ **Task 5 的 SKILL 侧分支必须显式处理
  `unknown_cost`**：命中即 MUST NOT 自动同族 fallback，改为报出 orphan warning + 提示跑
  `cleanup --cancel`。若 Task 5 沿用旧的「LOST ⇒ fallback」写法，本票的抑制就被绕过去了。
  这是 spec 要求的行为变化，不是回归。
- **C2**：`cleanup` 的 `rm` 前会**再拉一次** roster 做第二次 identity 核验（`stop` 前一次、
  `rm` 前一次），单次 cleanup 最多 3 次 `claude agents` 冷启动（~0.5s）。取消路径是低频
  人工动作，没有做缓存；若 Task 6 真机实测嫌慢，可把两次核验合并为一次（代价：stop 与 rm
  之间 roster 变化窗口不再被覆盖）。
- **C3（继承 Task 2 的 T217）**：`parse_utc_iso` 的宽 `except Exception` 吞噬面仍在，本票
  新增的 `probe_subtree` / `verify_identity` 都调用了 `load_witness`（其内部依赖它）。
  未在本票扩大修复范围（属既有 defer 项）。
