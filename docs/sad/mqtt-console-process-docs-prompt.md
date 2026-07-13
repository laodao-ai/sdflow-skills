# Prompt：过程轴文档归位（C 候选正式模板 · mqtt-console 已验证）

> 状态：**✅ 已接地验证，提升为交付候选 C 的正式 prompt 模板**（2026-07-13）。
> 首跑实例：mqtt-console（commit `be526d4`）——产出 `environments.md` 203 行 + `testing-strategy.md` 341 行，三个源文件真删（零双写），命令出处全中（Makefile 四 target 行号精确、零虚构），并反向重指 20 处引用。回执 → `06-process-axis-grounding-receipt.md`。
> **复用到新项目时唯一要改的**：STEP 0 的素材源清单、事实校验源清单、三个「硬骨头」（换成该项目自己的）。骨架与全局禁令**原样保留**。
> 用法：在目标仓开一个 session，把 §「PROMPT 正文」整段贴进去。
> 关键前提（决定骨架形态）：目标项目通常 **不缺这些文档，只是散落错位 + 多处双写**。故本 prompt 是**归位/蒸馏型**，不是生成型——见下方「为什么不能写成生成型」。

---

## 为什么不能写成「按模板生成」型（起草者必读）

天真写法（「读 05 模板 → 填 environments.md」）会让模型**重新写一份**，而现有素材原地不动，结果：

```
现状：testing 内容 2 份（docs/modules/testing.md · roadmaps/v2/testing-strategy.md）
天真 prompt 跑完：3 份（+ 新建的 testing-strategy.md）
             env 内容 2 份（docs/getting-started.md 原地 + 新建 environments.md）
```

**双写漂移正是 05 §3 全篇要防的东西**，用生成型 prompt 会亲手造出来。所以骨架必须是：**盘点 → 判归属 → 搬运（含删源/留指针）→ 补空 → 反向瘦身 → 自检**。「新写」只发生在真正没有素材的空槽里。

---

## PROMPT 正文（整段复制到 mqtt-console session）

````text
你的任务：把本仓（Sarvelo MQTT Console）**已经存在但散落错位**的「过程轴」文档归位成两份真相源，并瘦身其来源与入口。

这是**归位/蒸馏**任务，不是从零生成。绝大部分内容已经写好了，散在 5 个地方。你的活是搬运、切分、去重、补空——**不是重写一遍**。

═══════════════════════════════════════════
【方法论真相源：先读，不要跳过】
═══════════════════════════════════════════

读这三份（在另一个仓，用绝对路径）：

1. /Users/cheneyzhao/Documents/04-sdflow-skills/docs/sad/05-process-axis-document-system.md
   —— 过程轴文档体系方法论。重点：§2 文档集与槽、§3 文档间边界、§3.1 testing-strategy ↔ environments 的精确切线表（10 行归属表）、§4 SAD 投影 vs 项目自填。
2. /Users/cheneyzhao/Documents/04-sdflow-skills/docs/sad/environments-template-draft.md
   —— environments.md 的十六槽模板 + README/CLAUDE 引用范式（附 A/B）。
3. /Users/cheneyzhao/Documents/04-sdflow-skills/docs/sad/04-ecosystem-boundaries.md
   —— §2 SAD 边界四问（判「这段该不该留在 SAD / 该归哪」）、§4 相邻文档边界表、§5 真相源分工表。

核心判据只有一条，全程用它：**每格内容只有一个家；跨格一律引用，禁复述。**

═══════════════════════════════════════════
【目标态】
═══════════════════════════════════════════

产出 2 份新真相源，落 **`openspec/architecture/`（与 `sad.md` 同居）**——不落项目根、不落 `docs/`：
过程轴与空间轴（SAD）同属**设计真相源层**；`docs/` 是 as-built 解释层（系统「是什么」），「怎么搭/怎么跑」不属于它。

- `openspec/architecture/environments.md`     —— 过程·操作轴：dev 搭建 / test 执行 / deploy 发布（十六槽，照模板）
- `openspec/architecture/testing-strategy.md` —— 过程·方法轴：测什么、怎么分层、测试哲学、护栏、盲区

