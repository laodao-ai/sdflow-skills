# add-sdflow-devenv

> 设计源：`docs/sad/07-devenv-skill-design.md`（九条设计点逐条拍定）
> 接地证据：`docs/sad/06-process-axis-grounding-receipt.md`（mqtt-console 实测）

## Why

技术架构定了之后，**把项目的开发/测试环境真正建起来**这件事在生态里无 skill 覆盖：`sdflow-architecture` 的交棒止于「过程轴文档指路（指出不代写）」，下游是空的；`sdflow-init` 铺的是 **workflow 的运行环境**（规则 bundle），按定义不管项目内容。于是「定测试策略 → 落 Makefile/broker/CI/harness → 跑通 → 出真相源文档」全靠人手搓。

### 证据分层（诚实版）〔spec-review-amendment · CEO-1/CEO-3〕

> ⚠️ **本节曾把一条预测风险写成「接地实测暴露」，并把一条被证伪的推论当作立项支点。设计门（Q5=B）要求：维持 orchestrator 路线，但 MUST 修掉伪证据。** 以下为订正版。

| # | 现象 | 证据强度 |
|---|---|---|
| 1 | **散落双写** —— 同一份测试策略存在 3 处、env 内容存在 2 处 | ✅ **实测**（mqtt-console，`06`） |
| 2 | **无门禁** —— `assert-bindings` 这类检查无任何自动触发点，全靠人记得跑 | ✅ **实测**（`06 §2.3`） |
| 3 | **命令虚构** —— 纯文档型 prompt 为对齐模板范式而编造不存在的 target | ⚠️ **预测，未观测**。归位场景的实测结果是**零虚构**（`06:44`：「Makefile 四 target 行号全中，零虚构」）。虚构风险属 **greenfield 模式的推断**，而 greenfield **零样本** —— Q2 的上游试点将首次验证它 |

### 天花板声明（MUST 如实记，设计门 Q5=B 的条件）〔spec-review-amendment · CEO-3〕

`docs/sad/05` 曾拍板「D（独立 skill）不立」，其候选集把 skill 误当「生成器」（于是一证伪「从 SAD 投影只有 12%」就否掉了它），且 B 候选建立在对 `sdflow-init` 职责的误解上——**这两条推翻成立**。

但**原推论「那 88% 全是待决策项」是错的**：`06 §4.2` 已把二分改为**三分**——SAD 投影 / **构建配置投影**（各层执行命令 · 工具链版本 · 配置项默认值，**机械可读**）/ 纯人写。**88% 里有一大块是机械可抽的，不是待决策项。**

而真正的纯人写部分——**常见坑 · 护栏 · mock 边界 · 已知盲区**——来源是**踩坑史 / 决策史 / 测试哲学**，**day-0 根本问不出来**（坑还没踩、flake 还没暴露）。而 `06 §1.1` 恰恰认定：两份文档的**最高价值就是这些**。

⇒ **诚实的天花板**：greenfield 首跑，本 skill 能产出的是「**一个可跑的 Makefile + 一张泳道表 + 一张明确的待建清单**」，**不包含** `06` 认定的全部价值。**坑与护栏只能随时间收割**（本 change 不做 harvest loop，登记为 Q-4 演进方向）。

**在这个天花板之上，skill 仍然立得住**——因为它交付的是**手搓拿不到的三样**：① 落地物**真的被执行过**（而非「文档说它能跑」）② 泳道状态**机械可查**（而非散落在人脑里）③ **lint 有触发点**（挂 `sdflow-maintain`，见 R-15）——**第三条正是手搓 prompt 最缺的那一环**（也是本 proposal 原先自己也缺的，见 CEO-2 的 dogfood 自指坑）。

## What Changes

