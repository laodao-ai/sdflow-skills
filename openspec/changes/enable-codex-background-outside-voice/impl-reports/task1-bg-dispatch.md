# Task 1 impl-report — 后台派发落地（preflight 无副作用 + dispatch ≤5 秒 + worker 跨 shell 存活）

**R-ID**: OVBG-01, OVBG-02
**新增文件**（两个，无既有文件改动）：

| 文件 | 角色 |
|---|---|
| `sdflow-init/assets/hack/outside-voice-job.py` | canonical 源资产（`setup.sh` 分发面，Task 5 接安装）。含 `version` / `preflight` / `dispatch` / `worker` 四个子命令 |
| `sdflow-init/tests/test_outside_voice_job.py` | 41 条契约测试（40 条离线 fake + 1 条真机 `claude --bg --exec` 跨 shell 存活 smoke） |

`proposal.md` / `design.md` / `specs/` / `tasks.md` / `superpowers-plan.md` **未改动**；无 `task<N>-` 完成标签、
未勾任何复选框（`git status` 只有上面两个 `??`）。

## 落笔前的接缝核验（真打开过）

- `sdflow-init/assets/hack/outside-voice.sh`（755 行）——既有 `exec --context-file <f> [--timeout <s>]`
  契约、四旗 Claude argv、`OV_CLAUDE_READ_FENCE`、rc 语义（0/1/124/3/2）。worker 原样调它，
  **零改动、零复制**（prompt render / secret scan / FRAME / 截断仍是它的独家职责）。
- `sdflow-init/tests/test_outside_voice{,_utf8,_child_lifecycle}.py`——既有 golden 口径（fake `timeout`
  stub、`SDFLOW_VOICE_*` 清脏、`bash <helper>` 调用姿势），本文件沿用。
- 本 change 的 `design.md`（Data Model / Sequence / ADR-1..D-6 / NFR / Security）与
  `specs/outside-voice-background-jobs/spec.md`（OVBG-01/02 全文 + Scenario）。
- `sdflow-spec-review/SKILL.md:367-376`——run-dir 约定 `{change_dir}/.outside-voice/<run-id>/`、
  `dispatch-manifest.tsv` 的现有 producer 是 SKILL 自身（∴ 本票不抢写，见「未做项」）。
- `.gitignore:19` `**/.outside-voice/`——run-dir 已递归 gitignore，本票无需新增条目。

## 本机真机核验（②：不猜，先探）

在写代码之前对 research-preview 形态做了四次真实探针（`~/scratchpad/probe`，已 `claude rm` 清理）：

| 探针 | 结论 |
|---|---|
| `claude --version` | `2.1.220 (Claude Code)` ≥ 下限 2.1.169 |
| `claude --bg --exec '<cmd>'` | ~1.1 秒返回 `backgrounded · <8位hex> · <完整命令>`；发起 shell 退出后作业继续跑满 `sleep 5` 并写完文件 ⇒ **跨 shell 存活成立** |
| `claude agents --all --json` | 0.17 秒；顶层 list；background 条目字段 = `id`/`cwd`/`kind:"background"`/`startedAt`/`sessionId`/`state`/`name`，**`name` 就是下发的完整命令串** |
| bg session 环境 | 环境变量**被继承**（自设 `MYPROBE` 可见）、`PATH` 完整、`CLAUDECODE` 未设、cwd = 发起时 cwd |

`name` 字段承载完整命令这一点是本票 dispatch 核验机制的地基：attempt nonce 写进命令 ⇒
「外部 job 到底产生没有」变成一条**可机读信号**，而不是 dispatch 自述。

## 实现要点（与设计条款的对应）

**preflight（无副作用，D-6）** —— 四项检查，任一不过即 `reason_code="preflight-error"` + exit 1，
stderr 逐条给 actionable 提示：
`posix-shell`（`os.name`/`sys.platform ∈ {darwin,linux}`/`/bin/sh` 可执行）·
`claude-version`（≥2.1.169）· `agents-json`（rc=0 且顶层 list）· `capability-manifest`（同代安装快照）。
**全程只跑 `--version` 与 `agents --all --json` 两条只读命令**，MUST NOT `--bg --exec 'true'`、
MUST NOT 建 dummy job。

