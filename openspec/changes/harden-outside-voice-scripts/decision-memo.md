---
schema_version: 1
change: harden-outside-voice-scripts
branch: feat/harden-outside-voice-scripts
generated_at: "2026-08-04T14:52:26+00:00"
decision_hash: "f10088d2daa3"
---

# 决策纪要 · harden-outside-voice-scripts

## 目标态

修复 outside-voice.sh 的 3 处缺陷（T176/T230/T174）：1 处安全面 + 2 处廉价加固。

## 拍板决策

- **D1 T176 拒绝 timeout=0** — outside-voice.sh:893 的 `--timeout` 校验，在既有纯数字校验之后加数值比较 `[ "$((10#$2))" -eq 0 ]`（`10#` 强制十进制，正确捕获 `0`/`00`/`000` 等所有前导零变体）。exit 2 与既有非法值行为一致。[spec-review-amendment：原方案用 case `0)` 字面匹配，只挡 "0" 不挡 "00"/"000"，被六声收敛识破]
- **D2 T230 出境 stdout 加上限** — do_exec 的 `cat last-message.md` 前 `wc -c` 检查，超 `OV_MAX_CONTEXT_BYTES`（同入境阈值 200KB）时 `head -c` 截断 + stderr 告警 `OV_OUTPUT_TRUNCATED=1`。wc 失败时 fail-closed（强制截断 + stderr `OV_OUTPUT_SIZE_CHECK_FAILED=1`），不静默放行。[spec-review-amendment：原方案 `${ov_outsize:-0}` 在 wc 失败时落 0 → 静默全量输出，与入境侧 fail-loud 不对称] **砍掉的候选**：拒绝输出（exit 1）— 丢弃已付费结果不合理；UTF-8 回扫 — 入境回扫的 stdout 协议不同，复用代价不匹配影响。
- **D3 T174 fake-timeout 取整** — 测试桩 `$(( sec * 10 ))` 改 `awk` 支持浮点数。虽然没有代码路径传非整数（argparse type=int + outside-voice.sh 只接受纯数字），但改一行成本≈0。

## 调研后移出的 issue

- **T227**（worker 信号转发）— 退回延后池。理由：① issue 自注属设计级加固非 bug 修复（当前实现合规 OVBG-05）；② 前提未验（`claude --bg` 的 stop 是 per-pid 还是 group-kill 未核实）；③ 思路②改 cleanup 需过设计门改 spec。按通则③不加宽 + roadmap 原则「大块延后」，不在清理批次做。
- **T173**（KILL 兜底无测试）— WONTDO。`test_runner_ignoring_term_dies_under_group_kill_escalation` 已完整覆盖该路径。
- **T178**（磁盘满 CI 无守）— WONTDO。macOS CI 泳道已跑 hdiutil ramdisk 测试。

## 承重约束

- **C1 outside-voice.sh `--timeout` 校验 MUST 拒绝数值为零的输入（含 `0`/`00`/`000`）** — 验证方式：`--timeout 0`、`--timeout 00`、`--timeout 000` 均应 exit 2；证据锚：`outside-voice.sh:893-895` 修改点 [spec-review-amendment]
- **C2 出境截断阈值复用入境 OV_MAX_CONTEXT_BYTES** — 验证方式：代码中 `wc -c` 比较同一个变量；证据锚：`outside-voice.sh:206` 既有定义

## 接受的边角

- T230 出境截断不做 UTF-8 回扫 — 概率：中等（本项目评审 findings 惯例中文，CJK 3 字节字符在 200KB 边界劈开概率 ≈ 2/3）；影响：低（只影响末尾 1-3 字节，下游 `errors="replace"` 不会崩溃）；完美成本：复用入境 `utf8_head_trim` 可行但 stdout 协议不同、影响范围极小不匹配成本。[spec-review-amendment：原措辞"大概率 ASCII"被五声收敛证伪]
- T174 的修法在当前没有可达路径——纯防御性，改一行 awk 成本≈0。

## 三镜代价

本次无 TG-23 命中。
