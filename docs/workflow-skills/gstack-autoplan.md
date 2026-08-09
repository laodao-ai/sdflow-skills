# 外部 skill 展开 · gstack `autoplan`

> **定位：非运行时依赖的第三方 skill 参考**——`sdflow-spec-review`/`sdflow-roadmap` 的广审层已改为
> 自持 fresh 子代理实现的 strategy/plan-eng 双镜（单批 dispatch，见
> [sdflow-spec-review 详解](./sdflow-spec-review.md)），不再原生调用本 skill。本文保留作为
> `autoplan` 自身设计的参考资料。
>
> **一句话**：一条命令，把粗略计划跑成一份被 **CEO / Design / Eng / DX 四道审**深度审过的计划——
> 方法论/严格度与手动逐个跑这四个审**完全相同**，唯一区别是中间的 AskUserQuestion 被 **6 条决策原则**自动决策，
> 只有「品味决策」留到最后审批门交人。

---

## 1. 在本 workflow 中的位置与契约（历史形态，已退役）

| 维度 | 内容 |
|---|---|
| 谁调它 | **无**（本仓当前无 skill 运行时调用它；广审已改为 `sdflow-spec-review`/`sdflow-roadmap` 自持双镜，见上方定位说明） |
| 进（输入） | 一个**计划文件** + 仓库上下文（CLAUDE.md / TODOS.md / git log / git diff / 已有 design） |
| 出（产物） | 计划文件**原地增补**（各 phase review 章节 + consensus 表 + `## Decision Audit Trail` 审计表 + 聚合任务表）；restore point 外置；per-phase 任务 JSONL；review logs |
| 历史接入方式（已废止） | 曾由主 session 汇总其结论落盘 `{change_dir}/gstack-review.md`，findings 纳入 spec-review 的合并池 |

---

## 2. 内部流程（顺序执行，MANDATORY）

**硬约束**：`CEO → Design → Eng → DX` 严格顺序，每 phase 完整跑完才开下一个，**禁并行**（每 phase 建立在前一个之上）。

```mermaid
flowchart TD
    P0["Phase 0 · Intake + Restore Point<br/>存原始计划 + 读上下文 + 检测 UI/DX scope + 从磁盘 Read 四审 skill"]
    P05["Phase 0.5 · Codex 可用性预检<br/>auth/version 探测；失败则全程降级 Claude-only"]
    P1["Phase 1 · CEO Review（战略/范围/前提）<br/>Step0 + 11 sections · dual voices · ★premise gate"]
    P2["Phase 2 · Design Review（仅 UI scope）<br/>7 passes 0-10 打分"]
    P3["Phase 3 · Eng Review（架构/质量/测试/性能）<br/>+ test plan artifact · Section3 测试审永不跳"]
    P35["Phase 3.5 · DX Review（仅 DX scope）<br/>8 passes + TTHW + DX Scorecard"]
    PG["Pre-Gate Verification<br/>逐条核验各 phase 产物真落盘，缺则回补（最多 2 次）"]
    P4["Phase 4 · Final Approval Gate<br/>jq 聚合任务表 → ★呈现汇总 → AskUserQuestion（A~E）"]
    P0 --> P05 --> P1 --> P2 --> P3 --> P35 --> PG --> P4
    P1 -. "无 UI scope 跳过" .-> P3
    P3 -. "无 DX scope 跳过" .-> PG

    AUDIT["## Decision Audit Trail<br/>每次自动决策增量追加一行到磁盘"]
    P1 -.每步决策.-> AUDIT
```

