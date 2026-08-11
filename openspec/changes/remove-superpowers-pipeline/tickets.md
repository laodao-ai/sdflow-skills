---
impl-pipeline: tickets
---

## Global Constraints

逐字摘自 design.md 的硬约束与 Compliance 条款：

- `impl_route.py` 保留半场（`frontier` / `task-text` 子命令、`parse_blocked_by`、`_detect_cycle`、`next_ready`、`extract_task_text`、`TopoError`、`BLOCKED_BY_RE`）**接口与行为逐字不变**。
- **不改 gate 的完成判据窗口机制与 checkpoint 标签契约**（`TAG_RE` / `git log --diff-filter=A` / frontmatter 状态集判据均不动，本 change 只动计划文件的*定位*）。
- 遵守 bundle 单一权威源纪律（先改 assets 再 `sdflow-init update` 推送，禁只改下游）。
- 托管区块（CLAUDE.md/AGENTS.md 的 `sdflow:principles` 与 workflow 区块）不手改——经 `sdflow-init update` / `sync_principles.py` 机械刷新。
- 遵守基准 5：不新写任何计划文件解析；Blocked-by 拓扑继续复用 `parse_blocked_by` 单一源。
- 不卸载 superpowers 插件本身；不动 `sdflow-upstream-watch` 的 superpowers 追踪目标；不动 archive 历史件与既有 ADR 正文（例外：0033/0042 互指指针）。
- 测试退役参照系判定：assert 参照系 = 目标态已不存在的行为 ⇒ 退役。

### Task 1: 路由切除与保留半场回归

**Blocked-by:** none
**R-ID:** R1, R6

从 `sdflow-implement/scripts/impl_route.py` 切除全部路由函数与 `route` 子命令：删除 `_cmd_route` / route subparser / `read_config_pipeline` / `read_plan_marker` / `resolve_pipeline` / `LEGAL_PIPELINES` / `_PIPELINE_KEY_RE` / `RouteStop` / `_get_plan_sha`、`_yq` 及仅为其服务的 import；文件头注释从「管线路由三跳」改写为 tickets 调度 helper 自述。

同步测试：`test_impl_route.py` 的 route/config/marker 参照系用例退役（断言目标态已不存在的行为），frontier / task-text / 拓扑用例保留并全绿。`test_yq_wrapper_consistency.py` 成员表去 impl_route 条目（`_yq` 随路由删除退出消费面）。

核验保留半场接口逐字不变：`parse_blocked_by` / `TopoError` / `BLOCKED_BY_RE` 签名与行为零改动，gate sibling-import 回归绿（`test_gate_closing_ticket.py` 保留用例通过）。

- [x] `impl_route.py` 路由函数与 `route` 子命令已删除，文件头注释已改写
- [x] `_yq` 及仅为其服务的 import 已删除
- [x] `test_impl_route.py` 路由相关用例已退役，保留半场用例全绿
- [x] `test_yq_wrapper_consistency.py` 成员表已去 impl_route 条目
- [x] 保留半场接口（`parse_blocked_by` / `TopoError` / `BLOCKED_BY_RE`）签名与行为零改动
- [x] `test_gate_closing_ticket.py` 保留用例（gate sibling-import）通过

### Task 2: gate 单名 resolver 与测试同步

**Blocked-by:** 1
**R-ID:** R2, R7, R8

`ship_gate.py` 的 `PLAN_FILENAMES` 缩为 `("tickets.md",)`（保留 resolver 函数形状供 gate/测试共用）；删双存在判 UNKNOWN 分支与旧名收尾票 grandfather 分支；RUN_PLAN reason / UNKNOWN 表 / 文件头注释中的双名表述改单名；`PLAN_FILENAMES` 上方「共享 resolver」说明注释块（引用已删符号 `impl_route.resolve_pipeline`）改写。新增遗留旧名兜底：`tickets.md` 缺席 ∧ `superpowers-plan.md` 存在 ⇒ fail-closed 判 UNKNOWN + 人工清理提示（设计门 Q1 拍板）。

