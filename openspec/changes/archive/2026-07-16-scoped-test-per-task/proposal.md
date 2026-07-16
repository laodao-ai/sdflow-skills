## Why

阶段三编排器 `sdflow-ship`（A 路径）派发 `subagent-driven-development` 时是「自动执行」**零注入测试范围**；而 workflow bundle 的 `workflow.md` 步骤 6/7 又写死了「每任务完成跑测试套件」这一**加重措辞**。二者叠加，使实现期测试范围逐任务不统一、零星出现「每任务跑全量回归」（实证：mqtt-console 的 `harden-subscription-concurrency` Task2 Step4 写了「+ 全量回归」，而 `backend-subscription-authority` Task8 仅跑 scoped）。这浪费测试执行墙钟，且违背 superpowers `subagent-driven-development` 原生设计——implementer 只跑覆盖自己改动的 scoped test，全量 whole-branch 回归仅在 final review 前跑一次。

跨三项目 git numstat 实证已确认：测试占比由「栈构成 × change 类型」决定（是 TDD ~1.5x 本性），**不是** sdflow 流程、也不是任务粒度。故本 change **只纠测试执行范围**，不碰测试代码量、不碰任务粒度。

## What Changes

- **workflow.md 步骤 6/7**（bundle 权威源 `sdflow-init/assets/workflow/`）：把「每任务完成跑测试套件」改为「每任务只跑覆盖本任务的 scoped test（named test files）确认无 warning；全量 `-race`/回归套件仅在 final whole-branch 终审前跑一次」。
- **sdflow-ship/SKILL.md RUN_PLAN 分支**：`→ subagent-driven-development 自动执行` 处补测试范围纪律注入（薄编排、引用 workflow.md 为单一源、不复述细节；**不动** checkpoint 主锚契约措辞）。
- 经 `sdflow-init update` 推下游 + 本仓 `setup.sh`；跑 `sdflow-ship/tests/` 验证 ship_gate 判据无回归。
- 非 **BREAKING**：措辞纠正，向 SDD 原生轻量回归对齐。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `spec-workflow`：**ADDED** 一条 Requirement——阶段三派发 `subagent-dev` 注入测试范围纪律（每任务 scoped test + 全量回归仅 final whole-branch 终审一次）。既有「阶段三过设计门后连续自动跑到 merge」Requirement 不改，本 change 只在该 capability 补这一条派发约束。

## Impact

- **文件**：`sdflow-init/assets/workflow/workflow.md`（步骤 6/7）、`sdflow-ship/SKILL.md`（RUN_PLAN 分支）。
- **分发**：bundle 权威源改动 → `sdflow-init update` 推各消费仓 `openspec/workflow/` + 本仓 `setup.sh` 刷新 `~/.sdflow`。
- **测试**：`sdflow-ship/tests/`（验证 RUN_PLAN 相关断言、ship_gate 判据无回归）。
- **不涉及** `ship_gate.py` 判据逻辑（测试范围不是完成判据）。

## Success Metrics

- workflow.md 步骤 6/7 与 sdflow-ship RUN_PLAN 均含 scoped-test 纪律措辞，且全量回归明确限定「final whole-branch 终审一次」。
- `sdflow-ship/tests/` 全绿（ship_gate 判据无回归）。
- `sdflow-init update` 后下游 workflow.md 托管块同步刷新、无残差。

## Non-Goals

- 不改测试代码量、不改任务粒度（三项目实证：测试占比 = 栈 × change 类型、非流程；粒度普遍健康）。
- 不做「领域约束逐字进 Global Constraints」（注入点 A）——实测 A 路径 plan 的 Global Constraints 已详尽含领域约束（writing-plans 原生 copied-verbatim + spec-review 收口已覆盖），收益 ≈ 0。
- 不改 `ship_gate.py` 完成判据（测试范围非 gate 判据）。
- 不改 checkpoint 主锚契约措辞、不改「原子任务/参考 tasks.md」措辞。

## Assumptions〔TG-22〕

- **假设**：改 workflow.md 步骤 6/7 与 sdflow-ship RUN_PLAN 的测试范围措辞**不影响 ship_gate 完成判据**（gate 只认 checkpoint 命名空间标签，不解析测试范围文本）。**失效影响**：若 gate 竟依赖测试措辞，改动可能扰动 `CONTINUE_IMPL`/`RERUN` 判定 → 由 tasks 中「跑 `sdflow-ship/tests/` 验证判据无回归」兜住。

## Compliance

遵 `spec-workflow` 既有 Requirement「workflow bundle 改在权威源、经部署下发」：改动落于 `sdflow-init/assets/workflow/` 权威源，经 `sdflow-init update` 下发，不在下游项目直接改。不涉及数据/安全/外部服务合规——N/A。
