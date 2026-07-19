# Task 2 修复轮 1 — 双轴审 C1 / C2 / C3

**Change**: `harden-repo-root-fail-closed` · **Task**: 2（repo_root 六步身份校验）
**基线 HEAD**: `5d47212` · **前置报告**: `task2-repo-root-identity-validation.md`（本文件不覆盖它）

三条全部闭合，无 defer。

---

## C1【Critical】回落分支自己抛裸 `FileNotFoundError` → RC=1 + Traceback

### 缺陷复现（修复前，实测）

```
$ mkdir -p /tmp/c1probe/doomed && cd /tmp/c1probe
$ python3 -c "os.chdir('doomed'); os.rmdir(cwd); run(buglist.py scan)"
RC 1
...
  File ".../buglist.py", line 640, in repo_root
    return os.path.abspath(start)
  File ".../posixpath.py", line 379, in abspath
    cwd = os.getcwd()
FileNotFoundError: [Errno 2] No such file or directory
```

链条确认与评审意见一致：cwd 被删 → `subprocess.run(cwd=start)` 让 git 以 128 退出 →
落**回落分支** → `os.path.abspath(".")` 内部调 `os.getcwd()` **自己抛** `FileNotFoundError`
→ 逃出 `repo_root` → `main()` 只 `except ValueError` 接不住 → 裸 Traceback + RC=1。

**抛点在 `repo_root` 自己 owns 的回落分支里，与 argparse 默认值无关** ⇒ 本票闭合，未 defer 到 Task 3。

### 修法：消除抛点，而不是再包一层 try

首轮的步骤① 只在 `start is None` 时求 cwd；`start` 为**相对路径**（argparse 默认 `"."`）时
`start` 一路带着相对性走到回落分支，由 `abspath` 在那里才去触 cwd。修法是把「触 cwd」这件事
**全部前移并收敛到步骤①b 的单一守护点**：

```python
    # ① 起点可信性（显式起点的存在性拒绝，保持原判据）
    if start is not None and not os.path.isdir(start):
        raise ValueError("ERROR: 仓根探测起点不是既存目录: " + ascii(start)[:200] + ...)
    # ①b 起点归一化为绝对路径——**本步同时替回落分支承担 fail-closed**
    if start is None or not os.path.isabs(start):
        try:
            cwd = os.getcwd()
        except OSError:                     # ← CF-4 一并扩为 OSError
            raise ValueError(
                "ERROR: 无法确定仓根探测起点; cause: 进程当前工作目录已不存在或不可访问; "
                "fix: 切换到一个既存目录后重试，或显式指定一个绝对路径作为起点"
            ) from None
        start = cwd if start is None else os.path.join(cwd, start)
    start = os.path.normpath(start)
```

回落分支随之变成**结构上不可能抛**：

```python
    except (OSError, subprocess.CalledProcessError):
        # start 已在步骤①b 归一化为绝对路径 ⇒ 本行不再触 os.getcwd()，结构上不可能抛
        # OSError。这是本回落分支 fail-closed 的方式：**消除抛点**，而不是再包一层 try。
        return os.path.abspath(start)
```

#### ⚠️ 与评审建议的一处偏离（显式登记，请复审确认）

评审原话是「`os.path.abspath(start)` 的 `OSError` 转成受控 `ValueError`」，即**在回落分支就地包一层 try**。
我改为**在上游消除抛点**，理由三条：

1. **可观测契约完全一致** —— 三份脚本实测均为 `exit 2` + `ERROR:/cause:/fix:` 三段式诊断 + stderr 无 Traceback。
2. **就地包 try 会产生一条无法做变异确认的死分支** —— 归一化之后 `abspath` 对绝对路径是恒等映射、
   永不触 cwd，那个 `except` 永远走不到。写一条「删掉它也不会变红」的守护，直接违反 PV 规则 5 的精神。
3. **结构硬约束** 要求「`try` 只包 `subprocess.run`」。就地包 try 会在函数里引入第二个 `try`；
   前移方案把守护放在 git 调用之前，`subprocess.run` 那个 `try` 的形状原样不动
   （只捕 `OSError`/`CalledProcessError`、`TimeoutExpired` 单独 `raise`、无 `except Exception`）。

