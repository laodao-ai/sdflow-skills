# Code review · domain 镜 · fix4

审查对象：`align-sdflow-spec-with-openspec-schema`  
审查盘面：`7bc8d6947c644596d35e7ef65cd9c8a089c6005c`  
范围：最终修复后的 schema 迁移、project-local schema 分发与 `config.yaml` 窄改写。仅只读复审；未修改业务代码或 `code-review-report.md`。

## 范围与清单

本 change 不命中 TG-01/02/03 的技术栈领域 delta，按通用 `CR-01` 至 `CR-09` 审核，重点核对 `spec-workflow` 的「schema 随 bundle 下发、迁移前置、CLI 版本门」Requirement。

## Findings（置信 ≥80）

### D2 · 高 · CR-02 / CR-09 · 置信度 97

当 `openspec/config.yaml` 使用合法的 YAML 文档起始行并带 inline comment（例如 `--- # local config`），且缺少顶层 `schema:` 时，缺键分支会把 `schema:` 插到文档起始标记之前，形成两个 YAML document。CLI 通常只消费最后一个 document，因此实际配置仍缺少目标 schema；安装器却报告已更新。

- 证据：[`_set_schema_key()`](../../../../sdflow-init/scripts/init.py:344) 仅识别字节完全等于 `---\n` 或 `---\r\n` 的文档起始行；未命中时在 offset 0 插入。`handle_config()` 随后返回 `updated`。
- 独立复现：临时消费仓写入 `b"--- # local config\\r\\ncontext: keep\\r\\n"`，调用 `handle_config(..., "update", schema="sdflow-spec-driven")` 后得到 `b"schema: sdflow-spec-driven\\r\\n--- # local config\\r\\ncontext: keep\\r\\n"`。
- 影响：这是缺键迁移的合法 YAML 输入。version gate 通过后，使用者会看到成功结果，却仍运行在未启用 fork 的配置上，违反「下发 schema 后切换 config」与可观测性契约。
- 建议：把 YAML document-start 行识别扩展为保留注释与行尾字节的 `---` 标记；若文件包含 document-start，始终在该标记之后插入缺失的 `schema:`，并补 CRLF + inline-comment 的字节级回归。

### D3 · 高 · CR-02 / CR-09 · 置信度 96

`copy_bundle()` 在 project-local schema 权威源缺失时静默跳过 schema 复制；`run()` 仍会完成在途 change 补写并将 `config.yaml` 切至 `sdflow-spec-driven`。结果是配置引用不存在的 schema，安装器仍报告成功。

- 证据：[`copy_bundle()`](../../../../sdflow-init/scripts/init.py:245) 对 `schema_src` 使用 `if os.path.isdir(schema_src)`，缺失时不抛错；[`run()`](../../../../sdflow-init/scripts/init.py:967) 不核验目标目录已落盘，随后无条件调用 `handle_config(..., schema=target_schema)`。
- 独立复现：临时消费仓具备 `proposal.md` 与 `config.yaml`，将 `SCHEMAS_SRC` 指向不存在目录后顺序执行 `migrate_changes()`、`copy_bundle(..., include_schema=True)`、`handle_config(...)`；最终 `config.yaml` 为 `schema: sdflow-spec-driven`，而 `openspec/schemas/sdflow-spec-driven/` 不存在。
- 影响：不完整/损坏的 skill asset 安装会把消费仓推进不可解析状态；下一次 `openspec` 命令失败时，根因已被错误的成功汇总掩盖。与 workflow bundle 源缺失时 `copytree()` fail-loud 的行为也不一致。
- 建议：版本门通过且要求下发 schema 时，权威源目录不存在应直接抛 `RuntimeError`；复制后验证目标 `schema.yaml` 存在，再允许迁移与 config 切换。补覆盖缺失 schema asset 时的 fail-loud 与 config 不变断言。

## 已验证

- 之前修复的 marker 原子发布、双合法 schema marker、缺顶层键、schema 行 inline comment、兄弟 schema 保留、UTF-8 BOM + CRLF 单键改写均在当前定向聚合中通过。
- `python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py` → `118 passed, 1 skipped`，退出码 0。
- `openspec schema validate sdflow-spec-driven`、`openspec status --change align-sdflow-spec-with-openspec-schema --json`、`openspec instructions specs --change align-sdflow-spec-with-openspec-schema --json`、`openspec instructions tasks --change align-sdflow-spec-with-openspec-schema --json` → 均退出码 0。
- `git diff --check origin/main...HEAD` → 通过。
- 全量 `pytest`：按用户明确批准跳过；此前超时退出码为 `124`，未宣称通过。

## 结论

**BLOCKED。** 当前盘面已关闭此前 marker 原子性、双合法绑定、缺键、schema 行 inline comment、兄弟 schema 与 BOM 重复键问题；但 D2、D3 仍会在正常迁移/安装输入下造成 schema 未启用或引用不存在的 schema，修复并补回归后需再次复审。
