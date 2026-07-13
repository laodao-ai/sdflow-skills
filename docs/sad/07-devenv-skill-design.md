# devenv skill 设计：产出形态 · 内容 · 质量判定 · 人机分工

> 状态：**设计收敛**（九条设计点逐条拍定，2026-07-13）——待终审 → 作为 change `add-sdflow-devenv` 的设计源。
> **真相源移交声明**（同 02）：skill 落地后，方法论 live 真相源移交 `sdflow-devenv/references/`；此后本文冻结为设计考古层，修订一律改 references。
> 来源标注：2026-07-13 brainstorming 会话（九条逐条讨论）；接地证据 = `06-process-axis-grounding-receipt.md`（mqtt-console 实测）。
> **前置推翻**：本 skill 的成立推翻了 `05` §5「D 不立」的拍板——该结论的候选集把 skill 误当「生成器」，且 B 建立在对 `sdflow-init` 职责的误解上。详见 `05` §5.2 与本文 附录 A1/A2/A3。
> **本文档自包含**：不依赖其他文档即可使用；引用外部内容一律内嵌正文，外部文档仅作来源标注。
> 命题：做一个「开发/测试环境搭建 skill」——技术架构定了之后，**把项目的 dev/test 运行环境真正建起来**（不只是一份文档）。
> 四问（同 02）：①产出什么 ②包含哪些内容 ③质量如何判定 ④哪些 AI 能推荐 / 哪些需人提供后 AI 再推荐。

---

## 0. 目标与范围校准

### 0.1 skill 目标（一句话）

**技术架构定了 → 定测试策略 → 把开发/测试环境搭起来**：出决策、落脚手架、跑通、出真相源文档 + 入口索引。

**关键校准（2026-07-13 操作者拍定）**：目标**不是产出两份文档**，而是**建立环境**——文档是它的真相源产物之一，不是全部。这一条推翻了 `05` §5 的整个候选框架（它把 skill 等同于「文档生成器」，因而否得太快）。

### 0.2 生态位：三个「环境」必须分清

| skill | 建的是什么「环境」 | 管项目内容吗 |
|---|---|---|
| `sdflow-init` | **workflow 的运行环境**（规则 bundle、`opsx-init` 托管块） | ❌ 不管——**这是它的定义**（操作者 2026-07-13 澄清） |
| **`sdflow-devenv`** | **项目的 dev/test 运行环境**（Makefile、broker、CI、测试 harness） | ✅ 就是它 |
| `sdflow-architecture` | 不建环境，定**空间结构**（SAD） | ✅ 但只管结构 |

同名不同层。`sdflow-init` 不碰项目内容，所以「生成项目文档 + 更新 INDEX」**不能挂在它身上**——`05` §5 的 B 候选（并入 init 维护扫描）由此**作废**。

- **上游**：`sdflow-architecture` §5.3「过程轴文档指路（指出不代写）」——它给锚、拒绝代写，本 skill 接住。
- **下游**：交棒回常规 change 流程（`/opsx:ff`），此后各 change 在这套环境里跑测试。
- **不管**：单次 change 的 spec/design · **业务测试用例**（归各 change）· 时间轴排期（`/sdflow-roadmap`）· 生产运维 runbook（本 skill 只到 deploy 操作，不含 on-call/SLO）。

### 0.3 DoD 重定义：渐进，不是一次性全绿（操作者 2026-07-13 拍定）

skill 的完成态**不是「全部泳道 verified」**——项目刚开始不可能把所有事定下来，**有方向和基本能力就行**，开发过程中逐步验证完善。

因此**泳道三态状态机**（每条泳道独立推进）：

```
planned  ──▶  scaffolded  ──▶  verified
决定要有       harness+smoke      smoke 真跑绿过
这条泳道       写了，没跑绿
```

这个重定义**系统性降低两类要求**（对称 02 §0.1 的「skeleton-ready」）：

- **对完成度的要求**：允许停在 `planned` / `scaffolded`，**不阻塞**；skill 可重入，下次 continue 推进一格。
- **对环境的要求**：本机缺依赖（无 Docker / 无 mosquitto）**不是失败**——如实标 `scaffolded` + 写清 `blocked_by`，给修复指引。

**但诚实是硬要求**（fail-closed 的落点在此，不在完成度）：`scaffolded` **MUST 带非空 `blocked_by`**——不许标个状态就蒙混过去。**「跑不绿」是合法状态，「跑不绿却装作跑得绿」不是。**

### 0.4 与 02 的对称关系

| | `sdflow-architecture` | `sdflow-devenv` |
|---|---|---|
| 轴 | 空间（子系统怎么切） | 过程（怎么开发/测试） |
| 产出 | SAD（文档） | 文档 **+ 落地物**（真代码） |
| 状态机 | 文档级：draft → skeleton-ready → validated | **泳道级**：planned → scaffolded → verified |
| DoD | 每条 L1 contract 被一次真实调用穿过 | **每条泳道被一次真实运行穿过**（渐进达成） |
| 交棒 | 骨架 change（不代开） | 回常规 change 流程 |

---

## 1. 产出什么（形态）

**三类产物**，缺一不可——只出文档 = 半成品，只出脚手架 = 没有真相源。

| # | 产物 | 位置 | 说明 |
|---|---|---|---|
| 1 | **`environments.md`** | `openspec/architecture/` | 过程·操作轴真相源：dev 搭建 / test 执行 / deploy 发布。frontmatter 存泳道状态（机械真相源），正文命令表**由脚本渲染** |
| 2 | **`testing-strategy.md`** | 同上 | 过程·方法轴真相源：泳道分层 / contract=集成测试点 / mock 边界 / 护栏 / 盲区 |
| 3 | **`devenv-log.md`** | 同上 | append-only 留痕：模式分流 · 泳道状态迁移 · 降级 · 冷审轮次（对称 `sad-log.md`；continue 断点恢复靠它） |
| 4 | **落地物**（真代码） | 项目各处 | 见 §1.4 清单 |
| 5 | **入口** | 项目根 / openspec | `opsx-devenv` 托管块 → CLAUDE.md / AGENTS.md / README.md；`openspec/INDEX.md` 条目 |

### 1.1 落位：与 SAD 同居（`05` §2.2.1）

