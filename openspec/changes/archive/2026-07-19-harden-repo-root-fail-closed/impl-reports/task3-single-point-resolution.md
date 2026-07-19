# Task 3 — 单点解析：仓根在一次调用内只解析一次（R2）

**Blocked-by**: 2 · **起点 HEAD**: 6bc3feb · **pytest**: `/usr/bin/python3 -m pytest`

---

## 1. 做了什么

| tasks | 内容 | 落点 |
|---|---|---|
| 1.2 | 删 16 处 `cmd_*` / `_*_snapshot` 内的 `root = repo_root(args.root)` → `root = args.root` | 三份 recorder |
| 1.2b | `repo_root` docstring 改为最终态（ADR-5 单点解析），三份同步 | 三份 recorder |
| 1.2c | `--root` argparse 默认值 `"."` → `None` + 理由注释 | 三份 recorder |
| 1.9 补强 | 「未指定 vs 显式指定」两条路径可区分的 CLI 级用例 | 三份 tests |
| 1.11 | 跨进程重解析锚定用例（**当前 `xfail(strict=True)`，见 §5**） | 三份 tests |
| 静态断言 | `repo_root(` Call 节点数 + 归属函数、`--root` 默认值，均用 `ast.walk` | 三份 tests |

新增测试 9 条（每份 recorder 3 条），全套件 passed 1851 → 1860。

---

## 2. AST Call 节点数实测（tasks 1.2 的判据）

手段 `ast.walk` 数 `ast.Call` 且 `func` 为 `Name('repo_root')`——**未用 grep**（grep 会把
`def repo_root(` 与 docstring 字面量算进来）。

**改造前（HEAD 6bc3feb）**：

```
sdflow-issues/scripts/issues.py     7  [1629, 2086, 2128, 2176, 2210, 2280, 2418]
sdflow-buglist/scripts/buglist.py   6  [1307, 1356, 1429, 1513, 1560, 1691]
sdflow-todolist/scripts/todolist.py 6  [1272, 1299, 1400, 1484, 1539, 1665]
TOTAL 19
```

**改造后**：

```
sdflow-issues/scripts/issues.py     1  [2423]
sdflow-buglist/scripts/buglist.py   1  [1701]
sdflow-todolist/scripts/todolist.py 1  [1675]
TOTAL 3
```

删掉的 16 处所在函数（改造前 AST 归属实测）：

- `issues.py`：`cmd_reindex` · `_batch_lint_snapshot` · `cmd_batch_add` · `cmd_batch_set_status` · `cmd_batch_rename` · `cmd_sweep`
- `buglist.py`：`_next_id_snapshot` · `cmd_add` · `cmd_set_status` · `cmd_triage` · `_scan_snapshot`
- `todolist.py`：同 buglist 五处

剩余 3 处全部归属 `main()`，由测试
`test_repo_root_is_resolved_once_per_process_and_only_in_main` 机械守（每份断言
`len(calls) == 1` 且 `owners == ["main"]`，合计即 3）。

---

## 3. 验收框逐条证据

### ☑ 命令函数内 `repo_root` 调用归零；全脚本 19 → 3，手段 `ast.walk`

见 §2。守护用例三份各一。

### ☑ `--root` 未指定与显式指定两条路径行为可区分

- 机械层：`test_root_argparse_default_is_none`（三份）——AST 取 `add_argument("--root", …)`
  的 `default` 关键字，断言恰有一个且为 `Constant(None)`。
- 行为层：`test_unspecified_root_probes_cwd_while_explicit_root_is_validated`（三份）——
  **同一个 cwd**（仓库的嵌套子目录）下跑两次：
  - 未指定 → exit 0，`repo/openspec/issues` 被创建、`nested/openspec` 未被创建（走 `os.getcwd()` 探测到仓根）；
  - `--root <不存在路径>` → exit 2 + stderr 含 `仓根探测起点不是既存目录` + 该路径未被具现（走 `isdir` 起点校验，在调 git 之前）。

  两条断言的是**不同的可观测结果**，不是同一条路径的两种写法。**未仅凭退出码判定**
  （坏 root 与坏 scan id 都是 exit 2）。

### ☑ `repo_root` docstring 与新架构一致

三份旧 docstring 描述的是「所有 cmd_* 现在统一先 `root = repo_root(args.root)` 再拼路径」，
ADR-5 后失真。三份改为同一段最终态表述：单点解析、`main()` 解析后写回 `args.root`、
其余一律 `root = args.root`、「一次」的边界是**进程**。

