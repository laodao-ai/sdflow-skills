# tasks — mlh-p3-determ-guards

> TDD 纪律：每任务组先写失败测试、再实现、跑绿。数据类改动，改 scripts/ 必同步跑对应 tests/。
> 每任务组收尾 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p3-determ-guards:task<N>-<slug> "<描述>"`（带 change 命名空间 + 横杠，ship_gate TAG_RE 主锚）。
> 依赖顺序：Task 1（归一 2 个逻辑异写 → AST 等价一致性测试；D6/A2 已在 grill 定夺，无需 SDD 期再决）→ Task 2（config_lint）→ Task 3（batch lint）→ Task 4（收尾验证）。Task 2/3 独立可换序。

## 1. recorder 镜像 helper 一致性测试（3.A，spec 需求①④）〔grill: 锁 AST 等价, Path B〕

> grill 已定夺：契约 = 剥 docstring 后 AST 等价（非 byte）；9 个 helper 当前即过，2 个逻辑异写（split_sections/block_ranges）本组顺手归一。见 design D2/D6。

- [x] 1.1 **先归一 2 个逻辑异写**（前置，使 AST 契约对全 11 个成立）：把 `sdflow-todolist/scripts/todolist.py` 的 `split_sections`/`block_ranges` 表达式**归一到 `sdflow-buglist/scripts/buglist.py` 的写法**（已 diff 核实行为等价）。**只改表达式写法、不改行为、不改 docstring 语境**：
      - `split_sections`（一处）：todolist `rows_start = table_hdr + 2` → buglist `sep = table_hdr + 1; rows_start = sep + 1`。
      - `block_ranges`（**两处**·spec-review H3）：① starts 构造 列表推导+walrus → for-loop+append；② 消费循环 `for i, bid in starts:` → `for idx, (i, bid) in enumerate(starts):`。**两处都改**，否则 AST 仍不等。
- [x] 1.2 归一后跑 todolist 全测确认零回归：`pytest sdflow-todolist/tests/ -v`（design D6 硬要求——归一不得触行为面）。
- [x] 1.3 新建 `sdflow-buglist/tests/test_mirror_consistency.py`：用 `importlib.util.spec_from_file_location` 从三份 recorder 脚本各自加载 module（不 import 包，避免耦合）；写 helper `_ast_no_doc(fn)`：`textwrap.dedent(inspect.getsource(fn))` → `ast.parse` → 剥函数首个 docstring 表达式 → `ast.dump`。定义 `THREE_WAY`（atomic_write/repo_root/_reject_cell_unsafe）+ `TWO_WAY`（八个表解析/文档 helper）常量。
- [x] 1.4 写 3 向断言：`_ast_no_doc(BUG.f)==_ast_no_doc(TODO.f)==_ast_no_doc(ISSUES.f)` for f in THREE_WAY；失败信息含 helper 名 + 哪几份不一致。
- [x] 1.5 写 2 向断言：`_ast_no_doc(BUG.f)==_ast_no_doc(TODO.f)` for f in TWO_WAY；**断言范围不含 issues.py**（issues 不含表解析 helper）。
- [x] 1.6 写 docstring 分化不报漂移用例（`test_docstring_diff_ok`）：确认现存三份 helper（docstring 本就不同，如 issues.atomic_write 多注记）一致性测试通过——守的是行为、非字面。
- [x] 1.7 写故意逻辑分叉证伪用例（`test_logic_drift_is_caught`）：临时构造一个 AST 不等的 helper 对（如注入改一处逻辑）→ 断言 `_ast_no_doc` 比对报不等（证守卫抓真漂移、非 no-op）。
- [x] 1.8 **helper 删除证伪**（spec 需求① scenario·L1）：确认比对代码用**直接属性访问**取 helper（`getattr(m, f)`）、**未用 try/except 吞 AttributeError**——某 recorder 删 helper 时测试须因 AttributeError 而红，不静默跳过。加注释锁死该约束。
- [x] 1.9 **PRIORITIES 常量值相等断言**（spec 需求①新 scenario·M1，Task3 依赖前置）：待 Task3 在 issues.py 声明 `PRIORITIES` 后，在本测试文件加 `test_priorities_constant_consistency`：`assert BUG.PRIORITIES == ISS.PRIORITIES`（**独立 `==` 路径、非 getsource**——getsource 对 list 抛 TypeError）。**注**：此断言依赖 Task3 已声明 issues.PRIORITIES；若 Task3 后置，本项在 Task3 完成后回补并重跑（tasks 顺序：Task1 先建 harness，PRIORITIES 断言随 Task3 落地补入本文件，Task4 收尾确认）。
- [x] 1.10 **基线跑**：`pytest sdflow-buglist/tests/test_mirror_consistency.py -v` 全绿（剥 docstring 后 11 个 helper 全 AST 等价）。若意外红 → 停下核对归一是否完整（尤其 block_ranges 两处）/拓扑是否偏差，**MUST NOT 为过测试偷改行为面**。
- [x] 1.11 `pytest sdflow-buglist/tests/` + `pytest sdflow-todolist/tests/`（1.2 已跑，此处复核归一零回归）全绿。
- [x] 1.12 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p3-determ-guards:task1-mirror-consistency "recorder helper 3向/2向 剥docstring-AST等价一致性测试(grill Path B) + 归一2个逻辑异写(block_ranges两处,零回归) + docstring分化放行/逻辑分叉/helper删除证伪"`

