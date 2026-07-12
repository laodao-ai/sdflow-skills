# 新项目「系统设计 → 模块设计 → 实施」方法论探讨

> 状态：**活文档**（讨论基线，随后续逐题讨论回填结论）
> 来源：2026-07-12 `/opsx:explore` 探讨记录
> 待办清单见文末「待讨论问题清单」——每解决一题回填结论与指针。

---

## 0. 背景与原始提案

**背景**：AI 生成模块级代码的质量已可保证，但局部最优 ≠ 整体最优。瓶颈上移到系统总体设计、roadmap 与任务拆分。

**原始三步提案**：

1. **架构设计（SAD）**：系统划分为多个子系统，每个子系统有明确目标/范围/边界，子系统间确定 contract，标注各子系统特别注意事项。
2. **子系统设计文档**：子系统拆分为子模块，每个子模块有明确目标/范围/边界，说明子模块如何实现子系统对外 contract，子模块间确定 contract，标注注意事项。
3. **子模块细化设计**：拆分成一个个 task / change。

---

## 1. 总判断

**三步框架作为文档层级是对的，作为时间顺序是危险的。**

锚点：Parnas《A Rational Design Process: How and Why to Fake It》(1986)——理性的自顶向下设计过程在现实中从不存在（设计上层时不可能预知下层展开后才暴露的信息）；正确做法是「装作」按理性过程做：**文档按 SAD→子系统→模块 的理性结构组织和维护，过程允许迭代回改**。

三步框架在业界坐标系里的对应：

| 三步层级 | C4 模型 (Simon Brown) | arc42 / ISO 42010 | DDD 战略设计 |
|---|---|---|---|
| 系统 → 子系统 + contract | Context → Container | Building Block View L1（黑盒→白盒） | Bounded Context + Context Map |
| 子系统 → 子模块 + contract | Container → Component | Building Block View L2 | Aggregate / 模块划分 |
| 子模块 → task/change | Component → Code | — | 战术设计 |

骨架无需怀疑（≈ stepwise refinement + design by contract）。真正要解决的是三件事：**每层缺了什么、过程顺序怎么改、AI 把什么变了**。

---

## 2. 每一层都缺的三样东西

### 2.1 分解判据没有说出来

「把系统划分为子系统」——**按什么划**是方法论里最著名的坑。Parnas 1972：按处理流程（flowchart）分解是直觉且错误的；按**信息隐藏**分解（每个模块藏住一个「未来可能变化的设计决策」）才正确。AI 时代坑更深：让模型「分子系统」，默认给出的就是流程式分解（语料里最多的形态）。

候选判据（通常组合使用）：

- **变化率 / 变化原因**：一起变的放一起，独立变的分开（信息隐藏的现代表述）
- **领域语言边界**（DDD bounded context）：同一个词两边含义不同处即边界
- **数据所有权**：谁 owns 写权，单写者原则
- **认知负载**（Team Topologies）→ AI 语境翻译为 **context 预算**：一个子系统的完整设计 + 邻居 contract 必须装进一个 agent 的有效上下文

**关键实践**：SAD 必须写明「按什么判据划的、否决了哪些划法、为什么」（= 一条 ADR）。判据不落盘，边界争议会反复重吵，AI 会按默认判据悄悄漂移。

### 2.2 Contract 的内涵远大于接口签名

把 contract 写成 API 签名列表是最大执行风险。能真正约束 AI 生成的 contract 至少五层：

1. **语法**：API / schema / 类型（机器可查）
2. **语义**：不变量、前置/后置条件、**错误语义**（哪类错误谁负责、error taxonomy）、幂等性、顺序与并发假设
3. **质量**：延迟/吞吐预算、一致性等级
4. **所有权**：数据谁写、谁只能读
5. **演进**：向后兼容策略、版本规则

为什么对 AI 特别关键：**AI 会用「合理但发散」的假设填掉 contract 没说的每一条缝**。「局部最优拼起来全局崩坏」的具体机制，大部分是缝隙被两边用不同假设填了（错误处理、重试语义、时间/时区/ID 各造一套）。

