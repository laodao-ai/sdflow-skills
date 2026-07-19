# code-review-fix1 — outside-voice.sh 代码审返修

对象：`sdflow-init/assets/hack/outside-voice.sh`（1.4.2 → **1.4.3**）。
背景：代码审五镜（含两个跨模型 codex voice）咬出「exit 0/成功措辞，但事情没做成」的 6 处必修
（M1–M6）+ 2 处必登记（R1/R2），均已由编排层独立核实成立。本轮逐条返修 + 补测试锁 + 变异验证。

版本号已从 `1.4.2` 升至 `1.4.3`，`test_outside_voice.py::test_version` golden 已同步更新
（含各条修复的简述）。开发 checkout 已跑 `bash setup.sh`（symlink，改源即时生效；`~/.sdflow/hack/
outside-voice.sh` 已随之更新）。

## M1 — 回扫不可用必须 fail-loud 非零

**改法**：`render_prompt()` 结构性重排——回扫可用性检查（`backscan_ok`）移到【任何 stdout 内容
写出之前】。检查失败 ⇒ 打印固定诊断 + `OV_UTF8_BACKSCAN_UNAVAILABLE=1` ⇒ `exit 1`，不产出任何
prompt 内容、不进入 head/tail/cat 分支。`do_exec` 既有的「render_prompt 非零即 exit」逻辑保证
runner 不会被启动。

**退出码选择**：复用 `exec` 契约里已有的通用非零桶「1」（该桶本就是"多种失败原因共用同一退出码
+ stderr 区分"的既有风格，如 timeout 缺失/runner 未设/等）；同时把这条原因加入 `render-prompt`
子命令自己的契约表（此前只有 0/2/3，现新增 1）。头部契约注释已同步更新（两处：exec 段的退出码表、
render-prompt 段新增说明行）。

**测试锁**：
- `test_backscan_fallback_emits_visible_marker`（mock 回扫函数）— 已更新断言：`returncode != 0`、
  `OV_UTF8_BACKSCAN_DROPPED=`/`OV_TRUNCATED=` 均不出现（证明确实在任何"继续截断"输出之前就退出）。
- `test_render_prompt_real_od_failure_reports_backscan_unavailable`（真 od 二进制失败，端到端）—
  已更新断言：`returncode != 0`、`stdout == b""`。

**变异验证（手工，已实跑）**：构造一份把 M1 fail-loud 还原成旧版"打哨兵后仍兜底 htrim=0/tskip=0
继续截断"的 mutant，跑上述两条测试：

```
FAILED test_backscan_fallback_emits_visible_marker
  AssertionError: assert 0 != 0  （旧版 rc=0，新断言要求非 0）
FAILED test_render_prompt_real_od_failure_reports_backscan_unavailable
  AssertionError: M1 复发：od 真实失败却仍 exit 0 ... assert 0 != 0
```

两条测试均按预期转红，mutant 已删除。

## M2 — `_ov_bytes_at` 核验真实 od 返回码 + 收到字节数/取值范围

**改法**：
- `_ov_bytes_at()` 改为先用命令替换单独捕获 `od` 本身的输出与【它自己的】返回码
  （`raw=$(od ...) || return 1`），格式化步骤（`tr`/`grep`）的成败不再冒充 od 的成败。
- 新增 `_ov_read_bytes_strict()`：在 `_ov_bytes_at` 成功的基础上，额外核验收到的字节数
  **严格等于**请求的 `count`、且每项在 `0..255`；任一不满足 ⇒ 输出空、返回 1。
- `utf8_head_trim`/`utf8_tail_skip` 改用 `_ov_read_bytes_strict`，取失败仍输出空串（F-新1 既有
  契约不变）。

**测试锁 + 变异验证（均已实跑，绿）**：
- `test_ov_bytes_at_propagates_real_od_exit_code_not_pipeline_tail`：塞一个"先吐 2 字节再
  `exit 1`"的假 `od`，断言 `_ov_bytes_at` 返回 `RC=1`；变异对照（还原成旧管道实现）同一输入下
  `RC=0`——证明断言确实由"单独捕获 od 返回码"这个修复点承重。
