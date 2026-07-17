# Task 2 fix2 — participant fallback 与验收矩阵修复报告

状态：DONE（本 ticket 范围；Windows 实机执行留在 Task 5 final verification）

## 修复结论

- 三份 recorder 保持 AST 等价：participant capability validation 失败不会进入 participant core，而是回到普通 top-level `O_CREAT|O_EXCL` acquire。repo 无 lock 时调用成为 owner；repo 有 lock 时在任何业务 discovery/read 前以 `recorder lock occupied` fail-fast。
- invalid/expired participant 使用三份真实 CLI 双分支验证：bug/todo `scan --json` 与 issues `reindex` 在空仓均 owner-success，在已有 owner lock 时均 conflict。
- 原同进程嵌套锁测试升级为 `multiprocessing` spawn + `Event` 的真实双进程 barrier：reader 持锁暂停时 writer CLI 冲突、writer 持锁且已读取 snapshot 后 reader CLI 冲突，两端 release 后 contender 均成功。
- shared document producer 用两个独立 spawn 进程验证：producer A 在 read→replace 之间暂停，producer B 首次 acquire 冲突；A release/replace 后 B 重试 acquire，并明确观察到包含 A 更新的最新 bytes 后再写入，最终两个 namespace 更新均保留。
- `init.py::run()` 以 stub 掉无关 bundle/global-hook 操作的集成测试覆盖 `init`/`update` 两路 × 缺失/已有/重复/user-bytes 四种 `.gitignore` 盘面；两路均实际读取 canonical `runtime-gitignore.txt` 并调用 merge，重复 fail-closed、其它 bytes 保留。
- 新增 Windows-only local-disk smoke runner contract：`sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py`。非 Windows 明确 skip，不能计为实机证据；Task 5 在 actual Windows local drive 直接执行该文件，验证 acquire/conflict/replace/cleanup 与 sharing-violation 原文件保留。
- 按要求未实现 Standards Minor；T151 由编排层落盘且未修改内容。

## TDD 红 → 绿

- 红测：`3 failed, 36 passed, 1 skipped`；三项失败分别是 bug/todo/issues invalid participant 在无 lock 时仍直接 exit 2，准确复现 reviewer Important 1。
- 修复后定向矩阵：`46 passed, 1 skipped`；skip 仅为 actual Windows local-disk smoke，当前 macOS host 未伪报 Windows PASS。

## 验证

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task2_semantic_lock.py sdflow-init/tests/test_runtime_gitignore.py sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `46 passed, 1 skipped`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/test_runtime_gitignore.py -W error` → `338 passed, 1 skipped`。
- `uv run --with pytest pytest -q` → PASS（按本次新增测试计数为 `1499 passed, 1 skipped`；唯一 skip 同上）。
- `python3 -m py_compile sdflow-buglist/scripts/buglist.py sdflow-todolist/scripts/todolist.py sdflow-issues/scripts/issues.py sdflow-init/scripts/init.py` → PASS。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid。
- `git diff --check` → PASS。

## Windows Task 5 执行合同

当前环境没有 Windows runner，MUST NOT 制造或声称实机 PASS。Task 5 / `tasks.md 7.4` 应在 actual Windows local-disk runner 执行：

```powershell
py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error
```

runner 的 pytest temp path 若是 UNC/network path，测试会失败而不是 skip/假绿；network/userspace filesystem 与 power-loss durability 仍不在承诺内。
