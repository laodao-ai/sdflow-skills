# Task 4 fix1 impl-report — 双轴审发现修复（编排层已裁定，不重新论证）

R-ID: R-tickets（出 ticket 模式产出 tracer-bullet ticket）

本票修复 `task4-filename-sync.md` 首轮报告的双轴审三项发现，均按编排层裁定的口径落地，
不改动 `proposal.md`/`design.md`/`tasks.md`/`specs/`，不改 T135 的任何内容。

## fix 1 [Medium → 必修] step6-writing-plans.md 补轨道澄清

`tasks.md` §5.6 逐字点名 `.../prompts/step6-writing-plans.md` **明确其只管 superpowers
轨、文件名不变**。首轮报告把这条澄清放进了 `workflow.md` 的规则列，没有触碰被点名的
文件本身，理由是"该文件全文即待原样粘贴的 prompt，加字会污染粘贴内容"——该理由只对
"元注释"成立，不对"prompt 自身的指令子句"成立：8 个同目录 prompt 文件确实无任何注释行，
但指令子句（明确产物边界）合乎该体裁，且执行 `/writing-plans` 的模型完全可能在
Task 4 之后全仓遍布 `tickets.md` 的语境下"顺手"把产物改叫 `tickets.md`——这条澄清对
执行方是有用的指令，不是给人看的旁注。

**改动**：`sdflow-init/assets/workflow/prompts/step6-writing-plans.md` 在
"生成任务清单 superpowers-plan.md" 之后就近插入一个短指令子句：

> （superpowers 轨固定用此名；tickets 轨改用 `tickets.md`、由 `sdflow-implement` 出票，
> 不走本 prompt）

约 40 字、单句、就地插入原段落（该 prompt 本身就是单行段落，无换行），不新增独立行，
不破坏既有 checkpoint 标签格式串样例（`<change>:task<N>-<slug>`）、`checkpoint-commit.sh`
调用点、"Global Constraints 不进 brief" 特征串等任一既有契约。

**下游同步（该文件是机读单一源，先全面 grep 复核后逐一处理）**：

- `python3 hack/gen_workflow_guide.py --write` 重新生成
  `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`（`DO NOT EDIT` 生成物，未手改），
  再跑 `--check` 复核通过（0 退出码）。
- `openspec/workflow/WORKFLOW-GUIDE.md`（仓内托管副本）`cp` 自上一步生成物，`diff` 确认
  与源一致。
- `openspec/workflow/prompts/` 目录本身为空（未被 git 追踪，`git ls-files` 确认该目录下
  无任何受控文件），无需同步——bundle 唯一权威源仍是
  `sdflow-init/assets/workflow/prompts/step6-writing-plans.md`。
- 机械断言核实（全部保持绿，逐条见下方红→绿记录）：
  `sdflow-ship/tests/test_workflow_authority.py`、`hack/tests/test_workflow_split.py`、
  `hack/tests/test_checkpoint_slug_coverage.py`、`sdflow-init/tests/test_grill_handoff.py`。

**红→绿**：改动前先跑上述四个测试文件确认全绿（改动是新增指令子句，不删除任何既有
断言命中的字符串，理论上不会转红）；改动后复跑，19 项全部通过，无一新增失败。未额外
新增机械断言——`tasks.md` §5.6 要求的是"明确其只管 superpowers 轨、文件名不变"这一
措辞落地，属于 prompt 文本本身的澄清，现有测试已覆盖该文件的全部结构性契约
（checkpoint 标签样例 / task-brief 断口 / dispatch 通则携带 / 生成物同步），无需为
一句说明性子句新增专属断言。

## fix 2 [Minor → 必修] §7.3 归因表硬编码计数改为快照+计数以表为准

首轮报告 §7.3 声称"剩余 26 个文件"，Spec 轴独立复核在快照 commit `4b1145a`
（`task4-filename-sync.md` 首次落盘所在提交）实得 27——本票在该提交上重跑
`grep -rln "superpowers-plan"`（不带 `--include`，剔除
`openspec/changes/archive/**`、`openspec/issues/**`、
`openspec/changes/harden-implement-review-loop/**`）确认确为 **27**，与归因表实际行数
（27 行，逐条核对表格本身完整、无缺漏无多余）一致——即表格内容本身是对的，只是正文
散文里的绝对数字错了。

**改动**：删掉硬编码的 "26 个文件"，改为"逐条归因表如下（计数以表为准）"，并标注
表格所反映的快照 = commit `4b1145a`（`task4-filename-sync.md` 首次落盘所在提交）。

