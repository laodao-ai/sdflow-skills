---
ship-gate:
  verify: PASS
  reviewed_sha: 8febc63e55c7e95042c4fd3a7080c25cc089fde1
---

# Verify Report: harden-issues-read-write

## 结论

**PASS** — 四个 Task 的全部需求均已实现且有可机验锚点。684 passed, 7 skipped, 3 xfailed。真实数据 reindex 无假阳（open 174, closed 113）。

## 逐需求核对表

### Task 1: 读取路径词表校验（两层同步）

| # | 需求 | 判定 | 锚点 |
|---|---|---|---|
| 1.1 | `_build_effective_snapshot` status 词表校验 → problems.append | ✅ | `sdflow-issues/scripts/sdflow_issues_core/__init__.py:898-901` |
| 1.2 | `_build_effective_snapshot` specific_field 词表校验 → problems.append | ✅ | `sdflow-issues/scripts/sdflow_issues_core/__init__.py:902-905` |
| 1.3 | `validate_scan_envelope` 枚举漂移降级为 problems（不 raise） | ✅ | `sdflow-issues/scripts/issues.py:437-446` |
| 1.4 | 测试：脏 status legacy 行 → problems 非空 + 项仍在 items | ✅ | `test_frontmatter_dual_reader.py::test_legacy_row_dirty_status_downgrades_to_problem_not_raise` |
| 1.5 | 测试：脏 status → reindex 端到端不崩 + problems 非空 | ✅ | `test_task4_rename_snapshot.py::test_reindex_downgrades_status_drift_end_to_end_instead_of_crashing` |
| — | 测试：脏 specific_field legacy 行 → problems 非空 + 项仍在 items | ✅ | `test_frontmatter_dual_reader.py::test_legacy_row_dirty_specific_field_downgrades_to_problem_not_raise` |
| — | [impl-review-fix] frontmatter 层枚举校验也移至 _build_effective_snapshot 统一降级 | ✅ | `__init__.py:617-619` 注释 + `test_frontmatter_dual_reader.py:418-427` 验证不再 raise |

### Task 2: reindex 总项数守卫（两段式解析）

| # | 需求 | 判定 | 锚点 |
|---|---|---|---|
| 2.1 | `_count_index_items` 两段式解析（open 行 + closed 聚合行 N） | ✅ | `sdflow-issues/scripts/issues.py:614-637` |
| 2.2 | `_reindex_core` 写盘前调用，新 < 旧 → raise ReindexStageError | ✅ | `sdflow-issues/scripts/issues.py:653-666` |
| 2.3 | 测试：旧 N 项 + 新 < N → raise + INDEX 未覆盖 | ✅ | `test_issues.py::TestReindexCountGuard::test_raises_and_preserves_index_when_new_scan_has_fewer_items_than_old` |
| 2.4 | 测试：旧 INDEX 只有 closed 项 + 新丢失 → raise | ✅ | `test_issues.py::TestReindexCountGuard::test_raises_when_old_index_has_only_closed_items_and_new_scan_loses_them` |
| 2.5 | 测试：首次建（旧不存在）→ 正常写入 | ✅ | `test_issues.py::TestReindexGuardEdgeCases::test_first_reindex_on_empty_root_not_blocked_by_guard` |
| 2.6 | 测试：旧 INDEX 格式损坏 → 返回 0 + 跳过校验 + 记 problem 警告 | ✅ | `test_issues.py::TestReindexGuardEdgeCases::test_corrupted_old_index_returns_zero_and_does_not_block_reindex` |
| — | [impl-review-fix] 旧 INDEX 存在但解析为 0 时记 problem 警告 | ✅ | `sdflow-issues/scripts/issues.py:654-659` |
| — | [impl-review-fix] `_count_index_items` 加 errors="replace" 防解码崩 | ✅ | `sdflow-issues/scripts/issues.py:626` |

### Task 3: sweep 路径 triage 状态解耦

| # | 需求 | 判定 | 锚点 |
|---|---|---|---|
| 3.1 | `_bug_triage` / `_todo_triage` 加 promote 参数（默认 True） | ✅ | `__init__.py:1799` + `__init__.py:1841` |
| 3.2 | triage CLI 新增 --batch-only flag → promote=False | ✅ | `__init__.py:2137-2138` + `__init__.py:2103` |
| 3.3 | cmd_sweep 子进程调用改为 triage --batch-only | ✅ | `sdflow-issues/scripts/issues.py:1182` |
| 3.4 | 测试：直接 triage OPEN → PROPOSED（原行为不变） | ✅ | `test_buglist.py::test_open_item_triage_sets_proposed_and_batch` + `test_todolist.py::test_open_item_triage_sets_proposed_and_batch` |
| 3.5 | 测试：triage --batch-only OPEN → status 仍 OPEN + batch 已更新 | ✅ | `test_buglist.py::test_batch_only_triage_does_not_promote_open_status` + `test_todolist.py::test_batch_only_triage_does_not_promote_open_status` |
| 3.6 | 测试：cmd_sweep 端到端 → status 保持原样 | ✅ | `test_issues.py::TestSweep::test_sweep_open_ungrouped` |

### Task 4: 文档同步

| # | 需求 | 判定 | 锚点 |
|---|---|---|---|
| 4.1 | SKILL.md triage 命令表补 --batch-only 说明 | ✅ | `sdflow-issues/SKILL.md:499` |
| 4.2 | SKILL.md sweep 协议注明使用 --batch-only | ✅ | `sdflow-issues/SKILL.md:406,411,509` |
| 4.3 | `__init__.py` triage CLI help 补 --batch-only 说明 | ✅ | `__init__.py:2137-2138` |
| 4.4 | batch rename 段落保持原文 | ✅ | SKILL.md 未改动 rename 段落（无 diff） |

### Task 5: 验证

| # | 需求 | 判定 | 锚点 |
|---|---|---|---|
| 5.1 | 全量 pytest 绿 | ✅ | HEAD `8febc63` 跑 684 passed, 7 skipped, 3 xfailed |
| 5.2 | 真实数据 reindex 无假阳 | ✅ | `issues.py reindex` 输出 open 174, closed 113, exit 0 |

## impl-reports SHA 一致性

impl-reports/task4-verification.md 记录 unit 层 SHA = `536b442`。此后有两个 impl-review-fix 提交（`2743650`, `8febc63`），均为代码审修复（enum 校验统一降级 + count-guard 补 problem 警告 + errors="replace"），测试在 HEAD `8febc63` 全量重跑确认绿。

## 缺口清单

无核心功能缺口。
