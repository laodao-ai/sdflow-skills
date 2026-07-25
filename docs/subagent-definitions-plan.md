# subagent 的定义与调度（调研 + 实施方案）

> **本文不是 as-built 文档**，不属于 `docs/README.md` 的阅读路径。它记录的是 **sdflow 工作流工具链**的
> 一项待实现改进，与 mqtt-console 应用代码无关。放在 `docs/` 仅为便于查阅。
>
> **调研日期**：2026-07-25 · **状态**：方案已定，未实施
>
> **目标**：用合适的方式定义和调度 subagent，综合权衡**效率、质量、时间、token 成本**四个维度。

## 1. 权衡框架

四个维度不是并列的，它们两两之间有明确的换向关系：

| 维度 | 主要调节手段 | 与其他维度的冲突 |
|---|---|---|
| **质量** | 档位（model-tiers）· 镜的数量与多样性 · fresh context 独立性 | 与 token 成本、时间直接对冲 |
| **token 成本** | 档位下放 · effort 降档 · prompt 长度 · 镜数量 | 与质量对冲；与时间**不**对冲（并行不增 token） |
| **时间**（墙钟） | 并行度 · 往返次数 · 单次 effort | 与 token 成本基本正交——并行压缩墙钟但不省 token |
| **效率**（人的注意力） | 减少人门次数 · 报告可读性 · 降低误报率 | 与质量部分对冲（宁可多报，但多报耗人） |

**关键认识：时间和 token 成本是两个独立的旋钮。** 并行 fan-out 压缩墙钟但一分钱不省；
降档/降 effort 省 token 但不一定更快。当前额度紧张的约束下，**token 成本维的优先级高于时间维**。

**质量维不能整体让位。** `model-tiers.md` 铁律：带门禁、无人逐条复核的步 MUST NOT 降档——
假绿会放不完整的活过关。所以省 token 只能从非门禁步下手。

### 1.1 第五个变量：prompt cache

token 成本维内部还藏着一个不能只看「单轮花多少」的变量——**切换调节旋钮本身要付缓存重建的钱**。

`effort` 与 `model` 都是 **cache key 的一部分**：

| 变更 | Tools 缓存 | System 缓存 | Messages 缓存 |
|---|:---:|:---:|:---:|
| 模型切换 | ✘ | ✘ | ✘（**无 escape hatch**，缓存按模型隔离） |
| **effort 变更** | model-specific | model-specific | **✘ 必失效** |
| thinking 参数变更 | model-specific | model-specific | ✘ |
| `tool_choice` / 图片增删 | ✓ | ✓ | ✘ |

对一个长会话，Messages 缓存就是绝大部分——**effort 一切，实际等同整个前缀作废**。
代价量级：cache read = 基础输入价 **0.1x**，cache write = 1.25x（5 分钟 TTL）/ 2x（1 小时 TTL）。
一次切换 ≈ 把整个上下文按 **20 倍于缓存命中**的价格重算一遍，**上下文越长越贵**。

例外：**把 effort 显式设成该模型的默认值等价于不传，不触发失效**（Opus 5 默认 `high`，
所以「显式 high」与「不设」同 key；但 `high → medium` 是真切换）。

**⇒ 由此得出本文档最重要的一条结论**（见 §5、§6 的排序理由）：

> **子代理的 effort 是缓存中性的，主 session 的 effort 不是。**
> 子代理跑在 fresh context——本来就没有缓存可丢；主 session 每切一次付一次全前缀重写。

**「context 要不要重新加载」是另一回事，答案是不用。** 缓存在服务端，会话内容在 Claude Code 本地，
每轮本来就整份重发。缓存失效只影响**计费与计算**，不丢对话、不用重读文件、不等于 `/clear`。

## 2. 现状：sdflow 怎么定义和调度 subagent

### 2.1 定义方式

当前**没有** agent 定义文件（`~/.claude/agents/` 与 `.claude/agents/` 均为空）。
每个子代理由编排器在运行时拼 prompt，通过 Agent 工具派发，档位由
`resolve-models.sh` 按宿主机队解析后经 `model` 参数传入。

### 2.2 调度策略（已有机制）

