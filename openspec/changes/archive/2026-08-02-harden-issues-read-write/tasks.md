## 概述

issues 台账读写路径加固（T231 + B12）。改动面 = `sdflow_issues_core/__init__.py` + `issues.py` + `SKILL.md` + 测试。[spec-review-amendment]

## Tasks

### Task 1: 读取路径词表校验（两层同步）[spec-review-amendment]

- [x] 1.1 `_build_effective_snapshot`（`__init__.py:826-901`）自检段追加 status 词表校验（`item["status"] not in spec.status_values` → `problems.append`）
- [x] 1.2 `_build_effective_snapshot` 自检段追加 specific_field 词表校验（`item[sf] not in spec.specific_values` → `problems.append`）
- [x] 1.3 `validate_scan_envelope`（`issues.py:437-440`）status/specific_field 枚举漂移的硬 raise 降级为收进 problems + 继续
- [x] 1.4 测试：构造脏 status/type/priority 的 legacy 行 → 断言 problems 非空 + 项仍在 items 中 + scan 正常返回
- [x] 1.5 测试：构造脏 status 项 → 跑 `issues.py reindex`（端到端）→ 断言不崩 + problems 非空

### Task 2: reindex 总项数守卫（两段式解析）[spec-review-amendment]

- [x] 2.1 `issues.py` 新增 `_count_index_items(path)` 辅助函数：两段式解析旧 INDEX.md — open = 数 `| [A-Z]\d+ |` 行，closed = 解析"共 N 项已闭合"聚合行的 N，返回两者之和。不存在/不可解析 → 返回 0 + 记 problem 警告
- [x] 2.2 `_reindex_core` 写盘前调用，新 < 旧 → `raise ReindexStageError`
- [x] 2.3 测试：构造旧 INDEX 有 N 项（含 closed 聚合行）、新扫描 < N → 断言 raise + INDEX 未被覆盖
- [x] 2.4 测试：旧 INDEX 只有 closed 项（open=0）、新扫描丢了 closed 项 → 断言 raise（不被"首次建"跳过）
- [x] 2.5 测试：首次建（旧不存在）→ 正常写入
- [x] 2.6 测试：旧 INDEX 格式损坏 → 返回 0（跳过校验 + 记 problem 警告），不卡死 reindex

### Task 3: sweep 路径 triage 状态解耦 [spec-review-amendment]

- [x] 3.1 `_bug_triage` / `_todo_triage` 加 `promote` 参数（默认 True），`promote=False` 时 `new_status = old_status`
- [x] 3.2 `triage` CLI 子命令新增 `--batch-only` flag → `promote=False`
- [x] 3.3 `cmd_sweep`（`issues.py:1126-1132`）的子进程调用改为 `triage --batch-only --id X --批次 Y`
- [x] 3.4 测试：直接 triage OPEN 项（无 --batch-only）→ 断言 status 变为 PROPOSED（原行为不变）
- [x] 3.5 测试：triage --batch-only OPEN 项 → 断言 status 仍为 OPEN + batch 已更新
- [x] 3.6 测试：cmd_sweep 端到端 → 断言被 sweep 项 status 保持原样

### Task 4: 文档同步 [spec-review-amendment]

- [x] 4.1 SKILL.md:495-496 triage 命令表：补充 `--batch-only` 说明
- [x] 4.2 SKILL.md:505 sweep 协议描述：注明 sweep 使用 `--batch-only`
- [x] 4.3 `__init__.py:2117` triage CLI help 文案：补充 `--batch-only` 说明
- [x] 4.4 SKILL.md:392-393 batch rename 段落：保持原文（仍然准确——rename 走独立路径的理由不变，因为直接 triage 仍推进状态）

### Task 5: 验证

- [x] 5.1 全量 `pytest sdflow-issues/tests/` 绿
- [x] 5.2 在本仓跑 `python3 sdflow-issues/scripts/issues.py reindex` 确认现有数据不假阳
