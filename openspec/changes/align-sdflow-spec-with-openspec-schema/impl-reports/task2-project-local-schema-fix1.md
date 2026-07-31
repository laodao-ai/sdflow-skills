# Task 2 Fix 1 实现报告：project-local schema 下发与迁移

## 结论

**DONE_WITH_CONCERNS**

本轮仅修复 Task 2 Standards / Spec 评审明确指出的三个缺口；未修改
`tickets.md`，未创建 checkpoint commit。

## 修复范围

### 1. 命令缺失版本门测试

新增 `test_missing_cli_fails_closed`：注入 `openspec --version` 抛出
`OSError`，验证初始化器保持内置 `spec-driven` schema、不部署
`openspec/schemas/`。

### 2. 迁移补写失败的 fail-closed 路径

新增 `test_migration_failure_stops_before_schema_and_config_switch`：对实际
`.openspec.yaml` marker 写入注入 `OSError`，验证：

- run 以 `SystemExit(1)` 中止；
- `openspec/schemas/` 尚未部署；
- `openspec/config.yaml` 字节级保持原样；
- 目标 change 未留下迁移 marker。

现有实现已保持“先迁移、后 bundle/config 切换”的顺序，失败异常继续向
`run()` 的统一错误出口传播。

### 3. stray 目录隔离

在 `migrate_changes()` 文档中明确机械定义：`openspec/changes/` 下缺少
`proposal.md` 的目录是 stray，不属于 change，不参与迁移；`archive` 是
单独的显式排除项。

新增 `test_stray_directory_without_proposal_is_ignored`，验证 stray 不产生
`.openspec.yaml`，而同级真实在途 change 仍正常补写 marker。

## 验证

命令：

```text
pytest sdflow-init/tests/test_init.py -q
```

结果：**53 passed, 1 skipped**。

`git diff --check`：通过。

## 遗留关注

此前 `pytest sdflow-init/tests -q` 曾在 120 秒内无输出并超时；本轮按用户
要求只运行定点测试，未将全量测试宣称为通过。

