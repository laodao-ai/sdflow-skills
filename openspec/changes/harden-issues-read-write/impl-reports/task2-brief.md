### Task 2: reindex 总项数只增不减守卫

**Blocked-by:** none
**R-ID:** R2

在 `issues.py` 新增 `_count_index_items(path)` 辅助函数：两段式解析旧 INDEX.md（open = 数 `| [A-Z]\d+ |` 表格行，closed = 解析"共 N 项已闭合"聚合行的 N），返回两者之和。不存在/不可解析 → 返回 0。

`_reindex_core` 写盘前调用该函数，新扫描总项数 < 旧总项数 → `raise ReindexStageError` 拒绝覆盖。

- [ ] 新增 `_count_index_items(index_path)` 函数：两段式解析 open 行数 + closed 聚合数
- [ ] `_reindex_core` 写盘前调用，`new_count < old_count` 且 `old_count > 0` → raise ReindexStageError
- [ ] 测试：旧 INDEX 有 N 项（含 closed 聚合行）、新扫描 < N → 断言 raise + INDEX 未被覆盖
- [ ] 测试：旧 INDEX 只有 closed 项（open=0、closed>0）、新扫描丢了 closed 项 → 断言 raise
- [ ] 测试：首次建（旧不存在）→ 正常写入不触发守卫
- [ ] 测试：旧 INDEX 格式损坏 → 返回 0 跳过校验，不卡死 reindex

