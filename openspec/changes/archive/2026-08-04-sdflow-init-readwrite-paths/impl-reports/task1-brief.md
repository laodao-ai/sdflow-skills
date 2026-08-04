### Task 1: T64 mkstemp 唯一名修复

**Blocked-by:** none
**R-ID:** —

将 `_atomic_write_settings()` 的 tmp 文件从固定名 `<settings>.tmp` 改为 `tempfile.mkstemp` 唯一名，关闭无锁降级路径下的并发撕裂窗口。mkstemp **MUST** 在外层 `try` 内（CR-1：mkstemp 底层 `open(O_CREAT|O_EXCL)` 权限拒绝/只读/满盘时抛 OSError，放在 try 外会击穿 fail-safe 契约）。内层 `try/except BaseException` 确保 mkstemp 成功后的残留 tmp 被清理。加 `flush()` + `os.fsync()` 对齐 `_atomic_write()` 风格（CR-7）。

- [ ] `_atomic_write_settings()` 使用 `tempfile.mkstemp` 替代固定名 tmp，mkstemp 在外层 try 内
- [ ] 测试：验证 tmp 文件名非固定（mock mkstemp 或检查 os.replace 被调用时的源路径前缀）
- [ ] 测试：mkstemp 失败时返回 False 而非裸抛（mock mkstemp 抛 OSError，断言返回 False）

