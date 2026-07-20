# Task 5 · code 域改用顶层条目比较，两个消费方各有覆盖

**R-ID:** R2 · **Blocked-by:** 1 · **范围:** tasks 2.3 + 测试 5.11a / 5.11b / 5.12
**不做:** 评审 SKILL 时序（ADR-7）、文档收尾、全历史核验（都属 Task 6）

## 消掉的中间态

Task 3 落地 design 域内容比较后，code 分支仍是旧的 `git log <sha>..HEAD --name-only`
提交遍历（源码标注「归属 Task 5 的 tasks 2.3」）。它有两个已登记缺陷：
① `--name-only` 对 merge 提交不产 diff ⇒ **code 域 evil-merge 漏检**（merge 树里 resolve 出的
源码改动整帧漏掉）；② 提交遍历是「碰过哪些路径」的枚举式代理，与 design 域被换掉的那类推断同源。
本票把它换成**锚 vs HEAD 顶层条目映射比较**。

## 做了什么

### 2.3 code 分支重写（`ship_gate.py::is_stale`）

```python
# scope == "code"
anchor_top = ls_tree_map(root, sha, recursive=False)
head_top   = ls_tree_map(root, "HEAD", recursive=False)
anchor_code = {p: v for p, v in anchor_top.items() if p != b"openspec"}
head_code   = {p: v for p, v in head_top.items() if p != b"openspec"}
if anchor_code == head_code:
    return False, "fresh"
return True, "stale"
```

- **顶层条目的浅层快照**（`path→(mode,type,oid)` 映射，非递归）。tree 条目的 oid 递归摘要
  整棵子树 ⇒ 顶层某目录内**任意深度**的源码改动都翻转其顶层 tree oid、被捕获，无需 `-r`。
- **排除 `openspec` 记账条目**在 Python 侧按条目名做（`p != b"openspec"`），git pathspec 语义完全不参与。
- 谓词方向与 design 域**相反**：design 比「四件套 + specs/ 的内容是否变」；code 比「**排除 openspec 后**
  的顶层条目是否变」。∴ 没照抄 design 补丁的谓词。

**`ls_tree_map` 复用而非另造轮子**：为它加 `recursive`（默认 True，design 三个调用点不变）与
`pathspecs=()` 两个默认参数。design 域走 `recursive=True + 监视集 pathspecs`；code 域走
`recursive=False + 无 pathspecs`。`-z`（关 C-quote）、rc≠0⇒`GateIndeterminate`（读失败不折成空集
假等值）、原始字节 path 键——三条口径两域共用，天然不漂移。

**两条已实测证伪的错误路径，实现里都没走**（Compliance / design ADR-2 / 坑#2#3）：
- **MUST NOT 整树 sha**：done 写 `verify-report.md`（openspec 内）即改整树 sha ⇒ 正常收尾流程
  第一步假阳。∴ 排除 openspec 后按剩余顶层条目比。
- **MUST NOT 负向 pathspec** `':!openspec'`：继承外部可控的 `GIT_ICASE_PATHSPECS`。∴ 排除在 Python 侧。

### 收益（design.md 威胁模型两行 · 本域改判据唯一正面收益）

| 场景 | 旧 `--name-only` | 新顶层条目映射 |
|---|---|---|
| 代码审后经 merge 提交 resolve 引入源码改动 | 🔴 merge 不产 diff ⇒ 漏检 | ✅ 顶层 tree oid 变 ⇒ stale |
| `git mv` 把源码搬进 `openspec/` | 🔴 rename 检测只出目标（在 openspec 内被视 fresh） | ✅ 源顶层条目消失 ⇒ 映射不等 ⇒ stale |

### 头注释订正（随本改动失真的登记）

模块头 docstring「已知不覆盖」原写「**code 域仍走 --name-only … evil-merge 漏检依旧存在，
登记待后续」——本票改判后该句已失真。就地订正为「code 域已改顶层条目映射比较、比树终态而非
diff ⇒ evil-merge 改动被顶层 tree oid 反映、不再漏检（两域同源修复）」。属源码注释（本票产物），
非四件套；头 docstring 的整体重写仍归 Task 6.1。

## 测试（全部经 `is_stale` 公共入口 / `run_gate` 端到端，MUST NOT 只直调内部 helper）

`sdflow-ship/tests/test_gate_freshness.py` 新增一节（4 个用例）：

| 用例 | 覆盖 | 消费方 | 经何入口 |
|---|---|---|---|
| `test_code_domain_merge_introduces_source_change_is_stale` | 5.11a | **code-review-report**（e2e RERUN_STALE next=sdflow-code-review） | `is_stale(_CR_REL)` + `run_gate` |
| `test_code_domain_git_mv_source_into_openspec_is_stale` | 5.11b | **verify-report**（e2e RERUN_STALE next=sdflow-done） | `is_stale(_VF_REL)` + `run_gate` |
| `test_code_domain_openspec_accounting_writes_stay_fresh` | 5.12 fresh | 两消费方各求 fresh | `is_stale(_CR_REL)` + `is_stale(_VF_REL)` |
| `test_code_domain_excludes_openspec_by_entry_name_not_pathspec` | 2.3 机械守 | code-review-report | `is_stale(_CR_REL)` + 直读 `ls_tree_map` 校前提 |

