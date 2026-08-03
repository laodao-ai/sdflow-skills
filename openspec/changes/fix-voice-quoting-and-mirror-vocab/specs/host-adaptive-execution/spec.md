## Purpose

扩展 `fanout-capability` 锚的 `mirrors=` 合法 token 集，加入 `history`——使 code-review
的历史镜可以用真名记录，消除借用 `grounding` token 的语义不精确问题，并修正
`dead-fanout-multi-mirror` 一致性 lint 对 `history` token 的漏算。

## MODIFIED Requirements

### Requirement: mirrors= 合法 token 集扩展为四值

`fanout-capability` 锚的 `mirrors=` 取值文法 SHALL 为 `—`（未 fan-out）XOR 非空的
`{domain,adversarial,grounding,history}` 逗号分隔子集。`anchor_lint` 的 `_FANOUT_MIRRORS`
SHALL 与此四值集一致。

#### Scenario: history token 被接受
- **WHEN** `fanout-capability` 锚的 `mirrors=` 包含 `history` token
- **THEN** `anchor_lint._parse_mirrors()` SHALL 返回合法解析结果，MUST NOT 报 `unknown-token`

#### Scenario: dead-fanout-multi-mirror 覆盖 history token
- **WHEN** `sdflow:fanout-capability` 锚记 `subagents="unavailable"`，而同锚 `mirrors=` 清单中 `∈ {domain,adversarial,grounding,history}`（按值去重）的计数 > 1
- **THEN** `anchor_lint` SHALL 报错阻塞（违规类型 `dead-fanout-multi-mirror`）

#### Scenario: code-review 历史镜用真名
- **WHEN** code-review 的第三镜（历史镜）实际 fan-out 完成
- **THEN** SKILL SHALL 在 `mirrors=` 中记 `history`（非 `grounding`）
