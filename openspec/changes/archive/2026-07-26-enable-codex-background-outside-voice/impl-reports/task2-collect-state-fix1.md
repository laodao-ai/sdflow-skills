# Task 2 · fix 轮 1（Standards 轴 FAIL → 修复）

**范围**：`sdflow-init/assets/hack/outside-voice-job.py` + `sdflow-init/tests/test_outside_voice_job.py`
**基线**：`6b0313e`（fix 前）。行号一律取**修后**文件。
**未动**：`proposal.md` / `design.md` / `specs/` / `tasks.md` / `superpowers-plan.md`（未勾框、未打完成标签）。

---

## I1（Important）· collect 把「rc 尚未发布」的 LOST 判定永久冻结

**发现**：`cmd_collect` 只看 `payload["terminal"]` 就落 `collected.json`。但 LOST（startup deadline
过期 / liveness 终态无 rc）与 RESERVED 是**非 durable 证据**推出的终态——worker 可能只是慢。
一旦冻结，之后真实发布的 `rc=0` + findings 再也取不回来，二次 collect 只会原样回放
`LOST/exec-error`、`stdout_path` 缺席 ⇒ 一次**已计费**的 voice 被静默丢弃。

**修法**（`outside-voice-job.py:1447`）：`_first_writer_wins_json` 的落盘条件从
`kind == "ok"` 收紧为 `kind == "ok" and status.get("rc") is not None`。
无 rc 的终态**只返回、不冻结**，交 Task 3 reconcile。

依据是 `design.md:214` 的原话 —— 「**terminal rc 后** collect 幂等」。实现把它扩到了 rc 之前，
属自行加宽；本次收回到 spec 原文口径。docstring（契约单一源）同步写明这条边界。

**副作用（已确认可接受）**：`rc` 文件存在但内容非纯十进制（`rc_bad` → `CORRUPT`）时
`status["rc"]` 亦为 `None`，故也不冻结。该形态的重算是确定性的（rc 文件内容不变 ⇒ 同一
`state/reason_code`，仅 `collected_at` 逐次刷新），且「坏 rc 可被 reconcile 修正」方向正确。
既有 `test_collect_rc_to_reason_code_table[rc_bad]` 仍绿。

**机械锚**：`test_collect_does_not_freeze_a_lost_verdict_reached_before_rc_was_published`
（`sdflow-init/tests/test_outside_voice_job.py:1551`）——
collect#1 判 LOST 且断言 `collected.json` **不存在** → 补齐 started/terminal/rc=0 + `REAL FINDINGS`
→ collect#2 拿到 `ok` / `SUCCEEDED` / 真实 `stdout_path` + digest → collect#3 逐字节等于 #2（rc 后幂等仍在）。
反向验红（fix 前）：`assert not collected.json.exists()` 失败。

## I2（Important）· await 每个 poll 都 spawn 一次 `claude agents --all --json`

**发现**：`cmd_await` 每轮都调 `derive_status(..., liveness=None)`，而 `derive_status` 在 rc 缺席时
必探针。默认 `poll-interval=0.5s`、上界 `timeout(3600)+grace(30)` ⇒ 单站点单次 await 最多
~7260 次 Node CLI 冷启动（实测 0.17s/次，CLI 卡顿时每轮吃满 `CLI_PROBE_TIMEOUT_SECONDS=5`），
两站点并行翻倍。

**修法**：新增 `LIVENESS_PROBE_INTERVAL_SECONDS = 5.0`（`:896`），`cmd_await` 内做**探针独立节流**
（`:1390-1404`）：盘面仍按 `poll-interval` 读（本地 stat，便宜），liveness 每 ≥5s 才真探一次，
其余轮次把缓存值喂给 `derive_status`。缓存刷新条件是 `payload["liveness"] is not None`
（⟺ 本轮真的走到了探针分支；rc 已发布 / 元数据坏 的早退路径不探也不刷新）。

**代价**：liveness 变化（job 突然消失）最多晚 5 秒被看见。**不推迟任何真实终态的识别**——
rc 一旦发布就优先于 liveness 参与判定（ADR-2），LOST 本就只是「探不到」的兜底分类。

