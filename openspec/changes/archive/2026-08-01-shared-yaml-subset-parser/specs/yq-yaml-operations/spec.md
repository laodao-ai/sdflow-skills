# Spec · yq-yaml-operations

## ADDED Requirements

### Requirement: R1 — yq 依赖检测

`setup.sh` 的 `check_dependencies()` 函数 MUST 检测 yq 可用性。

#### Scenario:
- WHEN yq 已安装且为 mikefarah/yq THEN 输出 `✓ yq (version)` 
- WHEN yq 已安装但为 kislyuk/yq（pip 版） THEN 输出警告 + 安装指引
- WHEN yq 未安装 THEN 输出 `✗ yq` + 按平台的安装命令（brew/winget/snap）
- WHEN yq 未安装 THEN `setup.sh` 不中止（降级汇报，与 skipped 范式一致）
- WHEN yq 已安装且为 mikefarah/yq 但版本 < 4.16.0 THEN 输出版本过低警告 + 升级指引 [spec-review-amendment F5]

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
- WHEN frontmatter 未闭合 THEN best-effort 检测：`_yq()` 返回后校验顶层结构类型须为 dict，非 dict 视为坏块 raise 错误（yq exit code 在此场景不可靠——行为取决于 body 内容是否碰巧为合法 YAML）[spec-review-amendment F4]

### Requirement: R6 — 业务逻辑与 YAML 解析分离

各脚本的业务逻辑（字段验证、状态机、枚举校验）MUST 保留在 Python 侧，仅 YAML 解析委托给 yq。

#### Scenario:
- WHEN `ship_gate.py` 读到 frontmatter THEN `FIELD_VALIDATORS` 校验在 Python dict 上执行
- WHEN `init.py` 读到 model-tiers THEN fleet/tier 键验证（越域键、畸形头）在 Python dict 上执行
- WHEN `sad_schema.py` 读到 frontmatter THEN `TOP_KEYS` / `FACT_KEYS` 白名单校验在 Python dict 上执行
- WHEN `impl_route.py` 遇到非法 impl-pipeline 值 THEN 仍然 raise `RouteStop`

### Requirement: R7 — yq 不可用或执行失败时 fail-loud

所有使用 yq 的脚本 MUST 在 yq 不可用或执行失败时给出明确错误和安装指引。

#### Scenario:
- WHEN `shutil.which("yq")` 返回 None THEN 打印三平台安装命令到 stderr 并 `sys.exit(1)`
- WHEN yq 执行非零退出 THEN 必须 raise（转发 yq 的 stderr），即使调用方传了 default 也不吞——「键不存在」（exit 0 + stdout=null）与「解析失败」（exit≠0）MUST 是两条不同分支 [spec-review-amendment F2]
- WHEN 首次调用 yq 时 `--version` 输出不含 `mikefarah` THEN 打印身份错误 + 安装指引并 `sys.exit(1)`——身份校验 MUST 在每个脚本的 `_yq()` 封装内做（首次调用时探测 + 进程内缓存），不仅在 setup.sh [spec-review-amendment F6]

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

7 个脚本中的全部手搓 YAML 解析函数 MUST 删除（见 design §2 改动清单），**但 ship_gate.py 的 duplicate-key/tab-indent 原始文本预扫描除外**（见 R11）。

#### Scenario:
- WHEN 实现完成 THEN `grep -rn 'def _strip_inline_comment\|def _find_top_level_block\|def _second_level_keys\|def _schema_from_config\|def _set_schema_key\|def _marker_schema\|def _parse_model_tiers_block\|def _extract_scalar\|def read_metrics_enabled\|def frontmatter_end\|def read_verify_state'` 在目标脚本中零命中（注意：`parse_ship_gate_frontmatter` 从此列表移除——该函数内的 duplicate-key/tab-indent 预扫描由 R11 保留）
- WHEN 实现完成 THEN 既有测试全绿

### Requirement: R11 — ship_gate.py 保留 duplicate-key/tab-indent 原始文本预扫描 [spec-review-amendment F1·Q1]

`ship_gate.py` MUST 保留一段轻量原始文本预扫描（不做通用 YAML 解析），在 yq 读取**之前**检测 frontmatter 中的 duplicate-key 和 tab-indent。yq 对重复键静默取最后值（dict 天然不保留重复信息），故此检测不可委托给 yq。

#### Scenario:
- WHEN frontmatter 含重复 `ship-gate:` 顶层键 THEN 返回 `("ship-gate", "duplicate-key")` 拒绝放行（与现有行为一致）
- WHEN frontmatter 含 tab 缩进 THEN 返回 `("frontmatter", "tab-indent")`（与现有行为一致）
- WHEN 预扫描通过 THEN 继续走 yq 读取 + FIELD_VALIDATORS 校验

### Requirement: R12 — 7 份 `_yq()` 一致性 golden test [spec-review-amendment Q2]

7 个脚本各自包含的 `_yq()` 封装 MUST 由 golden test 守一致——机械检查 7 份封装的核心逻辑是否字节一致。

#### Scenario:
- WHEN 任一脚本的 `_yq()` 被修改而其他 6 份未同步 THEN golden test 红
- WHEN 全部 7 份 `_yq()` 核心逻辑一致 THEN golden test 绿

### Requirement: R13 — yq 表达式写操作值传递安全 [spec-review-amendment F7]

写操作的值 MUST NOT 通过 f-string 直接插入 yq 表达式。MUST 使用 yq 的 `env()` 函数或对值做转义传递。

#### Scenario:
- WHEN 设置 schema 值 THEN 通过环境变量传值：`env(VAR)` 或 `strenv(VAR)`
- WHEN 值含 `"` 或 yq 特殊字符 THEN 不产生表达式注入
