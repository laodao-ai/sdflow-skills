# add-sdflow-devenv

> 设计源：`docs/sad/07-devenv-skill-design.md` · 接地证据：`docs/sad/06-process-axis-grounding-receipt.md`（mqtt-console 实测）
> **本文档已按 round-2 设计门（2026-07-13）重写**——前一版围绕 negative control 建立的一整套主张已作废，见 `design.md` ADR-0/ADR-4。

## Why

技术架构定了之后，**把项目的开发/测试环境真正建起来**这件事在生态里无 skill 覆盖：`sdflow-architecture` 的交棒止于「过程轴文档指路（指出不代写）」，下游是空的；`sdflow-init` 铺的是 **workflow 的运行环境**（规则 bundle），按定义不管项目内容。于是「定测试策略 → 落 Makefile/CI/harness → 跑通 → 出真相源文档」全靠人手搓。

**核心承诺（操作者定调）**：**不管什么项目，跑完这个 skill 都能拿到一份完整的测试与验证策略框架**——单元 / 集成 / e2e 三层，每层交代清楚「本项目怎么实现 · 测试规范 · 方法与流程 · 要配什么工具脚本 · 状态」。**做不了的写「不适用 + 后果」，要人做的写「人怎么做」。一层都不许留白。** 这个框架**后续可迭代调整**，不是一次定死。

### 证据分层（诚实版）

| # | 现象 | 证据强度 |
|---|---|---|
| 1 | **散落双写** —— 同一份测试策略存在 3 处、env 内容存在 2 处 | ✅ **实测**（mqtt-console，`06`） |
| 2 | **无门禁** —— `assert-bindings` 这类检查无任何自动触发点，全靠人记得跑 | ✅ **实测**（`06 §2.3`） |
| 3 | **命令虚构** —— 纯文档型 prompt 为对齐模板范式而编造不存在的 target | ⚠️ **预测，未观测**。归位场景的实测结果是**零虚构**（`06:44`：「Makefile 四 target 行号全中，零虚构」）。虚构风险属 **greenfield 模式的推断**，而 greenfield **零样本**——上游试点将首次验证它 |

> 接地镜（round-2）已核验：本表与 `06` 一致，**无残留伪证据**。

### 天花板声明（MUST 如实记）

`docs/sad/05` 曾拍板「D（独立 skill）不立」，其候选集把 skill 误当「生成器」（于是一证伪「从 SAD 投影只有 12%」就否掉了它），且 B 候选建立在对 `sdflow-init` 职责的误解上——**这两条推翻成立**。

但**原推论「那 88% 全是待决策项」是错的**：`06 §4.2` 已把二分改为**三分**——SAD 投影 / **构建配置投影**（各层执行命令 · 工具链版本 · 配置项默认值，**机械可读**）/ 纯人写。**88% 里有一大块是机械可抽的。**

而真正的纯人写部分——**常见坑 · 护栏 · mock 边界 · 已知盲区**——来源是**踩坑史 / 决策史 / 测试哲学**，**day-0 根本问不出来**（坑还没踩、flake 还没暴露）。而 `06 §1.1` 恰恰认定：两份文档的**最高价值就是这些**。

⇒ **诚实的天花板**：greenfield 首跑，本 skill 能产出的是「**一份三层测试框架 + 一个可跑的 Makefile + 一张泳道表 + 一张明确的待建清单**」，**不包含** `06` 认定的全部价值。**坑与护栏只能随时间收割**（本 change 不做 harvest loop，登记为 Q-4）。

**在这个天花板之上，skill 仍然立得住**——它交付的是**手搓拿不到的四样**：

1. **三层框架无一层留白**——手搓 prompt 不会强制你回答"e2e 怎么办"，而这个 skill 会（不适用也得写后果）
2. **落地物真的被执行过**（而非"文档说它能跑"）——或如实标注"这层只能人工验证，人按 X 步骤做"
3. **泳道状态机械可查**（而非散落在人脑里）
4. **lint 有触发点**（挂 `sdflow-maintain`）——**手搓 prompt 最缺的那一环**（也是本 proposal 原先自己也缺的，dogfood 自指坑）

