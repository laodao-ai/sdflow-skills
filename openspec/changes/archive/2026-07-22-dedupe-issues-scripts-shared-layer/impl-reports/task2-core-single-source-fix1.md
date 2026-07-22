# Task 2 双轴审 fix1 — core single-source 去重

Change: `dedupe-issues-scripts-shared-layer` · Task 2 re-review 发现修复
文件主战场：`sdflow-issues/scripts/sdflow_issues_core/__init__.py` + `sdflow-issues/tests/`

全套件基线（改前）：**2100 passed, 8 skipped, 3 xfailed**（146.63s）。
本次为纯重构 + 测试诚实化，外部行为（stdout JSON / 落盘字节 / 退出码）零变化。

---

## Important-1 — 4 个策略函数 pool-agnostic 写头/写尾去重

`_bug_set_status` / `_todo_set_status` / `_bug_triage` / `_todo_triage` 各自逐字带一段
overlay-model 构建头 + 近逐字写尾。抽取为两个 **pool-agnostic** 公共 helper，4 处复用。
genuine 分岔（bug FIXED 门禁 / todo 惰性建块 + require_marker 动态算）留在中段策略里不动。

抽取的 helper 签名：

```python
def _prepare_overlay_model(document, pool, canonical, item):
    """拷贝既有 overlay model（无则建 minimal overlay 骨架），深拷 items 后置入更新后的 item。
    差异经参数 pool/canonical/item 注入，无 pool 值分支。"""

def _commit_mutation(document, model, insertions, path, pool, canonical, require_marker, output):
    """splice → render → 关系自检 → 原子落盘 → stdout JSON。
    output 为调用方预建的结果 dict（各命令 JSON 形态不同，此处只序列化打印）。"""
```

- **写头**：原 5 行 `model = dict(...); model["items"] = dict(...); model["items"][canonical] = item`
  → `model = _prepare_overlay_model(document, spec.pool, canonical, item)`（4 处）。
- **写尾**：原 `_splice_body_lines → _render_recorder_document → atomic_write_bytes(_validated_rendered_mutation(...)) → print(json.dumps(...))`
  → `_commit_mutation(document, model, insertions, path, spec.pool, canonical, <require_marker>, <output_dict>)`（4 处）。
- **pool-agnostic 核验**：两 helper 内均无 `"bug"`/`"todo"` 字面分支；pool 差异仍由既有 `PoolStrategy`
  具名字段（`build_block`/`header`/`set_status`/`triage`…）承载。符合 Global Constraint「helper 必须 pool-agnostic」。
- **require_marker 参数化**：set_status（bug/todo）与 bug triage 传 `True`；todo triage 传其动态算出的
  `require_marker` 变量——差异经参数注入，未改判定逻辑。
- **output dict 参数化**：set_status 出 `{id,old,new,file}`；triage 出 `{id,old_status,new_status,batch,file}`。
  由调用方预建（含 `os.path.relpath(path, root)`），helper 只负责 `print(json.dumps(..., ensure_ascii=False))`——
  stdout 字节零变化。

## Important-2 — minimal marker-block 三处字节组装去重

三处（`_promotion_insertions` 内 / `_todo_set_status` / `_todo_triage`）逐字重实现同一 6 行
`<!-- sdflow-issue-block:start … end -->` 字节块，仅 `history` 传参形态（bytes vs tuple）不同。
抽取为单一承重-契约 helper：

```python
def _minimal_marker_block(canonical, item, eol, history):
    """惰性建的 minimal sdflow-issue-block 6 行字节块。history 为**已拼接的字节**
    （tuple 形态调用方先 b"".join(...)）。三处促升路径共用此单一源——格式一变只改此处。"""
```

- `_promotion_insertions`：`history` 是 tuple → 传 `b"".join(history)`。
- `_todo_set_status`：`history` 已是 bytes（`hist.encode()+eol`）→ 直接传 `history`。
- `_todo_triage`：`history` 是 tuple → 传 `b"".join(history)`。

字节拼接顺序、编码（marker=ascii / 标题+summary=utf-8）、eol 用法逐字保留 ⇒ 落盘字节零变化。

