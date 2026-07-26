# Task 4 实现报告 — runner 隔离加固与出境面封堵

**票**：Task 4（R-ID: **OVBG-04**，兼落 OVBG-05 的子树核验信号）
**起点**：`256c0eb`（Task 3 双轴审通过）
**改动面**：`outside-voice.sh`（1.4.3 → **1.5.0**）+ `outside-voice-job.py`（仅契约 docstring 订正）
+ 两份测试（`test_outside_voice.py` / `test_outside_voice_job.py`）
**全量**：`2464 passed, 10 skipped, 3 xfailed`（基线 2441/8/3 ⇒ **+23 passed，+2 skipped**）

---

## 一、做了什么

### 1. 三面隔离旗（OVBG-04 argv 契约）

`outside-voice.sh` 的 claude 反向分支在既有四旗之后新增：

```sh
--effort "$ov_effort" --safe-mode --no-session-persistence
```

`ov_effort="${SDFLOW_VOICE_EFFORT:-high}"`。

**为什么不在本脚本再校验 effort 取值域**（明写决策，非遗漏）：本机 `claude --help` 的
`--effort` 枚举是 `low, medium, high, xhigh, max`（5 档），而上游 `outside-voice-job.py`
的 `EFFORT_VALUES` 只放行 3 档。在 shell 里再抄一份枚举 = 凭空造第二个漂移面，而收益
只是把「claude 自己 fail-loud」换成「helper fail-loud」。且该值只作**一个 argv 词**下发
（不可能拆出第二个 flag），无注入面。∴ 单点校验留在 job helper，本脚本只做透传 + 缺省。

**版本升 1.5.0**（不是 1.4.4）：新增了两条对外可观察契约（argv 形态 + 一个新 sidecar 文件），
不是内部修复。

### 2. runner pid sidecar（**硬交接 A**）

新增 `ov_publish_runner_pid()`：`$SDFLOW_VOICE_RUNNER_PID_FILE` 非空时，把 `OV_RUNNER_PID`
（GNU timeout 自身 pid = 它 setpgid 出的那个独立组的 pgid）以**纯十进制**、临时文件 + `mv`
原子发布，`umask 077` ⇒ **0600**。**两条 runner 路径（codex / claude）都落**——后台通道的
runner 由调用方决定，helper 不预设只有 claude。

三条边界，都在代码注释里显式登记：

| 边界 | 处理 |
|---|---|
| **「spawn 之前落盘」在 shell 层不可能** | pid 只有 `&` 之后（`$!`）才存在 ⇒ 只能 spawn 后**立即**写、早于 `wait`。残余窗口与既有残余 (b) 同源：`&` 与写入之间落信号 ⇒ 文件缺席 ⇒ 消费侧 `probe_subtree` 退回判据 ⑤ 的盘面推断（terminal witness 在场即判 `exited`）。**〔fix1 订正〕** 本行原写「退回 fail-closed 的 `unverifiable`（不是误判 exited），方向安全」——**被自家消费侧代码证伪**：`runner_kind=="absent"` 直落 ⑤，而该窄口里 helper 恰是被信号打死的 ⇒ ⑤ **误判 exited**、孤儿 runner 仍在计费。这正是 ④ 要关、而它自己缺席时关不满的口子；登记为已知窄口，不声称方向安全 |
| **写入失败** | 打 `OV_RUNNER_PID_PUBLISH_FAILED=1 stage=... path=...`（结构化字段，无 context 正文）并**继续跑 voice**——它是清理辅助信号、不是交付物；掀掉 voice 是拿主交付物去换一个辅助信号 |
| **写完不删** | 与消费侧 `read_runner_pid` docstring 已声明的模型一致（「串到别人的活 pid ⇒ 判 alive；pid 被复用 ⇒ 同样判 alive」——两个误判方向都是 fail-closed）。删掉反而会让 helper 被 SIGKILL 那一格失去 ④ 的直接信号 |

### 3. `SDFLOW_VOICE_EFFORT` 契约登记（**硬交接 B**）

头部契约块新增两条 env 输入（`SDFLOW_VOICE_EFFORT` / `SDFLOW_VOICE_RUNNER_PID_FILE`）与
新 stderr 哨兵 `OV_RUNNER_PID_PUBLISH_FAILED=1`。并加了一条**机械锚**把
「代码里读了它」与「契约里写了它」绑死（见下表「三条硬交接」的 B 行），防再次出现 Task 1 那种「已下发、
零消费者、却已写进 job.json 当事实」的无主变量。

