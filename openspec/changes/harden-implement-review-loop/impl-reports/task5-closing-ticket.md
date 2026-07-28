# Task 5 impl-report：每票测试范围分层 + 强制「实现验证」收尾票 + gate 第四道校验

范围：`tasks.md` §4（4.1–4.10）+ §6.1 + §7.6。设计意图（proposal/design/tasks/specs）未改动，
仅实现 SKILL.md 指令文本 + `ship_gate.py` 脚本 + 测试 + `adr/0032`。

## 交付清单

| 项 | 文件 | 说明 |
|---|---|---|
| 4.1 测试范围契约改写 | `sdflow-implement/SKILL.md`「每 ticket 派 fresh implementer」节 | "结束前跑一次全套件" → "单元 + 本票 e2e（若有）+ Blocked-by 链上集成"，MUST NOT 跑无依赖集成/e2e |
| 4.2 e2e 场景定义 | 同上「产出：3–6 张 tracer-bullet 垂直切片」节 | 验收标准复选框标 `[e2e]` 即该票 e2e 场景；未标即无 e2e |
| 4.3 收尾票规则 | 同上新增「强制「实现验证」收尾 ticket」节 | Blocked-by 全部功能票号、不计 3–6 预算、`R-ID: all` |
| 4.4 聚合套件发现契约 | 同上「聚合套件发现契约」子节 | 命令来源优先级 / 真跑一遍 / 缺层不罢工（五条逐字落地） |
| 4.5 证据 schema | 同上（4.4 子节内） | `<层>\|<命令原文>\|<退出码>\|<SHA>`，未覆盖层写 `<层>\|—\|未覆盖\|<依据>` |
| 4.6 四类失败分诊 | 同上（4.4 子节内） | 回归/既有红测/flaky/环境故障 四类处置 |
| 4.7 执行契约差异 | 同上「收尾票与普通票的三处执行契约差异」子节 | 豁免 red-before-green / 证据锚不依赖 commit / Standards 轴扩至"加 skip" |
| 4.8 verify 引用规则 | `sdflow-done/SKILL.md`「第一步：Verify」步骤 4（新插入，原 4/5/6 顺延为 5/6/7） | tickets 轨找收尾票 impl-report；superpowers 轨判「不适用」非 gap |
| 4.9 gate 第四道校验 | `sdflow-ship/scripts/ship_gate.py`：新增 `CLOSING_TICKET_R_ID` / `_R_ID_RE` / `_plan_task_r_ids` / `_load_parse_blocked_by` / `plan_closing_ticket_check`，接入 `decide()`（`plan_was_renamed` 检查之后、`plan_first_sha` 之前） | 仅 `tickets.md` 生效；`superpowers-plan.md` grandfather 并把提示串带入后续 emit reason |
| 4.10 测试 | `sdflow-ship/tests/test_gate_closing_ticket.py`（新增，10 用例） | 绿/删收尾票红/Blocked-by 漏号红/grandfather 不红/收尾票不唯一红 + 4 条单元层直调 |
| 6.1 ADR | `openspec/adr/0032-closing-ticket-aggregate-regression-checkpoint.md`（新增） | 含被砍候选（verify 主动执行 / 移到 code-review 之后）+ 接受的残余风险 |
| 7.6 superpowers 轨回归 | `sdflow-ship/tests/test_superpowers_track_regression.py`（新增，4 用例） | fixture 仓 `config.yaml: impl-pipeline: superpowers`，MUST NOT 碰本仓真实 config.yaml |

## 关键实现决策

- **Blocked-by 拓扑解析复用单一源**：`ship_gate.py` 惰性（函数内）sibling-import
  `sdflow-implement/scripts/impl_route.py::parse_blocked_by`，镜像该文件反向 import
  `ship_gate.FenceTracker` 的既有手法。惰性是关键——`decide()` 运行期本模块已执行完毕，
  此时 import `impl_route`（它又会 sibling-import 本模块）不构成循环导入；若放模块顶层
  则会触发真循环导入（`impl_route.py` 顶层已经在 import `ship_gate`）。
- **R-ID 提取新写一个 fence-aware 单遍扫描**（`_plan_task_r_ids`，与 `_parse_plan` 同构：同一
  份 `FenceTracker` + `TASK_TITLE_RE`）——基准 5 判据是"这是不是通用 Markdown 解析器"，本函数
  只认一个字面槽位（`R-ID:` 行），有界、不手搓。
