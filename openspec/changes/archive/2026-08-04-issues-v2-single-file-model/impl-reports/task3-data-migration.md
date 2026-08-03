# Task 3 实现报告：本仓数据迁移 + 旧文件清理 + 测试调整

## 迁移执行

```
python3 sdflow-issues/scripts/issues_v2.py --root . migrate
```

（脚本本体已在 Task 1/2 落地为 `issues_v2.py`；design.md 里的 `issues.py` 是目标态命名，
本 change 当前阶段该脚本文件名仍是 `issues_v2.py`——是否连同旧 v1 `issues.py` 一并重命名
留给 Task 4「消费方更新」处理，Task 3 未做重命名，仅按现状调用。）

统计：

```json
{
  "files_scanned": 11,
  "parse_errors": 0,
  "shadowed": 35,
  "migrated": 287,
  "skipped_existing": 0,
  "mapping_errors": 0,
  "batch_notes_applied": 204,
  "resolved_by": {"matched": 78, "note_no_token": 50, "no_history_line": 3}
}
```

验证：
- `openspec/issues/open/*.md` = 156 个，`openspec/issues/closed/*.md` = 131 个，合计 287 ✅
- `INDEX.md` 表体 156 行（open 全量），`CLOSED.md` 表体 131 行（closed 全量）✅

## 旧文件清理（`git rm`，历史可溯）

数据文件：`openspec/issues/buglist/`（10 文件）、`todolist/`（1 文件）、`batches.md`、
`batch-triage-rules.md`、`consolidation-plan.md`。

脚本：`sdflow-issues/scripts/buglist.py`、`todolist.py`、`migrate_legacy.py`、
`sdflow_issues_core/__init__.py`（2175 行），以及 v1 统一入口 `issues.py`（1305 行，按
orchestrator 指示明确删除；当前 v2 单一入口仍是 `issues_v2.py`）。

## 测试调整

**删除**（17 个文件，全部格式/机制耦合于 v1，测试对象已不存在）：
`test_buglist.py`、`test_todolist.py`、`test_determinism_guards.py`、`test_migrate_legacy.py`、
`test_repo_root_identity_todolist.py`、`test_repo_root_identity_buglist.py`（与保留的
`test_repo_root_identity_issues.py` 逐条重复，只留一份）、`test_issues.py`、
`test_pool_spec_schema.py`、`test_task4_rename_snapshot.py`、`test_task5_delivery_contract.py`、
`test_frontmatter_dual_reader.py`、`test_downstream_reference_guard.py`（连带断言
`openspec/issues/{buglist,todolist}` 池目录必须存在，与 v2 目标态矛盾）、
`test_patch_discipline.py`（只守护已删除测试用到的 `conftest.py` dispatch 补桩纪律）、
`test_batch_lint.py`、`test_task2_semantic_lock.py`、`test_task3_frontmatter_writer.py`、
`test_task6_cli_equivalence_harness.py`（v1 三薄入口互相等价性检查，v2 单入口无此概念）。
`sdflow-issues/tests/conftest.py` 一并删除：其 `dispatch_run`/`scan_only_run`/
`argv_contains` 补桩工厂只被上述已删除测试使用，且模块顶层 `import issues` / `import
sdflow_issues_core` 会阻断整个 `sdflow-issues/tests/` 目录的 collection。

**保留 + 改造**（3 个文件）：

1. `test_repo_root_identity_issues.py` —— import/`SCRIPT` 改指向 `issues_v2.py`；
   `_fake_git_stdout` 改为返回 utf-8 编码 bytes（`issues_v2.py` 的 `repo_root` 不传
   `text=True`，走 bytes stdout + 手动 `.decode`，与已删除的 v1 `issues.py` 行为不同）；
   一处内嵌子进程脚本的 `from issues import repo_root` 改为 `from issues_v2 import
   repo_root`；删除唯一依赖 v1 `recorder_lock`/`RECORDER_LOCK_ENV`/委派链协议的 xfail 用例
   `test_child_resolving_a_different_root_must_fail_loudly`（v2 无仓级锁，场景前提不成立）；
   `_core_ast()` 辅助函数删除、改用已有的 `_script_ast()`（v2 单文件无独立 core 模块）。
   49 个用例全部通过。
2. `test_task2_windows_local_fs_smoke.py` —— 删除 `test_windows_local_disk_
   acquire_conflict_replace_cleanup`（recorder_lock 端到端，机制已在 v2 移除；其中
   `merge_runtime_gitignore` 的 replace-fault 覆盖已由 `sdflow-init/tests/
   test_runtime_gitignore.py::test_merge_runtime_gitignore_write_and_replace_faults_
   preserve_original` 独立覆盖，无覆盖损失）；其余 5 个 repo_root Windows 冒烟用例改为
   加载 `issues_v2.py`；setup.sh 安装产物字节比对目标从 `buglist.py` 改为 `issues_v2.py`。
   非 Windows 宿主上 6 个用例全部 skip（预期，无法在本机验证行为，仅验证 collection/import
   不再报错）。
3. `test_task6_coverage_gate.py` —— 整体重写：v1 版本比对「argparse 枚举」与「v1 三脚本
   equivalence harness 覆盖清单」，equivalence harness 已删除、比对对象不存在。改为直接比对
   `issues_v2.py` argparse 自身枚举的 6 个 subcommand（`add`/`set-status`/`scan`/
   `reindex`/`next-id`/`migrate`，`让工具自己回答` 而非手搓名单）与 `test_issues_v2.py`
   源码里出现的 subcommand 字面量，逐一核验均被覆盖。1 个用例通过。

## 测试结果

```
pytest sdflow-issues/tests/ -q
→ 105 passed, 6 skipped (Windows-only) in 7.9s
```

`sdflow-issues/tests/` 下全绿。

**已知未覆盖（明确超出 Task 3 范围，留给 Task 4）**：全仓 `pytest` 实跑结果
`2458 passed, 13 failed, 10 skipped in 284.53s`——13 个失败全部集中在
`hack/tests/test_harden_sdflow_spec_followup_closure.py`（`FileNotFoundError`：该文件硬编码
`TODO_SCRIPT = ROOT / "sdflow-issues/scripts/todolist.py"` 并 subprocess 调用它；
`todolist.py` 已按本票要求删除）。这条路径更新明确登记在 tasks.md 4.3（"更新
`hack/tests/test_harden_sdflow_spec_followup_closure.py`：`TODO_SCRIPT` 路径"），不在
Task 3（"本仓数据迁移 + 旧文件清理 + 测试调整"）的验收范围内，未顺手修改（rule ③ 不越权
改动非本票范围的消费方文件）。留待 Task 4 implementer 处理；除这 13 个之外，全仓其余
2458 个用例（含 `sdflow-issues/tests/` 全部 105 个）绿。

## 验收对照

- [x] 迁移完成，open/ + closed/ 文件数之和 = 287
- [x] INDEX.md 列出 open/ 中全部 issue，CLOSED.md 列出 closed/ 中全部
- [x] 旧文件（buglist/、todolist/、batches.md 等）和旧脚本（buglist.py、todolist.py、
      sdflow_issues_core/、migrate_legacy.py，以及 v1 issues.py）已删除
- [x] 格式耦合的旧测试已清理（17 个文件）
- [x] 格式无关的不变量测试改造后通过（仓根解析、Windows 编码、覆盖率门禁）——
      `pytest sdflow-issues/tests/` 105 passed, 6 skipped
