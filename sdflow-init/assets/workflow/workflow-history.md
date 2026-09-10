# workflow 演进史（考古层）

> **正文即最终态（DOC-1）**：`workflow.md` 只放当前约束。
> 本文放**只有读过上一版的人才需要**的东西——它不构成任何当前约束。
> **模型 MUST NOT 为了执行流程而读本文。**

### A1 · 相对旧版 15 步手动 runbook，去掉了什么

| 旧 step | 去向 |
|---|---|
| 两个 `/clear` 会话断点 | **删** —— 独立性由子代理 fresh context 给，不由 `/clear` 给（§三.2） |
| 旧 step 7「手动合并两份报告」 | **删** —— `sdflow-spec-review` 编排器内部合成一份 |
| 旧 step 11 独立第三方广审工具 review 步骤 | **并入** `sdflow-code-review` 的 Step1 |
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
七维拷问），删除该三分支路由与 footage 落盘机制。

**同批（非同因）移除**：`openspec/matt/` 套件（issue tracker / triage labels / domain docs）在同一
change 内一并删除，但**与本次讨论层重构无因果关系**——`git log` 实测 `sdflow-issues` 生于本仓首个
commit（2026-07-03），早于 `openspec/matt/` 建立（2026-07-10）一周；本仓自始至终用 `sdflow-issues`
追踪工作项，matt 的 issue-tracker 角色**从未真正投入使用**，属历史遗留死配置、独立可删。同批处置
的理由是 fold 判据（相关且低成本），不是依赖关系。详见 `openspec/adr/0037-roadmap-discussion-layer-internalization-and-matt-removal.md`。

`ff-generation-constraints.md` 的 `wayfinder-resolved:` 前缀溯源规则**保留但标 legacy**——消费仓
**存量**（重构前生成）footage 仍可能被该前缀溯源引用；新建 roadmap 包不再产生此前缀的新实例。

### A5 · 「③ 生成过程」从三相位四 skill 收窄为两相位两 skill（`sdflow-spec` 吸收 brainstorming + grill）

`generation-process.md` 原版 §二把「③ 生成过程」拆成三个相位：**发散**（`opsx:explore`）、
**收敛**（`brainstorming`，逼出 2-3 方案 → 逐段批准 → 落设计）、**对抗压测**（`grill-me` /
`grill-with-docs`，把设计往死里问、逐分支死磕薄弱处）。§三进一步论证：`config.yaml` 把①结构、
②约束固化后，`brainstorming` 的机械步被吸收（方案落 BASE-12 槽、自检靠 S 扫描、写文档靠 ff），
只剩 R 桶；而 grill 正是专锤 R 桶的工具，逐项命中标准与锚：

| grill（尤其 -with-docs）的动作 | 命中的标准 / 锚 |
|------|------|
| 揪模糊 / 重载术语 → 定准 | BASE-09 歧义 / 术语定义 |
| 代码 vs 主张 不一致就揭穿 | D-1 代码事实（Accurate · 锚① 代码库） |
| 编边界场景压测 | BASE-01 四类场景 + BASE-06 错误路径 |
| 逐分支死磕决策树 | BASE-27 时序可执行性（实现者会卡哪） |
| 落 ADR + 词汇表 | BASE-12 ADR + 锚③ 既有决策 / ADR |

当时的结论：**brainstorming 是"产设计"的收敛器，grill 是"锤设计"的对抗器**——结构与约束已被
config 守住后，真正稀缺的是对抗压测，grill 比再跑一遍 brainstorming 的机械自检更值钱。

**后续演进**：`/sdflow-spec` 上线后把「发散 + 对抗 + 生成」收进一个入口——相位 A 澄清、相位 B 拷问
（承接原 grill 锤炼 R 桶的职责）、相位 C 生成四件套一次连续跑，且拷问结构性前置于成文（改想法比
改四份成文便宜）。`brainstorming` / `grill-me` / `grill-with-docs` 三个独立 skill 不再是「③ 生成
过程」推荐流水线的组成部分，`fix-workflow-bundle-staleness` 据此把 §二 现行化为「两相位两 skill」
（`opsx:explore` + `/sdflow-spec`），§三整节移入本条。
