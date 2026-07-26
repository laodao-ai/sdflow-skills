# Task 2 实现报告 — 终态派生的 status / await / collect

**票**：Task 2（R-ID: OVBG-02, OVBG-03, HAE-09；对应 `tasks.md` 1.3）
**Blocked-by**：Task 1（`93a1258`，49 条契约测试全绿，未推翻其任何既有契约）
**实现 commit**：`b4c1488`（+ 一次命名修正，见「反向变异」小节）

## 做了什么

在 `sdflow-init/assets/hack/outside-voice-job.py` 上加三个**只读**子命令，全部建在 Task 1
已经放上盘面的证据之上（`<site>.reserve` / `.job.json` / `.started.json` / `.terminal.json` /
`.rc` / `.stdout` / `.stderr`），不改 Task 1 的任何既有行为：

| 子命令 | 契约 |
|---|---|
| `status --run-dir --site [--timeout]` | 纯派生当前归类：读盘面 + 一次 `claude agents --all --json` liveness 探针。终态站点**根本不探 liveness**（NFR「单次查询 ≤5 秒」自然满足） |
| `await --run-dir --site [--timeout] [--max-wait] [--poll-interval]` | 有界等到终态。上界不从 dispatch 时刻起算 |
| `collect --run-dir --site [--timeout]` | 幂等收集：只在 rc 发布后读 stdout，核对 witness digest，首次结果原子发布为 `<site>.collected.json` |

三者 stdout 恒为**单行 JSON**、同一形状；`exit 0 ⟺ payload["ok"] ⟺ reason_code == "ok"`，
usage-error 走 exit 2。

**状态枚举**（design.md 状态机 + 两个补格）：
`MISSING | RESERVED | STARTING | RUNNING | SUCCEEDED | TIMED_OUT | FAILED | LOST | CORRUPT`。
`RESERVED/STARTING/RUNNING` 三个未终态状态的 `reason_code` 恒为 `null` ⇒ **构造上不可能被读成 ok**。

**判定顺序是契约，不是风格**（写在 `derive_status` docstring 里）：
① job metadata（坏 ⇒ CORRUPT，**此时不看 rc、不碰 stdout**）→ ② rc（终态发布点，一旦存在
liveness 完全不参与，ADR-2）→ ③ witness identity → ④ liveness 终态且无 rc ⇒ LOST（不等满
timeout）→ ⑤ 时间上界。

## 每条验收标准的机械锚

> 全部锚均经**反向变异**验过可判别（把实现改回错误形态 → 对应锚变红），见文末表。
> 测试文件：`sdflow-init/tests/test_outside_voice_job.py`（49 → **239** 条）。

### ① rc × liveness × 元数据 逐组合确定性归类，且终态前不读 stdout

- **笛卡尔本体**：`test_status_cartesian_classification` —— `itertools.product` 参数化
  **7 × 6 × 3 = 126** 组合，逐组合断言 `(state, reason_code, terminal, ok)`。
  - rc 维度 7：`absent / rc0_nonempty / rc0_empty / rc124 / rc3 / rc_other / rc_bad`
    （票面 5 格 + `absent`（pending/lost 那一半根本进不来）+ `rc3`（见 ② 的 secret-hit 说明））
  - liveness 维度 6：`working / done / failed / stopped / missing` + `unavailable`（探针本身失效）
  - 元数据维度 3：`complete / missing-field / schema-drift`
  - 期望表 `_expected_classification()` **逐条抄自 spec 原文**（OVBG-02 的派生规则 + 「元数据
    损坏不得猜成功」Scenario + SKILL ⑦ 的 rc 表），**MUST NOT 从实现回读**——否则等于用实现证明实现。
- **liveness 不得越过 rc**：`test_liveness_never_overrides_a_published_rc` —— 6 种 liveness 下
  rc=0+非空 stdout 恒 `(SUCCEEDED, ok)`，且 `liveness is None`（终态站点压根没探）。ADR-2 直锚。
