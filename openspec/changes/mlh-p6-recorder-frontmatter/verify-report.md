---
ship-gate:
  verify: FAIL
---
# Verify Report — mlh-p6-recorder-frontmatter

**结论：FAIL——唯一剩余门是 actual Windows local-disk smoke（无 无-skip 执行锚，deferred todolist T154）。原全仓 `-W error` warning 门已按 change-report 成因溯源决策 fold 清零（`1619 passed, 2 skipped`）。Windows 兼容目标未取得执行锚前，按目标态不得归档。**

- 日期：2026-07-17
- Change：`mlh-p6-recorder-frontmatter`
- 核验基线：`HEAD 58e99b4` + 工作区未提交的 7.5 fold 修复（4 站点未关闭文件 + docstring）；merge-base `7fd59e63fdc83b6b63d860fccc064c12ce02ddf1`

## 逐需求核对

| 需求/任务 | 代码出处锚点 | 状态 |
|---|---|---|
| `SW-RI-1` frontmatter v1、strict shared envelope、legacy/overlay dual-read、marker prose、bytes writer | `sdflow-buglist/scripts/buglist.py:402` `render_recorder_namespace`; `:532` `parse_recorder_document`; `:568` `read_recorder_document`; `sdflow-buglist/tests/test_frontmatter_dual_reader.py::test_canonical_renderer_has_unique_golden_bytes_and_round_trips_unicode`; `::test_scan_dual_reads_canonical_overlay_and_legacy`; `::test_bad_namespace_is_fail_closed_without_json_stdout`; `sdflow-buglist/tests/test_task3_frontmatter_writer.py::test_bug_add_creates_canonical_frontmatter_without_legacy_row`; `::test_bug_set_status_promotes_legacy_item_without_rewriting_old_bytes`; `::test_overlay_writer_preserves_bom_crlf_and_external_namespace_bytes` | ✅ 实现 |
| `SW-RI-1` consumer JSON/安装后 legacy+canonical+overlay smoke | `sdflow-buglist/tests/test_task5_delivery_contract.py::test_upgraded_install_known_consumer_smoke`（实际执行安装后两个 `scan --json`、`reindex --strict`、`sweep`，见 `:206-277`） | ✅ 实现 |
| `SW-RI-2` ASCII semantic ID、跨池唯一、exclusive snapshot lock、owner/participant、原子写与 runtime ignore | `sdflow-buglist/scripts/buglist.py:84-85,121-137,201-250`; `sdflow-init/scripts/init.py:90` `merge_runtime_gitignore`; `sdflow-buglist/tests/test_task2_semantic_lock.py::test_twenty_process_adds_are_unique_or_fail_loud`; `::test_reader_writer_barrier_is_bidirectional_across_processes`; `::test_two_cooperative_namespace_producers_use_cross_process_barrier`; `::test_real_sweep_reindex_scan_nested_delegation`; `sdflow-init/tests/test_runtime_gitignore.py::test_run_init_and_update_use_canonical_runtime_merge` | ✅ 实现 |
| `SW-RI-2` Windows local FS acquire/conflict/participant/replace/cleanup + setup copy | 契约测试存在：`sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py:20,31-92`；workflow 存在：`.github/workflows/windows-recorder-smoke.yml:23-33`；但本机定向套件显示这两项均 `skipped`，`git ls-remote` 无该 feature branch，`gh run list --branch feat/mlh-p6-recorder-frontmatter` 返回 `[]`，按 workflow 名查询返回 404；没有 Windows run URL/hash/log | ❌ 核心缺失 |
| `SW-RI-3` 每 dated file read/parse=1、rename 不调 recorder scan、updated snapshot reindex、registry provenance/retry | `sdflow-issues/scripts/issues.py:764` `read_rename_snapshot`; `:1473` `_reindex_core`; `:2114` `cmd_batch_rename`; `sdflow-issues/tests/test_task4_rename_snapshot.py::test_read_rename_snapshot_reads_and_parses_each_dated_file_once`; `::test_batch_rename_uses_direct_snapshot_zero_recorder_scans_and_writes_provenance`; `::test_batch_rename_retry_converges_all_old_mixed_and_all_new`; `::test_batch_rename_stage_fault_is_nonzero_and_original_command_recovers` | ✅ 实现 |
| `SW-RI-4` reindex problems 可观测、default/strict 分层、fatal fail-closed、同 snapshot 派生输出 | `sdflow-issues/scripts/issues.py:1164` `validate_scan_envelope`; `:1473` `_reindex_core`; `sdflow-issues/tests/test_task4_rename_snapshot.py::test_reindex_consumer_drift_preserves_existing_index_and_batches`; `::test_reindex_rejects_schema_value_drift_from_each_pool_before_derived_writes`; `::test_reindex_core_uses_supplied_snapshot_without_rescanning`; recorder/issue 定向套件 `445 passed, 2 skipped` | ✅ 实现 |
| `DG-RI-1` 三向/两向 helper 镜像一致性、自包含、旧 helper 退役 | `sdflow-buglist/tests/test_mirror_consistency.py:64-101` 显式 roster；`::test_three_way_mirror_consistency`; `::test_two_way_mirror_consistency`; `::test_helper_deletion_is_not_silently_swallowed`; 单独执行 `7 passed`；source grep 未发现 `import yaml`、跨 recorder import 或 `_reject_cell_unsafe` 活引用 | ✅ 实现 |
| Tasks `6.1-6.4` corpus 对账、ADR/术语、dogfood、roadmap/issues reconciliation | `sdflow-buglist/tests/test_task5_delivery_contract.py::test_repository_legacy_corpus_matches_independent_projection_item_by_item`; `openspec/adr/0025-recorder-versioned-frontmatter-overlay-and-snapshot-lock.md:50-77`; `openspec/CONTEXT.md:224-258`; `openspec/issues/todolist/2026-07-todolist.md:1-13,1408-1501`; `openspec/roadmaps/mechanical-layer-hardening/roadmap.md:200-206` | ✅ 实现 |
| Task `7.1` recorder 定向 `-W error` | `uv run --with pytest pytest sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `445 passed, 2 skipped in 26.57s`; skips 是 `test_task2_windows_local_fs_smoke.py` 的两项 Windows-only case | ✅ POSIX 定向门通过；Windows 另见核心缺口 |
| Task `7.2` mirror + source grep | `uv run --with pytest pytest sdflow-buglist/tests/test_mirror_consistency.py -W error -q` → `7 passed`; source grep 结果为空 | ✅ 实现 |
| Task `7.3` 全仓 `pytest -W error` | fold 修 4 个 pre-existing 未关闭文件站点后 `uv run --with pytest pytest -W error` → `1619 passed, 2 skipped in 75.41s`（2 skip = Windows-only）；`openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid，`git diff --check` → 0 | ✅ 验证门达成 |
| Task `7.4` known-consumer smoke + actual Windows smoke | known-consumer：`test_upgraded_install_known_consumer_smoke` 已在定向套件通过；actual Windows：无执行锚，`tasks.md` 7.4 仍诚实保持未完成（deferred，登记 todolist T154） | ❌ 核心缺失（唯一剩余门）|

