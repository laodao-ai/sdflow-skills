# Task 2 双轴审第 1 轮返修（fix1）

**范围**：F1（Important）+ M1/M2/M3（Minor，同文件同函数，面治不点补）。
**触面**：`sdflow-ship/scripts/ship_gate.py`（`_git_env`）、`sdflow-ship/tests/test_gate_git_layer.py`。
**未触**：`proposal.md` / `design.md` / `specs/` / `tasks.md`（设计意图非本期作者）；`superpowers-plan.md` 复选框未勾。

---

## F1 — 环境面未封死：global gitconfig 仍是外部可控的判定输入通道

### 选型：`GIT_CONFIG_GLOBAL` / `GIT_CONFIG_SYSTEM` 回填空设备（**非** `-c` 逐项覆盖）

**依据**：

1. **不破坏 denylist 口径**。剔除仍是全 `GIT_*` 前缀，两个键是**剔干净之后由本进程写死**的 —
   本进程注入 ≠ 外部可控。外部若预置 `GIT_CONFIG_GLOBAL=/attacker.gitconfig`，先被 denylist 剔掉，
   再被覆盖，两道都过（已由 `test_env_is_a_denylist_not_an_allowlist` 机械守）。
2. **面治**。`-c i18n.logOutputEncoding=UTF-8 -c log.showSignature=false` 是**点名已知 knob**，
   与本函数当初选「剔全前缀而非点名 `GIT_DIR`/`GIT_ICASE_PATHSPECS`」的理由同构地错：config 键集只增不减，
   点名等于承诺「git 不再新增能改变输出的配置项」。整片禁读一次覆盖整个 config 面。
3. **跨平台可移植（已查证，非想当然）**。空设备是 git **官方文档**给的写法 —— `man 1 git` 第 1199-1206 行：
   > GIT_CONFIG_GLOBAL, GIT_CONFIG_SYSTEM … **Can be set to /dev/null to skip reading configuration
   > files of the respective level.**

   代码里取 `os.devnull` 而非字面量 `"/dev/null"`：Windows 上它就是原生 `nul`（Git for Windows 的
   compat 层对 `/dev/null` 和 `nul` 都认，用平台原生值免赌 compat 映射）。

**代价 / 边界（显式登记）**：

- repo-local `.git/config` **未**封 —— 那是被判仓自身的一部分（越权改它 git 留痕可审计），不属「外部环境态」。
  判定不因它改变，仍由既有 `test_verdict_is_identical_under_polluted_git_env`（`diff.ignoreSubmodules=all`）守。
- 子进程从此读不到 global 的 `user.name` 等 —— 本文件只做只读查询（`log`/`rev-parse`/`ls-tree`/`show`/
  `cat-file`），不写对象，无影响。
- **连带修**：旧用例 `test_non_git_prefixed_vars_pass_through` 的透传探针**本身就是 F1 那个洞**
  （它用 `XDG_CONFIG_HOME` 指一份 global gitconfig，证明的正是「外部 global config 真被 git 读到」）。
  改用不经 config 面的行为级探针 `PAGER` → `git var GIT_PAGER`，透传口径不减（仍是行为级证据，
  非对 helper 内部实现的断言），且 allowlist 化时照样变红。

### 新增守卫（与评审方实测同形）

| 用例 | 层级 |
|---|---|
| `test_global_gitconfig_cannot_alter_judgment_input` | **判定输入级**：`$HOME/.gitconfig` + `$XDG_CONFIG_HOME/git/config` 双埋 `i18n.logOutputEncoding=GBK` + `log.showSignature=true`，断言 `run_git(log -1 --format=%s)` 逐字仍是 `主题中文` |
| `test_verdict_is_identical_under_polluted_global_config[fresh/stale]` | **判定结论级**：端到端跑脚本（HOME/XDG 经子进程 env 传入），污染前后 `(退出码, verdict)` 相等 |
| `test_config_files_are_neutralized_in_child_env` | **口径级**：两个键 == `os.devnull`（守「先剔后填」的顺序） |

### 变异证明 F1（删掉 `_git_env` 里那两行注入）

3 条变红：`test_global_gitconfig_cannot_alter_judgment_input`、
`test_config_files_are_neutralized_in_child_env`、`test_env_is_a_denylist_not_an_allowlist`。