两份真相源落 `openspec/architecture/`，**不落项目根、不落 `docs/`**：过程轴与空间轴同属**设计真相源层**；`docs/` 是 as-built 解释层（系统「是什么」），「怎么搭/怎么跑」不属于它；落项目根则两头不靠。

### 1.2 承载形态：全直写，质量门内建（操作者 2026-07-13 拍定）

文档与脚手架**都直落盘，不开 change 壳**（recorder 式，先例：`sdflow-architecture` 规则 4 / `sdflow-roadmap`）。

理由：**环境是前置基础设施**——走 change 壳有鸡生蛋（该 change 自己的测试要靠这套环境才能跑）。质量靠四层门内建：`devenv_lint`（机械）+ **smoke 真跑**（可执行性）+ 冷审子代理（语义）+ 人门（看 diff）。

### 1.3 单一真相源纪律：命令表机械渲染，不双写

泳道的命令、出处、状态在 frontmatter 是**机械真相源**；正文那张命令表（命令 | 跑什么 | 出处 | 状态）**由 `devenv_scaffold.py render` 从 frontmatter 渲染**，带 `DO NOT EDIT` banner。

理由：两处各写一遍必漂移（承 CLAUDE.md 设计基准 1「一致性机械化优先」；生态先例：`issues/INDEX.md` 的 DO-NOT-EDIT banner）。

```yaml
---
lanes:
  - id: hermetic
    status: verified
    command: "go test ./..."
    source: "Go 工具链"
    smoke: "internal/console/smoke_test.go"
    covers: ["§5.2 消息运行时", "§5.4 Workspace 编排"]   # ← SAD contract 锚，E2 对账用
    deps: []                                            # 无外部依赖 ⇒ negative control 不适用
  - id: integration
    status: scaffolded
    command: "make integration"
    source: "Makefile:11-14"
    smoke: "internal/console/integration_smoke_test.go"
    deps: ["mosquitto"]                                 # ← negative control 抽掉它，smoke 必须红
    blocked_by: "本机无 mosquitto — brew install mosquitto 后 /sdflow-devenv continue"
sad: missing        # 降级留痕（§5 起手 A）：无 SAD，contract 集成点靠读码猜
---
```

### 1.4 落地物清单与边界（2026-07-13 逐条拍定）

| 落地物 | 写吗 | 谁 owns |
|---|---|---|
| **Makefile target**（每泳道一个） | ✅ 核心——**门禁逻辑在此** | **人**（skill 只追加） |
| 测试 harness（build tag / 进程内 broker 包 / fixture 工厂） | ✅ | 人（skill 只追加） |
| **每泳道一条 smoke** | ✅ `verified` 的唯一证据 | 人（skill 只追加；**归位模式复用已有测试**） |
| broker / 依赖服务（compose 或 `hack/` 启停脚本） | ✅ | 人（skill 只追加） |
| doctor 依赖自查（缺什么、怎么装） | ✅ =「常见坑」槽的可执行版 | 人（skill 只追加） |
| **CI 配置** | ⚠️ 可选，**且只做调用壳** | 人（skill 只追加） |

**CI 只做调用壳**（拍定）：

```
Makefile:  make integration          ← 真门禁在这
CI 配置:   - run: make integration    ← 只是个调用者
```

三条理由：**无 CI 的项目照样有完整本地门禁**（mqtt-console 无 CI，门禁全在 Makefile + `hack/`，接地实证可用）· **CI 平台可换而门禁不变** · **本地与 CI 跑同一条命令**，不会出现「CI 绿本地红」。项目无 CI → CI 槽显式 `N/A` + **记后果**（§2.1 纪律）。

**核心边界：skill 是「追加者」，不是「拥有者」。**

frontmatter 的 `source` 字段**可以指向人写的行**——所以 skill 不需要接管 Makefile，只需两个动作：**已有的 target → 登记**（读出来写进 frontmatter，跑 smoke 验证）· **缺失的 target → 追加**。lint 只查 `source` 指的行**存不存在**，不关心那行是谁写的。

于是**托管区块只用于两处，落地物一概不用**：

| 对象 | 谁 owns | 机制 |
|---|---|---|
| `environments.md` 的命令表 | **skill** | 机械渲染 + `DO NOT EDIT` banner |
| CLAUDE / AGENTS / README / INDEX | **skill** | `opsx-devenv` 托管块，幂等整块替换 |
| **Makefile / CI / harness / smoke** | **人** | **无托管块**——skill 只追加，追加时带一行来源注释供审计 |

Makefile 不设托管块的理由：托管块意味着「这块归 skill、会被整块覆盖」，而 Makefile 是**人机共有的活文件**，人随时会改 target 的实现。skill 只管「有没有这个 target」，不管「它里面怎么写」。

**重名冲突 → fail-closed**：已有 `integration:` 但语义不是本泳道 → 脚本报冲突、留人裁决，**MUST NOT 静默覆盖**（先例：`sad_scaffold.py context-add` 同名术语 fail-closed）。

### 1.5 git 前置（写真代码 / 删用户文件的护栏）

**写代码是加法，删源是减法——风险不对称，故分治**：

| 动作 | git 前置 |
|---|---|
| 写落地物（Makefile / compose / CI / harness / smoke） | **不要求**工作区干净 |
| **归位模式的删源** | **fail-closed 要求工作区干净** |

删源那条 fail-closed 的理由：删错了想 `git revert`，若工作区混着用户其他未提交改动，会**把它们一起 revert 掉**——要求先 commit/stash，是让「可回滚」这个承诺真的成立。

**分支**：不强制开分支（recorder 式直写 + 多次 `continue` 增量推进，开一堆分支反成累赘）；但**在默认分支上 → 提示建议开分支**，让人拍。
**不自动 commit**（承 `CLAUDE.md`：commit 只在用户要求时），收尾给建议 message + `git add` 提示。
**人门必看 diff**（④ 议程第 3 条）——真代码进仓的最后一道人类护栏。

## 2. 包含哪些内容（槽）

### 2.1 `environments.md` 十六槽

（来源：`environments-template-draft.md`，已由 mqtt-console 接地补槽。原草案自称「十六槽」实列 14 个，接地补入两槽后**真为 16**。）

