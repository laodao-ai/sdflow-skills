### Task 4: init.py 的 YAML 解析改为 yq

**Blocked-by:** 2
**R-ID:** R3, R4, R6, R7, R9, R10, R13

`init.py` 是改动量最大的脚本（~175 行手搓 YAML 解析）。`_schema_from_config` / `_set_schema_key` / `_marker_schema` / `_find_top_level_block` / `_second_level_keys` / `_parse_model_tiers_block` / `_valid_model_id` / `_validate_schema_authority` / `lint_config` 的 YAML 部分全部替换为 `_yq()` 调用。`_parse_model_tiers_block` 的业务逻辑（fleet_ctx 状态机、越域键检测、畸形头检测）从 YAML 解析中分离：yq 读到 JSON dict 后 Python 侧做键集验证。`_set_schema_key` 写操作用 `strenv()` 传值。删除全部被替代的手搓函数并更新零依赖声明注释。`lint_config` 入口前新增 `_check_yq()` 门。

- [ ] 全部手搓 YAML 解析函数已删除并替换为 `_yq()` 调用
- [ ] `_parse_model_tiers_block` 的业务逻辑在 yq 返回的 Python dict 上执行
- [ ] `_set_schema_key` 写操作通过环境变量传值（R13）
- [ ] `lint_config` 入口前有 yq 可用性检测
- [ ] 零依赖声明注释已更新
- [ ] `pytest sdflow-init/tests/` 全绿