**代价/残余风险**：保护点与失效点不再同处一行。若日后有人把步骤①b 的归一化删掉或后移到 git 调用之后，
回落分支会静默回归。**该风险已被机械覆盖**——见下方变异确认②，删掉①b 时新增的 CLI 用例立刻复现
原始 `RC:1 + FileNotFoundError`。

### 顺带 fold：CF-4（Standards 轴 Minor）

首轮步骤① 只捕 `FileNotFoundError`；`PermissionError`（父目录 r/x 权限被撤）同属 `OSError`、会同样裸逃。
已随上文一并扩为 `except OSError`。两条是同一族缺陷（裸 `OSError` 逃逸击穿「stderr 无 Traceback」承诺），
同一票修掉，未留给 Task 3。

### 新增验证（三份各一，共 6 例）

| 用例 | 层级 | 断言 |
|---|---|---|
| `test_cli_with_deleted_process_cwd_exits_two_without_traceback` | **CLI 真子进程** | `RC == 2` · stderr 无 `Traceback` · 含 `ERROR: 无法确定仓根探测起点` · 含 `cause:`/`fix:` |
| `test_getcwd_permission_error_is_controlled_too` | 函数层 | `PermissionError` → 受控 `ValueError`（CF-4 守护） |

`test_getcwd_permission_error_is_controlled_too` mock 的是 `os.getcwd`（**外部环境行为**），
**不是** `os.path.isabs`/`isdir`/`realpath`（判据本身）—— 未触碰方法论红线。

---

## C2【Important】「经 CLI 调用 exit 2」缺自动化绿锚

首轮 81 例全在函数层；唯一覆盖 CLI 半条的 4 个用例当前是红的（Task 4 的 mock 面）⇒ **绿锚压在红用例上 = 没有锚**。

新增 `test_cli_bad_root_exits_two_with_diagnostic_on_stderr`（三份各一），走
**`--root` 指向不存在目录**这条现在就能触发的路径，**不依赖 Task 4 的红用例转绿**：

```python
    proc = subprocess.run([sys.executable, SCRIPT, "--root", str(missing), SUBCMD], ...)
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert proc.stderr.startswith("ERROR: ")
    assert "仓根探测起点不是既存目录" in proc.stderr        # ← 退出码不可区分 ⇒ 必须断言诊断内容
    assert "cause:" in proc.stderr and "fix:" in proc.stderr
    assert repr(str(missing))[1:-1] in proc.stderr          # 被拒值出现在诊断里
    assert not missing.exists()                              # 坏路径 MUST NOT 被 makedirs 具现
    assert _entries(tmp_path) == []
```

遵守「退出码可区分性」约束：坏 root 与坏 scan id 都产生 exit 2 ⇒ 用例**同时断言 stderr 的具体诊断内容**，
未仅凭退出码判定通过。

---

## C3【Minor】fold 判据不一致

`sdflow-issues/tests/test_issues.py::TestRepoRoot::test_falls_back_to_abspath_when_git_command_raises`
的红只是桩签名缺 `env=`/`timeout=`，与已 fold 的 `test_task3_frontmatter_writer[A7]` 同属
「本票签名变更直接触发」。判据统一 ⇒ 一并 fold：

```python
-        def boom(cmd, cwd=None, capture_output=True, text=True, check=True):
+        # `**kwargs`：repo_root 现在还会传 env= / timeout=，写死签名会 TypeError。
+        # 只补桩签名，不改被测行为（回落分支仍应返回 abspath(start)）。
+        def boom(cmd, **kwargs):
             raise subprocess.CalledProcessError(128, cmd)
```

**只补桩签名，未改被测行为**（断言仍为 `result == os.path.abspath(str(tmp_path))`，原样保留）。

---

## 变异确认（PV 规则 5）— 两次实际输出

### 变异① C2 守护：拆掉步骤① 的起点存在性拒绝

```
MUTATED: 拆掉步骤① 起点存在性拒绝  (`if start is not None and not os.path.isdir(start):` → `if False:`)

E       AssertionError: (0, '（无匹配 bug）\n\n✓ frontmatter/marker/legacy 关系一致\n', '')
E       assert 0 == 2
E        +  where 0 = CompletedProcess(args=[..., '--root', '.../no-such-root', 'scan'],
E                                      returncode=0, stdout='（无匹配 bug）\n...', stderr='').returncode
1 failed in 0.07s
```

