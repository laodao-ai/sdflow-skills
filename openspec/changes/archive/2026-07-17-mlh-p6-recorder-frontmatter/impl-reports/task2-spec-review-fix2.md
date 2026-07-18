# Task 2 Spec Re-review fix2 — semantic ID 与 repository snapshot lock

结论：**PASS**（commit `a4186936c6c791f28ec6a2ba6dc8975659eef3e6`；审查范围 `1177e10..a418693`；机械输入 `task2-review-package-fix2.diff`）。

## fix1 两个 Important 复核

### 1. invalid/expired participant fallback — 已修复

- 三份 `recorder_lock()` 均恢复批准语义：capability validation 失败不会进入 participant core，而是继续普通 top-level `O_CREAT|O_EXCL` acquire。
- repo 无 lock 时，bug/todo `scan --json` 与 issues `reindex` 均作为 owner 成功；repo 已有 lock 时均在业务 discovery/read 前以 `recorder lock occupied` fail-fast。
- 独立反例复跑：invalid token + 无 lock → exit 0、成功 JSON、退出后无残留 lock。
- 三份 lock/helper 继续由 mirror AST guard 约束；合法 nested delegation 与越级拒绝行为未回退。

### 2. barrier、init/update 与 Windows smoke contract — 已修复（按 ticket scope）

- reader↔writer 已改为 `multiprocessing` spawn + `Event` 的真实双进程双向 barrier；持锁期间实际 CLI contender 冲突，release 后成功。
- 两个 cooperative namespace producer 由独立 spawn 进程完成 read→pause→replace、竞争失败、release 后重新 acquire/read latest/write，最终两个 namespace 更新均保留。
- `sdflow-init.run()` 的 `init`/`update` 两路均有 integration matrix，覆盖 missing/existing/user-bytes/duplicate，并核对实际读取 canonical `runtime-gitignore.txt`。
- Windows local-disk smoke 是独立可执行测试文件，覆盖 acquire/conflict、真实 replace、sharing-violation fault 与 cleanup；非 Windows 以显式 platform skip 退出，未把 macOS 结果伪装为 Windows PASS，并拒绝 UNC temp path。
- actual Windows runner 执行明确属于 whole-change Task 5 的 `tasks.md 7.4`。Task 2 的 3.x ticket 要求在本轮交付可直接执行且不假绿的 smoke contract；没有条款要求在 Task 2/macOS 上提前产出 Windows 实机结果，因此不把 7.4 倒灌为本 ticket 阻断。

## Critical

无。

## Important

无。

## Minor

无。

## Verification

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task2_semantic_lock.py sdflow-init/tests/test_runtime_gitignore.py sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `46 passed, 1 skipped`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/test_runtime_gitignore.py -W error` → `338 passed, 1 skipped`。
- `python3 -m py_compile ...` 与严格 OpenSpec validate 均 PASS。
- implementation-scoped `git diff --check` PASS；完整区间只命中按编排要求原样纳入的固定旧审包 trailing whitespace，不属于本次实现或 Spec finding。

Task 2 的 semantic ID、exclusive snapshot lock、participant delegation、并发/fault/barrier、只读锁域与 runtime-ignore 合同，在本 ticket 范围内验收通过。Windows 实机结果由 Task 5 / `tasks.md 7.4` 执行并记录。
