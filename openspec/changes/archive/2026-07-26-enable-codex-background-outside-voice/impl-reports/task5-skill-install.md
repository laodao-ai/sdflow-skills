# Task 5 impl report —— 两份评审 SKILL 的宿主自适应调度切换与安装快照

**R-ID**：HAE-08 / HAE-09 / OVBG-01（落笔前已逐条通读 delta spec 的 SHALL + 全部 Scenario）
**Blocked-by**：Task 3、Task 4（均已 checkpoint，起手 HEAD = `0345400`）

---

## 一、做了什么

| 文件 | 改动 |
|---|---|
| `sdflow-spec-review/SKILL.md` / `sdflow-code-review/SKILL.md` | `sdflow:async-branch` marker 段整体重写（宿主分流：claude-host 保留 harness async + sync 降级；codex-host 走 job helper 的 preflight → dispatch → await → collect → cleanup）；**Codex 同步 300 秒兼容分支彻底删除**；marker 段外的 dispatch-manifest 扩为 4 列（+ `attempt_nonce`，`<task_id>` 列在 codex-host 填 `job_id`）；fallback 段里「与 codex 侧 300s 不对称」这句被本次删除弄陈旧，同步订正 |
| `setup.sh` | `install_sdflow` 新增 `*.py` 安装循环（cp + exec 位）；**先删 manifest → 拷贝 → 最后调 `install-manifest` 写快照**；`$_py` 解释器探测上移到 `install_sdflow` 之前（与 retire-hooks 共用同一个） |
| `sdflow-init/assets/hack/outside-voice-job.py` | 新增 `install-manifest [--dir <d>]` 子命令 + 头注释契约条目 —— 安装步据此调**同一份** `write_manifest()`/`compute_manifest()`，shell 侧零 hash 口径 |
| `hack/tests/test_async_branch_parity.py` | +9 条段内**内容** golden（1 负向 + 8 正向） |
| `sdflow-init/tests/test_setup_sdflow.py` | +6 条安装快照用例（`TestCapabilitySnapshot`） |
| `sdflow-init/tests/test_outside_voice_job.py` | +5 条安装态用例（`install-manifest` CLI × 2、安装态 preflight、安装态 skew、**安装态 lifecycle smoke**） |

**未改**（按执行契约）：`proposal.md` / `design.md` / `specs/` / `tasks.md` / `openspec/specs/`；未勾任何复选框、未打 `task5-` 完成标签。

---

## 二、逐条验收标准 → 机械锚

| 验收标准 | 机械锚 |
|---|---|
| 两 SKILL 等值段同步修改、Codex sync 300 秒路径删除、**负向 golden** | `test_codex_sync_300s_compat_branch_is_deleted`（矩阵行级：codex 行内既不许有 `sync`（先摘 `async` 子串再查）也不许有 `300`）。**反向变异实证**：把 `\| sync \| host=codex \| 300 \| ≥330000ms \|` 接回去 → `1 failed`；撤回 → `1 passed`（本轮真跑过，非推断） |
| job id / site / attempt nonce 追加 dispatch manifest | `test_dispatch_manifest_records_job_id_and_attempt_nonce`（两侧各查一次；printf 行现为 4 列且同时含 `job_id` / `attempt_nonce`） |
| Step3 barrier 用有界 await/collect；rc → `ok/timeout/exec-error/secret-hit` | 段内 ⑤ codex 分支（`collect` 幂等 + **先看 exit code**，`2`=usage-error 形状不同）与 ⑥（`await` 有界、helper 自定上界）；`test_codex_branch_goes_through_the_background_job_helper` 守四个子命令俱在 |
| RUNNING 不早退 / 外层 wait 回收后不重派 / stderr 不进 findings 与报告 | `test_barrier_invariants_survive`（`MUST NOT 自造轮询循环` + `timeout 只允许由实际 124 产生` + `MUST NOT 重新 dispatch`）、`test_stderr_never_reaches_findings_or_the_tracked_report` |
| 锚行契约 / `reason_code` 枚举 / anchor 矩阵 / `declared-sites` 公式不变 | `test_anchor_line_reason_code_enum_is_unchanged`（逐字面量）；`git diff` 显示 `declared-sites` 段、锚行、`anchor_lint` 相关文件**零改动**；全量套件里既有 `anchor_lint` 笛卡尔 golden 全绿 |
| parity gate 证明 marker 段逐字节一致 | `python3 hack/check_async_branch_parity.py` → `✅ 2 处 async host 调度段逐字节一致`；段是**同一份文本 splice 进两侧**产生的，非手抄 |
| 同代 capability 快照原子安装；执行权限/解释器、安装中断、新旧混配、stale copy 有测试 | `TestCapabilitySnapshot` 六条：`test_installs_job_helper_with_exec_bit_and_python3_interpreter`（exec 位 + `#!`/python3）、`test_writes_a_capability_manifest_that_verifies_against_installed_bytes`（逐成员 sha256 对齐安装后字节）、`test_rerun_keeps_the_snapshot_consistent`、`test_hand_mutated_install_is_skew_and_fails_closed`（新旧混配/stale copy）、`test_rerun_heals_a_stale_copy`（对照组：证上条的红来自 skew）、`test_interrupted_install_leaves_no_consistent_snapshot`（真制造中断：把已安装 shell helper 置 0444 ⇒ 下次 `cp` 失败 ⇒ `set -e` 中止 ⇒ **manifest 已先删、未重写** ⇒ 无「自洽但陈旧」的快照） |
| 从临时全局 home 的已安装路径跑通 lifecycle 的无模型 smoke | `test_installed_path_runs_dispatch_collect_cleanup_offline`：真跑 `bash setup.sh`（HOME/SDFLOW_HOME → tmp）→ dispatch（`job_id`/`attempt_nonce`/`dispatch_duration_seconds ≤ 5s`）→ await（`terminal=true`、`reason_code=ok`）→ collect（`unknown_cost=false`、`runner/effort`、`duration_seconds`）→ cleanup（`removed=true`、`orphan_warning=None`，且 fake `claude` 调用日志里确有 `("rm","5eeded01")`） |
| manifest/hash skew ⇒ preflight fail-closed + 刷新指引 | `test_installed_snapshot_fails_closed_on_manifest_skew_with_a_refresh_hint`（exit 1、`checks["capability-manifest"].ok=False`、stderr 含 `setup.sh`） |
| 使用说明五项 | 段内 ⑨；`test_usage_notes_cover_version_policy_preview_and_platform_boundary`（`2.1.169` / `disableAgentView` / research preview / POSIX / `setup.sh` × `sdflow-init update` 两条分发链） |

