---
impl-pipeline: tickets
---

## Global Constraints

- 改动面仅 `sdflow-implement/SKILL.md` 一个文件的 prose 条款，不涉及脚本代码或测试变更
- `impl_route.py`（`next_ready` 已支持多候选返回）零改动
- `ship_gate.py`（gate 完成窗口零改动，`done_task_ids` 穿透 merge commit）零改动
- `sdflow-ship/SKILL.md`（链序零改动）零改动
- MUST NOT 预写实现代码或具体文件路径——ticket 只描述"交付什么行为"
- 本次修改的是 SKILL.md 的指令层约束（prose），不是编程语言代码——implementer 的工作是编辑 Markdown 段落
- 并行安全兜底从"不存在的 git add fail-loud"升级为 worktree 隔离下 `git merge` 原生冲突检测（真正的 fail-loud）
- Codex 宿主退化为串行（行为与改动前完全一致），MUST NOT 在无能力的宿主上强行造轮子
- gate 影响零改动：`done_task_ids`（`ship_gate.py:1478-1496`）使用 `git log sha..HEAD --no-merges --format=%s`，无 `--first-parent` → 遍历穿透 merge commit 看到 worktree 分支上的 checkpoint 标签

### Task 1: 出票模式追加并行安全生成约束

**Blocked-by:** none
**R-ID:** R2

在 `sdflow-implement/SKILL.md` 的「产出：3–6 张 tracer-bullet 垂直切片」段末（`[e2e]` 表达方式段之后、「宽重构例外」段之前）追加一段并行安全约束条款。内容须覆盖：

1. 对 `Blocked-by` 声明使得 `next_ready` 可能同时返回的一组 ticket，出票方 MUST 确认——行为边界不重叠（不改同一模块的同一接口）、一个的产出不是另一个的输入、有疑问时保守声明依赖（宁可串行不可误并行）
2. 收尾节点唯一约束：若产出多张 `Blocked-by` 覆盖全部其余票号的 ticket，SHALL 让后者追加声明对前者的 `Blocked-by`，确保收尾节点唯一
3. 标注为指令层语义约束（出票方的模型判断），并说明兜底为 worktree 隔离下 `git merge` 原生冲突检测

- [x] 在 SKILL.md 出票模式的垂直切片段末（`[e2e]` 段后、宽重构例外前）追加并行安全约束段落
- [x] 约束内容与 delta spec「出 ticket 模式并行安全生成约束」Requirement 一致
- [x] 含收尾节点唯一约束（多张全阻塞票须声明互相 Blocked-by）

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

- [x] 将 `### frontier 严格串行` 改为 `### frontier 宿主条件化受限并行`
- [x] 描述宿主分支判据（`$SDFLOW_HOST` 第零步已 resolve）
- [x] Claude 宿主：并行 dispatch 时序（`isolation: "worktree"` → 收集 → 逐票 merge → 串行审+checkpoint）
- [x] Codex/unknown 宿主：退化为串行（按号序逐个派发，行为不变）
- [x] review-package：并行批次用 `merge_parent1..merge_commit` 天然隔离，串行票沿用既有规则
- [x] fix 轮 diff 显式声明沿用既有规则（串行审阶段单线程，无并发）
- [x] 异常处理说明（BLOCKED 票 worktree 直接丢弃不 merge，完成票正常审）
- [x] merge conflict 处理（`git merge --no-ff` 冲突时上报人介入）
- [x] 同步更新 frontmatter `description`（第 4-9 行）中"串行"表述
- [x] 同步更新引言段（第 155-158 行）中"串行"表述
- [x] dispatch prompt `git add` 按文件名约束降为建议性最佳实践

### Task 3: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task3-verify.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [ ] 单元测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
