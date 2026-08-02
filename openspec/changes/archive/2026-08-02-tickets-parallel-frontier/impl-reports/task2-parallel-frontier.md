# Task 2: 执行模式 frontier 从严格串行改为宿主条件化受限并行 — impl-report

## Status: DONE

## What was done

三处改动，均在 `sdflow-implement/SKILL.md`：

1. **frontmatter description**（行 4-9）：「串行派 fresh implementer」→「宿主条件化受限并行派 fresh implementer」
2. **引言段**（行 155-156）：「frontier 串行 + 每 ticket 双轴审」→「frontier 宿主条件化受限并行 + 每 ticket 双轴审」
3. **frontier 段**（行 487-495）：标题 + 正文全段重写
   - 标题：`### frontier 严格串行` → `### frontier 宿主条件化受限并行`
   - 宿主分支判据：`host=claude` 并行 + worktree 隔离，`host=codex`/`unknown` 退化串行
   - Claude 宿主并行 dispatch 时序：`isolation: "worktree"` → 收集全部返回 → 逐票 merge `git merge --no-ff` → 串行双轴审 → checkpoint
   - 并行 dispatch 约束：独立 worktree、`git add` 降为 MAY、双轴审串行、收尾票始终串行
   - review-package 并行批次规则：`merge_parent1..merge_commit` 天然隔离；串行票沿用既有；fix 轮沿用既有
   - 异常处理：BLOCKED 票 worktree 直接丢弃不 merge，完成票正常审
   - merge conflict 处理：`git merge --no-ff` 冲突时 halt envelope 上报人介入

## Verification

- 全部 11 条验收标准逐一覆盖
- `git add` MUST 约束在当前 SKILL.md 中不存在（无需降级），已在新段落中用 MAY 建议性表述
- delta spec R1 的 6 个 Scenario 逐一有对应 prose 覆盖
