# Task 4 Fix 2 — rename snapshot provenance

## 结论

已关闭 fix1 复审剩余的全部 C/I/M，改动严格限定于四项：malformed legacy row 的 batch 真值门禁、provenance retry 的 `{old,new}` target relation preflight、scan envelope ID 类型门禁、pure-legacy marker collision 定位诊断。

## 改动

- malformed legacy row 不再用 old/new 字面命中推断安全性。仅当前 8 个标准位置可独立通过 ID、required field、enum/status 校验，且尾随 cells 不含 old/new 时，才允许作为与 retag 无关的 trailing-cell warning；中间插 cell、短行、target key 藏在尾随 cells 等不可证明盘面均在 registry 写前 fatal。frontmatter shadow 的 frozen row 仍跳过 legacy 真值推断。
- relation preflight target 从 `batch == old` 扩为 provenance-matched `{old,new}` owned items；all-old、mixed、all-new 的 canonical/overlay/pure-legacy 均在任何写盘前执行 marker/frontmatter relation gate，合法 all-new retry 仍幂等收敛。
- `validate_scan_envelope()` 先断言 `item[index].id` 是 string，再做 legacy alias/canonical 解析；`null/int/list/object` 均走 `ValueError` 三段式 CLI 诊断，无 traceback，INDEX/batches bytes 不变。
- pure-legacy target 先执行 candidate-aware `_legacy_block_range()`，再执行 document-wide structural gate；完整或部分预存 marker 均报告 target legacy ID、file、line、`stage=preflight` 与原命令，并在写前拒绝。
- 将旧 warning-only 回归 fixture 从不可判的中间插 cell 改为可证明的 trailing cell，使测试继续覆盖允许的 nonfatal boundary，而不放宽目标态门禁。

## TDD 与验证

- RED：新增 18 个核心失败覆盖 ID 错型/CLI、完整与部分 marker collision、all-new/mixed × canonical/overlay/pure-legacy、无 old/new 字面的中间插 cell 与真实 CLI bytes unchanged；另补 target key 出现在 trailing cell 的不可判回归。
- GREEN（定向 + mirror）：`uv run --with pytest pytest -q sdflow-issues/tests/test_task4_rename_snapshot.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `98 passed`。
- 受影响三 skill：`uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `437 passed, 1 skipped`（Windows-only）。
- 全量 functional：`uv run --with pytest pytest -q` → `1611 passed, 1 skipped`。
- 全量 strict：`uv run --with pytest pytest -q -W error` → `1573 passed, 1 skipped, 38 failed`；38 项均为仓内既有 ResourceWarning/PytestUnraisableExceptionWarning 基线：`sdflow-maintain` 37 项、`sdflow-architecture` 1 项，本次触达的 recorder 定向与受影响集合在 `-W error` 下全绿。
- Diff hygiene：`git diff --check` → PASS。

评审 package `task4-review-package.diff` 与 `task4-review-fix1-package.diff` 保持原样，未纳入本修复提交。