- `test_ov_read_bytes_strict_rejects_partial_output_even_when_producer_reports_success`：
  mock `_ov_bytes_at` 返回 2 个字节但自称 `rc=0`（请求 3 个），断言 `_ov_read_bytes_strict`
  判定 `RC=1`；变异对照（重现旧版"只查完全为空"判据）同一输入下 `RC=0`。
- `test_ov_read_bytes_strict_rejects_out_of_range_values`：越界字节值（999）判定失败。

## M3 — 关键写入逐项核验返回码 + do_exec 侧磁盘写满不依赖磁盘的兜底诊断

**改法**：
- `render_prompt()` 内 `emit_frame`/两处空行/BEGIN·END 横幅/`head`/`tail`/`cat` 全部加
  `|| { echo "OV_RENDER_WRITE_FAILED=1 stage=..." >&2; exit 1; }`。
- `do_exec()`：子壳执行 `render_prompt` 后，若 `rc != 0` **且** `$workdir/render.meta` 为空
  （即上面那些写入自己也失败到没留下任何诊断），补一条**不经过 workdir 磁盘路径**、直写
  本进程真实 stderr 的固定诊断行：
  `outside-voice: render_prompt 非零退出(rc=...)——诊断文件为空（疑似 workdir 所在磁盘写满/
  写入失败），无法给出更详细原因`。

**真实复现（对抗镜 B 的 2MB ramdisk 手法，本轮独立复现）**：用 `hdiutil` 建 2MB HFS ramdisk，
精确填到仅剩 ~4–8KB 可用空间，`TMPDIR` 指向该卷后跑 `exec`。对照组用 `git show HEAD:...` 取出
的**真实改动前**脚本（非推测/模拟）在同一块新建 ramdisk 上跑同样条件，实验组用当前已修复脚本
在另一块同规格新建 ramdisk 上跑：

```
[PRE-FIX  · git HEAD 原始 1.4.2]
target=10000 avail_now=8192 rc=1 stdout_bytes=0 stderr_bytes=0     ← 零诊断信息（原病）
target=8000  avail_now=4096 rc=1 stdout_bytes=0 stderr_bytes=0
target=6000  avail_now=4096 rc=1 stdout_bytes=0 stderr_bytes=0

[POST-FIX · 当前 1.4.3]
target=10000 avail_now=8192 rc=1 stdout_bytes=0 stderr_bytes=154
target=8000  avail_now=4096 rc=1 stdout_bytes=0 stderr_bytes=154
target=6000  avail_now=4096 rc=1 stdout_bytes=0 stderr_bytes=154
stderr 内容：outside-voice: render_prompt 非零退出(rc=1)——诊断文件为空（疑似 workdir 所在
磁盘写满/写入失败），无法给出更详细原因
```

**自动化回归**：`test_exec_disk_full_render_meta_gets_unconditional_stderr_diagnostic`
（`test_outside_voice_utf8.py`）——用两块**独立**的全新 ramdisk（避免同一块小容量卷反复
churn 造成的碎片化漂移，已实测过"复用同一块盘二次填充会导致第二次连 `mktemp -d` 都失败"的
陷阱并改用双卷方案规避），一块跑当前修复版确认非空诊断，另一块跑"摘掉兜底诊断"的 mutant
确认 stderr 变回全空。macOS `hdiutil` 专属，非 Darwin/无权限环境显式 `pytest.skip`。
运行 3 次确认稳定通过，且已验证测试结束后 ramdisk 设备正确 detach（`umount -f` 挂载点 +
`hdiutil detach -force` 兜底，解决了"新挂载卷被 Spotlight 短暂持有导致 detach 报告成功但
实际未卸载"的 macOS 特有陷阱）。

## M4 — kill 失败不得宣称成功

**改法**：`ov_cleanup()` 的 KILL 升级步（无论组级还是单 PID）后，追加一轮复探（`kill -0`，
同样 ~1s 宽限轮询）。复探仍存活 **或** kill 本身返回非零 ⇒ 打 `OV_KILL_FAILED=1 pid=... target=...
kill_rc=... still_alive=...`（结构化字段，无 context 正文），**MUST NOT** 打印"已 SIGKILL 兜底"；
仅当复探确认目标真的消失且 kill 返回码为 0 时才打印成功措辞。

