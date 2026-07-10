---
ship-gate:
  verify: PASS
---

# Verify Report — matt-workflow-integration

- 日期：2026-07-11
- change：`matt-workflow-integration`
- **结论：PASS**（20 项任务 + 7 条 impl-orchestration Requirement + 3 条 spec-workflow Requirement 全部核实；唯一遗留为 6.3 的「运行 checkout 还原」——属 merge+push 后已排期的发布边界步，Minor，可接受）

核对方式：不信任复选框与既有报告措辞，逐条落可机验锚点（测试名 / 文件:行 / 实测输出）。可运行验证：
`python3 -m pytest sdflow-implement/tests/ sdflow-ship/tests/ sdflow-init/tests/ -q` → **355 passed**；
`readlink ~/.claude/skills/sdflow-implement` 与 `~/.codex/skills/sdflow-implement` → 均指向 dev checkout。

## 逐任务核对表（tasks.md 20 项）

| 需求/任务 | 代码出处（文件:行 / 测试 / 实测） | 状态 |
|---|---|---|
| 1.1 SKILL.md 骨架·双模式·派发字面契约·无 disable-model-invocation | `sdflow-implement/SKILL.md:1-10`（frontmatter 无该旗标）、`:26-39`（模式派发契约 `mode=tickets-plan\|tickets-exec`，声明「与 plan 头部逐字共用」）；无「出 ticket 后继续执行」路径（`:137-153` 落盘→checkpoint→返回三步，MUST NOT 同调用直通执行） | ✅ |
| 1.2 出 ticket 契约：3-6 张切片·Blocked-by·expand–contract·Global Constraints 逐字·验收框·外衣文件名+标题+marker·删 quiz·收尾 checkpoint | `SKILL.md:74-135`（切片/宽重构例外 E5 `:83-90`）、`:92-104`（外衣：`superpowers-plan.md`+`### Task N:`+单键 frontmatter）、`:137-153`（显式 checkpoint 命令原文 `:145`）、`:134`（删 quiz-the-user）；模板样例过 gate 三道校验 → `test_tickets_plan_golden.py`（GOLDEN 3 票、无重号、无失衡 fence，全绿） | ✅ |
| 1.3 执行模式：frontier 串行·fresh implementer·状态词表四值·halt envelope·report file 交接·cannot-verify 预算上界 | `SKILL.md:155-252`（串行红线 `:170-172`、四值处置表 `:190-202`、halt envelope 五要素 `:204-211`、report 路径契约 `:186`、cannot-verify 预算>3 文件 `:249-252`、双写时序 `:182-188`） | ✅ |
| 1.4 每 ticket 双轴审·domains 注入必填槽·<400 词·Critical/Important→fix环·Minor→todolist 带 change·无 warm 终审 | `SKILL.md:254-277`（Standards 轴 domains 经 resolve-workflow.sh 注入=必填槽 `:259-262`、F13 未覆盖不宣称通过 `:261-262`、封顶<400 词 `:256`、fix+re-review 熔断 `:267-271`、Minor JSON 带 `"change"` `:272-273`、无 warm final `:275-277`） | ✅ |
| 1.5 裁剪边界声明：无 warm 终审/无 ledger/无 task-brief 各一句去向 | `SKILL.md:279-291`（三项各附去向说明） | ✅ |
| 2.1 ship description 中性化 + 链序条件路由 + 权威声明 | `sdflow-ship/SKILL.md:3`（description 用「实现管线」中性表述）、`:29`（RUN_PLAN/CONTINUE_IMPL 三跳确定值路由 + route CLI 调用 + 「链序为权威、gate next 仅信息性」声明）；其余链序段零改动 | ✅ |
| 2.2 config 增 impl-pipeline 可选键注释段 + lint 放行 + 不注入存量 | `sdflow-init/assets/workflow/config.template.yaml:64-67`、`openspec/config.yaml:61-64`（均注释态、缺省勿填）；实测 `lint_config` 含/不含该键均返回 `[]`（放行） | ✅ |
| 2.3 stdlib-only route + frontier helper + pytest + PIPELINE_RECEIPT | `sdflow-implement/scripts/impl_route.py`（route `:350-387`、frontier `:390-420`、PIPELINE_RECEIPT 一行 `:385-386`、非法/重复 marker→RouteStop `:136-180`、拓扑环/自环/缺依赖 `:281-291`）；不 import yaml/不触 gate（`:13-15`）；`test_impl_route.py` 全绿（路由矩阵+拓扑+跨脚本 golden 回归） | ✅ |
| 3.1 workflow.md 阶段一三段分流 + wayfinder 缺装降级 + 事中可观察判据 | `sdflow-init/assets/workflow/workflow.md:12-24`（图：清晰→ff/单session→explore/超单session→wayfinder，缺装→explore 降级 `:22`）、`:80-81`（explore 行 + wayfinder 1b 行，判据「已跨 session/跨天/经历 /clear 未收敛」事中可观察 `:17-19`） | ✅ |
| 3.2 ff-constraints 衔接契约节 + 独立切片建议条款 + 双注入通道 + zoom≤8+grep 锚 | `ff-generation-constraints.md:25-43`（衔接契约：逐区读 map、TG 前置写 Notes、回链，zoom≤8 `:36`，grep 锚 `〔wayfinder-resolved:...〕` `:39-41`）、`:45-55`（切片建议独立条款，条件=`impl-pipeline: tickets`，MUST NOT 用 wayfinder-resolved 前缀）；双注入 = `openspec/config.yaml:38,47`（rules 段契约文本）+ `workflow.md:82`（ff 调用行携带 map 路径）；两条款条件互不渗漏（`:47-48` 显式声明勿混） | ✅ |
| 3.3 workflow.md grill 行瘦跑措辞 | `workflow.md:83`（grill prompt：已决分支引 resolution 快速核对即过、新生成/未决照常死磕、无回链锚一律全深度、MUST NOT 整跳 grill） | ✅ |
| 3.4 阶段三 config 键脚注 + 禁 /clear 并列 sdflow-implement + 刷新托管块 | `workflow.md:45-46,87,88`（config 键脚注，不改默认口径）、`:95,132`（禁 /clear 并列 sdflow-implement）；`sdflow-init/assets/snippets/claude-section.md:13` 与 `CLAUDE.md:128` 托管块 —— `diff` 确认逐字一致 | ✅ |
| 4.1 disable-model-invocation 实测 + 结论留档 | `impl-notes.md:3-14`（结论「阻断」+ 两次独立实证依据；处置：维持不写旗标） | ✅ |
| 4.2 出 ticket→gate→执行最小演练留档 | `impl-notes.md:16-40`（7 步演练表，全程 gate 零改动零 UNKNOWN；receipt/后置双写/resume 续审/frontier 拓扑全过） | ✅ |
| 4.3 golden-file 回归（committed 样例 + 边界 fixtures） | `sdflow-ship/tests/fixtures/tickets_plan_golden.md` + `tickets_plan_fenced_header.md` + `tickets_plan_fence_dangling.md`；`test_tickets_plan_golden.py`（plan_task_ids/unbalanced_fence/duplicate_task/checkbox_done_ids + 边界断言，全绿） | ✅ |
| 5.1 试点选样+判赢通道+PIPELINE_RECEIPT留档+档位钉死mid+roadmap Phase C 占位 | `pilot-briefing.md`（候选池①、拒绝条件②、判据三条③定性无数字阈值、receipt 逐change留档④、档位钉死mid⑦、SHIPPED后再生retro⑥）；`openspec/roadmaps/workflow-cost-optimization/roadmap.md:165-168`（阶段 C 占位：目标句+雾区备注） | ✅ |
| 5.2 ≥1 消费仓缺省路径验证 | `pilot-briefing.md:68-87`（`~/Documents/10-michi` 无键、`route` 输出 `pipeline=superpowers`、验证前后 git status 零变化；RUN_PLAN 仍派 writing-plans） | ✅ |
| 6.1 README 增 sdflow-implement 行 + 活文档留 Phase B | `README.md:21`（编排（阶段三）行）+ `:30`（归数据类 skill，因含 scripts/tests——比 tasks 粗分「编排类」更精确，非缺口）；活文档全量表述留 Phase B 记于 `impl-notes.md:42-45` | ✅ |
| 6.2 dev checkout 重跑 setup.sh 建链 | `readlink ~/.claude/skills/sdflow-implement` 与 `~/.codex/skills/sdflow-implement` → 均 = `/Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-implement`（链接已建、无孤儿） | ✅ |
| 6.3 测后还原与发布窗口（CLAUDE.md 反向窗口句 + 运行 checkout 还原） | CLAUDE.md 反向窗口句已落 `CLAUDE.md:101`（pull 后链序即生效、新 skill 链接须 setup 后才存在）；**运行 checkout（~/.skills/sdflow-skills）还原 symlink 属 merge+push 后发布边界步，已排期经 /sdflow-upgrade 执行**（tasks.md 诚实注记，`readlink ~/.claude/skills/sdflow-implement` 现指向 dev checkout 属测试期正常态） | ⚠️Minor |

