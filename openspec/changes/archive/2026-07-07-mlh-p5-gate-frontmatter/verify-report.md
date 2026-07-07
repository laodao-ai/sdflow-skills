---
ship-gate:
  verify: PASS
---
# verify 报告 — mlh-p5-gate-frontmatter

**结论：PASS**

日期：2026-07-08 · change：mlh-p5-gate-frontmatter

> 反假✅纪律：每条 ✅ 附一个可机验锚点（测试名 / commit / 文件:行）。核对代码实况，不信复选框。

## 逐需求核对表

| 需求/任务 | 代码出处（文件:行 / 测试名 / commit） | 状态 |
|---|---|---|
| D1 live 4 类读点全退役 dual-read→frontmatter-only（anchors_in/pick_exclusive/peek/anchor_set 熔断均迁 frontmatter） | `ship_gate.py:264` 注释「已从 live decide() 退役」；`decide()`(649-810) 内 grep `anchors_in(`/`pick_exclusive(` 非注释调用 = 0；`live_ship_gate_state`:469 存在，decide 唯一 live 读入口 | ✅ |
| D2 手写解析器只认文件首块 + 零 `import yaml` | `parse_ship_gate_frontmatter`:291-379（首行去 BOM `﻿`:304、`lines[0].strip()!="---"`→absent:307、下个 `---` 界块:310-316）；`test_no_import_yaml`（ast 断言）passed；grep 源码 `import yaml` 仅出现在 282 行注释、无真实 import | ✅ |
| D3 坏≠无键退出码映射（live 坏→UNKNOWN(6)/归档坏→none/absent→无锚语义） | `_fail_closed_on_bad`:462 emit UNKNOWN(6)；`live_ship_gate_state`:469；`archived_verify_state`:196-198 坏→'none' fail-safe；`test_frontmatter_parse`/`_live_read`/`_archived` passed | ✅ |
| D4 共用 parse_ship_gate_frontmatter + 归档 dual-read + F2 `_line_scoped_hits` 永久保留 | `archived_verify_state`:196 调 `parse_ship_gate_frontmatter`（frontmatter 优先）→ absent 回退 `_line_scoped_hits`:202（inline 半场保留）；`_line_scoped_hits`:260-279；注释 14/89 声明永久保留 | ✅ |
| A2 首块严格：正文横线/锚提及不参与 | `parse_ship_gate_frontmatter`:304-316 `splitlines()`+首行界定；直接探测运行确认正文 `---` 块不被当 frontmatter；named 测试 passed | ✅ |
| D5 同字段/顶层重复键→UNKNOWN（非取最后一个） | `:334-335`（顶层 ship-gate 重复→duplicate-key）、`:370-372`（同名字段计数>1→duplicate-key）；named test `duplicate_key` passed | ✅ |
| 三 producer frontmatter 模板列0可解析 | `test_producer_frontmatter_parseable` passed（真从 SKILL.md 抽取喂 parser）；`sdflow-spec-review/SKILL.md:115`、`sdflow-done/SKILL.md:81/88`、`sdflow-code-review/SKILL.md:170/177` 均 `ship-gate:` 顶格 + merge 规则 | ✅ |
| 自身报告迁 frontmatter dogfood 不 REFUSE on itself | 只读跑 `ship_gate.py --change mlh-p5-gate-frontmatter` → `RUN_VERIFY`(exit 0)，非 REFUSE_START（证 design_approved+code_review 从 frontmatter 读出）；`spec-review-report.md:1-4` `design_approved: true`、`code-review-report.md:1-4` `code_review: pass` 均列0 | ✅ |
| code-review crfix 5 组真闭合（commit 15351f0） | 直接探测 parser：嵌套字段`note.design_approved`→state={}(不假过门,FIX-1)/`ship-gate: []`→bad-type(FIX-2)/YAML `#`注释→verify:PASS 正确剥离(FIX-3)/tab 顶层键→tab-indent(FIX-4)；commit 15351f0 含 74 行改 + 4 测试文件 | ✅ |
| A3 fail-closed 退出码不歧义（UNKNOWN vs 无锚语义分治） | `_coerce_ship_gate_value`:385、越域`:376`out-of-domain、类型不符`:374`bad-type → 均 UNKNOWN(6)；absent→调用方走既有语义 | ✅ |
| A5 fail-closed reason 携字段名+失败类别 | `_fail_closed_on_bad`:462-464 reason 含 `字段={field} 类别={cat}`；`test_frontmatter_fail_closed` passed | ✅ |
| 归档 dual-read 行为测试（旧 inline / 新 frontmatter / 坏→none / 未闭合 fence 保守） | named `archived_inline`/`archived_frontmatter`/`archived_unclosed` passed；`archived_verify_state`:196-208 | ✅ |
| live 正文提及锚字面免疫（B4/B5 根治） | named `live_body_mention` passed；live 只读 frontmatter，正文平面不参与 | ✅ |
| 全仓回归全绿 | `pytest sdflow-ship/tests/ -q` = **154 passed**；全仓 `pytest -q` = **672 passed**（无 B5 失败） | ✅ |
| tasks 0.1-6.2 全部 | 上述锚点覆盖；`openspec validate` 由主 session 确认 | ✅ |

## 缺口清单

**核心缺口（FAIL）**：无。

**Minor / deferred（可接受，非缺口）**：
- **T74**（裸 `---` 首行 robustness 增强）— 已登记延后项，非本 change 缺口。当前解析器对首行严格要求 `---`，已满足 spec A2；robustness 增强属 nice-to-have。
- **T75**（死代码清理：`anchors_in`/`pick_exclusive` 退役后仅 test-referenced 孤儿）— 已登记延后项。源码 `:264` 注释已声明其为「test-referenced 孤儿，不再运行时共用」，功能正确、无门禁影响，清理属 Minor。

## 结论

PASS — D1-D4 五铁律核心读点全迁 frontmatter、手写 stdlib 零 yaml、坏≠无键退出码映射、归档 dual-read + F2 inline 永久保留均有机验锚点；三 producer 模板列0可解析、自身报告 dogfood 闭环（RUN_VERIFY 非 REFUSE）、crfix 5 组直测闭合；sdflow-ship 154 passed、全仓 672 passed 无 B5 失败。T74/T75 为已登记 deferred，非缺口。
