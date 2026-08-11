# Tasks · remove-superpowers-pipeline

R-ID 图例（与本 change specs/ delta 双向追溯）：

- **R1** = impl-orchestration《阶段三派发直连 sdflow-implement（唯一管线）》（ADDED）
- **R2** = impl-orchestration《出 ticket 模式产出 tracer-bullet ticket 并落盘即返回（tickets.md 单名）》（ADDED，取代同名旧需求）
- **R3** = impl-orchestration《执行模式宿主条件化受限并行工作 frontier 并以文件交接》（MODIFIED，交叉引用换名）
- **R4** = impl-orchestration《ticket 文件兼容 ship_gate 既有完成判据契约》（MODIFIED）
- **R5** = impl-orchestration《implementer dispatch 携带信号权威归属声明》（MODIFIED）
- **R6** = impl-orchestration REMOVED《管线路由为手动确定值，零模型自动判断》《试点回退与熔断哨兵》
- **R7** = spec-workflow《阶段三过设计门后连续自动跑到 merge（tickets 唯一管线）》（ADDED，取代同名旧需求）
- **R8** = spec-workflow《阶段三编排台账确定性（ship_gate）》（MODIFIED，计划文件名术语）
- **R9** = spec-workflow《失鲜判定 MUST 直接比较内容…》（MODIFIED，计划文件名术语）
- **R10** = spec-workflow REMOVED《impl-pipeline 缺省为 tickets》
- **R11** = yq-yaml-operations《R3/R5/R6》（REMOVED + 换名 ADDED，impl-pipeline Scenario 删除）〔spec-review-amendment〕

## 1. 路由切除（impl_route.py）

- [ ] 1.1 删除 `route` 子命令与全部路由函数（`_cmd_route` / route subparser / `read_config_pipeline` / `read_plan_marker` / `resolve_pipeline` / `LEGAL_PIPELINES` / `_PIPELINE_KEY_RE` / `RouteStop` / `_get_plan_sha`），文件头「管线路由三跳」注释改写为 tickets 调度 helper 自述；`_yq` 及仅为其服务的 import 一并删除（唯一调用点全在被删函数内），`test_yq_wrapper_consistency.py` 成员表去 impl_route 条目〔R1/R6；设计门 Q2 拍板，spec-review-amendment〕
- [ ] 1.2 `test_impl_route.py`：route/config/marker 参照系用例退役，frontier / task-text / 拓扑用例保留并全绿〔R1〕
- [ ] 1.3 核验保留半场接口逐字不变：`parse_blocked_by` / `TopoError` / `BLOCKED_BY_RE` 签名与行为零改动，gate sibling-import 回归绿（`test_gate_closing_ticket.py`）〔R3；`_yq` 随 Q2 拍板移入 1.1 删除集〕

## 2. gate 单名 resolver（ship_gate.py）

- [ ] 2.1 `PLAN_FILENAMES` 缩为 `("tickets.md",)`（resolver 函数形状保留）、删双存在判 UNKNOWN 分支、删旧名收尾票 grandfather 分支、RUN_PLAN reason / UNKNOWN 表 / 文件头注释的双名表述改单名；`PLAN_FILENAMES` 上方 :1329-1335「共享 resolver」说明注释块（引用 `impl_route.resolve_pipeline`）纳入改写；新增遗留旧名兜底：`tickets.md` 缺席 ∧ `superpowers-plan.md` 存在 ⇒ fail-closed 判 UNKNOWN + 人工清理提示〔R2/R7/R8；spec-review-amendment，Q1 拍板〕
- [ ] 2.2 测试同步：`test_plan_resolver.py` 旧名探测 / 双名 UNKNOWN / 改名迁移窗口用例退役；`test_superpowers_track_regression.py` 整文件删除；`test_harden_sdflow_spec_followup_closure.py` fixture 改名 `tickets.md`；gate 共享 fixture `approved_change` 默认写入名改 `tickets.md`，7 个消费文件（test_gate_git_layer / test_gate_freshness / test_gate_namespace / test_gate_impl_progress / test_gate_tail / test_gate_reviewed_sha / test_plan_resolver，63 处调用）逐一核验旧名语义依赖；`test_gate_closing_ticket.py` 的 `test_grandfather_old_name_without_closing_ticket_not_rejected`（:130）与 `test_plan_closing_ticket_check_grandfathers_old_name`（:160）退役；Q1 兜底分支配一条测试（遗留旧名单独存在 ⇒ UNKNOWN）〔R2；spec-review-amendment〕
- [ ] 2.3 完成判据窗口（`git log --diff-filter=A` 锚 `tickets.md`）与收尾票无条件校验回归：sdflow-ship 全测试套绿〔R2/R8〕

## 3. SKILL 文案收口

