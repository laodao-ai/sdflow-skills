# Task 3 · fix1（双轴审轮 1：Standards FAIL + Spec FAIL）

被修对象：`sdflow-init/assets/hack/outside-voice-job.py`、`sdflow-init/tests/test_outside_voice_job.py`。
两条 Critical **同源**：`cleanup` 的子树核验在两条不同路径上都能给出假的「已清理」。按面治（`CLAUDE.md` 基准 3）
一次扫全，不只补被点穿的两处。

---

## C1（Standards）· `probe_subtree` 组长分支的假阳 —— 前提被本仓自己的 helper 证伪

### 发现

旧 docstring 断言「worker → bash helper → claude 都是同步 fork，**不换组** ⇒ `killpg(pgid, 0)` 是子树是否
有活口的直接答案」。这个前提是假的：`outside-voice.sh:428-431 / 474-481` 白纸黑字写着 GNU timeout 会
`setpgid` 把自己放进**独立进程组**（PGID 恒等于 timeout 自身 PID）—— 真正烧额度的 runner 整棵在别的组里。

**本机复现（`gtimeout` = `/opt/homebrew/bin/gtimeout`）**：worker 自建组 25874（pgid 25874）→ 子
`gtimeout 60 sleep 60` 落到组 **25876**；`kill -9 25874` 后

```
25874 pid GONE      25874 pgid GONE      ← 旧代码据此判 EXITED
25876 pid alive     25876 pgid alive     ← 而 runner 整棵还在跑、还在计费
```

触发路径不是边角：`cleanup --cancel` 命中孤儿逃逸（父被 SIGKILL ⇒ bash trap 不执行）时正是此形态 ⇒
`stopped-removed` / `fallback_allowed=True` ⇒ 自动同族 fallback 在一次仍在计费的 voice 上再叠一次。

### 修法

`probe_subtree` 重排为一条**只用直接信号判 exited**的判定阶梯（`outside-voice-job.py`，函数 docstring
即契约正文）：

| 步 | 判据 | 结论 |
|---|---|---|
| ① | started witness / worker identity 缺席 | `unverifiable` |
| ② | worker pid 存活 / 不可判定 | `alive` / `unverifiable` |
| ③ | worker 是组长且组内仍有活口 | `alive`（组探针**只判 alive，永不判 exited**） |
| ④ | `<site>.runner.pid` 在场 | 探 pid+pgid：任一活 ⇒ `alive`；两者都确定不存在 ⇒ `exited`；否则 / 文件损坏 ⇒ `unverifiable` |
| ⑤ | ④ 缺席 + terminal witness 在场 | `exited`（`subprocess.call` 同步返回 ⇒ helper 已 exit、其 `wait` 已回收 runner） |
| ⑥ | 两个信号都没有 | `unverifiable`（**旧代码在这里返回 exited**） |

新增 `RUNNER_PID_SUFFIX` / `runner_pid_path()` / `read_runner_pid()` / `probe_runner_pid()`。
`read_runner_pid` 与 `<site>.rc` 同构：纯十进制单值、strict `\A\d+\Z` 解析、坏值 ⇒ `corrupt` ⇒ fail-closed。

⑤ 的**残余已在 docstring 显式登记**：helper 若被 SIGKILL 打死（trap 不执行），`subprocess.call` 同样返回、
witness 同样发布，而孤儿 runner 仍活着 —— 这个窄口只能由 ④ 的直接信号关掉，故 ④ 一旦在场 MUST NOT 走到 ⑤
（代码顺序即此约束，锚见 `test_probe_subtree_answers_from_the_runner_pid_sidecar_before_the_disk_inference`）。

### 与评审建议的一处**明说的偏离**

评审建议 `<site>.runner.json`；本票落成 **`<site>.runner.pid`（裸十进制）**。理由：这个文件由 **shell** 写，
JSON witness 要它正确拼出 `schema_version`/`site`/`run_id`/`attempt_nonce` 四项才不被判 corrupt，
**任一项写错的代价是 cleanup 永久 fail-closed**；而 identity 绑定在这里并不承重（run-dir × site 每次 attempt
唯一 —— 同 site 重复 dispatch 是硬失败），且两个误判方向都安全（串到别人的活 pid ⇒ 判 alive；pid 被复用
⇒ 同样判 alive）。格式与既有 `<site>.rc` 同构，不新造第二种口径。若 Task 4 认为需要 JSON，改 `read_runner_pid`
一处即可，消费侧其余不动。