## 逐 Requirement 核对（spec delta）

### impl-orchestration（全 ADDED，7 条）

| Requirement | 锚点 | 状态 |
|---|---|---|
| R1 管线路由为手动确定值，零模型自动判断 | `impl_route.py`（三跳 config→marker→缺省 `:89-190`；marker 非法/重复→RouteStop 停不静默回退 `:136-180`；ship_gate 零依赖 `:13-15`；PIPELINE_RECEIPT `:385`）；ship `SKILL.md:29` 显式字面 args 派发；Scenario「缺省与非法值 fail 向旧管线」→ `test_config_value_typo`/`test_cli_route_unknown_config_value_echoed`；Scenario「在途不受 config 切换」→ `test_cli_route_marker_locks_over_config_change` | ✅ |
| R2 出 ticket 模式产出 tracer-bullet 并落盘即返回 | `SKILL.md:56-153`（3-6 张切片、禁预写代码/路径 `:74-78`、expand–contract 例外+批次不占预算 `:83-90`、Global Constraints 逐字 `:99-101`、落盘→checkpoint→返回 `:137-153`、删 quiz `:134`） | ✅ |
| R3 ticket 文件兼容 ship_gate 完成判据契约 | `SKILL.md:92-104,213-240`（外衣文件名/标题/单键 frontmatter、后置双写 `:213-226`、plan 结构不可变 `:102-103`）；`ship_gate.py` 零改动 → golden 全绿 `test_tickets_plan_golden.py`；Scenario「双通道判定完成」→ `test_golden_checkbox_done_ids`（Task1 勾框计入） | ✅ |
| R4 执行模式串行 frontier 并以文件交接 | `SKILL.md:155-252`（串行 `:170-172`、fresh implementer `:174-188`、状态词表四值 `:190-202`、halt envelope `:204-211`、report/review-package 文件交接 `:186,242-248`、cannot-verify 预算上界 `:249-252`）；frontier next-ready 确定性 helper → `impl_route.py:313-318` + `test_parse_diamond`/`test_cli_frontier_prints_ready_list` | ✅ |
| R5 每 ticket 双轴审加修复环，领域清单注入 Standards 轴 | `SKILL.md:254-277`（注入点 B 必填槽 `:259-262`、F13 降级不宣称通过 `:261-262`、Critical/Important→fix+re-review `:267-271`、Minor→todolist 带 change `:272-273`、无 warm final `:275-277`） | ✅ |
| R6 不引入 ledger 与 task-brief 层 | `SKILL.md:279-291`（无 ledger→gate 双通道 resume；无 task-brief→ticket 文本即 brief） | ✅ |
| R7 试点回退与熔断哨兵 | `pilot-briefing.md`（哨兵③恶化即熔断、选样拒绝条件②、SHIPPED后再生retro核对哨兵⑥、receipt 与 config 意图核对④）；roadmap `:165-168` Phase C 硬前置于 Phase A 判赢 | ✅ |

