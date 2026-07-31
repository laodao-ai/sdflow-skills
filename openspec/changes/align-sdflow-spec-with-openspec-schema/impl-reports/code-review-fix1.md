# Code review fix1 — align-sdflow-spec-with-openspec-schema

修复范围：仅处理 `code-review-domain.md` 与 `code-review-adversarial.md` 已采纳的 schema 分发、配置切换和在途 change 迁移阻断项；未改 `code-review-report.md`，未创建 checkpoint。

## 已修复的 findings

1. `[impl-review-fix]` `migrate_changes()` 改为同目录临时文件写入、`flush()` + `fsync()` 后 `os.replace()` 原子发布。已有 `.openspec.yaml` 会校验为唯一、可解析且值等于预期旧内置 `spec-driven`；截断、畸形或值不匹配均 fail-loud。重跑会接受此前已成功写入的旧 schema 锁，不会因全局配置已切到 fork 而误报异常。
2. `[impl-review-fix]` `_set_schema_key()` 在缺失顶层 `schema:` 时确定性插入该行（保留既有内容与换行风格）；`handle_config()` 只有实际完成后才返回 `updated`。
3. `[impl-review-fix]` `copy_bundle()` 仅收敛 `openspec/schemas/sdflow-spec-driven/`，不再删除 `schemas/` 下消费仓拥有的兄弟 schema。
4. `[impl-review-fix]` `_set_schema_key()` 只替换 schema value，保留 inline comment、空白、行尾及其它配置字节。

## 回归验证

- `python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py`
  - 结果：`67 passed, 1 skipped`（退出码 0）。
- `git diff --check`
  - 结果：通过（退出码 0）。
- 全量 `pytest`
  - 按用户明确授权跳过；此前超时退出码为 `124`，未宣称通过。

## 结论

四项 BLOCKED finding 均已修复并有定向回归覆盖，待按 `sdflow-code-review` 流程复审。
