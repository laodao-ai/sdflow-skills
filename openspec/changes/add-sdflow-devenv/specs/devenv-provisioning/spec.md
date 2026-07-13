## ADDED Requirements

### Requirement: preflight 两级与三模式分流

skill 每次触发 SHALL 先跑 `devenv_scaffold.py init`，按退出码分流，MUST NOT 自造半套布局、MUST NOT 静默继续。

- **无 `openspec/` 布局 → fail-closed**（exit 3）：原样转述 preflight 指引（先 `/sdflow-init`）。
- **`sad.md` 缺失 → 显式降级，不 fail-closed**：SHALL 响亮警告「拿不到子系统 contract 清单与外部依赖清单，泳道覆盖对账（E2）失效、依赖形态四问只能靠读码猜，可能漏边界；建议先 `/sdflow-architecture`」，并在 `environments.md` frontmatter 留痕 `sad: missing`，然后继续。**MUST NOT 佯装有 SAD**。
- **`environments.md` 已存在**（exit 4）：MUST NOT 静默覆盖，SHALL 显式向操作者区分 **continue**（推进泳道 / 增补）与 **replan**（技术栈或测试策略被推翻，重走泳道设计）后带 `--on-exists` 重跑；continue 前 SHALL 先读 `devenv-log.md` 定位断点。
- **检出存量素材**（已有 Makefile / 测试 / 散落的 env·testing 文档）→ SHALL 提示可走**归位模式**。

#### Scenario: 无 openspec 布局时拒绝运行
- **WHEN** 消费仓无 `openspec/` 布局
- **THEN** skill 以 exit 3 fail-closed，转述「先跑 /sdflow-init」指引，且不创建任何文件

#### Scenario: SAD 缺失降级但响亮留痕
- **WHEN** 消费仓无 `openspec/architecture/sad.md`
- **THEN** skill 显式警告覆盖对账将失效并建议先跑 /sdflow-architecture，在 frontmatter 写入 `sad: missing`，然后继续执行

#### Scenario: 已存在产物不静默覆盖
- **WHEN** `environments.md` 已存在且 skill 被再次触发
- **THEN** skill 显式区分 continue 与 replan 后才写入

### Requirement: 事实采集与时序纪律

skill SHALL 从 SAD 投影候选事实**给操作者复核**（MUST NOT 直接采信）：栈与平台约束 ← SAD §2 · **依赖形态 ← SAD §3 外边界** · **集成测试点 ← SAD §5 contract**。SAD 无源的事实（CI 平台 / 团队机器可用依赖 / 部署形态）SHALL 向操作者提问。

**时序纪律（加粗强制）**：**MUST 实际向操作者提问并获得人的回答之后，才允许记录；MUST NOT 预填、MUST NOT 替操作者臆测答案。**

#### Scenario: SAD 有源事实需人复核
- **WHEN** SAD 存在且含 §2 约束与 §3 外边界
- **THEN** skill 把投影出的候选事实呈现给操作者复核，操作者确认或修正后才记录

#### Scenario: 无源事实必须提问
- **WHEN** 需要知道 CI 平台或团队机器可用依赖
- **THEN** skill 向操作者提问并等待回答，MUST NOT 自行臆测

### Requirement: 泳道设计候选与拍板

skill SHALL 按 `references/lane-patterns.md` 的**依赖形态四问**（有无外部有状态依赖 / UI / 语言桥 / 真硬件）推导泳道候选，**MUST NOT 按语言分格**。一个项目 = 多个形态叠加，泳道 = 各形态阶梯的**并集**。

`lane-patterns.md` SHALL **只固化「问什么」**（形态四问 · 每种形态为何需要该阶梯的判据 · 最小可用集判据），**MUST NOT 固化「答什么」**（具体工具/库选型）——工具选型 SHALL 由模型现场调研推荐、**由人决策**。参考实例 SHALL 标注为「实例，非规格」。

**未覆盖形态**（无真样本）SHALL 走兜底：模型按四问临场推导并**显式标注「本形态无参考实例，系临场推导」**，同时登记 todo，**MUST NOT 凭空编造权威候选**。

拍板产出 SHALL 含：泳道清单 · 各测什么 · mock 边界 · 各自 `covers`（SAD contract 锚）· **最小可用集**（初期先建哪条，其余标 `planned`）。

#### Scenario: 按依赖形态而非语言推导泳道
- **WHEN** 项目为 Go 后端 + 外部 broker + Svelte 前端 + 语言桥绑定
- **THEN** skill 按形态叠加产出泳道并集（外部依赖阶梯 + UI 阶梯 + 语言桥门禁），而非按 Go/Node 分别套用语言模板

#### Scenario: 未覆盖形态不编造权威候选
- **WHEN** 项目落到 lane-patterns 无参考实例的形态
- **THEN** skill 临场推导候选并显式标注「无参考实例，系临场推导」，同时登记 todo

### Requirement: 泳道三态状态机与渐进 DoD

每条泳道 SHALL 独立处于三态之一：`planned`（决定要有）→ `scaffolded`（harness + smoke 已写、未跑绿）→ `verified`（smoke 真跑绿过）。状态迁移 SHALL 只由 `devenv_scaffold.py set-lane` 执行，**表外迁移一律拒绝**；模型/人 MUST NOT 手改 frontmatter 跳级。

