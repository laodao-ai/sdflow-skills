# hand-off — rebuild-sdflow-roadmap-v2（2026-07-11）

## ✅ 完成了什么（锚点已复核，非搬运 verify）

- **sdflow-roadmap 四件套→三件套主体重写**（SKILL.md 430→489 行）：三件套直写 `openspec/roadmaps/{name}/`、去 `plan-{topic}` change 壳、收尾 checklist 五项软门（含引用图锚点句式/frontier 全目录扫描+越权留痕/CONTEXT-adr 基线核对）、存量四件套兼容模式 + requirements.md 逃生舱 + create/continue/replan 生命周期（含启发式判据）。锚：verify-report 逐条（readlink 双宿主即时生效；「四件套」roadmap 语境全仓 156 命中七档处置清零活残留）。
- **讨论层三分支分档**：双判据（起手显性信号/事中触发，禁轮数预估）+ office-hours 第三分支（Q-D，含 gate-0 野心信号补检/回流再判/双信号优先级/职权边界）+ 压缩前 flush + 无雾自降级 + 宿主中立探测 + tracker doc preflight + grilling 未装/套件漂移降级 + 路由对照表 6 例。
- **footage 约定**：命名权先定（字面量调用语）、map 持久字段（Tracker root/Effort kind）、顶部路标行、再入约定（单 map 分批/30 票归档 map-N+closed 标记+归档前未决票核对）、票状态机 `open→claimed→resolved|abandoned`（SKILL↔tracker doc 逐字一致）、规则 3 两段式（footage/ 与包根 memo.md 均不被三件套引用）。
- **模板层**：删 requirements-template；design-template「需求与目标态」无编号头部章（伸缩判据+具名占位兜底）；roadmap-template 近细远雾（附录仅近期、回指锚点注释）；task-log-template（Review 处置骨架+`> 状态：ACTIVE|review-waived|未审待恢复`+阶段 0 例外+产出清单去 memo）；memo-template（短档可选+压缩 flush+无 wayfinder 长档降级例外）；long-flow 轮数表废弃标注。实施 change 命名统一 `-p<N>`（回填解析器 `PREFIX_RE` 契约，phase-N 会 NO_ASSOCIATION——code-voice 抓获，全仓活示例清零含 verify M-1 后记）。
- **消费仓约定双锚**：tracker doc Wayfinding 条件分流（`<root>`）+ 持久字段 + stale claim 重认领 + 边界三条（footage 不进 triage/误落票不贴五态）；CLAUDE.md 块内锚句 + 块外 :79 段结构性第二锚。
- **4.1 wayfinding 最小实测**：真实 `/sdflow-roadmap` 调用起步，六操作+中断恢复+字段派生路径全过、共享真相源零污染——proposal 假设 1 消解。锚：impl-notes §4.1 判定表。
- **代码审**：6 源 29 canonical → 24 修复（12 高，含 5 项「design 承诺了但指令没落」落地缺口与 8 项模板↔SKILL 契约矛盾）。锚：code-review-report + commit 418afb3。

## ⏳ 未完成 / 延后

- **批次 `rebuild-sdflow-roadmap-v2`**（见 `openspec/issues/batches.md` / INDEX，sweep 已圈 3 项）：
  - **T129**：存量 wco/mlh 两包迁移（tasks 5.1-5.3 受控延后——Q-C 前置②「首个新流程 roadmap 走通端到端」未满足；前置核验与操作序列指针见 impl-notes §5.1-5.3；触发条件 = 首个新流程 roadmap SHIPPED 且目标包无在飞 change）。
  - **T130**：ff-generation-constraints.md:43 边界句「四件套」→「三件套」一词同步（assets 权威源，本 change Compliance 零 assets 改动故未扫）。
  - **T131**：workflow.md 阶段一 wayfinder 探测 Claude 单宿主硬编码 → 宿主中立口径（assets，同上）。
- verify Minor：M-1 已在收尾 fold 修复（见 verify-report 后记），零遗留。
- spec delta 两处笔误（「旧 §5」实为 §6、「:265」实为 :272）——archive 子代理按码订正主 specs（code-review F25 指令锚）。

## ▶ 下一阶段建议

1. **首个新流程 roadmap**：下次真实规划需求直接走新 SKILL 全流程（讨论分档→结晶三件套→分档 review→五项 checklist）——走通即解锁 T129 迁移（建议紧随其后执行，一并清 T130/T131 组一个 assets 小批次）。
2. **与 matt-workflow-integration 的协同面已闭合**：三段分流（mainflow）与三分支（roadmap 讨论层）判据同源 F11、职权边界已双向声明（code-review X2/F21 裁决）；office-hours 仅 roadmap 层用。
3. Roadmap 回填：exit 3（本 change 非 roadmap 驱动，正确退现状）。
