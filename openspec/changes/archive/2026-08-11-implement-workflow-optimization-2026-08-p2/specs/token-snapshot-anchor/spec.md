# token-snapshot-anchor delta — implement-workflow-optimization-2026-08-p2

## ADDED Requirements

### Requirement: done 收尾终态快照

sdflow-done 收尾流程 SHALL 在 archive 动作发生之前（change 目录尚在原位时）采集一次终态 token 快照：`step="done-final"`、anchor 语义与 checkpoint 快照同口径（主 session transcript 自报路径，per-子代理无机械承诺的既有诚实边界不变），追加进 change 目录既有 token 锚文件并随 archive 一同迁入归档。采集失败 SHALL 显式降级且 MUST NOT 阻挡收尾流程（与 checkpoint 侧「采集失败显式降级」同口径）。archive 之后发生的用量（归档、提交、合并动作自身）为已声明的残余盲区，MUST NOT 被表述为已覆盖。已知边界〔spec-review-amendment〕：done 收尾若跨 session 重试（archive 失败后新会话重跑），终态快照行会成为新 session 分组首行、其累计用量被全额计入，token 统计可能重复计入——view-only 精度边界，契约文档 SHALL 如实声明，不改脚本。

#### Scenario: archive 前采集终态快照
- **WHEN** sdflow-done 进行到 archive 动作之前
- **THEN** change 目录 token 锚文件新增一行 `step="done-final"` 快照，随后 archive 将其与 change 目录一同迁走；retro join 可读到该行

#### Scenario: 采集失败不挡收尾
- **WHEN** 终态快照采集失败（transcript 不可读等）
- **THEN** 收尾流程照常继续，失败以显式降级记录呈现，MUST NOT 因快照失败中断 archive/commit/merge

#### Scenario: 残余盲区如实声明
- **WHEN** 复盘消费终态快照数据
- **THEN** archive/commit/merge 自身用量不在快照覆盖内的事实可从契约文档读到，MUST NOT 出现「收尾用量已全量覆盖」的表述
