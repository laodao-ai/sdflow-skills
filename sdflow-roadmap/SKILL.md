---
name: sdflow-roadmap
description: |
  制作"分阶段 roadmap"的规划工作流。产出 4 件套（requirements / design / roadmap / task-log）+ 可选 memo，
  保存到 `openspec/roadmaps/{name}/` 作为项目长期真相源，并通过一个 OpenSpec 变更承载本次产出过程。
  触发场景：开始新项目、面对大量需求需要梳理、准备大规模重构、想分阶段实施一个超出单次变更能完成的事。
  用户说"做一个 roadmap"、"帮我规划 xxx"、"分阶段实现 xxx"、"先想清楚再动手"、"有一堆事不知道从哪开始"、
  "重构计划"、"新项目怎么起步"、"这个项目太大了要拆"时必须使用本 skill。即使用户没明说"roadmap"三个字，
  只要项目规模超出单次 change 能完成，就主动建议使用本 skill——宁可 trigger 后发现不需要轻量退出，
  也不要漏掉让用户陷入"边做边改"的陷阱。Trigger with /sdflow-roadmap。
---

# Roadmap Planner

把一个**超过单次 change 能完成**的项目/重构/需求集合，转化成分阶段可执行的规划文档包。产出 4 件套（+ 可选 memo）保存到 `openspec/roadmaps/{name}/`，作为项目长期真相源。

## 为什么需要这个 skill

SDD（Spec-Driven Development）的最小必要集是"先想透再动手"。OpenSpec 的 `/opsx:new` 很好地承载了**单次变更**的 spec→design→tasks→implement，但面对"项目级"规模（多阶段、多变更、跨月）时，单次变更太小——需要一个比变更更大的层级来统摄**长期规划**。

roadmap 就是这个层级：

| 层级 | 位置 | 读者 | 生命周期 |
|---|---|---|---|
| **roadmap 文档包** | `openspec/roadmaps/{name}/` | 人类 + AI 助手 | **长期**（贯穿整个项目） |
| OpenSpec 变更 | `openspec/changes/{change-name}/` | 工具 + 归档查阅 | 短期（一次交付即归档） |

两者协作：roadmap 的每个阶段子任务 → 对应一次未来的 OpenSpec 变更。

## 必须遵守的硬性规则

这些是本 skill 的**不可妥协点**，违反其中任何一条都会让产出失去价值：

### 规则 1：保存位置硬性固定

- roadmap 四件套必须保存到 `openspec/roadmaps/{kebab-case-name}/`
- `{name}` 用 kebab-case，语义化、短小（如 `rebuild-blog-v2`、`migrate-to-pg`、`unify-auth`）
- **禁止**放到 `doc/blog/`、`docs/`、`plans/` 等其他位置——这是历史教训（博客 v2 初版放 `doc/blog/` 后期被迫迁移）

### 规则 2：子任务 = 一次 OpenSpec 变更的粒度

- `roadmap.md` 里每个子任务应该**恰好是一次 `/opsx:new` 能完成的工作**
- 如果某个子任务感觉要拆成 5 个 change 才能做完 → 它本身应该是一个"子阶段"，而非一个任务
- **禁止**在 roadmap 阶段做"子任务的细化"——那是未来实施变更（`implement-{phase-name}`）的 scope

### 规则 3：四件套不引用 memo

- 正式四件套（requirements / design / roadmap / task-log）之间可以互相引用
- `memo.md`（讨论备忘，可选）**不出现在四件套的任何引用里**，哪怕"详见 memo"也不行
- 理由：memo 是"决策形成过程"的考古证据，正式文档是"决策结晶"。血统类比：memo 是 footage，design §决策 是 edit。如果正式文档引用 memo，会让读者以为 memo 是权威源，但其实 memo 是讨论草稿
- memo 可以独立存在，作为历史参考

### 规则 4：产出过程必须通过 OpenSpec 变更承载

