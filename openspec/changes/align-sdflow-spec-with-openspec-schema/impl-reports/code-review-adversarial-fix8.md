# Code review · adversarial fix8

审查对象：`align-sdflow-spec-with-openspec-schema`

被审盘面：`dc67af388a471acbe36d95a83ac7eab65948c304`

本轮按对抗镜只读复审；未修改业务代码或 `code-review-report.md`。

## 已核验的运行期边界

- `schema : value` 现在由 `_schema_from_config()` 与 `_set_schema_key()` 使用一致的受限匹配识别，保留键到冒号之间的空白、值后缀和行尾；不会再把合法键误判为缺失并插入重复键。
- 缺失键的写入会跨过 BOM、前导注释/空行、`%YAML`/`%TAG` directives，并在可带注释的 `---` document start 之后插入；已有键的 BOM、CRLF、inline comment 和 comment-only 形态均由定点回归覆盖。
- migration marker 采用原子写入，已存在 marker 仅接受 `spec-driven` 或 `sdflow-spec-driven`；权威 schema 和所有引用模板在替换 managed fork、切换 config 前验证，缺失时 fail-loud。

## 验证

- `python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py`：`127 passed, 1 skipped`，退出码 `0`。
- `openspec schema validate sdflow-spec-driven`、`openspec status --change align-sdflow-spec-with-openspec-schema --json`、`openspec instructions specs --change align-sdflow-spec-with-openspec-schema --json` 和 `openspec instructions tasks --change align-sdflow-spec-with-openspec-schema --json`：退出码均为 `0`。
- 工作树 `git diff --check`：通过。
- 全量 `pytest`：按用户明确批准跳过；此前真实结果为超时退出码 `124`，未记为通过。

## Findings（置信 ≥80）

### A6 · 中 · CR-09 · 发布基线仍含已提交尾随空白

- 证据：`git diff --check origin/main...HEAD` 退出码 `2`，报告 `openspec/changes/align-sdflow-spec-with-openspec-schema/impl-reports/code-review-domain-fix7.md` 第 3、4 行存在 trailing whitespace。
- 影响：工作树检查通过只证明未提交差异干净，不能覆盖交付盘面；发布基线仍不能通过仓库要求的空白检查。
- 处置：本镜只读，未修改该历史报告；应清理这两处空白后再复审。该项不否定 schema 业务边界修复，但阻断本次最终放行。
- 置信：99%。命令输出可重复，且问题位于当前 `HEAD` 已提交范围。

## 结论

**BLOCKED。** schema 写入、YAML directives、注释/document start、模板完整性和 CLI 行为均已通过本轮核验；但发布面 `git diff --check origin/main...HEAD` 仍失败，不能将 `dc67af3` 标记为最终放行。全量 pytest 为获批准的超时跳过，并非绿色结果。
