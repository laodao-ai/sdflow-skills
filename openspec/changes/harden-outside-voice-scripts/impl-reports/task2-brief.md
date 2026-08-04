### Task 2: 出境 stdout 大小限制 + 专项测试

**Blocked-by:** none
**R-ID:** R2

在 outside-voice.sh 的 `do_exec` 函数中，`secret_scan_or_exit` 与 `cat "$workdir/last-message.md"` 之间（L831-832 附近），加出境大小检查：`wc -c` 取文件大小，超 `OV_MAX_CONTEXT_BYTES` 时用 `head -c` 截断 + stderr 告警 `OV_OUTPUT_TRUNCATED=1`；wc 失败时 fail-closed（case 校验空/非数字 → 强制截断 + stderr `OV_OUTPUT_SIZE_CHECK_FAILED=1`）。

在 test_outside_voice.py 中新增以下测试用例：
- 构造超 OV_MAX_CONTEXT_BYTES 的 `last-message.md`，断言 stdout 被截断到限长 + stderr 含 `OV_OUTPUT_TRUNCATED=1`
- 出境 stdout 恰好 = OV_MAX_CONTEXT_BYTES 时完整输出（无截断、无告警）

- [ ] stdout 超限时被截断到 OV_MAX_CONTEXT_BYTES 字节
- [ ] stderr 含 `OV_OUTPUT_TRUNCATED=1` 告警（含 original_bytes 和 limit）
- [ ] stdout 恰好 = OV_MAX_CONTEXT_BYTES 时完整输出、无截断
- [ ] wc 失败场景下 fail-closed（强制截断 + stderr `OV_OUTPUT_SIZE_CHECK_FAILED=1`）

