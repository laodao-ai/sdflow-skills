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

### Requirement: smoke 真跑与 negative control

`verified` 的判定 SHALL 由**脚本执行验证**得出，**MUST NOT 由模型自称**。判据为**双向**：

```
verified ⟺ 依赖就绪时 smoke 绿 ∧ 抽掉依赖时 smoke 红
```

第二条即 **negative control**：一条泳道的 smoke 价值在于**真穿过它的依赖**，故抽掉依赖（不启动 broker / 容器）后它 **MUST 红**；**抽掉依赖仍绿 ⇒ 该 smoke 未真正穿过依赖（vacuous）⇒ MUST NOT 置 `verified`**。

`deps` 为空的泳道（纯逻辑 / 无外部依赖）**豁免** negative control，退回「smoke 含断言语句」这一最低机械门槛 + 冷审。

#### Scenario: 抽掉依赖仍绿判为 vacuous
- **WHEN** 某泳道 `deps: ["mosquitto"]`，停掉 mosquitto 后 smoke 仍然通过
- **THEN** skill 判该 smoke 为 vacuous，该泳道 MUST NOT 置 `verified`，并记录该判定

#### Scenario: 双向判据成立才置 verified
- **WHEN** 依赖就绪时 smoke 绿且抽掉依赖时 smoke 红
- **THEN** 该泳道置 `verified`

#### Scenario: 无依赖泳道豁免阴性对照
- **WHEN** 某泳道 `deps: []`
- **THEN** 仅以「smoke 绿 + 含断言语句」为判据，不执行 negative control

### Requirement: smoke 执行边界

skill 跑 smoke SHALL 遵守四条边界：

1. **跑前先列出将执行的命令给操作者过目**，MUST NOT 偷跑——尤其会起容器 / 占端口者；操作者可指定跳过某条（该泳道留 `planned`）。
2. **每条命令 SHALL 设超时**；超时 → `scaffolded` + `blocked_by` 如实写明「超时，未确认是环境问题还是 smoke 本身挂了」。
3. **失败 MUST NOT 重试、MUST NOT 进入 debug 循环**——跑一次，失败即如实记 `blocked_by`（原始报错摘要 + 修复指引）。skill 的职责是**「建 + 验」而非「调通」**；修复归下次 `continue`。
4. **真硬件泳道 MUST NOT 尝试执行**（需烧板）→ 直接 `scaffolded` + 指向 `embedded-test-sop` 的手动 SOP。

skill **MUST NOT 替操作者安装系统依赖**（如 `brew install` / `docker pull` / `npx playwright install`）——只提供 doctor 脚本与安装命令。

#### Scenario: 执行前列命令
- **WHEN** skill 即将执行会启动 Docker 容器的 smoke
- **THEN** skill 先列出该命令请操作者过目，获得同意后才执行

#### Scenario: 失败不进 debug 循环
- **WHEN** 某条 smoke 首次执行失败
- **THEN** skill 如实记录 `blocked_by`（含报错摘要与修复指引）并继续下一条泳道，MUST NOT 反复重试或自行 debug

#### Scenario: 不替操作者装依赖
- **WHEN** 检出本机缺少某系统依赖
- **THEN** skill 输出安装命令与 doctor 指引，MUST NOT 自行执行安装

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

人门 SHALL 按固定议程逐条过：① 泳道设计复核 ② 未 `verified` 泳道逐条确认（接受现状 / 现在就装依赖）③ **落地物 diff 过目**（真代码进仓的最后一道人类护栏）④ N/A 槽逐条确认（是现状还是该有而没建）。

#### Scenario: 冷审必须 fresh 子代理
- **WHEN** 进入冷审步
- **THEN** skill 派 fresh-context 子代理执行，主 session MUST NOT 自查

#### Scenario: 落地物 diff 必过人门
- **WHEN** skill 已写入 Makefile / harness / smoke 等真代码
- **THEN** 人门议程含 diff 过目，操作者确认后才进入收尾

### Requirement: 机械 lint 五条与诚实输出

`devenv_lint.py` SHALL 执行五条机械检查：① **命令出处一致性**（`verified` 态泳道的 `source` 指向行必须存在）② **指针不悬空**（Markdown 链接 + 章节锚可达）③ **删源残留引用**（含代码注释）④ **N/A 显式性**（槽在但内容空 → 报错；显式 `N/A — <理由> + <后果>` 才通过）⑤ **入口复述检测**（README/CLAUDE 出现真相源才该有的完整命令表 → 告警）。

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

### Requirement: 文档渲染与单一真相源

泳道的 `command` / `source` / `status` / `deps` / `covers` / `blocked_by` SHALL 以 `environments.md` 的 **frontmatter 为唯一机械真相源**。正文的命令表 SHALL 由 `devenv_scaffold.py render` **从 frontmatter 渲染**，并带 `DO NOT EDIT` banner，**MUST NOT 由人手写**——两处各写一遍必漂移。

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

### Requirement: 并发安全写入

`environments.md` / `testing-strategy.md` / `devenv-log.md` 的写入 SHALL 防并发损坏（**两个 session 同时跑本 skill 会撞车**）：所有落盘 **MUST 原子写**（temp + rename）；对同一文件的读-改-写序列 **MUST 持锁**（如 exclusive-create lock），**MUST NOT** 以「读入内存 → 改 → 覆写」的裸序列执行。

`devenv-log.md` SHALL 为 **append-only**，MUST NOT 改写既有行；`--line` 值含换行符 SHALL 被拒绝（防伪造审计行）。

#### Scenario: 并发写不丢更新
- **WHEN** 两个进程同时对同一 `environments.md` 执行 set-lane
- **THEN** 两次更新均不丢失，或后者显式失败提示重试，MUST NOT 静默覆盖前者

#### Scenario: log 拒绝多行值
- **WHEN** 留痕 `--line` 的值含换行符
- **THEN** 脚本以坏输入退出码拒绝

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
