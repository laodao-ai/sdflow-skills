# Task 3 Spec 轴复审（fix1）

结论：**PASS**

本次为只读复审，未修改生产代码或 `tickets.md`。复审对象为 Task 3（R-ID：`SA-05`、`SA-17`）及其 fix1 当前盘面。

## 复审输入

- `sdflow-spec/SKILL.md` 当前 diff
- `impl-reports/task3-phase-c-cli-load.md`
- `impl-reports/task3-spec-review.md`
- `impl-reports/task3-standards-review.md`
- `impl-reports/task3-brief.md`
- `tickets.md` 的 Task 3 条目
- `design.md`
- `specs/spec-authoring/spec.md`
- `specs/spec-workflow/spec.md`
- `hack/tests/test_task3_phase_c_contract.py`

## R-ID / 验收项逐项核对

| 验收项 | 当前证据 | 结论 |
|---|---|---|
| 委派标记成对时在应用载荷前剥离；无标记 no-op；不成对 fail-closed 并报告 `problem`、`cause`、`fix` | `SKILL.md` C.3 明确成对标记、应用载荷前剥离、无标记 no-op，以及不成对的连续机械锚 `不成对则fail-closed` 和三字段报告要求；Task 3 契约测试通过 | PASS |
| glob 输出目标按 instruction 推导具体 capability spec 路径；既有文件使用 `existingOutputPaths` | C.3 明确 glob 仅为模式、按 instruction 推导 `具体\`specs/<capability>/spec.md`，既有输出只取 `status --json` 的 `existingOutputPaths` | PASS |
| 路径净化作用于推导出的具体路径，不把 glob 字面量当目标 | C.3 先处理 glob 语义，再对具体路径执行 change 根目录、artifact allowlist、逐组件 symlink 拒绝 | PASS |
| `skipped` 产物不创建文件，并从依赖阅读清单移除 | C.3 明确只认 CLI 自报 `status` 为 `skipped`，跳过且 `MUST NOT` 创建对应文件，并移除依赖阅读清单条目 | PASS |
| 阅读清单以 schema dependencies 为准，依赖图不足时回退写死超集 | C.2 明确读取对象列表 `id`/`done`/`path`/`description`，图覆盖时按图读，图不足时使用 proposal/design/specs 超集 | PASS |
| dependencies 断言验证对象列表四字段 | C.3 最小 schema 断言明确 dependencies 必须是对象列表，每项含 `id`、`done`、`path`、`description` | PASS |
| 终审 design↔specs 双向核对保留为 schema 切换后的兜底 | C.2/C.4 保留 schema 依赖图优先、缺口回退，以及终审 design↔specs 双向一致性核对；未将终审误写成唯一依赖防线 | PASS |

## 机械验证

命令：

```text
pytest -q hack/tests/test_task3_phase_c_contract.py
```

结果：`4 passed in 0.05s`。

该定点套件已覆盖 fix1 旧 review 的两个失败机械锚：

- 委派不成对的连续 `fail-closed` 锚；
- glob 推导具体 `specs/` 路径的连续锚。

## Unicode 门与追溯门

- `sdflow-spec/SKILL.md` 按 Python `len(read_text(encoding="utf-8"))` 计数为 **18,000**，满足 `<= 18,000` 门。
- `test_entry_is_within_unicode_character_budget`：通过。
- `test_final_review_accepts_change_directory_traceability`：通过。
- 当前追溯文字仍明确：追溯边界是整个 change 目录、被砍候选与理由可保留在 `decision-memo.md`，且 `design.md` 的一行纪要指针是合法路径；因此没有因措辞压缩破坏既有追溯契约。

## 相关 resident 套件

命令：

```text
pytest -q hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_sdflow_spec_failure_modes.py
```

结果：`28 passed, 5 failed`。

5 个失败均为 Windows 环境下既有 Bash/WSL/`env` 预检路径不可用：4 个 decision-memo hash 用例无法启动 WSL，1 个缺失 CLI 用例无法启动 Unix `env`。它们未命中 Task 3 代码契约；Task 3 定点契约及 Unicode/追溯两项相关门均已通过，因此不构成 Task 3 Spec 轴阻断。该环境限制不应被表述为全仓测试通过。

另行核验：`git diff --check` 通过。

## 最终判定

Task 3 的 SA-05/SA-17 文档语义、机械契约、Unicode 预算和追溯兼容门均满足。Spec 轴结论为 **PASS**，可以解除 Task 3 的 Spec 轴阻断；本报告不勾选 `tickets.md`，也不替代后续全量验证门。
