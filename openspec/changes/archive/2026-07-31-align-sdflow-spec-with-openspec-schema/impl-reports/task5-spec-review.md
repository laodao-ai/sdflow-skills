# Task 5 Spec 轴复审：回归测试与安装刷新门

## 结论

**BLOCKED**

Task 5 的回归测试与安装刷新证据已复核；安装刷新命令由用户确认使用 Git Bash 执行 `bash setup.sh`，退出码为 0，安装 40 个 skills 到 Claude/Codex 与 `.sdflow`，同步检查通过。但 Task 5 明确要求“安装刷新后全仓 `pytest` 通过”，本次复核执行 `pytest -q` 在 124 秒后超时，未取得全量通过证据，因此不能判定 PASS。

## 复核范围

- `impl-reports/task5-regression-install-refresh.md`
- `impl-reports/task5-brief.md`
- `tickets.md` Task 5（第 79–92 行）
- `tasks.md` 5.1–5.8 与测试覆盖图
- `sdflow-init/tests/test_task5_regression.py`
- `sdflow-init/tests/test_init.py` 中相关既有回归用例
- 当前工作树状态与 diff 检查

## 验收项核验

| 验收项 | 结果 | 证据 |
|---|---|---|
| 版本门：`<1.7.0`、`1.10.0`、命令缺失、非数字输出 | PASS | Task 5 新增数值 semver/fail-closed 测试；`test_init.py` 另有 CLI 输出与缺失命令用例；定点套件通过 |
| 迁移：缺绑定补写、已有绑定 no-op、archive/stray 跳过、单项失败阻止 config 切换 | PASS | `test_init.py` 覆盖迁移幂等、archive、stray、注入写失败；Task 5 新增顺序测试；定点套件通过 |
| copy bundle：权威源删除文件后清理孤儿 | PASS | Task 5 新增 `test_install_refresh_is_authoritative_and_prunes_schema_orphans`，并有定点破坏→失败→恢复→通过证据 |
| schema 内容：`id`/`generates`、委派标记、两条 `requires` 边 | PASS | Task 5 schema content contract 测试通过 |
| update 模式只改 schema 单键，其余 config 内容 byte-identical | PASS | `test_init.py::test_update_changes_only_schema_line` 通过 |
| 新增测试反恒真验证 | PASS（已提供证据） | 实现报告记录了定点破坏后预期失败；新增套件 `8 passed` |
| 权威 bundle 安装刷新 | PASS（用户提供证据） | 用户确认 Git Bash `bash setup.sh` exit 0，安装 40 个 skills 到 Claude/Codex 与 `.sdflow`；本地 `sync_principles.py --check` 为 22 个投放面一致；目标 skill 文件存在 |
| 安装刷新后全仓 `pytest` | **BLOCKED** | 本次执行 `pytest -q`，124 秒超时，未取得通过结果；实现报告此前也未有该门的绿证据 |

## 独立验证结果

- `pytest -q sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init.py`：**61 passed, 1 skipped**
- `python3 hack/sync_principles.py --check`：**22 个投放面全部一致**
- `git diff --check`：通过
- 当前未发现生产实现残留修改；工作树变更仅为 Task 5 brief、实现报告、新增回归测试与本复审报告
- 未运行、未重跑 `setup.sh`；本报告采用用户提供的 setup 结果

## 阻断项

仅剩 Task 5.7 / tickets.md 第 92 行的全量测试门：需要在已完成安装刷新后的同一工作树上取得 `pytest -q` 的退出码 0 及完整通过摘要。当前超时不能等同于通过，也不能据此推进 Task 6/后续收尾。`n