- **终态前不读 stdout（三条独立锚）**：
  1. `test_status_never_reads_stdout_before_terminal` —— 读取口被拆成两个模块级函数
     （`stdout_stat_evidence` 只 stat / `stdout_read_evidence` 才读正文），monkeypatch 两者为 spy，
     6 种 liveness 下 pending 站点断言 `calls == []`。**这是唯一真正的「有没有读过」判别器。**
  2. `test_status_stats_stdout_size_but_never_reads_its_content` —— 终态后也只 stat 不读正文。
  3. `test_status_of_a_running_site_survives_an_unreadable_stdout` —— `chmod 000` 负向探针
     （root 下无判别力 ⇒ 显式 `skipif geteuid()==0`，诚实降级不假绿）。

### ② 只有真实 124 归 timeout；terminal 无 rc / 失联 / 元数据损坏一律 exec-error

| 情形 | 锚 |
|---|---|
| rc=124 → `timeout` | `test_collect_rc_to_reason_code_table[rc124-timeout]` + 笛卡尔 18 格 |
| agent done/failed/stopped/missing 且无 rc → `LOST`/`exec-error`，**不等满 timeout** | `test_status_cli_maps_real_agent_states_through_the_id_channel`（4 参数）· `test_await_returns_immediately_when_the_job_is_gone`（断言 `elapsed < 20` 而 timeout=900） |
| rc 已发布但缺 terminal witness → `CORRUPT` | `test_terminal_rc_without_a_terminal_witness_is_corrupt` |
| witness attempt nonce 不符（上轮遗留混入）→ `CORRUPT` | `test_witness_attempt_nonce_mismatch_is_corrupt` |
| rc 非纯十进制 / rc=0 但 stdout 为空 / job JSON 缺字段 / schema drift → `exec-error` | 笛卡尔 + `test_collect_rc_to_reason_code_table[rc_bad-…][rc0_empty-…]` |
| stdout digest 与 witness 不符 → `CORRUPT` | `test_collect_detects_a_stdout_digest_mismatch` |
| collected witness 属别的 attempt → `exec-error` | `test_collect_refuses_to_reuse_a_collected_witness_from_another_attempt` |
| 盘面全空 → `MISSING`/`exec-error`（「起了没收」不得读作成功） | `test_site_with_nothing_on_disk_is_exec_error_never_ok` |

**`rc=3` 保持 `secret-hit`（不并入 exec-error）** —— 这不是加宽，是 HAE-09 的硬要求
（「reason_code 枚举语义 MUST 保持不变」）：两份评审 SKILL 调用协议 ⑦ 的同步分支表里
`exit 3 → secret-hit 且拒发不 fallback`。若并入 exec-error，调用方会拿**同一份已命中 secret 的
context** 再派一次同族 fallback，正是 OVBG-04 要杀的形态。这条判据写在实现的 `RC_SECRET_HIT`
注释与测试的 `_expected_classification` docstring 里。

**探不到 ≠ 丢了**（本票为诚实降级加的两条保守锚）：
- `test_liveness_probe_failure_does_not_declare_the_worker_lost`（CLI 不可达）
- `test_unknown_agent_state_is_inconclusive_not_terminal`（agents JSON state 枚举漂移）
两者一律回落时间上界判定，**MUST NOT** 因为一次探针失效就把所有在飞的合法 worker 判成 LOST
（那会让整条通道退回 efficacy=0，且伪装成 helper 故障）。

### ③ 产生 `reason_code="ok"` 的数量为 0 —— 机械断言

`test_no_pending_lost_or_corrupt_combination_ever_yields_ok`：遍历**同一份 126 组合**，
`offenders == []` + **正向对照** `ok_count == 6`（合法组合确实产出了 ok，防止「0 个 ok」
只是因为根本没有任何 ok 的空断言）。反向变异（把 RUNNING 的 reason_code 改成 `ok`）当场变红。

### ④ startup deadline 独立；worker 上界从可信 `started_at` 起算 timeout + 30s grace

- `test_startup_deadline_is_independent_of_the_worker_deadline` —— started sidecar 未发布时，
  未过 startup deadline = `STARTING`，已过 = `LOST`（与 worker timeout 无关）。
