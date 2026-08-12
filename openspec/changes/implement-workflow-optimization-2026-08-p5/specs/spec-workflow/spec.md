# spec-workflow · delta（implement-workflow-optimization-2026-08-p5）

## ADDED Requirements

### Requirement: 设计门报告拍板三问（拍板层）与机验锚

spec-review 报告的决策登记区 SHALL 在 `[需拍板]` 条目**之前**置顶一个「拍板三问」小节，
三问固定为：①**范围划界认不认**（锚 proposal 的 Non-Goals / Out-of-scope 划界）②**依赖/
顺序认不认**（锚 tasks 的任务边界与 Blocked-by 关系）③**风险赌注与对策认不认**（锚
`sdflow:hr-tg` 锚的 hit/declared 判定与对应对策条目）。每问 SHALL 由评审侧给出一句自答
（指回报告内证据位置），供人在设计 HARD-GATE 勾选认/不认。三问 SHALL 只落设计门报告
（spec-review），code-review 报告 MUST NOT 被要求含三问（无人门的报告不加拍板结构）。

拍板层 SHALL 落结构化锚 `<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->`（独占一行，
紧邻三问小节）。`anchor_lint` SHALL 对 `--layer spec-review` 校验该锚：存在性**恒须**
（always-on，不受 `metrics.enabled` 门控——报告结构契约与度量开关无关）；`q` 值 MUST 逐字
等于 `scope,deps,risk`（有序、无增减）；沿用 fence-aware 行级纪律（fence 内示范锚不算）。
`--layer code-review` MUST NOT 校验该锚。既有各类锚的检查语义 MUST NOT 因新锚加入而改变。

#### Scenario: 设计门报告含拍板三问与锚自检通过
- **WHEN** spec-review 报告的决策登记区顶部含三问小节与 `<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->` 锚行，`anchor_lint --layer spec-review` 运行
- **THEN** 脚本对该锚判合法（其余锚类照旧各自判定），三问小节供人在设计门逐项勾选

#### Scenario: 缺拍板层锚被拦
- **WHEN** spec-review 报告不含 fence 外的 `sdflow:gate-questions` 锚行，`anchor_lint --layer spec-review` 运行
- **THEN** 脚本 SHALL 非零退出并点名缺失拍板层锚，SKILL 自检步报错阻塞，MUST NOT 静默放行

#### Scenario: q 值变异被拦
- **WHEN** 锚行的 `q` 值缺项、增项、乱序或改写（如 `q="scope,risk"` / `q="deps,scope,risk"` / `q="scope,deps,risk,extra"`）
- **THEN** 脚本 SHALL 非零退出并点名 q 值与期望 `scope,deps,risk` 的差异

#### Scenario: code-review 报告不查拍板层锚
- **WHEN** 一份不含 `sdflow:gate-questions` 锚的 code-review 报告经 `anchor_lint --layer code-review` 自检
- **THEN** 脚本 MUST NOT 因缺该锚而非零退出（三问只属设计门契约）

#### Scenario: fence 内示范锚不算真锚
- **WHEN** spec-review 报告仅在 ``` fence 内含 `sdflow:gate-questions v1` 字面（语法示范），fence 外无真锚
- **THEN** 脚本 SHALL 判拍板层锚缺失并非零退出（fence-aware 纪律与既有锚类同口径）