## 核心缺口

1. **actual Windows local-disk runner 尚未执行。** `SW-RI-2` 明确把 Windows local FS 设为必须 smoke 的兼容目标，Task 7.4 也要求 acquire/conflict/participant/replace/cleanup 与 setup copy。macOS 上 `2 skipped`、workflow YAML、持久化触发器测试都只能证明“可运行定义存在”，不能证明 Windows 行为通过；远端也没有该 branch/run。必须先产生无 skip 的 Windows runner PASS 锚（run URL/hash/log），然后重新 verify。
2. ~~**Task 7.3 的全仓 warnings-as-errors 门未通过。**~~ **（已解决——按成因溯源决策 fold 清零。）** 原 38 项 pre-existing `ResourceWarning`/`PytestUnraisableExceptionWarning` 已修：4 个未关闭文件站点全部收口——`maintain_scan.py:184/:244` 裸 `open().read()` → `with`、`test_maintain_scan.py:224` 裸 `open(...,”w”).write()` → `with`（`-W error` 面治新发现，非原记「37 全在读」）、`test_sad_scaffold.py:525` 并发 `Popen(PIPE)` 只 `wait()` → `communicate()` drain。修后全仓 `pytest -W error` → `1619 passed, 2 skipped`。全仓机械守卫（把全仓 `-W error` 常态化为持久 CI 门）超出本 change 内聚范围，另开 hardening change（登记 todolist T155）。

## Minor 缺口

- ~~`cmd_triage` docstring 仍描述“写表格批次列”~~ **（已解决，本 change fold 改掉）**：两 recorder 镜像的 `cmd_triage` docstring（`buglist.py:1401`/`todolist.py:1370`）已改为描述 frontmatter 批次写入、legacy promotion 与 marker history 语义（对应 todolist `T153`）。
- 新登记的 deferred/后续项：`T154`（actual Windows smoke 未执行，本 change deferred）、`T155`（全仓 `-W error` 常态化 CI 守卫，另开 hardening change 起点）。
- 已登记的 `T151`（镜像守卫扩常量/类型定义）与 `T152`（review-package diff-check 记录口径）属于守卫/流程强化，不是 delta spec 的核心功能缺失。

FAIL：**唯一剩余门** = actual Windows local-disk smoke 无 无-skip 执行锚（deferred，todolist T154）。全仓 `pytest -W error` warning 门已按成因溯源决策 fold 清零（4 站点未关闭文件收口 → `1619 passed, 2 skipped`）。Windows 门未取得执行锚前停止归档。
