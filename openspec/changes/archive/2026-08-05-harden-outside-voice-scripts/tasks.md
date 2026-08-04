## 1. outside-voice.sh 修复

- [x] 1.1 T176: `--timeout` 校验拒绝 0 — `outside-voice.sh:893` 在 `''|*[!0-9]*)` 后加 `0)` 分支，exit 2
- [x] 1.2 T230: 出境 stdout 大小限制 — `outside-voice.sh:832` 附近，`cat last-message.md` 前加 `wc -c` 检查 + 超阈值 `head -c` 截断 + stderr 告警 `OV_OUTPUT_TRUNCATED=1`

## 2. 新代码路径专项测试 [spec-review-amendment]

- [x] 2.1 T176 测试: `--timeout 0` / `--timeout 00` / `--timeout 000` 均 exit 2，且不启动 runner
- [x] 2.2 T176 兼容性: `--timeout 01` 等非零前导零值正常接受（不误拒）
- [x] 2.3 T230 测试: 构造超 OV_MAX_CONTEXT_BYTES 的 `last-message.md`，断言 stdout 被截断到限长 + stderr 含 `OV_OUTPUT_TRUNCATED=1`
- [x] 2.4 T230 边界: 出境 stdout = OV_MAX_CONTEXT_BYTES 时完整输出（无截断、无告警）

## 3. 回归验证

- [x] 3.1 全量测试通过 — `/usr/bin/python3 -m pytest sdflow-init/tests/` 全绿
