# Task 3 · 双轴审第 1 轮返修（fix1）

承 `task3-content-compare.md`（首轮，不覆盖）。HEAD 起点 `c99f677`，分支 `feat/harden-gate-git-layer`。
五条：F1 退出码契约破损（按 Important 处理）· F2 豁免闸门漏校 blob · F3 测试基座不隔离 gitconfig ·
F4 登记理由实测为假 · F5 测试清理。

---

## F1 · `--change` 的非 UTF-8 字节把退出码打出契约集 —— 已修

**成因**：`--change` 经 argv 由 CPython 以 **surrogateescape** 解码，非 UTF-8 字节变 lone surrogate
（`\udcff`）。`is_stale` 里 `(base + "tasks.md").encode("utf-8")` 对它抛 `UnicodeEncodeError`，
而 `main()` 只捕 `GateIndeterminate` ⇒ 异常逸出 ⇒ **退出码 1**，落在契约集 `{0,3,4,5,6}` 之外
（违反 Global Constraints 末条，且撕开 Task 2 刚建立的契约）。

已独立复现：

```
'utf-8' codec can't encode character '\udcff' in position 19: surrogates not allowed
```

**修法**：`os.fsencode`。它是 argv 那次解码的**逆运算**，∴ 还原出的正是 git 在 `ls-tree -z` 里吐的
原始路径字节，与映射 key 的口径**天然对称**——不是「换个更宽容的编码」。

**MUST NOT 用 `except Exception` 兜底**（按评审要求未采用）：那会把编程错误一并吞成 UNKNOWN，
破坏 Task 2 的 Standards 轴已确认的「`main()` 只捕 `GateIndeterminate` ⇒ 无过度捕获」。

**用例**（两条，分工明确）：

| 用例 | 钉什么 |
|---|---|
| `test_non_utf8_change_reaches_design_branch_without_escaping` | **真的走到**那一行的编码点，经 `is_stale` 公共入口求值 |
| `test_non_utf8_change_exit_code_stays_in_contract_set` | 经 `main()` 求值，退出码 ∈ `{0,3,4,5,6}` |

> **🔴 诚实边界（第二条的覆盖缺口，显式登记）**：本机 APFS **拒绝**非 UTF-8 文件名
> （实测 `mkdir` → `[Errno 92] Illegal byte sequence`）⇒ 端到端那条走的是 `decide()` 的
> **归档短路半场**，够不到 design 域的路径编码那一行。它钉的是另一件事（argv 的非 UTF-8
> 字节在**任何**一步都不得逸出成退出码 1），不是 F1 本体。
> F1 本体由第一条覆盖——为绕开文件系统限制，它把两侧 `ls_tree_map` 直接摆好，
> 让 `is_stale` 从 `base` 拼出含 surrogate 的路径去查表。
> 这不是「测不到就算了」：**变异证明显示第一条对 F1 有完整判别力**（见下）。

### 变异证明 M-F1

`os.fsencode(...)` → `(base + "tasks.md").encode("utf-8")`：

```
E  UnicodeEncodeError: 'utf-8' codec can't encode character '\udcff' in position 19
FAILED test_non_utf8_change_reaches_design_branch_without_escaping
1 failed, 84 passed
```

改回后绿。

---

## F2 · 豁免闸门未校 `type == blob` —— 已修

**成因**：闸门只校 `mode/type` **两侧相等**。`ls-tree -r` **会**输出 gitlink
（`160000 commit <oid>\t<path>`）⇒ 两侧同为 `commit`、oid 不同时落进豁免分支 →
`cat-file blob` rc=128 → `UNKNOWN(6)`，诊断说「该路径已确认存在，故此为真读失败（仓损坏 / 权限）」。
方向 fail-closed（不放行），但**诊断口径错**——把「tasks.md 变成了 submodule」讲成「仓坏了」，
正是 `read_blob_bytes` docstring 自己禁止的那种误导。

**修法**：闸门加 `and after_entry[1] == b"blob"`（`before_entry[:2] == after_entry[:2]` 已保证两侧同类，
校一侧即足）。

**用例** `test_gitlink_tasks_is_stale_without_repo_corruption_diagnosis`：
用 `update-index --add --cacheinfo 160000,<oid>,<path>` 确定性造 gitlink（零网络、零 `.gitmodules`），
锚侧与 HEAD 侧各一个不同 oid。
**含前提校准**——先断言 `ls_tree_map` 确实把该项列成 `b"commit"`，否则本例失去区分力。
断言：判 stale + `REFUSE_START(3)` + 诊断**不含**「完整性 / 读取失败 / 读失败 / 仓损坏 / UNKNOWN」。

> 目录同名不构成同片洞：评审方已实测 `-r` 不输出 tree 项，未处理。

