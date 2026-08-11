# tickets 成唯一实现管线（superpowers 路由退役）

> Supersedes [adr/0033](./0033-tickets-plan-filename-split-by-track.md)（两轨计划文件名分列，双名语境随本决策成为历史）。

阶段三实现管线的 superpowers 旧轨（`writing-plans → subagent-driven-development`）整体删除，tickets 成唯一管线（用户 2026-08-11 拍板「以后只走 tickets」，T277）：`impl_route.py` 的 `route` 子命令与全部路由函数（config 键读取 / plan marker 路由 / `resolve_pipeline` / PIPELINE_RECEIPT）切除，ship 链序 RUN_PLAN/CONTINUE_IMPL 直连 `sdflow-implement mode=tickets-plan|tickets-exec`；`openspec/config.yaml` 的 `impl-pipeline` 键退役（存量键成无读取方的惰性键）；ship_gate 计划文件 resolver 缩为单名 `tickets.md`（双名探测 / 双存在判 UNKNOWN / 旧名收尾票 grandfather 一并删除）；`workflow/prompts/step6-writing-plans.md` 整文件删除。删除时机的前置条件已验证：在途 superpowers 轨 change 为零、本机全部下游消费仓无显式 `impl-pipeline: superpowers` 键。

**adr/0033（两轨计划文件名分列）的双名语境随本决策成为历史**——单名态下不存在「按轨分列」；0033 本文不改（历史记录照旧），其存活遗产是「在途 plan MUST NOT 重命名」（完成判据窗口锚 `git log --diff-filter=A -- <plan路径>` 不跟随重命名，此约束与轨道无关、继续有效）。adr/0017/0032 的双轨措辞同理按历史语境读。

演进链：matt-workflow-integration（tickets 管线以 `superpowers-plan.md` 外衣试点）→ adr/0033（文件名按轨分列）→ simplify-workflow（缺省从 superpowers 翻转为 tickets，superpowers 降为显式声明保留）→ 本决策（显式声明路径亦删，单管线收口）。

## Considered Options

- **深收口（选中）**：路由整体删除，单管线直连。单路路由器是纯开销（无信号可路由，违背机械化基准——路由三跳全在空转）；浅收口必然留一个二次清理碎片，违背「一个 change = 一个完整阶段结果」。代价：改动面大（路由脚本 / gate / 3 个 SKILL / 6 份 bundle 资产 / 2 个 specs / 测试群 / 托管区块），一次做完。
- **浅收口（保留单值路由器）**：`LEGAL_PIPELINES` 缩单值、marker 缺省翻转，改动小；但 PIPELINE_RECEIPT、config 键、marker 三跳继续空转，且「删除旧管线」目标只完成一半。
- **impl_route.py 整文件删**：探索期初案，查实后否决——该文件三分肢，`frontier` / `task-text` 子命令是 tickets 执行模式的调度基础设施，`parse_blocked_by` / `TopoError` 是 ship_gate 收尾票校验 sibling-import 的单一源（基准 5：拓扑解析不重写第二份）；整删当场打断 tickets 轨自身。修正为「切除路由半场、保留 tickets 基础设施、文件名不改」（改名需动 10+ 处纯机械引用，收益趋零）。

## Consequences

- `sdflow-ship` SKILL 链序 RUN_PLAN/CONTINUE_IMPL 不再调 route helper，按 gate verdict 直接以模式派发契约字面串派发 `sdflow-implement`；`pipeline=superpowers → writing-plans` 派发分支、marker 缺席回退 SDD 分支、PIPELINE_RECEIPT 均删除。
- `impl_route.py` 保留 `frontier` / `task-text` 子命令与 `parse_blocked_by` / `TopoError` / `BLOCKED_BY_RE` / `_yq`；`RouteStop` / `_get_plan_sha` 随 route 死。文件名保留（略偏的名字判为可接受边角）。
- `tickets.md` frontmatter 的 `impl-pipeline: tickets` 单键作为惰性文件格式契约保留——出票模板与 gate 幻影任务防护语境不动，本 change 不改文件格式。
- specs 收口：`impl-orchestration`（路由三跳 → 单管线直连、文件名分列 → 单名、收尾票 grandfather 删、聚合锚无条件化）+ `spec-workflow`（双轨 → 单轨、「impl-pipeline 缺省为 tickets」Requirement 退役）。
- bundle 资产（workflow.md / WORKFLOW-GUIDE / ff-generation-constraints / config.template / claude-section / quality-layering 的 superpowers SDD 节）改权威源后经 `sdflow-init update` 推送；下游仓在各自下次 update 前行为不变（缺省本就 tickets）。
- 测试面：`test_superpowers_track_regression.py` 整文件退役（参照系 = 目标态已不存在的行为）；`test_impl_route.py` route 半场用例、`test_plan_resolver.py` 双名/迁移窗口用例退役；frontier / task-text / 单名定位用例保留。
- superpowers 插件本身（brainstorming / TDD / systematic-debugging 等）与 `sdflow-upstream-watch` 的 superpowers 追踪目标均不受影响。回退 = revert 本 change 并在各消费仓重跑 `sdflow-init update`（方向性成本高，不设计快捷回退）。
