# 0023 · fan-out 能力探测 = **语义核验 + always-on 一致性 lint**（非机械下限）

> 状态：**Proposed**（2026-07-15 grill 立、**同日 spec-review 冷层降格**）——待该 change ship + Codex 宿主真机核验后升 Accepted。
> **⚠️ 修订史（DOC-1 例外：此处保留是因为『机械 vs 语义』的两次误判本身即本 ADR 的核心教训）**：grill 初稿定"探针=机械下限"；spec-review 冷层（4 镜 + codex voice）纠正——**「有信号」≠「有可机械捕获路径」**，探针经被监管方（主 session）自报、无可信脚本捕获，落在 §0.0「防伪」一侧 ⇒ **降格为语义核验 + always-on 一致性 lint**。标题与下文按降格后表述。
> 关联：`openspec/changes/add-codex-host-support/design.md` ADR-4（本 ADR 是对其切分线的修正）· `docs/sad/07` §0.0（机械层防漏不防伪）· `adr/0021`（核心承诺无机械兜底——本 ADR 是其**对偶**：那里信号不存在故不兜，这里信号存在故必兜）· `adr/0018`（机械校验器输出诚实）· CONTEXT「假✅」「机队锚定」。

## Context

`add-codex-host-support` 的**头号假绿**（proposal Why #2）：Codex 宿主默认不派子代理，于是多镜 fan-out **静默不发生**，主 session 自己把各镜的活干一遍，而 lens-metric 锚仍按 roster 逐镜落——**报告 7 镜、实跑 1 镜，独立率全是自己给自己打的分。**

设计初稿（design ADR-4）按 §0.0 自检「信号从哪来」，答「没有」，于是把整件事归语义层：靠 SKILL 指令缩 roster + 人读报告 + 事后 host 分组的独立率异常兜。

grill（2026-07-15）指出这条切分线**画错了位置**：它把两件不同的事混成一件——

1. **「第 N 面镜到底跑没跑」**——确实无确定性信号。主 session 是 agent session 里的唯一执行者，它可以声称「对抗镜 2 独立跑过」而实际自己顺手写了。**这一半归语义层是对的**（与 `adr/0021` 同构）。
2. **「这个 session 的 fan-out 机制到底还活着没有」**——**有**确定性信号。派一个 trivial 探针子代理、看它回不回哨兵值，就是「让工具自己回答」（基准 5）。Codex 宿主未授权 ⇒ 探针不回 ⇒ 机制死。

头号假绿的成因是 **(2)**（机制整个不工作），不是 **(1)**（某面镜说谎）。initoc 把 (2) 有信号的一半也推给了语义层，等于放走了本可机械设防的地板。

## Decision

**把切分线重画在 (1)/(2) 之间：机制活着没 = 机械下限，第 N 镜跑没跑 = 残余语义。**

1. **探针（let the tool answer）**：fan-out 前，主 session 派一个 trivial 探针子代理，回哨兵值 = 能力可用。`host=claude` ⇒ 恒可用（Task tool 是 Claude Code 核心，免探针）；`host=codex` ⇒ **MUST 探**（授权与否决定成败）；`host=unknown` ⇒ 不 fan-out。
2. **落锚**：探针结果落一行会话级锚 `<!-- sdflow:fanout-capability v1 host="…" subagents="available|unavailable" -->`，每轮评审一行。
3. **always-on 一致性 lint（拦自相矛盾，非拦伪造）**：`anchor_lint` 拦**锚行自身矛盾**——`subagents="unavailable"` 却出现 >1 个 **fan-out 镜行**（去重键**钉死按 `lens`**，`lens ∈ {domain, adversarial, grounding}`）。它拦的是**诚实的记录错误 / 自相矛盾**，**不是伪造**——决心谎报的主 session 写 `subagents="available"` 即绕过（无机械交叉核验）。此校验 **MUST always-on、与 `metrics.enabled` 解耦**（它读真实性信号、非价值度量；否则默认消费仓 metrics=false 时空转）；`host=codex` 报告里 fanout-capability 锚**必须在场**（缺锚不得绕过）。
4. **头号假绿的覆盖，诚实限定**：一致性 lint 只拦**「机制死变体」**（`unavailable` 却报多镜）。**「机制活 + 偷懒自代变体」**（`available` 但主 session 自代多镜、同症状）**无机械守、留语义层**。目标态下 `available` 是常态 ⇒ 后者才是活风险 ⇒ **MUST NOT 声称"头号假绿已事前拦截"**。

## 为何这样（判据，spec-review 冷层纠正后）

- **「有信号」≠「有可机械捕获路径」**：§0.0 的「让工具自己回答」（如 `make -n` 看 exit code）之所以机械，是**可信 shell 脚本**去捕获、被测方碰不到。fan-out 探针只能由**主 session（LLM）**去 spawn、观察、写锚——`anchor_lint` 读那行锚**无从核验它对应一次真 spawn**。∴ 探针结果经**被监管方自报**到达校验层，落在 §0.0「防伪」一侧，**不是机械门**。
- **内部矛盾（迫使降格）**：ADR-1 已承认 `host=` 可伪造、划为信任边界（host 还有 shell 源）；信号**更弱**的 `subagents=`（纯 LLM 观察、无 shell 源）没理由反而配得上机械门。同一把 §0.0 尺不能量出相反归属。
- **与 `adr/0021` 同源**：`0021`（devenv 核心承诺无机械兜底）说的正是——**一个"看起来像机械"的外壳（sha256 / 探针哨兵）不能让本质自报的信号变成机械门。** 本 ADR 是同一课的第二次。

## 代价（如实记）

- **一致性 lint 只拦「机制死的自相矛盾」**——机制活时的逐镜自代仍无机械守（残余语义层）。G1 因此比 grill 初判弱（从"事前机械拦截头号假绿"缩为"拦机制死变体 + 事后可发现"）。**诚实登记，不夸大。**
- 每轮 Codex 宿主评审多一个探针子代理（廉价、单轮）+ 语义核验价值。Claude 宿主免探针。
- `anchor_lint` 多读一类锚 + 一条 always-on 一致性校验；测试 +1 组。

## 被否方案

- **全归语义层（design ADR-4 grill 前初稿）**：放走了「机制死的自相矛盾」这个**真·可机械判**的一致性面（锚自身矛盾无需捕获真 spawn 即可判），一致性 lint 值得保留。
- **把探针当机械下限（grill 初稿）**：误把「有信号」当「有机械门」，忽略捕获环节由被监管方把持——即本 ADR 降格的原因。
- **给每面镜设「真跑过」机械证**：需要不存在的信号，硬造即假绿（同 `adr/0021`）。**MUST NOT。**
