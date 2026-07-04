# tasks — ship-gate-hardening-2

> 追溯：R1 = 需求「完成判据任务号按 change 命名空间隔离」〔T32〕· R2 = 需求「复选框辅通道按 Task 分段绑定」〔T34〕。
> 每 task commit MUST 用命名空间格式：`checkpoint-commit.sh <change>:task<N>-<slug>`（本 change=`ship-gate-hardening-2`，dogfood 新契约）。
> 顺序：先 T34（自包含、低耦合），后 T32（契约层）——降低交叉干扰。

## 1. T34 复选框按 Task 分段绑定〔R2〕

- [ ] 1.1 [TDD] 写失败测试（`sdflow-ship/tests/test_gate_impl_progress.py` 增）：R2 Scenario「全局单勾不放行未勾的其它 task」——plan task1 段全勾 / task2 段有 `- [ ]`、无 checkpoint 标签 → 期望 CONTINUE_IMPL 且 `done_tasks==["1"]`（现全局 `checkboxes_all` 会假齐放行，测试先红）
- [ ] 1.2 [TDD] 写失败测试：R2 Scenario「分段完成集与 checkpoint 主锚并集」——task1 由 checkpoint、task2 由其段复选框全勾 → 期望 RUN_CODE_REVIEW（两通道并集齐）
- [ ] 1.3 实现 `checkbox_done_ids(plan)` 替换 `checkboxes_all`（design ADR-3）：按 `TASK_TITLE_RE` 位置切段、每段独立判全勾 → 返回号集；`decide()` 完成判据合并 `done_ids = checkpoint_done ∪ checkbox_done`，再 `done & plan_ids`（B4 不变）
- [ ] 1.4 保留「plan 未提交（sha 空）且全 plan 无复选框 → UNKNOWN 双通道不可判」分支（design ADR-3）；1.1/1.2 转绿
- [ ] 1.5 回归绿：`test_checkbox_fallback_advances`（全勾推进）/`test_uncommitted_plan_no_checkbox_unknown`（双通道 UNKNOWN）逐字不变

## 2. T32 change 命名空间隔离〔R1〕（契约层，design scope-check 5 点）

- [ ] 2.1 [TDD] 写失败测试（新 `test_gate_namespace.py` 或增 impl_progress）：R1 Scenario「跨 change 命名空间标签不互相计入」——当前 change 的 `checkpoint(<change>:task1-)` 计入、另一 change 的 `checkpoint(<other>:task1-)` 落同窗口不计入 → 未完则 CONTINUE_IMPL 不假齐
- [ ] 2.2 [TDD] 写失败测试：R1 Scenario「旧无命名空间 checkpoint 向后兼容」——窗口内全裸标签 `checkpoint(task<N>-)` → 按窗口语义计入（= 升级前行为），不丢弃/不崩溃
- [ ] 2.3 实现 `TAG_RE` 可选命名组 `checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`（design ADR-1）+ `done_task_ids(root, sha, change)` 归属规则（design ADR-2）：命名组非空 → 仅当 `==change` 计入；命名组空（裸）→ 窗口计入。`decide()` 传 `change`
- [ ] 2.4 更新 `sdflow-ship/SKILL.md` RUN_PLAN→writing-plans 派发 args（scope-check 契约点①）：checkpoint 步名由 `task<N>-<slug>` 改为 `<change>:task<N>-<slug>`，并注明裸格式向后兼容
- [ ] 2.5 scope-check 契约点②验证：确认 `checkpoint-commit.sh` **零改**——逐字插值 step，`<change>:task<N>-<slug>` 作 step 传入即产 `checkpoint(<change>:task<N>-<slug>)`，无需改 producer（design 协议套件表）
- [ ] 2.6 回归绿：既有完成判据测试逐字不变——`test_plan_task1_same_commit_counts`〔B1〕/`test_offplan_task_no_false_complete`〔B4〕/`test_continue_impl_with_done_set`/`test_all_tags_present_advances`/`test_window_excludes_legacy_and_merge`/`test_revert_commit_not_counted`（均用裸格式 → ADR-2 保其计入）

## 3. 契约同步 + 收敛〔design 协议套件 scope-check 表〕

- [ ] 3.1 更新 `ship_gate.py` 头注释「已知不覆盖」（scope-check 契约点⑤）：+「两旧裸格式 change 同窗口交错撞 plan 号」残留假✅（Non-Goal）+ T33 工作树 dirty 停置理由；契约表若引用 checkpoint 格式则同步命名空间
- [ ] 3.2 全量 pytest 绿：`pytest sdflow-ship/tests/`（新增 R1/R2 锚测计入）+ 仓级 `pytest`（当前 328，不得回归）
- [ ] 3.3 收敛：spec delta（`specs/spec-workflow/spec.md` 两 ADDED 需求）随 change，archive 时由 sdflow-done 同步进主 `openspec/specs/spec-workflow/spec.md`；Success Metrics M1-M4 逐条对齐
