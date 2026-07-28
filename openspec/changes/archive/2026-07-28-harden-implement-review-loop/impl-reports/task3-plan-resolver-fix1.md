# Task 3 双轴审 fix1：改名 fail-closed + 单一源身份断言 + 死代码清理

状态：`DONE`

修复 `task3-plan-resolver.md` 双轴审的三条发现。不改 resolver 的对外接口
（`resolve_plan_path` / `PlanNameConflict` / `PLAN_FILENAMES` 签名与语义不变），只补
finding 1 要求的 fail-closed 行为、finding 2 要求的身份断言、finding 3 的死分支清理。

## finding 1 [Critical · Spec 轴]：改名窗口用例断言了「应被禁止的行为」→ 改为显式拒绝

**问题**：`test_inflight_plan_rename_resets_completion_window` 断言 `verdict ==
"CONTINUE_IMPL"` 且 `"1" not in done_tasks`——两个分支都不是"拒绝"，即现状实现对"在途
plan 被改名"这一被 design Migration Plan 明文禁止的场景，处置是"静默丢任务、正常放行"，
而不是"显式拒绝"。implementer 曾以"design Migration Plan 明文接受的已知残余风险"自辩，
但该文档只是文档层纪律，并未免除 tasks.md §5.10 字面更严格的测试断言要求。

**修复方向（编排层裁定，`T10-choice` ①档）**：取"显式拒绝"分支，MUST NOT 取"让 gate 透明
跟随改名"分支——后者会让 MUST NOT 重命名变得无害，等于注销规范性约束（改造设计，违通则③）。

**实现**：`sdflow-ship/scripts/ship_gate.py` 新增 `plan_was_renamed(root, plan_rel)`
（插入于 `plan_first_sha` 之后）。判据 = 比较不带 `--follow` 的 `git log --diff-filter=A`
首行 sha（同 `plan_first_sha` 口径）与带 `--follow` 的首行 sha：

- 路径从未被重命名 ⇒ 两次调用取到同一次真实创建提交，相等。
- 路径发生过重命名（`git mv` 旧名→新名）⇒ `--follow` 追溯重命名链条回到重命名前的原始
  创建提交，取到更早的 sha，不等。

两次 `git log` 调用、零解析（只取首行 sha），不演化为通用 rename 历史解析器（CLAUDE.md
基准 5）。`decide()` 在 `plan_first_sha` 之前接入：`plan_was_renamed(root, plan_rel)` 为真
⇒ `emit("UNKNOWN", ...)`，reason 提示"在途 plan 曾被重命名，完成判据窗口已失效……请改回
原文件名"。

**误报核验（自验，MUST 项）**：

1. 本 change 自己的在途 plan（`superpowers-plan.md`，从未改名）：
   `git log --diff-filter=A` 与 `git log --follow --diff-filter=A` 首行 sha 均为
   `87e2dde03362dfa2f4cbc9f76481339108bc87d1`，相等 ⇒ 不误报。跑真实
   `ship_gate.py --change harden-implement-review-loop` 确认仍 `CONTINUE_IMPL`，
   `done_tasks` 含 `1` 与 `2`。
2. 全仓扫描：`git ls-files | grep -E '(superpowers-plan|tickets)\.md$'`（42 个候选）逐个
   跑两次 `git log`：所有**从未归档**、从未 `git mv` 过的路径两者恒等；40 个不等的全部
   是 `archive/` 下**已归档**的 change（目录级归档搬迁被 git 记为 rename）。归档后的 change
   目录不再是当前活跃 `--change` 解析目标（`resolve_plan_path` 只对着当前 `cdir` 探测），
   `plan_was_renamed` 不会被喂到已归档路径，故这 40 个不等不构成误报面。
3. 新增反例用例 `test_never_renamed_plan_not_flagged`（见下）机械锁定"多次提交、从未
   `git mv` 的 plan 不应被判改名"，防止本次改动本身引入回归误报。

**测试改动（TDD：先改断言使其转红，再实现）**：`sdflow-ship/tests/test_plan_resolver.py`

- `test_inflight_plan_rename_resets_completion_window` 更名为
  `test_inflight_plan_rename_rejected_as_unknown`，docstring 与断言改为「该场景被显式拒绝」
  （`code == 6 and js["verdict"] == "UNKNOWN"` 且 reason 含"重命名"），不再断言
  `CONTINUE_IMPL`/漏数。改动前跑通该测试确认转红（`assert (0 == 6)`），实现后转绿。
