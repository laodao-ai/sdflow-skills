# tasks — ship-gate-hardening-2

> 追溯：R1 = 需求「完成判据任务号按 change 命名空间隔离」〔T32〕· R2 = 需求「复选框辅通道按 Task 分段绑定」〔T34〕。
> **本 change 自己的 task commit 用裸格式**〔spec-review 设计门 Q1=A / 对抗 B-4〕：`checkpoint-commit.sh task<N>-<slug>`（**非**命名空间格式）——因 RUN_PLAN（生成 plan）在链路里早于 task 1.4（改派发 args），本 change 的 plan 必然读到旧裸格式 args、无自动传导机制；self 走裸格式 = A1 向后兼容、gate 新旧解析器都认、零 churn、无自证损失。**命名空间 producer 格式靠 task 1.1/1.4 的真-git 测试验证正确性，对下一个 change 首次端到端消费**（本 change 只 dogfood parser/consumer）。
> **顺序：T32 解析器先行**——为自然 TDD 序（先落核心 parser 变更），非为消 churn（self=裸格式下新旧 gate 都认裸标签、本无 churn；grill Q2 原 churn 论证在 Q1=A 后不再适用）。

## 1. T32 change 命名空间隔离〔R1〕（解析器先行——dogfood 自举前提，design ADR-1/2 + 协议套件 scope-check）

- [x] 1.1 [TDD] 写失败测试（新 `test_gate_namespace.py` 或增 `test_gate_impl_progress.py`）：R1 Scenario「跨 change 命名空间标签不互相计入」。**MUST 用判别性负例**〔spec-review-amendment codex#2 反 vacuous test〕：plan={1,2}，当前 change 只有 `<change>:task1-`、另一 change 只有 `<other>:task2-` 落同窗口 → 期望 `done_tasks==["1"]` 且 CONTINUE_IMPL（若实现错误计入 other 的 task2 则 done={1,2} 假齐——此负例能区分"只计当前"vs"两个都计"，原"同号 task1"写法无区分力）。**测试 MUST 用真实 git commit fixture，非字符串 mock**〔A-F1〕
- [x] 1.2 [TDD] 写失败测试：R1 Scenario「旧无命名空间 checkpoint 向后兼容」——窗口内全裸标签 `checkpoint(task<N>-)` → 按窗口语义计入（= 升级前行为），不丢弃/不崩溃
- [x] 1.3 实现 `TAG_RE` 可选命名组 `checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`（design ADR-1）+ `done_task_ids(root, sha, change)` 归属规则（design ADR-2）：命名组非空 → 仅当 `==change` 计入；命名组空（裸）→ 窗口计入；`decide()` 传 `change`。**注**：`startswith("checkpoint(task"` 硬前缀过滤须同步放宽为容纳命名空间前缀（否则命名 checkpoint 被整条跳过）
- [x] 1.4 **同批改齐 3 处 producer 契约点**〔spec-review-amendment G1 blocker：3 声共识，漏权威源=T32 对主路径形同虚设〕：① **`sdflow-init/assets/workflow/workflow.md:74`（bundle 唯一权威源，CLAUDE.md 定）**——checkpoint 步名 `task<N>-<slug>`→`<change>:task<N>-<slug>`+注裸格式兼容；② `sdflow-ship/SKILL.md:29`（消费引用，同步改）；③ **`sdflow-ship/tests/test_workflow_authority.py:16`**——断言 token `"task<N>-"` 更新为命名空间格式（否则旧 token 被钉死、CI 反挡新格式）。archive 后按 CLAUDE.md 纪律触发 `sdflow-init update` 推下游（或 hand-off 显式记待做）
- [x] 1.5 scope-check 契约点②验证：确认 `checkpoint-commit.sh` **零改**——逐字插值 step，`<change>:task<N>-<slug>` 作 step 传入即产 `checkpoint(<change>:task<N>-<slug>)`，无需改 producer（design 协议套件表）
- [x] 1.6 回归绿：既有完成判据测试逐字不变——`test_plan_task1_same_commit_counts`〔B1〕/`test_offplan_task_no_false_complete`〔B4〕/`test_continue_impl_with_done_set`/`test_all_tags_present_advances`/`test_window_excludes_legacy_and_merge`/`test_revert_commit_not_counted`（均用裸格式 → ADR-2 保其计入）

## 2. T34 复选框按 Task 分段绑定〔R2〕

- [x] 2.1 [TDD] 写失败测试（`test_gate_impl_progress.py` 增）：R2 Scenario「全局单勾不放行未勾的其它 task」——plan task1 段全勾 / task2 段有 `- [ ]`、无 checkpoint 标签 → 期望 CONTINUE_IMPL 且 `done_tasks==["1"]`（现全局 `checkboxes_all` 会假齐放行，测试先红）
- [x] 2.2 [TDD] 写失败测试：R2 Scenario「分段完成集与 checkpoint 主锚并集」——task1 由 checkpoint、task2 由其段复选框全勾 → 期望 RUN_CODE_REVIEW（两通道并集齐）
- [x] 2.2b [TDD] 写失败测试〔spec-review-amendment codex#4/codex#3+对抗B-1c〕：① **fenced code block 内伪复选框不算完成**（plan 某 task 段的 ```代码块``` 里有 `- [x]`、真实行未勾 → 该 task 不判完成）；② **重号 Task 段 → UNKNOWN**（同一 `### Task 1:` 出现两段、一段全勾一段未勾 → 判 UNKNOWN，不假齐）。锚 `test_fenced_checkbox_not_counted` / `test_duplicate_task_number_unknown`
- [x] 2.3 实现 `checkbox_done_ids(plan)` 替换 `checkboxes_all`（design ADR-3）：按 `TASK_TITLE_RE` 位置切段（首个 `### Task` 前的前言段不归任何 task 号、其框忽略）、每段独立判全勾——复选框识别 **行锚定 `^\s*-\s+\[[ xX]\]`（非全文子串）+ 忽略 fenced code block**〔codex#4〕→ 返回号集；`plan_task_ids` 侧**检测重号 Task → 判 UNKNOWN**〔codex#3/B-1c，set 折叠会掩盖假✅〕；`decide()` 完成判据合并 `done_ids = checkpoint_done ∪ checkbox_done`，再 `done & plan_ids`（B4 不变）
- [x] 2.4 保留「plan 未提交（sha 空）且全 plan 无复选框 → UNKNOWN 双通道不可判」分支（design ADR-3）；2.1/2.2 转绿
- [x] 2.5 回归绿：`test_checkbox_fallback_advances`（全勾推进）/`test_uncommitted_plan_no_checkbox_unknown`（双通道 UNKNOWN）逐字不变

## 3. 契约同步 + 收敛〔design 协议套件 scope-check 表〕

- [x] 3.1 更新 `ship_gate.py` 头注释「已知不覆盖」（scope-check 契约点⑤）：+「污染方用旧裸格式 change stacking 进来 + 撞 plan 号」残留假✅（Non-Goal，MUST NOT 用"独立分支纪律"作缓解——立论自否，见 design Q1）+ T33 工作树 dirty 停置理由；契约表若引用 checkpoint 格式则同步命名空间
- [x] 3.2 全量 pytest 绿：`pytest sdflow-ship/tests/`（新增 R1/R2 锚测计入）+ 仓级 `pytest`（当前 328，不得回归）
- [x] 3.3 收敛：spec delta（`specs/spec-workflow/spec.md` 两 ADDED 需求）随 change，archive 时由 sdflow-done 同步进主 `openspec/specs/spec-workflow/spec.md`；Success Metrics M1-M4 逐条对齐