`issues.py` 的旧 docstring 另有一整段「Critical fix carry-over」考古层（描述 4 个 cmd_*
此前直接用裸 `args.root` 的历史），按 **DOC-1（正文即最终态）**一并删除——它正是「只有读过
上一版的人才需要的句子」。三份 docstring 现已同文（差异仅同名脚本互指的两个文件名）。

### ☐ 跨进程锚定用例存在 —— **用例已落，但断言当前为 `xfail(strict=True)`**

见 §5。这是本票唯一未闭合的验收框，且**不是可就地修复的实现疏漏，而是 design ADR-5 的一条
事实性假定被实测证伪**。

---

## 4. CF-4 / CF-5 的处置

### CF-4（`--root` 默认改 `None` 会激活裸 `OSError` 逃逸路径）——**核实为「Task 2 已做掉」，本票无需再改**

按票面要求自行 AST/读码核实，**未采信 carry-forward 的描述**。当前三份的实际状态：

```
sdflow-issues/scripts/issues.py:1180        except OSError:
sdflow-buglist/scripts/buglist.py:628       except OSError:
sdflow-todolist/scripts/todolist.py:628     except OSError:
```

即 `repo_root` 步骤①b 捕的已经是 `OSError`（`FileNotFoundError` 与 `PermissionError` 同族全覆盖），
Task 2 的 fix1 已扩过。carry-forward CF-4 写的「目前只捕 `FileNotFoundError`」是**登记时的快照**，
在 Task 2 fix1 之后已过期。

负例也已存在且三份齐备：`test_getcwd_permission_error_is_controlled_too`（mock `os.getcwd`
抛 `PermissionError`，断言得到受控 `ValueError`）。该用例 mock 的是**外部环境行为**，
不是 `isabs`/`isdir`/`realpath` 判据本身，符合方法论红线。

⇒ **本票未改这条 except**，改了反而是无意义扰动。结论有实测支撑，非「以现在触发不到为由不做」。

### CF-5（tasks 1.3c 的 CLI 层断言待回补）——**已闭合**

CLI 级用例 `test_cli_with_deleted_process_cwd_exits_two_without_traceback` 三份齐备
（Task 2 已落），断言：真子进程跑 CLI → `RC:2` + stderr 不含 `Traceback` + 含
`ERROR: 无法确定仓根探测起点` + `cause:` / `fix:`。**1.2c 落地后它才真正走到目标分支**：

| 链条 | 机械锚 |
|---|---|
| CLI 未指定 `--root` ⇒ `args.root is None` | `test_root_argparse_default_is_none`（AST 断言 default 为 `None`） |
| `repo_root(None)` 在 cwd 被删时受控失败 | `test_deleted_process_cwd_yields_controlled_failure`（函数层，直调 `repo_root()` 无参） |
| 该失败经 CLI 出口 ⇒ exit 2 + 无 Traceback | `test_cli_with_deleted_process_cwd_exits_two_without_traceback`（真子进程） |

三链各有独立机械锚，合起来覆盖 Scenario「进程当前工作目录在运行期被删除」的 CLI 面。

**未踩票面点名的坑**：`issues.py` 没有 `scan` 子命令。三份 CLI 用例各用自己真实的子命令
（buglist/todolist → `scan`，issues → `reindex`，实测确认 `issues.py` 的既有用例本来就用
`reindex`），且一律断言 stderr 的具体诊断内容而非只看退出码。

---

## 5. 🔴 主要发现：R2 Scenario「子进程解析出不同的根时响亮失败」**当前不成立**

### 5.1 实测复现（三份 recorder 一致）

构造 = spec 明写的场景：outer 是仓、inner 是 outer 内的嵌套仓；父进程在 inner 上持锁并以
`--root <inner>` 拉起子进程；两次解析之间 inner 失去 `.git`。

```
buglist   rc 0 | outer/openspec 被创建: True | stderr: (空)
todolist  rc 0 | outer/openspec 被创建: True | stderr: (空)
issues    rc 0 | outer/openspec 被创建: True | stderr: (空)
```

以 `buglist add` 做的第一轮 spike 更直接：子进程 **rc=0 并把新 bug 条目写进了 outer**
（`outer/openspec/issues/buglist/2026-07-19-buglist.md`），stdout 正常返回 `{"id": "B1", ...}`。
**这正是本 change 开篇要消灭的「静默写错目录」，只是走的是跨进程这条边。**