## Minor-3（fold）— `_todo_build_block` 内联 render_doc_block → 调共享

原 `if docs: b += "\n**关联文档**：" + "、".join(f"\`{d}\`" for d in docs) + "\n"`
→ `b += render_doc_block(docs)`（与 `_bug_build_block` 一致，消除格式二处副本）。
`render_doc_block` 对空 docs 返回 `""`，且函数顶部已 `docs = docs or []`，故 `if docs` 守卫可去除、行为等价。

## Minor-4（诚实降级 fold）— 终态一致性测试 overclaim docstring + 死代码

`sdflow-issues/tests/test_issues.py` 的 `TestTerminalStatusesCrossScriptConsistency`：

- **(a) docstring 诚实化**：删掉「多处独立硬编码、改一处忘另一处静默漂移」等单一源化（adr/0027）后
  已不成立的宣称；改为诚实描述当前三重护力 ——（a）外部字面锚 `{"FIXED","WONTFIX"}==TERMINAL_STATUSES["bug"]`、
  （b）`⊆ 独立 STATUS_CODES`、（c）cmd_scan 派生用法源锚。并点明「同源断言两侧同源、恒真、护力为零」。
- **(b) 删死代码**：`_inline_literal_sets`（:189）与 `_cmd_scan_nonterminal_literal`（:216）两个正则提取
  static method **确认全仓无任何调用点**后删除（grep 证据见下）。
- **(c) 保留有效锚**：外部字面锚（`test_terminal_sets_match_expected_literal_values`）、
  `⊆ STATUS_CODES`（`test_terminal_sets_are_subset_of_recorder_status_codes`）、
  cmd_scan 派生源锚（`"nonterminal = set(spec.status_values) - set(spec.terminal_set)" in core_src`）全部保留。
- `import re` 保留：文件他处（:1922）仍用 `re.match`/`re.escape`。

死代码 grep 证据（改前）：

```
$ grep -rn "_inline_literal_sets\|_cmd_scan_nonterminal_literal" sdflow-issues/
tests/test_issues.py:189:    def _inline_literal_sets(source_text):
tests/test_issues.py:216:    def _cmd_scan_nonterminal_literal(source_text):
```

仅两处定义、零调用点 ⇒ 确认死代码。

## 配套：源码巡检守卫同步（test_task3_frontmatter_writer.py）

`test_dated_writer_call_graph_has_no_legacy_table_or_text_writer_calls` 原逐字断言 4 个策略函数
源码内含 `atomic_write_bytes(`。写尾抽走后该断言失配（真阳，非回归）——按重构后的真实调用图更新：
负向断言（无 `atomic_write`/legacy 表/文本 writer 调用）全保留；正向断言改为
`"atomic_write_bytes(" in source or "_commit_mutation(" in source`，并加一条对 `_commit_mutation`
本体的传递断言（`atomic_write_bytes(` 在场）——护力等价（仍锁 byte-writer 路径、禁 legacy writer）。

---

## 外部行为零变化确认

- **stdout JSON**：4 个命令的输出 dict 由调用方预建、经 `_commit_mutation` 原样 `json.dumps(..., ensure_ascii=False)`
  打印，字段/顺序/`ensure_ascii` 逐字保留。
- **落盘字节**：`_minimal_marker_block` / `_prepare_overlay_model` / `_commit_mutation` 内部拼接、
  render、validate、write 调用序与参数逐字保留（仅 history 拼接责任移交调用方，等价）。
- **退出码/门禁**：FIXED 根因门、WONTFIX/DONE/WONTDO reason/evidence 门、marker 缺失 fail-closed
  全在中段策略里未动。

## 全套件实际输出（改后）

```
$ /usr/bin/python3 -m pytest -q   # 从仓根
........................................................................ [ 98%]
.......................                                                  [100%]
2100 passed, 8 skipped, 3 xfailed in 154.94s (0:02:34)
```

等价 oracle 保持全绿，与基线 2100 passed 一致 ⇒ 抽取为纯重构，外部行为零变化。
