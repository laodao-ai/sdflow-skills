## Why

outside-voice.sh 和 outside-voice-job.py 存在 6 处正确性/安全缺陷（T176/T227/T174/T173/T230/T178），其中两处是运行时安全面：`--timeout 0` 静默禁用超时导致进程挂死（T176），worker 无信号转发导致取消路径杀不死计费进程（T227）。其余四处是测试覆盖缺口和资源限制缺失。来源是 issues-triage-2026-08 roadmap B11 批次。

## What Changes

- **拒绝 `--timeout 0`**（T176）：outside-voice.sh 的 `--timeout` 参数校验加排 0（GNU timeout `DURATION=0` = 禁用超时）
- **worker 信号转发**（T227）：cmd_worker 从 `subprocess.call` 改 `Popen` + SIGTERM/SIGINT handler 转发给子进程 + 有界等待 + kill 兜底
- **fake-timeout 非整数兼容**（T174）：测试桩的 `$(( sec * 10 ))` 改为支持浮点数输入
- **KILL 兜底路径测试**（T173）：补 ov_cleanup KILL 升级路径的测试覆盖
- **出境 stdout 加上限**（T230）：do_exec 的 `cat last-message.md` 前加 `wc -c` 检查，超 OV_MAX_CONTEXT_BYTES 时截断 + 警告
- **磁盘满测试接缝**（T178）：用 `chmod 500` 模拟 workdir 不可写，验证 M3 诊断行产出

## Capabilities

### New Capabilities

（无新能力）

### Modified Capabilities

（无 spec 级行为变更——全部是既有行为的缺陷修复 + 测试补全）

## Impact

- `sdflow-init/assets/hack/outside-voice.sh`（2 处修改：timeout 校验 + 出境截断）
- `sdflow-init/assets/hack/outside-voice-job.py`（1 处修改：cmd_worker 信号转发）
- `sdflow-init/tests/test_outside_voice.py`（3 处新增测试：fake-timeout 取整 + KILL 路径 + 磁盘满）

无 API 变更，无外部依赖变更。

## Success Metrics

- 6 条 issue 全部可关闭（DONE + evidence）
- 既有测试全绿（`/usr/bin/python3 -m pytest sdflow-init/tests/`）
- 新增测试覆盖 T173/T174/T178 三个路径

## Non-Goals

- 不改 `run_cleanup`（已有完整 probe_subtree + claude stop + 子树核验路径）
- 不改 outside-voice.sh 的信号 trap 机制（残余 (a)(b)(c)(d*) 已登记、属 shell 层不可干净消除的窗口）
- 不做出境 UTF-8 边界回扫（入境已有，出境截断按字节切 + 警告够了）

## Priority

P1 — 安全面（timeout 禁用 + 进程杀不死）+ roadmap B11 排期批次

## Compliance

N/A

## Decisions

见 [decision-memo.md](decision-memo.md)。