skill 的完成态 **MUST NOT 要求全部泳道 `verified`**——允许停在 `planned` / `scaffolded`，不阻塞（渐进 DoD）。

**但诚实是硬要求**：`scaffolded` 态 **MUST 带非空 `blocked_by`**（说明卡在哪 + 怎么修 + 怎么 continue）；空 `blocked_by` → lint fail-closed。收尾时 skill **SHALL 逐条列出**仍处于 `planned` / `scaffolded` 的泳道，**MUST NOT 只埋进文件里**。

#### Scenario: 依赖缺失不算失败
- **WHEN** 本机无 mosquitto 导致集成泳道 smoke 跑不起来
- **THEN** 该泳道留在 `scaffolded` 且 `blocked_by` 写明「本机无 mosquitto — brew install mosquitto 后 /sdflow-devenv continue」，skill 继续处理其余泳道

#### Scenario: 空 blocked_by 被拒
- **WHEN** 某泳道状态为 `scaffolded` 但 `blocked_by` 为空
- **THEN** `devenv_lint` fail-closed 并报出该泳道

#### Scenario: 收尾显著呈现未完成泳道
- **WHEN** skill 收尾且存在未 `verified` 的泳道
- **THEN** 收尾报告逐条列出这些泳道及其 `blocked_by`

### Requirement: `verified` 由脚本亲自执行并落执行证据〔spec-review-amendment · ENG-1〕

`verified` **SHALL 只能由 `devenv_scaffold.py verify-lane` 子命令产出**。该子命令 **MUST 由脚本自己 fork 执行** smoke（正向跑 + 阴性对照跑），捕获 exit code / 时长 / 输出摘要 / 测试计数，**据此自行决定**写 `verified` 还是 `scaffolded + blocked_by`。

**`set-lane --status verified` MUST 一律拒绝**（exit 5）——状态 `verified` **MUST NOT** 由调用者（模型）传入。

> **理由**：原设计的子命令里**没有一个会执行 smoke**，实际数据流只能是「模型跑 → 模型读 exit code → 模型调 `set-lane --status verified`」⇒ 脚本对「到底跑没跑、绿没绿」**零独立证据** ⇒「脚本执行验证」退化为「**模型自称，脚本盖章**」。

`verify-lane` **MUST 原子写执行证据**至该 lane：`verified_at`（时间戳）· `verified_at_commit`（HEAD SHA）· `fwd_exit`（正向退出码）· `fwd_tests`（跑了几个测试 / 跳过几个）· `neg_exit`（阴性对照退出码，`n/a` 时为空）· `neg_strategy`（用了哪种抽离策略）· `evidence_digest`（command + smoke + source 的联合摘要）。

> **无执行证据落盘 ⇒ 冷审的「诚实镜」在数据上无从查证**——冷审子代理只能读文件、无法复跑命令，看到 `status: verified` 只能选择相信。执行证据是该镜的接地面。

**`verified` 是会过期的事实**〔CEO-8〕：`evidence_digest` 失配（人改了 Makefile recipe / 换了 smoke / 依赖升级）⇒ lint **MUST** 报「该泳道的验证证据已失效，需重跑 `verify-lane`」，**MUST NOT** 继续声称 `verified`。

#### Scenario: 模型不能自称 verified
- **WHEN** 调用 `set-lane --id X --status verified`
- **THEN** 脚本以 exit 5 拒绝，提示「`verified` 只能由 `verify-lane` 产出」

#### Scenario: verify-lane 亲自执行并落证据
- **WHEN** 调用 `verify-lane --id X`
- **THEN** 脚本自己执行正向跑与阴性对照跑，并把 `fwd_exit` / `neg_exit` / `neg_strategy` / `evidence_digest` / `verified_at_commit` 写入该 lane

#### Scenario: 证据失效时不再声称 verified
- **WHEN** 某 `verified` 泳道的 `evidence_digest` 与当前 Makefile recipe / smoke 内容不再匹配
- **THEN** lint 报该泳道验证证据失效并要求重跑 `verify-lane`

### Requirement: negative control 是强信号而非定义〔spec-review-amendment · ENG-8 · 设计门 Q3〕

negative control（抽掉依赖 → smoke 必红）**MUST NOT** 作为 `verified` 的充要定义（⟺）。

> **理由**：它只证明「命令**耦合**依赖」，**不证明「断言有效」**——smoke body 写 `assert True`，只要 harness 的 fixture 连不上 broker 就会 error，照样能拿到「正向绿 + 反向红」⇒ 被判 `verified`。且对 **testcontainers / 内嵌 fallback**（Go/Node 生态**主流**写法）完全免疫：`docker compose stop` 对它们毫无影响 ⇒ **永久误判 vacuous**。把一个右手边没有通用实现的等式写进 spec 当 ⟺，本身就是假绿。

**并行的两个机械门槛（两者独立，非替代）**：

