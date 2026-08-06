# 外部 skill 展开 · gstack `/document-generate`

> **一句话**：按 **Diataxis 四象限**（tutorial / how-to / reference / explanation）为一个 feature / module / 整个项目
> 从零生成结构化文档——**先通读全量代码再动笔**，杜绝"只描述一半功能"的文档。

> ⚠️ **定位澄清**：这不是 sdflow 工作流链上的一环（不像 `writing-plans` 是阶段三第 6 步）。
> 〔impl-review-fix：原文以「`/review` 是 `sdflow-code-review` 的 Step1」作类比——该依赖已由
> `absorb-gstack-review` 移除，Step1 现为自持 scope 审计，故删去该例。〕它是 **gstack 插件家族的独立通用 skill**，本仓库当前没有在 `openspec/workflow/` 或
> `sdflow-*` 编排器里调用它。可独立触发（"写文档"/"document this feature"），也可被同属 gstack 的
> `/document-release`（发版后文档更新）在发现覆盖缺口时调用来补洞。

---

## 1. 触发与调用形态

| 维度 | 内容 |
|---|---|
| 触发词 | "write docs for this" / "generate documentation" / "document this feature" / "create a tutorial" / "write a how-to" / "explain this module" / "docs for this project" |
| 调用方式 A | **独立触发**——用户直接指向一个 feature/module/项目说"document this" |
| 调用方式 B | **被 `/document-release` 调用**——后者先跑 coverage map 找出文档缺口，再把缺口实体交给本 skill 填 |
| 产物落点 | 内联到既有文件（README/ARCHITECTURE）、独立 `docs/` 目录文件，或两者都要——由 Step0 的 AskUserQuestion 决定 |
| 从不做 | 跳过 Step1 研究阶段直接写；把 tutorial 内容混进 reference 文档 |

---

## 2. 核心哲学：Diataxis 四象限

文档不是一个整体，而是服务**四种不同读者状态**的四种独立文体，各自模板、语气、验收标准都不同：

| 象限 | 读者状态 | 目的 |
|---|---|---|
| **Tutorial**（教程） | 新手，零基础 | 学习导向——手把手走一遍能跑起来的示例 |
| **How-to**（操作指南） | 已有基本认识，想完成具体任务 | 任务导向——怎么达成某个具体目标 |
| **Reference**（参考） | 需要查证细节 | 信息导向——完整、准确的技术描述 |
| **Explanation**（说明） | 想理解设计动机 | 理解导向——为什么这样设计 |

**不是每个实体都要四象限全给**。Step2 有一张判定矩阵（见下）决定某个实体该产出哪几种。

---

## 3. 完整流程（Step 0 → Step 9）

```mermaid
flowchart TD
    S0["Step0 · Scope & Intent<br/>确定文档目标(单实体/整项目/来自coverage gap)<br/>★AskUserQuestion 问落点：内联/独立文件/两者都要"]
    S1["Step1 · Codebase Archaeology（研究阶段，最重要）<br/>读入口文件+源码全文(非仅签名)+测试+既有NOTE/DESIGN注释<br/>产出内部概念图：Purpose/Key concepts/Public surface/Deps/Edge cases/Design decisions"]
    S2["Step2 · Diataxis Partitioning<br/>按判定矩阵为每个实体挑象限<br/>产出计划表；>5篇文档要★AskUserQuestion确认"]
    S3["Step3 · 先写 Reference<br/>事实性、完整、直接derive自代码，建立后续文档的词汇基础"]
    S4["Step4 · 写 Explanation<br/>先讲问题再讲方案；ASCII/Mermaid图；显式列trade-off"]
    S5["Step5 · 写 How-to<br/>标题必须'How to...'；每步必须可执行；含Verification+Troubleshooting"]
    S6["Step6 · 写 Tutorial<br/>Time-to-first-result < 3步；每步须产出可见变化"]
    S7["Step7 · Cross-Document Linking<br/>四象限互链+更新README/CLAUDE.md入口+检查死链接"]
    S8["Step8 · Quality Self-Review<br/>三道质量门：Accuracy/Completeness/Voice"]
    S9["Step9 · Commit & Output<br/>Redaction scan(HIGH凭据阻断)→点名暂存→commit→push→PR body加文档清单表"]
    S0 --> S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8 --> S9
```

