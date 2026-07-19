# Task 2 — `repo_root` 六步身份校验（三份同步）

**R-ID**：R1（仓根解析证明根的身份）· R3（三份逐字一致）
**tasks 覆盖**：1.1 / 1.3 / 1.3b / 1.3c / 1.4 / 1.5 / 1.6 / 1.7 / 1.8 / 1.10
**未碰**（属 Task 3/4）：1.2 / 1.2b / 1.2c / 1.9 / 1.11 / 2.x

---

## 1. 做了什么

### 实现（三份同步，同一提交）

- `sdflow-issues/scripts/issues.py`
- `sdflow-buglist/scripts/buglist.py`
- `sdflow-todolist/scripts/todolist.py`

三份 `repo_root` 的**函数体逐字节同款**（由脚本从 issues.py 抽体后注入另两份生成，非手抄），
docstring 各自不同（合法漂移，被 `_ast_no_doc` 剥离）。签名 `repo_root(start=".")` →
`repo_root(start=None)`。

### 测试（三份各一，共 27 × 3 = 81 例）

- `sdflow-issues/tests/test_repo_root_identity_issues.py`
- `sdflow-buglist/tests/test_repo_root_identity_buglist.py`
- `sdflow-todolist/tests/test_repo_root_identity_todolist.py`

> 文件名带 skill 后缀：本仓 `tests/` 无 `__init__.py`，同名 basename 会让 pytest
> 收集期 `import file mismatch` 直接报错（实测），既有惯例本就是全仓唯一 basename。

### 附带修复（fold，非 defer）

`sdflow-buglist/tests/test_task3_frontmatter_writer.py::test_noncanonical_request_does_not_alias_canonical_or_legacy_spelling[A7]`
——详见 §5。

---

## 2. 六步判据的最终形态

```
① 起点可信性  start is None → os.getcwd()（FileNotFoundError → 受控 ValueError）
              start 显式    → os.path.isdir(start)，否则 ValueError
② 环境净化    从 recorder_child_env("git", token=False) 的副本中剔除
              9 个具名变量 + GIT_CONFIG_KEY_* / GIT_CONFIG_VALUE_* 两个前缀族
③ 调 git      try 只包 subprocess.run(..., env=env, timeout=30)
                except TimeoutExpired          → raise ValueError（不回落）
                except (OSError, CalledProcessError) → return abspath(start)（回落）
④ 形状校验    top = stdout.rstrip("\r\n")；非空 ∧ isabs ∧ isdir
⑤ 祖先校验    commonpath([normcase(realpath(start)), normcase(realpath(top))])
              == normcase(realpath(top))                        ← 主防线
⑥ marker      os.path.exists(join(realpath(top), ".git"))       ← exists 而非 isdir
返回          os.path.realpath(top)
```

### 结构硬约束的落实

| 约束 | 落实情况 |
|---|---|
| `try` 只包 `subprocess.run` | ✅ 该 try 的 body 只有一条 `subprocess.run(...)` 赋值 |
| 只捕 `OSError` / `CalledProcessError` | ✅ |
| `TimeoutExpired` 单独 `raise` | ✅ 且置于两个 except 之前（它不是 `OSError` 子类，顺序上仍显式前置以防未来误改） |
| 一切校验与 `raise` 在 try 之外 | ✅ ④⑤⑥ 全在 try 之后 |
| 禁 `except Exception` | ✅ 全函数无 |
| 黑名单为**函数体内局部常量** | ✅ `discovery_env` / `discovery_env_prefixes` 是局部变量，随函数进 AST 三向比较、也随函数被 T170 搬走 |
| 不在 helper 内 `sys.exit` | ✅ |
| 不写 stdout | ✅ |
| `raise` 消息通用、不含脚本名 / `__file__` | ✅（三份消息逐字相同，故 AST 等价才成立） |
| 被拒值用 `ascii(value)[:N]` | ✅ N=200，三处被拒值全部经 `ascii()` |
| 诊断格式 `ERROR: …; cause: …; fix: …` | ✅ 五条消息全部同款 |

### ⚠️ 对「try 只包 subprocess.run」的一处**必要偏离**（显式登记，非疏忽）

步骤①在 `start is None` 分支里有第二个 `try`：