测试同步（63 处 fixture 迁移是本票主要工作量）：
- `test_plan_resolver.py`：旧名探测 / 双名 UNKNOWN / 改名迁移窗口用例退役；Q1 兜底分支配一条新测试（遗留旧名单独存在 ⇒ UNKNOWN）。
- `test_superpowers_track_regression.py`：整文件删除（存在意义即保护旧轨）。
- gate 共享 fixture `approved_change` 默认写入名改 `tickets.md`，7 个消费文件（test_gate_git_layer / test_gate_freshness / test_gate_namespace / test_gate_impl_progress / test_gate_tail / test_gate_reviewed_sha / test_plan_resolver）63 处调用逐一核验旧名语义依赖。
- `test_gate_closing_ticket.py` 的 `test_grandfather_old_name_without_closing_ticket_not_rejected`（:130）与 `test_plan_closing_ticket_check_grandfathers_old_name`（:160）退役。
- `test_harden_sdflow_spec_followup_closure.py` fixture 改名 `tickets.md`。
- 完成判据窗口（`git log --diff-filter=A` 锚 `tickets.md`）与收尾票无条件校验回归：sdflow-ship 全测试套绿。

- [x] `PLAN_FILENAMES` 已缩为单名，双存在 UNKNOWN / grandfather 分支已删
- [x] 遗留旧名兜底分支已新增并配测试
- [x] `test_plan_resolver.py` 旧名相关用例已退役
- [x] `test_superpowers_track_regression.py` 已整文件删除
- [x] 共享 fixture `approved_change` 默认写入名已改 `tickets.md`（7 文件 63 处核验）
- [x] `test_gate_closing_ticket.py` 两条 grandfather 用例已退役
- [x] sdflow-ship 全测试套绿（含完成判据窗口与收尾票校验回归）

### Task 3: SKILL 文案收口

**Blocked-by:** 1
**R-ID:** R1, R2, R4, R5

三份 SKILL.md 收口：

**sdflow-ship/SKILL.md**：链序 RUN_PLAN/CONTINUE_IMPL 段重写为直连派发（删 route 调用 / PIPELINE_RECEIPT / writing-plans 派发分支 / marker 缺席回退 SDD 分支 / 「试验期权威声明」）；完成摘要模板删 `pipeline={superpowers|tickets}` 槽位。

**sdflow-implement/SKILL.md**：删「缺省一律 superpowers」「双名分列」表述；聚合锚从条件化改无条件；frontmatter marker 表述改「文件格式契约（无路由读取方）」；description frontmatter（触发条件唯一权威文本）改「tickets 唯一管线，由 /sdflow-ship 按 gate 判定以显式 mode= 参数派发」。

**sdflow-done/SKILL.md**：删 verify 轨道判定步（`read_plan_marker`/`resolve_pipeline` 引用）、「superpowers 轨判不适用」分支、grandfather 警示；「实现期聚合覆盖」锚改无条件要求。

收口后全文 `grep -nE "superpowers|writing-plans|subagent-driven"` 逐条按 Success Metrics 合法残留清单分类处置——覆盖具名短语之外的残句。

- [x] `sdflow-ship/SKILL.md` 链序段已重写为直连派发，完成摘要已删管线槽位
- [x] `sdflow-implement/SKILL.md` 双轨表述已收口，description 已更新
- [x] `sdflow-done/SKILL.md` 轨道判定步与条件化分支已删除
- [x] 三 SKILL 的 superpowers/writing-plans/subagent-driven grep 仅剩合法残留

### Task 4: bundle 资产与 config 收口

**Blocked-by:** 2,3
**R-ID:** R7, R10, R11

**step6 删除**：删除 `sdflow-init/assets/workflow/prompts/step6-writing-plans.md`（唯一运行时消费者即被删 ship 分支）。守卫测试同步：`test_workflow_authority.py` 的 step6 断言退役；`test_workflow_split.py` / `test_checkpoint_slug_coverage.py` 名单去 step6 条目。

