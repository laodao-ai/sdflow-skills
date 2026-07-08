# hand-off — mlh-p5-parser-cleanup

> 阶段三收尾交接（verify 之后、archive 之前产出，随归档留档）。异步人类再入口 + 下阶段种子。

## ✅ 完成了什么（每条锚点已复核存在）

清结 `mlh-p5-gate-frontmatter` 遗留的两条 P5 尾巴（T74/T75），三腿全落、157 tests 绿 0 warning：

- **T74 首行 `---` 无闭合改判 absent**（P0 正确性 + spec 修订）：`parse_ship_gate_frontmatter` 的 `end is None` 分支 `("frontmatter","unterminated")` → `({}, None)`（`ship_gate.py:318-322`）；`unterminated` 死类别退役（docstring 枚举 + grep 源码零残留）；live 侧不再对干净的无闭合报告硬崩 UNKNOWN(6)，走既有无锚语义。
- **T74 live 结构诊断提示**（spec-review Q1=A / ADR-5）：`_unclosed_frontmatter_hint`（`ship_gate.py:464-480`）纯诊断，接入 design/code-review/verify 三读点（`:699/:771/:819`）+ verify stale 分支（`:807`，code-review 自动修 F2）；未改 parse 返回签名（三调用方不受波及）。
- **T74 归档杂交盲区登记**（grill-amendment Q2）：头注释「已知不覆盖」（`ship_gate.py:118-123`）+ 目标态回归测试 `test_archived_unclosed_no_inline_none`/`_with_inline_pass_is_registered_blindspot`。
- **T75 死符号清理**：删 `anchors_in`/`pick_exclusive`/`ANCHOR_DESIGN`/`ANCHOR_CR_PASS`/`ANCHOR_CR_BLOCKED` + `ALL_ANCHORS` 收缩至 verify-only（`:135`）；保留边界 `ANCHOR_VERIFY_PASS`/`ANCHOR_VERIFY_FAIL`/`_line_scoped_hits`（`:133-134/:264`，归档 dual-read 现役）；`test_gate_anchor_scope.py` 外科改写不压垮。
- **测试**：三读点集成 + parse 单元回归 + `test_anchor_set_absent_on_unclosed_frontmatter` 熔断不变量（`test_gate_breaker.py:82`）+ 目标态归档回归 + F2 stale-hint 回归（`test_gate_freshness.py`）；死符号 grep 零残留、三调用方（`:200/:410/:456`）未误删；`pytest -W error` 157 passed / 0 warning。

verify 判定：**PASS**，无核心缺口、无 Minor 缺口（见 verify-report.md，每 ✅ 附机验锚点）。

## ⏳ 未完成 / 延后

本 change 收尾 verify 无 Minor 缺口。code-review（多镜：1 领域 + 2 对抗 + 1 历史 + outside-voice codex）defer 2 项，已入 **todolist（批次 `mechanical-layer-hardening`）**：

- **T77**（spec 整洁性）：delta spec「过渡期 live 未迁 producer 回退 inline」Scenario 迁移窗已闭，宜未来标历史/收敛（终态子句已 governing、无活跃代码冲突，纯整洁性）。
- **T76**（归档盲区硬化后续，**须知**）：冷代码审对抗镜（parse-edge）给出比设计门「仅手工伪造」更锋利的可达性论证——归档「首行 `---` 无闭合 × 正文独占行 inline PASS 锚」杂交形态 → `archived_verify_state` 判 `pass` → D3 短路 SHIPPED（bit-复现为改动前 UNKNOWN(6) → 改动后 SHIPPED(0) 的回归）。**裁决**：此形态已被**设计门显式识别 + 判净负 + 接受**（design.md L136，grill-amendment Q2 + spec-review BR-2；mitigation = 无 producer 产出 + 头注册登记 + 目标态回归测试），实现忠实，阶段三不重开设计门（adr/0004）→ 未 block。但冷镜新增的迁移半成品编辑 / 自指文档可达路径值得未来复评：建议加**非语义** lint/监控扫「归档 verify-report 首行 `---` 无闭合」形态告警（不改 parser 语义、不重开设计门），据此复评「给归档侧特殊 fail-safe」的 ROI（design L121 当前选①绝）。

无被延后的 ≥2 方案决策（code-review 的 F2/F3 修复方案均有客观判据、直接自动修，无 T10 defer）。

## ▶ 下一阶段建议

- **P5 尾巴已清结**——mlh 机械层固化 roadmap 的 P5（recorder 索引→frontmatter，north-star）仍 defer（ADR-0010，本 change Non-Goals 明确不动）。下一阶段按 roadmap 推进 P6 或其它 mlh 腿时，一并评估 T76 的归档盲区 lint/监控（低优先，设计门中立、可独立成小 change）。
- **T77** 可在任一触及 spec-workflow spec 的维护 change 中顺手收敛（spec 整洁性，无紧迫性）。
- **toolkit 源仓提醒**：本 change 改 `ship_gate.py`（bundle 工具），merge + push 后，消费仓需 `sdflow-init update` 才拿到新 gate；本仓 `/sdflow-upgrade` 于新会话激活。
