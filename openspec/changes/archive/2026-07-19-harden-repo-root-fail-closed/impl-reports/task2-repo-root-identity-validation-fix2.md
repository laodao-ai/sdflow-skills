# Task 2 修复轮 2 — 接缝复审 N1 / N2

**Change**: `harden-repo-root-fail-closed` · **Task**: 2（repo_root 六步身份校验）
**基线 HEAD**: `a5dd34b` · **前置报告**: `task2-repo-root-identity-validation.md` / `-fix1.md`（本文件不覆盖它们）

两条 Minor 均闭合。**N2 在补锚过程中挖出一条本轮自己引入的真缺陷（lexical 归一化改变路径语义），
已按 fold 判据当场修掉**——见 N2「意外发现」。

---

## N1【Minor · 文档】偏离理由 #3 与事实不符

### AST 核实（先查后写，未照抄复审转述）

对三份脚本的 `repo_root` 做 `ast.walk` 统计 `ast.Try` 节点：

| 脚本 | `try` 数 | try#1（行） | try#2（行） |
|---|---|---|---|
| `sdflow-buglist/scripts/buglist.py` | **2** | 619 · body=`cwd = os.getcwd()` · handler=`OSError` | 637 · body=`out = subprocess.run([...])` · handlers=`TimeoutExpired` / `(OSError, CalledProcessError)` |
| `sdflow-todolist/scripts/todolist.py` | **2** | 619 · 同上 | 637 · 同上 |
| `sdflow-issues/scripts/issues.py` | **2** | 1176 · 同上 | 1194 · 同上 |

再查首轮基线 `git show 5d47212:sdflow-buglist/scripts/buglist.py`：步骤① 当时即为

```python
    if start is None:
        try:
            start = os.getcwd()
        except FileNotFoundError:
            raise ValueError(...) from None
```

⇒ **裹 `os.getcwd()` 的 try 首轮就已存在**并已在首轮报告里登记为必要偏离；fix1 只把它的 catch 从
`FileNotFoundError` 扩到 `OSError`（CF-4），**并未避免第二个 try**。复审判定成立。

### 处置

理由 #1（可观测契约一致）与 #2（就地包 try 产生无法变异确认的死分支）**各自独立成立 ⇒ 偏离结论不变**。
只订正 #3 的表述，改为陈述真实约束「`try` 只包 `subprocess.run`」+ 已登记的 `getcwd` 必要偏离，
并把就地包 try 的代价准确记为「**成为第三个** try，且裹的是已被证明不可能抛的路径」。
按 DOC-1 直接给最终态表述，未写演进史。

顺带把同一报告里那段修法代码贴的 `start = os.path.normpath(start)` 同步为最终形态——见 N2，该行已删除。

---

## N2【Minor · 覆盖】起点归一化缺专属测试锚

### 补的锚（三份各 4 例 = 12 例）

判据一律是「**结果与非 symlink / 无 `..` 的等价起点完全一致**」，不是「不抛异常」。
symlink 全部在 `tmp_path` 下真建，**未 mock `os.path.realpath` / `isdir` / `isabs`**。

| 用例 | 起点形态 | 断言 |
|---|---|---|
| `test_symlinked_repo_root_start_matches_real_path_result` | `link -> <repo>` | `repo_root(link) == repo_root(repo) == realpath(repo)` |
| `test_dotdot_in_start_matches_real_path_result` | `<repo>/sub/..` | `== repo_root(repo) == realpath(repo)` |
| `test_symlinked_start_with_subdir_matches_real_path_result` | `link/sub`（`link -> <repo>`） | `== repo_root(repo/sub) == realpath(repo)` |
| `test_dotdot_after_symlinked_dir_follows_kernel_not_lexical` | `link/..`（`link -> <repo>/sub`） | `== repo_root(repo) == realpath(repo)` |

### 意外发现（第 4 例）：lexical 归一化改变了路径语义 —— 本轮引入的真缺陷

`os.path.normpath` 是**纯字面**运算。起点为 `link/..`（`link -> <repo>/sub`）时：

- **内核语义**：`link/..` = `<repo>`（symlink **目标**的父目录）→ git 探测出仓根 `<repo>`。
- **`normpath` 结果**：`<tmp>`（link **自身**的父目录）——一个非 git 目录 ⇒ git 以 128 退出
  ⇒ 走回落分支 ⇒ `repo_root` 静默返回 `<tmp>`。

`<tmp>` 会被下游当作**可写仓根**，正是本 change 要消灭的「返回一个未经证明的根」形态。
首轮（`5d47212`）无此问题——它是 fix1 的 ①b 随手加的 `normpath` 引入的。

