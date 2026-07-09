<!-- R1 = Requirement「阶段三 subagent-dev 派发注入测试范围纪律」(specs/spec-workflow/spec.md) -->

## 1. workflow.md 权威源改措辞（单一源）

- [ ] 1.1 改 `sdflow-init/assets/workflow/workflow.md` 步骤 6：「每任务完成跑测试套件确认无 warning」→「每任务只跑覆盖本任务的 scoped test（named test files）确认无 warning；全量 `-race`/回归套件仅 final whole-branch 终审前一次」〔R1〕
- [ ] 1.2 改同文件步骤 7：「每任务完成跑测试套件」→ 同一 scoped 纪律 + 全量仅终审一次；措辞与步骤 6 保持一致〔R1〕

## 2. sdflow-ship 编排引用式注入

- [ ] 2.1 `sdflow-ship/SKILL.md` RUN_PLAN 分支：在「subagent-driven-development 自动执行」处补一句**引用式**测试范围纪律注入（引用 workflow.md 步骤 6/7 为单一源、不复述完整规则文本、**不动** checkpoint 主锚契约句）〔R1〕

## 3. 验证与下发

- [ ] 3.1 跑 `sdflow-ship/tests/` 确认 ship_gate verdict 判据（RUN_PLAN / CONTINUE_IMPL / RERUN 等）无回归——验证「措辞变更不扰动 gate 判据」scenario〔R1〕
- [ ] 3.2 `sdflow-init update` 推下游 + 本仓 `setup.sh` 刷新 `~/.sdflow`；核对下游各消费仓 `openspec/workflow/workflow.md` 托管块同步、无残差〔R1〕
