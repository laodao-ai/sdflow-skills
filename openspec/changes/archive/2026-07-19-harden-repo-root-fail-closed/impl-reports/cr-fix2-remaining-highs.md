# cr-fix2 — 代码审剩余 3 High + 2 Medium

**基线**：1895 passed / 8 skipped / 3 xfailed / 0 failed
**结果**：**1911 passed / 8 skipped / 3 xfailed / 0 failed**（+16 用例）

> **恒定量只有 `failed == 0` 与 `xfailed == 3`。** `passed + skipped` 随本轮新增用例
> 1879 → 1903 → 1919，**MUST NOT 当锚**（carry-forward.md 已登记此教训）。

改动面：三份 `scripts/*.py` 的 `repo_root`、三份 `tests/test_repo_root_identity_*.py`、
`sdflow-issues/tests/test_patch_discipline.py`。四件套 / `specs/` 未触；3 个
`xfail(strict=True)` 标记本身未动。

---

## F1（High）· `text=True` 未指定 encoding ⇒ 非 ASCII 输出绕过受控失败路径

### 修法

步骤③ 去掉 `text=True` 改 **bytes 捕获**；步骤⑥ 用 `os.fsdecode(out.stdout)` 解码。

**为什么选 `os.fsdecode` 而不是显式 `sys.getfilesystemencoding()` + `errors="surrogateescape"`**：
两者**语义完全等价**（fsdecode 的定义就是这一对），但 fsdecode 是 CPython
「字节 ↔ 路径」的**标准转换点**——git 返回的正是文件系统路径，用它是在表达
"这是一条路径"，而不是"这是一段恰好用某编码编出来的文本"。显式写那一对等于把
fsdecode 的定义抄一遍，**平白多一个漂移面**（三份镜像 × 两个参数），而这个 change
的整个主题就是消灭镜像漂移面。

**为什么 fail-closed 成立**：不可解码字节被 surrogateescape 保成 surrogate（**不抛异常**），
随后 `os.path.isdir(top)` 用同一编码往回编、得到原始字节 → 路径不存在 → 落进既有的
「git 返回的仓根不可用」分支，拿到带 ERROR/cause/fix 三元组的受控诊断。
即**没有新增分支**，只是让坏输入沿既有 fail-closed 路径走。

**副作用检查**：`os.fsdecode` 对 `str` 入参原样返回 ⇒ 注入 str stdout 的既有替身用例
（`_fake_git_stdout`）零影响，实测三份 identity 套件全绿。

### 击穿路径实证（修复前）

```
$ python3 -c "subprocess.run([...], capture_output=True, text=True, env=env)"
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 5: invalid start byte
BYTES 模式同一命令: b'/tmp/\xff\xfebad\n'      # 干净
```

`UnicodeDecodeError` **是 `ValueError` 的子类** —— 故它能被 `main()` 的
`except ValueError` 接住，但**不带三元组**，诊断质量断崖；Windows 上（本仓
`test_task2_windows_local_fs_smoke.py:107` 已记载）同一成因让读管道**线程**崩掉、
`out.stdout` 变成 `None` ⇒ `.rstrip` 抛 `AttributeError`（**连 ValueError 都不是**）
⇒ `except ValueError` 接不住 ⇒ 裸 Traceback。

### 新增用例

`test_undecodable_git_stdout_fails_closed_with_controlled_diagnosis`（三份各一）——
PATH 注入 fake git，`printf '/tmp/\377\376bad\n'` 直接吐坏字节（沿用本仓
`test_fake_git_on_path_returning_outer_repo_is_rejected` 的先例）。

⚠️ 断言用 **`type(exc.value) is ValueError`（精确类型）**，不是 `pytest.raises(ValueError)`
就完事——因为 `UnicodeDecodeError` 是子类，只写 `raises(ValueError)` 会让变异**不可区分**。

### 变异确认

| 变异 | 结果 |
|---|---|
| 恢复 `text=True` | **1 failed** |
| 去掉 `fsdecode`（裸 bytes rstrip） | 本用例 1 passed（不敏感），但 `sdflow-issues/tests/` **34 failed** |