| Phase | 视角 | 目标 | 注意事项 |
|---|---|---|---|
| 0 · Intake | — | 存 restore point、读上下文、检测 UI/DX scope、**从磁盘 Read 四审 skill 当指令跟随** | 应用 Section skip list（跳各子审的 Preamble/AskUQ/Telemetry/Outside-Voice 样板），只跟 review 方法论 |
| 0.5 · Codex 预检 | — | 判 Codex 可用性 | `codex_reviews=disabled` 或 auth 失败 → 全程降级 Claude-only（含双声） |
| 1 · CEO | 战略/范围/前提 | Step0 + 11 sections（架构/威胁模型/数据流/质量/测试/性能/可观测/部署/长期轨迹…） | Mode 固定 `SELECTIVE EXPANSION`；**唯一非自动决策的门 = 前提确认（premise gate）** |
| 2 · Design | 设计师之眼/UX | 7 passes（信息架构/交互状态覆盖/旅程/AI slop/设计系统/响应式无障碍/未决决策）0-10 打分 | **仅 UI scope 命中才跑**；结构性问题自动修，审美问题标 TASTE |
| 3 · Eng | 工程经理 | Step0 Scope Challenge + 架构/代码质量/测试/性能 | **Section3 测试审永不跳/不压缩**（读实际 diff、建 test diagram、写 test plan artifact）；有置信校准 + pre-emit 验证门 |
| 3.5 · DX | 「从没见过本产品的开发者」 | 8 passes + 开发者旅程图 + TTHW（Time to Hello World，目标<5min） | **仅 DX scope 命中才跑**；错误消息须 problem+cause+fix |

> **审计留盘（关键设计）**：每次自动决策后用 Edit **增量**追加一行到计划文件的 `## Decision Audit Trail`——
> 「审计留在磁盘，不在对话上下文里累积」，对抗 context 膨胀。

---

## 3. 6 条决策原则（autoplan 自动决策的核心）

这 6 条**代替用户回答**每一个中间 AskUserQuestion（但**不代替分析深度**）：

| # | 原则 | 要义 |
|---|---|---|
| 1 | **Choose completeness** | 做完整的那个，覆盖更多 edge case |
| 2 | **Boil lakes** | 修爆炸半径内一切（本计划改的文件 + 直接 importer）；半径内且 <1 天 CC 工作量自动批 |
| 3 | **Pragmatic** | 两方案修同一问题选更干净的；5 秒决定别 5 分钟 |
| 4 | **DRY** | 重复已有功能 → 拒；复用 |
| 5 | **Explicit over clever** | 10 行显然修复 > 200 行抽象；新人 30 秒读懂的赢 |
| 6 | **Bias toward action** | merge > review 循环 > 陈旧的反复权衡；标记顾虑但不阻塞 |

> **分阶段 tiebreaker**：CEO 阶段 P1+P2 主导；Eng 阶段 P5+P3 主导；Design 阶段 P5+P1 主导。
> **决策三分类**：Mechanical（唯一正确 → 静默自动）/ Taste（合理人会分歧 → 自动决策带推荐、升最终门）/ User Challenge（两模型一致认为用户既定方向该改 → **永不自动决策**）。

---

## 4. 内部调度的子 skill / 子代理

| 被调 | 类型 | 角色 |
|---|---|---|
| `plan-ceo-review` | 磁盘读入当指令 | CEO/创始人视角，前提 + 范围 + 战略 |
| `plan-design-review` | 磁盘读入当指令 | 设计师之眼，7 passes（仅 UI scope） |
| `plan-eng-review` | 磁盘读入当指令 | 工程经理，架构/质量/测试/性能 + test plan |
| `plan-devex-review` | 磁盘读入当指令 | DX 工程师，8 passes + TTHW（仅 DX scope） |
| 每 phase 一个 Claude subagent | Agent 工具（前台阻塞） | 「独立冷启动 reviewer，没看过任何前序审」，作 Claude 一路第二意见 |
| **Codex**（每 phase 一次） | `codex exec ... -s read-only` 外部命令 | 双声（dual voices）的 codex 一路第二意见；有 10min/12min 超时外闸，stall 则降级本 phase |

> **Codex 文件系统边界（硬前缀）**：所有发给 Codex 的 prompt 冠以「**不要读或执行任何 SKILL.md / skills/gstack 目录下文件**」——
> 防 Codex 那侧把磁盘上的 gstack skill 当指令执行（prompt-injection 防护）。

---

## 5. 人类门 / headless 降级

**只有两道非自动决策的门**：① Phase 1 的 **premise gate**（前提确认，须人类判断）；② **User Challenge**（两模型一致认为用户方向该改——**永不自动**，默认保持用户原方向）。外加 Phase 4 **Final Approval Gate** 一次性交人（A 全接受 / B 带 override / B2 逐条回应 / C 追问 / D 改计划重跑受影响 phase / E 推翻重来）。

