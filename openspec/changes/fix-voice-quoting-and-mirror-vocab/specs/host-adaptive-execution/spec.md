## Purpose

扩展 `fanout-capability` 锚的 `mirrors=` 合法 token 集，加入 `history`——使 code-review
的历史镜可以用真名记录，消除借用 `grounding` token 的语义不精确问题，并修正
`dead-fanout-multi-mirror` 一致性 lint 对 `history` token 的漏算。

## 改动方式 [spec-review-amendment S1/Q1]

本 change 对三份 spec 的 SHALL 条款均走**直接改主 spec**，不经 delta → archive 流程。
理由：改动仅为枚举值放宽（`{domain,adversarial,grounding}` → `{domain,adversarial,grounding,history}`），
不改变既有条款语义；delta 必须携带对应 Requirement 的全部现有 Scenario（本 spec 达 ~7 条），
工作量与价值不对称。

涉及三份主 spec 各自的行号见 tasks.md 2.4。
