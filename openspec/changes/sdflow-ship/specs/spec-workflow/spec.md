# spec-workflow Specification (delta)

> 本 delta = `sdflow-ship`：阶段三补编排层连续（确定性台账驱动）+ 决策协议脱离自评置信（T10）+ 模型档位映射（T11）+ 阶段二串行纪律（T20）。
> 真相源 = [`adr/0004`](../../../adr/0004-opsx-ship-stage3-orchestrator.md) + [`adr/0006`](../../../adr/0006-execution-model-baseline-fleet-anchored.md) + [design.md](../../design.md)。

## ADDED Requirements

### Requirement: 阶段三编排台账确定性（ship_gate）

`sdflow-ship` 的步序推进 MUST 由确定性脚本 `ship_gate.py` 判定（**盘面即状态**：以 change 目录产物存在性与结论行为账本，MUST NOT 设可变 state 文件造第二真相源）；编排 skill MUST 在每步前后调用 gate 并遵其判定，MUST NOT 以 prose 记忆步序。gate MUST 只读（零副作用）、双输出（首行人读摘要 + JSON 机读）、以退出码承载门禁语义（0=可推进 / 3=拒绝起跑 / 4=上游 blocker / 5=verify FAIL）。机判锚点 MUST 为**模板写死的机器注释行**〔grill-amendment：自然语言结论行正则对真实存档全 miss，禁作锚点〕：设计门拍板 = `<!-- ship-gate: design-approved -->`；verify 结论 = `<!-- ship-gate: verify=PASS -->` / `verify=FAIL`；code-review 放行 = `<!-- ship-gate: code-review=pass -->` / `=blocked`。三个报告的生成模板（sdflow-spec-review 拍板回写约定 / sdflow-done verify 模板 / sdflow-code-review 报告格式）MUST 输出对应锚行；gate 以字面查找（非正则）解析，锚行集合在脚本头注释与各模板双向钉死同 change 演进。

#### Scenario: 未过设计门拒绝起跑
- **WHEN** 对一个 spec-review-report.md 缺失或不含「设计门拍板」标记的 change 调用 /sdflow-ship
- **THEN** ship_gate 退出码 3（REFUSE_START），skill 停止并提示先完成设计门，MUST NOT 起跑任何阶段三步骤

#### Scenario: verify FAIL 停并上抛
- **WHEN** 链行进至 sdflow-done 后 verify-report.md 结论为 FAIL
- **THEN** gate 退出码 5，ship 停止、原样上抛缺口清单，MUST NOT 继续 archive/merge（任何一层评审覆盖不得无声蒸发）

#### Scenario: 前置产物缺失点名
- **WHEN** 某步产物缺失（如 code-review-report.md 不在）
- **THEN** gate 输出 next=对应 skill 与 missing 清单，编排按此推进；实现完成判据 MUST 以 **git 历史 checkpoint 任务标签为主锚**（plan 任务数 N 对 `checkpoint(task<k>-` 去重任务号集，齐 N 判完成〔grill-amendment〕）、plan 复选框全勾为辅，两通道皆不可判时 gate 判 UNKNOWN 停上抛，MUST NOT 猜测推进、MUST NOT 以 gitignored 的 SDD ledger 为判据

#### Scenario: 陈旧 FAIL 不卡死 resume〔grill-amendment D9〕
- **WHEN** verify-report 带 FAIL 锚行，其提交之后存在触及 `openspec/` 之外路径的修复提交，用户重调 /sdflow-ship
- **THEN** gate 判该结论陈旧 → NEXT=重跑 sdflow-done（重验），MUST NOT 以陈旧 FAIL 退出卡死

#### Scenario: 干预后陈旧 PASS 不放行〔grill-amendment D9〕
- **WHEN** 各门禁锚行均为 pass/PASS，但其后有人手改了 `openspec/` 之外的代码
- **THEN** gate 判受影响步结论陈旧 → 重跑该步，MUST NOT 让旧结论背书新代码直通 merge