### 4. `outside-voice-job.py` 的契约 docstring 订正（**不改行为**）

Task 3 写下的「helper MUST 在 spawn runner **之前**把 `OV_RUNNER_PID` 写入」是一条
**不可能被满足**的契约（pid 那时还不存在）。已订正为「spawn 后立即（`$!` 可得的最早时刻，
早于 `wait`）」并登记残余窗口。同时把两处「已接线、下游尚未消费」的注释更新为真实消费者。
**〔fix1 订正〕** 本节原标题写「两处」——实为**三处**：`probe_subtree` 判据 ④ 的
「helper 在 spawn runner 前落盘」当轮漏改，与另两处打架，已在 fix1 一并订正（Minor M1）。
`git diff` 核实：`outside-voice-job.py` 的改动**全部**是注释/docstring，零可执行行。

---

## 二、每条验收标准 → 机械锚

| # | 验收标准 | 锚（全部实跑过） |
|---|---|---|
| 1 | Claude 分支 argv golden 更新为显式三旗，模型仍只取 `SDFLOW_VOICE_MODEL`，helper 版本同步升级 | `test_exec_claude_isolation_flags_golden`（三旗齐全 + `--effort high`）· `test_exec_claude_effort_comes_from_the_dispatched_env` · `test_exec_claude_effort_defaults_to_high_without_the_env` · `test_version`（1.5.0） |
| 2 | 四旗 / FRAME / 两次 secret scan / 200KB 截断语义不变，既有 golden 不回归 | `test_exec_claude_reverse_path_three_flags_golden`（原样通过）+ 隔离旗 golden 内**同轮复验**四旗（防"加隔离旗时顺手改了工具集"）+ `test_exec_codex_path_untouched_by_claude_isolation_flags`（负向 parity）+ 全量 2464 绿 |
| 3 | safe mode 下 hooks/plugins/skills/memory 不执行，read-fence 仍拒绝凭证路径，只读工具精确为 `Read,Grep,Glob` | **真机**：`test_real_runner_isolates_ambient_customizations_and_keeps_the_read_fence` + **对照组** `test_real_runner_control_group_proves_the_probe_can_detect_ambient_leakage`（实际输出见第三节） |
| 4 | worker 先重定向再跑 payload；真实 `claude logs <id>` canary 证明 context / partial stdout / stderr / fake secret 均不入 transcript/state | **真机**：`test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`（内含裸 `--bg --exec` 对照组）+ **反向变异实证**（第三节） |
| 5 | job 与输出文件 0600；失败 stderr 只留 gitignored run-dir，tracked 报告只写 rc/行数/字节数 | 既有 `test_worker_output_files_are_0600` / job.json 0600 断言 + 新增 sidecar 0600 断言 + `test_failed_collect_reports_stderr_counts_but_never_its_text`（**失败**那一格，既有锚只覆盖 rc=0）；`.gitignore` 已有 `**/.outside-voice/` |
| 6 | 注入与越界：NUL/换行、仓外路径、重复 site、shell 元字符不能改写命令或越出本轮目录；非 POSIX fail-closed | `test_build_worker_command_refuses_control_characters`（NUL/`\n`/`\r`）· `test_dispatch_rejects_a_newline_in_a_path_before_any_external_side_effect` · `test_dispatch_rejects_a_run_dir_outside_the_repo_root`（既有只有 context-file 那一处）· 既有 `test_duplicate_site_is_rejected_before_external_side_effect` · `test_shell_metacharacters_in_paths_cannot_rewrite_the_dispatched_command` · `test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight`（既有只打 `os.name`，补 `sys.platform` 两格 + 顶到 `run_preflight`） |

### 三条硬交接的落地位置

| 交接 | 落地位置 | 锚 |
|---|---|---|
| **A** runner pid 文件 | `outside-voice.sh:454-489`（`ov_publish_runner_pid`，函数体 471 起）+ `:712`（codex 分支）+ `:744`（claude 分支） | `test_exec_publishes_the_runner_pid_sidecar`（**等于 timeout 自己的 pid**，不是"是个数字"）· **跨文件**：`test_real_helper_publishes_the_runner_pid_this_module_consumes`（worker 下发 → 真 helper 落盘 → `JOB.read_runner_pid` 解析）· **后果**：`test_the_published_runner_pid_unblocks_the_subtree_verdict`（刻意删掉 terminal witness，逼判定只能走 ④ ⇒ `SUBTREE_EXITED`；否则恒 `unverifiable`、`cleanup --cancel` 永不解闸） |
| **B** `SDFLOW_VOICE_EFFORT` 登记 | `outside-voice.sh:16-22`（头部契约块）+ `:743`（消费点 `ov_effort=`） | `test_env_contract_block_registers_every_consumed_variable`（从正文解析 `${SDFLOW_VOICE_*}` 消费点，逐个要求出现在头部契约块） |
| **C** `claude logs` canary 口径 | 测试 docstring 显式写明「路径不是 payload、不判红」，并断言 `str(ctx) in roster.stdout or job_id in roster.stdout` | `test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`；真机 roster 实测确认 `name` 承载完整 worker 命令串（含绝对路径，见第三节） |