## What Changes

- **新增 skill `sdflow-devenv`**——过程轴编排器（**非**生成器），五步流水线 + 三模式分流（新建 / 归位 / continue）。
- **⭐ 总则：无法明确确定的问题 → 模型研究提方案 → 人确认**〔round-2 · ADR-0〕。机械层**只保证「过程完整」与「诚实」**，**MUST NOT 试图替人判断质量**，**MUST NOT 硬凑假机械**（枚举 / dispatch 表 / 白名单包装成"脚本判定"）。
- **⭐ 测试三层框架，无一层可留白**〔round-2 · 操作者定调〕：`testing-strategy.md` MUST 覆盖 **单元 / 集成 / e2e**，每层 MUST 答五槽（怎么实现 · 规范 · 方法流程 · 要配什么工具脚本 · 状态）。状态三态各有强制附带项：`不适用` ⇒ **必须记后果**；`人工` ⇒ **必须写用户怎么做**；`已实现` ⇒ **必须有对应泳道**。**这三条是机械可查的**（槽在不在、后果段有没有、lane id 对不对得上）。
- **⭐ 验证方法由模型研究提出、人拍板**〔round-2 · ADR-4，**取代前一版的 negative control ⟺ 定义**〕：spec **只定证据的形状**（`method` / `executor` / `evidence`），**不枚举验证方法**。**「无法验证」不是合法状态——人工测试也是方法**，区别只在 `executor: script | human`。删掉了 `isolate` / `expected-failure predicate` / `kind → 策略 dispatch` / runner 白名单**一整片复杂度**。
- **证据只能由执行者本人写**〔ADR-5〕：`set-lane --status verified` **一律拒绝（exit 5）**。`executor: script` → **`verify-lane`**（脚本自己 fork 执行）；`executor: human` → **`confirm-lane`**（人门写，模型 MUST NOT 代填）。原设计的子命令里**没有一个会执行 smoke**，所谓「脚本验证」实为「模型自称、脚本盖章」。
- **泳道三态 + 渐进 DoD + 框架可迭代**：`planned → scaffolded → verified`，不强制全绿；诚实是硬要求。
- **lint 的触发点**：`devenv_lint` **挂进 `sdflow-maintain` 的扫描**。**没有触发点的 lint = 没有 lint**。**诚实边界**：maintain 是**人主动跑**的 ⇒ 这是「更响的提醒」而非硬门禁，MUST NOT 佯装硬拦截。
- **落地物（真代码，直写落盘）**：Makefile target（**门禁逻辑在此**）· CI 配置（**只生成独立新文件**）· harness · smoke · doctor。skill 是**追加者不是拥有者**——不设托管块，**重名 fail-closed（只判名字，不判语义）**。**v1 入口只支持行文本型**；`package.json` 型项目走 **Makefile 薄壳**。
- **数据落 JSON 侧文件**：`.devenv-lanes.json`（标准库、零依赖）。frontmatter 只留 `sad` / `mode` / `schema_version` 三个扁平标量；**`schema_version` 高于本实现 ⇒ fail-closed**。
- **③-pre 人门（执行之前）**〔ADR-5 时序〕：**模型生成的代码，在被执行之前必须先过人眼**。否决 ⇒ 按 **touched-files 事务清单**逐项回退（新写的→删，既有的→复原）——**MUST NOT** 用 `git checkout --`（对 untracked 无效）或无路径限定的 `git clean`（会误删操作者的文件）。
- **⭐ 跨 skill 面治**（非可选，承基准 3）：**三 skill 共用 `openspec/` 写域锁**——`devenv_scaffold` 用新锁 · `init.py` 的 `inject()` **补锁 + 原子写**（现为裸 `open(w)`）· **`sad_scaffold.py` 迁到共用锁 + 补 owner 核对**（现用 `.sad-scaffold.lock`，释放不核 owner）· `atomic_write` **加 mode 参数**（现硬编码 `0o644` ⇒ 生成的 doctor 脚本落盘即不可执行）。
- **修改 `sdflow-architecture`**：交棒话术指向 `/sdflow-devenv`。
- **修改 `sdflow-maintain`**：扫描面增加 devenv 健康度。
- **双向触发分流**：`sdflow-devenv` 加「装流程规则 → init」判据句，**`sdflow-init` 同时加反向排除句**（「建 dev/test 环境 → devenv」）——词面碰撞是双向的，只补一边不解决路由。
- **BREAKING**：无。纯增量（消费仓不跑本 skill 则完全无感）。

