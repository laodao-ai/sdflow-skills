### Task 3: ship_gate.py + impl_route.py 的 YAML 解析改为 yq

**Blocked-by:** 2
**R-ID:** R3, R5, R6, R7, R9, R10, R11, R13

`ship_gate.py`：`parse_ship_gate_frontmatter` 的 YAML 解析核心改为 `_yq('.ship-gate', path, front_matter=True)`，保留 `FIELD_VALIDATORS` / `_coerce_ship_gate_value` / `bad-type` / `out-of-domain` 业务校验。保留 duplicate-key/tab-indent 原始文本预扫描（在 yq 调用之前）。写操作（frontmatter 回写）用 `strenv()` 环境变量传值。

`impl_route.py`：`read_config_pipeline` 改为 `_yq('."impl-pipeline"', config_path)`，`read_plan_marker` 改为 `_yq('."impl-pipeline"', plan_path, front_matter=True)`。删除 `_extract_scalar` / `KEY_RE` / `FRONT_DELIM`。yq 非零退出映射为 `RouteStop`（damaged 语义）。

两个脚本有互相 import（`impl_route` 从 `ship_gate` import `FenceTracker`，`ship_gate` 惰性 import `impl_route` 的 `parse_blocked_by`），需一起改确保兼容。

- [ ] `ship_gate.py` 的 frontmatter YAML 解析核心已替换为 `_yq()` 调用
- [ ] `ship_gate.py` 保留 duplicate-key/tab-indent 原始文本预扫描（R11），在 yq 读取之前执行
- [ ] `ship_gate.py` 的 `FIELD_VALIDATORS` / 业务校验保留在 Python dict 上执行
- [ ] `ship_gate.py` 写操作通过环境变量传值（R13）
- [ ] `impl_route.py` 的 config 读取和 plan marker 读取已替换为 `_yq()` 调用
- [ ] `impl_route.py` 删除 `_extract_scalar` / `KEY_RE` / `FRONT_DELIM`
- [ ] 两个脚本的互相 import 关系正常工作
- [ ] `pytest sdflow-ship/tests/` 全绿
- [ ] `pytest sdflow-implement/tests/` 全绿