---

## 三、真机输出（脱敏）

### (a) `claude logs` canary —— worker 走既有重定向

```
DISPATCH rc= 0
{"…","effort":"high","job_id":"8c304a98","model":"opus","ok":true,"reason_code":"ok",…}
RC= 0
=== claude logs 8c304a98  rc=0 ===
（stdout 为空）
--- stderr ---
（空）
=== roster entry ===
{"id":"8c304a98","cwd":"…/repo","kind":"background","sessionId":"8c304a98-…",
 "name":"…/python3 …/outside-voice-job.py worker --run-dir …/20260725T-Man01 --site design-voice
         --context-file …/design-voice-context.md --repo-root …/repo --runner claude --model opus
         --effort high --timeout 900 --attempt-nonce b49a… --run-id 20260725T-Man01",
 "state":"done"}
CTX canary in logs: False
CTX canary in roster: False
```

`claude rm 8c304a98` 已清理。**roster 的 `name` 里只有绝对路径，没有 context 正文** ⇒ 交接 C 的口径实测成立。

### (b) 判别器有效性 —— 两条独立证明（**这是本票最要害的一段**）

「transcript 为空」本身**证不了任何事**：空既可能是重定向奏效，也可能是 `claude logs`
压根不捕获 background 命令的输出。故两侧各做一次：

**对照组（已写进自动化测试）**——裸 `--bg --exec`，无任何重定向：

```
$ claude --bg --exec "printf 'CONTROL_CANARY_A1B2\n'; printf 'CONTROL_ERR_A1B2\n' >&2; sleep 2"
backgrounded · 4d7b11b5 · …
$ claude logs 4d7b11b5
CONTROL_CANARY_A1B2
CONTROL_ERR_A1B2
```
⇒ `claude logs` **确实**捕获 background 命令的 stdout 与 stderr。

**反向变异（隔离副本，仓内零改动）**——把 `cmd_worker` 的 `os.dup2(out_fd,1)/dup2(err_fd,2)`
换成 `pass`，同一条真机流程重跑：

```
=== claude logs c0568eee  rc=0 ===
CTX_BODY_CANARY_5F2A9
aws_key=AKIAQQQQQQQQQQQQQQQQ
CTX_BODY_CANARY_5F2A9
aws_key=AKIAQQQQQQQQQQQQQQQQ
CTX canary in logs: True
```
⇒ **context 正文与假密钥双双进 transcript**。重定向是这条出境面唯一的闸，锚是真判别器。

### (c) safe-mode / read-fence / 只读工具集（真机模型探针）

探针项目里装满诱饵：`.claude/settings.json` 的 SessionStart hook（`touch <marker>`）、
`CLAUDE.md`（要求每次回复以 `MEMORY_CANARY_7Q3` 开头）、命中生产读围栏 `Read(//**/id_rsa*)`
的诱饵文件 `id_rsa_probe`（内容为无害自造串 `READ_FENCE_BREACHED_9K2`）。
**旗子清单不在测试里另抄一份**——先用假 claude 把生产 argv 原样抓下来，只换 model / add-dir
后交给真 CLI 重放。

```
=== SAFE-MODE 组 rc=0 ===
DENIED

TOOLS=Glob, Grep, Read

hook marker exists: False

=== 对照组（去掉 --safe-mode）rc=0 ===
MEMORY_CANARY_7Q3

好的

hook marker exists: True
```

四条同时成立：① SessionStart hook **未**执行 ② 项目 CLAUDE.md memory **未**加载
③ 读围栏在 safe mode 下**仍然**拒读（`DENIED`，诱饵内容零泄漏）④ 工具集精确为
`Glob, Grep, Read`。对照组**同时**证明两个诱饵在没有 `--safe-mode` 时是真会响的 ⇒
上面的"没出现"是证据，不是默认值。

