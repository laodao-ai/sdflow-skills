# Task 3 · design 域改为直接比较被审内容，退役路径枚举通路

**范围**：tasks 2.1 / 2.1b / 2.2 / 2.4（design 部分）/ 2.8 / 2.9
＋测试 5.1 / 5.2 / 5.4 / 5.5 / 5.7 / 5.10 / 5.18 / 5.15a / 5.15b
**R-ID**：R2、R4　**Blocked-by**：Task 1（`read_reviewed_sha` / `CAUSE_*` / `_git_run` / `run_git_bytes` 已就位，本票接着它建）

## 1. 落地了什么

`sdflow-ship/scripts/ship_gate.py`：

| 件 | 动作 |
|---|---|
| `design_pathspecs(base)` | **新增**。监视集 pathspec 的**单一源** = `DESIGN_WATCHED_NAMES` + `specs/`。`tasks.md` 也在其中，使存在性判定统一走 `ls-tree` 的干净语义 |
| `ls_tree_map(root, ref, pathspecs)` | **新增**。`git ls-tree -r -z <ref> -- <pathspecs>` → `{path_bytes: (mode, type, oid)}` |
| `read_blob_bytes(root, ref, path, label)` | **新增**。取内容字节；rc≠0 ⇒ `GateIndeterminate(CAUSE_READ_FAILED)` |
| `is_stale` design 分支 | **重写**：约 50 行帧遍历 → 映射比较 + 单一内容豁免（约 20 行） |
| `is_stale` 返回值 | `StaleResult` → 朴素 `(stale, freshness)` 二元组（`trigger` 随 ADR-4 退役） |
| `decide()` 的 design stale emit | 去掉 `stale_trigger` 与 `_stale_trigger_hint` 拼接（锚值可见性归 Task 4 的 2.7） |
| 帧比较整簇 | **整簇删除**（下方 §4 逐一列名） |
| `DESIGN_WATCHED_NAMES` / `_tasks_content_exempt` / `_normalize_checkbox_lines` | **保留复用**，且各有真实生产调用点（机械守见 §5 的 M15/M16） |

判定分层（对应 tasks 2.2）：

1. 锚侧与 HEAD 侧各跑一次 `ls_tree_map` → 映射**完全相等** ⇒ `fresh`，**0 次内容读取**；
2. 差异**仅在 `tasks.md`**、且**两侧均存在**、且**mode/type 相同** ⇒ 取两侧字节走 `_tasks_content_exempt`；
3. 其余任何差异（含 `tasks.md` 单侧缺失）⇒ `stale`。

因为比较单位是 `path → (mode, type, oid)` 映射，**新增 / 删除 / 改名 / 修改 / mode / 类型变更天然全覆盖**，
不需要另做双侧并集（映射比较本身即并集语义）。

## 2. 两处相对 design.md 字面的收紧，均为 fail-closed，显式登记

**(a) 内容读取用 `cat-file blob`，不是 `git show`。**
design.md ADR-2 的行文是「`git show` 只负责取内容」。二者在本函数的**契约面**（前提 = `ls-tree` 已确认双侧存在；
rc=0 取字节 / rc≠0 = 真读失败）完全一致，∴ 这不是换判据，是同契约下的更安全取法：
`show` 的输出受 textconv / smudge 等 config 影响，同一 blob 在不同 config 下可读出不同字节
⇒ 判定输入重新变成外部可控，**违反 ADR-6**（`_GIT_HARDEN` 只中和了 `core.quotePath`，够不着 textconv）。
仓内既有先例同判据（退役的 `blob_pair` 注释原文：「用 cat-file blob 而非 show：前者输出 object 的原始字节，绕开 smudge/textconv」）。

