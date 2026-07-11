## ADDED Requirements

### Requirement: step1-broad-review 锚数量一致性、多锚 mode 冲突 fail-closed〔T139〕

校验器 SHALL 收集 fence 外**全部** `step1-broad-review` 锚的 `mode`，MUST NOT 用 `.search` 只取首个：0 锚 → 既有坏输入 fail-closed；恰 1 锚 → 取其 mode；≥2 锚且 mode 全一致 → 取该 mode（容重复锚）；≥2 锚且 mode 冲突（如 native 与 simulated 并存）→ 非零退出 + stderr，MUST NOT 静默取首个而丢弃后者。

> 〔为何〕mlh-p4 后 `parse_mode` 用 `_S1_RE.search` 取首个锚，双锚（native 在前 / simulated 在后）静默取 native 忽略 simulated——属构造性/低概率（单锚是常态），但违「数量与 mode 一致否则 fail-closed」稳健取向；simulated 被静默丢会假装原生审计层在场。

#### Scenario: 单锚照常
- **WHEN** 报告恰含 1 个 `step1-broad-review` 锚 `mode="native"`
- **THEN** 取 `native`，行为与 mlh-p4 一致

#### Scenario: 双锚 mode 冲突非零退出
- **WHEN** 报告含 2 个 `step1-broad-review` 锚，`mode="native"` 在前、`mode="simulated"` 在后
- **THEN** 非零退出 + stderr `[outside_voice_guard] FAIL: <step1 锚 mode 冲突>`，MUST NOT 静默取 native

#### Scenario: 多锚 mode 一致容忍
- **WHEN** 报告含 ≥2 个 `step1-broad-review` 锚且 mode 全相同
- **THEN** 取该一致 mode，退出码 0（容重复）
