## ADDED Requirements

> ## ⭐ 总则：机械层**防漏，不防伪**〔三轮 spec-review 后拍定 · 真相源 `docs/sad/07` §0.0〕
>
> **skill 的目标是「有了这些过程，也有了人认可的结果」——不是「证明模型没有撒谎」。**
>
> | | 机械层 **MUST** 保证 | 机械层 **MUST NOT** 试图保证 |
> |---|---|---|
> | | **防漏（完整性）** | **防伪（真实性）** |
> | 内容 | 三层五槽有没有留白 · 泳道有没有验证方法 · `不适用` 有没有记后果 · `human` 有没有写「为什么程序跑不了」和「人怎么做」· 未完成的有没有被逐条列出来 | 这个 `verified` 是不是真跑过 · 人是不是真确认了 · smoke 是不是真穿过依赖 · `covers` 是不是真命中 |
> | 性质 | **结构检查**——全部有确定性信号 | **需要信号锚**——脆弱或不存在，**且本就不必防**（使用者就是那个人自己，他没有动机骗自己） |
>
> **三条推论（MUST 遵守）**：
>
> 1. **写下任何一条「MUST 机械保证 X」之前，先问「这个保证的信号从哪来」。** 答不上来 ⇒ 删掉它，或诚实划归语义层（人门 + 冷审）。**MUST NOT 硬凑一个长得像机械的东西**（枚举 / dispatch 表 / 白名单 / 派生自不存在的锚）。
> 2. **假机械比诚实的语义层更危险**——它让人以为有防线。
> 3. **能力边界如实写**：`verified` 是 **`verified-at <sha>`**（一次历史执行的记录），**不是「当前状态的绿灯」**；recipe 内部起的容器 skill **管不着**——**如实告知，不假装能回收**。
>
> **被本总则删除的方案见 `07` 附录 A13–A20**（negative control / 测试计数门槛 / `isolate` / `predicate` / `owned_by` 派生 / cleanup 自动记账 / `confirm-lane` 身份保证 / `method_digest` 的「可达」覆盖 / 三层框架的 Markdown 解析）。

---

### Requirement: preflight 两级与三模式分流

skill 每次触发 SHALL 先跑 `devenv_scaffold.py init`，按退出码分流，MUST NOT 自造半套布局、MUST NOT 静默继续。

- **无 `openspec/` 布局 → fail-closed**（exit 3）：原样转述 preflight 指引（先 `/sdflow-init`）。
- **`sad.md` 缺失 → 显式降级，不 fail-closed**：SHALL 响亮警告「拿不到子系统 contract 清单与外部依赖清单，泳道覆盖对账失效、依赖形态只能靠读码猜，可能漏边界；建议先 `/sdflow-architecture`」，并在 `environments.md` frontmatter 留痕 `sad: missing`，然后继续。**MUST NOT 佯装有 SAD**。
- **`environments.md` 已存在**（exit 4）：MUST NOT 静默覆盖，SHALL 显式向操作者区分 **continue**（推进泳道 / 增补）与 **replan**（技术栈或测试策略被推翻，重走设计）后带 `--on-exists` 重跑；continue 前 SHALL 先读 `devenv-log.md` 定位断点。
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

**批量呈现纪律（贯穿全流程，MUST NOT 只用在本步）**〔DX〕：凡「模型给候选 → 人确认」的环节（SAD 投影事实 · **三层框架五槽** · **泳道候选** · **验证方法**），SHALL **一次性批量呈现**为清单供操作者一次确认/挑错，**MUST NOT 逐条打断式提问**。**只有无源事实才逐条提问**——那才是真正需要操作者输入新信息的地方。

#### Scenario: SAD 有源事实需人复核
- **WHEN** SAD 存在且含 §2 约束与 §3 外边界
- **THEN** skill 把投影出的候选事实**批量**呈现给操作者复核，操作者确认或修正后才记录

#### Scenario: 无源事实必须提问
- **WHEN** 需要知道 CI 平台或团队机器可用依赖
- **THEN** skill 向操作者提问并等待回答，MUST NOT 自行臆测

### Requirement: 测试三层框架——三层必答，无一层可留白〔核心承诺〕

**不管什么项目，操作者跑完 skill 都拿到一份完整的测试与验证策略框架。**

三层框架 **MUST 落 JSON**（`.devenv-strategy.json`），`testing-strategy.md` **由脚本从 JSON 渲染**（`DO NOT EDIT` banner）。

> **为什么必须落 JSON**：若让 lint 去解析自由格式 Markdown（定位「单元测试」这一节、切出五个子槽、判断非空），就是**又一个手搓解析器**——本仓前科：`sad_schema.parse_frontmatter` 只支持扁平标量 · `init.py` 的 `inject()` 至今非 fence-aware · `ship_gate` 子串检测曾假阳。**`lanes[]` 已经落 JSON 了，同一道理必须贯彻**〔`07` 附录 A20〕。

**MUST 覆盖三层**：`unit` · `integration` · `e2e`。每层 **MUST 答五槽**（模型研究推荐，**人拍板**）：

| 槽 | JSON 键 | 内容 |
|---|---|---|
| ① 本项目怎么实现 | `how` | 框架 / 库 / 工具选型（**模型现场调研，MUST NOT 由 spec 预先钉死**） |
| ② 测试规范 | `convention` | 测试写在哪（目录/命名）· 什么算一个用例 · 该覆盖什么 |
| ③ 测试方法与流程 | `process` | 怎么跑 · 什么时候跑（本地/CI/提交前）· 谁来跑 |
| ④ 需要配备的工具与脚本 | `tooling` | 要装什么依赖 · 要写什么脚本/harness/fixture（**这些即落地物**） |
| ⑤ 状态 | `status` | `implemented` / `not-applicable` / `manual` |

**⑤ 三态的强制附带项（这是「防漏」的落点）**：

| `status` | **MUST 附带**（JSON 键） | 为什么 |
|---|---|---|
| `implemented` | `lane_ids: [...]` —— 指向的每条泳道 **MUST 存在且 `status ∈ {scaffolded, verified}`** | 声称已实现却没有泳道、**或只挂一条 `planned` 空壳**，都是文档在说谎 |
| **`not-applicable`** | `reason` **+ `consequence`**（「不做这层，我们因此看不见什么」） | **不写后果，`不适用` 就是一个不需要负责的逃生舱**；写了后果，它才是**被知情接受的取舍** |
| **`manual`** | `why_not_scriptable` **+ `human_steps`** | `人工` 不是「这层没人管」的同义词——**人工测试也是测试方法**，必须可复述、可交接、可执行 |

**`status: not-applicable` ⇒ ①–④ 槽豁免**（可统一填 `"不适用，见 consequence"`）。

> **为什么必须豁免**：否则就是逼模型为「不做这件事」编造「怎么实现 / 什么规范 / 什么工具」的废话 ⇒ **机械层奖励写满五槽的空话、惩罚诚实地说四槽不适用**（round-3 对抗镜实证的「填表游戏」）。

**反敷衍启发式（与 `blocked_by` 同款，MUST 有）**：`consequence` / `human_steps` **MUST NOT** 为纯占位符（`无` / `没有` / `N/A` / `TODO` / `待定` 独占整段 → 报警）。
> **诚实边界**：这是**启发式**——挡得住敷衍，**挡不住「写得像模像样但其实没用」**。后者归人门与冷审。

**框架是活的，MUST 可迭代**：开发中随时可 `continue` / `replan` 调整（某层从 `not-applicable` 变 `implemented`、工具选型换掉）。
**「不许留白」指五槽必须有答案（哪怕答案是「不适用 + 后果」），不等于要求三层全绿**——粗糙的首答（如「工具选型待调研」）**合法**；空白 / 占位符**不合法**。**首跑拿到「有方向和基本能力」的框架即达标。**

**SAD 缺失时**：集成层的 contract 锚（`covers`）失效 ⇒ 该层的「该覆盖什么」只能靠读码猜 ⇒ **MUST 显式标注此局限**，MUST NOT 佯装覆盖完整。