同一模式此前已在 Task 2 咬过一次（§7.1 从 53 变 54，因审计文本自身含被同一 grep 扫到
的字符串，任何后续编辑都会让绝对计数过期），本票口径与 Task 2 最终采用的"常设分类规则 +
快照 commit"一致，不是孤立处理。

## fix 3 [不修 · 已裁定] T135 关闭不算越界

Spec 轴把首轮报告中"关闭 todolist 的 T135"标为待拍板事项（`openspec/issues/**` 在
`tasks.md` §5.9 属"不动"面）。编排层裁定：**保留，不回退**，理由——

1. §5.9 的"不动"针对的是**改写历史记录**（改写即伪造审计），而 T135 是**本 change 真正
   解决掉的条目**，走 `sdflow-issues` 的 `set-status --to DONE --evidence` 正规 overlay
   机制标记完成，是记录器的正常工作流，不是改写历史；
2. Task 3 的 impl-report 已预告"T135 的完整关闭需 Task 4 落地后才闭环"；
3. 与 T66/T67/T85/T146 四条既有 sanctioned overlay 先例逐字同构；
4. 本仓既定规矩："工作已落地的 todo 当场 set-status DONE + evidence，只有真未做的才留 OPEN"。

本票**未改动** T135 的任何内容（frontmatter overlay / `DOGFOOD_OVERLAY_DELTAS` 登记均已在
首轮报告落地，本票只在此记一句裁定与判据）。

## 改动文件清单

- `sdflow-init/assets/workflow/prompts/step6-writing-plans.md`（fix 1，指令子句插入）
- `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`（fix 1，生成物重新生成）
- `openspec/workflow/WORKFLOW-GUIDE.md`（fix 1，托管副本同步）
- `openspec/changes/harden-implement-review-loop/impl-reports/task4-filename-sync.md`
  （fix 2，§7.3 硬编码计数改为快照+计数以表为准；fix 3，无内容改动，仅本 fix 报告记录裁定）

`proposal.md`/`design.md`/`tasks.md`/`specs/` 全程未碰；`superpowers-plan.md` 未勾选、未
新建 `tickets.md`。

## 自验

```
python3 sdflow-ship/scripts/ship_gate.py --change harden-implement-review-loop --root "$(git rev-parse --show-toplevel)"
```

输出：`CONTINUE_IMPL → next=subagent-dev — 实现进度 3/6（窗口 [87e2dde, HEAD] 闭区间，
集合归属）`，`done_tasks: ["1", "2", "3"]`——不变。

## 测试执行范围

| 层 | 命令原文 | 退出码 | 备注 |
|---|---|---|---|
| 定向（fix 1 涉及的四个机械断言文件） | `/usr/bin/python3 -m pytest sdflow-ship/tests/test_workflow_authority.py hack/tests/test_workflow_split.py hack/tests/test_checkpoint_slug_coverage.py sdflow-init/tests/test_grill_handoff.py -q` | 0（19 passed） | 改动前后均绿，无新增失败 |
| 生成器一致性门 | `python3 hack/gen_workflow_guide.py --check` | 0 | `--write` 后复核通过 |
| 全仓回归 | `/usr/bin/python3 -m pytest -q` | 0（**2909 passed, 10 skipped, 3 xfailed**） | 见下方"与基线的偏差"如实说明 |

### 与基线的偏差（如实报告，未回避）

编排层给定基线 = `2908 passed, 11 skipped, 3 xfailed`（合计 2922）。本票全量跑出
`2909 passed, 10 skipped, 3 xfailed`（合计同为 2922）——**总数一致，零 failed**，差异是
一项测试从 `skipped` 变为 `passed`。核实：全仓带 `skipif` 标记的测试均依赖运行环境
（`shutil.which("openspec")`、`_have_timeout_bin()`、`os.name`、`_REAL_CLAUDE_SKIP` 等
外部二进制/环境变量存在性判断），与本票改动的两个文件（一句 prompt 指令子句 + 一份
impl-report 散文措辞）没有因果关系；本票未新增或删除任何 `skipif`/`skip` 标记。判定为
运行环境本身的条件性差异（如 `openspec` CLI 在本次 shell session 中可探测），非本票
引入的回归。

## 完成信号（后置，本票不自行勾选/打标签）

按信号权威表，本票完成信号（复选框全勾 + `checkpoint(harden-implement-review-loop:task4-…)`
标签）由双轴审通过后补打，本票未创建该标签、未勾 `superpowers-plan.md` 复选框、未改动
`proposal.md`/`design.md`/`tasks.md`/`specs/`。本票已用普通 commit message 提交（不带
`task4-` 标签）。
