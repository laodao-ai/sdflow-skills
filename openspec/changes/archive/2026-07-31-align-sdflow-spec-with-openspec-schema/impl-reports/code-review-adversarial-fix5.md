# Code review · adversarial fix5

审查对象：`align-sdflow-spec-with-openspec-schema`

被审盘面：`5db85c8ce3562f07665006fd55c66320656498b5`

本轮按对抗镜只读复审；未修改业务代码或 `code-review-report.md`。

## Findings（置信 ≥80）

### A3 · 高 · CR-02 / CR-09 · 注释前缀后的 YAML document start 会被切成第二份文档

- 证据：`sdflow-init/scripts/init.py:378-381` 仅在 `lines[0]` 是 `---`（可带行内注释）时，把缺失的 `schema:` 插到 document start 之后。合法 YAML 可以在 document start 前保留注释或空行；这些形态下该条件不成立，schema 被插到文件开头。
- 独立复现：以 `# header\n--- # document\ncontext: keep\n` 调用 `handle_config(..., "update", schema="sdflow-spec-driven")`，实际得到 `schema: sdflow-spec-driven\n# header\n--- # document\ncontext: keep\n`；BOM+CRLF 及前导空行同样复现。
- 运行期后果：`---` 不再是该配置文档的起点，而是第二个 YAML document start。配置读取方若只消费首个 document，会静默丢失原有 `context`、`rules`、`metrics` 等设置；若拒绝多文档则更新失败。安装器仍报告已切换到 project-local schema，违背“只窄改 schema 单键、保留用户内容”的目标。
- 建议：缺键插入前扫描开头的 BOM、空行和注释，找到首个合法 document start 后再插入；补充带/不带 BOM、LF/CRLF、注释与空行前缀的字节级回归，并断言结果仅含一个 YAML document。
- 置信：95%。复现稳定，且 YAML `---` 文档边界语义确定。

## 已核验项

- 已独立运行：`python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py` → `123 passed, 1 skipped`，退出码 0。
- 已复核原子 marker、内置/fork 合法绑定、缺 schema、inline/comment-only schema、BOM、首行带注释 document start、兄弟 schema 保留、缺失权威 schema fail-loud 的实现与回归；A3 不在现有覆盖内。
- 工作树 `git diff --check` 通过。发布面 `git diff --check origin/main...HEAD` 仍因已提交的 `code-review-domain-fix4.md` 第 3–4 行尾随空白失败；该问题不由本轮修复引入，但仍会阻断发布面空白检查。
- 全量 `pytest`：按用户明确批准跳过；此前真实结果为超时退出码 `124`，未记为通过。

## 结论

**BLOCKED。** A3 会把带前置注释/空行的合法 YAML 配置拆成多文档；修复并补回归后需要再次对抗复审。另需清理既有报告的尾随空白，才能通过发布面空白检查。
