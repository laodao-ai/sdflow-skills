### Task 3: 使阶段一相位 C 消费真实 CLI 载荷

**Blocked-by:** 1
**R-ID:** SA-05, SA-17

阶段一相位 C 能消费 project-local schema 返回的 instruction/requires 载荷：先剥离只供官方入口阅读的委派段，再按真实依赖图阅读和生成；能处理 glob 输出目标、既有输出路径、skipped 产物和对象列表形式的 dependencies，同时保留 schema 不足时的 fallback。

- [ ] 委派标记成对时在应用载荷前剥离；无标记 no-op；不成对时 fail-closed 并报告 problem、cause、fix
- [ ] glob 输出目标被依据 instruction 推导为具体 capability spec 路径，既有文件改写使用 existingOutputPaths
- [ ] 路径净化作用于推导出的具体路径，不会把 glob 字面量当作合法目标
- [ ] `skipped` 产物不创建文件，且依赖它的阅读清单条目被移除
- [ ] 阅读清单以 schema requires 为准，并在依赖图不足时使用写死超集 fallback
- [ ] dependencies 断言接受且验证包含 `id`、`done`、`path`、`description` 的对象列表
- [ ] 终审 design↔specs 双向核被表述为 schema 已切换时的兜底，而非唯一防线`n