# Spec 评审规则（Spec Review）

> **定位**：spec 的 **Detection（生成后检查）层**规则，与 [`generation-process.md`](./generation-process.md)
> （生成层）成对。前提：结构①、约束② 已由 `config.yaml` 固化（Prevention），过程③ 由 generation-process
> 管。**review 只做 prevention 焊不住的残差**——不重做已被防住的机械项。项目无关。

---

## 一、review 是 Detection 残差（prevention 之后只查剩下的）

方法论铁律（shift-left）：**review 不重做 prevention 已防住的东西**。

```
  ✗ review 不该做（已被 prevention / lint 管）：
     占位符 · 内部一致 · 歧义 · 槽位是否齐全 · NFR 是否数字化
     → config 结构槽防住 + 一个 lint 扫描即可，不占 review 注意力

  ✓ review 必须做（prevention 焊不住的）：
     ① Validation / R 桶  scope 对不对、方案选得对不对、会不会炸（判断）
     ② 对抗             refute / 独立双声挑刺
     ③ 接地             读真实代码核验 Accurate
```

## 二、三条原则（来自 [Spec_Quality_Methodology.md](./reference/Spec_Quality_Methodology.md)）

### 原则 1 · 独立性（瑞士奶酪：自审无效）

作者审自己 = 同一片奶酪叠自己，洞不会错开。**review 必须由独立于作者的上下文做**：
fresh-context 子 agent / 第二声音（如 Codex）/ `/clear` 后重审 / grill。
→ 同 session 的 self-review 不算 review，只算生成期自检。

### 原则 2 · 接地（读真实代码）

`reference/Spec_Quality_Collaboration.md` 早已点出：**Accurate 是唯一没有 review 保障的标准**。
prevention 的 D-1 只在生成时管一半（写时核验）。review **必须读真实代码**核验
spec 里的代码事实（函数名/字段/API 路径/schema）是否真实存在、是否一致。

### 原则 3 · 对抗（refute，而非顺向确认）

不问"这 spec 对吗"，而是派独立视角"**请证明这 spec 会在实现期爆炸**"。
顺向 checklist 容易放过隐藏假设；对抗式更易揪出。

## 三、review 深度 = trigger 驱动（不分 S/M/L 档）

review 的本质 = **验证「命中的 TG 所激活的 槽/约束/图 是否真的对」**，而非通览全表：

```
  命中 TG-04(DB 迁移)  → 必审 backend·DB 段 + 迁移安全 + v_old/v_new 表是否正确
  命中 TG-17(安全)     → 必审 安全段 + 信任边界
  命中 TG-09(状态机)   → 必审 状态机图是否覆盖异常转换
  未命中的             → 不审（prevention 阶段它压根没出现）
```

TG 定义见 [`trigger-catalog.md`](./trigger-catalog.md)。

## 四、三层（每层独立、盲区互补）

| 层 | 做什么 | 由谁 | 对应 |
|----|--------|------|------|
| **L0 机械扫描** | 占位符/一致性（S 项） | lint / 脚本 | 不算 review，是门禁 |
| **L1 标准核对** | 命中 TG 的 domain 清单的 **R 项**逐条 | **独立 agent（非作者）** | spec-checklists |
| **L2 对抗 + 接地** | refute + 读真实代码 + 决策树死磕 | strategy/plan-eng 双镜（自持）/ grill / 读码 | **最高价值，主力** |

L0 机械、L1 标准、L2 判断——三层盲区不同，叠起来才不漏穿。

## 四点五、finding 分流：标注，不丢弃（escalate-not-drop）

每条 finding 标**置信度 + 严重度**便于分流，但**不确定项一律上抛给人，不静默丢**：

```
  置信高 → 直接采信，回流修 spec
  置信中 → 标"需人确认"，进 AskUserQuestion
  置信低 → 仍上抛（一行带过），绝不静默滤除
```

**与 sdflow-code-review 的置信过滤是有意的不对称**（与"代码即 ground truth 故 sdflow-code-review 去接地镜"同类）：

| | sdflow-code-review（代码） | sdflow-spec-review（设计） |
|---|---|---|
| finding 量 | 大（具体到行） | 小（设计级） |
| 单条漏掉的代价 | 低——CI/后续兜 | **高——设计洞会传导进实现** |
| 该优化 | 精度（少 nitpick） | **召回（别漏关键洞）** |
| 对不确定项 | **数值 <80 丢弃** | **标注 + 上抛，不丢** |

一个低置信的「这边界场景 spec 没覆盖」，在代码侧是 nitpick 该滤，在设计侧恰是**最该 surface 的高价值捕获**——故 sdflow-spec-review **不照搬数值一刀切**。它的"过滤"是第三步**对抗裁决**（强模型、带上下文，比 Haiku 数值打分更强）+ 第四步 **AskUserQuestion 上抛**，而非丢弃。

## 五、现有机制的分工（瘦身 / 保留 / 升格）

| 机制 | 独立性 | 处置 |
|------|--------|------|
| **brainstorming 自检**（占位/歧义/scope） | self | **退回生成期**——已被 config 吸收，review 阶段别重复 |
| **手写 checklist**（spec-quality/review-checklist） | self | 已 = `spec-checklists/`；review 只跑**命中 TG 的 R 项**，别全 BASE-01~28 逐条 |
| **强制画图** | self | 退化为「**验证**图存在/正确/未过时」，非重画（见 design-diagrams.md §五） |
| **广审双镜**（strategy/plan-eng，本 skill 自持 fresh 子代理，按 base R 项划分） | ✅ 独立 | **保留为主力**；覆盖 base 计划级 + 工程级 R 项（前提/范围/一致性/清晰度/ADR 决策/架构耦合/错误路径/NFR/安全…），火力集中 Validation + 判断，别再核对 config 已防的 T/S 项 |

净分工：**review 从"三套各自全量自检"收敛成"一条独立的、trigger 驱动的、专攻 Validation+对抗+接地 的链"**。机械项交给 config/lint，判断项交给独立 agent + 对抗。与生成侧三杠杆对称。

## 六、与体系其余部分的关系

- **生成/评审成对**：`generation-process.md`（Prevention 期对话）↔ 本文（Detection 期检查）。
- **不重复 prevention**：config.yaml 守的 T/S 项，review 不再逐条扫——这是 shift-left，不是放松。
- **复用 trigger-catalog**：review 深度按命中的 TG 决定，与约束/领域/画图/模版槽同源。
- **接地补 Accurate**：review 的读码核验，是 D-1（生成时）之外对 Accurate 的第二道（也是唯一的检查道）防线。

## 七、检查清单（做 spec review 时）

- [ ] review 是否由**独立上下文**做（非生成 spec 的同一 session）？
- [ ] 是否**读了真实代码**核验代码事实（而非只读 spec 自洽）？
- [ ] 是否做了**对抗式**追问（"证明它会炸"），而非只顺向打勾？
- [ ] 是否只审**命中 TG 的项**，没把 config 已防的 T/S 项重扫一遍？
- [ ] 命中 TG 的图是否验证了**正确性/未过时**（而非重画）？
- [ ] 每条 finding 是否标了**置信/严重度**，不确定项**上抛**而非静默丢（escalate-not-drop）？
- [ ] 发现的问题是否回流修正了 spec（而非只记录）？

*规则 v1 · 项目无关 · 配套 generation-process.md / trigger-catalog.md / spec-checklists/*