| 门槛 | 适用 | 内容 |
|---|---|---|
| **① 测试真跑门槛（对所有泳道强制）** | 全部 | 解析 runner 的**结构化输出**（`go test -json` / pytest `collected N items`），**MUST 断言「本次至少跑了 ≥1 个测试且 0 skipped」**——否则正向绿**不成立**（`go test` 无匹配测试 → exit 0；pytest 全 skip → exit 0；recipe 是 `@echo TODO` → exit 0） |
| **② negative control（强信号，条件适用）** | `neg_control: applicable` | 仅对**抽离机制已定义**的依赖类生效；反向的红 **MUST 匹配依赖特定的 expected-failure predicate**——**普通非零不通过**（红可能来自端口冲突 / 配置错误 / 前置步骤失败，不证明 smoke 正确） |

**`neg_control` MUST 为独立字段**（`applicable | n/a — <理由>`），**MUST NOT** 通过清空 `deps` 来绕过。

> **理由**：一条被误判 vacuous 的泳道，操作者最省力的出路就是清空 `deps` ⇒ negative control 整个消失 ⇒ **把假阴性换成了真·假绿**；且删 `deps` 会连带毁掉 doctor 与依赖清单。`neg_control: n/a` **MUST 触发冷审专镜 + 人门单独确认**。

#### Scenario: 空转的测试不算绿
- **WHEN** 正向跑 exit 0，但结构化输出显示 collected 0 个测试（或全部 skipped）
- **THEN** 正向绿不成立，该泳道 MUST NOT 置 `verified`，`blocked_by` 记「未跑到任何测试」

#### Scenario: 反向的红必须对得上因
- **WHEN** 阴性对照跑出非零退出，但错误不匹配该依赖的 expected-failure predicate（如实为端口冲突）
- **THEN** 该次阴性对照**不作为通过证据**，如实记录并留人裁决

#### Scenario: 不能靠清空 deps 绕过
- **WHEN** 某泳道的 `deps` 被清空以规避 negative control
- **THEN** lint 检出「有外部依赖形态但 `deps` 为空」并报错；豁免 MUST 走 `neg_control: n/a — <理由>` 并触发冷审专镜

### Requirement: 执行边界与「不伤害」红线〔spec-review-amendment · ENG-3（CRITICAL）〕

**最高红线：skill MUST NOT 破坏操作者的机器状态。**

原设计只禁「装依赖」（**加法**，可手动撤销），却允许「停服务」（**减法，破坏性更强**）且**11 条失败模式表中无一条要求恢复**——smoke 超时 / 脚本崩溃 / 操作者 Ctrl-C ⇒ 依赖**永久停在停止态**，而 skill 转头去跑下一条泳道。本条堵死它。

**R1 · 只能停自己启动的东西**：每个依赖 MUST 声明 `owned_by: skill | operator`。**`owned_by: operator`（host service / 已在运行的 compose / 用户 `brew services` 起的 broker）→ MUST NOT stop**，一律拒绝。

**R2 · 首选隔离式阴性对照，停服务是最后手段**：抽离依赖 SHALL 优先用**不改变机器状态**的策略——把 endpoint 指向必定不可达的地址（如 `MQTT_URL=tcp://127.0.0.1:1`）。**信号强度等价，副作用为零**。仅当隔离式不可行、且 `owned_by: skill` 时，才允许「停服务」，且 MUST：跑前**单列显著呈现**「将停止服务 X」（不混在命令清单里）· `try/finally` 恢复 · **恢复失败 MUST 响亮报告并写进 `devenv-log.md`**。

**R3 · 超时 MUST 杀进程树**：runner SHALL 以独立 process group / session 启动子进程；超时先 TERM、限时后 KILL **整棵进程树**——否则 `docker compose up` 的孤儿容器继续占端口，下一条泳道拿到**假的「端口占用」**。容器等资源进 **cleanup ledger**，在 `finally` / SIGINT / SIGTERM 中回收；**cleanup 失败 MUST 是独立失败状态**，不能只写普通 `blocked_by`。

**R4 · 跑前列命令 MUST 连 recipe body 一起展开**：只给操作者看 `make integration` 这**一行调用**，对「那个 target 里到底跑什么」提供**零信息量**——人只能橡皮图章。SHALL 同时展开该 target 的 recipe（recipe 本就要为 source digest 锚解析，成本为零）。

**R5 · 失败 MUST NOT 重试、MUST NOT 进入 debug 循环**——skill 的职责是「建 + 验」而非「调通」；修复归下次 `continue`。

**R6 · 真硬件泳道 MUST NOT 尝试执行**——由 lane 的 `kind: hardware` **机械识别**（非靠模型自觉），`verify-lane` 直接 refuse 并指向 `embedded-test-sop`。

**R7 · MUST NOT 替操作者安装系统依赖**——只提供 doctor 脚本与安装命令。

**R8 · 命令输出 MUST 脱敏后落盘**〔ENG-12〕：命令继承 agent session 的**完整环境变量**，失败回显可能含 `AMQP_URL=amqp://user:pass@host` 之类 ⇒ 写进 `blocked_by` / `devenv-log.md` ⇒ **commit → push**。捕获输出 SHALL：截断（尾 N 行 / 大小上限）· 过 secret 正则打码 · **MUST NOT** 把环境变量 dump 进任何落盘文件。

