# verify-report — ship-gate-hardening

日期：2026-07-04 · change：ship-gate-hardening

## 结论：PASS

<!-- ship-gate: verify=PASS -->

四缺陷（B1 窗口闭区间 / B2 尾流修订豁免 / B3+D3 硬化归档终态 / B4 完成判据集合归属）均已在真实代码落实，并各配用真实复现盘面断言正确 verdict 的回归测试。冷启核对每条 ✅ 均附机验锚点。`pytest sdflow-ship/tests/` 65 passed；仓级 `pytest` 328 passed（≥307 基线，不降）。仅剩 T32/T33/T34 为 pre-existing deferred（非本 change 引入），不构成核心缺口。

## 逐需求核对表

| 需求 / Scenario | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| B1 窗口闭区间 `[sha, HEAD]`（含 sha 自身 subject） | `ship_gate.py:249-268`（`done_task_ids` 追加 `self_subject`）；`test_gate_impl_progress.py::test_plan_task1_same_commit_counts`（plan+task1 同 commit → RUN_CODE_REVIEW 齐 N） | ✅ |
| B1 排他窗口既有路径回归（不多不少） | `test_gate_impl_progress.py::test_continue_impl_with_done_set` / `test_all_tags_present_advances` / `test_window_excludes_legacy_and_merge`（遗留标签+merge携带均被滤） | ✅ |
| B1 头注释/reason 契约同步为闭区间表述（T1.4） | `ship_gate.py:30-33`（头注释「窗口 [sha, HEAD] 闭区间」）+ `ship_gate.py:369`（CONTINUE_IMPL reason `窗口 [{sha[:7]}, HEAD] 闭区间`）——旧 `<sha>..HEAD --no-merges` 表述已清除 | ✅ |
| B2 尾流修订豁免精确式 `checkpoint(impl-review)` / `:…` | `ship_gate.py:161-178`（design 域分帧遍历 `--format=%x00%s`，精确式豁免）；`test_gate_freshness.py::test_impl_review_exempt_bare_and_colon`（裸+冒号两例不 REFUSE） | ✅ |
| B2 精确式边界：`)evil` / `-fix` / `X` 变体不豁免 | `ship_gate.py:169`（`==` 或 `startswith(":")`）；`test_impl_review_evil_suffix_stale` / `test_impl_review_fix_variant_stale`（均 REFUSE_START） | ✅ |
| B2 护栏①：豁免仅 `scope=="design"`，code 域逐字不变 | `ship_gate.py:179-184`（code 分支无 subject/无豁免）；`test_gate_freshness.py::test_stale_pass_reruns_not_ship` / `test_stale_fail_reruns_not_exit5` 回归绿 | ✅ |
| B2 护栏②：MUST NOT 加 `--no-merges`/`--first-parent`（BR-6） | `ship_gate.py:161`（`git log {sha}..HEAD --name-only --format=%x00%s`，无 --no-merges）+ 注释 :159 | ✅ |
| B2 BR-6 分帧边界：空 subject 帧 / 交错帧归属 | `test_empty_subject_touch_design_stale`（空消息触 design.md→失鲜）；`test_interleaved_impl_review_and_normal_stale`（豁免帧改 tasks.md + 普通帧改 design.md 并存→失鲜） | ✅ |
| B2 反向回归：普通 subject 触四件套照失鲜 | `test_gate_freshness.py::test_design_anchor_stale_on_design_edit`；中文名 spec `test_chinese_named_spec_edit_still_stale`（core.quotePath=false 加固） | ✅ |
| B2 T2.5 token 双向钉死契约测试（BR-5） | `test_anchor_contract.py:31-37`（gate 含 `checkpoint(impl-review)` 豁免 token ⟷ code-review SKILL 含 `checkpoint-commit.sh impl-review` step 名） | ✅ |
| B2 头注释豁免规则 + 已知不覆盖两条（T2.4） | `ship_gate.py:38-39`（豁免规则）+ `:50-53`（伪造 subject 绕过 / 豁免四件套随档 ship 两条声明） | ✅ |
| B3+D3 归档终态短路（decide 开头，pre-flight 前） | `ship_gate.py:293-325`（`if not cdir.exists()` 短路）；`test_gate_terminal.py::test_archived_in_base_with_verify_shipped`（SHIPPED exit0） | ✅ |
| B3 H3 `base_ref()`（main/master 优先，缺→UNKNOWN）+ 返回码可见 git | `ship_gate.py:91-107`（`run_git_rc`/`base_ref` refs/heads/ 限定）；`ship_gate.py:300-305`（base None→UNKNOWN/REFUSE 分岔） | ✅ |
| B3 H2 纯 git 域发现（`ls-tree`，非 fs glob） | `ship_gate.py:110-120`（`archived_dirs_in_tree`）；`test_untracked_junk_archive_not_run_verify`（未跟踪垃圾目录不误命中→REFUSE） | ✅ |
| B3 H5 `re.escape(change)` + 日期前缀 fullmatch（glob 元字符安全） | `ship_gate.py:118`（`re.compile(r"\d{4}-\d\d-\d\d-"+re.escape(change)+r"$")`）；`test_change_with_glob_metachar_safe`（`a?b` 不误中 axb→REFUSE） | ✅ |
| B3 H1 SHIPPED 追读 archived verify=PASS（空壳不放行）+ tri-state | `ship_gate.py:123-135`（`archived_verify_state` none/pass/conflict）+ `:306-319`；`test_shell_archive_no_verify_not_shipped`（无锚→UNKNOWN 非 SHIPPED）；`test_archived_verify_conflict_unknown`（PASS+FAIL→UNKNOWN） | ✅ |
| B3 分派：仅 HEAD 树（未并）→ RUN_VERIFY | `ship_gate.py:320-323`；`test_archived_only_in_head_run_verify`（next=sdflow-done） | ✅ |
| B3 change 不存在 → REFUSE（区分「未过设计门」） | `ship_gate.py:304-305,324-325`；`test_no_active_no_archive_refuse_not_exist` / `test_suffix_collision_not_matched`（后缀撞名不误中） | ✅ |
| B3 H4 detached HEAD 对 D3 无关（凭 base 树可达仍 SHIPPED）+ 移除 branch_state | `ship_gate.py:279-282`（branch_state 注释移除说明，代码无残留）；`test_detached_head_archived_shipped`（detached→SHIPPED）；`test_cross_branch_shipped_by_base`（跨分支→SHIPPED） | ✅ |
| B3 H1 续：final SHIPPED 谓词收紧（active 存在时不判 SHIPPED） | `ship_gate.py:415-423`（final 恒 RUN_VERIFY，无 glob 存在性判 SHIPPED）；`test_active_present_old_archive_active_wins`（active+旧档→走 pre-flight REFUSE） | ✅ |
| B3 run_git 注入 `core.quotePath=false` + `errors="replace"` | `ship_gate.py:82-96`（`_GIT_HARDEN` + `errors="replace"`）；`test_gbk_archived_verify_no_crash`（GBK 归档 verify 不崩、SHIPPED） | ✅ |
| B3 T3.3 头注释契约表补 SHIPPED/REFUSE/RUN_VERIFY/detached 变体 | `ship_gate.py:17,23,27`（契约表三行补变体 + detached 注记）+ `:54-55`（精确同名旧档已知不覆盖） | ✅ |
| B4 完成判据集合归属 `plan_ids ⊆ done_ids`（非基数） | `ship_gate.py:229-234`（`plan_task_ids`）+ `:353-370`（判据 `if plan_ids - done`，上报 `done & plan_ids`）；`test_offplan_task_no_false_complete`（task1+计划外task9→CONTINUE_IMPL 非假齐，done_tasks=["1"]） | ✅ |
| B4 回归：既有齐 N / 仅 task1 / merge 内计划外号 | `test_all_tags_present_advances` / `test_continue_impl_with_done_set` / `test_merged_branch_inner_commits_do_enter_window`（done=["9"]计划外→CONTINUE_IMPL done_tasks=[]） | ✅ |
| T5.1 SKILL.md REFUSE_START 两变体一致 | `sdflow-ship/SKILL.md:28`（「未过设计门…补锚」+「change 不存在…核对拼写」两分支）；`test_anchor_contract.py`/`test_skill_text.py` 绿（锚行字面集零改动） | ✅ |
| T5.2 全量回归 65 + 仓级 328（≥307 基线） | 实跑 `pytest sdflow-ship/tests/ -q` = 65 passed；`pytest -q` = 328 passed | ✅ |

## 缺口清单

核心缺口：无。

Minor / deferred：
- T32 / T33 / T34 — **pre-existing deferred**（源标注 = ship-gate-hardening，见 `code-review-report.md:34`）：change 命名空间 tag · 工作树 dirty 新鲜度 · 复选框分段绑定。均为 gate 既有局限的登记项，非本 change 引入的回归，已在 hand-off 引用，不阻断 ship。
- T5.3（归档时主 spec 同步）为 archive 阶段动作，由 sdflow-done archive CLI 自动执行 + 人工核对，属收尾步，不在本 verify 判据内。

## PASS
