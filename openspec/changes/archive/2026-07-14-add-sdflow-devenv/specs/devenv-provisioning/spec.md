## ADDED Requirements

> **真相源 = `docs/sad/07-devenv-skill-design.md`。** 本 spec 只写**契约**（MUST / MUST NOT / Scenario）。
> **一切「为什么不那样做」在 `07` 附录 A1–A28**，本文只留编号引用〔A-n〕（按 `openspec/rules/doc-authoring.md` DOC-1）。
>
> **两条上位原则**，凌驾于下列所有 Requirement：
>
> | | |
> |---|---|
> | **身份**（`07` §0.1） | **skill 是副驾**——辅助搭建环境 **+ 提醒操作者别忘了考虑什么**。不是替人开的生成器，也不是查人岗的审计官 |
> | **机械层边界**（`07` §0.0） | **防漏，不防伪。** 且**防漏的形态是「问」，不是「拦」**——机械层只拦**人看不见的**（`status` 拼成 `verifed` · 路径穿越 · 坏 JSON）；**人一眼看得见的（六槽留白）只报不拦**〔`adr/0021`〕 |

---

### Requirement: 核心承诺——三层框架，一层都不许留白

skill SHALL 对**任何项目**产出一份测试与验证的策略框架：**单元 / 集成 / e2e 三层**，每层交代清楚。

**「留白」定义为「该问的没问出口」，不是「格子里没字符串」**〔`adr/0021`〕：

- **`⚠️ 待定` 是合法产物**——人被问到、当场答不上来，如实落它。**MUST NOT 替人填。**
- **MUST NOT 因为待定太多而拦住流程**——skill 是副驾。
- 三层框架的**结构骨架**（三层都在）SHALL fail-closed；**内容完整性**只报不拦。

**承诺的兑现靠两条，都不是拦截**：

1. **A 层提问清单**（`references/testing-framework.md`）——保证每次都问同样的十五个问题（**枚举完备性不能靠模型临场回忆**）。
2. **代价可见**——`testing-strategy.md` 顶部 SHALL 渲染横幅；收尾报告 SHALL 逐条列出所有待定格。

#### Scenario: 全待定的运行仍然合法且可见
- **WHEN** 一次运行结束，三层十五格全是 `⚠️ 待定`
- **THEN** schema 校验通过，lint 退出码为 **0**（**不拦**）
- **AND** `testing-strategy.md` 顶部渲染 `⚠️ 本框架 15/15 格待定，尚不构成一份可用的测试策略`
- **AND** 收尾报告逐条列出十五个待定格

#### Scenario: 三层骨架缺失则 fail-closed
- **WHEN** `.devenv.json` 的 `layers` 缺少 `integration` 层
- **THEN** schema 校验失败，报「三层框架缺 integration 层 —— 一层都不许留白」

---

### Requirement: 「层」= 保真度刻度，不是测试类型分类法〔A25〕

一条泳道归哪层，SHALL 由「**它穿过哪些真实边界**」判定，**MUST NOT** 由它用什么测试框架判定。

| 层 | 判据 |
|---|---|
| `unit` | **不穿任何真实外部边界**（无网络 / 无真文件 / 无真进程 / 无真依赖） |
| `integration` | **穿过部分真实边界**（真 broker / 真进程 / 真语言桥 / 真生成物） |
| `e2e` | **端到端穿过全部真实边界**（真 UI / 真硬件 / 真部署形态） |

> vitest 的组件测试不连任何真实依赖 ⇒ **单元层**（渲染 DOM 不是穿过真实边界）；语言桥的结构门禁读**真的生成物文件** ⇒ **集成层**。

`layer` 是**唯一**的封闭枚举（它是核心承诺的骨架）。**其余一切分类字段 MUST 是自由文本**〔**A24**〕。

> **封闭枚举 = 未列举的形态当场罢工 = 一类项目被拒之门外**，直接背叛「不管什么项目」。

#### Scenario: 未列举的依赖形态照样合法
- **WHEN** 一条泳道的 `deps` 含 `{"name": "JTAG probe", "note": "接上 ESP-Prog，插 USB"}`
- **THEN** schema 校验通过（`deps[]` **无 `kind` 枚举**）

