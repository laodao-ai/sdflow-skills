# 外部 skill 展开 · `setup-matt-pocock-skills`

> 属 [Matt Pocock 套件调研](./matt-pocock-workflow.md)（§2.6）的深潜展开。
> **调研基线**：本机 `~/.claude/skills/setup-matt-pocock-skills/`（SKILL.md 127 行 + 5 个 seed 模板，2026-07-10）；
> 消费仓实例 = 本仓 `openspec/matt/*.md`（setup 已跑过，tracker 从默认 `docs/agents/` 改道 `openspec/matt/`）。
>
> **一句话**：套件的**第 0 步一次性铺设器**——把「工单在哪、triage 标签叫什么、域文档怎么摆」三件每仓各异的事，
> 面谈定案后写成三份**按仓翻译文档**，供其余 skills 运行时查阅。skill 与后端就此解耦。

---

## 1. 位置与契约

| 维度 | 内容 |
|---|---|
| 谁调它 | 人工一次性触发（`disable-model-invocation: true`，SKILL.md:4）；其余 engineering skills 首次使用前跑一遍 |
| 进（输入） | 仓库现状探测（`git remote`、CLAUDE.md/AGENTS.md、CONTEXT.md、`docs/adr/`、`docs/agents/` 既往产出、`.scratch/`）+ 用户三项决策 |
| 出（产物） | `docs/agents/{issue-tracker,triage-labels,domain}.md` 三份约定文档 + CLAUDE.md/AGENTS.md 的 `## Agent skills` 托管块 |
| 本性 | **prompt 驱动的面谈，不是确定性脚本**（SKILL.md:15「Explore, present what you found, confirm with the user, then write」） |
| 重跑语义 | 仅在换 tracker / 推倒重来时重跑（SKILL.md:127）；日常调整直接手改三份文档 |

---

## 2. 五步流程解剖

```
① Explore 探仓 ──▶ ② 三决策逐个面谈 ──▶ ③ 草稿确认可编辑 ──▶ ④ 写盘 ──▶ ⑤ 告知消费方
   （读现状不假设）    （每项先 ELI 解释）     （write 前给人改）
```

| 决策 | 选项 | 默认推导 | 追问 |
|---|---|---|---|
| **A · Issue tracker** | GitHub / GitLab / Local markdown / Other（Jira 等自由描述） | 探测驱动：`git remote` 指向谁提谁（SKILL.md:40） | 仅 GitHub/GitLab 追问「外部 PR 是否算请求面」（:47-51），本地 tracker 无 PR 概念跳过 |
| **B · Triage 词表** | 5 个 canonical 角色逐个可映射本仓既有标签 | 角色名即字符串（:65） | — |
| **C · 域文档布局** | Single-context（根 CONTEXT.md + docs/adr/）/ Multi-context（CONTEXT-MAP.md 指路） | 多数仓 single（:73） | — |

交互协议的三个可借细节：**一次只问一个决策**（:32「present a section, get the user's answer, then move to the next. Don't dump all three at once」）；**每节先给零基础 explainer**（:34，假定用户不懂术语）；**写盘前草稿可编辑**（:83）。

写盘的文件选择规则（:87-95）：CLAUDE.md 存在则编辑它，否则 AGENTS.md，两者皆无**问人不代选**；绝不双开；`## Agent skills` 块已存在则**就地更新不追加重复**。块本体只放一行摘要 + 指针（:99-113）——锚要薄，细节在被指的文档里。

---

## 3. 核心机制：抽象操作层 + 按仓翻译文档

下游 skills 全文只说**抽象动作**——"publish to the issue tracker"、"fetch the relevant ticket"、Wayfinding 六操作（Map/Child/Blocking/Frontier/Claim/Resolve）——由 setup 产出的约定文档在运行时把动作翻译成本仓的具体命令。同一操作在两个 seed 模板里的翻译对照：

