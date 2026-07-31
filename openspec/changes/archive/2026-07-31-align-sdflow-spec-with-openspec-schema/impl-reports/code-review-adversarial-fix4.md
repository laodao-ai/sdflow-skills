# Code review · adversarial fix4

审查对象：`align-sdflow-spec-with-openspec-schema`

被审盘面：`7bc8d6947c644596d35e7ef65cd9c8a089c6005c`

本轮按对抗镜只读复审；未修改业务代码或 `code-review-report.md`。

## Findings（置信 ≥80）

### A2 · 高 · CR-02 / CR-09 · comment-only `schema:` 行被改写为错误的 schema 名

- 证据：`sdflow-init/scripts/init.py:344-357` 的 `_set_schema_key()` 把冒号后的全部空白归入第一个捕获组，再直接拼接目标 schema 与剩余 suffix。对于合法的 `schema:    # 注释`，`#` 前的分隔空白已被消费，写出后变成 `schema:    sdflow-spec-driven# 注释`。
- 独立复现：临时项目执行 `handle_config(..., "update", schema="sdflow-spec-driven")` 后得到上述字节；`_schema_from_config()` 返回 `sdflow-spec-driven`，却掩盖了 YAML 将 `#` 视为值的一部分而不是注释的风险。
- 运行期后果：配置实际解析出的 schema 名不再是受管 fork，后续 OpenSpec CLI 的 schema 查找会失败或回退；安装器却报告更新成功。这是已有 `schema:` 但 value 为空、仅保留说明性注释时的正常配置路径，未被现有“带值 inline comment”测试覆盖。
- 建议：将“value 后的分隔空白”和“冒号后的缩进”分开捕获；在空值且 suffix 以 `#` 开始时，写入 schema 后必须保留至少一个空白。补充 LF、CRLF 与 BOM 的 comment-only schema 回归，并用实际 YAML/CLI 读取断言目标 schema 名。
- 置信：96%。字节级复现稳定，且 YAML 注释需由空白与 plain scalar 分隔。

## 已核验项

- 迁移 marker 原子发布、截断 marker fail-loud、内置与 fork 两种合法绑定、缺 schema 键插入、带值 inline comment、兄弟 schema 保留及 BOM 重复键均仍存在相应实现与回归。
- 当前独立定向聚合：`python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py hack/tests/test_task3_phase_c_contract.py` → `73 passed, 1 skipped`，退出码 0。
- `git diff --check origin/main...HEAD` 与工作树 `git diff --check` 均通过。
- 全量 `pytest`：按用户明确批准跳过；此前真实结果为超时退出码 `124`，未记为通过。

## 结论

**BLOCKED。** A2 会让合法的 comment-only `schema:` 配置被安装器静默改写为错误 schema 名；修复并补回归后需要再次对抗复审。
