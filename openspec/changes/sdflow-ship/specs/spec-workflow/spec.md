# spec-workflow Specification (delta)

> 本 delta = `sdflow-ship`：阶段三补编排层连续（确定性台账驱动）+ 决策协议脱离自评置信（T10）+ 模型档位映射（T11）+ 阶段二串行纪律（T20）。
> 真相源 = [`adr/0004`](../../../adr/0004-opsx-ship-stage3-orchestrator.md) + [`adr/0006`](../../../adr/0006-execution-model-baseline-fleet-anchored.md) + [design.md](../../design.md)。

## ADDED Requirements

### Requirement: 阶段三编排台账确定性（ship_gate）

`sdflow-ship` 的步序推进 MUST 由确定性脚本 `ship_gate.py` 判定（**盘面即状态**：以 change 目录产物存在性与结论行为账本，MUST NOT 设可变 state 文件造第二真相源）；编排 skill MUST 在每步前后调用 gate 并遵其判定，MUST NOT 以 prose 记忆步序。gate MUST 只读（零副作用）、双输出（首行人读摘要 + JSON 机读）、以退出码承载门禁语义（0=可推进 / 3=拒绝起跑 / 4=上游 blocker / 5=verify FAIL）。机判锚点字面 MUST 双向钉死（脚本解析规则 ↔ 各报告格式约定同 change 演进）：设计门拍板 = 报告含「设计门拍板」行；verify 结论 = `结论：PASS|FAIL`；code-review 放行 = 结论区含「建议进 /sdflow-done」且无未解 blocker。

#### Scenario: 未过设计门拒绝起跑
- **WHEN** 对一个 spec-review-report.md 缺失或不含「设计门拍板」标记的 change 调用 /sdflow-ship
- **THEN** ship_gate 退出码 3（REFUSE_START），skill 停止并提示先完成设计门，MUST NOT 起跑任何阶段三步骤

#### Scenario: verify FAIL 停并上抛
- **WHEN** 链行进至 sdflow-done 后 verify-report.md 结论为 FAIL
- **THEN** gate 退出码 5，ship 停止、原样上抛缺口清单，MUST NOT 继续 archive/merge（任何一层评审覆盖不得无声蒸发）

#### Scenario: 前置产物缺失点名
- **WHEN** 某步产物缺失（如 code-review-report.md 不在）
- **THEN** gate 输出 next=对应 skill 与 missing 清单，编排按此推进；完成判据不可判（如 plan 复选框与 SDD ledger 双缺）时 gate 判 UNKNOWN 停上抛，MUST NOT 猜测推进

#### Scenario: 条件步按 TG 判定
- **WHEN** change 的 proposal 未标注 TG-02（非嵌入式）
- **THEN** gate 对 step 5.5 输出 SKIP 并记录理由；命中 TG-02 时高风险/TG-18 细判归模型（每步内部判断，prose 允许域）

### Requirement: 模型档位映射（model-tiers）

模型档位与映射 MUST 以消费仓 `config.yaml` 的 `model-tiers` 段为真相源（强档=verify/对抗裁决/final 终审；中档=领域镜/生成/实现；弱档=纯机械步；各档默认模型随段下发）；编排 skill（sdflow-ship/done/spec-review/code-review）的模型选择 MUST 引用该段并 MUST 内联缺省保底（无该段时按 opus/sonnet/haiku 缺省运行，不失效不硬依赖）；规则文件 MUST NOT 写死具体模型产品名做强弱判据（机队锚定，adr/0006(c)）。

#### Scenario: 消费仓无 model-tiers 段仍可运行
- **WHEN** 存量消费仓 config.yaml 未合并 model-tiers 段，跑任一编排 skill
- **THEN** skill 按内联缺省档位（opus/sonnet/haiku）运行，MUST NOT 报错或静默降级门禁步模型

#### Scenario: verify 档位来自映射
- **WHEN** 消费仓 model-tiers 把强档映射为某模型
- **THEN** sdflow-done 的 verify 子代理按该映射选模型；映射缺失时用内联强档缺省，MUST NOT 落到弱档

## MODIFIED Requirements

### Requirement: 阶段三过设计门后连续自动跑到 merge

阶段三 SHALL 在阶段二设计门之后无任何阻塞人类门地连续运行 `writing-plans → subagent-dev → sdflow-code-review → sdflow-done`；**编排层入口 = `/sdflow-ship`**（一次调用驱动 5.5→9，按「阶段三编排台账确定性」需求经 ship_gate 推进；手动逐步仍为合法 reference 路径）。能修的自动修；**遇 ≥2 方案 MUST 按三级决策协议**〔T10，替换旧"有把握自动选"自评表述〕：①有客观判据（测试/断言/基准可判）→ 自动选并记理由；②无客观判据 → 派对抗镜复核推荐项，通过方自动选（复核记录进报告）；③复核不过或无从复核 → defer 进 buglist/todolist 并由 hand-off 引导另开 change 清理。MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。修不了或需拍板的 MUST 进 buglist/todolist 延后。

#### Scenario: 修不了的问题延后而非阻塞
- **WHEN** sdflow-code-review 发现一个本 change 修不掉的问题
- **THEN** 它进 buglist/todolist(defer) 并写入 hand-off，流程继续跑到 sdflow-done，不设人类门阻塞

#### Scenario: 无客观判据的两方案走对抗复核
- **WHEN** 阶段三某步遇两个可行方案且无测试/断言可判优劣
- **THEN** 派对抗镜尝试证伪推荐方案：未被证伪 → 自动选并记复核记录；被证伪或复核无法开展 → defer，MUST NOT 凭"有把握"直接选

#### Scenario: 一次调用驱动到 merge 建议
- **WHEN** 对已过设计门的 change 调用 /sdflow-ship 且各步门禁全通过
- **THEN** 链依 gate 判定逐步推进至 sdflow-done 完成（含 merge 缺省语义），输出最终摘要；全程无 AskUserQuestion

### Requirement: 阶段二产出单一合并报告

阶段二 SHALL 由 `sdflow-spec-review` 编排器串起 autoplan 与多镜评审并产出**单一** `spec-review-report.md`，MUST NOT 要求人工手动合并多份报告。**执行序 MUST 串行**〔T20〕：Step2 多镜 fan-out MUST 待 Step1 autoplan 完成并 checkpoint 之后启动，MUST NOT 与 Step1 并行——多镜的评审对象须包含 autoplan 的 `[gstack-amendment]` 改动；若历史运行已并行，Step3 裁决 MUST 对 autoplan amendment 做增量核对并在报告注明。

#### Scenario: 阶段二收尾
- **WHEN** autoplan 与 spec-review 镜均完成
- **THEN** 编排器输出一份已去重合并、含决策登记区的 spec-review-report.md，供设计 HARD-GATE 人工一次性评审

#### Scenario: 多镜等待 autoplan 先行
- **WHEN** sdflow-spec-review 执行 Step2 规划镜头时 Step1 autoplan 尚未 checkpoint
- **THEN** MUST 等待其完成后再 fan-out；MUST NOT 以"求快"并行化（评审对象缺 amendment = 丢失复审性质）