并瘦身 5 个来源/入口，使其**不再复述**上面两份的内容。

═══════════════════════════════════════════
【STEP 0 — 素材盘点（先读全，再动手）】
═══════════════════════════════════════════

读完以下全部文件，**逐节**（到 ## / ### 级）列一张盘点表，每节标注：内容性质（操作 / 方法 / 决策 / 架构 / 时间·阶段 / 入口索引）。

素材源：
- docs/getting-started.md            (198 行 — 其实就是 environments.md 的本体，只是没叫这名)
- docs/modules/testing.md            (308 行 — 测试体系 as-built：三条 lane / 逐文件门禁表 / harness+fixture / 前端 gate)
- openspec/roadmaps/mqtt-console-v2/testing-strategy.md  (217 行 — 测试路线：五泳道 / B13 决策 / 护栏 / **含时间轴内容**)
- README.md · CLAUDE.md · AGENTS.md  (入口类，现状可能已复述细节)
- docs/README.md                     (docs 索引，入口类)

事实校验源（**命令一律以这些为准，严禁凭印象臆造**）：
- Makefile        (注意：只有 integration / integration-docker / embedded 三个 target —— **没有** make dev/test/build)
- wails.json · package.json · hack/  (dev 与 gate 的真实入口)
- .github/workflows/   (**不存在** —— 这是事实，不是疏漏)

SAD 投影源（env/test 的一部分槽从这里投影，引用不复述）：
- openspec/architecture/sad.md  (§1 目标与质量属性[可测试性] · §2 约束[栈/平台] · §3 外边界 · §5 子系统 contract · §7 部署 · §8 横切)

═══════════════════════════════════════════
【STEP 1 — 归属判定（本任务的核心难点）】
═══════════════════════════════════════════

把 STEP 0 每一节判去一个目标格。用 05 §3.1 的切线表 + 04 §2 的 SAD 边界四问。目标格只有这六个：

  [A] environments.md §1/§2/§3   —— 操作：怎么搭、怎么跑、怎么发
  [B] testing-strategy.md         —— 方法：测什么、怎么分层、为什么这么分、护栏
  [C] 留在 roadmap                 —— 时间/阶段：M1a 前置重构、M1 golden 网、"目标态待某阶段做"
  [D] 留在 / 归还 SAD              —— 架构决策（为什么是这个结构）
  [E] 入口（README / CLAUDE / AGENTS）—— 只放最小命令 + 指针
  [F] 删除                         —— 与上述任一格重复的复述

