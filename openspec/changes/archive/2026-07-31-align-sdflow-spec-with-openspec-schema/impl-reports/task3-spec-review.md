# Task 3 Spec 轴复审报告

结论：**BLOCKED**

本复审仅覆盖 `tickets.md` 的 Task 3（R-ID：`SA-05`、`SA-17`）。按要求只读审查实现与验证结果；未修改生产代码、`tickets.md` 或其它既有文件。本报告是本次复审新增产物。

## 审查输入

- `impl-reports/task3-phase-c-cli-load.md`
- `impl-reports/task3-brief.md`
- `hack/tests/test_task3_phase_c_contract.py`
- `tickets.md` 的 Task 3
- `design.md`
- `specs/spec-authoring/spec.md`（SA-05、SA-17）
- `specs/spec-workflow/spec.md`（project-local schema 与版本/迁移边界）
- 当前 diff：`sdflow-spec/SKILL.md` 与新增 Task 3 契约测试

实现报告声明已修改 `sdflow-spec/SKILL.md` C.2/C.3/C.4，并曾达到 Task 3 契约测试 `4 passed`；当前工作树实际状态和测试结果以本报告为准。

## R-ID 与验收项逐项核对

| 验收项 | 当前实现/证据 | 判定 |
|---|---|---|
| 委派标记成对时在应用载荷前剥离；无标记 no-op；不成对 fail-closed 并报告 `problem`、`cause`、`fix` | `SKILL.md:439-440` 明确了成对标记、应用载荷前剥离、无标记 no-op、缺失/乱序/不成对 fail-closed 以及三字段报告要求；但 `test_phase_c_strips_delegation_before_applying_instruction` 失败，契约测试要求的无空格短语 `不成对则fail-closed` 在当前文本中不存在（当前为“缺失/乱序/不成对则”后换行再写 `fail-closed`）。 | **BLOCKED** |
| glob 输出目标依据 instruction 推导为具体 capability spec 路径，既有文件改写使用 `existingOutputPaths` | `SKILL.md:441-443` 说明 glob 只是模式、按 instruction 推导 `specs/<capability>/spec.md`，既有文件只取 `status --json` 的 `existingOutputPaths`，且禁止自行遍历。语义覆盖验收项；但同一契约测试因要求的连续文本 `具体\`specs/` 未命中而失败，当前路径文本被换行拆开。 | **BLOCKED** |
| 路径净化作用于推导出的具体路径，不把 glob 字面量当合法目标 | `SKILL.md:441-449` 明确推导具体路径后再净化，并保留 change 根目录、artifact allowlist、逐组件 symlink 拒绝。该项有文档证据。由于 Task 3 定点契约测试整体未通过，仍不能将 Task 3 标为绿。 | **BLOCKED（门禁继承）** |
| `skipped` 产物不创建文件，依赖它的阅读清单条目移除 | `SKILL.md:444-445` 明确只认 CLI 自报的 `skipped`，跳过且不得创建对应文件，并从依赖清单移除；契约测试该断言通过。 | PASS |
| 阅读清单以 schema requires 为准，依赖图不足时使用写死超集 fallback | `SKILL.md:412-423` 明确 dependencies 对象列表、图已覆盖时按图走、图不足时回退写死超集，并保留 specs/tasks 所需的 proposal/design/specs。契约测试对应断言通过；`spec-authoring/spec.md` 的 SA-05 场景与实现一致。 | PASS |
| dependencies 断言接受并验证含 `id`、`done`、`path`、`description` 的对象列表 | `SKILL.md:431-434` 明确 dependencies 必须为对象列表及四个字段。Task 3 契约测试对应断言通过。 | PASS |
| 终审 design↔specs 双向核表述为 schema 已切换时的兜底，而非唯一防线 | 当前 diff 删除了旧的“唯一超集”表述，C.2 改为 schema 依赖图优先、缺口回退超集；C.4 仍保留终审与 status/validate 分离。契约测试对应断言通过。 | PASS |

## 定点验证

命令：

```text
pytest -q hack/tests/test_task3_phase_c_contract.py
```

结果：**2 failed, 2 passed**。

失败项：

1. `test_phase_c_strips_delegation_before_applying_instruction`：未匹配 `不成对则fail-closed`。
2. `test_phase_c_handles_glob_existing_outputs_and_skipped_status`：未匹配 `具体`specs/`。

这两个失败都不是测试环境缺少外部命令，而是当前实现文案未满足仓库契约测试的机械锚。即使语义近似，Task 3 的契约门仍未通过。

另运行相关既有套件：

```text
pytest -q hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_sdflow_spec_failure_modes.py
```

结果：**26 passed, 7 failed**。

失败边界：

- `test_entry_is_within_unicode_character_budget`：当前 `sdflow-spec/SKILL.md` 为 18,060 个 Unicode 字符，超过 18,000 上限；这是本次 Task 3 diff 直接触发的可归因问题。
- `test_final_review_accepts_change_directory_traceability`：既有测试要求的旧措辞 `design.md` 的一行纪要指针是合法路径` 已被当前 diff 压缩删除，属于当前 diff 与既有契约不兼容。
- 其余 5 项为 Windows 环境下既有 Bash/WSL/`env` 预检失败；与 Task 3 语义无直接证据关联，不能据此宣称实现通过。

`git diff --check`：通过。

## 阻断项

1. Task 3 自身契约测试未通过（2 个失败）。必须让委派 fail-closed 与具体 spec 路径的机械锚与当前实现一致，并重新运行该定点测试。
2. 当前 Task 3 diff 使 `sdflow-spec/SKILL.md` 超出 18,000 Unicode 字符预算（18,060），需在不删除 Task 3 目标语义的前提下压缩并重新验证。
3. 当前 diff 删除了既有终审追溯契约测试要求的明确措辞，导致相关既有测试失败；需恢复等价机械锚，或按项目既有规则补齐兼容表述。

在上述阻断项关闭并重新运行验证前，Spec 轴不能给出 `PASS`，也不应勾选 Task 3 或进入后续 Task 4。