**Contract 的归宿是从散文走向可执行**（= 「一致性机械化优先」原则在架构层的投影）：

```
散文描述 → 结构化 schema         → contract test          → CI fitness function
(设计期)   (OpenAPI/proto/型别)    (Pact 式消费者驱动,       (依赖方向、分层规则,
                                    每条边界一套)             ArchUnit/import-linter 类)
           ── 机器可读 ──────────  ── 机器可验证 ─────────  ── 持续守护 ──
```

最后一档来自演进式架构（Ford/Parsons《Building Evolutionary Architectures》）：架构约束写成 CI fitness function，防「每个 change 局部合理、累积架构侵蚀」。散文 contract 约束不了 AI，可执行 contract 才行。

### 2.3 横切面在分解层级里没有家

「系统→子系统→模块」是一棵包含树，但错误分类学、认证授权、可观测性约定、时间/时区、ID 生成、重试与幂等、数据一致性策略——**横切关注面不属于任何子系统**。arc42 第 8 章「Cross-cutting Concepts」专门收容，是必需不是装饰。

对 AI 尤其致命：横切约定不集中一份，N 个模块的 N 次生成会各自发明 N 套。这是「局部最优 ≠ 全局最优」**最高频**的表现形式，且**分解怎么做都解决不了**——只能「约定集中化 + 每个模块任务把这份约定作为 context 强制携带」。

约定集中化自身也有机械化梯子：**散文约定 < 清单 < lint 规则 < 共享库（paved road：把「做对」变成阻力最小路径，如错误处理直接给 helper 库而非规范文字）**——能上台阶就上台阶，散文是最弱形态。

---

## 3. 过程改造：从瀑布到「骨架先行的流水线」

三段瀑布（所有 SAD → 所有子系统文档 → 才拆 task）的三个问题：

1. contract 是纸上假设，未经集成验证，错误逐层放大；
2. 文档保鲜成本随层数指数增长；
3. **均匀深度陷阱**：低风险 CRUD 子系统和高风险核心子系统花同样笔墨（Fairbanks《Just Enough Software Architecture》：设计是买保险，**深度 ∝ 风险**，保费别超过赔付额）。

```
  瀑布式（风险后置）:
  ┌─ SAD ─┐┌─ 子系统A/B/C 全部设计 ─┐┌─ 全部拆task ─┐┌─ 实现 ─┐┌─ 集成 ─┐
                                                              ▲
                                            contract 错误在这里才暴露，代价最大

  骨架先行的流水线（风险前置）:
  ┌─ SAD(轻) ─┐
  ┌─ Walking Skeleton ─┐   ◀── 第一个 change：穿过【所有】子系统 contract 的
        │                       最细端到端切片，唯一目的 = 用运行证据检验 L1 contracts
        ▼ contracts 被验证/修正 → 升为 frozen
  ┌─ 子系统A: L2设计 ─┐┌─ A 拆task+实现 ─┐
        ┌─ 子系统B: L2设计 ─┐┌─ B 拆task+实现 ─┐      ◀── 各子系统独立流水线，
              ┌─ 子系统C: 一页纸(低风险) ─┐┌─ C 实现 ─┐    深度按风险分配
        ▲
        └── 回流规则：下层发现上层错 → 必须改上层文档 + 记 ADR，禁止只在下层绕过
```

要点：

- **Walking skeleton / tracer bullet**（Cockburn、《程序员修炼之道》）：SAD 后第一个 change 不是任何子系统的第一个模块，而是穿过全部子系统边界的最细垂直切片，打通部署/集成/每条 contract。sdflow-implement 已在 ticket 层用 tracer-bullet，此处是**同一思想上移到系统层**。骨架 change 的 **DoD = 每条 L1 contract 至少被一次真实调用穿过 + 部署链路走通**——不是「功能可用」；骨架的交付物是被验证的 contract，功能薄到可笑才是对的。
- **Contract 成熟度分级**：`draft →（骨架验证后）validated → frozen`；frozen 后改动走显式变更流程（≈ ship_gate 设计门失鲜 REFUSE_START 的同一机制）。
- **回流（backflow）是三层文档活下来的唯一条件**：没有回流的三层文档 = 三层谎言。AI 时代更致命——人类读过期文档会起疑，AI 把它当 ground truth 喂进 context，等于主动投毒。（仓内先例：「先改 assets、再推下游」单一真相源纪律。）
- **流水线不设全局 barrier**：不要求「所有子系统 L2 完成才开始任何 L3」。唯一合法 barrier = 需要跨子系统信息汇总的决策点（如 contract 定稿评审——改一条边要两边同时看）。

