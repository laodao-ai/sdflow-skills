## ADDED Requirements

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