| § | 槽 |
|---|---|
| §1 dev | 前置工具链 · 本地依赖服务 · 构建+本地运行 · **构建副产物** · 常见坑 |
| §2 test | 测试依赖 · 各层执行命令（**带出处列**）· **测试选择路由** · CI 环境 · fixture/测试数据 · 方法指针 |
| §3 deploy | 目标平台+依赖版本 · 配置项清单 · 发布流程 · 回滚 · 架构决策指针 |

**两条接地纪律（血泪，MUST 守）**：

- **命令必须为真**：每条命令能在 Makefile / package.json 找到出处。在本 skill 里这条**天然成立**——命令表的出处就是 skill 自己刚写的 Makefile。（历史陷阱：纯文档型 prompt 会为对齐模板范式而**虚构** `make dev/test/build`。）
- **N/A 须连带记后果**：显式 `N/A — <理由>` 之外，还要记它**留下的洞**（例：CI = N/A ⇒「`assert-bindings` 因此无任何自动触发点」）。只写 N/A 不写代价 = 把缺口藏进「这项不适用」。

### 2.2 `testing-strategy.md` 九槽

（原 `05` §2.2 只给 5 槽，接地实测产物里价值最高的三节一个槽都没有 —— 已补。）

分层（各测什么、为什么这么分）· **分层隔离机理**（泳道为何不互相连带）· contract = 集成测试点 · 覆盖护栏 · mock 边界 · fixture 策略 · **测试编写 idiom**（怎么写出确定性断言）· **分层的实例化：逐文件门禁清单** · **已知盲区与测试债**

### 2.3 两文档的精确切线（`05` §3.1，17 行）

**方法/决策 → testing-strategy；环境/操作 → environments。** 与「SAD §7 决策 ↔ env §3 操作」是**同一把刀**。

最漂亮的一对切线（接地实证）：**flake 的定性与放行决策**（是什么 · 为何不修 · 靠什么护栏）→ testing-strategy；**flake 护栏的实现**（Makefile 的 `|| retry once`）→ environments。同一件事，决策面与操作面各有一个家。

---

## 3. 质量如何判定：语义判据全集 → 机械化拆解

> 推导顺序同 02 §3：先枚举「好环境」的语义判据全集，再逐条问「有无确定性信号」——能结构化的下沉为脚本断言，残余留给冷审镜与人门。**不从机械清单起手**（路灯谬误）。

### 3.1 语义判据全集（E1–E11）

| # | 判据 | 一句话定义 |
|---|---|---|
| E1 可执行性 | 文档里每条 `verified` 命令**真能跑**；新机器照文档能从零跑起来 |
| E2 泳道覆盖 | SAD 每条子系统 contract 被**至少一条泳道穿过**；跨真实边界（网络/文件/进程/语言桥）者不许只用假引擎糊弄 |
| E3 分层正当性 | 泳道互补不冗余，各有判据；能说清「为什么这条不能并进那条」 |
| E4 保真度阶梯 | 泳道按保真度/依赖递增；**确定性断言优先落最低层**（缩小 flake 能污染的断言面） |
| E5 故障隔离 | 泳道互不连带（build tag 解耦）；flake 的暴露面被关进一条泳道，不污染仲裁者 |
| E6 诚实度 | `planned/scaffolded/verified` 如实标；`scaffolded` 带 `blocked_by`；N/A 带理由+后果；盲区显式登记 |
| E7 单一真相源 | 命令/状态不双写（frontmatter → 正文机械渲染）；入口（README/CLAUDE）只放最小命令+指针，不复述 |
| E8 边界纪律 | 方法 vs 操作切线（§2.3）守住；架构决策不漏进 env（引用 SAD）；阶段计划不漏进 testing-strategy（归 roadmap） |
| E9 可移植性 | 依赖显式、可 doctor 自查；不依赖某台机器的隐式状态 |
| E10 smoke 非 vacuous | smoke 真穿过泳道——**有断言、能因回归而红**；不是「跑起来没报错」 |
| E11 演进可维护性 | 泳道可增量推进；环境变更能回写；状态迁移只走合法迁移表 |

### 3.2 逐条拆解：可结构化 vs 语义残余

| 判据 | 可结构化（确定性信号 → 脚本断言） | 语义残余 | 残余归属 |
|---|---|---|---|
| E1 | `verified` 态：`source` 指的文件行**真存在** + 命令**真能跑**（脚本执行） | 「新人照文档真跑得起来吗」（坑写全了吗） | 冷审镜 + 真人首跑 |
| E2 | SAD §5 contract 集合 vs 泳道 `covers` 字段并集**对账**（有 SAD 时；缺项列出） | `covers` 声明是否**真命中**（声明 ≠ 穿过） | 冷审镜（对抗镜） |
| E3 | — （近乎无信号） | 全部 | 冷审镜 |
| E4 | 弱启发：`verified` 泳道按依赖数排序，断言密度倒挂 → 只报不判 | 全部 | 冷审镜 |
| E5 | build tag 交叉引用检测（realbroker 泳道是否连带点亮 embedded 文件） | 隔离是否真有效 | 冷审镜 |
| E6 | **强**：`scaffolded` ⇒ `blocked_by` 非空；N/A 槽 ⇒ 理由+后果非空；槽在但内容空 → 报错 | 「N/A 是现状还是该有而没建」 | **人门** |
| E7 | **强**：正文命令表是渲染区块（banner 在）；入口复述检测（README 出现完整命令表 → 告警） | 真相源划分合理吗 | 冷审镜 |
| E8 | 弱启发：testing-strategy 里出现命令词面 / `M<n>` 阶段词面 → 只报不判 | 归属判定本身 | **冷审镜 + 人门**（`05` §3.1 自认语义边界） |
| E9 | doctor 脚本存在性；依赖清单每项有版本+安装法 | 真能在干净机器跑通吗 | 冷审镜 + 真人首跑 |
| E10 | ① 弱：smoke 含断言语句（AST/词面）<br>② **中强：negative control**——抽掉依赖，smoke **必须红**（见下注） | **语义恒真**（协议/框架层面导致断言恒真） | 冷审镜（对抗镜） |
| E11 | **强**：状态迁移只走合法迁移表；非法跳级 fail-closed | — | — |