---

## 4. AI 把什么变了：三个位移

前提「AI 模块级代码质量可保证」成立 ⇒ 瓶颈整体上移，具体三个位移：

1. **稀缺资源从「写代码」变成「全局一致性」**。局部生成便宜了，全局连贯更贵——它恰好是没法委托给单模块 agent 的东西，只能活在两处：作为 context 喂进去的**上游文档** + 抓漂移的**机械检查**。contract 可执行化与横切面集中化因此从「良好实践」升格为「生存必需」。
2. **设计文档的身份变了：从「人读的说明」变成「机器消费的 context artifact」**。模块级 task 派发时携带精确路由的上下文包——本模块 contract + 直接邻居 contract + 子系统不变量 + 横切约定，**而非整份 SAD**。文档层级 = context 路由结构；Team Topologies 的认知负载边界翻译为 context 预算边界。
3. **文档保鲜从「卫生问题」变成「正确性问题」**。文档是喂给下游生成的输入，过期输入 = 错误输出。回流规则、单一真相源、「contract 只在一处存、其他地方引用不复述」优先级全部上调。

---

## 5. 落到 sdflow 工具链：L2 是空档

| 三步层级 | 现有承载 | 状态 |
|---|---|---|
| L1: SAD | `openspec/roadmaps/{name}/design.md`（sdflow-roadmap 三件套；roadmap.md「近细远雾」= 风险驱动深度） | ✅ 已有 |
| L2: 子系统设计 | —— | ❌ **空档** |
| L3: 模块 → task/change | OpenSpec change（proposal/design/specs/tasks + 门禁链；「一个 change = 一个完整阶段结果」已立） | ✅ 已有 |

注意：roadmap.md 的「阶段」是**时间切**，「子系统」是**空间切**，两者正交——阶段结构不能顺便承载子系统分解。

L2 空档的三个选项：

- **a) 每子系统一个独立 roadmap 包**——太重，丢失 SAD 与子系统文档的父子关系。
- **b) `roadmaps/{name}/subsystems/{sub}.md`**——结构顺，但诱发三层文档各自复述 contract，双写发散。
- **c) Contract 进 `openspec/specs/`（capability specs），子系统设计文档只放「决策 + 注意事项」，contract 一律引用不复述**——**当前倾向**。理由：`openspec/specs/` 本来就是「系统当前真相」的家；delta-spec 机制天然是 contract 的版本化演进通道（change 提 delta → done 时同步回 specs），archive 环节已做「delta 对码核验」——**contract 单一真相源 + 回流机制这套最难的基建已存在**，缺的只是子系统级 contract 纳入 specs 的书写约定 + L2 文档「只引用不复述」的纪律。

三层「唯一真相」的分工（选项 c 下）：

| 真相源 | 管什么 |
|---|---|
| SAD（roadmap design.md） | 分解判据 + 全局决策 + 横切约定 |
| `openspec/specs/` | 全部 contract |
| 子系统设计文档 | 本子系统的设计决策与注意事项（contract 只引用） |
| change | 一次交付 |

每层的门：L1 → grill + review（sdflow-roadmap 已内建分档）；L3 → 完整门禁链；L2 → 按风险决定过不过门（低风险子系统一页纸直接走）。

---

## 待讨论问题清单

逐题讨论，解决一题回填一题（结论 + 指针）。

