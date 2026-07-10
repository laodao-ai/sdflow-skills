---
name: sdflow-roadmap
description: |
  制作"分阶段 roadmap"的规划工作流。产出三件套（design / roadmap / task-log，可选 memo）直写到
  `openspec/roadmaps/{name}/` 作为项目长期真相源；长讨论按需转 wayfinder 铺图（footage/）。
  触发场景：开始新项目、面对大量需求需要梳理、准备大规模重构、想分阶段实施一个超出单次变更能完成的事。
  用户说"做一个 roadmap"、"帮我规划 xxx"、"分阶段实现 xxx"、"先想清楚再动手"、"有一堆事不知道从哪开始"、
  "重构计划"、"新项目怎么起步"、"这个项目太大了要拆"时必须使用本 skill。即使用户没明说"roadmap"三个字，
  只要项目规模超出单次 change 能完成，就主动建议使用本 skill——宁可 trigger 后发现不需要轻量退出，
  也不要漏掉让用户陷入"边做边改"的陷阱。Trigger with /sdflow-roadmap。
---

# Roadmap Planner

把一个**超过单次 change 能完成**的项目/重构/需求集合，转化成分阶段可执行的规划文档包。产出三件套（design / roadmap / task-log，+ 可选 memo）直接保存到 `openspec/roadmaps/{name}/`，作为项目长期真相源。

## 为什么需要这个 skill

SDD（Spec-Driven Development）的最小必要集是"先想透再动手"。OpenSpec 的 `/opsx:new` 很好地承载了**单次变更**的 spec→design→tasks→implement，但面对"项目级"规模（多阶段、多变更、跨月）时，单次变更太小——需要一个比变更更大的层级来统摄**长期规划**。

roadmap 就是这个层级：

| 层级 | 位置 | 读者 | 生命周期 |
|---|---|---|---|
| **roadmap 文档包** | `openspec/roadmaps/{name}/` | 人类 + AI 助手 | **长期**（贯穿整个项目） |
| OpenSpec 变更 | `openspec/changes/{change-name}/` | 工具 + 归档查阅 | 短期（一次交付即归档） |

两者协作：roadmap 每个阶段子任务 → 对应一次**未来的**实施 OpenSpec 变更（不是本次产出 roadmap 走的变更——本次产出直写，不经变更壳，见规则 4）。

## 工作流概览

```
讨论层（分档路由，三分支）
├─ 起手长档信号 → wayfinder chart（落盘 footage/）
├─ 起手不明 → /opsx:explore 起步 → 事中触发升级 → wayfinder chart
└─ 产品/商业野心信号 → /office-hours 前置验证需求真实性 → 回到 explore 或 wayfinder
        │（讨论收敛）
        ▼
结晶：直写三件套 → openspec/roadmaps/{name}/
        │
        ▼
review：按野心分档 → /plan-eng-review（默认）或 /autoplan（野心信号）
        │
        ▼
收尾：checklist 五项软门 → 通过后软提示纳入版本控制
```

## 判定留痕总则

全流程有三个判定点：**①讨论分档**（explore/wayfinder/office-hours 三选一）**②review 分档**（eng 单审/autoplan 三连）**③收尾 checklist**（五项通过与否）。三处判定 MUST 在对话中显式陈述一行（不是内心判断），并在 task-log.md 留痕。**跳过类判定必须显著呈现**——单独一行、不埋进长消息——不允许静默略过。

## 必须遵守的硬性规则

这些是本 skill 的**不可妥协点**，违反其中任何一条都会让产出失去价值：

### 规则 1：保存位置硬性固定

- roadmap 三件套必须保存到 `openspec/roadmaps/{kebab-case-name}/`；长讨论的 footage 落 `openspec/roadmaps/{kebab-case-name}/footage/`
- `{name}` 用 kebab-case，语义化、短小（如 `rebuild-blog-v2`、`migrate-to-pg`、`unify-auth`）
- **禁止**放到 `doc/blog/`、`docs/`、`plans/` 等其他位置——这是历史教训（博客 v2 初版放 `doc/blog/` 后期被迫迁移）

### 规则 2：子任务 = 一次 OpenSpec 变更的粒度

- `roadmap.md` 里每个子任务应该**恰好是一次 `/opsx:new` 能完成的工作**
- 如果某个子任务感觉要拆成 5 个 change 才能做完 → 它本身应该是一个"子阶段"，而非一个任务
- **禁止**在 roadmap 阶段做"子任务的细化"——那是未来实施变更（`implement-{phase-name}`）的 scope

