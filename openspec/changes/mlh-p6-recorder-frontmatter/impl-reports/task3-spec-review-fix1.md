# Task 3 Spec Re-review fix1 — frontmatter writer、overlay promotion 与 marker prose

结论：**FAIL**（commit `d9d3ebf7320d6b4f27dc61b515925bf3859411d8`；固定范围 `cd02cc0..d9d3ebf`；机械输入 `task3-review-package-fix1.diff`，SHA-256 `5779d7d74104acada4a35ded38b4c2029fc74adcbff0058dfa1f1fc9eb63649b`）。

上一轮两个 Important 的数据安全与目标形态主体均已修复：marker parser/escape/collision matcher 已同构，existing-document mutation 会写前拒绝坏 marker，rendered candidate 会在 `atomic_write_bytes` 前重解析；legacy todo 仅改 batch 也会创建无伪历史的 minimal marker block。BOM/CRLF/shared-envelope、legacy bytes 与 EOF no-EOL promotion 的独立 probe 全部通过。但 marker collision 的批准诊断合同仍被通用 gate 遮蔽，尚不能 PASS。

## Critical

无。

## Important

### 1. legacy marker collision 虽已写前拒绝，但不再报告 legacy ID、行号与 `marker collision`

- spec 明确要求：候选 legacy block 内预存精确 marker 时，stderr 必须点名 `file/legacy ID/line` 与 `marker collision`，并保持原文件逐字节不变。见 `specs/spec-workflow/spec.md:70-72`。
- `_legacy_block_range()` 已具备完整诊断：`legacy marker collision` + `id={raw_id} line={...}`；但 `cmd_set_status/cmd_triage` 在进入该 helper 前先调用 `_reject_document_mutation()`。paired marker 在 pure-legacy 文档中先被 `_build_effective_snapshot()` 记为 `marker-only legacy：A7`，通用 gate 因而提前退出，candidate-specific collision 分支永远到不了。见 `sdflow-buglist/scripts/buglist.py:1016-1018,1124-1130,1143-1151,1331-1337`；todolist 为镜像实现。
- 独立 CLI 反例：B1 的唯一 legacy block 内放入带尾空白的 A7 start/end marker，执行 `set-status B1 --to VERIFIED`。命令 exit 2 且原 bytes 不变，但 stderr 仅为 `marker/ownership 结构非法; cause: marker-only legacy：A7`；不含 `B1`、`line=` 或 `marker collision`。因此行为 fail-closed 已修，批准的可定位诊断仍未实现。
- 对应旧回归本来要求 `marker collision`、`B1` 与 `line=`，fix1 将断言放宽为仅检查 `"marker" in stderr`，正好掩盖了该缺口。见 `sdflow-buglist/tests/test_task3_frontmatter_writer.py:256-275`。

建议修复：保留所有 existing-document mutation 的通用 marker gate，但在目标 item 属于未 promotion legacy owner 时，先对其唯一候选 block 执行 collision scan，或让通用 problem 携带 owner/line/collision 分类；恢复测试对 file、legacy ID、line 与 `marker collision` 的完整断言。不可通过继续放宽错误文案断言收口。

## 上一轮 Important 复核

### marker grammar / escape / collision / existing-document gate — 部分闭合

- **已修复**：三 recorder parser 与两 writer prose escape/legacy collision 共用 `_match_marker_line()`；带 ASCII space/tab 尾空白的 marker 识别范围一致。
- **已修复**：用户 prose 中 parser 可识别的尾空白 marker 会 HTML-escape；独立 add→scan 反例得到 `problems=[]`。
- **已修复**：已有 canonical B1 缺 end marker时 add B2 非零、原 bytes 不变。
- **已修复**：legacy block 内 paired trailing-space marker 会写前非零且原 bytes 不变。
- **仍缺**：上述 collision 未满足批准的精确诊断，构成本轮剩余 Important。

### todo batch-only promotion minimal block — 已修复

- pure-legacy、无 prose block、状态已为 `PROPOSED` 的 T1 执行仅 batch 变化的 triage：exit 0，写入 overlay 与 marker-framed minimal block，不生成 `PROPOSED → PROPOSED` 伪历史。
- 原 legacy table bytes 保留，随后 `scan --json` 返回新 batch 且 `problems=[]`。
- `_promotion_insertions()` 现在把“legacy owner 无 block”统一落为 minimal marker block，不再依赖 `history` 非空。

## Candidate reparse / bytes 复核

- 独立构造 UTF-8 BOM + CRLF shared envelope + external namespace + pure-legacy bug，legacy block 位于 EOF 且无末尾 EOL；执行 `set-status` 后成功。
- BOM、external namespace、legacy table/header bytes 与被包裹 block 内 bytes 均逐字节保留；新增 namespace/marker/history 全部沿用 CRLF，没有 lone LF。
- candidate reparse 得到 `marker_problems=[]` / `problems=[]`，旧 row 仍为 `OPEN`，frontmatter 当前值为 `VERIFIED`；证明 fix1 的写前重解析没有破坏 shared-envelope splice、legacy snapshot 或 EOL 边界。
- EOF 有/无 trailing EOL × history 有/无的新增四格测试也全部通过。

## Minor

无新增；旧 mutation docstring 偏差已由 T153 跟踪，不倒灌为本 fix1 阻断。

## Verification

- 固定 diff 与 `git diff --binary cd02cc0..d9d3ebf` byte-identical；SHA-256 均为 `5779d7d74104acada4a35ded38b4c2029fc74adcbff0058dfa1f1fc9eb63649b`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task3_frontmatter_writer.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `28 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `346 passed, 1 skipped`；skip 为既定 Windows local-disk smoke。
- 五组独立 CLI/bytes probes：marker escape、existing broken-marker add gate、legacy collision、todo batch-only minimal block、BOM+CRLF+shared-envelope+EOF promotion；除 collision 精确诊断外，目标行为均通过。

补齐 legacy collision 的 file/owner/line/classification 诊断并恢复严格回归后，Task 3 才可 PASS。
