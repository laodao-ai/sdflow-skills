# Task 3 fix1 Standards Re-review — frontmatter writer / overlay promotion

结论：**PASS（commit `d9d3ebf`，固定复核区间 `cd02cc0..d9d3ebf`）**

上一轮 2 个 Important 均已关闭；未发现新的 Critical / Important。上一轮 mutation docstring Minor 已进入 T153，本 fix ticket 按要求不实现，不阻断 PASS。

## 上轮 Important 逐项复核

### 1. legacy alias 资格过宽 — CLOSED

- `sdflow-buglist/scripts/buglist.py:1079-1101` 与 `sdflow-todolist/scripts/todolist.py:1044-1066` 先计算 canonical spelling；非 canonical 请求只有在 `raw_id == requested_id`、该 literal raw ID 仍位于 `document["rows"]`，且同 semantic key 尚无 canonical frontmatter owner 时才可进入 mutation。
- 独立 helper probe 构造三种 snapshot：canonical-only `A7` + 请求 `A007` → exit 1；raw legacy `A7` + 请求 `A007` → exit 1；raw legacy `A007` + 请求 `A007` → 正常返回 `A007`。这与“仅同文件确有该 raw legacy alias 才放行”的契约一致。
- 新 CLI 回归同时覆盖 canonical `A7` 与 raw legacy `A7` 的反向拒绝，并保留原 raw `A007` → canonical `A7` promotion 正向用例。拒绝路径保持原文件 bytes 不变。

### 2. EOF 无末尾换行时 history/end marker 粘连 — CLOSED

- `sdflow-buglist/scripts/buglist.py:1154-1175` 与 todolist 镜像 `_promotion_insertions()` 统一拥有 legacy block 定位、minimal block、history、marker 和 EOL boundary；当被包裹 block 的最后一行无 CR/LF 时，在旧 bytes 后补 document EOL，再追加 history/end marker。
- 独立纯内存 probe 对同一 EOF no-EOL legacy bug 分别执行无 history 与有 history promotion：旧 `**根因**：root` bytes 均原样保留，后续分别成为独立 end marker 行或独立 history + end marker 行；candidate parse 的 `marker_blocks` 均含 `B1`，`marker_problems=[]`。
- 新 golden 覆盖 trailing EOL 有/无 × history 有/无四格；todo batch-only、状态不变的 legacy promotion 也建立 minimal marker block且不伪造状态历史。

## Deep helper / candidate reparse / parity

- `_promotion_insertions()` 把上一轮散落在四个 command 分支的 promotion policy 收拢为单一深 helper；bug 用 `require_block=True` 对缺 legacy block fail-closed，todo 用 `False` 在无块时建立 minimal block。调用方只保留 pool 门禁、model mutation 与输出 shape，边界清晰。
- `_reject_document_mutation()` 在 existing-document mutation 前拒绝既有 marker/frontmatter ownership structural problem；`_validated_rendered_mutation()` 在每次 `atomic_write_bytes` 前重新 parse 完整候选，并核验 target frontmatter owner 与所需 marker relation。独立 probe 删除候选 end marker后调用 validator，得到 `rendered candidate 关系自检失败`，没有进入写盘。
- parser、prose escape、legacy collision scan 统一经 `_match_marker_line()` 与 `_ISSUE_MARKER_LINE_RE`；trailing ASCII horizontal whitespace 不再形成 parser/producer grammar skew。
- `_match_marker_line` 已进入 THREE_WAY AST roster，regex pattern/flags 在 bug/todo/issues 三份显式比较；promotion/reject/validation helpers进入 bug↔todo TWO_WAY roster。自包含保持不变，没有跨 skill runtime import。parity guard 可机械阻止本轮共享逻辑单边漂移。

## Critical

无。

## Important

无。

## Minor

### 保留项：旧 mutation docstring 与 frontmatter 实现不一致

- 上一轮指出的 `cmd_triage` 表格双写旧描述仍在；orchestration 已记录 T153，本 fix ticket 明确不实现。该文档债不影响本轮两项数据完整性修复与 CLI 行为，按要求保留、不阻断 PASS。

## 领域清单

领域清单未覆盖：规则根 `/Users/cheneyzhao/.sdflow/workflow` 的 `code-checklists/domains/` 仅含 backend、backend-go、embedded、embedded-esp32、embedded-ml307c，本 Python CLI 无匹配领域 checklist。本轮未静默宣称领域清单通过，按通用 CR-01~09、仓内 OpenSpec 目标态与 Fowler 深模块/变更边界完成复核。

## Verification

- 固定输入：`task3-review-package-fix1.diff` 与 `task3-frontmatter-writer-promotion-fix1.md`；前者 SHA-256 `5779d7d74104acada4a35ded38b4c2029fc74adcbff0058dfa1f1fc9eb63649b`，与 `git diff --binary cd02cc0..d9d3ebf` byte-identical。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task3_frontmatter_writer.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `28 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests sdflow-todolist/tests sdflow-issues/tests -W error` → `346 passed, 1 skipped`；skip 为既定 Windows local-disk smoke。fix1 实现报告记录的较早计数为 `344 passed, 1 skipped`，本次以固定 commit 当前实跑结果为准，均无 recorder failure。
- 独立 probes：alias 三态资格符合预期；EOF no-EOL 的 history 有/无候选均 parse-clean；删 end marker 的候选被 reparse validator 写前拒绝。
- `git diff --check d9d3ebf^..d9d3ebf` 对实现、测试与 helper parity 相关文件无 whitespace error。
- 本复核仅新增本报告，未修改实现或 commit。
