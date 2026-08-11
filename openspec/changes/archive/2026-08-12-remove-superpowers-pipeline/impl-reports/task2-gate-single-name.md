# Task 2：gate 单名 resolver 与测试同步

## 摘要

`ship_gate.py` 的计划文件 resolver 从双名探测（`tickets.md` / `superpowers-plan.md`，双存在
判 UNKNOWN、旧名收尾票 grandfather）收窄为单名 `tickets.md`，第四道收尾票校验无条件生效；新增
遗留旧名兜底（`tickets.md` 缺席 ∧ `superpowers-plan.md` 单独存在 ⇒ fail-closed UNKNOWN + 人工
清理提示，设计门 Q1）。7 个消费 `approved_change` 共享 fixture 的测试文件（63 处调用点）逐一核验
旧名语义依赖并同步；`test_superpowers_track_regression.py` 整文件删除；`test_gate_closing_ticket.py`
两条 grandfather 用例退役。`sdflow-ship`（342 用例）+ `sdflow-implement`（39 用例）全测试套绿。

## 实现改动

### `sdflow-ship/scripts/ship_gate.py`

1. `PLAN_FILENAMES = ("tickets.md",)`（单元素元组，resolver 函数形状保留）；新增
   `LEGACY_PLAN_FILENAME = "superpowers-plan.md"`（仅用于遗留旧名兜底探测）。
2. `PlanNameConflict` 异常类删除，替换为 `LegacyPlanNameFound`（语义从「双存在冲突」改为
   「新名缺席、旧名单独存在」）。
3. `resolve_plan_path` 重写：`tickets.md` 存在即返回（遗留旧名若也存在则被忽略，不参与判定、
   不触发任何诊断）；`tickets.md` 缺席且 `superpowers-plan.md` 存在 ⇒ raise
   `LegacyPlanNameFound`；两者皆缺 ⇒ 返回 `None`。
4. `plan_closing_ticket_check` 删除按文件名分流的 grandfather 分支（`if plan.name !=
   "tickets.md": return True, grandfathered...`），改为无条件执行收尾票 + Blocked-by 覆盖校验。
5. `decide()`：`except PlanNameConflict` → `except LegacyPlanNameFound`；RUN_PLAN reason 由
   「计划文件缺（tickets.md / superpowers-plan.md 均未找到）」改单名「计划文件缺（tickets.md
   未找到）」。
6. 文件头文档（verdict×exit×next 契约表 / 完成判据窗口段落 / 第四道校验描述）与
   `PLAN_FILENAMES` 上方的「共享 resolver」说明注释块同步改写为单名 + 遗留旧名兜底语义，移除
   对已删符号 `impl_route.resolve_pipeline` 的引用。

## 测试同步（63 处调用点核验结果）

`approved_change`（`test_gate_impl_progress.py`）的默认写入名由 `superpowers-plan.md` 改为
`tickets.md`。由于单名 resolver 下第四道收尾票校验无条件生效，逐一核验了全部 63 处
`approved_change(...)` / `_approved_with_tasks(...)` 调用点：

- **仅测 `_design_stale()`（不经 `run_gate()` 走到第四道校验）**：`plan=PLAN2` 原样保留，
  不受影响（3 处，`test_gate_freshness.py` 的 `test_specs_renamed_with_identical_content_is_stale`
  / `test_specs_subtree_edit_is_stale` / `test_tasks_appearing_only_on_head_side_is_stale`）。
- **早于第四道校验的门先行拦截**（悬空 fence / 标题 0 / 重号 Task 段）：plan 文本不受影响，
  只是写入名随 fixture 改名自动变化，行为不变（`test_gate_impl_progress.py` 的
  `test_t34_duplicate_task_number_unknown` / `test_t34_unclosed_fence_unknown` /
  `test_t34_unclosed_tilde_fence_unknown` / `test_t34_backtick_cannot_close_tilde_fence` /
  `test_plan_zero_titles_unknown`）。
