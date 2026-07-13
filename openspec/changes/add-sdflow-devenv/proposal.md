# add-sdflow-devenv

> 设计源：`docs/sad/07-devenv-skill-design.md`（九条设计点逐条拍定）
> 接地证据：`docs/sad/06-process-axis-grounding-receipt.md`（mqtt-console 实测）

## Why

技术架构定了之后，**把项目的开发/测试环境真正建起来**这件事在生态里无 skill 覆盖：`sdflow-architecture` 的交棒止于「过程轴文档指路（指出不代写）」，下游是空的；`sdflow-init` 铺的是 **workflow 的运行环境**（规则 bundle），按定义不管项目内容。于是「定测试策略 → 落 Makefile/broker/CI/harness → 跑通 → 出真相源文档」全靠人手搓。

mqtt-console 的接地实测暴露了手搓的三种系统性失败：**散落双写**（同一份测试策略存在 3 处、env 内容存在 2 处）· **命令虚构**（纯文档型 prompt 会为对齐模板范式而编造不存在的 `make dev/test/build`）· **无门禁**（`assert-bindings` 这类检查无任何自动触发点，全靠人记得跑）。

`docs/sad/05` 曾拍板「D（独立 skill）不立」，**已被推翻**：其候选集把 skill 误当「生成器」（于是一证伪「从 SAD 投影只有 12%」就否掉了它），且 B 候选建立在对 `sdflow-init` 职责的误解上。**正解：那 88% SAD 投影不出来的槽，恰恰全是待决策项——正需要一个编排器来问、来拍、来留痕**，与 `sdflow-architecture` 编排空间轴决策同构。

## What Changes

- **新增 skill `sdflow-devenv`**——过程轴编排器（**非**生成器），五步流水线（事实采集 → 泳道设计拍板 → 落地脚手架 + 真跑 → 冷审 + 人门 → 文档 + 入口 + 交棒）+ 三模式分流（新建 / 归位 / continue）。
- **泳道三态状态机 + 渐进 DoD**：`planned → scaffolded → verified`，逐条独立推进，**不强制全绿**（项目初期定不下所有事）；但**诚实是硬要求**——`scaffolded` MUST 带非空 `blocked_by`。
- **落地物（真代码，直写落盘）**：Makefile target（**门禁逻辑在此**）· broker/依赖服务 · CI 配置（**只做调用壳**）· 测试 harness · **每泳道一条 smoke** · doctor 依赖自查。skill 是**追加者不是拥有者**——落地物**不设托管块**，重名 fail-closed。
- **negative control（新判据）**：`verified ⟺ 依赖就绪时 smoke 绿 ∧ 抽掉依赖时 smoke 红`——把「vacuous smoke」这个头号假绿风险从「几乎纯语义」降为两级机械检查。
- **两份真相源 + 入口注入**：`openspec/architecture/{environments,testing-strategy}.md`（命令表**机械渲染**，frontmatter 为单一真相源）+ `devenv-log.md` 留痕；`opsx-devenv` 托管块 → CLAUDE/AGENTS/README + `openspec/INDEX.md`。
- **修改 `sdflow-architecture`**：§5.3 交棒话术从「指出不代写 + 给模板路径」改为**指向 `/sdflow-devenv`**；description 的生态路由句增加过程轴分流。
- **BREAKING**：无。纯增量（消费仓不跑本 skill 则完全无感）。

## Success Metrics

| # | 指标 | 判定 |
|---|---|---|
| SM-1 | **归位模式回归**：在 mqtt-console 复跑 `sdflow-devenv`（归位模式），产出的两份真相源与人工归位结果**语义一致**，且源文件删除集一致 | 人工比对 + `devenv_lint` 全绿 |
| SM-2 | **新建模式跑通**：至少 1 个绿地项目（有 SAD、无代码）跑通五步，产出**至少一条 `verified` 泳道** + 一张明确待建清单 | 该泳道 smoke 真跑绿 ∧ 通过 negative control |
| SM-3 | **机械门禁生效**：`devenv_lint` 五条检查（命令出处一致性 / 指针不悬空 / 删源残留引用 / N/A 显式性 / 入口复述检测）在故意注入的坏输入上**全部 fail-closed** | pytest 覆盖每条 |
| SM-4 | **诚实性**：任一 `scaffolded` 泳道 MUST 有非空 `blocked_by`；任一 `verified` 泳道 MUST 通过双向判据 | lint 断言 + pytest |
| SM-5 | **零双写**：命令/出处/状态只在 frontmatter 存在一份，正文表格由脚本渲染且带 DO-NOT-EDIT banner | lint 断言 |