**修法**：删掉 `start = os.path.normpath(start)`，三份同步（patch 脚本注入，各断言 `count == 1`）。
①b 需要的性质只有「起点恒为绝对路径」（回落分支不再触 `os.getcwd()`），**归一化不是它的一部分**；
路径语义一律交给内核与步骤⑤的 `os.path.realpath`。

**返回值等价性**：回落分支的 `os.path.abspath(start)` 对绝对路径本就等于 `normpath(start)`
⇒ 回落返回值与首轮/fix1 逐字一致，删除 `normpath` 不改变任何回落形态。
C1 的 fail-closed 也完好——起点仍恒为绝对路径。

**修复前实测（HEAD `a5dd34b`，第 4 例为红）**：

```
>       assert repo_root(str(link) + os.sep + "..") == repo_root(str(repo))
E       AssertionError: assert '/private/var...symlinked_di0' == '/private/var...nked_di0/repo'
E         - mlinked_di0/repo
E         + mlinked_di0
1 failed, 33 passed in 2.36s
```

### 变异确认（PV 规则 5）— 两次实际输出

**变异 A：把 `start = os.path.normpath(start)` 加回去**（即 fix1 形态）

```
FAILED sdflow-buglist/tests/test_repo_root_identity_buglist.py::test_dotdot_after_symlinked_dir_follows_kernel_not_lexical
1 failed, 33 passed in 2.37s
```

**变异 B：删掉整个 ①b 归一化**（退回首轮 `if start is None: start = os.getcwd()`）

```
FAILED ...::test_deleted_process_cwd_yields_controlled_failure
FAILED ...::test_cli_with_deleted_process_cwd_exits_two_without_traceback
FAILED ...::test_getcwd_permission_error_is_controlled_too
3 failed, 31 passed in 2.40s
```

### 🔴 如实登记：复审点名的那 3 例**不具变异区分力**

两次变异下，`test_symlinked_repo_root_start_matches_real_path_result` /
`test_dotdot_in_start_matches_real_path_result` /
`test_symlinked_start_with_subdir_matches_real_path_result` **全程绿**。

原因是**结构性**的，不是用例写得弱：`normpath` 对 `<repo>` / `<repo>/sub/..` /
`<tmp>/link/sub` 这三种形态的**字面**改写，与内核解析结果**恰好一致**（无「symlink 后跟 `..`」
这一步，lexical 与内核不分叉）。∴ 这三例是**正向回归锚**（定住「symlink / `..` 起点仍返回正确仓根」
这条契约），**不是** ①b 的变异守护——**不为了"有变异确认"而给它们硬凑一个假的**。

真正区分 ①b 归一化策略的是第 4 例（变异 A 独家拉红），区分 ①b「抬绝对路径」的是 fix1 已有的
C1 三例（变异 B 拉红）。两者合起来把 ①b 这一步的两个决策各自钉死。

变异均只在 `sdflow-buglist/scripts/buglist.py` 上做（`cp` 备份 → 改 → `cp` 还原），未污染另两份；
还原后该文件 `34 passed`。

---

## 三份同步 / 镜像一致性

`normpath` 的删除由同一个 patch 脚本注入三份（非手抄），三处 old-string 各断言 `count == 1`。
`test_mirror_consistency.py` 相关 **29 passed**——剥 docstring 后 `ast.dump` 三向等价保持绿。

结构硬约束复核：`try` 仍是 2 个且形状未变（AST 表见 N1）；黑名单仍是**函数体内局部常量**；
`GIT_DISCOVERY_ACROSS_FILESYSTEM` 仍在净化清单内；祖先校验（⑤）与 worktree marker（⑥）一字未动；
被拒值仍走 `ascii(value)[:200]`；无 `sys.exit` / stdout 写入 / `except Exception`。

## 全套件

| | failed | passed | skipped |
|---|---|---|---|
| 基线 `a5dd34b` | 4 | 1839 | 3 |
| 本轮 | **4** | **1851** | 3 |

`+12 passed` = 三份 recorder × 4 个新用例，红数未变。
剩余 4 红仍全部是 `test_task4_rename_snapshot.py::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[None|7|bad_id2|bad_id3]`（Task 4 scope）——
**本轮未动那 4 个用例，也未动 CF-1 的任何 mock 站点**。

三个 identity 测试文件：90 → **102 passed**。

## 垃圾树再生链

全套件跑完后检查仓根：**0 个 `{` 开头目录**。
