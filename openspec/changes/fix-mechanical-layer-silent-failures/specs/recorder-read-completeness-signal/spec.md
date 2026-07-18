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

消费方读到**缺少该字段**的 `scan --json` 输出时，**MUST** 将全部 `problems` 视为阻断级（fail-closed）。

**MUST NOT** 把「字段缺席」解释为「无阻断项」——缺席的成因是产出方不认识该字段（版本滞后），此时它对自身读取完整性的判断力恰恰最弱。

#### Scenario: 滞后产出方的输出被保守处置

- **WHEN** 消费方收到的 `scan --json` 不含阻断集字段，且 `problems` 非空
- **THEN** 全部 `problems` 按阻断处置，命令非零退出

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

两条路径的完整性判据 **MUST** 抽成**单一函数**共用，**MUST NOT** 各写一套（否则必然漂移；承 `adr/0011`）。

#### Scenario: reindex 在阻断下零写盘

- **WHEN** 取数产生非空阻断集，随后执行 `reindex`
- **THEN** 命令非零退出，且 `INDEX.md` 与 `batches.md` 字节均未变

#### Scenario: batch rename 在阻断下零写盘

- **WHEN** `read_rename_snapshot` 解析出的盘面触发完整性阻断
- **THEN** 命令在 `retag` 与任何 `atomic_write` **之前**非零退出；批次注册表与全部 dated 文档字节均未变

#### Scenario: 两条路径判据同源

- **WHEN** 检视实现
- **THEN** subprocess 路径与 in-process 路径调用的是**同一个**完整性判定函数

#### Scenario: 不读两池的命令有依据地排除

- **WHEN** 为本需求编写测试
- **THEN** 真正读两池的每条路径**各有**一条阻断断言；`batch lint` / `batch add` / `set-status` **不**编写阻断断言，且该排除在文档中附有依据（不读两池）
