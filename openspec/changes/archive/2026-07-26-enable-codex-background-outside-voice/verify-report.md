---
ship-gate:
  verify: PASS
  reviewed_sha: e3450df862c7556e23420b990dbb6d7d388dda0e
---

# verify 报告 — enable-codex-background-outside-voice

**日期**：2026-07-26
**change**：`enable-codex-background-outside-voice`
**被验盘面**：`e3450df862c7556e23420b990dbb6d7d388dda0e`（工作树另有一处未提交改动：`tasks.md` 的复选框对账）

## 结论

**PASS** —— 两份 delta spec 的 7 条 ADDED/MODIFIED 需求（OVBG-01~05、HAE-08~09）在代码与测试里
逐条有机械锚；17 条已勾任务全部核到出处。6.1 / 6.2 是**人（真人用户）于 2026-07-26 明确拍板的
降级范围**（Codex CLI 额度封锁至 07-29），非本次判定项；而 **6.3 的 else 分支经独立核实是真的完整
执行了**（详见第三节，含一条我亲跑的确定性反证）。无核心缺失；4 条 Minor 缺口全部可接受 / 已 defer。

## 一、自跑的机械证据（不引用任何已有报告的措辞）

| 命令 | 结果 |
|---|---|
| `/usr/bin/python3 -m pytest`（全量） | **2634 passed, 10 skipped, 3 xfailed**（258s） |
| `/usr/bin/python3 hack/check_async_branch_parity.py` | `✅ 2 处 async host 调度段逐字节一致`，rc=0 |
| `/usr/bin/python3 hack/sync_principles.py --check` | `✅ 18 个投放面全部与真相源一致`，rc=0 |
| `git diff --check` | rc=0 |
| `openspec validate enable-codex-background-outside-voice --strict` | `Change ... is valid` |
| `check_codex_efficacy_evidence.py check --evidence <transport-probe>` | **exit 1**，见第三节 |

10 条 skipped 逐条核过：7 条 Windows 本地盘 smoke、1 条信号风暴复现率用例、**2 条是 task 2.2 的真机
模型探针**（`SDFLOW_OV_REAL_MODEL_SMOKE=1` 才跑，实现票已亲跑并把真 stdout 录进 impl-report）。
**5.2 的无模型真集成 smoke 与 2.3 的 `claude logs` canary 均未 skip、本轮实跑通过**（本机装有 claude CLI）。

## 二、逐需求核对表

### 2.1 delta spec 需求