> **E2 特例注**：SAD 的两条高价值投影之一（另一条见下），也是 SAD 缺失时**损失最大**的——所以 `sad: missing` 要响亮留痕（§5 起手 A）。`covers` 声明的**正确性**无确定性信号（同 `adr/0018` 的 declared 命中集问题），归冷审。
>
> **SAD 的第二条高价值投影**：**依赖形态 ← SAD §3 外边界**。SAD 已把外部系统全列出来，`lane-patterns` 的形态四问基本可从它读出（§6.2）。两条投影都指向同一件事：**SAD 缺失时损失的不是「少写几个字」，是泳道设计失去锚**。
>
> **E10 特例注（vacuous-guard，本 skill 的头号假绿风险）**：「环境建好了」的全部证据就是 smoke。分三层治：
>
> 1. **机械弱**：含断言语句——只抓「完全没断言」这种最低级情形。
> 2. **机械中强 —— negative control（阴性对照）**：一条泳道的 smoke，价值在于**真穿过它的依赖**；那么**故意抽掉依赖（不启 broker/容器），它必须红**。**抽掉依赖还绿 ⇒ 根本没碰那个依赖 ⇒ vacuous。** 于是 `verified` 的判据升级为**双向**：
>
>    ```
>    verified  ⟺  依赖就绪时 smoke 绿  ∧  依赖缺失时 smoke 红
>    ```
>
>    **近乎免费**（不改代码、不做变异测试，只是不启动依赖再跑一遍，且失败很快）。仅适用于 `deps` 非空的泳道；`deps: []`（hermetic/纯单元）不适用——但它们的 vacuous 风险也最低（测纯逻辑，没有「假装穿过」的空间）。
>    **副产物**：本机缺依赖时 smoke **本来就该红**；若反而绿了，那不是「环境没问题」，是**这条 smoke 是假的**。
> 3. **冷审（唯一手段）**：**语义恒真**——机械绝无可能抓到。范例挂进镜单：mqtt-console 的泄漏探针曾用 `CleanSession=true` 重连，而 MQTT 3.1.1 规定 `CleanSession=1` 的 CONNACK **恒** `SessionPresent=0` ⇒ 该断言恒真，残留 session 回归**全部漏过**（staff-review 抓出的真缺陷）。断言语句在、数量>0、字面也不恒真——三层机械全部失效。

### 3.3 拆解产出 = skill 的三份组件清单

1. 「可结构化」列 → **`devenv_lint.py` 断言清单**
2. 「语义残余」列 → **冷审镜单**（`references/review-lenses.md`）
3. 价值类残余（E6 的 N/A 判断 / 技术栈选择 / 依赖装不装）→ **人门清单**

### 机制 A：泳道状态诚实（防「假绿环境」，服务 E6/E10）

对称 02 的「假设显影」。本 skill 最危险的属性是**看起来建好了**：Makefile 有 target、smoke 文件在、文档写得全——但没跑过，或跑绿了却什么都没断言。

对策：① 状态三态强制标注，`scaffolded` MUST 带 `blocked_by`；② smoke **由 skill 亲自跑**（不问「你跑过吗」）；③ vacuous-guard 冷审专职一镜；④ 收尾报告**逐条列出**还停在 `planned/scaffolded` 的泳道（不许埋进文件里）。

### 机制 B：命令溯源（服务 E1/E7）

每条命令标 `source`（`Makefile:11-14` / `package.json:10` / `Go 工具链`）。`verified` 态 lint **强制核验** source 行存在；`planned` 态不核验（命令还没造出来，标 `source: planned` 合法）。

---

## 4. 人机分工

**总原则（承 02）：人 owns 事实与价值，AI owns 枚举、推演与纪律。** 但本 skill 多一类：**AI owns 落地物起草**（真代码）。

- **人必须给的**：①**环境事实**（团队机器上有 Docker 吗？CI 平台是什么？能装 mosquitto 吗？）②**价值判断**（保真度值多少代价——要不要为 TLS 覆盖多养一套真 broker？③**依赖安装授权**（skill **不替你装系统依赖**，只给命令 + doctor）
- **AI 的强项**：①**泳道候选枚举**（`lane-patterns.md`——不靠临场回忆）②**脚手架起草**（Makefile / compose / harness / smoke）③**纪律**（渲染、留痕、lint）

### 4.1 分工矩阵

| 环节 | 人必须提供 | AI 推荐 → 人拍板 | AI 全自动（机械） |
|---|---|---|---|
| 事实采集 | CI 平台 · 本机/团队可用依赖 · 部署形态 | 从 SAD §2/§3/§5 投影出候选**给人复核** | 投影字段抽取 |
| 泳道设计 | **方案选择** · 保真度取舍 | **按技术栈给泳道候选**（lane-patterns）+ 各自代价 | 泳道 ↔ contract 覆盖对账 |
| 落地脚手架 | — | Makefile / compose / CI / harness / smoke **起草** | 文件落位 · 状态写入 |
| 跑通 | 装系统依赖（skill 只给指引） | 失败诊断 + 修复指引 | **真跑 smoke** · 状态迁移 |
| 文档 | — | 坑 / 护栏 / 盲区的**内容**（纯人写区，SAD 投影率为零） | 命令表渲染 · 槽完整性 |
| 入口 | — | — | 托管块注入 · INDEX 写入 |

> **接地实证（`06` §4）**：environments/testing-strategy 的 17 个槽里，SAD 真投影只有 2 个（12%），构建配置可投影约 5 个，**其余 10 个是纯人写**——而纯人写区（常见坑 / 四条护栏 / 已知盲区）恰恰是全篇最高价值的部分。**这不是「生成价值低」，而是「这 88% 全是待决策项，需要有人问、有人拍、有人留痕」**——正是编排器存在的理由。

---

## 5. 流程：五步 + 三模式

### 起手 A：preflight + 模式分流（脚本，退出码驱动）

```
python3 "$SKILL_DIR/scripts/devenv_scaffold.py" init --root "$REPO"
```

- **exit 3（无 `openspec/` 布局）**：**fail-closed**，原样转述指引（先 `/sdflow-init`）。同 `sdflow-architecture`。
- **`sad.md` 缺失**：**显式降级、不 fail-closed**（操作者 2026-07-13 拍定）——响亮警告「拿不到子系统 contract 清单，E2 覆盖对账将失效，testing-strategy §5 只能靠读码猜，可能漏边界；强烈建议先跑 `/sdflow-architecture`」+ 留痕 `sad: missing`，然后继续。**MUST NOT 佯装有 SAD**（同 Codex 宿主降级的 `walkthrough=self-review-degraded` 纪律）。
- **exit 4（`environments.md` 已存在）**：显式区分后带 `--on-exists` 重跑：
  - **continue**：推进泳道 / 增补（跳到步骤 ③）。先读 `devenv-log.md` 定位断点。
  - **replan**：技术栈或测试策略被推翻，重走 ②。
