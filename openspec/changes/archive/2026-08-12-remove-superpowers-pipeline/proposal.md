# Proposal · remove-superpowers-pipeline

## Why

用户已拍板「以后只走 tickets」（T277，2026-08-11）：`impl-pipeline: superpowers` 旧管线（writing-plans → subagent-driven-development）自 simplify-workflow 缺省翻转后仅作显式声明保留，而本机所有消费仓无一显式使用、在途旧轨 change 为零——路由三跳（config 键 → plan marker → 缺省）已全程空转，每轮 ship 链序多一次 helper 调用、每轮评审多一类「双轨条件化」分支要核，文案双轨叙述持续加重读者心智负担。删除时机成熟（无迁移保护对象），一次收口。

## What Changes

- **BREAKING** 删除 superpowers 实现管线路由：`impl_route.py` 切除 `route` 子命令与全部路由函数（`read_config_pipeline` / `read_plan_marker` / `resolve_pipeline` / `LEGAL_PIPELINES` / `RouteStop` / `_get_plan_sha` / PIPELINE_RECEIPT，及 `_yq`——其唯一调用点全在被删路由函数内，设计门 Q2 拍板随删、`test_yq_wrapper_consistency.py` 成员表同步〔spec-review-amendment〕）；保留 `frontier` / `task-text` 子命令与 `parse_blocked_by` / `TopoError` / `BLOCKED_BY_RE`（tickets 基础设施 + ship_gate sibling-import 单一源），文件名不改（memo D2）。
- **BREAKING** ship 链序直连：RUN_PLAN → `sdflow-implement mode=tickets-plan`、CONTINUE_IMPL → `mode=tickets-exec done_tasks=…`，不再经 route helper；`pipeline=superpowers → writing-plans` 派发分支、marker 缺席回退 SDD 分支删除。
- **BREAKING** `openspec/config.yaml` 的 `impl-pipeline` 键退役：本仓键 + 注释删除，`config.template.yaml` 键注释删除；存量键成无读取方的惰性键（本机下游为零，memo C2/C10）。
- ship_gate 计划文件 resolver 缩单名 `tickets.md`：双名探测、双存在判 UNKNOWN、旧名收尾票 grandfather 删除；完成判据窗口机制（`git log --diff-filter=A`）不变（memo C4）。新增遗留旧名兜底〔设计门 Q1 拍板，spec-review-amendment〕：`tickets.md` 缺席 ∧ `superpowers-plan.md` 存在 ⇒ fail-closed 判 UNKNOWN + 人工清理提示（防历史残留文件被静默忽略后重复出票）。
- 删除 `sdflow-init/assets/workflow/prompts/step6-writing-plans.md`（唯一运行时消费者即被删分支，memo C5）。
- SKILL 文案收口：`sdflow-ship`（链序段）、`sdflow-implement`（「缺省一律 superpowers」、聚合锚条件化、双名分列引述）、`sdflow-done`（verify 的「superpowers 轨判不适用」分支与 grandfather 警示）。
- bundle 资产收口并推下游：`workflow.md` / `WORKFLOW-GUIDE.md` / `ff-generation-constraints.md`（切片建议条件恒真化 → 无条件）/ `snippets/claude-section.md` / `reference/quality-layering.md`（superpowers SDD 注入点 A/B 与相关检查清单节退役）；改后 `sdflow-init update` 刷本仓托管区块（CLAUDE.md / AGENTS.md）。
- 测试面：`test_superpowers_track_regression.py` 整文件退役；`test_impl_route.py` route 半场用例、`test_plan_resolver.py` 旧名/双名/迁移窗口用例退役；`test_harden_sdflow_spec_followup_closure.py` fixture 改名；`test_workflow_authority.py` / `test_workflow_split.py` / `test_checkpoint_slug_coverage.py` 的 step6 条目退役/改名单（memo C7）；gate 共享 fixture `approved_change` 默认写入名迁 `tickets.md`（7 个 gate 测试文件 63 处消费点逐一核验）、`test_gate_closing_ticket.py` 两条 grandfather 用例（:130/:160）退役〔spec-review-amendment〕。
- docs：`impl-pipeline-matt-vs-superpowers.md` 头部加 obsolete 标注；README「Skills 列表」不受影响（无 skill 增删）。
- 已落 `adr/0042-tickets-sole-impl-pipeline.md`（memo D5，随 B 收敛 checkpoint 入库）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `impl-orchestration`：管线路由 Requirement 退役（REMOVED，由新增「阶段三派发直连 sdflow-implement（唯一管线）」承接）；「试点回退与熔断哨兵」Requirement 退役（config 回退通道随键退役消失）；出 ticket Requirement 换名重立为「…（tickets.md 单名）」（删双名/superpowers 轨 Scenario——CLI 的 MODIFIED 禁删 Scenario，走 REMOVED + 换名 ADDED）；「执行模式…」「ticket 文件兼容…」「implementer dispatch…」MODIFIED（单名/无条件化/交叉引用换名）。
- `spec-workflow`：阶段三 Requirement 换名重立为「…（tickets 唯一管线）」（同上原因，双轨路由/双名定位 Scenario 删除）；「阶段三编排台账确定性」「失鲜判定…」MODIFIED（完成判据窗口与 Scenario 例名 `superpowers-plan.md` → `tickets.md`，机制不变）；「impl-pipeline 缺省为 tickets」Requirement 退役。
- `yq-yaml-operations`〔spec-review-amendment〕：R3/R5/R6 各删一个 impl-pipeline 读取/非法值 Scenario（`impl_route.py` 随 route 半场退出 YAML 读取面），走 REMOVED + 换名 ADDED（MODIFIED 禁删 Scenario）；主 spec Purpose 的脚本枚举随 change 直接订正（R12 既有惯例）。

