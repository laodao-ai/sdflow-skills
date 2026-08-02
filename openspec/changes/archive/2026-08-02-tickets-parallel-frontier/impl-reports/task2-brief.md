### Task 2: 执行模式 frontier 从严格串行改为宿主条件化受限并行

**Blocked-by:** none
**R-ID:** R1

将 `sdflow-implement/SKILL.md` 的「### frontier 严格串行」段改为「### frontier 宿主条件化受限并行」，按 delta spec 的「执行模式宿主条件化受限并行工作 frontier」Requirement 实现。同时同步更新 frontmatter `description`（第 4-9 行）和引言段（第 155-158 行）中的"串行"表述。具体改动：

1. 标题改名：`### frontier 严格串行` → `### frontier 宿主条件化受限并行`
2. 宿主分支判据：`host=claude` 并行 + worktree 隔离，`host=codex`/`unknown` 退化串行
3. Claude 宿主并行 dispatch 时序：`isolation: "worktree"` → 收集全部返回 → 逐票 merge `git merge --no-ff` → 串行双轴审 → checkpoint
4. review-package 并行批次规则：merge commit 天然隔离，`merge_parent1..merge_commit`
5. fix 轮 diff 显式声明沿用既有规则（串行审阶段单线程，无并发）
6. 异常处理：BLOCKED 票 worktree 直接丢弃不 merge，完成票正常审
7. merge conflict 处理：`git merge --no-ff` 冲突时上报人介入
8. 同步更新 frontmatter description 中"串行"→"宿主条件化受限并行"
9. 同步更新引言段（第 155-158 行）中"串行"表述
10. dispatch prompt `git add` 按文件名 MUST 降为建议性最佳实践（如存在该约束）

- [ ] 将 `### frontier 严格串行` 改为 `### frontier 宿主条件化受限并行`
- [ ] 描述宿主分支判据（`$SDFLOW_HOST` 第零步已 resolve）
- [ ] Claude 宿主：并行 dispatch 时序（`isolation: "worktree"` → 收集 → 逐票 merge → 串行审+checkpoint）
- [ ] Codex/unknown 宿主：退化为串行（按号序逐个派发，行为不变）
- [ ] review-package：并行批次用 `merge_parent1..merge_commit` 天然隔离，串行票沿用既有规则
- [ ] fix 轮 diff 显式声明沿用既有规则（串行审阶段单线程，无并发）
- [ ] 异常处理说明（BLOCKED 票 worktree 直接丢弃不 merge，完成票正常审）
- [ ] merge conflict 处理（`git merge --no-ff` 冲突时上报人介入）
- [ ] 同步更新 frontmatter `description`（第 4-9 行）中"串行"表述
- [ ] 同步更新引言段（第 155-158 行）中"串行"表述
- [ ] dispatch prompt `git add` 按文件名约束降为建议性最佳实践