## Non-Goals

- **业务测试用例**——本 skill 只建 harness + 每泳道一条 smoke；业务回归网归各 change。
- **生产运维 runbook**（on-call / SLO / 告警）——本 skill 只到 deploy 操作。
- **替用户安装系统依赖**（`brew install` / `docker pull`）——只给 doctor 脚本 + 命令，副作用不可逆。
- **smoke 跑不绿时 debug 到通**——职责是「建 + 验」不是「调通」；跑不绿是合法状态（`scaffolded` + `blocked_by`），修复归下次 `continue`。
- **monorepo 多系统**——v1 单例 + 显式提示；演进路径 `openspec/architecture/{system}/` 与 SAD **同步升**（`covers` 要锚得住）。
- **时间轴排期 / 里程碑** → `sdflow-roadmap`。
- **从 SAD 自动生成文档**——接地实测投影率仅 12%，且投影出的是最不值钱的部分（详见 `06` §1）。

## 需求优先级〔TG-19〕

| P | 需求 | 理由 |
|---|---|---|
| **P0** | 五步编排 + 三模式分流 · 泳道状态机 + frontmatter schema · 落地物追加（Makefile/harness/smoke）· smoke 真跑 + **negative control** · `devenv_lint` 五条 · 两份真相源渲染 | 缺任一则 skill 不成立（P0 = 最小可用） |
| **P1** | `opsx-devenv` 托管块注入 + INDEX · `lane-patterns` 五格 · 冷审镜单 · 归位模式的删源三处置 + `grep` 引用面判据 · 并发安全（原子写 + 锁） | 可用但不完整；并发安全**不可后补**（见假设 A-4） |
| **P2** | doctor 脚本生成 · CI 调用壳生成 · `sdflow-architecture` §5.3 交棒话术改写 · 未覆盖形态的 todo 登记 | 增益项，可迭代 |

## 利益相关方与外部依赖〔TG-20〕

| 方 | 影响 |
|---|---|
| **消费仓**（mqtt-console / 04-iot-tools / 未来项目） | 新增 `openspec/architecture/{environments,testing-strategy,devenv-log}.md` + 落地物 + `opsx-devenv` 托管块；**不跑本 skill 则完全无感** |
| **`sdflow-architecture`** | §5.3 交棒话术 + description 路由句变更（本 change 的 MODIFIED capability） |
| **`sdflow-init`** | **不改**——`opsx-init` 区块与 `opsx-devenv` 区块互不干涉（不同 marker token）；本 skill **复用其 `inject` 算法**（token 定位 + 幂等整块替换），不跨 skill import |
| **`embedded-test-sop`** | 真硬件泳道**指向它**，不重造手动 SOP |
| **外部命令**（`make` / `go test` / `npm` / `docker` / `git`） | skill 执行它们；失败模式表见 design〔TG-08〕 |

## 开放问题〔TG-21〕

| # | 问题 | 负责人 / 截止 |
|---|---|---|
| Q-1 | `lane-patterns` 未覆盖形态（Java 服务 / 移动 app / 分布式）何时补格？v1 走「临场推导 + 登记 todo」兜底 | 操作者 / 首个撞上该形态的项目 |
| Q-2 | monorepo 多系统演进——需 SAD 先支持多系统（`covers` 才锚得住），两者绑定升级的时机 | 操作者 / 首个 monorepo 消费仓 |
| Q-3 | `devenv_lint` 的「入口复述检测」是弱启发（README 出现完整命令表 → 告警），阈值待接地校准 | 实现期 / 首跑后 |

## 假设〔TG-22〕

