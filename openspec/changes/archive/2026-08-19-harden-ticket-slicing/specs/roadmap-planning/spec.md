## ADDED Requirements

### Requirement: 阶段拆分锚定 change 拆分标准〔harden-ticket-slicing〕

roadmap 的每个阶段 SHALL 对应**一个完整内聚的阶段结果**（未来恰好一次 change 可交付），拆分判据 SHALL 引用 change 拆分标准单一源（`openspec/workflow/reference/change-decomposition-standard.md`，经 resolver 解析，指针引用 MUST NOT 复制标准文本）：MUST NOT 按来源批次 / 顺手凑票拆分阶段，MUST NOT 把一个内聚交付物拆散跨多阶段，MUST NOT 把不相干功能混入同一阶段。

#### Scenario: 生成 roadmap 时按完整阶段结果切分

- **WHEN** 生成阶段把一批目标切分为多个 roadmap 阶段
- **THEN** 每个阶段的交付物是一个可独立验收的完整内聚结果（对应未来一次 change），切分理由可对照拆分标准判定

#### Scenario: 发现某阶段混拼不相干能力时调整

- **WHEN** 拷问或 review 发现某阶段同时含两个互不耦合的能力
- **THEN** 按拆分标准拆为两个阶段（各自完整），MUST NOT 以「凑一个阶段省事」保留混拼
