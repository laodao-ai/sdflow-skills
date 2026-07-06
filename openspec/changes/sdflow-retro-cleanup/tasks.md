# Tasks — sdflow-retro 脚本清理批（T58-T61）

轻量清理：每项 TDD（先写反证哨兵测试 FAIL → 修 → 测过），逐项 checkpoint。跳 grill/spec-review/设计门（无新设计决策），保 code-review。

## 1. T58 — tilde fence 支持（`lens_metric_aggregate.py`）

- [ ] 1.1 写反证测试 `test_fence_aware_ignores_tilde_fence`（`~~~` 内锚被跳过）+ `test_tilde_fence_different_char_no_close`（``` 内的 `~~~` 不闭合、反之亦然）——修前 FAIL
- [ ] 1.2 `_FENCE_OPEN` 捕获 ``` 或 `~~~`；`_fence_aware_lines` 追踪 (marker 字符, 长度)，闭合须同字符且长度 ≥ 开启
- [ ] 1.3 跑 `test_lens_metric_aggregate.py` 全绿（含既有 nested-backtick 用例不回归）
- [ ] 1.4 checkpoint

## 2. T59 — 阈值共享常量（`lens_metric_aggregate.py` + `retro_report.py`）

- [ ] 2.1 写测试 `test_review_rounds_threshold_shared`（断言 `LMA.REVIEW_ROUNDS_THRESHOLD == 10` 且 `retro_report` 引用同源，非本地字面量）——修前 FAIL
- [ ] 2.2 `lens_metric_aggregate.py` 定义 `REVIEW_ROUNDS_THRESHOLD = 10`；`render_table` 用之（比较 + flag 串）
- [ ] 2.3 `retro_report.py` `surfacing_block` 引用 `LMA.REVIEW_ROUNDS_THRESHOLD`（比较 + 文案），去本地 `10` 字面量
- [ ] 2.4 跑两个 test 文件全绿（既有 `≥10` flag / surfacing 边界用例不回归）
- [ ] 2.5 checkpoint

## 3. T60 — `_run_git` 失败留痕（`retro_report.py`）

- [ ] 3.1 写反证测试 `test_run_git_failure_traces_stderr`（对失败 git 子命令，stderr 含告警）——修前 FAIL（无输出）
- [ ] 3.2 `_run_git` 捕 returncode，≠0 时 `sys.stderr.write` 告警（含 git stderr），仍返回 stdout
- [ ] 3.3 跑 `test_retro_report.py` 全绿（既有 boundary/normal 用例不回归）
- [ ] 3.4 checkpoint

## 4. T61 — 删死防御 + 显式契约（`lens_metric_aggregate.py` + `retro_report.py`）

- [ ] 4.1 写测试 `test_aggregate_missing_archive_returns_empty`（缺 archive 目录 → `([],[],[])` 不抛）锁契约——修前逻辑相同但契约未显式化
- [ ] 4.2 `aggregate` 早返回：`archive_root` 非目录 → 返回 `([], [], [])`（显式契约 + 注释）
- [ ] 4.3 `surfacing_block` / `build_report` 聚合③删死 `try/except`，改诚实注释（aggregate 内部已处理缺目录 + per-file 错误）
- [ ] 4.4 跑两个 test 文件全绿（既有 surfacing 空箱 / build_report 用例不回归）
- [ ] 4.5 checkpoint

## 5. 收尾

- [ ] 5.1 全量 `pytest sdflow-retro/scripts/tests/` 零回归、零 warning
- [ ] 5.2 dogfood 再生 `openspec/retro/report.md` 确认幂等无漂移（`python3 sdflow-retro/scripts/retro_report.py --root .`）
- [ ] 5.3 交 `/sdflow-code-review`（T58/T60 逻辑面真审）
