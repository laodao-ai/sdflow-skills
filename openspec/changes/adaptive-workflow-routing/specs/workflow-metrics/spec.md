# Spec Delta — workflow-metrics

## ADDED Requirements

### Requirement: 路由决策价值纳入度量维度

`lens-metric` 度量与只读聚合器 SHALL 扩出**路由决策维度**——记录每个 change 的路由决策（各阶段 FULL/LIGHT/SKIP、判定平凡与否、命中的 HR-TG 集）及其事后信号（该 change 是否有 buglist 回指 = LIGHT 逃逸；FULL 阶段是否各镜零产出 = FULL 空产出）。度量 MUST 复用现有 fence-aware 行级锚纪律与只读聚合口径（MUST NOT 落新持久态、MUST NOT 产合成分），承 config 门控（`metrics.enabled` 关闭时不落锚）。此维度供 `workflow-routing` 的后向校准消费。

#### Scenario: LIGHT 路由 change 事后落逃逸信号
- **WHEN** 某判定平凡走 LIGHT 的 change 归档后，buglist 出现回指该 change 的缺陷
- **THEN** 聚合器 SHALL 能在路由决策维度下呈现该 change 为「LIGHT 逃逸」样本，供人评估是否调整地板

#### Scenario: FULL 阶段零产出可聚合
- **WHEN** 多个命中某 HR-TG 成员的 change 走完 FULL，其对应阶段各镜均零 findings
- **THEN** 聚合器 SHALL 能呈现该 HR-TG 成员的「FULL 空产出率」，供人评估是否放松（判紧候选）

### Requirement: 路由校准复用 per-镜复评窗口且供数不供裁决

路由决策的校准 SHALL 复用「跑满复评窗口（默认 10）后按数据复评」机制（承既有 §7 复评注记与本能力「数据驱动反馈供数不供裁决」），把复评对象从「HR-TG 命中率 / per-镜采纳率」扩到「路由决策对错」。校准 MUST 供数不供裁决——`N≥复评窗口` 的判松/判紧候选 MUST 有机械 surfacing 点显著提示（复用 `/sdflow-maintain` 收尾检查步），MUST NOT 依数据自动改路由地板或自动砍阶段，MUST NOT 埋进长报告。

#### Scenario: 路由判松/判紧候选被机械显著提示
- **WHEN** `/sdflow-maintain` 运行时聚合表存在某路由决策类累计满复评窗口且未登记复评（如某 HR-TG 成员 FULL 空产出率高）
- **THEN** SHALL 在维护收尾显著提示该类待复评（只提示不判断、不自动调），MUST NOT 埋进长报告、MUST NOT 自动放松地板
