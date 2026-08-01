# Spec · yq-yaml-operations

## ADDED Requirements

### Requirement: R1 — yq 依赖检测

`setup.sh` 的 `check_dependencies()` 函数 MUST 检测 yq 可用性。

#### Scenario:
- WHEN yq 已安装且为 mikefarah/yq THEN 输出 `✓ yq (version)` 
- WHEN yq 已安装但为 kislyuk/yq（pip 版） THEN 输出警告 + 安装指引
- WHEN yq 未安装 THEN 输出 `✗ yq` + 按平台的安装命令（brew/winget/snap）
- WHEN yq 未安装 THEN `setup.sh` 不中止（降级汇报，与 skipped 范式一致）

### Requirement: R2 — 统一依赖预检

`setup.sh` 运行时 MUST 检测并报告全部运行依赖：python3 ≥ 3.7 / git / yq / openspec（可选）/ pytest（开发可选）。

#### Scenario:
- WHEN `setup.sh` 执行完毕 THEN 在汇总区域输出依赖检测结果（每项一行 ✓/✗/·）
- WHEN 存在必要依赖缺失 THEN 在汇总末尾输出安装指引
- WHEN 所有必要依赖满足 THEN 不额外输出（只有 ✓ 行）

### Requirement: R3 — config.yaml 读操作改为 yq

所有从 `openspec/config.yaml` 读取 YAML 值的脚本 MUST 使用 yq subprocess 调用。

#### Scenario:
- WHEN `init.py` 读取 `schema` 键 THEN 使用 `yq '.schema' config.yaml`
- WHEN `init.py` 读取 `model-tiers` 块 THEN 使用 `yq -o json '.model-tiers' config.yaml` + `json.loads()`
- WHEN `impl_route.py` 读取 `impl-pipeline` 键 THEN 使用 `yq '."impl-pipeline"' config.yaml`
- WHEN `anchor_lint.py` 读取 `metrics.enabled` THEN 使用 `yq '.metrics.enabled' config.yaml`
- WHEN 键不存在或被注释 THEN yq 返回 `null`，脚本使用 default 值
- WHEN config.yaml 含界外 YAML 构造（锚点、多文档等） THEN yq 正常处理（无需 reject_unbounded）

### Requirement: R4 — config.yaml 写操作改为 yq

`init.py` 的 `_set_schema_key` MUST 改为 `yq -i` 写操作。

#### Scenario:
- WHEN 设置 schema 值 THEN 使用 `yq -i '.schema = "value"' config.yaml`
- WHEN 写入后 THEN 原文件中的注释保留（yq `-i` 默认行为）
- WHEN 写入后 THEN 其他键值不变

### Requirement: R5 — Markdown frontmatter 读操作改为 yq

所有从 Markdown 文件读取 YAML frontmatter 的脚本 MUST 使用 yq `--front-matter=extract`。

#### Scenario:
- WHEN `ship_gate.py` 读取报告 frontmatter 的 ship-gate 块 THEN 使用 `yq --front-matter=extract -o json '.ship-gate' report.md`
- WHEN `impl_route.py` 读取 plan frontmatter 的 impl-pipeline 键 THEN 使用 `yq --front-matter=extract '."impl-pipeline"' plan.md`
- WHEN `roadmap_writeback_draft.py` 读取 verify-report 的 ship-gate.verify 键 THEN 使用 `yq --front-matter=extract '.ship-gate.verify' report.md`
- WHEN `sad_schema.py` 读取 SAD frontmatter THEN 使用 `yq --front-matter=extract -o json '.' sad.md`
- WHEN 文件无 frontmatter THEN yq 返回 `null`，脚本使用 default 值
- WHEN frontmatter 未闭合 THEN yq 非零退出，脚本 raise 错误

### Requirement: R6 — 业务逻辑与 YAML 解析分离

各脚本的业务逻辑（字段验证、状态机、枚举校验）MUST 保留在 Python 侧，仅 YAML 解析委托给 yq。

#### Scenario:
- WHEN `ship_gate.py` 读到 frontmatter THEN `FIELD_VALIDATORS` 校验在 Python dict 上执行
- WHEN `init.py` 读到 model-tiers THEN fleet/tier 键验证（越域键、畸形头）在 Python dict 上执行
- WHEN `sad_schema.py` 读到 frontmatter THEN `TOP_KEYS` / `FACT_KEYS` 白名单校验在 Python dict 上执行
- WHEN `impl_route.py` 遇到非法 impl-pipeline 值 THEN 仍然 raise `RouteStop`

### Requirement: R7 — yq 不可用时 fail-loud

所有使用 yq 的脚本 MUST 在 yq 不可用时给出明确错误和安装指引。

#### Scenario:
- WHEN `shutil.which("yq")` 返回 None THEN 打印三平台安装命令到 stderr 并 `sys.exit(1)`
- WHEN yq 执行非零退出 THEN 转发 yq 的 stderr 到调用方（而非静默降级）

### Requirement: R8 — ADR 记录

MUST 新增 `openspec/adr/0036-yq-replaces-hand-rolled-yaml.md` 记录引入 yq 外部依赖的决策。

#### Scenario:
- WHEN change 完成 THEN ADR 文件存在且包含：Context / Decision / Consequences 三节

## MODIFIED Requirements

### Requirement: R9 — 零依赖声明更新

各脚本的零依赖声明注释 MUST 更新为反映 yq 外部工具依赖（非 Python import 依赖）。

#### Scenario:
- WHEN `init.py:534` 的声明 THEN 改为 `MUST NOT import yaml — YAML 解析通过 yq 外部工具完成`
- WHEN 其他脚本有类似声明 THEN 同步更新

## REMOVED Requirements

### Requirement: R10 — 删除手搓 YAML 解析代码

7 个脚本中的全部手搓 YAML 解析函数 MUST 删除（见 design §2 改动清单）。

#### Scenario:
- WHEN 实现完成 THEN `grep -rn 'def _strip_inline_comment\|def _find_top_level_block\|def _second_level_keys\|def _schema_from_config\|def _set_schema_key\|def _marker_schema\|def _parse_model_tiers_block\|def _extract_scalar\|def read_metrics_enabled\|def frontmatter_end\|def read_verify_state\|def parse_ship_gate_frontmatter'` 在目标脚本中零命中
- WHEN 实现完成 THEN 既有测试全绿