**(b) 豁免额外要求 `tasks.md` 两侧 mode/type 相同。**
design.md 的分层文字只写了「两侧均存在」。若照字面实现，**仅 chmod / regular↔symlink** 的 `tasks.md`
会走到内容判据，而两版 blob 字节**完全相同** ⇒ 判豁免 ⇒ 状态位变更被静默放行。
这与 ADR-2 自己的论据「一次比较覆盖存在性 / 对象类型 / mode / 内容四者」直接冲突，
∴ 按 ADR-2 的**论据**（而非分层段的省略写法）补上闸门，方向 fail-closed。用例 `test_mode_only_change_on_tasks_is_stale` + 变异 M6。

## 3. 求值窗口（Task 4）尚未接入 —— 本票的已知边界

design 域失鲜目前仍在 `decide()` 的单一调用点**全阶段求值**（`RUN_SOP` / `RUN_PLAN` / `CONTINUE_IMPL` 三分支
接入是 tasks 2.5–2.7 = Task 4）。∴ 本票新增的端到端用例走的是「当前仍全阶段求值」的盘面，
Task 4 落地后其中依赖 verdict 取值的断言可能需要同批复核。

**随之而来的行为收紧（design.md ADR-3 已登记，此处再记一次）**：`checkpoint(impl-review)` 的
subject 豁免（BR-7）随帧遍历整簇退役 ⇒ **实现窗口内**改设计产物一律 `REFUSE_START`。
代码审期 / done 期的四件套修订不再误拦，靠的是 Task 4 的窗口限定，**不是**靠 subject 豁免。
在 Task 4 落地前，这两票之间的中间态会把代码审期的设计修订判失鲜——这是拆票的中间态，非终态。

## 4. 退役清单（tasks 2.8）与既有用例处置（5.15a / 5.15b）

### 4.1 生产代码：帧比较整簇，逐一列名

`frame_touched_paths`、帧遍历（`git log <sha>..HEAD --format=%H%x1f%s` + 逐帧循环）、
`design_frame_exempt` / `design_frame_exempt_reason`、`commit_parents`、`_parent_path_status`、
`_plain_content_modification`、`_plain_modification_from_raw`、`blob_pair`、`design_watched_subs`、
`STALE_CATEGORIES`、BR-7 subject 短路、`_stale_trigger_hint`、`StaleResult`（含 `.trigger`）。

**无悬空引用与孤儿代码**由机械守 `test_retired_frame_comparison_cluster_leaves_no_dangling_reference`
钉住：逐名断言「模块里没有该属性」**且**「代码行（去注释）里不出现该名字」，任一残留即红（变异 M14）。

### 4.2 既有用例 · 纯删除清单（5.15a）

随退役机制一并消失、且**无等价替代需求**者。全部来自 `sdflow-ship/tests/test_gate_freshness.py`。

