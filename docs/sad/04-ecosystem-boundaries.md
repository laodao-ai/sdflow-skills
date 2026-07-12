# SAD 生态与相邻文档边界：装什么 · 不装什么 · 引用谁

> 状态：**活文档**（explore 讨论 + 边界纪律；判据真相源已固化进 `sdflow-architecture/references/quality-criteria.md`「SAD 边界总则」，本文只展开与画图，引用不复述规则）。
> 来源：2026-07-12 `/opsx:explore`——由「SAD 该不该含 dev/test 环境需求、安装配置、单元/集成测试技术路线」之问逼出；与 03（L2）、00（三层）配套。
> 一句话：SAD 是 **空间轴 L1 × 架构决策** 的单一入口；越出这个交集的每一样，都有一个**相邻文档**是它的家，SAD 引用不复述。

---

## 1. 为什么需要这张图

连续两问都在探同一件事——SAD 边界该画在哪：

- 「子系统内部怎么实现」该不该进 SAD？→ 不该，归 **L2**（见 03）。
- 「dev/test 环境、安装配置、测试路线」该不该进 SAD？→ 大多不该，归**过程/工程轴文档**（本文）。

反复追问的根因是缺一条**边界判据**和一张**相邻文档地图**。补上后，「X 该不该进 SAD」不必每次重吵。

## 2. SAD 边界判据（四问，真相源在 `quality-criteria.md`）

一个 X 进 SAD **当且仅当四问皆是**（否则归相邻文档，SAD 引用不复述）：

```
① 跨子系统？        影响 ≥2 子系统的一致性         —— 否(单子系统内部) → L2
② 架构决策？        在约束内选了什么结构/契约       —— 否(操作步骤)     → README/runbook
③ 空间/当下？       不是时间排期                  —— 否(排期)        → roadmap
④ 下游 context 要带？ 模块 agent 生成时要知道的约束  —— 否(纯人读手册)  → CONTRIBUTING
```

判据背后是 SAD 自己的哲学（02 §0.3「刚好够」+ S11 单一真相源）：SAD 膨胀成 README+runbook+测试计划的大杂烩，就丧失了「系统结构真相源」的身份。

## 3. SAD 生态坐标系

SAD 居中，六条轴各挂一类相邻文档；SAD 只放每样的**架构决策切片**，细节在相邻文档：

```
                            时间轴
                     roadmaps/{name}/  (阶段·排期·per-effort)
                              ▲
          契约轴              │              决策轴
      openspec/specs/  ◀──────┼──────▶  openspec/adr/
     (contract 真相源)        │         (决策链 supersession)
                     ┌────────┴────────┐
                     │  SAD             │  architecture/sad.md
        语言轴 ◀─────┤  L1 空间结构      ├─────▶ 过程/工程轴
   CONTEXT.md        │  × 架构决策       │      testing-strategy.md (测试路线)
   (统一语言)         │  per-system 单例  │      README/CONTRIBUTING (装/配/dev-env)
                     └────────┬────────┘
                              ▼
                          空间轴（下钻）
                 architecture/subsystems/{sub}.md  (L2, per-system)
                 openspec/changes/                 (L3 一次交付)
```

## 4. 相邻文档边界表

| 轴 | 文档 | 粒度 | 管什么 | 与 SAD 的关系 |
|---|---|---|---|---|
| 空间·下钻 | `architecture/subsystems/{sub}.md`（L2, `sdflow-subsystem`） | per-system | 子系统→子模块+内部 contract | SAD §5 定子系统对外 contract；L2 实现它、引用不复述（见 03） |
| 空间·交付 | `openspec/changes/`（L3, `opsx:ff`） | per-change | 一次垂直交付 | 引用 SAD/specs 的 contract |
| 时间 | `roadmaps/{name}/`（`sdflow-roadmap`） | **per-effort** | 阶段/里程碑/排期 | SAD 不复述阶段；**成熟度只标空间状态**（planned/draft/validated），M 阶段归 roadmap（见 T1） |
| 决策 | `openspec/adr/` | per-system | 决策链（不可变+supersession） | SAD §4 只索引 |
| 语言 | `openspec/CONTEXT.md` | per-system | 统一语言 | SAD §10 只引用 |
| 契约 | `openspec/specs/`（capability） | per-system | contract 真相源（delta 回流） | SAD/L2 引用（**待 D2 拍**，见 03 §4） |
| 过程/工程 | `testing-strategy.md` | 工程实践 | 单元/集成测试路线、测试分层 | SAD §8 一条**横切引用**，不复述 |
| 过程/操作 | `README`/`CONTRIBUTING`/dev-setup | 操作手册 | 安装/配置步骤、dev 环境搭建 | SAD **不涉及**；§2 只记栈/平台**约束**、§8 只记**配置策略**决策 |