**六份 bundle 资产收口**：`workflow.md`（子步骤 A、显式 superpowers 段、检查清单行）/ `WORKFLOW-GUIDE.md`（同上）/ `ff-generation-constraints.md`（切片建议条件恒真化 → 改无条件）/ `config.template.yaml`（键注释删）/ `snippets/claude-section.md`（「缺省 tickets / 显式 superpowers」→「唯一管线」表述）/ `reference/quality-layering.md`（superpowers SDD 注入点 A/B 与「用 superpowers 跑实现时」清单节退役）。

**config 键退役**：本仓 `openspec/config.yaml` 删 `impl-pipeline` 键 + 注释。

**托管区块刷新**：`sdflow-init update` 刷本仓 CLAUDE.md / AGENTS.md 托管区块。

**INDEX 同步**：`openspec/INDEX.md` 的 impl-orchestration 描述行（「手动路由三跳」）改单管线表述。

**specs delta**：`specs/yq-yaml-operations/spec.md` delta——R3/R5/R6 的 impl-pipeline Scenario 删除落主 spec；主 spec Purpose 脚本枚举去 `impl_route.py`；`test_yq_wrapper_consistency.py` 成员表核验（Task 1 已完成去条目）。

- [x] `step6-writing-plans.md` 已删除，三份守卫测试名单已同步
- [x] 六份 bundle 资产 superpowers 叙述已收口
- [x] 本仓 `openspec/config.yaml` 的 `impl-pipeline` 键已删除
- [x] `sdflow-init update` 已执行，CLAUDE.md / AGENTS.md 托管区块已刷新
- [x] `openspec/INDEX.md` 描述行已更新
- [x] yq-yaml-operations delta spec 已同步

### Task 5: docs 与全仓扫尾

**Blocked-by:** 1,2,3,4
**R-ID:** R7

**docs 收口**：`docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md` 头部加 obsolete 标注（一行，指向 adr/0042）。现役视图文档同步：`docs/workflow-overview.md` / `docs/workflow-map.md`(+`.html`) / `docs/workflow-console.html` / `docs/criteria-mechanization-tracker.md` 去 superpowers 管线/writing-plans 阶段叙述。

**ADR 互指**：`adr/0033` 头部加一行 `> **Superseded by [adr/0042](./0042-tickets-sole-impl-pipeline.md)**` 指针；`adr/0042` 加一句 supersede adr/0033 声明（互指，两文正文其余逐字不动）。

**CLAUDE.md 手写段修正**：`CLAUDE.md`:215（托管区块外手写 prose）改写为不依赖 `impl-pipeline` 键存在性的表述。

**grep 扫尾**：`grep -rn "superpowers" --exclude-dir=archive --exclude-dir=.git` 在运行时路径（scripts / SKILL / bundle assets / specs 主文件）仅剩合法残留清单（upstream-watch 追踪目标、superpowers 插件非管线技能引用、docs 历史参考、adr 历史文本）——Success Metrics 判据。

**全仓 pytest**：`/usr/bin/python3 -m pytest` 全绿（含保留半场、gate 回归、hack 守卫全量）；verify-report 对 Success Metrics 第三条（ship 直连 e2e）显式标注「事后锚——由下一真实 change 的 /sdflow-ship 首跑承接」，MUST NOT 留白或假绿。

- [x] `impl-pipeline-matt-vs-superpowers.md` 头部已加 obsolete 标注
- [x] 现役视图文档已去 superpowers 管线叙述
- [x] ADR 0033/0042 已互加指针
- [x] `CLAUDE.md`:215 手写段已修正
- [x] grep 扫尾判据通过（运行时路径仅剩合法残留）
- [x] [e2e] 全仓 `/usr/bin/python3 -m pytest` 全绿

### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4,5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落 `impl-reports/task6-verify.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [x] 单元测试证据齐全并通过
- [x] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [x] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