```python
try:
    start = os.getcwd()
except FileNotFoundError:
    raise ValueError("ERROR: 无法确定仓根探测起点; ...") from None
```

**为什么不违反该约束的意图**：约束的理由是「否则新抛的 `ValueError` 会被自己的 except 接住，
fail-closed 归零」。这个 except 只捕 `FileNotFoundError`，**结构上不可能接住任何 `ValueError`**。

**为什么无法消除**：spec 明文要求 `os.getcwd()` 的 `FileNotFoundError` 转为受控 `ValueError`，
而 `os.getcwd()` 没有非异常的探测形式；唯一的无 try 写法 `os.path.isdir(".")` 被 spec 与 ADR-7
**显式禁止**（cwd 被删后它仍返回 `True`）。

---

## 3. 每个验收框的证据

| 验收框 | 证据 |
|---|---|
| 六步判据三份逐字一致，`determinism-guards` 三向 AST 等价保持绿 | `pytest sdflow-buglist/tests/test_mirror_consistency.py` → **7 passed**（`repo_root` 在 `THREE_WAY` roster 内） |
| 形状负例各自被拒 + 断言路径未被创建 | `test_shape_negatives_are_rejected`（6 参数：空串 / 纯空白 / `\n` / `relative/path` / `./relative` / 不存在的绝对路径）+ `test_multiline_stdout_is_rejected` + `test_trailing_space_is_preserved_not_stripped`；每例断言 `_entries(repo) == [".git"]` 且目标路径 `not exists` |
| `core.worktree` 回归用例存在 **且删掉祖先校验后变红** | `test_core_worktree_redirect_is_rejected`；变异确认见 §4 |
| `GIT_DIR`/`GIT_WORK_TREE`：净化后返回真实根 + 不净化时祖先校验独立拦得住 | `test_git_dir_and_work_tree_env_are_sanitized`（第一层）+ `test_ancestor_check_independently_catches_unsanitized_env`（第二层）；两条各有独立变异确认，见 §4 |
| 起点负例：调 git 前被拒且不被创建 | `test_missing_start_directory_is_rejected_before_calling_git` / `..._file_as_start_...` / `..._empty_string_...`——三例都用 `_forbid_subprocess()` 把 `subprocess.run` 换成**抛 AssertionError** 的桩：git 一旦被调用，测试立即以「git 不该被调用」失败。这是「先于调 git」的机械证明，不是时序推测 |
| 进程 cwd 被删除 → 受控失败 | `test_deleted_process_cwd_yields_controlled_failure`：子进程内 `chdir` → `rmdir` → 先断言 `os.path.isdir('.') is True`（前提核验，锚 ADR-7 的实测依据）→ 调 `repo_root()` → 断言 `CONTROLLED:ERROR: 无法确定仓根探测起点` 且 stderr 无 `Traceback` |
| 超时负例：受控失败且不回落 | `test_timeout_raises_and_does_not_fall_back`（断言 `ValueError` + `subprocess.run` **确实收到了正数 `timeout` kwarg**）+ `test_timeout_with_real_hanging_git`（PATH 注入真实 `sleep` shim，让 subprocess 自己触发 `TimeoutExpired`） |
| 正向回归 | `test_returns_root_from_nested_subdirectory` / `test_symlinked_start_resolves_to_real_root` / `test_linked_worktree_dot_git_is_a_file` / `test_submodule_dot_git_is_a_file` / `test_falls_back_outside_any_git_repo` / `test_bare_repo_falls_back` / `test_inside_dot_git_directory_falls_back` / `test_cli_still_exits_zero_outside_any_git_repo`（CLI 真跑，issues=`reindex`、buglist/todolist=`scan`，断言 exit 0 且 stderr 无 `Traceback`） |
| 1.3b cwd 不变性**双态**对照 | `test_bad_relative_value_rejected_regardless_of_cwd`：同一坏值 `"lure"` 在「cwd 下确有 `lure/` 目录」与「cwd 下没有」两个 cwd 各跑一次，断言两次结论**相同**，并断言仓外 cwd 目录仍为空 |

