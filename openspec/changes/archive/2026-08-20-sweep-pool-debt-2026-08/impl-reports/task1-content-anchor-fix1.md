# Task 1 fix1 — 补齐双轴审发现的三条缺失测试

Task 1（ship_gate 内容锚重写）实现代码本身两轴审已确认正确，不改产品代码。本轮只补测试。

## 1. [Critical] 归档 40-hex frontmatter 报告 → SHIPPED 回归 + 变异证明

- **新增**：`sdflow-ship/tests/test_gate_terminal.py::test_archived_legacy_40hex_frontmatter_shipped`
- 覆盖 spec Scenario「归档报告旧 40-hex 锚不阻断 SHIPPED」
  （`openspec/changes/sweep-pool-debt-2026-08/specs/spec-workflow/spec.md:288-296`）：
  归档目录 `verify-report.md` 携 **frontmatter**（非旧 inline HTML 锚）+ 40-hex `reviewed_sha`
  （无 `reviewed_manifest`，即迁移前旧格式）+ `verify: PASS` → gate 判 `SHIPPED`。
  区别于 `test_gate_terminal.py` 既有的 `mk_archive()` fixture（只用 inline 锚
  `<!-- ship-gate: verify=PASS -->`，走 absent→inline dual-read 分支）——本用例走的是
  `archived_verify_state()` 的 frontmatter 优先分支（`state, err = parse_ship_gate_frontmatter(out)`；
  `"verify" in state` 即采信，不校验 `reviewed_sha` 格式）。
- **Mutation 证明**：在 `ship_gate.py::archived_verify_state` 的 frontmatter 采信分支前插入
  `len(reviewed_sha) != 64` 校验（模拟"归档读点也执行 64-hex 校验"这一违反 spec 的实现）：
  - 变异后：`test_archived_legacy_40hex_frontmatter_shipped` 从 `code==0/SHIPPED` 变为
    `code==6`（`assert 6 == 0` 断言失败），确认测试真锁住了「archived 读点不因 reviewed_sha
    格式判坏 frontmatter」这个不变量。
  - 复原代码后重跑，`test_gate_terminal.py` 13 例全绿。

## 2. [Important] `anchor_writeback.py` 执行级单测

- **新增文件**：`sdflow-ship/tests/test_anchor_writeback_exec.py`（此前该脚本零执行级覆盖，
  `test_anchor_contract.py` 只做文本层字符串断言）。直接 `import anchor_writeback as aw` 并调用
  `aw.main(argv)`（非 subprocess，便于 `capsys` 断言 stderr 与 `pytest.raises(SystemExit)`）。
  5 条用例：
  1. `test_clean_tree_write_anchor_roundtrip` — 干净树正常写入，round-trip：
     `base64.b64decode(reviewed_manifest)` 的 sha256 == `reviewed_sha`（64-hex）。
  2. `test_dirty_watch_set_rejects_write` — 监视集内有未提交改动（`design.md`）→
     `SystemExit(!=0)` + stderr 含"未提交改动"；报告文件未被改写（真拒写非写坏值）。
  3. `test_allow_dirty_escape_hatch_permits_write` — 同上脏树，加 `--allow-dirty` → 正常写入。
  4. `test_empty_watch_domain_rejects_write` — 仓内只有 `openspec/` 一个顶层条目，
     `--domain code` 排除 openspec 后监视域为空集 → `SystemExit(!=0)` + stderr 含"空集"。
  5. `test_set_flag_writes_conclusion_and_anchor_atomically` — `--set design_approved=true`
     与锚字段同一次写入落盘（`design_approved is True` 且 `reviewed_sha`/`reviewed_manifest` 齐备）。
- **Mutation 证明**（逐条注入一个针对性 bug，确认对应用例变红，再 `git checkout` 复原）：
  1. 删除 `reviewed_manifest` 的写入行 → roundtrip 用例 `assert "reviewed_manifest" in state` 失败。
  2. 把脏树守卫的 `if not a.allow_dirty:` 恒改 `if False:`（守卫失效）→ 脏树用例
     `DID NOT RAISE SystemExit` 失败。
  3. 把守卫条件恒改 `if True:`（`--allow-dirty` 逃生口失效）→ escape-hatch 用例抛出未预期的
     `SystemExit(1)`（"未提交改动"），测试失败。
  4. 把空集守卫 `if not entries:` 恒改 `if False:`（空集守卫失效）→ 空集用例
     `DID NOT RAISE SystemExit` 失败。
  5. 把 `--set` 解析循环的 `for kv in a.set_fields:` 恒改 `for kv in []:`（丢弃 `--set`）→
     `assert state.get("design_approved") is True` 失败（`None is True`）。
  五次变异均单独注入、单独验证变红、单独 `git checkout -- sdflow-ship/scripts/anchor_writeback.py`
  复原，未叠加。复原后 `test_anchor_writeback_exec.py` 5 例全绿。

## 3. [Minor] rebase 免疫用例

- **新增**：`sdflow-ship/tests/test_gate_freshness.py::test_amend_rewriting_history_without_content_change_stays_fresh`
- 覆盖 brief MUST 项：内容不变、只重写提交历史（`git commit --amend -m "..."` 改 message，
  commit sha 因而变化）→ design 域 MUST 判 `fresh`（`is_stale()` 返回 `(False, "fresh")`）+
  gate 判 `CONTINUE_IMPL`。区别于既有 `_merge_amended`/
  `test_touching_the_report_does_not_move_the_anchor`（那两者改的是**内容**或"报告被触碰"，
  不是"历史被重写、内容原样"）。用例内含前提校准断言
  （`post_amend_sha != pre_amend_sha`，证明 amend 确实换了 commit sha，否则本例失去区分力）。
- **Mutation 证明**：在 `ship_gate.py::is_stale` 的 design 分支里，往 `head_entries` 里额外塞入
  一条 `{b"__head_commit_sha__": (b"100644", b"blob", <HEAD commit sha>)}`（模拟"意外把
  commit sha 混进指纹输入"这一击穿 rebase 免疫的实现回归）：
  - 变异后：`assert (stale, freshness) == (False, "fresh")` 失败为
    `AssertionError: assert (True, 'stale') == (False, 'fresh')`，确认测试真锁住了
    「digest 只认监视集树内容、不认 commit sha」这个不变量。
  - 复原代码后重跑，`test_gate_freshness.py` 全绿。

## 自查

```
/usr/bin/python3 -m pytest sdflow-ship/tests/ -q
........................................................................ [ 21%]
........................................................................ [ 42%]
........................................................................ [ 64%]
........................................................................ [ 85%]
...............................................                          [100%]
335 passed in 43.17s
```

`git diff --stat sdflow-ship/scripts/` 为空——所有 mutation 均在验证后立即
`git checkout` 复原，产品代码（`ship_gate.py` / `anchor_writeback.py`）本轮零改动。

## 未发现产品代码 bug

补测试过程中未发现产品代码真实缺陷；三条测试均在既有实现下自然通过（正例）、
在针对性 mutation 下按预期变红（负例/变异证明）。
