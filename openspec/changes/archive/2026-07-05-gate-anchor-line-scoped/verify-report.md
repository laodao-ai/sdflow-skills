# verify-report — gate-anchor-line-scoped

- 日期：2026-07-05
- change：gate-anchor-line-scoped

## 结论：PASS

<!-- ship-gate: verify=PASS -->

代码真实实现了 tasks.md / specs 的每条要求，逐条附可机验证据锚点，全量测试实证通过（sdflow-ship 105 passed / 仓级 368 passed，基线 350 不降）。

## 逐需求核对表

| 需求 / ADR | 代码出处 file:行 / 测试名 | 状态 |
|---|---|---|
| ADR-1/2/4 抽文本级核心 `_line_scoped_hits(text,candidates)->(hits,unbalanced)`，行锚定 + fence-aware | `ship_gate.py:214-231`（`line.strip() in cand` + `line.lstrip().startswith("```")` 翻转 + 返回 `(hits, in_fence)`） | ✅ |
| ADR-1/2 `anchors_in` 改走核心（读文件后调） | `ship_gate.py:234-240`（`return _line_scoped_hits(text, candidates)[0]`） | ✅ |
| ADR-4 `archived_verify_state` 折入共用核心（不再裸子串） | `ship_gate.py:156`（`hits, unbalanced = _line_scoped_hits(out, [PASS,FAIL])`），三态 conflict/pass/none 逐字保留 :159-162 | ✅ |
| 内联提及不命中 / 代码块内不命中 / 独占行命中 / 冲突多命中 | `test_gate_anchor_scope.py::test_inline_mention_not_hit`、`::test_fenced_anchor_not_hit`、`::test_standalone_anchor_hit`、`::test_conflict_multi_hit` | ✅ |
| ADR-4 archived 描述性 PASS→none（git fixture 端到端）+ 真 PASS→pass / 冲突→conflict | `::test_archived_descriptive_pass_none`、`::test_archived_true_pass_and_conflict`、核心单元 `::test_core_descriptive_pass_not_hit` | ✅ |
| ADR-5 未闭合 fence：`_line_scoped_hits` 回报 unbalanced；`pick_exclusive` 消费→UNKNOWN（reason 含「未闭合 fence」） | `ship_gate.py:259-262`；`::test_pick_exclusive_unbalanced_unknown`（断言 `EXIT_UNKNOWN` + reason 含「未闭合 fence」，区分 conflict 分支） | ✅ |
| ADR-5 `archived_verify_state` 消费 unbalanced→none（保守不 SHIPPED） | `ship_gate.py:157-158`；`::test_archived_unbalanced_none` | ✅ |
| ADR-6/A3 `tg02_hit` 头部区域 fence-aware + 声明行匹配（`in_fence` + `s.startswith("〔TG") and "〔TG-02" in s`） | `ship_gate.py:277-301`；`test_gate_impl_progress.py::test_tg02_body_mention_not_hit`、`::test_tg02_header_declaration_hit`、`::test_tg02_fenced_heading_in_header_still_hits`、`::test_tg02_fenced_example_in_header_not_hit`、`::test_tg02_header_descriptive_mention_not_hit`（3+ fence-aware 回归） | ✅ |
| 契约测试 corpus 锚样本双向钉死 + `checked>0` 空转兜底 | `::test_contract_archived_corpus_anchor_hits`（`assert checked > 0` :152，样本源=归档 corpus 非 SKILL 展示块） | ✅ |
| B4 端到端 gate 顶层判 REFUSE_START | `::test_decide_b4_board_refuse_start`（仅描述性锚 → exit 3 / verdict REFUSE_START） | ✅ |
| T32 命名空间过滤前缀放宽 `startswith("checkpoint(")`（否则命名标签被跳过） | `ship_gate.py:345-353`（可选命名空间捕获组 `TAG_RE` :274 + `ns != change` 排除） | ✅（关联需求，回归绿） |
| 头注释契约表 / 已知不覆盖（多行 HTML 注释、`~~~`/带标签围栏） | `ship_gate.py:67-79` 头注释块 | ✅ |
| 全量回归：`pytest sdflow-ship/tests/` 全绿 + 仓级不降 | 实测 sdflow-ship 105 passed；仓级 368 passed（≥350 基线） | ✅ |

## 缺口清单

- 核心 FAIL：无。
- Minor / deferred：task 3.5（`sdflow-code-review/SKILL.md:150-151` 展示块锚行尾注消歧义微调）在 tasks.md 中已标「非本 change 硬需求，defer 亦可」，属 skill 文档收紧，不影响 gate 核心功能，判 PASS 注明。

## 实证命令

- `python3 -m pytest sdflow-ship/tests/ -q` → 105 passed
- `python3 -m pytest sdflow-ship/tests/test_gate_anchor_scope.py sdflow-ship/tests/test_gate_impl_progress.py -v` → 39 passed
- `python3 -m pytest -q`（仓级）→ 368 passed