**方法论合规**：全部 81 例**无一** mock `os.path.isabs` / `isdir` / `realpath`。被替换的只有
两类外部依赖行为——git 的 stdout 内容、git 的挂死；判据本身一律走真实文件系统。
linked worktree / submodule 两例先断言 `.git` 真的是**文件**（前提核验），再断言返回值。

---

## 4. 变异确认（PV 规则 5 · 两次实际输出）

### 变异 ①：删除祖先校验（第⑤步 → `pass`）

```
=== MUTANT RUN (祖先校验被删除) ===
E           Failed: DID NOT RAISE <class 'ValueError'>
FAILED ...::test_core_worktree_redirect_is_rejected
FAILED ...::test_ancestor_check_independently_catches_unsanitized_env
2 failed, 25 deselected in 0.14s
```

```
=== RESTORED RUN ===
..                                                                       [100%]
2 passed, 25 deselected in 0.12s
```

⇒ 祖先校验的存在被两条用例独立证明；删掉它，`core.worktree` 缺口静默回归的路径当场变红。

### 变异 ②：删除环境净化（第②步 → `pass`）

```
=== MUTATION 2: 删除环境净化 ===
E  ValueError: ERROR: git 返回的仓根不包含探测起点: '.../test_git_dir_and_work_tree_env0/other';
   cause: 工作树被 core.worktree 或环境变量重定向到起点之外; ...
FAILED ...::test_git_dir_and_work_tree_env_are_sanitized
1 failed, 1 passed, 25 deselected in 0.18s
```

恢复后 `34 passed`（mirror + 全量 identity 套件）。

⇒ **两层防御各自独立有效**已被机械证明：删掉净化 → 净化用例红（且红在祖先校验上，正好实证
design 表格里「`GIT_DIR` 两层都能拦」那一格）；删掉祖先校验 → `core.worktree` 用例红
（净化对它零效果，实证「唯一防线」）。

> 变异期间原文件已 `cp` 备份并逐次还原，两次还原后均跑绿再继续。

---

## 5. 12 个 mock 站点的实际表现与判断

**结论：12 个里 5 个变红，7 个仍绿——且 7 个的绿经核对是「真绿」，不是退出码碰撞。**
按 dispatch 要求，**一个 mock 站点都没有改**（Task 4 scope）。

### 变红的 5 个（全部在 `sdflow-issues/tests/`）

| 站点 | 用例 | 红在哪 / 为什么 |
|---|---|---|
| `test_issues.py:339` | `TestRepoRoot::test_falls_back_to_abspath_when_git_command_raises` | 桩签名是 `boom(cmd, cwd=None, capture_output=True, text=True, check=True)`——新实现多传了 `env=` 与 `timeout=` ⇒ `TypeError`。旧代码的 `except Exception` 把它一并吞掉、走回落，**测试是靠这个吞咽通过的**；except 收窄后 `TypeError` 裸传播。⚠️ 这条本身就是一个被 `except Exception` 掩盖的假绿 |
| `test_task4_rename_snapshot.py:165` ×4 参数 | `test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[None/7/bad_id2/bad_id3]` | `assert "scan item[0].id" in diagnostic` 失败，实得 `ERROR: git 返回的仓根不可用: '{"bugs": [{"id": {}, ...`。**这正是本 change 开篇断言的假绿被当场证伪**：该用例此前「preserves_derived_bytes」成立的真实原因是 reindex 全程没访问 `tmp_path`（root 被解析成那段 JSON），而不是派生字节受保护 |

> 🔴 这 4 个用例现在报的是**坏 root**、不是**坏 scan id**——两者都 exit 2，但 stderr 可区分，
> 断言正是靠 `scan item[0].id` 把它们分开的。**这条断言救了这次判断**，也正是 spec
> 「拒绝理由必须可区分」要求的形状。修复归 Task 4（tasks 2.1，按 CF-1 做**面级** argv 分派）。

### 仍绿的 7 个——逐个核对，不当作通过信号

按 dispatch 要求真读了 ≥2 个（实际读了 4 个），判断如下：

