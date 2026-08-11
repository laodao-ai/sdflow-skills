# Task 5 — Done 终态快照接线

**状态**：DONE

## 做了什么

### 1. `sdflow-done/SKILL.md` 接线（§3.0，新增）
在「第三步：Archive + Spec 同步」标题之后、派发 Archive 子代理**之前**插入 `3.0 终态 token 快照` 子步：主 session 直接跑 `python3 ~/.sdflow/hack/token_snapshot.py --step done-final || true`（change 目录仍在原位）。段落内写明：
- 成功即在 `token-log.jsonl` 追加 `anchor=true` 行，随 archive 一起搬走；失败显式降级为 `anchor=false`，`|| true` 保证不挡收尾（同 checkpoint 侧口径）。
- 覆盖范围 = Verify + hand-off；archive/commit/merge 自身用量是已声明残余盲区（指回 `openspec/specs/token-snapshot-anchor/spec.md`），MUST NOT 表述为已全量覆盖。
- 已知边界：跨 session 重试收尾时该行会被计作新 session 分组首行、全额计入，token 统计可能重复计入（view-only 精度边界）。

### 2. `token_snapshot.py` 宿主判定补丁（`sdflow-init/assets/hack/token_snapshot.py`）
发现并修的真实缺口：脚本此前有模块级常量 `HOST = "claude"` **恒定硬编码**，`host` 字段从未反映实际宿主；且不论宿主是谁都会去扫 `~/.claude/projects/<munged-cwd>/` 做 mtime 回退——这与 brief「codex/unknown 宿主不走 Claude mtime fallback，直接落显式降级行」的目标态不符（此前只是「侥幸」——非 Claude 宿主该目录通常不存在，所以结果凑巧对，但不是显式判定，且 `host` 字段一直是假的）。

修法：新增 `detect_host(env=None)`，与 `outside-voice-job.py:detect_host()` 同口径（正信号判定：`CLAUDECODE=1` → claude；`CODEX_THREAD_ID` 非空 → codex；两者同时出现 = 冲突 → unknown；均缺席 → unknown）。`_collect()` 起手先判宿主，非 claude 宿主直接返回 `no-transcript` 降级行、完全不碰 `~/.claude/projects/`；`host` 字段如实写检测值（`_build_line` 新增 `host` 形参，`main()` 两处异常兜底分支同步改用 `detect_host()`）。

### 3. 测试
- `hack/tests/test_token_snapshot.py`：新增 `TestHostDetection`（4 个用例）——codex 宿主、unknown（无信号）、冲突信号（两信号同时出现）三种场景下，即便 mtime 回退目录里摆着一份完全合法、会被 claude 宿主命中的 transcript，也必须直接落 `no-transcript` 且 `host` 字段如实；另一用例覆盖 claude 基线场景 `host=="claude"` 不受影响。为使宿主分支测试确定性（不依赖跑测试的进程是否恰好带 `CLAUDECODE=1`），给 `_run_checkpoint`/`_run_token_snapshot_directly` 加了 `_apply_host_baseline` 辅助函数，默认注入 `CLAUDECODE=1` + 清空 `CODEX_THREAD_ID`，`extra_env` 某 key 传 `None` 表示从基线删除该 key（供新用例显式切换/清空宿主信号）。
  - Red-before-green 已验证：`git stash` 掉脚本改动、只留测试改动，新增 3 条 host-skip 用例全部 FAIL（旧脚本走 mtime 回退命中了本不该读到的 transcript）；恢复脚本改动后 17/17 全绿。
- `sdflow-retro/scripts/tests/test_retro_report.py`：新增 `test_compute_token_deltas_reads_done_final_step_row`（冒烟）——在 `archive_dir` 下构造含 `step="done-final"` 行的 `token-log.jsonl`，验证 `read_token_log` 与 `compute_token_deltas` 都能正常读到并正确差分。retro 消费侧对 `step` 值本无白名单校验（只认 `anchor=true` + usage 四计数合法 + session/step 非空字符串），此测试把「新 step 值免入侵改动即可读」的事实钉死为可回归验证的用例，而非仅凭代码走查断言。

### 4. 契约文档（未改动，核验已满足）
`openspec/changes/implement-workflow-optimization-2026-08-p2/specs/token-snapshot-anchor/spec.md`（delta spec）在 Phase C 生成阶段已写好本次全部行为契约（`step="done-final"`、失败降级、残余盲区声明、跨 session 重试已知边界），核对后确认与本次实现逐条一致，无需改动；archive 时会由 sdflow-done 第三步的 Archive 子代理同步进 `openspec/specs/token-snapshot-anchor/spec.md` 主 spec。

## 验收标准逐条核对

- [x] sdflow-done SKILL 第三步起手含 token_snapshot 调用接线 —— `sdflow-done/SKILL.md` §3.0
- [x] 失败显式降级不挡收尾流程 —— `|| true` + 脚本内已有的 try/except-to-degraded-line 全链路（未改动既有降级路径，只改宿主判定分支）
- [x] codex/unknown 宿主不走 Claude mtime fallback，直接显式降级 —— `detect_host()` + `_collect()` 起手分流；`hack/tests/test_token_snapshot.py::TestHostDetection` 4 用例覆盖
- [x] done-final step 值记入契约文档 —— delta spec 已含（Phase C 生成阶段写就，核对一致）
- [x] retro join 对 done-final 行可读 —— `test_compute_token_deltas_reads_done_final_step_row` 冒烟通过

## 测试证据

```
$ /usr/bin/python3 -m pytest hack/tests/test_token_snapshot.py -q
.................                                                        [100%]
17 passed in 1.92s

$ /usr/bin/python3 -m pytest sdflow-retro/scripts/tests/test_retro_report.py -q -k token
...................                                                      [100%]
19 passed, 69 deselected in 24.42s

$ /usr/bin/python3 -m pytest hack/ sdflow-retro/ -q
（全量）532 passed in 90.49s
```

全仓 `pytest -q`（含所有 skill）已另行在后台跑，超出 2 分钟前台超时窗口，未在本报告内附最终行数——`hack/` + `sdflow-retro/` 是本次改动唯一触及的两个测试面，已单独全绿；其余 skill 目录本次零改动，理论无关联失败风险。

## 已知边界 / 未做

- 未新增 `--anchor` 之类 CLI 显式开关——`anchor` 字段的 true/false 由采集是否成功自动决定（brief 括注「anchor=true」指的是成功时产出的记录字段值，非新参数），与既有 checkpoint 侧调用形态完全同构，无需引入新接口面（基准④简化）。
- 未改 `token-log.jsonl` schema、未改 `retro_report.py` 解析逻辑——`step` 字段本就无白名单校验，"done-final" 天然可读，遵 Non-Goals「不改 lens-metric 锚字段集」同精神（此处虽非 lens-metric 锚，但同样不引入新字段）。
- 跨 session 重试重复计入的边界按 delta spec 原文「不改脚本」——只声明不修复，本次未做任何缓解代码。
