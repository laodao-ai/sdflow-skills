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

`outside-voice.sh:893` 的 `case "$2"` 分支，在既有 `''|*[!0-9]*)` 之后加 `0)` 分支，exit 2（与 usage 一致）。

**砍掉的候选**：改为最小值下限（如 `[ "$tmo" -lt 1 ]`）— 过度设计，0 是唯一的危险值（GNU timeout `DURATION=0` = 禁用超时），负数已被 `*[!0-9]*` 拦。

### D2 · 出境 stdout 大小限制

`do_exec` 的 `cat "$workdir/last-message.md"`（第 832 行）前加检查：

```bash
ov_outsize=$(wc -c 2>/dev/null < "$workdir/last-message.md" | tr -d ' ')
if [ "${ov_outsize:-0}" -gt "$OV_MAX_CONTEXT_BYTES" ]; then
    echo "OV_OUTPUT_TRUNCATED=1 original_bytes=$ov_outsize limit=$OV_MAX_CONTEXT_BYTES" >&2
    head -c "$OV_MAX_CONTEXT_BYTES" "$workdir/last-message.md"
else
    cat "$workdir/last-message.md"
fi
```

复用入境同一个 `OV_MAX_CONTEXT_BYTES`（200KB 默认）。截断按字节、不做 UTF-8 回扫（模型输出大概率 ASCII/英文，且下游做文本匹配非字节验证；入境回扫的 stdout 协议与此不同，复用代价过高）。

### D3 · fake-timeout 非整数兼容

测试桩 `sdflow-init/tests/test_outside_voice.py:53` 的 `lim=$(( sec * 10 ))` 改为：

```bash
lim=$(awk "BEGIN{printf \"%d\", $sec * 10}")
```

当前没有代码路径会传非整数 sec（argparse `type=int` + outside-voice.sh 只接受纯数字），但改一行 awk 的成本≈0，消除测试桩的理论脆性。

## Risks / Trade-offs

- D2 的字节截断可能劈开多字节字符——影响低（模型输出大概率 ASCII），且截断只影响评审 findings 末尾。

## Decisions

见 [decision-memo.md](decision-memo.md)。