**机械锚**：`test_await_throttles_the_liveness_probe_far_below_the_poll_rate`（`:1705`）——
`--poll-interval 0.05 --max-wait 1.2`，用 fake claude 调用日志统计 `agents` 次数，断言
`len(probes) * 4 < polls`（polls 由 `waited_seconds/0.05` 反推）、`polls >= 10`（确认盘面真的密集轮询过）、
`liveness == "working"`（确认仍真探过，不是假绿）、`LIVENESS_PROBE_INTERVAL_SECONDS >= 5`。
反向验红（fix 前）：13 probes vs 25.2 polls → `13*4 < 25.2` 失败。

## M1 · `open(...).read()` 未关闭句柄（CR-04）

三处改 `with`：`stdout_read_evidence`（`:972`）、`stderr_stat_evidence`（`:985`）、`read_rc`（`:1066`）。
**机械锚**：无新增用例（纯资源纪律，无行为差异）；由既有 collect/status 全套（245 条）回归覆盖。

## M2 · `LIVENESS_ALIVE` dead constant

先 `grep -rn LIVENESS_ALIVE .`（排除 `.git`）确认全仓零引用（唯一命中是本次评审包
`task2-review-package.diff` 这一产物）⇒ **删除**。其上方注释描述的是 `LIVENESS_TERMINAL` 分档，
原样保留。**机械锚**：全量套件绿（若有隐藏消费者会 `AttributeError`）。

## M3 · `derive_status` 自递归无深度保护

**修法**：加 `_rechecked=False` 形参（`:1133`），判 LOST 前的「再看一眼 rc」只重入一次（`:1227-1230`）。

**实测到的真实后果比原判更糟**：无界重入不是「理论上无限递归」——`RecursionError` 会被
`parse_utc_iso` 的 `except Exception` 吞掉，于是静默降级成
`CORRUPT / "job metadata dispatched_at 时刻不可解析"`（即：一个**假的元数据损坏**判定）。
这一点在写红测试时由失败输出直接暴露，已写进代码注释。

**机械锚**：`test_rc_recheck_before_declaring_lost_is_bounded_to_one_retry`（`:1195`）——
monkeypatch `JOB.read_rc` 恒报「不存在」而 rc 文件实际在盘上（模拟 isfile 与 read 之间被移走），
断言得到 `LOST/exec-error`。反向验红：得到 `CORRUPT`（上述吞异常路径）。

## M4 · 模块 docstring 与 exit 2 契约不符

**修法**：`status` / `await` / `collect` 三个子命令的 exit 行统一补 `| 2=usage-error`；
「派生输出」节末尾新增一段警示：exit 2 走 reject 形状
（`{ok, state:"usage-error", reason_code, fallback_allowed, detail}`，**无 `terminal` / `rc` / 时刻字段**），
调用方 MUST 先看 exit code、MUST NOT 按 0|1 两分法直接读 `terminal`。
顺带把 I1 的幂等边界、I2 的探针节流写进各自子命令段（契约单一源同步）。

**机械锚**：`test_readonly_usage_error_exits_2_and_is_documented_in_the_contract_source`（`:1761`，
三个子命令参数化）——断言 exit 2 + `state == "usage-error"` + **`"terminal" not in payload`**，
并断言 `JOB.__doc__.count("2=usage-error") >= 3`（逐子命令写明，防只补一处）。

---

## 测试结果（如实记录）

```
/usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_job.py -q
245 passed in 71.00s
```

```
/usr/bin/python3 -m pytest -q
2395 passed, 8 skipped, 3 xfailed in 220.70s
```

基线 2389 passed / 8 skipped / 3 xfailed ⇒ **+6 全部为本轮新增锚**（I1×1、I2×1、M3×1、M4×3 参数化），
无回归、无跳过新增。`git diff --check` 干净（无空白错误）。

## 未修项（编排层已裁定，本轮 MUST NOT 顺手做）

| 项 | 归属 |
|---|---|
| Spec 轴 Minor 1：LOST 未带 `unknown_cost` / orphan-warning | Task 3（子树核验会在此路径上翻该字段） |
| Spec 轴 Minor 2：SKILL 侧对越界 config 的 clamp | Task 5 |
| `collected.json` × Task 3 reconcile 交互 | Task 3 |
| effort 是否真送达 runner | Task 4 |
| NFR 真实上界 | Task 6 |
