## ADDED Requirements

> **总则（凌驾于以下所有 Requirement）〔设计门 round-2〕**
>
> **无法明确确定的问题 → 模型研究并提方案 → 人确认。**
>
> skill 的机械层 **SHALL 只保证「过程完整」与「诚实」**——有没有验证方法 · 执行了没 · 证据是不是执行者本人写的 · 状态有没有撒谎。
> 机械层 **MUST NOT 试图替人判断「这个方案好不好」「这个验证有没有效」**。
>
> **MUST NOT 硬凑假机械**：凡机械够不着的（验证方法是否有效 · 依赖分类是否属实 · smoke 断言是否语义恒真 · `covers` 是否真命中），**一律诚实划归语义层**（模型提 + 人拍 + 冷审），**MUST NOT** 用枚举 / dispatch 表 / 白名单包装成"脚本判定"。
> **假机械比诚实的语义层更危险**——它让人以为有防线。

---

### Requirement: preflight 两级与三模式分流

skill 每次触发 SHALL 先跑 `devenv_scaffold.py init`，按退出码分流，MUST NOT 自造半套布局、MUST NOT 静默继续。

- **无 `openspec/` 布局 → fail-closed**（exit 3）：原样转述 preflight 指引（先 `/sdflow-init`）。
- **`sad.md` 缺失 → 显式降级，不 fail-closed**：SHALL 响亮警告「拿不到子系统 contract 清单与外部依赖清单，泳道覆盖对账失效、依赖形态只能靠读码猜，可能漏边界；建议先 `/sdflow-architecture`」，并在 `environments.md` frontmatter 留痕 `sad: missing`，然后继续。**MUST NOT 佯装有 SAD**。
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

**时序纪律**：**MUST 实际向操作者提问并获得人的回答之后，才允许记录；MUST NOT 预填、MUST NOT 替操作者臆测答案。**

SAD 投影出的候选事实 SHALL **批量呈现**为「结论 + 出处（SAD §x）」的一次性清单供操作者一次确认/挑错，**MUST NOT 逐条单独提问**（那是把架构阶段问过的话再问一遍）；**只有无源事实才逐条提问**——那才是真正需要操作者输入新信息的地方〔DX〕。

#### Scenario: SAD 有源事实需人复核
- **WHEN** SAD 存在且含 §2 约束与 §3 外边界
- **THEN** skill 把投影出的候选事实**批量**呈现给操作者复核，操作者确认或修正后才记录

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

### Requirement: 验证方法——模型研究提方案，人拍板〔设计门 round-2 · 核心〕

**每条泳道 MUST 有一个验证方法。** 验证方法 SHALL 由**模型根据该项目的实际开发/测试环境现场研究并推荐**（依赖形态 · 可用工具 · 平台约束 · 已有测试资产），**由操作者拍板**。

> **为什么不在 spec 里枚举验证方法**：本 skill 的前一版把 negative control（抽掉依赖 → smoke 必红）写成 `verified` 的**定义**，随即被迫为它发明 `isolate` 字段 / `expected-failure predicate` / `kind → 策略 dispatch` / runner 白名单——**一整片复杂度，全是在给一个不该被钉死的答案打补丁**，且其中数个"机械判定"的输入根本是模型自填的裸声明（假机械）。
>
> 真实项目的验证方法**由环境决定，不可预先枚举**。spec 能定的只有**证据的形状**，不是方法的清单。

**验证方法 SHALL 有明确的执行者（`executor`），二者其一**：

| `executor` | 含义 | 证据由谁写 |
|---|---|---|
| `script` | 方法可被脚本确定性执行（一条/一组可跑的命令 + 明确的通过判据） | **`verify-lane` 脚本自己 fork 执行后写入**，模型 MUST NOT 填 |
| `human` | 方法只能由人执行（真硬件烧板 · 平台不支持脚本执行 · 依赖生命周期内嵌不可插桩 · 需人眼判断的 UI/交互） | **人门流程写入**，模型 MUST NOT 代填 |

> **「无法验证」不是一个合法状态**——**人工测试也是验证方法**。任何泳道都能找到验证方法，区别只在 `executor` 是 `script` 还是 `human`。故本 spec **不设** `n/a` 通道。

**`verification.method` 为空 ⇒ lint fail-closed**——**不允许存在「不知道怎么验」的泳道**。

模型 SHALL 在提出验证方法时**如实说明其强度与盲区**（如「本方法只证明命令耦合了依赖，不证明断言有效」），**MUST NOT** 把弱信号说成强保证。`references/verification-patterns.md` 提供参考实例（**标注「实例，非规格」**），含已知的**负面知识**（如：轮询式连接观测对瞬时连接漏检率极高，不可作为判据；任何外部插桩都无法证伪语义恒真的断言）。

#### Scenario: 模型提方案人拍板
- **WHEN** skill 为某条外部依赖泳道设计验证方法
- **THEN** 模型根据该项目实际环境研究并推荐具体方法（含强度与盲区说明），呈交操作者拍板，操作者确认后才写入 `verification.method`

#### Scenario: 无验证方法的泳道被拒
- **WHEN** 某泳道的 `verification.method` 为空
- **THEN** `devenv_lint` fail-closed 并报出该泳道

#### Scenario: 脚本验不了的走人工验证
- **WHEN** 某泳道的依赖生命周期内嵌在 Makefile recipe 的字面文本里，无法被脚本插桩
- **THEN** 模型如实说明脚本化验证不可行，提出人工验证步骤，`executor: human`，该泳道**仍可**推进到 `verified`（经人门确认）

### Requirement: 测试策略框架——三层必答，无一层可留白〔设计门 round-2 · 操作者补充〕

**核心承诺：不管什么项目，操作者跑完 skill 都拿到一份完整的测试与验证策略框架。**

`testing-strategy.md` **MUST 覆盖测试三层**，**一层都不许留白**：**单元测试** · **集成测试** · **端到端（e2e）测试**。

每一层 **MUST 回答以下五个槽**（模型根据本项目实际环境研究并推荐，**由人拍板**）：

| 槽 | 内容 |
|---|---|
| **① 本项目怎么实现** | 框架 / 库 / 工具选型（模型现场调研推荐，**MUST NOT** 由 spec 预先钉死） |
| **② 测试规范** | 测试写在哪（目录/命名约定）· 什么算一个用例 · 该覆盖什么、不该覆盖什么 |
| **③ 测试方法与流程** | 怎么跑（命令）· 什么时候跑（本地/CI/提交前）· 谁来跑 |
| **④ 需要配备的工具与脚本** | 要装什么依赖 · 要写什么脚本/harness/fixture（**这些即落地物**） |
| **⑤ 状态** | **`已实现`** / **`不适用`** / **`人工`**（三选一，见下） |

