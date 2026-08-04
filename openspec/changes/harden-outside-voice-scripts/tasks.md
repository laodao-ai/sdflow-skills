## 1. outside-voice.sh 修复

- [ ] 1.1 T176: `--timeout` 校验拒绝 0 — `outside-voice.sh:893` 在 `''|*[!0-9]*)` 后加 `0)` 分支，exit 2
- [ ] 1.2 T230: 出境 stdout 大小限制 — `outside-voice.sh:832` 附近，`cat last-message.md` 前加 `wc -c` 检查 + 超阈值 `head -c` 截断 + stderr 告警 `OV_OUTPUT_TRUNCATED=1`

## 2. 测试桩修复

- [ ] 2.1 T174: fake-timeout 非整数兼容 — `test_outside_voice.py:53` 的 `$(( sec * 10 ))` 改 `awk` 支持浮点数

## 3. 回归验证

- [ ] 3.1 全量测试通过 — `/usr/bin/python3 -m pytest sdflow-init/tests/` 全绿