- **新增 skill `sdflow-devenv`**——过程轴编排器（**非**生成器），五步流水线（事实采集 → 泳道设计拍板 → 落地脚手架 + 真跑 → 冷审 + 人门 → 文档 + 入口 + 交棒）+ 三模式分流（新建 / 归位 / continue）。
- **泳道三态状态机 + 渐进 DoD**：`planned → scaffolded → verified`，逐条独立推进，**不强制全绿**（项目初期定不下所有事）；但**诚实是硬要求**——`scaffolded` MUST 带非空 `blocked_by`。
- **⭐ lint 的触发点（R-15，新增）**〔spec-review-amendment · CEO-2 · Q6=A〕：`devenv_lint` **挂进 `sdflow-maintain` 的扫描**。**没有触发点的 lint = 没有 lint**——「渐进 DoD」允许泳道停在 `scaffolded`，而防止它烂成僵尸文档的**唯一措施**就是「lint 复述未完成清单」；若无人调用该 lint，该措施为空，前提不成立。原设计把「无门禁」列为立项理由却自己也没门禁（**dogfood 自指坑**），本条堵死它。**诚实边界**：`sdflow-maintain` 是**人主动跑**的 ⇒ 这是「**更响的提醒**」而非**硬门禁**，MUST NOT 佯装硬拦截。
- **落地物（真代码，直写落盘）**：Makefile target（**门禁逻辑在此**）· broker/依赖服务 · CI 配置（**只生成独立新文件，不往用户既有 workflow 插 step**）· 测试 harness · **每泳道一条 smoke** · doctor 依赖自查。skill 是**追加者不是拥有者**——落地物**不设托管块**，重名 fail-closed。**v1 显式收窄**：落地物入口**只支持行文本型**（Makefile / justfile）；JSON（`package.json`）/ YAML（CI）的**结构化编辑进 Non-Goals**〔ENG-11〕。
- **`verified` 由脚本亲自执行并落执行证据**〔spec-review-amendment · ENG-1〕：新增 `verify-lane` 子命令——**由脚本自己 fork 正/反两跑**，捕获 exit code / 时长 / 输出摘要，据此自行决定状态并**原子写执行证据**（`verified_at` / `fwd_exit` / `neg_exit` / `neg_strategy` / `evidence_digest`）。**`set-lane --status verified` 一律拒绝**（exit 5）——`verified` 只能由 `verify-lane` 产出。原设计的子命令里**没有一个会执行 smoke**，所谓「脚本验证」实为「模型自称、脚本盖章」。
- **negative control：强信号，非定义**〔spec-review-amendment · ENG-8 · Q3〕：**不再**作为 `verified` 的 ⟺ 定义。它只证「命令**耦合**依赖」，**不证「断言有效」**（`assert True` 照样能拿到正绿反红），且对 **testcontainers / 内嵌 fallback**（Go/Node 主流写法）**永久误判**。改为：独立字段 `neg_control: applicable | n/a — <理由>`（**不靠删 `deps` 绕**——那会把假阴性换成真·假绿）· 仅对**抽离机制已定义**的依赖类生效 · 必须匹配 **expected-failure predicate**（普通非零不通过）。**并行强制一条机械门槛**：解析 `go test -json` / pytest `collected N`，断言「**至少跑了 ≥1 个测试且 0 skipped**」——这有确定性信号，按基准 1 该机械化。
- **数据落 JSON 侧文件**〔spec-review-amendment · ENG-5 · Q4〕：`lanes[]` **不放 frontmatter**，放 `openspec/architecture/.devenv-lanes.json`（**标准库、零依赖、round-trip 无损**）。原设计的嵌套 YAML **无解析方案**——本机无 PyYAML，本仓唯一先例只支持扁平标量。frontmatter 只留 `sad` / `mode` / **`schema_version`** 三个扁平标量。
- **两份真相源 + 入口注入**：`openspec/architecture/{environments,testing-strategy}.md`（命令表**机械渲染**）+ `devenv-log.md` 留痕；`opsx-devenv` 托管块 → CLAUDE/AGENTS/README + `openspec/INDEX.md`。
- **修改 `sdflow-architecture`**：§5.3 交棒话术从「指出不代写 + 给模板路径」改为**指向 `/sdflow-devenv`**；description 的生态路由句增加过程轴分流。
- **修改 `sdflow-maintain`**：扫描面增加 `environments.md` 健康度（调 `devenv_lint`）〔R-15〕。
- **BREAKING**：无。纯增量（消费仓不跑本 skill 则完全无感）。

