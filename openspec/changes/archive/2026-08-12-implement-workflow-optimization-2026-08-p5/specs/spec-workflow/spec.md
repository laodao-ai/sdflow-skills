# spec-workflow · delta（implement-workflow-optimization-2026-08-p5）

## ADDED Requirements

### Requirement: GQ 设计门报告拍板三问（拍板层）与机验锚

spec-review 报告的决策登记区 SHALL 在 `[需拍板]` 条目**之前**置顶一个「拍板三问」小节，
三问固定为：①**范围划界认不认**（锚 proposal 的 Non-Goals / Out-of-scope 划界）②**依赖/
顺序认不认**（锚 tasks 的任务边界与 Blocked-by 关系）③**风险赌注与对策认不认**（锚
`sdflow:hr-tg` 锚的 hit/declared 判定与对应对策条目）。每问 SHALL 由评审侧给出一句自答
（指回报告内证据位置），供人在设计 HARD-GATE 勾选认/不认。三问 SHALL 只落设计门报告
（spec-review），code-review 报告 MUST NOT 被要求含三问（无人门的报告不加拍板结构）。

拍板层 SHALL 落结构化锚 `<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->`（独占一行，
紧邻三问小节）。`anchor_lint` SHALL 对 `--layer spec-review` 校验该锚：存在性**恒须**
（always-on，不受 `metrics.enabled` 门控——报告结构契约与度量开关无关）；`q` 值 MUST 逐字
等于 `scope,deps,risk`（有序、无增减），锚行在场但缺 `q=` 属性 SHALL 同判违规；fence 外
出现 ≥2 条该锚 SHALL 判重复违规（fail-closed，沿 `duplicate-fanout-anchor` 先例）；沿用
fence-aware 行级纪律（fence 内示范锚不算）。`--layer code-review` MUST NOT 校验该锚。
既有各类锚的检查语义 MUST NOT 因新锚加入而改变。[spec-review-amendment] 本机验为**拍板层
声明锚机验**（锚存在 + q 值逐字）——三问正文小节是否真实在场属 SKILL 报告模版契约 +
设计门人读层，无机械保证，MUST NOT 声称三问内容已被机械兜底。

#### Scenario: 设计门报告含拍板三问与锚自检通过
- **WHEN** spec-review 报告的决策登记区顶部含三问小节与 `<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->` 锚行，`anchor_lint --layer spec-review` 运行
- **THEN** 脚本对该锚判合法（其余锚类照旧各自判定），三问小节供人在设计门逐项勾选

#### Scenario: 缺拍板层锚被拦
- **WHEN** spec-review 报告不含 fence 外的 `sdflow:gate-questions` 锚行，`anchor_lint --layer spec-review` 运行
- **THEN** 脚本 SHALL 非零退出并点名缺失拍板层锚，SKILL 自检步报错阻塞，MUST NOT 静默放行

#### Scenario: q 值变异被拦
- **WHEN** 锚行的 `q` 值缺项、增项、乱序、改写（如 `q="scope,risk"` / `q="deps,scope,risk"` / `q="scope,deps,risk,extra"`），或锚行在场但完全缺 `q=` 属性 [spec-review-amendment]
- **THEN** 脚本 SHALL 非零退出并点名 q 值与期望 `scope,deps,risk` 的差异（缺属性点名缺失）

#### Scenario: 重复拍板层锚被拦 [spec-review-amendment]
- **WHEN** spec-review 报告 fence 外出现 ≥2 条 `sdflow:gate-questions` 锚行（无论各自 q 值合法与否）
- **THEN** 脚本 SHALL 非零退出并点名重复（与 `duplicate-fanout-anchor` 同口径 fail-closed），MUST NOT 取首/取末静默放行

#### Scenario: code-review 报告不查拍板层锚
- **WHEN** 一份不含 `sdflow:gate-questions` 锚的 code-review 报告经 `anchor_lint --layer code-review` 自检
- **THEN** 脚本 MUST NOT 因缺该锚而非零退出（三问只属设计门契约）

#### Scenario: fence 内示范锚不算真锚
- **WHEN** spec-review 报告仅在 ``` fence 内含 `sdflow:gate-questions v1` 字面（语法示范），fence 外无真锚
- **THEN** 脚本 SHALL 判拍板层锚缺失并非零退出（fence-aware 纪律与既有锚类同口径）

## MODIFIED Requirements

### Requirement: 阶段一入口为唯一线性路径，模型可自动触发

[spec-review-amendment]（跨模型 voice 发现：本 Requirement 的「拷问协议不因触发方式改变」
Scenario 枚举「一次一问」为拷问协议内容，与本 change SA-03 的呈现与拍板分离协议矛盾——
delta 同步该措辞，其余条款原样保留。）

阶段一入口 SHALL 为唯一线性路径：`explore(条件) → sdflow-spec → /clear → sdflow-spec-review`。不再有分支 A/B 双轨选择。

- **`opsx:explore`**：条件前置步——问题模糊/方向未定时先 explore 发散；问题清晰时跳过。
- **`/sdflow-spec`**：唯一生成入口——澄清(A) → 拷问(B) → 生成(C) 三相位连续跑，产四件套 + `decision-memo.md`。
- **自动触发**：`sdflow-spec` MUST NOT 声明 `disable-model-invocation: true`。模型 SHALL 在以下情形自动 invoke `/sdflow-spec`：① explore 中人示意收敛（如「开搞」「做吧」「开 change」）；② 用户描述需求且需要开 change 时。模型 MUST NOT 自主判断「该开 change 了」——须有人的示意信号。
- **拷问不可省**：触发方式的变更 SHALL NOT 影响相位 B 的拷问协议。任何进入相位 C 的路径 SHALL 先产出非空 `decision-memo.md`。
- **FF-0 三分支判定**不受影响：保护分支建 / 已在 `feat/{本 change}` 跳过 / 在其它 feature 分支 halt 问人。

#### Scenario: 用户在 explore 中示意收敛

- **WHEN** 用户在 opsx:explore 中表达「开搞」「做吧」「开 change」等收敛信号
- **THEN** 模型自动 invoke `/sdflow-spec`，带入 explore 上下文

#### Scenario: 用户直接描述需求

- **WHEN** 用户说「做 X」且需要开 change，未指定入口
- **THEN** 模型直接 invoke `/sdflow-spec`

#### Scenario: 模型不自主触发

- **WHEN** explore 讨论仍在发散，用户未表达收敛信号
- **THEN** 模型 MUST NOT 自动 invoke `/sdflow-spec`

#### Scenario: 拷问协议不因触发方式改变

- **WHEN** sdflow-spec 由模型自动触发（而非用户手动敲）
- **THEN** 相位 B 的人机对话拷问（按 SA-03 呈现与拍板分离协议提问、承重约束逐条站稳、停止信号需证据锚）照常执行，MUST NOT 缩减或跳过
