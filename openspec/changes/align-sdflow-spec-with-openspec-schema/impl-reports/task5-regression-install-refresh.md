# Task 5 实现报告：回归测试与安装刷新门

## 结论

**DONE_WITH_CONCERNS**

已完成 Task 5 回归测试新增与定点 TDD 验证；未修改 `tickets.md`，未创建 task checkpoint。

## 变更

- 新增 `sdflow-init/tests/test_task5_regression.py`。
- 覆盖安装刷新整删重拷与 schema 孤儿清理、CLI 版本门数值比较、CLI 不可用时 fail-closed、迁移先于 config 切换，以及 schema 内容契约。
- 未修改生产实现；未修改 `tickets.md`。

## TDD 证据

1. 对 `sdflow-init/scripts/init.py` 的 schema 部署分支做临时定点破坏。
2. 运行：`pytest -q sdflow-init/tests/test_task5_regression.py::test_install_refresh_is_authoritative_and_prunes_schema_orphans`
3. 结果：按预期失败，刷新后 stale schema 目录仍存在。
4. 恢复生产实现后运行新增套件：`8 passed`。

## 已完成验证

- `pytest -q sdflow-init/tests/test_task5_regression.py`：**8 passed**
- `pytest -q sdflow-init/tests/test_init.py`：**53 passed, 1 skipped**
- `git diff --check`：通过
- 工作树仅有本报告、Task 5 brief 与新增测试文件的未提交变更；无生产代码残留修改。

## 用户批准的例外

- 使用 Git Bash 执行 `bash setup.sh` 已成功退出（40 个 skill、`.sdflow` 与同步检查均通过）。
- 全仓 `pytest -q` 重新尝试后在 90 秒超时，退出码 `124`；用户明确批准跳过，故如实记录为未通过/未完成，不将其写成绿。
