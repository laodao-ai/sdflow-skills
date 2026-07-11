# 自制 skill 展开 · `grill-with-docs`

> 属 [工作流总览](../workflow-overview.md) 的展开。这是**阶段一生成的「人类对话岛」**（第 3 步）——
> 对抗压测设计、对齐术语、边界场景、代码与主张不符即揭穿；落 ADR / 术语表。
>
> **一句话**：`Interview me relentlessly about every aspect of this plan until we reach a shared understanding.`
> 逐分支死磕设计树，一次一题、等反馈再下一题；能查码就查码。

> **本文与前 7 份的最大不同**：grill **是一种 stance（姿态），不是机械流程**——没有固定步骤、没有必产物、没有门禁脚本。
> 因此它的「建议式 vs 强制」几乎**全是建议式**：它的严谨性由**人类亲自拷问**保证，由**下游设计门**兜底。

---

## 1. 位置与契约

| 维度 | 内容 |
|---|---|
| 谁调它 | 阶段一第 3 步（`opsx:ff` 生成四件套之后、设计审之前），非平凡变更 |
| 进（输入） | `{change_dir}` 的 design.md（+ proposal/specs/tasks）+ 真实代码（`sdflow-ship/scripts/ship_gate.py` 等） |
| 出（产物） | design/ADR/CONTEXT 更新（标 `[grill-amendment]`）；`docs/adr/NNNN-*.md`（按需）；`CONTEXT.md` 术语表（按需，lazily） |
| 本性 | **人类对话岛**——人对着设计死磕，不折叠、不自动化 |
| 收敛 | **收敛后才 checkpoint**（多轮中途不提交，只收敛后一次） |
| 组成 | **薄包装** = `/grilling`（拷问引擎）+ `/domain-modeling`（落 ADR/术语）——SKILL.md 仅一句 `Run a /grilling session, using the /domain-modeling skill`（拆解见 §7.1） |
| 调用约束 | `disable-model-invocation: true`——**模型不能自调，只能人 `/grill-with-docs` 触发**；这正是 grill 常被静默跳过的机械根因（§7.2） |

> **grill 不可轻跳**：grill 是对 explore 的二次审视；「跳过类判定」别埋进长消息里——须显著呈现（见记忆 [[grill-not-skippable]]）。

---

## 2. 内部「流程」（其实是一套姿态 + 触发反应）

grill 没有 Step1/2/3。它是一个**循环对话** + 若干**触发即反应**的动作：

```mermaid
flowchart TD
    Q["提一个问题（一次一题）"] --> W{"能查码回答?"}
    W -->|能| CODE["查代码回答（不空问）"]
    W -->|不能| A["等人类反馈"]
    CODE --> A
    A --> R{"对话中触发了什么?"}
    R -->|术语与 glossary 冲突| G1["立即揭穿：你的 glossary 定义 X，你却像在说 Y"]
    R -->|用词模糊/重载| G2["提出精确的规范术语（account = Customer 还是 User?）"]
    R -->|讨论领域关系| G3["用具体场景压测边界"]
    R -->|主张与代码不符| G4["交叉引用揭穿矛盾"]
    R -->|某术语已解决| G5["就地更新 CONTEXT.md（不批量）"]
    R -->|难逆+意外+真权衡 三者全真| G6["提议落一个 ADR（否则跳过）"]
    G1 --> NEXT["下一分支"]
    G2 --> NEXT
    G3 --> NEXT
    G4 --> NEXT
    G5 --> NEXT
    G6 --> NEXT
    NEXT --> Q
    NEXT -.收敛.-> CONV["达成共识 → checkpoint（一次）+ 标 [grill-amendment]"]
```

| 姿态/动作 | 目标 | 注意事项 |
|---|---|---|
| 一次一题 | 逐分支死磕、解依赖 | 每题给出推荐答案；**等反馈再下一题**，别一次抛一堆 |
| 能查码就查码 | 主张落到代码 ground truth | 别拿能查的东西空问用户 |
| Challenge against glossary | 术语一致 | 与 `CONTEXT.md` 已有定义冲突 → **立即揭穿** |
| Sharpen fuzzy language | 消除模糊/重载词 | 提精确规范术语（account→Customer/User） |
| Concrete scenarios | 压测领域关系边界 | 造 edge-case 场景逼精确 |
| Cross-reference code | 揭穿主张与代码矛盾 | 「你的代码取消整个 Order，但你刚说支持部分取消——哪个对？」 |
| Update CONTEXT.md inline | 术语解决即记 | **不批量**；CONTEXT.md 是**纯术语表**，禁塞实现细节/spec/scratch |
| Offer ADRs sparingly | 记「为什么」 | **三门槛全真才落**：① 难逆 ② 无背景会困惑 ③ 真权衡；缺一即跳 |

