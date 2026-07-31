# Code review · adversarial fix6

审查对象：`align-sdflow-spec-with-openspec-schema`

被审盘面：`423f9a8cb117e7bcb75a5b9652e3c974cd5d256b`

本轮按对抗镜只读复审；未修改业务代码或 `code-review-report.md`。

## Findings（置信 ≥80）

### A4 · 高 · CR-02 / CR-09 · YAML directive 前插入 schema 会把合法配置拆成多文档

- 证据：`sdflow-init/scripts/init.py:414-421` 在缺少顶层 `schema:` 时，只跳过空行和注释；遇到第一个非注释行即 `break`。因此合法 YAML 的 `%YAML 1.2` 或 `%TAG ...` directive 位于 `---` document start 之前时，安装器不会继续寻找 document start，而是将新 schema 插在 directive 前。
- 独立复现：对 `%YAML 1.2\n---\ncontext: keep\n` 和 `%TAG !e! tag:example.com,2026:\n---\ncontext: keep\n` 调用 `handle_config(..., "update", schema="sdflow-spec-driven")`，均写出 `schema: sdflow-spec-driven` 在 directive 之前的字节序列。随后以 PyYAML 解析，两个输入均报 `expected a single document in the stream`。
- 运行期后果：原有配置被分割为多份 YAML document；配置读取方若只读取首份，会静默丢失原本的 `context`、`rules`、`metrics` 等设置，若拒绝多文档则 update 后无法读取配置。安装器仍返回 `updated`，违背“只窄改 schema 单键、保留用户内容”的契约。
- 建议：缺键插入时跳过合法 YAML directives，并在其后的 `---`（可带 inline comment）之后插入；若 directive 后缺 document start，则 fail-loud 或遵循 YAML 单文档规则处理。补充 `%YAML`、`%TAG`、BOM、LF/CRLF 的字节级回归，并用实际 YAML 解析断言输出保持单文档。
- 置信：96%。复现稳定，且 YAML directive 必须位于其所属 document start 之前。

## 已核验项

- 已独立运行：`python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py` → `125 passed, 1 skipped`，退出码 0。
- 已复核原子 marker、内置/fork 合法绑定、缺 schema 键插入、inline/comment-only schema、BOM、前导注释/空行 document start、兄弟 schema 保留及权威 schema/模板缺失 fail-loud 的实现与回归；A4 不在现有覆盖内。
- 工作树 `git diff --check` 与发布面 `git diff --check origin/main...HEAD` 均通过（报告写入前）。
- 全量 `pytest`：按用户明确批准跳过；此前真实结果为超时退出码 `124`，未记为通过。

## 结论

**BLOCKED。** A4 会让带 YAML directive 的合法配置在 update 后拆成多文档；修复并补回归后需要再次对抗复审。
