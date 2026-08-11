> 本 delta 由 spec-review 补齐〔spec-review-amendment D3〕：`impl_route.py` 随 route 半场删除退出 YAML 读取面，主 spec R3/R5/R6 中的 impl-pipeline Scenario 成死 spec（三处均不含 "superpowers" 字面串，是 grep 扫尾判据盲区）。MODIFIED 禁删 Scenario ⇒ 走 REMOVED + 换名 ADDED（与本 change impl-orchestration delta 同惯例）。

## ADDED Requirements

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

## REMOVED Requirements

### Requirement: R3 — config.yaml 读操作改为 yq

**Reason**: 换名重立为「R3 — config.yaml 读操作改为 yq（impl-pipeline 键退役后）」（见 ADDED）——「读取 impl-pipeline 键」Scenario（`impl_route.py` 读 config 键）随 route 半场删除〔adr/0042〕：`read_config_pipeline` 物理删除后该 Scenario 无实现对象；MODIFIED 无法删 Scenario，故走 REMOVED + 换名 ADDED；能力本身无损失。

**Migration**: 其余条款（`init.py` `_schema_from_config` 例外说明及其余全部 Scenario）逐字迁入 ADDED 需求。

### Requirement: R5 — Markdown frontmatter 读操作改为 yq

**Reason**: 换名重立为「R5 — Markdown frontmatter 读操作改为 yq（impl-pipeline marker 退役后）」——「impl_route.py 读取 impl-pipeline 键」Scenario（plan frontmatter 路由读取）随 `read_plan_marker` 删除〔adr/0042〕；`tickets.md` 的 marker 降格为无读取方的文件格式契约（见 impl-orchestration delta）。

**Migration**: 其余条款与 Scenario 逐字迁入 ADDED 需求。

### Requirement: R6 — 业务逻辑与 YAML 解析分离

**Reason**: 换名重立为「R6 — 业务逻辑与 YAML 解析分离（管线路由退役后）」——「impl_route.py 的非法值处理」Scenario（非法 impl-pipeline 值 raise `RouteStop`）随 `RouteStop` 与全部路由函数删除〔adr/0042〕。

**Migration**: 其余条款与 Scenario 逐字迁入 ADDED 需求。