| 站点 | 判断 |
|---|---|
| `test_task4_rename_snapshot.py:140` | **真绿**。调的是 `_reindex_core(str(tmp_path))`，**不经 `main()`** ⇒ 全程不调 `repo_root`。且断言是 `pytest.raises(ValueError)` + 派生字节不变，`tmp_path` 真实存在，写入路径真实生效 |
| `test_task4_rename_snapshot.py:218` | **真绿**，同上（`_reindex_core` 直调），且 `pytest.raises(ValueError, match=field)` 带内容匹配，不是裸退出码 |
| `test_issues.py:409` | **真绿**。直调 `read_pool(str(tmp_path))`，与 `repo_root` 无交集；断言 `"simulated subprocess failure" in str(exc)`，有内容锚 |
| `test_issues.py:1609` | **真绿**，且**这就是 CF-1 推荐的目标形态**：桩已按 argv 分派（`if "scan" in cmd: ...; return real_run(cmd, **kwargs)`），非 scan 的调用透传真实行为；且直调 `cmd_sweep(args)` 不经 `main()`。**Task 4 做面级改造时可直接以它为样板** |
| `test_task4_rename_snapshot.py:267/773`、`test_issues.py:1642/1674/1709/1753` | 未逐条精读，但全部是「直调 `cmd_*` / `_reindex_core`、不经 `main()`」或「argv 分派 + 透传」两种形态之一 —— 与上面四条同族。**列为 Task 4 复核项，不由本票背书** |

> 结论要点：**「不经 `main()`」是这 7 个仍绿的共同原因**，不是「加固没生效」，也不是退出码碰撞。
> `repo_root` 只在 `main()` 入口被调用（这与 ADR-5 登记的契约一致：`cmd_*` 信任调用方已校验 `args.root`）。

---

## 6. 附带修复（fold）：`test_task3_frontmatter_writer.py[A7]`

**不属 12 个 mock 站点**，是我这一票的加固**直接触发**的第 6 个红。

- **现象**：`assert add.returncode == 0` 失败（该行是 `test_noncanonical_request_does_not_alias_canonical_or_legacy_spelling`
  的第二段，`canonical_root = tmp_path / "canonical"` **从未 mkdir**）。
- **根因**：该用例依赖的是旧的宽松行为——`--root` 指向不存在的目录时回落 `abspath(start)`，
  再由下游 `os.makedirs` 把它**静默具现**出来。**这正是 design 失败模式表里
  「`--root` 指向不存在/非目录 → 下游 makedirs 具现该坏路径」那一行要消灭的行为。**
- **判断**：不是加固写错了，是**测试编码了被废止的契约**（③ 目标态导向：不能拿它反推目标缩水）。
- **处置**：给 `canonical_root` 补一行 `mkdir()` + 三行 why 注释指向 spec。**未改任何被测代码。**
- **前后对照**：改前 `git stash` 到本票之前的树上跑该文件 → `21 passed`（证明确是本票引入，
  非既有 flake、非 order-dependent——单独跑也红）；改后 `21 passed`。

---

## 7. 全套件结果

| 轮次 | 结果 |
|---|---|
| 加固后首轮（未 fold A7） | `6 failed, 1827 passed, 4 skipped in 121.51s` |
| fold A7 后终轮 | 见下方「终轮」 |

**终轮**：`5 failed, 1829 passed, 3 skipped in 116.89s`。
（skipped 4→3 是既有的负载/环境敏感项，与本票判据无关：本票新增的 81 例中只有
`test_timeout_with_real_hanging_git` 带 skip 条件，且仅在 `win32` 触发，本机不触发。）
5 个 failed **全部**是 §5 表列的 12-mock-site 红，**全部属 Task 4 scope**，本票未动：

```
FAILED sdflow-issues/tests/test_issues.py::TestRepoRoot::test_falls_back_to_abspath_when_git_command_raises
FAILED sdflow-issues/tests/test_task4_rename_snapshot.py::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[None]
FAILED sdflow-issues/tests/test_task4_rename_snapshot.py::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[7]
FAILED sdflow-issues/tests/test_task4_rename_snapshot.py::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[bad_id2]
FAILED sdflow-issues/tests/test_task4_rename_snapshot.py::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[bad_id3]
```

CF-3 相关：`test_exec_claude_reverse_path_three_flags_golden` 本轮两次全量跑**均未失败**
（与 Task 1 的观察一致，进一步收窄「全量跑必红」这个已被证伪的描述）。

---

## 8. 🟢 垃圾树是否仍再生 —— **不再生**（本票最重要的正向证据）

