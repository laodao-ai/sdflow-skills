# 过程轴文档体系：文档集 · 边界 · 交付形态

> 状态：**活文档**（explore 方法论产出）。**重构自** `05-ops-skill-design-draft.md`——原文预设「做一个 ops skill」，本轮把主题拓宽为**过程轴文档体系的方法论**（有几份 · 各装什么 · 各自边界），**skill 从占位主题降级为 §5 的交付选项之一**（用户 2026-07-12：「最后不一定是 skill，也可能是模板+prompt」）。
> 定位：这是过程轴缺失的「00/01」——architecture 轴有方法论（00/01）垫底才有 02 skill 设计；过程轴此前只有 04（生态定位）+ environments 模板草案，**没有方法论**。本文补上它。
> 引用不复述：轴间边界判据引用 `04-ecosystem-boundaries.md`（六轴生态 + SAD 边界总则），本文只展开过程轴**内部**的文档集与交付。

---

## 1. 轴定位（过程轴管什么、不管什么）

过程轴 = **「怎么开发、测试、运维、上手」的操作/程序性知识**。它与其余五轴正交，明确**不含**：

```
结构（SAD/L2）· 排期（roadmap）· 决策 why（ADR）· 术语（CONTEXT）· 契约（specs）
                                    └─ 这五样在 04 已分清，本文不重述 ─┘
过程轴 = 操作(搭建/运行/部署) + 方法(测试) + 协作(贡献) + 上手(入口索引)
```

判据仍是 SAD 边界总则第②问的镜像：**「操作步骤」不进 SAD/L2，归过程轴文档**（`04` / `quality-criteria.md` 边界总则）。本文管的是：这些「操作步骤」自己该怎么组织成文档。

## 2. 文档集

### 2.1 第一刀：两类文档

过程轴内部先分两类——这是组织文档集的**第一刀**，也决定后面交付机制（§5）：

- **真相源类**：每份 own 一个操作子域，是该子域内容的**唯一出处**；
- **入口·索引类**：自己 **own 任何内容**，只做「概要 + 指向真相源」；跨轴聚合指针。

### 2.2 枚举表

| # | 文档 | 类型 · 子轴 | 目标（一句话） | 应含内容（槽） | 普适性 | SAD 投影锚 |
|---|---|---|---|---|---|---|
| 1 | **environments.md** | 真相源 · 操作 | 从零到能跑：dev 搭建 / test 执行 / deploy 发布 | §1 dev（工具链·本地依赖·构建运行·坑）· §2 test（依赖·各层命令·CI·fixture）· §3 deploy（平台·配置项·发布·回滚） | 普适（deploy 对纯库可 N/A） | §2约束→工具链 · §3外边界→本地依赖 · §7→deploy · §8→配置项 |
| 2 | **testing-strategy.md** | 真相源 · 方法 | 测什么、怎么分层、测试哲学 | 分层（unit/int/e2e 各测什么）· contract=集成测试点 · 覆盖护栏 · mock/fixture 策略 · 测试数据来源 | 普适 | §1可测试性→方法 · §5 contract→集成点 |
| 3 | **CONTRIBUTING.md** | 真相源 · 协作 | 人怎么贡献：流程与规约 | 分支策略 · commit 规约 · PR/review 流程 · 代码风格指针 ·（sdflow 项目：指向 openspec workflow） | 普适但常薄 | 无（纯人流程，SAD 不投影） |
| 4 | *runbook.md* | 真相源 · 运维 | 服务出问题怎么办 | 监控/告警 · 事故响应 · on-call · SLO | **条件**（仅长驻服务；桌面/CLI/库 → 并 env §3 或 N/A） | §7部署拓扑 · §8可观测性 |
| 5 | **README.md** | 入口 · 索引 | 人的第一入口：是什么 + 去哪 | 一句话 what/why · 快速开始（关键命令）· 各真相源指针 | 普适 | 无（跨轴聚合指针） |
| 6 | **CLAUDE.md** / AGENTS.md | 入口 · 索引 | agent 的 context 入口 | build/test/run/deploy 各一行命令 · 指向真相源 | 普适 | 无（同上） |

### 2.3「有几份」的答案

**核心 3 份真相源**（env / test / contrib）+ **2 份入口**（README / CLAUDE）+ **1 份条件**（runbook，仅服务）。

- 对 **mqtt-console**（桌面 app）：env / test / README / CLAUDE 是活的；CONTRIBUTING 薄（大半 = openspec workflow 指针）；runbook N/A。
- **普适槽 vs 条件槽**（同 SAD 十节「填或显式 N/A」纪律）：槽普适，但 env §3 deploy 对纯库 N/A、runbook 对非服务 N/A。**是「填或显式 N/A」，不是「每项目一套新槽」。**

