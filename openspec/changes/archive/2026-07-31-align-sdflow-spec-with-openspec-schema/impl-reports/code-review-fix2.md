# Code review fix2 — A1

修复范围：仅处理 `code-review-adversarial-fix2.md` 的 A1；未修改 `code-review-report.md`，未创建 checkpoint。

## 修复

`migrate_changes()` 对已有 `.openspec.yaml` 保持严格可解析校验，但将合法 schema 值限定为：

- 内置 `spec-driven`
- 项目本地 `sdflow-spec-driven`

因此，缺失 marker 的旧在途 change 仍补写内置 `spec-driven`；已绑定上述任一合法 schema 的 change 均保持 no-op。截断、畸形、重复或未知 schema 值仍 fail-loud。

新增回归覆盖：版本门通过并切到 fork 后，新建一个已绑定 `sdflow-spec-driven` 的在途 change，再次运行 `update` 不会阻断，marker 和配置均保持 fork schema。

## 验证

- `python -m pytest -q sdflow-init/tests/test_init.py::TestProjectLocalSchema::test_update_accepts_existing_fork_bound_change`
  - `1 passed in 0.76s`，退出码 0。
- `python -m pytest -q sdflow-init/tests/test_init.py sdflow-init/tests/test_task5_regression.py`
  - `68 passed, 1 skipped in 12.45s`，退出码 0。
- `git diff --check`
  - 通过，退出码 0。
- 全量 `pytest`
  - 按用户明确批准跳过；此前超时退出码 `124`，未宣称通过。

## 结论

A1 已修复并有定向回归覆盖；未修改总报告，未创建 checkpoint。
