# 把三镜决策框架焊进 workflow 源头（T46）

## Why

「三镜决策框架（系统镜 / 用户镜 / 开发循环镜 + 定主次）」当前**只活在私有记忆** `decision-three-lens-framework.md`（行为层真相源）。但：

- **子代理够不着**：sdflow-spec-review / sdflow-code-review 的评审镜是 fresh-context 子代理，不继承主 session 记忆——它们做决策登记 / 自动裁决时看不到这套框架。
- **其它 checkout / 用户没有**：workflow bundle 是**发布给其它项目和用户的产品**，必须自包含；依赖某人机器上的私有记忆 = 换台机器 / 换个用户就退化。

T46 = 把框架从私有记忆**搬进发布的 workflow bundle**，让「决策必按三镜 + 定主次」跨 session / 子代理 / checkout 稳定生效，不再依赖运行者的私有记忆。

## What Changes

三处落点（均在权威源 `sdflow-init/assets/workflow/` 与自制 skill，非消费仓副本）：

1. **`spec-checklists/spec-quality-base.md` BASE-12**（书面层）：三镜评估法挂进「候选方案」、主次判定行挂进「理由」；**仅 TG-23（≥2 合理方案 / 非显然设计）触发时 MUST 写**，不下沉到琐碎决策。
2. **`workflow.md` G2 决策登记区**：登记格式「选项 + 推荐 + 两方后果」→「选项 + 推荐 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**」。
3. **`sdflow-code-review/SKILL.md` Step 4**：≥2 方案自动选推荐的「记理由」→ 按**三镜 + 主次**记，与 spec-review 决策登记口径一致、产品自包含。

**spec delta（防漂移锚）**：`spec-workflow/spec.md` 两条行为需求同步——「评审决策登记进报告」的后果字段 + 「outside-voice tension」的 TENSION 条目格式，从「各分支后果 / 两方视角」→「三面后果 + 主次判定」。

**分层强度**：行为层（私有记忆保留，仍是行为真相源）每个决策都用；书面层（bundle）只在 TG-23 触发时 MUST——避免样板税。

## Capabilities

- **Modified**: `spec-workflow` — 评审决策登记 / outside-voice tension 的决策后果格式升级为三面后果 + 主次判定。

## Priority

P2（治理层增强，非阻塞）。改动传导进此后**每个**决策的登记与裁决口径，故走独立 change + spec delta 留审计与防漂移锚（不裸改源）。

## Out of Scope

- **不改行为层记忆**：`decision-three-lens-framework.md` 仍是行为真相源，本 change 只做「私有记忆 → 发布 bundle」的搬运与锚定。
- **不重写既有 ADR**：review-tool-followups 的 ADR-0/1/2 已按三镜回填，作参考样例，不动。
- **不新增独立规则文件 / 编号项**：三镜挂进 BASE-12 现有槽（见 design ADR-1），不建 `three-lens.md` 或 BASE-30（避双源）。