## 3. 文档间边界（引用不复述）

每格内容只有一个家，跨格一律引用、禁复述（承 `04` §5 真相源分工 + S11 单一真相源）：

```
SAD §7 部署(决策) ──被引──▶ environments §3(操作)      ← 决策 vs 操作
testing-strategy(方法) ─被引─▶ environments §2(测试环境) ← 方法 vs 环境
environments(真相源) ──被引──▶ README / CLAUDE.md(入口)  ← 真相 vs 入口
CONTRIBUTING(人流程) ──引──▶ openspec workflow(规则真相源) ← 项目流程 vs 工作流规则
```

**入口类的边界纪律更严**：README/CLAUDE **MUST NOT** 复述任何真相源细节，只放「最小起步命令 + 指针」——否则入口一膨胀就成了第二个真相源，指针与本体双写漂移（范式见 `environments-template-draft.md` 附 A/B）。

### 3.1 testing-strategy ↔ environments §2 的精确切线（2026-07-12 拍板：拆）

上图第 2 条链（方法 vs 环境）是过程轴内最易糊的一处（fixture/测试数据两边都想放）。**拍板：拆**——testing-strategy 独立第 3 份真相源，**不并入 env §2**。切线 = **方法/决策 vs 环境/操作**，与第 1 条链（SAD §7 决策 ↔ env §3 操作）**同一把刀**（体系一致，非给 testing 开特例）：

| 内容 | testing-strategy（方法/决策） | environments §2（环境/操作） |
|---|:---:|:---:|
| 分层：unit/int/e2e 各测什么、为什么这么分 | ✓ | |
| contract = 集成测试点（哪些边界必被穿过） | ✓ | |
| 覆盖目标 / 门禁护栏（policy 阈值） | ✓ | |
| mock 边界选在哪（策略） | ✓ | |
| fixture **策略**（golden-file / factory · 数据代表什么） | ✓ | |
| 各层**执行命令**（`make test` / `go test ./...`） | | ✓ |
| 测试**依赖**（起 broker / playwright 浏览器） | | ✓ |
| CI runner 平台 / headless 处理 / 缓存 | | ✓ |
| fixture **文件在哪 / 怎么生成**（`make test-data`） | | ✓ |
| 覆盖率**当前数字** | | ✓（或不放，工具产出） |

> **拍板依据（决策三镜 + 主次）**：**主 = 系统镜**——方法（稳定哲学）与环境（易变工具链）是**两条独立变化轴**，混一则易变部分每次改动搅动稳定部分（违 S11 演进可维护），且「决策 vs 操作」本就是过程轴统一组织原则。**佐证**：用户镜（reviewer 问「测得够不够好」vs contributor 问「怎么跑」，两类读者→两个文档）+ 开发循环镜（合并 diff 噪音）是同根（两轴混一）的两个侧面，非独立理由。**次要保留**：小项目 testing-strategy 薄 → 用 §2.3「填或显式 N/A」化解，**不构成合并理由**（目标态导向：别拿现状"薄"缩水目标）。切线**无确定性硬信号**（「命令/路径→env」是弱启发），属语义边界，靠起草纪律守 + git 审计兜。
> **现实一致**：`environments-template-draft.md` §2 边界注（「测什么/怎么分层归 testing-strategy——本节只放环境依赖+执行命令」）已隐含此切线，本节把它**显式化 + 补精确归属表**，无需回改模板。

## 4. SAD 投影 vs 项目自填

真相源类文档的槽分两种来源，**比例决定交付形态**（§5）：

| 槽来源 | 例 | 谁填 |
|---|---|---|
| **SAD 投影**（5.3 交棒给锚） | env 工具链←§2约束 · env 本地依赖←§3外边界 · env deploy←§7 · env 配置项←§8 · test 方法←§1 可测试性 · test 集成点←§5 contract | 可从 SAD 机械/半机械投影 |
| **项目自填**（SAD 无源） | env 首次搭建的坑 · 各层测试**执行命令** · CI 缓存/headless 处理 · fixture/测试数据来源 · 回滚具体步骤 | 只能项目现场填 |

**关键观察**：env/test 里**约一半槽能从 SAD 锚投影，另一半是纯项目操作**（SAD 无源）。这意味着——**任何「从 SAD 自动生成 environments」的机制，天花板只有一半**；另一半必须项目填。**生成价值有限。**

