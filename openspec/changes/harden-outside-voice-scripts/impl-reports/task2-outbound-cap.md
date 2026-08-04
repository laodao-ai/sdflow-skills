### Task 2: 出境 stdout 大小限制 + 专项测试 — impl report

**R-ID:** R2 · **Blocked-by:** none

## 改了什么

`sdflow-init/assets/hack/outside-voice.sh` 的 `do_exec` 函数，在 `secret_scan_or_exit
"$workdir/last-message.md"`（原 L831）与 `cat "$workdir/last-message.md"`（原 L832）之间，
按 `design.md` D2 节的代码原样加出境大小检查：

```bash
ov_outsize=$(wc -c 2>/dev/null < "$workdir/last-message.md" | tr -d ' ')
case "${ov_outsize:-}" in
  ''|*[!0-9]*)
    echo "OV_OUTPUT_SIZE_CHECK_FAILED=1" >&2
    ov_outsize="$((OV_MAX_CONTEXT_BYTES + 1))"
    ;;
esac
if [ "$ov_outsize" -gt "$OV_MAX_CONTEXT_BYTES" ]; then
    echo "OV_OUTPUT_TRUNCATED=1 original_bytes=$ov_outsize limit=$OV_MAX_CONTEXT_BYTES" >&2
    head -c "$OV_MAX_CONTEXT_BYTES" "$workdir/last-message.md"
else
    cat "$workdir/last-message.md"
fi
```

- 复用入境同一个 `OV_MAX_CONTEXT_BYTES`（承重约束 C2），不新增独立出境上限变量。
- `wc -c` 读取失败（空输出或非数字）时 fail-closed：不静默放行整份未知大小的输出，
  强制把 `ov_outsize` 置为 `OV_MAX_CONTEXT_BYTES + 1`（必然触发截断分支）+ 打
  `OV_OUTPUT_SIZE_CHECK_FAILED=1` 到 stderr。
- 截断按字节（`head -c`），不做 UTF-8 回扫（design D2 已接受的边角，影响低）。
- `ov_outsize` 加进 `do_exec` 顶部既有的 `local` 声明列表，避免泄漏为全局变量。

## 测试

`sdflow-init/tests/test_outside_voice.py` 新增 3 条用例（放在 D2 专属小节，紧跟既有的
「出境侧 secret_scan」用例之后）：

1. `test_exec_output_truncated_over_limit` — 假 codex 产出 5000 字节、`OV_MAX_CONTEXT_BYTES=1000`，
   断言 stdout 恰好截到 1000 字节且内容正确，stderr 含
   `OV_OUTPUT_TRUNCATED=1 original_bytes=5000 limit=1000`。
2. `test_exec_output_exact_limit_not_truncated` — 假 codex 产出恰好 1000 字节、上限同为 1000，
   断言完整输出、stderr 不含 `OV_OUTPUT_TRUNCATED`（边界不算超限）。
3. `test_exec_output_wc_failure_fails_closed` — 用一个有状态的假 `wc`（PATH 前置）：第 1 次调用
   （`render_prompt` 的入境 ctx 体积检查）正常放行，第 2 次调用（本 change 的出境检查）模拟失败
   （空输出、非零退出），断言 stderr 含 `OV_OUTPUT_SIZE_CHECK_FAILED=1` 且同时触发
   `OV_OUTPUT_TRUNCATED=1`（fail-closed 分支强制截断），stdout ≤ 上限。
   注：真实文件不可读场景已被更早的 `secret_scan_or_exit`（用 `grep` 读文件）挡住并以不同
   路径 exit 2/3，故本用例改用假 `wc` 模拟「文件可读但 `wc` 本身失败」（资源耗尽/竞态类）的场景，
   这正是 fail-closed 分支要覆盖的现实触发点。

配套：`make_fake_codex` 新增 `big_output` 模式（`FAKE_CODEX_OUTPUT_BYTES` 控制字节数，
`head -c N /dev/zero | tr '\0' 'A'` 产出精确字节数、无换行，便于边界断言）。

### Red-before-green 核验

新增/修改断言前先破坏被测点确认真红：`git stash` 暂存脚本改动（只留测试改动），跑新增 3 条用例——
`test_exec_output_truncated_over_limit` 与 `test_exec_output_wc_failure_fails_closed` 均按预期
FAIL（未截断/未 fail-closed）；`test_exec_output_exact_limit_not_truncated`
在无检查的旧代码下也天然通过（边界值不截断时 cat 全量 = 截断后仍是全量，此用例本身是
「行为保持」回归锚，非本 change 独有的失败信号，符合预期）。`git stash pop` 恢复实现后，
3 条全部 PASS。

## 测试结果

```
/usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice.py -v
...
63 passed, 2 skipped in 21.94s
```

2 个 skip 是既有的 `test_real_runner_*`（真实 runner 环境门控，与本改动无关，未受影响）。
全部既有用例保持绿，新增 3 条全绿。

## 范围内 4 条验收对照

- [x] stdout 超限时被截断到 `OV_MAX_CONTEXT_BYTES` 字节 — `test_exec_output_truncated_over_limit`
- [x] stderr 含 `OV_OUTPUT_TRUNCATED=1` 告警（含 `original_bytes` 和 `limit`）— 同上
- [x] stdout 恰好 = `OV_MAX_CONTEXT_BYTES` 时完整输出、无截断 — `test_exec_output_exact_limit_not_truncated`
- [x] wc 失败场景下 fail-closed（强制截断 + stderr `OV_OUTPUT_SIZE_CHECK_FAILED=1`）—
  `test_exec_output_wc_failure_fails_closed`

## 备注

- 未触碰 D1（`--timeout 0`，属 Task 1）与 D3（WONTDO，不在范围内）。
- `tickets.md` / 完成标签按信号权威表约定，本报告不代劳勾选或打标签，留给双轴审后的执行模式补打。