---

## 3. 产物格式（两个 lazily 创建的文档）

| 文档 | 是什么 | 关键规则 |
|---|---|---|
| `CONTEXT.md`（多 context 用 `CONTEXT-MAP.md`） | **术语表 glossary，仅此** | 有意见（多词选最佳、其余列 alias 避免）、显式 flag 冲突、定义一句话（定义 IS 不是 does）、只收本 context 特有术语（通用编程概念不收）、写示例对话 |
| `docs/adr/NNNN-slug.md` | 决策记录 | 顺序编号、可单段、价值在记「**做了什么决定 + 为什么**」；三门槛才落；lazily 建目录 |

---

## 4. 内部调度

grill **不派子代理、不调脚本**（对话岛，主 session 直接与人对话）。它只**读**真实代码（查码揭穿矛盾）、**写** design/ADR/CONTEXT，收敛后调 `checkpoint-commit.sh grill`。这是它与其他 7 份 skill 的结构性差异：**零 fan-out、零机械门**。

---

## 5. 人类门

**整个 grill 就是人类**——它不是「停一次的门」，而是**人类深度参与的持续对话**。唯一自动化收尾是收敛后的一次 checkpoint。在 workflow 里，grill 与设计 HARD-GATE 是**两个不同的人类接触点**：grill 是「人对抗设计」（生成阶段、不折叠），设计门是「人过报告拍板」（评审阶段、唯一 HARD-GATE）。

---

## 6. ★ 本 workflow 注入的规则/prompt —— 建议式 vs 强制

