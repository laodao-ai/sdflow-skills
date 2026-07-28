# Task 3 impl-report — 计划文件名共享 resolver（机械核心，双存在 fail-closed）

R-ID: R-tickets, R-stage3

## 交付内容

单一源 resolver 落地于 `sdflow-ship/scripts/ship_gate.py`（新函数 `resolve_plan_path` +
新常量 `PLAN_FILENAMES = ("tickets.md", "superpowers-plan.md")` + 新异常
`PlanNameConflict`），`sdflow-implement/scripts/impl_route.py` 经既有 sibling-import 机制
（与 `FenceTracker` 同一条路径）直接 import 同一份，**未手抄第二份候选列表**。

### 改动文件

- `sdflow-ship/scripts/ship_gate.py`
  - 新增 `PLAN_FILENAMES` / `PlanNameConflict` / `resolve_plan_path`（插入于 `tg02_hit` 之后、
    `plan_task_ids` 之前）。
  - `decide()` step 6/7 改用 `resolve_plan_path(cdir)`：命中其一 → 用之；双存在 →
    `emit("UNKNOWN", ...)` 并在 reason 里点名两个文件名 + 提示"请人工删除其一"；两者皆无 →
    `emit_windowed("RUN_PLAN", ...)`，reason 改为「计划文件缺（tickets.md /
    superpowers-plan.md 均未找到）」。
  - 模块 docstring 契约表：`RUN_PLAN` 行、`UNKNOWN` 行、"完成判据窗口"段的文件名措辞同步
    改为经 resolver 定位的表述（不再硬编码单一旧名）。
- `sdflow-implement/scripts/impl_route.py`
  - sibling-import 块新增 `resolve_plan_path` / `PlanNameConflict` / `PLAN_FILENAMES`（与
    `FenceTracker` 同一条 `sys.path` 路径、同一个 `try/except`）；导入失败时三者均置空/空
    元组，走 fail-closed（与 `FenceTracker` 缺失同一停机纪律）。
  - `_cmd_route`：把硬编码的 `plan_path = ... / "superpowers-plan.md"` 改为调用
    `_resolve_plan_path(change_dir)`；resolver 不可用 → fail-closed 打印诊断并
    `return EXIT_ROUTE_STOP`；冲突 → 捕获 `PlanNameConflict` 打印并 `return EXIT_ROUTE_STOP`；
    都不存在 → 用 `PLAN_FILENAMES[0]`（新名）拼一个不存在的占位路径，下游
    `read_plan_marker`/`_get_plan_sha` 对不存在文件的既有语义（None/"-"）不变。
  - **docstring 中指向 archive 归档文件的两处实路径未改**（`matt-workflow-integration/
    superpowers-plan.md`、`archive/2026-07-03-sdflow-ship/superpowers-plan.md`）——按брief
    与 tasks.md §5.9 要求逐字核实保留。

### 测试（新增，未改动既有测试字面量）

- `sdflow-ship/tests/test_plan_resolver.py`（新文件，14 用例）：
  - 单元层：`resolve_plan_path` 都不存在→None／仅新名／仅旧名／双存在→`PlanNameConflict`／
    目录同名不算命中。
  - gate 端到端层：仅新名 `tickets.md` 走完整 `CONTINUE_IMPL`→`RUN_CODE_REVIEW` 链路；
    都不存在时 `RUN_PLAN` 的 reason 同时提及两个文件名；双存在时 gate `UNKNOWN`(exit 6)，
    reason 同时含两个文件名与"删除其一"。
  - **§5.10 `[e2e]` 改名窗口用例**
    `test_inflight_plan_rename_resets_completion_window`：造「改名前有 task1 checkpoint、
    改名后跑 gate」的 fixture（`git mv superpowers-plan.md tickets.md` + 一次提交）——
    实测结果：resolver 正确 pickup 改名后的新文件（不会误判 UNKNOWN），但
    `plan_first_sha` 的 `--diff-filter=A` 不跟随重命名，窗口起点被推到改名 commit，
    task1 的 checkpoint 落窗口外 → `done_tasks` 不含 `"1"`。**本用例锁定的是design
    Migration Plan 已明文接受的已知残余风险**（"该完成判定被 gate 拒绝承认"），不是
    resolver 的缺陷——resolver 契约只负责按当前落盘文件名定位，不做重命名历史跟踪
    （若要修复需要 `git log --diff-filter=A -M`/`--follow` 类重命名跟随，超出 D5 的
    resolver 范围，且与"在途 plan MUST NOT 重命名"的纪律本身互斥——不做机械修复，
    只做机械证据）。
