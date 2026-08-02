## Tasks

### Task 1: 出票模式加并行安全生成约束

在 `sdflow-implement/SKILL.md` 的「产出：3–6 张 tracer-bullet 垂直切片」段末追加并行安全约束条款：出票时对同层级 ticket 须确认行为边界不重叠、产出不互为输入、有疑问保守声明依赖。标注为指令层约束非机械门。

- [ ] 在 `SKILL.md` 出票模式的垂直切片段末追加并行安全约束段落
- [ ] 约束内容与 delta spec「出 ticket 模式并行安全生成约束」一致

### Task 2: 执行模式 frontier 从严格串行改为受限并行

在 `sdflow-implement/SKILL.md` 的「frontier 严格串行」段改为「frontier 受限并行」：`next_ready` 返回多个时并行派发、返回后逐票串行审。补 `PARALLEL_BASE` 记录 + review-package 文件范围隔离逻辑。补 implementer dispatch prompt 的 `git add` 按文件名约束。

- [ ] 将 `### frontier 严格串行` 改为 `### frontier 受限并行`
- [ ] 描述并行 dispatch 时序（并行 impl → 收集 → 串行审+checkpoint）
- [ ] 补 `PARALLEL_BASE` 记录与 review-package 文件隔离的编排逻辑
- [ ] 在 implementer dispatch prompt 段加 `git add` 按文件名约束
- [ ] 异常处理说明（等全部返回后逐个处理）
