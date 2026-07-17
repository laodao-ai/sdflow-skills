# Task 2 fix1 Standards Re-review — semantic ID / repository lock

结论：**PASS（commit `1177e1007c66b534bf8d535bb70cde165e92a306`，复核区间 `9f9adc6..1177e10`）**

上一轮 5 个 Important 均已关闭；未发现新的 Critical / Important。上一轮 three-way guard 的 Minor 按要求保留，不阻断本轮 PASS。

## 上轮 Important 逐项复核

### 1. lock metadata 初始化失败遗留 stale lock — CLOSED

- `sdflow-buglist/scripts/buglist.py:169-228`（三向 AST 等价）新增 `_write_all()` 与 `metadata_published` 分阶段 cleanup：short write 会继续写；publish 前 write/fsync/close 异常按已记录 inode identity 删除本进程 lock；publish 后仍要求 identity + token 才 unlink replacement-sensitive lock。
- 独立 fault probe 将 `os.write` 强制抛 `OSError("probe write failed")`：原始 `OSError` 未被 ownership-lost 覆盖，`.recorder.lock` 不存在。
- 回归覆盖三脚本 short write、write failure、fsync/close fault、partial metadata 与 replacement preservation。

### 2. invalid participant token 静默升级 owner — CLOSED

- `sdflow-buglist/scripts/buglist.py:148-186,268-283`（三向镜像）以环境变量 presence 作为 participant attempt：只要 `SDFLOW_RECORDER_LOCK_TOKEN` 在 env 中，validation 失败直接传播，不再 fallback acquire。
- 新增 delegation chain 与逐边批准图；真实 `sweep → reindex → scan` 成功，越级 edge 与 malformed/mismatched chain 拒绝。
- 独立 CLI probe 使用 expired token：exit 2，stderr 为 `invalid recorder participant`，且无 lock 残留。

### 3. read-only lock 包住 JSON render — CLOSED

- `sdflow-buglist/scripts/buglist.py:1373-1379` 与 todolist 对应路径把 `scan` / `next-id` 拆为 lock 内 snapshot、lock 外 render；`sdflow-issues/scripts/issues.py:1875-1878` 对 `batch-lint` 同样拆分。mutation 仍走原持锁 dispatch。
- 独立 monkeypatch probe 在 recorder result `json.dumps` 入口观测 `.recorder.lock`：`[False]`；blocked stdout 回归也断言所有 write 均发生在 unlock 后。

### 4. runtime `.gitignore` 非原子截断写 — CLOSED

- `sdflow-init/scripts/init.py:90-135` 改为同目录 `mkstemp`，完整 binary write + flush/fsync、mode 对齐、关闭 handle 后 `os.replace`，finally 清 tmp。
- write/replace fault 回归均验证 original bytes 不变且无 tmp 残留；closed-temp-handle replace contract 已单测。

### 5. 测试证据不足 — CLOSED

- Task 2 定向矩阵现为 36 cases，覆盖上一轮点名的 metadata short/raise/fsync/close、invalid-token CLI、nested delegation/越级拒绝、reader↔writer barrier、render/stdout release ordering、20-process 最终盘面、writer fault、cooperative document lock 与 `.gitignore` write/replace failure。
- 20-process 用例现额外 scan 最终盘面，要求落盘 ID 集合精确等于所有成功返回 ID，不再只检查返回值唯一。
- 实际执行定向、受影响全套与全仓套件均通过，证据与 fix1 报告一致。

## Critical

无。

## Important

无。

## Minor

### 1. three-way AST guard 仍不保护共享常量与 class 定义（保留项）

- `sdflow-buglist/tests/test_mirror_consistency.py:64-77` 已把 `_write_all` 加入 helper roster，但仍未显式比较 `RECORDER_LOCK_ENV`、`RECORDER_DELEGATION_CHAIN_ENV`、`RECORDER_PARTICIPANT_ALLOWLIST`、`RECORDER_DELEGATION_GRAPH`、`CANONICAL_ID_RE` 的值，也未比较 `RecorderLockState` / `RecorderLockError` class AST。
- 当前三份值与类型定义一致；这是未来防漂移完整性问题，本轮按要求不阻断实现。

## 领域清单

领域清单未覆盖：无匹配 Python CLI checklist。规则根为 `/Users/cheneyzhao/.sdflow/workflow`，现有 domains 仅 backend、backend-go、embedded、embedded-esp32、embedded-ml307c；本轮未静默宣称领域清单通过，按仓内标准、目标规格与 Fowler 级可维护性复核。

## Verification

- 固定输入：`task2-review-package-fix1.diff`（133,484 bytes）与 `task2-semantic-id-lock-fix1.md`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task2_semantic_lock.py sdflow-init/tests/test_runtime_gitignore.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `36 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/test_runtime_gitignore.py -W error` → `328 passed`。
- `uv run --with pytest pytest -q` → `1489 passed`。
- 独立 probes：metadata write fault → 原始 `OSError` + no lock；expired participant token → exit 2 + no lock；scan JSON serialization → lock observed `[False]`。
