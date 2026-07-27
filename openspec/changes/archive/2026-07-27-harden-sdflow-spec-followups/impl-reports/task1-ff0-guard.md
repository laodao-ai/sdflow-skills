# Task 1 实现报告：FF-0 对错仓不执法

## 测试 seam

- **公共接口边界**：把 hook 当作独立 PreToolUse 可执行程序，通过 stdin 输入宿主 payload（`tool_name`、payload `cwd`、Bash `command`），只通过进程退出码与 stdout JSON 观察行为。
- **可观察契约**：直接 literal 创建调用继续表现为 silent pass 或 `permissionDecision: deny`；未判定调用输出仅含 `hookEventName` 与 `additionalContext`，不得出现任何 `permissionDecision`；测试不导入或调用 hook 内部函数。
- **边界依据**：这是 Claude Code 实际调用 hook 的公开协议，也是既有 `run_hook` 测试 seam；仓库/Git 通过临时真实仓库接地，不 mock hook 内部协作者。

## 红绿证据

- **Slice 1：cwd 未判定**
  - RED：`uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py::test_compound_call_on_protected_branch_is_audited_without_decision -q`，失败于旧实现输出 `permissionDecision` / `permissionDecisionReason`，而非 `additionalContext`。
  - GREEN：同命令 `1 passed in 0.16s`。
- **Slice 2：wrapper / 换行分类**
  - RED：`test_non_direct_literal_forms_are_cwd_ambiguous` 初跑 `2 failed, 7 passed`，`bash -lc` 与换行形态被误分为 `change-name-unparseable`。
  - GREEN：收紧 literal 前缀判定后 `9 passed in 0.73s`。
- **Slice 3：缺失 change 名**
  - RED：加入 `openspec new change --json` 后动态名组 `1 failed, 7 passed`，旧新中间态把 `--json` 误当 change 名并 deny。
  - GREEN：排除 option-as-name 后该组 `8 passed in 0.78s`。
- **Slice 4：canonical 叙述**
  - RED：`test_ff0_rule_and_sdflow_spec_entry_state_the_finite_grammar_boundary` 失败，canonical 未出现「单条直接 literal」边界。
  - GREEN：同步 canonical workflow 与 `sdflow-spec` 入口后 `1 passed`。

## 改动摘要

- 在 hook 中新增整条命令的正向有限 grammar：仅单条直接 `openspec new change` / `openspec change new` literal 调用使用 payload `cwd` 进入原三分支，保留引号、水平空白、`--json` 变体和哨兵行为。
- 非直接调用输出 `cwd-ambiguous`，动态/无法读取的名字输出 `change-name-unparseable`；两者的 hook JSON 只有 `hookEventName` + `additionalContext`，不设置任何 `permissionDecision`。
- 将多处创建字样的 stacking deny 前移到 cwd/Git 探测之前；同名重复调用也必须拆分。
- 同步 `ff-generation-constraints.md` 与 `sdflow-spec/SKILL.md` 的 grammar、原因码和不解析 shell 边界，并增加 canonical 防漂移测试。

## 测试命令与结果

- `uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py hack/tests/test_canonical_entry_sync.py -q` → `85 passed in 5.82s`。
- `python3 hack/sync_principles.py --check` → `22 个投放面全部与真相源一致`。
- `git diff --check` → PASS（无输出）。
- `uv run --with pytest pytest -q` → `1 failed, 2817 passed, 10 skipped, 3 xfailed in 301.20s`。唯一失败为 `test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight[platform-win32]`，见 Concerns。
- 单独复现上述失败 → `1 failed in 0.61s`；`git diff --name-only <before-sha> -- sdflow-init/assets/hack/outside-voice-job.py sdflow-init/tests/test_outside_voice_job.py` 无输出，确认该失败面未被 Task 1 修改。

## Concerns

- 全量套件未全绿：未修改的 `outside-voice-job` 测试在 macOS / Python 3.14.6 上 monkeypatch `sys.platform="win32"` 后，`shutil.which("claude")` 进入 Windows 路径并因 `_winapi is None` 抛 `AttributeError`。该失败与 FF-0 调用图无关，且相关实现/测试相对 before-SHA 无 diff；本票按范围约束未修复它。
- 本票只改 canonical 源与入口；全局 hook / bundle 安装刷新属于后续 Task 4，本次未运行 `init.py update --dev` 或 `setup.sh`。