```mermaid
flowchart LR
    subgraph 降级["AskUserQuestion 降级链（按 SESSION_KIND）"]
        C["Conductor<br/>不调 AUQ → 渲染 prose 并 STOP"]
        S["spawned<br/>自动选推荐项"]
        H["headless<br/>BLOCKED，停等（无人可答）"]
        I["interactive 且工具报错<br/>prose fallback（ELI10+Completeness+Recommendation）"]
    end
```

> **历史适配（已随本 skill 退役而失效）**：`sdflow-spec-review` 曾走连续自动流（G2「中途不 AskUserQuestion」），
> 把 autoplan 的 premise/challenge/最终门**登记进 spec-review-report.md 决策登记区**，等阶段二设计门一次拍板——
> 详见 §6（历史设计说明，现由自持双镜 + Step3 决策登记区直接承接，不再经由 autoplan）。

---

## 6. ★ 历史设计说明：本 workflow 曾如何注入规则/prompt 影响 autoplan —— 建议式 vs 强制

**统一判据**（见[总览 §注入的强制性](../workflow-overview.md#8-外部-skill-的注入强制性建议式-vs-强制统一规律)）：autoplan 是 **prompt 驱动**（磁盘读 skill 当指令跟随），本 workflow 的注入也在 **prompt 层** → **默认建议式**；只有背后有**确定性载体**（脚本 / 文件 / 被下游门读取的 git 产物）才转强制。autoplan **没有对「调用方注入指令」做特权分级**——注入的要求与 skill 正文同级混入模型上下文。

| 注入项（来自 sdflow-spec-review） | 注入方式 | 建议式 / 强制 | 靠什么 |
|---|---|---|---|
| 「原生执行，不派子代理转述模拟」 | sdflow 侧规则 | **半强制**（对 sdflow 侧） | Step1 报告写 `mode="native"` 锚行 + Step3 **锚行存在性自检**（grep 缺失即报错阻塞）——机械兜底在 sdflow 编排层，非 autoplan 内部 |
| 「中途不弹窗，人类门登记进报告」（G2/C5） | prompt 适配 | **建议式，且与 autoplan 硬不变量张力** | autoplan 把 premise gate / User Challenge 钉为「NEVER auto-decided」、headless→BLOCKED；本 workflow 不「强制关掉」它，而是让**主 session 承接**其决策登记进报告、留到设计门。靠主 session 遵从，非机制强制 |
| 「findings 纳入合并池 + 落盘 `gstack-review.md`」 | 主 session 动作 | **强制（在 sdflow 侧）** | autoplan 原生只写 plan file、无写任意路径能力 → 落盘由**主 session** 做（sdflow 侧确定性动作），不依赖 autoplan |
| 「扩审某清单 / 多审一个维度」 | prompt 注入 | **建议式（会被吸收）** | 与 autoplan 完整性取向（P1/boil-the-ocean）同向，几乎必被当指令执行；但受 full-depth 红线约束（扩审也不得压缩既有 section） |

**结论**：autoplan 的**审查内容层**（读哪些 skill、审哪些维度）高度可被 prompt 影响、当指令执行；而**人类门 / 顺序执行 / full-depth / Codex 边界**是被反复钉死的不变量，注入若想取消它们，模型有明确原文依据抵抗——但这仍是「靠模型遵从的软门禁」，**非运行时代码级强制**。本 workflow 真正的机械兜底不在 autoplan 内部，而在 **sdflow-spec-review 编排层的锚行自检** + **下游设计门 HARD-GATE**。

---

## 7. 小结

- autoplan = **四审顺序跑 + 6 原则自动决策 + 审计留盘 + 最终门交人**，把 15-30 个中间问题压成一次审批。
- **历史形态**：在本 workflow 曾用作 spec-review 的「广审层」；现已由 `sdflow-spec-review`/`sdflow-roadmap`
  自持的 strategy/plan-eng 双镜取代，不再调用。
- 上述「注入建议式/强制」分析属历史设计说明，供了解退役前的机制脉络参考。
