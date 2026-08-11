# workflow-retro Specification

## Purpose
把「全项目 change 成本×价值复盘」固化为可验证需求：只读再生 `openspec/retro/report.md`（git 历史阶段墙钟为成本维 + 归档评审报告 `lens-metric` 锚为价值维），view-only 不写新持久态、不增量手工维护；change 边界靠提交路径检测而非 checkpoint tag 格式；时间维只到阶段级并诚实标注含人决策时间；数据缺口显性化、失败降级留痕；报告只呈现供人复评，不自动砍镜/降采样/调优先级。
## Requirements
### Requirement: sdflow-retro 只读再生全项目 change 成本×价值复盘

`sdflow-retro` SHALL 从 git 历史（成本/时间维）+ 归档评审报告的 `lens-metric` 锚（价值维）**只读再生**全项目所有 change 的复盘报告，落 `openspec/retro/report.md`。报告 SHALL 为可随时重跑的 **view**（锚行与 git 历史为 state 真相源），MUST NOT 写入新持久可变态、MUST NOT 增量手工维护（承 `lens_metric_aggregate.py` view-only 契约，避免漂移）。报告文件 SHALL **tracked（提交进 git）作长期活文档**（团队可见）；跑 `/sdflow-retro` 再生并提交刷新，归档新 change 后未跑前 report 为 stale 属**已知接受取舍**（锚/git 历史才是真相源）。报告 SHALL **含进行中 change**（活动 `openspec/changes/*/`，标 `in-progress`），MUST NOT 只报已归档而藏当前工作。复盘 SHALL **供数不供裁决**：呈现每个 change 的阶段墙钟 + 镜 findings/采纳率/独立率 + 双峰/阶段占比聚合，「砍哪镜/降采样/调优先级」一律人决，retro MUST NOT 依数据自动决策。

#### Scenario: 再生全项目复盘
- **WHEN** `/sdflow-retro` 对含 ≥1 归档 change 的仓运行
- **THEN** SHALL 再生 `openspec/retro/report.md`，每个已归档 change 有一行成本（阶段墙钟）+ 一行价值（镜 findings/采纳率，或标注"无度量锚"），并聚合出阶段占比 / 成本双峰
- **THEN** 二次运行（源无变化）SHALL 产出等价报告（view-only 幂等），MUST NOT 因重跑产生漂移

#### Scenario: 含进行中 change 标 in-progress
- **WHEN** 仓内存在活动（未归档）change
- **THEN** SHALL 将其纳入报告并标 `in-progress`（成本维取其部分生命周期），价值维若未落锚则标"无度量锚"，MUST NOT 从报告静默排除进行中工作

#### Scenario: 价值维扫 active+archive 两源、跨 spec+code 两份报告〔D11〕
- **WHEN** 某 change（活动或归档）同时有 `spec-review-report.md` 与 `code-review-report.md`，各带 layer 不同的 lens-metric 锚
- **THEN** per-change 价值 join SHALL 扫 **active `changes/*/` 与 archive 两处**、聚合**两份报告**的锚并按 layer 分归属，MUST NOT 只扫 archive（否则有锚的活动 change 被误标"无度量锚"）、MUST NOT 只取一份（否则漏 spec/code 一半锚）

#### Scenario: N≥10 待复评镜机械显著呈现〔D12〕
- **WHEN** 聚合表存在某镜出现轮数 ≥10 未复评
- **THEN** SHALL 在报告顶部**独立 `⚠️ 待复评` 区块 + 固定前缀标记**呈现（位置/标记可机验），MUST NOT 仅以"显著"形容词表述（不可机验 = 死列风险自我复现，同 `grill-not-skippable`）

#### Scenario: 只呈现不决策
- **WHEN** 某镜采纳率/独立率低、或某 change 成本畸高
- **THEN** SHALL 在报告显著呈现供人判断，MUST NOT 自动标记"应砍"或改任何 workflow 配置

### Requirement: change 边界靠提交路径检测，不依赖 checkpoint tag 格式

