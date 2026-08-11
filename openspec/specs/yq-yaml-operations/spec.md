# yq-yaml-operations Specification

## Purpose
本仓 5 个脚本（`sdflow-init/scripts/init.py`、`sdflow-ship/scripts/ship_gate.py`、
`sdflow-init/assets/workflow/tools/anchor_lint.py`（评审机械层权威源，全局单份共享，
不再有消费仓镜像——见 `openspec/adr/0039-eliminate-dual-distribution-chain.md`）、
`sdflow-done/scripts/roadmap_writeback_draft.py`、
`sdflow-architecture/scripts/sad_schema.py`）读取 `config.yaml` 顶层键/`model-tiers`/
`metrics` 块，以及 Markdown frontmatter（评审报告、plan、SAD 文档）。这些 YAML/frontmatter
子集解析统一委托外部 `mikefarah/yq` 二进制（见 `openspec/adr/0036-yq-replaces-hand-rolled-yaml.md`），
不再手搓无界语法面的解析器（CLAUDE.md 基准 5）；业务判断（字段白名单、枚举校验、状态机）
保留在 Python 侧。少数有确定性信号但与既有契约冲突、或 yq 对真实输入有已证实缺陷的场景，
显式保留纯文本预扫描或既有实现，逐处记录理由（见 R3/R4/R10/R11）。
## Requirements
### Requirement: R1 — yq 依赖检测

`setup.sh` 的 `check_dependencies()` 函数 MUST 检测 yq 可用性。

#### Scenario: yq 已安装且为 mikefarah/yq
- **WHEN** yq 已安装且为 mikefarah/yq
- **THEN** 输出 `✓ yq (version)`

#### Scenario: yq 已安装但为 kislyuk/yq（pip 版）
- **WHEN** yq 已安装但为 kislyuk/yq
- **THEN** 输出警告 + 安装指引

#### Scenario: yq 未安装
- **WHEN** yq 未安装
- **THEN** 输出 `✗ yq` + 按平台的安装命令（brew/winget/snap）
- **AND** `setup.sh` 不中止（降级汇报，与 skipped 范式一致）

#### Scenario: mikefarah/yq 版本过低
- **WHEN** yq 已安装且为 mikefarah/yq 但版本 < 4.16.0
- **THEN** 输出版本过低警告 + 升级指引

### Requirement: R2 — 统一依赖预检

`setup.sh` 运行时 MUST 检测并报告全部运行依赖：python3 ≥ 3.7 / git / yq / openspec（可选）/ pytest（开发可选）。

#### Scenario: 汇总输出
- **WHEN** `setup.sh` 执行完毕
- **THEN** 在汇总区域输出依赖检测结果（每项一行 ✓/✗/·）
- **AND** 存在必要依赖缺失时在汇总末尾输出安装指引
- **AND** 所有必要依赖满足时不额外输出（只有 ✓ 行）

### Requirement: R4 — config.yaml 写操作

`init.py` 的 `_set_schema_key` 写 `schema` 键 MUST 保留既有字节级正则原地替换实现，
MUST NOT 接入 `yq -i`：mikefarah/yq v4.53.3 对「文档以 `--- # 注释` 起始」这类真实存在的
写法执行 `.schema = "x"` 后会把相邻内容行合并进注释、造成键级语义丢失（非仅格式差异），
超出可接受的写操作副作用范围；既有正则实现已被字节级测试锁定、且比 yq 更正确。全仓当前
无其他 yq 写调用点。

#### Scenario: 设置 schema 值
- **WHEN** 设置 schema 值
- **THEN** 使用既有字节级正则原地替换（`_set_schema_key`），仅替换 `schema:` 的 value 部分

#### Scenario: 写入后其余内容不变
- **WHEN** 写入后
- **THEN** 原文件中的注释、其他键值、字节序保持不变（仅目标 value 被替换）

### Requirement: R7 — yq 不可用或执行失败时 fail-loud

所有使用 yq 的脚本 MUST 在 yq 不可用或执行失败时给出明确错误和安装指引。

#### Scenario: yq 二进制缺失
- **WHEN** `shutil.which("yq")` 返回 None
- **THEN** 打印三平台安装命令到 stderr 并 fail-loud（`sys.exit(1)` 或 `raise RuntimeError`，
  依脚本既有错误处理路径而定）

#### Scenario: yq 执行非零退出
- **WHEN** yq 执行非零退出
- **THEN** 必须 raise（转发 yq 的 stderr），即使调用方传了 default 也不吞——「键不存在」
  （exit 0 + stdout=null）与「解析失败」（exit≠0）MUST 是两条不同分支

#### Scenario: yq 身份不符
- **WHEN** 首次调用 yq 时 `--version` 输出不含 `mikefarah`
- **THEN** 打印身份错误 + 安装指引并 fail-loud——身份校验 MUST 在每个脚本的 `_yq()` 封装内做
  （首次调用时探测 + 进程内缓存），不仅在 setup.sh