**⑤ 状态的三态，各有强制附带项**：

| 状态 | 含义 | **MUST 附带** |
|---|---|---|
| `已实现` | 该层已有可跑的入口 | 对应**泳道**（`lanes[]` 中的一条或多条）+ 其命令与出处 |
| **`不适用`** | 该层在本项目**确实不需要** | **理由 + 后果**——「不做这层，我们因此看不见什么」。**MUST NOT 只写 `N/A` 了事** |
| **`人工`** | 该层无法自动化，需人执行 | **用户按什么方式来做**——具体步骤 / 检查清单 / 何时执行。**MUST NOT 只写「人工测试」四个字** |

> **为什么 `不适用` 必须写后果**：一个纯库项目可能真的没有 e2e——但「没有 e2e」意味着「集成后的真实使用路径无人验证」。**不写后果，`不适用` 就成了一个不需要负责的逃生舱**；写了后果，它才是一个**被知情接受的取舍**。
>
> **为什么 `人工` 必须写"怎么做"**：`人工` 不是"这层没人管"的同义词——**人工测试也是测试方法**（见「验证方法」Requirement 的总则）。它必须像自动化测试一样可复述、可交接、可执行。

**三层与泳道的关系**：`testing-strategy.md` 是**策略与框架**（方法轴：怎么测），`environments.md` 是**操作**（操作轴：怎么跑），`lanes[]` 是**机械真相源**，把两者连起来——**一条泳道 = 某一层的一个可执行入口**。`已实现` 的层 MUST 至少对应一条泳道；`人工` 的层对应 `executor: human` 的泳道。

**框架是活的，MUST 可迭代**：`testing-strategy.md` **MUST NOT** 被当作一次性定死的文档。开发过程中随时可 `continue` / `replan` 调整（某层从 `不适用` 变 `已实现`、工具选型换掉、规范收紧）。**首跑拿到"有方向和基本能力"的框架即达标**，不要求三层全绿。

**SAD 缺失时的降级**：无 SAD ⇒ 集成层的 contract 锚（`covers`）失效 ⇒ **该层的"该覆盖什么"只能靠读码猜** ⇒ **MUST 显式标注此局限**，MUST NOT 佯装覆盖完整。

#### Scenario: 三层全部有交代
- **WHEN** skill 产出 `testing-strategy.md`
- **THEN** 单元 / 集成 / e2e 三层各自的五个槽全部有内容，无一层留白

#### Scenario: 不适用必须记后果
- **WHEN** 某纯算法库项目的 e2e 层被判为不适用
- **THEN** 该层写明 `不适用 — <理由>`，**并连带写出后果**（「集成后的真实使用路径无人验证」），lint 检出「只写 N/A 未记后果」则报错

#### Scenario: 人工层必须写清人怎么做
- **WHEN** 某嵌入式项目的 e2e 层只能靠人烧板实测
- **THEN** 该层状态为 `人工`，并写明用户按什么步骤执行（指向 `embedded-test-sop`）、何时执行、检查什么，MUST NOT 只写「人工测试」

#### Scenario: 已实现的层必须落到泳道
- **WHEN** 某层状态为 `已实现`
- **THEN** `lanes[]` 中至少有一条泳道对应该层，且其命令有出处

#### Scenario: 框架可迭代
- **WHEN** 开发中期某层从 `不适用` 改为 `已实现`
- **THEN** 经 `continue` / `replan` 更新 `testing-strategy.md` 与 `lanes[]`，MUST NOT 要求推倒重来

### Requirement: 泳道三态与渐进 DoD

每条泳道 SHALL 独立处于三态之一：`planned`（决定要有）→ `scaffolded`（harness + smoke 已写、验证方法已定，但未验）→ `verified`（验证方法已被执行，且结果被认可）。

**状态迁移 SHALL 只由脚本子命令执行，表外迁移一律拒绝；模型/人 MUST NOT 手改数据文件跳级。** 具体分工见「状态迁移的执行者分工」。

skill 的完成态 **MUST NOT 要求全部泳道 `verified`**——允许停在 `planned` / `scaffolded`，不阻塞（渐进 DoD）。

**但诚实是硬要求**：`scaffolded` 态 **MUST 带非空 `blocked_by`**；空 `blocked_by` → lint fail-closed。收尾时 skill **SHALL 逐条列出**仍处于 `planned` / `scaffolded` 的泳道，**MUST NOT 只埋进文件里**。

收尾报告 SHALL 用一句话给出**整体判定与下一步**（如「环境已可用于 N 条能力，M 条待补；下次直接触发本 skill 即走 continue」），**MUST NOT 让操作者自己猜进度含义或下一步怎么调用**〔DX〕。

**`blocked_by` 的最小结构校验**〔DX〕：lint SHALL 断言 `blocked_by` **不只是非空**——MUST 包含可辨认的**修复指引**（可执行命令片段 / 明确的待办动作）。仅有 `TODO` / `待定` / 空白字符类内容 ⇒ 报警。

> **诚实边界**：此校验是**启发式**（结构性信号，非语义判断）——它挡得住敷衍，挡不住「写得像模像样但其实没用」。后者归人门。

#### Scenario: 依赖缺失不算失败
- **WHEN** 本机无 mosquitto 导致集成泳道 smoke 跑不起来
- **THEN** 该泳道留在 `scaffolded` 且 `blocked_by` 写明「本机无 mosquitto — `brew install mosquitto` 后 `/sdflow-devenv` continue」，skill 继续处理其余泳道

#### Scenario: 敷衍的 blocked_by 被抓
- **WHEN** 某 `scaffolded` 泳道的 `blocked_by` 内容为 `TODO`
- **THEN** `devenv_lint` 报警——`blocked_by` 必须含可辨认的修复指引

#### Scenario: 收尾显著呈现未完成泳道与下一步
- **WHEN** skill 收尾且存在未 `verified` 的泳道
- **THEN** 收尾报告逐条列出这些泳道及其 `blocked_by`，并给出整体判定与下一步调用方式

### Requirement: 状态迁移的执行者分工——证据只能由执行者本人写〔设计门 round-2〕

**`verified` MUST NOT 由模型传入。** 两条通道，各自的证据只能由其执行者写：

**通道 A · `executor: script` ⇒ `devenv_scaffold.py verify-lane`**

`verify-lane` **MUST 由脚本自己 fork 执行** `verification.method` 声明的命令，捕获 exit code / 时长 / 输出摘要，**据此自行决定**写 `verified` 还是 `scaffolded + blocked_by`。

