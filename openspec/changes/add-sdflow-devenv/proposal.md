# add-sdflow-devenv

> 设计源：`docs/sad/07-devenv-skill-design.md` · 接地证据：`docs/sad/06-process-axis-grounding-receipt.md`（mqtt-console 实测）
> **本文档已按第三轮设计门（2026-07-13，14 镜 / 100+ findings）重写**。根因诊断：前两版把「辅助工具」设计成了「审计系统」——几乎每条致命 finding 都是「你这个机械保证有洞」，**没有一条**是「这个 skill 不好用」。新总则见下：机械层**防漏，不防伪**（`07` §0.0，真相源）。围绕 negative control / `owned_by` 派生 / cleanup ledger 自动记账 / `confirm-lane` 调用者身份保证建立的整套「防伪」机制**已删除**，见 `design.md` ADR-0/ADR-4/ADR-5，`07` 附录 A13–A20。

## Why

技术架构定了之后，**把项目的开发/测试环境真正建起来**这件事在生态里无 skill 覆盖：`sdflow-architecture` 的交棒止于「过程轴文档指路（指出不代写）」，下游是空的；`sdflow-init` 铺的是 **workflow 的运行环境**（规则 bundle），按定义不管项目内容。于是「定测试策略 → 落 Makefile/CI/harness → 跑通 → 出真相源文档」全靠人手搓。

**核心承诺（操作者定调）**：**不管什么项目，跑完这个 skill 都能拿到一份测试与验证的策略框架**——单元 / 集成 / e2e 三层，**一层不许留白**。做不了的写「不适用 + 后果」，要人做的写「人怎么做」。这个框架**可迭代**，不是一次定死，不是首跑就要求全绿。

### ⭐ 总则：机械层防漏，不防伪〔三轮 spec-review 后拍定 · 真相源 `07` §0.0〕

**skill 的目标是「有了这些过程，也有了人认可的结果」——不是「证明模型没有撒谎」。** 使用 skill 的就是那个人自己——**他没有动机骗自己**。故机械层只保证**防漏（完整性：该有的有没有）**，**不保证防伪（真实性：说的是不是真的）**。

**写下任何一条「MUST 机械保证 X」之前，先问「这个保证的信号从哪来」。** 答不上来 ⇒ 删掉它，或诚实划归语义层（人门 + 冷审）。**假机械比诚实的语义层更危险**——它让人以为有防线。前两版正是在这条总则之下反复复发：第三轮甚至是在专门为治此病而写的 ADR-0 之下，又造了七处新的假机械——根因是目标错位，不是执行不力。

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

⇒ **诚实的天花板**：**greenfield 首跑，本 skill 能产出的是「一份三层测试框架 + 一个可跑的 Makefile + 一张泳道表 + 一张待建清单」**，**不包含** `06` 认定的全部价值。**坑与护栏只能随时间收割**（本 change 不做 harvest loop，登记为 Q-4）。

**在这个天花板之上，skill 仍然立得住**——它交付的是**手搓拿不到的四样**：

1. **三层框架无一层留白**——手搓 prompt 不会强制你回答"e2e 怎么办"，而这个 skill 会（不适用也得写后果）
2. **落地物真的被执行过**（而非"文档说它能跑"）——或如实标注"这层只能人工验证，人按 X 步骤做"
3. **泳道状态机械可查**（而非散落在人脑里）
4. **lint 有触发点**（挂 `sdflow-maintain`）——**手搓 prompt 最缺的那一环**（也是本 proposal 原先自己也缺的，dogfood 自指坑）

## What Changes

