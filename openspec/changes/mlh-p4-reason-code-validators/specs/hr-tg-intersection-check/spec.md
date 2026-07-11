## ADDED Requirements

### Requirement: 模型传入命中 TG 集与 HR-TG 子集求交〔spec-review Q-D·推翻 grill Q1〕

校验器 SHALL 吃**模型判好的命中 TG 集**作入参（不自扫 proposal 声明），与 HR-TG 子集求交，输出**带「依据模型判定」的**结果——`hit:[...]｜依据模型判定:[...]` + 规范锚串 或 `none｜依据模型判定:[...]`，把模型给的输入集显式暴露供复审（**不 emit 裸 `none`**，adr/0018）。

> 〔为何模型传入而非自扫声明〕grill Q1 曾选「泛化 tg02_hit 扫 proposal 头部声明」、否决「模型传入」；冷镜爆点5 证明前提为假——TG 声明散落且格式不一（proposal 括号 `（TG-01）` / design section 锚 `## …〔TG-08〕` / 顶部 `〔TG〕` 行不统一），头部扫描**捕不全**（本 change 的 TG-08 在 design.md、proposal 用括号 → 扫描得空集却实际命中 HR-TG 成员）。「命中哪些 TG」无确定性信号 = 判断归模型；脚本只做确定性的交集 + 锚。

#### Scenario: 命中 HR-TG 成员
- **WHEN** 模型传入命中集 `[TG-04, TG-16, TG-19]`
- **THEN** 输出 `hit:[TG-04,TG-16]｜依据模型判定:[TG-04,TG-16,TG-19]` + 规范锚串（TG-19 不属 HR-TG 故不在 hit、但在依据里可见）；命中集 `sorted(set(...))` 确定序

#### Scenario: 命中 TG 无一属 HR-TG
- **WHEN** 模型传入 `[TG-01, TG-19]`（均不在子集）
- **THEN** 输出 `none｜依据模型判定:[TG-01,TG-19]`，退出码 0

#### Scenario: 模型给的集为空
- **WHEN** 模型传入空集 `[]`
- **THEN** 输出 `none｜依据模型判定:[]`（依据可见，非静默 none）

### Requirement: HR-TG 清单从单一源读、禁硬编码

校验器 SHALL 从 `$RULES_ROOT/trigger-catalog.md` 的 `## 七、HR-TG 子集` 段 `> 成员：` 行 parse HR-TG 成员，MUST NOT 在脚本内硬编码成员副本——改单一源即改行为。trigger-catalog 路径 SHALL 由入参（`--trigger-catalog`，SKILL 供 `$RULES_ROOT/trigger-catalog.md`）给定，MUST NOT 用 `__file__.parent.parent` 推导（`openspec/workflow/` 下无 trigger-catalog 副本，会 fail-closed 空跑）〔spec-review A3〕。

#### Scenario: 单一源变更即生效
- **WHEN** `trigger-catalog.md` 的 `> 成员：` 行增删某 TG 编号
- **THEN** 校验器求交结果随之变化，无需改脚本

#### Scenario: 单一源损坏 fail-closed
- **WHEN** `## 七、HR-TG` 段或 `> 成员：` 行缺失 / 不可读
- **THEN** 退出码非 0 + stderr 原因，MUST NOT 静默按空子集放行