| 需求 | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| **OVBG-01** 2.1.169 共同能力下限 | `outside-voice-job.py:165` `MIN_CLAUDE_VERSION=(2,1,169)`；`:376-395` `check_claude_version` | ✅ |
| OVBG-01 `--bg --exec` research-preview 形态 | `outside-voice-job.py:741` `[claude_bin,"--bg","--exec",command]` | ✅ |
| OVBG-01 monotonic 5s deadline + 超时回收进程树 | `:171` `DISPATCH_DEADLINE_SECONDS=5.0`；`:733` `deadline=start+…`；`:588` `_kill_process_tree`，`:754/:768` 两处调用 | ✅ |
| OVBG-01 preflight 无副作用（不建 dummy job） | `:422 run_preflight` 只跑 `--version` + `agents --all --json`；负向 golden `test_preflight_*`（`:392/:399/:409/:417`） | ✅ |
| OVBG-01 复用同一份 `outside-voice.sh exec` | `:558 build_worker_command` → `cmd_worker` 调 helper；`test_worker_passes_runner_model_effort_env_to_real_helper` | ✅ |
| OVBG-01 capability manifest / hash fail-closed | `:299 compute_manifest` `:317 verify_manifest`；`MANIFEST_ENTRIES`(:181)；`test_preflight_fails_closed_on_capability_manifest_skew` 等 4 条 | ✅ |
| OVBG-01 v1 仅 POSIX，其他平台 fail-closed | `:360 check_posix_shell`、`SUPPORTED_SYS_PLATFORMS`(:210)；`test_preflight_fails_closed_on_non_posix_platform`(:392)、`test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight`(:3441) | ✅ |
| **OVBG-02** `O_CREAT\|O_EXCL` reserve + 同 run ≤2 站点 | `:492` `os.open(..., O_CREAT\|O_EXCL, 0o600)`；`:501` `MAX_SITES_PER_RUN`；`test_duplicate_site_is_rejected_before_external_side_effect`(:479)、`test_third_distinct_site_is_rejected_before_external_side_effect`(:490) | ✅ |
| OVBG-02 job.json 必填字段 + atomic rename | `:837-849` `atomic_write_json(job_path(...), mode=0o600)`；`JOB_REQUIRED_FIELDS`(:1068) 含 host/runner/model/effort/job_id/dispatched_at… | ✅ |
| OVBG-02 worker 发布 started → terminal → rc（三段原子） | `:872 publish_started` `:909 publish_terminal` `:891 publish_rc`（各 0600 + temp+rename） | ✅ |
| OVBG-02 终态前不读 stdout；rc=0 但 stdout 空判 exec-error | `:1390` `stdout_stat_evidence(...)  # stat，不读正文`；`:1393-1396` | ✅ |
| OVBG-02 缺 terminal witness 不得只凭 rc 判成功 | `:1383-1387` `"rc 已发布但缺少可核验的 terminal witness"` → CORRUPT | ✅ |
| OVBG-02 dispatch→metadata 崩溃 ⇒ unknown-cost，不自动重派 | `run_cleanup` 首段 `:1892-1908`（无 metadata ⇒ `identity-unverified` + `unknown_cost=True`，拒删 reserve） | ✅ |
| **OVBG-03** 有界 await（helper 内节流，主 session 不自造轮询） | `:2202 cmd_await`；`MAX_AWAIT_WAIT_SECONDS = 3600+30`(:1024)；SKILL ⑥ 明写 `MUST NOT 自造轮询循环` | ✅ |
| OVBG-03 startup deadline 独立于 worker timeout | `STARTUP_DEADLINE_SECONDS=5`(:187)；`:1423-1428` 用 `job["startup_deadline_at"]` 单独判 | ✅ |
| OVBG-03 内层上界从可信 `started_at` 起算 + 30s grace | `AWAIT_GRACE_SECONDS=30`(:1018)；`:1431` `now > started_epoch + timeout_seconds + AWAIT_GRACE_SECONDS` | ✅ |
| OVBG-03 timeout 只由真实 rc=124 产生 | `RC_TIMEOUT=124`(:1056)；`:1397-1399` 唯一产出 `REASON_TIMEOUT` 的分支 | ✅ |
| OVBG-03 job failed/stopped/missing 且无 rc ⇒ exec-error 非 timeout | `:1409-1421` `_lost("...但 rc 缺席 —— 判 exec-error，MUST NOT 冒充 timeout")` | ✅ |
| OVBG-03 900 默认 / 1..3600 | `DEFAULT_TIMEOUT_SECONDS=900`(:189)、`MIN/MAX_TIMEOUT_SECONDS`(:190-191)；SKILL ① 同口径 clamp | ✅ |
| OVBG-03 显式 `reconcile --run-dir`，禁猜「最新 run」 | `:2139 run_reconcile`；`test_reconcile_requires_an_explicit_run_dir`(:2834)、`test_reconcile_never_reaches_into_a_sibling_or_newer_run_dir`(:2841) | ✅ |
| **OVBG-04** 四旗原样复用 | `outside-voice.sh:750-753` `--tools "Read,Grep,Glob" --strict-mcp-config --add-dir --settings` | ✅ |
| OVBG-04 `--effort high --safe-mode --no-session-persistence` | `outside-voice.sh:749-753`；`EFFORT_VALUES=("high",)`(:210) 钉死单值、降档 fail-loud(`:666`) | ✅ |
| OVBG-04 strong 模型走 `SDFLOW_VOICE_MODEL` 单一源 | `outside-voice.sh:658-659`（runner=claude 时必须非空）+ `:750` | ✅ |
| OVBG-04 worker 输出 0600 + 先重定向再执行 | `cmd_worker:947-949` `os.open(..., O_TRUNC, 0o600)` + `dup2`；`test_worker_output_files_are_0600`(:1025) | ✅ |
| OVBG-04 `claude logs` 不成为第二出境面（含对照组） | `test_outside_voice_job.py:3368-3392`（先跑裸 `--bg --exec` 做对照组证探针有判别力），本轮**实跑未 skip** | ✅ |
| OVBG-04 ambient customizations 隔离（真机 + 对照组） | `test_outside_voice.py:975/992` 双探针（safe-mode 组 + 去 `--safe-mode` 对照组）；实现票已亲跑，输出录于 `impl-reports/task4-runner-isolation.md:150-168` | ✅（默认 skip，见第四节 M2） |
| OVBG-04 run dir 不入库 | `.gitignore:19` `**/.outside-voice/` | ✅ |
| **OVBG-05** collect 后 `claude rm` | `run_cleanup:1950+` rc 已发布 ∧ 已 collect 才清 roster；`:1854 claude_job_action` | ✅ |
| OVBG-05 identity → stop → 子树核验 → rm | `:1755 verify_identity`、`:1626 probe_subtree`、`:1707 wait_subtree_exited` | ✅ |
| OVBG-05 子树不可证 ⇒ orphan-warning + 抑制自动 fallback | `:1932-1941` `orphan-warning` 分支（`unknown_cost=True`，无 `fallback_allowed`）；`test_reconcile_reports_an_orphan_warning_and_exits_nonzero`(:3001) | ✅ |
| OVBG-05 不删本轮审计证据 | `run_cleanup` docstring `:1883` **不写、不删 run-dir 里的任何文件** | ✅ |
| **HAE-08** 两 SKILL 宿主分流等值段 | `sdflow-{spec,code}-review/SKILL.md` `sdflow:async-branch` 段；`check_async_branch_parity.py` 本轮 rc=0 | ✅ |
| HAE-08 删除 Codex sync 300s 兼容分支（负向 golden） | `test_codex_sync_300s_compat_branch_is_deleted`（矩阵行面）+ `test_sync_wait_for_claude_compat_path_is_deleted_in_prose_too`（散文面），`test_async_branch_parity.py:280/410` | ✅ |
| HAE-08 Claude-host harness async 保留 + sync 降级保留 | SKILL ③ 矩阵四行（async·harness / async·后台作业 / sync 降级 / 不跑 exec） | ✅ |
| **HAE-09** 锚契约与 anchor_lint 矩阵不变 | SKILL ⑦ 同一张退出码表；`declared-sites` 公式段留 marker 外未改；全量 pytest 含既有 anchor golden 全绿 | ✅ |
| HAE-09 rc→reason_code 映射（124/3/其他） | `:1397-1403`（124→timeout、3→secret-hit、其余非零→exec-error） | ✅ |
| HAE-09 stderr 只出计数、不进 tracked 报告 | `:1117 stderr_stat_evidence`（只 stat）；SKILL ⑥ 末「写出面同样受限」 | ✅ |
| HAE-09 `unknown_cost` ⇒ 落 `fallback-unavailable` 不落 ok/timeout/exec-error | SKILL ⑥/⑦ 的 🔴 条款 | ✅ |