- **新增 skill `sdflow-devenv`**——过程轴编排器（**非**生成器），五步流水线 + 三模式分流（新建 / 归位 / continue）。
- **⭐ 总则：机械层防漏，不防伪**〔`07` §0.0〕。**写下任何一条「MUST 机械保证 X」之前，先问「这个保证的信号从哪来」**——答不上来就删或划归语义层，**MUST NOT 硬凑假机械**（枚举 / dispatch 表 / 白名单 / 派生自不存在的锚）。
- **⭐ 测试三层框架（`.devenv-strategy.json`），无一层可留白**：`unit` / `integration` / `e2e` 各答五槽（`how`/`convention`/`process`/`tooling`/`status`），**MUST 落 JSON**——`testing-strategy.md` 由脚本从 JSON 渲染（`DO NOT EDIT` banner），**MUST NOT 让 lint 解析自由格式 Markdown**（本仓前科：手搓解析器屡次假阳）。三态各有强制附带项：`implemented` ⇒ `lane_ids` 存在且对应泳道非 `planned`；`not-applicable` ⇒ `reason` + `consequence` 非占位（豁免其余四槽）；`manual` ⇒ `why_not_scriptable` + `human_steps` 非占位。
- **⭐ 验证方法由模型研究提出、人拍板**〔ADR-4，取代前一版的 negative control ⟺ 定义〕：`executor: script` 是**默认、首选**；`human` 是**降级路径**，需写明为何程序跑不了。**MUST 分清两种「跑不了」**：方法本身没法程序跑（→ `executor: human` + `why_not_scriptable`）vs 能跑但条件不具备（→ `scaffolded` + `blocked_by`，下次 continue 再跑）——前一版把这两者混成一条 `human` 通道，「本机缺个依赖」也被标成「只能人工验证」，那是在撒谎。**「无法验证」不是合法状态**——人工测试也是验证方法，不设 `n/a` 通道。
- **证据只能由执行者本人写**〔ADR-5〕：`set-lane --status verified` **一律拒绝**。`executor: script` → **`verify-lane`**（脚本自己 fork 执行，捕获 exit code / 时长 / digest）；`executor: human` → **`confirm-lane`**（人门写）。**`confirm-lane` 产出的绿如实标 `human-attested`**（人说的，不是脚本验的）——**MUST NOT 声称脚本保证了执行者本人写入**：agent session 里模型是唯一的命令执行者，那条 MUST 按字面永远为假，**且本就不必防**（总则）。
- **`verified` 的语义钉死为 `verified-at <sha>`**——一次历史执行的记录，**不是当前状态的绿灯**：`method_digest` 不覆盖被测实现（覆盖它需要跨语言 import 图静态分析，零依赖做不到），业务代码一改，那个绿灯就在说谎，故渲染时 MUST 带 commit 锚。
- **路径 containment 校验**：`source.file` / `smoke` / `fixtures[]` / 外部配置文件 / touched-files 清单全是模型填的自由文本，**MUST 经统一 containment helper**（拒绝绝对路径 / `..` / symlink 祖先 / 仓外 realpath）后才能读/写/删。
- **touched-files 事务 journal**（`.devenv-txn.json`）：写入任何落地物之前先原子落盘，记录**原完整内容**（非仅 digest——digest 恢复不了文件）+ 原 mode。③-pre 被否决 ⇒ 按 journal 精确回退（新写的删、既有的用原内容复原），**MUST NOT** 用 `git checkout --`（对 untracked 无效）或无路径限定的 `git clean`（会误删操作者未 add 的其他文件）。崩溃后下次启动检测未完成 journal 并提供回退/继续选择。
- **digest 按文件类型分治**：Makefile recipe 剥空白但保留 tab 缩进；YAML/JSON/lockfile 及其余一律对原始字节 sha256、不做任何规范化——**YAML 的行首缩进本身就是语义**，套用 Makefile 的规范化规则会让缩进不同、语义不同的 YAML 算出同一 digest（与「行号锚」同构的假绿）。
- **⭐ 跨 skill 面治**（承基准 3，非可选）：三 skill 共用 `openspec/` 写域锁（`openspec/.sdflow-write.lock`）——`devenv_scaffold.py` 用新锁；**`sdflow-init/scripts/init.py` 的 `inject()` 补锁 + 原子写**（现为裸 `open(w)` 全量覆写、无锁无原子写）；**`sdflow-architecture/scripts/sad_scaffold.py` 从 `.sad-scaffold.lock` 迁到共用锁，并补 owner 记录 + 释放前核对**（现 `_acquire_lock` **从来没写入过 owner 信息**，`_release_lock` 也不核对）；**`atomic_write` 加 `mode` 参数**（现硬编码 `0o644`，复用它写 doctor 脚本会落盘即不可执行）。锁**短持有、MUST NOT 跨验证执行持有**，状态写入用 CAS、快照覆盖整条不可变 verification plan（`status`/`executor`/`kind`/`method`/`source`/`smoke`/`fixtures`/`env`/`deps`，不只 `status`）。加双向分流句（`sdflow-devenv` ⇄ `sdflow-init`）。
- **泳道三态 + 渐进 DoD + 框架可迭代**：`planned → scaffolded → verified`，不强制全绿；诚实是硬要求（`scaffolded` MUST 带非空且非占位的 `blocked_by`）。
- **lint 的触发点**：`devenv_lint` **挂进 `sdflow-maintain` 的扫描**。**没有触发点的 lint = 没有 lint**（本 change 立项理由之一，前两版的 lint 自己也没有触发点——dogfood 自指坑）。**诚实边界**：maintain 是**人主动跑**的 ⇒ 这是「更响的提醒」而非硬门禁，MUST NOT 佯装硬拦截。
- **落地物（真代码，直写落盘）**：Makefile target（门禁逻辑在此）· CI 配置（只生成独立新文件）· harness · smoke · doctor。skill 是**追加者不是拥有者**——不设托管块，重名 fail-closed（只判名字，不判语义）。v1 入口只支持行文本型；`package.json` 型项目走 Makefile 薄壳。
- **数据落两份 JSON 侧文件**（`openspec/architecture/`，均标准库 `json`、零依赖）：`.devenv-lanes.json`（泳道）· `.devenv-strategy.json`（测试三层框架）。frontmatter 只留 `sad` / `mode` / `schema_version` 三个扁平标量；`schema_version` 高于本实现 ⇒ fail-closed。
- **③-pre 人门（执行之前）**〔ADR-5 时序〕：模型生成的代码 + 验证方法 + 全部无独立信号的声明清单（`kind`/`layer`/`executor`/`fixtures`/`env`），在被执行之前必须先过人眼；否决 ⇒ 按 touched-files journal 精确回退。
- **修改 `sdflow-architecture`**：交棒话术指向 `/sdflow-devenv`。
- **修改 `sdflow-maintain`**：扫描面增加 devenv 健康度。
- **双向触发分流**：`sdflow-devenv` 加「装流程规则 → init」判据句，`sdflow-init` 同时加反向排除句（「建 dev/test 环境 → devenv」）——词面碰撞是双向的，只补一边不解决路由。
- **BREAKING**：无。纯增量（消费仓不跑本 skill 则完全无感）。

