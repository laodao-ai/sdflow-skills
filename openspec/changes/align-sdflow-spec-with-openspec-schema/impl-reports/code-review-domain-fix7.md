# Code review · domain 镜 · fix7

审查对象：`align-sdflow-spec-with-openspec-schema`
审查盘面：`fc24e97e9f4912644fb2d2a5404ae2cd5c5735ed`
范围：project-local schema 的分发、在途 change migration、`config.yaml` 的受限写入，以及权威 schema/template 完整性。仅做只读复审；未修改业务代码或 `code-review-report.md`。

## 清单与复核范围

本 change 不命中 TG-01/02/03 的技术栈领域 delta；按通用 `CR-01` 至 `CR-09` 复审，重点为：

- `CR-01/CR-02`：版本门、迁移 marker 和 schema 写入的失败路径必须 fail-loud，且不能在失败后切换配置；
- `CR-04`：marker/config 原子写入的临时文件清理与发布顺序；
- `CR-09`：BOM、行尾、注释、document start、`%YAML`/`%TAG` directives、既有 marker、缺失权威资产及缺失 template 的回归覆盖。

## 已验证

- `_set_schema_key()` 只替换首个顶层 `schema:` 的值；没有该键时会跨过 BOM、空行、注释和 YAML directives，并在 document start 后插入。`schema:    # comment` 保留合法的注释分隔，CRLF 和其它原始字节保留。
- `migrate_changes()` 以原子 marker 写入补写在途 change；已有 marker 仅接受 `spec-driven` 或 `sdflow-spec-driven`，截断、未知和畸形 marker 均中止，不会静默切换 config。
- `copy_bundle()` 在删除已部署 fork 前验证权威 `schema.yaml` 与所有 `template:` 引用；任一资产缺失会在 config 切换前失败，且不会删除兄弟 schema。
- 独立补测了三组 directives/document-start 组合（含前置注释、空行、UTF-8 BOM、CRLF、`%YAML` 和 `%TAG`）；均只产生一个 `schema:`，其位置在 `---` 后，且 `_schema_from_config()` 能读回 `sdflow-spec-driven`。
- 定向聚合执行：

  ```text
  python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_canonical_entry_sync.py
  126 passed, 1 skipped
  ```

- 工作树 `git diff --check` 通过。全量 `pytest` 按用户明确批准跳过；此前真实结果为超时退出码 `124`，未记为通过。

## 非本镜阻断提示

`git diff --check origin/main...HEAD` 仍因已提交的 `impl-reports/code-review-domain-fix6.md` 第 3、4 行尾随空格返回 `2`。这不是当前 schema 领域实现缺陷，也不影响本镜对 fix7 盘面的判断；若发布门采用基线差异空白检查，应由汇总/历史镜在合并前清理该既有报告问题。

## 结论

**PASS（领域镜）**。本镜未发现新的 schema 分发、迁移、配置写入或权威资产完整性缺陷；当前盘面可进入汇总裁决。全量测试仍为经用户批准的超时跳过，而非绿色结果。