| # | 问题 | 状态 | 结论指针 |
|---|---|---|---|
| Q1 | **分解判据与试验田**：判据（变化率/领域边界/数据所有权/context 预算）如何在具体新项目上选择与组合？需要一个真实项目接地验证 | ✅ 已结 | 见文末「Q1 结论」 |
| Q2 | **L2 落地形态**：选项 c 往下推演——子系统级 capability 在 `specs/` 的命名与粒度约定、L2 文档模板 | ⏳ 待讨论 | — |
| Q3 | **Contract 机械化档位**：梯子爬到 schema / contract test / CI fitness function 哪一档，按项目栈与寿命定 | ⏳ 待讨论 | — |
| Q4 | **沉淀成 skill**：升级 `sdflow-roadmap`（加 L2 + 骨架先行编排）vs 新开 `sdflow-sad`——本身是一次「拆分标准」的应用 | ⏳ 待讨论 | — |

**建议顺序**：先 Q1 后 Q2——拿真项目把判据和 L2 形态跑一遍，方法论才算过接地检验；否则等于在犯「纸上 contract 未经集成验证」的错。

> **议程重构（2026-07-12）**：Q1 收结后，讨论改为按原始三步逐步推进——步骤一（架构设计）见 `01-step1-architecture-design.md`（逐条讨论中）；步骤二（子系统设计，吸收 Q2）、步骤三（任务拆分）后续各开一份文档。Q3（contract 机械化档位）、Q4（沉淀成 skill）挂在三步讨论完成之后。

---

## Q1 结论：分解判据的选择与组合（业界最佳实践锚定）

> 接地样本：Sarvelo mqtt-console 演练——**n=1 验证点，非结论来源**。演练价值：四判据各咬住一类真实裂缝（枢纽包 / 横切渗漏 / 绑定层淤积 / context 超预算），且仪器成本 ≈ 80 行脚本，可行性成立。

### 1. 四判据的业界谱系（无一自创，各有权威脉络）

| 判据 | 权威脉络 |
|---|---|
| **变化率 / 波动性** | Parnas 信息隐藏 (1972) → Common Closure Principle（Martin 组件原则：一起变的放一起）→ volatility-based decomposition（Löwy《Righting Software》，显式反功能分解）→ 实证仪器化：change coupling / hotspot 分析（Tornhill《Your Code as a Crime Scene》《Software Design X-Rays》，已产品化为 CodeScene）、DSM / propagation cost（MacCormack/Baldwin/Rusnak） |
| **领域语言** | DDD bounded context（Evans）→「服务边界 = 语言边界」（Newman《Building Microservices》）→ 工业实践如 Uber DOMA；配套 subdomain 分类 core/supporting/generic（Vernon；Nick Tune core domain charts）决定设计投资深度 |
| **数据所有权** | database-per-service / 单写者原则（微服务时代普及，Newman 等）；「跨边界双写」是边界画错的经典信号，单体内模块边界同样适用 |
| **认知负载 → context 预算** | Conway (1968) → Team Topologies cognitive load（Skelton/Pais）→ **AI 语境外推为 context 预算——emerging，尚无权威定论（诚实边界，标注为外推）** |

### 2. 组合的最佳实践形态：不是单选，是固定顺序的流水线

业界无单一标准文本，但主流实践收敛为：

```
第一刀   领域语言边界（DDD 战略设计）
  │      —— 同时服务人的理解、组织设计、AI context 路由，是共识度最高的起点
  ▼
修正     变化率 / 波动性
  │      —— 防「按名词切」陷阱：entity-service 反模式（User服务/Order服务看似领域
  │         切分，实为功能分解变体；Nygard、Löwy 均有权威批判）。
  │         注意：AI 让模型自由分解时的默认输出恰是此形态，此判据是主要解毒剂
  ▼
校验     数据所有权
  │      —— 每类数据唯一 writer；出现跨子系统双写 = 边界错误信号
  ▼
约束     认知负载 / context 预算
  │      —— 尺寸上限：一个子系统的设计 + contract 装进一个 agent 有效上下文
  ▼
分配     subdomain 分类（core / supporting / generic）
         —— 设计深度 ∝ 战略价值 × 风险（衔接 §3 Fairbanks 风险驱动：core 深设计、
            generic 用现成方案一页纸带过）
```

