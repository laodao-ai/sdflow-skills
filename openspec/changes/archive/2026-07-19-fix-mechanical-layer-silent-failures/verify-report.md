---
ship-gate:
  verify: PASS
---

# verify-report — fix-mechanical-layer-silent-failures

**日期**：2026-07-19 · **change**：`fix-mechanical-layer-silent-failures`

## 结论

**PASS**（含 1 条显式登记的已知残余 B14、1 条正当 defer B13）

核验方式：不看复选框、不信 impl-report 措辞，逐条回到脚本源码与测试实跑取锚。
本轮实跑锚：`/usr/bin/python3 -m pytest -q` → **1753 passed, 3 skipped**（112s）；
`hack/check_async_branch_parity.py` → `✅ 2 处 async host 调度段逐字节一致`；
`diff sdflow-init/assets/hack/outside-voice.sh ~/.sdflow/hack/outside-voice.sh` → 无差异。

## 逐需求核对表

### R1 — 截断产出恒为合法 UTF-8（P0）

| 需求/任务 | 代码出处 / 测试名 | 状态 |
|---|---|---|
| 1.1 UTF-8 边界回扫（头段回退 / 尾段跳 continuation），只认 UTF-8 不做编码检测 | `outside-voice.sh:280 utf8_head_trim()`、`:316 utf8_tail_skip()`、`_ov_is_cont`；边界断言 `test_non_utf8_lead_bytes_follow_utf8_semantics_not_sniffing`（`test_outside_voice_utf8.py:131`） | ✅ |
| 1.2 `head -c` / `tail -c` 切点接入回扫结果 | `outside-voice.sh:370-392`（`htrim`/`tskip` → `hlen=half-htrim`、`tlen=half-tskip`）→ `:403 head -c "$hlen"`、`:406 tail -c "$tlen"` | ✅ |
| 1.3 stderr 增补丢弃字节数，MUST NOT 写 context 正文 | `outside-voice.sh:408 OV_TRUNCATED_DROPPED_BYTES=`、`:409 OV_UTF8_BACKSCAN_DROPPED=`（纯计数）；`test_stderr_reports_dropped_byte_counts`（:222）、`test_ascii_truncation_reports_zero_backscan_loss`（:237）、`test_tail_skip_unreadable_file_does_not_pollute_stderr_contract`（:268） | ✅ |
| 1.4 连续切点全覆盖，头尾两段**分别**严格解码 | `test_every_cut_offset_yields_two_valid_utf8_halves`（`test_outside_voice_utf8.py:84`，语料含 ASCII/2B 拉丁/3B CJK/4B emoji，逐切点扫描）+ `test_render_prompt_emits_valid_utf8_when_truncating`（:213，参数化） | ✅ |
| 1.5 纯 ASCII 丢弃 0 字节 | `test_pure_ascii_loses_zero_bytes`（:119）；另有 `test_backscan_never_over_trims`（:109，trim/skip ≤3，防「多切几字节蒙混」） | ✅ |
| 1.6 变异验证：回扫恒返回 0 ⇒ 1.4 转红 | `test_mutation_constant_zero_backscan_turns_the_scan_red`（:95，override 两函数为 `echo 0` 后断言 failures 非空） | ✅ 测试承重已证 |
| 1.7 `secret_scan` 在截断之前扫整文件、无出境回归 | `outside-voice.sh:351 secret_scan "$ctx"` 位于 `:365` 截断分支之前；`test_secret_scan_still_covers_whole_file_before_truncation`（:245） | ✅ |
| 附加（实现期自修，非 tasks 原文）：回扫不可用时 fail-loud 而非静默按字节切 | `outside-voice.sh:376-388`（`backscan_ok=false` → `OV_UTF8_BACKSCAN_UNAVAILABLE=1` + `exit 1`）；`test_backscan_fallback_emits_visible_marker`（:309）、`test_head_trim_reports_failure_not_zero_when_byte_read_fails`（:360）、`test_render_prompt_real_od_failure_reports_backscan_unavailable`（:395） | ✅ 强化 |

### R2 — 父被回收时 runner 子进程必死（P1）

