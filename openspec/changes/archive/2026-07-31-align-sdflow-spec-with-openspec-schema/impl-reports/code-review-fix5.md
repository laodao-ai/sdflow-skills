# Code review · fix5

审查对象：`align-sdflow-spec-with-openspec-schema`

本轮修复 domain 镜 D4；保留当前 `46d8d27` 中的 A3 修复，不修改 `code-review-report.md`，不创建 checkpoint。

## 修复

- `copy_bundle(include_schema=True)` 现在在删除已部署的 `sdflow-spec-driven` fork 之前验证权威 schema。
- 验证要求 `schema.yaml` 存在且可读取，并从其中逐条提取 `template:` 引用，确认每个引用在 `templates/` 下对应普通文件存在；当前权威 schema 的四个模板均受此门覆盖。
- 任一模板缺失、引用为空或越出 `templates/` 时抛出 `RuntimeError`。`run(update)` 因 `copy_bundle()` 在 `handle_config()` 之前失败，不会切换 `config.yaml`。
- 实现仅使用 Python 标准库，未引入 YAML 依赖。

## 回归与检查

- 新增回归：复制权威 schema 后删除 `templates/spec.md`，执行 `run(update)`，断言退出失败、现有 managed fork 未被删除、`config.yaml` 原字节不变。
- `python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py`：`125 passed, 1 skipped`。
- `git diff --check`：通过。
- 按用户指示未运行全量 `pytest`；此前全量运行曾超时退出码 `124`，未记为通过。

## 结论

D4 的权威 schema 模板缺失路径现已 fail-loud，并在替换 fork 或切换 config 前停止。等待后续复审与 checkpoint。