## Success Metrics

| # | 指标 | 判定 |
|---|---|---|
| **SM-1** | **⭐ 三层框架无留白**：任一项目跑完，`testing-strategy.md` 的 unit/integration/e2e × 五槽**全部有内容**；`不适用` 有后果、`人工` 有步骤、`已实现` 有对应泳道 | lint 断言 + pytest |
| SM-2 | **归位模式回归**：在 **checkin 的 brownfield fixture** 上跑归位，删源集与搬运结果**确定性断言** | pytest（fixture 在 `tests/fixtures/brownfield/`） |
| SM-3 | **新建模式跑通**：绿地项目跑通五步，产出完整三层框架 + **至少一条 `verified` 泳道**（`script` 或 `human` 通道均可）+ 待建清单 | 执行证据落盘 |
| SM-4 | **lint 有触发点且真拦得住**：`devenv_lint` **在 `sdflow-maintain` 扫描中被自动调用**，并在一次**真实回归**上拦下（人改了 Makefile 使 `method_digest` 失配） | maintain 集成测试 |
| SM-5 | **诚实性**：`scaffolded` ⇒ `blocked_by` 非空且含可辨认修复指引；`verified` ⇒ **执行证据齐全**且 `blocked_by` **为空**；`verification.method` **不得为空** | lint 断言 + pytest |
| SM-6 | **零双写 + 无恒真断言**：`source` 用 **digest 锚**（非行号）；造「行还在、内容变了」的坏输入必须被抓 | pytest |
| SM-7 | **产品有效性**：绿地项目从 clean checkout 到**首条测试跑通**的耗时 · 所需**人工回答数** · 生成 diff 被操作者**保留的比例** | 上游试点实测记录 |
| SM-8 | **不伤害**：验证若改变了机器状态，异常中断（超时 / SIGINT / **SIGKILL 后下次启动**）下**恢复仍执行**；**MUST NOT 停止非本次运行启动的依赖**（`owned_by` 派生为 `operator` → 拒绝）；子进程**不继承 agent 完整环境** | pytest（注入异常 → 断言恢复被调用 / 断言 env allowlist） |

> **SM-3 的诚实边界**：真正的 **greenfield 零代码**项目（SAD 刚写完，一行代码没有）可能**结构性达不成**"≥1 条 verified"——没代码就没有能跑绿的东西。此时达标线为：**三层框架完整 + 泳道表 + 待建清单**，`verified` 数可为 0。**MUST NOT** 为了凑一个 `verified` 而造一个没有实际意义的空跑测试。

## Non-Goals

