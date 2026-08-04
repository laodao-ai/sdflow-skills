# Hand-off: harden-outside-voice-scripts

**日期**：2026-08-05

## ✅ 完成了什么

- **T176 `--timeout 0` 拒绝**：`outside-voice.sh:916` 加 `[ "$((10#$2))" -eq 0 ] && usage`，正确捕获 `0`/`00`/`000` 等所有前导零变体（锚：`test_usage_exec_timeout_zero_exit2` 3 条参数化 + `test_exec_timeout_leading_zero_accepted` + `test_exec_timeout_normal_value_unaffected`）
- **T230 出境 stdout 大小限制**：`outside-voice.sh:839-851` 加 wc-c 检查 + head-c 截断 + fail-closed（锚：`test_exec_output_truncated_over_limit` + `test_exec_output_exact_limit_not_truncated` + `test_exec_output_wc_failure_fails_closed`）
- **stderr 契约补登记**：`outside-voice.sh:143-146` 补 `OV_OUTPUT_TRUNCATED=1` 和 `OV_OUTPUT_SIZE_CHECK_FAILED=1` 两条新信号
- **聚合回归**：788 passed, 4 skipped @ `014ad8a`（锚：`impl-reports/task3-verify.md`）

## ⏳ 未完成 / 延后

- 无 defer 项（code-review 0 采纳）
- 无未闭合 bug/todo（issues scan 返回空）
- **T174 WONTDO**：fake-timeout 非整数兼容——不可达路径 + awk 截断引入新语义错误，设计门拍板不做

## ▶ 下一阶段建议

- T227（worker 信号转发）已退回延后池，若要做需独立开 change 过设计门
- 出境截断的 UTF-8 回扫（spec-review 接受的边角）——影响低（末尾 1-3 字节 + `errors="replace"` 兜底），可在下一批加固中择机补