#### Scenario: 拒绝停止操作者的服务
- **WHEN** 某依赖 `owned_by: operator`（如用户 brew services 起的 mosquitto），而阴性对照需要抽离它
- **THEN** skill MUST NOT 停止它；改用隔离式策略；若隔离式不可行则该泳道 `neg_control: n/a — 依赖为操作者所有，不可停`

#### Scenario: 中断也要恢复
- **WHEN** 阴性对照期间 smoke 超时 / 脚本抛异常 / 收到 SIGINT
- **THEN** 被抽离的依赖 MUST 在 `finally` 中恢复；恢复失败 MUST 响亮报告并写进 devenv-log

#### Scenario: 超时杀掉整棵进程树
- **WHEN** `make integration` 超时，其子进程已拉起 docker 容器
- **THEN** runner 杀掉整个进程组并按 cleanup ledger 回收容器，MUST NOT 留下孤儿占用端口

#### Scenario: 跑前展开 recipe
- **WHEN** skill 即将执行 `make integration`
- **THEN** 呈现给操作者的内容包含该 target 的 recipe body，而不只是 `make integration` 这一行

#### Scenario: secret 不进落盘文件
- **WHEN** 失败命令的 stderr 含形如 `PASSWORD=xxx` 的内容
- **THEN** 写入 `blocked_by` / devenv-log 前 MUST 打码

#### Scenario: 真硬件泳道机械拒绝执行
- **WHEN** 某泳道 `kind: hardware`
- **THEN** `verify-lane` 直接 refuse 执行（脚本判定，非模型自觉），置 `scaffolded` 并指向 `embedded-test-sop`

### Requirement: 落地物追加边界——skill 是追加者非拥有者

落地物（Makefile target / CI 配置 / 测试 harness / smoke / broker 启停脚本 / doctor）**MUST NOT 设托管区块**——它们是**人机共有的活文件**，人随时会改其实现。skill SHALL 只执行两个动作：**已有的 → 登记**（读出并写入 frontmatter 的 `source`，跑 smoke 验证）· **缺失的 → 追加**（新写，并带一行来源注释供审计）。

lint SHALL 只核验 `source` 指向的文件行**是否存在**，**MUST NOT 关心该行由谁写、内容如何**。

**重名冲突 → fail-closed**：欲追加的 target 名已存在但语义不符 → 脚本报冲突、留人裁决，**MUST NOT 静默覆盖**。

**门禁逻辑 SHALL 落在 Makefile（或等价项目脚本入口），CI 配置只做调用壳**（`- run: make integration`）——保证无 CI 的项目仍有完整本地门禁、CI 平台可换而门禁不变、本地与 CI 跑同一条命令。项目无 CI → CI 槽显式 `N/A` **并连带记后果**。

**归位模式的 smoke SHALL 从已有测试中选取一条作为锚**（`smoke:` 字段指向它），**MUST NOT 新写冗余 smoke**。

#### Scenario: 已有 target 只登记不接管
- **WHEN** 消费仓 Makefile 已有 `integration:` target 且语义即本泳道
- **THEN** skill 将其登记进 frontmatter（`source: "Makefile:11-14"`），不改写该 target 内容

#### Scenario: 重名语义不符时 fail-closed
- **WHEN** 欲追加的 target 名已存在但语义不是本泳道
- **THEN** 脚本报冲突并留人裁决，MUST NOT 静默覆盖

#### Scenario: 归位模式复用已有测试当 smoke
- **WHEN** 归位模式下该泳道已有可用测试
- **THEN** `smoke:` 指向该已有测试文件，不新写 smoke

### Requirement: 归位模式——素材盘点、判归属、删源

归位模式 SHALL 在事实采集前插入「素材盘点 → 判归属 → 搬运表」，其后与新建模式共用后半段。

**搬运表 MUST 先给操作者确认再落笔**——归属判定是全流程**唯一无确定性信号**的一步，人门 SHALL 放在此处，**MUST NOT 放在末尾审文档**。

删源 SHALL 区分**三种处置**，并以 `grep` 被引用面作判据：引用数为 0 → 可直接删；引用可枚举 → 改掉这些引用后删；引用面广/散 → **降为一行指针**。三种处置分别为：**整体删除** / **部分保留 + 改写** / **降为一行指针**。

搬运表 **SHALL 单列一节「以下 N 个文件将被整体删除」显著呈现**，**MUST NOT 只在表格行内标记而埋进长消息**。

**删源 MUST fail-closed 要求工作区干净**（`git status` 非空 → 拒绝，提示先 commit 或 stash）——否则误删后 `git revert` 会波及操作者其他未提交改动，「可回滚」承诺不成立。

删源后 SHALL 扫描残留引用，**覆盖代码注释**（非仅 Markdown 链接）。

#### Scenario: 搬运表先确认再落笔
- **WHEN** 归位模式完成素材盘点与归属判定
- **THEN** skill 呈现搬运表并等待操作者确认，确认前 MUST NOT 写入或删除任何文件

#### Scenario: 工作区不干净时拒绝删源
- **WHEN** 归位模式将删源但 `git status` 显示有未提交改动
- **THEN** skill fail-closed，提示先 commit 或 stash，MUST NOT 执行删除

#### Scenario: 引用面广者降为指针
- **WHEN** 某待删源文件被十余处引用
- **THEN** skill 提议降为一行指针而非整体删除，由操作者拍板