| 退役机制 | 被删用例 | 条数 |
|---|---|---|
| `design_watched_subs`（帧内触及路径集） | `test_watched_subs_is_not_the_full_file_list`、`test_watched_subs_collects_all_watched_members` | 2 |
| `blob_pair`（帧内前后两版 blob） | `test_blob_pair_returns_raw_bytes_verbatim`、`..._preserves_crlf_and_trailing_newline_difference`、`..._rc_failure_on_both_sides_is_not_equal_bytes`、`..._rc_failure_on_one_side_is_conservative`、`..._added_in_this_commit_is_conservative`、`..._deleted_in_this_commit_is_conservative`、`..._renamed_away_is_conservative`、`..._chmod_only_is_conservative`、`..._type_change_to_symlink_is_conservative` | 9 |
| `_plain_modification_from_raw` / `_plain_content_modification`（raw 行形态闸门） | `test_plain_content_modification_true_only_for_real_edit`、`test_raw_line_plain_modification_true_for_content_edit`、`test_raw_line_rejects_non_modification_statuses`、`test_raw_line_rejects_mode_only_change`、`test_raw_line_rejects_malformed_shapes`、`test_plain_content_modification_false_when_path_untouched` | 6 |
| `commit_parents`（逐 parent 求值） | `test_commit_parents_enumerates_every_parent_of_a_merge`、`..._root_commit_is_empty`、`..._unresolvable_sha_is_none` | 3 |
| BR-6 护栏（帧遍历的 `git log` 开关） | `test_br6_guard_no_no_merges_or_first_parent_in_design_scope`、`test_frame_sha_parsed_from_subject_with_spaces_and_colons` | 2 |
| `design_frame_exempt`（帧级豁免 + 各道保守回落） | `test_design_frame_exempt_true_on_pure_checkbox_flip`、`test_exempt_conservative_when_other_watched_path_touched_even_if_content_ok`、`test_exempt_conservative_on_root_commit`、`test_exempt_conservative_on_unresolvable_sha`、`test_exempt_conservative_when_form_disqualified`、`test_exempt_conservative_when_added_in_this_commit`、`test_exempt_requires_every_parent_of_a_merge`、`test_design_frame_exempt_false_when_other_watched_path_touched` | 8 |
| BR-7 subject 豁免真值表（⑧a/⑧b/⑧c） | `test_tt_exact_subject_pure_flip_exempt`、`test_tt_exact_subject_semantic_exempt_by_subject`、`test_tt_variant_subject_pure_flip_exempt_via_content`、`test_tt_variant_subject_semantic_stale`、`test_tt_empty_subject_pure_flip_exempt_via_content`、`test_tt_empty_subject_semantic_stale`、`test_tt_plain_subject_pure_flip_exempt_via_content`、`test_tt_plain_subject_semantic_stale`、`test_exact_subject_short_circuits_before_any_blob_read`、`test_non_exact_subject_does_reach_blob_read`、`test_content_channel_verdict_independent_of_subject`（4 参数化）、`test_impl_review_exempt_bare_and_colon`、`test_impl_review_evil_suffix_stale`、`test_impl_review_fix_variant_stale`、`test_empty_subject_touch_design_stale`、`test_interleaved_impl_review_and_normal_stale` | 15（+3 参数化格） |
| `StaleResult.trigger` / `STALE_CATEGORIES`（⑨a–⑨c 触发点诊断） | `test_stale_trigger_category_mixed_paths`、`..._content_changed`、`..._shape_unfit`、`..._blob_unreadable`、`test_default_disposition_recommends_rerun_design_gate_only`、`test_code_domain_freshness_string_unchanged_and_no_trigger`、`test_is_stale_result_stays_two_tuple_compatible`、`test_frame_enum_failed_is_registered_category` | 8 |
| `frame_touched_paths` 枚举协议（F1/F2 机械守） | `test_merge_frame_is_actually_enumerated`、`test_frame_paths_include_rename_source`、`test_frame_paths_preserve_tab_unquoted`、`test_stale_when_commit_enumeration_fails`、`test_stale_when_frame_path_enumeration_fails`、`test_frame_touched_paths_returns_none_on_git_failure` | 6 |

> `test_default_disposition_recommends_rerun_design_gate_only` 归纯删除：它断言的两件事一件已无对象
> （`_stale_trigger_hint` 拼串），另一件（「reason 里 MUST NOT 出现 `checkpoint(impl-review)`」）
> 在 subject 豁免整体退役后**在定义上不可能违反**——那条指引所指的机制已经不存在了。

### 4.3 既有用例 · 需重新设计等价用例清单（5.15b）

承载**仍然生效**的安全承诺者，逐条改写成内容比较版本并入新编号体系。

