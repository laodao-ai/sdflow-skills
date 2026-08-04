## Why

outside-voice.sh 存在 1 处运行时安全缺陷 + 2 处廉价加固缺口（T176/T230/T174）。其中 T176 是安全面：`--timeout 0` 静默禁用超时导致进程挂死。来源是 issues-triage-2026-08 roadmap B11 批次。

## What Changes

- **拒绝 `--timeout 0`**（T176）：outside-voice.sh 的 `--timeout` 参数校验加排 0（GNU timeout `DURATION=0` = 禁用超时）
- **出境 stdout 加上限**（T230）：do_exec 的 `cat last-message.md` 前加 `wc -c` 检查，超 OV_MAX_CONTEXT_BYTES 时截断 + stderr 告警
- **fake-timeout 非整数兼容**（T174）：测试桩的 `$(( sec * 10 ))` 改为支持浮点数输入

## Capabilities

### New Capabilities

（无新能力）

### Modified Capabilities

（无 spec 级行为变更——全部是既有行为的缺陷修复 + 测试桩兼容）

## Impact

- `sdflow-init/assets/hack/outside-voice.sh`（2 处修改：timeout 校验 + 出境截断）
- `sdflow-init/tests/test_outside_voice.py`（1 处修改：fake-timeout 取整）

无 API 变更，无外部依赖变更。

## Success Metrics

- 3 条 issue 全部可关闭（DONE + evidence）
- 既有测试全绿（`/usr/bin/python3 -m pytest sdflow-init/tests/`）

## Non-Goals

- 不改 outside-voice-job.py 的 cmd_worker 信号转发（T227，设计级加固，前提未验，退回延后池）
- 不补 KILL 兜底路径测试（T173，已有 test_runner_ignoring_term_dies_under_group_kill_escalation 覆盖，WONTDO）
- 不补磁盘满测试（T178，本地 macOS 开发机已覆盖 hdiutil ramdisk 测试（CI=true 时 skip），WONTDO）[spec-review-amendment]

## Priority

P1 — 安全面（timeout 禁用）+ roadmap B11 排期批次

## Compliance

N/A

## Decisions

见 [decision-memo.md](decision-memo.md)。