| 机制 | 内容 | 出处 |
|---|---|---|
| **档位分层** | strong（终门/裁决）· mid（领域镜/对抗镜/实现）· light（接地镜/历史镜/commit） | `model-tiers.md` |
| **串行纪律 T20** | Step1 autoplan 必须 checkpoint 完成后才能 fan-out，**禁止与 Step2 并行**（多镜评审对象须含 autoplan amendment） | `sdflow-spec-review/SKILL.md:145` |
| **能力探针 + roster 降级** | fan-out 前先派 trivial 探针判子代理是否可用；不可用则缩 roster 到主 session 能独立完成的镜，报告显著标注「单镜降级」 | `sdflow-spec-review/SKILL.md:155-168` |
| **镜内并行** | Step2 的领域镜/对抗镜/接地镜并行 fan-out | `SKILL.md:143` |
| **度量锚** | 每轮落 `lens-metric` 锚，记录 roster 与 per-镜 findings（受 `metrics.enabled` 门控） | `SKILL.md:224` |

### 2.3 现存缺口

**① effort 无法按子代理控制。** 主 session 的 reasoning effort 被 fan-out 子代理继承，
调整是全局的——跑一轮 spec-review，主 session 和 5–8 个镜一起升降，
做不到「裁决用高档、机械镜用低档」。**这是「Agent 工具直接派」这条路径的限制**，
换用 agent 定义文件可解（§4.1 / §4.6）。

**② 四条通则的传播靠自觉，无机械保证。** `sdflow-spec-review/SKILL.md:192` 要求每个子代理
prompt 原文整段携带四条通则，但该 SKILL 自己承认这是**对主 session 的指令、非机械门**——
漏带无人拦截，而漏带的后果是确定的（冷上下文的镜必然把「现状能跑」当成「设计是对的」）。

**③ 无工具边界。** 接地镜、历史镜本应只读，当前没有任何机制阻止它们写文件。

**④ token 成本维无数据。** 见下节。

## 3. 度量能力：数据其实一直在落，但从没聚合过

这是本次调研最有行动价值的发现。

| 项 | 状态 |
|---|---|
| `openspec/config.yaml` 的 `metrics.enabled` | **`true`**（第 84-85 行）——lens-metric 锚一直在落 |
| `openspec/retro/` | **不存在**——`/sdflow-retro` 从未跑过 |

`sdflow-retro` 的职责正是「成本×价值复盘」：从 git 提交历史抽各 change 的**阶段墙钟**（成本维），
join 归档评审报告里的 **lens-metric 锚**（价值维），聚合出 per-change 明细、阶段占比、
成本双峰、**per-镜价值表**。它明确「只呈现不决策——砍镜/降采样/优先级永远人决」。

**⇒ 你已经积累了多个 change 的原始数据，只是从没看过聚合结果。**
在动任何手之前先跑一次 `/sdflow-retro`，能把「哪个镜真的出问题、哪个阶段真的费时间」
从推断变成实测。

**retro 覆盖不到的维度**：它有墙钟和价值，**没有 token 成本**。
token 维目前只能靠 `/usage` 的窗口百分比做前后对比，粒度粗（整数百分比），
且无法归因到具体镜。这是度量体系的真实空白。

## 4. 手段 A：用 agent 定义文件固化角色

### 4.1 三条路径的能力对比

**三条路径不是三选一。** ② 是**定义载体**，① ③ 是**调度路径**；② 与 ① 组合、② 与 ③ 组合都成立
（③ 通过 `agentType` 参数引用定义文件）。真正互斥的只有 ① 和 ③。

| | ① Agent 工具直接派（sdflow 现走这条） | ② agent 定义文件 | ③ Workflow 的 `agent()` |
|---|---|---|---|
| **本质** | 调度路径 | **定义载体** | 调度路径 |
| 角色描述在哪 | 每次调用现拼 prompt | `.claude/agents/*.md` frontmatter + 正文 | 每次调用现拼 prompt |
| 指定 model | ✅ 参数 | ✅ frontmatter（**优先级低于 ①③ 的参数**） | ✅ `opts.model` |
| **指定 effort** | ❌ **无此参数** | ✅ **`effort:`（已验证，见 §4.6）** | ✅ `opts.effort` |
| 限制工具集 | ❌ | ✅ `tools:`，**还能限制可派的子代理** | ❌（继承定义或默认） |
| 控制流 | 模型自己决定派谁、派几个 | — | **确定性 JS 脚本**（循环 / 条件 / fan-out） |
| 结构化返回 | ❌ 只有文本 | — | ✅ `schema:` 强制校验 + 自动重试 |
| 可续聊 | ✅ `SendMessage` 带上下文续跑 | — | ❌ 一次性 |
| 断点续跑 | ❌ | — | ✅ `resumeFromRunId`，未变前缀命中缓存 |
| **触发门槛** | 随时 | — | **需用户显式授权** |
| Codex 宿主有对应物 | ✅ | ❌ | ❌ |

**逐条的硬限制**：