#### Scenario: deps[].kind 已废除
- **WHEN** `.devenv.json` 里某个 dep 带 `kind` 字段
- **THEN** schema 校验失败，指向 A24

---

### Requirement: 六槽——每层必答，第六槽是这个 skill 存在的理由

每层 SHALL 答**六槽**。其中 **⑤ 状态不问**（从泳道投影算出）⇒ 实际要问的是 **5 × 3 = 十五个问题**。

| 槽 | 内容 |
|---|---|
| ① `how` | 本项目怎么实现（框架/库/工具选型；**MUST NOT 由本 spec 预先钉死**） |
| ② `convention` | 测试规范（写在哪 · 什么算一个用例 · **不该覆盖什么**） |
| ③ `process` | 测试方法与流程（**怎么跑** · 何时跑 · 谁跑）⟹ **落成泳道的 `verification`** |
| ④ `tooling` | 要装什么依赖 · 要写什么 harness/fixture ⟹ **落成泳道的 `deps` + 落地物** |
| ⑤ 状态 | ⚠️ **不问。从 `lanes[]` 投影算出** |
| ⑥ `blind_spots` | ⭐ **这层证明了什么 · 看不见什么** |

**⑥ SHALL 对每种状态都答**（不只是 `不适用`）：已跑绿的层答「这层绿了，你依然不知道什么」；`不适用` 答「不做这层，你因此看不见什么」；`human` 答「人跑一遍能确认什么、确认不了什么」。

> **人最容易忘的不是「用什么框架」**（一搜就有，模型必答）。**人最容易忘的是「我这层全绿了，可我还是不知道什么」。**
> 冷审 SHALL 设**盲区镜**：⑥ 槽写的若对**所有项目**都成立（「单元层不证明集成正确性」），它就是套话，SHALL 报出。

#### Scenario: 不适用时豁免其余槽
- **WHEN** 某层 `status: not-applicable`，带 `reason` + `consequence`
- **THEN** schema 校验通过，①–④、⑥ 槽豁免
- **AND** lint 的待定分母**排除该层**（否则永远「有待定」）

#### Scenario: 不适用 MUST 带后果
- **WHEN** 某层 `status: not-applicable`，只有 `reason` 没有 `consequence`
- **THEN** 拒绝写入，报「不写后果，`不适用` 就是一个不需要负责的逃生舱」

---

### Requirement: 层状态是泳道的投影，MUST NOT 手写〔A25〕

层 **SHALL NOT** 有手写的状态字段。其状态 SHALL 由 `lanes[]` **机械投影**算出：

**🔴 投影 SHALL 取最弱的那条泳道，MUST NOT 取最强的那条**〔A29〕：

| 层状态 | 定义 |
|---|---|
| `not-applicable` | 零泳道 + 人写了 `reason` + `consequence` ← **唯一需要人拍的层状态** |
| `planned` | 有泳道，全部 `planned` |
| `scaffolded` | 至少一条 `scaffolded`，**无 `verified`** → 渲染成「**已搭好，未验证（<blocked_by>）**」 |
| **`partial`** | **有 `verified`，但不是全部** → 渲染成「**⚠️ 部分验证 —— N 条泳道里只跑绿了 M 条**」 |
| `verified` | **全部**泳道 `verified` → 渲染成「**已验证 @ `<sha>` · <日期>**」 |

> **「至少一条 `verified` ⇒ 层 `verified`」是假绿**——它是本 Requirement 要杀的那条病（手写层状态会撒谎），
> **换到投影函数里又长了出来**。mqtt-console 试点实证〔A29〕：e2e 层三条泳道，`packaged-app-boot` /
> `packaged-app-visual` 都是 `planned`（**打包冒烟压根没做，而那正是「能不能交付」的唯一证据**），
> 标题照报「✅ 已验证」。**而标题那一行才是被读的那一行**——下面泳道表里那两个 `○` 救不了它。
>
> **杀掉一个机制，不等于杀掉它的病。**

#### Scenario: 一条绿不能把整层染绿
- **WHEN** 某层三条泳道：一条 `verified`，两条 `planned`
- **THEN** 层状态投影为 **`partial`**，渲染成「**⚠️ 部分验证 —— 3 条泳道里只跑绿了 1 条**」
- **AND** **MUST NOT** 渲染成「✅ 已验证」