## 2. config_lint（3.B①，spec 需求②）〔spec-review: 手写 stdlib + mode 值 + 条件化〕

> 关键订正（多镜）：**不 import yaml**（手写行扫描 follow anchor_lint::read_metrics_enabled）；**不 add_subparsers**（config-lint 作 mode 第 4 值、早分支 return，同 retire-hooks）；顶层块缺失条件化放行（防 mlh-p2 假阳）；需拍板 Q1 = 手写 vs PyYAML（推荐手写）。

- [x] 2.1 先写失败测试 `sdflow-init/tests/test_config_lint.py`：坏结构(扫不出 schema/rules) / 缺 `rules.proposal` / **构造** model-tiers 越域子键 / **构造** metrics 块含 `enabled: yes-please`(非bool) → 各断言非零退出 + reason 含关键词。**回归基线**：当前真实 `openspec/config.yaml` → 退出 0。**条件化放行**：无 model-tiers 块 → 0；**无 metrics 块的消费仓风格 config fixture → 退出 0**（防 mlh-p2 同类假阳，M3）。
- [x] 2.2 跑测试确认失败（mode 未实现）。
- [x] 2.3 在 `sdflow-init/scripts/init.py` 实现 `config-lint`：**加进现有 `mode` 的 `choices` 列表 + 早分支 return（同 retire-hooks，MUST NOT 引入 add_subparsers 重构）**；`--root` 缺省经 `git rev-parse --show-toplevel` 探 git 根、非 git 降级 `"."`。**手写 stdlib 行级扫描**（follow `assets/workflow/tools/anchor_lint.py::read_metrics_enabled`）：定位顶层 `schema:`/`rules:` 键存在、`rules:` 下 proposal/specs/design/tasks 四子键、`model-tiers:`(若存在)子键 ⊆ {strong,mid,light}、`metrics:`(若存在)`enabled` 值 ∈ {true,false}。**所有顶层块用「先探测存在再校验」，块缺失放行、绝不裸取抛 KeyError**。违规累积 reason、stderr 输出、非零退出；干净退出 0。只校验结构，不碰内容文案。
- [x] 2.4 **CLI 冒烟测试**（adv-A 爆点2·防破坏既有 mode）：加 `subprocess.run(["python3", init.py, "init"/"update"/"retire-hooks", ...])` 冒烟，确认加 config-lint 后既有 3 个 mode 解析未受扰动。
- [x] 2.5 `pytest sdflow-init/tests/` 全绿。
- [x] 2.6 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p3-determ-guards:task2-config-lint "init.py config-lint(mode第4值,手写stdlib扫描不import yaml)：必填段+tier枚举+metrics条件化,块缺失放行fail-closed+既有mode冒烟+测试"`

## 3. issues.py batch lint（3.B②，spec 需求③）〔spec-review: 优先级占位符豁免 + 后缀不校验〕

> 关键订正（五镜）：优先级也豁免 `<待填>`（H1）；前导 token 后**剩余一律不校验**（H4，`P1 ★` 须过）。

- [x] 3.1 先写失败测试 `sdflow-issues/tests/`（扩 test_issues.py 或新文件）：**坏**——`优先级: 高`/`优先级: PX`(非占位) → 非零；`计划:` 空(非占位) → 非零。**过**——`优先级: P2（T10 已 DONE）`/`—（已闭合）`/**`P1 ★`(裸星号后缀)**/**`<待填>`(占位豁免)** → 通过；`计划: <待填>` → 通过。**回归基线**：当前真实 batches.md 全条目（含 3 条 `优先级: <待填>` + 1 条 `P1 ★`）→ 退出 0。
- [x] 3.2 跑测试确认失败（子命令未实现）。
- [x] 3.3 在 `issues.py` 声明 `PRIORITIES = ["P0","P1","P2","P3","P4"]`（同 buglist.py:57；一致性由 Task1.9 值相等断言守，非跨 import）。实现 `batch lint`：读 batches.md → `_split_batches_entries` 逐条 → 对每条 entry_lines 新写正则 grep `优先级:`/`计划:` 值 → **值 == `BATCH_PLACEHOLDER` 则两字段均豁免**；否则 优先级 `re.match(r"^(P\d|—)", v.strip())` 取前导 token ∈ `PRIORITIES∪{—}`、**匹配后剩余不校验**；计划非占位时校验非空白。违规非零退出 + 指明批次/字段；只读、不覆写人写行。
- [x] 3.4 `pytest sdflow-issues/tests/` 全绿。
- [x] 3.5 回到 Task1.9 补 `test_priorities_constant_consistency`（`BUG.PRIORITIES == ISS.PRIORITIES`）并重跑 `pytest sdflow-buglist/tests/` 绿。
- [x] 3.6 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p3-determ-guards:task3-batch-lint "issues.py batch lint：优先级/计划占位符豁免+前导token后缀不校验(P1★过)+声明PRIORITIES(值断言守漂移)，复用_split_batches_entries只读，fail-closed+测试"`

## 4. 收尾验证（spec 全需求交叉核）

- [x] 4.1 全量测试：`pytest sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/` 全绿。
- [x] 4.2 手验 fail-closed：故意造坏 config / 坏 batch 字段 → 跑 lint 确认非零退出（临时改、验完还原）。
- [x] 4.3 手验现存数据零假阳：对当前真实 config.yaml（有 metrics 块、无 model-tiers 活跃段）+ batches.md（含 3 条 `优先级: <待填>`、`P1 ★`、`—（已闭合）`）跑 lint → 均退出 0。**核**：model-tiers 越域 + 无 metrics 块 两分支靠构造 fixture 测（真实文件测不到），确认 Task2.1 已含。
- [x] 4.4 `openspec validate mlh-p3-determ-guards` 通过。
- [x] 4.5 确认 Task 1 归一（todolist split_sections/block_ranges）已随 checkpoint 提交、todolist 全测零回归留痕（D6 顺手修边界）。
- [x] 4.6 checkpoint（纯验证无文件改动则空提交标记）：`~/.sdflow/hack/checkpoint-commit.sh mlh-p3-determ-guards:task4-verify "收尾全量验证：pytest全绿+fail-closed手验+现存零假阳+openspec validate"`
