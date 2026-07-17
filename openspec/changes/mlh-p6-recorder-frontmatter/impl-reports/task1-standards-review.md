# Task 1 Standards Review — strict dual-reader

结论：**PASS（HEAD `6c4f0f9`，最终 re-review）**

## 轮次审计

### 第一轮 — FAIL

- Critical：overlay `A007/A7` 按 literal shadow，产生两个 effective item。
- Important：indented ownership 变体回退 legacy；prose table 被误计 legacy region；scan 未收敛为一次 document parse；fatal diagnostic 缺 path。
- Minor：坏输入矩阵与三 recorder parity/golden 不足。

### 第二轮 — FAIL

- 第一轮 semantic shadow、跨文件 fatal、原 ownership 变体、parse-count、path diagnostic 与三向 parity 已闭合。
- Critical：canonical prose 的 8-column 示例表仍被解析为 ghost machine item。
- Important：fenced `## 状态总览` false fatal；external opaque value 提及 `sdflow-issues` false fatal。

### 第三轮 — PASS

- `sdflow-buglist/scripts/buglist.py:284-320,544-581,659-730`：legacy region 由 fence-aware、heading-bound `_legacy_table_sections()` 判定；canonical prose 不再进入 legacy rows/effective snapshot。
- `sdflow-buglist/scripts/buglist.py:209-249`：ownership 检查收窄到 column-0 变体与 orphan indented owner；合法 external indented opaque value 可含 `sdflow-issues` 文本。
- `sdflow-buglist/scripts/buglist.py:659-730`（三份镜像）：parser 直接生成 `effective_items/effective_occurrences/problems`；canonical prose、fenced overview、opaque sibling、overlay semantic alias 的三 recorder snapshot 完全一致。

### 最终轮 — PASS

- `sdflow-buglist/scripts/buglist.py:209-249`（三份镜像）：ownership 判定进一步收窄到顶层 quoted/explicit/key-colon 变体与无 owner 的 indented 变体；external same-line value、indented opaque value 和 comment 中的普通文本不再误杀，原 fail-closed ownership 样例仍保持 fatal。
- `sdflow-buglist/tests/test_frontmatter_dual_reader.py:229-468`：三向矩阵现覆盖 canonical golden、pure legacy、overlay semantic shadow、effective occurrences/problems、marker corruption、encoding/EOL、surrogate、字段集合与枚举。
- 三 recorder 定向全套 `298 passed`，无 warning。

## Critical

无。

## Important

无。

## Minor

无。

## Verification

- 第二轮三个对抗样例逐项复现：8-column prose 仅返回 frontmatter `B1`、`problems=[]`；fenced 状态表示例不再触发 mode mismatch；external opaque mention 正常解析。
- parser-direct parity：buglist/todolist/issues 对 canonical prose、fenced overview、opaque sibling、overlay `A007→A7` 的 effective snapshot 相等。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_frontmatter_dual_reader.py sdflow-buglist/tests/test_mirror_consistency.py` → `29 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `298 passed`。
- backend/embedded domain checklist：无命中，未作领域清单假通过。
