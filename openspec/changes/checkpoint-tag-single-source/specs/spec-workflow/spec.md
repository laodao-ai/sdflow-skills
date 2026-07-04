## ADDED Requirements

### Requirement: checkpoint 标签格式契约单一真相源

checkpoint 任务标签格式（`checkpoint(<change>:task<N>-<slug>)`，含裸格式向后兼容）活在三个耦合站点——`ship_gate.py` 的 `TAG_RE`（解析权威）、`workflow.md`（bundle 文档权威）、`sdflow-ship/SKILL.md`（派发指令）。这三站 MUST 由一条**机械绑定测试**钉死一致，MUST NOT 靠人工同步各处散文。格式**字面** MUST 有单一文档真相源（`workflow.md`），派发指令 MUST 引用而非独立复述该字面。此为纯防漂移加固，`TAG_RE` 的解析语义 MUST 逐字不变。

#### Scenario: 文档格式串与解析器双向绑定

- **WHEN** 存在一条契约测试，从 `workflow.md`（及 `SKILL.md` 若含字面）出现的格式构造真实 checkpoint subject（如 `checkpoint(demo:task1-slug): msg`）
- **THEN** 该测试 MUST 断言 `ship_gate.py` 的 `TAG_RE.match` 成功且捕获组 = `("demo", "1")`；MUST 直接读文档文件 + import `TAG_RE`（MUST NOT 硬编码期望串使测试与被测源解耦），使文档改格式字面或正则改捕获组时任一单侧漂移即令断言失衡报红

#### Scenario: 裸格式向后兼容在文档与解析器两端一致

- **WHEN** 契约测试校验裸格式 `checkpoint(task1-slug)`
- **THEN** 测试 MUST 断言 `TAG_RE` 仍 match（命名空间捕获组为 `None`）且文档仍声明裸格式向后兼容——防「顺手」把裸兼容从文档删除却漏改仍认裸格式的 `TAG_RE`（doc↔parser 漂移）

#### Scenario: 派发指令引用而非复述格式字面

- **WHEN** `sdflow-ship/SKILL.md` 的 RUN_PLAN 派发段需要指示 implementer 用何种 checkpoint 标签格式
- **THEN** 该段 MUST 以引用 `workflow.md` 权威定义的方式表达格式（MUST NOT 自带完整格式字面复述），但 MUST 保留派发动作与语义要点（「由 implementer 执行」「gate 只认当前 change」等派发时必须在场的操作指令 MUST NOT 一并抽走，防派发指令不自足）
