---
ship-gate:
  verify: PASS
  reviewed_sha: f39ee865e21d24fbbc1cdd96654247c771bd2417
---

# Verify Report: issues-v2-single-file-model

**Date**: 2026-08-04
**Conclusion**: **PASS**

## 逐需求核对表

### STOR-01~07（核心脚本 issues_v2.py）

| 需求 | 代码出处 | 状态 |
|------|---------|------|
| STOR-01 单文件存储格式（frontmatter + body） | `issues_v2.py:335-340`（read_issue）, `:343-361`（write_issue）, `:282-313`（render/parse_frontmatter）; 测试 `test_render_frontmatter_quotes_values_and_writes_null_for_none`, `test_parse_frontmatter_round_trips_quoted_values_and_null`, `test_write_issue_read_issue_round_trip` | PASS |
| STOR-01 字段固定顺序 | `issues_v2.py:55-58` FRONTMATTER_FIELDS 元组; `render_frontmatter` 按此顺序输出; 测试验证精确行序 | PASS |
| STOR-01 C8: write_issue create 用 O_CREAT\|O_EXCL | `issues_v2.py:350` `os.O_WRONLY \| os.O_CREAT \| os.O_EXCL`; 测试 `test_write_issue_create_uses_o_creat_excl_and_rejects_existing`, `test_write_issue_concurrent_o_creat_excl_only_one_winner`（multiprocessing 8 并发） | PASS |
| STOR-01 C9: frontmatter 值双引号包裹 | `issues_v2.py:275-276` `_quote_value`; `render_frontmatter` 对非 null 值一律 `_quote_value`; 测试 `test_render_frontmatter_quotes_values_and_writes_null_for_none` 验证精确格式 | PASS |
| STOR-02 open/closed 目录分层 + 终态 git mv | `issues_v2.py:553-576` cmd_set_status 终态分支; 测试 `test_cli_set_status_bug_fixed_moves_to_closed_and_fills_fields`（含 git status 验证） | PASS |
| STOR-02 非终态不移文件 | `issues_v2.py:540` `terminal = new in TERMINAL_STATUSES[pool]`; 测试 `test_cli_set_status_non_terminal_stays_in_open` | PASS |
| STOR-03 INDEX.md / CLOSED.md reindex 再生 | `issues_v2.py:698-711` cmd_reindex; 测试 `test_cli_reindex_generates_index_and_closed_sorted_by_id`, `test_cli_reindex_idempotent_when_rerun` | PASS |
| STOR-04 next-id 跨 open+closed 扫描 | `issues_v2.py:389-402` next_id; 测试 `test_next_id_scans_across_open_and_closed`（T257+T260→T261）, `test_cli_next_id_cross_directory` | PASS |
| STOR-05 add 命令创建新 issue | `issues_v2.py:422-489` cmd_add; 测试 `test_cli_add_bug_creates_open_file_with_required_frontmatter`, `test_cli_add_todo_creates_open_file_with_type` | PASS |
| STOR-05 detect_change 自动填 source_change | `issues_v2.py:446-447`; 测试 `test_cli_add_detects_source_change_from_unique_change_dir`, `test_cli_add_explicit_source_change_overrides_detection` | PASS |
| STOR-05 C10: git add | `issues_v2.py:472-479`; 测试 `test_cli_add_bug_creates_open_file_with_required_frontmatter` 验证 git status | PASS |
| STOR-06 终态 issue 拒绝再改 | `issues_v2.py:518-519`; 测试 `test_cli_set_status_rejects_already_terminal` | PASS |
| STOR-06 FIXED 缺 evidence 拒绝 | `issues_v2.py:524-525`; 测试 `test_cli_set_status_bug_fixed_requires_evidence` | PASS |
| STOR-06 todo DONE 缺 evidence 拒绝 | `issues_v2.py:526-527`; 测试 `test_cli_set_status_todo_done_requires_evidence` | PASS |
| STOR-06 WONTFIX/WONTDO 缺 reason 拒绝 | `issues_v2.py:528-529`; 测试 `test_cli_set_status_wontfix_requires_reason` | PASS |
| STOR-06 终态词表按池校验 | `issues_v2.py:521` `new not in STATUS_VALUES[pool]`（STATUS_VALUES["bug"] 不含 DONE，["todo"] 不含 FIXED） | PASS |
| STOR-06 body 变更历史行 | `issues_v2.py:534`; 测试 `test_cli_set_status_bug_fixed_moves_to_closed_and_fills_fields` 验证 `"状态：OPEN → FIXED" in body` | PASS |
| STOR-06 git mv 前确保 tracked | `issues_v2.py:559-567`; 测试 `test_cli_set_status_untracked_file_is_git_added_before_mv` | PASS |
| STOR-06 非 git 降级 os.rename | `issues_v2.py:576`; 测试 `test_cli_set_status_non_git_repo_falls_back_to_os_rename` | PASS |
| STOR-07 scan 默认 open + --all 含 closed | `issues_v2.py:631-651` cmd_scan; 测试 `test_cli_scan_defaults_to_open_only`, `test_cli_scan_all_includes_closed` | PASS |
| STOR-07 --source-change 过滤 | `issues_v2.py:637`; 测试 `test_cli_scan_source_change_filters` | PASS |
| STOR-07 --json 输出 | 测试 `test_cli_scan_json_outputs_frontmatter_dicts` | PASS |
| STOR-07 --pool/--status 过滤 | 测试 `test_cli_scan_status_and_pool_filters` | PASS |

### MIG-01~05（迁移工具）