**「已实现」/「人工」两个词 SHALL NOT 出现于文档**〔A25〕：

- 「已实现」实指「有脚手架」（其旧定义只要求泳道 ≥ `scaffolded` = **写了但没验**）⇒ **它在装。**
- 「人工」与泳道的 `executor: human` **双写**（违反单一真相源）。

> **层状态零手写 ⇒ 无法伪造、无法漂移。这是结构性保证，不是拦截**——**让坏事没法发生，而不是发生后抓它。**

#### Scenario: 手写层状态被拒
- **WHEN** `.devenv.json` 的 `layers.unit` 带 `status: "verified"`
- **THEN** schema 校验失败，报「层状态是从 lanes[] 投影算出的，MUST NOT 手写」

#### Scenario: 从未跑绿的层不得称为已实现
- **WHEN** 某层唯一的泳道是 `scaffolded`（`blocked_by: 本机无 mosquitto`）
- **THEN** 渲染为「⏸ 已搭好，未验证」，**文档中不出现「已实现」字样**

---

### Requirement: 验证方法——模型研究提方案，人拍板；尽可能跑一遍确认

`verification.method` SHALL 是**一条能跑的命令**。模型现场调研提候选、**自陈 `strength`**（证明了什么 / 盲区是什么），**由人拍板**。

**`executor: script` 是默认首选。** 模型 **MUST NOT** 预判「这个大概跑不了」就标 `human` 偷懒——**先试着跑**。

**「跑不了」有两种，SHALL 分清**：

| 情形 | 状态 |
|---|---|
| **方法本身没法用程序跑**（真板烧录 · UI 视觉判断） | `executor: human` + **为什么程序跑不了** + **人怎么做** |
| **方法能跑，但当前条件不具备**（本机没装 mosquitto） | `scaffolded` + `blocked_by`，下次 `continue` 再跑 |

> **把后者标成前者，是在撒谎。**

**「无法验证」不是合法状态**——人工测试也是验证方法。**不设 `n/a` 通道。**

#### Scenario: 条件不具备不得伪装成不可脚本化
- **WHEN** 泳道 `executor: script`，操作者调 `confirm-lane`
- **THEN** 拒绝，提示「「本机缺个依赖」不是「方法本身没法用程序跑」——把前者标成后者是在撒谎」

---

### Requirement: 状态迁移——证据只能由执行者本人写

| 迁移 | 命令 | 前置 |
|---|---|---|
| — → `planned` | `set-lane --status planned` | 三层框架 ② 步拍板后 |
| `planned` → `scaffolded` | `set-lane --status scaffolded --blocked-by "<原因>"` | **`blocked_by` 非空且含可辨认的修复指引** |
| `scaffolded` → `verified`（script） | **`verify-lane`** | **脚本亲自 fork 执行**，捕获真实 exit code，**自行决定**写 `verified` 还是 `scaffolded + blocked_by` |
| `scaffolded` → `verified`（human） | **`confirm-lane`** | 人跑完后经人门写入，**如实标 `attested_by: human`** |
| `verified` → `scaffolded` | `set-lane --status scaffolded` | **由人决定**——`continue` 时 skill 问一句〔A23：**没有** sha256 时效锚〕 |

**`set-lane --status verified` SHALL 一律拒绝（exit 5）。**

> **⚠️ 这一条 MUST NOT 被当作「防伪」来辩护**——作为防伪它一文不值（`method` 设成 `true` 三个字符就能击穿）〔A18〕。
> **它的真实价值是「副驾顺手帮你试火」**：脚本亲自跑一遍，**当场告诉操作者「这条跑得起来 / 这条缺 mosquitto」**。**它保证的是「跑过了」，不是「模型没撒谎」。**

**`verified` 的语义 SHALL 钉死为 `verified-at <sha>`**——一次历史执行的记录，**不是「当前状态的绿灯」**（任何 digest 都覆盖不了被测实现〔A19〕）。渲染 SHALL 带 **commit 锚 + 日期**，**MUST NOT** 呈现为无条件的绿。

#### Scenario: set-lane 拒绝产出 verified
- **WHEN** 调用 `set-lane --status verified`
- **THEN** 退出码 5，提示用 `verify-lane` 或 `confirm-lane`

