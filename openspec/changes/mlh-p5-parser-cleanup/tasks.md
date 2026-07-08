# Tasks — mlh-p5-parser-cleanup

> 追溯：全部任务归属 Requirement **「阶段三编排台账确定性（ship_gate）」**（MODIFIED）。
> 关键 Scenario 锚：`首行 --- 无闭合判 absent 不硬崩`(T74)、`live 报告 frontmatter 写坏 fail-closed`(收窄)、`解析半场退役边界`(T75)、`归档旧 inline 锚 dual-read 永久兼容`(保留边界)。

## 1. T74 — 首行 `---` 无闭合改判 absent〔Scenario: 首行 --- 无闭合判 absent 不硬崩〕

- [ ] 1.1 `ship_gate.py` `parse_ship_gate_frontmatter`：`end is None`（首行 `---` 无闭合）分支由 `return {}, ("frontmatter", "unterminated")` 改为 `return {}, None`（absent）；注释写明「无闭合 → 首块不成立 → 非坏、非 frontmatter block」。
- [ ] 1.2 退役 `unterminated` 死类别：docstring 的 `category ∈ unterminated|duplicate-key|out-of-domain|bad-type|tab-indent` 移除 `unterminated`；同步 A5/emit reason 相关注释若提及 unterminated 则订正。
- [ ] 1.3 grep `unterminated` 全库确认无任何**产生路径**（仅剩历史注释或零残留），作为 1.1/1.2 完成验证。
- [ ] 1.4〔grill-amendment Q2〕 `ship_gate.py` 头注释「已知不覆盖」登记归档杂交盲区：「首行 `---` 无闭合 × 正文独占一行 inline PASS 锚」→ 归档回退 inline 可判假 pass，但无 producer 产出（目标态 producer 不写 inline、旧 producer 首行 `#`），须手工伪造归档=显式越权（adr/0008/0011）。注明目标态论证依据。

## 2. T75 — live inline 死代码删除〔Scenario: 解析半场退役边界〕

- [ ] 2.1 删函数 `anchors_in`、`pick_exclusive`（Task6 已从 `decide()` 摘除，仅剩 test 引用孤儿）。
- [ ] 2.2 删常量 `ANCHOR_DESIGN`、`ANCHOR_CR_PASS`、`ANCHOR_CR_BLOCKED`；`ALL_ANCHORS` 列表收缩（去这三项）。
- [ ] 2.3 **保留边界核实**〔Scenario: 归档旧 inline 锚 dual-read 永久兼容〕：`ANCHOR_VERIFY_PASS` / `ANCHOR_VERIFY_FAIL`（`archived_verify_state` L202/L205 真用）、`_line_scoped_hits`（归档 dual-read 现役唯一调用方）**MUST NOT 删**——删除前 grep 各符号引用点确认仅归档路径 + test 在用。
- [ ] 2.4 删除 2.1/2.2 死符号在 `sdflow-ship/tests/` 里对应的孤儿测试（仅测死符号存在性/行为、无其它断言价值的用例）。

## 3. 测试与回归〔TG-18；Scenario 全覆盖〕

- [ ] 3.1 新增回归：喂「首行 `---` + 全文无第二个 `---`」文本 → 断言 `parse_ship_gate_frontmatter` 返回 `({}, None)`；并加 live 侧集成断言（该报告作 spec-review-report → REFUSE_START(3)、作 verify-report → 不 emit UNKNOWN(6)），坐实不硬崩。
- [ ] 3.2 原断言 `unterminated` 的既有用例（若存在于 `test_frontmatter_parse.py` 等）改断言 absent（`({}, None)`）——保留输入、改期望。
- [ ] 3.3 归档 dual-read 不回归：跑既有 `test_frontmatter_archived.py` / 88 归档兼容用例，确认 `ANCHOR_VERIFY_PASS/FAIL` + `_line_scoped_hits` 删除清理未波及、SHIPPED 判定不变。
- [ ] 3.4 收口验证：grep 死符号（`anchors_in`/`pick_exclusive`/`ANCHOR_DESIGN`/`ANCHOR_CR_PASS`/`ANCHOR_CR_BLOCKED`）在源码 + 测试**零残留引用**；`pytest sdflow-ship/tests/` 全绿。
- [ ] 3.5〔grill-amendment Q2；Scenario: 归档漏闭合 frontmatter 目标态 fail-safe〕目标态归档回归：喂「首行 `---` 无闭合 + 正文无 inline 锚」的归档 verify-report（模拟 producer 迁后漏闭合）→ 断言 `archived_verify_state` 判 `none`（回退 inline 扫空、不 SHIPPED）；对照断言「首行 `---` 无闭合 + 正文有独占一行 inline PASS 锚」杂交形态判 pass（记录其为已登记越权盲区、非正常可达）。

## 测试覆盖图（TG-18）

```
code path                                    → 测试类型
─────────────────────────────────────────────────────────────
parse: 首行 --- 无闭合 → ({}, None)          → 单元回归 (3.1a)
live: 无闭合报告 → REFUSE_START(3)/不 UNKNOWN → 集成 (3.1b)
parse: 原 unterminated 输入 → absent          → 单元(改期望) (3.2)
archived_verify_state: inline dual-read 兼容  → 归档回归(既有) (3.3)
archived: 漏闭合 frontmatter(无 inline) → none → 目标态归档回归 (3.5)
死符号删除 → 零残留引用 + 全绿                 → grep 门 + 全量 pytest (3.4)
─────────────────────────────────────────────────────────────
保留未变（不测新，回归护）: 首块成立后坏 → UNKNOWN(6)、重复键 → UNKNOWN、
                          归档 frontmatter 读、命名空间/复选框完成判据
```
