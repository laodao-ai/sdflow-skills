# ship-gate-hardening — 实现计划（superpowers-plan）

> 阶段三 SDD 实现。被修：`sdflow-ship/scripts/ship_gate.py` + `sdflow-ship/tests/`。
> **提交契约**：每任务完成用 `~/.sdflow/hack/checkpoint-commit.sh task<N>-<slug> "<描述>"`（gate 主锚）。
> TDD：先写红测 → 实现转绿 → 跑 `pytest sdflow-ship/tests/` → checkpoint。
> 设计源：design.md D1-D5 + 「D3 硬化 bundle」H1-H6；需求：spec Scenario〔B1/B2/B3+D3/B4〕。

### Task 1: B1 窗口闭区间 + 头注释收口（design D1 / BR-8）

- 红测 `test_gate_impl_progress.py`：plan 与 `checkpoint(task1-x)` 同 commit → task1 计入、齐 N（Scenario B1）。
- 改 `done_task_ids(root, sha)`：除 `{sha}..HEAD --no-merges` 外，追加 `git log -1 --format=%s <sha>` 按同 `startswith("checkpoint(task")`+`TAG_RE.match` 解析并入 ids（窗口闭区间 `[sha,HEAD]`）。
- BR-8：同步头注释 `:30-32` 完成判据窗口块（旧 `<sha>..HEAD --no-merges`）+ CONTINUE_IMPL reason 串 `:241`（旧 `窗口 {sha[:7]}..HEAD --no-merges`）为闭区间表述。
- 回归：plan 单独提交路径不多不少数。
- checkpoint `task1-window-closed`。

### Task 2: B4 完成判据集合归属（design D5 / 设计门 Q1）

- 红测 `test_gate_impl_progress.py`：plan=task1/task2、done={task1, 计划外 task9} → CONTINUE_IMPL 非假齐、done_tasks 不含 9（Scenario B4）。
- 新增 `plan_task_ids(plan)`：解析 `### Task <n>:` 号集（复用 `TASK_TITLE_RE`，返回 `set[str]`）。
- 改 `decide()` 完成判据：`len(done) < n` → `plan_ids - done_ids`（未齐条件 `plan_ids - done_ids != ∅`）；CONTINUE_IMPL 上报 `done_tasks = sorted(done_ids & plan_ids, key=int)`；`n` 计数保留给 UNKNOWN（plan 无标题）判定。
- 回归：`test_all_tags_present_advances`/`test_continue_impl_with_done_set`/`test_merged_branch_inner_commits_do_enter_window`（done=["9"] N=2 → CONTINUE_IMPL）绿。
- checkpoint `task2-membership`。

### Task 3: B2 精确式豁免 + 分帧遍历 + 护栏 + token 契约（design D2 / BR-6 / BR-7 / BR-5）

- 红测 `test_gate_freshness.py`：①`checkpoint(impl-review)` 与 `: 描述` 触及 design.md/tasks.md → 不失鲜；②普通 subject 触及 design.md → 失鲜；③`checkpoint(impl-review-fix)`/`impl-reviewX`/`checkpoint(impl-review)evil` → 不豁免（BR-7 精确式）；④空 subject 帧触及 design.md → 失鲜（BR-6）；⑤同窗口 impl-review 改 tasks.md + 普通 subject 改 design.md 交错 → 后者失鲜（BR-6 分帧正确）。
- 改 `is_stale(scope="design")`：`git log {sha}..HEAD --name-only --format=%x00%s` 分帧（`\x00` 起每帧首行=subject、余行=文件）遍历；豁免判据**精确式** `sub == "checkpoint(impl-review)" or sub.startswith("checkpoint(impl-review):")`。护栏：只 scope=="design" 豁免，code 域逐字不变；**MUST NOT 加 `--no-merges`/`--first-parent`**。
- BR-5：新增契约测试（`test_anchor_contract.py` 同款或新文件）把豁免 token 字面 `checkpoint(impl-review` 与 code-review 约定 step 名钉死。
- 头注释：D9 分域段加精确式豁免 + 「已知不覆盖」两条（伪造/手工 subject 绕过；经豁免语义改动静默 ship）。
- checkpoint `task3-exempt-precise`。

### Task 4: B3 归档终态 + D3 硬化 bundle H1-H6（design D3 / 设计门 Q3）

- 新建 `test_gate_terminal.py` ×10（design D4 表 B3 行 ①-⑩）：base 树+verify锚→SHIPPED；仅HEAD树→RUN_VERIFY；皆无→REFUSE不存在；active+精确同名旧档→active优先；后缀撞名→不误命中；跨分支已并→SHIPPED；空壳无verify锚→不SHIPPED（H1）；未跟踪垃圾目录→不误RUN_VERIFY（H2）；detached+已并→SHIPPED（H4）；`--change`含元字符→安全（H5）。
- 加 `run_git_rc(root,*args)`（返回 `(rc, stdout)`，H3 区分错误/空）+ `base_ref(root)`（main/master 优先，无→None）。
- 加 `list_archive_dirs(root, ref, change)`：`git ls-tree <ref> openspec/changes/archive/` 列子项，`re.escape(change)` 套 `\d{4}-\d\d-\d\d-` fullmatch（H2 纯 git 域 + H5 注入防御）。
- `decide()` git 健全性后、pre-flight 前插归档短路：`cdir` 不存在 → 求 `in_head = list_archive_dirs(HEAD)`、`in_base = list_archive_dirs(base)`；base 为 None → UNKNOWN；`in_base` 非空且其中任一目录 archived `verify-report.md` 含 verify=PASS 锚（H1 追读）→ SHIPPED；仅 `in_head` 非空 → RUN_VERIFY「归档未并 base」；皆空 → REFUSE「change 不存在（active 与 archive 均无）」。
- H1 final 路径收紧：`decide()` 尾 `archived` 谓词——active 存在时不再凭 glob 判 SHIPPED；active 存在 + verify=PASS + hand-off → RUN_VERIFY（archive+merge 待 done）。相应改 `test_gate_tail.py::test_full_pass_to_shipped`、`test_gate_freshness.py::test_uncommitted_report_is_fresh`：SHIPPED 改经 active 缺席 + base 树 + verify 锚构造。
- H4：头注释/`branch_state` detached 语义分域（D3 短路不经 branch_state，detached 仍可 SHIPPED）。
- checkpoint `task4-terminal-hardened`。

### Task 5: 契约同步 + 全量回归（tasks §5）

- 头注释契约表：SHIPPED 行（含归档后重跑+追读 verify 锚）、REFUSE_START change 不存在变体、RUN_VERIFY 归档未并变体（BR-10）、detached 分域、完成判据集合归属；「已知不覆盖」精确同名旧档一条。
- `sdflow-ship/SKILL.md` 链序段：REFUSE_START 两分支提示语一致核对；`test_skill_text.py`/`test_anchor_contract.py` 绿。
- 全量 `pytest sdflow-ship/tests/` + 仓级 `pytest` 全绿（基线不降）。
- checkpoint `task5-contract-sync`。