### 2.2 逐任务核对（17 条已勾）

| 任务 | 出处 | 状态 |
|---|---|---|
| 1.1 CLI/shape 测试 + 负向 preflight golden | `test_outside_voice_job.py`（150 个 `def test_`），`:392-417` preflight 负向组 | ✅ |
| 1.2 dispatch/worker | `cmd_dispatch:657`、`cmd_worker:933`、`build_worker_command:558`（`shlex.join`，`:585`） | ✅ |
| 1.3 status/await/collect 状态笛卡尔 | `derive_status:1314`（含 STARTING/RUNNING/SUCCEEDED/TIMED_OUT/FAILED/LOST/CORRUPT）；`build_collect_payload:1493` | ✅ |
| 1.4 可重入 collect + reconcile + identity-safe cleanup | `_first_writer_wins_json:1440`（幂等）、`run_reconcile:2139`、`run_cleanup:1882` | ✅ |
| 2.1 Claude argv golden + 三隔离旗 + 版本升级 | `outside-voice.sh:167` `OV_VERSION="outside-voice.sh 1.5.0"`；`test_exec_claude_isolation_flags_golden` | ✅ |
| 2.2 safe-mode 真机回归 + 对照组 | `test_outside_voice.py:976/993`（默认 skip，实现票亲跑） | ✅ |
| 2.3 注入/越界 + `claude logs` canary + 0600 | `test_shell_metacharacters_in_paths_cannot_rewrite_the_dispatched_command`、`:3368` canary、`:1025` 0600 | ✅ |
| 3.1 两 SKILL 同步改 + 负向 golden | parity rc=0 + 两条删除性 golden | ✅ |
| 3.2 job id/site/nonce 进 `dispatch-manifest.tsv`、有界 await/collect | SKILL ④「MUST 就地记进 ⑧ 的记账表，并…追加落盘 `dispatch-manifest.tsv`」+ ⑥ | ✅ |
| 3.3 执行模式矩阵 / timeout 解析 / 记账 / cleanup 纪律 + parity | SKILL ①③⑧⑨；`check_async_branch_parity.py` rc=0；`declared-sites` 公式段未动 | ✅ |
| 4.1 `setup.sh` 同代快照原子安装 | `setup.sh:150`（先删 manifest）→ `:170` `*.py` 安装循环 → `:189` `install-manifest`；`test_installed_path_runs_dispatch_collect_cleanup_offline`(:3540)、`test_interrupted_install_leaves_no_consistent_snapshot` | ✅ |
| 4.2 使用说明 / 版本 skew / 两条分发链 | SKILL ⑨ 五项；`test_usage_notes_cover_version_policy_preview_and_platform_boundary` | ✅ |
| 5.1 fake CLI 单测全矩阵 | 150 条用例，本轮全绿 | ✅ |
| 5.2 已安装快照的无模型真集成 smoke | `:3540 test_installed_path_runs_dispatch_collect_cleanup_offline`（真跑 `bash setup.sh` 到 tmp HOME）+ `:1135` 真 `--bg --exec` 跨 shell 存活；**均未 skip、本轮实跑** | ✅ |
| 5.3 四条门 + 全量 pytest | 本报告第一节全部由我亲跑复现 | ✅ |
| 6.3 二分出口的 else 分支 | 见第三节 | ✅ |
| 6.4 `openspec validate --strict` + 范围核 | validate 通过；范围核见第四节 M1 | ✅（含 Minor） |

