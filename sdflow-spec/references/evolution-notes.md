# 演进依据与未来门契约

> 仅在审计历史取舍，或设计未来 T132 grill 收敛 gate 时读取。本文不参与默认阶段一执行。

## 1. 薄编排与未启用外派

外派链路曾通过可用性门，但同一真实 change 的 A/B 比较中，subagent 路成本高于 thin 路，
且未观察到质量收益；因此依验收失败分支回退到主 session 亲查、亲写。该结论基于 N=1，
只支持“不启用”，不支持声称外派永远无效。

## 2. 入口纪律的来源

- 工作树前置检查设为硬 halt，是因为脏改动会被 `git checkout -b` 带到新分支，再被
  `checkpoint-commit.sh` 的 `git add -A` 裹入 checkpoint。
- 派发参数采用 `subagent_type`，不用 Workflow `agentType`；后者属于已否决的调度路径。
- 出口 `/clear` 的合法理由只有 cache 按模型隔离和产审错档纪律；主审独立性由阶段二 fresh
  reviewer 提供，MUST NOT 用“主审裁决需冷视角”重复论证。

## 3. T132 的 A/B 未来输入契约

T132 保持 OPEN。本 reference 不实现 gate，不改 `sdflow-spec-review` 起手行为，只定义未来 gate
必须识别的两个入口契约，且规则身份不得使用会漂移的行号：

- 分支 A：A 需要身份、hash、必填节有效的 `decision-memo.md`，并同时存在
  `checkpoint(sdflow-spec-grill)` 提交锚。
- 分支 B：B 需要既有 `checkpoint(grill)` 或未来 gate 明确认可的 `sdflow:grill-done` 锚。

未来实现必须按入口分治；MUST NOT 用分支 B 的 grill 信号拒绝正常走 `/sdflow-spec` 的分支 A，
也 MUST NOT 仅凭非空 memo 证明拷问真实发生。

## 4. Codex 诚实边界

当前只观察到用户显式触发 `sdflow-spec` 被接受；本 session 没有模型可调用的 Skill 执行面。
接口缺席不是“模型调用被机械拒绝”的正向实证。后续宿主能力变化时应重新核验并更新本记录。