#### Scenario: 三层全部有交代
- **WHEN** skill 产出三层框架
- **THEN** `unit` / `integration` / `e2e` 三层在 `.devenv-strategy.json` 中各自的槽全部有内容，无一层留白

#### Scenario: 不适用必须记后果且豁免其余槽
- **WHEN** 某纯算法库项目的 e2e 层被判为 `not-applicable`
- **THEN** 该层 MUST 有非占位的 `consequence`（如「集成后的真实使用路径无人验证」）；`how`/`convention`/`process`/`tooling` 四槽**豁免**，lint MUST NOT 因其为占位内容而报错

#### Scenario: 人工层必须写清为何不可脚本化与人怎么做
- **WHEN** 某嵌入式项目的 e2e 层只能靠人烧板实测
- **THEN** 该层 `status: manual`，`why_not_scriptable` 与 `human_steps` 均非占位（指向 `embedded-test-sop`）

#### Scenario: 已实现的层不能挂靠空壳泳道
- **WHEN** 某层 `status: implemented`，其 `lane_ids` 指向的泳道 `status` 为 `planned`
- **THEN** lint fail-closed——`implemented` 要求对应泳道 `status ∈ {scaffolded, verified}`

#### Scenario: 后果段敷衍被抓
- **WHEN** 某层 `consequence` 内容为「无」
- **THEN** lint 报警

### Requirement: 泳道设计候选与拍板

skill SHALL 按 `references/lane-patterns.md` 的**依赖形态四问**（有无外部有状态依赖 / UI / 语言桥 / 真硬件）推导泳道候选，**MUST NOT 按语言分格**。一个项目 = 多个形态叠加，泳道 = 各形态阶梯的**并集**。

`lane-patterns.md` SHALL **只固化「问什么」**，**MUST NOT 固化「答什么」**——工具选型 SHALL 由模型现场调研推荐、**由人决策**。参考实例 SHALL 标注为「实例，非规格」。

**未覆盖形态** SHALL 走兜底：模型按四问临场推导并**显式标注「本形态无参考实例，系临场推导」**，同时登记 todo，**MUST NOT 凭空编造权威候选**。

拍板产出 SHALL 含：泳道清单 · **各属哪一层（`layer`）** · 各测什么 · mock 边界 · 各自 `covers` · **最小可用集**。

#### Scenario: 按依赖形态而非语言推导泳道
- **WHEN** 项目为 Go 后端 + 外部 broker + Svelte 前端 + 语言桥绑定
- **THEN** skill 按形态叠加产出泳道并集，而非按 Go/Node 分别套用语言模板

#### Scenario: 未覆盖形态不编造权威候选
- **WHEN** 项目落到 lane-patterns 无参考实例的形态
- **THEN** skill 临场推导候选并显式标注「无参考实例，系临场推导」，同时登记 todo

### Requirement: 验证方法——模型研究提方案，人拍板；尽可能跑一遍确认〔核心〕

**每条泳道 MUST 有一个验证方法。** 由**模型根据该项目的实际开发/测试环境现场研究并推荐**（含**自陈的强度与盲区**），**由操作者拍板**。

> **为什么不在 spec 里枚举验证方法**：前一版把 negative control 写成 `verified` 的**定义**，随即被迫为它发明 `isolate` / `expected-failure predicate` / `kind → 策略 dispatch` / runner 白名单——**一整片复杂度，全是在给一个不该被钉死的答案打补丁**，且三轮评审逐一证伪（`07` 附录 A13–A15）。**真实项目的验证方法由环境决定，不可预先枚举。spec 能定的只有证据的形状。**

**`executor` 的优先级：`script` 是默认、是首选；`human` 是降级路径。**

**模型 MUST NOT 预判「这个大概跑不了」就直接标 `human` 偷懒——先试着跑。**

**「跑不了」有两种，MUST 分清**：

| 情形 | 处置 | 例子 |
|---|---|---|
| **方法本身没法用程序跑** | `executor: human`，**MUST 写 `why_not_scriptable`** | 真硬件烧板 · UI 视觉判断 · 需人眼看的交互 · 非 POSIX 平台 |
| **方法能跑，但当前条件不具备** | **`scaffolded` + `blocked_by`**（下次 `continue` 再跑） | 本机没装 mosquitto · 没有 Docker |

> **前一版把这两者混成一条 `human` 通道** ⇒「本机缺个依赖」也被标成「这条只能人工验证」——**那是在撒谎**。

**「无法验证」不是合法状态**——**人工测试也是验证方法**。故本 spec **不设** `n/a` 通道。

**`verification.method` 与 `verification.strength` 为空 ⇒ lint fail-closed。**

模型 SHALL 在 `strength` 中**如实说明该方法证明了什么、盲区是什么**（如「只证明命令耦合了依赖，不证明断言有效」），**MUST NOT** 把弱信号说成强保证。`references/verification-patterns.md` 提供参考实例（**标注「实例，非规格」**）与**已知负面知识**（`07` §3.2 E10 注）。

**防偷懒不靠机械**：人门会看到每条 `human` 的 `why_not_scriptable`；六条泳道全标人工，操作者自己就觉得不对劲。**让人看得见，而不是让脚本抓贼**（总则）。

#### Scenario: 模型提方案人拍板
- **WHEN** skill 为某条外部依赖泳道设计验证方法
- **THEN** 模型研究并推荐具体方法（含强度与盲区），**批量**呈交操作者拍板，确认后才写入

#### Scenario: 无验证方法或无强度自陈的泳道被拒
- **WHEN** 某泳道的 `verification.method` 或 `verification.strength` 为空
- **THEN** `devenv_lint` fail-closed 并报出该泳道

#### Scenario: 缺依赖不等于只能人工
- **WHEN** 某泳道的验证命令可被程序执行，但本机没装 mosquitto
- **THEN** 该泳道 `executor` 保持 `script`，状态为 `scaffolded` + `blocked_by`，**MUST NOT** 被标成 `executor: human`

#### Scenario: 脚本验不了的走人工验证
- **WHEN** 某泳道 `kind: hardware`
- **THEN** `executor: human`，`why_not_scriptable` 与 `human_steps` 均非空，该泳道**仍可**推进到 `verified`（经人门确认）

### Requirement: 泳道三态与渐进 DoD

每条泳道 SHALL 独立处于三态之一：`planned` → `scaffolded`（harness + smoke 已写、验证方法已定，未验）→ `verified`（验证方法已执行，结果被认可）。

skill 的完成态 **MUST NOT 要求全部泳道 `verified`**——允许停在 `planned` / `scaffolded`，不阻塞（渐进 DoD）。

**但诚实是硬要求**：`scaffolded` 态 **MUST 带非空 `blocked_by`**，且 `blocked_by` **MUST 含可辨认的修复指引**（可执行命令片段 / 明确的待办动作）。仅有 `TODO` / `待定` / 空白字符类内容 ⇒ 报警。
> **诚实边界**：此校验是**启发式**——挡得住敷衍，挡不住「写得像模像样但没用」。后者归人门。

收尾时 skill **SHALL 逐条列出**仍处于 `planned` / `scaffolded` 的泳道，**MUST NOT 只埋进文件里**；并 SHALL 用一句话给出**整体判定与下一步**（如「环境已可用于 N 条能力，M 条待补；下次直接触发本 skill 即走 continue」），**MUST NOT 让操作者自己猜**。

#### Scenario: 依赖缺失不算失败
- **WHEN** 本机无 mosquitto 导致集成泳道跑不起来
- **THEN** 该泳道留在 `scaffolded` 且 `blocked_by` 写明「本机无 mosquitto — `brew install mosquitto` 后 `/sdflow-devenv` continue」，skill 继续处理其余泳道

#### Scenario: 敷衍的 blocked_by 被抓
- **WHEN** 某 `scaffolded` 泳道的 `blocked_by` 内容为 `TODO`
- **THEN** `devenv_lint` 报警

#### Scenario: 收尾显著呈现未完成泳道与下一步
- **WHEN** skill 收尾且存在未 `verified` 的泳道
- **THEN** 收尾报告逐条列出这些泳道及其 `blocked_by`，并给出整体判定与下一步调用方式

