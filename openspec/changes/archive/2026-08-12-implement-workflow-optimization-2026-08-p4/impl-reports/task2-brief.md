### Task 2: effort agent 定义铺设与 install_agents 验证

**Blocked-by:** 1
**R-ID:** HAE-2

铺设 5 个全局 agent 定义 `sdflow-effort-{low,medium,high,xhigh,max}`（frontmatter 含排他 description「仅由 sdflow 编排 SKILL 派发选用」、`model: inherit`、`effort: <值>`），放入既有 `sdflow-spec/agents/` 目录（设计门拍板 Q2=C：install_agents 守卫/manifest 零改动，新增 `.md` 自动纳入）。同步 CLAUDE.md/design 对该目录的描述 + 目录内注记。假 HOME 测试加 effort 定义专项断言（铺设幂等 / 不覆盖他人 / 孤儿清理 / Windows skip）。

- [ ] 5 个 `sdflow-effort-*.md` 定义文件就位于 `sdflow-spec/agents/`，frontmatter 正确
- [ ] install_agents 铺设到 `~/.claude/agents/` 且既有所有权守卫/孤儿清理行为不变
- [ ] 假 HOME 测试覆盖：effort 定义铺设幂等、非本仓同名不覆盖、源删除后孤儿清理
- [ ] CLAUDE.md 对 `sdflow-spec/agents/` 目录描述同步更新