#### Scenario: 删源后扫残留引用含代码注释
- **WHEN** 源文件已删除
- **THEN** skill 扫描全仓残留引用，覆盖代码注释中的路径引用

### Requirement: 冷审与人门

冷审 **MUST 由 fresh 子代理执行**（Agent 工具），**禁止生成 session 自查**（自证偏差）。冷审 SHALL 按 `references/review-lenses.md` 取镜，至少覆盖：**覆盖镜**（SAD 哪条 contract 未被任何泳道穿过 / `covers` 声明是否真命中）· **vacuous 镜**（smoke 是否语义恒真）· **边界镜**（架构决策是否漏进 environments / 阶段计划是否漏进 testing-strategy）· **诚实镜**（`planned` 是否被伪装成 `verified` / `blocked_by` 是否敷衍）；**归位模式加删源镜**（源文件是否真删、残留引用是否扫净）。

冷审失败 SHALL 重派一次；再失败 SHALL **显式报告缺口**，**MUST NOT 无冷审静默过人门**。宿主无 fresh 子代理原语时 SHALL **显式降级并响亮留痕**，**MUST NOT 佯装冷审**。

**人门 MUST 拆成两道，且 diff 门 MUST 在执行之前**〔spec-review-amendment · ENG-7〕：

> **理由**：原设计的时序是「写落地物 → 跑 smoke → 跑阴性对照 → … → 人门（含 diff 过目）」——**模型生成的 recipe body 与 smoke 源码，在任何人看过一眼之前就已经被执行了**。而「跑前列命令给操作者过目」给人看的是 `make integration` 这**一行调用**，对「target 里到底跑什么」提供**零信息量**。真正危险的内容恰恰不在那个门里。

| 门 | 位置 | 议程 |
|---|---|---|
| **③-pre（执行前）** | 写完落地物、**跑 smoke 之前** | **落地物 diff 过目**（含 recipe body 与 smoke 源码全文）+ 将执行的命令清单（**recipe 展开**）+ 「将停止服务 X」的显著呈现（若有）。**这是真正的最后一道护栏。** **否决 → MUST 回退本次追加的改动**（工作区干净是前置，`git checkout -- <files>` 可行），MUST NOT 带着被否决的代码继续执行 |
| **④（执行后）** | 冷审之后 | ① 泳道设计复核 ② 未 `verified` 泳道逐条确认（接受现状 / 现在装依赖）③ N/A 槽逐条确认 ④ 归位模式：**删源清单确认**（含 backup manifest 位置） |

#### Scenario: 生成的代码在执行前被人看过
- **WHEN** skill 写完 Makefile target 与 smoke 源码
- **THEN** 在执行任何 smoke 之前，先呈现完整 diff（含 recipe body 与 smoke 全文）供操作者过目

#### Scenario: 否决 diff 则回退
- **WHEN** 操作者在 ③-pre 否决落地物 diff
- **THEN** skill 回退本次追加的改动，MUST NOT 继续执行 smoke

#### Scenario: 冷审必须 fresh 子代理
- **WHEN** 进入冷审步
- **THEN** skill 派 fresh-context 子代理执行，主 session MUST NOT 自查

#### Scenario: 落地物 diff 必过人门
- **WHEN** skill 已写入 Makefile / harness / smoke 等真代码
- **THEN** 人门议程含 diff 过目，操作者确认后才进入收尾

### Requirement: lint 的触发点——挂 `sdflow-maintain`〔spec-review-amendment · CEO-2（CRITICAL）· 设计门 Q6〕

`devenv_lint` **MUST 有自动触发点**：`sdflow-maintain` 在扫描 `openspec/` 一致性时 **SHALL 调用它**，报告：未 `verified` 的泳道清单 · 失配的 source digest · 空 `blocked_by` · 失效的执行证据。

> **理由（dogfood 自指坑）**：本 change 把「无门禁——`assert-bindings` 这类检查无任何自动触发点，全靠人记得跑」列为**立项理由之一**，而原设计的 `devenv_lint` **自己也没有任何触发点**（与 `ship_gate` / `sdflow-done` / `sdflow-maintain` 零集成）。
>
> 更致命：**「渐进 DoD」允许泳道停在 `scaffolded`，而防止它烂成僵尸文档的唯一措施就是「lint 复述未完成清单」——若无人调用该 lint，该措施为空，前提结构性不成立。**「不强制完成」+「不检查未完成」= **名存实亡**，两者只能选一个。
>
> **诚实边界**：`sdflow-maintain` 是**人主动跑**的 ⇒ 本条提供的是「**更响的提醒**」而非**硬门禁**。此局限 MUST 显式登记，**MUST NOT 佯装硬拦截**（是否再加 `ship_gate` 硬拦截 → proposal Q-5）。

#### Scenario: maintain 扫描调用 devenv lint
- **WHEN** 在已有 `environments.md` 的消费仓运行 `sdflow-maintain`
- **THEN** 其扫描结果包含 devenv 健康度：未 verified 泳道清单、失配的 source digest、空 blocked_by

#### Scenario: 真实回归被拦下
- **WHEN** 操作者修改了某 `verified` 泳道对应的 Makefile recipe（digest 失配）
- **THEN** 下次 `sdflow-maintain` 扫描报出该泳道验证证据失效，要求重跑 `verify-lane`