### Requirement: 状态迁移的执行者分工——证据只能由执行者本人写

**`verified` MUST NOT 由模型传入。`set-lane --status verified` MUST 一律拒绝**——`set-lane` 只管 `planned` / `scaffolded` 两态。

> **理由**：若无脚本亲自执行，实际数据流只能是「模型跑 → 模型读 exit code → 模型调 `set-lane --status verified`」⇒ 脚本对「到底跑没跑、绿没绿」**零独立证据** ⇒ 退化为「**模型自称，脚本盖章**」。
>
> **注意本条不是「防伪」**（总则）——它的价值是：**脚本顺手就能拿到真实的 exit code，成本极低，且对「过程完整」确实有用**（能当场告诉操作者「这条跑得起来 / 这条缺 mosquitto」）。**它保证的是「跑过了」，不是「模型没撒谎」。**

**两条通道**：

| `executor` | 子命令 | 证据 |
|---|---|---|
| `script` | **`verify-lane`** —— 脚本**自己 fork 执行** `verification.method`，捕获 exit code / 时长 / 输出摘要，**自行决定**写 `verified` 还是 `scaffolded + blocked_by` | `at` · `at_commit`（HEAD SHA）· `exit` · `output_digest` · **`file_digests`** · **`method_at_verify`** |
| `human` | **`confirm-lane`** —— 人跑完人工验证后，经人门写入 | `at` · `at_commit` · **`confirmed_what`** · **`file_digests`** · **`method_at_verify`** · **`attested_by: human`** |

> **`verify-lane` 同时是「target 存在且能跑」的唯一判官**〔A21〕：`selector` 拼错 / target 不存在 ⇒ make 报 `No rule to make target` ⇒ `exit≠0` ⇒ **进不了 `verified`**。**make 自己解释自己的语法**——覆盖 100% 语法面，零解析器。**MUST NOT** 在 verify 之前另加一道「静态检查 target 是否存在」的正则。

**`confirm-lane` 产出的 `verified` MUST 如实标 `human-attested`（人说的，不是脚本验的）**，并在渲染进文档时**与脚本验证的绿可区分**。

> **MUST NOT 声称「脚本保证了执行者本人写入」**〔`07` 附录 A18〕：**在 agent session 里，模型是唯一的命令执行者**——人只在对话里回答「同意/否决」，从无「人亲自开终端敲命令」的通道。「模型 MUST NOT 代替操作者调用」这句话**按字面永远为假**。**且本就不必防**（总则：使用者就是那个人自己）⇒ **如实标注，不设防伪。**

**`verified` 的语义 MUST 钉死：它是 `verified-at <sha>`——一次历史执行的记录，不是「当前工作区状态的绿灯」。**

> **理由**：`file_digests` **不覆盖被测实现**（覆盖它需要跨语言 import 图静态分析，零第三方依赖做不到——`07` 附录 A19）⇒ **业务代码一改，那个绿灯就在说谎**。故渲染进文档时 **MUST 带 commit 锚**，**MUST NOT 呈现为无条件的绿**。

**`evidence.file_digests` 的覆盖面（MUST 明确，MUST NOT 写「可达」这种做不到的词）**：`source.file`（非 `-` 时，**整份文件的原始字节；MUST NOT 提取 recipe body**〔A21〕）+ `smoke` 文件 + **lane 显式声明的 `fixtures: []` 清单**。
`fixtures` 由**模型声明、人门确认**（无独立信号 ⇒ 语义层，进 ③-pre 分类清单）。

**`evidence.method_at_verify` MUST 记录验证发生时的 `verification.method` 原文**（一个字符串）：

> **为什么需要它**〔A21 的面治补口〕：旧 `method_digest` 覆盖「验证命令字符串 + recipe body + smoke + fixtures」。A21 把它换成只认**文件**的 `file_digests` 后，**`verification.method` 这个字符串本身掉出了时效锚**——人把 `method` 从 `make integration` 改成 `make integration-fast`，一个文件都没动 ⇒ `file_digests` 不变 ⇒ lint 全绿 ⇒ `verified` 继续挂着，**而它验的根本不是这条命令**。
> **它过闸门**：信号 = 两个字符串比较（确定性）；性质 = **防漏**（操作者改了方法忘了重跑），**非防伪**。成本 ≈ 一个字段 + 一行比较。
> **CAS 不顶替它**：`plan_snapshot` 覆盖 `method`，但那是**验证执行期间的并发保护**（防止跑到一半被改），**不是跨时间的时效检测**——两者作用域不同。

**证据失效**：以下任一 ⇒ lint **MUST** 报「验证证据已过期，需重验」，**MUST NOT** 继续声称 `verified`：

1. **`file_digests` 失配**（`source.file` / `smoke` / 声明的 `fixtures` 任一字节变了）→ 报「`<file>` 已改动」。**允许多报**（改了 Makefile 里别的 target 也触发）——刻意如此，**防漏宁可多报**〔A21〕
2. **`verification.method` ≠ `evidence.method_at_verify`** → 报「验证方法已改动（`<旧>` → `<新>`），需重验」

> **仍然覆盖不到的（MUST 如实写明，MUST NOT 佯装）**：**被测实现**（`07` A19：跨语言 import 图分析零依赖做不到）⇒ **`verified` 是 `verified-at <sha>`**。

#### Scenario: 改了验证方法字符串使证据过期
- **WHEN** 某 `verified` 泳道的 `verification.method` 被从 `make integration` 改为 `make integration-fast`，但未重跑验证
- **THEN** lint 报「验证方法已改动，需重验」——**MUST NOT** 因「文件都没变、`file_digests` 未失配」而放行

#### Scenario: 模型不能自称 verified
- **WHEN** 调用 `set-lane --id X --status verified`
- **THEN** 脚本拒绝，提示「`verified` 只能由 `verify-lane`（script）或 `confirm-lane`（human）产出」

#### Scenario: verify-lane 亲自执行并落证据
- **WHEN** 对 `executor: script` 的泳道调用 `verify-lane --id X`
- **THEN** 脚本自己 fork 执行验证命令，把 `exit` / `output_digest` / **`file_digests`** / `at_commit` 写入该 lane

#### Scenario: human 通道的绿如实标注
- **WHEN** 某 `executor: human` 泳道经 `confirm-lane` 进入 `verified`
- **THEN** 数据中标 `attested_by: human`，渲染进 `environments.md` 时显示为「已确认（人工验证）」而非与脚本验证的绿混同

#### Scenario: verified 带 commit 锚
- **WHEN** 渲染 `environments.md` 的泳道状态表
- **THEN** `verified` 显示为 `verified-at <sha 前 7 位>`，MUST NOT 呈现为无条件的绿

#### Scenario: 改了声明的 fixture 使证据过期
- **WHEN** 某 `verified` 泳道 `fixtures` 清单中的文件被修改，`file_digests` 失配
- **THEN** lint 报该泳道验证证据已过期并要求重验

### Requirement: 执行边界与「不伤害」

**最高红线：skill MUST NOT 破坏操作者的机器状态。**

> **本条的适用范围已大幅收窄**〔`07` 附录 A16/A17〕：前一版把「抽掉依赖」写死为 `verified` 的必要步骤，于是「停服务」成了常规动作，需要一整套红线兜底（`owned_by` 派生 + cleanup 自动记账）。**那两个机制的锚都不存在**——`verification.method` 是**任意命令文本**，recipe 内部的 `ctl.sh start` 启了什么，**skill 根本不知道**。
>
> **现在：skill 自己不改变机器状态。** 它只是**跑操作者拍板过的命令**。命令内部做了什么（起容器、起 daemon）是**项目自己的事**，skill **不管理那些资源的生命周期，也不假装能管理**。

**R1 · skill MUST NOT 主动启停任何依赖服务** —— 依赖的启停归 `verification.method` 内部（recipe 自己 `start`/`stop`）或归操作者。**故本 spec 不设 `owned_by` 字段**（无锚可派生）。

**R2 · 超时 MUST 杀进程树，能力边界 MUST 如实告知**：runner SHALL 以独立 process group 启动子进程；超时先 TERM、限时后 KILL **整棵进程树**。