```
############ M1: 恢复 text=True ############
E       assert <class 'UnicodeDecodeError'> is ValueError
E        +  where <class 'UnicodeDecodeError'> = type(UnicodeDecodeError('utf-8', b'/tmp/\xff\xfebad\n', 5, 6, 'invalid start byte'))
FAILED ...::test_undecodable_git_stdout_fails_closed_with_controlled_diagnosis
1 failed, 49 deselected in 0.38s

############ M1b: 去掉 fsdecode ############
（本用例）1 passed, 49 deselected        ← 单点不敏感
（sdflow-issues/tests/ 全量）34 failed, 236 passed   ← 面上敏感
```

> **登记**：M1b 单点不敏感是**如实的**——该用例锚的是「解码失败不逃出受控路径」这个
> 性质，而裸 bytes 恰好也满足它（bytes 路径同样 isdir 失败 → 同一条 ValueError）。
> 「返回值必须是 str」由另外 34 个既有用例守着，两者是不同的面，无需合并到一个用例里。

---

## F2（High）· 双门 AST 守对 `MonkeyPatch` 别名形式失明

### 修法

门 A 的接收器判据从「名字字面量 == `monkeypatch`」（`func.value.id == "monkeypatch"`）
**放宽为「任意 `<expr>.setattr`」**，收窄改由**实参**承担（目标模块名为 `subprocess`、
属性为 `"run"`；或 2 参形式的字符串以 `subprocess.run` 结尾）。

**采用评审建议，未改进**——验证过它确实足够：`.setattr(<…>.subprocess, "run", …)`
这个**形状**本身已判别，绑定变量名只会引入盲区而不增加精度。
**实测放宽后本目录零新增违规**（11 passed，无需扩白名单）——即判据没有变松到误伤。

### 配套

- **重构**：`_iter_run_patch_sites(path)` 拆出 `_iter_run_patch_sites_in_source(source)`，
  让自检可以直接喂源码串（`ast` 只认源码，从文件还是从串读无语义差别）
  ⇒ **不必往 `tests/` 里落一堆诱饵文件**。
- **自检语料** `GATE_A_ALIAS_SAMPLES` + `test_gate_a_sees_monkeypatch_aliases`，四种形式：
  `mp = monkeypatch` / `pytest.MonkeyPatch()` / `pytest.MonkeyPatch.context()` /
  别名 + 2 参字符串形式。每条都断言**两件事**：门 A 看得见该站点，且裸 lambda
  **不被误认成工厂调用**（否则门 A 会判它合规）。
- **docstring 能力边界订正**：原文把「绕开 `monkeypatch.setattr` 的路径」列进"守不住"，
  但**别名形式本身就是 `monkeypatch.setattr`** ⇒ 读者会以为已覆盖。已改写为
  「绕开 `.setattr` 的路径」，并新增「接收器判据为什么不认名字」一节记录该洞与实测。

### 变异确认

```
############ M2: 恢复「接收器须名为 monkeypatch」 ############
FAILED ...::test_gate_a_sees_monkeypatch_aliases[上下文管理器 MonkeyPatch.context()]
FAILED ...::test_gate_a_sees_monkeypatch_aliases[别名 + 2 参字符串形式]
FAILED ...::test_gate_a_sees_monkeypatch_aliases[别名绑定 mp = monkeypatch]
FAILED ...::test_gate_a_sees_monkeypatch_aliases[直接实例化 pytest.MonkeyPatch()]
4 failed, 7 passed in 0.09s
```

---

## F3（High）· 任一 skill 目录出现 pytest 配置 ⇒ 仓根守护静默失效

### 落点论证（题目要求自行判断并说明）

**先说结论：不进仓根 `conftest.py`，落在三份 identity 测试文件里。**

**理由是结构性的，不是 D6 的措辞之争**：退化态**恰恰是「仓根 conftest 没被加载」**。
任何落在仓根 conftest（或仓根 `pytest.ini`、或任何仓根级集中式落点）的自检，
在它要检测的那个场景里**自己也一并出局** —— 集中式落点在这里**结构上做不到**。
∴ 自检**必须落在退化态下仍被收集的地方，即叶子**（`<skill>/tests/`）。

D6「仓根 conftest 只承载 cwd 断言、MUST NOT 塞其他共享 fixture」因此**没有被触碰**：
本轮对仓根 `conftest.py` 与 `pytest.ini` **一个字都没改**。
「自检算不算 cwd 断言的一部分」这个问题不必回答——它**不能**放在那里。

**为什么是这三份文件**：它们是本 change 拥有的、且分属三个 recorder skill 的叶子，
一次覆盖三个最需要守的 skill（三者都真做文件系统写入 + git 探测）。