### 规则 3：三件套不引用考古层（两段式）

- 正式三件套（design / roadmap / task-log）之间可以互相引用
- 三件套 **MUST NOT** 引用 `footage/` 下任何内容（wayfinder map/票），**也 MUST NOT** 引用包根 `memo.md`——哪怕"详见 footage"或"详见 memo"也不行
- 理由：两者同为"决策形成过程"的考古证据，物理位置不同（footage 是 wayfinder 落盘、memo 是 skill 自家短档），但引用禁令相同。血统类比：footage/memo 是 footage（录像素材），design §决策 是 edit（成片）。如果正式文档引用考古层，会让读者以为考古层是权威源
- 考古层中有价值的结论 **SHALL** 精炼后写入三件套；考古层本身可独立存在作历史参考

### 规则 4：产出直写，不经变更壳

- 本次产出直接 Write 到 `openspec/roadmaps/{name}/`，**不经**任何变更壳承载（旧版本曾用一个专门的变更承载产出过程，现直写）——recorder 式直写，先例 = buglist/todolist/issues 三个 recorder 直写 `openspec/issues/`
- 结晶前先判定同名包是否已存在：不存在 → **create**；存在 → 显式向操作者区分 **continue**（增量更新，保留既有 task-log/Review 处置）与 **replan**（重规划，先在 task-log.md 落一条重规划记录再改写），**MUST NOT** 静默覆盖既有活文档
- 详细的存量兼容模式 / 逃生舱 / 生命周期判定见下节「产出模式」

### 规则 5：只做规划，不实施

- 本 skill 输出**文档**，不输出代码、不配置服务器、不创建仓库
- 实施动作留给"未来的 OpenSpec 变更"（`implement-blog-phase-1` 这类）
- 如果用户在 roadmap 产出过程中要求"顺手把 X 也做了"，提醒他：那属于阶段 1 实施变更的 scope
- 这条边界同样约束 wayfinder 铺图期间的 **Task** 类型票（wayfinder 唯一"做而非决定"的票型）：roadmap 讨论期的 Task 票 **MUST** 限定为**可行性验证**性质（如注册一个服务账号以判断其 API、探测现有系统现状），**MUST NOT** 用来产出正式实施成果——产出实施成果仍属未来阶段实施变更的 scope

---

## 产出模式：直写与包生命周期

### 存量四文件包兼容模式

本仓库和一切消费仓（skill 全局 symlink 分发）里存在含独立 `requirements.md` 的旧结构包——这是本 skill 早期版本的产出形态，**冻结为合法历史形态**：

- 续跑/更新这类存量包时 **MUST** 兼容其原有结构继续工作
- **MUST NOT** 报错、**MUST NOT** 强推迁移、**MUST NOT** 因存在独立 `requirements.md` 拒绝工作
- 至多输出一行提示：「存量四文件包，兼容模式」——**不告警刷屏**

### requirements.md 逃生舱

操作者显式要求为某个包保留独立 `requirements.md`（无论新建包还是续跑既有包）时 **SHALL** 遵从：仍按下文「结晶：产出三件套」里 design.md 头部「需求与目标态」章的内容框架（痛点 / 目标态判据 / 验收门槛 / Non-Goals）书写，只是把它物理拆成独立文件；design.md 头部 **须注明「非默认形态」**。这是**例外路径**，不是默认产出步骤——默认路径下本 skill 全程不生成独立 requirements.md。

### 包生命周期：create / continue / replan

结晶阶段（即将 Write 三件套之前）**SHALL** 先判定 `openspec/roadmaps/{name}/` 是否已存在：

| 判定 | 场景 | 动作 |
|---|---|---|
| **create** | 目录不存在 | 直接创建三件套 |
| **continue** | 目录已存在，本次是增量推进 | 保留既有 task-log.md 的历史记录与「Review 处置」小节，只追加/更新受影响章节 |
| **replan** | 目录已存在，本次是推翻重规划 | **先**在 task-log.md 落一条重规划记录（原因 + 时间），**再**改写受影响文件 |

无论 continue 或 replan，**MUST NOT** 静默覆盖既有活文档——向操作者显式说明区分依据，让其确认走哪条。

---

## 启动检查：评估讨论充分度（gate-0）