### 5.2 根因：兜底机制不在假定的位置

design ADR-5 与 spec R2 都写：

> 子进程若解析出不同的根，其 `_lock_path` 处无锁文件 ⇒ `RecorderLockError` 响亮失败

`validate_recorder_participant` **确实**会抛 `RecorderLockError`。但 `recorder_lock` 把它吞掉了：

- `sdflow-issues/scripts/issues.py:194`
- `sdflow-buglist/scripts/buglist.py:207`
- `sdflow-todolist/scripts/todolist.py:207`

```python
try:
    participant = validate_recorder_participant(root, inherited, command)
except RecorderLockError:
    participant = None          # ← 吞掉，回落 owner 模式
if participant is not None:
    ...
path = _lock_path(root)
os.makedirs(os.path.dirname(path), exist_ok=True)   # ← 在**错误的根**上具现
```

同根场景下这个洞看不见：回落 owner 后 `O_EXCL` 撞上父进程的锁 → `recorder lock occupied` →
响亮失败。**「响亮」是同根这一巧合带来的，不是绑定校验带来的。** 一旦根发生分裂，
锁路径也随之分裂，`O_EXCL` 不再冲突 ⇒ 静默成为 owner。

### 5.3 为什么 Task 3 不就地修

修法只能是给锁协议加 **owner-root 绑定**（父进程把已解析的根随 token 一起下传，子进程比对
不一致即响亮失败）。而**任何让「participant 校验失败 ⇒ 响亮失败」的改法都会撞上既有契约测试**
`sdflow-buglist/tests/test_task2_semantic_lock.py::test_invalid_participant_env_falls_back_to_owner_or_conflict`
——它显式断言「坏 participant env ⇒ 回落 owner ⇒ exit 0」，且三份 recorder 参数化覆盖。

实测证据（§6 变异 2）：把那三行 `except` 去掉后，1.11 锚定用例 XPASS，
**同时** `test_invalid_participant_env_falls_back_to_owner_or_conflict[buglist]` 变红。
两条契约**在当前协议下无法同时成立**——区分二者所需的信号（父进程的根）根本没被传下来。

⇒ 这是 **design 层面的事实性假定被证伪**，不是实现疏漏。修它要动 recorder 锁协议
（`recorder_child_env` + `recorder_lock` + 三份 `main()` + AST 镜像 + 另一个 change 的 spec），
属**设计门议题**。票面禁止碰 `design.md` / `specs/`（ship gate 设计门失鲜），故本票
**如实登记 + 落机械锚**，不擅自改协议、更不删弱那条既有契约。

### 5.4 落的是什么锚

`test_child_resolving_a_different_root_must_fail_loudly`（三份各一），断言**按 spec 的要求写**
（子进程 MUST 非 0 退出 + outer 下 MUST NOT 出现 `openspec/`），标
`@pytest.mark.xfail(strict=True)` 并在 reason 里写明缺口、根因、冲突对象与「为何不就地改」。

选 `xfail(strict=True)` 而非「断言现状（rc==0）」：后者是**把 bug 写成契约**，等于给缺口发合格证。
strict xfail 的性质是——**缺口一旦被堵上，用例 XPASS → strict 判红 → 强制有人回来删标记**，
是活的机械锚，不是注释。

用例内含**前提核验**：`assert repo_root(str(inner)) == realpath(outer)`——若哪天 `repo_root`
的行为变了、子进程不再解析出不同的根，这条会先炸，避免用例悄悄退化成「测了个别的东西」
（对照 CF-8 的 `sleep` shim 踩坑：不查原因改断言 ⇒ 得到一个测错东西的假绿）。

---

## 6. 变异确认实测（PV 规则 5）

### 变异 1 — 单点解析守护

把 `buglist.cmd_add` 的 `root = args.root` 改回 `root = repo_root(args.root)`：

```
FAILED sdflow-buglist/tests/test_repo_root_identity_buglist.py::test_repo_root_is_resolved_once_per_process_and_only_in_main
E   +  where 2 = len([<ast.Call object at 0x1089fd550>, <ast.Call object at 0x108a7a880>])
1 failed in 0.03s
```

还原后绿。⇒ 守护是活的。