| 原用例 | 承载的承诺 | 等价件（新） |
|---|---|---|
| `test_evil_merge_design_edit_is_stale` | 改动只存在于 merge 自身 resolve 出的树 ⇒ 失鲜 | 同名（改写：不再断言 `stale_trigger`，改经 `is_stale` + `run_gate` 双断言） |
| `test_evil_merge_tasks_semantic_edit_is_stale` | 同上的 `tasks.md` 分支 | 同名（改写） |
| `test_merge_frame_pure_flip_is_exempt_end_to_end` | merge 上纯勾选翻转仍豁免（反向判别性） | `test_merge_pure_checkbox_flip_is_exempt_end_to_end` |
| `test_git_mv_tasks_is_stale_end_to_end` | `git mv` 迁出监视集 ⇒ 失鲜 | `test_git_mv_tasks_out_of_watched_set_is_stale`（＋ 5.18 的 rename-away 参数化格补诊断口径） |
| `test_spec_path_with_tab_is_stale` | 含 Tab 路径不逃出监视集 | 同名（改写：`-z` 保原始字节，断言不再依赖 `stale_trigger`） |
| `test_frame_paths_preserve_tab_unquoted` | `-z` 协议本身（路径无 C-quote） | `test_ls_tree_keeps_tab_path_raw_and_unquoted`（机械守迁到新取数口径） |
| `test_chinese_named_spec_edit_still_stale` | 非 ASCII 路径不因 C-quote 放行 | 同名（保留，断言不变；变异 M1 证明它现在守的是 `-z`） |
| `test_tasks_only_checkbox_flip_not_stale` / `test_tasks_flip_plus_source_code_not_stale` / `test_merge_commit_pure_flip_not_stale` | 纯勾选翻转豁免（含 `git add -A` 打包形态） | `test_pure_checkbox_flip_is_fresh_in_every_phase`（两阶段参数化，含同帧源码） |
| `test_e2e_flip_plus_design_edit_still_stale` | 豁免只在差异仅限 `tasks.md` 时成立 | `test_checkbox_flip_plus_design_edit_is_stale` |
| `test_e2e_tasks_wording_change_still_stale` | 勾选框以外的 `tasks.md` 改动 ⇒ 失鲜 | `test_tasks_change_beyond_checkbox_is_stale` |
| `test_blob_pair_rc_failure_on_both_sides_is_not_equal_bytes` | 🔴「读失败 ≠ 内容为空」 | `test_blob_read_failure_on_both_sides_is_not_equal_content`（升级为经 `is_stale` 公共入口，原用例只直调 helper） |
| `test_blob_pair_chmod_only_is_conservative` | mode 变更不被内容判据放行 | `test_mode_only_change_on_tasks_is_stale`（经公共入口） |
| `test_e2e_br7_impl_review_subject_exemption_intact` | 豁免面不由被监管方书写的 subject 决定 | `test_impl_review_subject_no_longer_buys_any_exemption`（**方向反转**：subject 维度整体消失后，该越权口不再买得到豁免；防后人加回来） |

**保留未动**：`_tasks_content_exempt` / `_normalize_checkbox_lines` 的全部纯函数用例（⑦a/⑦b、
fence 口径、`CHECKBOX_RE` 单一源、F3 缩进代码块 / HTML 注释块）——这三处是保留复用件，其判据一字未改。

## 5. 变异证明（5.14 · 按守卫计数）

每条**实际改坏源码 → 跑对应用例 → 确认变红 → 还原**（跑手 `scratchpad/mutate_task3.py`，每条均附还原后复跑）。
**MUST NOT 以「用例存在且为绿」充当证明** —— 下表每行的「变异后」列都是实测的红。

