# workflow-retro Delta Specification

## ADDED Requirements

### Requirement: per-镜实修率历史回算（窄文法 + 三数 + 样本量闸门）

retro 报告 SHALL 新增「聚合④ per-镜实修率（历史回算）」独立段，对归档评审报告按严格窄文法回算 per-(layer, lens) 实修率。[spec-review-amendment] **fix-status 三态判定**：finding 行含精确标注 `已修[impl-review-fix]` 判实修；含 defer 类标注判 defer；**含 `impl-review-fix` 裸串或处置动词（已修/采纳/自动修）但不命中精确 needle 的行 SHALL 进未知桶，MUST NOT 默认判「未修」**——仅无任何处置信号的 finding 行判未修。[spec-review-amendment] **镜归属 = 封闭 lens 关键词表（与 LENS_ENUM 同源的六值映射，`域` 为 `领域` 的记号内别名）仅在有界来源记号内匹配**（表格行「来源」列、或 `〔…〕`/`【…】` 标签形态），MUST NOT 对 finding 行自由文本做无边界子串匹配；记号内精确命中一个才可判定，零个或多个命中、或无有界记号，一律进未知桶，MUST NOT 猜测归属。每镜 SHALL 输出可判定样本数 / 未知数 / 覆盖率三数；实修率分母 = 可判定数；可判定数 < 5（最小无歧义样本量阈值，常量单一源）的镜 SHALL 标注「参考」且 MUST NOT 呈现为砍留依据。change 边界内存在修复类 commit 时 SHALL 打「有 commit 佐证」flag，该 flag MUST NOT 参与实修判定。窄文法 MUST NOT 为提高覆盖率而放宽（散文面无界，未知桶是合法残余）。

#### Scenario: 可判定样本计入实修率

- **WHEN** 归档报告中某 finding 行同时含 `已修[impl-review-fix]` 标注且 lens 关键词精确命中一个
- **THEN** 该样本计入对应 (layer, lens) 的可判定数与实修数，实修率随之更新

#### Scenario: 归属歧义进未知桶

- **WHEN** finding 行含处置标注但有界来源记号内 lens 关键词零命中或命中多个
- **THEN** 该样本计入未知数，不进任何镜的分母，报告三数中未知数可见

#### Scenario: 处置信号歧义进未知桶（不判未修）[spec-review-amendment]

- **WHEN** finding 行含 `impl-review-fix` 裸串或处置动词（如 `已修 [impl-review-fix]` 带空格变体、`采纳[impl-review-fix]`、无标注的 `已修：…`）但不命中精确 needle `已修[impl-review-fix]`
- **THEN** 该样本进未知桶，MUST NOT 计入「未修」，报告未知数相应可见

#### Scenario: 关键词出现在自由文本不构成归属 [spec-review-amendment]

- **WHEN** finding 行的有界来源记号外（如文件名、问题描述）出现 lens 关键词（如路径含 `outside-voice`、描述含「历史注释」）且行内无有界来源记号命中
- **THEN** 该样本进未知桶，MUST NOT 被判定为对应镜的可判定样本

#### Scenario: 样本量不足标参考

- **WHEN** 某镜可判定样本数少于阈值 5
- **THEN** 该镜实修率带「参考」标注呈现，报告不将其列为砍留依据

#### Scenario: 报告再生含三数注记

- **WHEN** 对含归档评审报告的仓库再生 retro 报告
- **THEN** 报告含聚合④段，每镜行呈现 实修数 / 可判定 / 未知 / 覆盖率 / 实修率 / 佐证 flag，与既有聚合③段（细粒度五元组）互不混算

### Requirement: per-change token 维 join（读快照锚，缺锚显式）

retro 的 per-change 表 SHALL 新增 tokens 列：读取各 change 目录（活动或归档）的 token-log.jsonl，按 session 分组、组内相邻 `anchor=true` 行差分并归属后一行的 step（attribute-to-next），session 首行全额计入其 step；列值呈现 output / input / cache_creation / cache_read 四计数（紧凑串，缩写对照 `out`/`in`/`cc`/`cr` [spec-review-amendment]），MUST NOT 合成单一总分（四者计价不同）。change 无 token-log 或全为降级行时 SHALL 显式呈现「—」（无锚），MUST NOT 留空或以零冒充。`anchor=false` 行 MUST NOT 计入任何计数。[spec-review-amendment] 无法解析的行（截断/坏 JSON）SHALL 按 `anchor=false` 等价处理并逐行跳过，MUST NOT 让单行损坏中断该 change 或整份报告的生成。

#### Scenario: 有锚 change 呈现四计数

- **WHEN** 某 change 目录含 ≥2 行同 session 的 `anchor=true` 快照
- **THEN** per-change 表该行 tokens 列呈现四计数聚合值，且数值等于按 attribute-to-next 差分口径的累加结果

#### Scenario: 存量无锚 change 显式标注

- **WHEN** 某 change（如本机制引入前归档的存量 change）无 token-log.jsonl
- **THEN** tokens 列显示「—」，报告其余列不受影响

#### Scenario: 降级行不入计数

- **WHEN** token-log.jsonl 中存在 `anchor=false` 降级行
- **THEN** 该行不参与差分与聚合，仅 `anchor=true` 行入计数

#### Scenario: 损坏行不拖垮报告 [spec-review-amendment]

- **WHEN** 某 change 的 token-log.jsonl 含一行无法解析的内容（截断半行/非法 JSON）
- **THEN** 该行被逐行跳过（等价 `anchor=false`），该 change 其余行正常计入，整份 retro 报告其余 change 不受影响地生成
