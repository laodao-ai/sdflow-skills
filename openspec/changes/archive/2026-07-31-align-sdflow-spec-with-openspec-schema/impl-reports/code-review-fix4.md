# Code review · fix4

审查对象：`align-sdflow-spec-with-openspec-schema`

本轮处理 A2、D2、D3；未修改 `code-review-report.md`，未创建 checkpoint，也未把未提交工作树伪报为已放行的 SHA。

## 修复

- **A2**：`schema:    # 注释` 现在改写为 `schema:    sdflow-spec-driven # 注释`。保留冒号后的原缩进、BOM、CRLF 和注释内容，并补空白以保持 YAML 注释分隔语义。
- **D2**：缺失 `schema:` 且首行为 `--- # local config` 时，schema 现在插入该 YAML document marker 之后，保留 marker 注释与 CRLF，不再生成第二个 document。
- **D3**：`copy_bundle(include_schema=True)` 先验证权威 `sdflow-spec-driven/schema.yaml` 存在；缺失时抛出 `RuntimeError`。`run()` 因此在调用 `handle_config()` 前中止，config 不会切换到不存在的 fork。

## 回归与检查

- 新增 comment-only schema（含 BOM）、带注释 document start、缺失权威 schema 和 run 不切 config 的回归。
- `python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py`：`123 passed, 1 skipped`。
- `git diff --check`：通过。
- 全量 `pytest`：按用户明确批准跳过；此前真实结果为超时退出码 `124`，本轮未宣称绿色。

## 结论

A2、D2、D3 的复现路径均已被字节级或流程级回归覆盖；等待后续代码审复核与 checkpoint，不写总报告。
