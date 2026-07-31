# Code review · adversarial fix7

审查对象：`align-sdflow-spec-with-openspec-schema`

被审盘面：`fc24e97e9f4912644fb2d2a5404ae2cd5c5735ed`

本轮按对抗镜只读复审；未修改业务代码或 `code-review-report.md`。

## Findings（置信 ≥80）

### A5 · 高 · CR-02 / CR-09 · 合法的 `schema :` 被误判为缺键，update 写出重复 schema

- 证据：`sdflow-init/scripts/init.py:378` 与 `:396` 都只识别精确的 `schema:`；YAML block mapping 合法允许键与冒号之间出现空白，因此 `schema : spec-driven` 是顶层 `schema` 键，却不会被读取或定点改写。
- 独立复现：先以 PyYAML 解析 `schema : spec-driven\ncontext: keep\n`，得到 `{'schema': 'spec-driven', 'context': 'keep'}`。再对同一字节调用 `handle_config(root, "update", schema="sdflow-spec-driven")`，返回 `updated`，但输出为：

  ```yaml
  schema: sdflow-spec-driven
  schema : spec-driven
  context: keep
  ```

- 运行期后果：安装器宣称仅改写单个 schema 键，实际留下两个语义相同的 YAML 键。不同 YAML 消费方可能采用首值、末值或拒绝重复键；因此 project-local schema 可能未启用、仍落在旧 schema，或后续 OpenSpec 命令直接失败。comment-only 的合法变体 `schema :    # note` 同样可复现。
- 建议：把 `_schema_from_config()` 与 `_set_schema_key()` 的顶层键识别统一为可接受合法 key-to-colon 空白的受限模式，并定点保留其余字节；新增 LF/CRLF、BOM、value 与 comment-only 两类 `schema :` 回归，断言输出只含一条 schema 键并可被实际 YAML/OpenSpec 解析。
- 置信：98%。已由真实更新路径稳定复现，且输入经 YAML 解析确认合法。

## 已核验项

- 定向聚合：`python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py` → `126 passed, 1 skipped`，退出码 0。该聚合尚未覆盖 A5。
- 已复核 fix6 的 YAML directives、BOM/CRLF、document start、行内及 comment-only schema、原子 marker、合法 marker 绑定和权威 schema/template fail-loud 路径；A5 在现有回归中没有等价覆盖。
- 工作树 `git diff --check` 通过。发布面 `git diff --check origin/main...HEAD` 仍报 `code-review-domain-fix6.md` 两处已提交尾随空格；这不是本轮业务 finding，但在交付前须清理。
- 全量 `pytest`：按用户明确批准跳过；此前真实结果为超时退出码 `124`，未记为通过。

## 结论

**BLOCKED。** A5 会把合法配置改写为重复 schema 键，违背单键窄改与 project-local schema 可靠启用的目标；修复并补字节级回归后需要再次对抗复审。
