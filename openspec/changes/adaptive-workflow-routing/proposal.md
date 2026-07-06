# Proposal — adaptive-workflow-routing

## Why

现 workflow 对每个 change 一律付全额固定成本（grill + spec-review 多镜 + superpowers + code-review 多镜 + done），即使平凡 change 也如此。结果是**把「合批摊薄」逼成反模式**——本轮就差点为省 loop 成本 fold G1+G2（被 fold-vs-defer AND 门拦下）。真正的解不是合批，是**让单 change 成本随复杂度/清晰度自适应**：平凡 change 便宜到可以随便开，拆分就不再亏。

现设计「深度由触发决定，不分 S/M/L」是对的地基，但它**只单向升级、从不放行轻量化**。本 change 补上向下路由这一半，并配一个后向校准环防止「自评滥用换皮」。

## What Changes

- **HR-TG 双向化**：复用 `trigger-catalog.md §7` 现有 HR-TG 子集（单一源），把它从「命中→升级触发额外 cross-model」扩为双向——**命中→升级（现状不变），空集→放行轻量化（新增语义）**。不造新机制。
- **新增一个 HR-TG 成员 TG-27**（评审机制 / gate 契约 / workflow bundle 自身变更）：grounding 发现现 HR-TG 子集全是产品码风险，缺「元层」类——改 gate 的 change 做错会静默放过坏活且难回退（活体证据：dogfood gate 子串 bug 曾假过设计门），符合 HR-TG 入选判据。**本 change 自己就是 TG-27，自证此缺口**。
- **路由评判器（信号→四谓词机判→路由）**：每个阶段交接点（ff 后 / grill 后 / spec-review 后…）跑——L0 信号采集（脚本）→ L1 四谓词判定（P1–P4 **全脚本机判、无模型判断层、无标量分数**）→ L2 每阶段路由 + 平凡声明。**语义残留**（先例真同类/需求真无歧义）不由路由器判，归 grill（人·推荐+征询）。
- **「非平凡」硬定义**（吸收 T9）：四条谓词任一即非平凡——P1 命中 HR-TG / P2 面超阈（结构信号为主，>100 净行兜底）/ P3 有开放决策 / P4 非 known-pattern。**P4 known-pattern 双来源**：①bundle 内通用平凡形状白名单（脚本判、项目无关、单一源；起手三条=注释-文档-only·tests/-only·版本常量-only；扩容即 TG-27 走 FULL）∨ ②指名可核归档先例；皆无→非 known-pattern。判「平凡」MUST 在 ff 产物写一行显式声明供设计门核，**声明与脚本硬信号对不上当场穿帮**（反自评滥用）。新项目空 archive 保守默认 FULL、仅白名单形状 day-1 轻量化，随 archive 暖机。
- **可自动轻量化集 = { spec-review, superpowers }**：spec-review（HR-TG∅ 走 autoplan-lite）、superpowers（机械走 inline TDD）。done 恒跑。**grill、code-review 不属此集**（下）。
- **grill**：不属可自动轻量化阶段——只经推荐器**建议跳 + 征询用户**，机器绝不代跳（承 `grill-not-skippable` 反馈 + adr/0004「本性不可折叠」）。
- **BREAKING（spec 级）**：`sdflow-code-review 每次全跑` 精确化为**两层规则**——**Step1（scope-drift+完成度）恒跑**、**Step2（多镜 fan-out）对任何有逻辑面的 change 全跑，仅白名单机判无逻辑面形状（注释/test/版本）可免**（多镜结构零产出），Step1 scope-drift 守卫该免除。**非**「只高风险才跑」（默认开、仅机判无逻辑面免）。
- **阶段交接推荐器**（吸收 T28）：每个边界读 change 状态 → 输出下一步路由 + 可复制 prompt。
- **后向校准器**（吸收进 workflow-metrics）：复用 lens-metric（T53 已 ship）+ §7 已有「跑满 10 次复评子集」，度量对象从「HR-TG 命中率」扩到「路由决策对错」（LIGHT 事后有 buglist 回指=判松；FULL 各镜零产出=判紧）→ 数据驱动调 HR-TG 边界 / 谓词判据。

## Capabilities

### New Capabilities
- `workflow-routing`: 路由评判器（信号→四谓词机判→路由）+ 非平凡硬定义 + HR-TG 双向化语义 + 每阶段 light/full 政策 + 阶段交接推荐器 + 平凡声明的反滥用门核。

