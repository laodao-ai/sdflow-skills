# 0020 · SAD 生态位与生命周期（空间轴 skill 独立 + architecture/ 单例三层 + skeleton-ready DoD）

> 状态：**Proposed**（2026-07-12，grill `add-sdflow-architecture` 收敛时立）——待该 change ship + 首个消费仓试点后升 Accepted。
> 关联：`docs/sad/02-sad-skill-design.md`（设计定稿考古层，真相源移交声明在其头部）· change `add-sdflow-architecture` design DEC-1~12 · adr/0007（命名整合）· sdflow-roadmap 规则 4（直写先例）· CONTEXT「SAD / skeleton-ready / 骨架 change / 骨架切片建议 / 事实三问 / 假设显影」。

## Context

生态已有时间轴规划（sdflow-roadmap）与交付管线（change/ship），**空间轴（架构设计）缺位**：子系统拆分无规则、contract 无落点、SAD 无载体。方法论经 `/opsx:explore` 多轮收敛为 docs/sad/00–02（判据流水线、S1–S11 质量判据、五步流程、骨架先行）。实践先例：mqtt-console 的 roadmap 包自发长出 `technical-architecture.md`——design.md 装不下架构细节会自然分裂，**需求真实**；但其落位（effort 包内）是「该 roadmap 恰好等于整个产品」的巧合，非通例。

## Decision

1. **独立 skill `sdflow-architecture`**，不升级/并入 sdflow-roadmap——roadmap 切时间、SAD 切空间，两轴正交；触发分工双侧指路（新项目起步尚无 SAD → 先 architecture，时间轴规划 → roadmap）。
2. **落位 `openspec/architecture/`，per-system 项目级单例**（非 per-effort）：`sad.md`（live，永远当前态）+ `openspec/adr/`（decision，不可变 + supersession）+ `sad-log.md` & git（history，append-only 判定留痕）——文档三层分离在消费仓目录上直接成型。
3. **职责三分、互引不复述**：roadmap design.md = WHY-product，SAD = HOW-structure（子系统/contract/横切），roadmap.md = WHEN。
4. **SAD 直写、不经 change 壳**（先例 roadmap 规则 4，旧版变更壳已实证废弃；质量门内建：lint + 冷走查 + 升档镜阵 + 人门）；**第一个 change 壳 = 人拍板开的骨架 change**（skill 只产内嵌「骨架切片建议」节，不代开）。
5. **DoD = skeleton-ready**（够切骨架即合格）：纸上 contract 皆假设，骨架验证前无定稿；contract 成熟度 `planned/draft/validated/frozen` 由骨架落地逐条回写。

## 为何这样（判据）

- **两轴正交 + 拆分标准**（一个 skill 一个内聚职责）：时间规划与空间架构混进一个 skill 违反「一个完整阶段结果」。
- **生命周期错配**：SAD 生命周期 = 系统生命周期 > effort 生命周期——roadmap 包归档后系统还活着，SAD 住 effort 包必成孤儿。
- **骨架先行是结构性机制非流程建议**：它重定义 DoD，从根上消解「day-0 逼准数 / 逼 contract 五层全满」的过度索取（价值占位、主干三层即可）。
- **直写**：规划文档进 change 管线是 roadmap v1 已踩过并废弃的坑；change 的 delta/verify/archive 语义对永生 live 文档空转。

## 被否方案

- SAD 放 `roadmaps/{name}/` 包内 / 升级 sdflow-roadmap 承载（落位与生命周期错配）；
- 「approved 定稿 SAD」语义（违骨架先行——伪严谨 + 过度索取，docs/sad/02 附录 A3）；
- skill 代开骨架 change（越权工作流决策，打穿「直写规划层 / 管线实施层」分界）；
- 独立 skeleton-draft 交棒文件（必复述 SAD §5、必失鲜——改为内嵌暂态节）。

## Consequences

- **正**：消费仓三层目录范式统一（live/decision/history）；空间轴能力补位；roadmap/architecture 分工与调用序清晰（SAD → 骨架 → roadmap ⇄ L2 just-in-time → changes，不强制）。
- **负 / 代价**：sdflow-roadmap 的 design 模板需后续瘦身 change（短期两文档职责靠「互引不复述」纪律维持）；消费仓新增 `architecture/` 布局由 skill 运行时创建（无 openspec 布局则 preflight fail-closed 指引 sdflow-init）。
- **残余**：L2 子系统设计方法论未定（change OQ1）；多系统 monorepo 的 `architecture/{system}/` 演进已预留未实现（change 假设 A4）。
