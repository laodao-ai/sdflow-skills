# Code review · domain 镜 · fix8

审查对象：`align-sdflow-spec-with-openspec-schema`
审查盘面：`dc67af388a471acbe36d95a83ac7eab65948c304`
范围：project-local schema 的分发、在途 change migration、`config.yaml` 的受限写入，以及权威 schema/template 完整性。仅做只读复审；未修改业务代码或 `code-review-report.md`。

## 清单与复核范围

本 change 不命中 TG-01/02/03 的技术栈领域 delta；按通用 `CR-01` 至 `CR-09` 复审，重点核对：

- `CR-01/CR-02`：版本门、migration marker、权威 schema/template 缺失与 config 切换失败路径必须 fail-loud；
- `CR-04`：marker/config 原子写入的发布顺序和临时文件清理；
- `CR-09`：BOM、LF/CRLF、键名与冒号之间空白、行内/仅注释 schema、前置注释/空行、YAML directives、document start，以及单键改写和回归覆盖。

## 已验证

- 当前 HEAD 与审查盘面完全一致：`dc67af388a471acbe36d95a83ac7eab65948c304`。
- `_schema_from_config()` 与 `_set_schema_key()` 同时接受顶层 `schema:` 和合法的 `schema :`。后者只替换该键的值，保留冒号前后的空白、CRLF、BOM、行内注释与其余字节；不会再插入第二个 schema 键。
- 缺失 schema 时，写入逻辑会跨过前置注释、空行及 `%YAML`/`%TAG` directives，在带可选注释的 `---` document start 后插入键。既有回归覆盖 comment-only schema、BOM、CRLF、前置注释与 directives 组合。
- `migrate_changes()` 对新 marker 使用原子写入；既有 marker 仅接受 `spec-driven` 或 `sdflow-spec-driven`，截断、未知或畸形 marker 会中止，不能继续切换 config。
- `copy_bundle()` 在删除已部署 fork 之前验证权威 `schema.yaml` 和全部 `template:` 引用；缺任一资产即停止，保留现有 fork 与 config，也不删除兄弟 schema。
- 定向聚合独立复跑：

  ```text
  python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py
  127 passed, 1 skipped
  ```

- 实际 CLI 验证均退出 `0`：`openspec schema validate sdflow-spec-driven`、`openspec status --change align-sdflow-spec-with-openspec-schema --json`、`openspec instructions specs --change align-sdflow-spec-with-openspec-schema --json` 与 `openspec instructions tasks --change align-sdflow-spec-with-openspec-schema --json`。该 change 的 marker 保持 `spec-driven` 是既有在途 change 绑定，项目默认 config 已为 `sdflow-spec-driven`，两者一致于迁移设计。
- 工作树 `git diff --check` 通过。全量 `pytest` 依用户明确批准跳过；此前实际超时退出码为 `124`，未记为绿色。

## 交付 caveat

`git diff --check origin/main...HEAD` 仍因已提交的 `impl-reports/code-review-domain-fix7.md` 第 3、4 行尾随空格返回 `2`。它不是本镜发现的 schema 实现缺陷，但若发布门以基线差异空白检查为准，仍须在汇总/历史镜处清理后才可放行。

## 结论

**PASS（领域镜，带发布面 caveat）**。本镜未发现新的 schema 分发、迁移、配置写入或权威资产完整性缺陷。全量测试状态仍是经用户批准的超时跳过，而非通过。
