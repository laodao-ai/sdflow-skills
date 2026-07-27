# Task 1 fix5 实现报告：FF-0 动态 marker 收束

## 测试 seam

- **公共接口边界**：沿用 PreToolUse 进程 seam；测试经 stdin 输入 Bash `command` 与 payload `cwd`，只观察 stdout JSON。
- **可观察契约**：命令起点（前面仅水平空白）的直接创建前缀若 name expression 含有限动态 marker，则输出 `change-name-unparseable` 的无决策审计；wrapper 使用同一表达式时仍优先输出 `cwd-ambiguous`。单个无效 literal / option 保持前者，不含动态 marker 的后置散文保持后者。

## 红绿证据

- **RED**：先把 `${NAME}`、`foo"${BAR}"`、`$1`、`$?`、嵌套 `$()` 与三类 glob 加入 direct 公共进程用例；首次目标组为 `4 failed, 7 passed in 2.94s`，缺口集中在 `${NAME}`、`$1`、`$?` 与嵌套替换，旧实现均误报 `cwd-ambiguous`。
- **GREEN**：以单一 `DYNAMIC_NAME_MARKERS` 代替 `$` 具体语法枚举；`$` 一次覆盖参数展开与任意深度 `$()`，并保留反引号及 glob marker。direct 两种创建前缀交叉覆盖 11 种表达式，目标组 `11 passed in 0.99s`。
- **优先级回归**：wrapper 两种形态与 10 种相同表达式做 cross-product；连同 invalid literal / option、无动态 marker 后置散文的目标组为 `60 passed, 60 deselected in 4.85s`。

## 修复摘要

- 保留从命令起点锚定、只允许前置水平空白的 direct-prefix 骨架；先排除 newline，再从直接前缀后的 name expression 首字段检查有限动态 marker，不解析或展开 shell。
- wrapper 因无法命中 anchored direct prefix，优先保持 `cwd-ambiguous`；完整 direct literal 仍由原三分支处理，stacking deny、ack 与哨兵逻辑未改。
- canonical `ff-generation-constraints.md` 与 `sdflow-spec/SKILL.md` 同步写明 direct 动态名、wrapper 优先级、invalid literal / option 与后置散文边界；契约测试机械锚定两处一致。
- 未改 proposal、design、specs、tasks、计划复选框或 checkpoint；未触碰主 session 的 `task1-review-package.diff`。

## 测试命令与结果

- `uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py -q` → `120 passed in 10.70s`。
- `uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py hack/tests/test_canonical_entry_sync.py -q` → `152 passed in 10.37s`。
- `python3 hack/sync_principles.py --check` → `22 个投放面全部与真相源一致`。
- `python3 -m py_compile sdflow-init/assets/hooks/ff0-branch-guard.py` → PASS。
- `git diff --check` → PASS（无输出）。
- `uv run --with pytest pytest -q` → `1 failed, 2883 passed, 11 skipped, 3 xfailed in 284.21s`；唯一失败见 Concerns。

## Concerns

- 全量套件唯一失败仍是 fix4 已记录的无关基线：`test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight[platform-win32]` 在 macOS / Python 3.14.6 上 monkeypatch `sys.platform="win32"` 后，`shutil.which("claude")` 因 `_winapi is None` 抛 `AttributeError`。本 fix 未修改 outside-voice job 或对应测试，未越界处理。
