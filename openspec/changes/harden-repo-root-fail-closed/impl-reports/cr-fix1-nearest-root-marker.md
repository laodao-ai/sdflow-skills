# cr-fix1 — 最近仓根 marker 上溯（代码审核心缺陷修复）

**范围**：三份 `repo_root`（`sdflow-{issues,buglist,todolist}/scripts/*.py`）+ 三份对应
`tests/test_repo_root_identity_*.py` + `pytest.ini` + 两个 CI workflow。
**四件套（proposal/design/tasks/specs）未改动**——落差登记进本报告末节，留设计门一次性回写。

---

## 1. 根因

四个独立评审来源收敛到同一处，根因是两句「证明不足」：

1. **祖先校验只证明了「`top` 是 `start` 的祖先」，没证明「`top` 是 `start` 的【最近】仓根」。**
   ⇒ 外层祖先仓库四项判据全过（缺陷 A）。
2. **回落分支只证明了「返回了绝对路径」，没证明「这是个该写的地方」。**
   ⇒ git 以非 0 退出但进程确实在仓内时，静默返回仓库子目录（缺陷 B）。

第 2 条的**成因写在旧 docstring 里**：它把非 0 退出枚举为「非 git 仓库 / git 不可用 /
bare repo / `.git/` 目录内」。**该枚举不完备**——`safe.directory`（dubious ownership）、
损坏的 `.git/config` 同样以 128 退出。把「退出码非 0」当成「不在仓库里」的判据，
是**用一个无界的失败面去冒充一个有界的语义**。

> 🔴 目标态视角（基准 2 / 通则③）：缺陷 B 在**目标态下的高频触发面不是「配置写坏」**
> （那是我用来构造复现的**人工**姿势），而是 `detected dubious ownership`——容器 / CI /
> 共享 checkout 里 git **常态性**以 128 拒答，而进程确实在仓内。用「现存语料里没见过
> 坏 config」论证「这条分支很少走」会直接误判。

---

## 2. 最终判据形态

判据从 6 步扩到 9 步（③→④⑤ 拆开、末尾加⑨）：

| # | 判据 | 变化 |
|---|---|---|
| ① / ①b | 起点可信性 + 归一化为绝对路径 | 不变 |
| ② | 环境净化（`GIT_DISCOVERY_ACROSS_FILESYSTEM` 保留在清单内） | 不变 |
| ③ | 调 git；失败**只记录** `out = None`，**不在 try 内 return/raise** | 改 |
| **④** | **最近仓根 marker 上溯**（自 `start_real` 逐级向上找第一个 `.git`） | **新增** |
| **⑤** | **git 失败裁决**：`marker_dir` 存在 ⇒ `raise`；一层都没有 ⇒ 回落 | **新增** |
| ⑥ | 形状校验 | 原④ |
| ⑦ | 祖先校验（+ `commonpath` 的 `ValueError` 三元组包装，F3） | 原⑤ + 改 |
| ⑧ | worktree marker | 原⑥ |
| **⑨** | **最近根一致**：`marker_dir == top_real` | **新增** |

**⑧ MUST 排在 ⑨ 之前**——⑨ 通过的前提是 `top_real` 自带 marker，两步顺序颠倒会让 ⑧ 变成
死代码，「重定向到**非仓库**目录」的专属诊断随之丢失。三条防线因此各守一种成因、各自可变异确认：

- 重定向到**旁系**目录 → ⑦（既有用例）
- 重定向到**非仓库**目录 → ⑧（既有用例）
- 重定向到**外层祖先仓库** → ⑨（新增用例）

### 结构约束遵守情况

- `try` 只包 `subprocess.run`：**保持**。失败分支改为 `out = None`，裁决与 `raise` 全部移到
  try 之外（步骤⑤）——这同时消除了「新抛的 `ValueError` 被自己的 `except` 接住」的隐患。
- 只捕 `OSError`/`CalledProcessError`，`TimeoutExpired` 单独 `raise`，无 `except Exception`：**保持**。
- 新增常量 `git_timeout = 30` 写在**函数体内**（F4），与 `discovery_env` 同理由——模块级常量的
  **值**不在三向 AST 镜像守护的覆盖范围内。
- 被拒值一律 `ascii(value)[:200]`；无 stdout 写入；无 `sys.exit`；`raise` 文案通用、不含脚本名/`__file__`。
- 诊断一律 `ERROR: ...; cause: ...; fix: ...`。
- 三份剥 docstring 后 `ast.dump` 相等：`test_mirror_consistency.py` **7 passed**。
- **MUST NOT parse git stderr**（基准 5）：④ 只用 `os.path.exists` 这一个确定性文件系统信号，
  未读取 stderr 一个字节。

