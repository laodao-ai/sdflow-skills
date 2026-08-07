## RENAMED Requirements

- FROM: `` ### Requirement: R12 — 7 份 `_yq()` 一致性 golden test ``
- TO: `` ### Requirement: R12 — `_yq()` 一致性 golden test ``

## MODIFIED Requirements

### Requirement: R12 — `_yq()` 一致性 golden test

各消费脚本内联的 `_yq()` 封装 MUST 由 golden test 守核心逻辑一致；封装体量小到共享收益低于跨脚本 import 的耦合成本，故不共享实现，改由测试机械守一致。〔fix-probe-scan-precision〕封装份数 MUST NOT 在 spec 或测试文档里写死计数（`openspec/workflow/tools/anchor_lint.py` 镜像随本 change 删除即为实例——写死的「7 份」当场失真；以 golden test 的 `TARGETS` 实际枚举为准，本仓「别硬编码数字、让脚本自己报」取向）。Purpose 段的脚本枚举同批订正（Purpose 非 Requirement，随 change 直接改主 spec）。

#### Scenario: 封装漂移
- **WHEN** 任一脚本的 `_yq()` 被修改而其他脚本未同步
- **THEN** golden test 红

#### Scenario: 全部一致
- **WHEN** 全部在册 `_yq()` 核心逻辑一致
- **THEN** golden test 绿
