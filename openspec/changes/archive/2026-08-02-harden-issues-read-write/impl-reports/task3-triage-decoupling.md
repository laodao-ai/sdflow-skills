# Task 3: sweep 路径 triage 状态解耦 + 文档同步

## 改动

- `sdflow-issues/scripts/sdflow_issues_core/__init__.py`
  - `_bug_triage(args, spec, promote=True)` / `_todo_triage(args, spec, promote=True)`：新增
    `promote` 参数（默认 `True`，保持原行为）。`promote=False` 时跳过 `open_untriaged` 推进逻辑，
    `new_status = old_status`（批次仍照常写入）。
  - `_cmd_triage(args, spec, strat)`：改为 `strat.triage(args, spec, promote=not args.batch_only)`。
  - `triage` 子命令 argparse 新增 `--batch-only`（`action="store_true"`, `dest="batch_only"`）。
- `sdflow-issues/scripts/issues.py`
  - `cmd_sweep` 的子进程 triage 调用改为 `triage --batch-only --id X --批次 Y`（原行为：赋批次 +
    推进未分诊开放态 → 现行为：只赋批次，状态原样保留，由人工 triage 负责推进）。
- `sdflow-issues/SKILL.md`
  - triage 命令面说明（原 495-496 行区域）补充 `--batch-only` 语义。
  - sweep 协议描述（原 405-411、501-507 行区域）注明 sweep 固定走 `triage --batch-only`，
    只赋批次不推进状态，状态推进留给人工 triage。

## 测试

- `sdflow-issues/tests/test_buglist.py::TestTriage::test_batch_only_triage_does_not_promote_open_status`
  （新增）：`--batch-only` 触发 OPEN 项 → status 仍 OPEN + batch 已更新。
- `sdflow-issues/tests/test_todolist.py::TestTriage::test_batch_only_triage_does_not_promote_open_status`
  （新增）：同上，todo 池。
- `sdflow-issues/tests/test_buglist.py::TestTriage::test_open_item_triage_sets_proposed_and_batch`
  （既有，未改）：无 `--batch-only` 的直接 triage OPEN 项 → status 变 PROPOSED，验证原行为不变。
- `sdflow-issues/tests/test_issues.py::TestSweep::test_sweep_open_ungrouped`（改）：断言 sweep 后
  B1/T1（OPEN）、B2（IN_PROGRESS）status 均保持原状态，不再断言推进为 PROPOSED。
- `sdflow-issues/tests/test_issues.py::TestSweep::test_sweep_rerun_converges`（改）：同上，
  重跑收敛后 B1/B2 状态断言由 PROPOSED 改为 OPEN（原状态）。

TDD 过程：先加/改断言确认红（`--batch-only` 未识别报 argparse 错误；sweep 断言 PROPOSED≠OPEN 实际
仍是 PROPOSED），再实现代码使其转绿。

## 验证

| 层 | 命令 | 退出码 | SHA |
|---|---|---|---|
| unit | python3 -m pytest sdflow-issues/tests/ -x -v | 0 | badfa5fb1656b3616783c170ca4f8be92927a044 |

全量 673 passed, 7 skipped, 3 xfailed（含本 change 前置的 skipped/xfailed 用例，与本 task 无关）。

## 备注

- 本 worktree 的 git 历史不含 `harden-issues-read-write` 的 `tickets.md`（该文件仅存在于
  `feat/harden-issues-read-write` 分支 `68c74ae`，本 worktree 基于 `main` 分支的 `badfa5f`）；
  `openspec/changes/harden-issues-read-write/` 目录在本 worktree 内由本次任务新建（仅含
  `impl-reports/`），任务描述已由派发 prompt 完整给出（与主分支 `tickets.md` Task 3 段核对一致），
  未影响本票的实现范围。
- 改动面严格限定在 Global Constraints 声明的四类文件（core/issues.py/SKILL.md/测试），未触碰
  Task 1/2 涉及的 `_build_effective_snapshot`/`_count_index_items`/`validate_scan_envelope`。
