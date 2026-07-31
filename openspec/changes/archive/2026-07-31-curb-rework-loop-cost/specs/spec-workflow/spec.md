## ADDED Requirements

### Requirement: sdflow-code-review 自动修复后的复审边界与硬上限

`sdflow-code-review` 的 Step4 自动修复**改的正是被审的源码盘面**，而报告 `reviewed_sha` 锚的是修复后的盘面——**那份修复本身未经任何镜审查**。该缺口 SHALL 由一轮受限复审闭合，且该复审 SHALL 有硬上限。

- **自动修复发生后 SHALL 复审一轮**：范围 SHALL 限定为**本轮修复 diff**，MUST NOT 重审全量分支 diff。
- **硬上限 = 1 轮**〔adr/0035〕：该轮复审若仍报出 Critical/Important，**SHALL NOT 自发进入第三轮**——全部 defer 进 buglist，并在 `code-review-report.md` 显式标注「复审上限已达，N 项残差已 defer」。
- **无自动修复时不触发本复审**（无源码改动 ⇒ 锚取当前 HEAD 即被审基线，本就自洽）。
- 残差的兜底责任在 `sdflow-done` 的 verify（位于所有修复之后）与 issues 池的异步再入口，**MUST NOT** 靠延长本循环来兜。

**表述一致性 SHALL 被维持**：`sdflow-implement` 与 `sdflow-code-review` 两侧关于「code-review 是否存在 fix 循环」的描述 SHALL 一致——本需求确立的形态是「**存在，且硬上限 1 轮**」。任一侧 MUST NOT 出现「无 re-review 闭环」这类与之相反的表述。

**诚实边界**：本需求是**指令层约束**，由编排器自报遵守；`ship_gate` 不为复审轮数新增机械门。MUST NOT 将其表述为机械保证。

#### Scenario: 自动修复后复审一轮且只审修复 diff

- **WHEN** Step4 产生了自动修复并完成「仅源码」的 checkpoint 提交
- **THEN** SHALL 派一轮复审，其输入 diff 范围为该修复提交本身，MUST NOT 重新打包整个分支 diff

#### Scenario: 复审仍有 Important 时 defer 而非再审

- **WHEN** 复审轮报出 2 条 Important
- **THEN** 该 2 条 SHALL defer 进 buglist，`code-review-report.md` 标注「复审上限已达，2 项残差已 defer」；MUST NOT 派第三轮复审或再次自动修复

#### Scenario: 无自动修复时不触发复审

- **WHEN** 某次 code-review 的 Step4 无任何可自动修复项
- **THEN** SHALL NOT 触发本复审轮，报告 `reviewed_sha` 取被审基线 HEAD

#### Scenario: 两侧表述不得相反

- **WHEN** 有人在 `sdflow-code-review/SKILL.md` 写下「无 re-review 紧闭环」而 `sdflow-implement/SKILL.md` 同时称其有「fix 循环」
- **THEN** 该状态 SHALL 判为违反本需求——两侧 SHALL 统一表述为「存在复审循环，硬上限 1 轮」