#### Scenario: 跑红不是失败
- **WHEN** `verify-lane` 执行的命令 exit 7
- **THEN** 泳道落 `scaffolded` + `blocked_by`（含原始报错摘要），**脚本退出码仍为 0**——**跑不绿是合法状态**

#### Scenario: 人工确认如实标注
- **WHEN** `confirm-lane` 产出绿
- **THEN** `evidence.attested_by == "human"`，渲染时标「**人工确认**」

---

### Requirement: 执行边界与「不伤害」

1. **跑前列命令让人过目**，不偷跑——尤其会起容器 / 占端口的。人可以说「这条跳过，标 `planned`」。
2. **③-pre 人门 MUST 在执行之前**，且 SHALL **给人看 smoke 与 harness 的 diff**——只给「跑什么命令」是不够的（`make integration` 这一行对「里面到底跑什么」提供**零信息量**）。
3. **每条命令有超时**。超时 → `scaffolded` + `blocked_by` 如实写「超时，**未确认**是环境问题还是 smoke 本身挂了」。
4. **失败不重试、不 debug**——**诊断可以给，修复不做**。skill 的职责是「建 + 验」，不是「调通」；一旦允许 debug，它会在一条泳道上耗光整个 session。
5. **MUST NOT 替操作者装系统依赖**——给命令 + doctor 脚本。
6. **真硬件泳道天然不跑**（要烧板）→ `scaffolded` + 指向 `embedded-test-sop`，**不复述那份 SOP**。

#### Scenario: 超时如实记录不确定性
- **WHEN** `verify-lane` 超时
- **THEN** `blocked_by` 含「未确认是环境问题还是 smoke 本身挂了」——**MUST NOT** 断言是哪一个

---

### Requirement: 落地物——按风险分两类，MUST NOT 预设「用什么跑测试」〔A24〕

本 spec **SHALL NOT** 钉死跑测试的载体（Makefile？`package.json` scripts？`justfile`？**还是根本不需要，一条裸命令就够**）。**这是模型看着项目现场决定的。**

| 类 | skill 的纪律 |
|---|---|
| **新建文件**（smoke · harness · 依赖服务启停 · doctor） | 直接写。**风险为零**（文件本来不存在） |
| **改已有文件**（把命令接进项目已有的任务系统） | **① 先给 diff 人确认 ② 幂等标记块 ③ 可精确回滚 ④ MUST NOT 猜文件里原来有什么** |

**默认路径是「不改」**：大多数项目根本不需要接线。

**MUST NOT 解析 Makefile / shell / 任何语言的语法**〔A21〕——**无界语法面禁手搓**。「命令能不能跑」由 `verify-lane` **真跑一遍**，**让工具自己判**。
**要知道文件里原来有什么，SHALL 问人**：「你项目里已经有跑集成测试的命令吗？」

**target 重名的检测方式**：`verify-lane` 跑的时候，**GNU make 自己会打 `warning: overriding recipe for target` 到 stderr** ⇒ **捕获它即可**。**零额外执行、零解析器。**

> **⚠️ MUST NOT 为了检测而额外造一次执行**：`make -n` 探测会**执行任意代码**（`$(shell …)` 在解析期就求值；`include` 的 remake 规则会**真往仓库写文件**）。**正解是从已经在发生的那次执行里读信号。**

#### Scenario: 命令不存在由工具自己判
- **WHEN** `verification.method` 是 `make no-such-target`
- **THEN** make 报 `No rule to make target` → exit≠0 → 泳道进不了 `verified`（**skill 从未解析过 Makefile**）

#### Scenario: target 重名被 make 自己揭发
- **WHEN** `verify-lane` 执行 make，stderr 含 `overriding recipe for target`
- **THEN** skill 响亮报出「检测到 target 重名 —— 你原来的定义可能已被覆盖（后定义的赢）」

---

### Requirement: skill 没有删除能力——可改内容，MUST NOT 删除文件〔A26 · `adr/0022`〕

**skill MUST NOT 删除操作者的任何文件。**

> **爆炸半径不受控**——指向它的引用可能在**仓外**（别人的书签、别的仓的文档、藏在代码注释里的路径）。

