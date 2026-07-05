# spec-review 报告 — gate-anchor-line-scoped

> 阶段二设计审（编排多镜）。审查对象：修 B4——ship_gate.py 锚检测裸子串→行级整行等值+fence-aware，抽共用 `_line_scoped_hits`，`anchors_in`+`archived_verify_state` 两处折入。本 change 已先过 grill（Q1 折入 line 143 / Q2 ADR-2 定位），本审在 grill 之上再做独立多镜。

## 命中范围

- **TG**：TG-25（契约套件）/ TG-23（≥2 方案）/ TG-22（未验证前提）/ TG-18（测试计划）/ TG-12（决策逻辑）。技术栈 TG-01/02/03 **均不命中**（元仓 Python gate 脚本）。
- **HR-TG 子集**（{04,06,07,08,09,16,17,26}）命中 = **none** → 不开领域专属 cross-model。
- **镜阵**：领域镜 0（无栈命中）· 对抗镜 2 · 接地镜 1 · outside-voice(design-voice, codex) 1 · Step1 原生广审。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="锚检测=纯内部 gate 逻辑，不涉 DB/API/并发/信任边界/状态机，HR-TG 子集无一命中" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="" findings="2" truncated="false" -->

---

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [已拍板 A] Q1-TENSION 未闭合 fence + 互斥锚对 = 危险假阳（codex OV-2 证伪 │
│                      grill Q2 的「安全侧」前提）→ A 加 unbalanced 处理(荐) │
│                      / B 接受并如实记缺口。重开 grill Q2。                  │
│ [自动决策] D1  BR-1 proposal TG 头误标 TG-01 → 已改（去 TG-01，元仓无栈） │
│ [自动决策] D2  BR-2 task2.1 测试落法与 archived_verify_state 签名不符 →   │
│                已改（拆核心单元 + git fixture 端到端两层）                  │
│ [自动决策] D3  BR-3/OV-1/对抗镜1 收敛：契约样本源歧义 → tasks3.4 已钉      │
│                「样本源=归档 corpus，非 SKILL 展示块」+ 3.5 消歧义源头     │
│ [自动决策] D4  design 行号漂移(_parse_plan) → 已按接地镜校正              │
│ [已拍板] Q2-DOGFOOD 跑 gate 现场：tg02_hit(:237) 第三个同类子串 bug 假   │
│               RUN_SOP 卡本 change ship → 折入本 change(Q3=A1 声明式匹配)   │
│ [已裁掉]  X1   对抗镜1/2 均判「未闭合 fence=安全侧」→ 被 OV-2 具体两锚     │
│                场景推翻（非静默丢：见下裁决）                              │
│ [已裁掉]  X2   OV-1 即时假阴断言（真报告会漏锚）→ 15/15 归档实证证伪，     │
│                但其模板脆性子论点采纳为 D3                                  │
└──────────────────────────────────────────────────────────────────────────┘
```

### [需拍板] Q1-TENSION — 未闭合 fence 对互斥锚对的危险假阳（codex OV-2）

- **两方视角**：
  - **codex OV-2（外部声）**：`_line_scoped_hits` 仅奇偶翻转。盘面「正锚在 fence 外 + 未闭合 \`\`\` + 负锚在内被吞」→ 只返正锚 → `pick_exclusive`（:220 `positive in found` 真 → 返 `"pos"`）/ `archived_verify_state`（`has_pass=T/has_fail=F` → `"pass"`）从**应有 conflict/UNKNOWN 翻成 pass** → 假 SHIPPED / 假放行。**旧裸子串两锚都命中 → conflict（安全）**——即 ADR-2 对此盘面是**引入**危险假阳的回归。
  - **对抗镜1+2（主审侧）**：均判未闭合 fence 只致「多一次重验/人工核验」的安全侧假阴。**但二者只分析了单锚 / 无锚吞没**（→None→STEP_IN_PROGRESS / none），**未覆盖两锚非对称吞没**（正在外负在内）——OV-2 恰打在此盲区。
- **主审裁决**：**codex OV-2 CONFIRMED**。走码核实 `pick_exclusive` 在 `found={正锚}` 时返 `"pos"` 非 `None`，机制成立；旧行为确为 conflict。两对抗镜的「安全侧」结论在**两锚场景被推翻**（escalate-not-drop：多数说安全 ≠ 覆盖一个已证实的具体危险）。
- **现实性**：需报告同含正+负锚且未闭合 fence 隔断——构造性、非常见；但 gate 本旨即防畸形报告假阳（B4 本身就是"异常报告"），且旧行为安全、本 change 使其危险=回归。
- **选项 + 后果**：
  - **A（推荐）** 给 `_line_scoped_hits` 加未闭合 fence 检测（复用现成 `plan_unbalanced_fence` :353-356，接地镜确认存在），互斥锚对调用方（`pick_exclusive`/`archived_verify_state`）遇 unbalanced → 判 UNKNOWN/none（保守）。**后果**：+~5 行 + 2 测试；闭合回归；契合「堵假阳」本旨；**重写 grill Q2 决策**（Q2 依赖的前提已伪）。
  - **B** 接受，Non-Goals **如实**记「互斥锚对 + 未闭合 fence = 已知假阳缺口」（非安全侧）。**后果**：scope 最小，但在一个专为堵假阳而生的 change 里留一个新假阳洞，自相矛盾。
- design.md Non-Goals 已先行**改正**为如实表述并指向本条（不留"安全侧"假声明）。

---

## 各镜 findings

### 对抗镜1（隐藏假设/边界，sonnet）
- fence toggle 边界（语言标签/缩进/同行/`~~~`）：**NO-EXPLOSION**，全仓语料核实非现实盘面。
- whole-line 假阴：核心断言真（15/15 归档锚独占顶格）；**中**severity 实现陷阱 = task3.4「模板样本」歧义（同 OV-1）→ 采纳 D3。
- archived_verify_state 折入 / decide 顶层堵 B4：**NO-EXPLOSION**（分支语义保留、B4 端到端可测）。

### 对抗镜2（失败模式/spec 一致，sonnet）
- 锚检测点穷举 / spec delta↔主spec 逐字diff / ADR↔task 追溯 / 零外扩回归：**四角度 NO-FINDING**（delta 22 Scenario 逐字保留+2新、无矛盾；追溯完整；既有测试锚全独占不受影响）。
- 其「未闭合 fence 安全侧」子结论 → 见 X1（被 OV-2 推翻）。

### 接地镜（读码核验，haiku）
- **9/9 全符**：anchors_in :203 纯子串 ✓ / archived_verify_state :143 裸子串+三态+git show ✓ / pick_exclusive :219 调 anchors_in ✓ / :408 设计门 ✓ / :478 ✓ / :237 TG-02 非锚 ✓ / T34 fence 追踪 :313-317 ✓ / **裸子串锚判定仅 :143 一处（无第三路径）** ✓ / 受影响测试=preflight·terminal·tail·freshness ✓。
- 增量：`plan_unbalanced_fence` :353-356 **已存在** → 支撑 Q1-TENSION 选项 A 低成本。

### outside-voice（codex, design-voice）
- **OV-1（high→部分）**：真锚独占假设 vs 模板尾注/反引号 → 即时假阴断言被 15/15 实证证伪（X2），模板脆性子论点采纳（D3）。
- **OV-2（medium→CONFIRMED 升格）**：未闭合 fence 互斥锚对危险假阳 → Q1-TENSION 主发现。

---

## 收敛口

设计 HARD-GATE **已批准（Q1=A）**：Q1-TENSION 采纳选项 A——加未闭合 fence 检测，互斥锚对遇 unbalanced 保守判 UNKNOWN/none（design ADR-5 / tasks §2b / spec delta 新增 Scenario 均已落）。其余 findings 已作 [spec-review-amendment] 落地。**可进 writing-plans → 实现**。

## 拍板记录

- **Q1-TENSION → A（采纳）**：加 unbalanced 处理（复用 `plan_unbalanced_fence` :353-356），互斥锚对（`pick_exclusive`/`archived_verify_state`）遇未闭合 fence 保守失败到安全侧。design ADR-5 + tasks 2b.1-2b.3 + spec delta「未闭合 fence 隔断互斥锚对不判假通过」Scenario 已同步。
- 用户于设计 HARD-GATE 批准（选 A）。
- **Q2-DOGFOOD → 折入 / Q3 → A1**：跑 ship_gate 现场暴露 `tg02_hit`(:237) 第三个同类子串 bug——对 proposal 里 TG-02 描述性提及假阳 → 假 RUN_SOP 卡住本 change 自己 ship。用户拍板折入本 change；修法 Q3=A1 声明式 `〔TG-02` 匹配（非行锚——TG 标签内联）。design +ADR-6, tasks +§2c, spec delta +Scenario(26 条)。
- 用户于设计 HARD-GATE 再次批准（含 tg02 折入 + Q3=A1）。锚刷新至本次提交（防新增四件套改动使拍板失鲜）：

- **Q3-dogfood-2 → A3（头部区域限定）**：实现期跑 gate 再暴露 Q3=A1 的 `〔TG-02` 整体子串（含加冒号）仍被本 change proposal 正文示例声明串 `〔TG-02：`（line 42）假阳。用户拍板 A3：`tg02_hit` 只扫 proposal 头部声明区（首个 `## ` 前）。design ADR-6/tasks §2c/spec tg02 Scenario 同步；实现 @627396d（tg02 header-region + 活体回归）。锚随本次四件套同步再刷新（防失鲜）。

<!-- ship-gate: design-approved -->
