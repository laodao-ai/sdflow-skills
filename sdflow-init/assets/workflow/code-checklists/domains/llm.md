# 代码审查领域：LLM 集成面（通用）

> `extends: base` —— 代码**消费 LLM/agent 产出**这一面特有的审查维度，语言无关；
> 通用维度见 [`../code-review-base.md`](../code-review-base.md)。
> **code-review-only domain**：本领域清单只在代码审（`/review`）侧登记，设计审（spec-checklists）侧无对应文件。

---

| ID | 规则 | 触发条件 | 检查点 |
|----|------|---------|--------|
| CR-LLM-01 | **输出信任边界** | 代码消费外部/不可信 LLM 或 agent 产出并持久化/执行/外呼 | LLM 生成的结构化值（email / URL / 名称 / JSON 对象等）在持久化或对外发送前须做格式与 shape 校验，不当作已验证输入直接落库/转发；LLM 生成的 URL 在发起外呼前须过 allowlist（防 SSRF——模型可能编出内网地址或恶意域名，即便看起来像正常 URL）；LLM 输出写入知识库/向量库/RAG 索引前须做防注入处理（防存储型 prompt 注入——恶意/误导文本被后续检索复读进另一次 LLM 调用，污染下游决策） |
| CR-LLM-02 | **Prompt 一致性** | 新增/修改 prompt 或工具（tool/function）声明 | prompt 中的列表/序号采用 1-indexed（模型对 0-indexed 表述的一致性弱于人类工程师习惯，易致偏移错位）；prompt 里声称提供的工具/能力与代码实际的 wiring（tool schema 注册、系统 prompt 描述）一致，不得声明了却未真正接线；限额/约束（如「最多 N 条」「不超过 M 字」）只在单一处声明，避免多处重复声明导致后续只改一处、产生漂移 |

*规则集 v1 · extends base · 项目无关*
