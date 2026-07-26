# Task 1 · fix 轮次 1 —— 双轴审 FAIL 后的修复报告

**票**：Task 1（后台派发落地——preflight 无副作用 + dispatch ≤5 秒 + worker 跨 shell 存活）
**R-ID**：OVBG-01, OVBG-02
**修复基线**：`890c6e4`（首轮实现）
**被改文件**：`sdflow-init/assets/hack/outside-voice-job.py`、`sdflow-init/tests/test_outside_voice_job.py`
（`outside-voice.sh` / `proposal.md` / `design.md` / `specs/` / `tasks.md` / `superpowers-plan.md` 一字未动）

TDD 纪律：**先把 11 条断言在 fix 前的实现上跑红**（`git stash` 实现、只留测试），确认每条红的
**理由**都是它要抓的那个缺陷，再转绿。红态实证逐条附在下方。

---

## Critical

### C1 · worker 构造的 `env` 从未传给 `subprocess.call` ⇒ 真 helper 必然 rc=1

**修法**：`cmd_worker` 的 `subprocess.call(...)` 补 `env=env`
（`outside-voice-job.py:822`）。同处加了一段承重注释，点名「env 是 worker→helper 之间
**唯一**的 runner/model/effort 通道」——helper 的既有 `exec` 契约只吃 `--context-file` /
`--timeout` 两个 flag，漏传等于把整条后台通道对真 voice 判死。

**机械锚（两条，一 fake 一真）**：

1. `test_worker_passes_runner_model_effort_env_to_helper`
   （`tests/test_outside_voice_job.py:804`）——`FAKE_HELPER` 现在把收到的三个变量原样回显
   （`ENV_RUNNER=` / `ENV_MODEL=` / `ENV_EFFORT=`），调用方 env 里刻意 pop 掉这三个变量，
   child 拿到值就只可能来自 worker 显式构造的 env。
   *fix 前红*：`AssertionError: ENV_RUNNER=<unset>\nENV_MODEL=<unset>\nENV_EFFORT=<unset>`。
2. `test_worker_env_reaches_the_real_shell_helper`
   （`tests/test_outside_voice_job.py:823`）——**让 worker 调仓内真的 `outside-voice.sh`**，
   补上评审指出的那条「没有任何一条用例让 worker 碰真 helper」的接缝。不调模型：用真 helper 的
   三条**早期**拒绝路径做判别器（下表为本机实测，全部在任何 runner 调用之前返回）：

   | 送达情况 | stderr | rc |
   |---|---|---|
   | runner 未送达 | `SDFLOW_VOICE_RUNNER 未设置（host=unknown…）` | 1 |
   | runner 送达但值非法 | `未知 SDFLOW_VOICE_RUNNER: bogus-runner（仅支持 codex\|claude）` | 1 |
   | runner+model 都送达、context 不存在 | `context file not found/unreadable: …` | **2** |

   用例走 ① 与 ③ 两格，断言 stderr **不**再是「未设置」、且 `.rc` 分别为 `1` / `2`。
   *fix 前红*：`assert 'SDFLOW_VOICE_RUNNER 未设置' not in ...` —— 与评审实测同一条报错。

---

## Important

### I1 · nonce 核验窗口与超时路径（两个缺陷同一片）

**修法**：新增独立常量 `NONCE_LOOKUP_GRACE_SECONDS = 5.0`（`outside-voice-job.py:81`），
`lookup_deadline = time.monotonic() + NONCE_LOOKUP_GRACE_SECONDS`（`:615`）。
**成功路径与 kill 后路径同一口径**——既不再跟 dispatch 抢那份 5 秒预算（(a)），
SIGKILL 之后也不再是零 grace（(b)）。`find_jobs_by_nonce` 一旦命中立刻返回，
所以只有「job 确实没产生」的路径才会把 grace 耗满，而那正是判错要双倍付费的一格。

**机械锚**：`test_dispatch_grants_bounded_grace_when_job_registers_after_the_kill`
（`tests/test_outside_voice_job.py:622`）。`FAKE_CLAUDE` 新增 `FAKE_CLAUDE_BG_STATE_DELAY`
（用**独立 session 的 detached 进程**延迟写 roster，才能在 dispatch 回收 spawn 进程树之后仍然发生）
与 `FAKE_CLAUDE_HANG_CHILD=0`（不留持有管道的孙子进程，kill 后立即收流）。
job 在 kill 之后 ~2 秒才进 roster，断言落 `unknown-cost` / `fallback_allowed=false` / reserve 保留 /
无 `job.json`，并断言整段仍有界。
评审点名的「现有 `test_dispatch_reclaims_...` 把 `FAKE_CLAUDE_AGENTS_MODE` 钉死 `empty`、结构上照不到该竞态」——
新用例正是补这一格，两条用例的 roster 行为互不重叠。
*fix 前红*：`assert 'exec-error' == 'unknown-cost'`，且 payload 里写着「已回收 reservation」+
`fallback_allowed: True`（**孤儿付费 job + 一次 fallback 重付**同时发生，与评审判断一致）。