- 本次产出不是"直接 Write 一堆文件"，而是通过一个 `/opsx:new` 创建的变更**承载**
- 变更命名：`plan-{kebab-case-topic}` 或 `rebuild-{kebab-case-topic}`
- 产出物路径：保存到 `openspec/roadmaps/{name}/`，不是变更内部的 `specs/`
- 变更完成后走 `/opsx:archive` 归档

### 规则 5：只做规划，不实施

- 本 skill 输出**文档**，不输出代码、不配置服务器、不创建仓库
- 实施动作留给"未来的 OpenSpec 变更"（`implement-blog-phase-1` 这类）
- 如果用户在 roadmap 产出过程中要求"顺手把 X 也做了"，提醒他：那属于阶段 1 实施变更的 scope

---

## 启动检查：评估讨论充分度

roadmap 的质量 100% 取决于讨论是否充分。开工前**必须**先评估：

```
□ 目标用户 / 受众清楚吗？
□ 核心功能的"要做 vs 不做"已经划清了吗？
□ 关键技术路径有 2+ 候选方案对比过吗？
□ 阶段划分有过构思（不要求最终版）吗？
□ 已知的主要权衡 / 风险已识别吗？
```

### 5 项全通过 → 直接进入"产出阶段"

用户通常已经经过一轮充分讨论（可能是前一轮对话里的），此时 roadmap-planner 可以直接起草。

### 任一项未通过 → 先做发散讨论

根据用户描述的项目性质，选合适的讨论工具：

**主用 `/opsx:explore`**（绝大多数场景）
- 进入探索模式，与用户对话式地吃透需求 / 方案 / 阶段
- explore 里的决策可以自然沉淀到 `design.md`，过渡无缝

**例外 1：偏商业可行性 → 先 `/office-hours`**（再回来走 explore）
- 触发信号：用户描述里有"获客"/"变现"/"用户画像未定"/"要不要做这个产品"
- 典型例子：面向外部用户的 SaaS、社区、付费工具
- office-hours 的 6 问（Demand/Status-quo/Wedge/Observation/Future-fit）把需求真实性逼出来后，再回到 explore 讨论技术路径
- **不触发**的场景（绝大多数）：技术重构、内部工具、基础设施、博客/文档工程、个人项目

**例外 2：单个 feature 的深度设计 → `/superpowers:brainstorming`**
- 这不在 roadmap-planner 主流程里，而是**未来实施变更内部**用
- 触发时机：阶段 X 实施时，某个子任务需要对比 2-3 个架构方案并产出正式 design doc
- roadmap-planner 里**只提及**此情况，不调用

---

## memo.md 策略：讨论规模预估

讨论阶段是 skill 最脆弱的环节——它不产出正式文档，一次上下文压缩或 `/clear` 就能让"为什么选 C 而不是 A/B/D"的推理过程永久消失。`memo.md` 是这段过程的**唯一**可持久化载体。

开工前必须评估讨论规模，据此选定 memo 策略：

| 预估讨论规模 | memo 策略 |
|---|---|
| **短**：<10 轮、单次 session 内完成 | 可选；如不写，`design.md` 的"决策"章节要写得足够厚实 |
| **中**：10-30 轮、单 session 内 | 建议讨论结束时一次性 flush 到 `memo.md` |
| **长**：>30 轮、跨 `/clear`、跨天、或跑过 office-hours 6 问 | **强制**：阶段 1 开始即 `touch memo.md` 骨架，讨论中增量 append |

**规模判别不确定时向上一档取**——倾向多留 footage、少丢推理过程。

**"强制"只指"必须存在且被持续更新"**——不要求措辞优雅。memo 是 footage，不是 edit；粗糙是它的正常形态。不要因为怕写得不好看就不写。

与启动检查 A（讨论充分度）的关系：A 问"讨论够不够深"，此节问"讨论要不要留痕"。两者**都过**才进入工作流阶段 2。

---

## 工作流：五阶段