- **检出存量素材**（`docs/getting-started.md` / `docs/**/testing*.md` / roadmap 包里的 testing-strategy / 已有 Makefile 与测试）→ 提示走**归位模式**。

### 三模式

| 模式 | 项目状态 | 内容从哪来 | 头号风险 | 人门放哪 |
|---|---|---|---|---|
| **新建**（greenfield） | 有 SAD，无代码/无构建配置/无文档 | **人拍**（问 + 候选 → 决策） | 虚构不存在的命令 | 泳道候选拍板（②） |
| **归位**（brownfield） | 有代码、有构建配置、文档散落或缺失 | **蒸馏**（读 Makefile/测试/散落文档 → 判归属） | **只新建不删源**（制造双写） | **搬运表确认**（①'） |
| **continue** | 已有本 skill 产物 | 增量 | 状态谎报 | 按需 |

> **归位模式 = 在 ① 前面插一段「素材盘点 + 判归属 + 搬运删源」，后半段与新建完全共用**（补缺失的泳道、落脚手架、跑 smoke、出文档、注入入口）。为一段前置拆两个 skill 不划算 → **并入**（操作者 2026-07-13 拍定）。
> 归位骨架已由 mqtt-console 验证有效（`mqtt-console-process-docs-prompt.md`）：**盘点 → 判归属 → 搬运（含删源）→ 补空 → 反向瘦身 → 自检**。若写成「读模板 → 填文档」的生成型，模型会重写一份而源文件原地不动 ⇒ **双写变三写**。

### 五步

**① 事实采集**——SAD 有源的**投影出来给人复核**（不直接采信，同 02 的成熟项目回填分支纪律），无源的**问**：

- 投影：栈与平台约束 ← SAD §2 · 外部依赖 ← SAD §3 · **集成测试点 ← SAD §5 contract**（E2 的锚）
- 必问（SAD 无源）：CI 平台？团队机器可用依赖（Docker / 特定 broker）？部署形态？
- **时序纪律**（同 02）：MUST 实际提问并获得回答后才允许记录；MUST NOT 预填/臆测。

**（①' 归位模式专属）素材盘点 + 判归属 + 搬运表**——按 `references/boundary-rules.md`（切线表 + 边界四问）把每节判去一个格：`environments` / `testing-strategy` / roadmap（时间轴）/ SAD（架构决策）/ 入口（最小命令+指针）/ 删除（重复复述）。**搬运表 MUST 先给人确认再落笔**——归属判定是全流程**唯一无确定性信号**的一步，人门放这里，不放末尾审文档。

**删源的三种处置**（不是一个动作，搬运表 MUST 区分）：

| 处置 | 何时 | 例（mqtt-console 接地） |
|---|---|---|
| **整体删除** | 内容全搬走，且无人引用 | `docs/modules/testing.md` |
| **部分保留 + 改写** | 只搬走一部分（如方法层），剩余留下 + 加指针 | `roadmaps/v2/testing-strategy.md`（方法搬走、时间轴留下） |
| **降为一行指针** | 内容全搬走，但**外部引用面广**，直接删会大面积悬空 | 被十几处引用的入口文档 |

**判据有确定性信号 —— `grep` 被引用面**（skill 先跑统计，带着数字进人门）：

```
引用数 = 0         → 可直接删
引用数少（可枚举） → 改掉这些引用 + 删（mqtt-console 那次改了 20 处）
引用数多 / 散      → 降为一行指针，避免大面积改动
```

**呈现纪律**：搬运表 MUST 单列一节「**以下 N 个文件将被整体删除**」，**不许只在表格某行标个 `[删除]` 混过去**（承 `grill-not-skippable`：跳过类判定别埋进长消息）。
**删后 MUST 扫残留引用**——且要扫到**代码注释里**（mqtt-console 那次，旧路径藏在 `Makefile` 注释和 7 个测试文件注释里，共 20 处）。落成 `devenv_lint` 的机械检查，不靠人记得。
**git 前置**：删源 **fail-closed 要求工作区干净**（§1.5）。

**② 泳道设计出候选 → 人拍**——按 `references/lane-patterns.md` 给候选（**不让人从零想**）。拍板产出：几条泳道 · 各测什么 · mock 边界在哪 · 各守哪条 contract（`covers`）。候选数由**真实分歧**驱动（同 02 §5.2：禁稻草人凑数；无分歧允许单方案直出但 MUST 显式声明一行）。

**③ 落地脚手架 + 真跑**——写 Makefile target / compose / CI 配置 / harness / **每泳道一条 smoke**（**归位模式：从已有测试里选一条当锚，不新写冗余的**），然后**skill 亲自跑**（不问「你跑过吗」——`verified` 的全部证据在此）：

- 依赖就绪时绿 **∧** 抽掉依赖时红（negative control，§3.2 E10）→ `verified`
- 不绿 / 依赖缺失 / negative control 不成立 → 留 `scaffolded` + **写清 `blocked_by`**

**执行边界（四条，2026-07-13 拍定）**：

1. **跑前先列命令让人过目**，不偷跑——尤其会起容器 / 占端口的。人可以说「这条跳过，标 `planned`」。
2. **每条命令有超时**（承 mqtt-console `-timeout 120s` 经验：无界超时会空耗）。超时 → `scaffolded` + `blocked_by` 如实写「超时，未确认是环境问题还是 smoke 本身挂了」。
3. **失败不重试、不 debug** ——跑一次，失败就如实记 `blocked_by`（原始报错摘要 + 修复指引），**MUST NOT 陷进 debug 循环**。**skill 的职责是「建 + 验」，不是「调通」**；一旦允许它 debug，它会在一条泳道上耗光整个 session，而这与渐进 DoD 直接矛盾——**跑不绿本来就是合法状态**。修 smoke 是下次 `continue` 的活。
4. **真硬件泳道天然不跑**（要烧板）→ 直接 `scaffolded` + 指向 `embedded-test-sop` 的手动 SOP。

**MUST NOT 替操作者装系统依赖**（改用户机器、副作用不可逆）——给 doctor 脚本 + 安装命令。