### Requirement: R8 — ADR 记录

MUST 存在 `openspec/adr/0036-yq-replaces-hand-rolled-yaml.md` 记录引入 yq 外部依赖的决策。

#### Scenario: ADR 三节齐备
- **WHEN** 查阅该 ADR
- **THEN** 文件存在且包含 Context / Decision / Consequences 三节

### Requirement: R9 — 零依赖声明反映外部工具依赖

各脚本的零依赖声明注释 MUST 反映 yq 外部工具依赖（非 Python import 依赖），措辞体现
「零依赖不变量收窄为不 import 解析库，代价见 adr/0036」。

#### Scenario: init.py 的声明
- **WHEN** 查阅 `init.py` 的零依赖声明
- **THEN** 声明为 `MUST NOT import yaml — YAML 解析通过 yq 外部工具完成`（收窄措辞并引用 adr/0036）

#### Scenario: 其他脚本的声明
- **WHEN** 查阅其余 6 个脚本的零依赖声明
- **THEN** 措辞与 init.py 一致地反映 yq 外部工具依赖

### Requirement: R10 — 手搓 YAML 解析代码归零（含记录在案的保留清单）

7 个脚本中的手搓 YAML/frontmatter 语法解析函数 MUST 删除或收窄为纯业务判断，
**但下列记录在案的保留除外**（每处均为有界语法面定位，非无界 YAML 解析，理由详见
`openspec/adr/0036-yq-replaces-hand-rolled-yaml.md` Decision 节）：

- `ship_gate.py` 的 duplicate-key/tab-indent 原始文本预扫描（R11）；
- `roadmap_writeback_draft.py` / `sad_schema.py` 的 frontmatter 闭合性文本预扫描
  （yq 对未闭合输入可能静默"解析成功"，与既有 fail-closed 契约冲突）；
- `sad_schema.py` 的 `frontmatter_end`（供 `sad_scaffold.py` 做行级原地改写定位，
  yq 是值抽取器、不回答行位置问题）；
- `init.py` 的 `_schema_from_config` / `_set_schema_key`（R3/R4 已证实的 yq 缺陷例外）；
- `init.py` 的 `_marker_schema` / `roadmap_writeback_draft.py` 的 `read_verify_state`
  ——入口函数名保留，内部取值已改为调用 `_yq()`。

#### Scenario: 手搓语法扫描函数归零
- **WHEN** 在目标脚本中 grep `_strip_inline_comment` / `_find_top_level_block` /
  `_second_level_keys` / 旧版 `_parse_model_tiers_block`（行扫描器）/ `_extract_scalar`
- **THEN** 零命中

#### Scenario: 既有测试全绿
- **WHEN** 实现完成
- **THEN** 既有测试套件全绿

### Requirement: R11 — ship_gate.py 保留 duplicate-key/tab-indent 原始文本预扫描

`ship_gate.py` MUST 保留一段轻量原始文本预扫描（不做通用 YAML 解析），在 yq 读取**之前**
检测 frontmatter 中的 duplicate-key 和 tab-indent。yq 对重复键静默取最后值（dict 天然不
保留重复信息），故此检测不可委托给 yq。

#### Scenario: 重复顶层键
- **WHEN** frontmatter 含重复 `ship-gate:` 顶层键
- **THEN** 返回 `("ship-gate", "duplicate-key")` 拒绝放行（与现有行为一致）

#### Scenario: tab 缩进
- **WHEN** frontmatter 含 tab 缩进
- **THEN** 返回 `("frontmatter", "tab-indent")`（与现有行为一致）

#### Scenario: 预扫描通过
- **WHEN** 预扫描通过
- **THEN** 继续走 yq 读取 + `FIELD_VALIDATORS` 校验

### Requirement: R12 — `_yq()` 一致性 golden test

各消费脚本内联的 `_yq()` 封装 MUST 由 golden test 守核心逻辑一致；封装体量小到共享收益低于跨脚本 import 的耦合成本，故不共享实现，改由测试机械守一致。〔fix-probe-scan-precision〕封装份数 MUST NOT 在 spec 或测试文档里写死计数（`openspec/workflow/tools/anchor_lint.py` 镜像随本 change 删除即为实例——写死的「7 份」当场失真；以 golden test 的 `TARGETS` 实际枚举为准，本仓「别硬编码数字、让脚本自己报」取向）。Purpose 段的脚本枚举同批订正（Purpose 非 Requirement，随 change 直接改主 spec）。

#### Scenario: 封装漂移
- **WHEN** 任一脚本的 `_yq()` 被修改而其他脚本未同步
- **THEN** golden test 红

#### Scenario: 全部一致
- **WHEN** 全部在册 `_yq()` 核心逻辑一致
- **THEN** golden test 绿

