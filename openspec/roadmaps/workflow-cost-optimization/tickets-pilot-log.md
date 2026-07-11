# tickets 管线试点执行记录（Phase A）

> **用途**：tickets 实现管线（sdflow-implement）Phase A 试点的逐 change 执行记录 + 判赢材料留档。
> 格式与判据源：`openspec/changes/archive/2026-07-10-matt-workflow-integration/pilot-briefing.md`（④ 留档格式、③ 判据三条 + 分桶口径、⑤ 观测项）。
> **消费方**：本 roadmap（workflow-cost-optimization）P5「frontier 受限并行」以 Phase A 判赢为硬前置（见 `roadmap.md`）。
> **只呈现不裁定**：本表按 pilot-briefing ⑥ 节奏逐条累积；判赢/熔断由人读判据三条拍板，本表不代判。

---

## 样本 #1 — mlh-p4-reason-code-validators（SHIPPED 2026-07-11）

### ④ PIPELINE_RECEIPT 留档 + 计样前核对

| change | PIPELINE_RECEIPT 原文 | 核对结论 |
|---|---|---|
| mlh-p4-reason-code-validators | `change=mlh-p4-reason-code-validators config=tickets marker=tickets pipeline=tickets plan_sha=533a9f0` | `config=marker=pipeline=tickets` 三字段一致 → **样本有效**（不剔除）。 |

### 判据① 墙钟 —— ⚠ 跨桶打折，改按 per-ticket 分别归桶

**为何打折**：pilot-briefing ③ 对照口径「每个试点 change 先归入其类型桶、**禁跨桶比较**」。本 change 出于「三校验器三合一 + 接入 + 回灌」的自然边界，5 票**跨 3 个类型桶**，故 change 级总墙钟（61.0 min）**不可**与任一单桶历史中位数对照——判据①在 change 级不成立。补救 = 按 per-ticket 归桶留原始墙钟，供 retro 各桶内同类对照。

| 票 | 交付 | 类型桶 | impl+双轴审墙钟 | implementer 状态 | 码/测 LOC |
|---|---|---|---|---|---|
| T1 | outside_voice_guard | **代码质量·新增单脚本校验器** | 15.9 min | DONE | 149 / 241 |
| T2 | hr_tg_intersect | **代码质量·新增单脚本校验器** | 8.8 min | DONE | 114 / 233 |
| T3 | review_disposition_check | **代码质量·新增单脚本校验器** | 13.1 min | DONE | 149 / 236 |
| T4 | 3×SKILL.md 接入 + anchor_lint declared= | **接入/整合·跨技能接线** | 14.6 min | DONE | +19(anchor) / 接线 |
| T5 | bundle 回灌 + dogfood | **基础设施/发布·同步+验收** | 8.6 min | DONE | 0 新码 / dogfood |

**per-ticket 分桶聚合（供 retro 各桶内对照，禁跨桶）**：
- 代码质量·单脚本校验器桶：T1/T2/T3，n=3，墙钟中位 **13.1 min/票**（8.8–15.9）。
- 接入/整合桶：T4，n=1，**14.6 min**。
- 基础设施/发布桶：T5，n=1，**8.6 min**。

> **粒度警示（勿误比）**：tickets 的「票」= 一个完整校验器（垂直切片）；历史 superpowers 基线的「task」= 校验器的**子部件**（如 lens-metric-emit 把 1 个 emitter 拆 8 task）。故「代码质量桶」内比较应在**同交付粒度**上做——同型对照 = `lens-metric-emit`（superpowers，1 个 198-LOC emitter，实现环 ~54 min），但其复杂度更高，仍 confounded。**判据①的方向性结论 DEFERRED 给人读 retro**（须取各桶同粒度历史中位数），本表不断言 Δ 方向。

### 判据② 冷层 Critical/严重 findings 与 verify FAIL —— 不升 ✅

- 冷层 `sdflow-code-review`：2 中危假绿（fence-aware）+ 5 defer hardening + 1 codex 独家；**Critical/严重 = 0**。
- `sdflow-done` verify：**PASS**（无 FAIL）。
- 判据② 满足（不升）。

### 判据③ 护栏哨兵 —— 未触发熔断 ⚠（黄旗观测）

- 哨兵定义：冷层捕获「本应被每 ticket 审拦住的**严重项**」占比不恶化；恶化 = 熔断。
- 本 change：冷层捕获的 2 项假绿均为 **中危（medium），非严重/Critical** → **严重项逃逸 = 0 → 哨兵未触发、不熔断**。
- **黄旗观测（不计入熔断，供 Phase B 参考）**：这 2 条中危假绿是校验器**次要解析路径**的 fence-aware 缺陷，10 次每票双轴审（~632k token）**全绿放过**、由冷层独家抓出。根因 = 双轴审逐票验「主路径验收达标」，对**跨票的「面」级问题**（次要解析路径口径漂移）天然盲（memory: 点驱动修补 vs 面治）。**若后续样本此类中危逃逸复现，应升级评估**是否双轴审对「机械+规格锁死」类工作插桩过度、真防线在冷层。

### ⑤ 观测项（非判据，尽力采集）

| 观测项 | 本样本值 | 备注 |
|---|---|---|
| NEEDS_CONTEXT 停摆率 | **0/5**（5 票全 DONE，0 NEEDS_CONTEXT/BLOCKED） | 支持「行为级 ticket 文本即 brief」假设（proposal 假设③）——本样本未证伪 |
| token 维度（实测子代理） | **~2.08M**（实现环 1.20M：impl 0.56M + **双轴审 0.63M/30%**；冷层+2 轮修+复验 0.88M，其中 fence 事故独占 ~0.55M） | 「尽力采集」；双轴审 30% 为结构性成本，fence 事故 + 首次学习为一次性 |

### confounders（判据可信度打折项，成文留档）

1. **跨 3 桶**（违 pilot-briefing:35）→ 判据①change 级失效，已按 per-ticket 补救（上）。
2. **叠 3 first-of-kind**：首个 tickets 试点 + 首次三校验器同型套 + 首次 fence-aware 假绿事故；实现环 61min 与 2.08M token 含显著一次性成本，**非 tickets 稳态**。
3. **内容难度混入**：fence 解析本身绕（2 轮修 + 1 次贪婪回归），冷层+修占 ~0.55M token 是内容难度、非管线开销。

### 小结（本样本，不代判 Phase A）

判据②满足、判据③未熔断（1 条黄旗观测）、判据①按 per-ticket 归桶留档待 retro 同桶对照。**样本 n=1 且重度 confounded，不足以对 tickets 判赢/判负**——按 pilot-briefing ⑥，需从候选池再取非首次、单桶候选累积 2–3 个样本，方可由人读判据三条拍板 Phase A 是否进 Phase B。

---

*样本 #2 起后续追加于此。*
