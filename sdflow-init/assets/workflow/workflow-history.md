# workflow 演进史（考古层）

> **正文即最终态（DOC-1）**：`workflow.md` 只放当前约束。
> 本文放**只有读过上一版的人才需要**的东西——它不构成任何当前约束。
> **模型 MUST NOT 为了执行流程而读本文。**

### A1 · 相对旧版 15 步手动 runbook，去掉了什么

| 旧 step | 去向 |
|---|---|
| 两个 `/clear` 会话断点 | **删** —— 独立性由子代理 fresh context 给，不由 `/clear` 给（§三.2） |
| 旧 step 7「手动合并两份报告」 | **删** —— `sdflow-spec-review` 编排器内部合成一份 |
| 旧 step 11 独立 `gstack/review` | **并入** `sdflow-code-review` 的 Step1 |
| 旧 step 12「`sdflow-code-review` 高风险才跑」 | **升级为每次全跑**〔P3c〕 |
| 旧 step 13 官方 `/code-review` 独立 step | **弃用**〔P3d〕——插件能力仅内部借用 |
| 旧 step 14 人类门 | **删** —— 阶段三无人类门〔P3e〕 |

### A2 · prompt 从表格搬进 `prompts/`（2026-07-14）

原来每步的 prompt 全文内联在 §二 的表格单元格里。问题：**模型为了取一行 prompt，要 `Read` 整份 19.6KB
的 workflow.md**——而它只需要其中 300 字节。

现在 prompt 的**单一源 = `prompts/step*.md`**，一步一文件；表格只留指针；
人读完整版 = **`WORKFLOW-GUIDE.md`（生成物，prompt 全文内联）**，由 `hack/gen_workflow_guide.py` 从
本文件 + `prompts/` 机械拼装，**MUST NOT 手改**（改了会被下次生成覆盖，且与单一源漂移）。

### A3 · grill 的 wayfinder「瘦跑」已废除（2026-07-14）

原 grill prompt 有一段：「上游 wayfinder 已决分支：引 resolution 快速核对即过」。**已整段删除。**

**理由**：瘦跑本身就在破坏 grill 的独立性——拿上游产出给自己松绑，二次审视就退化成盖章。
`ff-generation-constraints.md` 的 `wayfinder-resolved:` 锚现在**只用于溯源**，不再是任何减负判据。

### A4 · `sdflow-roadmap` 讨论层的 wayfinder 三分支路由已移除（2026-08-06）

`sdflow-roadmap` 原按规模三分支路由（explore / wayfinder 铺图 / office-hours），wayfinder 分支
产出 `openspec/roadmaps/{name}/footage/` map + ticket 票（`open/claimed/resolved/abandoned` 状态机）。
`refactor-roadmap-internalize-deps` 将讨论层内化为单一 memo 载体（三态 create/continue/replan +
七维拷问），删除该三分支路由与 footage 落盘机制；`openspec/matt/` 套件（issue tracker / triage
labels / domain docs）随之整体移除（前提消解：无 wayfinder 调用点）。

`ff-generation-constraints.md` 的 `wayfinder-resolved:` 前缀溯源规则**保留但标 legacy**——消费仓
**存量**（重构前生成）footage 仍可能被该前缀溯源引用；新建 roadmap 包不再产生此前缀的新实例。
