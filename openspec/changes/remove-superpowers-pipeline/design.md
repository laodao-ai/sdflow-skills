# Design · remove-superpowers-pipeline

## Context

动机见 proposal.md《Why》。现状约束（塑形本设计的仅此四条）：

- `impl_route.py` 是三分肢文件：route 半场（管线路由）与 frontier/task-text 半场（tickets 调度基础设施）共居一文件；`ship_gate.py` 经惰性 sibling-import 消费其 `parse_blocked_by` / `TopoError`（收尾票 Blocked-by 校验单一源，基准 5：拓扑解析不写第二份）。
- `ship_gate.py` 的计划文件定位层（`PLAN_FILENAMES` 双名探测 + 旧名 grandfather）是纯定位逻辑，路由权威从不在 gate（零 config 依赖不变量，specs/impl-orchestration 明文）。
- bundle 权威源在 `sdflow-init/assets/workflow/`，改规则先改 assets 再 `sdflow-init update` 推送；本仓 CLAUDE.md/AGENTS.md 托管区块由 update 刷新。
- 在途旧轨 change 为零、本机下游仓无显式旧值键（memo C1/C2）——无迁移保护对象，可一次切净。

## Goals / Non-Goals

**Goals:**

- 运行时路径（scripts / SKILL / bundle assets / specs）中 superpowers 管线分支归零：无路由调用、无双名探测、无双轨条件化文案。
- `impl_route.py` 保留半场（frontier / task-text / parse_blocked_by）接口与行为逐字不变——gate sibling-import 与 sdflow-implement 执行模式零感知。
- 测试面与实现同步收口：退役参照系（目标态已不存在的行为）的用例删除，保留半场用例全绿。

**Non-Goals:**

- 见 proposal.md《Non-Goals》；设计层补充一条边界：**不改 gate 的完成判据窗口机制与 checkpoint 标签契约**（`TAG_RE` / `git log --diff-filter=A` / frontmatter 状态集判据均不动，本 change 只动计划文件的*定位*）。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)；架构级决策已记 [`adr/0042`](../../adr/0042-tickets-sole-impl-pipeline.md)（TG-23）。

## 路由行为对照（v_old / v_new）

| 场景 | v_old（三跳路由） | v_new（直连） |
|---|---|---|
| RUN_PLAN | `impl_route.py route` 读 config 键 → PIPELINE_RECEIPT → tickets ⇒ 派 `sdflow-implement mode=tickets-plan`；superpowers ⇒ 派 writing-plans（step6 prompt 全文） | 无 helper 调用，直接派 `sdflow-implement mode=tickets-plan change={change}` |
| CONTINUE_IMPL | 重调 `route` 读 plan marker → tickets ⇒ `mode=tickets-exec`；marker 缺席 ⇒ 回退 SDD dispatch；marker 非法 ⇒ RouteStop/UNKNOWN | 无 helper 调用，直接派 `sdflow-implement mode=tickets-exec done_tasks={gate JSON 透传}` |
| 计划文件定位 | 双名按序探测（`tickets.md` → `superpowers-plan.md`）；双存在 ⇒ UNKNOWN；旧名 ⇒ 收尾票校验 grandfather 跳过 | 单名 `tickets.md`；存在 ⇒ 用之（收尾票校验一律执行）；不存在 ⇒ RUN_PLAN |
| config `impl-pipeline` 键 | tickets/superpowers 合法值；缺省 tickets | 无读取方（键退役；存量键惰性无害） |
| `tickets.md` frontmatter marker | 路由锁定信号（`read_plan_marker` 消费） | 惰性文件格式契约（写而不读，模板不变，memo D3） |
| gate JSON `next` 在 RUN_PLAN/CONTINUE_IMPL | 输出 writing-plans/subagent-dev，仅信息性（试验期权威声明凌驾） | 与实际派发一致（信息性错位随分支消失而消解） |

## 组件依赖图（目标态；带 ✂ 者本次删除）

