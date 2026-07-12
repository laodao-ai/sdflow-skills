# roadmap-planning Delta Spec

## ADDED Requirements

### Requirement: 新项目起步的架构先行指路〔spec-review-amendment〕

`sdflow-roadmap/SKILL.md` 的 description SHALL 含指路句「新项目起步尚无架构设计（SAD）时，先 `/sdflow-architecture`」，并 SHALL 注明前置条件（消费仓需已 `sdflow-init`）——与 sdflow-architecture 侧的反向指路（时间轴规划 → sdflow-roadmap）构成双侧分工，消解「新项目起步」入口的现役触发冲突（对应 architecture-design capability 的 REQ「触发分工与互相指路」；本 delta 使 roadmap-planning 侧文本有 spec of record，archive 对码核验可锚）。

#### Scenario: description 含指路句与前置条件
- **WHEN** 检查 `sdflow-roadmap/SKILL.md` 的 frontmatter description 文本
- **THEN** 含「先 `/sdflow-architecture`」指路句及「需已 sdflow-init」前置条件提示
