## Why

sdflow 工作流当前有双轨入口（分支 A: sdflow-spec / 分支 B: explore→ff→grill）、条件步（wayfinder chart、embedded-test-sop）、手动触发限制（sdflow-spec `disable-model-invocation: true`）等历史复杂度。分支 B 的三种例外情形已被 sdflow-spec 覆盖（Codex 宿主支持、三相位内建分步），wayfinder 和 embedded-test-sop 使用频率极低。这些复杂度增加了 workflow 文档 ≈150 行、CLAUDE.md ≈80 行的认知负担，却不带来对等的价值。

## What Changes

- **合并双轨为唯一线性路径**：`explore(条件) → sdflow-spec → /clear → spec-review → HARD-GATE → /clear → sdflow-ship[implement→code-review→done→merge]`
- **删除旧三步流程引用**：从 workflow bundle 中移除 `opsx:ff`、`grill-with-docs` 作为独立步骤的引导（skill 本体不删，只不再在流程中推荐）
- **删除 wayfinder chart**：从流程文档和 ff-generation-constraints.md 中移除所有 wayfinder 引用
- **彻底删除 embedded-test-sop**：删除 skill 目录 + ship_gate.py 的 RUN_SOP verdict + 相关测试 + workflow 引用
- **解除 sdflow-spec 手动触发限制**：删除 `disable-model-invocation: true`，模型可在用户示意时自动触发（explore 收敛后「开搞」即自动接 sdflow-spec）
- **impl-pipeline 缺省翻为 tickets**：无显式键的项目默认走 sdflow-implement（tickets 管线），显式 `impl-pipeline: superpowers` 仍走旧管线
- **workflow.md G1 分析移入附录**：正文简化为一条规则，详细推导保留在附录

## Success Metrics

- workflow.md 步骤表从 10 行降到 6 行
- generation-process.md 从 §四 两个分支合并为单一入口描述
- CLAUDE.md 的「阶段一入口」「sunset 条件」「grill-with-docs」段落全部删除（≈80 行）
- ship_gate.py 删除 RUN_SOP 分支（17 处代码 + 21 处测试），测试全绿
- 全流程只有一个人类停点（HARD-GATE），不再需要人手动敲 `/sdflow-spec` 或 `/grill-with-docs`

## Non-Goals

- 不改 sdflow-spec 内部的三相位协议（A/B/C）——只改触发方式，不改运行过程
- 不删除 opsx:ff / grill-with-docs / opsx:explore 的 skill 本体——两个是 openspec CLI 生成物，一个在仓外
- 不改 sdflow-spec-review / sdflow-code-review / sdflow-done 的行为
- 不重构 ship_gate.py 的整体架构（只删 RUN_SOP 分支）

## Compliance

N/A

## Capabilities

### New Capabilities

（无新能力）

### Modified Capabilities

- `spec-workflow`: 删除双轨入口、wayfinder 引用、embedded-test-sop 自动触发；解除 sdflow-spec 手动限制；翻转 impl-pipeline 缺省

## Impact

- **workflow bundle（权威源，推给所有下游项目）**：workflow.md、generation-process.md、ff-generation-constraints.md、WORKFLOW-GUIDE.md 重写/删段；prompts/ 下 3 个文件删除
- **snippets（注入下游 CLAUDE.md）**：claude-section.md 删分支 B/wayfinder/手动限制段落
- **sdflow-ship**：SKILL.md 删 RUN_SOP 描述；ship_gate.py 删 RUN_SOP verdict + tg02_hit 检测（17 处代码 + 21 处测试）
- **sdflow-spec**：SKILL.md 删 `disable-model-invocation: true`
- **embedded-test-sop**：整个 skill 目录删除
- **本仓 CLAUDE.md**：重写入口规则、删 sunset 条件、删 grill-with-docs 段落
- **本仓 openspec/config.yaml**：更新 impl-pipeline 注释
- **下游 15 个无显式 impl-pipeline 键的项目**：sdflow-init update 后行为从 superpowers 翻到 tickets