> **如实告知（MUST NOT 假装能回收）**：**recipe 内部起的 Docker 容器不属于子进程组，杀进程树杀不到它。** 超时/中断后 skill **SHALL 响亮报告**「本次验证被中止，**可能留下孤儿资源（容器/端口占用），请检查**」，并把该提示写进 `blocked_by` 与 `devenv-log.md`。**MUST NOT** 声称已清理。

**平台边界**：进程树杀灭 v1 **只承诺 POSIX**（`start_new_session` + `os.killpg`）。**非 POSIX ⇒ `verify-lane` refuse**，响亮告知，该泳道走 `executor: human`。**MUST NOT** 写一段从未在该平台执行过的代码并声称它能杀进程树。（Windows 的 `taskkill /T /F` 零依赖可行但**未实测** ⇒ 挂 Q-5。）

**R3 · 跑前列命令 MUST 连 recipe body 一起展开**：只给操作者看 `make integration` 这一行调用，对「target 里到底跑什么」提供**零信息量**——人只能橡皮图章。

**R4 · 失败 MUST NOT 重试、MUST NOT 进入 debug 循环**——职责是「建 + 验」而非「调通」。

**R5 · MUST NOT 替操作者安装系统依赖**——只提供 doctor 脚本与安装命令。

**R6 · 真硬件泳道 MUST NOT 由脚本执行**：`kind: hardware` ⇒ `verify-lane` refuse ⇒ 走 `executor: human`（指向 `embedded-test-sop`）。
> **`kind` 的诚实边界**：`kind` 是模型填的、**无独立信号** ⇒ **MUST 进 ③-pre 人门分类清单 + 冷审分类镜**，**MUST NOT 佯装这是纯机械识别**。

**R7 · 子进程 MUST 走最小环境 allowlist，MUST NOT 继承 agent 的完整环境**：

> **理由**：命令继承 agent session 的完整环境变量后，**被执行的 recipe 或其下游脚本可把凭证写进文件、发往网络**——**事后打码管不着这些**。**recipe 展开不能替代执行环境隔离。**

**默认 allowlist SHALL 覆盖真实工具链的最低需求**（`references/` 给按栈的推荐起步集，标「实例，非规格」）：`PATH` · `HOME` · `SHELL` · `TMPDIR` · `LANG`/`LC_ALL` · `TERM` · **按栈追加**（Go：`GOPATH`/`GOCACHE`/`GOMODCACHE`/`GOPROXY`/`GOFLAGS`；Docker：`DOCKER_HOST`/`DOCKER_CONFIG`；网络：`SSL_CERT_FILE`/`*_PROXY`）。
lane 需要的额外变量 SHALL **显式声明**（`env: []`）；**该声明无独立信号 ⇒ MUST 进 ③-pre 人门清单**。**敏感变量需人门单独授权，且 MUST NOT 落盘。**

落盘的命令输出 SHALL **额外**截断 + 过 secret 正则打码——**但此为 best-effort 缓解、非泄露保证**；正则集合 SHALL 登记已知盲区，**MUST NOT 用绝对语气佯装保证**。

#### Scenario: 中止后如实告知可能的孤儿资源
- **WHEN** `make integration` 超时被杀，而它内部起的 Docker 容器不在子进程组内
- **THEN** skill 杀掉能杀的进程树，并**响亮报告**「可能留下孤儿资源，请检查」写进 `blocked_by` 与 devenv-log，**MUST NOT** 声称已清理

#### Scenario: 非 POSIX 平台不做无证据的执行
- **WHEN** 在非 POSIX 平台触发 `verify-lane`
- **THEN** 脚本 refuse 并告知平台限制，该泳道改走 `executor: human`

#### Scenario: 子进程不继承完整环境
- **WHEN** runner 执行验证命令
- **THEN** 子进程环境由 allowlist 构造，agent session 的其余环境变量（含凭证）MUST NOT 被继承

#### Scenario: 跑前展开 recipe
- **WHEN** skill 即将执行 `make integration`
- **THEN** 呈现给操作者的内容包含该 target 的 recipe body，而不只是 `make integration` 这一行

### Requirement: 路径边界校验——所有模型提供的路径 MUST 经 containment 检查〔codex round-3〕

`source.file` · `smoke` · `fixtures[]` · 外部配置文件 · touched-files 清单 —— **全是模型填的自由文本**。

**所有读 / 写 / 删 / digest 的路径 MUST 经统一的 containment helper**：

1. **只接受 repo-relative 的规范化路径**——拒绝绝对路径、拒绝 `..`
2. **逐级 `lstat` 拒绝 symlink 祖先目录**（不只是目标文件本身）
3. **验证最终 `realpath` 位于消费仓根之内**

任一项不满足 ⇒ **fail-closed 拒绝该路径**，如实报告。

> **前一版只在删源护栏里拒绝「目标文件本身是 symlink」** ⇒ 绝对路径 / `..` / symlink 父目录 / 仓外 realpath **全部畅通**，skill 可被引导去写或删仓外的文件。

#### Scenario: 拒绝仓外路径
- **WHEN** 某 lane 的 `smoke` 字段为 `../../etc/passwd` 或绝对路径
- **THEN** containment helper fail-closed 拒绝，MUST NOT 读写该路径

#### Scenario: 拒绝 symlink 祖先
- **WHEN** 某路径的父目录是指向仓外的 symlink
- **THEN** containment helper fail-closed 拒绝

### Requirement: 落地物追加边界——skill 是追加者非拥有者

落地物（Makefile target / CI 配置 / harness / smoke / doctor）**MUST NOT 设托管区块**——它们是**人机共有的活文件**。skill SHALL 只执行两个动作：**已有的 → 登记** · **缺失的 → 追加**（带一行来源注释供审计）。

**重名冲突 → fail-closed**：欲追加的 target 名已存在 ⇒ 脚本报冲突、留人裁决，**MUST NOT 静默覆盖**。
> **诚实边界**：脚本**只能判定「名字碰撞」**——「语义符不符」**无确定性信号，归模型 + 人**。脚本 **MUST NOT** 佯装它在判断语义。

**门禁逻辑 SHALL 落在 Makefile（或等价项目脚本入口），CI 配置只做调用壳**。项目无 CI → CI 槽显式 `不适用` **并连带记后果**。

**v1 入口支持边界**：`inject` **只支持行文本型入口**（Markdown / Makefile / YAML）。**结构化入口（`package.json`）v1 MUST NOT 直接注入** ⇒ 走 **Makefile 薄壳**。CI 配置 **只生成独立新文件**，MUST NOT 就地改写既有 CI 文件。

**归位模式的 smoke SHALL 从已有测试中选取一条作为锚**，**MUST NOT 新写冗余 smoke**。

#### Scenario: 已有 target 只登记不接管
- **WHEN** 消费仓 Makefile 已有 `integration:` target
- **THEN** skill 将其登记进 `source`（按 selector + digest，非行号），不改写该 target 内容

#### Scenario: 重名即 fail-closed（不判语义）
- **WHEN** 欲追加的 target 名已存在
- **THEN** 脚本报名字冲突并留人裁决，MUST NOT 静默覆盖，且 MUST NOT 声称自己判断了语义

#### Scenario: package.json 项目走 Makefile 薄壳
- **WHEN** 消费仓为 Node 项目
- **THEN** skill 追加 Makefile target 调用 `npm run`，MUST NOT 直接注入 `package.json`

### Requirement: 归位模式——素材盘点、判归属、删源

归位模式 SHALL 在事实采集前插入「素材盘点 → 判归属 → 搬运表」，其后与新建模式共用后半段。

**搬运表 MUST 先给操作者确认再落笔**——归属判定是全流程**唯一无确定性信号**的一步，人门 SHALL 放在此处。

删源 SHALL 区分**三种处置**，以 `grep` 被引用面作判据：引用数为 0 → 可直接删；引用可枚举 → 改掉引用后删；引用面广/散 → **降为一行指针**。

搬运表 **SHALL 单列一节「以下 N 个文件将被整体删除」显著呈现**。

删源后 SHALL 扫描残留引用，**覆盖代码注释**，**排除 `.devenv-backup/`**。