### 已登记的必要偏离（第 2 处）

步骤⑦ 为 F3 新增了一个 `try/except ValueError` 包 `os.path.commonpath`。这是继步骤①b 裹
`os.getcwd()` 之后的**第二处**必要偏离，理由同款：try 体内**只有一个表达式、且不含本函数自己的
`raise`**，不会重演「自己的 ValueError 被自己接住」。

---

## 3. 两条缺陷：复现 → 修复前后

### 缺陷 A（Critical）· `core.worktree` 指向外层祖先仓库

构造：`outer/`（git 仓）内含 `proj/`（git 仓），`proj` 的 `core.worktree` 指向 `outer` 绝对路径；
清空全部 `GIT_*` 后调 `repo_root(proj)`。

| | 结果 |
|---|---|
| **修复前** | `RESULT: <…>/reproA/outer` ← **返回外层仓库**（四项判据全过） |
| **修复后** | `RAISED: ERROR: git 返回的仓根不是起点所属的最近仓库: '<…>/outer'; cause: 自起点上溯遇到的第一个 .git 位于 '<…>/outer/proj'，git 却返回了更外层的仓库…; fix: …` |

**同形变体（PATH 注入的 fake git 返回外层仓）**——证明⑨拦的是「答案不是最近仓根」这个**性质**，
而非 `core.worktree` 这一种成因：

| | 结果 |
|---|---|
| **修复前** | `RESULT: <…>/pathwrap/outer` |
| **修复后** | `RAISED: ERROR: git 返回的仓根不是起点所属的最近仓库…` |

### 缺陷 B（High ×3 来源）· git 非 0 退出但起点在仓内

构造：真 git 仓 `repo/`，写坏 `.git/config`（`safe.directory` 拒答的同形态：rc=128 + 起点在仓内），
从 `repo/sub` 调用。前提已真跑核验 `git rev-parse` rc=128。

| | 结果 |
|---|---|
| **修复前** | `RESULT: <…>/repo/sub` ← **返回仓库子目录**，下游会在仓内造出第二套 `openspec/issues/` |
| **修复后** | `RAISED: ERROR: 起点位于 git 仓库内但 git 拒绝作答: '<…>/repo/sub'; cause: 上溯找到 .git marker，而 git rev-parse --show-toplevel 以非 0 退出（dubious ownership / 配置损坏 / git 不可用等); fix: 修复 git 配置后重试（如 git config --global --add safe.directory <仓根>），或显式指定 --root` |

CLI 级复核（仓内只读子目录）：修复前裸 Traceback / 静默建树，修复后 `rc=0` + 单行受控诊断。

---

## 4. 合法场景实测（逐个真跑，无一误伤）

推荐修法在**所有**被要求核验的合法场景上均未误伤：

| 场景 | 修复后 | 判定 |
|---|---|---|
| 普通仓库根 | `<L>/plain` | ✅ |
| **仓库子目录**起点 | `<L>/plain` | ✅ |
| **linked worktree**（`.git` 实测为 **FILE**） | `<L>/wt` | ✅ 上溯用 `exists` 认文件形态 |
| **submodule**（`.git` 实测为 **FILE**） | `<L>/super/sub` | ✅ 返回最近的那个（submodule 自身） |
| **symlink 起点** | `<L>/plain` | ✅ 走 `start_real` |
| **嵌套仓库正常情形**（outer+inner 均为仓、无 core.worktree），从 inner 起 | `<L>/nest/inner` | ✅ **未被新判据拒掉**（关键非回归） |
| 嵌套仓库，从 outer 起 | `<L>/nest` | ✅ |
| **非 git 仓库** | 回落 `<L>/notgit`，exit 0 | ✅ 行为不变 |
| **bare repo** | 回落 `<L>/bare.git` | ✅ **行为不变**（bare 目录内无 `.git` 条目 ⇒ 上溯找不到 marker ⇒ 合法回落） |
| **`.git/` 目录内部**起点 | **`raise`**（原为回落返回 `.git/hooks` 自身） | ⚠️ **行为变更，见下** |

### 唯一的行为变更：`.git/` 内部起点

| | 行为 |
|---|---|
| 修复前 | `RESULT: <L>/plain/.git/hooks` ← 回落返回 `.git` 内部路径 |
| 修复后 | `RAISED: ERROR: 起点位于 git 仓库内但 git 拒绝作答…` |

