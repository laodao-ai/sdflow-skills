## ADDED Requirements

### Requirement: 读取器区分「可能没读全」与「读全了但有瑕疵」

recorder 各池脚本（`buglist.py` / `todolist.py`）产出的 `problems` 诊断项 **SHALL** 在**产生处**被分级：凡表示「本次读取可能不完整」者 **MUST** 同时进入阻断集，其余（读全了、仅某条数据有瑕疵）**MAY** 仅告警。

分级 **MUST** 在 append 诊断项的同一位置判定（产生处已知语义），**MUST NOT** 由消费方对 `problems` 的散文文本做模式匹配还原——那是在无界的自然语言面上手搓解析器（基准 ⑤），且三脚本措辞各自演进必然漂移。

承 `adr/0018` 配套铁律 (d)：切分判据是**该信号是否污染本次输出的完整性**，不是它的严重程度感受。

#### Scenario: 完整性类诊断进阻断集

- **WHEN** 读取时发现块存在但对应总览表行缺失（可能漏读条目）
- **THEN** 该诊断项同时出现在 `problems` 与阻断集中

#### Scenario: 瑕疵类诊断不进阻断集

- **WHEN** 读取时发现重复 ID 或总览表行 arity 异常（已读全，某条数据脏）
- **THEN** 该诊断项出现在 `problems`，但**不**进入阻断集

### Requirement: 阻断集以 additive 字段承载，缺席即全部阻断

`scan --json` 的输出 **SHALL** 以**新增**字段承载阻断集，`problems` 字段自身的类型与内容 **MUST NOT** 改变（既有消费者零影响）。

消费方读到**缺少该字段**的 `scan --json` 输出时，**MUST** 生成一个**独立的阻断 sentinel**，其成立**与 `problems` 是否为空无关**；同时将全部 `problems` 视为阻断级（fail-closed）。

`[spec-review-amendment]` 初版只写「将全部 `problems` 视为阻断」——滞后 producer 完全不认识新盘面格式时可同时产出**空 items + 空 problems + 无该字段**，此时该规则作用在空集上、阻断集仍为空 ⇒ **放行**。∴ 缺席本身必须独立成阻断项。

**字段整体缺席** 与 **明确的空阻断集** **MUST 可区分**：前者是「产出方不认识该字段」⇒ 阻断；后者是「已判定无阻断项」⇒ 放行。

**MUST NOT** 把「字段缺席」解释为「无阻断项」——缺席的成因是产出方不认识该字段（版本滞后），此时它对自身读取完整性的判断力恰恰最弱。

#### Scenario: 滞后产出方的输出被保守处置

- **WHEN** 消费方收到的 `scan --json` 不含阻断集字段，且 `problems` 非空
- **THEN** 全部 `problems` 按阻断处置，命令非零退出

#### Scenario: 缺席字段 + 空 problems 仍阻断

- **WHEN** `scan --json` 同时满足：items 为空、`problems` 为空、且不含阻断集字段
- **THEN** 命令仍非零退出且零写盘（缺席 sentinel 独立成立）

#### Scenario: 既有消费者不受影响

- **WHEN** 只读取 `problems` 字段的既有消费者解析新版 `scan --json`
- **THEN** 其读到的 `problems` 类型与内容与改动前一致，解析不失败

### Requirement: 阻断判定覆盖每一条真正读两池的取数路径

阻断判定 **SHALL** 覆盖**每一条真正读取两池数据的路径**，**MUST NOT** 仅对个别子命令收集。

受覆盖路径 **MUST** 包含：

- **subprocess `scan --json` 路径**（`sweep`、`reindex`、`batch rename` 后半）——经 additive 阻断集字段承载；
- **in-process snapshot 路径**（`batch rename` 前半）——**无 JSON 字段可缺席**，**MUST** 另立判定（见下）。

**只读批次注册表、不读两池的命令**（`batch lint`、`batch add`、`set-status`）**不在本需求范围内**——它们不存在「读残缺」风险。为其编写阻断断言 **MUST NOT** 被视为覆盖度，那是无法写出真断言的假绿。

**写盘类**路径的阻断判定 **MUST** 前置于**任何**写盘动作（承 `adr/0022`）。

两条路径的完整性判据 **MUST** 发同一套**机器可读 diagnostic code**，并由**同一份 conformance fixtures** 机械核验三个 producer/parser 对同一畸形输入吐出相同码。

**MUST NOT** 要求两路调用同一个 Python 函数——`_scan_pool` 走 subprocess 正是为避免跨 skill import（`adr/0025`：三份 helper 物理复制、维护成本由 fixtures 与 parity 承担）。「同一函数」照字面落地只能引入被禁的跨 skill 运行时耦合，或**各写两份却伪称同源**（后者测不出漂移）。**同源的是契约，不是函数体。**

#### Scenario: reindex 在阻断下零写盘

- **WHEN** 取数产生非空阻断集，随后执行 `reindex`
- **THEN** 命令非零退出，且 `INDEX.md` 与 `batches.md` 字节均未变

#### Scenario: batch rename 在阻断下零写盘

- **WHEN** `read_rename_snapshot` 解析出的盘面触发完整性阻断
- **THEN** 命令在 `retag` 与任何 `atomic_write` **之前**非零退出；批次注册表与全部 dated 文档字节均未变

#### Scenario: 三方对同一畸形输入吐出相同 diagnostic code

- **WHEN** 把同一份 conformance fixture（含各类畸形盘面）分别喂给 `buglist.py`、`todolist.py` 与 `issues.py` 的 in-process parser
- **THEN** 三方产出的 diagnostic code 集合相同；任一方偏离即非零退出

> 本 Scenario 取代初版的「WHEN 检视实现 THEN 调用同一个函数」`[spec-review-amendment]`——那个 WHEN **不是运行时可触发条件**，只能靠人读代码，属伪机械门（与 R7 初版同病）。

#### Scenario: 不读两池的命令有依据地排除

- **WHEN** 为本需求编写测试
- **THEN** 真正读两池的每条路径**各有**一条阻断断言；`batch lint` / `batch add` / `set-status` **不**编写阻断断言，且该排除在文档中附有依据（不读两池）
