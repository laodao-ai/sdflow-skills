<!-- R1 = Requirement「阶段三 subagent-dev 派发注入测试范围纪律」(specs/spec-workflow/spec.md) -->

## 作废说明（回填 2026-08-20，非勾选任务清单）

本 change 的全部 3 组任务**从未执行**（无 `hand-off.md` / `verify-report.md`，代码/文档零改动痕迹）。

**被 supersede 方**：`remove-superpowers-pipeline`（2026-08-12 归档）——该 change 把
`subagent-driven-development`（superpowers 实现管线）整体移除，tickets 成为阶段三唯一管线；
本 change 的核心 Requirement「阶段三 subagent-dev 派发注入测试范围纪律」是针对
`subagent-driven-development` 派发点的纪律注入，其派发点本身已随 supersede 方物理消失，
本 change 的目标载体不复存在。

**核验**：`openspec/specs/spec-workflow/spec.md` 现无「阶段三 subagent-dev 派发注入测试范围纪律」
Requirement（既未曾并入，`remove-superpowers-pipeline` 的 spec delta 中也未见其身影）；
`sdflow-init/assets/workflow/workflow.md` 步骤 6/7 措辞未见本 change 拟改的「scoped test」纪律句。

原三组任务内容（供追溯，非待办）：

1. `workflow.md` 权威源改措辞（单一源）——步骤 6/7 改为 scoped test 纪律。
2. `sdflow-ship/SKILL.md` RUN_PLAN 分支补引用式测试范围纪律注入。
3. 验证与下发——`sdflow-ship/tests/` gate 判据回归 + `sdflow-init update` 推下游。

不可勾选处置：MUST NOT 为过 `openspec validate --archived` 而补勾任何一条——任务从未执行，
勾选即记录伪造。