### 机械锚

| 测试 | 钉住什么 |
|---|---|
| `test_probe_subtree_will_not_call_a_dead_group_leader_exited_when_a_child_escaped` | **真起一对进程**（`os.setpgrp()` 组长 + 真 `gtimeout` 换组逃逸）：先机械断言 `getpgid(runner) != leader`（换组是前提不是假设）、`_pgid_alive(leader) is False`（骗人的信号真的出现了）、`_pid_alive(runner) is True`（runner 真的还活着），再断言无信号 ⇒ `unverifiable`、有信号 ⇒ `alive` |
| `test_probe_subtree_is_unverifiable_for_a_dead_group_leader_without_a_runner_signal` | 组空 ⇒ 不可判 exited；同形态 + 已死 runner 信号 ⇒ 才判 exited |
| `test_probe_subtree_answers_from_the_runner_pid_sidecar_before_the_disk_inference` | 活 runner + 已发布 terminal witness ⇒ 仍 `alive`（④ 压过 ⑤） |
| `test_probe_subtree_is_unverifiable_when_the_runner_pid_sidecar_is_corrupt` | 坏信号 ≠ 无信号，MUST NOT 静默退回弱推断 |
| `test_worker_hands_the_runner_pid_file_path_down_to_the_helper` | 跨票交接的机械锚（见下节） |

---

## 🔴 跨票交接 —— **Task 4 MUST 做的一件事（漏了这条洞就还在）**

**Task 4 的 implementer 请读这一节。**

本票**未改** `outside-voice.sh`（属 Task 4 文件）。C1 只做到了 fail-closed：runner 的直接信号缺席时，
`probe_subtree` 的组长分支判 `unverifiable` 而不再假称 `exited`。**这意味着在 Task 4 落地之前，
`cleanup --cancel` 对「无 terminal witness 的站点」永远走 `orphan-warning`、永远不解闸 fallback。**
这不是 bug，是诚实降级 —— 但它要靠 Task 4 才回到可用。

**Task 4 MUST 在 `outside-voice.sh` 的 `exec` 路径里做**：

1. 读环境变量 **`SDFLOW_VOICE_RUNNER_PID_FILE`**（worker 已下发，值 = `<run_dir>/<site>.runner.pid` 绝对路径；
   已由 `test_worker_hands_the_runner_pid_file_path_down_to_the_helper` 钉死）。
2. 在 **spawn runner 之前 / `OV_RUNNER_PID=$!` 之后立刻**，把 `OV_RUNNER_PID` 以**纯十进制**
   （无前后缀、无换行要求但允许尾随换行）**原子**写入该路径（临时文件 + `mv`）。
   `OV_RUNNER_PID` == GNU timeout 自身 PID == 它 `setpgid` 出的那个独立组的 PGID —— 这正是消费侧要探的东西。
3. 变量为空 / 未设置时**什么都别写**（宁可缺信号 ⇒ 消费侧 fail-closed，也不要写个空文件 ⇒ 判 `corrupt`）。

**为什么不能省**：worker 自己的进程组**圈不住** timeout 自建的组。缺这个文件 ⇒ 「runner 子树是否退出」
在盘面上**没有任何直接证据**，⑤ 的 terminal-witness 推断又恰好在「helper 被 SIGKILL、孤儿 runner 逃逸」
这一个场景下失效 —— 而那正是 `outside-voice.sh:482-488` 自己登记的残余 (a)。**Task 4 改完 isolation flags
但没写这个文件，这条洞仍在。**

契约的单一源 = `outside-voice-job.py` 模块 docstring 的 `worker` 段（已写入）+ `probe_subtree` docstring 的 ④。

---

## C2（Spec）· roster 无此 job 时 cleanup 无条件返回成功

### 发现