## 5. 真相源分工表（扩展 02 §1「分家」）

02 §1 只分了 ADR/CONTEXT/假设清单三家；本文按六轴补全，**每类内容唯一真相源，SAD 引用不复述**：

| 内容 | 唯一真相源 | SAD 里的形态 |
|---|---|---|
| 子系统对外 contract | SAD §5（或 `specs/`，待 D2） | 本体 或 引用 |
| 子模块/内部 contract | L2 subsystems（或 `specs/`） | 不含 |
| 阶段/排期 | roadmap | 不含（成熟度是空间状态，非阶段） |
| 决策 why | ADR | §4 索引 |
| 术语 | CONTEXT | §10 引用 |
| 测试路线 | testing-strategy | §8 一行引用 |
| 安装/配置步骤 | README/CONTRIBUTING | 不含 |
| 配置**策略**（决策） | SAD §8 横切 | 本体 |
| 平台/栈**约束** | SAD §2 | 本体 |

## 6. 这一问的两个收获

1. **识别出"过程/工程轴"**——SAD 生态此前系统对待了空间/时间/决策/语言/契约五轴，**漏了过程/工程轴**（测试策略 + 操作手册）。用户这一问补上了它。现实印证：mqtt-console 的 `testing-strategy.md` 现在**寄生在 roadmap 包**，与 `technical-architecture.md`(L2) 同构——都是缺正规 home 的相邻文档临时挤进 roadmap。
2. **T1 复现（SAD 越界标时间轴）**——mqtt-console SAD 的 contract 注释混入了 M 阶段（`draft(M2b planned)`），把 roadmap 的时间信息写进了空间文档。目标态：SAD 只标**空间成熟度**（planned/draft/validated/frozen），「哪个 M 阶段推进它」引用 roadmap。这条边界现在是糊的（同 03 §5.1 T1）。

## 7. dev/test/install/测试 四样的归属裁决

| 用户提的 | 架构切片（进 SAD，多已在） | 操作/过程主体（→ 相邻文档） |
|---|---|---|
| 开发/测试环境需求 | 栈/平台/工具链约束 → §2 | 装什么、起本地依赖步骤 → CONTRIBUTING |
| 安装配置 | 配置**策略** → §8 横切；分发形态 → §7 | 安装命令/步骤 → README |
| 单元/集成测试路线 | **可测试性**质量属性 → §1；架构撑测试（双sink可headless测/Engine可mock/contract 即集成测试点） | 框架/目录/泳道细节 → testing-strategy |

> 业界锚：arc42 把「测试概念」放 §8 Cross-cutting、testability 是质量属性，**没有**安装/dev环境/测试计划一等章节；C4 只画结构不碰过程。SAD 的测试观本就内建为 **contract-driven**（骨架 DoD =「每条 contract 被真实调用穿过」= 集成测试的架构表达）。

## 8. 固化清单（→ a）

已随本轮固化进 `sdflow-architecture/references/`（skill 运行时可见）：

- `quality-criteria.md`：加「SAD 边界总则」（§2 四问，本文引用它不复述）
- `checklists/quality-attribute-candidates.md`：补 **可测试性** 候选
- `checklists/cross-cutting-template.md`：补 **测试策略** 横切候选

**未固化（留决策）**：T1（SAD 只标空间成熟度、M 阶段引用 roadmap）牵动 sad-template contract 行约定 + 与 roadmap 的引用纪律，属 D5，接地试跑后一并定（见 03 §7 D5）。

---

## 参考锚

- arc42 §2 Constraints / §7 Deployment / §8 Cross-cutting Concepts（测试概念归此）· ISO 42010
- Ousterhout《A Philosophy of Software Design》——testability 作为深模块/接口质量
- 02 §0.3 范围分层「刚好够」· §1 分家表 · quality-criteria S11 单一真相源
- 03（L2 与 roadmap 正交、technical-architecture.md 寄生）· 00 §5（L2 空档）/ §140（空间×时间正交）
