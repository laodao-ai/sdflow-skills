# Task 3 Standards 轴审查

结论：`BLOCKED`

## 审查范围

- `impl-reports/task3-phase-c-cli-load.md`
- `impl-reports/task3-brief.md`
- `hack/tests/test_task3_phase_c_contract.py`
- `tickets.md` 的 Task 3
- `design.md`、`specs/spec-authoring/spec.md`
- 当前 `sdflow-spec/SKILL.md` diff

本次为只读审查；未修改生产代码或 `tickets.md`。

## 阻断项

### B1：Task 3 定点契约测试未通过

运行：

```text
pytest -q hack/tests/test_task3_phase_c_contract.py
```

结果：`2 failed, 2 passed`。

失败项：

1. `test_phase_c_strips_delegation_before_applying_instruction`
   - 测试要求去空格后的文本包含 `不成对则fail-closed`。
   - 实际实现位于 `sdflow-spec/SKILL.md:439-440`，文本为“缺失/乱序/不成对则”后换行接 `fail-closed`，契约测试未命中。
2. `test_phase_c_handles_glob_existing_outputs_and_skipped_status`
   - 测试要求包含 `具体\`specs/`。
   - 实际实现位于 `sdflow-spec/SKILL.md:441-443`，为“推导具体”后换行再写 `` `specs/<capability>/spec.md` ``，契约测试未命中。

这不是可忽略的报告格式问题：Task 3 的新增机械契约当前为红，不能把该任务标为已通过。需要修复实现文字或同步修复契约测试后，重新运行该定点测试并取得全绿；本审查未代为修改二者。

## 规格与实现核对

已确认 `SKILL.md` 已表达以下目标行为：

- `dependencies` 是含 `id` / `done` / `path` / `description` 的对象列表（约第 431-434 行）。
- 委派区块在应用载荷前剥离；无标记 no-op；缺失、乱序或不成对时报告 `problem + cause + fix` 并 fail-closed（约第 438-440 行）。
- glob 目标按 instruction 推导为具体 `specs/<capability>/spec.md`；既有文件只取 `status --json` 的 `existingOutputPaths`（约第 441-443 行）。
- `skipped` 产物跳过、不创建文件，并从依赖阅读清单移除（约第 444-445 行）。
- 终审保留 `design ↔ specs` 双向一致性检查（约第 472-480 行）。

上述内容与 Task 3 brief、Task 3 ticket 以及 `spec-authoring` 规格中的 SA-17 场景方向一致。但当前机械契约测试失败，尚不足以证明交付面稳定。

## 其他验证

- `git diff --check`：通过。
- 未运行全量测试；本次阻断已由 Task 3 定点契约测试直接给出。
- 当前实现 diff 只涉及 `sdflow-spec/SKILL.md`；契约测试为新增未跟踪文件。

## 解除条件

1. 使 `hack/tests/test_task3_phase_c_contract.py` 四项测试全绿。
2. 重新运行并记录同一命令的结果。
3. 由后续 Standards 复审重新判定 Task 3。
