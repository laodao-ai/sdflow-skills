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

## 4. ship_gate.py frontmatter 解析改为 yq [R5, R6, R7, R10, R11]

- [ ] 4.1 新增 `_yq()` 薄封装（含身份校验 + encoding="utf-8"）
- [ ] 4.2 保留 duplicate-key/tab-indent 原始文本预扫描（R11）——在 yq 读取**之前**用轻量文本扫描检测重复顶层键和 tab 缩进，通过后再走 yq
- [ ] 4.3 `parse_ship_gate_frontmatter` 的 YAML 解析核心改为 `_yq('.ship-gate', path, front_matter=True)` + `FIELD_VALIDATORS` 校验保留
- [ ] 4.4 `bad-type` / `out-of-domain` 错误分类在 yq 读出的 dict 上验证（这两类不依赖原始文本）
- [ ] 4.5 跑 `pytest sdflow-ship/tests/` 全绿

## 5. anchor_lint.py YAML 解析改为 yq [R3, R7, R10]

- [ ] 5.1 `read_metrics_enabled` → `_yq('.metrics.enabled', config_path, default=False)`
- [ ] 5.2 同步更新 bundle 副本（`sdflow-init/assets/workflow/tools/anchor_lint.py`）
- [ ] 5.3 跑 `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 全绿

## 6. roadmap_writeback_draft.py + sad_schema.py frontmatter 改为 yq [R5, R6, R7, R10]

- [ ] 6.1 `roadmap_writeback_draft.py`: `read_verify_state` → `_yq('.ship-gate.verify', path, front_matter=True)`
- [ ] 6.2 `sad_schema.py`: `parse_frontmatter` → `_yq('.', path, front_matter=True)` + `TOP_KEYS` / `FACT_KEYS` 白名单校验保留
- [ ] 6.3 跑 `pytest sdflow-done/tests/` 和 `pytest sdflow-architecture/tests/` 全绿

## 7. ADR + 收尾 [R8, R9]

- [ ] 7.1 新增 `openspec/adr/0036-yq-replaces-hand-rolled-yaml.md`（含零依赖不变量精神收窄的代价陈述）[spec-review-amendment F13]
- [ ] 7.2 全仓 `pytest` 全绿
- [ ] 7.3 `grep` 验证目标脚本中无手搓 YAML 解析函数残留（R10 scenario，注意 `parse_ship_gate_frontmatter` 的 duplicate-key/tab-indent 预扫描部分由 R11 保留）

## 8. CI + golden test + 测试修订 [R12, spec-review-amendment F8/F9]

- [ ] 8.1 `mechanical-gates.yml` 显式安装 + 钉版本 yq [spec-review-amendment F8]
- [ ] 8.2 新增 `_yq()` 一致性 golden test——机械检查 7 份封装核心逻辑字节一致 [R12]
- [ ] 8.3 重写以下测试断言（yq 方案下精确诊断不可复现）[spec-review-amendment F9]：
  - `test_impl_route.py` 的 `unknown-value:` 前缀断言——改为验证 yq 整体解析失败的行为
  - 其他依赖手搓逐行扫描器局部诊断的断言——逐一核查并调整
- [ ] 8.4 proposal Success Metrics 增第5条：yq 安装 + 端到端读写验证 [spec-review-amendment C10]