## Success Metrics

> ⚠️ 〔spec-review-amendment · CEO-11〕原 SM **只能证明实现自洽，不能证明产品有效**（SM-1 以人工归位为金标准 = **循环验证**；其余全是内部 schema/lint）。下表补入**产品有效性指标**（SM-6/7），并把 SM-3 从「lint 能工作」改为「**lint 会被跑**」。

| # | 指标 | 判定 |
|---|---|---|
| SM-1 | **归位模式回归**：在 **checkin 的 brownfield fixture** 上跑归位，删源集与搬运结果**确定性断言**〔ENG-17：原「mqtt-console 副本 + 人工比对」跑一次后**永不再跑**，归位模式此后零回归〕 | pytest（fixture 在 `tests/fixtures/brownfield/`） |
| SM-2 | **新建模式跑通**：绿地项目跑通五步，产出**至少一条 `verified` 泳道** + 一张明确待建清单 | `verify-lane` 亲自执行、**执行证据落盘** |
| SM-3 | **⭐ lint 有触发点且真拦得住**：`devenv_lint` **在 `sdflow-maintain` 扫描中被自动调用**，并在一次**真实回归**上拦下（如人改了 Makefile 使 `verified` 泳道的 source digest 失配）〔Q6=A · CEO-2〕 | maintain 集成测试 |
| SM-4 | **诚实性**：`scaffolded` MUST 有非空 `blocked_by`；`verified` MUST 有**执行证据**（`fwd_exit` / `neg_exit` / `evidence_digest`）；`verified` 泳道 MUST NOT 残留旧 `blocked_by`〔ENG-15〕 | lint 断言 + pytest |
| SM-5 | **零双写**：`command` 与 `source` 的一致性由 **digest 锚**（非行号）保证；正文表格由脚本渲染且带 DO-NOT-EDIT banner〔ENG-4：行号锚 + 「查行存在」对任何长度 ≥N 的文件**恒真**〕 | lint 断言 + pytest（造「行还在、内容变了」的坏输入） |
| **SM-6** | **产品有效性（新增）**：绿地项目从 **clean checkout 到首条真实测试跑通**的耗时 · 所需**人工回答数** · 生成 diff 被操作者**保留的比例** | Q2 试点实测记录 |
| **SM-7** | **不伤害（新增）**〔ENG-3〕：negative control 执行后，**所有被抽离的依赖 100% 恢复**；异常中断（超时 / SIGINT / 崩溃）下**恢复仍执行**（`finally`）；**MUST NOT 停止非本次运行启动的依赖**（`owned_by: operator` → 拒绝） | pytest（注入异常 → 断言 up 被调用） |

## Non-Goals

- **业务测试用例**——本 skill 只建 harness + 每泳道一条 smoke；业务回归网归各 change。
- **生产运维 runbook**（on-call / SLO / 告警）——本 skill 只到 deploy 操作。
- **替用户安装系统依赖**（`brew install` / `docker pull`）——只给 doctor 脚本 + 命令，副作用不可逆。
- **smoke 跑不绿时 debug 到通**——职责是「建 + 验」不是「调通」；跑不绿是合法状态（`scaffolded` + `blocked_by`），修复归下次 `continue`。
- **monorepo 多系统**——v1 单例 + 显式提示；演进路径 `openspec/architecture/{system}/` 与 SAD **同步升**（`covers` 要锚得住）。
- **时间轴排期 / 里程碑** → `sdflow-roadmap`。
- **从 SAD 自动生成文档**——接地实测投影率仅 12%，且投影出的是最不值钱的部分（详见 `06` §1）。
- **JSON / YAML 落地物的结构化编辑**〔spec-review-amendment · ENG-11〕——v1 **只支持行文本型入口**（Makefile / justfile）。往 `package.json` 的 `scripts` 加一条 = **JSON 结构化读-改-写**；往 `ci.yml` 加 step = **YAML 结构化编辑**（缩进敏感、注释保留）——**「追加 + 行锚」抽象对这两者根本不适用**。CI 配置**只生成独立新文件**（`.github/workflows/devenv.yml`，skill 全量拥有），**MUST NOT** 往用户既有 workflow 插 step；`package.json` 型项目走「生成 Makefile 薄壳去调 npm script」。登记 todo。
- **坑 / 护栏 / 盲区的 harvest loop**〔CEO-3 天花板〕——从 buglist / code-review 报告机械喂 flake 与盲区进 `testing-strategy`。这是本 skill **最高价值的演进方向**（`06` 认定两份文档的价值主要在此），但**本 change 不做**，登记为 Q-4。

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