### Requirement: R13 — yq 表达式写操作值传递安全

写操作的值 MUST NOT 通过 f-string 直接插入 yq 表达式。使用 `yq -i` 写值时 MUST 使用
`env()`/`strenv()` 或对值做转义传递。当前全仓无 `_yq(..., in_place=True)` 调用点
（唯一写操作 `_set_schema_key` 为纯 Python 正则替换，见 R4），本约束对未来新增的 yq
写操作生效。

#### Scenario: 设置 schema 值
- **WHEN** 未来新增 yq 写操作设置某值
- **THEN** 通过环境变量传值：`env(VAR)` 或 `strenv(VAR)`

#### Scenario: 值含特殊字符
- **WHEN** 值含 `"` 或 yq 特殊字符
- **THEN** 不产生表达式注入

### Requirement: R3 — config.yaml 读操作改为 yq（impl-pipeline 键退役后）

从 `openspec/config.yaml` 读取 YAML 值的脚本 MUST 使用 yq subprocess 调用，**除 `init.py` 的
`_schema_from_config` 外**——该函数与其写搭档 `_set_schema_key`（见 R4）因 mikefarah/yq
`--header-preprocess` 对「文档以 `--- # 注释` 起始」这类真实写法存在已证实的数据丢失缺陷
（读侧吞并下一行内容、写侧合并注释导致键丢失），且两个缓解 flag 互斥，故保留既有的
字节级正则实现（定位单一固定字面量键 `schema:`，有界语法面，非通用 YAML 解析）。

#### Scenario: 读取 model-tiers 块
- **WHEN** `init.py` 读取 `model-tiers` 块
- **THEN** 使用 `yq -o json '.model-tiers' config.yaml` + `json.loads()`

#### Scenario: 读取 metrics.enabled
- **WHEN** `anchor_lint.py` 读取 `metrics.enabled`
- **THEN** 使用 `yq '.metrics.enabled' config.yaml`

#### Scenario: 键不存在
- **WHEN** 键不存在或被注释
- **THEN** yq 返回 `null`，脚本使用 default 值

#### Scenario: 界外 YAML 构造
- **WHEN** config.yaml 含界外 YAML 构造（锚点、多文档等）
- **THEN** yq 正常处理（无需 reject_unbounded）

#### Scenario: schema 键读取的既有实现例外
- **WHEN** `init.py` 读取 `schema` 顶层键（`_schema_from_config`）
- **THEN** 使用既有字节级正则定位 `schema:` 前缀，不经 yq（理由见本需求正文）

### Requirement: R5 — Markdown frontmatter 读操作改为 yq（impl-pipeline marker 退役后）

所有从 Markdown 文件读取 YAML frontmatter 的脚本 MUST 使用 yq `--front-matter=extract`。

#### Scenario: ship_gate.py 读取 ship-gate 块
- **WHEN** `ship_gate.py` 读取报告 frontmatter 的 ship-gate 块
- **THEN** 使用 `yq --front-matter=extract -o json '."ship-gate"' report.md`

#### Scenario: roadmap_writeback_draft.py 读取 verify 键
- **WHEN** `roadmap_writeback_draft.py` 读取 verify-report 的 ship-gate.verify 键
- **THEN** 使用 `yq --front-matter=extract '.ship-gate.verify' report.md`

#### Scenario: sad_schema.py 读取 SAD frontmatter
- **WHEN** `sad_schema.py` 读取 SAD frontmatter
- **THEN** 使用 `yq --front-matter=extract -o json '.' sad.md`

#### Scenario: 无 frontmatter
- **WHEN** 文件无 frontmatter
- **THEN** yq 返回 `null`，脚本使用 default 值

#### Scenario: frontmatter 未闭合
- **WHEN** frontmatter 未闭合
- **THEN** best-effort 检测：`_yq()` 返回后校验顶层结构类型须为 dict，非 dict 视为坏块 raise 错误
  （yq exit code 在此场景不可靠——行为取决于 body 内容是否碰巧为合法 YAML）

### Requirement: R6 — 业务逻辑与 YAML 解析分离（管线路由退役后）

各脚本的业务逻辑（字段验证、状态机、枚举校验）MUST 保留在 Python 侧，仅 YAML 解析委托给 yq。

#### Scenario: ship_gate.py 的字段校验
- **WHEN** `ship_gate.py` 读到 frontmatter
- **THEN** `FIELD_VALIDATORS` 校验在 Python dict 上执行

#### Scenario: init.py 的 model-tiers 校验
- **WHEN** `init.py` 读到 model-tiers
- **THEN** fleet/tier 键验证（越域键、畸形头）在 Python dict 上执行

#### Scenario: sad_schema.py 的白名单校验
- **WHEN** `sad_schema.py` 读到 frontmatter
- **THEN** `TOP_KEYS` / `FACT_KEYS` 白名单校验在 Python dict 上执行

