## ADDED Requirements

### Requirement: roadmap task-log『Review 处置』小节存在性 + 非空断言

校验器 SHALL 断言 roadmap task-log 的 `## Review 处置` 小节存在且非空（非仅脚手架注释 / 空白），输出 reason_code `section-missing|section-empty|present`。`present` 退出码 0。小节缺失 MUST NOT 被当作「无未处置条目」真空通过。

#### Scenario: 小节缺失
- **WHEN** task-log 无 `## Review 处置` 标题
- **THEN** 输出 `section-missing`，退出码非 0（不真空通过）

#### Scenario: 小节仅脚手架 / 空
- **WHEN** `## Review 处置` 存在但正文仅模版占位注释或空白
- **THEN** 输出 `section-empty`，退出码非 0

#### Scenario: 小节有内容
- **WHEN** `## Review 处置` 存在且含非脚手架实体内容
- **THEN** 输出 `present`，退出码 0

### Requirement: 逐条已处置为显式模型信任边界、不被子串陷阱假阳

校验器 MUST NOT 断言「逐条已处置」（格式三实例不统一、无字面 token、机械不可达），此判定显式保留给模型。检测 MUST NOT 用裸子串匹配 `未处置`——须 fence / 结构感知，避免收尾声明句「本小节无『未处置』状态条目」触发假阳。

#### Scenario: 收尾声明句不假阳
- **WHEN** 小节含收尾句「本小节**无**『未处置』状态条目」（该句含子串「未处置」）
- **THEN** 校验器判 `present`，MUST NOT 因子串「未处置」误报为存在未处置条目

#### Scenario: 不冒充逐条完整性
- **WHEN** 小节存在且非空但某条目实际缺状态标记
- **THEN** 校验器仍只输出 `present`（存在 + 非空达成），逐条完整性交模型判断——脚本不假装覆盖

### Requirement: 坏输入 fail-closed

校验器 SHALL 对 task-log 文件缺失 / 不可读以非零退出 + stderr 原因结束。

#### Scenario: 文件不可读
- **WHEN** task-log 路径不存在或解码失败
- **THEN** 退出码非 0，stderr 打印 `[review_disposition_check] FAIL: <原因>`