roadmap 的质量 100% 取决于讨论是否充分。开工前**必须**先评估：

```
□ 目标用户 / 受众清楚吗？
□ 核心功能的"要做 vs 不做"已经划清了吗？
□ 关键技术路径有 2+ 候选方案对比过吗？
□ 阶段划分有过构思（不要求最终版）吗？
□ 已知的主要权衡 / 风险已识别吗？
```

### 5 项全通过 → 直接进入"结晶"

用户通常已经经过一轮充分讨论（可能是前一轮对话里的），此时 roadmap-planner 可以直接起草。**判定点①**：显式说明「gate-0 五项已过，直接结晶」这一行依据，并写入 task-log.md。

### 任一项未通过 → 先进讨论层（见下节三分支路由）

---

## 讨论层：三分支路由

判定点①的核心：讨论工具怎么选。**双判据**，**MUST NOT** 依赖事前轮数预估——「聊多少轮该升级」不可观测，判据只认信号，不认计数。

### 分支 A（默认）：`/opsx:explore`

起手信号不明确时的默认起点：与用户对话式地吃透需求/方案/阶段，决策自然沉淀到 design.md，过渡无缝。

### 分支 B：wayfinder chart（长档）

**双判据的两个触发来源**：

- **起手显性信号**：请求自带长档特征——多阶段 roadmap、明示跨天推进、议题横跨多个子系统 → **直接**起手 wayfinder chart，不经 explore
- **事中触发**：explore 起步后，讨论**实际**跨 session/跨天、或经历上下文压缩/重置仍未收敛 → 升级切 wayfinder chart。触发判定承认**双来源**：人类口述（"这事聊了好几天了"）或盘面信号（memo 已存在且内容显示未收敛）——**MUST NOT** 假装新 session 能凭空判定历史轮次

**压缩前抢救**：explore 起步的讨论若检测到上下文压缩将要/刚刚发生、而 map 尚未建立，**SHALL** 先把当前推理要点 flush 进 memo.md（此场景下 memo **转为必需**，不再是可选），再判定是否升级 wayfinder——避免"压缩后才触发升级、能抢救的已是有损摘要"。

**无雾自降级**：wayfinder chart 第 2 步（广度 grill）**SHALL 先以未持久化预检判雾**——即先在对话里判断有没有雾，判定**有雾**才落盘建 map/票；若已经建了文件才发现无雾，**清理已建文件并留一行痕迹**。判定无雾时不建 map，退回 explore 单 session 讨论后直接结晶；广度 grill 期间已经产生的讨论要点 **SHALL** 转录进后续 explore 讨论或 memo，**MUST NOT** 因判定无雾而清零。

**宿主中立探测**：起手长档信号或事中触发命中后，先按**当前运行宿主**（Claude Code 或 Codex）探测 wayfinder 是否装载（如 `ls ~/.claude/skills/wayfinder` 或 `ls ~/.codex/skills/wayfinder`，取当前宿主对应路径）——**MUST NOT** 以 Claude 路径存在代理"全局可用"（Codex 宿主目前接地实测未装 wayfinder，这条降级路径会常驻）。不可用时显式提示并降级 explore+memo（长档策略回旧制），流程不阻塞。

**tracker doc preflight**：宿主探测通过后，**SHALL** 校验消费仓 `openspec/matt/issue-tracker.md` 是否存在且含 Wayfinding 小节。缺失时 **fail-closed 不进 wayfinder**：给出确定的初始化指引（提示运行 matt 套件的初始化 skill 铺设 tracker doc），并降级 explore+memo，不阻塞流程。

**wayfinder 票内的 domain-modeling 语境声明**：wayfinder 票内调用 grilling/domain-modeling（写术语/ADR）时，调用语 **SHALL** 声明「roadmap 探索期，决策未定稿」——避免把讨论期的临时判断当定稿写进 `openspec/CONTEXT.md`/`openspec/adr/`（收尾 checklist ⑤ 项会核对这条留下的增量，见下文）。

### 分支 C：`/office-hours` 前置验证（第三分支）

**触发信号**（产品/商业野心信号词表——review 分档共用同一张表，见下文「review：按野心分档」）：外部用户、变现、获客、"用户画像未定"、"要不要做这个产品"。典型例子：面向外部用户的 SaaS、社区、付费工具。

**不触发**的场景（绝大多数）：技术重构、内部工具、基础设施、博客/文档工程、个人项目。

