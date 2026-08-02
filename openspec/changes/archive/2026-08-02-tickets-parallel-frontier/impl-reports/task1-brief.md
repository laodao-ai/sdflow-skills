### Task 1: 出票模式追加并行安全生成约束

**Blocked-by:** none
**R-ID:** R2

在 `sdflow-implement/SKILL.md` 的「产出：3–6 张 tracer-bullet 垂直切片」段末（`[e2e]` 表达方式段之后、「宽重构例外」段之前）追加一段并行安全约束条款。内容须覆盖：

1. 对 `Blocked-by` 声明使得 `next_ready` 可能同时返回的一组 ticket，出票方 MUST 确认——行为边界不重叠（不改同一模块的同一接口）、一个的产出不是另一个的输入、有疑问时保守声明依赖（宁可串行不可误并行）
2. 收尾节点唯一约束：若产出多张 `Blocked-by` 覆盖全部其余票号的 ticket，SHALL 让后者追加声明对前者的 `Blocked-by`，确保收尾节点唯一
3. 标注为指令层语义约束（出票方的模型判断），并说明兜底为 worktree 隔离下 `git merge` 原生冲突检测

- [ ] 在 SKILL.md 出票模式的垂直切片段末（`[e2e]` 段后、宽重构例外前）追加并行安全约束段落
- [ ] 约束内容与 delta spec「出 ticket 模式并行安全生成约束」Requirement 一致
- [ ] 含收尾节点唯一约束（多张全阻塞票须声明互相 Blocked-by）

