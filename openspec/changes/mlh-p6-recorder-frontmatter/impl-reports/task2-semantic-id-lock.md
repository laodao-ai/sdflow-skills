# Task 2 — semantic ID 与 repository snapshot lock 实现报告

状态：DONE

## 范围与结论

- 三个 recorder 脚本各自内联、AST 等价地实现 canonical ASCII ID、semantic key、repository snapshot discovery、`O_CREAT|O_EXCL` lock、participant token 校验、owner identity/token 终检与受控 child env；生产脚本之间未新增跨 import。
- bug/todo `scan` 以单次 repository snapshot 读取两池 dated 文件；`next-id`、自动/显式 `add` 在同一锁域使用同一 semantic inventory。自定义单字母 ASCII prefix 保留，`A007`/`A7`、Unicode digits 与跨池复用均 fail-closed。
- bug/todo `scan/next-id/add/set-status/triage` 与 issues `reindex/sweep/batch lint/add/set-status/rename` 的 CLI dispatch 全部在仓级 exclusive lock 内；stdout 先捕获为内存结果，释放 lock 后才写出，慢 consumer 不延长锁域。
- issues 复合命令只给 allowlist recorder child 转发同 repo token；participant 校验后不二次 acquire/release。非 allowlist child env 剥离 token；伪造、过期、cross-repo、partial metadata 与 ownership-lost 均 fail-loud，错误不输出 token且给出精确 break-glass 路径。
- 新增 canonical `sdflow-init/assets/snippets/runtime-gitignore.txt` 与 `merge_runtime_gitignore()`；init/update 共用的 `run()` 路径幂等合并，重复条目 fail-closed、其它用户 bytes 保留。本仓 `.gitignore` 对应条目恰一条。

## TDD 与故障验收

- 先落 `test_task2_semantic_lock.py` 红测；初次运行 `4 failed`（缺 canonical/lock helper），实现后转绿。
- 新增 20 个并发进程 `add --prefix A`：所有成功 ID 唯一；竞争失败均明确为 `recorder lock occupied`；无正常路径 lock 残留。
- 覆盖 owner/participant、伪造 token、cross-repo、非 allowlist、partial metadata 初始化窗口、replacement lock ownership-lost 与 replacement lock 保留。
- 既有 atomic-write 定向套件继续覆盖 temp write/chmod/replace 异常时旧 bytes/mode 保持与 tmp 清理；本任务未削弱原原子替换协议。
- runtime ignore 覆盖 CRLF 用户 bytes、二次调用 byte-noop、重复条目拒绝且文件不变。

## 验证

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task2_semantic_lock.py -W error`：`7 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/test_runtime_gitignore.py -W error`：见本次实现终检，全部通过。
- `python3 -m py_compile sdflow-buglist/scripts/buglist.py sdflow-todolist/scripts/todolist.py sdflow-issues/scripts/issues.py sdflow-init/scripts/init.py`：PASS。
- `git diff --check`：PASS。
- dogfood/asset 精确行检查：两处各 `1` 条 `/openspec/issues/.recorder.lock`。

## 边界

- lock 是 cooperative protocol；不阻止编辑器、Git 或绕协议 producer。普通 path API 的 identity/token 终检与 unlink 之间仍有非 cooperative TOCTOU residual。
- local filesystem 是本实现保证边界；network/userspace FS 不承诺。`os.replace` 未扩展为完整 file+directory fsync，power-loss durability 不在本任务承诺内。
- legacy alias 的最终 frontmatter/marker promotion 由后续 Task 3 writer 落盘；本任务已焊死 semantic 定位、冲突与 canonical 新写前置条件。
