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

### Requirement: 阻断判定覆盖全部取数调用方

阻断集 **SHALL** 在**共用取数入口**被收集并向全部调用方传递，**MUST NOT** 仅对个别子命令收集（现状：多数调用方传空、连诊断都看不到）。

受覆盖的调用方 **MUST** 至少包含：`sweep`、`reindex`、`batch rename`、`batch add`、`set-status`、`lint`。**写盘类**调用方的阻断判定 **MUST** 前置于任何写盘动作（承 `adr/0022`）。

#### Scenario: 写盘类调用方在阻断下零写盘

- **WHEN** 取数产生非空阻断集，随后执行 `reindex`
- **THEN** 命令非零退出，且 `INDEX.md` 与 `batches.md` 字节均未变

#### Scenario: 每个调用方各自验证

- **WHEN** 为本需求编写测试
- **THEN** 上述每个调用方**各有**一条阻断场景断言（承 `adr/0011`：共用解析核心的返回语义按消费方各自定），**MUST NOT** 仅测一条路径即宣称覆盖
