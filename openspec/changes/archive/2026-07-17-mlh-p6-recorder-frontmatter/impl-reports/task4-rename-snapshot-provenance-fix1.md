# Task 4 Fix 1 实现报告

## 结论

Task 4 双轴评审的 Critical / Important 已全部修复。batch rename 现在在 registry-first 写入前完成 target-aware preflight；strict scan consumer 与 recorder schema 值域一致，同时保留合法 pure-legacy ASCII alias；canonical、pure-legacy、overlay 在 bug/todo 两池的 snapshot / retag 契约已有直接回归锚点。

## 修复内容

- 为 target canonical / overlay 文档增加 marker/ownership 写前拒绝；pure-legacy bug promotion 使用 semantic-unique block resolver，拒绝缺 block、重复 candidate 与候选块内预存精确 marker。
- 对内存 retag 结果执行不触发二次 dated parse 的 relation 自检：frontmatter ownership、marker 成对关系和 bug block 必备关系必须成立，保持每个 dated 文件 read/parse 各一次。
- legacy row 按 batch 真值分层：7/8 列且字段可判时继续；影响 old target / new orphan 的 arity 歧义、缺字段和非法 enum/ID 在 preflight fatal；被 frontmatter shadow 的冻结 legacy row 不参与当前 batch 真值；与 rename 无关且可判的 arity problem 仍回显并成功。
- strict scan envelope 接受合法 positive pure-legacy alias（如 `A007`），拒绝 Unicode/mixed digits、非法 spelling；`module` / `summary` 要求 nonblank，`change` / `batch` 只允许 `null` 或非空 string，并校验 Unicode scalar。
- 增加 canonical / pure-legacy / overlay × bug / todo producer parity，overlay 双池 retag 的 frozen row/body、frontmatter current value、snapshot reuse、read/parse call-count，以及四类 preflight 拒写全盘 bytes 保持回归。

## TDD 记录

- RED：新增定向场景后 `15 failed, 48 passed`，失败逐项对应 alias/schema、四类 preflight 与 target/new arity 歧义。
- GREEN：`uv run --with pytest pytest -q sdflow-issues/tests/test_task4_rename_snapshot.py -W error` → `72 passed`。

## 验证

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_mirror_consistency.py sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `418 passed, 1 skipped`（Windows-only）。
- `uv run --with pytest pytest -q` → `1592 passed, 1 skipped`。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid。
- `python3 hack/sync_principles.py --check` → `20` 个投放面一致。
- `git diff --check` → PASS。

固定评审报告与 `task4-review-package.diff` 未修改。