- [ ] 3.1 `sdflow-ship/SKILL.md`：链序 RUN_PLAN/CONTINUE_IMPL 改直连派发（删 route 调用、PIPELINE_RECEIPT、writing-plans 派发分支、marker 缺席回退 SDD 分支、「试验期权威声明」、完成摘要 `pipeline={…}` 槽位）〔R1〕
- [ ] 3.2 `sdflow-implement/SKILL.md`：删「缺省一律 superpowers」「双名分列」表述，聚合锚条件化 → 无条件，frontmatter marker 表述改「文件格式契约（无路由读取方）」〔R2/R4/R5〕
- [ ] 3.3 `sdflow-done/SKILL.md`：删 verify 轨道判定步（`read_plan_marker`/`resolve_pipeline` 引用）、「superpowers 轨判不适用」分支、grandfather 警示；「实现期聚合覆盖」锚无条件要求〔R2〕
- [ ] 3.4 三 SKILL 收口后全文 `grep -nE "superpowers|writing-plans|subagent-driven"` 逐条按 Success Metrics 合法残留清单分类处置——覆盖具名短语之外的残句（如 `sdflow-implement/SKILL.md`:158 旧管线比较句、description frontmatter 的 impl-pipeline 锚定文案）〔R1/R2；spec-review-amendment〕

## 4. bundle 资产与 config

- [ ] 4.1 删除 `sdflow-init/assets/workflow/prompts/step6-writing-plans.md`；守卫测试同步：`test_workflow_authority.py` 的 step6 断言退役、`test_workflow_split.py` / `test_checkpoint_slug_coverage.py` 名单去 step6 条目〔R1〕
- [ ] 4.2 六份 bundle 资产收口：`workflow.md` / `WORKFLOW-GUIDE.md` / `ff-generation-constraints.md`（切片建议条件恒真化 → 改无条件）/ `config.template.yaml`（键注释删）/ `snippets/claude-section.md`（唯一管线表述）/ `reference/quality-layering.md`（superpowers SDD 注入点 A/B 与「用 superpowers 跑实现时」清单节退役）〔R7〕
- [ ] 4.3 本仓 `openspec/config.yaml` 删 `impl-pipeline` 键 + 注释〔R10〕
- [ ] 4.4 `sdflow-init update` 刷本仓 CLAUDE.md / AGENTS.md 托管区块；`openspec/INDEX.md` 的 impl-orchestration 描述行（「手动路由三跳」）同步改单管线〔R7〕
- [ ] 4.5 `specs/yq-yaml-operations/spec.md` delta（评审补齐）随归档同步核验：R3/R5/R6 的 impl-pipeline Scenario 删除落主 spec；主 spec Purpose 脚本枚举去 `impl_route.py`（R12 惯例：Purpose 随 change 直接改主 spec）；`test_yq_wrapper_consistency.py` 成员表去 impl_route 条目（Q2 已拍板：`_yq` 随 route 半场删除）〔R11；spec-review-amendment〕

## 5. docs 与全仓扫尾

- [ ] 5.1 `docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md` 头部加 obsolete 标注（一行，指向 adr/0042）
- [ ] 5.2 grep 扫尾：`grep -rn "superpowers" --exclude-dir=archive --exclude-dir=.git` 在运行时路径（scripts / SKILL / bundle assets / specs 主文件）仅剩合法残留清单（upstream-watch 追踪目标、superpowers 插件非管线技能引用、docs 历史参考、adr 历史文本）——proposal《Success Metrics》判据
- [ ] 5.3 全仓测试绿：`/usr/bin/python3 -m pytest`（含保留半场、gate 回归、hack 守卫全量）；verify-report 对 Success Metrics 第三条（ship 直连 e2e）显式标注「事后锚——由下一真实 change 的 /sdflow-ship 首跑承接」，MUST NOT 留白或假绿〔spec-review-amendment〕
- [ ] 5.4 `CLAUDE.md`:215（托管区块外手写 prose）改写为不依赖 `impl-pipeline` 键存在性的表述（去「已开 impl-pipeline: tickets 的仓」前提）〔spec-review-amendment〕
- [ ] 5.5 现役视图文档同步：`docs/workflow-overview.md` / `docs/workflow-map.md`(+`.html`) / `docs/workflow-console.html` / `docs/criteria-mechanization-tracker.md` 去 superpowers 管线/writing-plans 阶段叙述〔R7；spec-review-amendment〕
- [ ] 5.6 `openspec/adr/0033-tickets-plan-filename-split-by-track.md` 头部加一行 `> **Superseded by [adr/0042](./0042-tickets-sole-impl-pipeline.md)**` 指针；`adr/0042` 加一句 supersede adr/0033 声明（互指，两文正文其余逐字不动）〔设计门 Q3 拍板，spec-review-amendment〕

## 测试覆盖图（TG-18：code path → 测试类型）

| code path | 测试类型 / 锚 |
|---|---|
| `impl_route.py` 保留半场（frontier / task-text / parse_blocked_by） | 单元：`test_impl_route.py` 保留用例 |
| `ship_gate.py` 单名 resolver + 收尾票无条件校验 | 单元：`test_plan_resolver.py` 保留用例 + `test_gate_closing_ticket.py` |
| gate sibling-import `parse_blocked_by` / `TopoError` | 单元：`test_gate_closing_ticket.py`（导入路径真跑） |
| 完成判据窗口（`tickets.md` 首提交锚） | 既有 gate 回归：`test_gate_impl_progress.py` / `test_gate_freshness.py` |
| bundle 名单守卫（step6 移除后） | `hack/tests/test_workflow_split.py` / `test_checkpoint_slug_coverage.py` |
| ship 链序直连（无路由调用） | e2e：下一真实 change 的 /sdflow-ship dogfood（事后锚，Success Metrics 第三条） |