## Success Metrics

| # | 指标 | 判定 |
|---|---|---|
| **SM-1** | **⭐ 三层框架无留白**：任一项目跑完，`.devenv-strategy.json` 的 unit/integration/e2e 三层各自五槽（或 `not-applicable` 的豁免槽）**全部有内容**；`not-applicable` 有 `consequence`、`manual` 有 `why_not_scriptable`+`human_steps`、`implemented` 有对应泳道 | lint 断言 |
| SM-2 | **归位模式回归**：在 **checkin 的 brownfield fixture** 上跑归位，删源集与搬运结果**确定性断言** | pytest（fixture 在 `tests/fixtures/brownfield/`） |
| SM-3 | **新建模式跑通**：绿地项目跑通五步，产出完整三层框架 + 泳道表 + 待建清单。**诚实边界：零代码 greenfield 的 `verified` 数可为 0**，达标线 = 三层框架完整 + 泳道表 + 待建清单，**MUST NOT 为凑 `verified` 造空跑测试** | 执行证据落盘 |
| SM-4 | **lint 有触发点且真拦得住**：`devenv_lint` **在 `sdflow-maintain` 扫描中被自动调用**，并在一次**真实回归**上拦下（人改了 Makefile 使 `method_digest` 失配） | maintain 集成测试 |
| SM-5 | **诚实性**：`verification.method`/`strength` 非空；`verified` ⇒ 证据（`evidence`）齐全**且 `blocked_by` 为空**；`scaffolded` ⇒ `blocked_by` 非空且**含可辨认修复指引**（非纯占位符） | lint 断言 + pytest |
| SM-6 | **无恒真断言**：`source` 出处锚用**内容 digest**（非行号），造「行还在、内容变了」的坏输入必须被抓；**YAML 缩进变化被抓**（digest 按文件类型分治，不对 YAML 做空白规范化） | pytest |
| SM-7 | **产品有效性**：绿地项目从 clean checkout 到**首条测试跑通**的耗时 · 所需**人工回答数** · 生成 diff 被操作者**保留的比例** | 上游试点实测记录 |
| SM-8 | **不伤害**：**注意——不再是「抽离的依赖 100% 恢复」**（skill 不再启停依赖，见 R1）：超时/中断后**如实报告可能的孤儿资源**（容器/端口占用），**MUST NOT 声称已清理**；子进程 env **不含 allowlist 外的变量**（含凭证不被继承）；路径 containment **拒绝仓外读/写/删** | pytest（注入超时 → 断言报告文案 / 断言 env allowlist / 断言 containment 拒绝） |