### I2 · `effort` 被校验、被记进 `job.json`，却从未送达 runner

**修法**：worker 把 effort 与 runner/model **同路**下发——`env["SDFLOW_VOICE_EFFORT"] = args.effort`
（`outside-voice-job.py:811`），使 `job.json` 里的 `"effort"` 成为**真实下发值**而非装饰。
`job.json` 的 effort 字段按 design Data Model 要求保留，未摘。

**接线边界（按裁定，明写）**：helper 侧把 `SDFLOW_VOICE_EFFORT` 真正变成 `--effort <e>` argv
属 **Task 4** 范围，**本票未改 `outside-voice.sh` 一个字符**。当前状态 = 「worker 侧已接线、
下游尚未消费」；Task 4 接上即生效，无需再回头改 worker。这一点在代码注释里也写死了
（`outside-voice-job.py:798-802` 与 `:808-810`），防 Task 4 的人重新发明一条通道。

**机械锚**：同 C1 的 `test_worker_passes_runner_model_effort_env_to_helper`
（用例把 effort 改成 `medium`，避开与默认值同值的假绿）。

### I3 · `dispatch_duration_seconds` 在核验之前算完 ⇒ 断言结构性恒真

**修法**：`duration = time.monotonic() - start` 挪到 nonce 核验**之后**（`outside-voice-job.py:621`），
并在原地写明「只算到 `communicate()` 返回的话，这个值从构造上就 <deadline，任何与 deadline
比较的断言都恒真」。

**机械锚（改打真实墙钟，不回读被测自己写的字段）**：

- 新增 `test_dispatch_duration_covers_nonce_verification_not_just_the_spawn`（`tests:504`）——
  让 CLI 秒退（`rc!=0`）、roster 恒空，墙钟里剩下的全部就是那段有界 grace；断言
  `duration >= NONCE_LOOKUP_GRACE_SECONDS * 0.8`（fix 前该值 ≈0.1 秒 ⇒ 红）、
  `duration <= elapsed`（外部计时）、`elapsed < DEADLINE + GRACE + 10`（有界）。
- 改写 `test_dispatch_returns_within_monotonic_deadline_with_verified_job_id`（`tests:489`）——
  删掉恒真的 `duration < DISPATCH_DEADLINE_SECONDS`，换成外部墙钟
  `elapsed < DEADLINE + GRACE`（成功路径 MUST NOT 把 grace 耗满）+ `duration <= elapsed`。
- `test_dispatch_reclaims_process_tree_and_reserve_when_deadline_expires`（`tests:568`）与真机
  `test_background_worker_survives_dispatching_shell_exit` 的上界改为由常量表达（`DEADLINE + GRACE`），
  不再是硬编码的 `30` / `5`。

---

## Minor（按裁定 fold 修掉）

### M1 · `find_jobs_by_nonce` 只认 `name`，`state=done` 条目没有 `name`

**修法**：抽出 `_job_matches_attempt(item, nonce, id_hint)`（`outside-voice-job.py:474`）——
**name 带 nonce** 与 **id 等于本次 dispatch stdout 的 short id** 两条**并列**通道，任一命中即视为
「属于本次 attempt」。`find_jobs_by_nonce` 增加 `id_hint` 形参（`:489`），
`cmd_dispatch` 把 `_parse_job_id_hint(stdout_text)` 的结果在核验**之前**解出并传入（`:614`）。
契约注释里点名了 `state=done` 无 `name` 这一约束及其后果（helper 缺失这类 <1s 终态的 worker）。

**机械锚**：`test_dispatch_verifies_attempt_by_job_id_when_done_entry_has_no_name`（`tests:649`），
配 `FAKE_CLAUDE` 新增的 `done-noname` agents 模式（`state=done` + 无 `name`）。
*fix 前红*：`无法核验唯一 canonical job id：…有 0 个` / `state=unknown-cost`。

**连带修正 fake 的 `nomatch` 模式**：它原本只改 `name`、保留真 `id`，在 id 通道并列之后会经由
id 命中而自相矛盾。已同步把 `id` 也换成无关值（`0000dead`），使该模式仍然表达「本次 attempt
没有产生任何 job」的原意。这是让 fixture 跟上被拓宽的匹配契约，不是把断言改松——
`test_dispatch_fails_closed_when_no_job_carries_the_attempt_nonce` 的判定与门槛一字未改。

### M3 · `_parse_job_id_hint` 的 docstring 与用法自相矛盾

**修法**：删除 `hint != job_id` 那条**单独的** fail-closed 判据（原 fix 前版本的 `:655-659`），
hint 全面降级为「只参与匹配、永不单独构成失败」；fail-closed 收敛到**唯一一条**判据 ——
「两条通道并集之后命中是否唯一」（`outside-voice-job.py:648`，注释写明理由 `:644`）。
docstring 同步改写（`:456`）。理由：该格式属 research preview，一次漂移解出的垃圾 hex
若能否掉一次好 dispatch，「解析不构成失败判据」就是空话；而真正的两 job 冲突仍被唯一性判据抓住
（`test_dispatch_fails_closed_when_canonical_job_id_is_not_unique` 不变、仍绿）。

