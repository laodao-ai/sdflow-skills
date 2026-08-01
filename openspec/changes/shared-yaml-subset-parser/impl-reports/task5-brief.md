### Task 5: 剩余脚本 + ADR + CI + golden test

**Blocked-by:** 2,3,4
**R-ID:** R5, R6, R7, R8, R9, R10, R12

`roadmap_writeback_draft.py`：`read_verify_state` 改为 `_yq('.ship-gate.verify', path, front_matter=True)` + 保留 `PASS`/`FAIL` 枚举校验。`sad_schema.py`：`frontmatter_end` / `parse_frontmatter` 改为 `_yq('.', path, front_matter=True)` + 保留 `TOP_KEYS` / `FACT_KEYS` / `FACT_VALUES` 白名单校验。

新增 ADR `openspec/adr/0036-yq-replaces-hand-rolled-yaml.md`（Context / Decision / Consequences 三节）。CI `mechanical-gates.yml` 显式安装 + 钉版本 yq。新增 `_yq()` 一致性 golden test 检查 7 份封装核心逻辑字节一致。重写依赖手搓逐行扫描器诊断的测试断言（yq 方案下精确诊断不可复现）。`grep` 验证目标脚本中无手搓 YAML 解析函数残留。

- [ ] `roadmap_writeback_draft.py` 的 frontmatter 解析已替换为 `_yq()` + 枚举校验保留
- [ ] `sad_schema.py` 的 frontmatter 解析已替换为 `_yq()` + 白名单校验保留
- [ ] `pytest sdflow-done/tests/` 全绿
- [ ] `pytest sdflow-architecture/tests/` 全绿
- [ ] ADR-0036 存在且含 Context / Decision / Consequences 三节
- [ ] `mechanical-gates.yml` 显式安装 yq（钉版本）
- [ ] `_yq()` golden test 检查 7 份封装一致性
- [ ] `grep` 验证目标脚本无手搓 YAML 解析函数残留（R11 预扫描除外）