#### Scenario: 无锚行产物 = 步进行中〔grill-amendment D9〕
- **WHEN** 某报告文件存在但不含任何 ship-gate 锚行（如中断的半成品）
- **THEN** gate 判该步进行中 → NEXT=重跑该步，MUST NOT 当作已完成

#### Scenario: 暂停后重调即续、人机同权〔grill-amendment D9〕
- **WHEN** 链中途停止（任意原因），期间用户手动完成了某步（如手跑 /sdflow-code-review 产出报告），之后重调 /sdflow-ship
- **THEN** gate 仅凭盘面推进（不辨产者），从下一缺口继续；实现中断场景 gate 输出已完成任务号集供 SDD 勿重派；ship MUST NOT 依赖任何跨步内存状态

#### Scenario: 条件步按 TG 判定
- **WHEN** change 的 proposal 未标注 TG-02（非嵌入式）
- **THEN** gate 对 step 5.5 输出 SKIP 并记录理由；命中 TG-02 时高风险/TG-18 细判归模型（每步内部判断，prose 允许域）

### Requirement: 模型档位映射（model-tiers）

模型档位定义、职责清单与 canonical 缺省 MUST 以 workflow bundle 规则文件 **`model-tiers.md`** 为单一真相源（经 resolver 全局解析；强档=verify/对抗裁决/final 终审；中档=领域镜/生成/实现；弱档=纯机械步；缺省 opus/sonnet/haiku）〔grill-amendment：推翻"config 段真相源 + SKILL 内联缺省×4"——多处 copy 漂移面〕；消费仓 `config.yaml` 的 `model-tiers` 段 MUST 仅作可选 per-repo **覆盖**；编排 skill（sdflow-ship/done/spec-review/code-review）的模型选择 MUST 以一句引用指向规则文件与覆盖段，MUST NOT 内联具体模型名（机队锚定，adr/0006(c)）。

#### Scenario: 消费仓无覆盖段用 canonical 缺省
- **WHEN** 消费仓 config.yaml 无 model-tiers 段，跑任一编排 skill
- **THEN** skill 按规则根 `model-tiers.md` 的 canonical 缺省档位运行，MUST NOT 报错、MUST NOT 静默降级门禁步模型

#### Scenario: verify 档位来自映射（覆盖优先）
- **WHEN** 消费仓 config.yaml model-tiers 段把强档覆盖为某模型
- **THEN** sdflow-done 的 verify 子代理按覆盖映射选模型；无覆盖时用规则文件强档缺省，MUST NOT 落到弱档

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

#### Scenario: ship 零 git 写操作、merge 意图透传〔grill-amendment〕
- **WHEN** 用户以"跑到 merge 前停"类意图调用 /sdflow-ship
- **THEN** ship 将 opt-out 原样透传给 sdflow-done（merge 由 done 一处执行/跳过）；ship 自身 MUST NOT commit/merge/push，MUST NOT 自动 push（摘要提醒手动 push；toolkit 源仓附激活提示）

### Requirement: 阶段二产出单一合并报告

阶段二 SHALL 由 `sdflow-spec-review` 编排器串起 autoplan 与多镜评审并产出**单一** `spec-review-report.md`，MUST NOT 要求人工手动合并多份报告。**执行序 MUST 串行**〔T20〕：Step2 多镜 fan-out MUST 待 Step1 autoplan 完成并 checkpoint 之后启动，MUST NOT 与 Step1 并行——多镜的评审对象须包含 autoplan 的 `[gstack-amendment]` 改动；若历史运行已并行，Step3 裁决 MUST 对 autoplan amendment 做增量核对并在报告注明。

#### Scenario: 阶段二收尾
- **WHEN** autoplan 与 spec-review 镜均完成
- **THEN** 编排器输出一份已去重合并、含决策登记区的 spec-review-report.md，供设计 HARD-GATE 人工一次性评审

#### Scenario: 多镜等待 autoplan 先行
- **WHEN** sdflow-spec-review 执行 Step2 规划镜头时 Step1 autoplan 尚未 checkpoint
- **THEN** MUST 等待其完成后再 fan-out；MUST NOT 以"求快"并行化（评审对象缺 amendment = 丢失复审性质）
