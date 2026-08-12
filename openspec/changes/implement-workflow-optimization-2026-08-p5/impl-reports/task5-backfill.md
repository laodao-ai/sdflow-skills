# Task 5 实现报告：收尾回填（roadmap + issues + hand-off）

## 状态

DONE

## 范围（对照 tickets.md Task 5）

- roadmap 阶段 5 回填：5.3 措辞按 memo D4 修正、5.2 过时措辞修正（Step3→Step4）、子任务勾选、
  验收标准状态更新。
- issues set-status：T275→DONE、T101→DONE；T256 确认仍 OPEN 且调研段在册。
- hand-off 注记：拍板三问首个真实 dogfood 挂下一次设计审。

## 1. roadmap 阶段 5 回填

文件：`openspec/roadmaps/workflow-optimization-2026-08/roadmap.md`
（该 roadmap 实为归档前的 `workflow-cost-optimization` 更名后的现行文件——
`openspec/roadmaps/workflow-cost-optimization/` 已整体归档到 `archive/`，本仓当前活跃 roadmap
目录是 `workflow-optimization-2026-08/`，brief 中的旧路径已核实为过期路径，改在正确的现行文件
上操作）。

- **5.2 过时措辞修正**：`spec-review SKILL Step3 报告模版` → `Step4`。核实依据：
  `sdflow-spec-review/SKILL.md` 现行步骤划分为「第三步：机械引用核 + 综合裁决」「第四步：产出」，
  拍板三问小节与 `sdflow:gate-questions` 锚行落在**第四步「产出」**（`SKILL.md:352-364`「报告
  决策登记区格式」），旧措辞「Step3」是过时残留，已改为 Step4；Task 1
  （`impl-reports/task1-anchor-lint.md:141`）也独立佐证「锚是否落在 Step4」是 Task 3 范围。
- **5.3 措辞按 memo D4 修正**：原「T256 评估收口……按五问收敛为「做 / 明确不做并记因」」
  改写为「T256 调研记录 + 保持 OPEN」，正文重写为实际收敛结果（人 2026-08-12 拍板：不能只以
  当前 repo 状态判断，先调研先记录、本 change 不实现），并注明该结论已追加进
  `openspec/issues/open/todo/T256.md`。同时同步了「验收标准」与「交付物」两节里与此矛盾的
  「T256 三条 issue 全部到达终态」「T256 评估结论（闭环关闭）」旧措辞（均与 D4 拍板的
  「T256 保持 OPEN」直接冲突，一并修正，非 brief 未点名但属同一措辞面的必要一致性维护）。
- **子任务勾选**：5.1（T275）、5.2（T101）、5.3（T256）三项标记完成，并各附一句证据锚；
  5.4（实现验证收尾）保持未勾选——它是 Task 6 的范围，不属本票。同时补勾了「前置条件」里
  遗留的 1.A.2（考古层修订锚保留界线人工拍板，已由 decision-memo D1 拍板 + Task 4 执行）。
- **验收标准状态**：审计留档条、issue 终态条已勾选（T256 特别注明"保持 OPEN 即该条的正确
  最终状态，非未完成"，避免与「全部到达终态」字面产生新的矛盾）；拍板三问 dogfood 条、
  全仓 pytest 条、change 归档条**保持未勾选**（分别待下一次真实设计审、Task 6、Task 6 之后
  的归档流程），前者显式指回本次新写的 `hand-off-notes.md`。
- **顺带修正数字错误**（面治，非 brief 字面要求但同一措辞面）：roadmap 阶段 5 全文原写
  「14 个 SKILL.md」，实测（`audit/skill-doc1-audit.md` 标题 + Task 4 ticket 原文「7+8=15」）
  为 **15 个**，三处（5.1 子任务、验收标准、交付物）一并订正为 15；阶段 1 历史记录段
  （`roadmap.md:68`，2026-08-10 已完成条目，写「7/14」）保留不动——那是入池时点的估计值，
  按 DOC-1「正文即最终态、演进史进附录」的历史记录不倒改原则，不属本次回填范围。
- **附录 B 子任务总数表**：阶段 5 行由「已细化 2026-08-12，待执行」更新为
  「5.1–5.3 完成 2026-08-12……5.4 待 Task 6 验证收尾」，反映实际进度。

