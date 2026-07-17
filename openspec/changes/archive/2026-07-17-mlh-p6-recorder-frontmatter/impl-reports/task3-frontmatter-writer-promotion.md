# Task 3 — frontmatter writer、overlay promotion 与 marker prose 实现报告

状态：DONE

## 交付结论

- bug/todo `add` 已切到 versioned `sdflow-issues` frontmatter：新 dated 文件写 `mode=canonical`，已有 legacy 文件或仅含 sibling namespace 的共享 envelope 写/补 `mode=overlay`；新 item 不再写 Markdown 总览表 row。
- 索引字段由 canonical JSON object 承载，`|`、CR/LF 与 Unicode 可无损 round-trip；CLI JSON shape 保持兼容。新 writer 使用 `atomic_write_bytes`，既有 BOM、LF/CRLF、外部 namespace、legacy body 与 mode bits 保持在自有 splice 边界之外不变。
- `set-status`/`triage` 按 effective ownership 更新：frontmatter-owned item 只改 canonical index 与 marker history；未 promotion legacy item 从旧 row 构造完整 overlay item，原位给唯一旧 block 套 canonical marker，旧 row、旧属性表和既有 prose bytes 不重写。todo 无块时按需创建 minimal marker block。
- legacy alias promotion 已 canonicalize：孤立 `A007` mutation 成功后写 `A7` frontmatter key/marker/JSON result，同文件 shadow 仍按 semantic key。
- marker 写前守卫覆盖缺块、多候选、损坏 marker 与候选 legacy block 内预存 marker collision；失败保持原文件逐字节不变。连续 promotion 按 `model.items` ownership 分区，避免同文件先提升 B1 后把仍属 legacy 的 B2 误当 frontmatter owner。
- 新 prose 不复制可变 `status/batch`。heading 使用显式单行 title 或 summary 空白折叠后的 display title；summary 各物理行转 blockquote；用户 prose 中精确 marker 独占行 HTML-escape；source/project/history note 走窄 line-safety，合法 pipe 不再被 table-cell guard 误拒。
- 三份 recorder 保持零跨 skill runtime import；`atomic_write_bytes`、document parser envelope 字段、`_reject_line_unsafe` 纳入 THREE_WAY mirror，新增 document splice、marker/prose/promotion helpers 纳入 TWO_WAY mirror。

## TDD 证据

- 首个 canonical bug CLI/raw-bytes 测试先红于旧 `_reject_cell_unsafe`（module 含 pipe/换行被拒），最小 writer 实现后转绿。
- canonical todo 测试同样先红于旧 table-cell guard，随后转绿；legacy bug/todo add 分别先红于“existing dated file 尚不可写”，实现 overlay splice 后转绿。
- bug legacy `set-status` promotion 先红于旧表/属性双写结果，切换 overlay+marker+history 后转绿；todo blockless promotion 先红于 reason 中 pipe 被旧 guard 拒绝，切换 minimal marker writer 后转绿。
- bug `A007` triage 先红于 batch pipe guard，完成 canonical alias promotion 后转绿；todo canonical triage 先红于 `_find_row_file` 找不到 frontmatter item，切换 canonical snapshot mutation 后转绿。
- BOM+CRLF/shared-envelope golden 先红，准确发现 appended prose 混入 lone LF；block renderer 改为沿用 document EOL 后转绿。
- recorder 旧套件首次重基线为 `303 passed, 33 failed, 1 skipped`。逐项确认失败来自旧表双写/pipe reject 断言或不合法的 bug 缺块 fixture；目标态重基线后又暴露并修复同文件连续 promotion ownership 缺陷，最终全绿。

## 验证

- `python3 -m py_compile sdflow-buglist/scripts/buglist.py sdflow-todolist/scripts/todolist.py sdflow-issues/scripts/issues.py`：PASS。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task3_frontmatter_writer.py sdflow-buglist/tests/test_mirror_consistency.py -W error`：`19 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error`：`337 passed, 1 skipped`；唯一 skip 为 Task 5 的 Windows local-disk 实机 smoke。
- `uv run --with pytest pytest -q --disable-warnings`：`1511 passed, 1 skipped in 72.33s`，exit 0。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive`：valid。
- `git diff --check`：PASS。

## 边界与后续

- Windows local-disk 实机 smoke 按既定分工留给 Task 5，不阻塞本 ticket；network/userspace filesystem 与 power-loss durability 仍不在承诺内。
- 本 ticket 未修改 `sdflow-init/assets/workflow/`，未勾选 `tasks.md` checkbox，未创建 `task3-*` checkpoint。
