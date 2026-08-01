---
impl-pipeline: tickets
---

## Global Constraints

以下逐字摘自本 change design.md / spec.md 的 MUST / MUST NOT / SHALL / Compliance 条款：

- 零依赖不变量：yq 是外部二进制（同 git），subprocess 调用不违反 `MUST NOT import yaml`
- 基准 5（无界不手搓）：yq 是该基准的正解实例——让工具自己回答自己的语法
- GC-2 边界锁：不受影响——`_yq()` 封装各脚本内联，不跨脚本 import
- 每个脚本的 `_yq()` 薄封装 MUST 含：`shutil.which` 检测 + `--version` 身份校验（`mikefarah`）+ 进程内缓存 + fail-loud + `encoding="utf-8", errors="replace"`
- yq 执行非零退出 MUST raise（转发 stderr），即使调用方传了 default 也不吞——「键不存在」（exit 0 + stdout=null）与「解析失败」（exit≠0）MUST 是两条不同分支 [R7/F2]
- 写操作值传递 MUST NOT 用 f-string 插值，MUST 用环境变量 `strenv()` [R13/F7]
- 各脚本的业务逻辑（字段验证、状态机、枚举校验）MUST 保留在 Python 侧，仅 YAML 解析委托给 yq [R6]
- `ship_gate.py` MUST 保留 duplicate-key/tab-indent 原始文本预扫描（在 yq 读取之前），yq 对重复键静默取最后值 [R11]
- frontmatter 模式下 `_yq()` 返回后校验顶层结构类型须为 dict，非 dict 视为坏块 raise 错误 [R5/F4]
- `resolve-models.sh` 不改（shell 脚本，Non-Goal）
- 不把 yq 打包进 `~/.sdflow/bin/`，全局安装由包管理器管理
- 不重构依赖管理为框架，只做检测 + 提示
- 不扩展到非 YAML 格式的解析优化
- 新增 Python 入口脚本须带 4 行 `reconfigure` 前导（本 change 不新增入口脚本，不触发）

### Task 1: setup.sh 依赖预检系统

**Blocked-by:** none
**R-ID:** R1, R2

`setup.sh` 新增 `check_dependencies()` 函数，在 `install_sdflow` 之后、门禁检查之前统一检测并报告全部运行依赖（python3 ≥ 3.7 / git / yq / openspec / pytest）。既有 python3 检测逻辑迁入此函数。yq 检测含 mikefarah vs kislyuk 区分（`--version` 输出含 `mikefarah`）。缺失时按平台输出安装指引（brew/winget/snap）。不中止 setup.sh（降级汇报）。

- [ ] `setup.sh` 运行后输出每项依赖一行状态（✓/✗/·）
- [ ] yq 已安装但为 kislyuk/yq 时输出警告 + 正确版本安装指引
- [ ] yq 未安装时输出 ✗ + 三平台安装命令
- [ ] 必要依赖缺失时在末尾汇总安装指引，但不中止 setup.sh
- [ ] 既有 python3 检测逻辑已从原位迁入 `check_dependencies()`，不重复

### Task 2: anchor_lint.py 的 YAML 解析改为 yq

**Blocked-by:** none
**R-ID:** R3, R7, R9, R10

两份 `anchor_lint.py`（`openspec/workflow/tools/anchor_lint.py` 与 `sdflow-init/assets/workflow/tools/anchor_lint.py`）的 `read_metrics_enabled` 函数替换为 `_yq('.metrics.enabled', config_path, default=False)`。新增 `_yq()` 薄封装（含身份校验 + fail-loud）。删除被替代的手搓 YAML 读取代码。同步更新零依赖声明注释。两份副本保持字节一致。

- [ ] `read_metrics_enabled` 改为通过 `_yq()` 读取
- [ ] `_yq()` 封装含 `shutil.which` 检测 + `--version` 身份校验 + 进程内缓存 + fail-loud
- [ ] 两份 `anchor_lint.py` 副本字节一致
- [ ] `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 全绿
- [ ] 零依赖声明注释已更新

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

### Task 5: 剩余脚本 + ADR + CI + golden test

**Blocked-by:** 2,3,4
**R-ID:** R5, R6, R7, R8, R9, R10, R12

`roadmap_writeback_draft.py`：`read_verify_state` 改为 `_yq('.ship-gate.verify', path, front_matter=True)` + 保留 `PASS`/`FAIL` 枚举校验。`sad_schema.py`：`frontmatter_end` / `parse_frontmatter` 改为 `_yq('.', path, front_matter=True)` + 保留 `TOP_KEYS` / `FACT_KEYS` / `FACT_VALUES` 白名单校验。

新增 ADR `openspec/adr/0036-yq-replaces-hand-rolled-yaml.md`（Context / Decision / Consequences 三节）。CI `mechanical-gates.yml` 显式安装 + 钉版本 yq。新增 `_yq()` 一致性 golden test 检查 7 份封装核心逻辑字节一致。重写依赖手搓逐行扫描器诊断的测试断言（yq 方案下精确诊断不可复现）。`grep` 验证目标脚本中无手搓 YAML 解析函数残留。

- [ ] `roadmap_writeback_draft.py` 的 frontmatter 解析已替换为 `_yq()` + 枚举校验保留
- [ ] `sad_schema.py` 的 frontmatter 解析已替换为 `_yq()` + 白名单校验保留
- [ ] `pytest sdflow-done/tests/` 全绿
- [ ] `pytest sdflow-architecture/tests/` 全绿
- [ ] ADR-0036 存在且含 Context / Decision / Consequences 三节
- [ ] `mechanical-gates.yml` 显式安装 yq（钉版本）
- [ ] `_yq()` golden test 检查 7 份封装一致性
- [ ] `grep` 验证目标脚本无手搓 YAML 解析函数残留（R11 预扫描除外）

### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4,5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落 `impl-reports/task6-verification.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