**capability manifest** —— `capability-manifest.json`（与 job helper 同目录）记
`{schema_version, entries:{outside-voice-job.py, outside-voice.sh, skill-principles.md → sha256}, generation}`；
`generation` 由 entries 重算比对（挡手改）。计算与写入的**单一源** = 模块函数
`compute_manifest()` / `write_manifest()`，供 Task 5 的 setup.sh 安装步与本文件测试共用，防两份口径漂移。

**reservation（外部副作用之前）** —— `acquire_reservation()` 用 `os.open(O_WRONLY|O_CREAT|O_EXCL, 0o600)`
原子占坑；`FileExistsError` 分两类：有 `<site>.job.json` ⇒ `duplicate-site`，无 ⇒ `unknown-cost`。
占坑成功后数 `*.reserve`，>2 即**退回自己的坑**并落 `slot-limit`（此刻仍无任何外部副作用）。
三种拒绝一律 `fallback_allowed=false`——它们要么是硬失败、要么成本未知，立即 fallback 会叠加费用。

**dispatch（monotonic 5 秒）** —— `time.monotonic()` 起 deadline；
`subprocess.Popen([claude,'--bg','--exec',cmd], start_new_session=True)` ⇒ 超时用
`os.killpg(os.getpgid(pid), SIGKILL)` 回收**整棵进程树**。随后按 attempt nonce 在 agents JSON 里
核验：**恰好 1 个** background 条目携带该 nonce 才算成功；0 个/≥2 个/与 stdout 解析出的 short id
不一致 ⇒ 一律 `unknown-cost` fail-closed（stdout 解析只作**交叉核验线索**，解析不出不构成失败判据——
该输出格式属 research preview，会漂）。
- 超时/非零 **且** 检出外部 job ⇒ `unknown-cost`，**保留** reserve 交给 reconcile；
- 超时/非零 **且** 未检出外部 job ⇒ 回收 reserve，`exec-error` + `fallback_allowed=true`。

**worker** —— 第一动作即 `os.dup2` 把自身与 child 的 fd 1/2 直接接到 0600 的
`<site>.stdout`/`<site>.stderr`（**在执行任何可携带 payload 的代码之前**），随后
`started.json` → `bash outside-voice.sh exec` → `terminal.json` → atomic-rename `<site>.rc`。
rc 恒为纯十进制（被信号杀死的负返回码按 shell 惯例归一成 128+signum）；helper 缺失/启动失败
也照样发布 terminal + rc（127/126），**不留「没有终态可读」的黑洞**。worker 自身 exit 恒 0——
真实结果只经 `.rc` 发布，MUST NOT 让 supervisor 的 job state 充当结果通道（ADR-2）。

## 逐条验收标准 × 机械锚

测试文件统一路径 `sdflow-init/tests/test_outside_voice_job.py`。