- `test_worker_upper_bound_counts_from_trusted_started_at_plus_grace` —— **dispatch 已过 400 秒、
  started 才过 10 秒、timeout=60** 的排队 worker 判 `RUNNING`（从 dispatch 起算会当场误杀）；
  越过 `started_at + 60 + 30` 才判 `LOST`，且断言 `reason_code != "timeout"`。
- `AWAIT_GRACE_SECONDS == 30` 由 `test_default_timeout_and_range_are_the_single_shared_constants` 钉死。

### ⑤ 站点仍 RUNNING 时有界 await 不早退、不落 timeout

- `test_await_waits_for_a_real_rc_and_never_early_timeouts` —— 后台线程 1.5 秒后才发布 rc；
  断言 `elapsed >= 1.4` **且** `reason_code == "ok"`（既证不早退、又证没把等待当 timeout）。
- `test_await_exhausting_max_wait_stays_running_and_is_not_timeout` —— 外层 `--max-wait 1` 耗尽时
  仍返回 `(RUNNING, reason_code=None)`，**不落 timeout**。
- `test_await_declares_lost_after_started_plus_timeout_plus_grace` —— 越界归 `LOST` 而非 timeout，
  且 `elapsed < 20`（有界，不等满）。
- `test_await_on_a_bare_reservation_does_not_spin_forever` —— `RESERVED`（unknown-cost）永远不会
  自行到达终态 ⇒ 立即返回交 reconcile（Task 3），不死等。

### ⑥ collect 幂等 + 结构化证据

- `test_collect_is_idempotent_byte_for_byte` —— 两次 collect 之间 `sleep(1.1)`（保证「重算」会得到
  不同的 `collected_at`），断言 `first.stdout == second.stdout` **逐字节相等**。
  实现：首次结果整份原子发布为 `<site>.collected.json`，用 **temp 全量写完 → `os.link`**（目标已存在
  即失败 ⇒ 首写者胜，且读者看到的一定是写完之后的完整文件），重复 collect 原样回放。
- `test_collect_returns_structured_machine_readable_evidence` —— 断言 16 个字段非空：
  `dispatched_at / started_at / terminal_at / collected_at / duration_seconds / runner / model /
  effort / stdout_sha256 / stdout_bytes / stdout_lines / stderr_bytes / rc / job_id /
  attempt_nonce / timeout_seconds`；`duration_seconds` 是 **`terminal_at − started_at` 的自然耗时**
  （断言落在 900..940 区间，构造上排除了「墙钟外壳」与「从 dispatch 起算」两种错法）；
  `stdout_sha256` 与真实文件重算值相等；`stdout_path` **只在 `ok` 时出现**。
- **stderr 只出计数**：断言 `"fake-stderr" not in json.dumps(payload)` —— 未过出境 scan 的正文
  MUST NOT 出现在任何可能落进 tracked 报告的通道里。

### ⑦ 超时上限复用既有 async timeout 配置项（默认 900、范围 1..3600、越界拒绝）

**先查了读取路径**：全仓 `grep -rln "async-timeout-seconds"` 只命中两份评审 SKILL、
`openspec/config.yaml` 的注释块与 change 文档 —— **没有任何脚本解析它**；它由主 session 按
`sdflow-spec-review/SKILL.md` 调用协议 ① 直读 `config.yaml`（校验 1..3600、回落 900），再以
`--timeout` 传给 dispatch。∴ 本票的「复用」= 接到那条既有链上，**不新造第二份解析**：

- `await/status/collect` 的默认上界取 `job.json.timeout_seconds`（dispatch 当时记下的那个值，
  Task 1 已按 `MIN/MAX/DEFAULT_TIMEOUT_SECONDS` 校验过）——锚：
  `test_await_default_upper_bound_comes_from_job_metadata_timeout`（断言 `timeout_seconds == 900`）。
