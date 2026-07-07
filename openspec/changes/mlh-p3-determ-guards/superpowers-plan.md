# mlh-p3-determ-guards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为机械层补两处 fail-closed 确定性守卫——recorder 镜像 helper 一致性测试（AST 等价）+ config/batches 人写字段 lint（config_lint、batch lint）。

**Architecture:** 三份 recorder（buglist/todolist/issues）刻意 verbatim 各自持有共享 helper（D4 红线禁跨 skill import）。本 change 用「剥 docstring 后 AST 等价」的一致性测试守其不漂移（Path B，grill 拍板），并顺手归一 2 个逻辑等价异写使 AST 契约对全 11 helper 成立。另加两个 fail-closed 校验器：`init.py config-lint`（第 4 个 mode，手写 stdlib 行扫描不 import yaml）、`issues.py batch lint`（复用 `_split_batches_entries` 只读语法校验）。零行为改动、零 SKILL.md 改动、纯增测/校验器。

**Tech Stack:** Python 3 stdlib only（`ast`/`inspect`/`textwrap`/`importlib.util`/`re`/`subprocess`）；pytest。**MUST NOT 引入 PyYAML 或任何第三方依赖**（全仓零依赖惯例；脚本以 symlink 铺消费仓，import yaml 会 ImportError 崩）。

## Global Constraints

- **TDD 纪律**：每任务组先写失败测试、跑红、再实现、跑绿。数据类改动，改 `scripts/` 必同步跑对应 `tests/`。
- **零行为改动**：不改 recorder 现有读写逻辑、不改 config/batches 现有内容、不改任何 SKILL.md、不触 bundle 行为面。
- **D4 硬红线**：①recorder 绝不跨 skill import（用 `importlib.util` 独立加载 + `inspect.getsource` 只读断言）；②绝不覆写人写行（batch lint 只读语法校验）。
- **fail-closed**：新校验器违规 → stderr human reason + 非零退出；干净 → 退出 0。顶层块缺失一律条件化放行、绝不裸取抛 KeyError。
- **checkpoint TAG 格式**：每任务组收尾 commit MUST 用 `~/.sdflow/hack/checkpoint-commit.sh mlh-p3-determ-guards:task<N>-<slug> "<描述>"`（带 change 命名空间 `mlh-p3-determ-guards:` + `task<N>-` 横杠，`ship_gate.py` TAG_RE 主锚契约；跨 change stacking 不污染）。
- **PRIORITIES 单一源**：`PRIORITIES = ["P0","P1","P2","P3","P4"]`（buglist.py:57 权威）；issues.py 内声明同款常量，一致性由值相等断言守，**不跨 import**。
- **`—` = U+2014**（em dash，接地核实与正则字面一致）。

---

### Task 1: recorder 镜像 helper 一致性测试（3.A，spec 需求①④）

**Files:**
- Modify: `sdflow-todolist/scripts/todolist.py`（`split_sections` / `block_ranges` 两处归一到 buglist 写法，只改表达式、不改行为）
- Create: `sdflow-buglist/tests/test_mirror_consistency.py`
- Test: `pytest sdflow-buglist/tests/ sdflow-todolist/tests/`

**Interfaces:**
- Consumes: `sdflow-buglist/scripts/buglist.py`、`sdflow-todolist/scripts/todolist.py`、`sdflow-issues/scripts/issues.py` 的源码（只读断言，不 import 包）。
- Produces: `test_mirror_consistency.py` 中的 `_ast_no_doc(fn)` helper、`THREE_WAY` / `TWO_WAY` 常量 —— Task 3 Step「补 PRIORITIES 断言」回填 `test_priorities_constant_consistency` 到同文件。

> grill 已定夺：契约 = 剥 docstring 后 AST 等价（非 byte）；9 个 helper 当前即过，2 个逻辑异写（split_sections/block_ranges）本组顺手归一。见 design D2/D6。**先归一、再建 harness**——否则 AST 契约对 2 处逻辑异写假红。

- [ ] **Step 1: 先归一 todolist 的 `split_sections`（前置，使 AST 契约成立）**

打开 `sdflow-todolist/scripts/todolist.py`，先 Read 对照 `sdflow-buglist/scripts/buglist.py` 同名函数确认行为等价，再把 todolist 侧 `split_sections` 的表达式归一到 buglist 写法：
- todolist 当前：`rows_start = table_hdr + 2`
- 归一为 buglist 写法：`sep = table_hdr + 1` 后 `rows_start = sep + 1`

