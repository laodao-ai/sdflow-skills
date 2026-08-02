# Hand-off — harden-issues-read-write

## ✅ 完成了什么

- **读取路径两层词表校验**：`_build_effective_snapshot`（core 层）+ `validate_scan_envelope`（consumer 边界）对 status/specific_field 超出词表的值统一降级为 `problems.append`，不 raise、不丢弃项。代码审发现 `_validated_recorder_model` 的 frontmatter 枚举硬 raise 未被覆盖（对 canonical 格式项是死代码），已修复移除。
  - 锚：`__init__.py:899-908`（core 校验）+ `issues.py:437-446`（consumer 降级）+ `__init__.py:618-621` 移除（impl-review-fix R1）
  - 测试：`test_frontmatter_dual_reader.py` 4 个脏值测试 + `test_task4_rename_snapshot.py` 2 个端到端测试
- **reindex 总项数只增不减守卫**：`_count_index_items` 两段式解析（open 行数 + closed 聚合数），`_reindex_core` 写盘前 `new < old → ReindexStageError` 拒覆盖。
  - 锚：`issues.py:610-637`（`_count_index_items`）+ `issues.py:653-660`（守卫）
  - 测试：`test_issues.py` 的 `TestCountIndexItems`（5 例）+ `TestReindexCountGuard`（4 例）
- **sweep 路径 triage 状态解耦**：`_bug_triage`/`_todo_triage` 加 `promote` 参数，`triage` CLI 新增 `--batch-only`，`cmd_sweep` 改用 `triage --batch-only`。
  - 锚：`__init__.py:1800-1811`（bug promote）+ `__init__.py:1842-1853`（todo promote）+ `issues.py:1176`（sweep 调用）
  - 测试：`test_buglist.py`/`test_todolist.py` batch-only 测试 + `test_issues.py` sweep 端到端断言更新
- **SKILL.md 文档同步**：triage 命令表补充 `--batch-only` 说明，sweep 协议注明状态解耦。
- **代码审自动修复 3 项**：R1 frontmatter 枚举降级、R2 count-guard 缺失 problem 警告、R3 UnicodeDecodeError 防护。

## ⏳ 未完成 / 延后

- sweep 结果：0 项匹配（本 change 未新增 buglist/todolist 项）
- 代码审已裁掉的 4 项低置信度观察点（X1-X4）均为 minor/nitpick，不影响功能

## ▶ 下一阶段建议

本 change 是独立的读取路径加固，无后续 change 依赖。相关的 T231（原始缺陷报告）可在归档后标 DONE。
