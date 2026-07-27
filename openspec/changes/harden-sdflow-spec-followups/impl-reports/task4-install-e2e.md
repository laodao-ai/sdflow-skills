# Task 4 安装刷新与端到端验收

## 结果

**DONE**。Task 4 所要求的 canonical、dogfood、全局 hook、Claude/Codex skill 与全量回归均已实跑并通过。
实现期未修改 `superpowers-plan.md` 的验收复选框，未创建 `checkpoint(harden-sdflow-spec-followups:task4-...)` 提交。

## 本票发现并修复的真实问题

1. `init update --dev` 的托管块注入少一个分隔空行，随后 `setup.sh` 的通则同步检查会报
   `CLAUDE.md` / `AGENTS.md` 漂移。`inject()` 现保留 outer marker 后的空行，并以
   `TestInjectMarkerMigration::test_nested_managed_content_keeps_separator_after_outer_marker` 回归。
2. `--dev` 会把 toolkit-only `sdflow-init/assets/workflow/tools/tests/` 复制到 dogfood
   `openspec/workflow/tools/tests/`；仓根 pytest 因同名模块出现 7 个 `import file mismatch`。
   `copy_bundle(full=True)` 现和普通 update 一样排除该目录，并清除历史遗留副本；新增首次部署和
   重复更新收敛两条回归。该目录不是运行时 bundle 的组成部分。
3. 全量回归暴露 `sys.platform == "win32"` 的非 POSIX fail-closed 测试会在 capability 已拒绝后仍进入
   `shutil.which()` 的 Windows `_winapi` 分支。`run_preflight()` 现先取 POSIX gate，拒绝时不探测外部 CLI；
   `test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight` 三个参数化用例通过。

## 验收记录

| 项目 | 实际命令 / 比对 | 结果 |
| --- | --- | --- |
| focused 契约集 | `uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py hack/tests/test_canonical_entry_sync.py hack/tests/test_sdflow_spec_failure_modes.py hack/tests/test_sdflow_spec_agents.py hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_harden_sdflow_spec_followup_closure.py sdflow-init/tests/test_init.py::TestBundleToolsOnly sdflow-init/tests/test_init.py::TestInjectMarkerMigration -q` | 173 passed |
| 非 POSIX 修复 | `uv run --with pytest pytest sdflow-init/tests/test_outside_voice_job.py::test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight -q` | 3 passed |
| 规则与规格门 | `python3 hack/sync_principles.py --check`；`openspec validate --all --strict`；`git diff --check` | 22 个投放面一致；21 passed / 0 failed；通过 |
| 开发刷新 | `python3 sdflow-init/scripts/init.py update --root . --dev` | hook 已最新且已注册；无相关 skipped |
| dogfood 清理 | 清除本次 `--dev` 产生的 13 个未跟踪 canonical rules 副本；保留 tracked runtime tools、`WORKFLOW-GUIDE.md` 与 `lens-metric-contract.md` | 通过 |
| setup | `bash setup.sh` | 43 项安装成功；无 skipped；principles、workflow guide、async parity 均通过 |
| 安装机械比对 | hook 字节 + settings 注册；Claude/Codex `sdflow-spec` symlink；`~/.sdflow/workflow` symlink；6 个 hack 分发件字节 + capability manifest | 通过 |
| 全量回归 | `uv run --with pytest pytest -q` | **2843 passed, 11 skipped, 3 xfailed in 287.04s**，exit 0 |

首次全量在修复前实际得到 `1 failed, 2842 passed, 11 skipped, 3 xfailed`：失败为
`test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight[platform-win32]`，已由第 3 项修复并在最终全量中消除。
11 个 skip 与 3 个 xfail 为测试套件的既有条件性标记；最终无 failure。
