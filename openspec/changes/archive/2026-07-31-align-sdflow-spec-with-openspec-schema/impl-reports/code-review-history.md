# Code Review · History 镜

## 审查对象与基线

- change：`align-sdflow-spec-with-openspec-schema`
- 审查 HEAD：`bed0c093eac91b0e998e0d623f8011c186f00e2e`
- 仓库基线：`origin/main` 的 merge-base `bf026aa63a8dc6833029e81c9b91f2a91c76152b`
- 计划锚：`206b660`；设计门审查 SHA：`117e503ca164c632d4b7b6b3573b0c103d746881`
- 宿主：Codex；本镜为 history；本次只读，不修改业务代码或总报告。

## 结论

**BLOCKED 建议。** 发现 1 个高置信度的证据锚问题，导致当前 HEAD 尚未获得同一 SHA 的 Task 7 验证证据；另有 1 个低优先级的 diff hygiene 问题。全量 `pytest` 按用户批准不再等待，已有超时 `124` 不计为通过。

## Findings

### H1 · Task 7 验证报告没有锚定当前 HEAD

- 严重度：P1（发布证据阻断）
- 置信度：0.99
- 位置：`impl-reports/task7-implementation-verification.md:7,16-17`；`tickets.md:111-115`
- 事实：当前审查对象是 `bed0c09`，但 Task 7 报告明确把全部层级命令锚定在 `b980da1`；`bed0c09` 随后新增了该报告并修改了 Task 7 勾选状态。报告因此没有证明“当前 HEAD”的验证结果，且 tickets 的文字要求每层记录同一最终 SHA。
- 采纳：**采纳**。这是历史镜的直接职责，不是把元数据提交误判成业务代码变更；设计门与 code-review 的 reviewed SHA 语义要求证据对准被审盘面。
- 建议：在当前 HEAD 重新执行变更相关聚合/CLI 验证并把结果锚到完整 SHA；全量 pytest 继续保留退出码 `124` 的未完成记录，不得改写为绿色。无需扩大到全量等待。

### H2 · `git diff --check` 在当前变更上不干净

- 严重度：P2（质量卫生）
- 置信度：1.00
- 位置：新增 `impl-reports/task1-brief.md` 等多个报告的 EOF 空行；`openspec/workflow/reference/Token_Saving_Strategies.md:11-135` 多处尾随空格。
- 事实：`git diff --check bf026aa... HEAD` 返回非零，并列出上述新增/生成文件的问题。
- 采纳：**采纳为发布前清理项，暂不单独升级为业务阻断**。这些不改变运行逻辑，但仓库贡献指南明确要求执行 `git diff --check`，且生成 bundle 进入版本库后同样属于提交面。
- 建议：在最终提交前清理报告 EOF 多余空行和生成文档尾随空格，再重跑 `git diff --check`。

## History / scope 核对

- `origin/main` 基线到 HEAD 包含 `8ba0f10..117e503` 的 CLI 1.7.0 生成物、roadmap、阶段一产物与设计审查提交；这些提交早于本 change 的实现计划 `206b660`，但均被当前 proposal/ADR 明确引用，并直接支撑本 change 的 CLI 版本、roadmap 与 schema 决策。因此记录为**已核对、裁掉 scope-drift finding**，置信度 0.93：它们扩大了 PR diff，但没有证据表明是无关业务能力。
- 从计划 `206b660` 到当前 HEAD 的实现文件集中在 schema bundle、`sdflow-init`、`sdflow-spec`、文档、契约测试和实现证据；未发现 stores、宿主适配、roadmap P2/P3 等 proposal 明确列出的 non-goal 被实现。
- 当前 `openspec validate align-sdflow-spec-with-openspec-schema --strict --type change` 通过；`openspec status` 将该既有 change 显示为 `spec-driven`，与迁移规则“先为在途 change 保留旧 schema 绑定、再切全局 config”一致，不计为漂移。

## 验证记录

- 变更相关 Task 7 报告记录：`110 passed, 1 skipped`，退出码 0；但其证据 SHA 是 `b980da1`，因此不能替代当前 HEAD 的证据。
- 全量 pytest：不再等待；此前退出码 `124`，按用户明确批准跳过，未宣称通过。
- `openspec validate ... --strict --type change`：退出码 0。
- `git diff --check`：失败，见 H2。

## 最终建议

**BLOCKED**：先补齐 H1 的当前 HEAD 验证锚；H2 在最终提交前清理。除这两项外，历史范围、计划范围、已有 ADR/问题台账与当前变更的 scope 对齐。