| 处置 | skill 做什么 | 内容 |
|---|---|---|
| **整体失效** | 文件**开头**加 `> ⚠️ 已失效 —— 内容已迁至 <path>` | **原样保留**（范围 = 整份，无歧义） |
| **部分失效** | **删掉失效的那部分内容**（+ 留指针） | **删除**——**「失效范围」必须由「它不存在了」界定**；留着内容只加标记，读者无法判断哪几行失效了 |
| **真删文件** | ❌ 收尾报告给出 `git rm <file>`，**人自己敲** | 人决定 |

**引用面统计**（`grep`，**SHALL 扫到代码注释里**）SHALL 带着数字进人门。
**搬运表 SHALL 单列一节「以下 N 个文件建议删除（命令附后）」**——**不许只在表格某行标个 `[删除]` 混过去**。

**由此，「删源前工作区必须干净」这道护栏失去对象，SHALL 删除。**

#### Scenario: 归位模式不删文件
- **WHEN** 归位模式判定 `docs/modules/testing.md` 内容已全部搬走
- **THEN** skill 在该文件**开头加失效标记**，内容原样保留
- **AND** 收尾报告给出 `git rm docs/modules/testing.md`

#### Scenario: 代码里没有删除接口
- **WHEN** AST 扫描 `devenv_scaffold.py` 的调用
- **THEN** 不存在 `unlink` / `rmtree` / `remove` / `rmdir`

---

### Requirement: 路径 containment——所有模型提供的路径 MUST 经校验

`smoke` / 落地物路径 / touched-files 全是**模型填的自由文本**。任何读/写之前 **SHALL 经 containment 校验**：拒绝空路径 · 含空字节 · 绝对路径 · `..` · **symlink 祖先或自身** · realpath 落在仓外。

> **路径穿越是「人看不见的」** ⇒ **必须拦**（区别于六槽留白，那是人一眼看得见的）。

#### Scenario: 路径逃逸被拒
- **WHEN** `set-lane --smoke ../../../etc/passwd`
- **THEN** 退出码 2，报路径越界

#### Scenario: symlink 祖先亦被拒
- **WHEN** 路径的**父目录**是指向仓外的 symlink
- **THEN** 拒绝（**只查目标自身不够**）

---

### Requirement: 数据模型——一份 JSON，零 digest、零封闭枚举（除 layer）

**机械载体只有一份**：`openspec/architecture/.devenv.json`（`layers` + `lanes`）。`environments.md` **完全在机械层之外**（见下）。

**五条 MUST NOT**（逐条对应一条被否方案）：

| MUST NOT | 〔案〕 |
|---|---|
| `deps[]` 有 `owned_by`（「运行时派生」的锚不存在） | A16 |
| `source` 有 `digest`，或是结构化契约（`{file,kind,selector}`） | A21 · **A24** |
| `evidence` 有任何**时效 digest** | **A23** |
| **出处按行号**（行号锚是**恒真断言**） | 机制 B |
| **层状态手写** | **A25** |

**MUST NOT 有文件锁 / CAS / 原子写**〔A23〕——防一个不会发生的并发；JSON 写坏的后果是「重跑一次」，而真代码的护栏是 **git**。
**MUST NOT 用 YAML frontmatter 承载它**〔A20〕——嵌套结构在零第三方依赖下没有可用的解析方案。

**`verified` 的证据 = 一次历史执行的坐标**：`at_commit` · `at_time` · `exit` · `attested_by`。**无时效锚。**

#### Scenario: schema 里没有已否机制的痕迹
- **WHEN** AST 扫描 `devenv_schema.py` 的**标识符与导入**（**非文本、非注释、非报错文案**）
- **THEN** 不含 `digest` / `sha256` / `recipe` / `makefile` / `atomic_write` / `plan_snapshot`
- **AND** 不 `import re` / `hashlib` / `fcntl`

---

### Requirement: 两文档的切线——测试 vs 非测试〔A27〕

| 文档 | 管什么 | 机械载体 |
|---|---|---|
| **`testing-strategy.md`** | **测试的一切**——选型 · 规范 · **命令怎么跑** · 装什么写什么 · 状态 · 信心与盲区。**一层一个完整交代** | ✅ 从 `.devenv.json` **机械渲染**（`DO NOT EDIT` banner） |
| **`environments.md`** | **非测试**——dev 搭建（含 ⭐**常见坑**）· deploy 发布（含 ⭐**回滚**）。test 节 = **一行指针** | ❌ **零 JSON 载体、零机械渲染** |

