# Task 3 fix1 — frontmatter writer / promotion review 修复报告

状态：DONE

## 结论

- 已修复 `task3-spec-review.md` 与 `task3-standards-review.md` 的全部四条 Important。
- parser、prose escape 与 legacy collision scan 现共用一份 marker-line grammar：canonical marker 后允许 ASCII horizontal whitespace，并在用户 prose 中按同一语法 escape；三份 recorder 的 parser helper 继续由 THREE_WAY AST mirror 守卫。
- 所有 existing-document mutation 在构造候选前拒绝 marker structural problem / ownership ambiguity；所有 dated mutation 在 `atomic_write_bytes` 前重新 parse 候选 rendered bytes，并断言 frontmatter owner 与所需 marker relation 成立。
- 非 canonical mutation spelling 仅在同一 document 存在 literal 相同、尚未 promotion 的 raw legacy row 时放行。canonical `A7` 与 raw legacy `A7` 均不再接受请求 `A007`，raw legacy `A007` → canonical `A7` 的既有正向 promotion 保留。
- bug/todo promotion 已收敛到共享深 helper：helper 统一决定 legacy block/minimal block、marker、history 与 EOL 边界。legacy block 位于 EOF 且没有末尾换行时，先完整保留旧 bytes，再补 document EOL 后写 history/end marker。
- legacy todo 即使只改 batch、状态不变，也创建 marker-framed minimal block；不会伪造 `PROPOSED → PROPOSED` 历史。
- Standards Review 的 Minor（旧 mutation docstring）未在本 fix ticket 实现；由 orchestration 已记录的 T153 跟踪。

## TDD 证据

- 先加入七个 CLI/bytes 反例并确认 `7 failed`：trailing-space marker escape、已有坏 marker 文件 add gate、legacy trailing-space marker collision、noncanonical alias、todo batch-only minimal block、EOF no-EOL history/no-history 两轴。
- 最小实现后七条反例全部转绿；随后将 EOF golden 扩成 trailing EOL 有/无 × history 有/无四格矩阵。
- 定向 Task 3 + mirror 最终：`28 passed`。

## 验证

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task3_frontmatter_writer.py sdflow-buglist/tests/test_mirror_consistency.py -W error`：`28 passed in 1.30s`。
- `uv run --with pytest pytest -q sdflow-buglist/tests sdflow-todolist/tests sdflow-issues/tests`：`344 passed, 1 skipped in 24.46s`；唯一 skip 为既定 Windows local-disk smoke。
- `uv run --with pytest pytest -q --disable-warnings`：`1520 passed, 1 skipped in 72.38s`。
- `uv run --with pytest pytest -q -W error`：`1482 passed, 1 skipped, 38 failed`；失败均为本 ticket 范围外既有 ResourceWarning 门禁（`sdflow-maintain` 未关闭文件与 `sdflow-architecture` 并发测试 pipe），没有 recorder 功能断言失败。
- `python3 -m py_compile sdflow-buglist/scripts/buglist.py sdflow-todolist/scripts/todolist.py sdflow-issues/scripts/issues.py`：PASS。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive`：valid。
- `git diff --check`（review package 纳入 index 前的实现/测试/报告 diff）：PASS。固定审查输入 `task3-review-package.diff` 自身携带 patch payload 的尾空白，纳入 index 后会被 `git diff --cached --check` 如实报告；该文件必须保持 SHA-256 `f26742e263faf47d5797a261c7ce478ae812700d4aaa9a0b630d57cf6adbcc4e`，本 fix 未为通过 whitespace check 篡改固定输入。

## 边界

- 未修改 `sdflow-init/assets/workflow/`，未勾选 `tasks.md` checkbox，未创建 Task 3 checkpoint。
- review package、两份 reviewer 报告与 T153 todolist 变更保持 orchestration 原内容，仅随本 fix 的普通提交一起纳入。
