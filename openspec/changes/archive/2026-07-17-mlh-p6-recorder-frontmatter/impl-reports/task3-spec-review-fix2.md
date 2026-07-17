# Task 3 Spec Re-review fix2 — legacy marker collision 熔断边界

结论：**PASS**（commit `b5136a04b93b2b228d087b11f0239e3ed9ad2762`；固定范围 `d9d3ebf..b5136a0`；机械输入 `task3-review-package-fix2.diff`，SHA-256 `f3efea53f96a8223efb7e1d69669a588d2c7615b617a35489767ff8f6a3b873d`）。

## 上一轮唯一 Important 复核

### legacy marker collision 精确诊断 — 已修复

- bug/todo `set-status`、`triage` 在 generic marker/ownership gate 前调用 `_preflight_target_legacy_block()`；仅对仍由 legacy row 拥有且存在候选 prose block 的目标执行 `_legacy_block_range()` collision scan。见 `sdflow-buglist/scripts/buglist.py:1154-1162,1342,1417`，todolist 为镜像实现。
- 独立真实 CLI probe（普通 marker）：B1 唯一 legacy block 内含无尾空白的 A7 start/end marker，`set-status B1 --to VERIFIED` exit 2；stderr 同时包含 `file=...`、`id=B1`、`line=12`、`legacy marker collision`，原文件 bytes 不变。
- 独立真实 CLI probe（尾空白 marker）：start 后含 spaces、end 后含 tab，结果同样 exit 2，stderr 四要素完整，原文件 bytes 不变。证明 preflight 与 parser 的 marker grammar 一致。
- 两条 regression 已恢复严格断言，不再只检查宽泛的 `"marker"`：普通 collision 见 `sdflow-buglist/tests/test_task3_frontmatter_writer.py:256-278`，尾空白 collision 见 `:433-449`。

### generic gate 未被绕过 — 已确认

- 独立构造同文件两个 legacy item：目标 B1 block 干净，非目标 B2 block 内含 paired A7 marker。B1 target preflight 通过后，generic `_reject_document_mutation()` 仍以 `marker/ownership 结构非法; cause: marker-only legacy：A7` 非零拒绝，文件 bytes 不变。
- 既有 canonical B1 缺 end marker后再 add B2 的回归也继续通过；target-aware preflight 没有放宽 existing-document fail-closed。
- `_preflight_target_legacy_block` 已纳入 bug/todo TWO_WAY AST roster，自包含镜像边界保持不变。

## Critical

无。

## Important

无。

## Minor

无。

## Verification

- 固定 diff 与 `git diff --binary d9d3ebf..b5136a0` byte-identical；SHA-256 均为 `f3efea53f96a8223efb7e1d69669a588d2c7615b617a35489767ff8f6a3b873d`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task3_frontmatter_writer.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `28 passed`。
- 三组独立 CLI bytes probe：普通 collision、尾空白 collision、非目标坏 marker generic gate；全部满足预期。

上一轮唯一 Important 已闭合，Task 3 Spec 验收通过。
