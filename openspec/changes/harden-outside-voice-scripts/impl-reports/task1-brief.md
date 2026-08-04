### Task 1: --timeout 0 拒绝 + 专项测试

**Blocked-by:** none
**R-ID:** R1

在 outside-voice.sh 的 `--timeout` 参数解析中（L893-895 附近），既有纯数字校验 `''|*[!0-9]*)` 之后、`tmo="$2"` 赋值之前，加数值比较 `[ "$((10#$2))" -eq 0 ] && usage`。`10#` 强制十进制解析，正确捕获 `0`/`00`/`000` 等所有前导零变体。

在 test_outside_voice.py 中新增以下测试用例：
- `--timeout 0`、`--timeout 00`、`--timeout 000` 均 exit 2 且不启动 runner
- `--timeout 01` 等非零前导零值正常接受（不误拒）

- [ ] `--timeout 0` exit 2（不启动 runner）
- [ ] `--timeout 00` exit 2（不启动 runner）
- [ ] `--timeout 000` exit 2（不启动 runner）
- [ ] `--timeout 01` 正常接受、不报错
- [ ] 既有 `--timeout` 正常值（如 300）行为不受影响