```
┌─ 阶段 1：讨论（按需触发 explore / office-hours）─┐
│   确认讨论充分度 → 不足则先讨论                   │
└───────────────────┬────────────────────────────┘
                    ▼
┌─ 阶段 2：开 OpenSpec 变更 ─────────────────────┐
│   /opsx:new plan-{topic}  或  rebuild-{topic}  │
│   变更的 proposal/design/tasks 承载"产出过程"  │
└───────────────────┬────────────────────────────┘
                    ▼
┌─ 阶段 3：产出四件套到 openspec/roadmaps/{name}/ ─┐
│   requirements.md / design.md                    │
│   roadmap.md / task-log.md                       │
│   (可选) memo.md                                 │
└───────────────────┬──────────────────────────────┘
                    ▼
┌─ 阶段 3.5：交叉 review（强烈建议）────────────┐
│   /autoplan （一键三合一，推荐）               │
│   或单跑 /plan-ceo-review / /plan-eng-review  │
│         /plan-design-review                   │
│   针对 4 件套内容质量做批判性审视             │
└───────────────────┬───────────────────────────┘
                    ▼
┌─ 阶段 4：归档变更 ────────────────────────────┐
│   /opsx:archive {change-name}                 │
│   roadmap 文档包留在 openspec/roadmaps/       │
└───────────────────────────────────────────────┘
```

**重要澄清**：`opsx:verify` ≠ 内容 review。它只检查"实现做到了 spec 承诺"（合规性），**不看内容质量**。roadmap 的内容质量把关靠阶段 3.5 的 plan-review skill，不能省、也不能被 verify 替代。

### 阶段 2 详细：开 OpenSpec 变更的做法

有两种路径，依项目复杂度选：

**路径 A：`/opsx:new {name}`**（推荐，深度可控）
- 适合项目比较大，需要分步讨论 proposal → design → specs → tasks
- 每个产出物按依赖顺序生成

**路径 B：`/opsx:ff {name}`**（快速，一把梭）
- 适合讨论已经充分、直接把结论倾注到所有产出物
- 适合已经做过 explore 并得出明确结论的场景

两种路径完成后，变更的 `tasks.md` 应当指向"产出 roadmap 文档包"：

```markdown
## 范围说明

本次变更的交付物是产出 `openspec/roadmaps/{name}/` 下的 roadmap 文档包。
实际实施由未来的独立变更（如 `implement-{name}-phase-1`）按 roadmap 阶段分解驱动。

## 1. 归档 / 整理（如有废弃文档需处置）
- [ ] ...

## 2. 产出 roadmap 文档包
- [ ] 2.1 生成 openspec/roadmaps/{name}/requirements.md
- [ ] 2.2 生成 openspec/roadmaps/{name}/design.md
- [ ] 2.3 生成 openspec/roadmaps/{name}/roadmap.md
- [ ] 2.4 生成 openspec/roadmaps/{name}/task-log.md
- [ ] 2.5 (可选) 保留或生成 openspec/roadmaps/{name}/memo.md

## 3. 交叉 review（强烈建议，别跳过——见陷阱 6）
- [ ] 3.1 把 4 件套作为"整体 plan"显式说明给 review skill（见 SKILL.md 阶段 3.5 的措辞）
- [ ] 3.2 默认跑 `/autoplan`；或按侧重单跑 `/plan-eng-review`、`/plan-ceo-review`、`/plan-design-review`
- [ ] 3.3 将 review 产出的**所有 issue** 列入 `task-log.md` 的 "## Review 处置" 小节，每条必须显式标注下列状态之一：
      - ✅ **采纳**：写明已在哪个文件哪一节改动
      - ❌ **拒绝**：写明拒绝理由（不得空白"不采纳"，理由必须可供后人复核）
      - ⏭ **延后**：写明延后到哪个阶段 / 哪个后续变更处理
- [ ] 3.4 确认 `task-log.md` "## Review 处置" 小节**不存在"未处置"状态**的条目——此条是归档前的**人工复核项**（作者或 AI 目视扫一遍）。`/opsx:verify` 自身不扫此小节，将来若给 verify 接 post-hook 可自动化此检查
- [ ] 3.5 （如整体跳过 review）在 `task-log.md` 留一条"未做 review，风险自担"的痕迹，归档前再确认一次该决定

## 4. 交叉引用
- [ ] 4.1 在 CLAUDE.md 补充 roadmap 索引（建议但非必须）

## 5. 归档本变更
- [ ] 5.1 通过 `/opsx:archive` 归档
```