change 生命周期边界 SHALL 由 `git log -- openspec/changes/<name>/`（含归档路径 `openspec/changes/archive/<date>-<name>/`）确定——即"提交碰哪个 change 目录"归属该 change，MUST NOT 依赖 checkpoint tag 里是否嵌 change 名。checkpoint tag 前缀 SHALL 仅用于**阶段映射**（grill/spec-review/impl-review/done-verify/…）。此设计 MUST NOT 改动 `checkpoint-commit.sh` 的 tag 格式，以免破坏 `ship_gate.py` 既有解析契约（命名空间任务标签 + `checkpoint(impl-review)` 精确豁免）。

#### Scenario: 归属靠路径、阶段靠前缀
- **WHEN** retro 处理一个 change（活动目录或归档目录）
- **THEN** SHALL 用 `git log -- <该 change 路径>` 拿到其全部提交并归属该 change，阶段由 checkpoint 前缀词表映射
- **THEN** MUST NOT 要求 checkpoint tag 携带 change 名，MUST NOT 改 `checkpoint-commit.sh` tag 格式

#### Scenario: 历史裸标签 best-effort
- **WHEN** 某历史 change 的 checkpoint 为裸阶段标签（`checkpoint(spec-review)` 无 change 名）
- **THEN** 归属仍由提交路径确定（不受裸标签影响），阶段由前缀映射；映射不出的归"unknown 阶段"桶并在报告标注，MUST NOT 静默漏

#### Scenario: done/归档阶段靠 path-rename 非 subject 前缀〔D8〕
- **WHEN** 某 change 的归档提交 subject 为 `chore(openspec)`/`feat(...)` 而非 `checkpoint(done-archive)`（实测 14/15 归档提交如此）
- **THEN** done/收尾阶段 SHALL 由"提交把 change 目录 `git mv` 进 `archive/`"的**路径 rename 事件**判定，MUST NOT 仅靠 subject 前缀（否则 done 阶段对多数历史 change 恒空）

#### Scenario: seed change 边界守卫〔D9〕
- **WHEN** 某 change 的 pre-archive 路径 `git log` 为 0 提交（创世 mass 提交只碰其 archive 路径），或全 change 只有恰好 1 提交
- **THEN** SHALL 兜底查 archive 路径 + 显式守卫 0/1 提交（墙钟不可算即标"边界不可解析"计入 K、不崩），并剔除碰 ≥3 change 目录的 seed-mass 提交，MUST NOT 因单样本假设"pre-archive 路径必非空"而崩或漏

### Requirement: 时间维只到阶段级且诚实标注含人决策时间

成本/时间维 SHALL 只到**阶段级**（相邻 checkpoint 的时间戳差），MUST NOT 假装能拆到 per-镜 fan-out 耗时（adr/0009：harness 不暴露子代理耗时）。阶段墙钟 SHALL 显式标注为"阶段 elapsed（含人读/拍板/生成时间）"，MUST NOT 呈现为纯 agent 计算耗时或纯 fan-out 延迟。

#### Scenario: 阶段墙钟标注口径
- **WHEN** 报告呈现某阶段墙钟 Δ
- **THEN** SHALL 标注其为"阶段级 elapsed（含人时间）"口径，MUST NOT 标为 per-镜或纯 agent 耗时

### Requirement: 复盘缺口显性、失败 fail-safe 不 fail-silent

报告 SHALL 在顶部呈现覆盖计数（覆盖 N change / M 有镜锚 / K 边界不可解析），让数据缺口显性，MUST NOT 让局部缺失伪装成"全覆盖"。解析失败（change 无提交历史 / 前缀映射不出 / 锚缺失 / 归档报告 fence 污染 / git 输出畸形）SHALL 各自降级留痕（标注该项、跳过坏行、不崩），MUST NOT 静默丢或整体崩溃。

#### Scenario: 覆盖计数显性
- **WHEN** 若干 change 缺 lens-metric 锚或边界不可解析
- **THEN** 报告顶部 SHALL 列出覆盖/缺口计数，缺锚 change 的价值维标"无度量锚"、边界不可解析 change 单独列出，MUST NOT 从报告静默消失

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