> **理由**：若无脚本亲自执行，实际数据流只能是「模型跑 → 模型读 exit code → 模型调 `set-lane --status verified`」⇒ 脚本对「到底跑没跑、绿没绿」**零独立证据** ⇒「脚本验证」退化为「**模型自称，脚本盖章**」。

**通道 B · `executor: human` ⇒ `devenv_scaffold.py confirm-lane`**

`confirm-lane` **SHALL 只能从人门流程调用**，写入人确认的证据。**模型 MUST NOT 代替操作者调用它。**

**`set-lane --status verified` MUST 一律拒绝（exit 5）**——`set-lane` 只管 `planned` / `scaffolded` 两态。

**执行证据（`evidence`）的形状**：

| `executor` | 必填字段 |
|---|---|
| `script` | `at`（时间戳）· `at_commit`（HEAD SHA）· `exit`（退出码）· `output_digest`（输出摘要的 sha256）· `method_digest`（验证方法 + smoke + source 的联合摘要） |
| `human` | `at` · `at_commit` · `confirmed_what`（人确认了什么——一句话）· `method_digest` |

> **无执行证据落盘 ⇒ 冷审的「诚实镜」在数据上无从查证**——冷审子代理只能读文件、无法复跑命令。执行证据是该镜的接地面。

**`verified` 是会过期的事实**：`method_digest` 失配（人改了 recipe / 换了 smoke / 改了验证方法）⇒ lint **MUST** 报「该泳道的验证证据已失效，需重验」，**MUST NOT** 继续声称 `verified`。

**`method_digest` 的输入 SHALL 覆盖验证真正依赖的全部内容**：验证命令（含 Makefile recipe body 展开）· smoke 文件 · smoke 可达的 harness/fixture 文件 · 依赖声明中引用的外部文件（如 compose.yml）· 依赖的 lockfile（若存在）。**MUST NOT** 只摘命令字符串——改 fixture 让断言失效是 vacuous smoke 的主要引入路径，只摘命令则纹丝不动〔ENG · codex〕。

#### Scenario: 模型不能自称 verified
- **WHEN** 调用 `set-lane --id X --status verified`
- **THEN** 脚本以 exit 5 拒绝，提示「`verified` 只能由 `verify-lane`（script）或 `confirm-lane`（human）产出」

#### Scenario: verify-lane 亲自执行并落证据
- **WHEN** 对 `executor: script` 的泳道调用 `verify-lane --id X`
- **THEN** 脚本自己执行验证命令，并把 `exit` / `output_digest` / `method_digest` / `at_commit` 写入该 lane

#### Scenario: 人工验证经人门落证据
- **WHEN** 某 `executor: human` 泳道的人工验证已由操作者执行完毕
- **THEN** 经人门调用 `confirm-lane` 写入 `confirmed_what` 与 `at_commit`，该泳道进入 `verified`

#### Scenario: 改了 fixture 使证据失效
- **WHEN** 某 `verified` 泳道的 smoke 所依赖的 fixture 文件被修改，`method_digest` 失配
- **THEN** lint 报该泳道验证证据失效并要求重验

### Requirement: 执行边界与「不伤害」红线

**最高红线：skill MUST NOT 破坏操作者的机器状态。**

> **本条的适用范围已收窄**〔设计门 round-2〕：前一版把「抽掉依赖」写死为 `verified` 的必要步骤，于是「停服务」成了常规动作，需要一整套红线兜底。现在验证方法由模型提、人拍板——**多数方案根本不动机器状态**。本条只在**模型提出的方案确实需要改变机器状态时**适用。

**R1 · 只能停自己启动的东西，且 `owned_by` MUST 为派生而非声明**：依赖的 `owned_by` **SHALL 由 skill 的运行时事实推导**——只有**本次运行内 skill 自己调用过启动命令**的依赖才记 `skill`；**此前已在运行的一律 `operator`**。**`owned_by: operator` → MUST NOT stop**。

> **理由**：若 `owned_by` 是模型自填的裸声明，R1 红线的全部效力压在一个无独立信号的字段上——模型把用户 `brew services` 起的 broker 误标为 `skill`，红线直接失效。**派生使它有了运行时锚。**

**R2 · 改变机器状态的方案 MUST 单列显著呈现**：跑前**单列**「将停止服务 X」/「将改变 Y」（**不混在命令清单里**）· `try/finally` 恢复 · **恢复失败 MUST 响亮报告并写进 `devenv-log.md`**。

**R3 · 超时 MUST 杀进程树 + cleanup ledger MUST 落盘**：runner SHALL 以独立 process group / session 启动子进程；超时先 TERM、限时后 KILL **整棵进程树**。**cleanup ledger MUST 落盘**（`openspec/architecture/.devenv-cleanup.ledger`，**资源创建成功后立即写入**，而非函数返回时才写）——否则脚本被 `SIGKILL` 时 ledger 随进程蒸发，而 R3 要防的**正是**这种场景。skill **每次启动 SHALL 先扫描遗留 ledger 条目**并尝试回收或响亮报告。**cleanup 失败 MUST 是独立失败状态**，不能只写普通 `blocked_by`。

**平台边界（如实登记）**：进程树杀灭 v1 **只承诺 POSIX**（`start_new_session` + `os.killpg`）。**非 POSIX 平台 ⇒ `verify-lane` 显式 refuse**，响亮告知「本平台的进程树杀灭未经验证，不做无证据的执行」，该泳道走 `executor: human` 通道。**MUST NOT** 写一段从未在该平台执行过的代码并声称它能杀进程树。（Windows 的 `taskkill /T /F` 方案零依赖可行，但**未经实测**⇒ 挂 todo，实测后再升为 `script`。）

**R4 · 跑前列命令 MUST 连 recipe body 一起展开**：只给操作者看 `make integration` 这**一行调用**，对「那个 target 里到底跑什么」提供**零信息量**——人只能橡皮图章。SHALL 同时展开该 target 的 recipe。

**R5 · 失败 MUST NOT 重试、MUST NOT 进入 debug 循环**——skill 的职责是「建 + 验」而非「调通」；修复归下次 `continue`。

**R6 · 真硬件泳道 MUST NOT 由脚本执行**：由 lane 的 `kind: hardware` 识别，`verify-lane` refuse。**但该泳道不因此无法 `verified`**——它走 `executor: human`（按 `embedded-test-sop` 人工执行 + 人门确认）。

> **`kind` 的诚实边界**：`kind` 是模型填的、**无独立信号**，脚本"按 `kind` 判定"本质上仍是模型自觉套了层壳。故 `kind: hardware` 的判定 **MUST 同时进人门确认清单**（见「冷审与人门」的 ③-pre 议程），**MUST NOT** 佯装这是纯机械识别。

