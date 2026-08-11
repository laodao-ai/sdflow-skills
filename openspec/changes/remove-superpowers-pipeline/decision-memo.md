---
schema_version: 1
change: remove-superpowers-pipeline
branch: feat/remove-superpowers-pipeline
generated_at: 2026-08-11T22:11:38+08:00
decision_hash: 4fc3399eeffe
---

# 决策纪要 · remove-superpowers-pipeline

## 目标态

tickets 是唯一实现管线：superpowers 路由分支（config 键 → marker → writing-plans/subagent-dev）及其全部支撑设施（route 子命令、双名 resolver、grandfather、step6 prompt、双轨 specs/文案）删除，ship 链序直连 `sdflow-implement`（T277，用户 2026-08-11 拍板）。

## 拍板决策

- **D1 深收口**（用户 2026-08-11 拍板「同意 深收口，go」）：superpowers 管线路由整体删除，tickets 成唯一实现管线；ship 链序 RUN_PLAN/CONTINUE_IMPL 直连 `sdflow-implement mode=tickets-plan|tickets-exec`（不再经 route helper，PIPELINE_RECEIPT 随之退役）；config `impl-pipeline` 键退役；gate resolver 缩单名。**砍掉的候选**：浅收口（保留单值路由器）——单路路由器纯开销、三跳空转，且必然留二次清理碎片，违背「一个 change = 一个完整阶段结果」。
- **D2 impl_route.py 切除而非整删**（用户 2026-08-11 确认）：删 route 子命令 + 全部路由函数（`read_config_pipeline` / `read_plan_marker` / `resolve_pipeline` / `LEGAL_PIPELINES` / `_PIPELINE_KEY_RE` / `RouteStop` / `_get_plan_sha` / PIPELINE_RECEIPT）；保留 `frontier` / `task-text` 子命令与 `parse_blocked_by` / `TopoError` / `BLOCKED_BY_RE` / `_yq`（tickets 基础设施 + gate sibling-import 单一源，见 C3）；**文件名不改**（改名要动 10+ 处纯机械引用，收益趋零，通则④；名字略偏判可接受边角）。**砍掉的候选**：整文件删——查实后否决，会打断 tickets 轨自身的 frontier 调度与 gate 收尾票校验（C3）；顺手改名 `tickets_frontier.py`——不加宽。
- **D3 marker 保留**：`tickets.md` frontmatter 的 `impl-pipeline: tickets` 单键作为文件格式契约保留（见 C6），本 change 不动出票模板与 gate 幻影任务防护语境。**砍掉的候选**：连 marker 一起删——要动出票模板 + gate frontmatter 处理，收益趋零。
- **D4 docs 处置**：`docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md` 头部加一行「结论已执行：superpowers 管线已移除（remove-superpowers-pipeline）」的 obsolete 标注；`superpowers-subagent-dev.md` / `superpowers-writing-plans.md` 保留不动（上游第三方 skill 参考笔记，superpowers 仍是 upstream-watch 追踪目标）。
- **D5 ADR 已落**（用户 2026-08-11 确认）：`openspec/adr/0042-tickets-sole-impl-pipeline.md`——记录移除决策、三分肢切除边界、adr/0033 双名语境成为历史（0033 本文不改）。
- **Non-goals**：不卸载 superpowers 插件本身（brainstorming/TDD 等继续用）；不动 `sdflow-upstream-watch` 的 superpowers 追踪目标；不动 archive 历史件与既有 ADR 文本；不动 `openspec/CONTEXT.md`（:40 合规边界属插件通用条款、:188 tickets 定义与目标态一致，已核无冲突）。

## 承重约束

- **C1 在途 superpowers 轨 change 为零**——删除无迁移保护对象。
  验证方式：CLI 实跑；**证据锚**：`openspec list` → "No active changes"；`ls openspec/changes/` 仅 `archive/`（2026-08-11）。
- **C2 本机全部下游消费仓无显式 `impl-pipeline: superpowers` 键**——键退役不破坏任何已知消费方。
  验证方式：find+grep 5 个仓的 `openspec/config.yaml`；**证据锚**：01-laodao / 05-sarvelo / 10-michi / 11-michi-kb-build 无键；本仓 `tickets`（2026-08-11 实跑输出）。
- **C3 impl_route.py 三分肢，MUST NOT 整文件删**：
  - route 半场（`route` 子命令 / `read_config_pipeline` / `read_plan_marker` / `resolve_pipeline` / `LEGAL_PIPELINES` / `_PIPELINE_KEY_RE` / `RouteStop` / `_get_plan_sha` / PIPELINE_RECEIPT）仅服务管线路由，随 superpowers 死。**证据锚**：`RouteStop` 仅 route 路径 raise/捕获（impl_route.py:224-271,534）；`_get_plan_sha` 仅 `_cmd_route` 调（impl_route.py:566）。
  - `frontier` / `task-text` 子命令 + `parse_blocked_by` / `_detect_cycle` / `next_ready` / `extract_task_text` / `TopoError` / `BLOCKED_BY_RE` / `_yq` 是 tickets 轨自身基础设施，保留。**证据锚**：sdflow-implement/SKILL.md:241,244,470,492,530 消费 frontier/task-text。
  - `ship_gate.py` sibling-import `parse_blocked_by` / `TopoError`（收尾票 Blocked-by 校验单一源，基准 5）——文件与该接口 MUST 存续。**证据锚**：ship_gate.py:1576-1591。