| 抽象操作 | GitHub 后端（issue-tracker-github.md） | Local markdown 后端（issue-tracker-local.md） |
|---|---|---|
| Map | 单 issue 打 `wayfinder:map` 标签（:40） | **文件名即标签**：`<effort>/map.md`（:25） |
| Child ticket | GitHub sub-issue（`gh api` sub-issues endpoint，:41） | `<effort>/issues/<NN>-<slug>.md`，`Type:` 行装票型（:26） |
| Blocking | **原生 issue dependencies**（UI 可见，:42） | 正文 `Blocked by: NN, NN` 行（:27） |
| Frontier | `gh issue list` + blocked_by 过滤 + 无 assignee（:43） | 扫 `issues/` 目录，未阻塞未认领按编号优先（:28） |
| Claim | `gh issue edit --add-assignee @me`（:44） | 写 `Status: claimed`（:29） |
| Resolve | comment + close + 回写 map（:45） | `## Answer` + `Status: resolved` + 回写 map（:30） |

三个配套设计：

- **每后端内置降级链**：sub-issues 未启用 → map 正文 task list + 子票顶部 `Part of #<map>` 行（github.md:41）；原生依赖不可用 → `Blocked by: #<n>` 文本行（:42）；GitLab blocking 是付费功能 → 同款文本行降级。**给不变量的例外场景也给结构化协议**，不留「没有就算了」。
- **协议名与实现名分离**：triage 状态机永远以 5 个 canonical 角色运转，仓库只改映射表右列——skill 逻辑零改动适配任意标签体系。
- **逃生舱也是契约**：Other tracker 让用户一段话描述、记为散文照读（SKILL.md:45,123）——可插拔后端的兜底不是报错而是降为 prose。

三层加载全景（套件通用，setup 是第三层的生产者）：SKILL.md 常驻 → 同目录 seed 模板按需读 → **运行时才解析的消费仓约定文档**，统一句式指过去（"should have been provided to you — run /setup-matt-pocock-skills if not"）。

---

## 4. 本仓实例与已验证的注入点性质

本仓 setup 产物改道 `openspec/matt/{issue-tracker,triage-labels,domain}.md`（默认是 `docs/agents/`），CLAUDE.md 托管块指路。2026-07-10 探索 roadmap 重构时对注入点做过亲验：

- **注入点唯一**：wayfinder 自身零路径硬编码，落盘位置完全委托 tracker doc 的 Wayfinding 小节（wayfinder/SKILL.md:25「Consult the tracker doc's "Wayfinding operations" section」）；本仓该小节在 `openspec/matt/issue-tracker.md:22-31`。**改这一个文件即可重定向 map/tickets 落盘位置**（如 roadmap 类 effort 分流到 `openspec/roadmaps/{name}/footage/`）。
- **重定向不破坏机制**：票号 NN 作用域本就 per-effort（issue-tracker.md:10,27）、frontier 本就只扫本 effort 的 `issues/`（:29）、map 标签在本地 tracker 是「文件名即 map.md」——三者都不因换目录而失效。
- **triage 天然免扫 wayfinder 票**：triage 只按「Skill 操作规则」小节（:14-20）圈定的 `openspec/matt/<feature>/` 工作，wayfinder 票的 `Status:` 词表（claimed/resolved）与五个 triage 标签是两套词——目录分流反而消除了「Unlabeled — never triaged」桶的噪音。

---

## 5. 已知脆弱点（三条，均有实证）