**R7 · MUST NOT 替操作者安装系统依赖**——只提供 doctor 脚本与安装命令。

**R8 · 子进程 MUST 走最小环境 allowlist，MUST NOT 继承 agent 的完整环境**〔codex〕：

> **理由**：前一版只要求「输出**事后**过 secret 正则打码」。但命令继承了 agent session 的完整环境变量后，**被执行的 recipe 或其下游脚本仍可把凭证写进文件、发往网络**——事后打码管不着这些。**recipe 展开不能替代执行环境隔离。**

runner SHALL 以**显式 allowlist** 构造子进程环境（`PATH` / `HOME` / lane 显式声明的变量）。lane 需要的额外变量 SHALL 显式声明；**敏感变量需人门单独授权，且 MUST NOT 落盘**。
落盘的命令输出 SHALL **额外**截断 + 过 secret 正则打码——但此为**尽力而为的缓解（best-effort），非泄露保证**；正则集合 SHALL 登记其已知盲区，**MUST NOT** 用绝对语气佯装保证。

#### Scenario: 拒绝停止操作者的服务
- **WHEN** 某依赖在 skill 启动前就已在运行（`owned_by` 派生为 `operator`），而某验证方案需要停止它
- **THEN** skill MUST NOT 停止它；该方案不可用，模型 SHALL 提出不改变机器状态的替代方案，或改走 `executor: human`

#### Scenario: 中断也要恢复
- **WHEN** 验证期间 smoke 超时 / 脚本抛异常 / 收到 SIGINT
- **THEN** 被改变的机器状态 MUST 在 `finally` 中恢复；恢复失败 MUST 响亮报告并写进 devenv-log

#### Scenario: 脚本被强杀后下次启动自愈
- **WHEN** 上一次运行被 `SIGKILL`，cleanup ledger 中留有未回收的容器条目
- **THEN** skill 下次启动时扫描到该条目，尝试回收或响亮报告，MUST NOT 无视

#### Scenario: 非 POSIX 平台不做无证据的执行
- **WHEN** 在非 POSIX 平台触发 `verify-lane`
- **THEN** 脚本显式 refuse 并告知平台限制，该泳道改走 `executor: human`

#### Scenario: 子进程不继承完整环境
- **WHEN** runner 执行 smoke 命令
- **THEN** 子进程环境由 allowlist 构造，agent session 的其余环境变量（含凭证）MUST NOT 被继承

#### Scenario: 跑前展开 recipe
- **WHEN** skill 即将执行 `make integration`
- **THEN** 呈现给操作者的内容包含该 target 的 recipe body，而不只是 `make integration` 这一行

### Requirement: 落地物追加边界——skill 是追加者非拥有者

落地物（Makefile target / CI 配置 / 测试 harness / smoke / doctor）**MUST NOT 设托管区块**——它们是**人机共有的活文件**，人随时会改其实现。skill SHALL 只执行两个动作：**已有的 → 登记**（读出并写入 `source`，跑验证）· **缺失的 → 追加**（新写，并带一行来源注释供审计）。

**重名冲突 → fail-closed**：欲追加的 target 名已存在 ⇒ 脚本报冲突、留人裁决，**MUST NOT 静默覆盖**。

> **诚实边界**〔ENG-16〕：脚本**只能判定「名字碰撞」**——「语义符不符」**无确定性信号，归模型 + 人**。脚本 **MUST NOT** 佯装它在判断语义。

**门禁逻辑 SHALL 落在 Makefile（或等价项目脚本入口），CI 配置只做调用壳**（`- run: make integration`）——保证无 CI 的项目仍有完整本地门禁、CI 平台可换而门禁不变、本地与 CI 跑同一条命令。项目无 CI → CI 槽显式 `N/A` **并连带记后果**。

**v1 入口支持边界（如实登记）**〔ENG-11〕：`inject` **只支持行文本型入口**（Markdown / Makefile / YAML）。**结构化入口（`package.json` 等）v1 MUST NOT 直接注入**——此类项目 SHALL 走 **Makefile 薄壳**（Makefile target 调 `npm run x`），由人自行维护 `package.json`。CI 配置 **只生成独立新文件**，MUST NOT 就地改写既有 CI 文件。

**归位模式的 smoke SHALL 从已有测试中选取一条作为锚**（`smoke:` 字段指向它），**MUST NOT 新写冗余 smoke**。

#### Scenario: 已有 target 只登记不接管
- **WHEN** 消费仓 Makefile 已有 `integration:` target 且语义即本泳道
- **THEN** skill 将其登记进 `source`（按 selector + digest，非行号），不改写该 target 内容

#### Scenario: 重名即 fail-closed（不判语义）
- **WHEN** 欲追加的 target 名已存在
- **THEN** 脚本报名字冲突并留人裁决，MUST NOT 静默覆盖，且 MUST NOT 声称自己判断了语义

#### Scenario: package.json 项目走 Makefile 薄壳
- **WHEN** 消费仓为 Node 项目，门禁命令需落地
- **THEN** skill 追加 Makefile target 调用 `npm run`，MUST NOT 直接注入 `package.json`

#### Scenario: 归位模式复用已有测试当 smoke
- **WHEN** 归位模式下该泳道已有可用测试
- **THEN** `smoke:` 指向该已有测试文件，不新写 smoke

### Requirement: 归位模式——素材盘点、判归属、删源

归位模式 SHALL 在事实采集前插入「素材盘点 → 判归属 → 搬运表」，其后与新建模式共用后半段。

**搬运表 MUST 先给操作者确认再落笔**——归属判定是全流程**唯一无确定性信号**的一步，人门 SHALL 放在此处，**MUST NOT 放在末尾审文档**。

删源 SHALL 区分**三种处置**，并以 `grep` 被引用面作判据：引用数为 0 → 可直接删；引用可枚举 → 改掉这些引用后删；引用面广/散 → **降为一行指针**。

搬运表 **SHALL 单列一节「以下 N 个文件将被整体删除」显著呈现**，**MUST NOT 只在表格行内标记而埋进长消息**。

删源后 SHALL 扫描残留引用，**覆盖代码注释**（非仅 Markdown 链接）。

#### Scenario: 搬运表先确认再落笔
- **WHEN** 归位模式完成素材盘点与归属判定
- **THEN** skill 呈现搬运表并等待操作者确认，确认前 MUST NOT 写入或删除任何文件

#### Scenario: 引用面广者降为指针
- **WHEN** 某待删源文件被十余处引用
- **THEN** skill 提议降为一行指针而非整体删除，由操作者拍板

