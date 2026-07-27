# Task 1 fix1 实现报告：FF-0 名称与动态后缀收紧

## 测试 seam

- **公共接口边界**：沿用首轮已确认的 PreToolUse 进程 seam；测试以 stdin 传入 `tool_name`、payload `cwd` 与 Bash `command`，只观察进程退出码和 stdout JSON。
- **可观察契约**：非法 OpenSpec change 名、option-as-name 与 quoted-prefix + dynamic-suffix 都只能输出含 `change-name-unparseable` 的 `additionalContext`，不得输出 `permissionDecision`；合法直接 literal 仍进入既有三分支。
- **同步 seam**：canonical workflow 与 `sdflow-spec/SKILL.md` 的保护分支行必须同时包含 `main`、`master`、`默认分支`；以同一行锚防止入口再次漏写默认分支。

## 红绿证据

- **Slice 1：OpenSpec 合法名 pattern**
  - RED：新增 `--help`、`-h`、`Foo`、`foo_bar`、`foo.bar`、`1foo`、`foo-`、`foo--bar` 公共进程回归后，`test_invalid_openspec_change_names_are_unparseable` 为 `8 failed in 0.94s`；旧正则把它们都送入 protected-branch deny。
  - GREEN：将唯一合法名 pattern 收紧为 `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`，并让 bare token 与 quoted token 共用该校验后，名称、既有动态名和合法引号变体合跑 `21 passed in 2.02s`。
- **Slice 2：quoted-prefix + dynamic-suffix**
  - RED：在 detached baseline `1053c26` 上加入题定三类回归，`"add-"$NAME`、`'add-'$(printf foo)`、`"add-"*` 为 `3 failed in 0.27s`，均被误分为 `cwd-ambiguous`。为避免只靠 `add-` 本身非法而假绿，另加合法 quoted prefix `"add"$NAME`，修复中间态为 `1 failed, 3 passed in 0.36s`。
  - GREEN：有限检查 closing quote 后是否无空白拼接动态后缀，不解释 shell 最终 token；四类回归 `4 passed in 0.32s`。
- **Slice 3：默认分支同步锚**
  - RED：新增 `test_ff0_rule_and_sdflow_spec_entry_agree_on_protected_branches` 后 `1 failed in 0.02s`，定位 `sdflow-spec/SKILL.md` 保护分支行缺少“默认分支”。
  - GREEN：入口表格改为 `保护分支（main / master / 默认分支）` 后同用例 `1 passed in 0.01s`。

## 修复摘要

- `ff0-branch-guard.py` 现在只以 OpenSpec lowercase kebab-case pattern 接受 literal change 名；大写、下划线、点、非法连字符及 option-as-name 全部走 `change-name-unparseable` 无决策审计。
- `undecided_reason()` 只做有限 token 分类：quoted prefix 后紧接变量、命令替换、glob 或其他非分隔符即判动态后缀；未新增 shell 解析或展开。
- `sdflow-spec/SKILL.md` 的三分支表补回“默认分支”，canonical 同步测试逐载体、逐单行锚住 `main / master / 默认分支`。

## 测试命令与结果

- `uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py hack/tests/test_canonical_entry_sync.py -q` → `98 passed in 6.52s`。
- `python3 hack/sync_principles.py --check` → `22 个投放面全部与真相源一致`。
- `python3 -m py_compile sdflow-init/assets/hooks/ff0-branch-guard.py` → PASS。
- `git diff --check` → PASS（无输出）。
- `uv run --with pytest pytest -q` → `1 failed, 2829 passed, 11 skipped, 3 xfailed in 291.72s`；唯一失败见 Concerns。

## Concerns

- 全量套件仍有首轮报告已记录的同一个无关失败：`test_non_posix_platforms_fail_closed_all_the_way_up_to_preflight[platform-win32]` 在 macOS / Python 3.14.6 上 monkeypatch `sys.platform="win32"` 后，`shutil.which("claude")` 因 `_winapi is None` 抛 `AttributeError`。本 fix 未修改 `sdflow-init/assets/hack/outside-voice-job.py` 或 `sdflow-init/tests/test_outside_voice_job.py`，未越界修复该基线问题。
- 按 change 的 Task 4 边界，本 fix 未运行 `init.py update --dev` 或 `setup.sh`，也未刷新全局 hook / bundle。