⚠ 三个已知的硬骨头，必须显式处理并在报告里写明你的判定与理由：

  (1) roadmaps/v2/testing-strategy.md 的 §4.2「目标态（M1a 前置的 tag 重构）」和 §6「M1 golden 网（占位）」
      —— 这是**时间轴**内容，混在方法文档里。默认判 [C] 留在 roadmap，**不要**搬进 testing-strategy.md。
      （方法论侧记：05 §3 的边界图漏画了 testing-strategy ↔ roadmap 这条链，这是接地暴露的。）

  (2) docs/modules/testing.md §4「逐文件门禁表」（哪个测试文件跑在哪条 lane）
      —— 既不是「为什么这么分层」(方法)，也不是「怎么跑」(命令)，而是**分层的实例化清单**。
      05 §3.1 的切线表十行**没有这一行**。你要自己判 [A] 还是 [B]，并在报告里给出判据
      （提示：问「它随工具链变还是随测试哲学变？」「reviewer 读还是 contributor 读？」），
      **明确标注这是切线表的新增行提案**。

  (3) docs/modules/testing.md 的位置本身
      —— docs/modules/* 是 L2 子系统文档（mqtt-engine / pack / console / frontend …），
      但「测试」不是子系统，它是过程轴。搬空后此文件应删除或降为一行指针。

输出：一张完整的「源节 → 目标格」搬运表。**先把这张表给我看，等我确认后再写文件。**

═══════════════════════════════════════════
【STEP 2 — 写 environments.md】
═══════════════════════════════════════════

照 environments-template-draft.md 的十六槽。纪律：

- **命令必须是真的**：以 Makefile / wails.json / package.json / hack/ 为准。项目**没有** make dev/test/build，
  就照实写 `wails dev` / `go test ./...` / `make integration` 等真实命令。**不得为了对齐模板范式而虚构 Makefile target。**
  （如果你认为该项目应当把命令收拢进 Makefile —— 那是一条 todo，写进报告，**不是**在文档里假装它已存在。）
- **CI 槽 = 显式 N/A**：本仓无 .github/workflows。写 `N/A — 当前无 CI，本地门禁经 hack/ 脚本与 make integration`（照实描述），
  **不要留空、不要假装有 CI**。这是「填或显式 N/A」纪律。
- **三条红线**（模板已列）：只放操作；测试方法归 testing-strategy.md（本文 §2 只放测试环境依赖 + 执行命令）；
  部署的架构决策归 SAD §7（本文 §3 只放搭建/配置项/发布/回滚操作），一律引用不复述。
- deploy 槽按桌面 app 实填（跨平台 binary / wails build / headless build tag）；无服务端的部分显式 N/A。

═══════════════════════════════════════════
【STEP 3 — 写 testing-strategy.md】
═══════════════════════════════════════════

内容 = 两份现有 testing 文档的**方法层交集与合并**，去掉命令、去掉阶段。应含：

- 分层：三条 Go lane（hermetic / embedded / realbroker）+ 前端（vitest / playwright）+ 绑定门禁，**各测什么、为什么这么分**
- **分层隔离机理**：泳道之间为什么不互相连带（build tag 解耦 = 故障隔离，非命名洁癖）
- contract = 集成测试点（哪些边界必被穿过 —— 对 SAD §5 的 contract 引用不复述）
- mock 边界选在哪（svcFakeEngine 的边界是策略决策）
- fixture **策略**（数据代表什么、golden/factory 取向；具体文件路径与生成命令归 env §2）
- **测试编写 idiom**：怎么写出确定性断言（barrier / retry-until-settled / escalating-burst 之类对抗异步的套路）
- 护栏 / 可信回归网（含 B13「不修，靠回归网放行」这条决策及其四条护栏）
  —— ⚠ 只放**决策与护栏语义**；护栏的**实现**（Makefile 的 `|| retry once`）归 env §2.2
- **分层的实例化：逐文件门禁清单**（哪个测试文件跑哪条泳道 —— 见硬骨头 (2)）
- **已知盲区与测试债**（哪条不变量架构上守不住、哪些 flake 未根治）

**MUST NOT 含**：执行命令、CI 配置、fixture 文件路径与生成命令（→ env §2）；M1a/M1 阶段计划（→ roadmap）。

═══════════════════════════════════════════
【STEP 4 — 反向瘦身（不做这步就等于制造双写）】
═══════════════════════════════════════════

- docs/getting-started.md      → 内容已搬空。**删除**，或降为一行指针 `→ ../environments.md`。
                                  （§7 代码地图、§9 下一步读什么 不属过程轴：前者归 SAD/CONTEXT，后者归 README/docs 索引，按 STEP 1 判定处置。）
- docs/modules/testing.md      → 同上，删除或降为指针。
- roadmaps/v2/testing-strategy.md → **只保留时间轴内容**（M1a tag 重构、M1 golden 网），方法部分改为引用 ../../testing-strategy.md。
                                    若剩余内容太薄，合并回该 roadmap 的 roadmap.md 并删除此文件。
- README.md · CLAUDE.md · AGENTS.md → 照模板附 A/B：**只留最小起步命令 + 指针**，MUST NOT 复述 env/test 细节。
                                       现有的「开发命令」「技术栈」等节，凡与 environments.md 重复的一律删，换成指针。
- docs/README.md               → 更新索引指向两份新真相源。

═══════════════════════════════════════════
【STEP 5 — 自检（逐条给证据，不许空口说过）】
═══════════════════════════════════════════

- [ ] 无双写：任一句操作/方法内容只出现在一个文件里。给出你的去重检查方法。
- [ ] 命令为真：environments.md 里每条命令都能在 Makefile / wails.json / package.json / hack/ 找到出处（列出对照）。
- [ ] 指针不悬空：每个 `见 X` 的 X 都存在，锚点/章节号对得上。
- [ ] 无越界：environments.md 里没有「为什么是这个架构」；testing-strategy.md 里没有命令、没有 M 阶段。
- [ ] N/A 显式：CI 槽、deploy 的服务端相关槽等，都是显式 N/A + 理由，不是留空。

═══════════════════════════════════════════
【STEP 6 — 方法论回执（这是本次任务的另一半价值，别省）】
═══════════════════════════════════════════

跑完后单独输出一节「回执 → 05 方法论」，回答：

1. **§4「一半投影」这个比例，真是一半吗？** 数一下：environments.md + testing-strategy.md 的槽里，
   有多少能从 sad.md 投影（SAD 有源）、多少是纯项目自填（SAD 无源）。给出实际比例。
   —— 这个数字直接决定 05 §5「生成价值只有一半 ⇒ 不值得做独立 ops skill」这个论证站不站得住。
2. **§2 的槽对不对？** 哪些槽在本项目是空的/N/A？有没有本项目有内容但模板**没给槽**的（模板缺口）？
3. **§3.1 的切线表够不够？** 你在 STEP 1 (2) 判的「逐文件门禁表」应该新增为哪一行？还有别的空白格吗？
4. **本次工作里，哪些是机械的（可脚本化 / 可模板化），哪些非人判不可？**
   —— 这决定 05 §5 的 B（并入 sdflow-init 维护扫描）该守什么、C（模板+prompt）够不够用。
5. **搬运过程中最容易判错的边界是哪条？** 给一个你差点判错的具体例子。

═══════════════════════════════════════════
【全局禁令】
═══════════════════════════════════════════

- ✗ 不得重写已有内容 —— 能搬就搬，保留现有措辞与已沉淀的判断（B13 决策、四条护栏、三条 lane 命名等都是真金）。
- ✗ 不得臆造命令 / CI / Makefile target。
- ✗ 不得把架构决策（why）写进 environments.md —— 引用 SAD。
- ✗ 不得把 roadmap 的阶段计划写进 testing-strategy.md。
- ✗ 不得只新建不删源 —— 那是制造双写，本任务的头号失败模式。
- ✓ STEP 1 的搬运表**必须先给我确认**，再动笔写文件。
````

---

## 这个 prompt 的设计要点（给 05 方法论的反哺）

| 设计 | 为什么 |
|---|---|
| **归位型骨架**（盘点→判归属→搬→瘦身），而非填模板 | 素材已存在且已双写；生成型 prompt 的必然产物是三写。这一条应回写进 05 §5 的 C 候选描述——**「模板 + prompt」的 prompt 必须是归位型**，纯模板不足以防双写。 |
| STEP 1 结果**先给人确认**再落笔 | 归属判定是全任务唯一无确定性信号的部分（05 §3.1 已承认切线属语义边界）。人门放在这里，而不是放在末尾审文档。 |
| 三个「硬骨头」显式点名 | 都是勘察时真撞上的，模型不点名会顺手糊过去：时间轴混入方法文档 · 切线表空白格 · 测试文档寄生 L2 层。 |
| STEP 6 方法论回执 | 05 §6 说这次接地是为了**验证 B+C 倾向 + 槽对不对 + 投影比例真不真**。不设回执，跑完只有文档、没有判据，前置就白做了。 |
| 事实校验源清单（Makefile / wails.json / 无 CI） | 模板附 A/B 用 `make dev/test/build` 举例，本项目全不存在。不钉死这一条，模型会照模板范式虚构 target。 |

## 已知会被这次接地检验的三条 05 论断

1. **§4「SAD 只投影一半槽」** —— STEP 6.1 直接量出真实比例。若远低于一半，§5「生成价值有限 ⇒ D 不立」的论证反而**更强**；若远高于一半，D（独立 ops skill）要重新过一遍。
2. **§3.1 切线表十行** —— 「逐文件门禁表」已确认是空白格（洞 2），大概率还有别的。
3. **§3 边界图四条链** —— 已确认漏了 testing-strategy ↔ roadmap（洞 1）。这条链在 sdflow 生态里普遍存在（roadmap 包是所有无家文档的临时寄生处），值得补进 05 §3。