- **⭐ 替人判断验证方法有没有效**〔ADR-0〕——skill 保证「有方法 · 执行了 · 证据是执行者写的 · 状态没撒谎」，**不保证方法本身有效**。质量由模型能力 + 人判断 + 冷审保证。
- **堵住 `assert True`**——证明"跟依赖说过话"≠证明"断言有效"。要堵它只有**变异测试**（太重）⇒ **机械层堵不死，诚实划归冷审语义镜**。
- **业务测试用例**——本 skill 只建 harness + 每泳道一条 smoke；业务回归网归各 change。
- **生产运维 runbook**（on-call / SLO / 告警）。
- **替用户安装系统依赖**（`brew install` / `docker pull`）——只给 doctor 脚本 + 命令，副作用不可逆。
- **smoke 跑不绿时 debug 到通**——职责是「建 + 验」不是「调通」；跑不绿是合法状态。
- **monorepo 多系统**——v1 单例 + 显式提示。
- **时间轴排期 / 里程碑** → `sdflow-roadmap`。
- **从 SAD 自动生成文档**——投影率仅 12%，且投影出的是最不值钱的部分。
- **JSON / YAML 落地物的结构化编辑**——v1 **只支持行文本型入口**。CI 配置**只生成独立新文件**，MUST NOT 往用户既有 workflow 插 step；`package.json` 型项目走 **Makefile 薄壳**。
- **Windows 的进程树杀灭**〔ADR-11〕——`taskkill /T /F` 零依赖可行，但**无 Windows 环境实测** ⇒ **MUST NOT 写一段从未在该平台执行过的代码并声称它能杀进程树**。非 POSIX ⇒ `verify-lane` refuse，走 `executor: human`。挂 Q-5。
- **坑 / 护栏 / 盲区的 harvest loop**——这是本 skill **最高价值的演进方向**，但**本 change 不做**，登记为 Q-4。

## 需求优先级〔TG-19〕

| P | 需求 | 理由 |
|---|---|---|
| **P0** | 五步编排 + 三模式分流 · **测试三层框架（五槽 + 三态强制附带项）** · **验证方法（`method`/`executor`/`evidence`）** · 泳道三态 + JSON schema · 落地物追加 · **`verify-lane` + `confirm-lane`** · **③-pre 人门 + touched-files 回退** · `devenv_lint` 诚实检查 · 两份真相源渲染 | 缺任一则 skill 不成立 |
| **P1** | `opsx-devenv` 托管块注入（fence-aware）+ INDEX · `lane-patterns` / `verification-patterns` · 冷审镜单（含**验证方法镜** + **分类镜**）· 归位模式删源三处置 + 护栏 · **跨 skill 写域锁（三条腿）** · **最小环境 allowlist** · **cleanup ledger 落盘** | 可用但不完整；并发安全与不伤害**不可后补** |
| **P2** | doctor 脚本生成 · CI 调用壳生成 · `sdflow-architecture` 交棒话术改写 · **双向分流句** · 未覆盖形态的 todo 登记 | 增益项，可迭代 |

## 利益相关方与外部依赖〔TG-20〕

| 方 | 影响 |
|---|---|
| **消费仓** | 新增 `openspec/architecture/{environments,testing-strategy,devenv-log}.md` + 落地物 + `opsx-devenv` 托管块；**不跑本 skill 则完全无感** |
| **`sdflow-architecture`** | 交棒话术 + description 路由句变更（MODIFIED capability）· **`sad_scaffold.py` 迁共用锁 + `atomic_write` 加 mode 参数**（面治） |
| **`sdflow-init`** | **要改**（面治，非可选）：`inject()` 补锁 + 原子写；description 加**反向排除句** |
| **`sdflow-maintain`** | 扫描面增加 devenv 健康度（**新增代码**——现为四类硬编码扫描，**无插件挂点**） |
| **`embedded-test-sop`** | 真硬件泳道**指向它**作为 `executor: human` 的验证方法，不重造手动 SOP |
| **外部命令**（`make` / `go test` / `npm` / `docker` / `git`） | skill 执行它们；失败模式表见 design〔TG-08〕 |

## ⭐ 实现前置（设计门 Q2 拍定，MUST 先于 tasks 第 1 组）

**先跑 `sdflow-architecture` 的首个真实试点**——用本来要做 SM-3 的**同一个绿地项目**。

`add-sdflow-architecture` 归档于 2026-07-12，其 hand-off 明写「**首个真实试点（最高优先）**……SM-4 证伪钟起点」——**该试点未做**。而 devenv 对 SAD 的依赖是硬的（依赖形态四问 ← SAD §3 外边界；`covers` 对账 ← SAD §5 contract）。

**一个项目的成本，同时给两个 skill 去风险**：