office-hours 的 6 问（Demand/Status-quo/Wedge/Observation/Future-fit）把需求真实性逼出来后，**回到分支 A 或 B** 继续技术路径讨论——office-hours 本身不产出三件套内容，只是前置校验。

### 深度设计不在本流程内

单个 feature 的深度架构设计（`/superpowers:brainstorming`）**不在** roadmap-planner 主流程里，而是**未来实施变更内部**用：阶段 X 实施时某个子任务需要对比 2-3 个架构方案并产出正式 design doc。roadmap-planner 里只提及此情况，不调用。

### 路由对照表（自检基准，≥4 例）

| 用户开场白示例 | 判定信号 | 期望路由 |
|---|---|---|
| "帮我做一个未来半年的博客重建 roadmap，从选主题到迁移" | 起手显性信号：多阶段+跨月 | 直入 wayfinder chart |
| "这个项目要不要做，先看看有没有人真的需要" | 产品/商业野心信号：需求真实性未定 | `/office-hours` 前置验证 → 回 explore/wayfinder |
| "帮我理一下这几个 bug 先后修哪个" | 无多阶段/无跨天信号，规模小 | gate-0 大概率直接过或轻量 explore，不建 map |
| "我们聊聊要不要重构鉴权模块，还没想清楚" | 起手不明，无显式长档信号 | `/opsx:explore` 起步，视后续实际轮次/压缩情况事中触发 |
| "这个 idea 已经聊了三天了，一直定不下来，帮我整理" | 事中触发信号（口述"聊了三天"） | 尚未建 map → 立即 wayfinder chart；若正逼近压缩 → 先 flush memo 再判定 |

---

## footage：wayfinder 落盘与引用边界

讨论收敛后（走了 wayfinder 长档路径）留下的 map 与票是**考古层**，产出规则如下：

### 落盘位置

- map：`openspec/roadmaps/{name}/footage/map.md`
- 票：`openspec/roadmaps/{name}/footage/issues/<NN>-<slug>.md`（本地 Markdown tracker 约定：`Type:` 记 `research`/`prototype`/`grilling`/`task`，`Status:` 记 `claimed`/`resolved`）

三件套引用边界见规则 3（两段式，不重复）。

### 命名权先定

kebab-case `{name}` **SHALL** 由 sdflow-roadmap 在调用 wayfinder chart **之前**确定，并以**固定字面量**（含完整 map 路径）写入调用语——wayfinder 自己的"Name the destination"步只精化 destination 的表述，**MUST NOT** 另起 slug。调用语模板（`{name}` 与路径必须替换为具体字面量，禁止用"这个项目"等指代残留）：

```
为 {kebab-case-name} 铺一张 wayfinder map，落盘于
openspec/roadmaps/{kebab-case-name}/footage/map.md
（票落 openspec/roadmaps/{kebab-case-name}/footage/issues/）。
destination = 三件套定稿（design.md + roadmap.md + task-log.md）。
```

### map 持久字段

map.md 头部 **SHALL** 持久化两个字段，后续任何 session 的续跑/新建票 **SHALL 只从这两个字段派生路径**，**MUST NOT** 重新做语义判别（防止双根分裂）：

```
Tracker root: openspec/roadmaps/{name}/footage/
Effort kind: roadmap
```

### 顶部路标行

map.md 顶部（Destination 之前）**SHALL** 留一行去向说明，例如：

```
> 本 map 及其票为讨论考古层（footage）；三件套（design.md / roadmap.md / task-log.md）不引用本目录任何内容。
```

### map 再入约定（钉死一种）

同一包二次 chart（如远期阶段补细讨论）**MUST NOT** 覆写既有 map。本 skill 钉死为**单 map 分批续用**：同一个 `map.md` 在其生命周期内允许多批次追加票，无需每次讨论都新开 map；**满 30 票时**归档当前 map 为 `footage/map-N.md`（`N` 从 1 起算）并新起一份 `map.md`，新 map 头部记一行「承接自 map-(N-1).md」，票号**不复用**（从旧 map 最大编号 +1 续起）。

---

## 结晶：产出三件套

每个文件使用 `references/` 下对应的模板骨架。读对应模板，按项目实际内容填充。

