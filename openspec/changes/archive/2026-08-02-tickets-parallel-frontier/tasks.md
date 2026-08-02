## Tasks

### Task 1: 出票模式加并行安全生成约束

在 `sdflow-implement/SKILL.md` 的「产出：3–6 张 tracer-bullet 垂直切片」段末追加并行安全约束条款：出票时对同层级 ticket 须确认行为边界不重叠、产出不互为输入、有疑问保守声明依赖。收尾节点唯一约束。标注为指令层约束。

- [x] 在 `SKILL.md` 出票模式的垂直切片段末追加并行安全约束段落
- [x] 约束内容与 delta spec「出 ticket 模式并行安全生成约束」一致
- [x] [spec-review-amendment] 补收尾节点唯一约束（多张全阻塞票须声明互相 Blocked-by）

### Task 2: 执行模式 frontier 从严格串行改为宿主条件化受限并行

在 `sdflow-implement/SKILL.md` 的「frontier 严格串行」段改为「frontier 宿主条件化受限并行」：`host=claude` 时 `next_ready` 返回多个用 `isolation: "worktree"` 并行派发，`host=codex`/`unknown` 退化为串行。补 merge 回主分支 + review-package 天然隔离逻辑。

- [x] 将 `### frontier 严格串行` 改为 `### frontier 宿主条件化受限并行`
- [x] 描述宿主分支判据（`$SDFLOW_HOST` 第零步已 resolve）
- [x] Claude 宿主：并行 dispatch 时序（`isolation: "worktree"` → 收集 → 逐票 merge → 串行审+checkpoint）
- [x] Codex/unknown 宿主：退化为串行（按号序逐个派发，行为不变）
- [x] review-package：并行批次用 `merge_parent1..merge_commit` 天然隔离，串行票沿用既有规则
- [x] fix 轮 diff 显式声明沿用既有规则（串行审阶段单线程，无并发）
- [x] 异常处理说明（BLOCKED 票 worktree 直接丢弃不 merge，完成票正常审）
- [x] merge conflict 处理（`git merge --no-ff` 冲突时上报人介入）
- [x] [spec-review-amendment] 同步更新 frontmatter `description`（`SKILL.md:6`）中"串行"表述
- [x] [spec-review-amendment] 同步更新正文引言段（`SKILL.md:155-158`）中"串行"表述
- [x] [spec-review-amendment] ~~dispatch prompt `git add` 按文件名 MUST~~ 降为建议性最佳实践