| 需求/任务 | 代码出处 / 测试名 | 状态 |
|---|---|---|
| 2.1 runner 后台启动 + 记 PID + `wait` 取回退出码 | `outside-voice.sh:637-649`（codex 路径）、`:660-666`（claude 路径）：`… &` → `OV_RUNNER_PID=$!` → `wait "$OV_RUNNER_PID"` | ✅ |
| 2.2 清理函数 TERM→宽限→KILL→删 workdir；trap 覆盖 `INT TERM HUP EXIT` | `ov_cleanup()` `:491-545`（`kill -TERM` → 10×0.1s 宽限 → KILL 升级 → 删 workdir）；trap 安装 `:601-608`（先一次合并 trap 兜底，再四条精确覆写） | ✅ |
| 2.3 stderr 记「已终止 runner PID N」 | `outside-voice.sh:511` `echo "outside-voice: 收到 ${src}，终止 runner 子进程 PID=${runner_pid}" >&2`；`test_cleanup_logs_the_terminated_runner_pid_without_context_body`（`test_outside_voice_child_lifecycle.py:425`） | ✅ |
| 2.4 外部 SIGTERM → `ps` 验尸无 ppid=1 残留 | `test_runner_subtree_dies_when_parent_is_signalled`（:170，参数化 INT/TERM/HUP × bash 矩阵）；变异对照 `test_mutation_no_op_cleanup_leaves_an_orphan`（:445，空 cleanup 必须留下孤儿 ⇒ 测试承重） | ✅ |
| 2.5 退出码 0 / 124 / 其他非零经 `wait` 原样透传 | `test_exit_code_zero_passthrough_after_backgrounding`（:662）、`test_exit_code_124_timeout_passthrough_after_backgrounding`（:677）、`test_other_nonzero_exit_code_still_maps_to_one`（:689） | ✅ |
| 2.6 文档显式登记 SIGKILL 残余，MUST NOT 写成「已消除孤儿」 | `design.md` D2 残余表 (a)(b)(c)（:67-77）+ 脚本头部 `:62-74`；机械守 `test_sigkill_residue_is_documented_not_claimed_solved`（:923）、`test_group_kill_fix_is_documented_in_design_without_overclaiming`（:254）、`test_signal_storm_residual_is_documented_as_distinct_from_a_b_c`（:274） | ✅ 登记有机械门看住，非纯 prose |
| 附加：D2.1 组级 KILL 升级 + 自杀风险守卫 + 降级哨兵 | `_ov_pgid_of` `:435`、`_ov_group_kill_decision` `:445`、`ov_cleanup:519-536`（`OV_GROUP_KILL_DEGRADED=1`）；`test_runner_ignoring_term_dies_under_group_kill_escalation`（:221）+ 4 条守卫判定单测（:507/:514/:524/:534）+ `test_group_kill_guard_degrades_instead_of_self_harm_when_timeout_shares_own_group`（:593）+ `test_pgid_of_reads_a_real_process_group_not_mocked`（:544） | ✅ 强化（commit `a45b5fc`） |

### A1 / 收尾

| 任务 | 锚点 | 状态 |
|---|---|---|
| 3.1 `mechanical-gates.yml` 纳入 1.4/2.4 测试，闭 Linux 缺口 | `.github/workflows/mechanical-gates.yml:24-25` matrix `[ubuntu-latest, macos-latest]` + `:47 python -m pytest -q -rs`（全套件，含两个新文件）；实绿 CI run **29674903570**（ubuntu-latest + macos-latest 双 job 均 success；macOS 1752 passed/4 skipped、ubuntu 1749/7）。〔**verify 自纠**：本报告初版锚的是 run `29670376668`，经编排层复核该 run **只有单个 `gates` job**——macOS 矩阵是其后的 commit `497727e` 才加入且当时未推送 ⇒ **macOS 泳道那时一次都没跑过**，原锚属假 ✅，已按实际重跑的 run 更正〕 | ✅ |
| 3.2 开发 checkout 跑 `setup.sh` | `diff sdflow-init/assets/hack/outside-voice.sh ~/.sdflow/hack/outside-voice.sh` 本轮实跑 → **无差异**（拷贝已刷新） | ✅ |
| 3.3 全套件 pytest 绿 | 本轮实跑 `1753 passed, 3 skipped` | ✅ |
| 3.4 `check_async_branch_parity.py` 绿（Non-Goal 守卫） | 本轮实跑 rc=0，`✅ 2 处 async host 调度段逐字节一致` | ✅ |
| 3.5 >200KB 真实中文 context 实跑，记 rc 与 `reason_code` | **本轮独立复现**：拼接本仓 md 造 260000 字节中文语料 → `render_prompt` rc=0，stderr `OV_TRUNCATED_DROPPED_BYTES=55203` / `OV_UTF8_BACKSCAN_DROPPED=3` / `OV_TRUNCATED=true`，产出 206053 字节 prompt **严格模式 UTF-8 解码通过**。端到端 codex 调用 rc=0 + 锚行 `reason_code="ok"` 的记录见 `impl-reports/task3-cross-platform.md:94-116`（未本轮重跑，属真实模型调用） | ✅ |

