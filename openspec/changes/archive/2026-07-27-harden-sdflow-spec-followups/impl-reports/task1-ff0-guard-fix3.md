# Task 1 fix3 实现报告：FF-0 bare-prefix 邻接引号分类

## 测试 seam

- **公共接口边界**：沿用 PreToolUse 进程 seam；测试经 stdin 传入 Bash `command` 与 payload `cwd`，只观察 stdout JSON。
- **可观察契约**：bare literal prefix 后紧邻 quoted variable、command substitution 或 glob 时，统一输出含 `change-name-unparseable` 的无决策审计；不得把 bare prefix 当完整合法 change 名，也不解释或展开 shell。

## 红绿证据

- **RED**：新增 `add"$NAME"`、`add"$(printf foo)"`、`add"*"` 三个公共进程用例后，目标测试为 `3 failed in 2.29s`；旧实现均输出 `cwd-ambiguous`。
- **GREEN**：在 bare token 后增加相邻引号的有限词法判断，不读取引号内容；目标测试为 `3 passed in 0.40s`。
- **回归收紧**：首次最小实现使既有 wrapper `bash -lc 'openspec new change add-foo'` 误报 `change-name-unparseable`。以既有公共进程测试为 RED，增加“创建字样前已有 wrapper 文本则仍为 `cwd-ambiguous`”的优先判断；目标与 wrapper 组随后 `12 passed in 0.88s`。

## 修复摘要

- `undecided_reason()` 不再把 `add"..."` 中的 `add` 截成完整合法名；bare prefix 紧邻任意 quoted fragment 时统一判 `change-name-unparseable`。
- 有前置 wrapper 文本时继续优先判 `cwd-ambiguous`，保持既有 wrapper 契约。
- 实现只检查创建字样前缀与相邻 quote 字符，没有解析或展开变量、命令替换、glob 或其他 shell 语义。

## 测试命令与结果

- `uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py -q` → `77 passed in 6.94s`。
- `python3 -m py_compile sdflow-init/assets/hooks/ff0-branch-guard.py` → PASS。
- `uv run --with pytest pytest -q` → `1 failed, 2840 passed, 11 skipped, 3 xfailed in 290.10s`；唯一失败见 Concerns。

## Concerns

- 全量套件仍是前序报告记录的同一个无关基线失败：`test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight[platform-win32]` 在 macOS / Python 3.14.6 上 monkeypatch `sys.platform="win32"` 后，`shutil.which("claude")` 因 `_winapi is None` 抛 `AttributeError`。本 fix 未修改 outside-voice job 或对应测试，未越界处理。
- 未改设计四件套、计划复选框或 checkpoint；未触碰主 session 的 `task1-review-package.diff`。
