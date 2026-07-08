# 改共用解析核心的返回语义，须按 producer 契约 + 目标态对每个调用方分别论证安全（非以迁移现状评估）

`ship_gate.py` 的 `parse_ship_gate_frontmatter(text)` 是 mlh-p5 定的**单一自持解析核心**（adr 家族①/A4 铁律「live 与归档 frontmatter 读共用同一严格核心」），被两个调用方共用：`live_ship_gate_state`（live 报告，走无锚语义分流）与 `archived_verify_state`（归档报告，D3 短路的 SHIPPED 判据源，absent 时**回退 inline dual-read**）。共用核心的好处是防两路解析漂移，**代价是**：改它任一返回语义，两个调用方**同时**受影响，且两侧的安全方向**可能相反**——live 侧 absent = 保守（不放行），归档侧 absent = 回退 inline（可能判 pass→SHIPPED）。

`mlh-p5-parser-cleanup`（T74）把「首行 `---` 无闭合」从 `unterminated`(坏) 改判 `absent`，初版 design 只论证了 live 侧安全、并错误声称「T74 只影响 live」。grill 揭穿：归档侧共用同一核心，行为亦变。**更关键的方法论错误**——初版用「现存 25 份归档 verify-report 有 24 份以 `#` 开头、无一触发」作「不可达」论据。这是**以迁移中途的现状评估设计**：frontmatter 承载态是 mlh-p5 起正在推进的目标，旧报告当然没有 frontmatter；拿迁移前快照当风险基线，会把「目标态才暴露的面」误判为「不存在」。正确论证必须锚在 **producer 契约 + 目标态**：`sdflow-done` verify 模板（SKILL.md）MUST prepend frontmatter、**不写 inline 锚**；故目标态归档报告 = frontmatter-only。据此重估「首行 `---` 无闭合」归档报告 → absent → 回退 inline → 正文**无 inline 可扫** → `none` → 不 SHIPPED = **fail-safe（与 live 侧同向安全）**；初版担心的「回退 inline 判假 pass」需「`---` 打头 × 正文 inline PASS 锚」杂交，**无 producer 会产出**（未来 producer 不写 inline、旧 producer 首行是 `#`）——此结论不依赖任何现状快照。

**决策**：改 `parse_ship_gate_frontmatter`（或任何 live/归档共用解析核心）的返回语义，MUST 对**每个调用方**基于 **producer 契约 + 目标态**分别论证安全（不得以迁移现状/当前语料评估），并显式验证两侧安全方向；论证结论 MUST 落测试钉死目标态行为。

## Considered Options

- **producer 契约 + 目标态双调用方论证（选中）**：把「安全」的判据从「当前语料是否触发」升格为「目标态 producer 会/不会产出该形态、每个调用方对该形态的处置方向」。零额外运行时机械，纯论证纪律 + 测试锚。对齐机队锚定「不押上游理想假设」的反面——这里是「不押迁移现状假设」，同样是「盘面/目标即真相，不押快照」。代价：改共用核心的 change 须多写一侧论证 + 一条目标态测试，但这正是共用核心防漂移收益的应付成本。
- **给归档侧对「无闭合」特殊 fail-safe（parse 返回可区分信号 or `archived_verify_state` 自探首行）**：未选——目标态归档侧对漏闭合本就 fail-safe（回退 inline 扫空→none），为一个 **producer 不产出**的杂交形态引入可区分信号，破坏 A4「共用严格核心」的简洁、增测试面，ROI 负；且它把「无闭合」在 live/归档做成两套语义，重新打开漂移面（A4 要防的正是这个）。
- **维持初版「以现状评估」+ 只影响 live 表述**：未选——方法论错误（以迁移现状否定设计目标），且事实错误（共用核心，归档侧行为确变）；会让未来改该核心的 change 复刻同一盲区（只看 live、只看现状）。

## Consequences

- **mlh-p5-parser-cleanup 落地本 ADR**：design 订正「只影响 live」为「共用 helper、归档侧行为亦变、目标态两侧同向 fail-safe」；spec delta 补归档侧 Scenario（目标态漏闭合 frontmatter + 无 inline → `none` 不 SHIPPED）；tasks 补该目标态归档回归测试；`ship_gate.py`「已知不覆盖」登记「`---` 打头 × inline PASS 杂交（无 producer 产出，须手工越权构造）」盲区。
- **与 adr/0006、0008、0009、0010 同哲学**：workflow「不押上游理想假设」——本 ADR 是其在**迁移期**的专项：不押「迁移现状 = 稳态」，论证锚目标态。
- **与 A4 铁律互补**：A4 立「共用严格核心防漂移」，本 ADR 补「共用的代价是改它须双侧论证」——两条合起来才完整（享防漂移收益、付双侧论证成本）。
- **CONTEXT.md**：新增术语「目标态论证（Target-state Reasoning）」——迁移期评估设计安全性 MUST 锚 producer 契约下的目标稳态，非迁移中途现状快照；与「盘面即状态」正交（后者说真相源是盘面，本条说迁移期的「盘面」要取目标态而非当前快照）。