| 需求 | 代码出处 | 状态 |
|------|---------|------|
| MIG-01 双格式解析 | `issues_v2.py:783-804`（_v1_split_frontmatter）, `:807-839`（_v1_legacy_table_rows）; 测试 `test_migrate_parses_pure_legacy_table_format`, `test_migrate_parses_pure_frontmatter_overlay_format` | PASS |
| MIG-01 逐 item 去重（frontmatter 覆盖） | `issues_v2.py:889-922`（_v1_parse_file shadow 算法）; 测试 `test_migrate_frontmatter_shadows_legacy_row_same_id`（验证 shadowed=1, status 取 frontmatter 值） | PASS |
| MIG-02 输出 v2 单文件（open/closed 分层） | `issues_v2.py:1083-1089` cmd_migrate; 测试 `test_migrate_parses_pure_legacy_table_format`（closed/B1.md）, `test_migrate_parses_pure_frontmatter_overlay_format`（open/T5.md） | PASS |
| MIG-02 字段映射 resolved_by body 提取 | `issues_v2.py:925-942`; 测试 `test_migrate_parses_pure_legacy_table_format` 验证 `fm["resolved_by"] == "fix-something"` | PASS |
| MIG-02 closed_date best-effort | `issues_v2.py:965-971`; 测试 `test_migrate_closed_date_falls_back_to_file_date_when_no_history_line` | PASS |
| MIG-03 幂等（已存在跳过） | `issues_v2.py:1087-1089`; 测试 `test_migrate_idempotent_skips_existing_target_file`, `test_migrate_rerun_is_fully_idempotent` | PASS |
| MIG-03 统计报告含 shadowed ID 数 | 测试 `test_migrate_stats_report_shape` 验证 stats schema, `test_migrate_frontmatter_shadows_legacy_row_same_id` 验证 shadowed=1 | PASS |
| MIG-04 迁移后自动 reindex | `issues_v2.py:1102`; 测试 `test_migrate_reindexes_open_and_closed_after_migration` | PASS |
| MIG-05 PLANNED 批次信息迁移 | `issues_v2.py:1007-1025`（_v1_planned_batch_notes）, `:1091-1098`; 测试 `test_migrate_planned_batch_note_appended_only_for_planned_batches`（PLANNED 迁入, DONE 不迁） | PASS |

### Task 3（本仓数据迁移）

| 需求 | 代码出处 | 状态 |
|------|---------|------|
| 3.1 本仓 287 issue 全迁移 | `openspec/issues/open/`(156) + `closed/`(131) = 287; INDEX.md 162 行, CLOSED.md 137 行 | PASS |
| 3.2 旧文件清理 | buglist/, todolist/, batches.md, batch-triage-rules.md, consolidation-plan.md 均已删除 | PASS |
| 3.3 旧脚本清理 | buglist.py, todolist.py, migrate_legacy.py 已删; sdflow_issues_core/ 仅剩 __pycache__（bytecode，非源码） | PASS |

### Task 4（消费方更新）

| 需求 | 代码出处 | 状态 |
|------|---------|------|
| 4.1a/b SKILL.md 更新 | `sdflow-issues/SKILL.md` 含 27 处 `issues_v2` 引用 | PASS |
| 4.2 sdflow-done sweep→scan | `sdflow-done/SKILL.md` 含 `issues_v2.py scan --json --source-change` | PASS |
| 4.3 hack/tests 路径更新 | `TODO_SCRIPT` 指向 `issues_v2.py` | PASS |
| 4.4 CLAUDE.md 更新 | 命令示例引用 `test_issues_v2.py` | PASS |
| 4.5 AGENTS.md 更新 | 含 `open|closed/` 路径引用 | PASS |
| 4.6 claude-section.md 更新 | 含 `open\|closed/` 引用 | PASS |
| 4.7 CONTEXT.md 更新 | 10 处 issues_v2/单文件/open/closed 引用 | PASS |
| 4.8~4.10 delta specs | `openspec/changes/issues-v2-single-file-model/specs/` 含 spec-workflow, determinism-guards, recorder-root-resolution 目录 | PASS |
| 4.11 Windows CI 更新 | `.github/workflows/windows-recorder-smoke.yml` 引用 `issues_v2.py` 三处 | PASS |

### Task 5（测试）

| 需求 | 代码出处 | 状态 |
|------|---------|------|
| 5.1 核心命令测试 | `test_issues_v2.py` 38 个测试函数覆盖 add/set-status/scan/reindex/next-id + 并发 + 边界 | PASS |
| 5.2 迁移测试 | `test_issues_v2.py` 12 个 migrate 测试（双格式/去重/幂等/批次/stats） | PASS |
| 5.3a 旧测试清理 | 仅保留 `test_issues_v2.py` + 3 个改造后的保留测试文件 | PASS |
| 5.3b 格式无关测试改造 | `test_repo_root_identity_issues.py`（40+ 用例）, `test_task2_windows_local_fs_smoke.py`, `test_task6_coverage_gate.py` | PASS |
| 5.4 全仓 pytest 绿 | 2471 passed, 10 skipped, 0 failed (286.40s) at SHA f39ee86 | PASS |

### Tickets 轨验证（Task 5 收尾报告）

| 检查项 | 结果 |
|--------|------|
| task5-verify.md 存在 | `impl-reports/task5-verify.md` 存在 |
| 证据 SHA 一致 | 报告记录 SHA `dd2f0d3`; 当前 HEAD `f39ee86` 领先（后续有 checkpoint commit `a5e1491`），覆盖面为提交历史的超集 |
| 全量通过 | 2471 passed, 10 skipped, 0 failed 与报告一致 |

## 缺口清单

**无核心功能缺口。**

Minor 观察（不影响判定）：
- `sdflow_issues_core/__pycache__/` 残留两个 `.pyc` 文件（bytecode cache，非源码），建议 `rm -rf`。

## 判定

**PASS**