### spec-workflow（MODIFIED 1 + ADDED 2，3 条）

| Requirement | 锚点 | 状态 |
|---|---|---|
| W1 阶段三过设计门后连续跑到 merge（可选双轨，MODIFIED） | `workflow.md:43-58,87-90`（阶段三行：缺省 writing-plans→subagent-dev / 可选 impl-orchestration 手动路由；编排入口 `/sdflow-ship`）；`sdflow-ship/SKILL.md:29`（管线选择确定值路由、无模型判断、无新增人类门；BLOCKED 停机同构 BLOCKED_UPSTREAM）；T10 三级决策协议 `sdflow-ship/SKILL.md:23` | ✅ |
| W2 阶段一按雾量三段分流 + wayfinder→ff 衔接契约（ADDED） | `workflow.md:12-24,80-82`（三段分流 + 事中判定）；`ff-generation-constraints.md:25-43`（衔接契约三条 + zoom≤8 + grep 锚）；双注入通道 = `config.yaml:38,47` + `workflow.md:82`（FF-0 先例=仅写约束文件不构成注入，已双落） | ✅ |
| W3 grill 对上游已决分支瘦跑（ADDED） | `workflow.md:83`（引 resolution 快速核对即过、无回链锚全深度、MUST NOT 语义模糊匹配定已决、MUST NOT 整跳 grill）；`ff-generation-constraints.md:41`（瘦跑以 `wayfinder-resolved:` 前缀为唯一判据） | ✅ |

## 缺口清单

### 核心缺口

无。R1-R7、W1-W3 的 MUST 行为均有可机验锚点；`ship_gate.py` 零改动铁律经 355 测试（含跨脚本 golden 回归）与 impl-notes 演练双证。

### Minor 缺口（可接受 / 已排期）

- **6.3 运行 checkout（`~/.skills/sdflow-skills`）重跑 setup.sh 还原全局 symlink**：属 merge+push 后的**发布边界步**（adr/0005 协议下半场），tasks.md 已诚实注记为部分完成、并明确该步在 push 后经 `/sdflow-upgrade` 执行并以 `readlink` 验证。CLAUDE.md 反向窗口句（该任务的另一半）已落地（`CLAUDE.md:101`）。当前 `readlink` 指向 dev checkout 是测试期正常态，非缺陷。**判为 Minor（已排期发布边界步），不阻塞 verify PASS。**
- **6.1 分类措辞**：tasks 6.1 粗称 sdflow-implement 为「编排类」，README 实际归为「数据类 skill」（因其含 `scripts/`+`tests/`，符合本仓数据类定义）——README 分类**更精确**，非缺口，仅记录以免误读。

## 结论

PASS
