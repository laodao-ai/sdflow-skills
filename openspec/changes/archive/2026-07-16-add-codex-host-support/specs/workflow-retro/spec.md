## ADDED Requirements

### Requirement: 聚合器双代兼容读锚行，存量数据零丢失

`lens_metric_aggregate.py` 是**唯一读取存量归档锚行**的组件（`anchor_lint` 只校验当场评审报告、不扫归档）。它 SHALL 同时正确读取 v1 旧锚与含 `host=` 的新锚，**MUST NOT 静默丢弃任一代**。

兼容读规则 SHALL 钉死为（**不迁移存量数据、不 rewrite history**）：

| 读到 | 兼容读为 | 依据 |
|---|---|---|
| `runner="claude-fallback"`（已废弃枚举值） | `host="claude", runner="claude"` | 历史上所有 fallback 均发生在 Claude 宿主 |
| 锚行无 `host` 字段 | `host="claude"` | 历史上所有轮次均为 Claude 宿主（事实，非假设） |

分组键 SHALL 升为 `(layer, lens, host, runner, site)`，使 Codex 宿主轮次与 Claude 宿主轮次的采纳率/独立率**分别可见**，MUST NOT 混算——混算会让一方的同族 fallback 数据污染另一方的真跨模型信号。

聚合器 SHALL 保持 view-only（承本能力既有契约）：只呈现分组结果供人复评，MUST NOT 据 host 分组差异自动决策（砍镜 / 降采样 / 调优先级一律人决）。

#### Scenario: 旧锚按兼容规则读入不丢行
- **WHEN** 归档报告含 v1 锚行（`runner="claude-fallback"`，无 `host` 字段）
- **THEN** SHALL 读作 `host="claude", runner="claude"` 并计入聚合，MUST NOT 因枚举值已废弃或字段缺失而跳过该行（跳过 = 静默丢失历史价值数据）

#### Scenario: 改造前后对存量归档的聚合结果逐行一致
- **WHEN** 对本 change 之前已存在的全部归档报告（含 `openspec/retro/report.md` 现有的 `claude-fallback` 行）跑改造后的聚合器
- **THEN** 除新增的 `host` 列外，聚合结果的每行计数 SHALL 与改造前**逐行一致**（回归判据，可机验）

#### Scenario: 新旧锚混合仓正确分组
- **WHEN** 同一仓内既有 v1 旧锚的归档 change、又有 v2 新锚的 change
- **THEN** SHALL 按 `(layer,lens,host,runner,site)` 正确分组，旧锚归入 `host="claude"` 组，MUST NOT 因字段数不同而 parse 失败或把两代混成一行

#### Scenario: 宿主分组供人复评而不自动裁决
- **WHEN** 聚合发现 Codex 宿主轮次的「独立率」显著高于 Claude 宿主轮次（同族 fallback 自审的典型特征）
- **THEN** SHALL 在报告中如实呈现该分组差异供人判断，MUST NOT 自动标记"应砍"或改任何 workflow 配置