### 3. 绿地 / 存量双形态（统一「新项目」与「既有项目」两个场景）

| 判据 | 绿地形态（设计期 · 生成约束） | 存量形态（运行期 · 检验仪器） |
|---|---|---|
| 变化率 | **预期变化清单 + 变化情景演练**（Parnas anticipated changes / ATAM change scenario）：逐条检查「该变化只击中一个子系统吗」 | git 共变分析（CodeScene 类工具或自写脚本） |
| 领域语言 | 先建术语表，语义边界即候选边界 | 术语表 × 包结构对账（单包多语域检测） |
| 数据所有权 | 写权矩阵：每类数据唯一 writer | 写权矩阵对码核验 |
| context 预算 | 「子系统设计 + contract ≤ agent 有效上下文」作为分解验收条件 | LOC / 触碰热度 / 最小装载集测量 |

新项目用左列**生成**分解；分解 = 假设，跑若干阶段后用右列仪器**后验回检**。

### 4. 分解也有 fitness function（业界已产品化，非设想）

右列仪器全部可脚本化且多已产品化（CodeScene、ArchUnit / import-linter、DSM 工具链）→ 分解质量从一次性判断升级为**持续守护**：定期回跑（阶段边界 / retro 时机），共变漂移 → 回流修正 SAD。与之配套的边界演进共识：Fowler MonolithFirst / Brown modular monolith——**边界先在单体内以模块形态验证，稳定后才物理分布**（boundaries before distribution）。

### 5. 操作教训（演练实测，与文献印证一致）

1. **测量粒度 = 逻辑变更级，非 commit 级**：同一仓两个口径差 3 倍（跨前后端耦合 7% vs 19%）——commit 级系统性低估耦合；
2. **机械出信号、语义判机制**：仪器输出的正确形态是「裂缝清单 + 疑点清单」而非结论，机制归因（横切渗漏还是合理内聚）必须人 / 深读代码判——与 Tornhill 行为代码分析的既定用法一致；
3. **现状证据必配目标态追问**：热点可能只是「当前阶段恰好在做它」，必须追问「roadmap 后续阶段是否继续吸积」才能定性结构性 vs 暂时性。

---

## 参考文献锚

- Parnas, *On the Criteria To Be Used in Decomposing Systems into Modules* (1972) — 信息隐藏分解判据
- Parnas & Clements, *A Rational Design Process: How and Why to Fake It* (1986) — 文档结构 vs 时间顺序
- Simon Brown, *C4 Model* — 分层视图纪律
- arc42 / ISO/IEC/IEEE 42010 — SAD 结构与 viewpoint/concern
- Evans, *Domain-Driven Design* — bounded context / context map
- Fairbanks, *Just Enough Software Architecture* — 风险驱动设计深度
- Ford/Parsons/Kua, *Building Evolutionary Architectures* — fitness function
- Ousterhout, *A Philosophy of Software Design* — 深模块（接口窄、实现深）
- Skelton/Pais, *Team Topologies* — 认知负载边界（→ context 预算）
- Cockburn / Hunt & Thomas — walking skeleton / tracer bullet
- Löwy, *Righting Software* — volatility-based decomposition，反功能分解
- Tornhill, *Your Code as a Crime Scene* / *Software Design X-Rays* — change coupling / hotspot 实证仪器（CodeScene）
- MacCormack/Baldwin/Rusnak — DSM / propagation cost 模块度度量
- Newman, *Building Microservices* — 服务边界 = 语言边界、数据所有权
- Nygard — entity-service 反模式批判
- Martin, 组件原则（CCP/REP/CRP + ADP/SDP/SAP）— Common Closure = 变化率判据的组件级表述
- Fowler, *MonolithFirst* / Brown, modular monolith — 边界先验证后分布
- Vernon / Nick Tune — subdomain 分类（core/supporting/generic）与设计投资分配
