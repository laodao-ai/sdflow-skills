### Task 3: Q2 amendment 双向 coherence

**Blocked-by:** none
**R-ID:** amendment-bidirectional-coherence

改 `sdflow-spec-review/SKILL.md:298` 从「据此更新 design/specs」扩展到四件套任意产物（proposal/design/specs/tasks），引用 `/opsx:update` 的双向原则但不直接调用（`reviewed_sha` 时序冲突）。

验收标准：
- [ ] `sdflow-spec-review/SKILL.md` 的 amendment 写回段明确覆盖 proposal/design/specs/tasks 四件套
- [ ] 引用了双向原则（build order is a useful reading order, not a constraint on which artifacts may be revised）
- [ ] 提到最常见场景（评审发现 design 问题但根因在 proposal 的 Non-Goals 划错了）
- [ ] 未直接调用 `/opsx:update`