## Success Metric 逐条核对

### Metric 1 — 跨模型 voice 在超长中文 context 下的成功率（基准 rc=1 必失败 → 目标 rc=0 且 `reason_code="ok"`）

**达成。** 证据分两层：
- **本轮独立实跑**（不依赖任何已有报告）：260KB 真实中文 context 经 `render_prompt` 截断，产出 prompt 严格 UTF-8 解码通过、rc=0、回扫仅多丢 3 字节。这是「runner 报 `input is not valid UTF-8`」这条因果链的**根**被切断的直接证据。
- **机械回归**：`test_every_cut_offset_yields_two_valid_utf8_halves`（全切点 0 失败）+ 变异体转红（`test_mutation_constant_zero_backscan_turns_the_scan_red`）证明该断言承重；ubuntu+macos 两条 CI 泳道实绿（run **29674903570**，见上方自纠注）闭 A1。

### Metric 2 — 孤儿 runner 进程数，目标 0

**三分判定，不整体达成；但达成度与不达成面均被诚实登记 ⇒ 判 PASS + 已登记残余。**

| 路径 | 结论 | 锚点 |
|---|---|---|
| 单信号 INT/TERM/HUP 回收 | **达成**（0 孤儿） | `test_runner_subtree_dies_when_parent_is_signalled`（参数化三信号）+ 变异对照 `test_mutation_no_op_cleanup_leaves_an_orphan` |
| runner 主动 `trap '' TERM` 忽略终止信号 | **达成**（D2.1 组级 KILL 升级） | `test_runner_ignoring_term_dies_under_group_kill_escalation`；commit `a45b5fc` |
| 父进程 SIGKILL | **不达成**，spec 原文即允许的残余 (a) | spec.md「诚实边界」段 + `test_sigkill_residue_is_documented_not_claimed_solved` |
| **高频 × 多类型混合信号风暴** | **不达成，实测 67% 产孤儿** | `design.md` D2.2 (d\*)（:79-93）+ buglist **B14** + `test_mixed_high_frequency_signal_storm_can_defeat_trap_mechanism` |

**(a) 登记是否诚实 —— 我的独立判定：诚实，且是本仓少见的高标准登记。** 依据：
1. **数字原样保留**：`design.md:83` 与 B14 标题、`影响范围` 段均写「**实测 67%**」「15 次跑 10 次」，**没有**出现「极少见 / 偶发 / 可忽略」这类弱化词；`design.md:93` 更把「弱化为极少见」明列为 MUST NOT。
2. **直接承认 metric 未达成**：B14「影响范围」原文 —— 「R2『父被回收时 runner 子进程必死』与 Success Metric 2『孤儿 runner 进程数 = 0』在混合信号风暴下**实测不达成**（单信号路径实测达成）」。**没有把不达成写成达成**。
3. **不与 (a)(b)(c) 混谈**：明确区分「单指令级窄窗口」与「整条 trap 机制被压垮」，并有机械门 `test_signal_storm_residual_is_documented_as_distinct_from_a_b_c` 看住这段文字不被后人稀释。
4. **有对照组**：单一信号同频洪泛 0/10、慢速多类型 0 孤儿 —— 排除了「是 M5/M6 没做好」的替代解释，把引爆点锁在交集上。

