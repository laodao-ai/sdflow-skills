# spec-workflow Specification (delta)

> 本 delta 把 `openspec/workflow/` 端到端流程的**规范性行为**固化为可验证 Requirement。
> 详细设计与决策追溯见 change 的 design.md（G/P/I/C 系列）。
> **〔Phase A 范围〕本 delta 仅含 Phase A 的 9 条 Requirement**（连续化 + 提交自动化 + bundle 权威源）。
> Phase B（债务池 issues 结构 / 批次注册表）与 Phase C（跨模型 outside voice / HR-TG 判定）的 Requirement
> 已随 § 移出本 change，见 [../../ROADMAP.md](../../ROADMAP.md)「Phase B/C 待迁」，待各自 change 开工时并入其 spec delta。

## ADDED Requirements

### Requirement: 评审独立性由 fresh 子代理提供，不依赖会话重置

工作流 SHALL 通过 fresh-context 子代理 dispatch 获得评审独立性，MUST NOT 依赖 `/clear` 会话重置来隔离评审上下文，从而使评审阶段可连续自动运行。

#### Scenario: 设计评审无需先 /clear
- **WHEN** spec-review 编排器在生成/grill 上下文之后运行
- **THEN** 它以 fresh 子代理 fan-out 领域镜/对抗镜/接地镜，主 session 无需先 `/clear`

#### Scenario: 代码评审无需先 /clear
- **WHEN** impl-review 编排器在 subagent-dev 实现之后运行
- **THEN** 它以 fresh 子代理 fan-out 各镜，主 session 无需先 `/clear`

### Requirement: 评审决策登记进报告，不中途打断

评审编排器 SHALL 把决策点（自动决策与需人拍板）连同选项、推荐、各分支后果登记进评审报告，MUST NOT 在评审中途以 `AskUserQuestion` 打断，使一遍评审能自主跑到完成。

#### Scenario: spec-review 遇到 ≥2 合理方案
- **WHEN** 某评审镜发现一个有 ≥2 合理方案或核验不了的事实的决策点
- **THEN** 编排器把它写入 spec-review-report.md 决策登记区并继续，不中途弹 AskUserQuestion

### Requirement: 阶段二产出单一合并报告

阶段二 SHALL 由 `spec-review` 编排器串起 autoplan 与 spec-review 并产出**单一** `spec-review-report.md`，MUST NOT 要求人工手动合并多份报告。

#### Scenario: 阶段二收尾
- **WHEN** autoplan 与 spec-review 镜均完成
- **THEN** 编排器输出一份已去重合并、含决策登记区的 spec-review-report.md，供设计 HARD-GATE 人工一次性评审

### Requirement: impl-review 为每次全跑的独立强制主审

阶段三的 `impl-review` MUST 每次全跑、以独立冷视角作为强制代码评审主审（依据实测能抓真问题），SHALL NOT 因 subagent-dev 内部已评审而降级为高风险才跑的残差抽查。

#### Scenario: 普通变更也跑 impl-review
- **WHEN** 一个非高风险变更完成实现
- **THEN** impl-review 编排器仍全跑（领域镜+对抗镜+历史镜+置信过滤+scope-drift），产出 code-review-report.md

### Requirement: 阶段三过设计门后连续自动跑到 merge

阶段三 SHALL 在阶段二设计门之后无任何阻塞人类门地连续运行 `writing-plans → subagent-dev → impl-review → opsx-done`；能修的自动修，修不了或需拍板的 MUST 进 buglist/todolist 延后并由 hand-off 引导另开 change 清理。

#### Scenario: 修不了的问题延后而非阻塞
- **WHEN** impl-review 发现一个本 change 修不掉的问题
- **THEN** 它进 buglist/todolist(defer) 并写入 hand-off，流程继续跑到 opsx-done，不设人类门阻塞

### Requirement: verify 为收尾最终门，位于所有修复之后

`opsx-done` 的 verify MUST 在本 change 全部修复之后运行作为最终完整性门，SHALL NOT 前移进 impl-review（否则修复后 verify 结果 stale）；verify 判 ✅ 的每条需求 MUST 附一个可机验证据锚点（测试名/commit/文件:行），无锚点的 ✅ MUST 降级为 gap。

#### Scenario: 修复后才 verify
- **WHEN** impl-review 及其修复循环全部完成
- **THEN** opsx-done 先跑 verify（产 verify-report.md）再 archive

#### Scenario: 无证据锚点的 ✅ 降级为 gap
- **WHEN** verify 核对某条需求但找不到测试名/commit/文件:行等机验锚点
- **THEN** 该需求判为 gap（不得凭复选框或报告措辞判 ✅）

### Requirement: hand-off 交接产物替代人工核对清单

`opsx-done` SHALL 在 verify 之后、archive 之前产出 `hand-off.md`（done/not-done + 延后项 + 下阶段建议）随归档留档，作为人类异步再入口与下个 cleanup change 的输入种子；MUST NOT 保留旧的人工核对清单 `code-review-verify.md`。

#### Scenario: 收尾产出 hand-off
- **WHEN** verify 通过
- **THEN** opsx-done 生成 hand-off.md 并纳入归档

### Requirement: 每步提交由显式收尾动作驱动，不用 hook

工作流的 checkpoint 提交 MUST 由显式收尾动作（step prompt 追加指令 / 编排 skill 内置步）经共享脚本驱动，SHALL NOT 用 hook 驱动提交本身（hook 看不见逻辑步骤边界）；grill 多轮中途 MUST NOT 提交，仅收敛后一次。

#### Scenario: grill 收敛后才提交
- **WHEN** grill 多轮对话进行中
- **THEN** 不产生 checkpoint 提交；仅在 grill 收敛后一次性提交 design/ADR 更新

### Requirement: workflow bundle 改在权威源、经部署下发

workflow bundle（workflow.md / trigger-catalog.md / quality-layering.md / review UI / hooks / checkpoint 脚本）与自制 skill 的改动 MUST 在权威源（laodao-skills 的 `opsx-project-init/assets/` 与 skill 目录）进行；消费仓的 `openspec/workflow/` 等 SHALL 经 `opsx-project-init update` 重拉刷新，MUST NOT 只改消费仓副本。

#### Scenario: 修改 workflow 规则
- **WHEN** 需要修改 workflow.md
- **THEN** 改 laodao-skills 权威源 `assets/workflow/workflow.md`，消费仓走 `update` 采纳，不直接编辑消费仓的部署副本