**覆盖边界（如实登记，已写进用例 docstring）**：
- ✅ `pytest <recorder>/tests/`、`pytest <recorder>/tests/test_x.py` 等按 skill 的调用姿势 —— 有守。
- ✅ 全量 `pytest`（参数公共祖先 = 仓根，仓根 `pytest.ini` 先被命中）—— 不受影响。
- ❌ **其余 skill**（`sdflow-retro` / `sdflow-init` / …）的 `tests/` 下若出现 ini，
  以那个 skill 为参数单跑时**仍无自检**。这是本落点的残余，不假装全覆盖。

### 断言内容

`test_repo_root_guards_are_actually_loaded(request)` 断言三件事：

1. `Path(config.rootpath) == 仓根`（从 `__file__` 推，**不用 `config.rootpath` 自证**）；
2. `config.pluginmanager.has_plugin(str(仓根/"conftest.py"))` —— 确实注册在案；
3. 该 plugin 上 `pytest_runtest_call` 钩子仍在 —— **只查文件名不够**，一并核对 cwd
   断言的**实体**还活着。

### 变异确认

```
############ M3: 在 sdflow-issues/ 放 pyproject.toml 抢 rootdir ############
E  AssertionError: pytest rootdir=/…/04-sdflow-skills/sdflow-issues，不是仓根
   /…/04-sdflow-skills —— 多半是某个更深的目录出现了 pytest 配置段抢走了 rootdir；
   此时 confcutdir 同步塌陷，仓根 conftest.py 的 cwd 泄漏断言已经不生效了。
FAILED ...::test_repo_root_guards_are_actually_loaded
1 failed, 49 deselected in 0.02s

--- 同一退化态下，cwd 泄漏探针（对照组）---
1 passed in 0.00s        ← 用例真的往 cwd 写了文件，守护已死，却是绿的
```

对照组是这条的要害：**同一次退化里，被守护的不变量已经不设防、而它自己不会说话。**
自检把这个"无声"变成了"当场判红"。

---

## F4（Medium）· xfail 锚的前提断言写在 xfail 体内 ⇒ 前提烂掉也是绿

### 修法

前提核验从 `test_child_resolving_a_different_root_must_fail_loudly` 体内**摘出**，
新增**不带 xfail** 的 `test_child_root_drift_premise_climbs_to_outer`（三份各一），
额外加一条 `assert not (inner / ".git").exists()`（`rm -rf` 真失败时当场红）。
原位置留注释指向新用例并写明「为什么不能留在这里」。

**3 个 `xfail(strict=True)` 标记本身未动**（B15 机械锚，堵上即 XPASS 判红是有意设计）。

### 变异确认（含修复前后对照）

```
############ M4: 前提用例体内插 assert False ############
FAILED ...::test_child_root_drift_premise_climbs_to_outer
1 failed, 49 deselected in 0.06s          ← 修复后：红

--- 对照：同样的 assert False 插进 xfail 用例体内（修复前的形态）---
x
49 deselected, 1 xfailed in 0.06s         ← 修复前：绿，且 XFAIL 摘要照旧打印 R2 说明
```

---

## F5（Medium）· 诊断把 `--root` 描述成修复手段，但显式 `--root` 仍走同一次 git 探测

### 修法

`repo_root` 对显式起点与默认起点走的是**同一条**探测路径（步骤③ 不因 `start` 来源分叉）
⇒ 建议「改传 `--root`」的 6 处 `fix:` 一律删除该指引，改为**针对真实故障面**的可执行步骤：

| 分支 | 订正后的 `fix:` |
|---|---|
| ③ 超时 | 确认该目录所在文件系统未挂起（网络盘/自动挂载卷最常见），再在该目录手动跑 `git rev-parse --show-toplevel` 看是否同样卡住 |
| ⑤ git 拒绝作答 | 在该目录手动跑 `git rev-parse --show-toplevel` 看完整报错；若是 dubious ownership 则 `git config --global --add safe.directory <仓根>` |
| ⑥ 形状校验 | 在该起点手动跑 `git rev-parse --show-toplevel` 比对输出，并用 `which -a git` 确认 PATH 上的 git 未被 wrapper 替换 |
| ⑦ commonpath 无公共根 | 检查 `.git/config` 的 `core.worktree` 是否把工作树指到了另一个盘符，并清除 `GIT_WORK_TREE` / `GIT_DIR` 等重定向后重试 |
| ⑧ worktree marker 缺失 | 确认 `core.worktree` 未指向非仓库目录，并用 `which -a git` 确认 PATH 上的 git 未被 wrapper 替换 |
| ⑨ 最近根不一致 | 清除 `.git/config` 的 `core.worktree` 重定向，并用 `which -a git` 确认 PATH 上的 git 未被 wrapper 替换 |

