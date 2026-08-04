---
impl-pipeline: tickets
---

## Global Constraints

- outside-voice.sh `--timeout` 校验 MUST 拒绝数值为零的输入（含 `0`/`00`/`000`），exit 2 与既有非法值行为一致（承重约束 C1）
- 出境截断阈值复用入境 OV_MAX_CONTEXT_BYTES（承重约束 C2）
- wc 失败时 fail-closed（强制截断 + stderr `OV_OUTPUT_SIZE_CHECK_FAILED=1`），不静默放行
- 截断按字节（`head -c`），不做 UTF-8 回扫（接受的边角，影响低）
- D3 (fake-timeout 非整数兼容) 已 WONTDO，不在实现范围内
- 测试跑法：`/usr/bin/python3 -m pytest sdflow-init/tests/`

### Task 1: --timeout 0 拒绝 + 专项测试

**Blocked-by:** none
**R-ID:** R1

在 outside-voice.sh 的 `--timeout` 参数解析中（L893-895 附近），既有纯数字校验 `''|*[!0-9]*)` 之后、`tmo="$2"` 赋值之前，加数值比较 `[ "$((10#$2))" -eq 0 ] && usage`。`10#` 强制十进制解析，正确捕获 `0`/`00`/`000` 等所有前导零变体。

在 test_outside_voice.py 中新增以下测试用例：
- `--timeout 0`、`--timeout 00`、`--timeout 000` 均 exit 2 且不启动 runner
- `--timeout 01` 等非零前导零值正常接受（不误拒）

- [x] `--timeout 0` exit 2（不启动 runner）
- [x] `--timeout 00` exit 2（不启动 runner）
- [x] `--timeout 000` exit 2（不启动 runner）
- [x] `--timeout 01` 正常接受、不报错
- [x] 既有 `--timeout` 正常值（如 300）行为不受影响

### Task 2: 出境 stdout 大小限制 + 专项测试

**Blocked-by:** none
**R-ID:** R2

在 outside-voice.sh 的 `do_exec` 函数中，`secret_scan_or_exit` 与 `cat "$workdir/last-message.md"` 之间（L831-832 附近），加出境大小检查：`wc -c` 取文件大小，超 `OV_MAX_CONTEXT_BYTES` 时用 `head -c` 截断 + stderr 告警 `OV_OUTPUT_TRUNCATED=1`；wc 失败时 fail-closed（case 校验空/非数字 → 强制截断 + stderr `OV_OUTPUT_SIZE_CHECK_FAILED=1`）。

在 test_outside_voice.py 中新增以下测试用例：
- 构造超 OV_MAX_CONTEXT_BYTES 的 `last-message.md`，断言 stdout 被截断到限长 + stderr 含 `OV_OUTPUT_TRUNCATED=1`
- 出境 stdout 恰好 = OV_MAX_CONTEXT_BYTES 时完整输出（无截断、无告警）

- [x] stdout 超限时被截断到 OV_MAX_CONTEXT_BYTES 字节
- [x] stderr 含 `OV_OUTPUT_TRUNCATED=1` 告警（含 original_bytes 和 limit）
- [x] stdout 恰好 = OV_MAX_CONTEXT_BYTES 时完整输出、无截断
- [x] wc 失败场景下 fail-closed（强制截断 + stderr `OV_OUTPUT_SIZE_CHECK_FAILED=1`）

### Task 3: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task3-verify.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [x] 单元测试证据齐全并通过
- [x] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [x] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