### Modified Capabilities
- `spec-workflow`: ①「sdflow-code-review 为每次全跑」需求改为「每次必跑、深度自适应」（**BREAKING**，OQ3）；②设计门新增核「平凡声明 vs 脚本硬信号」；③各编排阶段行为受路由决策门控。
- `workflow-metrics`: 「数据驱动反馈供数不供裁决」扩到路由决策——新增路由决策价值度量维度（LIGHT 逃逸 / FULL 空产出），供后向校准。

## Impact

- **规则层（权威源 `sdflow-init/assets/workflow/`）**：`trigger-catalog.md`（HR-TG 双向化 + TG-27）、`workflow.md`（非平凡定义 + 每阶段路由 + 阶段推荐）。
- **编排 SKILL**：`sdflow-spec-review` / `sdflow-code-review` / `sdflow-ship` / `sdflow-done`（light/full 分支 + 推荐器输出）。
- **脚本（新）**：路由器 `workflow/tools/route.py`（四谓词机判 + 推荐输出，单一源；遵「机械交脚本」、**无模型判断层**），+ pytest。
- **托管块（改）**：`sdflow-init` 注入 CLAUDE.md/AGENTS.md 的托管块加一行「ff 后 MUST 跑 route.py」（驱动 ff→grill 边界，非改 opsx:ff）。
- **度量**：`lens-metric` 契约 / `lens_metric_aggregate.py` 扩路由决策维度。
- **吸收 issues**：T9（非平凡定义）、T28（阶段推荐）、T19 部分（grill 跳过条件）。
- **部署**：属 bundle 权威源改动，merge 后 MUST push → 运行 checkout `/sdflow-upgrade` 激活。

## Success Metrics

1. 平凡 change 的编排成本显著下降（目标：无 HR-TG 命中的小 change 走 ff→`/code-review` 本地→done，省去 grill + spec-review 多镜 + code-review 多镜三段）。
2. 反滥用门有效：至少一个「声明平凡但脚本算出 HR-TG 命中」的用例被设计门当场拒（可测）。
3. 校准环产出真数据：≥N 个 change 走完后，聚合器能按路由决策分桶（LIGHT 逃逸率 / FULL 空产出率）——部署后观察项。

## Non-Goals

- 不引入 S/M/L 自选尺寸标签（明确保留「深度由内容触发决定」地基）。
- 不改 done 收尾门的恒跑性（收尾最终门不因路由放松）。
- 不自动砍任何评审镜/层——校准环只供数，裁决由人（承 workflow-metrics「供数不供裁决」）。
- **不在本 change 定 T19「何时可跳 grill」的规则**——grill 只推荐 + 征询、不自动跳（grill 记忆约束；跳过规则是 T19 的独立评估，勿预设结论）。
- 不把 code-review 整体轻量化（Step1 恒跑、Step2 仅白名单免；见 What Changes BREAKING）。

## 需求优先级（TG-19）

- **P0**：HR-TG 双向化 + TG-27 + L1 地板判定 + 非平凡硬定义 + 平凡声明门核（安全地基，无此则轻量化=自评滥用）。
- **P1**：L0 信号脚本 + 每阶段 light/full 分支 + 阶段交接推荐器。
- **P2**：后向校准器（度量扩维）——依赖数据累积，冷启动期先只供数。

## 假设（TG-22）

- **假设**：lens-metric 锚会随后续 change 持续累积到可校准量（现仅 7 条）。**失效影响**：校准环冷启动期无数据，路由靠静态谓词兜底（OQ2）。
- **假设**：HR-TG 子集 + TG-27 覆盖了「做错难回退」的风险面。**失效影响**：漏进 HR-TG 的高危类被误判平凡→轻量化放过坏活（校准环事后捕获，但有滞后）。

## 开放问题（TG-21）

〔grill 已全拍，2026-07-06〕OQ1→D5（known-pattern 双来源）· OQ2 冷启动→D5 · OQ3→D6（code-review 两层切）。**三个原 OQ 全清**，仅余一处非阻塞 OQ2′（校准复评节奏，可实现期定）。详见 design.md Open Questions。

## Compliance

- 承 adr/0004（设计门红线不可子串假过）——本 change 强化而非削弱门禁：平凡声明是**新增**核验项，非放松。
- 承 workflow-metrics「供数不供裁决」——校准环不自动改路由，只供数据。
- 承 [[grill-not-skippable]] 共识——grill 跳过判定 MUST 显著呈现给用户。