- **需要通过第四道校验才能到达断言的验证点（大多数）**：`plan=PLAN2` → `plan=PLAN2_TICKETS`
  （已有的收尾票兼容 plan 常量），或对自定义 plan 字面量逐一补 `**Blocked-by:** none`（Task 1）
  与 `**Blocked-by:** 1\n**R-ID:** all`（兼作收尾 ticket 的 Task 2）。覆盖
  `test_gate_git_layer.py`（8 处）、`test_gate_namespace.py`（6 处）、`test_gate_tail.py`
  的共享 helper `impl_done`（1 处，被 `test_gate_freshness.py` 等多文件复用）、
  `test_gate_reviewed_sha.py`（6 处）、`test_gate_impl_progress.py`（21 处，含 9 处需手工补
  Blocked-by/R-ID 注解的 fence/checkbox 结构测试）、`test_gate_freshness.py`（含
  `_approved_with_tasks` 默认参数、`_seed_tasks` helper、parametrize 表、以及一处需同步改写
  文件名 + 内容基底的 `test_impl_source_edits_and_plan_checkbox_flip_keep_design_fresh`）、
  `test_plan_resolver.py`（除退役用例外的剩余部分）。

63 处调用点的核验发现：**parse_blocked_by 要求每个 Task 段都声明 `**Blocked-by:**`**
（包括无依赖的 Task 也须写 `**Blocked-by:** none`）——首轮补丁只给收尾 Task 加了
Blocked-by/R-ID，遗漏了功能 Task 的声明，导致 8 个用例先红（`收尾票校验无法解析 plan 的
Blocked-by 拓扑：Task 1 缺 Blocked-by 声明`），二轮补全后全绿。

### `test_gate_impl_progress.py`

- `approved_change` fixture 写入名改 `tickets.md`；旧注释（「MUST NOT 改，另有用例依赖旧名」）
  已随其依赖用例的退役一并改写为面向单名 resolver 的说明。
- 21 处 `plan=PLAN2` 调用中 15 处需换成 `PLAN2_TICKETS` 或补注解（详见上节），6 处
  （duplicate/fence/zero-title 早期拦截 + `test_non_git_root_unknown`）无需改动。

### `test_gate_git_layer.py` / `test_gate_namespace.py` / `test_gate_reviewed_sha.py`

三文件的全部 `plan=PLAN2` 调用（合计 20 处）统一换为 `plan=PLAN2_TICKETS`——这些测试聚焦
git 层加固 / 命名空间隔离 / reviewed_sha 校验，本身不关心 plan 结构，换用带收尾票的常量后
行为等价、且不再被第四道校验意外拦截。

### `test_gate_tail.py`

`impl_done` helper（被本文件 + `test_gate_freshness.py` 大量复用，是全文件影响面最广的
单点改动）默认 plan 换为 `PLAN2_TICKETS`。

### `test_gate_freshness.py`

- `_approved_with_tasks` 默认参数、`_seed_tasks` helper、parametrize 表（`(PLAN2,
  "CONTINUE_IMPL")` → `(PLAN2_TICKETS, "CONTINUE_IMPL")`）均改用 `PLAN2_TICKETS`。
- `test_impl_source_edits_and_plan_checkbox_flip_keep_design_fresh`：原测试依赖 `approved_change`
  写**旧名**、本用例另写一份修改版到**同一旧名**模拟"勾选回填"，注释明确写"MUST 沿用同一文件名
  否则会撞 `PlanNameConflict`"。单名 resolver 下该冲突机制已不存在（`PlanNameConflict` 已删），
  改为把回填内容写到 `tickets.md`（与 fixture 现在的写入名一致），基底由 `PLAN2` 换成
  `PLAN2_TICKETS`，docstring 同步改写。
- 7 处只调 `approved_change(repo, plan=PLAN2)` 后仅断言 `_design_stale()` 的用例（不经
  `run_gate()`）保持 `PLAN2` 不变——已在上节列出。

### `test_plan_resolver.py`（改动量最大的文件）

