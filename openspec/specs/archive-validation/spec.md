# archive-validation Specification

## Purpose
归档 change 的任务清单记录诚实性与结构合法性：归档即历史，其 `tasks.md` 必须如实反映「真实做了什么」；全量归档面通过 `openspec validate --archived`，并由 CI 机械守防回潮。

## Requirements

### Requirement: 归档 tasks.md MUST 如实反映完成状态

归档 change 的 `tasks.md` 复选框 MUST 与真实执行史一致：已真实完成（有实现 commit / run 锚可循）的任务勾 `- [x]`；确未执行的任务 MUST NOT 为通过校验而补勾。未落地即被 supersede 的 change，其 `tasks.md` SHALL 改写为**无勾选框的作废说明段**（指明 supersede 方与「从未执行」）。tickets 管线 change 的 `tasks.md` 勾选 SHALL 按收尾对账的既有语义对照 git log 回填。

#### Scenario: 作废 change 改写为说明段后过校验

- **WHEN** 某归档 change 的任务从未执行即被后续 change supersede，其 `tasks.md` 被改写为无勾选框的作废说明段
- **THEN** `openspec validate --archived` 对该 change MUST 通过，且记录如实（读者能看出「未执行、被谁取代」）

#### Scenario: 为过门假勾被禁止

- **WHEN** 某归档 change 的任务无任何实现 commit / run 锚可循，而校验因未勾复选框失败
- **THEN** 处置 MUST NOT 是勾选该任务——正解是改写为作废说明段或留 `- [ ]` + 说明并另行处置结构问题；任何「为绿而勾」MUST 判为记录伪造

#### Scenario: 已 ship 的 tickets 管线 change 回填

- **WHEN** 某 tickets 管线 change 已实现并 ship，但其 `tasks.md` 复选框在归档时未按收尾对账回填（0/N）
- **THEN** 回填 MUST 逐条对照 git log / 实现 commit 后勾选真实完成项，确未做的保留 `- [ ]` 并补说明

### Requirement: 归档面校验 MUST 由 CI 机械守

`openspec validate --archived` SHALL 在 CI 机械门泳道对全量归档面执行，0 failed 方绿〔sweep-pool-debt DT-6：先本地收敛、后接 CI，顺序不可颠倒〕。

#### Scenario: 定点破坏必红

- **WHEN** 任一归档 change 的 `tasks.md` 引入未勾复选框（或其它使 validate 失败的结构缺陷）并推上 CI
- **THEN** CI 的归档校验步 MUST 失败，MUST NOT 静默通过

#### Scenario: 全量绿基线

- **WHEN** 归档面收敛完成后在本地或 CI 执行 `openspec validate --archived`
- **THEN** 结果 MUST 为 0 failed（全量通过），任何回潮由 CI 拦截