| # | 被删/改反的守卫 | 变异后 | 还原后 | 对应用例 |
|---|---|---|---|---|
| M1 | `ls-tree` 的 `-z`（同时关 C-quote） | 1 failed, 2 passed | 3 passed | `test_ls_tree_keeps_tab_path_raw_and_unquoted` / `test_chinese_named_spec_edit_still_stale` / `test_spec_path_with_tab_is_stale` |
| M2 | `ls-tree` rc≠0 ⇒ `GateIndeterminate`（改成返回 `{}`） | 1 failed | 1 passed | `test_ls_tree_read_failure_is_indeterminate_not_fresh` |
| M3 | 协议外记录 ⇒ 不可判（改成 `continue`） | 1 failed | 1 passed | `test_ls_tree_unparsable_output_is_indeterminate` |
| M4 | 内容读 rc≠0 ⇒ 不可判（改成返回 `b""`） | 2 failed | 2 passed | `test_blob_read_failure_on_both_sides_is_not_equal_content` / `..._on_one_side_...` |
| M5 | 豁免前的**双侧存在性**闸门 | 2 failed | 2 passed | `test_one_sided_missing_tasks_is_stale_not_a_read_failure[delete/rename-away]` |
| M6 | 豁免前的 **mode/type 相等**闸门 | 1 failed | 1 passed | `test_mode_only_change_on_tasks_is_stale` |
| M7 | 豁免面 `diff == {tasks}`（放宽成 `tasks in diff`） | 1 failed | 1 passed | `test_checkbox_flip_plus_design_edit_is_stale` |
| M8 | `_tasks_content_exempt` 判据（恒真） | 2 failed | 2 passed | `test_tasks_change_beyond_checkbox_is_stale` / `test_evil_merge_tasks_semantic_edit_is_stale` |
| M9 | HEAD 侧映射（改成只取锚侧 = 单侧枚举） | 2 failed | 2 passed | `test_tasks_appearing_only_on_head_side_is_stale` / `test_revert_to_pre_anchor_content_is_stale` |
| M10 | 监视集里的 `specs/` 子树 | 4 failed | 4 passed | 5.10 四条（增 / 删 / rename / 改） |
| M11 | 监视集边界（画成整个 change 目录） | 2 failed | 2 passed | 5.1 两条（**监视集保住**的反向守） |
| M12 | 映射比较本体（短路成无条件 fresh） | 4 failed | 4 passed | 措辞改 / evil-merge / `git mv` / 回滚 四条 |
| M13 | 分层判定「映射相等 ⇒ 0 次内容读取」 | 1 failed | 1 passed | `test_no_content_read_when_maps_are_equal` |
| M14 | 退役完整性（复活 `blob_pair` 孤儿） | 1 failed | 1 passed | `test_retired_frame_comparison_cluster_leaves_no_dangling_reference` |
| M15 | `DESIGN_WATCHED_NAMES` 成员（去掉 `proposal.md`） | 1 failed | 1 passed | `test_retained_helpers_are_still_wired_into_production_path` |
| M16 | 保留件的**生产调用点**（`_tasks_content_exempt` 解绑成孤儿） | 3 failed | 3 passed | 同上 ＋ 5.2 两阶段格 |

### 5.5 的变异手段不同源（design.md 已登记，此处照约说明）

「无关的报告排版提交不移动锚」这条**没有可删的守卫**：新实现里锚是 `read_reviewed_sha` 读出来的常量，
**不存在反推逻辑**；而把 `report_last_sha` 复活进生产代码**违反 Compliance**
（「MUST NOT 回退到 `report_last_sha` 或任何反推式锚」）。
∴ 按 design.md 的指定改为**以旧实现为参照物的对比测试**：
`test_legacy_reanchoring_implementation_would_have_judged_fresh` 在**测试文件内**重建旧的反推锚
（`_legacy_report_last_sha`），在**同一个盘面**上断言四件事——

1. 旧锚 == 排版提交（确被无声前移，且 ≠ 被批准的盘面）；
2. 新锚 == 报告 frontmatter 录下的那个 commit（推不动）；
3. **旧锚下**监视集两侧映射逐字相等 ⇒ 旧实现在此判 `fresh`（偷改被埋在锚之前）；
4. 新实现在同一盘面判 `stale`。

两者结论**相反** ⇒ 配对用例 `test_report_reformat_commit_does_not_move_anchor` 的绿
不可能是旧行为侥幸给出的。这与「删掉守卫即变红」等效力，但手段不同源，故单独说明。

