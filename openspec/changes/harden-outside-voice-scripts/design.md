## Context

见 proposal.md — Why。标的脚本：`sdflow-init/assets/hack/outside-voice.sh`（910 行，bash）。由 `setup.sh` 安装到 `~/.sdflow/hack/`，运行时被 `sdflow-spec-review` 和 `sdflow-code-review` 两个评审 SKILL 消费。测试在 `sdflow-init/tests/test_outside_voice.py`。

## Goals / Non-Goals

**Goals:**
- 修复 3 处缺陷（T176/T230/T174）
- 每处修复有对应测试锚或既有测试覆盖

**Non-Goals:**
- 不改 outside-voice-job.py（T227 退回延后池：设计级加固 + 前提未验）
- T173/T178 已 WONTDO（调研发现已有测试覆盖）

## Decisions

### D1 · `--timeout 0` 拒绝方式

`outside-voice.sh:893` 的 `case "$2"` 分支，在既有 `''|*[!0-9]*)` 纯数字校验**之后**，加数值比较 `[ "$((10#$2))" -eq 0 ] && usage`，exit 2。`10#` 强制十进制解析，正确捕获 `0`/`00`/`000` 等所有前导零变体（shell `case` 的字面 `0)` 只匹配 `"0"`，不匹配 `"00"`）。[spec-review-amendment]

**砍掉的候选**：① 字面 case `0)` 分支 — 只匹配字符串 "0"，"00"/"000" 绕过（spec-review F1）；② 最小值下限（`[ "$tmo" -lt 1 ]`）— 过度设计，0 是唯一的危险值，负数已被 `*[!0-9]*` 拦。

### D2 · 出境 stdout 大小限制

`do_exec` 的 `cat "$workdir/last-message.md"`（第 832 行）前加检查：

```bash
ov_outsize=$(wc -c 2>/dev/null < "$workdir/last-message.md" | tr -d ' ')
# [spec-review-amendment] wc 失败时 fail-closed（安全默认=强制截断），不静默放行
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

复用入境同一个 `OV_MAX_CONTEXT_BYTES`（200KB 默认）。截断按字节、不做 UTF-8 回扫——接受截断可能在最后一个多字节字符（中文 CJK 3 字节）处产生非法 UTF-8（概率中等，非"大概率 ASCII"），但影响低：只影响 200KB 边界处末尾 1-3 字节，下游 `errors="replace"` 不会崩溃。D2 scope 是"bounded published evidence"（cap stdout 通道），非"bounded resource usage"（runner 已写完 last-message.md）。[spec-review-amendment]

### ~~D3 · fake-timeout 非整数兼容~~ — WONTDO [spec-review-amendment]

WONTDO。理由：① 非整数 sec 不可达（argparse `type=int` + shell `*[!0-9]*` 双重校验）；② awk `printf "%d"` 截断而非四舍五入，`sec=0.05 → lim=0 → 看门狗立即杀进程`，引入新语义错误；③ 设计门拍板 Q1→B。

## Risks / Trade-offs

- D2 的字节截断可能劈开多字节字符——影响低（模型输出大概率 ASCII），且截断只影响评审 findings 末尾。

## Decisions

见 [decision-memo.md](decision-memo.md)。