```
PRE  junk: 0
（全套件 1832 例跑完）
POST junk: <无输出>
```

两轮全量跑（fold 前 + fold 后）**跑完仓根均 0 棵 `{` 开头目录**，无需任何清理动作。

**且拿到了因果链的直接证据**，不只是「没看见」：变红的 4 个 `..._preserves_derived_bytes`
用例，stderr 实得

```
ERROR: git 返回的仓根不可用: '{"bugs": [{"id": {}, "module": "core", ...
```

——那段被当成仓根的 JSON **原本就是长出 4 棵垃圾树的那个值**，现在它在形状校验（第④步）
被拦下、`ValueError` 抛出、`makedirs` 根本没被走到。**再生链是被判据切断的，不是碰巧没触发。**

---

## 9. Concerns（交后续票 / 双轴审）

1. **【交 Task 4，非本票可修】** 5 个红全部落在 12-mock-site 面上。**MUST NOT 通过弱化
   `repo_root` 让它们变绿**——其中 4 个的红恰恰是本 change 立项时断言的假绿被证伪。
   `test_issues.py:1609` 可直接当面级 argv 分派的样板。
2. **【交 Task 3】** tasks 1.3c 的 **CLI 层**断言（`exit 2` + stderr 无 `Traceback`）本票只做到
   **函数层**（子进程直调 `repo_root()`）。原因：CLI 路径要走到 `start=None` 分支，前提是
   argparse `--root` 默认值改 `None`（tasks **1.2c**，属 Task 3）；当前默认仍是 `"."` ⇒
   CLI 下 cwd 被删时走的是显式起点分支。**Task 3 落 1.2c 后，MUST 回补这条 CLI 级断言**，
   否则该 Scenario 只有半条覆盖。
3. **【Windows · 交 tasks 4.6】** 第⑤步用 `os.path.commonpath`（依 ADR-2 的代码原样）。
   在 **Windows 跨盘符**下 `commonpath` 会自行抛 `ValueError("Paths don't have the same drive")`。
   行为上仍是 fail-closed（`main()` 的 `except ValueError` 照样接住 → exit 2 + stderr，无 traceback），
   但**诊断消息不带 `ERROR: …; cause: …; fix:` 格式**，可观测性降级。
   本地 macOS 照不到，**MUST NOT 用「理论上大概率能过」结案**（design Open Questions Q3 同款）。
   备选：改 `PurePath.is_relative_to`（spec 明列的另一选项，跨盘符返回 `False` 而非抛异常）
   ——但那是对 ADR-2 written decision 的偏离，留给设计门/Windows 泳道拍板。
4. **【测试机制的一处诚实降级】** tasks 1.8 建议「PATH 注入 `sleep` 包装」验超时。真等满
   `timeout=30` 会让每次跑套件多 30s 墙钟，不可接受。故拆成两条：
   `test_timeout_raises_and_does_not_fall_back` 断言**契约**（`ValueError` + 不回落 +
   `subprocess.run` 确实收到正数 `timeout` kwarg）；`test_timeout_with_real_hanging_git` 做
   **真 PATH 注入**（`/bin/sleep 120` shim）但把外层 `timeout` 收窄到 1s 来观察真实
   `TimeoutExpired` 路径。**未被覆盖的残余 = 「30 这个数值本身」**，无自动化锚。
   （踩坑记录：shim 首版写 `sleep 120` 且把 `PATH` 整个替换成 shim 目录 ⇒ `sleep` 也找不到、
   shell 退 127 走成回落分支、测试「DID NOT RAISE」。改为 `exec /bin/sleep 120` + `PATH` **前置**
   而非替换后才真的挂住。这条如果没查、直接改断言，就会变成又一个假绿。）
5. **【`isdir` 的 TOCTOU】** 第①步 `isdir(start)` 与第③步 `subprocess.run(cwd=start)` 之间存在
   竞态窗口。窗口内 start 被删 ⇒ `subprocess.run` 抛 `FileNotFoundError`（`OSError`）⇒
   落**回落分支**返回 `abspath(start)`，而非 fail-closed。属既有回落语义的边角，
   未在 spec 中被要求处置，**不擅自扩大 scope**，登记备查。