#### Scenario: 删源后扫残留引用含代码注释
- **WHEN** 源文件已删除
- **THEN** skill 扫描全仓残留引用，覆盖代码注释中的路径引用

### Requirement: 删源护栏——逐文件校验与可恢复备份〔设计门 Q1 的连带义务〕

> **设计门 Q1 拍定：归位模式留在本 change。** 代价是删源护栏 MUST 从「工作区干净」升级——**clean worktree 并不足以保护删除**：它不保证仓库有有效 HEAD、不保证待删文件已 tracked、不保护 ignored 文件 / submodule / symlink。

删源前 SHALL 做**一次性**入口检查：`git status` 非空 → 拒绝，提示先 commit 或 stash。**此检查只在归位删源入口执行一次**——backup manifest 的写入不重触发它〔对抗镜〕。

删除任一源文件前，skill **MUST 逐文件校验**：

1. 仓库有**有效 HEAD**（非 unborn branch）
2. 该文件**已 tracked**（untracked 文件删了 git 恢复不了）
3. **非 submodule、非 symlink**
4. 其**内容 digest 与搬运表人门确认时一致**（防确认后被改动）

任一项不满足 ⇒ **fail-closed 拒绝删除该文件**，如实报告原因。

**backup manifest SHALL 入 git**（落 `openspec/architecture/.devenv-backup/`，**MUST NOT** gitignore）——「可恢复」必须跨机器成立；若走 gitignore，换台机器 / CI / 新 checkout 即失效，「收尾告知还原方式」落空〔对抗镜 · codex〕。manifest SHALL 含被删文件的路径 + 内容 digest + 可还原的 patch，并在收尾对话中告知还原方式。

> **与残留引用扫描的冲突消解**〔codex〕：backup manifest 天然含旧路径与旧内容 ⇒ **删源残留引用扫描 MUST 排除 `.devenv-backup/`**，否则它必然自我命中。

#### Scenario: untracked 文件拒绝删除
- **WHEN** 搬运表中某待删源文件未被 git tracked
- **THEN** skill fail-closed 拒绝删除该文件，提示先 `git add` 或手动处理

#### Scenario: 确认后被改动则拒删
- **WHEN** 搬运表人门确认后、执行删除前，某待删文件内容发生变化（digest 不符）
- **THEN** skill 拒绝删除该文件并要求重新确认

#### Scenario: 删除可跨机器还原
- **WHEN** 归位模式执行了删源
- **THEN** `.devenv-backup/` 下存在**已入 git** 的 backup manifest，且收尾对话告知还原方式

#### Scenario: 残留引用扫描不自我命中
- **WHEN** 删源后扫描残留引用
- **THEN** 扫描排除 `.devenv-backup/`，MUST NOT 把备份内容报为残留引用

### Requirement: 冷审与人门

冷审 **MUST 由 fresh 子代理执行**（Agent 工具），**禁止生成 session 自查**（自证偏差）。冷审 SHALL 按 `references/review-lenses.md` 取镜，至少覆盖：

- **覆盖镜**：SAD 哪条 contract 未被任何泳道穿过 / `covers` 声明是否真命中
- **验证方法镜**〔round-2 新增〕：模型提的验证方法**是否名副其实**（强度是否被夸大 · 盲区是否被如实说出 · `executor` 判定是否合理）
- **分类镜**〔round-2 新增〕：`kind` / `owned_by` 的分类**是否属实**（这些字段无独立信号，是机械层的输入，**必须有一镜专查**）
- **vacuous 镜**：smoke 是否语义恒真
- **边界镜**：架构决策是否漏进 environments / 阶段计划是否漏进 testing-strategy
- **诚实镜**：`planned` 是否被伪装成 `verified` / `blocked_by` 是否敷衍
- **归位模式加删源镜**：源文件是否真删、残留引用是否扫净

冷审失败 SHALL 重派一次；再失败 SHALL **显式报告缺口**，**MUST NOT 无冷审静默过人门**。宿主无 fresh 子代理原语时 SHALL **显式降级并响亮留痕**，**MUST NOT 佯装冷审**。

**人门 MUST 拆成两道，且 diff 门 MUST 在执行之前**：

| 门 | 位置 | 议程 |
|---|---|---|
| **③-pre（执行前）** | 写完落地物、**执行任何验证之前** | ① **落地物 diff 过目**（含 recipe body 与 smoke 源码）② **验证方法逐条确认**（含模型自陈的强度与盲区）③ **依赖分类清单过目**（`kind` / `owned_by` / `executor`——**这些是机械层的输入，无独立信号，必须人看**）④ 将执行的命令清单（**recipe 展开**）⑤ 「将改变机器状态」的显著呈现（若有）。**否决 → MUST 回退本次追加的改动** |
| **④（执行后）** | 冷审之后 | ① 泳道设计复核 ② 未 `verified` 泳道逐条确认 ③ N/A 槽逐条确认 ④ `executor: human` 泳道的人工验证结果确认（→ `confirm-lane`）⑤ **归位模式：删源清单确认**——**MUST 单独拎出、要求比其余议程更明确的确认动作**（不可逆操作，MUST NOT 与常规议程同级快速划过） |

**③-pre 的呈现 SHALL 分级，MUST NOT 无差别全量倾倒**〔DX〕：**新写的**落地物（模型生成的 recipe body / smoke 源码）MUST 全文展示；**仅登记的既有 target** 只需展示登记映射（`source` 指向何处），**MUST NOT** 要求人重读一遍他自己写的、且 skill 不会改动的代码。

> **理由**：人门的敌人有两个——信息太少（橡皮图章）与**信息太多（疲劳性橡皮图章）**。前一版只解决了前者。

**人门呈现 SHALL 用人话，MUST NOT 直接抛内部字段名**〔DX〕：`executor` / `owned_by` / `kind` 这类字段 SHALL 先翻译成一句后果描述（如「这条泳道的验证只能靠人工跑一遍，脚本无法自动确认——接受吗？」）再呈现。

#### Scenario: 生成的代码在执行前被人看过
- **WHEN** skill 写完 Makefile target 与 smoke 源码
- **THEN** 在执行任何验证之前，先呈现完整 diff（含 recipe body 与 smoke 全文）供操作者过目

#### Scenario: 验证方法与依赖分类必过人门
- **WHEN** 进入 ③-pre 人门
- **THEN** 议程含「验证方法逐条确认（含强度与盲区）」与「依赖分类清单过目（`kind`/`owned_by`/`executor`）」

#### Scenario: 仅登记的既有 target 不要求人重读
- **WHEN** 某泳道是登记已有的 Makefile target（skill 不改其内容）
- **THEN** ③-pre 只展示登记映射，MUST NOT 展开该 target 全文要求人重读