- `sdflow-implement/tests/test_impl_route.py`（新增 4 用例，既有 71 用例字面量未改动）：
  - `test_cli_route_picks_up_new_plan_name_tickets_md`：仅 `tickets.md` 存在 → CLI route
    照常识别（marker/pipeline 与旧名等价）。
  - `test_cli_route_both_plan_names_present_fails_closed`：双存在 → `EXIT_ROUTE_STOP`(6)，
    stderr 同时含两个文件名。
  - `test_cli_route_new_plan_name_plan_sha_present_when_committed`：新名下 `plan_sha` 正常
    可读。
  - `test_resolve_plan_path_single_source_used_by_route`：核验 `impl_route._resolve_plan_path`
    确实是 `ship_gate.resolve_plan_path` 同一个对象（非手抄副本）。

## 全仓一致性核验（起手第 5 步，逐条归因）

不带 `--include` 全量 `grep -rn "superpowers-plan"`，非本票改动的命中全部落在：
① `sdflow-ship/tests/*.py`、`sdflow-implement/tests/test_impl_route.py` 既有用例字面量
（旧名，backward-compat 覆盖，本票 MUST NOT 改，属 Task 4 范围外的既有资产）；
② `openspec/changes/archive/**`（历史归档，不动）；
③ `openspec/issues/{buglist,todolist}/**`（历史记录/todo 描述，不动，含 T135——该 todo
描述的"应参数化"诉求本票已实现 resolver 机制，但 T135 的完整关闭需 Task 4 的文件名全量
改名落地后才闭环，本票不越权代 Task 4 关闭）；
④ `sdflow-init/assets/workflow/**`、`docs/**`、`openspec/specs/**`、`openspec/workflow/**`——
均属 Task 4/5.6/5.8 范围（文件名措辞全量同步），本票未触碰；
⑤ `impl_route.py` 两处 docstring 归档路径引用（brief 明确禁改）；
⑥ 本 change 自身 `superpowers-plan.md`（在途 plan，禁改名，本票严格未碰）。

**本票新增的两处 `superpowers-plan` 命中**（resolver 常量与向后兼容注释里的字面量）均在
`ship_gate.py`/`impl_route.py` 内，是 resolver 契约本身的一部分（候选文件名清单），非残留。

## 自验（本票最高危红线）

```
python3 sdflow-ship/scripts/ship_gate.py --change harden-implement-review-loop --root "$(git rev-parse --show-toplevel)"
```
输出：`CONTINUE_IMPL → next=subagent-dev — 实现进度 2/6（窗口 [87e2dde, HEAD] 闭区间，集合归属）`，
`done_tasks: ["1", "2"]`。本 change 自己的在途 plan 文件名（`superpowers-plan.md`）与目录结构
全程未被本票触碰；resolver 接管后仍正确识别旧名、窗口与完成集不受影响。

## 测试执行范围（本票 `Blocked-by: none`）

单元测试 + 全量 pytest（resolver 是 gate/route 共享核心，回归面即全仓，按 Global
Constraints 执行期通用条款要求）。

- `sdflow-ship/tests/`：345 passed（331 既有 + 14 新增 `test_plan_resolver.py`）。
- `sdflow-implement/tests/test_impl_route.py`：75 passed（71 既有 + 4 新增）。
- 全仓 `pytest`：**2907 passed, 11 skipped, 3 xfailed, 0 failed**（exit 0，286.89s）——
  全仓既有测试无一因本票改动变红。

| 层 | 命令原文 | 退出码 | 测试时 HEAD |
|---|---|---|---|
| 单元(sdflow-ship) | `/usr/bin/python3 -m pytest sdflow-ship/tests/ -q` | 0（345 passed） | 9f57dfbd2353fc7ecc8064cf4a5372ab76859025（工作树，本票提交前） |
| 单元(sdflow-implement) | `/usr/bin/python3 -m pytest sdflow-implement/tests/test_impl_route.py -q` | 0（75 passed） | 同上 |
| 全仓回归 | `/usr/bin/python3 -m pytest -q` | 0（2907 passed, 11 skipped, 3 xfailed） | 同上 |

## 本票边界（未做，属 Task 4，`Blocked-by: 3`）

- 各 `SKILL.md` / bundle / `docs/` 的文件名措辞同步（tasks.md §5.4–§5.6, §5.8）。
- 既有测试里的文件名字面量批量更新（本票逐条核实：未做任何此类改动，向后兼容路径已被
  新增测试覆盖验证仍然正确）。
- `openspec/adr/0033-*.md` 的撰写（Task 4）。

## 完成信号（后置，本票不自行勾选/打标签）

按信号权威表，本票完成信号（复选框全勾 + `checkpoint(harden-implement-review-loop:task3-…)`
标签）由双轴审通过后补打，实现期未创建该标签、未勾 `superpowers-plan.md` 复选框、
未改动 `proposal.md`/`design.md`/`tasks.md`/`specs/`。