> **SM-3 的诚实边界**：真正的 **greenfield 零代码**项目（SAD 刚写完，一行代码没有）可能**结构性达不成**"≥1 条 verified"——没代码就没有能跑绿的东西。此时达标线为：**三层框架完整 + 泳道表 + 待建清单**，`verified` 数可为 0。**MUST NOT** 为了凑一个 `verified` 而造一个没有实际意义的空跑测试。

## Non-Goals

- **⭐ 替人判断验证方法有没有效**〔总则〕——skill 保证「三层五槽没留白 · 每条泳道有验证方法 · 证据是执行者写的 · 状态没撒谎」，**不保证方法本身有效**。质量由模型能力 + 人判断 + 冷审保证。
- **⭐ 堵住 `assert True`**——证明"跟依赖说过话"≠证明"断言有效"。**任何外部插桩都堵不住**，要堵只有**变异测试**（太重）⇒ **机械层堵不死此项，诚实归冷审 vacuous 镜**（唯一防线）。
- **⭐ 证明「人真的做了人工验证」**——`confirm-lane` 产出的绿如实标 `human-attested`，但**不保证**人真的照着 `human_steps` 做了。**agent session 的架构边界**：模型是唯一的命令执行者，「人亲自敲命令」在机械上不可区分，**且本就不必防**（总则：使用者没有动机骗自己）。
- **⭐ 管理 skill 没有启动过的资源**——recipe 内部起的容器（如 `ctl.sh start` 拉起的 Docker 容器）**不属于子进程组**，skill **管不着**、也不假装能管理；超时/中断只如实报告「可能留下孤儿资源，请检查」。
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
| **P0** | 五步编排 + 三模式分流 · **测试三层框架（JSON + 五槽 + 三态强制附带项）** · **验证方法（`method`/`executor`/`strength`/`evidence`，两种「跑不了」分清）** · 泳道三态 + JSON schema · 落地物追加 · **`verify-lane` + `confirm-lane`** · **③-pre 人门 + touched-files journal 回退** · **路径 containment 校验** · `devenv_lint`（防漏检查）· 两份真相源渲染 | 缺任一则 skill 不成立 |
| **P1** | `opsx-devenv` 托管块注入（fence-aware）+ INDEX · `lane-patterns` / `verification-patterns`（标「实例，非规格」）· 冷审镜单（覆盖镜 / 验证方法镜 / 分类镜 / vacuous 镜 / 诚实镜）· 归位模式删源三处置 + 逐文件护栏 + 可恢复备份 · **跨 skill 写域锁（三条腿）+ CAS 快照** · **最小环境 allowlist** · **digest 按文件类型分治** | 可用但不完整；并发安全、路径边界、执行环境隔离**不可后补** |
| **P2** | doctor 脚本生成 · CI 调用壳生成 · `sdflow-architecture` 交棒话术改写 · **双向分流句** · 未覆盖形态的 todo 登记 | 增益项，可迭代 |

## 利益相关方与外部依赖〔TG-20〕

| 方 | 影响 |
|---|---|
| **消费仓** | 新增 `openspec/architecture/{environments,testing-strategy,devenv-log}.md` + `.devenv-lanes.json` + `.devenv-strategy.json` + 落地物 + `opsx-devenv` 托管块；**不跑本 skill 则完全无感** |
| **`sdflow-architecture`** | 交棒话术 + description 路由句变更（MODIFIED capability）· **`sad_scaffold.py` 迁共用锁 + 补 owner 记录/核对 + `atomic_write` 加 mode 参数**（面治） |
| **`sdflow-init`** | **要改**（面治，非可选）：`inject()` 补锁 + 原子写；description 加**反向排除句** |
| **`sdflow-maintain`** | 扫描面增加 devenv 健康度（**新增代码**——现为四类硬编码扫描，**无插件挂点**） |
| **`embedded-test-sop`** | 真硬件泳道**指向它**作为 `executor: human` 的验证方法，不重造手动 SOP |
| **外部命令**（`make` / `go test` / `npm` / `docker` / `git`） | skill 执行它们（子进程走最小环境 allowlist）；失败模式表见 design〔TG-08〕 |

