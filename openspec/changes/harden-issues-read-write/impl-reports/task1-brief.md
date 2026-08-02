### Task 1: 读取路径两层词表校验

**Blocked-by:** none
**R-ID:** R1

在 core 层 `_build_effective_snapshot`（`__init__.py:826-901`）的自检段追加 status 和 specific_field 词表校验：超出词表的值记入 `problems`，不 raise、不 `_die`、不丢弃项。

在 consumer 边界 `validate_scan_envelope`（`issues.py:437-440`）将 status 和 specific_field 枚举漂移的硬 `raise ValueError` 降级为收进 problems + 继续。

- [ ] `_build_effective_snapshot` 自检段追加 `item["status"] not in spec.status_values` → `problems.append`
- [ ] `_build_effective_snapshot` 自检段追加 `item[spec.specific_field] not in spec.specific_values` → `problems.append`
- [ ] `validate_scan_envelope` status/specific_field 枚举漂移的硬 raise 改为收进 problems + 继续
- [ ] 测试：构造脏 status 的 legacy 行 → 断言 problems 非空 + 项仍在 items 中 + scan 正常返回
- [ ] 测试：构造脏 specific_field 的 legacy 行 → 断言 problems 非空 + 项仍在 items 中
- [ ] 测试：构造脏 status 项 → 跑 `issues.py reindex` 端到端 → 断言不崩 + problems 非空