**(b) FAIL 还是 PASS —— 我判 PASS。** 理由（按 tasks/specs 原文，非跟随编排层）：
- **spec 的 SHALL 与其配套 Scenario 均已满足**：`specs/outside-voice-exec-integrity/spec.md` 对 R2 给出的三个 Scenario（SIGTERM 后无孤儿 / 退出码不回归 / SIGKILL 残余显式登记）**逐条有实跑测试锚**，无一落空。
- **(d\*) 的失效机理与 spec 明文豁免的 (a) 同族**：两者共同点是「**trap 根本没执行**」——helper 被信号**默认处置**直接终止（returncode 为负），而非 trap 里漏杀。spec 的诚实边界条款豁免的正是「trap 不可执行」这一类。把它判成核心缺口，等于要求本 change 在 bash trap 之外另建回收原语（flock / 外层监督者），那是 **design.md D2.2 明确定性的「设计级决策」**，超出本 change 的授权范围。
- **tasks.md 18 条无一未落实**：(d\*) 不对应任何一条 task，它是实现期由对抗镜**新发现**的面，处置方式为「登记 + 回归用例 + 另开 change」，符合 adr/0018。
- **⚠ 但 Metric 2 的字面「目标 0」在全信号形态下未达成必须显式说出来** —— 已在本节表格与缺口清单中列明，**MUST NOT** 在 hand-off 或归档时被压缩成「Metric 2 达成」。

## 缺口清单

### 核心缺口（FAIL 项）
**无。**

### 已登记残余（诚实性已独立评价）
- **B14 / D2.2 (d\*)** — 高频×多类型信号风暴击穿 trap（67%）。登记**诚实**（见上）。回归用例 `test_mixed_high_frequency_signal_storm_can_defeat_trap_mechanism` 存在，但本轮**未复现故 skip**（skip 文案已警告「勿因常 skip 就删除或撤销登记」）；概率性用例的这种降级不可避免，**Minor**：建议 hand-off 点名「该用例常 skip，非绿即证残余消失」。
- **(a) SIGKILL / (b) PID 记录窗口 / (c) PID 清零窗口（含 D2.1 后爆炸半径放大）** — `design.md:67-77`，三条并列登记 + 机械门守文本，性质为 shell 层不可消除窗口。**接受**。

### Minor 缺口（可接受 / deferred）
- **B13（出境 `secret_scan` 三洞）defer —— 我判 defer 正当。** 依据：① 三洞**均为既有缺口**，非本 change 引入（本 change 只动截断切点与子进程生命周期，两处都在**入境**侧；出境扫描点 `:689` 未被触碰）；② `proposal.md` Non-Goals 明写「**不改出境侧扫描**」，且该条附有可证伪假设，本次并未触发证伪；③ 若 fold，按洞(3)的修法（把 context 复制进受控 workdir、只扫描/渲染私有快照）会**重写整条 render/exec 数据通路**，远超「一个完整阶段结果」的 scope 边界，正是 `change-scope-one-complete-stage-result` 要避免的混装。④ 登记质量高：三洞根因**分治**（扫描点位置 / 检测器 fail-open / 对象同一性 TOCTOU）、各带修复方案与行号锚，并已在 buglist 明写「须在 hand-off 点名」。
  **⚠ 硬要求**：B13 是 **P1 安全项且两个独立镜判 critical**，hand-off **MUST 点名**，**MUST NOT** 随归档静默沉底；建议尽快开一个专门 change（与 B14 的设计级 change 可分可合）。
- **3.5 的端到端 codex 调用未本轮重跑**（真实模型调用有成本）。其 rc/`reason_code` 锚来自 `impl-reports/task3-cross-platform.md:94-116`。**可接受**：该链路的**因果根**（prompt 字节合法性）已由本轮独立实跑 + 全切点扫描测试双重坐实。

PASS —— tasks.md 18 条逐条有可机验锚点（源码行 + 测试名 + 实跑输出 + CI run 29674903570），全套件 1753 passed，两条机械门绿，Metric 1 本轮独立复现达成；Metric 2 在单信号与「runner 忽略 TERM」两条路径达成，混合信号风暴路径**不达成但登记诚实、不属 spec Scenario 覆盖面、修法属设计级**，故判已登记残余而非核心缺口；B13 defer 有 Non-Goal 与 scope 双重正当性，但须在 hand-off 显式点名。