#### Scenario: 冷审必须 fresh 子代理
- **WHEN** 进入冷审步
- **THEN** skill 派 fresh-context 子代理执行，主 session MUST NOT 自查

### Requirement: ③-pre 否决的回退——touched-files 事务清单〔设计门 round-2 · 对抗镜 · codex〕

skill **MUST 在写入任何落地物之前**生成 **touched-files 事务清单**，记录每个将被触碰的文件：路径 · **原先是否存在** · 原内容 digest · 原 mode。

③-pre 被否决 ⇒ 按清单**逐项回退**：**原先存在的** → 恢复原内容；**原先不存在的**（新写的 smoke / harness） → **删除该文件**。

> **理由**：前一版称「`git checkout -- <files>` 可行」——**但 `git checkout --` 对 untracked 文件不起作用**，而「缺失的 → 新写」是本 skill 的**主路径**（新写 smoke 是常规动作，不是边缘情形）。真能撤销新文件的是 `git clean`，而 **`git clean -f` 会连带删除操作者自己未 `git add` 的其他文件**——**「最后一道护栏」内部自带一个破坏性操作**。

回退 **MUST 只按清单精确定点**，**MUST NOT** 使用无路径限定的 `git clean`。回退前 SHALL 校验目标文件 digest 与写入后一致（防人在人门期间手改）；不一致 ⇒ 报告并留人裁决，MUST NOT 盲删。

#### Scenario: 否决后新写文件被精确删除
- **WHEN** 操作者在 ③-pre 否决落地物 diff，其中包含 skill 新写的 smoke 文件（untracked）
- **THEN** skill 按 touched-files 清单删除该新文件、恢复被修改的既有文件，**MUST NOT** 执行无路径限定的 `git clean`

#### Scenario: 回退前校验未被手改
- **WHEN** 回退时发现某文件 digest 与 skill 写入后不一致
- **THEN** skill 报告并留人裁决，MUST NOT 盲目删除或覆盖

### Requirement: lint 的触发点——挂 `sdflow-maintain`〔设计门 Q6〕

`devenv_lint` **MUST 有自动触发点**：`sdflow-maintain` 在扫描 `openspec/` 一致性时 **SHALL 调用它**。

> **理由（dogfood 自指坑）**：本 change 把「无门禁——检查无任何自动触发点、全靠人记得跑」列为**立项理由之一**，而前一版的 `devenv_lint` **自己也没有任何触发点**。
>
> 更致命：**「渐进 DoD」允许泳道停在 `scaffolded`，而防止它烂成僵尸文档的唯一措施就是「lint 复述未完成清单」——若无人调用该 lint，该措施为空。**「不强制完成」+「不检查未完成」= **名存实亡**。
>
> **诚实边界**：`sdflow-maintain` 是**人主动跑**的 ⇒ 本条提供的是「**更响的提醒**」而非**硬门禁**。此局限 MUST 显式登记，**MUST NOT 佯装硬拦截**。

> **实现说明**：`sdflow-maintain` 现为四类**硬编码**扫描，**无插件挂点** ⇒ 本条是**新增代码**，非「复用现成挂点」。

#### Scenario: maintain 扫描调用 devenv lint
- **WHEN** 在已有 `environments.md` 的消费仓运行 `sdflow-maintain`
- **THEN** 其扫描结果包含 devenv 健康度：未 verified 泳道清单、失效的验证证据、空/敷衍的 `blocked_by`

### Requirement: 机械 lint——只查诚实，不查质量

`devenv_lint.py` SHALL 执行以下机械检查（**全部是"诚实"检查，无一条试图判断"质量"**）：

1. **验证方法非空**：任一泳道 `verification.method` 为空 → fail-closed
2. **状态与证据匹配**：`verified` ⇒ `evidence` 齐全且 `method_digest` 未失配；`verified` ⇒ **`blocked_by` 必须为空**〔绿泳道上挂着「本机无 mosquitto」= 文档在说谎〕；`scaffolded` ⇒ `blocked_by` 非空且含可辨认修复指引
3. **测试三层框架完整性**〔round-2〕：`testing-strategy.md` 的 **unit / integration / e2e 三层 × 五槽**逐一存在且非空 → 缺任一 **fail-closed**
4. **三层状态的强制附带项**〔round-2〕：`不适用` ⇒ **必须有后果**（只写 `N/A` / 只写理由不写后果 → 报错）；`人工` ⇒ **必须有"用户怎么做"**（只写「人工测试」→ 报错）；`已实现` ⇒ **`lanes[]` 中必须有对应泳道**（声称已实现却无泳道 = 文档在说谎 → 报错）
5. **命令出处一致性**：按 **selector 重定位 + digest 比对**，**MUST NOT** 用行号存在性
6. **指针不悬空**：Markdown 链接 + 章节锚可达
7. **删源残留引用**（含代码注释，**排除 `.devenv-backup/`**）
8. **入口复述检测**：README/CLAUDE 出现真相源才该有的完整命令表 → 告警

> **第 3/4 条是真机械，不是假机械**：槽在不在、`不适用` 后面有没有跟后果段、`已实现` 有没有对应的 lane id——**全是结构性信号，脚本能确定性判定**。
> 但脚本 **MUST NOT** 判断「这个后果写得对不对」「这个人工步骤可不可行」——**那归人门与冷审**。

lint 通过码 SHALL 带诚实后缀（如 `structure-ok-SEMANTICS-UNCHECKED`）——**lint 通过 = 结构性通过 ≠ 内容已审**；内容质量由冷审 + 人门守。

lint SHALL 按泳道状态分档核验：`verified` → 强制 2、3；`scaffolded` → 强制 `smoke` 文件存在 + `blocked_by`；`planned` → 不核验命令出处。

#### Scenario: verified 泳道证据失效被抓
- **WHEN** 某 `verified` 泳道的 `method_digest` 与当前 recipe / smoke / fixture 不再匹配
- **THEN** lint fail-closed 并报出该泳道

#### Scenario: verified 泳道挂着 blocked_by 被抓
- **WHEN** 某泳道状态为 `verified` 但 `blocked_by` 非空
- **THEN** lint fail-closed——绿泳道不该有阻塞项

#### Scenario: lint 通过码诚实
- **WHEN** lint 全部机械检查通过
- **THEN** 输出的通过码明示「结构通过，语义未核」

### Requirement: 泳道数据落 JSON 侧文件与 digest 出处锚〔设计门 Q4〕

**泳道数据 MUST NOT 放 `environments.md` 的 frontmatter**，SHALL 落 `openspec/architecture/.devenv-lanes.json`（**标准库 `json`，零依赖，round-trip 无损**）。

