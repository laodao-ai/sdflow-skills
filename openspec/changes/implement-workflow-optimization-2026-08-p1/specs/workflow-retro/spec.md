# workflow-retro Delta Specification

## ADDED Requirements

### Requirement: per-镜实修率历史回算（窄文法 + 三数 + 样本量闸门）

retro 报告 SHALL 新增「聚合④ per-镜实修率（历史回算）」独立段，对归档评审报告按严格窄文法回算 per-(layer, lens) 实修率：finding 行含精确标注 `已修[impl-review-fix]` 判实修；镜归属经封闭 lens 关键词表（与 LENS_ENUM 同源的六值映射）在同行（含表格行「来源」列）匹配，精确命中一个才可判定，零个或多个命中一律进未知桶，MUST NOT 猜测归属。每镜 SHALL 输出可判定样本数 / 未知数 / 覆盖率三数；实修率分母 = 可判定数；可判定数 < 5（最小无歧义样本量阈值，常量单一源）的镜 SHALL 标注「参考」且 MUST NOT 呈现为砍留依据。change 边界内存在修复类 commit 时 SHALL 打「有 commit 佐证」flag，该 flag MUST NOT 参与实修判定。窄文法 MUST NOT 为提高覆盖率而放宽（散文面无界，未知桶是合法残余）。

#### Scenario: 可判定样本计入实修率

- **WHEN** 归档报告中某 finding 行同时含 `已修[impl-review-fix]` 标注且 lens 关键词精确命中一个
- **THEN** 该样本计入对应 (layer, lens) 的可判定数与实修数，实修率随之更新

#### Scenario: 归属歧义进未知桶

- **WHEN** finding 行含处置标注但 lens 关键词零命中或命中多个
- **THEN** 该样本计入未知数，不进任何镜的分母，报告三数中未知数可见

#### Scenario: 样本量不足标参考

- **WHEN** 某镜可判定样本数少于阈值 5
- **THEN** 该镜实修率带「参考」标注呈现，报告不将其列为砍留依据

#### Scenario: 报告再生含三数注记

- **WHEN** 对含归档评审报告的仓库再生 retro 报告
- **THEN** 报告含聚合④段，每镜行呈现 实修数 / 可判定 / 未知 / 覆盖率 / 实修率 / 佐证 flag，与既有聚合③段（细粒度五元组）互不混算

### Requirement: per-change token 维 join（读快照锚，缺锚显式）

retro 的 per-change 表 SHALL 新增 tokens 列：读取各 change 目录（活动或归档）的 token-log.jsonl，按 session 分组、组内相邻 `anchor=true` 行差分并归属后一行的 step（attribute-to-next，与阶段墙钟同口径），session 首行全额计入其 step；列值呈现 output / input / cache_creation / cache_read 四计数（紧凑串），MUST NOT 合成单一总分（四者计价不同）。change 无 token-log 或全为降级行时 SHALL 显式呈现「—」（无锚），MUST NOT 留空或以零冒充。`anchor=false` 行 MUST NOT 计入任何计数。

#### Scenario: 有锚 change 呈现四计数

- **WHEN** 某 change 目录含 ≥2 行同 session 的 `anchor=true` 快照
- **THEN** per-change 表该行 tokens 列呈现四计数聚合值，且数值等于按 attribute-to-next 差分口径的累加结果

#### Scenario: 存量无锚 change 显式标注

- **WHEN** 某 change（如本机制引入前归档的存量 change）无 token-log.jsonl
- **THEN** tokens 列显示「—」，报告其余列不受影响

#### Scenario: 降级行不入计数

- **WHEN** token-log.jsonl 中存在 `anchor=false` 降级行
- **THEN** 该行不参与差分与聚合，仅 `anchor=true` 行入计数