## 2. issues set-status

**brief 给出的命令语法与实际 CLI 不符**（`--status`/`--change` 均非法参数）——先跑
`issues_v2.py set-status --help` 核实真实签名为 `--id / --to / --evidence / --reason`，且无
`--change` 选项：`resolved_by`（记录关联 change）由脚本内 `detect_change(root)` 自动探测
（优先取 `openspec/changes/` 下唯一未归档目录，当前仓正是
`implement-workflow-optimization-2026-08-p5` 单目录，能正确自动探测，无需显式传参）。按修正后
语法执行：

```
python3 ~/.claude/skills/sdflow-issues/scripts/issues_v2.py --root . set-status --id T275 --to DONE --evidence "audit/skill-doc1-audit.md + 15 SKILL 逐文件清理"
→ {"id": "T275", "pool": "todo", "old": "OPEN", "new": "DONE", "file": "openspec/issues/closed/todo/T275.md"}

python3 ~/.claude/skills/sdflow-issues/scripts/issues_v2.py --root . set-status --id T101 --to DONE --evidence "anchor_lint gate-questions check + spec-review 报告三问模版"
→ {"id": "T101", "pool": "todo", "old": "PROPOSED", "new": "DONE", "file": "openspec/issues/closed/todo/T101.md"}
```

两条均终态化（自动 `git mv` 到 `closed/todo/`），`resolved_by` 由 `detect_change` 自动填为
`implement-workflow-optimization-2026-08-p5`。

**T256 核实**：`openspec/issues/open/todo/T256.md` frontmatter `status: "OPEN"` 未变；正文含
「2026-08-12 调研记录」段（本 change 相位 B 拷问期间写入，双宿主 PreCompact 机械落点核实 +
未来方向推荐），符合 brief 要求「确认仍 OPEN 且调研段在册」，本票未对该文件做任何写操作
（不改状态、不改正文）。

`reindex` 已跑一遍刷新 `INDEX.md`/`CLOSED.md`（open 72 项，closed 234 项）。

## 3. hand-off 注记

新建 `openspec/changes/implement-workflow-optimization-2026-08-p5/hand-off-notes.md`：记录
「拍板三问首个真实 dogfood」的时序注记——本 change 自身的 `spec-review-report.md` 产出于
Task 1/3（拍板三问锚 + Step4 报告模版）落地**之前**，用的是旧版 `sdflow-spec-review/SKILL.md`，
结构性无法自证；proposal.md Success Metrics 已预先记录此注记（`proposal.md:63-66`），本文件是
该注记在 change 收尾时的正式挂起，明确首个真实验证点 = 本 change 归档后任意下一个 change 的
`/sdflow-spec-review` 首次产出报告，并给出验证方式（报告应含三问小节 + `sdflow:gate-questions`
锚行，`anchor_lint --layer spec-review` 应 CLEAN）。同时说明 roadmap 阶段 5 验收标准第 3 条
保持未勾选是刻意的，非遗漏。

## 遗留说明（诚实边界，非本票缺陷）

- 5.4（实现验证收尾）与验收标准里的「全仓 pytest 绿」「change 归档」三条均保持未勾选——
  这些是 Task 6 的范围，本票（Task 5）按 tickets.md 定义不含验证收尾。
- 拍板三问的下一次设计审首次验证结果**不会**回填本报告或 hand-off-notes.md——按设计，那是
  未来某个不确定 change 的自然产物，不是本 change 的待办。

## 改动文件清单

- `openspec/roadmaps/workflow-optimization-2026-08/roadmap.md`（阶段 5 节措辞/勾选/验收标准/
  附录 B 更新）
- `openspec/issues/open/todo/T275.md` → `openspec/issues/closed/todo/T275.md`（git mv，脚本执行）
- `openspec/issues/open/todo/T101.md` → `openspec/issues/closed/todo/T101.md`（git mv，脚本执行）
- `openspec/issues/INDEX.md`、`openspec/issues/CLOSED.md`（reindex 再生）
- `openspec/changes/implement-workflow-optimization-2026-08-p5/hand-off-notes.md`（新建）

> 注：`tickets.md` 的验收复选框本身不由本 report 勾选（信号权威表：双轴审通过后由执行模式补打）。
