# Task 2 fix1 — semantic ID 与 repository snapshot lock 修复报告

状态：DONE

## 修复结论

- 三份 recorder 的 `recorder_lock()` 以 AST 等价实现 metadata write-all；metadata publish 前的 `write/fsync/close` 异常按已打开 FD 的 file identity 清理本进程创建的 inode，publish 后仍以 identity + token 终检并保留 replacement lock。
- participant env 只要存在即进入 capability validation；空、伪造、过期、跨 repo、缺 delegation chain 或非法 edge 全部 fail-closed，不再静默升级为 owner。
- capability 携带从 lock owner command 开始的 delegation chain，并逐边校验批准图：`sweep → {scan,triage,batch-add,reindex}`、`reindex → scan`、`batch-rename → scan`。已验证真实 `sweep → reindex → bug/todo scan`，越级 `scan/sweep → batch-rename` 拒绝。
- bug/todo `scan`、`next-id` 与 issues `batch lint` 先在锁内固化只读 snapshot，再在锁外 render/JSON serialization/stdout；mutation 仍持锁到最后写入完成。
- `merge_runtime_gitignore()` 改为同目录唯一 tempfile，完整 binary write + flush/fsync + mode 对齐后 `os.replace`；write/replace fault 时原 `.gitignore` bytes 不变且 tmp 清理。
- 三份 recorder 保持自包含；`_write_all` 纳入 THREE_WAY AST roster。未实现 reviewer 的 Minor（共享常量/class AST 扩面）。

## TDD 红 → 绿

- 首轮新增 seam 测试：`11 failed, 10 passed`。红项逐一复现 metadata short/raise 遗锁、非法 token 升 owner、delegation graph 缺失、锁内 JSON serialization 与 `.gitignore` 非原子写。
- 实现后最终 Task 2 定向矩阵：`36 passed`。覆盖：
  - 三向 short write/write failure，另有 fsync/close publication fault；
  - partial metadata、ownership-lost/replacement preservation、reader↔writer 双向 barrier；
  - 20-process add 成功 ID 唯一且最终盘面等于全部成功集合；
  - next-id 释放后竞态、非法 participant CLI、nested delegation 与越级伪造；
  - blocked JSON render/stdout 时 lock 已释放且输出不再读文件；
  - CLI writer fault 后旧目标不变、lock 无残留；
  - 两个 cooperative namespace producer 顺序 acquire 后保留彼此更新；
  - runtime ignore write/replace fault 与 closed-temp-handle replace contract。

## 验证

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task2_semantic_lock.py sdflow-init/tests/test_runtime_gitignore.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `36 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/test_runtime_gitignore.py -W error` → `328 passed`。
- `uv run --with pytest pytest -q` → `1489 passed`。
- `uv run --with pytest pytest -q -W error` → `1451 passed, 38 failed`；38 项均是本 diff 范围外既存 ResourceWarning：`sdflow-maintain` 的未关闭 `open(...).read()` 37 项、`sdflow-architecture` 并发 subprocess pipe 1 项。Task 2 相关套件在 `-W error` 下全绿。
- `python3 -m py_compile sdflow-buglist/scripts/buglist.py sdflow-todolist/scripts/todolist.py sdflow-issues/scripts/issues.py sdflow-init/scripts/init.py` → PASS。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid。
- `git diff --cached --check -- . ':(exclude)openspec/changes/mlh-p6-recorder-frontmatter/impl-reports/task2-review-package.diff'` → PASS。编排层要求原样纳入的固定审计输入 `task2-review-package.diff` 自带 `+ ` trailing-whitespace 行，未覆盖或清洗。
- `.gitignore` 与 canonical `runtime-gitignore.txt` 中 `/openspec/issues/.recorder.lock` 各恰好 `1` 条。

## 平台边界

本机为 macOS local filesystem，已执行 POSIX release gate；没有可用 Windows runner，故未伪报 Windows 实机 smoke。测试已锁定 Windows-compatible local-FS 合同：仅使用 stdlib `O_CREAT|O_EXCL`/`os.replace`，replace 前 tempfile handle 已关闭，sharing/replace failure 保持旧文件。Windows local-disk 实机 smoke 仍可复用同一测试；network/userspace filesystem 与 power-loss durability 继续明确不在承诺内。
