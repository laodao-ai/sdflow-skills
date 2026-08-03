### Task 2: 迁移工具 migrate + 测试

**Blocked-by:** 1
**R-ID:** MIG-01, MIG-02, MIG-03, MIG-04, MIG-05

在 `issues.py` 中实现 `cmd_migrate` 子命令，提供一次性从 v1 格式到 v2 格式的迁移。

**核心流程**：
1. 扫描 `openspec/issues/buglist/*.md` + `openspec/issues/todolist/*.md`
2. 每个文件：解析 legacy 表格行 → 再用 frontmatter overlay items 覆盖同 ID（frontmatter 优先）→ 得到 effective 集合
3. 每个 item：字段映射（resolved_by 从 body 提取、closed_date best-effort、date 从文件名提取）
4. 写 v2 文件：活跃 → open/{ID}.md，已关闭 → closed/{ID}.md
5. PLANNED 批次信息迁移：读 batches.md，把 PLANNED 批次的计划文本追加到成员 issue body
6. 幂等：已存在目标文件跳过（按 ID 判重）
7. 完成后自动调 reindex
8. 输出统计报告（迁移数、跳过数、shadowed ID 数、resolved_by 来源分桶）

**迁移数据约束豁免**：迁移产出的文件不经过 set-status，不受 STOR-06 门禁约束。

**测试**（tasks 5.2 对应，与实现同票 TDD）：
- 双格式共存去重（frontmatter 优先于 legacy 表格行）单元测试
- 迁移主流程集成测试（fixture 仓：含 resolved_by body 提取、closed_date best-effort）
- 幂等跳过集成测试
- PLANNED 批次信息迁移集成测试

- [ ] 解析纯 legacy 表格格式，从表格行+detail section 提取全部字段
- [ ] 解析纯 frontmatter overlay 格式，从 frontmatter+marker block 提取
- [ ] 同文件双格式共存时 frontmatter 优先于 legacy 表格行（ID 冲突去重）
- [ ] 字段映射正确：resolved_by 从 body 提取、closed_date best-effort、date 从文件名
- [ ] 活跃 issue 到 open/，已关闭到 closed/
- [ ] PLANNED 批次的计划文本迁移进成员 issue body
- [ ] 幂等：已存在的目标文件跳过，统计报告含 skipped 数
- [ ] 迁移后自动 reindex，INDEX.md/CLOSED.md 完整
- [ ] 统计报告含 shadowed ID 数和 resolved_by 来源分桶

