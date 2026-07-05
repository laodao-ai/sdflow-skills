# hand-off — gate-anchor-line-scoped

> 收尾交接（verify 之后 / archive 之前）。change 目的：把 ship_gate.py 的**子串检测**从"整体 `x in text`"收紧为行级/头部声明式，堵住"描述性提及被误判为真锚/真触发"的假阳（B4 元 bug + 2 轮 dogfood）。

## ✅ 完成了什么（每条附机验锚）

- **`_line_scoped_hits` 核心 + `anchors_in` 行锚定 + fence-aware**（ADR-1/2）— `ship_gate.py:214-231/240`；`test_gate_anchor_scope.py::test_inline_mention_not_hit`/`test_fenced_anchor_not_hit`/`test_standalone_anchor_hit`。
- **`archived_verify_state` 折入共用核心**（ADR-4）— `ship_gate.py:156`；`test_archived_descriptive_pass_none`（旧裸子串判 pass→假 SHIPPED，新判 none）。
- **未闭合 fence → 互斥锚对保守判定**（ADR-5，codex OV-2 抓的真回归）— `pick_exclusive`→UNKNOWN(reason 含"未闭合 fence")/`archived_verify_state`→none（`ship_gate.py:259-262/157`）；`test_pick_exclusive_unbalanced_unknown`/`test_archived_unbalanced_none`。
- **`tg02_hit` 头部区 fence-aware + 声明行匹配**（ADR-6/A3，2 轮 dogfood + 独立冷主审 tg02 安全 bug）— `ship_gate.py:277-301`；`test_gate_impl_progress.py` 3 条 fence-aware 回归（假阴嵌入式漏 SOP / 假阳示例 / 描述提及）+ 4 既有。
- **B4 元 bug → FIXED**（buglist B4，evidence=本 change）：设计门/SHIPPED 假过的根因（`anchors_in` 子串误配描述句）根治。`test_decide_b4_board_refuse_start` 端到端判 REFUSE_START。
- **契约测试 + 头注释 + 空转兜底**（Task5 + 代码审加固）— `test_contract_archived_corpus_anchor_hits`（钉归档语料 15/15 + `checked>0`）；头注释「已知不覆盖」5 条。
- verify=PASS（opus 强档，105 sdflow-ship + 仓级 368 绿，基线 350 不降）。code-review=pass（多镜 + codex，独立冷主审抓 tg02 fence-aware 安全 bug 已修）。

## ⏳ 未完成 / 延后

**批次 `gate-anchor-line-scoped`**（PLANNED，见 `openspec/issues/batches.md` + `INDEX.md`）：
- **T43**（本 change 代码审 defer，OV-code-1）：producer 模板（sdflow-code-review/spec-review SKILL 报告格式展示块）的机器锚收紧为独占 bare line——现带反引号/同行尾注，与真产报告不一致；防未来报告照抄模板致 gate 行锚定不认锚。**实证当前 15/15 真报告干净、非紧急**；本 change 正交（改的是 gate parser，非 producer 文档）。
- **T41**（评审结束输出可点击报告链接）/ **T42**（文档多图表、人机读分离）：本 session 提出的**跨切工作流 UX 改进**，与 gate-anchor 无直接关系，归入本批次仅因发现于本 session；建议单独评估。

**别的批次残留（不在本 change scope）**：
- **`checkpoint-tag-single-source` 批次**（PLANNED，P1★）：B4 本次已 FIXED，剩 **T37/T38**（delta spec Scenario 措辞/占位符用词澄清，纯文档 prose）。

**过程注记（2 轮 dogfood，值得记）**：tg02_hit 修法迭代了 3 次——Q3=A1 `〔TG-02` → 加冒号仍被正文示例假阳 → A3 头部区域 → 独立冷主审再抓头部扫描**非 fence-aware**（假阴嵌入式漏 SOP）。教训：改"讨论自身检测逻辑的 gate"时，proposal 正文含示例声明串是必然，任何整体子串都不够；且新增解析路径必须复用同文件既有 fence 口径（`_line_scoped_hits`/`_parse_plan`），别裸循环重实现。

## ▶ 下一阶段建议

1. **`checkpoint-tag-single-source` 批次收尾**（P1★但仅剩 T37/T38 纯文档）：T37/T38 是 delta spec Scenario 措辞澄清，轻量，可与其它文档清理合并成一个小 cleanup change，或 archive 时顺手。B4 已闭，该批次去掉 B4 后价值降为 P2。
2. **T43（producer 模板收紧）**：低优先，非紧急（真报告干净）；可与"评审报告格式规范化"一并做。
3. **T41/T42（工作流 UX）**：与本 gate 线无关，独立排期评估。
4. 本 change 已 ship（archive + merge main）；tg02 fence-aware 安全修使嵌入式 change 的强制 SOP 判定回到可靠。