- `--timeout` 显式传入时走**同一组常量**校验：`test_await_rejects_out_of_range_timeout[0/3601/abc/-1]`。
- `test_default_timeout_and_range_are_the_single_shared_constants` 钉死 `900` / `(1, 3600)` / `30`。
- 元数据里的 `timeout_seconds` 越界/非整同样判 `CORRUPT`（`load_job_metadata`）。

### 端到端接缝

`test_dispatch_worker_await_collect_end_to_end_offline` —— 用 Task 1 的 fake-claude `run` 模式真跑
`dispatch → worker` 写出盘面，再让本票的 `await → collect` 去认。这是「Task 1 写的证据格式与
Task 2 读的格式是否真的对得上」的唯一机械锚（两票各自绿但对不上，是跨票最典型的缺口）。

### CLI 与派生函数不是两份实现

`test_status_cli_is_a_thin_shell_over_derive_status`（`7 × 3 = 21` 参数）—— 逐组合断言
`CLI 单行 JSON == JOB.derive_status(...)` 且退出码与 `ok` 一致。没有这条，126 格笛卡尔只证明了
那个**没人调用的函数**是对的。

## 反向变异（判据是「锚会不会红」，不是「有没有新增测试」）

在实现副本上逐条改回错误形态、跑对应锚、`git checkout` 还原（仓内文件零残留，末次
`git status --short` 已空）：

| # | 变异 | 结果 |
|---|---|---|
| M1 | stdout 读取提前到 rc 判定之前 | **RED** `test_status_never_reads_stdout_before_terminal` |
| M2 | `rc=3` 并入 exec-error | **RED** 7 条（笛卡尔 rc3 六格 + collect 表） |
| M3 | worker 上界改从 `dispatched_at` 起算 | **RED** `…counts_from_trusted_started_at_plus_grace` + `…timeout_override…` |
| M4 | 把 `unavailable`/未知 state 也当已终结 | **RED** 4 条（含 CLI 层与笛卡尔） |
| M5 | collect 不落 collected witness | **RED** `test_collect_is_idempotent_byte_for_byte` |
| M6 | 缺 terminal witness 也认 rc | **RED** `test_terminal_rc_without_a_terminal_witness_is_corrupt` |
| M7 | 不核验 stdout digest | **RED** `test_collect_detects_a_stdout_digest_mismatch` |
| M8 | 未终态也当可收集 | **RED** `test_collect_before_terminal_…` |
| M9 | await 撞外层上界就落 timeout | **RED** `test_await_exhausting_max_wait_stays_running_and_is_not_timeout` |
| M10 | RUNNING 的 reason_code 给 `ok` | **RED** 笛卡尔 2 格 + `test_no_pending_lost_or_corrupt_combination_ever_yields_ok` |
| M11 | await 见 RUNNING 也 break（早退） | **RED** `…never_early_timeouts` + 端到端 |

**M1 顺带纠出一处命名过度声明**：原 `test_collect_before_terminal_is_not_ok_and_reads_no_stdout`
在 M1 下**照样绿**——它守的是**出口**（不给 `stdout_path`、不落 witness、不把正文带进自己的
stdout），不是「有没有读过」。已改名为
`…_and_leaks_no_partial_output` 并在 docstring 里写明该边界与真正的读取锚在哪。
（名字过度声明的测试 = 假绿的伪装形态，本仓 CLAUDE.md ③ 的直接靶子。）

## 测试结果（实跑，非自述）

```
/usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_job.py -q
  → 239 passed in 67.74s          （Task 1 的 49 条全部保持绿，新增 190 条）

/usr/bin/python3 -m pytest -q
  → 2389 passed, 8 skipped, 3 xfailed in 225.97s
     基线 2199 passed / 8 skipped / 3 xfailed ⇒ 净 +190，skip/xfail 数**未变**（无静默降级）

git diff --check → 无输出
```

> 备注（本机环境事实，非文档问题）：本机裸 `pytest` 不存在、默认 `python3` 未装 pytest，
> 必须 `/usr/bin/python3 -m pytest`。

## 未做 / 降级项（明说，不含糊）