> **MUST NOT 按「方法 vs 操作」切**〔A27〕——那会把「每层交代清楚」劈成两半，**用户想知道「集成测试怎么跑」就得翻两份文档自己拼**。**一个副驾的产物，不该是两份需要交叉引用的东西。**

**`environments.md` SHALL 有模版 + 提问清单**（`references/environments-template.md`，**十槽**），由 skill **铺骨架 + 逐槽问出来**，**此后归人 own，skill 不再覆盖**。

> **「有模版 + 逐槽问出口」和「有 JSON 载体」是两件事。** 这十槽是**长自由文本**（「新人最容易卡在哪一步」「有没有退不回去的东西」）——**把人写区强行 JSON 化，只会让人写得更烂**（`06` 接地实测：那 10 个纯人写槽**恰恰是全篇最高价值的部分**）。
> **最贵的三槽：常见坑 · 回滚 · 构建副产物**——**它们没有标准答案，模型答不出来，只能问人，所以最容易被静默略过。**

#### Scenario: environments.md 铺完归人 own
- **WHEN** 操作者手改了 `environments.md` 后再跑 `render`
- **THEN** `environments.md` **不被覆盖**（`render` 只管 `testing-strategy.md`）

#### Scenario: test 节只是一行指针
- **WHEN** 检查 `environments.md` 的 §2
- **THEN** 它只含指向 `testing-strategy.md` 的指针，**不复述任何测试命令**

---

### Requirement: lint——只报不拦，代价可见〔`adr/0021`〕

`devenv_lint` SHALL **退出码 0**，**即便十五格全待定**。

**它拦的唯一东西是「人看不见的」**：坏 JSON / schema 不合法（**退出码 2**）——**坏 JSON 渲染不出来，用户只会看到空白文档，还以为 skill 没跑**。

**它 SHALL 报**：

1. **代价横幅**（`⚠️ 本框架 N/M 格待定，尚不构成一份可用的测试策略` + 逐层列出待补的槽）
2. `environments.md` 的待定槽数（**点名最贵的三槽：常见坑 · 回滚 · 构建副产物**）
3. **未 `verified` 泳道 + 其 `blocked_by`**（**逐条列出，MUST NOT 只给计数**）
4. **敷衍的 `blocked_by`**（`TODO` / `环境问题` —— 它没告诉任何人下一步该干嘛）
5. **SAD contract 差集**（`covers` 未覆盖的）——**算出来是为了「问」，不是为了「拦」**

**`environments.md` 的待定 SHALL 用固定字符串计数**（数 `⚠️ 待定` 出现几次），**MUST NOT 解析 Markdown 结构**〔A20〕。

> 「找到 §1.5 这一节、切出内容、判断非空」= **又一个手搓 Markdown 解析器**，会在 fence / 嵌套 / 变体标题上罢工。
> **语法面只有一个元素（那个字面量），穷举得完 ⇒ 合法**〔基准 5〕。

#### Scenario: 全待定仍放行
- **WHEN** 十五格全 `⚠️ 待定`
- **THEN** lint 退出码 **0**，横幅写 `15/15 格待定`

#### Scenario: 报告永不因坏数据崩溃
- **WHEN** 某泳道缺 `id`（坏数据）
- **THEN** 报告仍能打印——**崩了人就什么都看不见，而「看得见」是 lint 存在的唯一理由**

---

### Requirement: 五步流程——核心承诺在第 ② 步产出〔A28〕

```
① 事实采集 + environments.md 十槽逐槽问
② ⭐ 三层框架逐层问六槽 → 泳道随之落定    ← 核心承诺在这一步产出，人门重心
③ 落地脚手架 + 尽可能跑一遍确认
④ 冷审 + 人门
⑤ 渲染 + 入口 + 交棒                      ← 是「渲染」，不是「产出」
```

**②：泳道不是一个独立的设计对象——它是六槽里 ③④ 的答案落成的形状。**

