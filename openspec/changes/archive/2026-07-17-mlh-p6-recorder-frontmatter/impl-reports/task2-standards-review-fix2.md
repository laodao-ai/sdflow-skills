# Task 2 fix2 Standards Re-review — participant fallback / verification matrix

结论：**PASS（commit `a4186936c6c791f28ec6a2ba6dc8975659eef3e6`，复核区间 `1177e10..a418693`）**

未发现新的 Critical / Important。上一轮 three-way parity Minor 已按规则记录为 T151，本轮不重复要求实现。

## 重点复核

### invalid-token owner fallback — PASS

- 三份 `recorder_lock()` 保持 AST 等价：participant validation 失败只是不进入 participant core，随后按普通 top-level `O_CREAT|O_EXCL` 竞争；已有 owner lock 时仍在业务 discovery/read 前 conflict。
- 独立真实 CLI probe：expired token 对空 repo `scan --json` exit 0 且正常释放 lock；同 token 在另一个 owner 持锁时 exit 2，stderr 含 `recorder lock occupied`。
- bug/todo/issues 三份 CLI 双分支参数化测试通过；delegation graph 的合法嵌套与越级拒绝逻辑未被 fallback 改坏。

### multiprocessing barrier — PASS

- `test_reader_writer_barrier_is_bidirectional_across_processes` 使用 `spawn` + `Event` 真正暂停持锁 reader/writer：竞争 CLI 在持锁期失败，release 后成功；writer snapshot 后 replace 的最终 bytes 也被核验。
- 两 namespace producer 用三个独立 spawn 进程验证：A read→replace 窗口内 B conflict；A release 后 B 重新 acquire，明确观察 A 最新 bytes 后再写，最终两个更新均保留。
- 这不再是上一轮同进程嵌套/顺序 acquire 的假 barrier。

### init/update integration — PASS

- `test_run_init_and_update_use_canonical_runtime_merge` 覆盖 `init` / `update` × missing / existing / user-bytes / duplicate 共 8 组。
- 测试通过真实 `run()` 读取 canonical `runtime-gitignore.txt` 并调用真实 atomic merge；仅 stub 无关 bundle/hook/inject 操作。单条幂等、用户 bytes 保留与 duplicate fail-closed 均有最终 bytes 断言。
- 独立执行该 integration 参数矩阵：`8 passed`。

### Windows-only smoke contract — PASS（合同已落，实机证据留 Task 5）

- `test_task2_windows_local_fs_smoke.py` 仅在 `sys.platform == "win32"` 收集执行，非 Windows 明确 skip；当前 macOS 的 skip 未被当成 Windows PASS。
- 合同覆盖 local path guard、lock acquire/conflict/cleanup、CRLF `.gitignore` replace，以及 simulated sharing-violation 时旧 bytes 与 tmp cleanup；文档给出 Task 5 actual Windows runner 的单文件命令。
- fix2 报告明确状态为“本 ticket DONE，Windows 实机执行留 Task 5”，没有伪报当前平台已完成 Windows smoke。

## Critical

无。

## Important

无。

## Minor

### 1. fix2 报告的 `git diff --check` 记录未注明机械审包例外

- 报告写 `git diff --check → PASS`，但实际对 `1177e10..a418693` 全区间执行会因新纳入的 `task2-review-package-fix1.diff` 中机械保真的 `+ ` 行失败。
- 排除该固定审计输入后，implementation/report/todolist diff 的 `git diff --check` 通过；不影响运行时实现，但验证记录应沿用 fix1 的显式 exclude 说明，避免把未执行成功的命令记为 PASS。

## 领域清单

领域清单未覆盖：无匹配 Python CLI checklist。规则根为 `/Users/cheneyzhao/.sdflow/workflow`，现有 domains 仅 backend、backend-go、embedded、embedded-esp32、embedded-ml307c；本轮未静默宣称领域清单通过，按仓内标准、目标规格与 Fowler 级可维护性复核。

## Verification

- 固定输入：`task2-review-package-fix2.diff`（169,306 bytes）与 `task2-semantic-id-lock-fix2.md`。
- 定向矩阵：`46 passed, 1 skipped`；唯一 skip 为 actual Windows local-disk smoke。
- 受影响全套：`338 passed, 1 skipped`。
- 全仓：`1499 passed, 1 skipped`。
- init/update integration 单跑：`8 passed`。
- 独立 fallback probe：空仓 exit 0 / no lock residue；已有 owner 时 exit 2 / occupied。
- `python3 -m py_compile ...` 与 `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive`：PASS / valid。
- `git diff --check 1177e10..a418693`：因机械审包 trailing whitespace 失败；排除 `task2-review-package-fix1.diff` 后 PASS。