**TDD 顺序留痕**：`TestCapabilitySnapshot` 六条与 9 条段内 golden 均**先写后实现**，各自实测红过（安装六条：`6 failed`；段内 golden：`6 failed, 29 passed`）；`install-manifest` 子命令的红态另有独立证据 —— 拿 `git show HEAD:…/outside-voice-job.py` 跑 `install-manifest` 得 `invalid choice`、rc=2。

---

## 三、五条跨票交接 —— 逐条落地位置与锚

| # | 交接 | 落地 | 锚 |
|---|---|---|---|
| 1 | `setup.sh` MUST 写 `capability-manifest.json` | `setup.sh:install_sdflow`（新增 `*.py` 循环 + 收尾调 `install-manifest --dir "$sdflow/hack"`）。**未抄第二份 hash 口径**：manifest 由 job helper 自己的 `compute_manifest()` 算 | `test_writes_a_capability_manifest_that_verifies_against_installed_bytes` + `test_installed_snapshot_passes_preflight_from_the_global_home`（**这条就是「真实安装态 preflight 必红」的翻绿锚**，并断言 `job_dir` 是安装路径、不含仓根） |
| 2 | Task 5 MUST 保留 SKILL 侧 config clamp | 段内 ① 保留「越界 → 一律回落默认 `900`、MUST NOT fail-closed 罢工」，并**新增一句显式理由**：helper 对越界 `--timeout` 是硬拒绝 ⇒ clamp MUST 在 SKILL 侧做完、MUST NOT 下推 | `test_skill_side_timeout_clamp_is_retained`（查 `回落默认 \`900\`` + `MUST NOT fail-closed 罢工` 两个字面量） |
| 3 | SKILL 分支 MUST 显式处理 `unknown_cost`（最要害） | 段内 ⑥ 新增独立条款：`unknown_cost=true`（覆盖**每一个** LOST 站点与残留 reservation）⇒ **MUST NOT 自动同族 fallback**，MUST 原样报出 `orphan_warning` + 提示跑 `cleanup … --cancel`，只有 helper 返回 `fallback_allowed=true` 后才可 fallback；该站点在此之前落 `exec-error`，MUST NOT 落 `ok`/`timeout`。④ 的 dispatch 失败分支同样按 `fallback_allowed` 二分（`duplicate-site`/`slot-limit`/`unknown-cost`/`usage-error` ⇒ 不 fallback、不重派）；⑦ 补一行「唯一例外 = `unknown_cost`」 | `test_codex_branch_gates_auto_fallback_on_unknown_cost`（`unknown_cost` + `cleanup --run-dir` + `--cancel` + `fallback_allowed`） |
| 4 | `probe_subtree` 相关 docstring 两处不准（T220） | **知情未改**（本票不必修，已 defer 冷层）。落笔期一律以代码为准读子树判定，未据 docstring 推理；`test_outside_voice_job.py:884-886` 与 `:2180` 保持原样 | `git diff sdflow-init/tests/test_outside_voice_job.py` 显示改动全在**文件末尾新增段**，两处 docstring 零改动 |
| 5 | `openspec/specs/` 主 spec 仍写「四旗」 | **知情未改**：归 archive 阶段的 delta 同步，实现期 MUST NOT 改 `openspec/specs/` | `git status` 无 `openspec/specs/` 条目 |

