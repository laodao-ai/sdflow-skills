## 概述

issues 台账读写路径加固（T231 + B12）。改动面 = `sdflow_issues_core/__init__.py` + `issues.py` + 测试。

## Tasks

### Task 1: 读取路径词表校验

- [ ] 1.1 `_scan_pool` 自检段追加 status 词表校验（`item["status"] not in spec.status_values` → `problems.append`）
- [ ] 1.2 `_scan_pool` 自检段追加 specific_field 词表校验（`item[sf] not in spec.specific_values` → `problems.append`）
- [ ] 1.3 测试：构造脏 status/type/priority 的 legacy 行 → 断言 problems 非空 + 项仍在 items 中 + scan 正常返回

### Task 2: reindex 总项数守卫

- [ ] 2.1 `issues.py` 新增 `_count_index_items(path)` 辅助函数：读旧 INDEX.md 计 `| T/B` 行数
- [ ] 2.2 `_reindex_core` 写盘前调用，新 < 旧 → `raise ReindexStageError`
- [ ] 2.3 测试：构造旧 INDEX 有 N 项、新扫描 < N → 断言 raise + INDEX 未被覆盖；首次建（旧不存在）→ 正常写入

### Task 3: triage 状态解耦

- [ ] 3.1 `_bug_triage` 删 `open_untriaged` 两行 + 条件赋值，改为 `new_status = old_status`
- [ ] 3.2 `_todo_triage` 同上
- [ ] 3.3 测试：对 OPEN 项跑 batch add → 断言 status 仍为 OPEN

### Task 4: 验证

- [ ] 4.1 全量 `pytest sdflow-issues/tests/` 绿
- [ ] 4.2 在本仓跑 `python3 sdflow-issues/scripts/issues.py reindex` 确认现有数据不假阳
