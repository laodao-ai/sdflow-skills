### Task 2: gate 单名 resolver 与测试同步

**Blocked-by:** 1
**R-ID:** R2, R7, R8

`ship_gate.py` 的 `PLAN_FILENAMES` 缩为 `("tickets.md",)`（保留 resolver 函数形状供 gate/测试共用）；删双存在判 UNKNOWN 分支与旧名收尾票 grandfather 分支；RUN_PLAN reason / UNKNOWN 表 / 文件头注释中的双名表述改单名；`PLAN_FILENAMES` 上方「共享 resolver」说明注释块（引用已删符号 `impl_route.resolve_pipeline`）改写。新增遗留旧名兜底：`tickets.md` 缺席 ∧ `superpowers-plan.md` 存在 ⇒ fail-closed 判 UNKNOWN + 人工清理提示（设计门 Q1 拍板）。

测试同步（63 处 fixture 迁移是本票主要工作量）：
- `test_plan_resolver.py`：旧名探测 / 双名 UNKNOWN / 改名迁移窗口用例退役；Q1 兜底分支配一条新测试（遗留旧名单独存在 ⇒ UNKNOWN）。
- `test_superpowers_track_regression.py`：整文件删除（存在意义即保护旧轨）。
- gate 共享 fixture `approved_change` 默认写入名改 `tickets.md`，7 个消费文件（test_gate_git_layer / test_gate_freshness / test_gate_namespace / test_gate_impl_progress / test_gate_tail / test_gate_reviewed_sha / test_plan_resolver）63 处调用逐一核验旧名语义依赖。
- `test_gate_closing_ticket.py` 的 `test_grandfather_old_name_without_closing_ticket_not_rejected`（:130）与 `test_plan_closing_ticket_check_grandfathers_old_name`（:160）退役。
- `test_harden_sdflow_spec_followup_closure.py` fixture 改名 `tickets.md`。
- 完成判据窗口（`git log --diff-filter=A` 锚 `tickets.md`）与收尾票无条件校验回归：sdflow-ship 全测试套绿。

- [ ] `PLAN_FILENAMES` 已缩为单名，双存在 UNKNOWN / grandfather 分支已删
- [ ] 遗留旧名兜底分支已新增并配测试
- [ ] `test_plan_resolver.py` 旧名相关用例已退役
- [ ] `test_superpowers_track_regression.py` 已整文件删除
- [ ] 共享 fixture `approved_change` 默认写入名已改 `tickets.md`（7 文件 63 处核验）
- [ ] `test_gate_closing_ticket.py` 两条 grandfather 用例已退役
- [ ] sdflow-ship 全测试套绿（含完成判据窗口与收尾票校验回归）

