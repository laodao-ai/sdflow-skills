# Tasks: complete-openspec-170-followup

## 1. P2: config 层注入

- [x] **Task 1.1**: `openspec/config.yaml` 新增 `operations.archive.guidance` 段（两条硬约束）
  - Requirement: archive-guidance-injection
  - 验证：`openspec instructions archive --change X --json` 返回 `operationGuidance` 数组

- [x] **Task 1.2**: `openspec/config.yaml` 的 `rules.specs` 加 `## Purpose` 规则
  - Requirement: purpose-rule-in-specs
  - 验证：读 config 确认规则存在

- [x] **Task 1.3**: `sdflow-init/assets/workflow/config.template.yaml` 同步 `operations` 段和 `## Purpose` 规则
  - Requirement: archive-guidance-injection, purpose-rule-in-specs
  - 验证：diff template 与 config 确认对齐

## 2. P3: sdflow-done archive 现代化

- [x] **Task 2.1**: archive 子代理 prompt 改用 `--json` 读 `warnings[]`
  - Requirement: archive-json-warnings
  - 验证：读 `sdflow-done/SKILL.md` 确认 prompt 使用 `--json` 且读 JSON warnings

- [x] **Task 2.2**: fallback 阶梯确认——确认现有文本不提及 REMOVED abort（已核实无需改动）[spec-review-amendment]
  - Requirement: fallback-ladder-slim
  - 验证：grep "REMOVED" sdflow-done/SKILL.md → 零命中即通过（恒真确认，不做文本修改）

- [x] **Task 2.3**: archive 侧认 skipped 态
  - Requirement: archive-recognizes-skipped
  - 验证：读 archive 子代理 prompt 确认对 skip_specs 的 specs status=skipped 有处理路径

## 3. Q2: amendment 双向 coherence

- [x] **Task 3.1**: `sdflow-spec-review/SKILL.md:298` 扩展 amendment 写回范围到四件套
  - Requirement: amendment-bidirectional-coherence
  - 验证：读 SKILL.md 确认 amendment 明确覆盖 proposal/design/specs/tasks，引用双向原则

## 4. 收尾

- [x] **Task 4.1**: roadmap 回写——更新 `openspec/roadmaps/openspec-1.7.0-followup/roadmap.md` 的 P2/P3/Q2 状态
  - 无对应 Requirement（元数据维护）