### 阶段 3 详细：产出四件套

每个文件使用 `references/` 下对应的模板骨架。读对应模板，按项目实际内容填充。模板里有占位符和"为什么"注释，指引如何取舍。

| 文件 | 内容核心 | 模板 |
|---|---|---|
| `requirements.md` | WHAT：做什么、为谁做 | `references/requirements-template.md` |
| `design.md` | HOW + WHY：怎么做、为什么这么做 | `references/design-template.md` |
| `roadmap.md` | WHEN：分阶段计划 + 每阶段验收 | `references/roadmap-template.md` |
| `task-log.md` | DID：执行过程记录（初始占位） | `references/task-log-template.md` |
| `memo.md` (可选) | 讨论备忘，考古用 | `references/memo-template.md` |

> 浏览 roadmap 文档包：用项目根 `openspec/serve.sh` 起 HTTP 服务、开 `openspec/review.html`（根查看器经路径 scope 导航到任意 `roadmaps/{name}/`）——不再每目录生成 `review.html` stub。

#### 4 件套之间的引用关系

```
requirements.md  ◀── design.md 引用（需求是设计依据）
                 ◀── roadmap.md 引用（阶段验收对应需求）

design.md        ◀── roadmap.md 引用（阶段分解基于架构）

roadmap.md       ◀── task-log.md 引用（日志记录 roadmap 的任务完成）
                 
memo.md          ✗  任何正式文档都不引用 memo（见规则 3）
```

### 阶段 3.5 详细：交叉 review（强烈建议，不是可选）

roadmap 4 件套写完就走归档，等于"spec 没评审就交付"——能用但埋雷。建议走一轮交叉 review 把内容质量问题暴露出来。

#### 为什么要 review（不能跳过的 3 种情况）

- **项目跨月、涉及多个阶段** → 小错误会在后续阶段被放大 10 倍
- **技术选型有 2+ 候选方案对比过** → review 可以挑战"为什么最终选 X"
- **作者是独立判断**（没有团队评审） → plan-review skill 是"自动化的二审"

#### 4 个 review skill 的分工

| Skill | 视角 | 重点 | 最适合 |
|---|---|---|---|
| `/plan-ceo-review` | CEO / 创始人 | scope、ambition、10 星产品盲区、premise 挑战 | 有商业/产品野心的项目 |
| `/plan-eng-review` | Eng Manager | 架构、数据流、边缘情况、阶段依赖、估时合理性 | **所有技术性项目**（几乎必做） |
| `/plan-design-review` | Designer | 每个设计维度 0-10 打分 | 含 UI/UX 组件的项目 |
| `/autoplan` | 合集 | 顺序跑 CEO + eng + design，6 原则自动决策，taste 级分歧才问作者 | "懒人模式" / 大项目 |

#### 推荐的触发方式

**默认推荐 `/autoplan`**——一次跑完三者，最后只在 taste-level 分歧时叫作者拍板。

**单跑**适合有明确侧重的场景：
- 只关心技术架构 → `/plan-eng-review`
- 简单项目想省时 → 单跑 `/plan-eng-review`，其他两个跳过
- 纯技术重构无产品野心 → CEO review 可跳
- 含前端 UI → 必加 `/plan-design-review`

#### 关键：把 4 件套作为"整体 plan"告诉 review skill

review skill 原本设计给**单个 plan 文件**。roadmap 是**多文件 4 件套**。触发时必须显式说明：

> 请把 `openspec/roadmaps/{name}/` 下的 `requirements.md` + `design.md` + `roadmap.md` 视为一个整体 plan 来 review。`roadmap.md` 是主入口，它引用其他两份作为上下文。`task-log.md` 是初始占位，不用 review。

不这样说，review skill 会只盯其中一份文件，遗漏跨文件的一致性问题（如 requirements 里的 P1 功能在 roadmap 里没对应阶段）。

