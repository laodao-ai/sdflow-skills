---
ship-gate:
  verify: PASS
  reviewed_sha: 8fabd05b165fc353ea271438d70d3b28f745b058
---

# Verify Report — harden-gate-git-layer

- 日期：2026-07-21
- Change：harden-gate-git-layer（换掉 ship_gate.py 失鲜判定：录锚 + 比内容 + 限定求值窗口 + git 调用层加固）
- 覆盖盘面：`git rev-parse HEAD` = `8fabd05b165fc353ea271438d70d3b28f745b058`
- pytest：`/usr/bin/python3 -m pytest sdflow-ship/tests/ -q` → **331 passed**（35.5s）

## 结论：PASS

5 条 spec Requirement 的全部 Scenario 均在 `ship_gate.py` 有对应实现、在 `sdflow-ship/tests/` 有机验锚点。三个 producer 模板（spec-review / code-review / done SKILL）均含 `reviewed_sha` 字段。退役簇（`report_last_sha` / 帧比较整簇 / `_stale_trigger_hint` / `StaleResult`）在源码中已无活跃 def/调用，仅剩注释登记退役事实。冷审 F1-F4 修复到位。未发现核心功能缺口。

## 逐需求核对表

### Requirement 1：判据只在其保护的风险真实存在的阶段求值（求值窗口）

| Scenario | 代码出处 | 测试锚点 | 状态 |
|---|---|---|---|
| 代码审期/done期不求值 design 失鲜 | `decide()` 三入口 `emit_windowed`（:1414/:1422/:1450），`:1397-1400` 有意留空 | `test_window_closed_during_code_review`、`test_window_closed_during_wrapup` | ✅ |
| 实现窗口三分支各自受保护 | `emit_windowed`(:1102)→`guard_design_freshness`(:1077) 各分支独立包装 | `test_window_run_sop/run_plan/continue_impl_evaluates_design_freshness`（三个独立用例） | ✅ |
| 实现期四件套实质修订被拦回重审 | `guard_design_freshness` stale→`REFUSE_START`(:1095) | `test_design_anchor_stale_on_design_edit`、`test_e2e_flip_plus_design_edit_still_stale` | ✅ |

### Requirement 2：直接比较内容，不从 git 管道推断路径变更

| Scenario | 代码出处 | 测试锚点 | 状态 |
|---|---|---|---|
| 实现期不得让设计门失鲜（监视集承重） | `is_stale` design 分支 ls-tree 映射比较（:799-837） | `test_design_anchor_survives_impl_commits`、`test_impl_source_edits_and_plan_checkbox_flip_keep_design_fresh` | ✅ |
| specs 新增/删除/rename 均失鲜 | `path→(mode,type,oid)` 映射不等（:802） | `test_specs_added_file_is_stale`、`_deleted_`、`_renamed_with_identical_content_` | ✅ |
| tasks.md 纯复选框翻转不失鲜（任何阶段） | `_tasks_content_exempt`(:753) 常开、按内容切 | `test_pure_checkbox_flip_is_fresh_in_every_phase`（多阶段参数化）、`test_checkbox_flip_across_many_commits` | ✅ |
| 合并把已批准产物换回锚前旧内容 | 映射比较不依赖提交拓扑（:800-802） | `test_revert_to_pre_anchor_content_is_stale` | ✅ |
| 代码审后源码改动被 code 域捕获 | `is_stale` code 分支顶层条目映射（:854-860） | `test_code_domain_merge_introduces_source_change_is_stale`、`_git_mv_source_into_openspec_` | ✅ |
| openspec 内记账不得让 code 域失鲜 | Python 侧按条目名排除 openspec（:856-857），非整树 sha、非负向 pathspec | `test_code_domain_openspec_accounting_writes_stay_fresh`、`_excludes_openspec_by_entry_name_not_pathspec` | ✅ |

### Requirement 3：评审锚由 producer 记录，不从提交历史反推

| Scenario | 代码出处 | 测试锚点 | 状态 |
|---|---|---|---|
| 锚指向被放行提交而非写报告时刻（ADR-7a） | `sdflow-code-review/SKILL.md` 两段提交时序（修复先提交→锚指它→报告单独提交） | `test_code_review_autofix_two_stage_commit_does_not_self_stale`、`_single_stage_commit_would_self_lock` | ✅ |
| 结论落盘前追加修订须先单独提交（ADR-7b） | `sdflow-spec-review/SKILL.md` 拍板前二次修订单独 checkpoint | `test_adr7b_second_revision_anchored_after_is_not_refused`、`_anchored_before_self_locks`、fixture `test_fixture_third_stage_*` | ✅ |
| 无关报告排版提交不移动锚 | `read_reviewed_sha`(:414) 只读录值，`report_last_sha` 退役（:391 注释） | `test_touching_the_report_does_not_move_the_anchor`、`test_report_reformat_commit_does_not_move_anchor`、`test_legacy_reanchoring_implementation_would_have_judged_fresh`（以旧实现为参照物，对应 5.5） | ✅ |
| 锚缺失/非法 fail-closed | `read_reviewed_sha` 四形态各抛 `GateIndeterminate`（:427-448），语法级 `_is_full_oid`(:898)/语义级 `cat-file -e ^{commit}`(:444) 分层 | `test_missing_anchor_is_unknown`、`_syntactically_invalid_anchor_`、`_anchor_object_absent_`、`_anchor_pointing_at_non_commit_object_`、`_missing_anchor_does_not_fall_back_to_inferred_anchor` | ✅ |
| 结论字段与锚原子写入 | 三 producer 模板 `design_approved`+`reviewed_sha` 同层同写（SKILL 拍板回写协议） | `test_code_review_report_missing_anchor_is_unknown`、`_verify_report_missing_anchor_`（中间态诊断点名缺 reviewed_sha） | ✅ |