- **①** 没有 effort 参数（子代理继承 session effort，出自 Workflow 文档的
  `omit to inherit the session effort`）；返回值只有文本，跑偏无重试；fan-out 数量与时机由模型判断。
- **②** **Claude 宿主专有，Codex 没有对应物**——`host-adaptive-execution` 要求两边可对齐，
  Codex 分支必须保留现有的 prompt 内联通则路径，等于维护两套。定义本身不能被调度，必须靠 ① 或 ③ 启动。
- **③** **需用户显式授权才能调用**（"ultracode" / 明确要求跑 workflow / skill 指令里写了）。
  **这是 ③ 不采纳的首要理由——一个要能自动跑的评审编排器不能建在需要每次人工开闸的机制上**，
  「重写成本大」是次要的。另有：并发上限 `min(16, 核数-2)`、单次 fan-out ≤4096 项、
  单 workflow 全生命周期 ≤1000 agent、嵌套仅一层、脚本内无文件系统与 `Date.now()`。

### 4.2 关键发现：档位机制与 agent 定义不冲突

初看是撞车的：sdflow 明令 **「MUST NOT 内联具体模型 id」**（`sdflow-spec-review/SKILL.md:292`，
因为档位须按宿主机队经 `resolve-models.sh` 解析），而 agent 定义的 `model:` 恰恰是静态写死的。

但 Agent 工具的 `model` 参数说明写着：**「Takes precedence over the agent definition's model
frontmatter」**——调用时传入的 model **覆盖** frontmatter。

**⇒ 正确姿势**：agent 定义**不写 `model`**，或写 **`model: inherit`**——后者是官方插件的实际写法
（全机 21 处实例）。编排器照旧传 `$SDFLOW_TIER_STRONG` / `$SDFLOW_TIER_MID` / `$SDFLOW_TIER_LIGHT`。
档位机制原封不动，同时白拿 agent 定义的其余能力。

### 4.3 角色清单与适配度

| 角色 | 出处 | 档位 | 工具边界 | 适配度 | 说明 |
|---|---|---|---|---|---|
| **接地镜** | spec-review | light | 只读 | **最高** | 纯 grep/读码核验，职责恒定，工具边界最清晰 |
| **历史镜** | code-review | light | 只读 + git | **最高** | 同上 |
| **commit** | done | light | git | 高 | 纯机械 |
| 领域镜 | spec/code-review | mid | 只读 | 高 | 恒定部分 = 通则 + 评审纪律 + 报告格式；变的只是领域与 change |
| 对抗镜 | spec/code-review | mid | 只读 | 高 | 同上 |
| verify | done | **strong** | 只读 + 跑测试 | 中 | 恒定部分 = 反假绿纪律、证据锚要求；但它是唯一终门，改动需谨慎 |
| implementer | implement | mid | 读写 | 中 | 恒定部分 = TDD 纪律 + Global Constraints |
| 冷走查 | architecture | **strong** | 只读 | 中 | 场景×子系统×contract 矩阵，结构稳定 |
| archive | done | mid | 读写 | 低 | 步骤性强，固化收益小 |
| outside-voice fallback | spec/code-review | — | — | 不适用 | 走 `outside-voice.sh` helper，不经 Agent 工具 |

**动态 prompt 不是障碍**——agent 定义固化的是角色恒定部分（人格、纪律、工具边界），
调用时的 `prompt` 参数照常传本次任务内容。

### 4.4 四维收益

| 收益 | 维度 |
|---|---|
| 传播纪律从「指令」变成「机制」，消除 §2.3② 的无保证缺口 | **质量** |
| tools 白名单防越权（接地镜不能写文件） | **质量** |
| **可派子代理的白名单**（见下） | **质量 + token 成本** |
| 每个子代理 prompt 少塞一份四条通则 × 5–8 镜 × 每轮 | **token 成本** |
| effort 可按角色固化（**已验证可行**，§4.6） | **token 成本 + 时间** |
| **且该 effort 是缓存中性的**——子代理 fresh context，无缓存可丢；主 session 切 effort 则每次全前缀重写（§1.1） | **token 成本** |

**`tools:` 的粒度比「读 / 写」更细**——条目可带作用域参数，限制该子代理**能再派哪些子代理**：

```yaml
tools: Read, Glob, Grep, Bash, Edit, Write, Agent(claude-security:explore)
```

含义是「可以再派子代理，但只能派 `explore` 这一个」（同理还有 `Workflow(plugin:name)`）。
对 sdflow 的直接价值：**领域镜可被授权只派接地镜、不能派别的**——当前的 prompt 纪律完全做不到这条硬约束。