**测试锁 + 变异验证（已实跑，绿）**：`test_ov_cleanup_reports_kill_failed_when_target_survives_kill`
——mock `kill` 使其对目标 PID 的 `-TERM`/`-KILL` 全部"报告成功但不做任何事"（`-0` 探活透传给真
`kill`），用一个真实存在、测试自己控制生死的 `sleep 300` 作为目标：断言打印 `OV_KILL_FAILED=1
pid=<pid>`、且不出现"已 SIGKILL 兜底"；变异对照（还原成旧版"kill 后无条件宣称已兜底"）在同一
仍存活的目标上确认会谎报成功。

## M5 — `ov_cleanup` 重入加固

**改法**：函数体第一条语句改为 `trap '' INT TERM HUP`（立即屏蔽三信号，EXIT 无需/无法屏蔽——
外层信号 handler 的 `exit 12x` 会再触发一次 EXIT trap，幂等空转）；紧随其后 `local runner_pid=
"$OV_RUNNER_PID"; OV_RUNNER_PID=""` 原子快照 + 清空全局；函数体自此往下（含全部 kill 调用）
一律基于局部快照 `runner_pid`，不再触碰全局 `OV_RUNNER_PID`。

**测试锁（结构锁，理由见测试 docstring）**：
- `test_ov_cleanup_masks_int_term_hup_immediately_on_entry`：断言屏蔽语句出现在函数体开头、
  等待循环之前。
- `test_ov_cleanup_snapshots_pid_and_clears_global_before_existence_check`：断言"屏蔽 → 快照
  → 清空全局 → 存活判定"的源码顺序，且清空全局之后的函数体内不再出现裸 `$OV_RUNNER_PID`；
  内联构造一份"旧式"（清空后仍用全局变量）样例验证断言逻辑本身确实能抓到这种回退。

**为什么是结构锁不是并发黑盒测试**：最初尝试用 `ov_cleanup TEST &` 背景化 + 主 shell 侧读全局
变量来验证"清理进行中全局已清空"，但 bash 的 `cmd &` 会 fork 独立子 shell，子 shell 内变量赋值
不会传播回父 shell——这条路径测的是假象，已放弃，改用确定性的源码顺序锁（有确定性信号 ⇒
机械判定，CLAUDE.md 基准①）。

**连带影响**：`ov_cleanup` 内 kill 调用的字面量从 `$OV_RUNNER_PID` 改为 `$runner_pid`，
`test_outside_voice_child_lifecycle.py::test_mutation_no_op_cleanup_leaves_an_orphan` 的三条
`.replace()` 字面量随之同步更新（该测试本身即为字面量匹配失败设了 `assert mutated != src` 的
自检，已确认更新后仍能正常触发变异）。

## M6 — trap 安装窗口 + 合并

**改法**：`OV_WORKDIR="$workdir"` 赋值后，先用【一次】`trap 'ov_cleanup SIGNAL; exit 1' EXIT INT
TERM HUP` 覆盖全部四个信号（收窄裸窗口——只由一次 bash 语句执行，不再是四条独立语句间的执行
间隙），随后立即用具体的四条独立 trap 语句覆写，恢复精确的信号名痕迹与退出码惯例
（130/143/129）。

**测试锁**：
- `test_trap_installation_is_a_single_combined_call_before_the_specific_ones`：断言合并 trap
  调用出现在 `OV_WORKDIR` 赋值之后、四条具体 trap 之前。
- `test_combined_trap_fallback_still_cleans_up_workdir`：变异体删掉四条具体 trap（只留合并
  兜底那条），验证：即便只有兜底 trap 生效，收到 TERM 后仍以 `exit 1`（非 shell 默认处置的
  负 returncode）收尾，且 runner/孙进程仍被正确清理——证明合并 trap 本身真的在承重，不是摆设。

**诚实边界**：本条只是**收窄**窗口（从"N 条独立 bash 语句的执行间隙"缩到"一次 trap 调用内部"），
不是**消除**——design.md/头部注释未做过度声称。

## R1 — 混合信号风暴登记（不修）

已写入 `design.md` D2 残余表新增小节 **D2.2**：明确 (d\*) 与 (a)(b)(c) 性质不同（整条 trap
机制被压垮 vs 窄时序缝）、给出触发条件（3 秒内 20–150ms 随机间隔交替 TERM/INT/HUP）、原始
实测复现率（15 次跑 10 次，67%）、对照组结论（单一信号类型同频洪泛 0/10；慢速多类型信号
trap 会重入但幂等扛住）、修法方向属设计级决策（超出代码审权限，需另开 change）、且不声称
已通过 M4/M5/M6 一并解决。机械锁：
`test_signal_storm_residual_is_documented_as_distinct_from_a_b_c`。

