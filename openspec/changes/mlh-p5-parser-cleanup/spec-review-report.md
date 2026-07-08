---
ship-gate:
  design_approved: true
---
# spec-review-report — mlh-p5-parser-cleanup

> **设计门已拍板批准**（2026-07-08）：人工过报告，Q1=A（DX 诊断增强纳入本 change），D1-D6 采纳项已回流 design/adr/specs/tasks。头部 frontmatter `design_approved: true` 为 `/sdflow-ship` pre-flight 唯一机判锚（正文此行供人读，不因迁移消失）。

> 阶段二设计评审（连续多镜编排）。对象：ship_gate.py 解析器收尾清理（T74 无闭合`---`改判 absent + unterminated 退役 + T75 死代码）。
> 镜配置：Step1 autoplan 广审（native：codex 跨家族 + Claude eng/DX subagent）· Step2 领域镜 0（无栈命中）+ 对抗镜 2（spec自洽/测试完备）+ 接地镜 1 · HR-TG=none。
> 前置：已过 3 轮 grill（Q1 exit0语义 / Q2 归档目标态+adr0011 / Q3 意图无关）。

<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG=23/19/18/12/20，HR-TG 子集={04,06,07,08,09,16,17,26} 交集为空" -->

## 结论

**无致命/高危 bug**。核心安全主张经两批独立冷镜逐点核码**成立**（absent 三读点不放行 / 死符号删除运行时零引用 / MODIFIED 完整保留 34 Scenario）。发现 **8 条 finding**：7 采纳（多为文档/测试完整性）+ 1 需拍板（DX 诊断增强）+ 1 defer。核心捕获 = **`anchor_set` 第三调用方**（三镜独立命中：codex + Claude eng subagent + 测试完备镜），暴露刚立的 adr/0011「每调用方论证」纪律**首次落地即漏一个调用方**——运行时安全（两语义都返空集）但论证+测试不闭环，必修。

**建议：进设计 HARD-GATE 拍板**（Q1 DX 诊断增强需人定 scope）。