## 5. 交付形态决策

### 5.1 三个候选

| | C 模板 + prompt | D 独立 skill（工作名 `sdflow-ops`） | B 并入 `sdflow-init` |
|---|---|---|---|
| 形态 | 结构化模板 + 一段起草 prompt，项目自跑 | 新 skill：init 从 SAD 投影生成 + 维护 + 边界守卫 | init 铺项目骨架时一并铺过程轴模板 |
| 成本 | 零（已有 `environments-template-draft`） | 一个新 skill 的建设 + 维护 | init 增量（已有铺设机制） |
| 生成价值 | —（人跑 prompt） | **仅一半**（§4：SAD 只投影一半槽） | 同 D，一次性 |
| 维护价值 | 无机制（靠人自觉） | **有**（入口指针漂移检测 + 边界守卫） | **有**（随 init update 扫描/刷新） |

### 5.2 天平已开始倾斜（不用等真写）

把 §2.1 + §4 合起来看，**交付判断的证据在文档集这一步就浮出来了**：

1. **生成价值有限**——§4：SAD 只投影一半槽，「从 SAD 自动生成 env」天花板只有一半，另一半项目必填。**⇒ 削弱 D 中「init 生成」这条腿。**
2. **维护价值真实**——§2.1：入口类（README/CLAUDE）的指针最易腐烂；真相源类的**边界越界**（架构决策漏进 env、测试方法漏进 env §2）是起草高发错。**⇒ 真正值得机制化的是「维护/守卫」，不是「生成」。**
3. **维护是「扫描已存在的文档」，天然属 init update 域**——`sdflow-init update` 已有「扫消费仓 + 刷新/告警」机制（tools/ 刷新、陈旧遮蔽告警）。指针漂移检测 + 过程轴边界守卫**同构于它现有职责**。

**初步倾向**：**B（并入 sdflow-init 的维护扫描）+ C（模板+prompt 起草）** 组合 —— 起草用模板+prompt（生成价值本就只一半，不值专门 skill）；维护/守卫挂 `sdflow-init update`（同构现有扫描）。**独立 ops skill（D）暂不立**——它的两条腿（生成、维护）一条只值一半、一条该归 init，**不足以撑起一个独立 skill**（承拆分标准：别为凑齐四轴硬造 skill）。

> ⚠ 此为**纸上倾向**，非定论。真写一份 mqtt-console environments 仍可能推翻（见 §6 前置）——但即使真写，也是验证「B+C」而非「从零判 C-vs-D」，判据已收窄。

### 5.3 若最终仍走 D：命名候选

- `sdflow-ops`（operations，涵盖 env+test+操作，工作名）
- `sdflow-environments`（太窄，漏 testing-strategy）
- `sdflow-runbook`（偏部署操作，漏 dev/test）

## 6. 前置与开放问题

- **前置（硬，接地验证）**：在 mqtt-console **真写一份 `environments.md`**（照 §2 模板填真实口径，把寄生在 roadmap 包的 `technical-architecture.md`/`testing-strategy.md` 搬出归位）。作用已从「从零判 C-vs-D」收窄为**验证 §5.2 的「B+C」倾向 + §2 槽对不对 + §4 投影比例真是不是一半**。**MUST NOT 纸上先建 skill。**
- **✅ 已拍（2026-07-12）**：**testing-strategy 从 env §2 独立**（不合并）——精确切线 + 决策三镜依据见 §3.1。「有几份」由此**确认为 3 份真相源**（非降为 2）。
- **开放问题**：① runbook 的服务/非服务判据能否机械化（有无长驻进程信号）· ② 入口指针漂移检测的机械化档位（字符串锚 vs 语义）· ③ 边界守卫复用 SAD 边界总则四问到什么程度 · ④ CONTRIBUTING 在 sdflow 项目薄到什么程度才值得单独成文（vs 一行指向 workflow）。

---

## 参考锚

- `04-ecosystem-boundaries.md`（六轴生态、SAD 边界总则、真相源分工）· `environments-template-draft.md`（env 模板 + 入口引用范式）
- `sdflow-architecture/SKILL.md` §5.3（上游「指出不代写」交棒锚）· `quality-criteria.md` 边界总则
- 方法论纪律：过程轴文档须从**真运行样本蒸馏**（同 architecture 02 距 00/01；`doc-distill-from-own-protocols`）——故 §6 前置硬性要求先真写一份
- 拆分标准：别为凑齐四轴硬造 skill（`CLAUDE.md` §设计基准 4 + `change-scope-one-complete-stage-result`）