- 文档头重写：移除「双存在 fail-closed」「旧名向后兼容」表述，改写为单名 + Q1 遗留旧名兜底。
- 单元层：
  - `test_resolve_plan_path_old_name_only_backward_compat` 退役 → 替换为
    `test_resolve_plan_path_legacy_only_raises_legacy_plan_name_found`（断言
    `LegacyPlanNameFound`）。
  - `test_resolve_plan_path_both_present_raises_conflict` 退役 → 原地替换为
    `test_resolve_plan_path_new_name_wins_when_legacy_also_present`（断言双存在时
    `resolve_plan_path` 直接返回 `tickets.md`，遗留旧名被忽略、不 raise）——保留对该 resolver
    分支（"hits 命中即早返回"）的单元覆盖，而非留白。
- gate 端到端层：
  - `test_neither_plan_name_present_run_plan_mentions_both_names` → 重命名为
    `test_neither_plan_name_present_run_plan_mentions_single_name`，断言 reason 只含
    `tickets.md`、不含 `superpowers-plan.md`。
  - `test_both_plan_names_present_gate_fails_closed_unknown` 退役 → 替换为两条新用例：
    `test_legacy_plan_name_alone_gate_fails_closed_unknown`（Q1 兜底：tickets.md 缺席 +
    遗留旧名单独存在 ⇒ UNKNOWN + 清理提示，tickets.md §2.2 要求的"Q1 兜底分支配一条新测试"）
    与 `test_new_name_present_ignores_legacy_gate_e2e`（双存在时新名优先、正常 CONTINUE_IMPL，
    与单元层新增用例对偶）。
  - 5.10 节：`test_mode2_two_step_rename_is_detected` / `test_mode3_rename_with_heavy_edit_is_detected`
    退役——两者的 fixture 前提是"旧名 plan 在途、迁移改名到新名"这一生命周期，单名 resolver 下
    `superpowers-plan.md` 已不再是任何合法在途 plan 的候选来源（存在即触发 Q1 fail-closed），
    参照系（旧名落盘后仍走正常 checkpoint 窗口判据）是目标态已不存在的行为。未受影响的
    `test_mode1_lookalike_plan_in_another_change_is_not_flagged`（跨 change 同模板误报，不涉及
    改名）与三条窗口误报/漏报回归用例（`test_normal_inflight_change_not_flagged` /
    `test_legacy_bare_tags_outside_window_do_not_trigger` /
    `test_other_change_namespaced_tags_outside_window_do_not_trigger`）保留，后三者的
    `plan=PLAN2` 换 `PLAN2_TICKETS`。
  - `PLAN_OLDNAME_RICH` 常量随其仅有的两个消费者（test_mode2/3）一并删除（面治：不留孤儿常量）。

### `test_superpowers_track_regression.py`

整文件删除（107 行）。该文件验证 `ship_gate` 第四道校验不误伤 superpowers 轨 plan、以及
`impl_route.py route` CLI 子命令仍正确解析 `impl-pipeline: superpowers`——前者的参照系
（旧名 grandfather）已随本票退役，后者调用的 `route` 子命令已随 Task 1 从 `impl_route.py`
整体切除（实测：`impl_route.py` 已无 `resolve_pipeline` / `_cmd_route` / `route` 子命令）。

### `test_gate_closing_ticket.py`

- 文档头重写，移除 grandfather 语义描述。
- `_seed_with_old_name` helper 删除（不再有任何调用点）。
- `test_grandfather_old_name_without_closing_ticket_not_rejected`（原 :130）与
  `test_plan_closing_ticket_check_grandfathers_old_name`（原 :160）两条用例删除。
- 其余 6 条（含收尾票绿 / 缺收尾票红 / Blocked-by 缺依赖红 / 收尾票不唯一红 + 2 条单元测试）
  未受影响，`_seed_with_new_name` 直写 `tickets.md`，与 `approved_change` 无关。

## 未按 ticket 字面执行的一处偏离（及理由）

