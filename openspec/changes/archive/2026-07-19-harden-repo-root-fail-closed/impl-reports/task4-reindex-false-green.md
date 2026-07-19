# Task 4 — 消除 reindex 假绿测试（R5）

**Blocked-by:** 2（已完成）· **R-ID:** R5 · **承接:** CF-1（面级 blanket mock 改造）

---

## 1. mock 站点实测数量与逐个处置

**自己重新数了一遍**（`grep -n 'issues_mod.subprocess, "run"'`），全仓 **12 处**，与 CF-1 记录的 12 一致：
`test_task4_rename_snapshot.py` 5 处 + `test_issues.py` 7 处。

### 分类：并非 12 处都是「整体替换」

按「是否对非目标子进程透传真实行为」把 12 处分成三类：

| # | 文件:行（改前） | 形态 | 处置 |
|---|---|---|---|
| 1 | `test_task4_rename_snapshot.py:140` | **整体替换** `lambda *_a, **_k: Proc()` | ✅ 改 argv 分派 |
| 2 | `test_task4_rename_snapshot.py:165` | **整体替换**（**本票目标用例**） | ✅ 改 argv 分派 |
| 3 | `test_task4_rename_snapshot.py:218` | **整体替换**（内部按 `command[1]` 分 pool，但对 `git` 也返 `Proc`） | ✅ 改 argv 分派 |
| 4 | `test_task4_rename_snapshot.py:267` | **整体替换** `no_subprocess` → 任何子进程即 `AssertionError` | ✅ 收窄为「只对 recorder scan 断言不得调用」 |
| 5 | `test_task4_rename_snapshot.py:773` | 已 argv 分派（`observe_run` 透传 `real_run`） | 无需改 |
| 6 | `test_issues.py:341` | 整体替换 `boom` 抛 `CalledProcessError` | **保留**——见下方论证 |
| 7 | `test_issues.py:411` | **整体替换** `fake_run(cmd, capture_output, text)` | ✅ 改 argv 分派 |
| 8–12 | `test_issues.py:1611 / 1644 / 1676 / 1711 / 1755` | 已 argv 分派（5 处均透传 `real_run`），CF-1 提到的样板 `1609` 即此族 | 无需改 |

⇒ **真正需要改造的是 5 处**（#1 #2 #3 #4 #7），另 6 处（#5 #8–#12）**本已是目标形态**，
1 处（#6）是**故意为之且正确**。

### #6 为什么保留（唯一的例外，须显式论证）

`test_falls_back_to_abspath_when_git_command_raises` 的被测对象**就是 `repo_root` 自己**——
它要验证的正是「git 抛 `CalledProcessError` → 回落 `abspath(start)`」这条分支。
此处劫持 `git rev-parse` 不是**副作用**，而是**断言本体**。改成 argv 分派透传会让该用例失去测试对象。
> 判据：blanket mock 的危害是「劫持了被测函数之外的调用」；这里 git 调用**在**被测函数之内。

---

## 2. 面级改造方案

在 `test_task4_rename_snapshot.py` 新增两个模块级 helper（单一源，5 个站点复用其中 4 个）：

- `_is_recorder_scan(command)` — 判据 `isinstance(command, (list, tuple)) and len(command) > 1 and "scan" in command`。
  依据是 `_scan_pool` 实测的命令形状 `[sys.executable, script, "--root", root, "scan", "--json"]`
  （`issues.py:1348-1350`，已打开确认）。**不解析 argv 语法**（基准 5：不新增解析器），只做成员判定。
- `_scan_only_run(handler)` — 返回一个按 argv 分派的 `subprocess.run` 替身：
  命中 recorder scan → 交给 `handler`；**其余一切子进程（尤其 `repo_root` 的
  `git rev-parse --show-toplevel`）透传 `real_run` 真实行为**。docstring 内联写明了
  「为什么 MUST NOT 整体替换」的假绿机理，防止后续被「简化」回去。

`test_issues.py:411` 因所在文件无该 helper，就地按同款模式写（透传 `real_run`），
与该文件已有的 5 个 argv 分派站点（#8–#12）风格一致。

---

## 3. 变异验证（PV 规则 5 · spec Scenario「变异验证——写入即变红」）

变异体：在 `issues.py:_reindex_core` 开头无条件向 `<root>/openspec/issues/INDEX.md` 写入 `b"MUTATED\n"`。

### 3a. 变异态 → **变红**（实际输出）

```
E       AssertionError: assert b'MUTATED\n' == b'old-index\n'
E         At index 0 diff: b'M' != b'o'
sdflow-issues/tests/test_task4_rename_snapshot.py:214: AssertionError
FAILED ...::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[None]
FAILED ...::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[7]
FAILED ...::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[bad_id2]
FAILED ...::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[bad_id3]
================== 4 failed, 4 passed, 83 deselected in 0.10s ==================
```

4 个参数化用例 **4/4 变红**。

### 3b. 撤销变异 → **变绿**（实际输出）

```
sdflow-issues/tests/test_task4_rename_snapshot.py ........               [100%]
======================= 8 passed, 83 deselected in 0.06s =======================
```

### 3c. 假绿判据的正面证据（**同一变异下旧形态恒绿**）

仅「改后变红」还不足以证明改前是假绿——改前该用例本就红（红在 root 诊断上），
无法直接观察其派生字节断言。故另跑一次**对照实验**：把用例还原成旧形态
（整体替换 `subprocess.run`），保留同一个变异体，只留派生字节断言：