```
/sdflow-ship SKILL 链序
   │  RUN_PLAN ──────────────► sdflow-implement mode=tickets-plan
   │  CONTINUE_IMPL ─────────► sdflow-implement mode=tickets-exec
   │       ✂ impl_route.py route（config 键 → marker → 缺省 三跳）
   │       ✂ writing-plans 派发分支（step6-writing-plans.md 整文件）
   │
   ├─ ship_gate.py
   │    ├─ resolve_plan_path ──► tickets.md（单名）
   │    │      ✂ superpowers-plan.md 探测 / 双存在 UNKNOWN / 收尾票 grandfather
   │    └─ sibling-import ────► impl_route.parse_blocked_by / TopoError（不变）
   │
   └─ sdflow-implement SKILL
        ├─ impl_route.py frontier ──► next-ready ticket 批（不变）
        └─ impl_route.py task-text ─► Task 段抽取（不变）
```

## 组件清单（改动面 × 动作）

| 组件 | 动作 |
|---|---|
| `sdflow-implement/scripts/impl_route.py` | 切除：`route` 子命令、`_cmd_route`、`read_config_pipeline`、`read_plan_marker`、`resolve_pipeline`、`LEGAL_PIPELINES`、`_PIPELINE_KEY_RE`、`RouteStop`、`_get_plan_sha`、文件头三跳注释改写为「tickets 调度 helper」自述。保留：`frontier` / `task-text` 子命令、`parse_blocked_by`、`_detect_cycle`、`next_ready`、`extract_task_text`、`TopoError`、`BLOCKED_BY_RE`、`_yq`——**接口与行为逐字不变** |
| `sdflow-ship/scripts/ship_gate.py` | `PLAN_FILENAMES` → `("tickets.md",)`（或收敛为常量单名，保留 resolver 函数形状供 gate/测试共用）；删旧名 grandfather 分支与双存在 UNKNOWN 分支；RUN_PLAN reason / UNKNOWN 表 / 文件头注释中的双名表述改单名；`PLAN_FILENAMES` 上方 :1329-1335「共享 resolver」说明注释块（引用被删符号 `impl_route.resolve_pipeline`）一并改写〔spec-review-amendment〕 |
| `sdflow-ship/SKILL.md` | 链序 RUN_PLAN/CONTINUE_IMPL 段重写为直连派发（含删「试验期权威声明」——`next` 信息性错位随分支消失）；完成摘要行 `pipeline={superpowers\|tickets}` → 删该槽位 |
| `sdflow-implement/SKILL.md` | 删「缺省一律 superpowers」「双名分列」「聚合锚按管线条件化」表述——聚合锚无条件化；frontmatter marker 表述改「文件格式契约（无路由读取方）」；**description frontmatter**（触发条件唯一权威文本，现锚定 impl-pipeline 键）改「tickets 唯一管线，由 /sdflow-ship 按 gate 判定以显式 mode= 参数派发」〔spec-review-amendment〕 |
| `sdflow-done/SKILL.md` | 删 verify 的轨道判定步（`read_plan_marker`/`resolve_pipeline` 引用）、「superpowers 轨判不适用」分支、grandfather 警示——「实现期聚合覆盖」锚无条件要求 |
| `sdflow-init/assets/workflow/` | `workflow.md`（子步骤 A、显式 superpowers 段、检查清单行）/ `WORKFLOW-GUIDE.md`（同上）/ `ff-generation-constraints.md`（切片建议条件行改无条件）/ `config.template.yaml`（键注释删）/ `prompts/step6-writing-plans.md`（**整文件删**）/ `reference/quality-layering.md`（superpowers SDD 注入点 A/B 与「用 superpowers 跑实现时」清单节删） |
| `sdflow-init/assets/snippets/claude-section.md` | 「实现管线缺省 = tickets／显式 superpowers」段 → 「实现管线 = tickets（唯一）」；改后 `sdflow-init update` 刷本仓 CLAUDE.md/AGENTS.md 托管区块 |
| `openspec/config.yaml` | `impl-pipeline` 键 + 注释（:60-64）删除 |
| `openspec/INDEX.md` | impl-orchestration 描述行（「手动路由三跳」）改单管线表述〔spec-review-amendment〕 |
| 测试群 | 见 memo C7 逐文件映射；另 `test_workflow_authority.py`（step6 TAG_RE 样例断言）与 `test_workflow_split.py` / `test_checkpoint_slug_coverage.py` 的 step6 条目随文件删除退役/改名单；gate 共享 fixture `approved_change` 默认写入名迁 `tickets.md`（test_gate_git_layer / freshness / namespace / impl_progress / tail / reviewed_sha / plan_resolver 7 文件 63 处消费点逐一核验），`test_gate_closing_ticket.py` :130/:160 两条 grandfather 用例退役〔spec-review-amendment〕 |
| `docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md` | 头部一行 obsolete 标注（指向 adr/0042）；现役视图文档 `docs/workflow-overview.md` / `docs/workflow-map.md`(+`.html`) / `docs/workflow-console.html` / `docs/criteria-mechanization-tracker.md` 同步去旧路由叙述〔spec-review-amendment〕 |
| specs | 见 proposal《Modified Capabilities》，delta 文件在本 change `specs/` 下 |