## ⭐ 实现前置（设计门拍定，MUST 先于 tasks 第 1 组）

**先跑 `sdflow-architecture` 的首个真实试点**——用本来要做 SM-3 的**同一个绿地项目**。

`add-sdflow-architecture` 归档于 2026-07-12，其 hand-off 明写「**首个真实试点（最高优先）**……SM-4 证伪钟起点」——**该试点未做**。而 devenv 对 SAD 的依赖是硬的（依赖形态四问 ← SAD §3 外边界；`covers` 对账 ← SAD §5 contract）。

**一个项目的成本，同时给两个 skill 去风险**：

1. 验证**真实 SAD 的 §3/§5 能否长出 devenv 需要的锚**
2. 验证 **greenfield 的「命令虚构」风险是否真实存在**（Why 段的唯一未观测项）
3. 验证 **`lane-patterns` 五格在第二个样本上是否还成立**（A-2 的 n=1 过拟合）
4. **⭐ 验证「模型能不能为三层各自提出像样的验证方法」**——这是新总则整条路线的前提。若模型提不出、或提出的方法经不起人门推敲，则本 skill 的核心承诺落空

## 开放问题〔TG-21〕

> **编号统一说明**：前一版 `proposal.md` / `design.md` / `specs/maintain-scan/spec.md` 三份文档的 Q 编号互相打架（`design.md` 现行 Q-4 = 「maintain 硬拦截」，与本表 Q-6 同题不同号）——本表为**统一编号**，`maintain-scan/spec.md` 已引用「proposal 的 Q-6」与本表一致；**遗留动作**：下次触碰 `design.md` 时把其 Q-1~Q-6 改按本表对齐（不在本 change scope 内单独动 design.md，登记为待办，`sdflow-maintain` 首次扫描本 change 时可作为一致性项核对）。

| # | 问题 | 负责人 / 截止 |
|---|---|---|
| Q-1 | `lane-patterns` / `verification-patterns` 未覆盖形态何时补格 | 操作者 / 首个撞上该形态的项目 |
| Q-2 | monorepo 多系统演进——需 SAD 先支持多系统 | 操作者 / 首个 monorepo 消费仓 |
| Q-3 | `devenv_lint` 的「入口复述检测」是弱启发，阈值待接地校准 | 实现期 / 首跑后 |
| **Q-4** | **harvest loop**（从 buglist / code-review 报告机械喂坑与盲区进 testing-strategy）——`06` 认定这是最高价值来源，而 day-0 编排器**拿不到它** | 操作者 / v2 |
| **Q-5** | Windows 的 `taskkill /T /F` 分支——零依赖可行但**无环境实测**。何时补？ | 操作者 / 有 Windows 环境时 |
| **Q-6** | `sdflow-maintain` 是**人主动跑**的 ⇒ lint 触发是「提醒」非「硬门禁」。是否需要在 `ship_gate` 加硬拦截？ | 操作者 / 首个僵尸 scaffolded 出现时 |
| **Q-7** | SAD 处于 `draft` 态时 contract 随时改名 ⇒ `covers` 锚可能悄悄失真。`sad` 字段是否需要第三态？ | v2 / 与 SAD 生命周期绑定 |
| **Q-8** | `schema_version` **低于**本实现已知版本时的策略（旧文件被新脚本读到）——v1 阶段无需处理（当前只有 v1），但**加了字段 ≠ 有升级路径** | **MUST 在引入 v2 的那个 change 里显式定义**（fail-closed 要求迁移 / 提供 `migrate` 子命令 / 只读兼容），**MUST NOT 在无设计的情况下现场处理** |