## 三、🔴 6.3 else 分支是否真被执行 —— 独立核实

任务 6.3 是二分句：**达标 ⇒ 关 T162 + 改「Codex efficacy=0」陈述；否则 ⇒ 保留 T162 + 如实记录，
不得以编排 smoke 假绿。** 6.1/6.2 未达标 ⇒ 必须走 else 分支。我逐条独立取锚：

| 应然 | 我取的锚 | 结论 |
|---|---|---|
| T162 仍 OPEN | `openspec/issues/todolist/2026-07-todolist.md:22` 总览表 JSON `"status":"OPEN"`；`openspec/issues/INDEX.md:318` `\| T162 \| todo \| OPEN \|`（双写一致） | ✅ 保留 |
| `openspec/CONTEXT.md` 的 efficacy 陈述一字未改 | `git diff a1aac9d HEAD -- openspec/CONTEXT.md` = **仅 +4 行**，内容是新增术语条目「Outside Voice 后台作业」，**无一处 efficacy 陈述被增删改** | ✅ 未改 |
| 既有 design 的 efficacy 陈述一字未改 | 全仓 `grep "efficacy=0"` 的既有陈述面全部落在 `openspec/changes/archive/2026-07-18-async-outside-voice/*`、`archive/2026-07-16-add-codex-host-support/*`、`docs/sdflow-fable5/20260717.md`、`openspec/specs/host-adaptive-execution/spec.md:242`；`git diff --stat a1aac9d HEAD` 中**这些路径一个都没出现** | ✅ 未改 |
| 本 change 的 `design.md` 未把 efficacy 写成已解 | `grep efficacy design.md` 仅 4 处，均为「真实 efficacy 门要求」的正向定义（`:164/:244/:270`），无一处宣称达成 | ✅ |
| `proposal.md` Success Metrics 未被改写以掩盖缺口 | `proposal.md:7` 仍原文写着「至少一个 `opus`+`high` 自然 >300 秒…由确定性检查器核验」，未降低门槛 | ✅ |
| 无任何 efficacy evidence.json 产出 | 全仓 `find -name "*efficacy*evidence*"` 只命中检查器本体与其测试，**零证据文件** | ✅ |
| 未把编排 smoke 当 efficacy 假绿 | **我亲跑反证**：`check_codex_efficacy_evidence.py check --evidence impl-reports/task6-transport-probe-evidence.json` → **exit 1**，stderr：`host=None ≠ 'codex'` ×2 + `⇒ tasks.md 6.3：保留 T162 并如实记录，MUST NOT 以编排 smoke 假绿` | ✅ **机械证伪** |
| 该 probe 的自我定性 | 文件名即 `task6-transport-probe-evidence.json`；`task6-real-efficacy.md:120` 小节标题「后台通道探针（**transport 证明，不是 efficacy 证明**）」；`:292` 明写 436s 那条「不在 codex 层内 ⇒ MUST NOT 单独记作达标」 | ✅ |
| `superpowers-plan.md` 验收框保持未勾 | Task 6 的前 3 条验收框 `- [ ]`（未勾），仅后 3 条已勾 | ✅ |
| 缺口有移交去向 | `todolist:2179-2196` T225（额度恢复后跑真实 Codex efficacy）+ T226（届时给检查器补 `--run-dir` 交叉核验），含额度封锁至 `2026-07-29 10:11` 的实录 | ✅ |
| hand-off.md | **尚不存在**（按 sdflow-done 流程在 verify 之后生成）⇒ 见第四节 M4 的前向义务 | ⚠️ 前向 |

