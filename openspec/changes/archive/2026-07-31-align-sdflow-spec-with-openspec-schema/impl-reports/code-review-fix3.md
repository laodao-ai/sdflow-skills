# Code review · fix3

修复对象：`align-sdflow-spec-with-openspec-schema`
基线盘面：`89e06a8c45aa353e90e92b4b587f46ee6f23be11`

## 已修复

- D1：`_schema_from_config()` 以 `utf-8-sig` 读取配置，将 UTF-8 BOM 视为编码前缀而非 YAML 键内容。
- D1：`_set_schema_key()` 在字节层分离并回写 BOM，只在正文中匹配首个顶层 `schema:`；CRLF、inline comment 与其余字节保持不变，不会插入第二个 schema 键。
- 回归：新增 BOM + CRLF + inline comment 的字节级测试，断言读取值正确、输出与预期字节完全一致、BOM 仍在且 `schema:` 仅出现一次。
- 发布面：清理 `code-review-adversarial-fix2.md` 已提交的两处尾随空白；未创建或修改 `code-review-report.md`。

## 验证

- `python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py` → `69 passed, 1 skipped`，退出码 0。
- `git diff --check` → 通过。
- 全量 `pytest`：按用户明确授权跳过；此前超时退出码 124，未记为通过。

发布范围的 `git diff --check origin/main...HEAD` 会在包含上述尾随空白修复的 checkpoint 后复跑并记录实际结果。