**两个消费方各有覆盖**（坑#4 · design 登记 `code-review-report` 今天零覆盖）：5.11a 端到端
落在 **code-review-report** 消费方（step8，`verify=PASS` 时 cr-stale 直接 RERUN_STALE）；5.11b
端到端落在 **verify-report** 消费方（`verify=FAIL` ⇒ step8 的 cr-stale 让位、判定落到 step9 的
verify 读点）。两条各驱动一个不同消费方到 stale 路径。

**5.11a 用真·code 域 evil-merge**（`_evil_merge_toplevel`）：两个 parent 都**只碰 openspec/**、
merge 提交自身 resolve 出顶层源码 `resolved.py` ⇒ 该改动**仅存在于 merge 树**。旧 `--name-only`
对 merge 不产 diff 会整帧漏掉；顶层映射只看锚与 HEAD 两端的树、对拓扑不敏感 ⇒ 必抓。这是相对
旧实现的判别性收益，不是随便一个「加了个文件」的用例。

## 变异证明（按守卫计数 · 每条删掉即变红 · 变异体先 `ast.parse` 确认可运行）

用 harness（`scratchpad/mutate.py`）对每条守卫做恒真/恒假替换、`ast.parse` 通过后跑目标用例，
确认转红，随即复原。**MUST NOT 以「用例存在且为绿」充当证明**——以下每条都实跑过变红。

| 守卫 | 变异（恒真/恒假，ast 可运行） | 目标用例 | 结果 |
|---|---|---|---|
| **G1** 不等映射 ⇒ stale（收益守卫） | `if anchor_code == head_code:` → `if True:`（恒 fresh） | 5.11a + 5.11b | **2 failed**（变红✅） |
| **G2** 排除 `openspec` 条目 | `if p != b"openspec"` → `if True`（两处，不排除） | 5.12 fresh + excludes-by-entry-name | **2 failed**（变红✅） |
| **G3** `recursive=False`（浅层顶层快照） | `recursive=False` → `recursive=True`（两处） | 5.12 fresh | **1 failed**（变红✅） |

- **G1** 是「code 域改判据唯一正面收益」的守卫：删掉它，merge/git-mv 引入的源码改动全部逃逸。
  5.11a、5.11b **各附一次**变异证明（对应 tasks 5.11a/b「MUST 各附变异证明」）。
- **G2** 变异（不排除 openspec）⇒ 记账写（落报告 / 归档移目录）改了 openspec 顶层 tree oid ⇒
  映射不等 ⇒ 误判 stale ⇒ 5.12 转红。这正是「MUST NOT 整树 sha」的机械体现。
- **G3** 变异（recursive=True）⇒ openspec 子树内的文件以 `openspec/...` 路径逐条进映射、不被
  `!= b"openspec"` 排除 ⇒ 记账写即失鲜 ⇒ 5.12 转红。证明浅层是必需的（否则排除口径失效）。

复原后 restore-check 用例复跑通过（文件完好）。

## 删除既有用例

**无删除**。旧 code 分支的既有端到端用例（`test_stale_pass_reruns_not_ship` /
`test_stale_fail_reruns_not_exit5` / `test_openspec_only_commits_keep_fresh` 等）**语义不变、逐字保留**
——它们断言的是消费方 verdict（RERUN_STALE / fresh），对「顶层条目 vs --name-only」的实现切换
不可见，切换后仍全绿（322→326，只增不改不删）。code 域此前没有承载「仍生效安全承诺」的
evil-merge/git-mv 专用用例可改写（那类只在 design 域存在，Task 3 已处理）；code 域的对应能力是
本票**新增**（5.11a/5.11b），非改写退役件。

## 测试结果

- `sdflow-ship/tests/`：**326 passed**（基线 322 + 本票 4）。
- 新增 4 用例单独跑：4 passed。
- `test_gate_git_layer.py`（design 域 ls_tree_map 相关，受 `recursive` 参数改动波及面）：32 passed。

## 边界 / Concerns

- **窗口右边界残余面不变**：code 域两个消费方是「位置即阶段」，本票未动求值窗口（那是 Task 4）。
- **头 docstring 整体重写**归 Task 6.1；本票只就地订正了随本改动**失真**的那一句 evil-merge 登记，
  避免留一条与代码矛盾的「已知不覆盖」误导后人（目标态导向：登记须反映改后现实）。
- **SHA-1 仓形态假设**沿用 Task 1（40 位 OID）；SHA-256 object-format 仓的锚会在 `read_reviewed_sha`
  语法级判非法，与本票无关（Task 1 已登记）。