**统一判据**见[总览 §8](../workflow-overview.md#8-外部-skill-的注入强制性建议式-vs-强制统一规律)。grill 几乎**全建议式**——它没有锚行自检、没有 ship-gate 锚、没有产物 schema。它的「强制性」来自**人类在场**和**下游门**，不来自自身机制。

| 项 | 类型 | 靠什么 |
|---|---|---|
| 收敛后 checkpoint + 标 `[grill-amendment]` | **半强制** | `checkpoint-commit.sh` 脚本提交（机械）；但「收敛了没/该不该提交」靠判断 |
| **ADR 三门槛**（难逆+意外+真权衡） | **建议式（判据纪律）** | 无脚本校验；靠模型遵从「三者全真才落」，防 ADR 泛滥 |
| **CONTEXT.md 纯术语表**（禁塞实现） | **建议式** | 无 schema 校验；靠遵从格式规则 |
| 「一次一题 / 能查码就查码 / 揭穿矛盾」 | **建议式（姿态）** | 纯 stance，靠模型 + 人类共同维持 |
| **grill 不可轻跳** | **建议式（须显著呈现）** | 无机制阻止跳过；靠「跳过判定别埋长消息、显著呈现」纪律 + 用户把关（记忆 [[grill-not-skippable]]） |
| grill 的**设计严谨性**整体 | **下游门兜底** | grill 漏挖的设计缺陷，由下游 [`sdflow-spec-review`](./sdflow-spec-review.md) 的对抗镜/接地镜/outside-voice 捕获——设计门是真正的 HARD-GATE |

**结论**：grill 是全流程**唯一刻意「不机械化」的步**——因为它的价值恰在**人类对抗的判断力**，机械门会杀死对话的开放性。它的产物（更硬的 design + ADR + 术语表）没有锚/门保证质量；保证来自两处：**① 人类亲自死磕**（grill 不可轻跳，须显著呈现跳过判定）；**② 下游 sdflow-spec-review 设计门审计** grill 收敛后的设计（对抗镜专证「这份 spec 会在实现期爆炸」）。即 **grill 建议式，设计门强制**——这与「注入处建议式、下游门处强制」是同一条规律，只是这里「注入」换成了「人类对话的严谨度」。

---

## 7. 组成 · 调用约束 · 提示词模版 · 落档路径（2026-07-11 调研补记）

### 7.1 组成拆解——薄包装 = grilling + domain-modeling

grill-with-docs 的 SKILL.md 只有一句：`Run a /grilling session, using the /domain-modeling skill`。即它本身零逻辑，是两个 skill 的薄包装：

| 内包 skill | 管什么 | 本文哪些规则来自它 |
|---|---|---|
| `/grilling`（拷问引擎） | relentless 逐分支走设计树、**一次一题**、每题给推荐、facts 查码 / decisions 抛人、未达共识不 enact | §2 的「一次一题 / 能查码就查码 / cross-reference code」 |
| `/domain-modeling`（落档） | challenge glossary / sharpen fuzzy / concrete scenarios / update CONTEXT.md inline / **ADR 三门槛** | §2-3 的术语表 + ADR 规则 |

> 拆开的用处：判「改哪条规则动哪个 skill」——改拷问节奏 → grilling；改落档格式 / 路径 → domain-modeling。

### 7.2 调用约束 = 静默跳过的机械根因（→ todolist T132 门）

grill-with-docs frontmatter `disable-model-invocation: true`：**模型调不动它**（Skill tool 直接拒），唯一入口是人手动 `/grill-with-docs`。这解释了「grill 常被静默跳过、要人手动触发」（记忆 [[grill-not-skippable]]）——不是模型偷懒，是机制上模型只能「提示人去触发」，那句提示一漏 grill 就没了。

- **治法**（T132，属 mechanical-layer-hardening）：`sdflow-spec-review` 起手加 **fail-closed 门**，机械核验「grill 已收敛」信号（`workflow.md:83` 强制的 grill checkpoint-commit，或 design.md 内补 `<!-- sdflow:grill-done -->` 锚），无信号 → `REFUSE_START` 提示先跑 grill。grill 本身不能自动跑，但「跑没跑」可机械断言——同 `ship_gate` 设计门新鲜度先例，把判断从模型记性挪到脚本。

### 7.3 提示词：校准 + 模版化（→ todolist T133）

主 session 提示人跑 grill 时须附**完整可复制 prompt**（T28），且**已半模版化**——`workflow.md:83` 有一条带 `{change dir}` 占位的 grill 模版。但那条是**校准前的重版**，需按下述校准：

**给什么（脚手架，非 grilling / config 自带）**：靶子 change dir、`[grill-amendment]` 标注、落档路径重定向（§7.4）、一个 `{非绑定怀疑点}` 模型填槽（本 change 特有、至多一句）。

**不给什么（会短路 grill）**：预装的、已分析好的弱点清单 + 推荐。grilling 的价值 = **独立穷尽走完整棵树、逮你没想到的盲点**；喂它你的弱点地图 = anchor 效应 + 让它只 validate 你的结论而非发现第 N+1 条。「一次一题 / facts 查码 / decisions 抛人 / 揭穿矛盾」等**别写进 prompt**——grilling / domain-modeling 自带，写 = 冗余（`workflow.md:83` 现版正夹着这些冗余项，待删）。

> **「做成模版自动生成？」**——是，但边界要清：模版由**静态脚手架**（change dir 占位 + `[grill-amendment]` + 路径重定向）+ **一个模型填槽**（`{非绑定怀疑点}`）组成。change dir 可机械填；怀疑点是**本 change 的接地判断，非机械可填**——模版给槽、模型在 emit 时填。故是「模版 + 一个判断槽」，非全确定性生成。T132 门 REFUSE 时按同一模版 emit。落地 = 把 `workflow.md:83` 那条校准（删冗余自带项 + 加 `{非绑定怀疑点}` 槽），workflow 与 gate 共用这一份单一源。

### 7.4 落档路径：domain-modeling 硬编码根 `docs/adr/`（→ todolist T134）

`domain-modeling` 裸 SKILL.md 硬编码根 `CONTEXT.md` + `docs/adr/`，**不读** `openspec/matt/domain.md`（`setup-matt-pocock-skills` 写的路径配置，详见 [该文档](./setup-matt-pocock-skills.md) §5 脆弱点 #4）。本仓靠 CLAUDE.md `## Agent skills` 块（`openspec/CONTEXT.md` + `openspec/adr/`）覆盖赢这场冲突——但 skill-local 硬编码是强 pull，脆。

- generation-process §六 的「复用前先对齐路径」= `setup-matt-pocock-skills` 已在 **config 层**做完（`openspec/matt/domain.md` + CLAUDE.md 块），理应 config 层管、prompt 不必重复。
- 但未硬化前（T134：让 domain-modeling domain.md-aware），grill prompt / `workflow.md:83` 模版**保留** `ADR→openspec/adr/、勿建根 docs/adr/` 作 belt-and-suspenders（几字换掉冲突风险；属脚手架非分析 seed，不违 §7.3 校准）。

---

## 8. 小结

- grill = **人类对话岛**：一次一题死磕设计、对齐术语、查码揭穿、按需落 ADR/术语表。
- **零 fan-out、零机械门**——刻意不机械化，保对话开放性。
- **几乎全建议式**；严谨性靠**人类在场**（不可轻跳）+ **下游设计门审计**兜底，与总览 §8 同一规律。
- **薄包装** = grilling + domain-modeling；`disable-model-invocation` 使它只能人触发 → 静默跳过的机械根因 → 治法是 spec-review 起手 fail-closed 门（T132）。提示词模版化落 `workflow.md:83`（校准：脚手架 + `{非绑定怀疑点}` 槽，删 grilling 自带冗余，T133）；落档路径靠 setup 的 config 层对齐 + belt-and-suspenders 重定向（T134）。