### 4.5 代价与风险

**① 新增漂移面（最重要）。** sdflow 以「四条通则单一源 + `sync_principles.py` 机械同步 +
`hack/tests/test_sync_principles.py` 守漂移」为设计。把通则写进 agent 定义等于新增投放面，
**必须同步纳入 `sync_principles.py` 的 `PROJECT_TARGETS`**，否则正是它一直在防的那个问题。

相关约束：`test_sync_principles.py:46` 的 `HEADLINES` 机械守四个子串——
`能查的自己查` / `先调研再给推荐` / `MUST NOT 拿现状反驳目标` / `方案尽量简化`。

**② 双宿主不对等。** `.claude/agents/` 是 Claude 宿主机制，Codex 宿主没有对应物。
sdflow 的 `host-adaptive-execution` 要求两边行为可对齐，需在 Codex 分支保留现有的
「prompt 内联通则」路径。

### 4.6 effort 字段与完整 frontmatter

**字段名就叫 `effort:`，取值同 effort 阶梯 `low` / `medium` / `high` / `xhigh` / `max`。**

证据：`claude-security` 官方插件的 **7 个** agent 定义全部使用该字段，路径
`~/.claude/plugins/marketplaces/claude-plugins-official/plugins/claude-security/agents/`：

```yaml
# scan-inventory.md
name: scan-inventory
description: Restricted read-only repository cartographer...
model: sonnet
effort: medium          # ← 字段名与取值
color: green
tools: Read, Glob, Grep
```

其余六个用 `effort: xhigh`。同一批文件同时证实 `model: inherit` 是合法值（即 §4.2 的推荐写法）。

**完整可用的 frontmatter 字段**（同批实测）：`name` · `description` · `model`（含 `inherit`）·
`effort` · `color` · `tools`（支持作用域参数）· `initialPrompt`。

> **查实例去 `~/.claude/plugins/marketplaces/`**——`~/.claude/agents/`、`.claude/agents/`
> 与 `~/.claude/plugins/cache/` 里都没有，只查前三处会误判为「本机零实例」。

## 5. 手段 B：调度参数（无需改定义即可调）

这些是**当前就能调**的旋钮，**改造**成本远低于手段 A（但见下文：改造成本 ≠ 运行成本）：

| 旋钮 | 影响维度 | 现状 | 可调方向 |
|---|---|---|---|
| **主 session effort** | token 成本 ↔ 质量 | 全局 high | 按**阶段**切：评审轮 high、实现轮 medium、机械活 low。两条注意：① 连带影响所有子代理（该连带由手段 A 解除，§4.6）② **每切一次清空缓存**（§1.1） |
| **镜的数量（roster）** | 质量 ↔ token 成本 | 按 TG 命中 + 风险升档 | 低风险 change 缩 roster；高风险保持。**缓存中性** |
| **档位映射** | 质量 ↔ token 成本 | strong=opus / mid=sonnet / light=haiku | 门禁步 MUST NOT 降；mid 可试 haiku 但风险自负。**只影响子代理，缓存中性** |
| **并行度** | 时间（不影响 token） | Step2 内并行 | 已并行，无优化空间；T20 禁止 Step1/Step2 并行是质量约束，不可破 |

**主 session effort 不是「零成本」旋钮。** 改造成本为零、立即生效不假，但**运行时每切一次
付一次全前缀重写**（§1.1）。在同一个长会话里按阶段来回切，省下的 token 可能被缓存重建吃掉甚至倒亏——
**会话越长，越容易倒亏**。

⇒ 主 session effort 的正确用法是**开会话时定好、整场不动**；「按阶段用不同 effort」这个目标
应当由**手段 A 的 per-agent effort** 实现，而不是靠主 session 来回切。

另注两条与缓存无关的限制：effort **不是**控制输出长度的杠杆（官方明确：Opus 5 上降 effort
不可靠地缩短可见输出），也不减轻 scope expansion。

> **同类提醒：切模型比切 effort 更贵。** 模型切换清空全部三层缓存且**没有任何 escape hatch**
> （缓存按模型隔离）。「切 Fable 5 跑一轮再切回」是两次全前缀重写——**在新会话里切，
> 不要在跑了很久的会话中途切**。

## 6. 实施路线

### 第 0 步：先拿基线（**做任何改动之前**）

1. 跑 `/sdflow-retro`，生成 `openspec/retro/report.md`——拿到 per-镜价值表与阶段墙钟
2. 记录当前 `/usage` 的周窗口百分比，作为 token 基线

