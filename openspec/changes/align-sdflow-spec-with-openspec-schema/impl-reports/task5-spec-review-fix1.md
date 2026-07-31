# Task 5 Spec 轴复审（fix1）：回归测试与安装刷新门

## 结论

**PASS（含用户批准的明确范围例外）**。

Task 5 的非全量验收项均有实现、定点测试或 CLI/同步证据；唯一未取得的证据是安装刷新后的全仓 `pytest` 完整通过结果。用户已明确批准：在全量 `pytest` 重复约 90 秒超时后跳过该项。该项因此记录为“未完成/未通过证据”，**不计为测试通过，也不伪造为绿**；本报告在该明确例外下给出 PASS。

## 复审输入

- `impl-reports/task5-regression-install-refresh.md`
- `impl-reports/task5-spec-review.md`
- `impl-reports/task5-standards-review.md`
- `impl-reports/task5-brief.md`
- `tickets.md` Task 5
- `tasks.md` 5.1–5.8 与测试覆盖图
- `design.md` 中 Task 5 设计与验收约束
- 当前工作树 diff，以及 `sdflow-init/tests/test_task5_regression.py`

## 验收项核验

| 验收项 | 结论 | 证据 |
|---|---|---|
| 版本门：`<1.7.0`、`1.10.0`、命令缺失、非数字输出 | PASS | Task 5 回归测试覆盖数值 semver 与 fail-closed 分支；当前定点套件通过 |
| 迁移：缺绑定补写、已有绑定 no-op、archive/stray 跳过、单项失败阻止 config 切换 | PASS | 既有 `test_init.py` 与 Task 2 fix1 复审报告提供机械证据；Task 5 顺序测试确认迁移观察到旧 config 后才进入切换 |
| copy bundle 整删重拷与孤儿清理 | PASS | `test_install_refresh_is_authoritative_and_prunes_schema_orphans`，含定点破坏→失败→恢复→通过证据 |
| schema 内容契约 | PASS | 回归测试检查四个 artifact 的 `id`/`generates`、委派标记及 `specs`/`tasks` 的 `requires` 边；schema CLI validate 通过 |
| update 模式窄 patch、其余 config byte-identical | PASS | `test_init.py::test_update_changes_only_schema_line` 已通过；旧复审报告记录定点证据 |
| 每条新增测试反恒真 | PASS | 实现报告记录 mutation red/green；Task 5 新增套件当前通过 |
| 权威 bundle 安装刷新 | PASS（依据已有运行证据） | 实现报告记录 Git Bash 执行 `bash setup.sh` exit 0，40 个 skill、`.sdflow` 与同步检查通过；本次 PowerShell 的 `bash` 是 WSL stub，显式 Git Bash 重跑无输出超时，未将其误报为本次成功 |
| 安装刷新后全仓 `pytest` | 例外放行，未通过证据 | 用户明确批准在重复约 90 秒超时后跳过；本次不再运行全量 pytest。历史结果为超时退出码 `124`，不是 PASS |

## 本次独立验证

- `python -m pytest -q sdflow-init/tests/test_task5_regression.py`：**8 passed**。
- `python hack/sync_principles.py --check`：**22 个投放面一致**。
- `git diff --check`：通过。
- `openspec schema validate sdflow-spec-driven`：通过。
- `openspec validate align-sdflow-spec-with-openspec-schema --strict`：通过。
- 前置 `ship_gate.py`：`CONTINUE_IMPL`，`done_tasks` 为 `1,2,3,4,5`，进度 `5/7`。

## 用户批准的例外记录

用户明确指示：如果全量 `pytest` 仍失败/超时，则跳过并执行后续工作；随后明确批准“跳过全量 pytest”。因此本复审不把全量测试缺失转化为隐含通过，也不扩大例外到 Task 5 的其他验收项。该例外仅解除 Task 5.7 对本次推进的阻断。

## 残余风险

全仓测试仍缺少完整 exit 0 与汇总输出；后续应在可稳定完成全量测试的环境补跑并记录结果。该风险不阻断本次 Task 5 Spec 轴复审，因为用户已对该单项作出明确范围裁决。