#### 跳过 review 的"合理"场景（且必须留痕）

- **修复型小项目**（fix-xxx），范围极小
- **已经做过充分外部 review**（比如跟同事白板讨论过）
- **时间极紧**——但必须在 `task-log.md` 里留一条"未做 review，风险自担"

#### review 结果如何处理

- review skill 有 Edit 权限，通常会**直接改** requirements/design/roadmap 文件
- 重大建议：作者拍板后手动改（review 给建议，不自动执行）
- review 通过后，才进入阶段 4 归档

---

### 阶段 4 详细：归档变更

```bash
# 检查所有产出物状态
openspec-cn status --change {change-name}

# 归档（如有 spec 增量，会同步到主规范）
openspec-cn archive {change-name} -y
```

归档后：
- 变更目录移到 `openspec/changes/archive/{date}-{name}/`（作为历史快照，不再更新）
- 3 个 capability（如有）进入 `openspec/specs/` 成为主规范
- **roadmap 文档包留在 `openspec/roadmaps/{name}/`** 作为持续更新的长期真相源

---

## 命名规范

### roadmap 目录名（= 变更名）

- **kebab-case**，语义化
- 动词开头优先（表达"要做什么"）
- 长度建议 ≤ 30 字符
- 例：`rebuild-blog-v2`、`migrate-to-postgres`、`unify-auth-system`、`add-analytics-pipeline`

### 变更名 vs roadmap 目录名

通常**相同**，即变更名就是 roadmap 目录名（见"博客 v2"实例：变更 `rebuild-blog-v2` ↔ roadmap `openspec/roadmaps/blog-v2-rebuild/` —— 实际上可以更一致地叫 `openspec/roadmaps/rebuild-blog-v2/`）。

建议：**变更名和 roadmap 目录名保持完全一致**，避免未来追溯时多个名字对应同一件事。

---

## 下游：阶段实施

roadmap 完成只是起点。后续每个阶段通过独立的 OpenSpec 变更推进：

```
/opsx:new implement-{roadmap-name}-phase-1    # 阶段 1 实施
/opsx:new implement-{roadmap-name}-phase-2    # 阶段 2 实施
...
```

每个实施变更的 proposal 里：
- **背景**：引用 `openspec/roadmaps/{name}/roadmap.md` 的对应阶段章节
- **设计复用**：`openspec/roadmaps/{name}/design.md`
- **规范扩展**：`openspec/specs/{capability}/`（如有相关 capability）

**阶段实施时如果某个子任务需要深度架构设计** → 切到 `/superpowers:brainstorming`（2-3 方案对比 + 单 feature design doc）。这是 brainstorming 的原生颗粒度。

---

## 常见陷阱

### 陷阱 1：讨论没充分就开始起草

**表现**：用户说一句"帮我做个 roadmap 吧"，skill 立刻开始写 requirements.md。

**后果**：写出的 roadmap 空洞、假设错误、阶段划分混乱，后续实施时不断推翻重来。

**正确**：过启动检查 5 条 checklist，不足就先 explore。

### 陷阱 2：子任务粒度过细

**表现**：roadmap.md 里的子任务写成 "配置 nginx HTTPS / 申请 Let's Encrypt 证书 / 配置 SSL 参数" 三条分列。

**后果**：这三条应该是一次"VPS 基础加固" change 内部的 checklist 项，而不是 roadmap 阶段的子任务。

**正确**：roadmap 子任务 = "VPS 基础加固"（一整体），一次变更能完成；具体 checklist 在该变更的 tasks.md 里。

### 陷阱 3：memo 被当成正式文档引用

**表现**：requirements.md 写"详见 `memo.md` §2.4"。

**后果**：memo 是草稿，未经打磨，长期维护成本高；读者看到引用会以为 memo 是权威源。

**正确**：memo 里有价值的内容**精炼或复制**进四件套；四件套不引用 memo。

### 陷阱 4：roadmap 文档包保存到错误位置

**表现**：保存到 `doc/` 或 `plans/`。