1. 验证**真实 SAD 的 §3/§5 能否长出 devenv 需要的锚**
2. 验证 **greenfield 的「命令虚构」风险是否真实存在**（Why 段的唯一未观测项）
3. 验证 **`lane-patterns` 五格在第二个样本上是否还成立**（A-2 的 n=1 过拟合）
4. **⭐ 验证「模型能不能为三层各自提出像样的验证方法」**——这是 ADR-0/ADR-4 整条路线的前提。若模型提不出、或提出的方法经不起人门推敲，则本 skill 的核心承诺落空

## 开放问题〔TG-21〕

| # | 问题 | 负责人 / 截止 |
|---|---|---|
| Q-1 | `lane-patterns` / `verification-patterns` 未覆盖形态何时补格 | 操作者 / 首个撞上该形态的项目 |
| Q-2 | monorepo 多系统演进——需 SAD 先支持多系统 | 操作者 / 首个 monorepo 消费仓 |
| Q-3 | `devenv_lint` 的「入口复述检测」是弱启发，阈值待接地校准 | 实现期 / 首跑后 |
| **Q-4** | **harvest loop**（从 buglist / code-review 报告机械喂坑与盲区进 testing-strategy）——`06` 认定这是最高价值来源，而 day-0 编排器**拿不到它** | 操作者 / v2 |
| **Q-5** | Windows 的 `taskkill /T /F` 分支——零依赖可行但**无环境实测**。何时补？ | 操作者 / 有 Windows 环境时 |
| **Q-6** | `sdflow-maintain` 是**人主动跑**的 ⇒ lint 触发是「提醒」非「硬门禁」。是否需要在 `ship_gate` 加硬拦截？ | 操作者 / 首个僵尸 scaffolded 出现时 |
| **Q-7** | SAD 处于 `draft` 态时 contract 随时改名 ⇒ `covers` 锚可能悄悄失真。`sad` 字段是否需要第三态？ | v2 / 与 SAD 生命周期绑定 |

## 假设〔TG-22〕

| # | 假设 | 失效影响 |
|---|---|---|
| ~~A-1~~ | ~~negative control 对所有依赖类型都成立~~ | ❌ **已证伪**（三条独立理由，见 ADR-4）——只证"耦合"不证"断言有效" · 对 testcontainers 永久误判 · **在本 change 自己的接地样本（mqtt-console）上结构性失效**（连接参数与依赖启停打包进同一条 recipe 的字面文本，对任何外部覆盖免疫）。⇒ **降为 `references/` 的参考实例**，不再是 `verified` 的定义 |
| **A-2** | **依赖形态五格**能覆盖多数项目 | ⚠️ **已削弱**——五格中三格全来自 mqtt-console，拿同一样本「自验」是**过拟合不是证伪**。上游试点将在**第二个样本**上首次检验 |
| ~~A-3~~ | ~~渐进 DoD 不会导致永久 `scaffolded`~~ | ❌ **已证伪**——原缓解依赖一个**没有触发点的 lint**。⇒ 挂进 `sdflow-maintain`。**残余**：maintain 人主动跑 ⇒ 仍是「提醒」非硬门禁，显式登记 |
| **A-4** | **两个 session 并发跑会撞车** | 已知**必然**发生。⇒ **`openspec/` 写域单一锁，三 skill 共用**（前一版只改了 `init.py`，**漏了 `sad_scaffold`**——"三 skill 共锁"只有两条腿） |
| **A-5** | 消费仓已有的 Makefile target **语义可被读懂并登记** | 若语义模糊 → `covers` 对账失真。缓解：登记结果进搬运表人门；**模糊者宁可标 `planned` 不强行登记**。**脚本只判名字碰撞，语义归模型+人** |
| **A-6** | **锁参数适用于本 skill 的临界区** | ❌ **已证伪**——`sad_scaffold` 的锁是为**亚秒级**操作调的（`LOCK_STALE_SEC = 120`），而验证可跑数分钟：锁若跨验证持有 ⇒ **活锁被判残留锁** ⇒ 提示用户删锁 ⇒ 两 session 同写。⇒ 锁**短持有** + **CAS 覆盖全部验证输入快照**（不只 `status`——否则旧验证能给新命令盖章） |
| **A-7** | **「不外发」⇒ 无 secret 出境面** | ❌ **已证伪**——子进程继承 agent 的**完整环境变量**，且被执行的 recipe 或其下游脚本**可把凭证写进文件、发往网络**——**事后打码管不着**。⇒ **主护栏 = 最小环境 allowlist**（不继承完整环境）；落盘输出的截断 + 打码为 **best-effort，非保证**，MUST NOT 用绝对语气佯装 |
| **A-8（新增）** | **模型能为三层各自提出像样的验证方法** | ⚠️ **未验证——这是 ADR-0/ADR-4 整条路线的前提**。若模型提不出、或提出的方法经不起人门推敲 ⇒ 核心承诺落空。**上游试点第 4 条专测此项** |