修复前实测输出（即评审方那个现象，逐字复现）：

```
E       AssertionError: global gitconfig 翻转了判定输入（HOME/XDG 是非 GIT_ 前缀通道，denylist 拦不住）
E       assert '��������' == '主题中文'
E         - 主题中文
E         + ��������
```

修复后同一断言：`run_git(...) == '主题中文'`，绿。变异已还原（`cp` 回备份 + `git diff` 核对）。

> 附独立复现（裸 git，非经本脚本）：`HOME` 置含 `i18n.logOutputEncoding=GBK` 的 gitconfig 后
> `git log -1 --format=%s` 输出 `��������`；加 `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null`
> 后输出 `主题中文`。git 2.50.1。

---

## M1 — 与 buglist 先例的差异登记

已读先例 `sdflow-buglist/scripts/buglist.py:613-618`：它只剔 discovery 类
（`GIT_DIR`/`GIT_WORK_TREE`/`GIT_COMMON_DIR`/`GIT_CEILING_DIRECTORIES`/`GIT_INDEX_FILE`/
`GIT_DISCOVERY_ACROSS_FILESYSTEM`/`GIT_CONFIG_COUNT`/`GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` +
`GIT_CONFIG_KEY_`/`GIT_CONFIG_VALUE_` 前缀），**刻意保留执行类**（`GIT_EXEC_PATH` 等）。

`_git_env` 剔全前缀 ⇒ 连 `GIT_EXEC_PATH` 一并剔。差异 + 理由 + **代价**已写进 docstring：
本文件只调 builtin 子命令，保留执行类无收益，而枚举「哪些算执行类」要长期跟 git 版本（正是本函数
拒绝的那种承诺）；代价 = 日后若引入非 builtin 子命令，git 可能找不到它而 rc≠0 → `run_git` 返 `""`
⇒ **静默降级而非 UNKNOWN**，届时 MUST 改为按 buglist 口径分类剔除，而非打特例补丁。
（登记项，本轮不改行为。）

## M2 — 单出口守卫扩到整片子进程写法

`SPAWN_RE = subprocess\.(?:run|Popen|call|check_call|check_output)\(|os\.system\(`，
断言 `findall(src) == ["subprocess.run("]`（列表相等而非计数，报错直接点名越界写法）。

**变异证明**：往 `ship_gate.py` 插一句 `subprocess.Popen(['git','status'])` →
`At index 0 diff: 'subprocess.Popen(' != 'subprocess.run('`，红。已还原。

## M3 — 拆掉硬编码的 `== 30`

`test_timeout_bound_is_the_shared_constant` 只断言 `seen["timeout"] == _sg.GIT_TIMEOUT_SECONDS`；
值本身另立 `test_shared_timeout_constant_value`。

**变异证明**：常量改 30→45 → **只有** `test_shared_timeout_constant_value` 红
（`where 45 = _sg.GIT_TIMEOUT_SECONDS`，文案准确），`..._shared_constant` 保持绿 —— 误导性变红已消。
（31 passed, 1 failed。）已还原。

---

## 测试结果

- `sdflow-ship/tests/test_gate_git_layer.py`：**32 passed**（基线 27，+5：F1 三条 + 拆分出的常量值 + `verdict_identical_under_polluted_global_config` 的第二个 param）
- `sdflow-ship/tests/`：**350 passed**
- 仓根全套件：**2103 passed, 8 skipped, 3 xfailed**（基线 2097 passed / 9 skipped）
  - +6 = 本轮 +5，另 +1 是 `test_outside_voice_child_lifecycle.py:436` 的高频信号风暴用例本轮**恰好复现**
    （该用例自述复现率环境敏感、经常 skip），与本次改动无关。

## 收尾

`git status --porcelain`（变异全部还原后）：

```
 M openspec/issues/todolist/2026-07-todolist.md      ← 前一轮评审留下的 T200/T201 记录，非本轮改动
 M sdflow-ship/scripts/ship_gate.py
 M sdflow-ship/tests/test_gate_git_layer.py
?? openspec/changes/harden-gate-git-layer/impl-reports/task2-review-package.diff
```
