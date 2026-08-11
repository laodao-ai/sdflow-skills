# Task 3: SKILL 文案收口 — 实现报告

## 范围

三份 SKILL.md 收口，收敛「tickets 唯一管线」目标态，删除全部 config 键→marker→缺省三跳路由、
双名分列（`tickets.md` / `superpowers-plan.md`）、grandfather 分支等双轨表述。

## 改动清单

### `sdflow-ship/SKILL.md`（10 行改动）

- 链序 `RUN_PLAN`/`CONTINUE_IMPL` 段整体重写：删 `impl_route.py route` 调用（两处）、
  `PIPELINE_RECEIPT`、`pipeline=superpowers → superpowers:writing-plans` 派发分支（含
  `step6-writing-plans.md` 全文派发指令）、marker 缺席回退 SDD 分支、`RouteStop`/UNKNOWN
  路由判据、以及「试验期权威声明」整段。改为直连派发字面串：`RUN_PLAN` → 直派
  `sdflow-implement mode=tickets-plan change={change}`；`CONTINUE_IMPL` → 直派
  `sdflow-implement mode=tickets-exec change={change} done_tasks=…`（值取自 gate JSON
  `done_tasks`，原样透传）。保留了 checkpoint 标签格式权威（`ship_gate.py` `TAG_RE`〔T36〕）
  的引用式提及——不复述格式串，仅换了挂载点（原挂在被删的 writing-plans 分支下，现挂在
  RUN_PLAN 直连派发的括注里），以维持 `test_workflow_authority.py::test_skill_does_not_
  restate_the_format` 断言（详见下方「意外发现与修复」）。
- resume 节「实现中断的 resume：gate 输出已完成任务号集 → 传 SDD 勿重派」改写为指名
  `sdflow-implement mode=tickets-exec`（原文用泛称「SDD」，已过时但不在 grep 关键词命中
  范围内，判定为同类残留一并清理）。
- SHIPPED 摘要模板：删除 `pipeline` 字段来源说明段落（「若本次调用内未曾回显
  PIPELINE_RECEIPT…先补跑一次上述 route 命令」）；完成摘要行删 `pipeline={superpowers|
  tickets}` 槽位。

### `sdflow-implement/SKILL.md`（53 行改动）

- **frontmatter description**（触发条件唯一权威文本）：「仅当仓 `openspec/config.yaml` 的
  `impl-pipeline` 键（或在途 plan 的 frontmatter marker）取值为 tickets 时」→「tickets 唯一
  管线，由 /sdflow-ship 按 gate 判定以显式 mode= 参数派发」，逐字对齐 brief 措辞。
- 正文引言段：删「两态的 gate 插入点力学与旧 writing-plans/subagent-dev 管线等价（D1/D2）」
  比较句，改为直述当前态（「经 `/sdflow-ship` 链序以显式参数直接派发」）；`ship_gate.py`
  零改动段删「试验期外衣」措辞（改「完成判据契约」）与「计划文件名按轨分列〔D5/adr-0033〕：
  superpowers 轨保持 `superpowers-plan.md` 不变，两名经共享 resolver 定位，双存在
  fail-closed」整段，改写为单名表述 + frontmatter marker「文件格式契约（无路由读取方）」。
- 「## 模式派发契约」标题从「F4 单一源，与本 change plan 头部逐字共用」改为「本 skill 唯一
  权威源」；删除与 archive 历史件 `openspec/changes/archive/2026-07-10-matt-workflow-
  integration/superpowers-plan.md` 保持逐字同步的约束句——该约束要求当前 SKILL 与一份被
  Non-Goals 冻结、且已描述被删路由行为的历史文件保持字面一致，随路由删除已失去意义；本
  SKILL.md 现为该契约的唯一权威源，不再有同步对象。同段「管线选择完全是外部确定值（config
  键 → plan marker → 缺省一律 superpowers）」改写为「`mode=` 由调用方（`/sdflow-ship` 按
  gate 判定）显式字面传入」。
- 「## 依赖的确定性 helper」：删除 `route` 子命令的调用说明整块（该子命令已随 Task 1 从
  `impl_route.py` 物理删除，保留会指向不存在的 CLI 命令——即使不改也会在下一次真实调用时
  argparse 报错，故本条属于「代码事实已变、文案必须跟上」的正确性问题，非仅措辞收口）；
  标题上方引言「路由与拓扑判断」删「路由」二字。
- 「收尾票的定位」节末句：「该锚**按管线条件化**，superpowers 轨判『不适用』而非 gap」→
  「该锚为**无条件要求**」，对齐 brief「聚合锚从条件化改无条件」要求。
- 「外衣」节：「落盘路径固定」行删双名对照，改单名 + memo/adr 出处；「gate 第四道校验」段
  删「当且仅当计划文件名为 tickets.md」条件从句、「旧名 `superpowers-plan.md` 不触发本项
  校验（grandfather…）」分支、以及「此判据只用文件名区分…不是轨道路由」的双名辨析句——
  改写为无条件描述（`tickets.md` 是唯一计划文件，无需再区分「新出/在途/他轨」）。

