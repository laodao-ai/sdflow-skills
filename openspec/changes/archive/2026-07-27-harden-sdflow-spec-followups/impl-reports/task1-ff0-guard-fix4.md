# Task 1 fix4 实现报告：FF-0 未判定原因正向分类

## 测试 seam

- **公共接口边界**：沿用 PreToolUse 进程 seam；测试经 stdin 输入 Bash `command` 与 payload `cwd`，只观察 stdout JSON。
- **可观察契约**：完整 direct literal 仍由上层三分支处理；未完整匹配时，wrapper、目录切换、compound、换行和散文输出 `cwd-ambiguous`，仅从命令起点开始的直接创建前缀加单个非 literal name expression 输出 `change-name-unparseable`。两类审计均不含 `permissionDecision`。

## 红绿证据

- **RED**：新增 `bash -lc` / `env -C` 与变量、命令替换、glob 的 2×3 cross-product 后，目标组 `6 failed, 4 passed in 2.76s`；六个 wrapper 组合均被旧的搜索加逐 token 特判误报为 `change-name-unparseable`。
- **GREEN**：删除逐 token 分支，改用一个从命令起点完整匹配的正向 `DIRECT_UNPARSEABLE_CHANGE_RE`；wrapper cross-product 与直接前缀变量/替换/glob/相邻 quoted dynamic 组全部通过。
- **回归收紧**：补后置散文 `openspec new change add-foo please`；既有换行、`--jsonfoo`、compound、多调用 stacking、三分支与哨兵回归保持通过。

## 修复摘要

- `undecided_reason()` 的优先级收敛为：换行先归 `cwd-ambiguous`；完整命中有限的直接非 literal name-expression grammar 才归 `change-name-unparseable`；其余一律 `cwd-ambiguous`。
- name-expression grammar 只做有限词法边界识别；不解释引号、不展开变量/glob、不执行命令替换，也不解析 shell。
- 未改 proposal、design、specs、tasks、计划复选框或 checkpoint；未触碰主 session 的 `task1-review-package.diff`。

## 测试命令与结果

- `uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py -q` → `87 passed in 8.91s`。
- `uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py hack/tests/test_canonical_entry_sync.py -q` → `120 passed in 8.40s`。
- `python3 hack/sync_principles.py --check` → `22 个投放面全部与真相源一致`。
- `python3 -m py_compile sdflow-init/assets/hooks/ff0-branch-guard.py` → PASS。
- `git diff --check` → PASS（无输出）。
- `uv run --with pytest pytest -q` → `1 failed, 2851 passed, 11 skipped, 3 xfailed in 284.83s`；唯一失败见 Concerns。

## Concerns

- 全量套件唯一失败仍是前序报告记录的无关基线：`test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight[platform-win32]` 在 macOS / Python 3.14.6 上 monkeypatch `sys.platform="win32"` 后，`shutil.which("claude")` 因 `_winapi is None` 抛 `AttributeError`。本 fix 未修改 outside-voice job 或对应测试，未越界处理。