`run_cleanup` 的 `IDENTITY_ABSENT` 分支直接 `return _cleanup_payload("absent", True, "…无需清理")` ——
既不探子树也不保留 orphan warning。而 **LOST 最主要的产生路径恰恰是 `probe_liveness` 返回 `missing`**
（= roster 无此条目 ⇒ `derive_status` 判 LOST）。评审亲跑复现：worker pid 真活着，reconcile 输出
`{"state":"LOST","ok":true,"action":"absent","unknown_cost":false,"orphan_warning":null}` ——
一个仍在跑、已计费的 worker 被报成干净通过。反向后果同源：子树确已退出时 `fallback_allowed` 也恒 False，
`ORPHAN_WARNING_TEMPLATE` 承诺的「跑 cleanup 解闸」对该路径**永不解闸**。

**测试盲区**：全部 LOST 用例的 roster 都仍列着该 job，`missing` 通道**从未穿过 cleanup**。

### 修法

ABSENT 分支改为先 `probe_subtree`：

- `exited` ⇒ `state="absent"`、`ok=True`、**`fallback_allowed=True`**（解闸这条反向后果一并修好）
- `alive` / `unverifiable` ⇒ `state="orphan-warning"`、`ok=False`、`unknown_cost=True`、orphan warning
  （含 job id 与判据 detail）

roster 无条目 ⇒ 没有 job 可 `stop`/`rm`，故本分支仍**零破坏性调用**（锚在 fake `claude` 调用日志上）。

### 机械锚

| 测试 | 钉住什么 |
|---|---|
| `test_cleanup_still_verifies_the_subtree_when_the_roster_no_longer_lists_the_job` | 真活 worker + 空 roster ⇒ `orphan-warning` / `subtree=alive` / `unknown_cost` / `fallback_allowed=False` / 零 stop-rm |
| `test_reconcile_will_not_report_a_site_clean_when_the_roster_dropped_a_live_worker` | 评审那条复现的 CLI 级版本：`state=LOST` + `action=orphan-warning` + `orphan_warnings==["design-voice"]` + exit 1 |
| `test_cleanup_is_idempotent_when_the_roster_no_longer_lists_the_job`（改） | 正向对照：子树**已证退出**才是幂等成功，且此时 `fallback_allowed=True`（旧版恒 False） |

---

## Important · `run_reconcile` 站点集为空时静默报绿

`reconcile --run-dir <空目录> --site design-voice` 旧版给 `{"ok": true, "sites": []}` + exit 0
（`all([])` 为真且无 warning）。操作者恢复 abandoned run 时敲错 site / 点错 run-dir，拿到的是「一切正常」，
**而那正是成本未知的场景**。

**修法**：抽出 `_reconcile_payload()`（一处算 warnings/unknown/ok），两个空集分支分治 ——
`--site` 未命中 ⇒ `state="usage-error"` + `cmd_reconcile` 映射 **exit 2**；run-dir 内一个站点都没有 ⇒
`ok=False` + 显式 detail（exit 1）。锚：`test_reconcile_rejects_a_site_the_run_dir_does_not_hold`、
`test_reconcile_does_not_report_an_empty_run_dir_as_all_clear`。

## Minor（fold）· `subtree` 字段语义不自洽

rc 已发布分支只把探针结果记进 payload（`alive` 也照 `rm` 且 `fallback_allowed=True`）。按评审裁定保留字段、
补注释说明它是**留痕不是闸门**：rc 已发布 ⇒ 额度已花完，而 fallback 的意义是「重试一次没拿到结果的 voice」，
已 collect 的终态不存在「再叠一次费用」的问题；探针值留给人工审计（真在这里读到 `alive`，说明 helper 是被
SIGKILL 打死的，见 `probe_subtree` ⑤ 的残余登记）。

---

## 面治自查：「还有哪条路径能在子树未证退出时返回成功 / 放行 fallback？」

逐条过了 `run_cleanup` / `reconcile_site` / `run_reconcile` 的**全部** `ok=True` 与 `fallback_allowed=True` 出口：

