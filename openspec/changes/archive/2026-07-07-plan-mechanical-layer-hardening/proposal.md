# plan-mechanical-layer-hardening

## Why

`openspec/CONTEXT.md` 的 adr/0006 已把「机械 prose 协议 MUST 脚本化/结构化」定为硬约束，但这条契约的执行面尚未系统化规划。三镜 survey 实测出一批待固化点（模型手数/手循环/字符串编码致解析歧义/镜像漂移无守卫），够格作一个**跨多次 change 的长期规划**——需要 roadmap 层级统摄。

## What Changes

本变更是**规划型 change**（rule 4/5）：交付物是产出 `openspec/roadmaps/mechanical-layer-hardening/` 下的 roadmap 文档包，**不实施任何脚本/迁移**。实际实施由未来独立变更（`implement-mechanical-layer-hardening-pN-*`）按 roadmap 阶段驱动。

- 产出 roadmap 四件套（requirements/design/roadmap/task-log）+ memo。
- 两腿六阶段：Leg1 脚本化（P1-P4，就绪优先）→ Leg2 去字符串化（P5 S1 就绪需先评 ROI、P6 S2 north-star 不排期）。
- 不产 capability spec（规划 change 无规范增量；各实施阶段的规范增量落 spec-workflow 或各 recorder skill 自包含约定）。

## Impact

- Affected: `openspec/roadmaps/mechanical-layer-hardening/`（新增文档包，长期真相源）。
- 无代码/脚本改动、无 spec delta。
- 承接：ADR 0010（家族② defer 判据）、T65（家族① 动机，todolist）、workflow-cost-optimization roadmap（正交姊妹）。