## 6. 覆盖对照（本票各验收项 → 用例）

| 验收项 | 用例 |
|---|---|
| 实现期改源码 + 勾实现计划复选框 ⇒ 设计门新鲜（5.1） | `test_impl_source_edits_and_plan_checkbox_flip_keep_design_fresh`、`test_impl_reports_and_tail_artifacts_keep_design_fresh` |
| 纯复选框翻转判新鲜，≥2 阶段各验一次；超出即失鲜（5.2） | `test_pure_checkbox_flip_is_fresh_in_every_phase[RUN_PLAN/CONTINUE_IMPL]`、`test_checkbox_flip_across_many_commits_is_still_fresh`、`test_tasks_change_beyond_checkbox_is_stale`、`test_checkbox_flip_plus_design_edit_is_stale` |
| 换回锚之前的旧内容即失鲜（5.4） | `test_revert_to_pre_anchor_content_is_stale` |
| `specs/` 增 / 删 / rename（内容不变）三类（5.10） | `test_specs_added_file_is_stale`、`test_specs_deleted_file_is_stale`、`test_specs_renamed_with_identical_content_is_stale`（＋`test_specs_subtree_edit_is_stale`） |
| 报告排版提交不移动锚，仍失鲜（5.5） | `test_report_reformat_commit_does_not_move_anchor` ＋ 对比件 `test_legacy_reanchoring_implementation_would_have_judged_fresh` |
| 单侧缺失判失鲜、诊断不呈读失败；真读失败受控（5.7 / 5.18） | `test_one_sided_missing_tasks_is_stale_not_a_read_failure[delete/rename-away]`、`test_tasks_appearing_only_on_head_side_is_stale`、`test_ls_tree_read_failure_is_indeterminate_not_fresh`、`test_ls_tree_unparsable_output_is_indeterminate`、`test_blob_read_failure_on_both_sides_is_not_equal_content`、`..._on_one_side_is_indeterminate` |
| 退役无悬空引用；保留件仍在且有调用点（2.8 / 2.9） | `test_retired_frame_comparison_cluster_leaves_no_dangling_reference`、`test_retained_helpers_are_still_wired_into_production_path`、`test_stale_verdict_carries_no_trigger_payload` |
| 退役用例分两类逐条登记（5.15a / 5.15b） | 本报告 §4.2 / §4.3 |
| 每条新增守卫各附变异证明（5.14） | 本报告 §5（16 条） |

**全部新增用例经 `is_stale` 公共入口或 `run_gate` 端到端求值**，无一只直调内部 helper
（本仓已有实证的假绿形态正是「只调 `blob_pair` 不走 `is_stale`」）。

## 7. 测试结果

- `sdflow-ship/`：**312 passed**（本票前 350 项含 51 项因退役而红）。
- 仓根全套件：**2064 passed, 9 skipped, 3 xfailed**。
  基线 2102 passed，差值 −38 = 退役 51 项（含参数化格）− 新增 13 项净额，与 §4 清单对得上。
  9 项 skip 含 `sdflow-init` 的 ramdisk 满盘用例（环境敏感，与本票无关）。

## 8. 交给下游的已知项

1. **Task 4** 接 tasks 2.5–2.7：三分支求值窗口 ＋ `emit` 补 `reviewed_sha`（ADR-4 的锚值可见性目前是空缺）。
   窗口接入后本票依赖 verdict 取值的端到端断言需同批复核（见 §3）。
2. **Task 5** 接 tasks 2.3：code 域顶层条目比较。本票**未动** `is_stale` 的 code 分支（仍是
   `git log --name-only`），注释已就地标注归属。
3. **T189 承重升格**：`_normalize_checkbox_lines` 现在是 design 域**唯一**的放行闸门，
   而它自己登记着基准 5 警号（口径应反转为白名单）。design.md 残余面已登记本次不 fold，
   源码 docstring 亦就地标注。