> **理由**：嵌套 `lanes[]`（含列表 × 含中文自由文本 × 含带冒号的值）**没有可用的解析/序列化方案**——目标环境**无 PyYAML**（本仓零第三方依赖，且 `test_anchor_contract.py` 有专门测试断言禁 `import yaml`），而唯一先例 `sad_schema.parse_frontmatter` 是**手搓的扁平标量解析器**（固定键白名单，无列表、无引号处理），写侧是**行级前缀匹配改写**（非正则）——这套手法在嵌套结构上完全用不了。

`environments.md` 的 frontmatter 只留三个**扁平标量**：`sad`（`present|missing`）· `mode`（`greenfield|brownfield`）· **`schema_version`**（`<int>`）。

**`schema_version` MUST 有消费行为，MUST NOT 只是留个位**：读到**高于**本实现已知版本 ⇒ **fail-closed** 报「skill 版本过旧，请升级」，**MUST NOT** 尽力解析；缺失 ⇒ fail-closed。

**数据模型**：

```json
{
  "schema_version": 1,
  "lanes": [{
    "id": "mqtt-integration",
    "kind": "external-dep | ui | lang-bridge | hardware | pure",
    "status": "planned | scaffolded | verified",
    "verification": {
      "method": "<模型提出、人拍板：怎么验>",
      "executor": "script | human",
      "strength": "<模型自陈：这个方法证明了什么、盲区是什么>",
      "evidence": {"at": "...", "at_commit": "...", "exit": 0,
                   "output_digest": "...", "method_digest": "...",
                   "confirmed_what": "<executor=human 时>"}
    },
    "source": {"file": "Makefile", "kind": "make-target",
               "selector": "integration", "digest": "<recipe 规范化后 sha256 前缀>"},
    "smoke": "<path>",
    "deps": [{"name": "mosquitto", "kind": "compose|host-service|port|toolchain|testcontainer",
              "owned_by": "skill | operator"}],
    "covers": ["<SAD contract 锚>"],
    "blocked_by": "<scaffolded 时必填：卡在哪 + 怎么修 + 怎么 continue>"
  }]
}
```

> **`kind` / `owned_by` 的诚实边界**：`kind` **无独立信号**（模型自填）⇒ **MUST 进 ③-pre 人门确认清单 + 冷审分类镜**，脚本按它分派时 **MUST NOT** 佯装这是机械识别。`owned_by` **MUST 为派生**（见 R1），有运行时锚。

**出处锚 MUST 按内容（digest），MUST NOT 按行号**：

> **理由**：`source: "Makefile:11-14"` + lint「查那行存不存在」——**「第 11-14 行存不存在」对任何长度 ≥14 行的文件恒为真**。用户在 Makefile 顶部插三行 ⇒ 锚点全部错位、lint 全绿。**这是一个恒真断言，即设计好的假绿。**

lint SHALL 用 parser 按 `selector` **重新定位** target，比对 recipe digest；**行号仅在 render 时动态生成供阅读，不作真相**。

**digest 的规范化规则 MUST 明确定义**：剥去行首/行尾空白与纯空行；**MUST 保留 tab 缩进本身**（Make recipe 的 tab 有语法意义，抹掉即改变语义）；**MUST NOT** 剥去注释（注释可能载有语义）。

正文的命令表 SHALL 由 `devenv_scaffold.py render` **从 `.devenv-lanes.json` 渲染**，带 `DO NOT EDIT` banner，**MUST NOT 由人手写**。

#### Scenario: 行号变动不导致假绿
- **WHEN** 操作者在 Makefile 顶部插入三行变量定义
- **THEN** lint 按 selector 重新定位 target 并比对 digest，digest 未变则通过、变了则报「实现已改动」；**MUST NOT** 因「那几行仍存在」而静默通过

#### Scenario: 未知 schema_version 拒绝解析
- **WHEN** `.devenv-lanes.json` 的 `schema_version` 高于本实现已知版本
- **THEN** 脚本 fail-closed 报「skill 版本过旧，请升级」，MUST NOT 尽力解析

#### Scenario: 零第三方依赖
- **WHEN** 在无 PyYAML 的环境运行 skill
- **THEN** 泳道数据读写正常（走标准库 json）

### Requirement: 文档渲染与两文档边界

skill SHALL 产出两份真相源，落 `openspec/architecture/`（与 `sad.md` 同居），**MUST NOT 落项目根或 `docs/`**：`environments.md`（操作轴：dev / test / deploy）· `testing-strategy.md`（方法轴：分层 / contract 集成点 / mock 边界 / 护栏 / 盲区）。

两文档边界 SHALL 守切线：**方法/决策 → testing-strategy；环境/操作 → environments**。架构决策 MUST 引用 SAD 不复述；阶段计划 MUST 归 roadmap 不写入 testing-strategy。

`environments.md` 的每条命令 SHALL 带**出处**；**N/A 槽 SHALL 连带记录其留下的后果**。

#### Scenario: 命令表机械渲染
- **WHEN** 某泳道状态由 `scaffolded` 变为 `verified`
- **THEN** 正文命令表经 render 重新生成并反映新状态，人无需手改正文

#### Scenario: 落位与 SAD 同居
- **WHEN** skill 产出两份真相源
- **THEN** 文件落在 `openspec/architecture/` 下，而非项目根或 `docs/`

### Requirement: 入口托管注入使用独立 marker

skill SHALL 将「最小命令 + 指针」注入消费仓入口文件（CLAUDE.md / AGENTS.md / README.md）与 `openspec/INDEX.md`，使用**自己的 marker token `opsx-devenv`**（`<!-- opsx-devenv:start -->` … `<!-- opsx-devenv:end -->`），采用 token 定位 + 幂等整块替换语义。

**MUST NOT 写入 `opsx-init` 的托管区块**——注入是整块替换，共用同一 marker 会使两个 skill 互相覆盖。

**`inject` MUST 为 fence-aware**：**MUST NOT** 照抄 `init.py` 的 `inject()`（其源码注释明示判据尚非 fence-aware，会命中代码块内演示的 marker，fence-aware 版本已 defer）。MUST 覆盖 CommonMark 全部 fence 变体（` ``` ` / `~~~` / 四 backtick / 缩进 fence）；孤儿 marker / 逆序 / 交错 → **fail-closed 报位置**。

入口文件 **MUST NOT 复述**真相源细节（完整命令表 / 配置项表），只放最小起步命令 + 指针。

#### Scenario: 独立 marker 不干扰 init 区块
- **WHEN** 消费仓已有 `opsx-init` 托管区块且 skill 执行注入
- **THEN** skill 只创建/替换 `opsx-devenv` 区块，`opsx-init` 区块内容不受影响

#### Scenario: 代码块内的 marker 演示不被劫持
- **WHEN** 消费仓的 README 在 ``` 代码块内演示了 `<!-- opsx-devenv:start -->`
- **THEN** `inject` 不把它当作真 marker，MUST NOT 注入进代码块