**④ 冷审 + 人门**——**MUST 由 fresh 子代理执行**（禁生成 session 自查，同 02）。按 `review-lenses.md` 取镜：

- **覆盖镜**（E2）：SAD 哪条 contract 没被任何泳道穿过？`covers` 声明是否真命中？
- **vacuous 镜**（E10）：smoke 跑绿但什么都没断言吗？删掉被测逻辑它会红吗？
- **边界镜**（E8）：架构决策漏进 env 了吗？阶段计划漏进 testing-strategy 了吗？
- **诚实镜**（E6）：`planned` 有没有被伪装成 `verified`？`blocked_by` 是真原因还是敷衍？
- **归位模式专属**：删源镜——搬运后源文件真删了吗？残留引用（含**代码注释里**的）扫干净了吗？

人门固定议程：① 泳道设计复核 ② 未 verified 泳道逐条确认（接受现状 / 现在就装依赖）③ 落地物 diff 过目（真代码进仓）④ N/A 槽逐条确认（是现状还是该有而没建）。

**⑤ 文档 + 入口 + 交棒**——渲染命令表 · 写两份真相源 · 注入 `opsx-devenv` 托管块（CLAUDE/AGENTS/README）+ `openspec/INDEX.md` · **收尾报告逐条列出未 verified 的泳道**。

---

## 6. 组件架构

### 6.1 组件映射（对称 02 §6.1）

| 组件 | 内容 | 载体 |
|---|---|---|
| ① 文档模版 | environments 十六槽（§2.1）+ testing-strategy 九槽（§2.2） | `references/environments-template.md` · `references/testing-strategy-template.md` |
| ② 生成方法 | §5 五步 + 三模式 + 时序纪律 | `SKILL.md` 主体 |
| ③ 质量判据 | E1–E11 + 拆解表（§3） | `references/quality-criteria.md`（**真相源**） |
| ④ review 工具 | 机械 + 语义 + 人门三层 | `scripts/devenv_lint.py` + `references/review-lenses.md` + 人门清单 |
| ⑤ **领域知识清单** | **泳道推导框架 + 参考实例**（②步的心脏；**非**查表式规格库）+ 切线表/归属判据（①'步） | `references/lane-patterns.md` · `references/boundary-rules.md` |

> ⑤ 与 02 的差异（**本 skill 的关键校准**）：02 说「枚举完备性不能靠模型临场回忆 ⇒ 清单固化」。本 skill **只固化到「问什么」为止**——**维度**（依赖形态四问）固化以保证推导路径可复现；**答案**（具体用什么工具/库）**交模型现场调研 + 人决策**，因为工具随生态演进、固化即腐烂，而模型的知识面本就比静态表广。详见 §6.2。

### 6.2 `lane-patterns.md`：推导框架 + 参考实例（**不是**查表式候选库）

**定位（2026-07-13 操作者校准）**：**固化「问什么」，不固化「答什么」**——泳道设计更多依赖大模型现场调研与推荐，**人做决策**；**不宜做太细太明确的限定**。

| | 固化（进 references） | 不固化（模型现场调研 + 人拍） |
|---|---|---|
| **内容** | 依赖形态四问 · 每种形态**为什么需要这个阶梯**的判据 · 「最小可用集先建哪条」的判据 | 具体**用什么工具**（进程内 broker 用哪个库？mock 用什么？容器用 testcontainers 吗？）· 各技术栈的泳道规格表 |
| **理由** | **维度稳定**（三层阶梯的道理十年不变）；且保证两次运行推导路径一致（枚举完备性） | **工具随生态演进**，固化即开始腐烂；模型的知识面本就比静态表广 |

⇒ 落回机械/语义切分线判据：**维度有确定性信号**（四问必问）；**工具选型无确定性信号**（模型调研 + 人决策）。

#### 关键设计：按**依赖形态**分格，不按语言分

按语言分格（Go 格 / Node 格 / Python 格）是**错的**——泳道结构不由语言决定，由**系统与外界的边界形态**决定。同样是 Go，连 broker 的服务与纯算法库泳道完全不同；而 Go 服务与 Java 服务连同一个 broker，泳道结构几乎一样。

**形态四问**（`covers` 之外，SAD 的第二条高价值投影：答案基本可从 **SAD §3 外边界**读出）：

1. 有无**外部有状态依赖**（broker / DB / 队列）？
2. 有无 **UI**？
3. 有无**语言桥 / 生成物契约**（绑定 / FFI / protobuf）？
4. 有无**真硬件**？

| 依赖形态 | 泳道阶梯（原理，非规格） | 参考实例 |
|---|---|---|
| **外部有状态依赖** | 假替身 → 进程内真实现 → 真实例。**为什么要中间层**：假替身证明不了「消息真穿过 TCP、真落成文件」；真实例又太重、不可移植 ⇒ 中间必须有个进程内层 | mqtt-console：hermetic / embedded / realbroker |
| **UI** | 确定性 DOM runner → 真浏览器。**真浏览器只守前者给不了的**（真 paint / 真 frame timing / 真 pointer），**刻意不重复**确定性断言 | mqtt-console：vitest / playwright |
| **语言桥 / 生成物契约** | 结构门禁（导出面 + arity）+ 形状测试（stub 下的返回值）——**两半各有归属，不可混** | mqtt-console：assert-bindings |
| **真硬件** | 主机侧单元 → 仿真 → 真板烧录 SOP（手动）。**SOP 本体引用 `embedded-test-sop`，不复述** | 04-iot-tools |
| **纯计算 / 脚本工具** | 单元 + golden；deploy 槽 N/A | 本仓（pytest） |

**核心性质：一个项目 = 多个形态叠加，泳道 = 各阶梯的并集。**

自验：mqtt-console = 外部依赖(3) + UI(2) + 语言桥(1) = **6 条泳道** —— 精确复现其真实泳道列表。模型可被已有实例证伪，不是拍脑袋分类法。

#### 每格给四样（**判据，不是规格**）

1. 泳道阶梯的**原理**（为什么这层不能并进那层）
2. **典型 flake 源 + 隔离机理**（例：进程内 broker 的锁竞争 flake → 关进一条泳道，另留真实例泳道当「免疫仲裁者」）
3. **代价**（要不要养一个真实例？值不值）
4. **最小可用集判据** ← 直接服务渐进 DoD

