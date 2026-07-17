# Task 3 Standards Review — frontmatter writer / overlay promotion

结论：**FAIL（commit `cd02cc0defbbcd447e81c6eee468e63a84458394`，固定审查区间 `68524e8..cd02cc0`）**

## Critical

无。

## Important

### 1. legacy alias 的接受边界被放宽到任意 semantic match，canonical item 也能被非 canonical spelling 修改

- 位置：`sdflow-buglist/scripts/buglist.py:1078-1088`；镜像于 `sdflow-todolist/scripts/todolist.py:1043-1053`。
- `_find_item_document()` 对用户输入直接调用 `semantic_id_key(requested_id, allow_legacy=True)`，随后只按 semantic key 搜索 `effective_items`。因此请求 `A007` 不仅能定位 raw legacy row `A007`，还会命中 canonical frontmatter item `A7`，甚至会命中 raw legacy row `A7`；函数没有验证“同文件确有与请求 spelling 相同的 raw legacy alias”。
- 独立内存 probe 以仅含 canonical `A7` 的 snapshot 调 `_find_item_document(..., "A007", ...)`，实际返回 `raw_id="A7"`。后续 `set-status`/`triage` 会成功修改 `A7` 并输出 canonical ID。
- 这违反已批准契约：“legacy reader MAY 保留孤立 raw spelling；mutation 仅在同文件确有该 raw legacy row 时接受该 alias；无 raw legacy alias 的非 canonical 用户输入必须拒绝”。它也削弱 CLI 的 canonical-ID compatibility 边界，让拼写错误静默落到另一条记录。
- 应先按 canonical grammar 处理正常请求；仅当请求为 legacy spelling 时，要求目标 document 中存在 literal 相同的未 promotion legacy row，且该 semantic key 仓级唯一，再允许 promotion。补 canonical `A7` + 请求 `A007`、raw legacy `A7` + 请求 `A007` 的拒绝测试，并保留 raw legacy `A007` 正向 promotion 测试。

### 2. EOF 无末尾换行时 promotion splice 会把新增内容粘到旧 prose；幂等 triage 可成功写出损坏 marker

- 位置：`sdflow-buglist/scripts/buglist.py:1126-1132,1306-1314,1363-1383`；镜像于 `sdflow-todolist/scripts/todolist.py:1091-1097,1265-1298,1345-1387`。
- `_splice_body_lines()` 忠实回放原 line bytes，但在 `insertions[len(lines)]` 前不确保 line boundary。合法 legacy block 若位于 EOF 且最后一行没有 EOL，promotion 的 history 或 end marker 会直接拼到旧 prose 末尾。
- 独立内存 probe 复现两种错误：`set-status` 生成 `**根因**：root> hist`，历史不再是独立 blockquote；更严重的是 terminal / 已 `PROPOSED` 的 bug `triage` 没有 history，生成 `**根因**：root<!-- ...end... -->`，parser 随即报告 `marker 缺 end` 与 `frontmatter 有 B1 但缺 marker block`。真实命令路径没有 write 后自检，仍会 exit 0 并打印成功 JSON。
- 原 legacy bytes 虽未被改写，但外围 marker/history 没有形成合法独立行，违反“原位包裹 + 后续只按 marker 定位”的目标；下一次 mutation 会被 marker guard 阻断。这是 bytes splice 的边界缺陷，不应以常见文件恰有 trailing newline 为前提。
- 应由一个深层 promotion helper 同时拥有 legacy range、EOL 与 marker/history policy：若被包裹范围末 byte 不是 `\n`，在旧 bytes 之后补 document EOL，再写 history/end marker；补 EOF 有/无 trailing newline、history 有/无两轴 golden，并在写前对候选 rendered bytes 重跑 document parser/关系校验。现有 `19 passed` 定向套件所有 promotion fixture 均以 EOL 结尾，因此未覆盖该缺陷。

## Minor

### 1. mutation docstring 仍描述已删除的表格双写流程

- `sdflow-buglist/scripts/buglist.py:1330-1340` 与 `sdflow-todolist/scripts/todolist.py:1312-1323` 仍声称 triage 更新“批次列/表行末列”、同步块内状态；实现已改为 frontmatter ownership + marker history，旧表明确只读。
- 这些注释位于核心 mutation 入口，会让后续维护者沿错误的 Fowler change boundary 理解代码。应与 module docstring / CLI help 一并改为 effective ownership、promotion 与 marker append 语义。

## 测试重基线审计

- 旧测试把“写表/双写”的断言迁到 frontmatter/marker 是目标态所需，并非本身掩盖缺陷；但重基线同时把 bug legacy fixture 普遍补成“详情块存在且末尾有换行”，使 EOF splice 缺口无法显现。
- 新 Task 3 测试覆盖 raw `A007` 正向 promotion，却没有覆盖“canonical item 不得接受 `A007`”的反向契约；因此 semantic-key 过度宽容仍全绿。
- `test_dated_writer_call_graph_has_no_legacy_table_or_text_writer_calls` 只做源码字符串检查，证明没有直接调用旧 helper，但不能证明 splice 边界、write 后关系合法性或 alias 资格。它不应替代行为 golden。

## 自包含 / parity / 深模块边界

- 三份 recorder 没有新增跨 skill runtime import；`atomic_write_bytes`、`_reject_line_unsafe` 已进 THREE_WAY，document/prose/splice helpers 已进 TWO_WAY，当前 AST parity 测试通过。
- parity 只能保证相同缺陷同步复制。当前 `_splice_body_lines` 是暴露 line index 的浅 primitive，promotion eligibility、marker wrapping、minimal block 与 history append 分散在四个 command 分支；Important 1/2 正是资格和边界未被单一深 helper 封装的结果。修复时应收拢 policy，而不是只在各 caller 分别补条件。

## 领域清单

领域清单未覆盖：规则根 `/Users/cheneyzhao/.sdflow/workflow` 的 `code-checklists/domains/` 仅含 backend、backend-go、embedded、embedded-esp32、embedded-ml307c，本 Python CLI 无匹配领域 checklist。本轮未静默宣称领域清单通过，按通用 CR-01~09、仓内 OpenSpec 目标态与 Fowler 深模块/变更边界完成审查。

## Verification

- 固定输入：`openspec/changes/mlh-p6-recorder-frontmatter/impl-reports/task3-review-package.diff`（`68524e8..cd02cc0`）与 `task3-frontmatter-writer-promotion.md`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task3_frontmatter_writer.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `19 passed`。
- 独立纯内存 probe：canonical-only `A7` 被请求 `A007` 命中；EOF 无 EOL + terminal triage splice 后 parser 得到 `marker 缺 end`。两项均证明现有绿测不足以支撑 PASS。
- 本审查仅新增本报告，未修改实现或 commit。
