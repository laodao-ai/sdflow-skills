# Task 2 Spec Re-review fix1 — semantic ID 与 repository snapshot lock

结论：**FAIL**（commit `1177e1007c66b534bf8d535bb70cde165e92a306`；审查范围 `9f9adc6..1177e10`；机械输入 `task2-review-package-fix1.diff`）。

## 上轮 4 个 Important 复核

- **已修复：metadata short write/异常遗留 lock。** 三份 `recorder_lock()` 现用 `_write_all()` 完整写 metadata；publish 前 write/fsync/close fault 按创建时 file identity 清理自身 inode，publish 后仍用 identity+token 保留 replacement lock。三向 short-write 与 fault probe 通过。
- **已修复：只读 JSON 格式化仍在锁内。** bug/todo `scan`、`next-id` 与 issues `batch lint` 已拆成锁内 snapshot 与锁外 render；serialization/stdout probe 均观察到 lock 已释放，render 只消费内存 snapshot。
- **已修复原问题，但引入新违约：delegation graph 已落地。** `sweep→{scan,triage,batch-add,reindex}`、`reindex→scan`、`batch-rename→scan` 逐边校验有效，原 `scan→batch-rename` 越级路径已拒绝；但 invalid/expired participant 的 fallback 语义被错误收紧，见 Important 1。
- **部分闭合：批准验收矩阵。** 20-process、metadata/target writer faults、ownership-lost、next-id race、nested delegation、blocked render/stdout 已补；真实 Windows smoke 与严格 barrier/integration 证据仍未完成，见 Important 2。

## Critical

无。

## Important

1. **伪造/过期 participant token 不再按顶层调用正常 acquire，违反批准场景。** `recorder_lock()` 现在只要环境中存在 `SDFLOW_RECORDER_LOCK_TOKEN` 就直接调用 `validate_recorder_participant()`，失败立即退出；此前的 owner fallback 被完全删除。最小复现：repo 无 lock、环境 token=`expired` 时，独立 `scan --json` 返回 exit 2，且未尝试创建 owner lock。批准 spec 的“伪造或过期 participant token 被拒”场景明确要求：不得进入 participant core，随后**按顶层调用正常 acquire**，仅当 lock 仍存在时才在业务读写前失败。应把 participant validation failure 转为清除 capability 后的正常 owner acquire（同时保持当前 chain/edge 校验不允许进入 participant core），并用“无 lock 可成为 owner / 有 lock fail-fast”双分支回归替换当前 `test_invalid_participant_env_cannot_upgrade_to_owner`。见 `specs/spec-workflow/spec.md:219-221`、三份脚本 `recorder_lock()`（如 `sdflow-buglist/scripts/buglist.py:179-193`）、`sdflow-buglist/tests/test_task2_semantic_lock.py:145-155`。

2. **Task 3.5–3.6 的强制验收矩阵仍未闭合。** 修复报告明确承认没有 Windows runner，因而没有批准合同要求的 Windows local-FS acquire/conflict/replace/cleanup 实机 smoke；“temp handle 已关闭”的 macOS contract test 不能替代 Windows sharing-violation 行为。新增所谓 reader↔writer “barrier”也只是同一进程内嵌套两个 `recorder_lock()`，shared producer 用例是两段顺序 acquire/read/write；两者都没有 barrier/event 暂停真实 reader/producer 并启动竞争进程，不能证明 command 的 discovery/read/replace 时序。runtime ignore 测试仍只直调 helper，没有分别走 `run(init)`/`run(update)` 验证缺失/已有/重复/用户 bytes 契约。应补真实双进程 barrier、init/update integration，以及 Windows local-disk smoke 结果后再把 Task 2 标为 DONE。见 `tasks.md:26-27`、`specs/spec-workflow/spec.md:247-273`、`sdflow-buglist/tests/test_task2_semantic_lock.py:238-285`、`sdflow-init/tests/test_runtime_gitignore.py:14-93`。

## Minor

无。

## Verification

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task2_semantic_lock.py sdflow-init/tests/test_runtime_gitignore.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `36 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/test_runtime_gitignore.py -W error` → `328 passed`。
- `python3 -m py_compile ...`、严格 OpenSpec validate、排除固定旧审包后的 `git diff --check` 均 PASS。
- 独立反例确认 invalid token + 无 lock 仍 exit 2；未进入 owner acquisition。

修复 invalid-token owner fallback，并补齐真实 barrier、init/update 与 Windows smoke 后，Task 2 才可 PASS。