**判定：6.3 的 else 分支被完整、诚实地执行了。** 最强的一条不是文字，而是那个检查器
**对本 change 自己产出的唯一一份真实 >300s 证据判红**（`host` 是盘面派生量、非自报，来自
`<site>.job.json` → `collected.json`，调用方没有 `--host` 入参可伪造）——即使有人想拿 transport
探针冒充 efficacy，机械门也会拦下。检查器自身的 docstring（`check_codex_efficacy_evidence.py:53-63`）
还主动声明了「`check` 不是防伪门，只核 JSON 内部自洽性，不回查 run-dir」这条诚实边界，并把加固挂 T225。

## 四、缺口清单

### 核心缺口（FAIL 项）

**无。**

### Minor 缺口（可接受 / deferred）

- **M1 —— 分支里混入 3 个本 change 授权范围外的提交**（触及任务 6.4「source change 只包含本 change
  授权范围」）。`de549f4 feat(sdflow-issues): 新增历史问题数据迁移工具`（`migrate_legacy.py` +384 /
  测试 +198 / `sdflow-issues/SKILL.md` +20，`openspec/` 下无对应 change/spec）与 `2a587a1`+`edf2ff9`
  两份调研文档（`docs/sdflow-context-policy.md` +288、`docs/subagent-definitions-plan.md` +328）。
  **已被本轮 code-review 独立识别并如实登记**（`code-review-report.md:45-49` / F4 低 / B22），
  处置权属人。**判 Minor 而非 FAIL**：它是「多带了东西」不是「少做了东西」，与两份 delta spec 的
  任何一条需求都不冲突，且全量 pytest 覆盖了它们（`test_migrate_legacy.py` 在绿名单内）。
  🔴 **合并前请人确认**：这三个提交是否随本 change 一起上 main。
- **M2 —— task 2.2 的两条真机 safe-mode 探针默认 skip**（需 `SDFLOW_OV_REAL_MODEL_SMOKE=1`）。
  实现票已亲跑并把真 stdout（含对照组「去掉 `--safe-mode` 后诱饵确实响了」）录进
  `impl-reports/task4-runner-isolation.md:150-168`。设计如此（每跑一次要真花模型额度），
  **可接受**；plugins/skills 隔离未独立探针一事已在该报告 §五.1 如实标注为「未独立验证」。
- **M3 —— `task6-real-efficacy.md:292` 把 probe 的 host 写作 `host="claude"`，而
  `task6-transport-probe-evidence.json` 里该字段实为 `null`**（旧格式 witness 无 `host` ⇒ emit 搬 None）。
  措辞不精确，但**结论方向一致且更严**（null 同样 ≠ codex，检查器照红），不影响任何判定。
  纯文档措辞，**可接受**。
- **M4 —— 前向义务（不是当前缺口）**：`hand-off.md` 尚未生成。它是 6.3 else 分支点名的三个载体
  之一 ⇒ 生成时 **MUST** 原样保留「Codex efficacy=0」缺口陈述、写明 6.1/6.2 未做及人拍板 A 的
  由来、并把 T225/T226 列为移交项，**MUST NOT** 写成「efficacy 已验证」。

### 已知 defer（本 change 明示、非缺口）

- **6.1 / 6.2**：真人用户 2026-07-26 拍板选项 A 降级合并，补证移交 **T225**（fold **T226**）。
  本次 verify **不因此判 FAIL**。
- 代码审 defer 7 项：**B21 / B22 + T226–T230**（`code-review-report.md`，`code_review: pass`，
  `reviewed_sha: 3cc89c1`）。

---

PASS