| 文件 | 内容核心 | 模板 |
|---|---|---|
| `design.md` | 需求与目标态（头部伸缩章：痛点/目标态判据/验收门槛/Non-Goals；产品型追加受众/功能取舍；混合/探索型走具名占位兜底，不硬造判据）+ HOW/WHY（怎么做、为什么这么做） | `references/design-template.md` |
| `roadmap.md` | WHEN：分阶段计划 + 每阶段验收（近细远雾，见下节） | `references/roadmap-template.md` |
| `task-log.md` | DID：执行过程记录（初始占位）+ Review 处置小节 | `references/task-log-template.md` |
| `memo.md`（可选） | 短档讨论备忘，考古用；长档由 footage 承载 | `references/memo-template.md` |

design.md 首部「需求与目标态」章 **不占用**正文既有 `## N.` 数字编号序列（无编号章名）——规避历史「design §N」位置引用随内容增删级联位移。

> 浏览 roadmap 文档包：用项目根 `openspec/serve.sh` 起 HTTP 服务、开 `openspec/review.html`（根查看器起于全树，经内置 INDEX/树浏览到任意 `roadmaps/{name}/`）——不再每目录生成 `review.html` stub（放弃 scoped 深链，可接受降级）。

### 三件套之间的引用关系

```
design.md         ◀── roadmap.md 引用（阶段分解基于架构/头部章判据）

roadmap.md        ◀── task-log.md 引用（日志记录 roadmap 的任务完成）

footage/、memo.md  ✗  三件套任何一份都不引用（见规则 3）
```

---

## review：按野心分档

三件套写完就走收尾，等于"spec 没评审就交付"——能用但埋雷。**判定点②**：按项目野心分档触发 review，并显式陈述一行判定依据。

### 分档判据（与 office-hours 共用同一张信号词表）

- **默认**：单跑 `/plan-eng-review`——技术重构、内部工具类项目，无产品/商业野心信号
- **野心信号才三连**：`/autoplan`——出现外部用户、变现、获客类信号（同讨论层分支 C 的触发词表）

### 关键：把三件套作为"整体 plan"告诉 review skill（存活验收）

review skill 原本设计给**单个 plan 文件**。roadmap 是**多文件三件套**。触发时必须显式说明：

> 请把 `openspec/roadmaps/{name}/` 下的 `design.md` + `roadmap.md` + `task-log.md` 视为一个整体 plan 来 review。`roadmap.md` 是主入口，它引用 design.md 作为上下文。`task-log.md` 是执行记录，重点看"Review 处置"小节是否完整。

不这样说，review skill 会只盯其中一份文件，遗漏跨文件的一致性问题。

### 跳过 review（仅限人类操作者显式授权）

跳过 review **仅限人类操作者显式授权**——agent 自身 **MUST NOT** 代决跳过。跳过后：

- 包状态记 `review-waived`，不与"已审"混同
- task-log.md 留一条「未做 review，风险自担」的痕迹（**判定点②的跳过类判定，须显著呈现，不埋长消息**）

### 显式覆盖默认分档

操作者显式要求覆盖默认分档（强制三连审 / 强制单审）时 **SHALL** 遵从，并在 task-log.md 记录偏离理由。

### review 依赖不可用时不静默

`/plan-eng-review` / `/autoplan` 未安装、调用失败或返回空时：**SHALL** 显式提示，task-log.md 留「未审待恢复」痕迹 + 给出修复/重试步骤，**MUST NOT** 把包当作已完成收尾（这不是"跳过"，是"故障"，两者状态不可混同）。

### review 结果如何处理

review 产出的每条 issue **SHALL** 在 task-log.md「## Review 处置」小节标注下列状态之一：

- ✅ **采纳**：写明已在哪个文件哪一节改动
- ❌ **拒绝**：写明拒绝理由（不得空白"不采纳"，理由必须可供后人复核）
- ⏭ **延后**：写明延后到哪个阶段/哪个后续变更处理

「Review 处置」小节**不存在未处置条目**是收尾 checklist ①的硬性前提。

---

## roadmap.md 近细远雾

roadmap.md **只对近期 1-2 个阶段**写满五节（前置条件/目标/子任务/验收标准/交付物）；**近期取 1 还是 2 个 SHALL 写明选择理由**（如并行依赖、交付节奏）。

更远的阶段 **SHALL 只写阶段目标一句 + 雾区备注**——雾区备注要写明「缺什么信息才能细化」，而不是空泛的"待细化"。**MUST NOT** 预写子任务分解与验收细节。

### 长周期依赖例外

