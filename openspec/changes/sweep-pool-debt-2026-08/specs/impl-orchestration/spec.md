## ADDED Requirements

### Requirement: 切片偏离审计行 SHALL 被代码审 scope 审计对账消费

`impl-reports/planning-decisions.md` 中的「切片偏离: …」审计行 SHALL 作为 `sdflow-code-review` Step1 scope 审计的输入之一〔sweep-pool-debt D6〕：Step1 SHALL 以「已申报偏离清单 × 实际 diff」做对账——既有产出侧的「MUST NOT 静默偏离」由此获得消费方（出票期对抗镜只复核**已申报**的偏离，静默偏离唯有对账能捕获）。

#### Scenario: 静默偏离被 Step1 对账捕获

- **WHEN** 出票实际偏离了 design.md「切片建议」草图（增/删/合并票、改阻塞边、改切片边界），但 `planning-decisions.md` 无对应「切片偏离: …」审计行
- **THEN** Step1 SHALL 将其作为 scope 审计 finding 上报（静默偏离），MUST NOT 因「出票期对抗镜已复核」而略过对账——对抗镜只见申报面，不见未申报面

#### Scenario: 已申报偏离与 diff 核对

- **WHEN** `planning-decisions.md` 含「切片偏离: …」审计行
- **THEN** Step1 SHALL 核对每条申报是否与实际 diff 相符；申报与实况不符（申报了未做、或做的超出申报）SHALL 同样以 finding 上报

#### Scenario: 无申报输入时对账降级不中断

- **WHEN** design.md 无「切片建议」节，或 `planning-decisions.md` 不存在 / 无「切片偏离」行
- **THEN** Step1 SHALL 记录「无偏离申报可对账」并按既有 scope 审计流程继续，MUST NOT 因该输入缺席而报错中断