- **C4 gate 路由零依赖成立，单名化不触路由语义**：ship_gate 不读 config（**证据锚**：specs/impl-orchestration/spec.md:8 明文；grep 证实 gate 的 frontmatter 处理全是 ship-gate 报告字段、无 impl-pipeline 读点）。`PLAN_FILENAMES` 双名探测（ship_gate.py:1342）、双存在判 UNKNOWN、旧名收尾票 grandfather（ship_gate.py:1542-1602）均为纯定位层，缩单名 `tickets.md` 不影响完成判据窗口机制（`git log --diff-filter=A -- <plan路径>` 与名字无关）。「在途 plan MUST NOT 重命名」约束与轨道无关、继续有效。
- **C5 step6-writing-plans.md 唯一运行时消费者 = ship SKILL 的 superpowers 派发分支**（sdflow-ship/SKILL.md:170）——整文件可删。其余引用均为守卫测试（test_workflow_authority.py 的 TAG_RE 契约样例断言、test_workflow_split.py 名单、test_checkpoint_slug_coverage.py:126 覆盖名单）与 adr/0033 历史文本，测试随文件同步退役/改名单。**证据锚**：grep -rl step6-writing-plans（2026-08-11 实跑）。
- **C6 tickets.md frontmatter `impl-pipeline: tickets` 单键保留**（惰性文件格式契约）：删除要动出票模板 + gate 幻影任务防护语境（F5），收益趋零——通则④可留边角。
- **C7 测试退役参照系判定**（按「assert 参照系 = 目标态已不存在的行为 ⇒ 退役」）：
  - `test_superpowers_track_regression.py`（107 行）整文件退役——存在意义即保护旧轨（其 docstring 自述）。
  - `test_impl_route.py` route/config/marker 相关用例退役，frontier/task-text/topo 用例保留。
  - `test_plan_resolver.py` 旧名探测（:50-57）、双名 UNKNOWN（:107-120）、改名迁移窗口（:217-243）用例退役；单名定位用例保留。
  - `test_harden_sdflow_spec_followup_closure.py` fixture 的 `superpowers-plan.md`（:38）改名 `tickets.md`（测试目的与轨道无关，仅换 fixture 名）。
  - `test_yq_wrapper_consistency.py` 的 impl_route.py 条目保留（`_yq` 仍在文件中）。
- **C8 specs 修改走 delta specs**，两个能力大改：`impl-orchestration`（路由三跳 Requirement → 单管线直连、文件名分列 Requirement → 单名、收尾票 grandfather 删、聚合锚无条件化、全部 superpowers Scenario 删、试验期外衣文件名 Requirement〔:144〕随本 change 收口）+ `spec-workflow`（阶段三双轨表述 → 单轨、完成判据窗口例名 `superpowers-plan.md` → `tickets.md`〔机制不变〕、「impl-pipeline 缺省为 tickets」Requirement〔:1676〕退役）。
- **C9 bundle 资产改动须回灌权威源再推下游**：`workflow.md` / `WORKFLOW-GUIDE.md` / `ff-generation-constraints.md`（切片建议条件恒真化 → 改无条件）/ `config.template.yaml`（键注释删）/ `snippets/claude-section.md`（缺省表述 → 唯一管线）/ `reference/quality-layering.md`（superpowers SDD 注入点 A/B 与「用 superpowers 跑实现时」检查清单节退役）。改后 `sdflow-init update` 刷本仓托管区块；下游仓待各自下次 update（无键 ⇒ 窗口期行为不变，缺省本就 tickets）。
- **C10 显式旧值无处置分支**：键整体退役 ⇒ 不存在「显式 superpowers 如何处置」问题；存量键（本机为零）成无读取方的惰性键。本仓 `openspec/config.yaml` 的键 + 注释（:60-64）删除。

## 接受的边角

- **impl_route.py 名字略偏**（route 死后文件仍叫 impl_route）——概率必然/影响极小（读者困惑一次，docstring 说明即可）/改名成本 10+ 处机械引用；**为何接受**：通则④，纯命名纯度收益不抵改动面。
- **change 目录名 remove-superpowers-pipeline 含"删文件"初案色彩**——实际是切除路由半场；**为何接受**：openspec 无 rename change 命令，名字仍准确描述目标（管线移除），非误导。
- **下游仓 update 窗口期 bundle 双态**——某下游仓在本 change 合并后、update 前，文案仍写双轨；**为何接受**：无键 ⇒ 行为缺省本就 tickets，双态只存在于人读文案层，无行为分叉。

## 三镜代价

（TG-23 命中：深收口 vs 浅收口）**系统镜**：深收口改动面大（路由脚本/gate/3 SKILL/6 bundle 资产/2 specs/测试群）但删的全是死支，回退 = revert + 下游 update，可控；浅收口留三跳空转 + 必然的二次 change。**用户镜**：无可感知行为变化（缺省本就 tickets、无人显式用旧值）；唯一变化是文案不再出现双轨叙述，读者心智负担下降。**开发循环镜**：深收口一次做完，此后 ship 链序少一次 helper 调用、少一个 receipt 概念、评审少一类"双轨条件化"分支要核。**主次判定**：开发循环镜为主——本 change 的全部收益都落在流程与心智负担减负，系统镜的改动面成本一次性支付。