---

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────────┐
│ [自动决策] 已采纳，设计门默认接受可覆盖                                  │
│  D1  BR-1/TC-1 anchor_set 第三调用方 → 补 adr/0011+design 论证 + 加测试   │
│  D2  BR-2 「两侧同向 fail-safe」→ 限定「目标态」+ Risks 点明取舍           │
│  D3  BR-3 ALL_ANCHORS 收缩压垮语料测试 → tasks 补外科改写                 │
│  D4  GR-1 design 表格三读点行号偏差 → 改符号锚（抗腐蚀）                   │
│  D5  TC-2 live 三读点测 2/3 → tasks 补 code-review 无闭合用例             │
│  D6  SC-1 A3 枚举①② 视觉混淆 → 改字母/数字区分（cosmetic）               │
│ [已决 Q1=A] 设计门拍板选 A 纳入                                          │
│  Q1  BR-4 DX 诊断增强 → 纳入本 change（design ADR-5 / spec Scenario /     │
│      tasks 1.5：live 上层加纯结构 reason，不改 parse 签名/verdict）        │
│ [已裁掉] 无（所有 finding 采纳或登记，无静默丢）                          │
│ [defer]  TC-3 BOM/CRLF+无闭合组合测试（代码路径正交可证，可选）           │
└──────────────────────────────────────────────────────────────────────┘
```

### Q1〔需拍板·≥2 方案〕BR-4 — DX 诊断增强是否纳入本 change scope

漏闭合 frontmatter → absent → 开发者见「缺 design-approved 锚 / 无锚重跑」，但他**确实写了** frontmatter（漏闭合行被当正文），线索归零、误导向「你没写」。改判前 `unterminated`→UNKNOWN reason 至少指向 frontmatter 结构。

- **选项 A（纳入）**：在 absent 分支 emit reason 加一句**纯结构**观察「首行为`---`但未见闭合`---`，已按正文处理；欲声明状态请补闭合行」。**≠ 意图探测**（candidate②=探测下一行是否 `key:` 形态；这里只报客观结构，不改任何 verdict、不重开自指、不复崩）。
- **选项 B（保持最简/defer）**：不加诊断，维持 design Risks 已登记的「诊断精度损失，方向安全可接受」。

**三面后果**：
- 系统镜：A 加一个纯结构判定（首行`---`且无闭合）落 reason，零判决改动、零新分支语义；B 零改动。
- 用户镜（开发者）：A 恢复 actionability（明确指向"补闭合行"）；B 开发者可能在"没写锚"方向空排查。
- 开发循环镜：A 一次小改闭合 DX 缺口，避免未来重复踩；B 留作已登记取舍，未来若真困扰再单开。

**推荐 A（主）**：低成本、恢复 actionability、subagent 已论证与意图探测可分（不重开自指免疫）。**主次判定**：DX 恢复 > 极简洁；且 A 的结构判定与本 change 主题（无闭合`---`识别）同源，fold 自然，不增循环成本。**次要保留**：若设计门认为 emit reason 改动触及 live 读点措辞需更谨慎，可 defer 单开——但本 change 已在改该分支，顺手成本最低。

---

## 各镜 findings（置信/严重度；低置信项亦上抛不滤）

### Step1 broad（autoplan native：codex + Claude eng/DX subagent）— 详见 gstack-review.md

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="ok" findings="1" truncated="false" -->


- **BR-1【CONFIRMED 三镜命中·高/低】** `parse_ship_gate_frontmatter` 三个调用方（`live_ship_gate_state` L477 / `archived_verify_state` L196 / **`anchor_set` L412**），design ADR-4 + adr/0011 写「两个」=事实错误。anchor_set 对 unterminated 与 absent 都返空集→**行为不变、运行时安全**，但违 adr/0011 自铸「改共用核心 MUST 对每个调用方论证」。→ **采纳 D1**。
- **BR-2【高/低】** 「两侧同向 fail-safe」只在**目标态**成立；过渡/旧档语境归档侧对杂交形态（首行`---`无闭合×正文 inline PASS）none→潜在 pass 是净负（已登记为越权/无 producer 产出）。→ **采纳 D2**。
- **BR-3【高/中】** `ALL_ANCHORS` 收缩会压垮 `test_gate_anchor_scope.py:150 test_contract_archived_corpus_anchor_hits`（L153 `assert DESIGN in exclusive`）→ AssertionError，冲突 Success Metric「pytest 全绿」；且实现者「删孤儿」有误删保留路径守卫风险。→ **采纳 D3**。
- **BR-4【高/低】** DX 诊断可加纯结构 reason 恢复 actionability（≠意图探测）。→ **需拍板 Q1**。
- 背书：absent 三读点不放行成立（另验 verify早检 L713 / cr_stale peek L780 附带读点安全）；死符号运行时零引用；unterminated 退役无第三方依赖；边界 BOM/CRLF 更安全。

### Step2 grounding（接地镜·代码事实核验）

- **GR-1【高/低】** design ADR-1 表格三读点**起点行号偏差**：design=L694(非L695) / code-review=L755(非L760) / verify=L789(非L795)——核心逻辑行对，起点漏前置块行。其余全部符号/死符号/保留边界/测试文件存在性**核对一致**。→ **采纳 D4**：改符号锚（行号易腐蚀，符合「盘面即状态」精神）。

### Step2 adversarial（对抗镜×2）

- **SC-1【spec自洽·高/低 cosmetic】** MODIFIED **完整保留 34 Scenario**（脚本核对 delta 36=34+2，archive 不丢）+ 5 项对抗全 refuted；仅 A3 段两个独立枚举都用①② 造成「哪个①」阅读歧义。→ **采纳 D6**（改标记）。
- **TC-1【测试完备·高/中】** `anchor_set`（第三调用方）无一测试锁定其对首行`---`无闭合返回空集的不变性；未来重构 anchor_set 短路会无声失守。→ **采纳 D1**（与 BR-1 配套补测试）。
- **TC-2【测试完备·高/中低】** design 表格自陈 live **三**读点，tasks 3.1 只测 design+verify，**漏 code-review** 分支（有隐性等价兜底但纪律缺口）。→ **采纳 D5**。
- **TC-3【测试完备·中/低】** BOM/CRLF+无闭合组合未显式测（代码路径正交可证）。→ **defer**（可选）。
- 背书：parse 全分支覆盖足；正常归档不误伤（3.3 既有回归兜底）；死符号误删有 pytest 全绿隐性护栏。

---

## lens-metric 度量锚（草稿值，设计门拍板时按 SR-M 最终化）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="2" sev="致0/高0/中1/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="3" sev="致0/高0/中1/低2" -->

---

## 收敛口

设计已由 3 轮 grill + 本轮 8 finding 夯实到高完整度，无致命/高危缺陷，核心安全主张多镜背书。**建议进设计 HARD-GATE**：人工过 Q1（DX 诊断增强 scope）后拍板 → 主 session 写 `ship-gate.design_approved: true` frontmatter → writing-plans。D1-D6 采纳项已回流 design/adr/specs/tasks（标 `[spec-review-amendment]`）。
