# Task 3: Q2 amendment 双向 coherence

## 改动摘要

- `sdflow-spec-review/SKILL.md:298`：将 amendment 写回段的表述从「据此更新 design/specs」扩展为「据此更新四件套中
  需要修订的产物（proposal / design / specs / tasks）」，并新增一句原则引用与最常见场景说明：
  - 原则：an edit to a later artifact may require revising an earlier one, not only the other way around
    （引自 `/opsx:update` 1.6.0）。
  - 最常见场景：评审发现 design 问题但根因在 proposal 的 Non-Goals 划错了。
  - 未改动其余上下文（该条目上方的度量锚段、反馈回路免责声明段，及下方「收敛口（1.6）」段落原样保留）。

## 验收核对

- amendment 写回段明确覆盖 proposal/design/specs/tasks 四件套：✅
- 引用了双向原则：✅
- 提到最常见场景（评审发现 design 问题但根因在 proposal）：✅
- 未直接调用 `/opsx:update`：✅（仅在正文中以引用形式提及 `/opsx:update` 1.6.0 的原则表述，未调用该 skill/命令，
  也未触发其 `reviewed_sha` 时序契约）