**未改**步骤① / ①b 的两处 —— 它们指的是「起点本身」，**在 git 之前**，指引真实有效
（①b 传绝对路径确实绕开 `os.getcwd()`）。

### 面治（基准 3）：不只是改文案

F5 原本是一条**纯散文修改、无任何守护** —— 照抄旧措辞的新分支会静默复活它。
故补机械守 `test_diagnostics_never_recommend_explicit_root`（三份各一）：
剥掉 docstring 后，`repo_root` 函数体内的字符串常量一律 MUST NOT 含 `--root`
（docstring 里描述子进程 `--root <已解析值>` 传参协议是合法的，故排除）。
**守的是整片诊断面，不是当场被点穿的那 6 处。**

### 变异确认

```
############ M5: 把 ⑨ 的 fix: 改回带「或显式指定 --root」 ############
E  assert not [(1337, '…; fix: 清除 core.worktree 重定向，或显式指定 --root，
   并用 which -a git 确认 PATH 上的 git 未被 wrapper 替换')]
FAILED ...::test_diagnostics_never_recommend_explicit_root
1 failed, 49 deselected in 0.03s
```

订正后的实际诊断（真跑 fake-git 触发 ⑨）：

```
ERROR: git 返回的仓根不是起点所属的最近仓库: '/private/var/…/tmplh4w7710/outer';
cause: 自起点上溯遇到的第一个 .git 位于 '/private/var/…/tmplh4w7710/outer/inner'，
git 却返回了更外层的仓库（core.worktree 指向祖先仓 / git 被替换）;
fix: 清除 .git/config 的 core.worktree 重定向，并用 which -a git 确认 PATH 上的 git
未被 wrapper 替换
```

---

## Global Constraints 合规

| 约束 | 状态 |
|---|---|
| `try` 只包 `subprocess.run`；校验与 raise 在 try 外 | ✅ 未新增 try；F1 是**去掉**参数 + try 外解码 |
| 只捕 `OSError`/`CalledProcessError`，`TimeoutExpired` 单独 raise，禁 `except Exception` | ✅ except 子句一字未动 |
| 新增常量 MUST 在函数体内，MUST NOT 模块级 | ✅ **本轮零新增常量**（`os.fsdecode` 是调用，非常量） |
| 被拒值 `ascii(value)[:N]`；禁 stdout；禁 `sys.exit`；文案不含脚本名 | ✅ 未动 |
| 诊断格式 `ERROR: …; cause: …; fix: …` | ✅ 只换 `fix:` 内容，三元组结构保持（用例断言三段齐全） |
| 三份 MUST 同步、剥 docstring 后 `ast.dump` 相等 | ✅ `test_mirror_consistency.py` 7 passed（三份由同一脚本逐字同步打入） |
| 基准 5：不新增解析器、不 parse git stderr | ✅ 新增的 AST 遍历是 **Python 语法面（有界，且用 stdlib `ast`，非手搓）**；未碰 git stderr |
| PV 规则 5：每条守护有「删掉就变红」的变异确认 | ✅ M1/M2/M3/M4/M5 五条，实际输出见上 |

## 新发现

1. **`UnicodeDecodeError` 是 `ValueError` 的子类** —— 意味着"用 `pytest.raises(ValueError)`
   断言 fail-closed"这一类用例**天然对解码故障不敏感**。本轮的 F1 用例已用精确类型断言
   规避；**其余以 `raises(ValueError)` 为终态断言的用例仍带这个盲区**（未展开排查，登记备查）。
2. **M1b 揭示的口径分工**：单个用例锚"性质"而非"实现"是对的，但要**如实登记它不敏感的变异**
   ——本报告已按面（34 个既有用例守 str 返回值）交代，未把两个面塞进一个用例假装全覆盖。
3. **仓外 shell 环境有 `git` shim**：本机 zsh 下裸跑 `git rev-parse` 会被劫持到某个
   `open-design` 项目的 pnpm 脚本（首次探测时撞到）。**不影响测试**（Python
   `subprocess.run(["git", …])` 走 execvp、不经 shell 别名），但**手工在终端复现
   git 相关用例时会看到莫名其妙的输出**，登记备查。