#### Scenario: 搬运表先确认再落笔
- **WHEN** 归位模式完成素材盘点与归属判定
- **THEN** skill 呈现搬运表并等待操作者确认，确认前 MUST NOT 写入或删除任何文件

#### Scenario: 引用面广者降为指针
- **WHEN** 某待删源文件被十余处引用
- **THEN** skill 提议降为一行指针而非整体删除，由操作者拍板

### Requirement: 删源护栏——逐文件校验与可恢复备份

删源前 SHALL 做**一次性入口检查**：`git status` 非空 → 拒绝（提示先 commit 或 stash）。**此检查只在归位删源入口执行一次**——backup manifest 的写入**不重触发**它。

删除任一源文件前，skill **MUST 逐文件校验**（**在 containment 检查之后**）：

1. 仓库有**有效 HEAD**（非 unborn branch）
2. 该文件**已 tracked**（untracked 删了 git 恢复不了）
3. **非 submodule、非 symlink**（含祖先，见 containment Requirement）
4. 其**内容 digest 与搬运表人门确认时一致**（防确认后被改动）

任一项不满足 ⇒ **fail-closed 拒绝删除该文件**。

**backup manifest SHALL 入 git**（`openspec/architecture/.devenv-backup/`，**MUST NOT gitignore**）——「可恢复」必须**跨机器**成立；走 gitignore 则换台机器 / CI / 新 checkout 即失效。manifest SHALL 含**被删文件的完整原内容**（非仅 digest）+ 路径 + mode，并在收尾告知还原方式。

#### Scenario: untracked 文件拒绝删除
- **WHEN** 搬运表中某待删源文件未被 git tracked
- **THEN** skill fail-closed 拒绝删除该文件

#### Scenario: 确认后被改动则拒删
- **WHEN** 人门确认后、执行删除前，某待删文件内容变化（digest 不符）
- **THEN** skill 拒绝删除并要求重新确认

#### Scenario: 删除可跨机器还原
- **WHEN** 归位模式执行了删源
- **THEN** `.devenv-backup/` 下存在**已入 git** 的 manifest（含完整原内容），收尾对话告知还原方式

### Requirement: 冷审与人门

冷审 **MUST 由 fresh 子代理执行**（Agent 工具），**禁止生成 session 自查**。冷审 SHALL 按 `references/review-lenses.md` 取镜，至少覆盖：

- **覆盖镜**：SAD 哪条 contract 未被任何泳道穿过 / `covers` 声明是否真命中
- **验证方法镜**：模型提的验证方法**是否名副其实**（`strength` 有无夸大 · 盲区有无如实说出 · `executor` 判定是否合理 · **`why_not_scriptable` 是否成立**）
- **分类镜**：`kind` / `layer` / `fixtures` / `env` 的声明**是否属实**（**这些无独立信号，却是机械层的输入，必须有一镜专查**）
- **vacuous 镜**（**唯一防线，MUST 如实声明**）：smoke 是否语义恒真 / `assert True` / fixture 是否真的让断言生效——**机械层堵不死此项**（总则）
- **诚实镜**：`planned` 是否被伪装成 `verified` / `blocked_by` 与 `consequence` 是否敷衍 / **`human-attested` 的 `confirmed_what` 是否具体可信**
- **归位模式加删源镜**

冷审失败 SHALL 重派一次；再失败 SHALL **显式报告缺口**，**MUST NOT 无冷审静默过人门**。宿主无 fresh 子代理原语 ⇒ **显式降级并响亮留痕**，**MUST NOT 佯装冷审**。

**人门 MUST 拆成两道，且 diff 门 MUST 在执行之前**：

| 门 | 位置 | 议程 |
|---|---|---|
| **③-pre（执行前）** | 写完落地物、**执行任何验证之前** | ① **新写落地物 diff 全文**（recipe body + smoke 源码）② **验证方法逐条确认**（含 `strength` 的强度与盲区）③ **声明清单过目**：`kind` / **`layer`** / `executor` / **`fixtures`** / **`env`**——**这些是机械层的输入，全部无独立信号，必须人看** ④ 将执行的命令（**recipe 展开**）。**否决 → MUST 按 touched-files 事务清单回退** |
| **④（执行后）** | 冷审之后 | ① 泳道设计复核 ② 未 `verified` 泳道逐条确认 ③ **三层框架的 `不适用` 槽逐条确认**（后果写对了吗）④ **`executor: human` 泳道的人工验证结果 → `confirm-lane`** ⑤ **归位模式：删源清单——MUST 单独拎出，要求比其余议程更明确的确认动作**（不可逆） |

**③-pre 的呈现 SHALL 分级**：**新写的**落地物 MUST 全文展示；**仅登记的既有 target** 只需展示登记映射，**MUST NOT** 要求人重读一遍他自己写的、且 skill 不会改动的代码。
**②③ 两项 SHALL 表格化一次性呈现**（「逐条」= 清单里逐行列出，**不是**逐条打断式提问）。

**人门呈现 SHALL 用人话**：`executor` / `kind` / `layer` 这类字段 SHALL 先翻译成一句后果描述再呈现。

#### Scenario: 生成的代码在执行前被人看过
- **WHEN** skill 写完 Makefile target 与 smoke 源码
- **THEN** 在执行任何验证之前，先呈现完整 diff 供操作者过目

#### Scenario: 全部无信号声明必过人门
- **WHEN** 进入 ③-pre 人门
- **THEN** 议程含 `kind` / `layer` / `executor` / `fixtures` / `env` 的声明清单，表格化一次性呈现

#### Scenario: 仅登记的既有 target 不要求人重读
- **WHEN** 某泳道是登记已有的 Makefile target（skill 不改其内容）
- **THEN** ③-pre 只展示登记映射，MUST NOT 展开该 target 全文

### Requirement: ③-pre 否决的回退——touched-files 事务 journal〔codex round-3〕

skill **MUST 在写入任何落地物之前**，**原子落盘** touched-files 事务 journal（`openspec/architecture/.devenv-txn.json`），记录每个将被触碰的文件：

- 路径（经 containment 校验）
- **原先是否存在**
- **原完整内容**（**非仅 digest**——digest 恢复不了文件）
- 原 mode

③-pre 被否决 ⇒ 按 journal **逐项回退**：**原先存在的** → 用 journal 里的原内容**恢复**；**原先不存在的**（新写的 smoke / harness）→ **删除该文件**。

**skill 每次启动 SHALL 先检查未完成的 journal**——若存在（上次在「写落地物 → ③-pre」之间崩溃），SHALL 向操作者报告并提供「回退 / 继续」选择，**MUST NOT 无视**。

回退成功后 SHALL 删除 journal。

> **前一版的两个致命缺陷**：① 清单**只记 digest 不记内容** ⇒「恢复原内容」**根本做不到**；② 清单**不持久** ⇒ session 崩溃后留下一堆**未经批准的文件**，下次运行无从复原。
>
> **回退 MUST 只按 journal 精确定点**，**MUST NOT** 使用 `git checkout --`（对 untracked **无效**，而「新写 smoke」是**主路径**）或**无路径限定的 `git clean`**（会误删操作者未 `git add` 的其他文件——**「最后一道护栏」内部自带一个破坏性操作**）。

#### Scenario: 否决后新写文件被精确删除
- **WHEN** 操作者在 ③-pre 否决落地物 diff，其中含 skill 新写的 smoke（untracked）
- **THEN** skill 按 journal 删除该新文件、用 journal 里的原内容恢复被修改的既有文件，**MUST NOT** 执行 `git clean`

#### Scenario: 崩溃后下次启动发现未完成事务
- **WHEN** 上次运行在写落地物之后、③-pre 之前崩溃，journal 未删除
- **THEN** skill 下次启动检测到该 journal，向操作者报告并提供「回退 / 继续」选择

### Requirement: lint 的触发点——挂 `sdflow-maintain`

`devenv_lint` **MUST 有自动触发点**：`sdflow-maintain` 在扫描 `openspec/` 一致性时 **SHALL 调用它**。

