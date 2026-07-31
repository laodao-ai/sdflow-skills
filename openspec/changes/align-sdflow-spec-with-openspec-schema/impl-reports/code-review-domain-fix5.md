# Code review · domain 镜 · fix5

审查对象：`align-sdflow-spec-with-openspec-schema`  
审查盘面：`5db85c8ce3562f07665006fd55c66320656498b5`  
范围：project-local schema 的分发、迁移前置和 `config.yaml` 窄改写。仅只读复审；未修改业务代码或 `code-review-report.md`。

## 范围与清单

本 change 不命中 TG-01/02/03 的技术栈领域 delta，按通用 `CR-01` 至 `CR-09` 审核，重点核对 `spec-workflow` 的「schema（`schema.yaml` + `templates/`）随 bundle 下发、迁移前置、CLI 版本门」Requirement。

## Findings（置信 ≥80）

### D4 · 高 · CR-02 / CR-09 · 置信度 97

权威 schema 的检查只验证 `schema.yaml` 存在，未验证该 YAML 中各 artifact 引用的模板是否齐全。若权威源缺少任一模板，`copy_bundle()` 仍会删除旧 fork、复制不完整目录；随后 `run()` 继续把 `config.yaml` 切换到 `sdflow-spec-driven`。消费仓因此指向一个无法被 OpenSpec 使用的 schema，但安装汇总会报成功。

- 证据：[`copy_bundle()`](../../../../sdflow-init/scripts/init.py:231) 的前置条件仅为 `schema.yaml` 是普通文件；复制后同样只检查目标 `schema.yaml`。当前 schema 的四个 artifact 均声明了 `template:`，而 [`run()`](../../../../sdflow-init/scripts/init.py:1019) 在复制完成后无完整性门，直接调用 `handle_config(..., schema=target_schema)`。
- 独立复现：将真实权威 schema 复制到临时消费仓源目录后删除 `templates/spec.md`，再执行 `copy_bundle(..., include_schema=True)` 与 `handle_config(..., "update", schema="sdflow-spec-driven")`。结果为 config 已切换、目标 `templates/spec.md` 不存在；随后真实 `openspec schema validate sdflow-spec-driven` 退出码为 `1`。
- 影响：这属于权威资产不完整的确定性失败路径，违反 schema 权威源由 `schema.yaml + templates/` 共同构成、缺失权威 schema 应 fail-loud 的契约。下一个 change 在生成 `specs` artifact 时才暴露错误，根因已被此前的安装成功信息掩盖。
- 建议：在删除消费仓 fork 或切换 config 前，验证权威源包含 `schema.yaml` 及 schema 中所有 `template:` 引用的文件；任一缺失则抛错且保持现有 config。补一条删除 `templates/spec.md`（或任意被引用模板）的回归，断言 `run(update)` 不切换 config。

## 已验证

- 之前修复的原子 marker、内置/fork 合法绑定、缺顶层 `schema:`、带值和 comment-only inline comment、UTF-8 BOM、带注释 document start、兄弟 schema 保留、以及 `schema.yaml` 整体缺失 fail-loud，均仍可在实现与回归中找到对应覆盖。
- `python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py`：`123 passed, 1 skipped`，退出码 `0`。
- `openspec schema validate sdflow-spec-driven`、目标 change 的 `status --json`、`instructions specs --json`、`instructions tasks --json`：均退出码 `0`。
- 工作树 `git diff --check`：通过。全量 `pytest` 按用户明确批准跳过；此前真实结果为超时退出码 `124`，未记为通过。

## 结论

**BLOCKED。** fix5 已关闭此前已知的 marker、YAML 单键改写、document-start、BOM、兄弟 schema 与完全缺失权威目录问题；D4 仍会把缺少被引用模板的损坏 schema 静默切入 config。修复并补回归后需再次领域复审。
