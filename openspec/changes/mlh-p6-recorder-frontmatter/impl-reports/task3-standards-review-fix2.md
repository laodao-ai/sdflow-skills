# Task 3 fix2 Standards Re-review — legacy marker collision diagnostic

结论：**PASS（commit `b5136a0`，固定复核区间 `d9d3ebf..b5136a0`）**

本轮只复核 fix2 新增回归。未发现新的 Critical / Important / Minor；上一轮已 PASS，既有 T153 文档债不在本轮重复展开。

## 新增回归复核

### 1. target-aware preflight 未放宽 generic marker gate — PASS

- `set-status` / `triage` 在 `_find_item_document()` 之后、`_reject_document_mutation()` 之前调用 `_preflight_target_legacy_block()`。preflight 只在目标仍由 legacy row 拥有且存在同 semantic ID 的 prose block 时复用 `_legacy_block_range()`；frontmatter 已拥有目标或没有目标候选块时不改变原 gate 的判定。
- `_preflight_target_legacy_block()` 不捕获异常、不删除 `document["problems"]`、也不改变 `_reject_document_mutation()`；preflight 正常返回后，generic gate 仍无条件执行。`add` 路径未接入 preflight，继续直接受 generic gate 保护。
- 独立纯内存反向 probe 构造“B1 目标块干净、B2 非目标块含 B9 marker”的 legacy document：B1 preflight 正常返回，随后 generic gate 仍以 `marker/ownership 结构非法; cause: marker-only legacy：B9` 拒绝。说明 fix2 只是把目标块碰撞提前为更精确诊断，没有形成 generic gate bypass。

### 2. 精确诊断与严格测试没有假绿 — PASS

- 独立 probe 对 B1 候选块内的 B9 marker 调用 preflight，实际得到单条批准诊断：`ERROR: file=/probe/target.md legacy marker collision; cause: id=B1 line=12; fix: 删除或转义候选块内预存 marker 后重试`。file、目标 ID、行号与 collision 原因来自同一异常，不是多个无关 stderr 片段碰巧满足 substring 断言。
- 两条真实 CLI regression 分别覆盖普通 marker 与带尾空白 marker；都要求非零退出、file、`id=B1`、`line=`、`marker collision`，并比较写前/写后 bytes 完全一致。普通 marker 用例还锁定 stdout 为空。断言针对 fix2 的目标态诊断，不会只凭 generic `marker` 文案假绿。
- 既有 canonical end marker 缺失后执行 `add` 的回归仍保留并通过，继续证明未对通用 malformed-marker 拒绝路径做放宽。

### 3. helper 深度、可维护性与 parity — PASS

- 新 helper 是窄职责的 validation/diagnostic boundary：只决定“目标是否需要 legacy block 预检”，具体 block 边界、marker grammar 与批准错误统一复用 `_legacy_block_range()` / `_match_marker_line()`，没有复制扫描或写盘策略。
- preflight 与后续 promotion 再定位目标块是有意的两阶段 fail-closed：前者保证 generic gate 之前保留 target-specific diagnostic，后者在实际构造 mutation 时重新取得范围；两者之间没有 I/O 或共享状态变更，不产生 TOCTOU 漂移。
- buglist/todolist 两份实现保持自包含，并已将 `_preflight_target_legacy_block` 纳入 `TWO_WAY` AST roster。`test_mirror_consistency.py` 实跑通过，可机械阻止单边漂移；未新增跨 skill runtime import。

## Critical

无。

## Important

无。

## Minor

无新增。

## 领域清单

领域清单未覆盖：`/Users/cheneyzhao/.sdflow/workflow/code-checklists/domains/` 仅有 backend、backend-go、embedded、embedded-esp32、embedded-ml307c，本 Python CLI 无匹配领域 checklist。本轮未静默宣称领域清单通过，按通用 CR-01~09、仓内 OpenSpec 目标态与 Fowler 深模块/变更边界完成复核。

## Verification

- 固定输入：`task3-review-package-fix2.diff` 与 `task3-frontmatter-writer-promotion-fix2.md`；前者 SHA-256 `f3efea53f96a8223efb7e1d69669a588d2c7615b617a35489767ff8f6a3b873d`，与 `git diff --binary d9d3ebf..b5136a0` byte-identical。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task3_frontmatter_writer.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `28 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests sdflow-todolist/tests sdflow-issues/tests -W error` → `346 passed, 1 skipped`；skip 为既定 Windows local-disk smoke。
- 独立 probes：目标块 marker collision 产出同一条精确 file/ID/line 诊断；非目标块 marker corruption 在目标 preflight 通过后仍被 generic gate 拒绝。
- 本复核仅新增本报告，未修改实现或 commit。