retro 的 per-change 表 SHALL 新增 tokens 列：先扫描**全部** change 目录（活动或归档）的 token-log.jsonl，按 session **全局**分组、组内相邻 `anchor=true` 行差分并归属后一行的 step（attribute-to-next）——同一 session 出现在多个 change 文件时，后一文件首行 SHALL 对前一文件末行差分、Δ 落该行所在 change，MUST NOT 双计数；仅 session 全局首行全额计入其 step [spec-review-amendment 设计门 Q1 拍板=A]；列值呈现 output / input / cache_creation / cache_read 四计数（紧凑串，缩写对照 `out`/`in`/`cc`/`cr` [spec-review-amendment]），MUST NOT 合成单一总分（四者计价不同）。change 无 token-log 或全为降级行时 SHALL 显式呈现「—」（无锚），MUST NOT 留空或以零冒充。`anchor=false` 行 MUST NOT 计入任何计数。[spec-review-amendment] 无法解析的行（截断/坏 JSON）SHALL 按 `anchor=false` 等价处理并逐行跳过，MUST NOT 让单行损坏中断该 change 或整份报告的生成。

#### Scenario: 有锚 change 呈现四计数

- **WHEN** 某 change 目录含 ≥2 行同 session 的 `anchor=true` 快照
- **THEN** per-change 表该行 tokens 列呈现四计数聚合值，且数值等于按 attribute-to-next 差分口径的累加结果

#### Scenario: 存量无锚 change 显式标注

- **WHEN** 某 change（如本机制引入前归档的存量 change）无 token-log.jsonl
- **THEN** tokens 列显示「—」，报告其余列不受影响

#### Scenario: 跨 change session 不双计数 [spec-review-amendment 设计门 Q1 拍板=A]

- **WHEN** 同一 session 的 `anchor=true` 快照行先后落在 change A 与 change B 的 token-log.jsonl
- **THEN** change B 的该 session 首行以对 change A 末行的差分入账，同一用量区间只计入一个 change 的 tokens 列

#### Scenario: 降级行不入计数

- **WHEN** token-log.jsonl 中存在 `anchor=false` 降级行
- **THEN** 该行不参与差分与聚合，仅 `anchor=true` 行入计数

#### Scenario: 损坏行不拖垮报告 [spec-review-amendment]

- **WHEN** 某 change 的 token-log.jsonl 含一行无法解析的内容（截断半行/非法 JSON）
- **THEN** 该行被逐行跳过（等价 `anchor=false`），该 change 其余行正常计入，整份 retro 报告其余 change 不受影响地生成

### Requirement: 待复评镜处置记录消费与行内注记

retro 报告生成器 SHALL 消费处置记录文件 `openspec/retro/mirror-dispositions.yaml`（每条含镜匹配键 + `disposition ∈ {保留, 降采样, 淘汰, 不适用}` + 日期 + 依据，降采样条目另含派发条件原文；匹配键与 lens-metric 聚合分组键同构）：待复评区块中命中处置记录的镜行 SHALL 行内追加处置注记（处置结果 + 日期），未命中的照旧 flag。错误语义 SHALL 分治：文件缺失 = 合法零注记态（向后兼容，照旧全 flag）；文件存在但 yaml 不可解析或 `disposition` 取值非法 ⇒ fail-loud 非零退出（宁红勿静默）；文件内存在未命中任何锚组的键 ⇒ 告警不阻断（已淘汰镜的存量条目属合法形态）。处置记录 MUST NOT 影响出现轮数计数本身（注记是呈现层，计数口径不变）。

#### Scenario: 已处置镜行内注记
- **WHEN** 某待复评镜在处置文件中有 `disposition: 降采样` 条目
- **THEN** 再生报告中该镜行追加处置注记（含处置结果与日期），该镜不再以未处置形态裸 flag

#### Scenario: 处置文件缺失时照旧全量 flag
- **WHEN** `mirror-dispositions.yaml` 不存在
- **THEN** 报告生成正常完成，待复评区块行为与引入本能力前一致（全部达阈值镜裸 flag），无告警噪声

#### Scenario: 坏 yaml fail-loud
- **WHEN** 处置文件存在但 yaml 语法坏、或某条 `disposition` 不在合法枚举内
- **THEN** 生成器非零退出并报出坏条目定位；MUST NOT 静默跳过坏条目继续生成（半坏注记比无注记更误导）

#### Scenario: 未命中锚组的存量条目告警不阻断
- **WHEN** 处置文件含一条键未命中当前任何锚组（如已淘汰镜的历史条目）
- **THEN** 报告照常生成，该条目以一行告警呈现，MUST NOT 判为错误退出