**只改表达式写法、不改行为、不改 docstring 语境。**

- [ ] **Step 2: 归一 todolist 的 `block_ranges`（两处独立差异，均须改）**

同文件 `block_ranges`，spec-review H3 实测**两处**差异，只改一处 AST 仍不等：
- ① starts 构造：todolist 的「列表推导 + walrus」→ buglist 的「for-loop + append」写法。
- ② 消费循环签名：todolist `for i, bid in starts:` → buglist `for idx, (i, bid) in enumerate(starts):`（含未用的 `idx`）。

以 buglist 为单一真相源，两处一并改齐。

- [ ] **Step 3: 归一后跑 todolist 全测确认零回归**

Run: `pytest sdflow-todolist/tests/ -v`
Expected: PASS（design D6 硬要求——归一不得触行为面；若红 → 停下核对归一是否完整/偏差，MUST NOT 为过测偷改行为）。

- [ ] **Step 4: 写一致性测试 harness（module 加载 + `_ast_no_doc`）**

Create `sdflow-buglist/tests/test_mirror_consistency.py`：用 `importlib.util.spec_from_file_location` 从三份 recorder 脚本各自加载 module（不 import 包，避免耦合）。写 helper `_ast_no_doc(fn)`：`textwrap.dedent(inspect.getsource(fn))` → `ast.parse` → 剥函数首个 docstring 表达式（若首 stmt 是 `ast.Expr` 且 value 为 `ast.Constant`/字符串则 pop）→ `ast.dump`。定义常量：

```python
THREE_WAY = ["atomic_write", "repo_root", "_reject_cell_unsafe"]
TWO_WAY   = ["detect_change", "normalize_doc_paths", "auto_default_doc",
             "split_sections", "parse_table_rows", "block_ranges",
             "_ids_in_files", "_find_row_file"]
```

- [ ] **Step 5: 写 3 向 + 2 向断言**

- 3 向：`for f in THREE_WAY: assert _ast_no_doc(getattr(BUG, f)) == _ast_no_doc(getattr(TODO, f)) == _ast_no_doc(getattr(ISS, f))`，失败信息含 helper 名 + 哪几份不一致。
- 2 向：`for f in TWO_WAY: assert _ast_no_doc(getattr(BUG, f)) == _ast_no_doc(getattr(TODO, f))`，**断言范围不含 issues.py**（issues 不含表解析 helper）。

- [ ] **Step 6: 写三条守卫证伪用例**

- `test_docstring_diff_ok`：现存三份 helper（docstring 本就不同，如 `issues.atomic_write` 多注记）一致性测试通过——守的是行为、非字面。
- `test_logic_drift_is_caught`：临时构造一个 AST 不等的 helper 对（注入改一处逻辑）→ 断言 `_ast_no_doc` 比对报不等（证守卫抓真漂移、非 no-op）。
- helper 删除证伪（spec 需求① scenario·L1）：确认比对代码用**直接属性访问** `getattr(m, f)`、**未用 try/except 吞 AttributeError**——某 recorder 删 helper 时须因 AttributeError 而红，不静默跳过；加注释锁死该约束。

- [ ] **Step 7: 基线跑，确认全绿**

Run: `pytest sdflow-buglist/tests/test_mirror_consistency.py -v`
Expected: PASS（剥 docstring 后 11 个 helper 全 AST 等价）。若意外红 → 停下核对归一是否完整（尤其 block_ranges 两处）/拓扑是否偏差，**MUST NOT 为过测偷改行为面**。

> 注：`test_priorities_constant_consistency`（需求① M1）依赖 Task 3 声明 issues.PRIORITIES，在 Task 3 完成后回填本文件（见 Task 3 Step 6）。

- [ ] **Step 8: 复核归一零回归 + Commit**

