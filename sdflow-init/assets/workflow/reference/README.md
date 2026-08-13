# reference/ — 说明文档（非 load-bearing，可删）

本目录是 spec 工作流的**纯说明 / 方法论文档**。它们解释「为什么这么设计」，
供人阅读理解，**不被 `config.yaml` 引用、不驱动任何执行步骤**。

> **删除本目录不影响工作流运行。** 工作流的执行依赖在上一级目录（本 bundle 权威源，
> 运行时经全局 canonical `~/.sdflow/workflow/` 解析）的操作文件：`trigger-catalog.md` /
> `spec-checklists/` / `design-diagrams.md` / `ff-generation-constraints.md` /
> `generation-process.md` / `spec-review.md` / `workflow.md`。

## 内容

| 文件 | 是什么 |
|------|--------|
| `Spec_Quality_Methodology.md` | L3 方法论：两轴元模型 + 三原则 + V&V（为什么这么设计质量体系） |
| `Spec_Quality_Collaboration.md` | brainstorming vs autoplan 的覆盖分析（历史分析） |
| `PRD_vs_Spec.md` | PRD 与 spec 的概念区分 |
| `quality-layering.md` | 质量分层 Prevention/Inline/Residual（代码层 shift-left）：为什么生成期已三层审、领域清单注入终审、事后 sdflow-code-review 仍每次全跑·独立冷·强制主审（P3c；消的是通用质量冗余，非缩掉 sdflow-code-review。操作指令在 workflow.md，本文只解释为什么） |
| `scope-drift-diagnosis.md` | 协议/契约文档漂移诊断：未完成 vs 未列入、诊断捷径、反 pattern（生成期强制动作在 BASE-29/TG-25，本文只解释为什么 + 排障） |

## 操作类 ⇄ 说明类 的划分判据

是否被 `config.yaml` 引用 / 是否驱动执行 → 是则操作类（留上级目录），否则说明类（放本目录）。