| # | 假设 | 失效影响 |
|---|---|---|
| **A-1** | **negative control 对所有依赖类型都成立**（抽掉依赖 → smoke 必红） | 若某类依赖有「优雅降级」路径（缺失时自动 fallback 而非报错），smoke 会绿 → **误判 vacuous**、把好泳道卡在 `scaffolded`。缓解：`deps: []` 显式豁免 + 冷审复核 |
| **A-2** | **依赖形态五格**（外部有状态依赖 / UI / 语言桥 / 真硬件 / 纯计算）能覆盖多数项目 | 若大量项目落到「未覆盖形态」，`lane-patterns` 退化为纯临场推导，枚举完备性丧失 → 两次运行推荐面不一致 |
| **A-3** | **渐进 DoD 不会导致永久 `scaffolded`**（人会回来 `continue`） | 若无人推进，文档长期停在「一条 verified + 五条 scaffolded」→ 环境名存实亡。缓解：收尾 MUST 逐条列出未 verified 泳道（不许埋进文件） |
| **A-4** | **两个 session 并发跑 devenv 会撞车**（同时写 frontmatter / log） | 已知**必然**发生（`sdflow-architecture` code-review 抓出 5 个 CRITICAL 并发 bug，最终用 exclusive-create lock 修）。本 change **MUST 从设计期就防**，不可后补〔TG-26〕 |
| **A-5** | 消费仓已有的 Makefile target **语义可被读懂并登记**（归位模式） | 若已有 target 语义模糊（一个 `test` 跑了三条泳道），登记会错位 → `covers` 对账失真。缓解：登记结果进搬运表人门 |

## Capabilities

### New Capabilities
- `devenv-provisioning`: 开发/测试环境搭建编排器——五步流水线 · 三模式分流 · 泳道三态状态机与渐进 DoD · 落地物追加（skill 为追加者非拥有者）· smoke 真跑与 negative control · 机械 lint 五条 · 两份真相源渲染与入口托管注入 · 并发安全写入。

### Modified Capabilities
- `architecture-design`: `Requirement: 触发分工与互相指路（生态路由）` 的指路集合扩充——SAD 交棒后的过程轴下游**从「指出不代写 + 给模板路径」改为指向 `/sdflow-devenv`**；description 增加过程轴分流句（「建 dev/test 环境 → `/sdflow-devenv`」），与既有的时间轴分流句（→ `sdflow-roadmap`）并列。

## Impact

**本仓**：

- 新目录 `sdflow-devenv/`（`SKILL.md` + `scripts/`×3 + `references/`×6 + `tests/`）
- 改 `sdflow-architecture/SKILL.md`（§5.3 交棒话术 + description 路由句）
- 改 `README.md`（Skills 列表）；**`setup.sh` 无需改**（自动识别含 `SKILL.md` 的顶层目录）
- 新增 pytest（本仓纪律：改 `scripts/` 必跑 `tests/`）

**消费仓**（跑本 skill 后）：`openspec/architecture/{environments,testing-strategy,devenv-log}.md` · 落地物（Makefile/compose/CI/harness/smoke/doctor）· `opsx-devenv` 托管块（CLAUDE/AGENTS/README）· `openspec/INDEX.md` 条目。

**技术栈标注**〔TG-01/02/03 均不命中〕：Markdown（SKILL.md / references）+ Python（scripts）。无后端服务、无前端、无嵌入式固件——下游**不选用** `spec-checklists/domains` 的 backend·go / frontend / embedded 领域清单。**但 `TG-26`（并发）与 `TG-08`（外部依赖）命中**，其领域段按「脚本/工具」栈就近取用（文件原子写、锁、子进程失败处理）。

## Compliance

- **skill 目录约定**：`SKILL.md`（frontmatter `name`/`description`）+ `scripts/` + `references/` + `tests/`，符合本仓 skill 结构；`setup.sh` 自动装载。
- **bundle 权威源纪律**：本 change **不改** `sdflow-init/assets/workflow/`（未新增/修改 spec 工作流规则），无需 `sdflow-init update` 回灌。
- **托管区块纪律**：`opsx-devenv` 为**新 marker token**，**MUST NOT** 写入 `opsx-init` 区块（`inject` 是整块替换，共用必然互相覆盖）。
- **审查顺序**：`/sdflow-spec-review`（设计门）→ 实现 → `/review`（本地 diff）→ push → `/sdflow-code-review`（远程 PR）→ `/sdflow-done`。
- **HR-TG**：命中 4 个高风险触发（TG-08 外部依赖 / TG-09 状态机 / TG-17 信任边界 / TG-26 并发）→ spec-review **单开领域 cross-model**。