**这是修正而非回归**：旧行为会让下游在 **git 的内部目录**里建出 `.git/openspec/issues/`——
正是本 change 要消灭的形态。上溯从 `<repo>/.git` 向上一层即命中 `<repo>/.git` marker，
「在仓里 + git 拒答」成立 ⇒ fail-closed。既有用例 `test_inside_dot_git_directory_falls_back`
（断言旧行为）已改写为 `test_inside_dot_git_directory_fails_closed`。**已登记为 spec 回写项 (h)。**

---

## 5. 变异确认（PV 规则 5）

四处新增/修改的守护，逐一确认「删掉就变红」。基线：`44 passed, 1 xfailed`。

| # | 变异 | 实际输出 |
|---|---|---|
| **1** | 删掉步骤⑨（最近根一致）整块 | `2 failed, 42 passed, 1 xfailed`<br>FAILED `test_core_worktree_redirect_to_ancestor_repo_is_rejected`<br>FAILED `test_fake_git_on_path_returning_outer_repo_is_rejected` |
| **2** | 步骤⑤ `if marker_dir is not None:` → `if False:`（退回旧的「一律回落」） | `2 failed, 42 passed, 1 xfailed`<br>FAILED `test_inside_dot_git_directory_fails_closed`<br>FAILED `test_git_refusing_inside_repo_fails_closed` |
| **3** | 步骤④ `os.path.exists` → `os.path.isdir`（打掉 `.git` 文件形态支持） | `3 failed, 41 passed, 1 xfailed`<br>FAILED `test_linked_worktree_dot_git_is_a_file`<br>FAILED `test_submodule_dot_git_is_a_file`<br>FAILED `test_linked_worktree_resolves_to_worktree` |
| **4** | 步骤⑦ 去掉 `commonpath` 的三元组包装（F3） | `1 failed, 44 passed, 1 xfailed`<br>FAILED `test_cross_drive_commonpath_gets_diagnostic_triplet` |

每次变异后均已还原并复跑确认回到 `44 passed, 1 xfailed`。

> 变异 3 的额外收获：它同时打红了**两条既有用例**，说明 `.git` 文件形态在本仓已有独立守护，
> 新增的上溯没有绕开它们。

---

## 6. 新增用例（每份 8 条 × 3 份 = 24 条）

负例（要求覆盖面全部落地）：
- `test_core_worktree_redirect_to_ancestor_repo_is_rejected` — 缺陷 A，**含前提核验**（真跑 git 确认 rc=0 且返回外层仓）
- `test_fake_git_on_path_returning_outer_repo_is_rejected` — PATH wrapper 返回外层仓
- `test_git_refusing_inside_repo_fails_closed` — 缺陷 B，**含前提核验**（真跑确认 rc≠0），`safe.directory` 同形态
- `test_inside_dot_git_directory_fails_closed` — 改写自旧的 falls_back
- `test_cross_drive_commonpath_gets_diagnostic_triplet` — F3

非回归正例：
- `test_git_refusing_outside_any_repo_still_falls_back` — 证明判据是「上溯无 marker」而非「rc≠0」，合法回落面未被一起 fail-closed
- `test_nested_inner_repo_resolves_to_inner` — 关键非回归
- `test_linked_worktree_resolves_to_worktree`、`test_repo_subdir_and_symlink_start_resolve_to_repo_root`

方法论：负例**无一** mock `os.path.isabs` / `isdir` / `realpath`，全部用 `tmp_path` 下真实路径 +
真实 `git init` 构造。唯一的注入点是 F3 用例里的 `commonpath`——注入的是**环境条件**
（跨盘符在 POSIX 上结构性不可达），与既有 `_fake_git_stdout` 注入 git 输出同性质，
**不是被测判据本身**。3 个 `xfail(strict=True)` 锚未动。

---

## 7. 一并修掉的其他项

- **F2（Medium）**：`pytest.ini` 加 `minversion = 8.0`，两个 workflow 改 `pip install "pytest>=8"`。
  已实测确认前提成立：`pytest.hookimpl` 的 `wrapper` 参数存在于 8.4.2；pytest 7.x 只有
  `hookwrapper` 且协议不同 ⇒ 仓根 conftest 收集当场抛错 ⇒ **全仓 1900 用例 collection 崩**。
  `pytest.ini` 自称「MUST NOT 承载其他配置」，注释里已说明 `minversion` 属**同一职责**：
  它是「rootdir 钉死 ⇒ conftest 一定被收集」这件事的**完整性前提**（收集得到 ≠ 收集得动）。
