# Task 4 Standards Compliance Review — Fix 1

结论：**BLOCKED**

- 固定 fix 审包：`impl-reports/task4-review-fix1-package.diff`（SHA-256 `dfb4ec7ed87a5a29a6f74e49a3cde3ad233e5dd501c7ca50cfdb23ff2da44695`）
- 固定范围：`b899792..8ed9bc2`；审包与 `git diff --binary b899792..8ed9bc2` byte-identical
- Findings：Critical 0 / Important 3 / Minor 0
- 原审 C1、I1、I2 的核心写前拒绝、schema 值域与 overlay parity 已补，但 arity 真值分层仍可误判；fix1 另引入 ID 错型裸 traceback，marker collision 的强制定位信息也未闭合。存在 Important，Task 4 仍不可通过 standards review。

## Checklist 适用性

workflow root 为 `/Users/cheneyzhao/.sdflow/workflow`。已复核 `code-checklists/code-review-base.md`、`code-checklists/README.md` 与 `domains/` 注册表；当前领域 delta 只覆盖 backend、backend-go、embedded、embedded-ml307c、embedded-esp32，本变更是 Python CLI + Markdown/frontmatter 数据管道，**领域清单未覆盖**。本轮依据通用 CR-01~09、Task 4/Global Constraints、`SW-RI-1`、`SW-RI-3`、`SW-RI-4`、`DG-RI-1` 与原双轴 findings 复审。

## Findings

### Important I1 — arity preflight 仍用 old/new 字面出现替代“item 仍可判”，可成功提交错误 registry/INDEX

- 位置：`sdflow-issues/scripts/issues.py:919-958`，测试缺口：`sdflow-issues/tests/test_task4_rename_snapshot.py:510-537`。
- 证据：对所有 `len(cells) not in (7, 8)` 的 row，当前逻辑只在 cells 中出现精确 `old_key/new_key` 或列数少于 7 时拒绝；否则直接 `continue`，没有证明 module/summary/enum/status/change/batch 的列位仍可靠。新增 success fixture 只覆盖“末尾多一个 trailing cell”这一种可判形态，不能证明中间多 `|` 后的列位仍可靠。
- 独立 PoC：`| B1 | core | old | injected | P2 | OPEN | 10:00 | chg | other |` 被 direct snapshot 解释成 `priority=injected,status=P2,time=OPEN,change=10:00,batch=chg`，只记录 arity warning；执行真实 `batch rename batch-old batch-new` 仍 exit 0，registry 写成 `batch-new`，INDEX 落入不存在的 `chg` 批次并写出错误 status/change。dated bytes 虽未改，但 registry 与派生输出已被错误提交。
- 违反：Task 4/`tasks.md` 4.5 与 `SW-RI-3` 明确只有“与 retag 无关且 item 仍可判”的 legacy problem 可默认成功；任何影响 item/batch 判定的 problem 必须在 registry 写前 fatal。原 Spec I4 未被真正修复。
- 修复：不要以 cells 是否含 old/new 推断 arity 安全。建立能证明列位的 legacy row 分类：只有明确的 7 列兼容形态和 8 列标准形态，或有可证明语法的无害尾随形态可继续；中间增删 cell、enum/status/字段错位或无法证明 batch 真值的 row 一律 preflight fatal。补上述“中间插 cell + unrelated final batch”回归，断言 registry/dated/INDEX/batches bytes 全不变；保留现有纯尾随无害 warning 用例。

### Important I2 — fix1 的 legacy alias 支持让非 string ID 从三段式错误退化为裸 `TypeError`