**没有基线，后续任何调整都无法判断是改好了还是改坏了。** 数据已经在归档报告里躺着，
跑一次就有。

### 第 1 期：调度参数中**缓存中性**的那几个（零改造）

按 §5 调 **roster 规模**与**档位映射**——这两个只作用于子代理，不碰主 session 前缀，缓存中性。
跑 1–2 个完整 change，对比 retro 报告与 usage 消耗。这一期不动任何代码，可随时回退。

**主 session effort 的阶段切换不在本期**——§1.1 表明它每切一次付一次全前缀重写，
在长会话里可能倒亏。本期只做一件与 effort 有关的事：**开会话时把 effort 定好，整场不动**，
观察不同 change 之间用不同固定值的效果（跨会话变，不在会话内变）。

### 第 2 期：agent 定义试点（**per-agent effort 的唯一无损路径**）

**只做接地镜和历史镜两个**：

- light 档、纯只读，`tools` 白名单收益最直接
- 职责最恒定，写完基本不用改
- 不碰门禁步（verify）与写操作（implementer），出问题不会伤到代码

写法照抄 §4.6 的样例：`model: inherit` + `effort: low`（机械核验不需要高档推理）+
`tools: Read, Glob, Grep, Bash`。唯一要观察的是「降 effort 后接地镜的核验质量是否退化」——
跑一轮看报告判断。

**这一期是「按角色用不同 effort」这个目标的唯一无损实现路径**——子代理是 fresh context，
给它设低 effort 既不影响主 session 的 effort、也不触碰主 session 的缓存（§1.1）。
主 session 来回切 effort 达不到同样效果，还要额外付缓存重建的钱。

### 第 3 期：推广（第 2 期跑顺后）

推广到领域镜 / 对抗镜。此时**必须一并完成** `sync_principles.py` 的改造——
把 agent 定义纳入投放面，让 `test_sync_principles.py` 守住漂移。

### 暂不纳入

- **verify**：唯一终门，铁律禁降档，机制未充分验证前不动
- **implementer / archive**：涉及写操作，风险不对称
- **Workflow 重写**：首要理由是 **Workflow 需用户每次显式授权**，自动跑的编排器不能建在人工开闸的机制上
  （§4.1）；重写成本大是次要理由

## 7. 未决问题

**agent 定义放本仓 `.claude/agents/` 还是全局 `~/.claude/agents/`？**

sdflow 是跨项目分发的 skill，放全局才能让所有项目受益；但放全局会影响全部项目，
且与「sdflow bundle 由 `sdflow-init` 铺设」的分发模型不一致。

倾向：**先放本仓验证**，跑顺后再考虑上提到全局，或纳入 `sdflow-init` 的铺设物。

## 8. 事实来源标注

| 结论 | 性质 |
|---|---|
| Agent 工具参数表无 effort | 实测（工具定义） |
| Agent 工具 `model` 参数覆盖 frontmatter | 实测（工具文档原文） |
| 子代理继承 session effort | 实测（Workflow 工具文档原文） |
| **effort frontmatter 字段名 = `effort`，取值 low…max** | **实测**（`~/.claude/plugins/marketplaces/claude-plugins-official/plugins/claude-security/agents/*.md`，7 实例） |
| `model: inherit` 是合法值 | 实测（同上，全机 21 处） |
| `tools:` 支持 `Agent(plugin:name)` 作用域参数 | 实测（`patch-generator.md` 等） |
| Workflow `agent()` 可经 `agentType` 引用 agent 定义 | 实测（`claude-security/workflows/scan.js`） |
| Workflow 需用户显式授权、并发与规模上限 | 实测（Workflow 工具文档原文） |
| **effort / model 是 cache key，切换即失效**；显式设为默认值不失效 | **实测**（`platform.claude.com/docs/en/build-with-claude/effort.md` §Changing effort mid-conversation + Best practices 5；prompt-caching 文档失效表） |
| cache read 0.1x / cache write 1.25x（5min）· 2x（1h） | 实测（官方定价） |
| 子代理 effort 缓存中性 | **推断**，基于「子代理 fresh context 无既有缓存」+「主 session 与子代理是独立请求前缀」；未实测 |
| 本仓 `metrics.enabled: true`、`openspec/retro/` 不存在 | 实测（`openspec/config.yaml:84-85`、目录检查） |
| sdflow 角色清单、档位映射、T20 串行纪律、roster 降级 | 实测（各 SKILL.md、`model-tiers.md`） |
| 「省 token」的具体量 | **未测**，无前后对比 |
| 「时间与 token 成本正交」 | **推断**，基于并行不改变总 token 量；未实测 |
