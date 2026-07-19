# Task 1 — fix 轮次 1：双轴审 F1 / F3 修复报告

**修复对象:** `impl-reports/task1-cleanup-polluted-env.md`（首轮报告，保留未覆盖）
**起始 HEAD:** 318f79f · **仓根起始状态:** 0 棵 brace 目录

只改了首轮报告一个文件。未触碰 `proposal.md` / `design.md` / `tasks.md` / `specs/`（避免 ship gate 设计门失鲜），
未触碰任何 `scripts/` 或测试代码（`repo_root` 加固是 Task 2 靶心）。

---

## F1【Important】勾框与报告正文自相矛盾，二次删除无记录

### 问题实质

首轮报告同时存在两句互斥的陈述：

- 第 125 行验收对照勾了 `[x] 仓根不再有以 { 开头的目录条目（复核 count = 0）`
- 第 65 行正文写「跑完全量 pytest 后再查，**4 棵树原样重现**」

而仓根当前确为 0 ⇒ 两句之间必然发生过一次**二次删除**，报告里却没有它的任何记录。
净结果 = **一个被后续事件推翻了的复核，仍在支撑一个勾着的框**——正是本 change 要治的那类假绿，
出现在本 change 自己的实现报告里。

### 修法：不是改措辞，是补证据 + 把承诺降到如实口径

**(1) 真跑一遍完整循环并捕获输出**，落为首轮报告的新增一节
`## 再生—清理循环的机械锚（fix 轮次 1）`，含 a–f 六步的**原样命令与原样输出**：

| 步 | 内容 | 实测结果 |
|---|---|---|
| a | 起始计数 | `count = 0` |
| b | `/usr/bin/python3 -m pytest sdflow-issues/tests/test_task4_rename_snapshot.py -q` | `91 passed in 1.31s`（**0 failed**） |
| c | 再次列举 + 首棵完整 `os.walk` 树 | `count = 4`，`total subdirs = 20 / total regular files = 0` |
| d | 带守卫 `shutil.rmtree`（5 道断言） | `all 4 guards passed`，4 次 `rmtree OK` |
| e | 最终列举 | `count = 0` |
| f | `git status --porcelain` | 仅 1 条本轮自产的评审包 diff，**无跟踪文件受影响** |

守卫五道闸（删前逐棵断言）：cwd `realpath` == 仓根 · 计数恰为 4 · `isdir` 且非 symlink ·
`realpath` 的父目录仍是仓根 · 树内 0 个普通文件。未用 shell glob（目录名含空格/引号/花括号/方括号）。

**(2) 改写验收对照第一条**为时点性表述，显式写出成立条件与失效条件，并把永久性达标的归属指向 Task 6：

> **【时点性达标】** … **成立条件：自该次清理后未在仓根跑过 pytest。** 任何一次仓根 pytest 都会立刻使本条失效 …
> 本条**不可读作「仓根已永久干净」**。「不再再生」的永久性达标由 Task 6 收口，前置是 Task 2 对 `repo_root` 的 fail-closed 加固。

归属核实（非转述）：`superpowers-plan.md:186` = `### Task 6: 面治闭环与收尾`，
其 `:207` 验收项原文即「垃圾目录树**未再生**（Task 1 删的是存量，本条验证的是「修完之后不会重新长出来」）」。

### 本轮的增量发现

1. **再生是确定性的，且不需要全量 pytest**——单跑 `test_task4_rename_snapshot.py` 一个文件（1.31s）即稳定产出 4 棵、
   形态与首轮**逐字节同形**（同样 20 子目录 / 0 文件）。首轮报告只说了「全量跑后重现」，本轮把触发面收窄到了一个文件。
2. **污染是绿测试的副作用**：触发步 `91 passed / 0 failed`。没有任何失败信号伴随污染
   ⇒ 靠「看测试红没红」永远发现不了它，这也是 Task 5（cwd 泄漏 autouse fixture）存在的理由。
3. **完整 walk 树坐实了双层下钻**：payload 里 `"file": "openspec/issues/buglist/2026-01-01-buglist.md"` 被切成路径后，
   尾段 `...2026-01-01-buglist.md"}], "problems": []}` 又被当成目录名继续生出 `openspec/issues`
   ⇒ 落盘深度 5 层。首轮只给了顶层 4 条与汇总数，本轮补了完整树。

---

## F3【Minor】Concern 3 未验证即断言（违 PV 规则 1）

### 核实结果：原断言一半是错的

首轮 Concern 3 称「若 **CI**/他人用默认 `python3` 会直接 `No module named pytest`」。
**真打开两个 workflow 核实**（未采信任何转述）：

- `.github/workflows/mechanical-gates.yml:33-34` — `- name: Install pytest` / `run: python -m pip install pytest`
  （矩阵 `os: [ubuntu-latest, macos-latest]`，`setup-python@v5` 固定 3.12）
- `.github/workflows/windows-recorder-smoke.yml:30-31` — `- name: Install pytest` / `run: py -m pip install pytest`

⇒ **两条泳道都显式装 pytest，CI 完全不在该风险面内。**

### 修法

Concern 3 改写为如实表述：保留本地默认 `python3`（`~/.local/bin/python3`）无 pytest 的事实，
删去对 CI 的错误外推，改为写明**两条 CI 泳道各自的 `文件:行` 与安装命令**，
并把风险范围收敛为「**仅限本地开发者用默认 `python3` 直跑**」。

---

## 验证

- 仓根 brace 目录计数 = **0**
- `git status --porcelain` = 干净（提交后）
- 未修改任何脚本 / 测试 / change 四件套，无 ship gate 失鲜风险

## 备注

`impl-reports/task1-review-package.diff`（本轮双轴审的评审包，132 行）此前为未跟踪状态，
按 `git add -A` 一并入库，作为审计轨迹保留。
