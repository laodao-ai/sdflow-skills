## Context

阶段三编排器 `sdflow-ship`（A 路径）在 `RUN_PLAN` 分支派发 `writing-plans → subagent-driven-development`，对 SDD 是「自动执行」**零注入测试范围**。而 workflow bundle 的 `workflow.md` 步骤 6/7 现措辞为「每任务完成跑测试套件」——即逐任务跑**全量套件**，与 superpowers `subagent-driven-development` 原生设计（implementer 只跑覆盖自己改动的 scoped test、全量 whole-branch 回归仅 final review 前一次）相冲突。

现状实证：测试范围逐任务不统一（mqtt-console `harden-subscription-concurrency` Task2 写「+ 全量回归」，`backend-subscription-authority` Task8 仅 scoped），浪费测试执行墙钟。

约束：
- `sdflow-ship` 薄编排原则——引用 `workflow.md` 为单一源、不复述细节（现有对 checkpoint 格式即如此处理："其余消费方只引用本处、不复述完整格式串"）。
- workflow bundle 改在权威源 `sdflow-init/assets/workflow/`、经 `sdflow-init update` 下发。
- 不动 `ship_gate.py` 完成判据、不动 checkpoint 主锚契约措辞。

## Goals / Non-Goals

**Goals:**
- 统一测试范围纪律：每任务只跑覆盖本任务的 scoped test；全量 `-race`/回归仅 final whole-branch 终审前一次。
- A 路径（sdflow-ship 编排）与 B 路径（手动 workflow.md）措辞一致，同步纠回 SDD 原生态。

**Non-Goals:**
- 不改测试代码量、不改任务粒度。
- 不做注入点 A（领域约束进 Global Constraints）。
- 不改 ship_gate 判据、不改 checkpoint 契约。

## Decisions

### ADR〔TG-23〕：测试范围纪律的承载位置

**选择：方案 B（workflow.md 单一源 + sdflow-ship 引用），弃方案 A（sdflow-ship 内嵌复述）。**

| 方案 | 做法 | 取舍 |
|---|---|---|
| A · 内嵌复述 | sdflow-ship RUN_PLAN 直接写全套 scoped 纪律文字 | ✗ 双源、复述→漂移、违背薄编排 |
| **B · 单一源引用** | workflow.md 步骤 6/7 承载纪律全文；sdflow-ship RUN_PLAN 只**引用** | ✓ 与现有 checkpoint 格式处理同构；单一源不漂移；A/B 路径同步纠正 |

**理由**：①与 sdflow-ship 现有对 checkpoint 格式的引用同构（引用 workflow.md、不复述）；②单一源避免 A 路径（ship 编排）与 B 路径（手动）漂移——改一处两路同纠；③守薄编排原则。

**落地形态**（派发链改动点）：
```
RUN_PLAN → writing-plans → subagent-dev 自动执行
                                 └─[注入] 测试范围纪律（引用 workflow.md 步6/7）
                                     ├ 每任务: 只跑覆盖本任务的 scoped test(named files)
                                     └ 全量 -race 回归: 仅 final whole-branch 终审一次
```
- workflow.md 步骤 6/7：「每任务完成跑测试套件」→「每任务只跑覆盖本任务的 scoped test（named test files）确认无 warning；全量 `-race`/回归套件仅 final whole-branch 终审前一次」。
- sdflow-ship/SKILL.md RUN_PLAN：`subagent-driven-development 自动执行` 处加一句引用式注入，不复述完整规则、不动 checkpoint 契约句。

## Risks / Trade-offs

- **[gate 竟依赖测试措辞]** → ship_gate 只认 checkpoint 命名空间标签、不解析测试范围文本；tasks 以跑 `sdflow-ship/tests/` 验证 verdict 判据无回归兜住。
- **[下游漂移]** → 经 `sdflow-init update` 下发 + 本仓 `setup.sh`；托管块刷新核对。
- **[引用而非复述 → implementer 读不到规则]** → sdflow-ship 运行时经 `resolve-workflow.sh` 解析 workflow 规则根，controller 派 SDD 时已持 workflow 上下文；与现有 checkpoint 格式引用同机制，风险等同、不新增。

## Compliance

遵 `spec-workflow` 既有 Requirement「workflow bundle 改在权威源、经部署下发」：改动落权威源 `sdflow-init/assets/workflow/`，经 `sdflow-init update` 下发，不在下游直接改。遵 sdflow-ship 薄编排（引用单一源）。不动 ship_gate 判据与 checkpoint 契约——显式声明，无沉默例外。不涉及数据/安全/外部合规。