Run: `pytest sdflow-buglist/tests/ && pytest sdflow-todolist/tests/`
Expected: PASS

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p3-determ-guards:task1-mirror-consistency "recorder helper 3向/2向 剥docstring-AST等价一致性测试(grill Path B) + 归一2个逻辑异写(block_ranges两处,零回归) + docstring分化放行/逻辑分叉/helper删除证伪"
```

---

### Task 2: config_lint（3.B①，spec 需求②）

**Files:**
- Modify: `sdflow-init/scripts/init.py`（`mode` 的 `choices` 加 `config-lint` + 早分支 return，MUST NOT 引入 `add_subparsers()` 重构）
- Create/Extend: `sdflow-init/tests/test_config_lint.py`
- Test: `pytest sdflow-init/tests/`

**Interfaces:**
- Consumes: `openspec/config.yaml`（回归基线，只读）；范式来源 `sdflow-init/assets/workflow/tools/anchor_lint.py::read_metrics_enabled`。
- Produces: `config-lint` mode（`python3 init.py config-lint [--root]`）。

> 关键订正（多镜）：**不 import yaml**（手写行扫描 follow anchor_lint::read_metrics_enabled）；**不 add_subparsers**（config-lint 作 mode 第 4 值、早分支 return，同 retire-hooks）；顶层块缺失条件化放行（防 mlh-p2 假阳）；Q1 已拍板 = 手写 stdlib。

- [ ] **Step 1: 先写失败测试**

Create/extend `sdflow-init/tests/test_config_lint.py`，用 subprocess 或直接调用 lint 入口，覆盖：
- **坏结构**（扫不出 `schema`/`rules`）→ 非零退出 + reason 含关键词。
- **缺 `rules.proposal`** → 非零 + reason。
- **构造 model-tiers 越域子键**（非 {strong,mid,light}）→ 非零 + reason。
- **构造 metrics 块含 `enabled: yes-please`（非 bool）** → 非零 + reason。
- **回归基线**：当前真实 `openspec/config.yaml` → 退出 0。
- **条件化放行**：无 model-tiers 块 → 0。
- **无 metrics 块的消费仓风格 config fixture → 退出 0**（防 mlh-p2 同类假阳，M3）。

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-init/tests/test_config_lint.py -v`
Expected: FAIL（mode 未实现，argparse 拒 `config-lint` 或函数不存在）。

- [ ] **Step 3: 实现 config-lint**

在 `sdflow-init/scripts/init.py`：
- **加进现有 `mode` 的 `choices` 列表 + 早分支 return**（同 `retire-hooks`，MUST NOT 引入 `add_subparsers` 重构）。
- `--root` 缺省经 `subprocess git rev-parse --show-toplevel` 探 git 根、非 git 降级 `"."`（M7）。
- **手写 stdlib 行级扫描**（follow `anchor_lint.py::read_metrics_enabled`）：定位顶层 `schema:` 键存在、`rules:` 下 proposal/specs/design/tasks 四子键、`model-tiers:`（若存在）子键 ⊆ {strong,mid,light}、`metrics:`（若存在）`enabled` 值 ∈ {true,false}。
- **所有顶层块用「先探测存在再校验」，块缺失放行、绝不裸取抛 KeyError**。
- 违规累积 reason、stderr 输出、非零退出；干净退出 0。只校验结构，不碰内容文案。

- [ ] **Step 4: CLI 冒烟测试（防破坏既有 mode）**

加 `subprocess.run(["python3", init_py, "init"/"update"/"retire-hooks", ...])` 冒烟（adv-A 爆点2），确认加 config-lint 后既有 3 个 mode 解析未受扰动。

- [ ] **Step 5: 跑绿 + Commit**