## Impact

- **代码**：`sdflow-implement/scripts/impl_route.py`（切除 route 半场）、`sdflow-ship/scripts/ship_gate.py`（单名 resolver + grandfather 删除）及两者测试群。
- **SKILL**：`sdflow-ship` / `sdflow-implement` / `sdflow-done` 三处文案。
- **bundle（推下游）**：6 份资产（workflow.md / WORKFLOW-GUIDE / ff-generation-constraints / config.template / claude-section / quality-layering）+ step6 prompt 删除；下游仓在各自下次 `sdflow-init update` 前文案双态但**行为不变**（缺省本就 tickets，无仓显式设旧值）。
- **specs**：`impl-orchestration` / `spec-workflow` / `yq-yaml-operations`〔spec-review-amendment〕三能力 delta。
- **不受影响**：superpowers 插件本身（brainstorming/TDD 等照用）、`sdflow-upstream-watch` 的 superpowers 追踪目标、archive 历史件、既有 ADR 文本、`tickets.md` frontmatter marker 文件格式（memo D3）。
- 技术栈：Markdown + Python 脚本，不命中 TG-01/02/03 领域清单。

## Success Metrics

- 全仓 pytest 绿（route 半场用例退役后，frontier / task-text / 单名定位 / gate 全量回归通过）。
- `grep -rn "superpowers" --exclude-dir=archive --exclude-dir=.git` 在运行时路径（scripts/SKILL/bundle assets/specs）仅剩合法残留：upstream-watch 追踪目标、superpowers 插件技能引用（brainstorming 等）、docs 历史参考、adr 历史文本。
- ship 链序端到端（下一个真实 change 的 RUN_PLAN → CONTINUE_IMPL → SHIPPED）不经任何路由调用直连成功。
- 现役视图文档（`docs/workflow-overview.md` / `docs/workflow-map.md`+`.html` / `docs/workflow-console.html` / `docs/criteria-mechanization-tracker.md`）不再含 superpowers 管线/writing-plans 阶段叙述〔spec-review-amendment〕。

## Non-Goals

- 不卸载 superpowers 插件、不动其任何非管线技能的使用。
- 不动 `sdflow-upstream-watch` 的 superpowers 上游追踪。
- 不改 `tickets.md` 文件格式（frontmatter marker 保留为惰性契约）。
- 不改 archive 历史件与既有 ADR 正文（例外〔设计门 Q3 拍板，spec-review-amendment〕：`adr/0033` 头部加一行 Superseded-by 指针指向 `adr/0042`、`adr/0042` 加一句 supersede 声明，两侧互指——对齐 adr/0002→0040 既有惯例，正文其余逐字不动）。
- 不重命名 `impl_route.py`。

## 需求优先级

- **P0**：路由切除 + ship 直连 + gate 单名 resolver + 测试面同步（行为收口的完整性，缺一即双态混跑风险）。
- **P1**：specs delta + 三 SKILL 文案 + bundle 资产回灌与托管区块刷新（文案与规范一致性）。
- **P2**：docs obsolete 标注。

## 利益相关方与外部依赖

- **下游消费仓**（本机 4 个 + 可能存在的其他机器 checkout）：行为无变化（无仓显式设旧值、缺省本就 tickets）；文案层在各自下次 `sdflow-init update` 时收敛。
- **运行 checkout**（`~/.skills/sdflow-skills`）：合并后按发布纪律 pull + `setup.sh`。
- 无外部计费服务、无第三方 API 依赖变化（TG-24 不命中）。

## 假设

- **「本机之外的机器无下游仓显式设 `impl-pipeline: superpowers`」未验证**（memo C2 只扫了本机）。失效影响：该仓的键成惰性键、行为落到缺省 tickets——**与显式声明意图一致的概率极低但后果可见**（该仓若真想走旧管线，旧管线已不存在，ship 直连 tickets 并在 plan 缺失时走 RUN_PLAN 出票，无静默混跑）；处置 = 键退役本身使任何取值都无行为差异，故该假设失效不产生错误路由，仅需人工知悉。

## Compliance

N/A（无合规约束命中：无用户数据、无外部服务、无许可证变更）。