- **F3（Low）**：见步骤⑦，已附变异确认。
- **F4（Low）**：`timeout=30` → 函数体内局部常量 `git_timeout`，附 why 注释
  （30s 是「文件系统卡死」的判定线，不是性能预算），且超时诊断改为引用该常量、不再有第二处字面 30。

---

## 8. 全套件结果

```
1895 passed, 8 skipped, 3 xfailed in 119.61s
```

对照 carry-forward 声明的恒定量：

| 恒定量 | 基线 | 本次 | 判定 |
|---|---|---|---|
| `passed + skipped` | 1879 | **1903** | ✅ 差值 **+24** = 新增 8 条 × 3 份，全部可解释 |
| `failed` | 0 | **0** | ✅ |
| `xfailed` | 3 | **3** | ✅ 三个 strict 锚未动 |

（按 carry-forward「⚠️ 全套件数字不是确定性锚」：passed/skipped 之间会因
`test_outside_voice_child_lifecycle.py:436` 浮动，故只锚上面三个量。）

---

## 9. 须在设计门回写 spec 的条目（CF-9 续）

本次修法与 `spec.md` 现有字面表述有落差。**MUST NOT 在本 change 实现期改四件套**
（触发 `ship_gate` 设计门失鲜 REFUSE_START），故登记于此：

| # | 落差 | 事实 | 处置 |
|---|---|---|---|
| **h** | `spec.md:34,102` 把「git 非 0 退出」**整块**归为回落分支 | 该口径**不完备且正是 fail-open 的成因**：`safe.directory` / 坏 config / `.git/` 内起点同样 rc=128，而进程**确实在仓内**。实测三条全部曾静默写错位置 | 回写为：**回落的判据是「自起点上溯一层 `.git` 都没找到」**，不是退出码。git 失败且找得到 marker ⇒ `raise` |
| **i** | spec 描述的是「证明 `top` 是 `start` 所属仓库的根」 | 祖先校验 + worktree marker **只能证明「是某个祖先仓的根」**——外层祖先仓库两条全过（实测缺陷 A + PATH wrapper 变体） | 回写为「**最近**仓库的根」，并补入第 9 条判据「最近根一致」 |
| **j** | spec 把 `.git/` 目录内起点列为「正常回落场景」 | 旧行为返回 `.git` 内部路径 ⇒ 下游会在 `.git/openspec/issues/` 建树。新行为 fail-closed | 从回落场景枚举中移出，改列为 fail-closed 场景 |
| **k** | 判据步数从「六步」变为「九步」 | ③ 拆为 ③④⑤、末尾加 ⑨ | spec / design / 三份测试模块 docstring 的「六步」表述同步（测试 docstring 本次已就地更新） |

> **性质**：h/i/j 与 CF-9 已有的 a–g **不同类**——a–g 是「实现对、文档措辞旧」，
> **h/i/j 是「原设计的判据本身不足，实现在评审中被证伪后收紧」**。收尾时
> **MUST NOT** 把它们混进「纯措辞订正」一栏。

---

## 10. 本次改动**未**覆盖的残余（已登记 B17）

代码审来源提到的缺陷 B「同族表现①」——**回落到「非仓库**且**不可写」目录时仍是裸 Traceback + rc=1**
（`mkdir /tmp/ro && chmod 555 /tmp/ro && cd /tmp/ro && … next-id`）——**cr-fix1 后实测仍在**，
已记 **B17（P2）**。

**为什么不在本次修**（不是遗漏，是判断）：

1. 此处 `repo_root` **回落是正确的**——`/tmp/ro` 上溯一层 `.git` 都没有，按本次确立的判据本就该回落。
   缺陷在回落**之后**：`makedirs` 抛 `PermissionError(OSError)`，而 `main()` 只 `except ValueError`。
   ⇒ 缺陷位置在 `recorder_lock` / makedirs 层，**不在 `repo_root` 内**，超出本次「只改 repo_root」的改动面。
2. **MUST NOT 把可写性判断塞回 `repo_root`**：`next-id` / `scan` 是**只读**命令，在只读目录下读取是
   合法用法。给 `repo_root` 加可写性门会把它们一起误伤——`repo_root` 的职责是**解析**仓根，不是**授权**写入。
3. 正解（已写进 B17 的修复方案）：makedirs / lock 层把 `OSError` 转成带 `ERROR/cause/fix` 三元组的
   `ValueError`，由 `main()` 既有的 `except ValueError` 统一收口。

缺陷 B 的**仓内**那半已由本次修复覆盖并有用例守护（`test_git_refusing_inside_repo_fails_closed`）。