> **理由（dogfood 自指坑）**：本 change 把「无门禁——检查无任何自动触发点」列为**立项理由之一**，而前一版的 `devenv_lint` **自己也没有任何触发点**。更致命：**「渐进 DoD」允许泳道停在 `scaffolded`，而防止它烂成僵尸文档的唯一措施就是「lint 复述未完成清单」——若无人调用该 lint，该措施为空。**
>
> **诚实边界**：`sdflow-maintain` 是**人主动跑**的 ⇒ 这是「**更响的提醒**」而非**硬门禁**。**MUST NOT 佯装硬拦截。**
>
> **实现说明**：`sdflow-maintain` 现为四类**硬编码**扫描，**无插件挂点** ⇒ 本条是**新增代码**。

`sdflow-maintain` 的报告 SHALL **原样透传** `devenv_lint` 的诚实后缀，**MUST NOT** 二次简化渲染成「verified = ✓」式的绿色状态〔codex〕。

#### Scenario: maintain 扫描调用 devenv lint
- **WHEN** 在已有 `environments.md` 的消费仓运行 `sdflow-maintain`
- **THEN** 扫描结果包含 devenv 健康度：未 verified 泳道清单 · **失配的 `file_digests`** · 空/敷衍的 `blocked_by` · **三层框架的留白**，且原样带诚实后缀

### Requirement: 机械 lint——只查诚实（防漏），不查质量（防伪）

`devenv_lint.py` SHALL 执行以下检查。**每一条都是「防漏」，无一条试图判断「质量」**（总则）：

1. **验证方法非空**：任一泳道 `verification.method` 或 `verification.strength` 为空 → fail-closed
2. **状态与证据匹配**：`verified` ⇒ `evidence` 齐全且 **`file_digests` 未失配** 且 **`verification.method` == `evidence.method_at_verify`**；`verified` ⇒ **`blocked_by` 必须为空**（绿泳道挂着「本机无 mosquitto」= 文档在说谎）；`scaffolded` ⇒ `blocked_by` 非空**且含可辨认修复指引**
3. **三层框架完整性**（读 `.devenv-strategy.json`，**非解析 Markdown**）：三层各自的槽逐一存在且非空 → 缺任一 fail-closed；**`status: not-applicable` 的层豁免 ①–④ 槽**
4. **三层状态的强制附带项**：`not-applicable` ⇒ `consequence` 非空**且非占位**；`manual` ⇒ `why_not_scriptable` + `human_steps` 非空**且非占位**；`implemented` ⇒ `lane_ids` 指向的泳道**存在且 `status ∈ {scaffolded, verified}`**
5. **命令出处一致性**：**只查 `evidence.file_digests` 未失配**（逐文件原始字节）。**MUST NOT** 用行号存在性；**MUST NOT** 对 `source` 做任何 make 语法解析——**既不提取 recipe，也不用正则查 target 存在性**〔A21〕。「target 能不能跑」由 `verify-lane` 真跑一遍让 make 自己判
6. **指针不悬空**：Markdown 链接 + 章节锚可达
7. **删源残留引用**（含代码注释，**排除 `.devenv-backup/`**）
8. **路径 containment**：所有声明的路径经边界校验
9. **入口复述检测**：README/CLAUDE 出现真相源才该有的完整命令表 → 告警

> **第 3/4 条是真机械**：读 JSON 字段（槽在不在、`consequence` 是不是占位、`lane_ids` 指向的泳道状态够不够）——**全是结构性信号**。
> 但脚本 **MUST NOT** 判断「这个后果写得对不对」「这个人工步骤可不可行」「这个验证方法有没有效」——**那归人门与冷审**（总则）。

lint 通过码 SHALL 带诚实后缀（`structure-ok-SEMANTICS-UNCHECKED`）——**lint 通过 = 结构性通过 ≠ 内容已审**。

lint SHALL 按泳道状态分档：`verified` → 强制 2、5；`scaffolded` → 强制 `smoke` 存在 + `blocked_by`；`planned` → 不核验命令出处。**第 3/4 条是文档级检查，与泳道状态无关，每次都跑。**

#### Scenario: verified 泳道证据过期被抓
- **WHEN** 某 `verified` 泳道的 `file_digests` 与当前 `source.file` / `smoke` / 声明的 `fixtures` 的字节内容不再匹配
- **THEN** lint fail-closed 报「验证证据已过期：`<file>` 已改动，请重跑」

#### Scenario: verified 泳道挂着 blocked_by 被抓
- **WHEN** 某泳道 `verified` 但 `blocked_by` 非空
- **THEN** lint fail-closed

#### Scenario: lint 通过码诚实
- **WHEN** lint 全部机械检查通过
- **THEN** 输出的通过码明示「结构通过，语义未核」

### Requirement: 数据模型——两份 JSON 侧文件与出处锚（**零 make 解析**）

**两份机械真相源，均落 `openspec/architecture/`，均为标准库 `json`（零依赖）**：

- **`.devenv-lanes.json`** —— 泳道
- **`.devenv-strategy.json`** —— 测试三层框架

`environments.md` / `testing-strategy.md` **由脚本从这两份 JSON 渲染**（`DO NOT EDIT` banner），**MUST NOT 由人手写**。frontmatter 只留三个**扁平标量**：`sad` · `mode` · `schema_version`。

**`schema_version` MUST 有完整的消费行为**：缺失 → fail-closed；**高于**本实现已知版本 → **fail-closed**「skill 版本过旧，请升级」，**MUST NOT 尽力解析**；**低于**本实现版本 → **v1 阶段无需处理（当前只有 v1）；后续版本演进 MUST 在引入该版本的 change 里显式定义策略**（fail-closed 要求迁移 / 提供 `migrate` 子命令 / 只读兼容），**MUST NOT 在无设计的情况下现场处理**。

**`.devenv-lanes.json` 数据模型**：

```json
{
  "schema_version": 1,
  "lanes": [{
    "id": "mqtt-integration",
    "layer": "unit | integration | e2e",
    "kind": "external-dep | ui | lang-bridge | hardware | pure",
    "status": "planned | scaffolded | verified",
    "verification": {
      "method":   "<模型提、人拍板：怎么验>",
      "executor": "script | human",
      "strength": "<模型自陈：证明了什么、盲区是什么>",
      "why_not_scriptable": "<executor=human 时必填>",
      "human_steps":        "<executor=human 时必填>",
      "evidence": {"at": "...", "at_commit": "<HEAD SHA — 给人读的坐标，不作机械比对基准>",
                   "exit": 0, "output_digest": "...",
                   "file_digests": {"<rel path>": "<sha256(原始字节)>"},
                   "method_at_verify": "<验证时的 method 原文——A21 的面治补口>",
                   "confirmed_what": "<human 时>", "attested_by": "script | human"}
    },
    "source": {"file": "Makefile", "kind": "make-target",
               "selector": "integration"},
    "smoke": "<path>",
    "fixtures": ["<path>..."],
    "env": ["<额外环境变量名>..."],
    "deps": [{"name": "mosquitto", "kind": "compose|host-service|port|toolchain|testcontainer"}],
    "covers": ["<SAD contract 锚>"],
    "blocked_by": "<scaffolded 时必填>"
  }]
}
```

> **无独立信号的字段（MUST 进 ③-pre 人门 + 冷审分类镜，MUST NOT 佯装机械）**：`kind` · `layer` · `covers` · `fixtures` · `env` · `strength` · `why_not_scriptable`。
> **本模型不含 `owned_by`**〔`07` 附录 A16〕——「运行时派生」的锚不存在（skill 不知道 recipe 内部启动了什么）。
> **`source` 不含 `digest`；`evidence` 不含 `method_digest`**〔`07` 附录 A21〕——时效锚统一为 `evidence.file_digests`（逐文件原始字节），**target 级 recipe 解析整个删除**。

**`.devenv-strategy.json` 数据模型**：

```json
{
  "schema_version": 1,
  "layers": {
    "unit":        {"how": "...", "convention": "...", "process": "...", "tooling": "...",
                    "status": "implemented", "lane_ids": ["hermetic"]},
    "integration": {"how": "...", "convention": "...", "process": "...", "tooling": "...",
                    "status": "manual",
                    "why_not_scriptable": "...", "human_steps": "..."},
    "e2e":         {"status": "not-applicable",
                    "reason": "...", "consequence": "<不做这层，我们因此看不见什么>"}
  },
  "known_blind_spots": ["<跨层的已知盲区与测试债>"]
}
```