| 出口 | 现状 | 判定 |
|---|---|---|
| `stopped-removed` | 门在 `wait_subtree_exited() == EXITED` | ✅ 已核验 |
| `absent` + fallback | **本次新加**：门在 `probe_subtree() == EXITED` | ✅ 已核验（C2） |
| `removed` + fallback（rc 已发布且已 collect） | 无子树门，只记 `subtree` 字段 | ⚠️ 保留（评审裁定 Minor）：额度已落袋、结果已在手，fallback 语义不适用；已补注释 |
| `reconcile_site` → `pending` `ok=True` | 站点仍在 deadline 内、roster 认得它 | ✅ 不声称已清理，也不放行 fallback |
| `reconcile_site` → `STATE_MISSING` / 残留 reserve | `ok=False` / `manual-cleanup-required` + unknown_cost | ✅ 原本即 fail-closed |
| `run_reconcile` 空站点集 | **本次新加** ok=False / usage-error | ✅（Important） |

另一处**顺带被扫到的同类面**（非评审点名，属同一片一致性）：`job.json` 在但 started witness 缺席
（worker 从未起跑）时，ABSENT 分支现在也走 `probe_subtree` ⇒ `unverifiable` ⇒ orphan warning。这与
`test_cleanup_leaves_an_orphan_warning_when_the_subtree_exit_cannot_be_proven` 的既有立场一致：
supervisor 接了这个 job，它有没有烧过额度**不可证**，MUST NOT 报干净。

---

## 测试结果（如实）

**TDD 红 → 绿**：先把源码 `git show ec0d690:` 还原成 fix 前版本，跑新锚 —— **10 failed**，
其中两条 Critical 的失败信息就是评审描述的形态：

```
test_probe_subtree_is_unverifiable_for_a_dead_group_leader_without_a_runner_signal
E   AssertionError: ('exited', 'worker pid=31591 与其进程组 pgid=31591 均已不存在')
E   assert 'exited' == 'unverifiable'

test_cleanup_still_verifies_the_subtree_when_the_roster_no_longer_lists_the_job
E   {"detail": "supervisor roster 已无此 job，无需清理", … "state": "absent",
E    "subtree": null, "unknown_cost": false}   assert 0 == 1

test_reconcile_will_not_report_a_site_clean_when_the_roster_dropped_a_live_worker
E   {"ok": true, "orphan_warnings": [], … "state": "LOST", "unknown_cost": false}  assert 0 == 1
```

还原修复后：

- `pytest sdflow-init/tests/test_outside_voice_job.py -q` → **291 passed**（fix 前 283）
- 全量 `/usr/bin/python3 -m pytest -q` → **2441 passed, 8 skipped, 3 xfailed**
  （基线 2433 / 8 / 3，+8 = 本次新增 8 条用例；另有 1 条既有用例被**改**而非新增）
- 全量首跑曾报 **2440 passed, 9 skipped**：多出的那次 skip 是环境敏感的既有守卫
  （`test_outside_voice_child_lifecycle.py:436` 的信号风暴复现率 / `_dead_pid()` 的 pid 回绕保护），
  **两次全量跑都 0 failed**。如实登记，未做进一步追查（低概率、无失败、追查成本不成比例）。
- `git diff --check` 干净。

## 未修项与理由

| 项 | 理由 |
|---|---|
| `status` 未接完整四项 roster 核验 | 两轴独立裁定为合理范围解读（spec 限定「破坏性操作前」，`status` 零破坏性动作）——**MUST NOT 改** |
| `test_reconcile_ignores_supervisor_jobs_it_holds_no_metadata_for` 结构性恒真 | 守护测试，Standards 轴判可接受 |
| C2（cleanup 最多 3 次 `claude agents` 冷启动） | 低频人工路径，Task 6 实测后再说 |
| C3（`parse_utc_iso` 宽 except） | 已是 defer 项 T217，本轮不扩大 |
| `removed` 分支的 fallback 未加子树门 | 见上「Minor」与面治表：评审裁定 + 语义不适用；已补注释使字段不再看着像闸门 |

**未改动的文件（契约要求）**：`proposal.md` / `design.md` / `specs/` / `tasks.md` / `outside-voice.sh`
（`git status` 亲验：本轮只有 `outside-voice-job.py` 与 `test_outside_voice_job.py` 两个 M）。
未勾任何复选框、未打 `task3-` 完成标签。
