## ADDED Requirements

### Requirement: 阶段二自持广审并单批 dispatch 产出单一合并报告

阶段二 SHALL 由 `sdflow-spec-review` 编排器把**自持广审镜**与多镜评审合并产出**单一** `spec-review-report.md`,MUST NOT 要求人工手动合并多份报告。

广审 SHALL 由两个恒跑 fresh 子代理承载——**strategy 镜**(计划级战略审:前提站得住吗/范围校准/长期轨迹/后悔场景,过 base 清单计划级 R 项)与 **plan-eng 镜**(计划级工程审:架构耦合/错误路径完备/测试计划/隐藏复杂度,过 base 清单工程 R 项);raw 名 `strategy`/`plan-eng`,canonical 折叠 `broad`。二者 SHALL 只返回结构化 findings,**MUST NOT 原地修订四件套**——amendment 统一在 Step3 裁决后落盘并标 `[spec-review-amendment]`。广审镜与领域镜的分工线:base 清单 R 项归广审镜,`domains/` 栈特定 R 项归领域镜。

全部镜(广审/领域/对抗/接地)SHALL **单批并行 dispatch**(能力探针在 dispatch 前恒跑一次,结果对全部镜共用)——旧「领域/对抗镜等待广审先行并 checkpoint」的串行纪律随 autoplan amendment 环节退役而废止,`checkpoint(spec-review-autoplan)` 标签停产(历史归档标签仍被 retro 解析识别)。

`step1-broad-review` 锚保留,mode SHALL ∈ `{subagent, main-session}`:`subagent` = 广审镜正常派发;`main-session` = 探针判 `subagents="unavailable"` 时主 session 亲做广审(恒跑守卫,MUST NOT 因子代理不可用而跳过广审层)。

#### Scenario: 阶段二收尾
- **WHEN** 全部镜与 outside-voice collect 完成
- **THEN** 编排器输出一份已去重合并、含决策登记区的 spec-review-report.md,供设计 HARD-GATE 人工一次性评审

#### Scenario: 单批并行 dispatch
- **WHEN** 编排器完成规划镜头(TG 判定、镜 roster、能力探针)
- **THEN** 广审镜/领域镜/对抗镜/接地镜 SHALL 在一条消息内并行派出,MUST NOT 为广审设置前置 checkpoint 或让其它镜等待广审完成

#### Scenario: 广审镜不修订盘面
- **WHEN** strategy 或 plan-eng 镜发现设计缺陷
- **THEN** 该发现作为结构化 findings(问题/证据/置信/严重度/建议)返回,进 Step3 合并池同池裁决;子代理 MUST NOT 直接编辑四件套

#### Scenario: 子代理不可用时广审降级不缺席
- **WHEN** 能力探针判 `subagents="unavailable"`
- **THEN** 广审由主 session 亲做,锚记 `mode="main-session"`,`mirrors=` 计入 `broad`(合法降级);MUST NOT 静默跳过广审层

## REMOVED Requirements

### Requirement: 阶段二产出单一合并报告

**Reason**: 该 Requirement 的执行序条款(领域/对抗镜等待 Step1 autoplan checkpoint、接地镜与 autoplan 并行、amendment 后不补跑接地镜)整体建立在「autoplan 原生执行并原地产 `[gstack-amendment]`」之上;autoplan 退役(ADR 0040)后广审镜只回 findings、不修订盘面,串行时序的存在理由消失。

**Migration**: 由「阶段二自持广审并单批 dispatch 产出单一合并报告」Requirement 承接——单一合并报告与决策登记区语义原样保留,执行序由「两段 dispatch」改为「单批并行」,广审载体由 autoplan 改为 strategy/plan-eng 恒跑子代理。

### Requirement: outside-voice 复用挂反静默守卫

**Reason**: 复用对象 `gstack-review.md` 随 Step1 自持化(autoplan 原生执行退役)不复存在,三前置守卫(来源/新鲜度/结构)失去判定物;C2「复用避双 codex」的成本前提(autoplan 每轮自带 codex 声)同时消失。

**Migration**: 设计侧 outside voice(design-voice)恒自跑——原守卫回落路径转正,调用协议(helper/超时/锚行/fallback)不变;`outside_voice_guard.py` 及其测试删除;`outside-voice` 锚的 `guard=` 字段从新锚文法移除(anchor_lint 不解析该字段,归档旧锚不迁移、无兼容影响)。