## ⭐ 实现前置（设计门 Q2 拍定，MUST 先于 tasks 第 1 组）

**先跑 `sdflow-architecture` 的首个真实试点**——用本来要做 SM-2 的**同一个绿地项目**。

`add-sdflow-architecture` 归档于 2026-07-12，其 hand-off 明写「**首个真实试点（最高优先）**……SM-4 证伪钟起点」——**该试点未做**。而 devenv 对 SAD 的依赖是硬的（依赖形态四问 ← SAD §3 外边界；`covers` 对账 ← SAD §5 contract）。

**一个项目的成本，同时给两个 skill 去风险**：

1. 验证**真实 SAD 的 §3/§5 能否长出 devenv 需要的锚**（否则两条高价值投影同时塌方，ADR-8 已承认无 SAD 则「泳道设计失去锚」）
2. 验证 **greenfield 的「命令虚构」风险是否真实存在**（Why 段的唯一未观测项）
3. 验证 **`lane-patterns` 五格在第二个样本上是否还成立**（A-2 的 n=1 过拟合）

## 开放问题〔TG-21〕

| # | 问题 | 负责人 / 截止 |
|---|---|---|
| Q-1 | `lane-patterns` 未覆盖形态（Java 服务 / 移动 app / 分布式）何时补格？v1 走「临场推导 + 登记 todo」兜底 | 操作者 / 首个撞上该形态的项目 |
| Q-2 | monorepo 多系统演进——需 SAD 先支持多系统（`covers` 才锚得住），两者绑定升级的时机 | 操作者 / 首个 monorepo 消费仓 |
| Q-3 | `devenv_lint` 的「入口复述检测」是弱启发，阈值待接地校准 | 实现期 / 首跑后 |
| **Q-4** | **harvest loop**（从 buglist / code-review 报告机械喂坑与盲区进 testing-strategy）——`06` 认定这是两份文档的**最高价值来源**，而 day-0 编排器**拿不到它**（CEO-3 天花板）。何时做？ | 操作者 / v2 |
| **Q-5** | `sdflow-maintain` 是**人主动跑**的 ⇒ R-15 的 lint 触发是「提醒」非「硬门禁」。是否需要在 `ship_gate` 加一道硬拦截？ | 操作者 / 首个僵尸 scaffolded 出现时 |
| **Q-6** | 抽依赖的**隔离式**策略（把 endpoint 指向不可达地址）要求 harness **从 env 读配置**。harness 硬编码 `localhost:1883` 时该策略失效 → 抽依赖后仍绿 → 好泳道被误判。是否要求生成的 harness **一律从 env 读**？ | 实现期 |

## 假设〔TG-22〕

> 〔spec-review-amendment〕A-1/A-3 已被评审**证伪或削弱**，下表为订正版。