**`hack/tests/test_harden_sdflow_spec_followup_closure.py` 的 `PLAN` 常量未按 ticket 文本
"fixture 改名 tickets.md" 执行，维持原状（`PLAN = CHANGE / "superpowers-plan.md"`）。**

核实过程：该常量指向 `harden-sdflow-spec-followups` change 的计划文件——该 change **已归档**
（`openspec/changes/archive/2026-07-27-harden-sdflow-spec-followups/`），其计划文件在磁盘上
真实、永久地名为 `superpowers-plan.md`（内容含被 `test_spec_authoring_requirement_ids_and_
resident_identity_are_consistent` 用例断言的具体 R-ID 值）。若照字面把常量改成 `tickets.md`，
该路径下不存在同名文件，测试会因 `FileNotFoundError` 直接崩溃。

本 change 的 Global Constraints 明文「不动 archive 历史件…（例外：0033/0042 互指指针）」，
`harden-sdflow-spec-followups` 不在例外名单内。据此判断：ticket 文本的这一句大概率是撰写时
对 `superpowers-plan` 字符串的全文匹配未加区分产生的误伤（该文件与本 change 的 gate resolver
逻辑无关，纯粹是碰巧提到同一字符串的历史归档引用），而非真实意图要求破坏一个真实存在、不可变
的历史工件引用。已保持该常量不变，`hack/tests/test_harden_sdflow_spec_followup_closure.py`
16 条用例全绿（未改动前后行为一致，运行结果附于下方验证记录）。

## 验证

```
$ /usr/bin/python3 -m pytest sdflow-ship/tests/ -q
342 passed in 43.74s

$ /usr/bin/python3 -m pytest sdflow-ship/tests/ sdflow-implement/tests/ -q
381 passed in 43.82s

$ /usr/bin/python3 -m pytest hack/tests/test_harden_sdflow_spec_followup_closure.py -q
16 passed in 0.67s
```

`git status --short` 改动文件集：

```
 M sdflow-ship/scripts/ship_gate.py
 M sdflow-ship/tests/test_gate_closing_ticket.py
 M sdflow-ship/tests/test_gate_freshness.py
 M sdflow-ship/tests/test_gate_git_layer.py
 M sdflow-ship/tests/test_gate_impl_progress.py
 M sdflow-ship/tests/test_gate_namespace.py
 M sdflow-ship/tests/test_gate_reviewed_sha.py
 M sdflow-ship/tests/test_gate_tail.py
 M sdflow-ship/tests/test_plan_resolver.py
 D sdflow-ship/tests/test_superpowers_track_regression.py
```

## Global Constraints 核验

- `impl_route.py` 保留半场接口逐字不变：本票未改动该文件（Task 1 已完成路由切除，未触碰
  frontier/task-text/parse_blocked_by/TopoError/BLOCKED_BY_RE）。
- gate 完成判据窗口机制（`TAG_RE` / `git log --diff-filter=A` / frontmatter 状态集判据）
  逐字未动——本票只动计划文件的*定位*（`resolve_plan_path` 的探测规则），窗口计算函数
  （`plan_first_sha` / `done_task_ids` / `stray_done_tag_commits` / `_tag_task_id`）零改动。

## 验收复选框自查（tickets.md Task 2）

- [x] `PLAN_FILENAMES` 已缩为单名，双存在 UNKNOWN / grandfather 分支已删
- [x] 遗留旧名兜底分支已新增并配测试（`test_resolve_plan_path_legacy_only_raises_legacy_plan_name_found`
      + `test_legacy_plan_name_alone_gate_fails_closed_unknown`）
- [x] `test_plan_resolver.py` 旧名相关用例已退役
- [x] `test_superpowers_track_regression.py` 已整文件删除
- [x] 共享 fixture `approved_change` 默认写入名已改 `tickets.md`（7 文件 63 处核验）
- [x] `test_gate_closing_ticket.py` 两条 grandfather 用例已退役
- [x] sdflow-ship 全测试套绿（342 用例，含完成判据窗口与收尾票校验回归）