> ⚠️ 过程事故（已修复，如实登记）：还原该变异时我用了
> `git checkout sdflow-buglist/scripts/buglist.py`，把 buglist.py 上**本票的全部改动**
> （5 处删除 + docstring + argparse 默认值）一并回退了。当场 `git status` 发现并按原样重做，
> 重做后 AST 计数（1/1/1，TOTAL 3）与镜像一致性测试均复核通过。
> **教训**：变异确认的还原手段 MUST 是「精确逆操作或文件级备份还原」，
> **MUST NOT 用 `git checkout <path>`**——它还原到的是 HEAD，不是变异前。
> 变异 2 即改用 `cp` 备份还原。

### 变异 2 — 跨进程锚定守护（票面点名的那一条）

按票面要求本应「削弱 `validate_recorder_participant` 的绑定校验 → 用例必须变红」。
**该手段在此不可分辨**：削弱绑定后，子进程在 outer 处仍读不到锁 metadata（那里本来就没有锁
文件），validate 照样失败、照样被 `recorder_lock` 吞掉 ⇒ 用例仍是 xfail，观察不到差别。
**这本身就是 §5.2 结论的独立佐证：绑定校验不是这条路径上的承重件，吞异常的那三行才是。**

故改做**反向变异**（把缺口补上，验证锚会不会跳）——去掉 `recorder_lock` 里吞异常的三行：

```
FAILED sdflow-buglist/tests/test_repo_root_identity_buglist.py::test_child_resolving_a_different_root_must_fail_loudly
[XPASS(strict)] R2 Scenario「子进程解析出不同的根时响亮失败」当前**不成立**…
1 failed in 0.13s
```

同一变异态下，既有契约测试的反应：

```
FAILED sdflow-buglist/tests/test_task2_semantic_lock.py::test_invalid_participant_env_falls_back_to_owner_or_conflict[sdflow-buglist/scripts/buglist.py-args0]
1 failed, 2 passed in 0.30s
```

还原后：

```
3 passed, 1 xfailed in 0.57s
```

⇒ 锚是活的（缺口一堵就跳红）；且 §5.3 的「两条契约互斥」是**实测结论，不是推断**。

---

## 7. 全套件结果

```
4 failed, 1860 passed, 3 skipped, 3 xfailed in 109.26s
```

- **红数 4，与接手时一致**，全部是
  `sdflow-issues/tests/test_task4_rename_snapshot.py::test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes[…]`
  的 4 个参数化用例（CF-1，Task 4 的面级 mock 改造范围）。**未动**这 4 个用例，也未动
  CF-1 点名的 12 个 blanket mock 站点。
- passed 1851 → 1860（+9 = 三份 × 3 条新用例）。
- xfailed 0 → 3（§5 的跨进程锚定，三份各一）。
- 镜像一致性：`sdflow-buglist/tests/test_mirror_consistency.py` **7 passed**，
  `repo_root` 三向 AST 等价仍绿（tasks 1.10）。
- 仓根 `find . -maxdepth 1 -name '{*'` **无输出**，Task 2 切断的再生链未复发。

---

## 8. Concerns

1. **🔴 R2 Scenario 3 未闭环（§5）**——需在设计门决策：是给锁协议加 owner-root 绑定
   （代价：改 `recorder_child_env` + `recorder_lock` + 三份 `main()` + AST 镜像，且须重写
   `test_invalid_participant_env_falls_back_to_owner_or_conflict` 的口径），还是修订 spec R2
   对该 Scenario 的表述。**MUST NOT 靠删掉那条 xfail 用例「解决」。**
   Task 6 收口时 MUST NOT 因 1.2 / 1.2b 两框已勾就把 R2 读成已闭环。

2. **`cmd_*` 现在无条件信任 `args.root`**——绕过 `main()` 直调 `cmd_*` 的测试若传相对路径或
   未校验路径，不再有 `repo_root` 兜底。design ADR-5 已核实存量调用传的都是绝对 `tmp_path`，
   本轮全套件也未暴露此类回归。但这是**目标态下的新契约**（「`args.root` 已被校验」是
   `cmd_*` 的前置条件），值得在后续新增测试时留意——目前无机械守护。

3. **`--root` 默认值改 `None` 的对外可见面**：CLI 行为等价（`repo_root(".")` 与
   `repo_root(None)` 只在 cwd 被删/不可访问时分叉，且分叉方向正是本 change 要的 fail-closed）。
   未发现仓内有依赖 `args.root == "."` 字面值的消费者。

4. **CF-4 的 carry-forward 描述已过期**——Task 2 fix1 修掉后未回写 carry-forward.md。
   本报告 §4 已给出实测现状；Task 6 汇总时**别照抄** CF-4 的原文当作待办。