## Risks / Trade-offs

- [gate sibling-import 断裂：切除 route 时误删/误动 `parse_blocked_by` 依赖的符号] → 保留半场接口逐字不变为硬约束；`test_gate_closing_ticket.py`（:130/:160 两条 grandfather 用例除外——它们断言被删行为，随本 change 退役〔spec-review-amendment〕）与 `test_impl_route.py` 保留半场用例作回归网；实现票按「先删测试再删实现」顺序防漏。
- [SKILL 文案收口遗漏（双轨表述残留某处）] → Success Metrics 的 grep 扫尾判据兜底（运行时路径仅剩合法残留清单）；评审接地镜核对。
- [下游仓 update 窗口期文案双态] → 已接受边角（memo「接受的边角」第三条）：无行为分叉，仅人读层双态。
- [其他机器存在未扫到的显式旧值键] → 键退役使任何取值无行为差异（proposal《假设》）；无静默混跑面。
- [step6 删除连带 checkpoint 标签契约样例丢失] → 标签契约权威本就是 `ship_gate.py TAG_RE`（step6 只是样例载体）；tickets 轨的标签指令在 `sdflow-implement/SKILL.md` 自持，`test_checkpoint_slug_coverage.py` 名单更新后继续守其余载体。

## Migration Plan

1. 本仓实现 + 全仓 pytest 绿 + 评审 + merge main（常规 change 流程，无特殊迁移步）。
2. 运行 checkout：`git pull` + **立即** `bash setup.sh`（发布纪律不变）。本 change 的真实偏斜向量不是 pull→setup 窗口——sdflow-ship / sdflow-implement 均为既存 symlink skill，pull 即原子刷新 SKILL 与脚本；而是**长跑 session 已把旧 SKILL 读入 context、磁盘其间被 pull 更新**：此时旧链序调已删的 route 子命令，argparse 报 invalid choice 且 exit 2——fail-loud，非静默错轨〔spec-review-amendment〕。
3. 下游仓：各自下次 `sdflow-init update` 收敛文案；不强制立即执行（行为无变化）。
4. **回滚** = `git revert` 本 change → 运行 checkout 重跑 `setup.sh` → 各已 update 的下游仓重跑 `sdflow-init update`。方向性成本高，不设计快捷回滚（adr/0042《Consequences》）。

## Compliance

- 遵守 bundle 单一权威源纪律（先改 assets 再 update 推送，禁只改下游）。
- 遵守 `openspec/rules/doc-authoring.md`（DOC-1）：本文只写目标态，演进语境在 adr/0042 与 memo。
- 遵守基准 5：不新写任何计划文件解析；Blocked-by 拓扑继续复用 `parse_blocked_by` 单一源。
- 托管区块（CLAUDE.md/AGENTS.md 的 `sdflow:principles` 与 workflow 区块）不手改——经 `sdflow-init update` / `sync_principles.py` 机械刷新。
- 无豁免项。

## Open Questions

（无——所有会影响 specs/方案/任务拆分的问题已在相位 B 拍板。）
