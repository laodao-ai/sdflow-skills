# Task 3: 代码审复审边界与文档分叉消除 — 实现报告

## 范围

在 `sdflow-code-review/SKILL.md` 落地 R-ID SW-1（自动修复后的复审边界与硬上限）三项改动，并核验
全仓无「无 re-review 紧闭环」类相反表述残存。无脚本、无数据迁移，纯 prose 契约编辑，符合 Global
Constraints「本 change 全部交付物是 SKILL.md prose，无脚本」。

## 逐项落地位置与内容

### 1. 新增复审边界规定（`sdflow-code-review/SKILL.md` 第四步「自动修 / 自动裁 / defer」，约
   293-307 行）

在「绝不 AskUserQuestion」之后、「裁决计数」之前插入新条目「自动修复后的复审边界（硬上限 1 轮）」
〔curb-rework-loop-cost · adr/0035〕，对齐 spec SW-1 的四个 Scenario：

- **有自动修复 ⇒ MUST 复审一轮**，范围限定为本轮修复 diff（Step5 第 3 步「仅源码」checkpoint 提交
  本身），MUST NOT 重新打包整个分支 diff 重审。
- **硬上限 = 1 轮**：该轮复审若仍报出 Critical/Important，MUST NOT 自发进入第三轮——全部 defer 进
  buglist，并在 `code-review-report.md` 显式标注「复审上限已达，N 项残差已 defer」；残差兜底责任
  交 `sdflow-done` verify 与 issues 池异步再入口，MUST NOT 靠延长本循环来兜。
- **无自动修复时不触发本复审**（无源码改动 ⇒ 锚取当前 HEAD 即被审基线，本就自洽）。
- **两侧表述统一**声明：本 skill 与 `sdflow-implement` 关于「code-review 是否存在 fix 循环」的描述
  SHALL 一致，统一为「存在复审循环，硬上限 1 轮」，MUST NOT 出现「无 re-review 闭环」类相反表述。
- **诚实边界**：指令层约束，编排器自报遵守；`ship_gate` 不为复审轮数新增机械门，MUST NOT 表述为
  机械保证（对齐 spec「诚实边界」段，MUST NOT 声称 ⑤⑥ 是机械保证）。

同时把该复审动作嵌入第五步「产出 + 收敛口」的执行顺序编号列表：原列表 1–7 步在「checkpoint 提交
（第一段，仅源码）」（第 3 步）之后插入新第 4 步「复审一轮（硬上限 1，仅当上一步产生了修复提交时
触发）」，原第 4–7 步顺延为第 5–8 步（取锚 / 写报告 / checkpoint 第二段 / 收敛口）。核对了列表内
既有的「第 3 步」「下一步」等交叉引用——均只指向未变号的第 3 步或相对位置，唯一涉及顺延项自身编号
的引用（新第 4 步内提到"下一步的报告"）已改写为显式「第 6 步」+「Step4」以消除与局部编号"第四步"
的歧义。

### 2. 对比表右列措辞对齐（`sdflow-code-review/SKILL.md` 约 181 行，「与注入点 B 的关系」ASCII 表）

原「机制」行右列「出报告 → 编排器修（无 re-review 紧闭环）」改为「出报告 → 编排器修 → 存在复审
循环，硬上限 1 轮（只审修复 diff）」——与新增规定第 1 项、以及 `sdflow-implement/SKILL.md`
（约 372/376 行既有措辞「`sdflow-code-review` 及其自动修复循环」「fix 循环」）三处统一。

`sdflow-implement/SKILL.md` 一侧未发现与「code-review 无 fix 循环」相反的表述——其现有措辞本就
断言 code-review「有」自动修复/fix 循环，无需改动；proposal.md 中引用的旧行号 `:349,353` 因 Task 2
先落地导致行号漂移，已用全文搜索重新定位到当前 `:372,376` 附近的等价措辞并核对语义一致。

顺带同步了衍生文档 `docs/workflow-skills/sdflow-code-review.md`（架构展开文档，直接镜像本 SKILL.md
该对比表的 mermaid 版本）：原 `S1["...出报告 → 编排器修（无紧闭环）"]` 与新规定矛盾，已同步改写为
「出报告 → 编排器修 → 存在复审循环，硬上限 1 轮」，避免同一事实在两份维护中的文档里各执一词。

### 3. 全仓 grep 核验（无脚本改动，纯核验）

`grep -rn "无 re-review|紧闭环"` 全仓扫描，结果分两类：

- **活文档（当前系统行为描述）**：仅 `sdflow-code-review/SKILL.md` 命中——且唯一命中行正是本次
  新增的「MUST NOT 出现『无 re-review 闭环』」禁用声明本身（引用被禁短语，非断言）。`docs/workflow-
  skills/sdflow-code-review.md` 已按上条同步修正，扫描后确认无残留。
- **change 自身工件（问题陈述/决策留痕）**：`proposal.md`、`design.md`、`decision-memo.md`、
  `tasks.md`、`tickets.md`、`spec-review-report.md`、`specs/spec-workflow/spec.md`、
  `adr/0035-*.md`，以及归档变更 `archive/2026-07-02-streamline-workflow-automation/design.md`——
  这些文件引用旧短语是在**陈述本 change 要修复的问题本身**（proposal 的动机段、ADR 的决策依据、
  spec 的反例 Scenario）或**历史归档快照**，按 DOC-1／premise-verification 规则不应重写：它们记录
  的是"曾经的错误表述"，不是当前系统行为的断言。未改动。

## 未改动范围确认

- 未触碰 `proposal.md` / `design.md` / `specs/` / `tasks.md` / `tickets.md`（未勾框、未打完成标签）。
- 未触碰 `sdflow-implement/SKILL.md`（核验后确认其既有措辞已与目标态一致，无需改动）。
- 未引入任何 Python 脚本或解析器。

## 证据

```
git diff --stat sdflow-code-review/SKILL.md docs/workflow-skills/sdflow-code-review.md
 docs/workflow-skills/sdflow-code-review.md |  2 +-
 sdflow-code-review/SKILL.md                | 37 ++++++++++++++++++-----
 2 files changed, 35 insertions(+), 14 deletions(-)
```

`git diff` 已核验实际改动（对比表措辞 + 新增复审边界条款 + 第五步编号列表插入并顺延 + 衍生文档
同步）与本报告描述一致。全仓 grep 结果已在上文第 3 项如实列出，含"为何不改"的判据。