### `sdflow-done/SKILL.md`（48 行改动）

- §0.3 tasks.md 复选框对账：删「或 `superpowers-plan.md` / subagent-driven-development
  〔D5：两轨计划文件名分列…〕」整段插入语，改单名表述。
- 第一步 Verify 第 4 项「实现期聚合覆盖需求」：删除整段轨道判定逻辑——「先判本 change 走的
  是哪条实现管线」起手句、对 `read_plan_marker`/`resolve_pipeline` 的判定实现引用、双名
  定位说明（`{tickets.md,superpowers-plan.md}`）、「按文件名判轨会让…被静默跳过」的
  grandfather 警示段、以及末尾单列的「superpowers 轨：该需求判『不适用』」分支。改写为
  「实现期聚合覆盖需求（无条件要求…）」标题 + 直接进入 tickets 收尾票核验逻辑（原「tickets
  轨」分支内容原样保留、去掉分支标签，成为唯一路径）。
- Merge 前一节脚注：「若实现期已逐 commit 提交（subagent-driven）」→「（tickets 管线逐
  ticket checkpoint 提交）」，指名当前唯一管线的提交模式。

### 保留的合法残留（未改动）

按 proposal.md《Success Metrics》四类合法残留清单核对，以下命中 grep 但未改动：

- `sdflow-implement/SKILL.md` 附录 A/B（4 处）：「借鉴 superpowers subagent-driven-
  development 的…」「对齐 superpowers writing-plans/subagent-driven-development 的
  pre-flight 冲突扫描」——均为设计出处说明（历史引用类），非当前路由/派发逻辑描述。
- `sdflow-done/SKILL.md` 模型档位对比脚注（1 处）：「对比 subagent-driven-development 的
  实现循环（高频、动态、上百任务）：那里『弱档转写实现 + 强档评审』是对的…」——用于说明
  sdflow-done 固定三步模型分档 vs. 动态任务循环模型分档风险的一般性设计原理对比，非声称
  当前系统仍走该管线，判定为历史/说明性引用，归入合法残留。

## 意外发现与修复

删除 `sdflow-ship/SKILL.md` 的 writing-plans 分支时，连带删除了该分支内唯一一处
`` `ship_gate.py` `TAG_RE`〔T36〕`` 引用，导致 `sdflow-ship/tests/test_workflow_authority.py::
test_skill_does_not_restate_the_format`（断言 SKILL.md 必须以「引用式」提及 `TAG_RE`、不得
复述完整格式串）失败。修复：在重写后的 `RUN_PLAN` 直连派发括注里补回同一条引用式声明
（「每 ticket 完成信号的 checkpoint 标签格式权威 = `ship_gate.py` `TAG_RE`〔T36〕，由
implementer 执行，此处不复述格式串」），语义与原文一致（checkpoint 标签格式的权威源仍是
`ship_gate.py` 的 `TAG_RE`），只是挂载点从「传给 writing-plans 的 args」改为「直连派发说明」。
测试复跑后绿。

## 验证

- `grep -nE "superpowers|writing-plans|subagent-driven" sdflow-ship/SKILL.md
  sdflow-implement/SKILL.md sdflow-done/SKILL.md`：剩余 5 处，全部落在上方「保留的合法残留」
  清单内，无遗漏双轨表述。
- `/usr/bin/python3 -m pytest sdflow-ship/tests/test_model_tiers.py
  sdflow-ship/tests/test_workflow_authority.py sdflow-ship/tests/test_anchor_contract.py -q`
  → 17 passed（含上方 TAG_RE 断言修复后复跑）。
- `/usr/bin/python3 -m pytest sdflow-ship/tests/ sdflow-implement/tests/ sdflow-done/tests/ -q`
  → 435 passed, 1 failed。失败项 `test_superpowers_track_regression.py::
  test_config_superpowers_route_resolves_superpowers` 断言 `impl_route.py route` 子命令存在，
  该子命令已被 Task 1 物理删除；此测试文件按 tickets.md Task 2 验收标准「整文件删除（存在
  意义即保护旧轨）」，退役属于 Task 2 范围，非本票引入的回归，确认为 Task 1 之后即已存在的
  预期失败态，不在 Task 3 修复范围内。
- `git diff --stat`：仅 3 个文件改动（`sdflow-done/SKILL.md` +37/-55 净行、
  `sdflow-implement/SKILL.md`、`sdflow-ship/SKILL.md`），无范围外改动。

## 验收标准自评

- [x] `sdflow-ship/SKILL.md` 链序段已重写为直连派发，完成摘要已删管线槽位
- [x] `sdflow-implement/SKILL.md` 双轨表述已收口，description 已更新
- [x] `sdflow-done/SKILL.md` 轨道判定步与条件化分支已删除
- [x] 三 SKILL 的 superpowers/writing-plans/subagent-driven grep 仅剩合法残留