> **最小可用集**：每格标出**初期只建哪一条**，其余标 `planned`。例（外部依赖形态）：先建「假替身」层（零依赖、秒级、确定性最高），进程内层与真实例层留 `planned`，等真撞到 wire 层问题再推进。⇒ skill 首跑产出的是**一条能跑的泳道 + 一张明确的待建清单**，**不是六条半空脚手架**。

#### 未覆盖形态的兜底（**不编**）

没有真样本的形态（Java 服务 / 移动 app / 分布式…）→ **MUST NOT 凭空编造权威候选**。走兜底：模型按形态四问**临场推导**，产出候选并**显式标注「本形态无参考实例，系临场推导」**，同时登记 todo 请求补格。**不因无格而卡住，也不假装有权威候选。**

> 参考实例一律标注为**「实例，非规格」**——是给模型看的示范，不是给它填的模板（承 `doc-distill-from-own-protocols`：从真运行样本蒸馏，不做通用最佳实践汇编）。

### 6.3 目录草图

```
sdflow-devenv/
├─ SKILL.md                          # ② 流程编排 + 三模式分流 + 时序纪律
├─ references/
│  ├─ lane-patterns.md               # ⑤ 泳道候选库（核心，②步）
│  ├─ boundary-rules.md              # ⑤ 切线表 + 归属判据（①'步，归位模式）
│  ├─ environments-template.md       # ① 十六槽
│  ├─ testing-strategy-template.md   # ① 九槽
│  ├─ quality-criteria.md            # ③ E1–E11 真相源
│  └─ review-lenses.md               # ④ 冷审镜单（投影 2）
├─ scripts/
│  ├─ devenv_scaffold.py             # init/分流 · set-lane · render · inject · log · transition
│  ├─ devenv_lint.py                 # ④ 机械断言（投影 1）
│  └─ devenv_schema.py               # frontmatter schema
└─ tests/                            # pytest（生态纪律：改 scripts 必跑 tests）
```

### 6.4 入口注入：自己的 marker，复用 init 的算法

`sdflow-init` 的 `inject(path, start, end, content)` 用 **token 定位 + 幂等整块替换**。本 skill **复用该算法**（同款 token 定位、同款幂等语义、已知的 fence 坑），但**必须用自己的 marker**：

```
<!-- opsx-devenv:start --> ... <!-- opsx-devenv:end -->
```

**MUST NOT 写进 `opsx-init` 的区块**——`inject` 是整块替换，共用一个 marker 会让两个 skill 互相覆盖。（生态先例：`sdflow-architecture` 也自带 `sad_scaffold.py` 写 ADR/CONTEXT，不跨 skill import。）

---

## 7. 生命周期

### 7.1 泳道状态迁移表（表外一律拒绝）

| 迁移 | 命令 | 前置 |
|---|---|---|
| — → planned | `set-lane --id X --status planned` | 泳道设计拍板后 |
| planned → scaffolded | `set-lane --id X --status scaffolded --smoke <path> --blocked-by "<原因>"` | smoke 文件存在；`blocked_by` **非空** |
| scaffolded → verified | `set-lane --id X --status verified` | **双向判据**（脚本执行验证，**非模型自称**）：依赖就绪时 smoke **绿** ∧ 抽掉依赖时 smoke **红**（negative control；`deps: []` 的泳道豁免第二条）；且 `source` 行存在 |
| verified → scaffolded（回落） | `set-lane --id X --status scaffolded --blocked-by "<原因>"` | 环境变更导致失效（如依赖升级破坏） |

### 7.2 环境变更的回写

开发过程中环境变了（换 CI、加泳道、broker 升级）→ `continue` 模式重入 → 改脚手架 → 重跑 smoke → 状态回写 → 重渲染命令表。**文档永远只有当前态**（live 层纪律，同 02 §7.1）；历史归 git。

---

## 8. 设计点（2026-07-13 逐条拍定，九条讨论）

| # | 设计点 | 结论 |
|---|---|---|
| D1 | `lane-patterns` 覆盖哪几格、多深？ | ✅ **按依赖形态分格（非语言）**，v1 五格全部从真样本蒸馏；**固化「问什么」不固化「答什么」**——工具选型交模型现场调研 + 人决策；实例标注「非规格」；未覆盖形态走兜底临场推导 + 登记 todo，**MUST NOT 凭空编造权威候选**（§6.2） |
| D2 | CI 生成到什么程度？ | ✅ **门禁逻辑进 Makefile，CI 只做调用壳**——无 CI 的项目照样有完整本地门禁；CI 平台可换而门禁不变；本地与 CI 跑同一条命令（§1.4） |
| D3 | E10 vacuous 能否机械化？ | ✅ **能，且比预想多**——**negative control**（抽掉依赖必须红）把 E10 从「几乎纯语义」升为**两级机械 + 一层冷审**；变异测试太重，不做；**语义恒真**归冷审（挂 `CleanSession` 真案例当范例）（§3.2） |
| D4 | 删源要不要单独人门？ | ✅ **不单开门，但并进搬运表人门 + 显著呈现**（单列「以下 N 个文件将被删除」）；**三种处置**（整体删 / 部分改写 / 降为指针）由 **`grep` 引用面**给判据；删后残留扫描入 lint；**删源 fail-closed 要求工作区干净**（§5 ①' + §1.5） |
| D5 | monorepo / 多语言？ | ✅ **多语言是伪问题**——泳道是 `(命令,依赖,保真度,covers)` 四元组，天然异构（mqtt-console 六泳道横跨三运行时）。**monorepo：v1 单例 + 显式提示**，演进路径 `openspec/architecture/{system}/` 与 SAD **同步升**（`covers` 要锚得住，两者绑定演进才不撕裂） |
| D6 | 与 `sdflow-init` 触发词面撞车？ | ✅ description 一句话判据：**装流程规则 → init；建项目 dev/test 环境 → devenv**（§9） |
| D7 | smoke 执行边界（新增） | ✅ **跑前列命令让人过目**（不偷跑）· 每条有超时 · **失败不 debug**（职责是「建+验」不是「调通」；跑不绿是合法状态）· 真硬件不跑 → 指 `embedded-test-sop`（§5 ③） |
| D8 | 落地物归谁 owns（新增） | ✅ **skill 是追加者不是拥有者**——Makefile/CI/harness/smoke **不设托管块**（人机共有的活文件），重名 fail-closed；托管块只用于 `environments.md` 命令表 + 入口四文件；**归位模式 smoke 复用已有测试**（§1.4） |

