# Task 3 fix2 — legacy marker collision 精确诊断修复报告

状态：DONE

## 结论

- 已修复 `task3-spec-review-fix1.md` 唯一剩余 Important。
- `set-status` / `triage` 定位目标后，若目标仍由 legacy row 拥有且存在候选 prose block，会先执行 target-aware legacy block preflight，再进入 generic marker/ownership gate。
- 候选 block 内存在 parser 可识别 marker 时，复用 `_legacy_block_range()` 的批准诊断：stderr 同时包含 file、目标 legacy ID、`line=` 与 `marker collision`，并在任何渲染或写盘前退出，原文件 bytes 不变。
- generic `_reject_document_mutation()` 未放宽：target preflight 通过后，其它 marker structural problem / ownership ambiguity 仍由通用 gate 拒绝；canonical 缺 end marker后再 add 的既有回归继续通过。
- 新 preflight helper 在 buglist/todolist 保持自包含镜像，并纳入 TWO_WAY AST roster；没有新增跨 skill runtime import。

## TDD 证据

- 先恢复两条真实 CLI regression 的严格断言：普通预存 marker 与带尾空白 marker 均要求 file + `id=B1` + `line=` + `marker collision`，并验证原 bytes 不变。
- 实现前：`2 failed`，实际 stderr 被 generic gate 遮蔽为 `marker-only legacy`。
- 加入 target-aware preflight 后：`2 passed`；完整 Task 3 + mirror 套件 `28 passed`。

## 验证

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task3_frontmatter_writer.py sdflow-buglist/tests/test_mirror_consistency.py -W error`：`28 passed in 1.36s`。
- `uv run --with pytest pytest -q sdflow-buglist/tests sdflow-todolist/tests sdflow-issues/tests -W error`：`346 passed, 1 skipped in 24.52s`；唯一 skip 为既定 Windows local-disk smoke。
- `uv run --with pytest pytest -q --disable-warnings`：`1520 passed, 1 skipped in 73.60s`。
- `python3 -m py_compile sdflow-buglist/scripts/buglist.py sdflow-todolist/scripts/todolist.py sdflow-issues/scripts/issues.py`：PASS。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive`：valid。
- `git diff --check`（固定 review package 纳入 index 前）：PASS。

## 边界

- 未修改 `sdflow-init/assets/workflow/`，未勾选 `tasks.md` checkbox，未创建 Task 3 checkpoint。
- `task3-review-package-fix1.diff` 与两份 fix1 re-review 报告保持 orchestration 原内容，仅随本 fix 的普通提交纳入。