## R2 — 混合信号风暴回归用例

已添加 `test_mixed_high_frequency_signal_storm_can_defeat_trap_mechanism`（复用既有
`_make_env` mock-runner 接缝）。

**⚠️ 本机复现率的重要发现（已如实记入 design.md 与测试 docstring，务必让下游知晓）**：
在本次改动的验证环境（Claude Code Bash 工具驱动的子进程沙箱）里，我用两种独立方式各做了
充分试验，试图复现 R1 报告的 67% 复现率：

| 驱动方式 | 目标代码 | 试验数 | 命中数 |
|---|---|---|---|
| Python `subprocess.send_signal`，20–150ms 随机间隔，3 秒 | 当前已修复代码（1.4.3） | 30 | 0 |
| Python `subprocess.send_signal`，20–150ms 随机间隔，3 秒 | 改动前原始代码（1.4.2，`git show HEAD:...`） | 30 | 0 |
| 纯 shell `kill` 循环，20–150ms 随机间隔，3 秒 | 当前已修复代码 | 20 | 0 |
| 纯 shell `kill` 循环，20–150ms 随机间隔，3 秒 | 改动前原始代码 | 20 | 0 |
| 纯 shell `kill` 循环，**无 sleep**（~4000 次信号/2 秒，远超原始复现条件） | 改动前原始代码 | 15 | 0 |

**合计 115 次试验、0 次复现**——即便针对完全未被本轮改动触碰的原始 1.4.2 代码、即便把信号
频率推到远超原始复现条件的极端压力（无 sleep 的紧循环），在本沙箱环境下都复现不出来。这
强烈说明 67% 这个数字**对驱动信号的执行环境高度敏感**（很可能是调用方 shell 的进程组/作业
控制语义或调度差异，而非 bash 版本本身），**不是本轮 M1–M6 的任何改动消除了它**（对照组用的
是完全未改动的原始代码）。

**处理方式**：`test_mixed_high_frequency_signal_storm_can_defeat_trap_mechanism` 在 `hit_count
== 0` 时走 `pytest.skip`（而非 fail 或静默通过）——docstring 与 skip 消息里都写明这不代表 D2.2
残余已消失，也提醒未来维护者不要因为"经常 skip"就删掉它或去 design.md 撤销登记。命中时（在
支持复现的环境下）会额外核验"确实留下孤儿"，坐实命中的确实是 D2.2 描述的那种整体失效，不是
巧合命中了别的非零退出路径。

## 测试与机械门结果

```
$ /usr/bin/python3 -m pytest -q            # 全仓库全套件
1753 passed, 3 skipped in 116.81s

$ /usr/bin/python3 -m pytest sdflow-init/tests/ -q   # outside-voice 专属三文件在内
304 passed in 56.87s   （返修前 outside-voice 三文件基线：295 passed）

$ python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ bash setup.sh   # 已跑，symlink 模式即时生效
[sync_principles] ✅ 20 个投放面全部与真相源一致
[gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致
```

3 个 skip 逐一核实：2 个是 `sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py` 里既有的
"需要真实 Windows 本地磁盘"用例（与本轮改动完全无关，本机 macOS 上一直如此跳过）；
1 个是本轮新增的 `test_mixed_high_frequency_signal_storm_can_defeat_trap_mechanism`——本机 15 次
试验 0 次复现（见上文 R2 一节的完整分析），按设计走 `pytest.skip` 而非 fail。

## 未改动 / 未涉及

- `secret_scan` 出境/入境覆盖面、四旗承重墙（`--tools`/`--strict-mcp-config`/`--add-dir`/
  `--settings`）、组级 KILL 守卫（D2.1）本身的判定逻辑——本轮未触碰，相关既有测试全绿。
- `Q1/Q2/Q3` 等既有 Open Questions 未重新打开。
- 未 push，未打 `task<N>-` 标签，改动处代码注释均标 `[impl-review-fix]`（M1–M6/R1/R2 各自的
  变更点使用对应编号 `〔M1 · code-review-fix1〕` 等标注，兼具可追溯性）。

## 状态

`DONE`
