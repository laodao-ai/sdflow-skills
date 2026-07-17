# Task 2 Spec Review — semantic ID 与 repository snapshot lock

结论：**FAIL**（commit `9f9adc6427254030166f4ca00281081bec13cf33`；审查范围 `ec8c38c..9f9adc6`；机械输入 `task2-review-package.diff`）。

## Critical

无。

## Important

1. **lock metadata 写入短写/异常会把本进程自己的初始化锁永久遗留。** `recorder_lock()` 只调用一次 `os.write()` 且不校验返回长度；写入异常或 short write 后，`finally` 又要求当前 metadata 可完整解析且 token 匹配才允许 unlink。此时 inode 仍是本进程刚创建的 inode，却被误报为 `ownership lost` 并保留空白/部分 lock，后续全部权威命令只能人工 break-glass。独立 fault probe 对 `os.write` 注入 short write 与 `OSError` 均复现 `lock_exists=True`（内容分别为 `b'{"com'` 与 `b''`）。这违反 spec 的异常路径释放与 Task 3.5“无正常异常路径残留 lock”；应完整写 metadata（循环/`write_all`），并在 metadata 尚未完成时仅凭已打开 FD 的 identity 安全清理仍为自身 inode 的路径，同时继续保留真正替代锁。见三份镜像脚本 `recorder_lock()`（例如 `sdflow-buglist/scripts/buglist.py:149-192`）。

2. **只读命令仍在 lock 内格式化 JSON。** 三个 CLI 都用 `redirect_stdout(StringIO)` 包住整个 `args.func(args)`，仅把最终 `sys.stdout.write()` 移到 lock 外；`cmd_scan()` 的 `json.dumps()` 仍在锁内。独立 probe 在 `json.dumps` 入口观测到 `.recorder.lock` 存在。批准合同要求 immutable snapshot materialize 后先 release，再格式化/输出；当前实现只能避免慢 OS stdout 写入占锁，不能避免慢 JSON 格式化占锁。应让 read command 返回已固化 model，在 `with recorder_lock(...)` 外完成 render/serialization，并补 blocked-format/stdout 回归。见 `sdflow-buglist/scripts/buglist.py:1261-1311`、`sdflow-todolist/scripts/todolist.py:1235-1284`、`sdflow-issues/scripts/issues.py:1817-1827`。

3. **participant allowlist 是扁平全集，未约束“当前复合调用图”，越级委派可被接受。** `recorder_child_env()` 与 `validate_recorder_participant()` 只检查命令是否属于全局 allowlist、repo/token 是否匹配，不核对 owner command 或 parent→child edge。独立 probe 以 owner command=`scan` 获取 token，随后 `recorder_child_env('batch-rename', token)` 和 `validate_recorder_participant(..., 'batch-rename')` 均成功，违反 spec 对“属于当前复合调用图”与“越级委派不得进入 participant core”的要求。应编码允许的 delegation graph（如 `sweep→{scan,triage,batch-add,reindex}`、`reindex→scan`）并把已验证 parent command/chain 纳入校验。见三份镜像脚本 `RECORDER_PARTICIPANT_ALLOWLIST`、`validate_recorder_participant()`、`recorder_child_env()`（例如 `sdflow-issues/scripts/issues.py:81-86,147-155,241-250`）。

4. **Task 3.5–3.6 的强制验收矩阵没有交付，实施报告的 DONE/覆盖结论不可成立。** 新增 `test_task2_semantic_lock.py` 只有 7 个测试，未覆盖 reader↔writer 双向 barrier、`next-id` 释放后竞态、`sweep→reindex→scan` 嵌套委派、writer fault 在 CLI lock 域内的 cleanup、两个合规 namespace producer 的 document-lock barrier、blocked JSON formatting/stdout，且仓内没有 Windows local-FS acquire/conflict/replace/cleanup smoke/runner。现有 ownership-lost 与 20-process 用例不能替代这些逐项批准场景；其中缺失的 metadata fault、blocked-format、越级委派测试已经实际漏掉前三项违约。应补齐全部场景并记录 Windows smoke 证据后再把 Task 2 标为 DONE。见 `sdflow-buglist/tests/test_task2_semantic_lock.py:21-102`、`sdflow-init/tests/test_runtime_gitignore.py:14-30`。

## Minor

无。

## 已通过的核对

- canonical ASCII ID、Unicode digit 拒绝、跨 bug/todo semantic 冲突及 repository-wide `next-id/add` inventory 的主路径成立。
- `scan/next-id/add/set-status/triage/reindex/sweep/batch lint/add/set-status/rename` 的 CLI dispatch 均进入 repository lock；runtime ignore canonical asset、init/update 共用 merge path与 dogfood 单条落盘存在。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/test_runtime_gitignore.py -W error` → `308 passed`。
- `python3 -m py_compile ...`、`git diff --check ec8c38c..9f9adc6`、两处 runtime-ignore 精确单条检查均 PASS。

修复以上 Important 并补齐批准的并发/故障/平台验收后，Task 2 才可 PASS。