### 变异证明 M-F2

`after_entry[1] == b"blob"` → `after_entry[1] is not None`（恒真，等价于删掉该守卫）：

```
E  ship_gate.GateIndeterminate: [read-failed] 读 锚侧 的 …/tasks.md@e9a1b3b… 内容失败（rc=128）
   ——该路径已确认存在，故此为真读失败（仓损坏 / 权限）
FAILED test_gitlink_tasks_is_stale_without_repo_corruption_diagnosis
1 failed, 84 passed
```

🔴 **变异体一字不差地复现了评审方描述的误导诊断**——既证守卫有判别力，也二次确证缺陷为真。
改回后绿。

---

## F3 · `repo` fixture 不隔离全局 gitconfig —— 已修

**为什么它独立成立**（与那次未复现的失败无关）：被退役的旧用例曾显式补偿
`core.autocrlf false` / `core.fileMode true`，**补偿随退役一并消失**；而现役用例仍建在这两项上——

- 纯复选框翻转类依赖 `tasks.md` 的**字节原样回环**（`autocrlf` 一开就 CRLF↔LF 悄悄改字节）；
- `test_mode_only_change_on_tasks_is_stale` 依赖 chmod 真进 git（`fileMode` 一关就失去区分力）。

**修法**（两层，按面治不点名）：

1. fixture 的 git 调用改用 `_git_env()`：剔 `GIT_*` 前缀 + 回填 `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM`
   = `os.devnull`。**口径与生产侧 `ship_gate.py::_git_env` 逐字同源**，理由也是同一条：
   判定输入不得受这台机器的 config 摆布。生产侧封的是「被判仓的读取口径」，这里封的是
   「测试基座造出来的盘面本身」——两者一旦分叉，测试造的仓就不是它断言的那个仓。
2. 另把两个关键取值写进 repo-local `.git/config`。理由：env 只管 fixture 自己起的进程，
   被测代码与少数直连 `subprocess` 的测试点另有各自 env 口径 ⇒ 落到仓上才对**任何**读取者一致。

**用例** `test_repo_fixture_pins_byte_and_mode_semantics`（parametrize 两项）。

### 变异证明 M-F3

删掉 fixture 里那两行 `git config`：

```
E  - false
E  + input
FAILED test_repo_fixture_pins_byte_and_mode_semantics[core.autocrlf-false]
1 failed, 84 passed
```

🔴 **意外的实证**：变异体读出的不是「未设置」而是 **`input`** —— **本开发机的全局 gitconfig
真的设了 `core.autocrlf=input`**。F3 不是假想的跨机器风险，它在这台机器上当场成立。
（基准 3 的正面注脚：此前它没造成可见失败，不等于它不是缺陷。）
改回后绿。

### 🔴 未复现的那次失败 —— MUST NOT 宣称已定位

`test_pure_checkbox_flip_is_fresh_in_every_phase[None-RUN_PLAN]` 在全套件第 1 轮失败过 1 次，
traceback 已丢失；编排层另跑 25 轮孤立态全绿。

**本轮未能复现原失败**（修前修后都没再现），∴ **不能声称 F3 是它的成因、也不能声称它已被修好**。
本轮能说的只有两件事：① F3 是独立成立的缺陷，已修 + 有变异证明；
② 收敛证据 = `sdflow-ship/tests/` **连跑 5 轮全绿**（下表），仅此而已。

---

## F4 · 收紧 (a) 的登记理由实测为假 —— 已订正

原理由（`ship_gate.py` docstring + `task3-content-compare.md` §2(a)）：
「`git show` 受 textconv/smudge 影响 ⇒ 判定输入外部可控 ⇒ 违反 ADR-6」。

**已自行复跑核对（git 2.50.1）**，构造 `.gitattributes` 写 `a.md diff=fake filter=sm`
+ `git config diff.fake.textconv` / `filter.sm.smudge`：

| 命令 | 输出 |
|---|---|
| `git show HEAD:a.md` | `REAL`（原始字节） |
| `git show --textconv HEAD:a.md` | `FAKED-SMUDGE`（**只有显式 flag 才转换**） |
| `git cat-file blob HEAD:a.md` | `REAL` |

**前提为假**，已在两处订正为可核实的表述：`cat-file blob` 是**契约级**原始字节原语；
`show <rev>:<path>` 输出原始字节是**默认行为**（`--textconv` 可翻转）；
选前者是**缩小可翻转面**，不是修补现存的洞。

**并补上那条必须写的推论**：`archived_verify_state`（`ship_gate.py:337`）用
`git show <ref>:<path>` 读归档 verify-report、输出直接喂 SHIPPED 判定，
**依同一口径评估不受影响、无需改动**。
留着错理由的代价是确定的：后人要么去修一个不存在的洞，要么据此推出别的错结论。