**机械锚**：`test_dispatch_is_not_blocked_by_a_drifted_backgrounded_stdout_format`（`tests:666`），
配 `FAKE_CLAUDE_BG_HINT_ID` 模拟 stdout 里的 id 漂移。
*fix 前红*：`canonical job id 交叉核验不一致：dispatch stdout=0badc0de，agents JSON=75d34378`。

### M2 · `run_preflight` 的 CLI 探针不在任何 deadline 内

**修法**：新增 `CLI_PROBE_TIMEOUT_SECONDS = 5`（`outside-voice-job.py:86`），
替换全部三处 `timeout=30`（`check_claude_version:250` / `check_agents_json:273` /
`find_jobs_by_nonce:499`）。核验轮询一并收口，因为它现在跑在 grace 预算里，
一次 30 秒挂死会直接吃掉整段 grace。常量注释附本机实测数据
（`claude --version` 0.06s、`claude agents --all --json` 0.17s）。

**机械锚**：`test_preflight_cli_probes_are_bounded_by_a_short_timeout`（`tests:400`）——
monkeypatch `_run_cli` 记录每次传入的 timeout，断言恰好两次探针且全部 ≤5。

### M4 · 两处 `os.unlink` 无保护

**修法**：抽出 `release_reservation(run_dir, site)`（`outside-voice-job.py:378`，返回 bool），
替换 `:579`（build 命令失败）与 `:597`（Popen 失败）两处裸 unlink，以及 `:637` 那处原本已有
try/except 的重复写法，三处统一。注释写明后果：降级路径上唯一还要交付的就是 stdout 那行带
`fallback_allowed` 的 JSON，一个 traceback 会让它空掉，把「可立即 fallback 的失败」变成哑失败。

**机械锚**：`test_release_reservation_never_raises_when_reserve_is_already_gone`（`tests:428`）。

---

## 未修项（裁定内，全部按原样保留）

| 项 | 理由 |
|---|---|
| `cmd_dispatch` 长函数拆分（Fowler） | 属重构、非正确性，本轮不做（裁定） |
| `timeout="abc"` 走 argparse exit 2 与优雅拒绝不可区分 | 现状 fail-closed 方向安全，不改（裁定） |
| Standards 轴三项 `⚠️ cannot-verify-from-diff`（`setup.sh` 未写 `capability-manifest.json`、四旗/`--safe-mode`、`claude logs` canary 口径） | 全属 Task 4/5 范围，本票不动（裁定） |

## 自报的取舍（需要下游知情，非未完成项）

- **失败路径的墙钟从 ~5 秒变为 ~10 秒**：核验 grace 独立之后，「job 确实没产生」的两条路径
  （CLI 秒退 / 超时被 kill）会把 5 秒 grace 耗满。成功路径不受影响（命中即返回，实测 <1 秒）。
  这是 I1 修法的直接代价，也是它的目的：用一段有界等待换掉「一次注册延迟就双倍付费 / 硬阻塞
  人工 reconcile」。design 的 `dispatch p95 ≤5 秒` 说的是 smoke 的**成功**路径，仍满足。
- `SDFLOW_VOICE_EFFORT` 目前是**已下发、下游未消费**的环境变量（见 I2 接线边界）。

---

## 全量测试

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_job.py -q
49 passed in 57.55s

$ /usr/bin/python3 -m pytest -q
2199 passed, 8 skipped, 3 xfailed in 218.74s (0:03:38)
```

真机集成用例 `test_background_worker_survives_dispatching_shell_exit`（真 `claude --bg --exec`）
**本轮实际执行并通过**，未 skip（本机 claude 版本满足 `MIN_CLAUDE_VERSION`）。

**fix 前红态实证**（`git stash` 掉实现、只留测试，同一命令）：

```
11 failed, 38 passed in 50.21s
FAILED ... ::test_preflight_cli_probes_are_bounded_by_a_short_timeout
FAILED ... ::test_release_reservation_never_raises_when_reserve_is_already_gone
FAILED ... ::test_dispatch_returns_within_monotonic_deadline_with_verified_job_id
FAILED ... ::test_dispatch_duration_covers_nonce_verification_not_just_the_spawn
FAILED ... ::test_dispatch_reclaims_process_tree_and_reserve_when_deadline_expires
FAILED ... ::test_dispatch_grants_bounded_grace_when_job_registers_after_the_kill
FAILED ... ::test_dispatch_verifies_attempt_by_job_id_when_done_entry_has_no_name
FAILED ... ::test_dispatch_is_not_blocked_by_a_drifted_backgrounded_stdout_format
FAILED ... ::test_worker_passes_runner_model_effort_env_to_helper
FAILED ... ::test_worker_env_reaches_the_real_shell_helper
FAILED ... ::test_background_worker_survives_dispatching_shell_exit
```

`git diff --check` 干净；`git status` 只有上述两个被改文件
（外加评审留下的未跟踪 `impl-reports/task1-review-package.diff`，未纳入提交）。
未勾 `superpowers-plan.md` 任何复选框、未打 `task<N>-` 完成标签、未动四件套。
