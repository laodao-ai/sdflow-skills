# Task 5 delivery reconciliation — fix 1

## Scope

修复 Task 5 双轴评审的本地可修项 I1、I3、I4，并为 I2 落盘可由 push/PR/手动触发的 actual Windows workflow；未修改固定评审报告或 `task5-review-package.diff`。

## Red → green

- 首轮定向：`2 failed, 6 passed, 2 skipped`。red 为缺失 Windows workflow 与 `sdflow-issues/SKILL.md` 仍含退役合同；两项 skip 是 actual-Windows-only，未用作通过证据。
- Windows smoke 现在按生产复合入口建立并恢复 `_ACTIVE_RECORDER_TOKEN` / `_ACTIVE_RECORDER_CHAIN`，验证 `reindex → scan` allowlist participant chain；同一通用前半段另由 POSIX 测试执行，避免 Windows 文件在 delegation setup 处假阻塞。
- corpus 对账改为 test-side 独立 Markdown table projection：不调用 `parse_table_rows`、`_legacy_item_from_row` 或其他 production legacy parser。动态枚举当前 7 个 bug rows + 152 个 todo rows，逐 item 比较全部关键字段；T2/T66/T67/T85/T146 均纳入显式 overlay 模型，其中 T66/T67/T85/T146 只允许 `PROPOSED → DONE`，T2 不允许字段 delta。
- `sdflow-issues/SKILL.md` 统一为显式 `--if-exists skip`、rename 任一阶段 fail-closed + provenance-backed 原命令重跑、sweep exclusive owner + allowlist participant；删除 warn-only、调用方解析错误字符串及“并发安全未焊接”旧合同。
- bug/todo 人读 scan 成功提示改为 `frontmatter/marker/legacy 关系一致`。
- 新增 `.github/workflows/windows-recorder-smoke.yml`：branch-agnostic `push` / `pull_request` / `workflow_dispatch`，`windows-latest` 上安装 Python/pytest 并精确执行 actual smoke。

## Verification

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task5_delivery_contract.py sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error` → `8 passed, 2 skipped`（skip 仅 actual Windows）。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `445 passed, 2 skipped`。
- `uv run --with pytest pytest -qq` → exit 0；`1621 tests collected`，进度终止于 100%，其中 `2 skipped` 为 actual-Windows-only，故普通 full 为 `1619 passed, 2 skipped`。
- `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/windows-recorder-smoke.yml")'` → YAML syntax PASS。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid。
- `python3 hack/sync_principles.py --check` → 20 个投放面一致。
- `git diff --check` 与新增 workflow 的 `git diff --no-index --check` → PASS。

## Windows actual status

actual Windows local-disk smoke **仍未执行**。本次没有 push 权限，且当前 Darwin 宿主没有 Windows 执行层；因此不得把本地 `2 skipped` 或 workflow 静态校验记为 tasks 7.4 PASS。当前 feature branch 一旦获准 push，相关路径触发 workflow；闭环证据仍须固定 commit 上执行：

```text
py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error
```

并保存 `2 passed`、无 skip 的 runner/commit/命令/结果。
