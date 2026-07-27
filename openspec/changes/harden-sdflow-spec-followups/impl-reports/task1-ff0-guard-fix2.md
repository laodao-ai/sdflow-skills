# Task 1 fix2 实现报告：FF-0 `--json` 边界与换行原因码

## 测试 seam

- **公共接口边界**：沿用 PreToolUse 进程 seam；测试经 stdin 传入 Bash `command` 与 payload `cwd`，只观察 stdout JSON。
- **可观察契约**：`--json` 仅在完整 token 后为水平空白或命令结束时才是 option；`--jsonfoo` / `--jsonfoo-bar` 必须输出 `change-name-unparseable` 的无决策审计。命令结构中出现换行时，必须优先输出 `cwd-ambiguous` 的无决策审计。

## 红绿证据

- **Slice 1：`--json` token 边界**
  - RED：新增 `--jsonfoo` 与 `--jsonfoo-bar` 公共进程回归后，`2 failed in 2.09s`；旧实现用 `tail.startswith("--json")` 剥掉前缀，将剩余 `foo*` 误判为合法 literal。
  - GREEN：仅在 `--json(?=$|[ \t])` 命中时剥 option；同组回归 `2 passed in 0.28s`。
- **Slice 2：换行优先级**
  - RED：新增命令前置、`openspec`/子命令中置、change 名之前、`--json` 与名字之间、命令末尾六类换行回归；其中 `openspec new change\nadd-foo` 与 `openspec new change --json\nadd-foo` 误报 `change-name-unparseable`，结果 `2 failed, 4 passed in 0.59s`。
  - GREEN：`undecided_reason()` 在 literal 名分类前先识别 `\n` / `\r`，统一落 `cwd-ambiguous`；两个 slice 合跑 `8 passed in 0.60s`。

## 修复摘要

- `undecided_reason()` 不再把带 `--json` 前缀的非法名字误剥成合法 change 名。
- 只要未直接匹配的创建命令含换行，原因码优先为 `cwd-ambiguous`；未新增 shell 解析或展开。
- 未修改 proposal、design、specs、tasks、计划复选框或 checkpoint；未触碰主 session 生成的 `task1-review-package.diff`。

## 测试命令与结果

- `uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py -q` → `74 passed in 6.84s`。
- `python3 -m py_compile sdflow-init/assets/hooks/ff0-branch-guard.py` → PASS。
- `git diff --check` → PASS（写报告前，无输出）。
- `uv run --with pytest pytest -q` → `1 failed, 2837 passed, 11 skipped, 3 xfailed in 290.09s`；唯一失败见 Concerns。

## Concerns

- 全量套件仍有 fix1 已记录的同一个无关基线失败：`test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight[platform-win32]` 在 macOS / Python 3.14.6 上 monkeypatch `sys.platform="win32"` 后，`shutil.which("claude")` 因 `_winapi is None` 抛 `AttributeError`。本 fix 未修改 outside-voice job 或对应测试，未越界处理。