仓内既有先例（退役的 `blob_pair` 注释）当年写的是同一句错理由 ⇒ **先例本身不构成证据**，一并作废。
本条是 `openspec/rules/premise-verification.md` 的实例。

---

## F5 · 测试清理 —— 已完成

| 处置 | 内容 |
|---|---|
| spy 去重 | `_spy_blob_reads` 上移到首个调用点之前；`test_no_content_read_when_maps_are_equal` / `test_content_read_does_happen_when_only_tasks_differs` 两处内联副本删除，改调 helper（三处共用单一源） |
| lambda 先用后定义 | `test_ls_tree_read_failure_is_indeterminate_not_fresh` 原 lambda 闭包引用**下一行才赋值**的 `_real`（能跑通纯属「lambda 体到调用时才求值」的巧合）⇒ 改为先取真值、再定义桩 |
| 打桩风格统一 | 5 处函数内 `import unittest.mock` 全部改 `monkeypatch` fixture。`test_retained_helpers_are_still_wired_into_production_path` 需要「打桩期 stale / 复原后 fresh」的对照 ⇒ 用 `monkeypatch.undo()` 显式复原，语义不变 |

清理后 `unittest.mock` 在 `test_gate_freshness.py` 内零残留。

---

## 测试结果

| 项 | 结果 |
|---|---|
| `sdflow-ship/tests/` 第 1 轮 | **317 passed** in 32.46s（基线 312 + 新增 5） |
| 连跑 5 轮（F3 收敛证据） | 317 / 317 / 317 / 317 / 317 **全绿**，32.1–32.3s |
| 仓根全套件 | **2070 passed, 8 skipped, 3 xfailed** in 139.42s |

**与基线（2064 passed, 9 skipped, 3 xfailed）的对账**：
passed +6 = 新增 5 条 + 1 条从 skip 翻为 pass；skipped −1 与之对冲，总数守恒。
翻转的那条落在 `sdflow-init/tests/`（`test_outside_voice_child_lifecycle.py` 与
`test_outside_voice_utf8.py` 两条**自登记为「常 skip、复现率环境敏感」**的用例之一），
**与本轮改动无因果**——本轮只动 `sdflow-ship/`。不低于基线，只增不减。

新增用例 5 条：F1×2、F2×1、F3×2（parametrize）。全部经 `is_stale` 公共入口或 `run_gate` 端到端求值。

### 变异证明汇总

| 编号 | 变异 | 结果 |
|---|---|---|
| M-F1 | `os.fsencode` → `.encode("utf-8")` | 1 failed（`UnicodeEncodeError`），84 passed → 改回绿 |
| M-F2 | `after_entry[1] == b"blob"` → 恒真 | 1 failed（复现误导诊断原文），84 passed → 改回绿 |
| M-F3 | 删 fixture 两行 `git config` | 1 failed（读出本机全局 `autocrlf=input`），84 passed → 改回绿 |

三次变异均已恢复原状，恢复后跑绿。

> M-F2 首次尝试用「整行删除」做变异，产生 `SyntaxError`（无判别力）⇒ 改为**恒真替换**重做。
> 登记此事：删行式变异在多行布尔条件里不等价于「删掉守卫」。

---

## 约束遵守

- 未改 `proposal.md` / `design.md` / `specs/` / `tasks.md`。
- 未在 commit subject 带 `task3-` 完成标签；未勾 `superpowers-plan.md` 复选框。
- `ship_gate.py` 零第三方依赖不变；退出码仍落在 `{0,3,4,5,6}`（F1 正是补回这条）。
- `main()` 的 `except` 仍只捕 `GateIndeterminate`（未引入 `except Exception`）。
- 未引入任何路径枚举通路 / 语义分诊层 / 重锚逃生口。

## 变异实验后的工作区状态

```
$ git status --porcelain
 M openspec/changes/harden-gate-git-layer/impl-reports/task3-content-compare.md
 M openspec/issues/todolist/2026-07-todolist.md
 M sdflow-ship/scripts/ship_gate.py
 M sdflow-ship/tests/conftest.py
 M sdflow-ship/tests/test_gate_freshness.py
?? openspec/changes/harden-gate-git-layer/impl-reports/task3-content-compare-fix1.md
?? openspec/changes/harden-gate-git-layer/impl-reports/task3-review-package.diff
```

三处变异均已还原（`ship_gate.py` / `conftest.py` 的 diff 只含本轮修复，不含变异体）。
`todolist` 与 `task3-review-package.diff` 的改动**先于本轮**（起手 `git status` 即已在），非本轮产物。