> **顺序 MUST NOT 颠倒**：先决定「集成层要不要做、用真 broker 还是进程内」，泳道才有的设计。**把框架排在泳道后面，等于让实现决定策略**〔A28〕。

**⑤ 从「产出」降为「渲染」**——兑现 §0.1：「目标不是产出两份文档，而是建立环境——文档是产物之一」。
**人门的重心在 ②**（你做决定的时候陪着你），**不在 ④**（你做完之后审你）。

**时序纪律**：SHALL 实际提问并获得回答后才允许记录。**MUST NOT 预填 / 臆测 / 替人拍板。**

**收尾报告 SHALL 逐条列出**（**不许埋进文件里**）：所有 `⚠️ 待定` 格 · 所有未 `verified` 泳道 + `blocked_by` · 所有**建议删除的文件**（附 `git rm` 命令）· 整体判定 + 下一步怎么调用。

#### Scenario: 答不上来落待定而非编造
- **WHEN** 操作者对「e2e 层怎么实现」答「还没想好」
- **THEN** 该槽落 `⚠️ 待定`，**MUST NOT 替人填一个看起来像话的答案**

---

### Requirement: 冷审——vacuous 镜与盲区镜是心脏

冷审 **SHALL 由 fresh 子代理执行**（禁生成 session 自查——**写的人看不见自己的盲区**）。

| 镜 | 何时取 |
|---|---|
| **vacuous 镜** ⭐ | **永远**——「删掉被测逻辑，这条 smoke 会红吗？」**机械层完全不管这个** |
| **盲区镜** ⭐ | **永远**——⑥ 槽写的若对所有项目都成立，它就是套话 |
| 覆盖镜 / 边界镜 / 诚实镜 | 按需 |
| 归位镜 | 仅归位模式 |

**vacuous SHALL 如实声明「机械层堵不住」**〔A12/A13/A14〕：三条机械方案全部证伪——计数门槛**被 `assert True` 完美满足** · negative control **只证耦合不证有效**（且对 testcontainers 永久误判）· 轮询观测**瞬时连接漏检 100%**。
**MUST NOT 佯装机械层能堵。**

> 负面知识 SHALL 记入 `references/verification-patterns.md`——**别让下一个人再走一遍。**

#### Scenario: vacuous 的边界如实写进文档
- **WHEN** 生成 `testing-strategy.md`
- **THEN** 文档中**不出现**任何「本框架保证测试有效」式的声称

---

### Requirement: 入口托管注入使用独立 marker

skill SHALL 用**自己的 marker**（`<!-- opsx-devenv:start -->` / `:end`）注入 CLAUDE / AGENTS / README，**幂等整块替换**。

**MUST NOT 写进 `opsx-init` 的区块**——`inject` 是整块替换，共用一个 marker 会让两个 skill 互相覆盖。

#### Scenario: 注入幂等且不覆盖人的内容
- **WHEN** 连跑两次 `inject`
- **THEN** 文件内容一致，marker 块只出现一次，**原有内容原样保留**

---

### Requirement: 触发分工与前置声明

| 说的是 | 走 |
|---|---|
| 装 **workflow 流程规则**（与技术栈无关） | `sdflow-init` |
| **建项目 dev/test 环境**（完全依赖技术栈） | **`sdflow-devenv`** |
| 分阶段 / 排期 / 里程碑 | `sdflow-roadmap`（时间轴） |
| 划分子系统 / 定 contract | `sdflow-architecture`（空间轴） |

**前置**：需已 `sdflow-init`（无 `openspec/` → **fail-closed，exit 3**）；**建议**先 `sdflow-architecture`（无 SAD → **显式降级，不 fail-closed**）。

#### Scenario: 无 openspec 布局则 fail-closed
- **WHEN** 消费仓无 `openspec/` 目录
- **THEN** 退出码 3，原样转述指引「先跑 `/sdflow-init`」

#### Scenario: 无 SAD 时响亮降级但不阻塞
- **WHEN** `openspec/architecture/sad.md` 不存在
- **THEN** 响亮告警「泳道覆盖对账**失效**；测试策略只能靠读码猜，**可能漏掉边界**」并留痕 `sad: missing`
- **AND** **继续运行**，**MUST NOT 佯装有 SAD**