- 新增 `test_never_renamed_plan_not_flagged`：正常完成 task1、无 `git mv`，断言仍
  `CONTINUE_IMPL` 且 `done_tasks` 含 `"1"`（防止本条修复反向引入"从未改名也被误判"的回归）。
- 模块 docstring 第 2c 条同步改写（原描述"锁定已知/接受的残余风险"，现描述"断言被显式拒绝"）。

## finding 2 [Important · Standards 轴]：单一源守卫是恒真锚 → 补身份断言

**问题**：`sdflow-implement/tests/test_impl_route.py::
test_resolve_plan_path_single_source_used_by_route` 注释声称核验"同一个对象、非各自手抄
的两份实现"，但断言只有 `ir._resolve_plan_path is not None` 与一次行为等价调用——若真被
换成手抄的第二份实现（行为一致但对象不同），该测试仍全绿，守不住它声称要守的东西。

**修复**：仿照同文件 `:653 assert ir._FenceTracker is sg.FenceTracker` 的身份断言范式，
补齐三处：

```python
assert ir._resolve_plan_path is sg.resolve_plan_path
assert ir._PlanNameConflict is sg.PlanNameConflict
assert ir._PLAN_FILENAMES is sg.PLAN_FILENAMES
```

**变异实测**（scratchpad 副本，未污染工作树，操作后已删除）：复制 `sdflow-implement/` +
`sdflow-ship/` 到 scratch，在副本的 `impl_route.py` sibling-import 块之后手抄一份等价的
`_resolve_plan_path` 函数与一份等价的 `_PLAN_FILENAMES` 元组字面量（同名遮蔽 import 结果，
行为完全一致——都能正确 resolve `tickets.md`）：

- **旧版行为等价断言**（`ir._resolve_plan_path(d) == d / "tickets.md"`）：单独探测，
  手写脚本验证返回值仍 `True`——**手抄副本骗过了旧断言**，证实其为恒真锚。
- **新版身份断言**：`pytest sdflow-implement/tests/test_impl_route.py::
  test_resolve_plan_path_single_source_used_by_route -q` 在变异副本上运行，第一条身份断言
  `ir._resolve_plan_path is sg.resolve_plan_path` 即失败（
  `AssertionError: assert <function _resolve_plan_path at 0x...> is <function
  resolve_plan_path at 0x...>`），测试必红。

变异副本已 `rm -rf` 清理，不留痕迹于仓库或 scratch 目录。

## finding 3 [Minor · Standards 轴]：不可达的死分支 → 去掉 `else` 兜底

`sdflow-implement/scripts/impl_route.py:470` 的
`_PLAN_FILENAMES[0] if _PLAN_FILENAMES else "tickets.md"`：走到该行时，`_resolve_plan_path
is None` 已在其前的 `if` 分支处理并 `return EXIT_ROUTE_STOP`（:456-461），即到达本行时 import
必已成功、`_PLAN_FILENAMES` 必非空——`else` 分支在当前控制流下不可达，且字面量
`"tickets.md"` 与 `PLAN_FILENAMES[0]` 重复。改为直接 `plan_path = change_dir /
_PLAN_FILENAMES[0]`，去掉不可达兜底与重复硬编码。

## 验证

- `pytest sdflow-ship/tests/test_plan_resolver.py -q` → 11 passed（含改名后新增两条：
  `test_inflight_plan_rename_rejected_as_unknown` / `test_never_renamed_plan_not_flagged`）。
- `pytest sdflow-ship/tests -q` → 342 passed。
- `pytest sdflow-implement/tests -q` → 79 passed（含 finding2 三条身份断言）。
- 全仓 `pytest -q` → 见 commit 消息/终端记录（回归面即全仓，resolver 是 gate/route 共享
  核心）。
- 自验 `python3 sdflow-ship/scripts/ship_gate.py --change harden-implement-review-loop
  --root "$(git rev-parse --show-toplevel)"` → `CONTINUE_IMPL`，
  `done_tasks: ["1", "2"]`——新增改名守卫对本 change 自己不误报。

## 未做/遗留

无。三条发现均已修复并测试覆盖；未触碰 `proposal.md` / `design.md` / `tasks.md` /
`specs/`。