### Requirement 4：内容比较区分读失败与内容为空

| Scenario | 代码出处 | 测试锚点 | 状态 |
|---|---|---|---|
| 读取失败保守判失鲜/UNKNOWN | `read_blob_bytes` rc≠0→`GateIndeterminate`(:561)，不折成 b"" | `test_blob_read_failure_on_both_sides_is_not_equal_content`、`_ls_tree_read_failure_is_indeterminate_not_fresh` | ✅ |
| 存在性判定由 ls-tree 承担（缺失≠失败） | `ls_tree_map` rc=0+不在结果=缺失（:522-533），`read_blob_bytes` 仅存在确认后调用 | `test_one_sided_missing_tasks_is_stale_not_a_read_failure`、`test_tasks_appearing_only_on_head_side_is_stale`、`_blob_read_failure_on_one_side_is_indeterminate` | ✅ |

### Requirement 5：git 调用失败落退出码契约集且不受外部态影响

| Scenario | 代码出处 | 测试锚点 | 状态 |
|---|---|---|---|
| git 不可用/不可执行 → UNKNOWN(6) 覆盖全部 helper | `_git_run` 单出口捕 OSError（:322），`run_git`/`run_git_rc`/`run_git_bytes` 共用 | `test_oserror_is_controlled_per_helper`、`_permission_error_`（HELPERS 三 helper 参数化）、`test_main_maps_git_unavailable_during_repo_root_resolution` | ✅ |
| git 调用挂起 → timeout=30 映射 UNKNOWN | `_git_run` 捕 TimeoutExpired（:319），`GIT_TIMEOUT_SECONDS=30`(:244) | `test_timeout_is_controlled_per_helper`、`_real_hang_times_out_per_helper`、`_shared_timeout_constant_value` | ✅ |
| 失败原因五类可区分可行动 | `_INDETERMINATE_ADVICE`(:1545) 五 CAUSE 各文案，`main()` 唯一映射点(:1583) | `test_five_causes_give_distinguishable_advice`、`test_indeterminate_reasons_are_mutually_distinguishable` | ✅ |
| 环境变量不改判定输入（denylist） | `_git_env` 剔 GIT_* 前缀(:292)+封 global/system config(:294-295) | `test_env_is_a_denylist_not_an_allowlist`、`_git_prefixed_vars_are_stripped`、`_non_git_prefixed_vars_pass_through`、`_verdict_is_identical_under_polluted_git_env`、`_config_files_are_neutralized_in_child_env` | ✅ |

### 冷审 F1-F4 修复

| 项 | 出处 | 测试锚点 | 状态 |
|---|---|---|---|
| F1：设计门 reviewed_sha 校验窗口内保证边界登记 + 非 builtin 剔 GIT_EXEC_PATH 代价登记 | 头注释(:26-32)、`_git_env` docstring(:281-289) | 头注释 + 残余面登记（无机械门，属登记项） | ✅ |
| F1：全局 gitconfig 位置封堵 | `_git_env` 回填 GIT_CONFIG_GLOBAL/SYSTEM=/dev/null（:294） | `test_global_gitconfig_cannot_alter_judgment_input`、`_verdict_is_identical_under_polluted_global_config` | ✅ |
| F2：ADR-4 三处 stale 都带 reviewed_sha（不只 design） | code 域(:1489)、verify 域(:1520) RERUN_STALE emit 补 reviewed_sha | `test_stale_pass_reruns_not_ship`(:42 断言)、`_stale_fail_reruns_not_exit5`(:58 断言) | ✅ |
| F3：报告读 OSError 收敛 + 缩进/HTML 注释代码块超集闸门 | `_read_report_text` 单出口(:405)、`is_indented_code_line`(:667)、`HtmlCommentTracker`(:675) | `test_unreadable_code_review_report_stays_in_contract`、`_content_stale_on_indented_code_block_flip`、`_html_comment_block_flip` | ✅ |
| 退役簇无悬空引用 | 帧比较整簇 + `_stale_trigger_hint`/`StaleResult` 已删 | `test_retired_frame_comparison_cluster_leaves_no_dangling_reference`、`_stale_verdict_carries_no_trigger_payload`、`_inferred_anchor_helper_is_gone` | ✅ |

## 缺口清单

### 核心缺口
无。

### Minor 缺口 / 已登记残余（可接受，非本 change scope）
- **归档终态盲区**（verify→merge 间无失鲜检查）— design.md 残余面显式登记并有意接受（与 T179 同盲区两半）。
- **窗口右边界间隙**（「实现刚完成」与「代码审进行中」盘面不可区分）— 纯盘面判据关不上，第二层由代码审 scope-drift（模型判断）兜，头注释 :102-107 登记。
- **T189 耦合与承重升格**（`_normalize_checkbox_lines` 成 design 域唯一豁免闸门，口径缺陷未修）— 独立面，登记 todolist T189，本次有意不 fold。
- **SHA-256 object-format 仓（64 位 OID）判非法**— `_is_full_oid` 硬取 40 位，与 design ADR-1 一致，作为已知边界登记在 impl-report Concerns。
- **repo-local `.git/config` 未封**— 能力等价残余（能写 .git/config 者已足以击穿 gate），`_git_env` docstring :272-279 显式登记为在案残余，非声称被守住。

以上均为文档级/可观测性级或已在四件套残余面显式接受的项，不构成核心功能缺失。

## PASS