远期阶段若涉及长交付周期前置（采购/合规/外部契约类），**允许且应当**提前写「前置条件」一节，其余四节仍留雾。

### 补细时机与重判分档

远期阶段成为下一个待实施阶段时（前序阶段全部交付），**SHALL** 补全五节（可经一次短讨论）。补细内容若命中产品/商业野心信号、或改变范围/不可逆承诺/验收判据，**SHALL** 重新过一遍 review 分档判定（非强制重跑三连审），判定结果记入 task-log.md。

### 前序放弃视为已处置

前序阶段某子任务被**终局判定放弃**（非未完成、非延后）时，记入 task-log.md 后**视为已处置**，计入"前序交付"判定，不永久阻塞 frontier 推进。

---

## 收尾 checklist：五项软门

收尾前 **SHALL** 执行以下五项确认，**判定点③**——显式陈述通过/不通过并写入 task-log.md；跳过类判定须显著呈现。任一项不通过 **SHALL** 提示补齐后再收尾，**MUST NOT** 静默跳过。

**① Review 处置无遗留**：task-log.md「Review 处置」小节不存在未处置状态的条目。

**② 三件套相互引用完整（最小引用图判定）**：roadmap.md 每个已细化阶段至少回指 design.md 对应决策一次；task-log.md 每条完成记录关联 roadmap.md 阶段；design 头部章与决策段无同值重复（只准互相引用，不准复述）。**不通过时报出具体文件与行号**，**MUST NOT** 笼统宣称「完整/不完整」。

**③ 考古层未被引用**：footage/（如走了长档）与包根 memo.md（如有）均未被三件套引用。

**④ wayfinder 闭环**（如走了长档路径）：frontier 为空，或每张未 resolve 的票已显式放弃并留痕，map 标注 closed——**MUST NOT** 带着 open/claimed 票宣告定稿。

**⑤ 共享真相源核对**：本次讨论期间 `openspec/CONTEXT.md` / `openspec/adr/` 的新增与改动逐条对照三件套终稿——被终稿推翻的判据标 `superseded`（或 revert）并在 task-log.md 记一行，**MUST NOT** 让讨论期临时判断以定稿姿态留存在全局共享文件里。

五项通过后，**SHALL** 软提示将包纳入版本控制（`git add`/`git commit`，软提示而非强制，与 recorder 先例对齐）。

---

## 命名规范

- **kebab-case**，语义化
- 动词开头优先（表达"要做什么"）
- 长度建议 ≤ 30 字符
- 例：`rebuild-blog-v2`、`migrate-to-postgres`、`unify-auth-system`、`add-analytics-pipeline`
- 这个名字同时是 `openspec/roadmaps/{name}/` 目录名、（如走长档）footage map 头部 `Tracker root:` 字段的锚，以及未来实施变更命名的前缀（`implement-{name}-phase-N`）——一名到底，避免未来追溯时多个名字对应同一件事

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

**表现**：用户说一句"帮我做个 roadmap 吧"，skill 立刻开始写 design.md。

**后果**：写出的 roadmap 空洞、假设错误、阶段划分混乱，后续实施时不断推翻重来。

**正确**：过 gate-0 五条 checklist，不足就先进讨论层三分支路由。

### 陷阱 2：子任务粒度过细

**表现**：roadmap.md 里的子任务写成 "配置 nginx HTTPS / 申请 Let's Encrypt 证书 / 配置 SSL 参数" 三条分列。

**后果**：这三条应该是一次"VPS 基础加固" change 内部的 checklist 项，而不是 roadmap 阶段的子任务。

**正确**：roadmap 子任务 = "VPS 基础加固"（一整体），一次变更能完成；具体 checklist 在该变更的 tasks.md 里。

### 陷阱 3：考古层被当成正式文档引用

**表现**：design.md 写"详见 `footage/map.md`"或"详见 `memo.md` §2.4"。

**后果**：footage/memo 是草稿，未经打磨，长期维护成本高；读者看到引用会以为它们是权威源。

**正确**：footage/memo 里有价值的内容**精炼或复制**进三件套；三件套不引用考古层（规则 3）。

### 陷阱 4：roadmap 文档包保存到错误位置

**表现**：保存到 `doc/` 或 `plans/`。

**后果**：与 OpenSpec 工作流脱钩，未来实施变更找不到引用路径；需要迁移时要改大量路径引用（博客 v2 的真实教训）。