### Requirement: 机械 lint 五条与诚实输出

`devenv_lint.py` SHALL 执行五条机械检查：① **命令出处一致性**（按 **selector 重定位 + digest 比对**，**MUST NOT** 用行号存在性——见「digest 出处锚」）② **指针不悬空**（Markdown 链接 + 章节锚可达）③ **删源残留引用**（含代码注释）④ **N/A 显式性**（槽在但内容空 → 报错；显式 `N/A — <理由> + <后果>` 才通过）⑤ **入口复述检测**（README/CLAUDE 出现真相源才该有的完整命令表 → 告警）。

另 SHALL 断言：`verified` ⇒ **执行证据齐全且未失效**、**`blocked_by` 必须为空**〔ENG-15：绿泳道上挂着「本机无 mosquitto」= 文档在说谎〕；`scaffolded` ⇒ `blocked_by` 非空。

lint 通过码 SHALL 带诚实后缀（如 `structure-ok-SEMANTICS-UNCHECKED`）——**lint 通过 = 结构性通过 ≠ 内容已审**；内容质量由冷审 + 人门守。

lint SHALL 按泳道状态分档核验：`verified` → 强制①；`scaffolded` → 强制 `smoke` 文件存在 + `blocked_by` 非空；`planned` → 不核验命令出处。

#### Scenario: verified 泳道 source 失效被抓
- **WHEN** 某 `verified` 泳道的 `source` 指向的 Makefile 行已不存在
- **THEN** lint fail-closed 并报出该泳道

#### Scenario: N/A 未记后果被抓
- **WHEN** CI 槽写了 `N/A` 但未记录其留下的后果
- **THEN** lint 报错

#### Scenario: lint 通过码诚实
- **WHEN** lint 全部机械检查通过
- **THEN** 输出的通过码明示「结构通过，语义未核」

### Requirement: 泳道数据落 JSON 侧文件与 digest 出处锚〔spec-review-amendment · ENG-5/ENG-4 · 设计门 Q4〕

**泳道数据 MUST NOT 放 `environments.md` 的 frontmatter**，SHALL 落 `openspec/architecture/.devenv-lanes.json`（**标准库 `json`，零依赖，round-trip 无损**）。

> **理由**：原设计的嵌套 `lanes[]`（8 键 × 含列表 × 含中文自由文本 × 含带冒号的值）**没有可用的解析/序列化方案**——目标环境**无 PyYAML**（本仓零第三方依赖，skill 靠 symlink 直接跑、无安装环节），而唯一先例 `sad_schema.parse_frontmatter` 是**手搓的扁平标量解析器**（固定键白名单，无列表、无引号处理），写侧是**行级正则改写**——这套手法在嵌套结构上完全用不了。

`environments.md` 的 frontmatter 只留三个**扁平标量**：`sad`（`present|missing`）· `mode`（`greenfield|brownfield`）· **`schema_version`**（`<int>`，原设计漏了；monorepo 演进要动 schema，无版本键则存量文件无升级路径）。

**`deps` MUST 为结构化描述符，lane MUST 有 `kind`**〔ENG-2（CRITICAL）〕：

```json
{
  "id": "mqtt-integration",
  "kind": "external-dep | ui | lang-bridge | hardware | pure",
  "status": "planned | scaffolded | verified",
  "neg_control": "applicable | n/a — <理由>",
  "deps": [
    {"name": "mosquitto",
     "kind": "compose | host-service | port | toolchain | testcontainer",
     "up": "<启动命令>", "down": "<抽离命令>",
     "owned_by": "skill | operator",
     "isolate": "<隔离式抽离：如 MQTT_URL=tcp://127.0.0.1:1>"}
  ]
}
```

> **理由**：原设计 `deps: [<name>...]` 是**裸字符串没有类型**，而 Q-4 却说要「按 `deps` 声明的类型分派」——**数据模型里根本没有类型这个信息**。给定 `["mosquitto"]`，执行器无从知道它是 compose 服务 / brew service / testcontainer ⇒ 只能猜，或回去问模型 ⇒ **「机械分派」变回模型判断**。
>
> 同一个洞炸掉另一条 MUST：原设计的 lane **无 `kind` 字段** ⇒「真硬件泳道 MUST NOT 执行」**无法机械识别**，只能靠模型自觉——而它防的恰恰是模型把烧板命令跑起来。

**`kind: hardware` ⇒ `verify-lane` 直接 refuse 执行**（脚本判定）。**`deps[].kind: toolchain`（编译器 / protoc / node）⇒ negative control 显式 `n/a`**——**你无法「抽掉」一个编译器**。原 Q-4 的三条策略（compose stop / 不启动进程 / 坏端口）只覆盖「可控的网络服务」，约为依赖空间的一半；toolchain / env 凭证 / host CLI 二进制 / 浏览器 / GPU **一条都没覆盖**——不在数据模型里给 `n/a` 通道，实现期必然现场编 per-dep hack。

**出处锚 MUST 按内容（digest），MUST NOT 按行号**：

