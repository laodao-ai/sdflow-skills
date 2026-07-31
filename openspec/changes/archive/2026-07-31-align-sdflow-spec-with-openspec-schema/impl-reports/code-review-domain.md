# Code review · domain 镜

审查对象：`align-sdflow-spec-with-openspec-schema`
审查盘面：`bed0c093eac91b0e998e0d623f8011c186f00e2e`
宿主：Codex；本镜为 fresh、只读审查，未改业务代码，未写总报告。

## 范围与清单

覆盖 project-local schema 的分发、CLI 版本门、在途 change 迁移、`sdflow-spec` CLI 载荷契约和同步文档。技术栈领域清单未命中 TG-01/02/03，故逐项核对通用 `CR-01` 至 `CR-09`；同时以本 change 的 `SW-SCHEMA` / `SA-05` / `SA-17` 为契约。

## Findings

### F1 · 高 · CR-02 · 置信度 96

`copy_bundle()` 在版本门通过时删除整个消费仓 `openspec/schemas/`，会抹掉不属于本 change 的 project-local schema。

- 证据：[`sdflow-init/scripts/init.py:256`](D:/02-laodao-ai/sdflow-skills/sdflow-init/scripts/init.py:256) 至 [`:260`](D:/02-laodao-ai/sdflow-skills/sdflow-init/scripts/init.py:260) 对 `openspec/schemas/` 直接 `rmtree()` 后复制全部 bundle schema。
- 契约：`SW-SCHEMA` 明确托管、整删重拷的目标是 `openspec/schemas/<name>/`，不是父目录；其它 schema 可以是消费项目自有的 schema。
- 影响：任一已有的第二 schema 会在普通 `sdflow-init update` 中被无提示删除，且无回滚路径。这违反了本变更的单一 fork 下发范围。
- 建议：只整删重拷 `openspec/schemas/sdflow-spec-driven/`；保留父目录和其它 schema。相应把当前仅断言 `old-schema` 被删除的测试改为断言目标 fork 内孤儿被清理、兄弟 schema 保留。
- 采纳：是。该路径在支持 CLI 的所有消费仓执行，属于实际数据丢失风险。

### F2 · 高 · CR-02 · 置信度 94

现有 `config.yaml` 缺失显式 `schema:` 键时，版本门通过后的 update 不会插入目标键，却会报告已更新；结果是 consumer 继续使用内置 schema，核心 fork 不会生效。

- 证据：[`sdflow-init/scripts/init.py:324`](D:/02-laodao-ai/sdflow-skills/sdflow-init/scripts/init.py:324) 至 [`:334`](D:/02-laodao-ai/sdflow-skills/sdflow-init/scripts/init.py:334) 将缺键解释为 `spec-driven`；但 [`:337`](D:/02-laodao-ai/sdflow-skills/sdflow-init/scripts/init.py:337) 至 [`:361`](D:/02-laodao-ai/sdflow-skills/sdflow-init/scripts/init.py:361) 找不到行时只返回 `False`，[`handle_config()` 的 `:369`](D:/02-laodao-ai/sdflow-skills/sdflow-init/scripts/init.py:369) 至 [`:371`](D:/02-laodao-ai/sdflow-skills/sdflow-init/scripts/init.py:371) 忽略这个返回值并报 `updated`。
- 契约：`SW-SCHEMA` 要求版本门通过后切换 consumer 的 `config.yaml` 到 fork；未写键本身表示 CLI 继续采用默认 `spec-driven`，不是已切换。
- 建议：`_set_schema_key()` 在未找到顶层键时保留既有字节并确定性插入一行 `schema: sdflow-spec-driven`，且为该旧配置形态加回归测试。
- 采纳：是。该情形直接使目标态静默退回内置 schema，与本 change 试图避免的静默失效相同。

### F3 · 中 · CR-02 / CR-09 · 置信度 89

即使存在 `schema:` 键，带 inline comment 的用户配置也会在切换时被整行覆盖，违背「仅改 schema 单键、其余内容 byte-identical」的迁移承诺。

- 证据：[`sdflow-init/scripts/init.py:345`](D:/02-laodao-ai/sdflow-skills/sdflow-init/scripts/init.py:345) 的正则命中整行，而 [`:347`](D:/02-laodao-ai/sdflow-skills/sdflow-init/scripts/init.py:347) 重写为不含原行后缀的字符串；例如 `schema: spec-driven # legacy` 会丢失 `# legacy`。
- 建议：只替换 YAML value 区间，保留 `#` 后的字节；新增 inline-comment 回归用例。现有测试只覆盖独立注释行，未覆盖此路径。
- 采纳：是。它不是运行时功能阻断，但会静默改写用户文档，和 installer 的窄范围 patch 契约不符。

## 已裁掉 / 未采纳

- X1（置信度 100）：`openspec schema validate sdflow-spec-driven` 成功，schema 四件套和 `requires` 边未发现结构性违约，裁掉为 finding。
- X2（置信度 100）：定向测试 `sdflow-init/tests/test_init.py`、`sdflow-init/tests/test_task5_regression.py`、`hack/tests/test_task3_phase_c_contract.py` 为 `65 passed, 1 skipped`；不能反驳上述三条未覆盖的消费仓形态，故不作通过依据以外的结论。
- X3（置信度 99）：`git diff --check bf026aa..bed0c09` 报告报告文件 EOF 空行与 `openspec/workflow/reference/Token_Saving_Strategies.md` 的 trailing whitespace。它们是质量问题，但不属于本镜 schema/migration/CLI/docs 行为 finding，已移交总审的范围与质量汇总。

## 验证边界

- 已运行：上述定向 pytest（`65 passed, 1 skipped`）；`openspec schema validate sdflow-spec-driven`（通过）。
- 全量 `pytest`：用户已明确批准超时后跳过；本镜未等待、未将其标为通过。

## 结论

**BLOCKED。** F1 与 F2 都会导致普通消费仓的 schema 分发/启用发生破坏性或静默失效，修复并补回归测试后应重新进行 domain 镜审查。