- 位置：`sdflow-issues/scripts/issues.py:1162`。
- 证据：fix1 将原 `canonical_id(item["id"])` 改为直接调用 `_legacy_semantic_id_key(item["id"])`；该 helper 对非 string 调 `re.fullmatch`。`id=null` 的合法 JSON 协议漂移因此抛 `TypeError: expected string or bytes-like object, got 'NoneType'`，而非 `ValueError`。CLI `main()` 只捕获 `ValueError`，故用户得到 traceback，缺 `ERROR: problem; cause; fix`。
- 违反：producer contract 要求 string `id/file`；`SW-RI-1` fatal diagnostics 要求统一 stderr 三段式并定位 field，CR-01/CR-02 要求上游坏类型走受控错误路径。虽然发生在派生物写前，诊断契约已回归。
- 修复：先显式检查 `isinstance(item["id"], str)`，再解析 legacy semantic key；所有非 string 与 malformed spelling 都抛带 `item[index].id` 的三段式 `ValueError`。参数化 `null/int/list/object`，并以真实 `reindex` 断言 nonzero、无 traceback、INDEX/batches bytes 不变。

### Important I3 — 成对 preexisting marker 会被通用 structural gate 抢先，丢失 target legacy ID 与 line

- 位置：`sdflow-issues/scripts/issues.py:888-916`，测试缺口：`sdflow-issues/tests/test_task4_rename_snapshot.py:325-354`。
- 证据：`_legacy_block_range()` 本可报告 `id={raw_id} line=...`，但 `_reject_target_document_problems()` 先扫描整个 document problems。候选 B1 block 内若预存完整 `start/end id=B9`，parser 先产出 `marker-only legacy：B9`，函数在 904 行直接抛出；后续 target-aware `_legacy_block_range(B1)` 永远不执行。真实诊断只有 file、B9 与通用 relation 文案，缺待提升 legacy ID `B1` 和碰撞 line。fix1 测试只插入孤立 start marker，且只断言 stage/原命令/bytes，不断言 file + target ID + line。
- 违反：`SW-RI-1` “legacy block 预存 marker 时 promotion 拒绝”要求点名 file/legacy ID/line；原 Standards C1 的修复条件也明确 start/end marker 与 candidate block 定位。拒写本身已修复，但强制可恢复诊断尚未闭合。
- 修复：对 target pure-legacy bug 先以 semantic-unique `_legacy_block_range()` 执行 candidate collision 检查，再处理 document-wide structural problems；或让 structural gate 将 marker 反查到 target candidate range并补齐 target ID/line。补完整 start+end、orphan end、nested/mismatched 各类 target candidate 测试，断言三段式诊断含 file、B1、实际 line、`stage=preflight`、原命令，且四类盘面 bytes 不变。

## 已确认修复且无回归的部分

- canonical/overlay missing marker 与 pure-legacy duplicate candidate 已在 registry 写前拒绝，四类盘面保持不变；retag 后 relation 自检不触发第二次 dated file read/document parse。
- strict consumer 已拒绝 module/summary 空白壳、change/batch 空串并校验 Unicode scalar；合法 pure-legacy `A007` 保持可读，Unicode/mixed digits 拒绝。
- canonical/pure-legacy/overlay × bug/todo direct snapshot parity 已补；overlay retag 保持 frozen row/body，更新 frontmatter 并复用 snapshot reindex，read/parse call-count 为 1。
- registry-first provenance、四阶段 fault recovery、scan=0、BOM/CRLF/span 保真与 generic reindex 默认/strict 门禁未被放宽。

## 验证

- `uv run --with pytest pytest -q sdflow-issues/tests/test_task4_rename_snapshot.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `79 passed`
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `418 passed, 1 skipped`（Windows-only）
- `git diff --check b899792..8ed9bc2` → PASS
- fixed package byte comparison → MATCH
- 独立只读 PoC：中间插 cell 的 unrelated arity row → rename 成功并写错 registry/INDEX；`id=null` → 裸 `TypeError`；完整 marker pair 位于 B1 candidate → preflight 拒绝但诊断缺 B1/line。

测试全绿不构成 PASS：I1 仍会把不可判盘面提交成成功，I2/I3 违反 fatal diagnostic contract。三项修复并补定向回归后需再次独立 Standards review。