**正确**：固定 `openspec/roadmaps/{name}/`，没有例外。

### 陷阱 5：同名包被静默覆盖

**表现**：结晶时发现 `openspec/roadmaps/{name}/` 已存在，没有向操作者确认就直接覆写。

**后果**：既有 task-log.md 的历史记录、已处置的 Review 条目、既往决策全部丢失，且无人察觉——直到需要追溯时才发现。

**正确**：先判定 create/continue/replan（见「产出模式」一节），continue 保留历史只增量更新，replan 先在 task-log.md 落重规划记录再改写。

### 陷阱 6：收尾 checklist 当成 review（把机械检查当内容质量）

**表现**：觉得"收尾 checklist 五项都过了就等于内容审过了"，跳过 review 分档。

**后果**：收尾 checklist 检查的是**结构性条件**（有没有处置记录、引用是否完整、雾区是否补齐留痕）——**不判断内容对不对**。roadmap 里的错误架构决策、不合理阶段划分、遗漏的需求，都能通过 checklist 但在 review 里暴露。

**正确**：两者不重叠、都不能省——review（`/plan-eng-review` 或 `/autoplan`）= **内容质量评审**（三件套产出后、收尾前审视"承诺的东西合不合理"）；收尾 checklist = **结构性软门**（review 处置完了没有、引用断没断链、雾区/闭环留痕全不全）。

### 陷阱 7：wayfinder 降级路径静默发生

**表现**：宿主未装 wayfinder，或消费仓 tracker doc 缺失 Wayfinding 小节，skill 没提示就直接退回 explore+memo，用户以为走了长档路径。

**后果**：用户以为讨论过程有 footage 持久化保护，实际压缩/中断后推理过程照样丢失。

**正确**：宿主中立探测 + tracker doc preflight 任一项不通过，**必须显式告知**（"当前宿主未装 wayfinder，降级为 explore+memo" / "tracker doc 缺失 Wayfinding 小节，给出初始化指引"），不静默切换。

---

## 与 CLAUDE.md 的配合

建议在项目根的 `CLAUDE.md` 的 "Directory Layout" 补一行：

```markdown
| `openspec/roadmaps/` | 项目级 roadmap 文档包（长期真相源），按项目分子目录；长讨论 footage 落 `roadmaps/{name}/footage/` |
```

以及在 Content Creation Context 或类似区块里提一下三件套的角色分工。这样未来的 AI 助手进入项目时，能一眼看到 roadmap 的存在。

---

## 参考模板

本 skill 的 `references/` 目录下有 5 个模板文件，是填充三件套的骨架：

- `references/design-template.md` — 整体设计模板（含「需求与目标态」头部伸缩章 + HOW/WHY）
- `references/roadmap-template.md` — 路线图模板（WHEN + 近细远雾分层 + 每阶段验收）
- `references/task-log-template.md` — 任务日志模板（DID，含使用约定）
- `references/memo-template.md` — 短档讨论备忘模板（可选，考古用；长档由 footage 取代）
- `references/long-flow-skill-paradigm.md` — **长流程 skill 设计范式**（本 skill 的方法论源头，也可作为其他长流程 skill 的体检清单）

起草每个文件时，读对应模板获取结构骨架，然后按项目实际内容填充。模板中用 `<占位符>` 和 `<!-- 注释 -->` 标注了需要填什么、为什么这样组织。

---

## 实战案例：博客 v2 重建（2026-04-19）

这个 skill 本身是从一次真实项目的经验里提炼出来的：

- **项目**：老刀AI码场博客 v2 重建（`openspec/roadmaps/blog-v2-rebuild/`）
- **起点**：用户对 v1 方案（双线 CDN + Railway Waline + 阿里云 OSS）不满
- **讨论阶段**：`/opsx:explore` 主导，发散出 4 个架构候选方向
- **决策**：方向 C（单机 VPS + Cloudflare 代理）+ Blowfish 主题 + GEO 一等公民
- **产出**：`openspec/roadmaps/blog-v2-rebuild/` 下的文档包（彼时结构含独立的需求文件，属该版本 skill 的历史形态；现行流程见上文「结晶：产出三件套」）
- **范围**：产出阶段只交付文档包，实际搭建推到 `implement-blog-phase-N` 系列变更

这个实例可以作为决策叙事的参考。未来执行本 skill 时，走的是当前文档描述的三件套直写流程，不复现该实例的历史产出机制。