### Requirement: 并发安全写入

所有落盘 **MUST 原子写**（`mkstemp` 唯一 tmp 名 + `os.replace`）；读-改-写序列 **MUST 持锁**。

**`atomic_write` MUST 接受 mode 参数**——`sad_scaffold` 现硬编码 `chmod 0o644`，复用它写 doctor / broker 脚本会导致**落盘即不可执行**；脚本类落地物传 `0o755`，覆盖既有文件时**保留原 mode**。

**锁 MUST 覆盖整个 `openspec/` 写域，三个 skill 共用同一锁名**（`openspec/.sdflow-write.lock`）。

> **理由（互斥性不可组合）**：给 devenv 单发一把 `.devenv-scaffold.lock`，与 `sad_scaffold` 的 `.sad-scaffold.lock` **是两把不同的锁**——但两者写入面**重叠**（都注入 CLAUDE/AGENTS/README/INDEX）。且 `init.py` 的 `inject()` 是**裸 `open(w)` 全量覆写，无锁、无原子写** ⇒ devenv 的注入被静默吃掉。「复用已验证机制」≠「**互斥性可组合**」。

本 change SHALL **同时改造三个 skill 的锁协议**（承基准 3：面治优先于点补）：

1. `devenv_scaffold.py` — 用新锁
2. `sdflow-init/scripts/init.py` — `inject()` **补锁 + 原子写**（现为裸 `open(w)`）
3. **`sdflow-architecture/scripts/sad_scaffold.py` — 从 `.sad-scaffold.lock` 迁到共用锁，并补 owner 核对**（现释放时不核 owner）〔codex〕

> **前一版只改了 `init.py`，漏了 `sad_scaffold`——「三 skill 共锁」在 tasks 里只有两条腿。**

**锁 MUST 短持有，MUST NOT 跨验证执行持有**：`sad_scaffold` 的锁参数为**亚秒级**操作而调（`LOCK_STALE_SEC = 120`），而验证可跑数分钟 ⇒ 锁若跨验证持有，**并发 session 会把活锁判成残留锁** → 提示「删锁重试」→ **两 session 同时写**。**陈旧锁检测由保护变成攻击面。**

**状态写入 MUST 用 CAS，且 CAS MUST 覆盖验证的全部输入快照**〔ENG · codex〕：

> **理由**：仅比对 `status` 不够——`verify-lane` 在无锁状态下读了 `method`/`source`/`smoke` 去跑数分钟，期间另一 session 可改同一 lane 的这些字段而**保持 `status` 不变**（它自己的 CAS 照样通过）⇒ 旧验证回写成功 ⇒ **lane 记的是新命令，证据是旧执行的**。**修活锁的那个修法，亲手打开了这个洞。**

`verify-lane` / `confirm-lane` SHALL 在读取时对 lane 的**全部验证输入**（`status` + `method` + `source` + `smoke` + `deps`）取快照 digest；回写时**在锁内**重读并比对该 digest，不一致 ⇒ **exit 5 拒绝**，要求重跑。回写 MUST **只 patch 那一条 lane**，MUST NOT 用内存快照覆写整份 lanes。

**退出码 MUST 一码一义**〔ENG · DX〕：不同失败原因 MUST 有不同退出码（调用者需据此区分「该停下报 bug」与「该重读重试」）。SHALL 提供一张覆盖全部子命令的退出码表，**MUST NOT** 让调用者退回解析 stderr 文本。

锁文件 MUST 记 owner（UUID + PID + 时间戳）；释放前**核对 owner**，**MUST NOT** 删除他人的锁。

`devenv-log.md` SHALL 为 **append-only**；`--line` 含换行符 SHALL 被拒绝（防伪造审计行）。

#### Scenario: 跨 skill 并发不丢注入
- **WHEN** devenv 正在注入 CLAUDE.md，另一 session 同时跑 `/sdflow-init update` 或 `/sdflow-architecture`
- **THEN** 三者经同一把 `openspec/` 写域锁串行化，任一方的托管块 MUST NOT 被静默覆盖

#### Scenario: CAS 拒绝陈旧验证回写
- **WHEN** `verify-lane` 跑了 5 分钟，期间另一 session 改了同一 lane 的 `verification.method`（`status` 未变）
- **THEN** 回写时快照 digest 比对失败，脚本 exit 拒绝，要求重跑验证

#### Scenario: 锁不跨长跑持有
- **WHEN** 某泳道的验证需跑 5 分钟
- **THEN** 锁在验证执行期间**不被持有**（只在写状态的瞬间持有），并发 session 不会把它误判为残留锁

#### Scenario: 生成的脚本可执行
- **WHEN** skill 生成 doctor 脚本
- **THEN** 落盘后具备可执行权限（`0o755`），MUST NOT 因硬编码 `0o644` 而落盘即不可执行

### Requirement: 触发分工与前置声明

`sdflow-devenv` 的 description SHALL 聚焦环境词面（定测试策略 / 搭开发环境 / 建测试环境 / 配 CI / 加测试泳道 / 这个项目怎么测），并含与 `sdflow-init` 的分流判据句：**装 workflow 流程规则 → `/sdflow-init`；建项目 dev/test 环境 → `/sdflow-devenv`**。

**分流 MUST 是双向的**〔DX〕：`sdflow-init` 的 description **SHALL 同时补一句反向排除句**（「不管理项目的 dev/test 运行环境 / 依赖 / CI —— 那部分 → `/sdflow-devenv`」）。词面碰撞（"初始化环境"）是双向的，**只补一边不解决路由**。

description SHALL 注明前置：需已 `sdflow-init`（无 `openspec/` 布局 → fail-closed）；**建议**先 `sdflow-architecture`（无 SAD → 降级可跑）。

真硬件泳道 SHALL 指向既有 `embedded-test-sop`，**MUST NOT 重造**手动测试 SOP。

#### Scenario: 双向分流句
- **WHEN** 检查两个 skill 的 description
- **THEN** `sdflow-devenv` 含「装流程规则 → init」判据句，且 `sdflow-init` 含「建项目 dev/test 环境 → devenv」反向排除句

#### Scenario: 真硬件泳道复用既有 skill
- **WHEN** 项目命中真硬件依赖形态
- **THEN** skill 指向 `embedded-test-sop` 作为该泳道的人工验证方法，不自行产出手动测试 SOP