## 9. 触发分流与模型档位

**触发分流**（写进 description）：

| 说的是 | 走 | 判据 |
|---|---|---|
| 「初始化 openspec / 铺 workflow 规则 / 装 spec 工作流」 | `sdflow-init` | 装**流程规则**，与技术栈**无关** |
| 「定测试策略 / 搭开发环境 / 建测试环境 / 配 CI / 加一条测试泳道 / 这个项目怎么测」 | **`sdflow-devenv`** | 建**项目运行环境**，**完全依赖技术栈** |
| 「分阶段 / 排期 / 里程碑」 | `sdflow-roadmap` | 时间轴 |
| 「划分子系统 / 定 contract」 | `sdflow-architecture` | 空间轴 |

一句话判据：**装流程规则 → init；建项目 dev/test 环境 → devenv。**
**前置声明**：需已 `sdflow-init`（无 `openspec/` → fail-closed）；**建议**先 `sdflow-architecture`（无 SAD → 降级可跑）。
**生态复用不重造**：真硬件泳道 → 指向 `embedded-test-sop`（它已 own 手动 SOP + 日志分析规则）。

**模型档位：全强档，无可下放的弱档步**（同 `sdflow-architecture`）。机械活（scaffold / lint / render / inject）已全脚本化、零模型；剩下的步全是判断：

- 事实采集 / 泳道候选 / 拍板编排 → 判断
- **脚手架起草** → 判断，且**质量直接决定产出可用性**：起草得烂，smoke 真跑会抓到，但 skill **不 debug**（D7）——它只会留一个 `scaffolded`，等于这次白跑
- **冷审** → 门禁判断，弱档 = **假绿放行**（承 `CLAUDE.md`：带门禁、无人逐条复核的步别用弱模型）

---

## 附录 A：被否方案记录

| # | 被否方案 | 否决理由（简记） | 日期 |
|---|---|---|---|
| A1 | **并入 `sdflow-init`**（`05` §5 的 B 候选） | `sdflow-init` 的定义是「初始化 sdflow workflow 的**运行环境**」，**不管具体项目内容**；而 environments/脚手架是项目内容。B 候选建立在对 init 职责的误解上 | 2026-07-13 |
| A2 | **纯文档编排器**（只产 environments + testing-strategy，不落脚手架） | 目标是**把环境建起来**，不只是一份文档。只出文档 = 把最难的一半（真建起来、真跑通）留给人 | 2026-07-13 |
| A3 | **从 SAD 投影生成**（`05` §5 的 D-生成腿） | 接地实测投影率仅 12%（严）/41%（宽），且能投影的恰是最不值钱的部分（一句话+指针）；真正的价值（坑/护栏/门禁表/盲区）SAD 投影率为零。**但这不否定 skill——88% 全是待决策项，正需要编排器** | 2026-07-13 |
| A4 | **一次性 fail-closed 全绿 DoD**（所有泳道必须 verified 才算完成） | 项目初期定不下所有事；本机缺依赖不是失败。改为**渐进 DoD** + 泳道三态 + `blocked_by` 强制非空（诚实是硬要求，完成度不是） | 2026-07-13 |
| A5 | **SAD 缺失 fail-closed** | 会把所有没做过 SAD 的存量项目挡在门外（而它们恰恰最需要补测试环境）。改为**显式降级 + 响亮留痕**（`sad: missing`），MUST NOT 佯装 | 2026-07-13 |
| A6 | **归位模式拆成独立 skill / 留作手跑 prompt** | 归位模式的后半段（补泳道、落脚手架、跑 smoke、出文档、注入入口）与新建**完全共用**，独有的只是前面一段「盘点+判归属+删源」。为一段前置拆两个 skill 不划算；且手跑 prompt 拿不到 lint / 冷审 / 托管注入——正是要做 skill 的四条理由 | 2026-07-13 |
| A7 | **命令表人写 + frontmatter 存状态**（双写） | 命令/出处/状态两处各写一遍必漂移。改为 frontmatter 为机械真相源、正文表格**脚本渲染**（DO-NOT-EDIT banner） | 2026-07-13 |
| A8 | **`lane-patterns` 按语言分格**（Go 格 / Node 格 / Python 格…） | 泳道结构**不由语言决定**，由**依赖形态**决定：同是 Go，连 broker 的服务与纯算法库泳道完全不同；而 Go 服务与 Java 服务连同一 broker，泳道结构几乎一样。改为**按依赖形态分格**（§6.2） | 2026-07-13 |
| A9 | **`lane-patterns` 做成查表式权威规格库**（每个技术栈一套完整泳道规格 + 工具选型） | ①**工具随生态演进**，固化即开始腐烂；②模型的知识面本就比静态表广；③操作者校准：「更多依赖大模型调研和推荐，**不宜做太细太明确的限定**，让大模型推荐、人做决策」。改为**只固化「问什么」**（维度 + 判据），答案交模型调研 + 人拍 | 2026-07-13 |
| A10 | **Makefile 设 `opsx-devenv` 托管块**（skill 拥有并整块覆盖） | Makefile 是**人机共有的活文件**——人随时会改 target 的实现，整块覆盖会吞掉人的改动。改为 **skill 只追加**、人 owns 内容；lint 只查 `source` 行存在性，不关心谁写的；重名 → fail-closed 留人裁决（§1.4） | 2026-07-13 |
| A11 | **smoke 跑不绿时 skill 负责 debug 到通** | 一旦允许 debug，skill 会在一条泳道上耗光整个 session，与**渐进 DoD 直接矛盾**——跑不绿本来就是合法状态。skill 的职责是**「建 + 验」不是「调通」**；失败如实记 `blocked_by`，修复是下次 `continue` 的活（§5 ③ / D7） | 2026-07-13 |
| A12 | **vacuous 检测靠变异测试**（删掉被测逻辑看 smoke 红不红） | 太重（要改代码 + 跑两遍全量）。改为 **negative control**——抽掉**依赖**（不启 broker/容器）看 smoke 红不红：同样是「能不能因缺失而红」的证据，但**近乎免费**（不改代码、失败很快）（§3.2 E10） | 2026-07-13 |