| # | 假设 | 失效影响 |
|---|---|---|
| ~~A-1~~ | ~~negative control 对所有依赖类型都成立~~ | ❌ **已证伪**（ENG-8）——它只证「命令**耦合**依赖」，不证「断言有效」；对 testcontainers / 内嵌 fallback（**主流写法**）永久误判。⇒ **降为强信号**（Q3），不再是 `verified` 的定义 |
| **A-2** | **依赖形态五格**能覆盖多数项目 | ⚠️ **已削弱**（CEO-5）——五格中三格全来自 mqtt-console，且拿同一样本「自验」是**过拟合不是证伪**。Q2 的上游试点将在**第二个样本**上首次检验；若不成立 → `lane-patterns` 退化为纯临场推导，枚举完备性丧失 |
| ~~A-3~~ | ~~渐进 DoD 不会导致永久 `scaffolded`（人会回来 continue）~~ | ❌ **已证伪**（CEO-2）——原缓解「lint 复述未完成清单」依赖一个**没有触发点的 lint**，结构性必然僵尸化。⇒ **R-15 把 lint 挂进 `sdflow-maintain`**（Q6）。**残余**：maintain 人主动跑 ⇒ 仍是「提醒」非「硬门禁」，此局限显式登记 |
| **A-4** | **两个 session 并发跑 devenv 会撞车** | 已知**必然**发生。⚠️ **原缓解不足**（ENG-6）：devenv 的锁**挡不住 `sdflow-init`**（不同锁名，且 `init.py` 的 inject 是裸 `open(w)` **无锁无原子写**）⇒ 注入会被静默吃掉。⇒ 锁提升为 **`openspec/` 写域单一锁**，三 skill 共用；顺带给 `init.py` 补锁 + 原子写（面治优先于点补） |
| **A-5** | 消费仓已有的 Makefile target **语义可被读懂并登记** | 若语义模糊（一个 `test` 跑三条泳道）→ `covers` 对账失真。缓解：登记结果进搬运表人门；**模糊者宁可标 `planned` 不强行登记** |
| **A-6（新增）** | **锁参数适用于本 skill 的临界区** | ❌ **已证伪**（ENG-10）——`sad_scaffold` 的锁是为**亚秒级**操作调的（`STALE=120s`），而 devenv 的 smoke 可跑几分钟：锁若跨 smoke 持有 ⇒ **活锁被判残留锁** ⇒ 提示用户删锁 ⇒ 两 session 同写（**陈旧锁检测从保护变成攻击面**）。⇒ 锁**短持有**（只包单次子命令）+ **CAS**（`--expect <prior-status>`）防 lost update |
| **A-7（新增）** | **「不外发」⇒ 无 secret 出境面** | ❌ **已证伪**（ENG-12）——命令继承 agent session 的**完整环境变量**，失败命令回显（如 `AMQP_URL=amqp://user:pass@host`）会写进 `blocked_by` / `devenv-log.md` → **commit → push**。**不主动外发，但把 secret 写进了必然被外发的载体**。⇒ 输出捕获 MUST 截断 + 过 secret 正则 + **MUST NOT** dump 环境变量 |

## Capabilities

### New Capabilities
- `devenv-provisioning`: 开发/测试环境搭建编排器——五步流水线 · 三模式分流 · 泳道三态状态机与渐进 DoD · 落地物追加（skill 为追加者非拥有者）· smoke 真跑与 negative control · 机械 lint 五条 · 两份真相源渲染与入口托管注入 · 并发安全写入。

### Modified Capabilities
- `architecture-design`: `Requirement: 触发分工与互相指路（生态路由）` 的指路集合扩充——SAD 交棒后的过程轴下游**从「指出不代写 + 给模板路径」改为指向 `/sdflow-devenv`**；description 增加过程轴分流句（「建 dev/test 环境 → `/sdflow-devenv`」），与既有的时间轴分流句（→ `sdflow-roadmap`）并列。
- `maintain-scan`〔spec-review-amendment · Q6=A · CEO-2〕: 扫描面**增加 `environments.md` 健康度**——`sdflow-maintain` 在扫 `openspec/` 一致性时 SHALL 调用 `devenv_lint`，报告未 `verified` 泳道清单、失配的 source digest、空 `blocked_by`。**这是 `devenv_lint` 唯一的触发点**（无此则「渐进 DoD」前提结构性不成立，见 A-3）。

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
