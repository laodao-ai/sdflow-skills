# Proposal: sdflow-ship

> 真相源 = [`adr/0004`](../../adr/0004-opsx-ship-stage3-orchestrator.md)（阶段三窄编排，含"改名须同步"条款）+ [`adr/0006`](../../adr/0006-execution-model-baseline-fleet-anchored.md) 约束(b)（ROADMAP 强制：**步序推进用确定性台账，SKILL prose 只管每步内部判断**）。命名循 `adr/0007`/R-SR-1：skill 定名 **`sdflow-ship`**（adr/0004 的 "opsx-ship" 为改名前暂名）。

## Why

三阶段的"连续"只做到了**设计层**（无强制中断），没做到**编排层**——过设计门后，人仍需照 workflow.md 逐步 copy prompt 手动驱动 5.5→9。且执行机队 = opus/sonnet/gpt-5.5（adr/0006）：弱主模型跑 15 步长表，漏 checkpoint / 漏注入点 B / 跳评审的概率随 prose 依赖上升——编排器是弱模型兜底机制，不是便利品。ROADMAP 建议序（footprint → rebrand → **ship**）走到本站。

## What Changes

- **新 skill `sdflow-ship`**：一次调用驱动阶段三 `embedded-test-sop`(条件) → `writing-plans`(→subagent-dev) → `sdflow-code-review` → `sdflow-done`(→merge)。meta-orchestrator：chain 现有 skill、不取代；**窄 scope 不越两个人类点**（不跨 grill、不跨设计门——过门后才起跑）。
- **确定性台账 `ship_gate.py`**〔adr/0006(b) 硬约束〕：**盘面即状态**——不设可变 state 文件，以 change 目录产物为账本；脚本机判"前置产物在否 / 上步门禁结论 / 下一步是谁"，输出结构化判定；SKILL.md 只写"每步前后调 gate 脚本、按其判定走"，禁 prose 步序记忆。
- **门禁传播机判**：`sdflow-done` verify FAIL / `sdflow-code-review` 真 blocker → gate 脚本从产物结论行判出 → 停并上抛（不蒙头跑）。起跑前置校验 = spec-review-report.md 存在**且含设计门拍板标记**（机判，无标记拒绝起跑）。
- **T10 认领——阶段三自动选推荐判据脱离自评置信**：决策协议三级：①有客观判据（测试/断言可判）→ 自动选并记理由；②无客观判据 → 对抗镜复核推荐项通过才自动选；③否则 defer。落 `sdflow-ship` SKILL.md 决策协议节 + 同步权威源 workflow.md 决策 4 措辞（替换"有把握自动选"的自评表述）。
- **T11 认领——模型档位映射进 config**：`config.template.yaml` 加 `model-tiers` 段（强档=verify/对抗裁决/final 终审；中档=领域镜/生成；弱档=纯机械步；各档默认模型），各编排 skill（sdflow-done/spec-review/code-review/ship）的模型选择节改为**引用该段**（缺省值内联保底），"强模型"措辞全部机队锚定落地。
- **T20 顺路——spec-review 串行纪律**：`sdflow-spec-review/SKILL.md` Step2 开头加 MUST 句（待 Step1 autoplan checkpoint 完成才 fan-out，禁并行——多镜评审对象须含 autoplan amendment）+ 已并行历史的补救纪律句。
- workflow.md 权威源：阶段三步骤表加"编排层入口 = `/sdflow-ship`"行（手动逐步仍为 reference 路径）；instance 经 `update --dev` 同步。
- 收尾同步：README 列表、ROADMAP 行更名 `sdflow-ship`、`adr/0004` 标题/暂名句按其自带条款同步注记。

## Capabilities

### New Capabilities

（无独立新 capability——编排层连续是 spec-workflow 既有能力域的行为扩展。）

### Modified Capabilities

- `spec-workflow`：①MODIFIED「阶段三过设计门后连续自动跑到 merge」——补编排层入口（sdflow-ship）、确定性台账、门禁传播、起跑前置校验、T10 决策协议；②ADD「阶段三编排台账确定性」（ship_gate 契约）；③ADD「模型档位映射」（config model-tiers 为真相源，skill 引用）；④MODIFIED「阶段二产出单一合并报告」——补 T20 串行纪律句（autoplan 先行）。

## Impact

- **代码**：新 `sdflow-ship/`（SKILL.md + `scripts/ship_gate.py` + tests）；`sdflow-init/assets/workflow/config.template.yaml`（model-tiers 段）+ workflow.md 步骤表；`sdflow-done`/`sdflow-spec-review`/`sdflow-code-review` SKILL.md（模型节引用 config + T20 句）；README/ROADMAP/adr-0004 注记。〔TG-01：bash/python 工具链，无领域清单命中〕
- **机械化**〔adr/0006〕：步序判定全在 `ship_gate.py`（pytest 单测覆盖各盘面态）；模型只做每步内部判断与 gate 输出的执行。
- **消费仓**：config 模版新段随 init 下发；存量仓 update 不动 config（既有语义），model-tiers 由模型按需合并——SKILL.md 缺省值保底，无段也能跑（不引入硬依赖）。

## Success Metrics

- `ship_gate.py` 单测覆盖全部盘面态：未过门拒跑 / 条件步命中与否 / 各步前置缺失点名 / verify FAIL 停 / blocker 停 / 全通推进到 merge 建议——**纯脚本单测**，不依赖模型行为。
- 一次 `/sdflow-ship` 调用在演练 change 上从过门态驱动到 merge 建议（真实激活演练归 hand-off，同 rebrand 模式）。
- 三个编排 skill 的"强模型"措辞零残留自评式表述（grep 断言）；workflow.md 决策 4 无"有把握自动选"旧句。
- config.template.yaml model-tiers 段 validate 通过且被 ≥4 个 SKILL.md 引用。

## Non-Goals

- 不做宽版全管线编排（不内置 grill/设计门暂停点——adr/0004 已弃）。
- 不改 subagent-driven-development / writing-plans 等外部 skill 本体（chain 不改造）。
- 不做跨模型镜（Phase C 范围）。
- ship_gate 不写可变 state 文件（盘面即状态；防第二真相源漂移）。

## Stakeholders & External Dependencies（TG-20）

- 依赖外部 skill 稳定性：superpowers（writing-plans/subagent-dev）与 gstack（review，经 sdflow-code-review 内部）——沿 adr/0002 复用产出物边界，ship 只认产物文件。
- 双 agent：sdflow-ship 装两侧；ship_gate.py 为 python 脚本（Codex 侧可执行，同 recorder 先例）。
- 消费仓：model-tiers 为可选增强段，缺省不破坏既有 config。

## Open Questions（TG-21）

1. gate 判定输出形态：JSON（机读友好）vs 单行文本（弱模型照抄友好）——design 定（倾向 JSON + 一行人读摘要双输出）。
2. "设计门拍板标记"的机判锚点措辞（现有两轮实践均含"设计门拍板"字样行；design 钉字面约定）。

## Compliance

无 DB/外部计费（D-2/TG-24 N/A）；不越人类点（adr/0004 红线）；门禁传播遵『任何一层评审覆盖不得无声蒸发』元原则；ship_gate 只读 change 目录产物、不改任何文件。
