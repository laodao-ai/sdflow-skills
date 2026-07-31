# Code review · domain 镜 · fix3

审查对象：`align-sdflow-spec-with-openspec-schema`
审查盘面：`89e06a8c45aa353e90e92b4b587f46ee6f23be11`
范围：最终 fix2 的 schema 迁移与分发契约。仅只读复审；未修改业务代码或 `code-review-report.md`。

## 范围与清单

本 change 不命中 TG-01/02/03 的技术栈领域 delta，按通用 `CR-01` 至 `CR-09` 复核，并以 `SW-SCHEMA` 的版本门、迁移前置、窄范围 config 改写和受管 fork 分发契约为准。

## Findings（置信 ≥80）

### D1 · 高 · CR-02 / CR-09 · 置信度 98

带 UTF-8 BOM 的既有 `openspec/config.yaml` 含顶层 `schema:` 时，会被误判为缺键；update 会在文件开头再插入一条 `schema:`，造成重复顶层键，违反「只改 schema value、其余字节保留」的迁移契约。

- 证据：[`_schema_from_config()`](../../../../sdflow-init/scripts/init.py) 的匹配要求行首即为 `schema:`，因此 BOM 开头的首行不匹配；[`_set_schema_key()`](../../../../sdflow-init/scripts/init.py) 同样无法匹配该行，随后其缺键分支在 BOM 后插入新键。
- 独立复现：临时消费仓写入 `b"\\xef\\xbb\\xbfschema: spec-driven  # retained\\r\\ncontext: keep\\r\\n"` 后调用 `handle_config(..., "update", schema="sdflow-spec-driven")`，结果为 `updated`，文件含两条 schema：新增 `schema: sdflow-spec-driven` 与原 `schema: spec-driven  # retained`。
- 影响：任何由带 BOM 编辑器生成的既有消费仓配置都会在版本门通过的 update 中获得歧义 YAML；不同解析器对重复键的取值策略不同，fork 可能未启用或配置校验失败。该路径属于目标态的正常迁移输入，不能以当前模板不写 BOM 为由裁掉。
- 建议：在读取与改写时把 BOM 作为文件前缀而非 YAML 行内容处理，确保命中并仅替换首个顶层 schema 的 value；补充 BOM + CRLF + inline comment 的字节级回归用例，并断言结果只保留一条 schema 键。

## 已验证的 fix2 契约

- 迁移 marker 采用同目录临时文件、`fsync()` 与 `os.replace()` 原子发布；既有 marker 严格解析，合法值接受 `spec-driven` 与 `sdflow-spec-driven`，其它值 fail-loud。
- 受管分发只整删重拷 `openspec/schemas/sdflow-spec-driven/`，兄弟 schema 保留；canonical 与 dogfood schema 的 SHA-256 均为 `7F75F12F8D11AD3305A1D912101ADA1BAA239A05814D6AABC7C546C08B202B3C`。
- 无 BOM 的缺键插入、inline comment 与其它字节保留已有覆盖；该覆盖未涵盖 BOM 输入，不能证明 D1。

## 验证

- `python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py` → `117 passed, 1 skipped`，退出码 0。
- `openspec schema validate sdflow-spec-driven`、`openspec status --change align-sdflow-spec-with-openspec-schema --json`、`openspec instructions specs --change align-sdflow-spec-with-openspec-schema --json`、`openspec instructions tasks --change align-sdflow-spec-with-openspec-schema --json` → 均退出码 0。
- `git diff --check` → 通过。
- 全量 `pytest`：按用户明确批准跳过；此前退出码为 `124`，未宣称通过。

## 结论

**BLOCKED。** fix2 已关闭此前 marker 原子性、双 schema 合法绑定、缺键插入、inline comment 和兄弟 schema 分发问题；但 D1 会使带 BOM 的正常既有配置在迁移时形成重复 schema 键。修复并补回归后，需要再次进行领域镜复审。
