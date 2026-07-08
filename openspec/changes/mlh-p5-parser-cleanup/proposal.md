## Why

`mlh-p5-gate-frontmatter`（gate 锚 inline→frontmatter）合并后留了两条非阻塞 defer 尾巴（T74/T75）。其中 T74 是一个**真的解析健壮性缺口 + spec 内部措辞张力**：`ship_gate.py` 的 `parse_ship_gate_frontmatter` 把「报告首行是 `---` 且全文无第二个 `---`」判为 `("frontmatter","unterminated")` → live 侧 `UNKNOWN(exit 6)` 硬崩一份本该走无锚语义的干净报告。当前语料侥幸不触发（现有报告均以 `#` 开头），但这与 spec 自身「frontmatter 只认第 1 行 `---` 到下一 `---` 止的唯一首块」定义相悖——没有闭合 `---` 就不构成首块，本应判 `absent`（无 frontmatter），却被打成「坏」fail-closed。趁 P5 上下文尚热一并清，把账结清。

## What Changes

- **T74（P0，正确性 + spec 修订）**：`parse_ship_gate_frontmatter` 中「首行 `---` 无闭合」由 `unterminated` 改判 `absent`（返回 `({}, None)`）——无闭合 `---` 不构成 frontmatter block，是正文/markdown 水平线。据此 **MODIFIED spec-workflow**：把「写坏 fail-closed」Scenario 的 ①「`---` 起止界定缺失/不配对」拆解，明确「首行 `---` 无闭合」归 absent（走既有无锚语义），只有「有配对首块但块内 ship-gate 键坏」才 fail-closed；与「只认首块」Scenario 的首块定义统一。
- **unterminated 死类别退役（P1，T74 连带）**：候选①落地后 `unterminated` 成永不产生的错误类别 → 从 `parse_ship_gate_frontmatter` docstring 的 `category` 枚举移除；相关测试用例改为断言 absent。
- **T75（P1，纯机械清理）**：删除 Task6 退役 live inline 读半场后只剩 test 引用的孤儿符号——函数 `anchors_in` / `pick_exclusive`，常量 `ANCHOR_DESIGN` / `ANCHOR_CR_PASS` / `ANCHOR_CR_BLOCKED`，连带收缩 `ALL_ANCHORS` 并删对应孤儿测试。

**非破坏**：三项均向后兼容——absent 语义不变（下游各步对无锚的处理不改）、死符号本就无运行时引用。

## Success Metrics

- 首行 `---` 无闭合的报告 → `parse_ship_gate_frontmatter` 返回 `({}, None)`，live 侧走无锚语义**不再崩 exit 6**（新增回归测试断言）。
- `unterminated` 类别在全代码库**无任何产生路径**（grep `unterminated` 仅剩历史注释/无）。
- 删死符号后 `pytest sdflow-ship/tests/` 全绿；死符号在源码与测试中**无残留引用**。
- `ANCHOR_VERIFY_PASS`/`ANCHOR_VERIFY_FAIL` + `_line_scoped_hits` 保留，`archived_verify_state` 归档 inline dual-read **不回归**（既有 88 归档报告兼容测试仍绿）。

## Capabilities

### New Capabilities
<!-- 无新增能力 -->

### Modified Capabilities
- `spec-workflow`: 「阶段三编排台账确定性（ship_gate）」的 frontmatter 解析边界修订——「首行 `---` 无闭合」由 fail-closed 改判 absent，弥合「只认首块」与「写坏 fail-closed」两 Scenario 的措辞张力；`unterminated` 错误类别退役。

## Impact

- **代码**：`sdflow-ship/scripts/ship_gate.py`（`parse_ship_gate_frontmatter` 改 1 行返回值 + docstring；删死符号 `anchors_in`/`pick_exclusive`/`ANCHOR_DESIGN`/`ANCHOR_CR_PASS`/`ANCHOR_CR_BLOCKED` + `ALL_ANCHORS` 收缩）、`sdflow-ship/tests/`（新增无闭合回归 + unterminated 用例改断言 absent + 删死符号孤儿测试）。
- **spec**：`openspec/specs/spec-workflow/spec.md` delta（MODIFIED「阶段三编排台账确定性」Requirement 的 fail-closed Scenario）。
- **外部影响方（TG-20，轻度）**：`ship_gate.py` 是 bundle 工具，经 `sdflow-init update` 铺到下游消费仓。本 change 是纯健壮性修复 + 清理、向后兼容，下游影响 = gate 判定对无闭合 `---` 报告更健壮、不误崩；无需下游动作（消费仓下次 `sdflow-init update` 自然拿到）。
- **依赖**：无新增依赖（`parse_ship_gate_frontmatter` 仍手写 stdlib，保零依赖不变量）。

## Non-Goals

- **不动 P6（recorder 索引→frontmatter）**：north-star，ADR 0010 defer，本 change 只清 P5 尾巴。
- **不改归档 dual-read 的分支结构**：`archived_verify_state` 的「frontmatter 优先→absent 回退 inline」分支骨架与 `_line_scoped_hits` 保留不动。**订正**〔grill-amendment Q2〕：因共用同一 parse 核心，改判 absent 对「首行 `---` 无闭合」归档报告的处置**确有变化**（`none`→回退 inline），非「逐字不变」；目标态论证证其 fail-safe（漏闭合归档无 inline 可扫→`none`），详见 `adr/0011` + design ADR-4。
- **不引入 candidate②（意图探测启发式）**：explore 已论证其在本仓「讨论 gate 自身」的报告上会精准误崩（重蹈 gate-substring-dogfood 覆辙），明确弃用，理由入 design ADR。
- **不改其他坏类别的 fail-closed 语义**：越域/重复键/tab 缩进/类型不符仍 UNKNOWN(exit 6)，只修「无闭合首块」这一条归类。

## Compliance

- **bundle 权威源纪律**：改的 `ship_gate.py` 在 `sdflow-ship/scripts/`（skill 源），非下游副本；符合「改权威源、经部署下发」。
- **机械层红线（design §决策 5）**：新判定仍 fail-closed 取向（absent 不放行，方向安全）+ pytest 覆盖坏输入断言退出码；判断部分不越权。
- **adr/0004 红线（正文提及不假过门）**：absent 判定后 live 不回退 inline、不扫正文，与既有边界一致。