顺带核实（不属交接、避免误伤）：`openspec/adr/0028` 提到 300 秒的那句本就写着「**不得**回到已被 5/5 rc124 证伪的同步 300 秒路径」——与本次删除同向，无需改；`openspec/specs/host-adaptive-execution/spec.md` 里的旧表述同属 archive 阶段 delta 同步范围，未动。

---

## 四、门与全量测试的实际输出

```
$ python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 18 个投放面全部与真相源一致
（rc=0）

$ git diff --check
（无输出，clean）

$ /usr/bin/python3 -m pytest -q
2488 passed, 11 skipped, 3 xfailed in 260.05s (0:04:20)
```

基线为 `2469 passed, 10 skipped, 3 xfailed`。差额 = 本票新增 **20** 条用例（6 + 5 + 9）；skip 数在 10/11 之间浮动的那一条是既有的
`test_outside_voice_child_lifecycle.py:436`（高频混合信号风暴复现率环境敏感，其 docstring 已登记「经常 skip 属预期」），
二次运行 `-rs` 列出的 skip 明细为 10 条、无本票新增 skip。

---

## 五、未做 / 降级项（如实报告）

1. **`bash setup.sh` 未在本机真实 HOME 上跑过**。所有安装锚都落在 `HOME`/`SDFLOW_HOME` 重定向到 tmp 的真实 `setup.sh` 执行上。
   理由：在开发 checkout 跑 setup 会把全局 `~/.sdflow` 与 `~/.claude/skills` 指向本 checkout（CLAUDE.md 的 dev/runtime 纪律要求测完还原），
   属对环境的破坏性动作，未获真人指示 ⇒ 不擅自执行。**合并后需在运行 checkout 重跑 `bash setup.sh` 才会生效**（⑨ 已把这条写进 SKILL）。
2. **安装态 lifecycle smoke 只把「模型边界」那一个文件换成替身**：`outside-voice.sh` 换成无模型 fake helper 后用**安装态自己的** `install-manifest` 重算快照；
   job helper、执行路径、manifest 口径全是 `setup.sh` 真装出来的那份。未被替换的真实 shell helper 另由
   `test_installed_snapshot_passes_preflight_from_the_global_home` 覆盖（它跑在**未经改动**的安装快照上）。
   ⚠ **该 smoke 无任何模型调用，MUST NOT 被当作 efficacy 证据** —— efficacy 归 Task 6。
3. **`install-manifest` 写不成时不中止安装**（只 `⚠` 告警）：后果是 preflight 红 ⇒ 后台通道走同族 fallback。
   取舍理由：manifest 是 Codex 后台通道的前提，不是 skills 安装的前提；为它 abort 整个 `setup.sh` 会让一个可选通道拖垮主路径（④ 简化 + 诚实降级）。
4. **`--max-wait` 未在 SKILL 里给建议值**：段内只写「MUST NOT 用它把 await 截短成早退」。上界口径的单一源在 helper（`started_at`+timeout+30s grace），
   SKILL 侧再给一个数就是第二份口径。

---

## 六、Concerns（交给双轴审判）

1. **`⑨ 使用说明` 放在 marker 段内**：它是站点无关的操作前提，放段内可由 parity gate 一并守住；代价是等值段变长。
   若评审认为使用说明该外置（如挪进 job helper 头注释或 README），需同时给出「谁来守它不漂」的答案 —— 目前答案是 parity gate + 段内 golden。
2. **负向 golden 的判据是「矩阵行级」**：它拦的是「codex 行重新长出 sync/300」。若将来有人把兼容分支写成散文而非表格行，本 golden 照不到。
   取舍：矩阵是该分支的**唯一**可执行形态（③ 明写「执行模式矩阵」），散文形态不构成可执行指令；再往上做需要语义判断，无确定性信号（基准 1 的合法残余）。
3. **`setup.sh` 的中断锚依赖 `cp` 对只读目标失败**。本机（darwin）实测确实失败并触发 `set -e`；若某平台 `cp` 行为不同，该用例会自证失效
   （它先断言 `r2.returncode != 0` 并附「本用例未制造出中断」的错误信息，不会静默变成空绿）。