| 步 | 目标 | 关键约束 |
|---|---|---|
| 0 · Scope & Intent | 定文档目标与落点 | 三选一（内联/独立/两者），**推荐"两者"**（兼顾可发现性与深度） |
| 1 · Codebase Archaeology | **全书面调研，不是抽查** | 显式要求"读实现文件全文，不是只看签名"；读测试因为它揭示预期行为、边界情况；产出结构化概念图后才准写 |
| 2 · Diataxis Partitioning | 决定每个实体产出哪些象限 | 用判定矩阵（下节）；文档数 >5 篇要先问 |
| 3 · Reference 先行 | 建立后续文档共用词汇 | **不写"为什么"**——那是 Explanation 的事；类型/默认值/约束必须写全（"接受字符串"不够，要"接受字符串，最多256字符，需匹配`^[a-z-]+$`"） |
| 4 · Explanation | 讲设计动机 | 先讲问题（真实失败模式，非抽象风险）再讲方案；trade-off 必须显式点名；**不重复 reference 内容，只链接** |
| 5 · How-to | 任务导向操作步骤 | 标题强制"How to..."；每步是可执行动词句，禁"consider whether..."类模糊表述；**任务可能失败就必须有 Troubleshooting** |
| 6 · Tutorial | 新手从零到跑起来 | **前3步内必须看到可见结果**；每步都产出可观察的变化；常见报错要内联展示错误+修法 |
| 7 · Cross-Document Linking | 保证可发现性 | 每篇新文档必须在 README 2 次点击内可达；有文档框架（Nextra/Docusaurus/MkDocs/VitePress）就接入其 sidebar/nav |
| 8 · Quality Self-Review | 三道门（见第4节） | 未通过必须修复才能进入 Step9 |
| 9 · Commit & Output | 落盘、扫描、提交 | **先过 redaction scan**（阻断 HIGH 级真实格式凭据泄漏）→按文件名逐个暂存（禁 `git add -A`）→commit→push→若有 PR 则在 PR body 追加文档清单表 |

---

## 4. Step8 质量门（三道，缺一不可）

- **Accuracy gate**：每个代码示例必须真能跑/编译/通过；每个 API 描述与实际签名一致；每个展示的命令产出描述中的结果；不留对已改名/删除实体的过期引用。
- **Completeness gate**：reference 覆盖 100% 公开接口；how-to 覆盖用户最可能尝试的前 3 个任务；tutorial 在 ≤3 步内出现可运行结果；explanation 点名 trade-off 而非只列选择。
- **Voice gate**：面向"聪明但没看过代码的人"写；术语首次出现要有简短内联注释；主动语态、具体名词、短句；用"你现在可以……"而非"该系统提供……"。

---

## 5. 值得注意的机制设计

1. **研究先于写作是硬规则**——Step1 明确写"这是最重要的一步，不要跳过或赶工"，且要求产出结构化概念图（Purpose/Key concepts/Public surface/Dependencies/Dependents/Edge cases/Design decisions）才允许进入分区阶段。防的是"文档只描述了一半功能"这类失败模式。
2. **四象限模板严格分工，禁止串味**：Reference 不解释 why，Explanation 不重复 reference 内容只链接，How-to 不教基础只讲任务——这条规则在 Important Rules 段重申，是全篇唯一被反复强调两次以上的红线。
3. **Tutorial 的"3步内见效"是量化验收标准**，不是模糊建议——Step6 规则与 Step8 Completeness gate 都各写了一遍同一条硬指标。
4. **提交前有实质性机械防护**：redaction scan 调 `gstack-redact` 对暂存内容做 HIGH 级凭据检测，命中就阻断提交（`example` fence 或 `AKIAIOSFODNN7EXAMPLE` 这类明显占位符会被过滤，但真实格式的凭据不会被 fence 豁免）——这是本 skill 里少数带机械校验而非纯自觉的环节。
5. **Commit 作者标注为 `Claude Opus 4.7`**——是 SKILL.md 模板里写死的字符串，不随实际运行模型变化，调研时不必当作"用了 Opus"的证据。

---

## 6. 与 gstack 通用基础设施的关系

SKILL.md 全文 1253 行，其中约 650 行（Preamble、AskUserQuestion Format、Artifacts Sync、Voice、Context Recovery、
Question Tuning、Telemetry 等）是 **gstack 全家 skill 共用的样板层**（session 追踪、遥测、跨会话记忆、升级检查、
CJK 转义规则等），并非 document-generate 独有的行为。本篇只展开 Step0–Step9 的**该 skill 特有编排逻辑**；
共用层细节可参考本目录下其他 `gstack-*` 展开文档（如 `gstack-review.md`）中的类似章节，此处不重复摘录。

---

## 7. 小结

- 核心贡献不是"能写文档"，而是**用 Diataxis 四象限把文档按读者场景切开**，并给每个象限配了独立模板、独立验收规则。
- 流程强制"研究通读全量代码 → 建概念图 → 分区 → 按象限顺序写（reference 先行建词汇 → explanation → how-to → tutorial）"，
  次序本身编码了"参考文档是后续文档共用词汇表"这条设计判断。
- 质量把关基本靠模型自觉（Step8 三道 gate 无机械校验工具），**唯一机械防护点是提交前的凭据 redaction scan**。
- 当前未接入本仓库 `sdflow-*` 编排链；若未来要用它给 sdflow-skills 自身生成 Diataxis 文档，需要额外决定：
  独立跑，还是包一层编排（类似 `sdflow-code-review` 之于 `/review`）来控制触发时机与产物落点。
