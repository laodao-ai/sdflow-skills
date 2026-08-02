# Task 1: 读取路径两层词表校验 — 实现报告

## 改动

1. **core 层** `_build_effective_snapshot`（`sdflow-issues/scripts/sdflow_issues_core/__init__.py`，
   合并 `effective_items` 之后新增自检循环）：对每个 `effective_items` 项追加
   `item["status"] not in spec.status_values` 与 `item[spec.specific_field] not in spec.specific_values`
   两条词表校验，命中即 `problems.append(...)`，不 raise、不 `_die`、不从 `effective_items` 里剔除。
2. **consumer 边界** `validate_scan_envelope`（`sdflow-issues/scripts/issues.py:437-446`）：把
   status / specific_field 枚举漂移的硬 `raise ValueError`（"枚举漂移"）降级为
   `data["problems"].append(...)` + 继续解析，脏值项仍原样出现在返回的 `items` 里。
3. 写入路径（`cmd_add` / `set-status` 的 `_die`）未改动，符合 Global Constraints。

## 测试

- `sdflow-issues/tests/test_frontmatter_dual_reader.py`：新增
  `test_legacy_row_dirty_status_downgrades_to_problem_not_raise` /
  `test_legacy_row_dirty_specific_field_downgrades_to_problem_not_raise`——用 todo 池
  （`requires_block=False`，避免"缺详细块"噪音 problem 掩盖断言意图）构造脏 status / 脏 type 的
  legacy 行，断言 `problems` 非空且**内容命中**该字段与脏值、脏值项仍在 `items` 中、
  `cmd_scan --json` 正常返回（不崩）。
- `sdflow-issues/tests/test_task4_rename_snapshot.py`：新增
  `test_validate_scan_envelope_downgrades_status_and_specific_field_drift_to_problems`（envelope
  层：脏 status + 脏 priority 同时命中，断言 items 原样保留、problems 命中两个字段）与
  `test_reindex_downgrades_status_drift_end_to_end_instead_of_crashing`（`_reindex_core` 端到端：
  bug 池返回脏 status 项、todo 池返回空，断言不 raise、problems 非空、`INDEX.md` 正常写盘）。
  同时**移除**两处已被本 change 目标态废止的旧断言：
  `test_validate_scan_envelope_rejects_protocol_drift` 里 `priority="P9"` 那一档（曾断言硬 raise，
  现按设计降级为 problems）、`test_reindex_consumer_drift_preserves_existing_index_and_batches`
  里 `status="NEW_ENUM"` 那一档（同理）。
- 未改动写入路径测试。

## 验证

| 层 | 命令 | 退出码 | SHA |
|---|---|---|---|
| unit | `python3 -m pytest sdflow-issues/tests/ -x -v` | 0（673 passed, 7 skipped, 3 xfailed） | badfa5fb1656b3616783c170ca4f8be92927a044 |

注：SHA 为本次实现前的 HEAD（工作区改动未提交——commit/checkpoint 由后续执行模式在双轴审通过后补打，
implementer 阶段不自行提交）。

## 备注（worktree 环境说明）

本 agent 运行在 worktree `agent-a405cf3a063cd1677`（分支 `worktree-agent-a405cf3a063cd1677`，
基于 `badfa5f`），与承载本 change 四件套的共享检出（分支 `feat/harden-issues-read-write`，
基于同一 `badfa5f` + 仅追加 `openspec/changes/harden-issues-read-write/` 文档，未改代码）是两个独立
worktree。已用 `git diff HEAD feat/harden-issues-read-write -- sdflow-issues/...` 核实两侧改动前的
源码字节完全一致，故本 worktree 内的实现与该分支等价、可安全合并。`openspec/changes/harden-issues-read-write/`
目录在本 worktree 内原不存在，本报告所在的 `impl-reports/` 子目录为本次新建。