**出处锚 MUST NOT 按行号**：

> **理由**：`source: "Makefile:11-14"` + lint「查那行存不存在」——**「第 11–14 行存不存在」对任何长度 ≥14 行的文件恒为真**。**这是一个恒真断言，即设计好的假绿。**

**`source` MUST NOT 含 `digest` 字段；lint MUST NOT 对 `source` 做任何 GNU make 语法解析**〔`07` 附录 A21〕——**既 MUST NOT 按 `selector` 重定位 target 提取 recipe body，也 MUST NOT 用正则查 target 存在性**：

> **理由一（禁 recipe 解析）**：**GNU make 的语法面无界**（条件块 / `define` / 双冒号 / 模式规则 / 续行 / 内联 `;` / target-specific 变量…）。手搓 make 解析器只能得到一个对真实 Makefile **有 N 种罢工姿势**的脆件，而**它罢工一次就击穿「不管什么项目都能给一份三层框架」这条核心承诺**——`ifeq`、双冒号、多 target 一行在真实 Makefile 里常见且合理。**同 A20（手搓 Markdown 解析器）同理，且 make 的语法面大一个数量级。**
>
> **理由二（连 target 存在性正则也禁）**：它过不了总则的信号闸门。**正则找不到 target 时**——**① fail-closed 报「不存在」**：但「正则找不到」**≠**「target 不存在」（`ifeq` 包裹 / `define` 内 / 一行多 target 均会漏判）⇒ **复杂 Makefile 上误报罢工，理由一原样复发**；**② 不报**：那它**永远不会 fail** ⇒ **恒真断言 = 假绿**。**两条路都是错的 ⇒ 该检查 MUST NOT 存在。**

**「target 真的存在、命令真的能跑」SHALL 由 `verify-lane` 真 fork 执行来保证——make 自己是权威判官**：

| 失效模式 | 谁抓住它 |
|---|---|
| `selector` 拼错 / target 压根不存在 | **`verify-lane` 跑 `make <selector>`** → make 报 `No rule to make target` → `exit≠0` → **泳道 MUST NOT 进 `verified`**（**make 自己解释自己的语法，覆盖 100% 语法面，零解析器**） |
| target 后来被人删了 / 改名了 | **`file_digests` 失配**（改 Makefile 必然改字节）→ lint 报「已改动，请重跑」 |

**⇒ lint 对 `source` 只查一件事：`evidence.file_digests` 未失配。** 行号仅在 render 时动态生成供阅读、**不作真相**。

> **一般化规则（MUST 贯彻全 skill）**：**凡机械层需要知道「某个 make / shell / 语言构造是什么意思」，正解是「让那个工具自己回答」（真跑一遍 / 调 `make -n`），MUST NOT 手搓解析器去猜。** 本 skill 的核心机制恰好就是「尽可能跑一遍确认」——**跑一遍，就是最强的解析器。**

**时效锚 = `evidence.file_digests`，MUST 逐文件、原始字节、零规范化**：

- **覆盖面** = `source.file`（非 `-` 时）+ `smoke` + lane **显式声明的** `fixtures[]`
- **算法** = `sha256(<文件原始字节>)`，**对所有文件类型一视同仁**；**MUST NOT** 做任何空白/注释/缩进规范化
  > **注**：原「digest 规范化规则按文件类型分治」（Makefile 剥空白保 tab / YAML 原始字节）**整条删除**——它是 **recipe 提取的衍生债**：只有把 recipe body 切出来才有缩进噪声、才需要 normalize。**不提取 recipe ⇒ 无需规范化 ⇒「通用 `normalize()` 把两份缩进不同的 YAML 算出同一 digest」这个假绿在结构上不可能发生。** 严格更强，且不可能踩错。
- **失配语义 = 提醒，不是抓贼**：报「`<file>` 自验证以来已改动 ⇒ 本泳道 `verified` 可能过期，请重跑」。**允许多报**（改了 Makefile 里的**别的** target 也会触发）——**这是刻意的**：多报的代价是重跑一次 smoke，消除多报的代价是 300 行解析器，且方向反了（**防漏宁可多报**）。
- **MUST NOT** 覆盖「smoke **可达**的所有 harness/fixture」（`07` A19：零依赖做不到跨语言 import 图分析）
- **MUST 如实写明：不覆盖被测实现** ⇒ `verified` = **`verified-at <sha>`**（历史执行记录，非当前绿灯）

> **时效锚 MUST NOT 改用 `at_commit` + `git diff`**〔round-4 否决〕：skill 的**主路径**是「落地物刚写完 → 立刻 fork 跑 smoke → 写 `verified`」，**此刻 Makefile target 与 smoke 必然是 uncommitted 的** ⇒ `git diff <at_commit> -- Makefile` **在验证成功的那一瞬间就报「已改动」**，锚在主路径上直接失效。`at_commit` 保留在 `evidence` 里，但它是**给人读的坐标**，**不作机械比对基准**。

**CAS 快照 digest 的算法 MUST 明确定义**：`sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode("utf-8"))`。

#### Scenario: 行号变动不导致假绿
- **WHEN** 操作者在 Makefile 顶部插入三行变量定义
- **THEN** lint **MUST NOT** 因「行号指向的行存在」而通过；`file_digests` 中 `Makefile` 的字节 digest 已变 → 报「`Makefile` 已改动，本泳道验证可能过期，请重跑」

#### Scenario: selector 指的 target 不存在——由 make 自己抓，非静态解析
- **WHEN** 某泳道 `source.selector: "integraton"`（拼错），Makefile 里只有 `integration`
- **THEN** `verify-lane` fork 执行 `make integraton` → make 报 `No rule to make target` → `exit≠0` ⇒ 泳道 **MUST NOT** 进 `verified`，如实落 `scaffolded` + `blocked_by`
- **AND** lint **MUST NOT** 试图用正则静态判断该 target 是否存在（`07` A21：该判断在「找不到」方向无确定性信号）

#### Scenario: 复杂 Makefile MUST NOT 导致 skill 罢工〔核心承诺回归守卫〕
- **WHEN** 项目的 Makefile 用了 `ifeq` 条件块 / `define` 块 / 双冒号规则 / 一行多 target / 续行 / target-specific 变量赋值 / 内联 `;` recipe
- **THEN** skill **MUST 全程正常工作**（digest 是整文件字节，与语法无关；能不能跑由 make 自己判）——**MUST NOT** 出现任何「Makefile 语法不支持 / 无法解析」类的 fail-closed 拒绝
- **理由**：核心承诺是「**不管什么项目**都能给一份三层框架」。**一个语法罢工分支 = 一类项目被拒之门外。**

#### Scenario: YAML 缩进变化必须被 digest 捕获
- **WHEN** 某 lane 声明的 `compose.yml` 的缩进层级被改动（语义变了）
- **THEN** 其 digest 变化被检出（原始字节 sha256 天然捕获），**MUST NOT** 因任何规范化而漏报

#### Scenario: 未知 schema_version 拒绝解析
- **WHEN** JSON 的 `schema_version` 高于本实现已知版本
- **THEN** 脚本 fail-closed 报「skill 版本过旧，请升级」

### Requirement: 文档渲染与两文档边界

skill SHALL 产出两份真相源，落 `openspec/architecture/`（与 `sad.md` 同居），**MUST NOT 落项目根或 `docs/`**：`environments.md`（操作轴：dev / test / deploy）· `testing-strategy.md`（方法轴：三层框架）。

两文档边界 SHALL 守切线：**方法/决策 → testing-strategy；环境/操作 → environments**。架构决策 MUST 引用 SAD 不复述；阶段计划 MUST 归 roadmap。

**渲染 MUST 携带诚实信息**〔对抗镜 round-3〕：

