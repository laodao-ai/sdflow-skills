wrote openspec/changes/sweep-pool-debt-2026-08/impl-reports/task2-brief.md: 14 lines
�archive-validation：归档 tasks.md MUST 如实反映完成状态 / 归档面校验 MUST 由 CI 机械守）

把归档区 tasks.md 收敛到「如实反映完成状态」，并加一道 CI 机械门守住归档面校验。执行序不可颠倒（DT-6）：先本地全量收敛并 `validate --archived` 0 failed，再改 CI。

- [ ] 桶B 14 个 change：逐条对照 git log / 实现 commit 回填漏勾复选框（确未做的留 `- [ ]` + 说明）
- [ ] 桶A 2 个 tickets 管线 change（remove-superpowers-pipeline 0/21、sdflow-init-readwrite-paths 0/12）：对照 git log 逐条回填
- [ ] 桶C scoped-test-per-task：tasks.md 改写为无勾选框作废说明段（指明被 remove-superpowers-pipeline supersede、从未执行）
- [ ] 本地 `openspec validate --archived` 全量 0 failed
- [ ] `.github/workflows/mechanical-gates.yml`：openspec pin 1.5.0→1.9.0 + 新增 `validate --archived` 步；新步复用既有 openspec 泳道同一 `if` 条件（CLI 仅装于 ubuntu-latest×3.12），同步更新该泳道「断言 CLI 1.5.0 具体行为」注释
- [ ] 定点破坏自证：临时引入一个未勾复选框确认该步真红后还原（恒真锚防线）