Run: `pytest sdflow-init/tests/`
Expected: PASS

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p3-determ-guards:task2-config-lint "init.py config-lint(mode第4值,手写stdlib扫描不import yaml)：必填段+tier枚举+metrics条件化,块缺失放行fail-closed+既有mode冒烟+测试"
```

---

### Task 3: issues.py batch lint（3.B②，spec 需求③）

**Files:**
- Modify: `sdflow-issues/scripts/issues.py`（声明 `PRIORITIES` + 实现 `batch lint`）
- Create/Extend: `sdflow-issues/tests/`（扩 test_issues.py 或新文件）
- Modify: `sdflow-buglist/tests/test_mirror_consistency.py`（回填 PRIORITIES 值断言）
- Test: `pytest sdflow-issues/tests/`、`pytest sdflow-buglist/tests/`

**Interfaces:**
- Consumes: `_split_batches_entries`（issues.py 现有，逐条切分 batches.md）；`BATCH_PLACEHOLDER`（issues.py:438，`<待填>`）；`PRIORITIES`（Task 1 harness 消费本 Step 声明的常量）。
- Produces: `PRIORITIES = ["P0","P1","P2","P3","P4"]`（issues.py，供 Task 1 值断言）；`batch lint` 子命令。

> 关键订正（五镜）：优先级也豁免 `<待填>`（H1）；前导 token 后**剩余一律不校验**（H4，`P1 ★` 须过）。

- [ ] **Step 1: 先写失败测试**

Create/extend `sdflow-issues/tests/`，覆盖：
- **坏**：`优先级: 高` / `优先级: PX`（非占位）→ 非零；`计划:` 空（非占位）→ 非零。
- **过**：`优先级: P2（T10 已 DONE）` / `—（已闭合）` / **`P1 ★`（裸星号后缀）** / **`<待填>`（占位豁免）** → 通过；`计划: <待填>` → 通过。
- **回归基线**：当前真实 batches.md 全条目（含 3 条 `优先级: <待填>` + 1 条 `P1 ★`）→ 退出 0。

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-issues/tests/ -v`
Expected: FAIL（`batch lint` 子命令未实现）。

- [ ] **Step 3: 声明 PRIORITIES + 实现 batch lint**

在 `issues.py`：
- 声明 `PRIORITIES = ["P0","P1","P2","P3","P4"]`（同 buglist.py:57；一致性由 Task 1 值相等断言守，非跨 import）。
- 实现 `batch lint`：读 batches.md → `_split_batches_entries` 逐条 → 对每条 entry_lines 新写正则 grep `优先级:` / `计划:` 值：
  - 值 == `BATCH_PLACEHOLDER` → **两字段均豁免**（D5）。
  - 否则 优先级 `re.match(r"^(P\d|—)", v.strip())` 取前导 token ∈ `PRIORITIES ∪ {—}`、**匹配后剩余不校验**（D4，`P1 ★` 须过）。
  - 计划非占位时校验非空白。
- 违规非零退出 + 指明批次/字段；只读、不覆写人写行。

- [ ] **Step 4: 跑绿**

Run: `pytest sdflow-issues/tests/`
Expected: PASS

- [ ] **Step 5: 回填 PRIORITIES 值断言到 Task 1 文件**

在 `sdflow-buglist/tests/test_mirror_consistency.py` 补 `test_priorities_constant_consistency`：`assert BUG.PRIORITIES == ISS.PRIORITIES`（**独立 `==` 路径、非 getsource**——getsource 对 list 抛 TypeError；R4）。

- [ ] **Step 6: 重跑 buglist 测试确认绿 + Commit**

Run: `pytest sdflow-buglist/tests/`
Expected: PASS

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p3-determ-guards:task3-batch-lint "issues.py batch lint：优先级/计划占位符豁免+前导token后缀不校验(P1★过)+声明PRIORITIES(值断言守漂移)，复用_split_batches_entries只读，fail-closed+测试"
```

---

### Task 4: 收尾验证（spec 全需求交叉核）

**Files:**
- Test only（无源码改动，纯验证）

- [ ] **Step 1: 全量测试**

Run: `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/`
Expected: 全绿。

- [ ] **Step 2: 手验 fail-closed**

故意造坏 config / 坏 batch 字段 → 跑 lint 确认非零退出（临时改、验完还原）。

- [ ] **Step 3: 手验现存数据零假阳**

对当前真实 config.yaml（有 metrics 块、无 model-tiers 活跃段）+ batches.md（含 3 条 `优先级: <待填>`、`P1 ★`、`—（已闭合）`）跑 lint → 均退出 0。**核**：model-tiers 越域 + 无 metrics 块 两分支靠构造 fixture 测（真实文件测不到），确认 Task 2 Step 1 已含。

- [ ] **Step 4: openspec validate**

Run: `openspec validate mlh-p3-determ-guards`
Expected: 通过。

- [ ] **Step 5: 确认 Task 1 归一留痕**

确认 Task 1 归一（todolist split_sections/block_ranges）已随 checkpoint 提交、todolist 全测零回归留痕（D6 顺手修边界）。

- [ ] **Step 6: Commit（收尾标记）**

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p3-determ-guards:task4-verify "收尾全量验证：pytest全绿+fail-closed手验+现存零假阳+openspec validate"
```
