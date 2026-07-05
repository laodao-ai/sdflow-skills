# hand-off — gate-checkpoint-hardening

> 2026-07-05。REC-1 合批：sdflow-ship / ship-gate-hardening-2 / checkpoint-tag-single-source 三批 + gate-anchor 的 T43，合一个 change 清 gate/checkpoint 硬化残项。经 grill(5 ADR) + spec-review(6 镜+codex, 1 致命修正) + code-review(6 修) 三层硬化。

## ✅ 完成了什么（verify PASS，每条附机验锚点）

- **T36 标签格式单源**：格式权威 = `ship_gate.py` TAG_RE（`:300-308` canonical-shape 注释 + slug 建议非契约 CR-3 + SR-4 checklist）；workflow.md 规则一处、SKILL 引用式；`test_workflow_authority.py:23-35` 断言改。
- **T43 锚模板裸行**：`sdflow-spec-review/SKILL.md:102` 去反引号、`sdflow-code-review/SKILL.md:149-152` pass/blocked 各配各注（SR-10）；`test_anchor_contract.py:20-30` 逐行 `strip()==anchor`（SR-6）。
- **T35 新鲜度 committed-only + merge untracked**：`ship_gate.py:64-70` committed-only 注释（无逻辑改）；`sdflow-done/SKILL.md:248-252` 机械"任何 ??→halt"（CR-4）+ `-c core.quotePath=false`（CR-6）+ gitignore 边界（CR-5）+ MUST NOT AskUserQuestion。
- **T26 熔断锚集判据 + 无状态 helper**：`ship_gate.py:250-266` `anchor_set`/`breaker_no_progress` 纯函数、不接收 HEAD/mtime、fail-safe 对称 before∨after=None→True（CR-2）；SKILL 熔断按 verdict 分治（锚集限 STEP_IN_PROGRESS，RERUN_STALE 以"仍 stale"为准，CR-1）；`test_gate_breaker.py` 4 例含 after=None。
- **T37/T38 spec 措辞**：delta `## MODIFIED Requirements`（spec.md:41）含 `<change-slug>`，归档时同步主 spec:517。
- 全仓 pytest **375 passed** 零回归；`openspec validate` 通过；6 个 task 命名空间 checkpoint 标签在位。

## ⏳ 未完成 / 延后 → 批次 `gate-checkpoint-hardening`（P3，见 issues/batches.md + INDEX.md）

- **T51**：tracked 非-openspec 改动被 sdflow-done commit 步 `git add -u` 先提交、绕过 merge 前 untracked 硬检查——需 commit 步暂存策略与 merge 卫生检查对齐（SR-2 缩简版只覆盖 untracked，tracked 一路 defer）。
- **T52**：merge untracked 精确 baseline 版（分支切出点 untracked 快照 diff），减少既有 debris 误停（当前 CR-4 机械版=任何 untracked→halt 人工 triage）。
- **接受取舍（非 defer，已登记）**：CR-ADV-1 熔断 helper 靠编排器 prose 调用、未进 gate `decide()`——持久化下沉撞"盘面即状态/gate 零副作用/ship 零跨步状态"三红线，spec-review SR-1 已裁为接受取舍；helper 从"prose 数数"降为"prose 调无状态比较"是三红线下可及的最硬。
- **决策记录**：Q1（熔断判据）/Q2（merge 机制）已在设计门由用户拍板定稿，非延后。

## ▶ 下一阶段建议

- 本 change merge 后，可关三批（sdflow-ship / ship-gate-hardening-2 / checkpoint-tag-single-source）+ gate-anchor 的 T43；余 T41/T42 留 REC-2（观测 & 人读体验）。
- 批次 `gate-checkpoint-hardening`(T51/T52) 优先级 P3——与 REC-2 或其它 sdflow-done/ship 触碰时随手带，不值单开循环（fold-vs-defer）。
- 合批路线图见 `openspec/issues/consolidation-plan.md`：REC-2（人读体验，P3）、REC-3（Toolkit 安装，P2）、G1 记录三件套、G7 init.py（sdflow-init-hardening）尚待。