| 验收标准 | 机械锚（测试名） |
|---|---|
| preflight 在旧版本 / agent view 被策略禁用 / 非 POSIX 三情形 fail-closed + actionable stderr | `test_preflight_fails_closed_on_old_claude_version`（断言 stderr 含 `2.1.169` 与「升级」）· `test_preflight_fails_closed_when_agent_view_disabled_by_policy`（断言 stderr 含 `disableAgentView`）· `test_preflight_fails_closed_on_non_posix_platform`（`monkeypatch` `os.name="nt"`，断言 hint 含 POSIX）· `test_preflight_fails_closed_when_agents_json_top_level_is_not_a_list` |
| 负向 golden：不执行 `--bg --exec 'true'`、不建 dummy job、无外部副作用 | `test_preflight_has_no_external_side_effect_and_never_runs_bg_exec`——遍历 fake claude 的**全部**调用日志断言 argv 不含 `--bg`/`--exec`/`true`；断言 fake 的 state 文件（只由 `--bg` 分支写）不存在；断言 job 目录与 run 目录顶层条目集**逐字节不变** |
| 任何外部副作用之前先 `O_CREAT|O_EXCL` 建 reservation | `test_reservation_exists_before_any_external_dispatch`——fake claude 在**每次被调用的当刻**快照 run-dir 条目集，断言 `--bg` 那次的快照里已含 `design-voice.reserve` |
| 同 site 重复派发在外部副作用前原子拒绝 | `test_duplicate_site_is_rejected_before_external_side_effect`（`state="duplicate-site"`、`fallback_allowed=false`、`--bg` 调用数 = 0） |
| 本 run 第三个不同 site 在外部副作用前原子拒绝 | `test_third_distinct_site_is_rejected_before_external_side_effect`（`state="slot-limit"`、`--bg` 调用数 = 0、自己的 reserve 已回收） |
| dispatch 在 monotonic 5 秒 deadline 内返回并核验唯一 canonical job id | `test_dispatch_returns_within_monotonic_deadline_with_verified_job_id`（`job_id=="75d34378"`、`dispatch_duration_seconds < 5`）· `test_dispatch_fails_closed_when_canonical_job_id_is_not_unique`（2 个匹配 ⇒ unknown-cost）· `test_dispatch_fails_closed_when_no_job_carries_the_attempt_nonce`（0 个匹配 ⇒ unknown-cost、不写 metadata） |
| 超时回收 spawn 进程树，并清理尚未产生外部 job 的 reserve | `test_dispatch_reclaims_process_tree_and_reserve_when_deadline_expires`——fake claude 挂起 60 秒并**再 spawn 一个孙进程**，把两个 PID 落盘；断言 dispatch <30 秒返回、reserve 已删、**两个 PID 均已不存在**（`os.kill(pid,0)` 轮询） |
| job metadata 临时文件 + atomic rename，字段齐全 | `test_dispatch_writes_job_metadata_atomically_with_required_fields`——逐字段断言 15 个必填字段；`command_sha256` 与 fake claude **实际收到的命令串**重算一致（非自述）；文件权限 `0o600`；run-dir 无 `.tmp-*` 残留 |
| 命令只带受校验路径/runner/model/timeout，不带 context 正文 | `test_dispatch_command_is_single_shell_quoted_worker_invocation`——`shlex.split` 还原 argv 逐项断言；断言命令串不含换行/NUL、**不含 context 文件正文** |
| 发起 shell 退出后 worker 仍跑到终态（无模型 job 证明跨 shell 存活） | `test_background_worker_survives_dispatching_shell_exit`（**真 `claude --bg --exec`**）——fake helper `sleep 6`；断言 dispatch 子进程返回时 `.rc` **尚不存在**（否则证不出跨 shell），随后轮询到 rc=0、stdout 含标记、started/terminal 均在；`finally` 里 `claude rm <job_id>` 清理 |
| worker 第一动作发布 started/process-tree identity | `test_worker_publishes_started_then_terminal_then_rc`——**由 child 自己看盘面**：fake helper 检查 `started.json` 是否存在并把结论写进 stdout，断言 `STARTED_SIDECAR_VISIBLE=yes`；started 含 `attempt_nonce`/ISO `started_at`/`worker.{pid,ppid,pgid}` |
| 终态发布 terminal witness 后**再** atomic rename 出纯十进制 rc | `test_worker_publish_order_is_terminal_witness_then_rc`（模块级 spy，断言调用序恰为 `[terminal.json, s.rc]`）· `test_worker_publishes_pure_decimal_rc_for_helper_timeout`（rc 文件 == `"124"` 且匹配 `^\d+$`）· `test_worker_publishes_rc_even_when_shell_helper_is_missing` |
| 残留 reserve（dispatch accepted ↔ metadata 发布之间崩溃）判 `unknown-cost`，禁自动重派/禁立即 fallback | `test_residual_reserve_without_metadata_is_unknown_cost`（`state="unknown-cost"`、`fallback_allowed=false`、`--bg` 调用数 = 0、reserve 保留）· `test_dispatch_deadline_with_external_job_present_is_unknown_cost`（超时但外部 job 已存在 ⇒ reserve 保留、不写 metadata） |

附加（非 checkbox，属同片安全面）：`test_worker_output_files_are_0600`（五个 sidecar 全 0600）·
`test_worker_redirects_own_and_child_streams_before_running_payload`（worker 进程 stdout/stderr **全空**）·
`test_dispatch_rejects_unsafe_site_names` / `_run_ids`（`../escape`、`a/b`、空格、`bad;rm -rf /`）·
`test_dispatch_rejects_context_file_outside_repo_root` · `test_dispatch_rejects_out_of_range_timeout`（0/3601/abc）·
`test_dispatch_fails_closed_when_preflight_not_ready` · `test_dispatch_to_worker_lifecycle_offline`（fake claude 真执行
下发命令 ⇒ 证明组出来的命令串确实跑得通 worker，全链无真模型）。

## 测试结果（如实）