```
scratchpad/test_false_green_proof.py ....                                [100%]
============================== 4 passed in 0.02s ===============================
```

**同一个变异**：旧形态 4 passed（**完全看不见**），新形态 4 failed。
⇒ 假绿判据被实证坐实：旧断言的成立与「派生字节是否被保护」无关，只与「reindex 压根没访问过目标目录」有关。
（对照脚本是 scratchpad 一次性产物，不入仓。）

---

## 4. 验收框逐条证据

### ☑ root 解析不再受全局 `subprocess.run` mock 污染，reindex 真正作用于临时目录

**证据（行为级，非源码级）**：改前诊断是
`ERROR: git 返回的仓根不可用: '{"bugs": [...' ...`（崩在 `repo_root` 形状校验），
改后诊断是 `... scan item[0].id ...`——该文案由 `validate_scan_envelope` 产出，
其调用链为 `main → cmd_reindex → _reindex_core → read_pool → _scan_pool → validate_scan_envelope`，
**只有 root 解析成功、reindex 真跑到 `tmp_path` 才可能出现**。

### ☑ 变异验证：写入即变红，恢复即变绿

见 §3，两次实际输出已录。

### ☑ 断言集完整

用例现有断言（`test_task4_rename_snapshot.py`）：

| 断言 | 覆盖的 spec 要求 |
|---|---|
| `exc_info.value.code == 2` | 受控退出 |
| `diagnostic.startswith("ERROR: ")` | 诊断格式 |
| `"scan item[0].id" in diagnostic` | **可区分性**——坏 scan id 的专属诊断 |
| `"仓根" not in diagnostic`（**新增**） | **反向可区分性**——排除「崩在 root 解析关口」 |
| `"; cause:" / "; fix:" in diagnostic` | 诊断格式 |
| `"Traceback" not in diagnostic` | 无 traceback |
| `index/batches.read_bytes()` 不变 | 派生字节 |
| `set(os.listdir(".")) - cwd_before == set()`（**新增**） | **cwd 无新增条目**（tasks 2.3） |

「MUST NOT 仅凭退出码判定通过」不仅满足，还**双向加固**了：
既断言「必须出现坏 scan id 的诊断」，又断言「必须不出现坏 root 的诊断」——
后者是对 Global Constraint「在更早的关口崩了会被误判为测中了目标」的正面机械守。

> cwd 断言此处**就地写在用例内**，而非依赖 Task 5 的根级 `conftest.py` autouse fixture：
> tasks 2.3 把它列为本用例断言集的一部分，且 Task 5 尚未落地。二者不冲突——
> Task 5 落地后这条是冗余但无害的局部锚。

### ☑ 未暴露新的 reindex 分支失败（tasks 2.4 无 fold 需求）

修复后 reindex 首次真正在这 4 个参数化用例下执行到 `_reindex_core`，
`sdflow-issues/tests/` 247 项全绿、全套件 0 failed ⇒ **没有此前从未执行过的分支失败被暴露**。
无 fold 项。

---

## 5. 全套件前后对比

| | failed | passed | skipped | xfailed |
|---|---|---|---|---|
| **改前**（dispatch 给出的基线） | **4** | 1860 | 3 | 3 |
| **改后**（实测） | **0** | 1863 | 4 | 3 |

- 4 个 failed 全部转绿，即本票目标用例的 4 个参数化实例。
- 总数守恒（1870 = 1870）。
- 3 个 `xfail(strict=True)`（Task 3 的 R2 跨进程缺口锚，B15）**保持 xfailed，未被触碰、未 XPASS**。
- 仓根 `find . -maxdepth 1 -name '{*'` **无输出**。

**skipped 3→4 已定位**（`pytest -rs` 实跑，非推测）。4 条 skip 全部是环境/概率依赖，与本票无关：

| skip | 性质 |
|---|---|
| `test_task2_windows_local_fs_smoke.py:59` / `:101` | `requires actual Windows local disk`（恒 skip，macOS） |
| `test_outside_voice_utf8.py:822` | M3 磁盘写满前提未建立（commit `91bc707` 已知，本地专属） |
| **`test_outside_voice_child_lifecycle.py:436`** | **本次多出的这一条**——「15 次高频混合信号风暴本轮一次都没复现」，用例自身 docstring 记载复现率环境敏感（105 次跨方法/跨版本实测），属**概率性 skip**，逐轮浮动 |

⇒ 3→4 的差额来自 `test_outside_voice_child_lifecycle.py:436` 的概率性 skip，
与本票改动（仅动 `sdflow-issues/tests/` 两个文件的 mock 粒度，未改任何 `scripts/`、
未触碰任何带 `skipif` 的用例）**无因果路径**。该用例的 skip 消息明写
「MUST NOT 因为本用例经常 skip 就删除它」——本票遵守，未动。

---

## 6. 未碰清单（合规声明）

- **未碰 `repo_root` 本体**（三份任一）。本票纯测试侧改造，无需改实现——
  修复路径是「让 mock 别劫持 git」，而非「让 `repo_root` 容忍坏输入」。
  `git checkout sdflow-issues/scripts/issues.py` 已撤销变异体，`git diff --stat` 确认改动仅
  `test_issues.py` + `test_task4_rename_snapshot.py` 两个文件。
- **未碰** `proposal.md` / `design.md` / `tasks.md` / `specs/`（不触发设计门失鲜）。
- 三份 `repo_root` AST 镜像一致性：`scripts/` 零改动 ⇒ 结构上不可能漂移；
  `test_mirror_consistency.py` 在全套件内绿。