⇒ 无守护时 CLI 对着一个**不存在的仓根静默 exit 0**，正是 spec 要消灭的 fail-open。新锚有效。

### 变异② C1 守护：删掉步骤①b 归一化 + `OSError` 守护

把①b 整段退回首轮形态（`if start is None: start = os.getcwd()`，无 try）：

```
MUTATED: 删掉①b 归一化 + OSError 守护

FAILED ...::test_deleted_process_cwd_yields_controlled_failure
FAILED ...::test_cli_with_deleted_process_cwd_exits_two_without_traceback
FAILED ...::test_getcwd_permission_error_is_controlled_too
3 failed, 27 passed in 2.23s
```

CLI 用例的失败详情**逐字复现了 C1 的原始缺陷形态**：

```
E       AssertionError: RC:1
E         ERR:Traceback (most recent call last):<NL>
E           File ".../buglist.py", line 630, in repo_root<NL>    out = subprocess.run(<NL>
E           ...subprocess.CalledProcessError: ... returned non-zero exit status 128.<NL>
E         During handling of the above exception, another exception occurred:<NL>
E         Traceback (most recent call last):<NL>
E           File ".../buglist.py", line 1677, in main<NL>    args.root = repo_root(args.root)<NL>
E           File ".../buglist.py", line 644, in repo_root<NL>    return os.path.abspath(start)<NL>
E           File ".../posixpath.py", line 379, in abspath<NL>    cwd = os.getcwd()<NL>
E         FileNotFoundError: [Errno 2] No such file or directory<NL>
```

⇒ 「删掉它就变红」成立，且红的形态 = 缺陷的形态。变异后已还原，还原后 `37 passed`。

> 两次变异均只在 `sdflow-buglist/scripts/buglist.py` 上做（改前 `cp` 备份、改后 `cp` 还原），
> 未污染另两份；还原后三向 AST 镜像一致性重跑为绿。

---

## 三份同步 / 镜像一致性

三份 `repo_root` 的改动由**同一个 patch 脚本注入**（非手抄），三处 old-string 各断言
`count == 1` 后整体替换。`test_mirror_consistency.py` **7 passed**——剥 docstring 后
`ast.dump` 三向等价保持绿。黑名单仍是**函数体内局部常量**（未改动，也未上移为模块级）。
祖先校验（步骤⑤）与环境净化清单（步骤②）**一字未动**，`GIT_DISCOVERY_ACROSS_FILESYSTEM` 仍在净化清单内。

## 全套件前后对比

| | failed | passed | skipped |
|---|---|---|---|
| 修复前（HEAD `5d47212`） | **5** | 1829 | 3 |
| 修复后 | **4** | 1839 | 3 |

`+10 passed / -1 failed` 的构成：**新增 9 例**（三份 recorder × 3 个新用例）+ **C3 fold 令 1 个红转绿**。
三个 identity 测试文件由 81 → **90 passed**。

修复后剩余 4 个红，全部是 `test_task4_rename_snapshot.py::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[None|7|bad_id2|bad_id3]`
—— 坏 root / 坏 scan id 的**退出码可区分性**，属 Task 4 的面级 argv 分派 scope，**本票未动那 4 个用例、也未动 CF-1 的任何 mock 站点**。
C3 那一个红（`test_falls_back_to_abspath_when_git_command_raises`）已按判据一致性 fold 转绿，5 → 4 与评审预期吻合。

## 垃圾树再生链

全套件跑完后检查仓根：**0 个 `{` 开头目录**，无回归。

## 新发现

1. **`issues.py` 无 `scan` 子命令**（其子命令为 `reindex` / `batch` / `sweep`）。
   复现 C1 时对 `issues.py` 跑 `scan` 会先被 argparse 拒掉（exit 2），**看起来像已修复**——
   这是一个会伪造绿的坑。三份的 CLI 级用例已按各自真实子命令参数化（buglist/todolist = `scan`，issues = `reindex`），
   `issues.py` 的 C1 修复已用 `reindex` 独立实测确认（`RC 2 | Traceback False`）。
2. **C1 的真实触发条件比评审描述更宽**：不止「cwd 被删」，任何**相对起点 + cwd 不可用**都会走到该抛点
   （含 `PermissionError`，即 CF-4）。①b 的归一化把这一整族一次覆盖，而非只补 cwd-被删这一个点
   （面治优先于点补）。