- `verified` **MUST 渲染为 `verified-at <sha 前 7 位>`**，MUST NOT 呈现为无条件的绿
- **`human-attested` 的绿 MUST 与脚本验证的绿可区分**（如「已确认（人工验证）」）
- **每条泳道的 `strength`（强度与盲区）MUST 渲染进文档**——**MUST NOT 只在人门口头呈现**

> **理由**：三个月后另一个人（或另一个 agent）打开 `environments.md`，若只看到「泳道 X：verified ✓」，当初那句「这个方法只证明命令耦合了依赖，不证明断言有效」**已经蒸发**。对首次拍板的操作者，`verified` 是「有盲区披露的、经人确认的绿」；对**任何后来者**，它退化成「绿灯」两个字。

`environments.md` 的每条命令 SHALL 带**出处**；**`不适用` 槽 SHALL 连带记录后果**。

#### Scenario: verified 带 commit 锚与强度披露
- **WHEN** 渲染某 `verified` 泳道
- **THEN** 显示 `verified-at <sha>` + 其 `strength`（该验证证明了什么、盲区是什么）

#### Scenario: 人工验证的绿可区分
- **WHEN** 渲染某 `attested_by: human` 的泳道
- **THEN** 显示为「已确认（人工验证）」，与脚本验证的绿在视觉上可区分

### Requirement: 入口托管注入使用独立 marker

skill SHALL 将「最小命令 + 指针」注入消费仓入口文件（CLAUDE.md / AGENTS.md / README.md）与 `openspec/INDEX.md`，使用**自己的 marker token `opsx-devenv`**，采用 token 定位 + 幂等整块替换语义。

**MUST NOT 写入 `opsx-init` 的托管区块**——注入是整块替换，共用同一 marker 会使两个 skill 互相覆盖。

**`inject` MUST 为 fence-aware**：**MUST NOT** 照抄 `init.py` 的 `inject()`（其 `:49-52` 注释明示判据尚非 fence-aware，会命中代码块内演示的 marker，fence-aware 版本已 defer）。MUST 覆盖 CommonMark 全部 fence 变体（` ``` ` / `~~~` / 四 backtick / 缩进 fence）；孤儿 / 逆序 / 交错 → **fail-closed 报位置**。

入口文件 **MUST NOT 复述**真相源细节，只放最小起步命令 + 指针。

#### Scenario: 独立 marker 不干扰 init 区块
- **WHEN** 消费仓已有 `opsx-init` 托管区块且 skill 执行注入
- **THEN** skill 只创建/替换 `opsx-devenv` 区块

#### Scenario: 代码块内的 marker 演示不被劫持
- **WHEN** 消费仓 README 在 ``` 代码块内演示了 `<!-- opsx-devenv:start -->`
- **THEN** `inject` 不把它当作真 marker

### Requirement: 并发安全写入

所有落盘 **MUST 原子写**（`mkstemp` 唯一 tmp 名 + `os.replace`）；读-改-写序列 **MUST 持锁**。

**`atomic_write` MUST 接受 mode 参数**——`sad_scaffold` 现硬编码 `chmod 0o644`，复用它写 doctor 脚本会**落盘即不可执行**；脚本类落地物传 `0o755`，覆盖既有文件时**保留原 mode**。

**锁 MUST 覆盖整个 `openspec/` 写域，三个 skill 共用同一锁名**（`openspec/.sdflow-write.lock`）。

> **理由（互斥性不可组合）**：给 devenv 单发一把锁，与 `sad_scaffold` 的 `.sad-scaffold.lock` **是两把不同的锁**——但两者写入面**重叠**。且 `init.py` 的 `inject()` 是**裸 `open(w)` 全量覆写，无锁、无原子写** ⇒ devenv 的注入被静默吃掉。

本 change SHALL **同时改造三个 skill 的锁协议**（面治优先于点补）：

1. `devenv_scaffold.py` — 用新锁
2. `sdflow-init/scripts/init.py` — `inject()` **补锁 + 原子写**
3. **`sdflow-architecture/scripts/sad_scaffold.py` — 从 `.sad-scaffold.lock` 迁到共用锁，并补 owner 记录 + 释放前核对**（现 `_acquire_lock` **根本没写入过 owner 信息**，`_release_lock` 也不核对）

**锁 MUST 短持有，MUST NOT 跨验证执行持有**：`sad_scaffold` 的 `LOCK_STALE_SEC = 120` 是为**亚秒级**操作而调，而验证可跑数分钟 ⇒ 锁若跨验证持有，**并发 session 会把活锁判成残留锁** → 提示「删锁重试」→ **两 session 同时写**。**陈旧锁检测由保护变成攻击面。**

**状态写入 MUST 用 CAS，快照 MUST 覆盖整个不可变的 verification plan**：`status` + `executor` + `kind` + `method` + `source` + `smoke` + `fixtures` + `env` + `deps`。

> **理由**：仅比对 `status` 不够——`verify-lane` 在无锁状态下读了这些字段去跑数分钟，期间另一 session 可改它们而**保持 `status` 不变**（它自己的 CAS 照样通过）⇒ 旧验证回写成功。**尤其 `executor` 与 `kind`**：长跑期间 lane 从 `script`/`pure` 被改成 `human`/`hardware`，旧脚本**仍能通过只比 `status` 的 CAS 回写**〔codex〕。

回写 MUST **只 patch 那一条 lane**。

**`cleanup ledger` 已删除**〔`07` 附录 A17〕——skill 不管理它没有启动过的资源。超时/中断后**如实报告可能的孤儿资源**（见「执行边界」R2），**MUST NOT 假装能回收**。

**退出码 MUST 一码一义**，SHALL 提供覆盖全部子命令的**退出码表**（在 `references/` 中，实现期照抄，**不留现场发明空间**）——「CAS 冲突」与「锁被占」**MUST NOT 共用同一码**（前者应重读重跑，后者应退避重试，处置完全相反）。

锁文件 MUST 记 owner（UUID + PID + 时间戳）；释放前**核对 owner**。

`devenv-log.md` SHALL 为 **append-only**；`--line` 含换行符 SHALL 被拒绝。

#### Scenario: 跨 skill 并发不丢注入
- **WHEN** devenv 正在注入 CLAUDE.md，另一 session 同时跑 `/sdflow-init update` 或 `/sdflow-architecture`
- **THEN** 三者经同一把写域锁串行化

#### Scenario: CAS 拒绝陈旧回写（改的不是 status）
- **WHEN** `verify-lane` 跑了 5 分钟，期间另一 session 把该 lane 的 `executor` 从 `script` 改成 `human`（`status` 未变）
- **THEN** 回写时快照 digest 比对失败，脚本拒绝，要求重跑

#### Scenario: 锁不跨长跑持有
- **WHEN** 某泳道的验证需跑 5 分钟
- **THEN** 锁在验证执行期间**不被持有**

#### Scenario: 生成的脚本可执行
- **WHEN** skill 生成 doctor 脚本
- **THEN** 落盘后具备可执行权限（`0o755`）

### Requirement: 触发分工与前置声明

`sdflow-devenv` 的 description SHALL 聚焦环境词面，并含与 `sdflow-init` 的分流判据句：**装 workflow 流程规则 → `/sdflow-init`；建项目 dev/test 环境 → `/sdflow-devenv`**。

**分流 MUST 是双向的**：`sdflow-init` 的 description **SHALL 同时补一句反向排除句**（「不管理项目的 dev/test 运行环境 / 依赖 / CI —— 那部分 → `/sdflow-devenv`」）。**词面碰撞（"初始化环境"）是双向的，只补一边不解决路由。**

description SHALL 注明前置：需已 `sdflow-init`；**建议**先 `sdflow-architecture`（无 SAD → 降级可跑）。

真硬件泳道 SHALL 指向既有 `embedded-test-sop` 作为 `executor: human` 的验证方法，**MUST NOT 重造**手动 SOP。

#### Scenario: 双向分流句
- **WHEN** 检查两个 skill 的 description
- **THEN** 各自含指向对方的判据句

#### Scenario: 真硬件泳道复用既有 skill
- **WHEN** 项目命中真硬件依赖形态
- **THEN** skill 指向 `embedded-test-sop`，不自行产出手动测试 SOP
