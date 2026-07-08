---
ship-gate:
  code_review: pass
---

## code-review 报告 — mlh-p5-parser-cleanup

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG-18(测试计划)/TG-20(外部影响方 bundle)，均不在 HR-TG 子集(TG-04/06/07/08/09/16/17/26)" -->

### 命中范围
- **栈/语言**：Python 3 stdlib（`sdflow-ship/scripts/ship_gate.py` 确定性只读台账 + pytest）。无 go/embedded 领域 delta 命中 → 领域镜过通用 base **CR-01~09**。
- **diff base**：`d94c385`（分支起点）；变更 = ship_gate.py（parse `end is None`→absent + `_unclosed_frontmatter_hint` + 三读点接线 + 删死符号 + ALL_ANCHORS 收缩）+ 6 测试文件 + change 四件套 + adr/0011 + CONTEXT.md 词条。
- **gstack/review（Step1，native）**：scope-drift = **无 implementer 顺手多改**（代码改动逐条吻合 plan；CONTENT.md 词条 + adr/0011 系设计/grill 阶段紧耦合产物，非 ship 期漂移，ship 实现子代理仅动 ship_gate.py + tests）；完成度 = **完整**（3 任务全落、tasks.md 15 子项全映射、逐任务 review clean、157 tests 绿 0 warning，无半成品）。
- **trivial_shape**：NOT_EXEMPT（behavior-path ship_gate.py）→ 照常 fan-out。
- **fan-out**：领域镜×1（CR-01~09）+ 对抗镜×2（parse 边界 / 三调用方 blast-radius）+ 历史镜×1 + outside-voice code-voice（codex）。**HR-TG=none**（不单开领域 cross-model）。

### Findings（置信 ≥80）

- **[中/设计门已接受]** F1 归档杂交盲区 SHIPPED 回归 · CR-01/CR-02 · `ship_gate.py:318-322`(parse absent)+`:200-206`(archived 回退 inline)+`:669-677`(D3 短路 SHIPPED) · 置信 95（对抗镜 parse-edge 用真实 CLI 端到端 bit-复现 UNKNOWN(6)→SHIPPED(0)）· **裁决：defer→todolist T76**（设计门已显式识别+判净负+接受，实现忠实，见「裁决」区）
- **[低]** F2 verify 读点 stale 分支先于 absent 分支、吞未闭合结构提示且「结论陈旧」措辞对无结论报告失准 · CR-07 可观测 · `ship_gate.py:801-804` · 置信 82 · **已修[impl-review-fix]**（stale 分支加性追加 `_unclosed_frontmatter_hint`，不改 verdict/退出码/next；新增 `test_stale_unclosed_verify_appends_hint`）
- **[低]** F3 grep `unterminated` 命中 2 条测试注释，与 plan Step8「tests/空输出」冲突（符合 proposal 成功指标「仅剩历史注释/无」但 plan 措辞过严）· CR-09 · `test_frontmatter_parse.py:32`/`test_gate_breaker.py:84` · 置信 80 · **已修[impl-review-fix]**（改注释措辞「旧错误类别」，grep 全净）

### 已裁掉（反静默压制，可审计）
- **X1（F5，<80 滤除）** 领域镜：`_unclosed_frontmatter_hint` 与 `live_ship_gate_state` 各 `read_text` 一次 = 二次文件 I/O（`ship_gate.py:464-480` vs `:453-456`）。置信 40 · **裁掉/不修**：非泄漏、纯冗余读，报告文件小、频率低，领域镜自身建议不重构（让 live_ship_gate_state 回传 text 会加耦合，ROI 负）。记录留痕。
- **X2（F4，spec 整洁性）** outside-voice：delta spec「过渡期 live 未迁 producer 回退 inline」Scenario 迁移窗已闭、与退役现实张力。**降级**：非代码缺陷——该 Scenario 末句「退役后 live MUST 只读 frontmatter」已 governing、WHEN 前提对 live 已空置、代码无活跃冲突；归档 dual-read 是另一独立 Scenario（正确保留）。**defer→todolist T77**（spec 整洁性，非本 change scope）。
- **X3** OV 初判 F1 为 high / 对抗镜 parse-edge 判 high：severity-in-context **降级**为「设计门已接受净负」（见裁决区），非未披露缺陷；behavior 事实保留、defer 硬化后续 T76。

### 修复 / defer 台账
- **自动修 2 项[impl-review-fix]**：F2（verify stale 分支加结构提示 + 回归测试）、F3（改测试注释措辞使 grep 全净）。
- **defer 2 项 → todolist**：T76（F1 归档盲区**非语义** lint/监控硬化后续 + 以更锋利可达性论证复评 ROI）、T77（F4 spec 过渡 Scenario 标历史）。
- **T10 复核**：本轮无「无客观判据的 ≥2 方案自动选」——F2/F3 修复方案均有客观判据（既有加性 hint pattern 已三读点验证 / 注释措辞改动零风险 + pytest 全绿），直接自动修，无需对抗镜复核。

#### 裁决详述 — F1（归档杂交盲区，冷层 vs 设计门）
冷代码审对抗镜（parse-edge）抓到「首行 `---` 无闭合 × 归档正文独占行 inline PASS 锚」→ `archived_verify_state` 由 `none`(fail-safe) 变 `pass` → D3 短路 **SHIPPED**，且 bit-对比坐实为改动前 UNKNOWN(6)→改动后 SHIPPED(0) 的回归，方向正是 gate 核心目的（防假 SHIPPED）被击穿方向。**这是冷独立层 load-bearing 的价值，不静默驳回。**
核实设计门实际论证（design.md L136，grill-amendment Q2 + spec-review BR-2）：**设计门已显式识别这一模一样的杂交形态**、**明确标注「净负」**（"T74 用 live 侧止崩换来归档侧此一形态 fail-safe 削弱"）、**明确承认过渡/旧档语境**，并接受之——mitigation = 无 producer 产出（新 producer 只写闭合 frontmatter、旧 producer 首行 `#`）+ 头注册登记「已知不覆盖」+ 目标态回归测试（tasks 3.5，已实现 `test_archived_unclosed_*` 双测钉死）；design L121 另显式论证「为何不给归档侧特殊 fail-safe（选①绝，ROI 负、破坏共用严格核心防漂移收益）」。
**裁决**：行为回归已被设计门（HARD 人类门）显式权衡接受，实现忠实（头注释 + 两条回归测试俱在）。阶段三 MUST NOT 重开设计门（adr/0004 红线）→ **不 block**。冷镜新增的可达性论证（迁移半成品编辑残留 inline / 自指文档独占行）确有价值，但「迁移编辑」与本设计「旧档永久 dual-read、从不迁移」相悖、「自指」被 `_line_scoped_hits` fence-aware 行锚定部分缓解 → 记 T76 供未来以更锋利论证复评 ROI（非语义 lint/监控，设计门中立）。

### 度量锚（lens-metric，metrics.enabled=true）
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="ok" findings="3" truncated="false" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="native" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="checklist" findings="2" 采纳="0" 裁掉="1" defer="1" 独立="0" sev="致0/高0/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="parse-edge+blast-radius" findings="1" 采纳="0" 裁掉="0" defer="1" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="blame" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="2" sev="致0/高1/中2/低0" -->

### 结论
- ☑ 建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）
- ☑ defer 残差已入 todolist（T76 归档盲区硬化后续 / T77 spec 过渡 Scenario 整洁性），hand-off 会引用
- 冷层 F1 已充分裁决：设计门显式接受的净负权衡、实现忠实、不 block；未来硬化路径已留痕 T76。