> **编号纪律**：本表为**唯一权威**。`design.md` 与 `specs/maintain-scan/spec.md` 的 Q 引用**以此为准**（前一版三份文档各用一套编号、互相打架，round-3 一致性镜抓出）。

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
| **A-8** | **模型能为三层各自提出像样的验证方法** | ⚠️ **未验证——这是整条路线的前提**。若模型提不出、或提出的方法经不起人门推敲 ⇒ 核心承诺落空。**上游试点第 4 条专测此项** |

## Capabilities

### New Capabilities
- `devenv-provisioning`: 开发/测试环境搭建编排器——五步流水线 · 三模式分流 · **测试三层框架（落 JSON，无一层留白）** · **验证方法（模型提 + 人拍板，`script` 首选/`human` 降级，两种「跑不了」分清）** · 证据只能由执行者本人写（`verify-lane`/`confirm-lane`，`human-attested` 如实标注）· `verified = verified-at <sha>` · 泳道三态与渐进 DoD · 落地物追加（追加者非拥有者）· **路径 containment 校验** · **③-pre 人门 + touched-files journal 回退** · digest 按文件类型分治 · 机械 lint（**只查诚实/防漏，不查质量/防伪**）· 两份真相源渲染与入口托管注入 · **跨 skill 写域锁 + CAS** · **最小环境 allowlist**。

### Modified Capabilities
- `architecture-design`: 交棒后的过程轴下游**从「指出不代写 + 给模板路径」改为指向 `/sdflow-devenv`**；description 增加过程轴分流句。
- `maintain-scan`: 扫描面**增加 devenv 健康度**——`sdflow-maintain` SHALL 调用 `devenv_lint`。**这是 `devenv_lint` 唯一的触发点**。

## Impact

**本仓**：

- 新目录 `sdflow-devenv/`（`SKILL.md` + `scripts/`×3 + `references/`×7 + `tests/`）
- 改 `sdflow-architecture/`（交棒话术 + description + **`sad_scaffold.py` 迁锁 + 补 owner 记录/核对 + `atomic_write` 加 mode**）
- 改 `sdflow-init/`（**`inject()` 补锁 + 原子写** + description **反向排除句**）
- 改 `sdflow-maintain/`（**新增** devenv 健康度扫描）
- 改 `README.md`（Skills 列表）；**`setup.sh` 无需改**
- 新增 pytest（本仓纪律：改 `scripts/` 必跑 `tests/`）

**消费仓**（跑本 skill 后）：`openspec/architecture/{environments,testing-strategy,devenv-log}.md` · `.devenv-lanes.json` · `.devenv-strategy.json` · `.devenv-txn.json`（临时，回退/提交后删除）· `.devenv-backup/`（归位模式删源时产生，**入 git、不 gitignore**）· 落地物 · `opsx-devenv` 托管块 · `openspec/INDEX.md` 条目 · `openspec/.sdflow-write.lock`（临时，三 skill 共用）。

**技术栈标注**：Markdown + Python。**TG-26（并发）与 TG-08（外部依赖）命中**。

## Compliance

- **skill 目录约定**：`SKILL.md` + `scripts/` + `references/` + `tests/`；`setup.sh` 自动装载。
- **bundle 权威源纪律**：本 change **不改** `sdflow-init/assets/workflow/`，无需 `sdflow-init update` 回灌。
- **托管区块纪律**：`opsx-devenv` 为**新 marker token**，**MUST NOT** 写入 `opsx-init` 区块。
- **机械化优先 + 诚实边界**（基准 1）：能机械化的一律机械化（防漏）；**机械够不着的（防伪）诚实划归语义层，MUST NOT 硬凑假机械**——这是本轮重写的第一原则（`07` §0.0）。
- **面治优先于点补**（基准 3）：`init.py` 补锁 · `sad_scaffold` 迁锁 + owner 核对 + mode 参数 · 双向分流句——一次扫全。
- **目标态导向**（基准 2）：三层框架锚目标态，**MUST NOT** 以「现存项目大多只有单元测试」论证「e2e 可省」——省了就写 `不适用 + 后果`。
- **审查顺序**：`/sdflow-spec-review`（设计门）→ 实现 → `/review` → push → `/sdflow-code-review` → `/sdflow-done`。
- **HR-TG**：命中 TG-08 / TG-09 / TG-17 / TG-26 → spec-review **单开领域 cross-model**。