| # | 脆弱点 | 证据 | 教训 |
|---|---|---|---|
| 1 | **skill 绕锚硬编码约定文档路径**：套件自家 code-review 写死 `docs/agents/issue-tracker.md`、PRD 搜索只看 `docs/`、`specs/`、`.scratch/`；qa 写死 `gh issue create` | code-review/SKILL.md:13,29,31；qa/SKILL.md:47-49；本仓实例在 `openspec/matt/` → 这两个 skill 打折扣 | 约定文档模式的阿喀琉斯之踵：**锚必须唯一（CLAUDE.md 块），skill 一律经锚解析，禁止写死约定文档位置** |
| 2 | **重跑覆盖定制**：Explore 步只查 `docs/agents/` 是否有既往产出（SKILL.md:27），不认识改道后的 `openspec/matt/`；重跑时若用户没细看草稿，定制会被 seed 模板覆盖回默认 | SKILL.md:27 vs 本仓改道事实 | 人在环确认是唯一兜底、非结构性保证；仓内定制应在 CLAUDE.md 锚块里**多写一句**当第二锚 |
| 3 | **小节名跨语言字面不匹配**：wayfinder 按英文 "Wayfinding operations" 找小节，本仓标题是中文「Wayfinding 约定」 | wayfinder/SKILL.md:25 vs openspec/matt/issue-tracker.md:22 | 模型大概率能对上，但鲁棒做法是标题带双语别名 |
| 4 | **`domain-modeling` 硬编码根 `docs/adr/`+`CONTEXT.md`**（`grill-with-docs` 内包）：不读本 skill 产出的 `openspec/matt/domain.md`，靠本 session CLAUDE.md `## Agent skills` 块覆盖赢冲突 | domain-modeling/SKILL.md「File structure」段 vs 本仓 openspec/ 布局；generation-process §六 已预警「否则另起一套 docs/adr/」 | 同 #1 阿喀琉斯之踵的又一实例，且更微妙：**本 skill 的 Section-C 域文档配置正为对齐它而设，但 domain-modeling 未 domain.md-aware → 对齐只落一半**（config 层写了、消费方不读）。硬化 = 让它 domain.md-path-aware（todolist T134）；未修前消费方（grill prompt / `workflow.md:83` 模版）手塞 `ADR→openspec/adr/` 重定向作 belt-and-suspenders。详见 [grill-with-docs.md](./grill-with-docs.md) §7.4 |

---

## 6. 对 sdflow 的可借鉴

sdflow 已有此模式四层里的三层，逐层对照：

| 层 | matt 做法 | sdflow 现状 | 可借的差量 |
|---|---|---|---|
| 引导式铺设 | Explore → 逐项面谈（带 explainer）→ 草稿确认 → 写盘 | ✅ sdflow-init（偏机械，少面谈） | 「一次一个决策 + 零基础 explainer」的交互协议 |
| CLAUDE.md 锚块 | `## Agent skills` 一行摘要+指针，就地更新 | ✅ sdflow-init 托管区块，机制相同 | — |
| 后端种子模板 | 同一约定的 GitHub/GitLab/local 三变体 | ⚠️ assets/ 有模板，无「多后端变体」概念 | 若 recorder 未来要支持 GitHub Issues 后端，此为现成范式 |
| **按仓翻译文档** | skills 说抽象动作，运行时查 tracker doc 翻译 | ❌ 产物路径硬编码在 SKILL.md 与脚本 | **本层是精髓，但要收窄地借**（见下） |

收窄的边界——**借「注入点」，不借「自由配置」**：

- matt 的可配置与 sdflow 的硬固定都是单一源设计，差别在单一源放哪：matt 放每仓翻译文档（适合**仓库间差异正当**的约定，如 tracker 后端）；sdflow 放全局 SKILL.md（适合**统一本身即价值**的路径，如 `openspec/roadmaps/` 硬固定——那是博客 v2 迁移之痛换来的疤，不是欠账）。
- **机械层分治**：sdflow 的路径有一半由脚本消费（buglist.py / ship_gate.py / retro_report.py），散文约定文档模型读得懂、脚本读不了。脚本消费的路径 → `config.yaml`（机器载体，缺失=默认 vs 存在坏=fail-closed 要分治）；仅模型消费的约定 → 翻译文档可行。
- sdflow 其实已有本模式的**更强工程化实例**：`resolve-workflow.sh` 之于规则解析（脚本三步解析 + exit 2 显式降级），比 matt 的散文指针硬。可借鉴的是把这个思路推广到「布局约定」类，而 matt 集成缝（tracker 后端、footage 位置、triage 词表）直接用 matt 自己的注入点 `openspec/matt/*.md`——那本来就是它设计好的扩展面。

---

*配套：[matt-pocock-workflow.md](./matt-pocock-workflow.md)（套件全景 + 12 条可借鉴机制）；[grill-with-docs.md](./grill-with-docs.md)（Section-C 域文档配置的下游消费方 + 脆弱点 #4 展开）；本仓消费实例 `openspec/matt/issue-tracker.md`。*