- **收尾票判据 = `R-ID: all` 字面量**（不是猜标题措辞），与 brief 指令一致；`Blocked-by` 覆盖
  判据 = 收尾票的 `Blocked-by` 集合 ⊇ `plan_ids - {closing_id}`。
- **grandfather 提示串通过 `plan_note` 变量线程进后续 emit reason**（`CONTINUE_IMPL` /
  `RUN_CODE_REVIEW` / 双通道不可判三处），非独立 emit——仿照既有 `sop_note` 模式。

## 测试基线回归（关键：修了 3 处既有 fixture）

`ship_gate` 第四道校验对**任何**文件名为 `tickets.md` 的 plan 生效，而 Task 3 遗留的部分测试
fixture（`PLAN2` 落新名场景）没有 `Blocked-by`/`R-ID` 声明，会被新校验拦成 `UNKNOWN`。按目标态
（tickets.md 一律受四道校验约束）修正三处：

- `sdflow-ship/tests/test_gate_impl_progress.py`：新增 `PLAN2_TICKETS` 常量（Task 2 兼作合法
  收尾票）；`test_plan_task1_same_commit_counts` 改用它；`test_uncommitted_plan_no_checkbox_unknown`
  的内联 plan 补上合法收尾票，使其仍然测到"双通道不可判"这条本该测的路径，而非在第四道先被拦下。
- `sdflow-ship/tests/test_plan_resolver.py`：两条 `_approved_change_with_new_name` 用例改用
  `PLAN2_TICKETS`。
- `test_inflight_plan_rename_rejected_as_unknown`（同文件）**未改**——本次把第四道校验放在
  `plan_was_renamed` 检查**之后**，故改名违规仍先于收尾票校验被拦下，原用例不受影响。

## 全量测试

`/usr/bin/python3 -m pytest`：**2921 passed, 1 failed, 11 skipped, 3 xfailed**（本任务新增 14
个测试用例，全部通过）。

**1 个 FAILED 为本任务之前已存在的问题，与 Task 5 无关**（已用 `git stash` 核实：在
`70aaf28`（Task 4 的 checkpoint 提交，本票工作开始前的 HEAD）上单独跑
`sdflow-issues/tests/test_downstream_reference_guard.py` 同样红）：

```
FAILED sdflow-issues/tests/test_downstream_reference_guard.py::test_no_legacy_skill_references_outside_allowlist
  openspec/changes/harden-implement-review-loop/impl-reports/task4-review-package.diff: sdflow-buglist
  openspec/changes/harden-implement-review-loop/impl-reports/task4-review-package.diff: sdflow-todolist
```

原因：Task 4 自己的 review-package diff 快照文件（`task4-review-package.diff`）里内嵌了一段旧
skill 名字面量（大概率是被审查的 diff 原文本身引用了旧名，快照原样收录）。该文件是 Task 4 的
工作产物/审计留痕，不在本票 §4/§6.1/§7.6 范围内，按信号权威表本票 MUST NOT 改动其他票的产物；
如实记录，留待后续（code-review 冷层或人工）处理，不在本报告里静默修掉。

## gate 自验（brief 指定命令）

```
python3 sdflow-ship/scripts/ship_gate.py --change harden-implement-review-loop --root "$(git rev-parse --show-toplevel)"
```

输出：`CONTINUE_IMPL`，`done_tasks=["1","2","3","4"]`，reason 含
"在途 plan 未含收尾票校验（grandfathered：文件名 'superpowers-plan.md' 非 tickets.md 新名...）"——
本 change 自己的 `superpowers-plan.md` 正确走 grandfather 分支，未被新校验误伤，也未被改名。

## 未做 / 遗留

- `sdflow-done/SKILL.md` 里新增的 verify 步骤 4（superpowers 轨判「不适用」）是**指令文本**，
  该 skill 无 `scripts/`、无自身 pytest 套件（CLAUDE.md 列明"带脚本+测试的 skill"清单不含
  `sdflow-done`）——对应的"可执行 e2e"部分（gate 侧不误伤）已在
  `test_superpowers_track_regression.py` 覆盖；verify 提示文案本身的正确性只能人工/未来实跑
  `sdflow-done` 核验，非本票可机械验证的残余。
- 上述预先存在的 `test_downstream_reference_guard` 失败未修复（超出本票范围，见上）。