```
source: {file: <path>, kind: make-target|npm-script|toolchain, selector: <target 名>, digest: <recipe 规范化后的 sha256 前缀>}
```

> **理由**：原设计的 `source: "Makefile:11-14"` + lint「查那行存不存在」——**「第 11-14 行存不存在」对任何长度 ≥14 行的文件恒为真**。用户在 Makefile 顶部插三行 ⇒ 锚点全部错位、lint 全绿、命令表继续声称出自那四行。**这是一个恒真断言，即设计好的假绿。**

lint SHALL 用 parser 按 `selector` **重新定位** target，比对 recipe digest；**行号仅在 render 时动态生成供阅读，不作真相**。digest 失配 ⇒ 报「该 target 的实现已被改动，请复核 `command` 是否仍准确并重跑 `verify-lane`」——这才是要抓的东西（**命令表说谎**），而非「行没了」。

正文的命令表 SHALL 由 `devenv_scaffold.py render` **从 `.devenv-lanes.json` 渲染**，带 `DO NOT EDIT` banner，**MUST NOT 由人手写**。

#### Scenario: 行号变动不导致假绿
- **WHEN** 操作者在 Makefile 顶部插入三行变量定义，使原 11-14 行指向不同内容
- **THEN** lint 按 selector 重新定位 target 并比对 digest，digest 未变则通过、变了则报「实现已改动」；**MUST NOT** 因「11-14 行仍存在」而静默通过

#### Scenario: 零第三方依赖
- **WHEN** 在无 PyYAML 的环境运行 skill
- **THEN** 泳道数据读写正常（走标准库 json），skill 不因缺少第三方依赖而失败

### Requirement: 文档渲染与两文档边界

skill SHALL 产出两份真相源，落 `openspec/architecture/`（与 `sad.md` 同居），**MUST NOT 落项目根或 `docs/`**：`environments.md`（操作轴）· `testing-strategy.md`（方法轴）。

skill SHALL 产出两份真相源，落 `openspec/architecture/`（与 `sad.md` 同居），**MUST NOT 落项目根或 `docs/`**：`environments.md`（操作轴：dev / test / deploy）· `testing-strategy.md`（方法轴：分层 / contract 集成点 / mock 边界 / 护栏 / 盲区）。

两文档边界 SHALL 守切线：**方法/决策 → testing-strategy；环境/操作 → environments**。架构决策 MUST 引用 SAD 不复述；阶段计划 MUST 归 roadmap 不写入 testing-strategy。

`environments.md` 的每条命令 SHALL 带**出处**；**N/A 槽 SHALL 连带记录其留下的后果**。

#### Scenario: 命令表机械渲染
- **WHEN** frontmatter 中某泳道状态由 scaffolded 变为 verified
- **THEN** 正文命令表经 render 重新生成并反映新状态，人无需手改正文

#### Scenario: 落位与 SAD 同居
- **WHEN** skill 产出两份真相源
- **THEN** 文件落在 `openspec/architecture/` 下，而非项目根或 `docs/`

### Requirement: 入口托管注入使用独立 marker

skill SHALL 将「最小命令 + 指针」注入消费仓入口文件（CLAUDE.md / AGENTS.md / README.md）与 `openspec/INDEX.md`，使用**自己的 marker token `opsx-devenv`**（`<!-- opsx-devenv:start -->` … `<!-- opsx-devenv:end -->`），采用 token 定位 + 幂等整块替换语义。

**MUST NOT 写入 `opsx-init` 的托管区块**——注入是整块替换，共用同一 marker 会使两个 skill 互相覆盖。

入口文件 **MUST NOT 复述**真相源细节（完整命令表 / 配置项表），只放最小起步命令 + 指针。

#### Scenario: 独立 marker 不干扰 init 区块
- **WHEN** 消费仓已有 `opsx-init` 托管区块且 skill 执行注入
- **THEN** skill 只创建/替换 `opsx-devenv` 区块，`opsx-init` 区块内容不受影响

#### Scenario: 重复注入幂等
- **WHEN** skill 二次触发并再次注入
- **THEN** 既有 `opsx-devenv` 区块被原位替换，不产生重复区块

### Requirement: 并发安全写入〔spec-review-amendment · ENG-6/ENG-10〕

所有落盘 **MUST 原子写**（`mkstemp` 唯一 tmp 名 + `os.replace`）；读-改-写序列 **MUST 持锁**，**MUST NOT** 以「读入内存 → 改 → 覆写」的裸序列执行。

**锁 MUST 覆盖整个 `openspec/` 写域，三个 skill 共用同一锁名**（如 `openspec/.sdflow-write.lock`）。

> **理由（互斥性不可组合）**：原设计给 devenv 单发一把 `.devenv-scaffold.lock`，与 `sad_scaffold` 的 `.sad-scaffold.lock` **是两把不同的锁**——但两者的写入面**重叠**（都注入 CLAUDE/AGENTS/README/INDEX）。且核验 `sdflow-init/scripts/init.py:126`：其 `inject()` 是**裸 `open(path,"w")` 全量覆写，无锁、无原子写** ⇒ devenv 注入 ‖ `/sdflow-init update` 覆写同一文件 ⇒ **devenv 的整块注入被静默吃掉**。「复用已验证机制」≠「**互斥性可组合**」。
>
> 本 change SHALL **顺带给 `init.py` 的 inject 补锁 + 原子写**（承基准 3：面治优先于点补——撞到的相邻漏网格一次扫全，而非给 devenv 发一把没人认的锁）。

