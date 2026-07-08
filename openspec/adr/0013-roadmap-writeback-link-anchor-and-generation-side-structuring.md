# roadmap 回写：关联锚契约 + 生成侧目标态结构化 + best-effort 记录维护

`done-roadmap-writeback` 给 `sdflow-done` 加「归档后回写关联 roadmap」步（勾复选框 + task-log 完成总结 + 里程碑/阶段状态）。grill design.md 纠正两处基准误用，据此把回写从「适配现状散文格式 + fail-closed 全停」重构为「生成侧结构化 + best-effort 记录维护」。

## Context（grill 两纠正）

**纠正①（基准：目标态 vs 现状快照）。** design 初版 ADR-1 用「现存 6 个归档 roadmap-驱动 change 的 proposal 引用形态不统一（2/6 全路径 `openspec/roadmaps/{name}/`、余中文别名/反引号/缺失）」证伪「L1 从 proposal 机械提取引用」。grill 揭穿这是**用现状快照否定目标**（CONTEXT『目标态论证』/`adr/0011`）——那 6 个是在**无回写功能、无关联契约**的旧世界写的，引用自由因当时无约束要统一；拿「迁移前旧数据当然没新形态」证「不可达」，即以现状否定设计目标。正解锚**目标态 producer 契约**（producer 会不会产确定性关联信号），非「现存 proposal 有没有」。

**纠正②（范式：记录维护 vs 正确性门）。** design 初版把 `lens_metric_emit` 的 all-or-nothing fail-closed 套到 roadmap 回写（子任务定位失败 → 整体不写）。grill 揭穿范式误用——emitter 是**正确性门**（错=假绿，零容忍 fail-closed 正当）；roadmap 回写是**记录维护**（漏写=记录陈旧、可事后补、非正确性缺陷）。记录维护该 **best-effort + 缺失显形**（反静默守卫），非 fail-closed 全停——为一个 id 定位不到就丢掉本可回写的部分，记录反而更差。

## Decision

1. **关联判据锚 producer 机器锚**。roadmap-驱动 change 起手在 proposal 写 `<!-- roadmap: {name} phase: {PN} subtask: {id,...} -->`；L1（关联哪个 roadmap）grep `name`、L2（哪些子任务）读 `subtask` 列表——**均读锚字段、MUST NOT 解析 proposal 自然语言引用**（措辞属概率空间、正则半数 miss，同 gate frontmatter / lens-metric 契约弃自然语言）。无锚 → 按无关联静默跳过（producer 违约的 fail-safe）。锚落 change 自身 proposal（单一源，无跨文档反查漂移）。

2. **结构化投入搬生成侧（目标态）**。不让 done 回写去适配现状散文（半个现状快照），而在 `sdflow-roadmap` 生成侧结构化 roadmap **索引层**：概览表加 `状态` enum 列、子任务复选框固定 id + 交付标注槽、task-log 条目加机器锚行；**叙述层**（目标/设计理由/完成总结叙述/里程碑句）留人读散文。生成一次、回写多次 → 结构化投入放 producer 侧摊销。同 recorder「总览表+详细块」、gate「frontmatter+正文」。

3. **回写 = best-effort + 降级标注（三级 fail-safe）**。全定位成功 → 全回写；部分成功 → 回写能做的 + **降级标注**未做项（task-log/最终摘要就地标，反静默）；完全无法解析格式 → 才提示留人工。fail-closed 只在末级。**回写全程不阻塞 archive/merge**（记录维护 altitude，非 verify 正确性门）。

4. **机械/判断切分**。勾选 + 阶段状态 cell 更新 + 关联检测 = 脚本机械写；完成总结叙述 + 里程碑句 = 模型写、脚本只校验机器锚在场（anchor_lint 式）。真正的「判断」收窄到两处：完成总结叙述、里程碑句。

5. **旧 2 roadmap 手动迁移新格式**（`mechanical-layer-hardening`、`workflow-cost-optimization`），**不背 dual-read**——只 2 个，一次性迁移比永久双读契约干净。

## Considered Options

- **producer 机器锚 + 生成侧结构化 + best-effort（选中）**：目标态根治，关联/定位/勾选机械化、判断收窄两处；与 lens-metric/gate 同范式（弃自然语言、结构化单一源）。代价：scope 扩至 6 件（含改 `sdflow-roadmap` + 迁移 2 roadmap），Non-Goal「不改 sdflow-roadmap」翻案——但 `sdflow-roadmap/SKILL.md:195` 本就预告「将来给 verify/done 接 hook 自动化」，配合非越界、是设计原意兑现。
- **解析 proposal 自然语言引用（弃）**：现状快照谬误的产物；引用形态自由（实证 2/6 全路径、余别名/缺失），措辞属概率空间、正则半数 miss（同 gate grill 教训）。
- **all-or-nothing fail-closed 回写（弃）**：正确性门范式误套记录维护；定位失败全停、丢弃可回写部分，记录更差，违反「尽力 + 缺失显形」。
- **在现状散文格式上硬做回写、不改生成侧（弃）**：半个现状快照——把结构化复杂度压在回写侧（每 change 一次、脆弱），而非生成侧一次摊销。
- **dual-read 新旧格式（弃）**：只 2 个旧 roadmap，永久双读契约成本 > 一次性手动迁移。

## Consequences

- **done-roadmap-writeback 落地本 ADR**：design 四 ADR 全翻案（ADR-1 锚 producer 机器锚 / ADR-2 时序不变、archive 路径追溯 / ADR-3 机械半进脚本 / ADR-4 best-effort 三级）；proposal 删 Non-Goal「不改 sdflow-roadmap」、scope 扩 6 件；specs 补关联锚契约 + best-effort 回写 + 阶段状态 enum + 降级标注 Scenario；tasks 补 sdflow-roadmap 两模板优化 + 2 roadmap 迁移 + `roadmap-link` 脚本。
- **sdflow-roadmap 生成格式升级**：`roadmap-template.md` 概览表加 `状态` enum 列（模板原无此列）+ 子任务交付标注槽；`task-log-template.md` 条目加机器锚行。是「盘面即状态」在 roadmap 层的落地。
- **与 adr/0006 同哲学**：把「roadmap 回写手工协议」脚本化 + 「roadmap 索引层散文」结构化——机械 prose 协议 MUST 脚本化/结构化的又一实例。
- **与 adr/0011（目标态论证）同源**：又一次实证「开发阶段锚目标态 producer 契约、非现状快照」——L1 判据锚「目标态 producer 会产机器锚」而非「现存 proposal 有没有」。
- **CONTEXT.md**：新增术语「关联锚」「roadmap 索引层 vs 叙述层」「记录维护回写 vs 正确性门」。