## Capabilities

### New Capabilities
- `devenv-provisioning`: 开发/测试环境搭建编排器——五步流水线 · 三模式分流 · **测试三层框架（无一层留白）** · **验证方法（模型提 + 人拍 + 证据只能由执行者写）** · 泳道三态与渐进 DoD · 落地物追加（追加者非拥有者）· **③-pre 人门 + touched-files 回退** · 机械 lint（**只查诚实，不查质量**）· 两份真相源渲染与入口托管注入 · **跨 skill 写域锁** · **最小环境 allowlist + cleanup ledger 落盘**。

### Modified Capabilities
- `architecture-design`: 交棒后的过程轴下游**从「指出不代写 + 给模板路径」改为指向 `/sdflow-devenv`**；description 增加过程轴分流句。
- `maintain-scan`: 扫描面**增加 devenv 健康度**——`sdflow-maintain` SHALL 调用 `devenv_lint`。**这是 `devenv_lint` 唯一的触发点**。

## Impact

**本仓**：

- 新目录 `sdflow-devenv/`（`SKILL.md` + `scripts/`×3 + `references/`×7 + `tests/`）
- 改 `sdflow-architecture/`（交棒话术 + description + **`sad_scaffold.py` 迁锁 + `atomic_write` 加 mode**）
- 改 `sdflow-init/`（**`inject()` 补锁 + 原子写** + description **反向排除句**）
- 改 `sdflow-maintain/`（**新增** devenv 健康度扫描）
- 改 `README.md`（Skills 列表）；**`setup.sh` 无需改**
- 新增 pytest（本仓纪律：改 `scripts/` 必跑 `tests/`）

**消费仓**（跑本 skill 后）：`openspec/architecture/{environments,testing-strategy,devenv-log}.md` · `.devenv-lanes.json` · `.devenv-cleanup.ledger` · 落地物 · `opsx-devenv` 托管块 · `openspec/INDEX.md` 条目。

**技术栈标注**：Markdown + Python。**TG-26（并发）与 TG-08（外部依赖）命中**。

## Compliance

- **skill 目录约定**：`SKILL.md` + `scripts/` + `references/` + `tests/`；`setup.sh` 自动装载。
- **bundle 权威源纪律**：本 change **不改** `sdflow-init/assets/workflow/`，无需 `sdflow-init update` 回灌。
- **托管区块纪律**：`opsx-devenv` 为**新 marker token**，**MUST NOT** 写入 `opsx-init` 区块。
- **机械化优先 + 诚实边界**（基准 1 · **ADR-0**）：能机械化的一律机械化；**机械够不着的诚实划归语义层，MUST NOT 硬凑假机械**。
- **面治优先于点补**（基准 3）：`init.py` 补锁 · `sad_scaffold` 迁锁 + mode 参数 · 双向分流句——一次扫全。
- **目标态导向**（基准 2）：三层框架锚目标态，**MUST NOT** 以「现存项目大多只有单元测试」论证「e2e 可省」——省了就写 `不适用 + 后果`。
- **审查顺序**：`/sdflow-spec-review`（设计门）→ 实现 → `/review` → push → `/sdflow-code-review` → `/sdflow-done`。
- **HR-TG**：命中 TG-08 / TG-09 / TG-17 / TG-26 → spec-review **单开领域 cross-model**。