| 项 | 状态 | 理由 |
|---|---|---|
| `reconcile --run-dir`、identity-safe cleanup（`stop → 核验子树 → rm`） | **未做** | 票面范围边界明写归 **Task 3**。本票在需要它的两处只**留出接口**：`RESERVED` 状态带 `unknown_cost: true` 且 await 立即返回；`LOST` 只归类不做任何破坏性动作 |
| `--effort high --safe-mode --no-session-persistence` 四旗与 `claude logs` canary | **未做** | 归 **Task 4**。collect 返回的 `effort` 取自 `job.json`（Task 1 已下发 `SDFLOW_VOICE_EFFORT`，下游 `outside-voice.sh` 尚未消费——Task 1 报告已交接此事）⇒ 该字段目前证明的是**下发值**，不是 runner 实际生效值 |
| `setup.sh` 安装快照 / 两份 SKILL 的调度段改造 | **未做** | 归 **Task 5**（Task 1 报告已交接：`setup.sh` 未写 `capability-manifest.json` ⇒ 真实安装态 preflight 仍必红） |
| 真实模型 efficacy | **未做** | 归 **Task 6**。本票全部用 fake claude + fake helper，**MUST NOT** 当 efficacy 证据 |
| `status`/`collect` 的 NFR「≤5 秒」 | 只有**弱**锚 | `test_status_cli_emits_single_line_json_for_a_running_site` 断言 `elapsed < 5`，但 fake claude 是秒退的 ⇒ 该断言在本机恒真。真上界由 `CLI_PROBE_TIMEOUT_SECONDS=5`（Task 1 常量）保证，终态站点则完全不探 liveness |

## Concerns（交编排层裁决，本票已按设计原样交付）

1. **startup deadline = dispatch 时刻 + 5 秒是硬判据，可能误杀 supervisor 冷启动慢的合法 worker。**
   `design.md` 状态机原文即「STARTING ── startup deadline 到且无 started sidecar ──▶ LOST」，
   无 liveness 限定，故**照原样实现**。风险面：dispatch 本身要等到 job 进 agents roster 才返回
   （Task 1 的 nonce 核验），worker 第一动作就是发布 started sidecar，∴ 正常路径余量充裕；
   但 supervisor 冷启动慢时会把一次**已计费**的合法 dispatch 降级成 `exec-error` + 同族 fallback。
   可选收敛（**未实施**，属改设计）：STARTING 过期时若 liveness 仍为 `working`，改为继续等到
   `dispatched_at + startup + timeout + grace` 的兜底上界。**建议留到 Task 6 真实 efficacy 跑完后
   按实测决定**——现在改属于拿推测反驳设计。
2. **`<site>.collected.json` 是本票新增的第 6 个 sidecar。** 它不是可变 status（首写者胜、只写一次），
   但确实是新增的落盘面。理由：OVBG-02 明写「collect SHALL 幂等返回**首次** `collected_at`」，
   跨进程调用下这只能靠落盘。已在实现的模块 docstring「盘面即状态」段落里写明它与 ADR-2 的关系。
   Task 3 的 reconcile 需要知道它的存在（terminal 已 collect 过的 job 可直接 `rm`）。
3. **rc=3 → `secret-hit` 是本票在票面 5 格之外补的一格。** 依据是 HAE-09「reason_code 枚举语义
   MUST 保持不变」+ SKILL ⑦ 的既有同步分支表。若编排层认为应并入 exec-error，改一行
   （`RC_SECRET_HIT` 分支）即可，但需同步改 SKILL ⑦ 与 `_expected_classification`。

## 未触碰（按票面硬约束核过）

`git show --stat b4c1488` 只含两个文件：`sdflow-init/assets/hack/outside-voice-job.py` 与
`sdflow-init/tests/test_outside_voice_job.py`。
**未改** `proposal.md` / `design.md` / `specs/` / `tasks.md`；
**未勾** `superpowers-plan.md` 任何复选框；**未打** `task<N>-` 完成标签（commit subject 为普通
`feat(outside-voice): …`）。
