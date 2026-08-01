# Tasks · shared-yaml-subset-parser

## 1. 依赖预检系统 [R1, R2]

- [ ] 1.1 `setup.sh` 新增 `check_dependencies()` 函数，检测 python3/git/yq/openspec/pytest
- [ ] 1.2 yq 检测含 mikefarah vs kislyuk 区分（`--version` 输出含 `mikefarah` 标志）
- [ ] 1.3 缺失时按平台输出安装指引（brew/winget/snap）
- [ ] 1.4 调用点：`install_sdflow` 之后、门禁检查之前
- [ ] 1.5 既有 python3 检测逻辑迁入 `check_dependencies()`（统一入口，不重复）

## 2. init.py YAML 解析改为 yq [R3, R4, R6, R7, R9, R10]

- [ ] 2.1 新增 `_yq()` 薄封装（含 `shutil.which` 检测 + fail-loud）
- [ ] 2.2 `_schema_from_config` → `_yq('.schema', config_path, default=BUILTIN_SCHEMA)`
- [ ] 2.3 `_set_schema_key` → `_yq(f'.schema = "{schema}"', config_path, in_place=True)`
- [ ] 2.4 `_marker_schema` → `_yq('.schema', marker_path)` + 校验逻辑保留
- [ ] 2.5 `_find_top_level_block` / `_second_level_keys` → `_yq` 按键路径读取
- [ ] 2.6 `_parse_model_tiers_block` → `_yq('.model-tiers', ...)` + Python dict 验证（fleet/tier 键集校验、越域键检测、畸形头检测）
- [ ] 2.7 `lint_config` 的 metrics 读取 → `_yq('.metrics.enabled', ...)`
- [ ] 2.8 `_validate_schema_authority` → `_yq('.template', schema_yaml_path)`
- [ ] 2.9 删除已被替代的手搓函数，更新零依赖声明注释
- [ ] 2.10 跑 `pytest sdflow-init/tests/` 全绿

## 3. impl_route.py YAML 解析改为 yq [R3, R5, R6, R7, R10]

- [ ] 3.1 新增 `_yq()` 薄封装
- [ ] 3.2 `read_config_pipeline` → `_yq('."impl-pipeline"', config_path, default="superpowers")` + 非法值校验保留
- [ ] 3.3 `read_plan_marker` → `_yq('."impl-pipeline"', plan_path, front_matter=True)` + `RouteStop` 逻辑保留
- [ ] 3.4 删除 `_extract_scalar` / KEY_RE / FRONT_DELIM
- [ ] 3.5 跑 `pytest sdflow-implement/tests/` 全绿

## 4. ship_gate.py frontmatter 解析改为 yq [R5, R6, R7, R10]

- [ ] 4.1 新增 `_yq()` 薄封装
- [ ] 4.2 `parse_ship_gate_frontmatter` → `_yq('.ship-gate', path, front_matter=True)` + `FIELD_VALIDATORS` 校验保留
- [ ] 4.3 保留错误分类（`duplicate-key` / `out-of-domain` / `bad-type` / `tab-indent`）——在 yq 读出的 dict 上验证
- [ ] 4.4 跑 `pytest sdflow-ship/tests/` 全绿

## 5. anchor_lint.py YAML 解析改为 yq [R3, R7, R10]

- [ ] 5.1 `read_metrics_enabled` → `_yq('.metrics.enabled', config_path, default=False)`
- [ ] 5.2 同步更新 bundle 副本（`sdflow-init/assets/workflow/tools/anchor_lint.py`）
- [ ] 5.3 跑 `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 全绿

## 6. roadmap_writeback_draft.py + sad_schema.py frontmatter 改为 yq [R5, R6, R7, R10]

- [ ] 6.1 `roadmap_writeback_draft.py`: `read_verify_state` → `_yq('.ship-gate.verify', path, front_matter=True)`
- [ ] 6.2 `sad_schema.py`: `parse_frontmatter` → `_yq('.', path, front_matter=True)` + `TOP_KEYS` / `FACT_KEYS` 白名单校验保留
- [ ] 6.3 跑 `pytest sdflow-done/tests/` 和 `pytest sdflow-architecture/tests/` 全绿

## 7. ADR + 收尾 [R8, R9]

- [ ] 7.1 新增 `openspec/adr/0036-yq-replaces-hand-rolled-yaml.md`
- [ ] 7.2 全仓 `pytest` 全绿
- [ ] 7.3 `grep` 验证目标脚本中无手搓 YAML 解析函数残留（R10 scenario）