**后果**：与 OpenSpec 工作流脱钩，未来实施变更找不到引用路径；需要迁移时要改大量路径引用（博客 v2 的真实教训）。

**正确**：固定 `openspec/roadmaps/{name}/`，没有例外。

### 陷阱 5：变更内部也生成了一份 4 件套

**表现**：`openspec/changes/{name}/` 下也产出了 requirements/design/roadmap 等。

**后果**：同一内容两处存在（变更内部 + roadmap 目录），未来维护成本翻倍。

**正确**：变更内部只有 SDD 标配（proposal/design/specs/tasks，其中 design 和 tasks 可以简短指向 roadmap 目录）；roadmap 4 件套只在 `openspec/roadmaps/{name}/` 存在。

### 陷阱 6：只跑 opsx:verify 不跑 plan-review（把合规当质量）

**表现**：觉得"/opsx:verify 就是 review"，跳过阶段 3.5 的 plan-review。

**后果**：`opsx:verify` 只检查"实现做到了 spec 承诺"（合规性），**不看内容质量**。roadmap 里的错误架构决策、不合理阶段划分、遗漏的需求，都能通过 verify 但在 plan-review 里暴露。

**正确**：分工清晰，两者不重叠、都不能省：
- `/opsx:verify` = **合规检查**（实施完成后、归档前确认"做了什么 = 承诺了什么"）
- `/autoplan` 或 `/plan-{ceo,eng,design}-review` = **内容质量评审**（roadmap 产出后、归档前审视"承诺的东西合不合理"）

---

## 与 CLAUDE.md 的配合

建议在项目根的 `CLAUDE.md` 的 "Directory Layout" 补一行：

```markdown
| `openspec/roadmaps/` | 项目级 roadmap 文档包（长期真相源），按项目分子目录 |
```

以及在 Content Creation Context 或类似区块里提一下 4 件套的角色分工。这样未来的 AI 助手进入项目时，能一眼看到 roadmap 的存在。

---

## 参考模板

本 skill 的 `references/` 目录下有 5 个模板文件，是填充四件套的骨架：

- `references/requirements-template.md` — 需求综述模板（WHAT）
- `references/design-template.md` — 整体设计模板（HOW + WHY）
- `references/roadmap-template.md` — 路线图模板（WHEN + 每阶段验收）
- `references/task-log-template.md` — 任务日志模板（DID，含使用约定）
- `references/memo-template.md` — 讨论备忘模板（可选，考古用）
- `references/long-flow-skill-paradigm.md` — **长流程 skill 设计范式**（本 skill 的方法论源头。讨论讲清了为什么"讨论规模预估""契约可验证性 A/B/C 级"等决策的逻辑，也可作为其他长流程 skill 的体检清单）

起草每个文件时，读对应模板获取结构骨架，然后按项目实际内容填充。模板中用 `<占位符>` 和 `<!-- 注释 -->` 标注了需要填什么、为什么这样组织。

---

## 实战案例：博客 v2 重建（2026-04-19）

这个 skill 本身是从一次真实项目的经验里提炼出来的：

- **项目**：老刀AI码场博客 v2 重建（`openspec/roadmaps/blog-v2-rebuild/`）
- **起点**：用户对 v1 方案（双线 CDN + Railway Waline + 阿里云 OSS）不满
- **讨论阶段**：`/opsx:explore` 主导，发散出 4 个架构候选方向
- **决策**：方向 C（单机 VPS + Cloudflare 代理）+ Blowfish 主题 + GEO 一等公民
- **变更**：`/opsx:ff rebuild-blog-v2` 创建并产出 proposal/design/specs/tasks
- **范围调整**：本次变更只产出文档包，实际搭建推到 `implement-blog-phase-N` 系列变更
- **产出**：`openspec/roadmaps/blog-v2-rebuild/` 下 5 个文件
- **归档**：`/opsx:archive rebuild-blog-v2`，3 个 capability 进入 `openspec/specs/`

这个实例可以作为"标准形态"的参考。未来执行本 skill 时，可以对照这个实例检验流程是否走完整。
