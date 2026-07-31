### Task 1: 建立可验证的 project-local schema 契约

**Blocked-by:** none
**R-ID:** SW-SCHEMA

系统拥有一个由内置 schema fork 出来的 project-local schema，四个 artifact 的标识和输出模式保持兼容，同时携带阶段一委派提示；其依赖图使 `specs` 读取 proposal/design、`tasks` 读取 proposal/design/specs，design 产物为无条件产物。

- [ ] schema 由 `schema fork` 产出而非 `schema init` 产出
- [ ] 四个 artifact 的 `id` 与 `generates` 和内置契约逐字一致
- [ ] 四个 artifact 的委派标记成对，文案要求停止并提示人敲 `/sdflow-spec`
- [ ] `specs` 与 `tasks` 的 `requires` 边符合目标依赖图，design instruction 无条件生成
- [ ] CLI schema validate 通过`n