# Code review · domain 镜 · fix6

审查对象：`align-sdflow-spec-with-openspec-schema`
审查盘面：`423f9a8cb117e7bcb75a5b9652e3c974cd5d256b`
范围：project-local schema 的分发、迁移前置及 `config.yaml` 窄改写。仅只读复审；未修改业务代码或 `code-review-report.md`。

## 范围与清单

本 change 不命中 TG-01/02/03 的技术栈领域 delta，按通用 `CR-01` 至 `CR-09` 审核，重点核对 `spec-workflow` 的 project-local schema 下发、迁移前置、CLI 版本门与既有配置保留契约。

## Findings（置信 ≥80）

### D5 · 高 · CR-02 / CR-09 · 置信度 96

当既有合法 YAML 配置带 `%YAML 1.2` 指令和 document start、但没有顶层 `schema:` 时，`_set_schema_key()` 会在 YAML 指令之前插入 schema 键。YAML 指令必须处于文档开头，改写后的配置因此不可解析；安装器会报告已更新，但下一次 OpenSpec 命令直接失败。

- 证据：[`_set_schema_key()`](../../../../sdflow-init/scripts/init.py:411) 仅跳过空行和注释，遇到 `%YAML 1.2` 立即停止扫描，`insert_at` 保持 `0`；随后 [`_atomic_write()`](../../../../sdflow-init/scripts/init.py:422) 写出 `schema:` 在 YAML directive 之前的文件。
- 独立复现：输入 `%YAML 1.2\n--- # config\ncontext: keep\n` 后调用 `handle_config(..., "update", schema="sdflow-spec-driven")`，实际字节为 `schema: sdflow-spec-driven\n%YAML 1.2\n--- # config\ncontext: keep\n`。
- CLI 证据：以该结果作为临时仓 `openspec/config.yaml` 执行 `openspec status --json`，退出码 `1`，返回 `invalid_store_pointer`，并指出 config 无法作为 YAML 读取。
- 影响：这是现有消费仓的合法 YAML 形态；版本门通过时，`sdflow-init update` 会把原本可读的配置改为不可读，违背「只窄改 schema 单键、保留用户内容」以及 update 后可继续使用 OpenSpec 的目标。
- 建议：缺 schema 时解析并保留 YAML directive 序列（包括可选 `%YAML` / `%TAG` 和随后的 document start），把新键插入第一个 document start 之后；补 LF、CRLF、BOM、注释前缀与 YAML directive 组合的字节级回归，并用 `openspec status --json` 验证产物可读。

## 已验证

- 已复核此前修复的原子 marker、内置/fork 合法绑定、缺 schema、inline/comment-only 注释、BOM、带前缀注释和空行的 document start、兄弟 schema 保留，以及权威 schema 或其被引用模板缺失时 fail-loud 的路径。
- 独立运行：`python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py`，结果为 `125 passed, 1 skipped`，退出码 `0`。
- `git diff --check` 与 `git diff --check origin/main...HEAD` 均通过。
- 全量 `pytest` 按用户明确批准跳过；此前真实结果为超时退出码 `124`，未记为通过。

## 结论

**BLOCKED。** 当前盘面已覆盖此前发现的 schema 迁移、配置写入、document start 与权威 schema 完整性边界，但 D5 仍会将带 YAML directive 的合法配置写坏。修复并补回归后需要再次领域复审。