单文件：

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_job.py -q -rs
41 passed in 37.86s
```

真机 smoke 确实**跑了**（未 skip，`-rs` 无 skip 行）；单独跑：

```
$ /usr/bin/python3 -m pytest ... -k "survives" -v
1 passed, 37 deselected in 8.33s
```

全量：

```
$ /usr/bin/python3 -m pytest -q -rs
2188 passed, 8 skipped, 3 xfailed in 191.03s (0:03:11)
```

8 条 skip 全部是既有环境性 skip（1 条信号风暴复现率 + 7 条 Windows 本地盘），与本票无关。
`git diff --check` 干净。跨版本：`/usr/bin/python3` 3.9.6 全绿；`python3` 3.14.6 上
`py_compile` + `version` + `preflight` 三条烟测通过（CI 泳道跑 3.12，语法/API 均在 3.9 兼容集内）。

## 未做 / 降级项（本票范围外，如实登记）

1. **`setup.sh` 尚未安装 `*.py`、也尚未生成 `capability-manifest.json`** —— 属 Task 5 的
   「兼容快照原子安装」checkbox。后果**当前可见且诚实**：开发 checkout 里直接跑
   `outside-voice-job.py preflight` 会因 manifest 缺失 fail-closed（实测输出见上）。
   `write_manifest()` 已作为单一计算源就位，Task 5 只需在安装步调它。
2. **`--effort high --safe-mode --no-session-persistence` 尚未进 `outside-voice.sh` 的 Claude argv**
   —— 属 Task 4。本票把 `effort` 记进 job metadata（可机读证据链已就位），但 worker 调 helper 时
   仍走既有 `exec --context-file --timeout` 契约，**未改 `outside-voice.sh` 一个字节**。
3. **`dispatch-manifest.tsv` 不由本 helper 追加** —— 现 producer 是两份 SKILL（`SKILL.md:376`），
   「job id/site/nonce 追加 manifest」是 Task 5 的 checkbox。dispatch 已把 `job_id`/`site`/
   `attempt_nonce` 结构化返回，Task 5 直接取用即可。
4. **`status` / `await` / `collect` / `cleanup` / `reconcile` 子命令未实现** —— Task 2/3 范围。
   本票只把证据按 started → terminal → rc 放上盘面，不做任何状态派生。
5. **`STARTUP_DEADLINE_SECONDS = 5`** —— 取 `design.md` job.json 示例的字面值
   （`dispatched_at` 02:00:00 → `startup_deadline_at` 02:00:05）。本票只把它**写进 metadata**，
   不消费；实际「启动 deadline 是否够宽」的判定归 Task 2。真机 smoke 观察到 worker 在
   dispatch 返回后 1 秒内即发布 started sidecar，5 秒有余量，但**这是单次采样，不是阈值证明**。

## Concerns（交编排层）

1. **同 site 并发在途 dispatcher 会被归类成 `unknown-cost` 而非 `duplicate-site`**：判据是
   「reserve 存在但 job.json 尚未发布」，而在途 dispatcher 恰好处于这个窗口。两者都是拒绝且
   `fallback_allowed=false`，方向保守（不会多花钱），但 `unknown-cost` 的措辞会把「对方正在正常
   派发」说成「成本未知需人工 reconcile」。修法要么给 reserve 加 liveness 探针（读 `dispatcher_pid`
   探活），要么接受措辞。按 ④ 五问：概率低（同 site 并发 dispatch 本身即契约违规）、影响小
   （只是提示语，不改判定）、完美成本不低（PID 探活跨主机不可靠）⇒ **本票选择接受，登记在此**。
2. **`claude agents --all --json` 的 `name` 字段承载完整命令串**：本票的 nonce 核验机制依赖它，
   同时它也意味着 supervisor state 里**会有**一条完整的 worker 命令（含 run-dir/context 文件的
   绝对**路径**，不含正文）。Task 4 的「`claude logs <id>` canary 回归」需要把这条纳入口径——
   路径不是 payload，但它是一条已存在的、结构化的外泄面，**不该被 canary 测试意外判红**。
3. **`--exec` 仍未出现在 `claude --help`**（本机 2.1.220 实测）：与 design 的 research-preview
   定性一致。本票的 preflight **不**探测 `--exec` 是否存在（那需要副作用），最终能力核验落在
   真实 dispatch 的 nonce 匹配上——若未来 `--exec` 被移除，表现为「dispatch 非零 + 无 nonce 命中」
   ⇒ `exec-error` + `fallback_allowed=true`，即 5 秒级诚实降级，符合 ADR-3。
