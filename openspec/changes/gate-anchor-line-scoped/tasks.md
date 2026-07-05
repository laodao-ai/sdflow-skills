# tasks — gate-anchor-line-scoped

> 追溯：R1 = 需求「阶段三编排台账确定性（ship_gate）」MODIFIED——锚检测 MUST 行级整行等值 + fence-aware，**两处解析点（`anchors_in` + `archived_verify_state`）统一到共用核心**（B4）。设计决策 = design.md ADR-1/2/3/4〔grill-amendment Q1/Q2〕。
> commit 用命名空间格式：`bash ~/.sdflow/hack/checkpoint-commit.sh gate-anchor-line-scoped:task<N>-<slug> "<msg>"`（gate 主锚契约）。

## 1. 抽文本级核心 + `anchors_in` 改走它（design ADR-1/2/4）

- [ ] 1.1 [TDD] 写失败测试（新 `test_gate_anchor_scope.py`）：**内联提及不命中**——写一个 `spec-review-report.md`，正文含一行描述句 `拍板后才写 \`<!-- ship-gate: design-approved -->\`（当前未获批）`（锚内联在句中、行内反引号），断言 `anchors_in(path, ["<!-- ship-gate: design-approved -->"]) == []`（B4 活体复现文本）
- [ ] 1.2 [TDD] 写失败测试：**代码块内锚不命中**——报告含 \`\`\` 围栏，围栏内独占一行放锚字面，真实结论区无锚，断言 `anchors_in` 返回 `[]`（ADR-2）
- [ ] 1.3 [TDD] 写正例测试：**独占一行锚命中**——报告结论区一行只有 `<!-- ship-gate: design-approved -->`（前后可有空白），断言命中；`verify=PASS` 独占一行同理命中
- [ ] 1.4 [TDD] 写冲突回归测试：`verify=PASS` 与 `verify=FAIL` 各独占一行并存 → `anchors_in(path, [PASS, FAIL])` 返回二者（保 ADR-3 多命中，下游 UNKNOWN 冲突判定不破）
- [ ] 1.5 实现：抽文本级核心 `_line_scoped_hits(text, candidates)`（逐行 `strip()` 等值 + `line.lstrip().startswith("```")` fence 翻转跳过、返回按 `candidates` 原序去重），改写 `anchors_in`（`ship_gate.py:198-203`）读文件后调核心；1.1-1.4 转绿
- [ ] 1.6 运行 `pytest sdflow-ship/tests/test_gate_anchor_scope.py -v` 全绿

## 2. `archived_verify_state` 折入共用核心（design ADR-4 · grill Q1）

- [ ] 2.1 [TDD] 写失败测试：造一份 archived `verify-report.md` 文本，正文**描述性提及** `<!-- ship-gate: verify=PASS -->`（内联句 / 代码块内）但**无真独占 PASS 锚**，断言 `archived_verify_state` 判 **`none`**（非 `pass`）——旧裸子串会误判 `pass` → 假 SHIPPED，此负例先红
- [ ] 2.2 [TDD] 回归测试：真 archived verify-report（PASS 独占一行）→ `archived_verify_state` 判 `pass`；PASS+FAIL 各独占一行并存 → 判 `conflict`（三态逐字不变）
- [ ] 2.3 实现：`archived_verify_state`（`ship_gate.py:143`）把 `X in out` 裸子串改为 `hits = _line_scoped_hits(out, [PASS, FAIL]); has_pass = PASS in hits; has_fail = FAIL in hits`；`conflict`/`pass`/`none` 分派逐字不变；2.1/2.2 转绿
- [ ] 2.4 回归：`test_gate_terminal.py` 中消费 `archived_verify_state` 的 SHIPPED/空壳 fail-safe 用例逐字不变保持绿（真锚仍命中，空壳仍 fail-safe）

## 3. 端到端门禁回归 + 契约同步

- [ ] 3.1 [TDD] 端到端负例：构造一个 change 目录，其 `spec-review-report.md` **仅**含描述性锚提及（无独占锚行）、无 tasks 产物，跑 `decide()` 断言 `REFUSE_START`（exit 3，未过设计门）——证 B4 盘面在 gate 顶层已堵（非仅单元层）
- [ ] 3.2 回归：既有设计门/归档终态用例（`test_gate_terminal.py` 及任何消费 `anchors_in`/`archived_verify_state` 的用例）逐字不变保持绿——真锚（模板独占一行）在新实现命中，pre-flight/SHIPPED 路径行为不变
- [ ] 3.3 `ship_gate.py` 头注释契约表：锚检测语义补一句「机判锚 MUST 独占一行（行级等值，忽略 \`\`\` 代码块），两处解析点（anchors_in / archived_verify_state）共用 `_line_scoped_hits`——描述性提及/文档示例不触发」；「已知不覆盖」追加两条：①多行 HTML 注释内嵌锚不解析（人为构造，显式越权同权级）②未闭合 fence 吞真锚→失败到安全侧（不做 unbalanced→UNKNOWN，见 design Non-Goals）
- [ ] 3.4〔锚检测契约测试〕新增/增补契约测试：把三模板真产的锚行样本 ↔ `_line_scoped_hits` 命中双向钉死（模板若把锚与它文同行输出则测试变红报警，防假设失效静默回归）

## 4. 全量回归 + 收敛

- [ ] 4.1 `pytest sdflow-ship/tests/` 全绿 + 仓级 `pytest` 无回归（当前 350 基线不降）
- [ ] 4.2 收敛：spec delta（`specs/spec-workflow/spec.md` MODIFIED 需求）随 change，archive 时由 sdflow-done 同步进主 `openspec/specs/spec-workflow/spec.md`；buglist **B4 → FIXED**（evidence = 本 change + 测试名）

## 测试覆盖图〔TG-18〕

```
  code path                                    测试类型                 文件
  ─────────────────────────────────────────────────────────────────────────────
  _line_scoped_hits 内联提及不命中         →  pytest 单元(临时报告文件)   test_gate_anchor_scope.py(新)
  _line_scoped_hits 代码块内锚不命中       →  pytest 单元                 test_gate_anchor_scope.py(新)
  anchors_in 独占锚命中/多命中(冲突)       →  pytest 单元 + 冲突回归       test_gate_anchor_scope.py(新)
  archived_verify_state 描述性 PASS→none   →  pytest 单元                 test_gate_anchor_scope.py(新)
  archived_verify_state 真 PASS→pass/冲突  →  pytest 回归                 test_gate_anchor_scope.py(新)
  decide() B4 盘面顶层判 REFUSE_START      →  pytest 集成(change 目录)     test_gate_anchor_scope.py(新)
  设计门/归档终态既有路径                  →  pytest 回归                 test_gate_terminal.py(既有)
  模板锚样本 ↔ _line_scoped_hits 命中契约  →  pytest 契约                 test_anchor_contract.py(增)或新
```