> 该探针默认 **skip**（要真花模型调用），显式 `SDFLOW_OV_REAL_MODEL_SMOKE=1` 才跑。
> 全量套件里的 `+2 skipped` 就是这两条。

---

## 四、反向变异复核（新锚逐条验红；均在 scratchpad 独立副本进行，仓内文件零改动）

| 变异 | 结果 |
|---|---|
| 去掉 `--safe-mode` | **RED** `test_exec_claude_isolation_flags_golden` |
| `ov_effort` 硬编码成 `"high"`（不读 env） | **RED** `test_exec_claude_effort_comes_from_the_dispatched_env` |
| 删掉两处 `ov_publish_runner_pid` 调用 | **RED ×5**：三条 helper 侧 + **两条跨文件交接锚**（`test_real_helper_publishes_the_runner_pid_this_module_consumes` / `test_the_published_runner_pid_unblocks_the_subtree_verdict`） |
| 头部契约块删掉 `SDFLOW_VOICE_EFFORT` 的全部提及 | **RED** `test_env_contract_block_registers_every_consumed_variable` |
| 同上，删 `SDFLOW_VOICE_RUNNER_PID_FILE` | **RED** 同上 |
| `build_worker_command` 的 `shlex.join` → `" ".join` | **RED** `test_shell_metacharacters_in_paths_cannot_rewrite_the_dispatched_command`（bash 真去执行了 `touch`） |
| `cmd_worker` 去掉 `os.dup2` 重定向 | **RED**（真机，见 (b)） |

> 变异复核**只在** `scratchpad/mutrepo` 的整树副本里做（承接 Task 3 编排层记录的"变异互踩"教训）。
> 复核结束已 `rm -rf` 该副本，`git status` 只剩本票的 4 个改动文件。

---

## 五、未做 / 诚实降级

1. **`--safe-mode` 对 plugins / skills 的隔离未独立探针**。已直接探到的是 **hooks（任意命令执行，
   影响最大）与 memory（prompt 注入面）**，且对照组证明这两类诱饵在无 safe-mode 时确会生效。
   plugins/skills 与它们由**同一个 flag、同一套 customization 加载机制**管辖（`claude --help`
   逐项列出）。独立探针要么靠模型自报（弱锚、易飘），要么要装真插件（成本远高于收益）。
   ⇒ 按通则④简化，此处**如实标注为未独立验证**，不写成"已验"。
2. **`openspec/specs/host-adaptive-execution/spec.md` 与 `spec-workflow/spec.md` 仍只写「四旗」**。
   本 change 的 delta（OVBG-04）已含三面隔离旗，主 spec 由 **archive 阶段的 delta 同步**统一更新；
   实现期改 `openspec/specs/` 既越本票范围、也与流程相悖。**未改，记在此供 done 阶段核对。**
3. **`setup.sh` 的 `capability-manifest.json` 仍未写**（Task 1 报告已交接，归 **Task 5**）
   ⇒ 真实安装态 preflight 仍会红。本票新增的三旗与 sidecar 在**测试态**（`job_home` fixture
   现算 manifest）全绿，与该缺口正交。

## 六、Concerns（交下游票 / 评审判定，非本票遗漏）

1. **`EFFORT_VALUES` 只有 3 档，而 CLI 支持 5 档（`xhigh` / `max`）。** 现状 = job helper 更严，
   fail-closed 方向安全，本票不动。若将来要用 `xhigh`，改的是 `outside-voice-job.py` 的
   `EFFORT_VALUES` 一处——shell 侧无需同步（这正是不抄第二份枚举的收益）。
2. **`<site>.runner.pid` 写后不删**（含 rc 已发布的正常终态）。留档 = 一致的 fail-closed
   方向（stale/复用 pid ⇒ 判 alive），与 Task 3 的消费侧模型一致；代价是**理论上**的 pid 复用
   可能让一个早已结束的站点在 `cleanup --cancel` 时判 alive。概率极低（正常终态走的是
   「已 collect ⇒ 直接 rm」路径，根本不调 `probe_subtree`），且方向安全 ⇒ 不加删除逻辑。
3. **`claude --bg --exec` 是 research preview**：`backgrounded · <id> · <cmd>` 的 stdout 格式与
   `claude logs` 的行为都可能漂。canary 测试的对照组会在 `claude logs` 行为漂到"不再捕获输出"
   时**主动失败**（而不是静默退化成假绿）——这是有意设计的失效方向。
