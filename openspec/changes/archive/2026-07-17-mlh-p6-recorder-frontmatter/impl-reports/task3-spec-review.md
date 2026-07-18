# Task 3 Spec Review — frontmatter writer、overlay promotion 与 marker prose

结论：**FAIL**（commit `cd02cc0defbbcd447e81c6eee468e63a84458394`；固定范围 `68524e8..cd02cc0`；机械输入 `task3-review-package.diff`，SHA-256 `f26742e263faf47d5797a261c7ce478ae812700d4aaa9a0b630d57cf6adbcc4e`）。

Task 3 的 canonical/overlay writer 主路径、legacy raw alias canonicalization、旧表/旧属性表 bytes 保留、BOM/CRLF/shared-envelope splice、display title/summary blockquote/窄 line-safety，以及停止 legacy table/status/batch 双写均已有实现与绿色回归证据；但 marker fail-closed 与 todo promotion 仍有两项目标态缺口，不能 PASS。

## Critical

无。

## Important

### 1. marker grammar、escape/collision guard 与 mutation gate 不同构，可成功写出或继续扩大坏 marker 结构

- parser 用 `^...-->\s*$` 识别 marker，接受 closing `-->` 后的尾空白；但 `_RESERVED_MARKER_LINE_RE`、`_escape_user_markers()` 与 legacy collision guard 只匹配无尾空白的字面行。因此同一物理行会被 parser 当 marker，却不会被 renderer escape，也不会被 promotion 写前 collision guard 拒绝。见 `sdflow-buglist/scripts/buglist.py:760-771,934-965,1116-1122`；todolist 为镜像实现。
- 独立 CLI 反例 1：新建 canonical bug，`phenomenon` 含独占行 `<!-- sdflow-issue-block:start id=A7 -->   `。`add` exit 0，原行未 escape；随后 `scan --json` 报 `marker 嵌套：B1 → A7`。这违反 tasks 2.5 的“escape 用户内容中的精确 marker 独占行”与 Task 3 的 marker 写前拒绝目标：producer 自己成功产生了不满足 marker relation 的新文件。
- 独立 CLI 反例 2：pure-legacy bug 的唯一 B1 block 内预存一对带尾空白的 A7 start/end marker。`set-status B1 --to VERIFIED` exit 0 并写入 overlay/外围 B1 marker；随后 scan 同时报 nested、ID mismatch、orphan end 与 B1 缺 marker block。原文件本应在 frontmatter/外围 marker/history 任一写盘前保持逐字节不变。该行为直接违反 tasks 2.4、design Lifecycle Update 与 spec 的 legacy marker collision fail-closed。
- `cmd_add()` 对已有 document 也不检查 `document["marker_problems"]` 就追加 model/prose 并写盘。独立 CLI 反例 3：已有 canonical B1 缺 end marker时，再 add B2 仍 exit 0、文件发生写入，scan 从单一“B1 缺 end”扩大为 nested/mismatch 且 B1/B2 都缺有效 marker。见 `sdflow-buglist/scripts/buglist.py:1238-1252`、`sdflow-todolist/scripts/todolist.py:1181-1198`。

建议修复：把 parser、用户 prose escape、legacy collision scan 共用同一份 marker-line grammar（或把 parser 收窄到 renderer 唯一 canonical bytes），并让所有 existing-document mutation 在写盘前拒绝 marker structural problems/ownership ambiguity；加入上述三个 CLI bytes-preservation 回归。

### 2. legacy todo 仅 batch 变化时 promotion 不创建 minimal marker block

- `todolist.py::cmd_triage()` 只有状态发生变化才构造 `history`。对无 legacy block 的 item，`history` 为空时直接 `insertions = {}`，随后仍把完整 item 写入 overlay 并更新 batch。见 `sdflow-todolist/scripts/todolist.py:1335-1371,1386-1389`。
- 独立 CLI 反例：pure-legacy、无 prose block 的 T1 已是 `PROPOSED`，执行 `triage --id T1 --批次 new`。命令 exit 0，frontmatter overlay/batch 已更新、旧表 bytes 保留，但文件完全没有 `sdflow-issue-block:start id=T1`。
- 这不满足 tasks 2.4 的“todo 无块建 minimal block”和 design Lifecycle Update 的“legacy todo 无 block 时创建 marker-framed minimal block”。canonical todo 原生轻量项允许无块，不等于 legacy mutation/promotion 可以跳过批准的 promotion marker 形态。

建议修复：把“是否需要创建 minimal marker block”绑定到 `not frontmatter_owned and no legacy candidate block`，而不是绑定到 `history` 是否非空；状态不变的 triage 仍创建 marker-framed minimal block，但不伪造状态历史。补 PROPOSED/终态 legacy todo 仅改 batch 的回归。

## Minor

无。

## Verification

- 固定 diff 与 `git diff --binary 68524e8..cd02cc0` byte-identical；两者 SHA-256 均为 `f26742e263faf47d5797a261c7ce478ae812700d4aaa9a0b630d57cf6adbcc4e`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task3_frontmatter_writer.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `19 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `337 passed, 1 skipped`；skip 为既定 Windows local-disk smoke。
- source/call-graph 核对确认 Task 3 的 `cmd_add/cmd_set_status/cmd_triage` 使用 `atomic_write_bytes`，没有调用 `atomic_write`、`_reject_cell_unsafe`、`split_sections` 或 `parse_table_rows`；独立 bytes probes 也确认正常 canonical/overlay 与 legacy promotion 不改旧 table/status/batch snapshot。

修复以上两项 Important 并加入反例回归后，Task 3 才可 PASS。
