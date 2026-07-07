# Design — plan-mechanical-layer-hardening

本变更是**规划型 change**，设计的权威源在 roadmap 文档包，不在本变更内部（rule 5：变更内部 design 简短指向 roadmap 目录，避免同内容两处）。

- **整体设计（权威）**：`openspec/roadmaps/mechanical-layer-hardening/design.md`（两腿架构 × adr/0006 根契约、7 决策、候选全表、风险回滚、Q&A 已决议）。
- **需求**：`openspec/roadmaps/mechanical-layer-hardening/requirements.md`
- **阶段计划**：`openspec/roadmaps/mechanical-layer-hardening/roadmap.md`

## 本变更自身的设计取舍

- **无 capability spec**：规划 change 不定义规范增量；各实施阶段（`implement-mechanical-layer-hardening-pN-*`）的规范增量届时落 `spec-workflow` 或各 recorder skill 自包含约定（映射见 roadmap.md 附录 C）。
- **无代码改动**：只产出文档包（长期真相源），实施留给未来独立变更。