**锁 MUST 短持有，MUST NOT 跨 smoke 执行持有**〔ENG-10〕：

> **理由**：`sad_scaffold` 的锁参数为**亚秒级**操作而调（`STALE=120s`），而 devenv 的 smoke 可跑数分钟 ⇒ 锁若跨 smoke 持有，**并发 session 会把活锁判成残留锁** → 提示用户「删锁重试」→ 用户照做 → **两 session 同时写**。**陈旧锁检测由保护变成攻击面。**

**状态写入 MUST 用 CAS**：`set-lane` / `verify-lane` SHALL 接受 `--expect <prior-status>`，锁内重读、lane 不存在或状态 ≠ expect ⇒ **exit 5 拒绝**（防真正的临界区——「模型读 lanes → 跑 smoke（进程外，长时间） → 写 status」——发生 lost update）。回写 MUST **只 patch 那一条 lane**，MUST NOT 用内存快照覆写整份 lanes。

锁文件 MUST 记 owner（UUID + PID + 时间戳）；释放前**核对 owner**，**MUST NOT** 删除他人的锁。

`devenv-log.md` SHALL 为 **append-only**；`--line` 含换行符 SHALL 被拒绝（防伪造审计行）。

#### Scenario: 跨 skill 并发不丢注入
- **WHEN** devenv 正在注入 CLAUDE.md，另一 session 同时跑 `/sdflow-init update`
- **THEN** 两者经同一把 `openspec/` 写域锁串行化，任一方的托管块 MUST NOT 被静默覆盖

#### Scenario: CAS 拒绝陈旧写入
- **WHEN** 模型基于旧快照调 `set-lane --expect scaffolded`，但期间另一 session 已把该 lane 改成 planned
- **THEN** 脚本 exit 5 拒绝，提示重读后重试

#### Scenario: 锁不跨长跑持有
- **WHEN** 某泳道的 smoke 需跑 5 分钟
- **THEN** 锁在 smoke 执行期间**不被持有**（只在写状态的瞬间持有），并发 session 不会把它误判为残留锁

### Requirement: 归位模式的删源护栏〔spec-review-amendment · codex-Eng · 设计门 Q1 的连带义务〕

> **设计门 Q1 拍定：归位模式留在本 change。** 代价是删源护栏 MUST 从「工作区干净」升级——**clean worktree 并不足以保护删除**：它不保证仓库有有效 HEAD、不保证待删文件已 tracked、不保护 ignored 文件 / submodule / symlink。

删除任一源文件前，skill **MUST 逐文件校验**：

1. 仓库有**有效 HEAD**（非 unborn branch）
2. 该文件**已 tracked**（untracked 文件删了 git 恢复不了）
3. **非 submodule、非 symlink**
4. 其**内容 digest 与搬运表人门确认时一致**（防确认后被改动）

任一项不满足 ⇒ **fail-closed 拒绝删除该文件**，如实报告原因。

删除前 SHALL 生成**可恢复的 backup manifest**（被删文件的路径 + 内容 digest + 可还原的 patch），落 `openspec/architecture/.devenv-backup/`，并在收尾对话中告知还原方式。

#### Scenario: untracked 文件拒绝删除
- **WHEN** 搬运表中某待删源文件未被 git tracked
- **THEN** skill fail-closed 拒绝删除该文件，提示先 `git add` 或手动处理

#### Scenario: 确认后被改动则拒删
- **WHEN** 搬运表人门确认后、执行删除前，某待删文件内容发生变化（digest 不符）
- **THEN** skill 拒绝删除该文件并要求重新确认

#### Scenario: 删除可还原
- **WHEN** 归位模式执行了删源
- **THEN** `.devenv-backup/` 下存在可还原的 backup manifest，且收尾对话告知还原方式

### Requirement: 触发分工与前置声明

`sdflow-devenv` 的 description SHALL 聚焦环境词面（定测试策略 / 搭开发环境 / 建测试环境 / 配 CI / 加测试泳道 / 这个项目怎么测），并含与 `sdflow-init` 的分流判据句：**装 workflow 流程规则 → `/sdflow-init`；建项目 dev/test 环境 → `/sdflow-devenv`**（消解「初始化环境」这一词面在两 skill 间的触发冲突）。

description SHALL 注明前置：需已 `sdflow-init`（无 `openspec/` 布局 → fail-closed）；**建议**先 `sdflow-architecture`（无 SAD → 降级可跑）。

真硬件泳道 SHALL 指向既有 `embedded-test-sop`，**MUST NOT 重造**手动测试 SOP。

#### Scenario: description 含与 init 的分流句
- **WHEN** 检查 `sdflow-devenv/SKILL.md` 的 description
- **THEN** 其中含「装流程规则 → init；建项目 dev/test 环境 → devenv」判据句与两条前置声明

#### Scenario: 真硬件泳道复用既有 skill
- **WHEN** 项目命中真硬件依赖形态
- **THEN** skill 指向 `embedded-test-sop`，不自行产出手动测试 SOP
