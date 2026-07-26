# add-sdflow-spec · 设计评审报告（阶段二）

> 评审对象盘面：`7f221c9`（四件套 = ff 初稿 `bd6601e` + grill 5 问收敛 `7f221c9`）
> 评审执行：`/sdflow-spec-review` 一次连续跑 · 主 session = Opus（强档）· host=claude · 双声全开无降级

---

## 收敛口（先看这段）

**建议：不进设计 HARD-GATE，先处理下方 5 条 `致` 级 finding。**

理由不是「设计写得不好」——四件套的结构完整度、追溯完备性、诚实边界纪律都在本仓平均线之上（详见文末「核过无问题」段，18 项）。**问题集中在两类**：

1. **三条当场可验证的事实错误**（F-01 `agentType` 参数名 / F-02 与 canonical 规则冲突 / F-03 `status` 语义误读）——不是取舍分歧，是打开文件就能核的硬伤，且每一条都会让某个承重机制**从第一天起就静默失效**。
2. **一个内部自相矛盾**（F-04：`proposal.md:28` 自认「非机械保证」vs `design.md:94`「跳过风险结构性消灭」）——同一份设计里，核心价值主张的强度前后不一致。

**六镜 + 双声高度收敛**：CEO/Eng/DX 三相位各自的 6 维一致性表，**共 18 维中 14 维 CONFIRMED 为负、零 DISAGREE**。这个收敛度在本仓评审史上属高位。

---

## 决策登记区

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │ [需拍板]  Q1  本 change 要不要拆分？（两个模型的 User Challenge）       │
  │ [需拍板]  Q2  `/clear` 出口序列 vs workflow.md G1，三选一               │
  │ [需拍板]  Q3  agent 定义分发层级：全局 vs 随 skill 目录                 │
  │ [需拍板]  Q4  决策纪要承载力存疑 —— 要不要先做 A/B 实测再定 D2          │
  │ [自动决策] D1-D7  autoplan 相位裁决（见下）                            │
  │ [已裁掉]  X1-X3  reviewer 原始发现 + 裁掉理由（可审计，不静默丢）        │
  └──────────────────────────────────────────────────────────────────────┘
```

### 🔴 Q1 —— 本 change 要不要拆分？（**User Challenge**：两个模型都反对当前 scope）

- **你定的**：一个 change 交付 `sdflow-spec` 完整管线（skill 本体 + 2 个 agent 定义 + setup 铺设 + sync 投放面 + 文档改写）。
- **Codex 与 Claude 独立收敛到几乎相同的拆分建议**：
  ① **可靠性 change**（拷问前移 + 结构化 memo + canonical 规则更新 + spec-review fail-closed 门，**不用 subagent**）
  → ② **成本实验 change**（同管线 A/B 测 writer/researcher，量总 token/美元/质量/返工/延迟）
  → ③ **产品化 change**（实验达标才新增公共入口 + 下游分发 + 旧入口退役）
- **为什么**：当前 change 同时押注新交互、新顺序、新状态产物、两类 agent、模型分档、全局安装、成本优化 ⇒ **任何结果都无法归因**；而唯一支持「上 subagent」的理由（成本）本身未被证实（F-08）。
- **⚠️ 两个模型都不知道的上下文**：你在 `CLAUDE.md` 基准 4 已明确「**拆分标准 = 一个 change 一个完整阶段结果，不按同批来源/顺手/凑票数**」，并明确「**碎片化是反复对现状提疑问 + 给妥协方案的根因**」。若「阶段一单一入口管线」本身就是一个完整内聚阶段结果，则当前 scope 是对的，**拆分反而违反基准 4**。
- **如果拆了但你原来是对的，代价**：多付两轮 workflow 循环固定成本（本仓已记录该成本高），且 ① 单独交付价值有限。
- 两个模型**均未**把此标为安全/可行性风险 ⇒ 属取向分歧，非风险警报。
- **你的原方向为默认。** 不明确改口即按原样推进。

**三镜代价**（供拍板）：
- **系统镜**：拆分 → 三个 change 各自可回退、归因清晰；不拆 → 一个大 change，出问题时无法判断是哪一层的错。
- **用户镜**：拆分 → 你要等三轮才拿到完整管线；不拆 → 一次到位但首版带着未验证的成本假设。
- **开发循环镜**：拆分 → 多两轮 workflow 固定成本（高）；不拆 → 单轮，但若 F-08 成立，第二轮返工不可避免。
- **主次判定**：**开发循环镜主导**。若你认可「阶段一管线是一个完整阶段结果」，不拆是对的；此时**建议的最小让步 = 把 D2（判断/机械分层外派）降为可选路径**，先按「薄编排」形态（主 session 亲写，D2 自己已写明这是合法降级形态，`design.md:96`）交付并把 agent 定义/外派作为**同 change 内的第二阶段任务**，用一次真实 dogfood 决定是否启用——这样既不拆 change，也不在未证实的成本假设上押注。

### 🔴 Q2 —— `/clear` 出口序列 vs workflow.md 的 G1，三选一

**冲突是硬的**（F-02 的一部分，独立由 Claude-DX 与 Codex-DX 双侧命中）：

- `sdflow-init/assets/workflow/workflow.md:91` 把「**子代理 fresh-context 替代 `/clear`**」标为「**关键设计决策 2（最关键，G1）**」，`:5-6` 明文「**全流程不用 `/clear`**」；`reference/quality-layering.md:107,117` 同。
- 而 `spec.md:113`（SA-09）把 `/clear` 写成 **MUST 原样贴出**的强制步骤。
- `design.md:104`（D6）给的三重依据里「主审裁决需冷视角」这一条，**恰恰是 G1 已经正面回答过的问题**（`quality-layering.md:101-107`：sdflow-code-review 的冷靠独立编排器 + fresh 子代理 fan-out，不靠 `/clear`）。D6 **没有引用、没有反驳、没有说明为何不适用**。
- `design.md:155-163` 的 Compliance 逐条核了 adr/0005、通则托管、host-adaptive、DOC-1、基准 5 —— **唯独没核 G1** ⇒ 判定为**漏查，不是权衡后的显式偏离**。
- 佐证：现有 grill→spec-review 过渡（`workflow.md:79-81`）本身就**没有** `/clear`，G1 是当前真实在跑的规则。

**三个选项**：

| | 做法 | 代价 |
|---|---|---|
| **A（推荐）** | **保留 `/clear`，但同 change 修订 G1**：在 `workflow.md`/`quality-layering.md` 里为「阶段一→二」这一段写明例外与理由（D6 的两条依据里，**cache 按模型隔离 + 产/审错档**是 G1 没覆盖的新论据，站得住；「主审冷视角」那条要删，它已被 G1 回答） | 动 bundle canonical，下游随 `sdflow-init update` 获得；改动小但必须做 |
| B | **放弃 `/clear`**，出口序列简化为「换档 → `/sdflow-spec-review`」，冷由 spec-review 自己的 fan-out 提供 | 与 G1 一致、零规则冲突；但失去 cache/换档的成本收益 |
| C | 保留 `/clear` 且不动 canonical | ❌ **不推荐**：从 merge 那刻起本仓存在两条互相矛盾的阶段一规范，且 AI 从 bundle 读到的是旧的那条 |

**推荐 A**，依据：D6 的 cache 隔离与产/审错档两条是 G1 未覆盖的新论据（G1 的论证只针对「独立性」，没谈「成本」与「档位」）；且 A 顺手把 F-02 的一部分一起结掉。

### 🔴 Q3 —— agent 定义分发层级：全局 `~/.claude/agents/` vs 随 skill 目录

- `proposal.md:46` 定了「v1 由 setup.sh 装 `~/.claude/agents/`（全局）」，但**设计自己引的调研文档给的是相反倾向**：`docs/subagent-definitions-plan.md:303-308`「**先放本仓验证**，跑顺后再考虑上提到全局……放全局会影响全部项目，且与『sdflow bundle 由 sdflow-init 铺设』的分发模型不一致」。四件套**未给出反驳理由** ⇒ 属「悄悄改了调研结论」。
- **另一路证据**（CEO 镜实测官方 marketplace）：官方 `claude-plugins-official/plugins/feature-dev` 的打包方式是 **`<plugin>/agents/`（与插件同包）**，不是全局目录。
- **但**：全局可能确实是目标态所需 —— skill 要在**其它项目**里跑，仓内 `.claude/agents/` 到不了。
- **推荐**：**维持全局决定，但 design D3 MUST 补一句反驳 §7 的理由**（「仓内放置无法服务跨项目使用，故直接全局；代价 = 全局命名空间污染 + Windows 守卫不可实现，见 F-10」），并给两个 agent 的 `description` 写成**排他式**（「仅由 `/sdflow-spec` 编排派发，其它场景 MUST NOT 选用」）——因为 SKILL 有 `disable-model-invocation` 挡自动触发，**agent 定义没有对应机制**，全局 agent 会进入每个 session 的可选名册，而 `sdflow-spec-writer` 持有 `Write`。

### 🔴 Q4 —— 决策纪要承载力存疑：要不要先做 A/B 实测再定 D2

- 对抗镜 A 用**真实归档样本**证伪了 D2 的核心假设：`openspec/changes/archive/2026-07-18-async-outside-voice/design.md` 的 9 条 ADR 里 **≥4 条带 `[grill]`/`[spec-review-amendment]`/`[seam-review-amendment]` 复合标记** ⇒ 其最终形态依赖**多轮、跨阶段、跨模型**输入，不是 Phase B 一次拷问收敛能压缩进一份 5 字段纪要的东西。
- Codex-CEO 从另一角度收敛到同一处（C-5）：「写 design 会发现架构缺口、写 spec 会发现不可验收表述 —— **这些发现本身就是判断工作**」，而 writer 被禁止询问用户 ⇒ 遇缺口只能猜/漏写/失败，随后主 session 读回直接修正 ⇒ 实际形成**双写**。
- **这是行为层推断（中置信），不是事实错误** ⇒ 登记为需拍板，不自动裁决。
- **推荐**：不改 D2 的目标，但把 **tasks 4.3 的 dogfood 从「小型真实需求」改为「一个真实复杂 change」**，并加一条验收：人工比对「纪要驱动的 design.md」vs「有完整拷问上下文的 design.md」的**论证密度差距**（而非只查字段填没填）。零额外机制，只改一条任务措辞。

### [自动决策] autoplan 相位裁决

| # | 决策 | 分类 | 依据 |
|---|---|---|---|
| D1 | UI scope=否 → 跳过 Design 相位 | Mechanical | 无渲染面 |
| D2 | DX scope=是 → 跑 DX 相位 | Mechanical | 交付物是开发者工具 |
| D3 | 双声全开（codex 0.145.0 + Claude 子代理） | Mechanical | 两侧均可用，无降级 |
| D4 | premise gate 不弹窗，结论入本报告 | G2 铁律 | sdflow-spec-review 规定中途不 AskUserQuestion |
| D5 | Eng 与 DX 相位并行（偏离 autoplan 严格串行） | Taste | 省一轮墙钟；DX 只带 CEO 上下文。已如实标注，未观察到漏项 |
| D6 | 跳过 gstack 自身运维提示 | Mechanical | 与评审目标无关且需 AskUserQuestion |
| D7 | design-voice 复用 autoplan 的 codex findings，不重开 | Mechanical | `outside_voice_guard.py` 判 `reason_code=none`（三前置全过），避免双 codex |

---

## Findings（合并去重后 32 条 · 按严重度）

> 「命中镜」= 去重前哪些镜独立报过。**高收敛项（≥3 镜）标 🔥**。

### 致 · critical（5 条）

#### 🔥 F-01 `agentType` 是 Workflow JS 的参数，不是 Agent 工具的 —— 派发注定失败，而 fallback 是「减配 + 提权」路径

**命中镜**：broad(Claude-Eng F2) · adversarial(对抗镜A F1) · outside-voice/design-voice(Codex-Eng E-9) · outside-voice/hr-tg(V-3)　**置信度**：高

- 设计自己引的来源 `docs/subagent-definitions-plan.md:114-145` 把三条路径分清：①Agent 工具（参数 `subagent_type`）②agent 定义文件（载体）③Workflow `agent()`（参数 **`agentType`**）。同文 `:145` 明记 **③ 不采纳**（需用户每次显式授权）⇒ 本方案走的必然是 ①+②，参数名应是 **`subagent_type`**。
- 本仓三处先例一致用 `subagent_type`（`.claude/skills/openspec-archive-change/SKILL.md:69` 等）；15 个 SKILL.md **无一使用** `agentType`。
- 而 `design.md:42-43,98`、`spec.md:87,91`、`tasks.md:20` 全部写 `agentType`。
- **后果链**：派发失败 → SA-07 的 fallback **当场吸收** → 管线照跑、报告最多一行「降级」→ **agents 文件铺了、sync 守着、setup 装了，唯独没人在用它，而机械层（4.1 pytest / setup --check）全绿**。这是一条**设计好的静默失败通道**。
- **`tasks.md:31`（4.2）是恒绿门**：原文「失败则按 fallback 路径验证」⇒ 成功算过、失败也算过，**永远不会红**。
- **hr-tg voice 的独家加码（V-3）**：fallback **不只是行为减配，是撤掉唯一的工具权限边界 = 降级即提权**。`spec.md:87` 把工具白名单绑在 agent 定义上，`:93-95` 却退到「通用子代理 + prompt」；`docs/subagent-definitions-plan.md:116-123` 明确直接 Agent 路径无法限制工具集。
- **建议**：① 三处一律改 `subagent_type`；② tasks 1.x 增一条**实测 GO/NO-GO 门**（照 `mlh-p5-gate-frontmatter` tasks 0.6 的既有格式：写任何 producer 前先实测派发）；③ 4.2 拆成两条独立结论（「派发链路 GO/NO-GO」会红 + 「fallback 路径可用」），**MUST NOT** 用「失败就验 fallback」把两条并成一条；④ 采纳 V-3 的处置：**无法证明 fallback 具有等价工具集时，researcher 直接降级为主 session 亲查、writer 由主 session 亲写，不得用权限更宽的通用子代理当安全 fallback**。

#### 🔥 F-02 与 bundle canonical 规则**正面冲突**，形成多真相源 —— 本轮最高收敛项（5 镜、4 个文件）

**命中镜**：broad(Claude-CEO F2 / Claude-DX D-1) · domain(#1) · adversarial(对抗镜A F7) · outside-voice/design-voice(Codex-DX X-1 / Codex-CEO C-9 / Codex-Eng 附注)　**置信度**：高

四个不同的既有权威文件与本 change 冲突，而四件套**无一处提到它们**（`grep -c generation-process` 四件套全部 = 0）：

| 冲突文件 | 它规定的 | 本 change 的 | 性质 |
|---|---|---|---|
| `sdflow-init/assets/workflow/generation-process.md:47-58` | 推荐流水线 = `explore→ff→grill` | 单入口 `/sdflow-spec` | 即时冲突。该文件 `:81-84` **原文警告**「否则它会另起一套……形成第二套真相源，正是我们一路在消除的漂移」 |
| `sdflow-init/assets/workflow/workflow.md:5,13,76,91` | 阶段一三步；**全流程不用 `/clear`（G1，标为最关键）** | `/clear` 为 MUST | 见 Q2 |
| `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md:16` | 继续教旧流程（生成物） | — | 需随源重生成 |
| `openspec/specs/spec-workflow/spec.md:968-994` | **已有两条正式 Requirement** 涉及阶段一衔接（wayfinder→ff 衔接契约、grill 对已决分支瘦跑） | `proposal.md:23` 声称 `Modified Capabilities: 无`，理由「现有 specs 的 requirement 层不含阶段一入口约定」 | **该理由与事实不符** |

- 关键放大因素：本仓运行时经 `resolve-workflow.sh` 解析到**全局 canonical**（仓内不留规则副本）⇒ **本仓 agent 读到的仍是旧流水线**。这不是「下游推广」问题，是**即时的、本仓内的**冲突。
- `proposal.md:47` 只把「bundle workflow.md 下游推广」defer 了 —— 而 `generation-process.md` 不是 workflow.md，且冲突当下就存在。
- **建议**：把这四个文件纳入本 change 的 Impact 与 tasks（**P0，不可 defer**）。最小改法：`generation-process.md` 第四节加分支「已装 sdflow-spec 的仓：单入口取代三步；未装：沿用下方流水线」；`workflow.md` 按 Q2 处理；`WORKFLOW-GUIDE.md` 改源后重生成；`proposal.md` 的 `Modified Capabilities` 补 `spec-workflow` 的两条 Requirement 如何共存/路由。

#### 🔥 F-03 `openspec status` 的「完成」= **文件存在**，不是「合格」；仓内已有的 `validate` 结构门整份设计只字未提

**命中镜**：broad(Claude-Eng F1) · adversarial(对抗镜B 事故5) · outside-voice/design-voice(Codex-Eng E-6)　**置信度**：高（CLI 源码实证）

- CLI 源码实证：`@fission-ai/openspec/dist/core/artifact-graph/state.js:25-29` 原文 *"Checks if an artifact is complete by checking if its **generated file(s) exist**."*；实跑 `openspec status --json` 的字段就叫 `existingOutputPaths`。
- **三条决策叠成闭环漏洞**：writer 写半截（命中 max-output-tokens）→ 文件存在 → `status: done` → `spec.md:69` **禁止**看内容判完成态 → `spec.md:109` 明令**不重写已完成产物** ⇒ **坏产物永久锁死**，级联进下一个产物，直到阶段二才可能被发现。
- **反讽**：`design.md:162` 把这套记为「遵守基准 5（无界语法禁手搓）：产物存在性与完成态一律问 openspec CLI，让工具自己回答」——**问对了工具，问错了问题**。CLI 回答的是「存在吗」，设计需要的是「合格吗」。
- 仓内**已有** `openspec validate` 且已被定义为四件套结构门：`docs/criteria-mechanization-tracker.md:25`、`sdflow-done/SKILL.md:360`。四件套**零处**提及（本轮实跑 `openspec validate add-sdflow-spec --strict` → `is valid`，exit 0，命令确实存在）。
- **建议**：① 相位 C 每个产物写后 MUST 跑 `openspec validate <change> --strict`，非零即判**未完成**、进重试/亲写阶梯；② SA-05 的措辞拆成三句——「**完成态**问 status；**合格态**问 validate；MUST NOT 手搓 Markdown 解析器」（否则实现方会照字面把 validate 一起禁掉）；③ SA-08 可重入判据从「status ready」改为「status ready **或** validate 不过」；④ 写入用临时文件 + 原子替换（voice V-2 同向）。

#### 🔥 F-04 「拷问不可跳过」不成立，且四件套内部自相矛盾；仓内已有更便宜的机械解法从未被比过

**命中镜**：broad(Codex-CEO C-2 / Claude-CEO F1) · adversarial(对抗镜C #3) · outside-voice/design-voice(Codex-DX X-2)　**置信度**：高

- **内部矛盾**：`proposal.md:28` 自认「**结构性改善而非机械保证**……不冒充机械门」 vs `design.md:94` 声称「**跳过风险结构性消灭**」。同一份设计对核心价值主张给了两个强度。
- **机制上没解决根因**：新 skill 自己 `disable-model-invocation: true`（`spec.md:7`），三原 skill 全保留且 `opsx:ff` **模型可自调**（`proposal.md:9,57`）⇒ **新管线比它要替代的路径更难被触发，不是更难被绕过**。（直接观测：本次运行的可用 skill 清单里有 `opsx:ff`/`opsx:explore`，没有 `grill-with-docs`，也不会有 `sdflow-spec`。）
- **SA-01 的机械条件只是「存在非空决策纪要」**（`spec.md:7,13`）—— 模型可以直接合成一份字段齐全的 memo，不能证明发生过对抗拷问。
- **对抗镜C 挖到根因**：不是「纪要能不能造假」，而是**决定何时转相位的判据本身无操作定义**——「成熟可提前进 B」「承重约束全站稳」「一撤则候选整列塌缩」（`design.md:76-77`、`spec.md:35`）全是形容词级描述，无阈值、无清单、无样例，且被赋予 SHALL 级约束力。
- 🔴 **仓内已有一条为它专门设计、成本低两个数量级的解法，D1 备选表一个字未提**：`openspec/issues/todolist/2026-07-todolist.md:232` —— **T132，状态 OPEN，2026-07-11 记录**：「spec-review 起手机械核验『grill 已收敛』信号（checkpoint-commit 或 `<!-- sdflow:grill-done -->` 锚），无信号 → REFUSE_START」。载体、fail-closed 语义、先例（ship_gate 设计门新鲜度）全都已定。`design.md:94` 的 D1 备选只列了「现状式先生成后拷问」「Spec Kit 式生成初稿再 clarify」。
- **建议**：① 消除内部矛盾——`design.md:94` 改为与 proposal 同口径的诚实措辞；② D1 备选表补 T132 并说明为何仍需新 skill（或直接先做 T132，**无论本 change 是否推进 T132 都该做——它是唯一能覆盖「人直接敲 opsx:ff」那条路径的机制**）；③ 给三个相位转换判据至少一条最小充分条件（如：每条承重约束必须有 researcher 供证的 file:line 或人确认记录，缺一不可站稳）。

#### 🔥 F-05 脏工作树 + `git add -A` → 无差别提交；**本仓已真实发生过一次**，且已有的强制纪律未被继承

**命中镜**：broad(Claude-Eng F8) · adversarial(对抗镜B 事故1) · outside-voice/design-voice(Codex-Eng E-1)　**置信度**：高

- 复现：用户在任意分支有未提交的活 → 触发 `/sdflow-spec` → 走到 B 收敛 → FF-0 `git checkout -b`（**不清空未提交改动，只是带到新分支**）→ `openspec new change` → 写 memo → `checkpoint-commit.sh`。
- `sdflow-init/assets/hack/checkpoint-commit.sh:51` 是**无条件 `git add -A`**（含未跟踪文件）⇒ 用户那堆无关改动被静默塞进 `checkpoint(phase-b)`，而报告只说「memo 已落盘」。
- **决定性证据**：`openspec/issues/buglist/2026-07-04-buglist.md:26-28` —— **同一根因已真实发生过**（「`add -A` 把未提交的 superpowers-plan.md 随 task1 checkpoint 一起入库」导致 gate 窗口误判）。
- **且本仓已有血换来的纪律，本设计没继承**：`sdflow-code-review/SKILL.md:303,348-349` 🔴 标记「**跑本步前 MUST 先 `git status --porcelain` 确认工作树只剩报告文件**」。`design.md:112-121` 失败模式表六行全是工具失败，**没有一行覆盖工作树不洁**。
- 连带：`design.md:110`（D9）的「拷问后放弃则留带纪要的空 change 目录，**删分支即净**」**失真**——删分支会连用户被裹挟进来的活一起删。
- **建议**：SA-09 补一条 MUST：B 收敛 checkpoint 前先 `git status --porcelain`，若含 `decision-memo.md`/`.openspec.yaml` 之外的条目 → halt 报告给人（对齐 sdflow-code-review 1.6b 既有模式）；`design.md:110` 的「删分支即净」补条件限定「**当且仅当** B 收敛时工作树干净」；失败模式表补「人在 B 中途放弃」一行（D9 把它变成了常态可达）。

### 高 · high（9 条）

#### 🔥 F-06 TG-17 判定错误 ⇒ BASE-28 必填槽整块缺失；新增出境通道未复用仓内既有防线

**命中镜**：broad(Claude-Eng F3) · domain(#2) · outside-voice/design-voice(Codex-Eng E-5) · outside-voice/hr-tg(V-4, V-5)　**置信度**：高

- `proposal.md:71` 声称「无涉敏感数据/信任边界变更（**TG-17 不命中**）」，而 researcher 白名单是 `Read, Glob, Grep, **Bash**, WebFetch, WebSearch`，设计断言「**六者皆只读、不破无写权边界**」（`design.md:98`、`spec.md:87`）。
- **`Bash` 不是只读**：能 `>` 重定向、`rm`、`git commit`、`curl -X POST`。工具 allowlist **不能限制 Bash 子命令**，白名单在这里一点没挡住。
- ⚠️ **这句话是 `[grill-amendment]` 标记的**——它是拷问轮**之后新加进来的**结论，即拷问过程反而把一个错误论断固化成了 spec 里的 SHALL 级描述。
- 同一错误在设计引的源里就有先例（`docs/subagent-definitions-plan.md:145` 把 `Read, Glob, Grep, Bash` 标为「只读」）——**别拿它当依据，那是同一个错**。
- **hr-tg voice 的独家加码**：
  - **V-4**：仓内**已有** secret_scan / 读围栏 / 不可信数据框架（`openspec/specs/host-adaptive-execution/spec.md:82-96` 明确要求 secret scan + 读围栏 + 拒发语义），而 researcher 这条新出境通道**完全未复用**。建议拆成 **local researcher（无网络）+ web researcher（无仓库读取/Bash，只收主 session 生成的最小净化查询）**，任何外发参数先过 secret scan，命中即拒发且禁 fallback。
  - **V-5**：**联网结果没有被定义为不可信证据** —— 外部页面可经间接 prompt injection 驱动一个同时持有仓库读取和 `Bash` 的 agent。`tasks.md:8` 只要求返回结论与 URL，无内容隔离/指令降权/交叉验证契约。（领域镜 #2 独立命中同一点。）
- **建议**：① `proposal.md` Compliance 改判 TG-17 命中，补 design 的 BASE-28「安全与数据保护」段；② 二选一处理 Bash——**推荐**用作用域参数收窄（`docs/subagent-definitions-plan.md:223-224` 实测 `tools` 支持作用域参数）写成 `Bash(git log:*), Bash(rg:*)` 之类，**备选**如实改称「检索取向；`Bash` 非只读，只读性由角色纪律约束，**属指令层非机械门**」（对齐本仓诚实边界纪律的标准写法）；③ 采纳 V-4 的双 agent 拆分与 secret scan 复用；④ 采纳 V-5：requirement 层规定 Web 内容一律作不可执行数据。

#### F-07 `resolvedOutputPath` confused-deputy：第三方 CLI 的输出被直接提升为写入目标

**命中镜**：outside-voice/hr-tg(V-2)　**跨模型独家**　**置信度**：高

- `spec.md:59` 要求 writer 自取 CLI 的 JSON 并写入 `resolvedOutputPath`；`design.md:98` 给 writer `Bash, Write`。四件套**未规定路径归一化或 change-root containment** ⇒ 路径穿越、绝对路径、symlink 逃逸均无防护。
- **建议**：由确定性 wrapper 解析并验证 JSON；对目标做 canonicalization，要求严格位于 `openspec/changes/<name>/`、匹配预期 artifact allowlist、拒绝 symlink 逃逸，再把净化后的路径交给 writer。

#### 🔥 F-08 成本论证不成立 —— 三种独立算法同向，且基线数字**查无来源**

**命中镜**：broad(Codex-CEO C-4 / Claude-CEO F3,F4,F6) · adversarial(对抗镜C #1,#2) · outside-voice/design-voice(Codex-DX X-8)　**置信度**：高

四条互相独立的证伪：

1. **基线是编造的**（对抗镜C 实测）：`grep -rn "65KB\|40 轮"` 全仓**除本 change 自身外零命中**。实测 48 个归档 change 的四件套字节数：**中位数 42,536 字节**（65KB 落在第 85 百分位）；**本 change 自己的四件套实测 42,351 字节** —— 几乎正好是中位数，自己就反证了 65KB 这个「量级」。
2. **绝对值差 6–8 倍**（CEO 镜算术）：单价核实**全对**（Fable $50/M、Opus $25/M、Sonnet $15/M；-70%/-40% 正确），但 42–65KB ≈ 20–30K output tokens ⇒ 生成环节节省上限 ≈ **$0.88**（Fable 主）/ **$0.25**（Opus 主），而 `proposal.md:51` 声称节省 **$5-7**。
3. **混淆 token 数与单价**（Codex-CEO）：四个串行 fresh-context writer 重复读 instructions/memo/依赖产物，后续 writer 重读前序产物，主 session 终审又读回四件套 ⇒ **总 token 很可能上升**，只是因模型便宜而美元成本下降。「token reduction」与「美元下降」不是同一主张。
4. **Success Metric #1 是重言式**（对抗镜C #2）：「生成环节按 mid 档价（$15/M，降 ≥40%）」测的是**单价表常量**——只要子代理确实派到 Sonnet，这个百分比在任何情况下都成立。它测的是「有没有派到便宜模型」，**不是「这次重构是否让阶段一变便宜」**。

补充：
- **优化的是 11% 的阶段**（`openspec/retro/report.md:70-79`：ff 9% + grill 2%），而代价可能落在下游更贵的阶段（spec-review 13%，另一口径 43%）。`design.md:141` 的缓解「spec-review 安全网不变」恰好承认了下游要兜，却把兜的成本算作零。
- **仓内已有形状完全相同、悬 10 天未闭合的同类主张**：`openspec/roadmaps/workflow-cost-optimization/roadmap.md:84`「核心实现已交付，**阶段尚未验收闭合**……尚缺①机械镜实际 token/轮下降且墙钟不回归的基线对比」。本 change 未引用，也未说明为何这次的 `/usage` 粗粒度对比会比上次更可信。
- ⏰ **Sonnet 现有 $10/M 促销价 2026-08-31 到期**，8/31 前的任何 dogfood 会高估稳态节省约 33%。
- **建议**：① 删掉「65KB/40 轮」，NFR 表改用 42KB 实测中位数重算；② Success Metric #1 改成「dogfood change 的阶段一**总** token/美元成本（含 researcher + writer + memo 往返 + 终审读回）」；③ 把「关掉 roadmap P2 的①号证据」并入本 change 验收，一套度量覆盖两者；④ 若数字撑不起叙事，**如实把价值主张收窄为「拷问前置 + `/clear` 无损」两条**——`proposal.md:40` 自己也写了「质量收益独立成立」。

#### 🔥 F-09 机械覆盖虚高：九条 requirement 零机械测试；4.2 是**恒绿门**；覆盖图 over-claim

**命中镜**：broad(Claude-Eng F5 / Codex-CEO C-8) · adversarial(对抗镜A F1 / 对抗镜C #7) · outside-voice/design-voice(Codex-Eng E-10)　**置信度**：高

逐条判定（tasks.md:30-33）：

| 任务 | 性质 | 判据 |
|---|---|---|
| 4.1 pytest 全绿 | **真机械**（仅覆盖 SA-07 的通则块渲染那一半） | `hack/tests/test_sync_principles.py:22` |
| 4.1 setup.sh 幂等「无 skipped 异常」 | **自报** | `hack/tests/` 实查只有 4 个文件，**全仓无任何 setup.sh 测试** |
| 4.2 派发冒烟 | **自报 + 恒绿** | 原文「失败则按 fallback 路径验证」⇒ 不可能红 |
| 4.3 dogfood | **自报**（且 N=1、自评） | 覆盖图自己写「行为层人核」 |
| 4.4 /clear 抽检 | **自报** | 同上 |

- **完全没有机械测试的**：SA-01、SA-02、SA-03、SA-04、SA-06、SA-08、SA-09、SA-10（**九条**，含 Codex 独立点名的同一集合）。SA-05 只验最终存在态；SA-07 只机械覆盖静态定义与安装。
- **追溯断裂**：`tasks.md:3` 声称「SA-01~SA-10 全部被至少一个任务覆盖」，但 §4 的标签里 **SA-02、SA-03、SA-10 一次都没出现**，而 `tasks.md:42` 的覆盖图却写「三相位管线行为（SA-01~06, 09, 10）」——把 SA-02/03/10 算进了没有任务标签支撑的格子。
- **建议**：① 4.2 去恒绿化（见 F-01）；② **补全仓第一个 setup.sh 测试** `hack/tests/test_install_agents.py`（`tmp_path` 当假 HOME 跑 `bash setup.sh`，断言：铺出软链且指向本仓 / 预置非本仓同名文件不被覆盖且进 skipped / 删源重跑清悬空链 / 重跑幂等）——正好覆盖 F-10 那个「机制不可迁移」的面；③ 补两条真机械断言：`openspec validate --strict`（F-03）+ `decision-memo.md` 必填小节非空的 grep 门（`proposal.md:28` 已把它写成「机械审计信号」，但没有任何任务把它变成一条会红的检查）；④ SA-02/03/10 要么补进 4.3 核验清单，要么在覆盖图里**如实标「无验证（纯指令层）」**——MUST NOT 让覆盖图声称任务没提供的覆盖。

#### 🔥 F-10 `setup.sh` 的安装协议**只适用于目录型 skill**，散装 `agents/*.md` 套不进去；回滚方案是假的

**命中镜**：broad(Claude-Eng F4 / Claude-CEO F8) · outside-voice/design-voice(Codex-Eng E-3, E-4)　**置信度**：高

- `setup.sh:38-39`：`for skill_dir in "$REPO_DIR"/*/; do [ -f "$skill_dir/SKILL.md" ] || continue` —— 只认**顶层目录**且必须含 SKILL.md。`sdflow-spec/agents/` 是二级目录，散装 `.md` 进不了这个循环。
- `setup.sh:27-32` `is_our_marker_copy()` 判据 `[ -f "$1/.sdflow-skills" ]` —— marker 是**目录内的文件**。对 `~/.claude/agents/sdflow-researcher.md` 这样的散装文件，该路径是**路径谬误、恒 false** ⇒ **Windows copy 分支的所有权守卫不可能实现**（要么无条件覆盖用户同名文件，要么无条件 skip）。
- `setup.sh:106` 的非软链分支判据 `[ ! -d "$REPO_DIR/$entry_name" ]` 对 `sdflow-researcher.md` **恒真**；`setup.sh:211` 的 `cleanup_orphans` 只对两个 skills 目录调用。
- Unix 分支 `setup.sh:60` 会**无条件替换任何同名 symlink**，并非真正的所有权守卫。
- **回滚是假的**：`design.md:149` 说「revert + 重跑 setup.sh，孤儿链接清理机制自动移除 agents 链接」——但 revert 会把新增的 agents 铺设段**连同其清理逻辑一起撤掉** ⇒ 重跑时没有代码去看 `~/.claude/agents/` ⇒ 两个悬空软链**永久留下**。（与 skills 不同：skills 的 `cleanup_orphans` 是**通用**的、不随单个 skill 被 revert。）
- 与之矛盾的三处声明：`proposal.md:11`「沿用 symlink/copy 机制」、`spec.md:87`「含所有权守卫与孤儿清理」、`design.md:144`「铺设走 setup.sh 所有权守卫模式」。
- **建议**：① design 组件表与 SA-07 改成如实描述：**新写 `install_agents()`**，Unix 逐文件 `ln -snf`，所有权守卫降级为「**只接管软链、且 readlink 指向本仓**，其余一律 skip 并计入 `skipped[]`」（对齐 `setup.sh:128-134` 处理 `$sdflow/workflow` 的既有 idiom）；② **Windows 分支 MUST 明写取舍**（建议「Windows 下不铺 agents、走 fallback 内联路径」并在 `skipped[]` 报一行）——别写做不出来的东西；③ `design.md:149` 的回滚说法改为如实（「revert 后需手动删除，或先跑一次未 revert 的 setup 的 uninstall 分支」）。

#### 🔥 F-11 状态机缺失：重入判定 / 陈旧 memo / 第二个 change / 分支已存在，四个洞

**命中镜**：broad(Claude-Eng F7,F12 / Codex-CEO C-1) · adversarial(对抗镜B 事故2,事故4) · outside-voice/design-voice(Codex-Eng E-2,E-7)　**置信度**：高

- **SA-05 与 SA-08 互相矛盾**：`spec.md:59` 无条件要求 B 收敛时 `openspec new change`，`spec.md:103` 又要求已有产物时从 ready 项继续。
- **FF-0 是弱判据**：`ff-generation-constraints.md:16-17`「已在 feature 分支 → 跳过（幂等）」；`ff0-branch-guard.py:23,70` 硬拦只看 `{main, master}` ⇒ 在 `feat/change-A` 上开 change B **一路放行**，两个 change 的产物挤在一条分支上，PR 的「设计→实现」故事线当场破掉，`sdflow-done` 的 merge 会一次带走两个 change。原流程一次一个 change、中间隔 `/clear` 和 merge；**新管线单一入口、会话内可连跑**且 D9 把建分支提到 B 收敛 ⇒ 这个状态变得常见得多。
- **陈旧 memo 全绿通过**：Phase C 对 memo 只检查「存在且必填字段非空」（`spec.md:14,59`）⇒ 上一次废弃运行留下的非空 memo 被**无条件当作当前决策**。而 D9 自己承认会留下「带纪要的空 change 目录」（`design.md:110`）。
- **`git checkout -b` 失败无处置分支**：分支已存在时 Git 直接报错，`design.md:64` 序列图与失败模式表都没有这条路径。
- **重入的入口判定完全无定义**：change 名从哪来？怎么知道有在途 change？相位 A/B 要不要重跑？
- **建议**：① 定义显式状态机 `absent → B-draft → B-finalized → C-partial → complete`；② FF-0 检查改**三分支判定**（保护分支 → `checkout -b`；`feat/{本 change}` → 跳过（真幂等）；**其它 feature 分支 → 停下问人**——三种意图导致实质不同的产物，属通则③里必须确认的那类）；③ memo 加 `schema_version` / `change` / `branch` / 时间戳 / 决策 hash，C 起手核对不上即拒绝；④ `checkout -b` 失败时 fallback 到 `git checkout feat/{change}`（存在则复用）否则如实报告。

#### 🔥 F-12 Phase B 收敛前**零持久化**，而 D9 否决 scratchpad 的理由对自己的方案完全同样成立

**命中镜**：broad(Claude-DX D-2) · adversarial(对抗镜A F4 / 对抗镜B 事故3) · outside-voice/design-voice(Codex-DX X-3)　**置信度**：高

- `design.md:110`（D9）否决 scratchpad 的理由是「**scratchpad 为 per-session 目录，session 崩溃/换 session 即丢承重件，可重入被击穿**」——但**当前选定的方案（B 收敛才落盘）对「B 收敛之前」这段窗口，持久化程度和 scratchpad 完全一样（都是零）**，只是丢失窗口从「到 C 起手」挪到「到 B 收敛」。
- 且轮数**无上限**：`spec.md:35`（SA-03）明确禁止用「预设问题问完」当停止条件，`design.md:59,63` 写「…若干轮…」，`proposal.md:51` 自己按 **40 轮**估算 ⇒ 首次落盘无有限上界。
- 失败模式表六行**无一覆盖「session 在 A/B 收敛前中断」**；`spec.md:47`（SA-04）的措辞恰好只保证「**已收敛**的拷问成果」不丢。
- **对抗镜A 的加码（F4）**：锚点纪要只活在对话里 ⇒ 长拷问中主 session 对「承重约束」的理解可能在第 15 轮已悄悄偏离第 3 轮，而**没有落盘对照物可回查**。本仓已有两条同族实证（memory 锚 `grill-check-authority-glossary-before-defining`、`grill-question-loadbearing-constraint-collapses-candidates`：多轮拷问在无外部锚时会自我强化错误方向）。
- **建议**：Phase B 内部加轻量增量落盘点（每次承重约束「站稳」时追加写 memo 草稿版本，而非等全部站稳才一次性落盘），把全损窗口从「整个 A+B」收窄到「两次保存之间」；或至少在报告里**如实标注「中断即从头开始」为已知限制**。

#### F-13 `openspec CLI ≥1.5` 只有下界没有上界，而 **1.6.0 已发布 16 天**，且仓内无任何 pin

**命中镜**：adversarial(对抗镜C #5) · outside-voice/hr-tg(V-1)　**置信度**：高

- 实查 npm registry：`@fission-ai/openspec` 最新稳定版 **1.6.0，发布于 2026-07-10**（本次评审 2026-07-26 的 16 天前）；本机 `openspec --version` = **1.5.0**；`openspec-upgrade/SKILL.md:192` 固定执行 `npm install -g @fission-ai/openspec@latest`，**无版本锁定**；仓内无 package.json/lockfile pin。10 个月内 41 个版本，仍在活跃迭代。
- ⇒ **不是理论风险，是当下事实**：只要有人在本 change 落地前后跑过一次 `/openspec-upgrade`，环境就跳到 1.6.0，而所有设计假设（`instructions --json` 载荷 schema、`status --json` 字段名、`new change` 目录布局）**只在 1.5.0 上实测过**。
- SA-05/D8 把「CLI 不可用/报错」设为唯一 fail-closed 分支，**没覆盖「版本对、行为变」**——合法 JSON 的 schema 漂移会绕过 exit-code 检测（V-1 同向）。
- **建议**：标注「最后验证版本 = 1.5.0」并给上界；spec-writer 自调 `instructions --json` 时做一次最小 schema 断言（必需字段存在性 + 类型），不兼容即 fail-closed 并报告实际版本。

#### F-14 产物依赖图被误读：CLI 报告 design 与 specs **互不依赖**

**命中镜**：adversarial(对抗镜A F2)　**独家**　**置信度**：高（命令实跑）

- 实跑 `openspec instructions design --change add-sdflow-spec --json` 与 `... specs ...`：两者 `dependencies` **都是 `[proposal]`** ⇒ CLI 报告的真实依赖图是 `proposal → {design, specs}（并行分支）→ tasks`，**不是** `design.md:78` 写的「proposal → design/specs → tasks」线性序列。
- **后果**：SA-05 把「串行」包装成「CLI 依赖序决定」，但生成子代理的三输入之一是「**依赖产物**全文（自读）」——若照字面按 CLI `dependencies` 走，**specs writer 根本不会去读 design.md**（它不在 CLI 报告的依赖里）⇒ 产出与 design 矛盾的 delta spec。而 SA-06 终审只核「纪要↔产物」，**不核「design↔specs 互相一致」** ⇒ 这类矛盾直接漏进阶段二。
- **建议**：SKILL.md 显式写死每个产物的**强制阅读清单**（作者自定，不是 CLI 依赖图），别用「依赖产物」这个会被误读的说法；SA-06 终审补一条「design↔specs 互相一致」。

### 中 · medium（12 条）

#### F-15 【需拍板 Q4】决策纪要承载力不足 —— 见上方 Q4
**命中镜**：adversarial(对抗镜A F3) · outside-voice/design-voice(Codex-CEO C-5)　**置信度**：中　**裁决：defer 至设计门**

#### F-16 SKILL.md 体量大概率创全仓新高，且九条决策无一谈体量控制
**命中镜**：broad(Claude-DX D-4) · outside-voice/design-voice(Codex-DX X-7)　**置信度**：中

- 实测基线：最短 `sdflow-upgrade` **168 行 / 10.7KB**；最长两个（均为**单一职责**编排器）`sdflow-spec-review` **490 行 / 72.7KB**、`sdflow-code-review` **572 行 / 75.5KB**。
- `tasks.md:14-21` 要求单文件承载三相位 + 停止条件 + dispatch 契约 + 档位解析 + CLI 协议 + 重试阶梯 + Codex 降级 + checkpoint + ADR/术语钩子 + 出口序列 ⇒ 行为面明显更宽，大概率突破 700-800 行 / 80-90KB。
- 失效模式：lost-in-the-middle、提前宣告阶段完成、漏掉降级报告、重入走错分支——**一次 happy-path dogfood 抓不到**。
- `sdflow-code-review` 能控在 75KB 的关键手段之一是把领域清单**外置**到 `code-checklists/domains`；design 无类似设计，D 系列九条决策**没有一条谈 SKILL.md 自身的体量**。
- **建议**：降级阶梯表、ADR/术语最小模板、决策纪要字段 schema 这类「表格型、少判断」内容拆到 `sdflow-spec/references/`，SKILL.md 主体只留三相位编排逻辑与判断指引；在 design 里显式记一条体量控制决策。

#### F-17 三入口并存但**选择规则完全未定义** + 新入口不可被模型推荐
**命中镜**：broad(Claude-DX D-3) · outside-voice/design-voice(Codex-DX X-4 / Codex-CEO C-7)　**置信度**：高

- 新 skill `disable-model-invocation: true`（模型唤不起，只能人敲），三个旧入口仍活着且**模型能唤起**。`tasks.md:25` 的「**适用场景**」四个字是全部四件套里唯一提到选择规则的地方，**没有任何具体标准**（不是 TG 触发、不是场景清单、什么都没定义）。
- `tasks.md:26` 只要求把新名字加进 README 列表，无可靠首次发现路径；而 canonical 文档仍主动引导旧流程（F-02）。
- 对照本仓其它编排器的 `description` 都写清了何时触发、覆盖什么、与相邻 skill 如何分工。
- 三入口继续存活 ⇒ 维护成本是**永久叠加**而非替换，且无退出条件。
- **建议**：在 design 给一句可执行判断规则并写进 spec 作为 requirement（不只是 CLAUDE.md 非托管区的自由文字，否则这条规则本身也会漂移）；README 顶部给可复制 Quick Start；`setup.sh` 成功摘要显示「首选入口 `/sdflow-spec`」；**给旧路径明确的 sunset 条件**（达到采用率/质量/成本阈值后文档不再推荐；未达阈值则删新 skill）。

#### F-18 失败/降级报告只要求「要报」，不要求 problem + cause + fix
**命中镜**：broad(Claude-DX D-5) · outside-voice/design-voice(Codex-DX X-5)　**置信度**：中

- `spec.md:65-67`（CLI 缺失）只写「中止并报错」，未要求报版本/失败命令/根因/修复命令；`spec.md:93-95`（agent 缺失）只写「标注该降级」；`spec.md:101-103`（SA-08）只写「出现在完成报告中」；`design.md:112-121` 的「处置」列全是动作描述。
- 后果：安装问题会长期隐藏在「能跑但更贵、更慢」的降级模式里；报告易退化成「spec-writer 失败，已亲写」这种无信息量的一句话。
- **建议**：SA-05/07/08 补一条通用约束「降级/失败报告 SHALL 含：触发原因 + 判定依据（exit code / 文件缺失）+ **可执行的下一步**（如「回运行 checkout 跑 `bash setup.sh`」「跑 `/openspec-upgrade`」）」，各补一条 Scenario 断言；验证任务补故障注入（CLI missing / version-too-old / agent collision / writer partial-write）。

#### F-19 【需拍板 Q3】全局 agents 分发层级与设计自引调研结论相反 —— 见上方 Q3
**命中镜**：broad(Claude-Eng F11 / Claude-CEO F8,F9)　**置信度**：高（分发层级相左）/ 中（模型可自选全局 agent，按 `subagent_type` 语义推断未实测）　**裁决：defer 至设计门**

#### F-20 proposal P2 的立项理由与仓内 retro 数据**直接矛盾**（premise-verification 违规）
**命中镜**：broad(Claude-CEO F5)　**置信度**：高

- `proposal.md:35`：「**P2**：checkpoint 阶段锚（补 retro 数据**阶段一无独立打点**的缺口）」。
- 而 `openspec/retro/report.md:77` 有 `| ff | 1691.5 | 9% |`、`:79` 有 `| grill | 345.4 | 2% |` —— **打点存在且已参与聚合**。`openspec/roadmaps/workflow-cost-optimization/roadmap.md:68` 也引用了这组数据。
- 真实缺口是 `unknown` 桶占 **56%**（`report.md:72`）——若目标是提高归因率，那是另一个问题，应当照实写。
- **建议**：改写该理由或直接删掉 P2。

#### F-21 memo↔design 双写无优先级规则，且 design 原生槽位**装不下「承重约束」**
**命中镜**：broad(Claude-CEO F7) · domain(#4)　**置信度**：高（模版为实跑核验）

- 实跑 `openspec instructions design --change add-sdflow-spec --json`：原生 Sections = `Context / Goals-Non-Goals / **Decisions** / Risks-Trade-offs / Migration Plan / Open Questions`。memo 的「**承重约束[]（约束 + 验证方式/证据锚）**」**没有对应槽位**，而它正是 D1/SA-03 里最承重的东西（`design.md:77`「一撤则候选整列塌缩」）；「接受的边角[]」属 Risks 而非 Decisions。
- `spec.md:47` 要求「内容 SHALL 并入 design.md……memo 文件保留为审计锚」⇒ 同一批决策两份副本，**失配时以谁为准无定义**。
- 领域镜 #4 补一层：**「锚点纪要」（Phase A→B 对话内产物）与「决策纪要」（B 收敛后落盘产物）的关系从未显式定义**——`spec.md` 只提过一次「锚点纪要压缩」，其余全文只谈决策纪要，属可歧义条款。
- **建议**（**推荐 ①**）：① **不并入** —— memo 就是 `/clear` 无损的载体，它在 change 目录里、spec-review 读得到；design.md 的 Decisions 只留指针（符合 DOC-1 的查表式引用）。SA-04 的验收不变式单靠 memo 就已满足，「保留 + 并入」的双写成本全部是白付的。② 若坚持并入，则明确「memo 并入后即冻结、design.md 为唯一现行真相源」，并说明承重约束落到哪个 section。③ 无论哪种，**显式定义锚点纪要与决策纪要的关系**。

#### F-22 sync_principles 投放面若硬编码「两个 agents 文件」，SA-07 声称的守卫场景**做不出来**；且味源可能错配
**命中镜**：broad(Claude-Eng F10) · outside-voice/design-voice(Codex-Eng E-11)　**置信度**：高

- `spec.md:97-99`（SA-07 场景）：「或**新增 agent 定义未纳入投放面** → `--check` 或 `hack/tests/` 变红」。而 `tasks.md:10` 写「渲染进**两个** agents 文件」= 硬编码清单 —— **硬编码清单无法让「新增第三个未纳入」变红**（新文件不在清单里，`targets()` 根本不去看它）。对比 `skills()`（`hack/sync_principles.py:58-60`）用的就是 `REPO.iterdir()` **glob 发现**，正是为了这个语义。
- **味源错配风险**：`hack/sync_principles.py:119` 的 `targets()` 只给顶层 skills 配 `SOURCE`（skill 味），`PROJECT_TARGETS` 固定用 `SOURCE_PROJECT`（项目味）。若把 agents 直接加进 `PROJECT_TARGETS`，会注入**错误版本**——而 `design.md:29` 明确要求用 skill 味源。
- **建议**：tasks 1.3 明写实现方式 = **glob** `sorted((REPO/"sdflow-spec"/"agents").glob("*.md"))` 加进 `targets()`（与 `skills()` 同 idiom），并新增 `AGENT_TARGETS` 显式配 `SOURCE`；tasks 1.4 增一条定点用例「往 `agents/` 放一个新 `.md` → `--check` 必红」。

#### F-23 外派阈值「材料 ≳ 数百行」在派发**前**不可判定，且未数字化
**命中镜**：adversarial(对抗镜A F5) · domain(#7)　**置信度**：中

- `spec.md:19,22`（SA-02）唯一表述是「**预计**读取材料 ≳ 数百行」，没有给出「如何预计」的操作定义。本质是循环问题：要知道一次搜索命中多少行，通常得先跑一次才知道；而「先跑一次看看」要么等于主 session 已经查完（阈值失去意义），要么是又一次决策消耗。
- 后果：系统性低估未知规模的调研任务，或在阈值边界反复纠结（违 SA-03 的快速收敛精神），实际行为退化成「薄编排」（D2 备选里被否的形态），而报告仍写「遵守外派阈值」这类自证。
- **建议**：改成事后可复核的形式（「若主 session 直接查超过 X 次工具调用，下次同类任务改派」），或如实承认这是纯判断、不写成可「遵守」的规则。

#### F-24 终审「判断性偏差改 / 措辞放过」的线不可操作 —— 中间态未覆盖
**命中镜**：adversarial(对抗镜A F6)　**置信度**：中

- `spec.md:73-83`（SA-06）只给了两个**极端**例子（决策遗漏/相反 vs 纯风格），没覆盖高频中间态：**内容都在、但论证强度被稀释**（如把纪要里「D6 的三重依据」压缩成一句话）。这正是自然语言压缩的常见行为。
- 后果：同一类偏差的处理因人/因时而异，无可复现标准，且**没有任何机械信号能发现这种不一致**（它长得就像「终审做了、报告也写了」）。
- **建议**：给这类中间态一条显式判据（如：纪要里「砍掉的候选 + 理由」字段若在产物里**完全消失**才算偏差；措辞压缩但候选/理由仍可追溯则放过）。

#### F-25 外部检索失败无 deadline、无退避、无错误分类
**命中镜**：outside-voice/hr-tg(V-6)　**跨模型独家**　**置信度**：高

- `design.md:117` 把超时完全交给宿主且明确「**不重试检索**」；失败表没有区分 429/5xx、认证失败、schema 不兼容、网络不可达。且「宿主管理默认超时 → 主 session 亲查」**可能再次调用同一故障依赖**，无法形成真正的降级。
- **建议**：规定总时间预算；仅对 429/5xx 做一次带 jitter 的有界重试，认证/schema 错误立即 fail-closed；降级前确认替代路径不复用同一故障依赖，并报告依赖、错误类别、修复动作。

#### F-26 三相位序列图只画 happy path，六种失败/降级路径图中不可见
**命中镜**：domain(#6)　**置信度**：高

- `design.md:53-73` 的序列图（TG-10 激活）不含失败模式表里的六条路径，也不含 SA-01 的「纪要缺失退回相位 B」分支。按 `design-diagrams.md` 的规则，命中 TG 的图须验证**正确性/未过时**——本条即验证结果。
- **建议**：序列图补关键异常分支（至少「纪要缺失 → 退回 B」「writer 失败 → 重试 → 亲写」两条），或另附一张降级流程图。

#### F-27 BASE-12 三镜在同一文档内执行不一致
**命中镜**：domain(#3)　**置信度**：高

- D1/D2/D3/D6 有完整的「三镜 + 主次判定」，而同样带「备选」的 **D5/D8/D9 没有**（`design.md:100` 起）。命中 TG-23 的决策应一致执行。
- **建议**：D5/D8/D9 补三镜 + 主次判定，或说明为何这三条不适用（如「代价显然、无实质权衡」）。

### 低 · low（5 条 · 一行带过，可审计不静默丢）

- **F-28** `CLAUDE.md:192`「投放面 | **15 个 SKILL.md**」加入 sdflow-spec 后过期，`tasks.md` §3 未覆盖 CLAUDE.md 架构段/托管机制段。修法按本仓既有：**删掉数字让脚本自己报**（`hack/sync_principles.py:144` 已在打印 `len(targets())`）；扫 `grep -rn "15 个"` **不加 `--include` 限定**（跨文件类型残留教训）。〔命中：broad〕
- **F-29** `spec.md:99`（SA-07）称 `--check` 是「setup.sh 每次执行 → **变红**」的门，实际 `setup.sh:261-266` 的 `if !` 结构使 `set -e` 不触发、**退出码恒 0** ⇒ 是**提示不是门**。真正会红的是 `hack/tests/`。建议措辞改为「`hack/tests/` 变红（机械门）；setup.sh 额外打印漂移警告（提示，非门）」。〔命中：broad + outside-voice/design-voice〕
- **F-30** SA-08 的「**重试一次**」无任何依据（四件套与调研文档均未解释为何是 1 次）。**按通则④判为可接受边角，不建议为它单独返工**；若顺手改，建议写成「按失败类型判断（瞬时错误重试，schema/契约错误不重试直接降级）」。〔命中：adversarial〕
- **F-31** `proposal.md:46` 开放问题第 2/3 条只写「待 dogfood 后另 change」，**无负责人/截止**，与第 1 条的规范格式不一致（BASE-15 落空）。〔命中：domain〕
- **F-32** `disable-model-invocation: true` 在 **Codex 宿主**的语义未验证。本仓已有实测证明该字段有非直觉的 harness 特定行为：`openspec/changes/archive/2026-07-10-matt-workflow-integration/impl-notes.md:3-14` —— 它会让主 session 经 Skill tool 调用该 skill **直接被 harness 拒绝**（两次独立实证），并因此影响了 `sdflow-implement` 的 frontmatter 决策。本 change 给 `sdflow-spec` 也写了该旗标但未核验 Codex 侧行为。低置信上抛。〔命中：adversarial〕

---

## 已裁掉（反静默压制 · 原始发现 + 裁掉理由，供设计门复核「裁得对不对」）

| # | 原始发现 | 来源镜 | 裁掉理由 |
|---|---|---|---|
| **X1** | 接地镜结论「四件套代码事实核验**通过率 95%+**，不符项仅 1 个」 | grounding | **裁掉这个综合结论，保留其 21 项 ✅ 数据。** 接地镜跑在弱档（haiku），把 `agentType` 归类为「🟡 运行时行为核不了」而**漏掉了参数名事实错误**——而两个中档镜（Claude-Eng、对抗镜A）各自打开 `docs/subagent-definitions-plan.md:114-145` 独立确认了该错误（F-01，致级）。一个漏掉致级事实错误的核验，其「95% 通过率」不能作为结论采信。**本轮 grounding 独立=0，如实落进度量锚。** |
| **X2** | Codex-DX X-6 判「Migration Plan **没有覆盖 pull→setup skew**」为 high 缺口 | outside-voice/design-voice + broad | **部分裁掉，部分保留。** 裁掉的部分：Claude-DX D-6 独立核过后判定——该场景属 `CLAUDE.md:177,182` 已记载的通用「反向窗口」，且因 `disable-model-invocation: true`，唯一后果是「敲命令提示不存在」，**无静默误调风险**（不像 `impl-pipeline: tickets` 那例）。⇒ 不构成本 change 独有的新风险。**保留的部分**：X-6 关于「从**开发 checkout** 跑 `setup.sh` 会把全局 skill 链接**整体**指向 WIP checkout（`setup.sh:38,68`），而非只测新 skill」这半条是真的，已并入 F-10 的建议与 F-17 的升级面。 |
| **X3** | 对抗镜B 起手清单第 5 条「`decision-memo.md` 这个新文件会触发下游 ship_gate 设计门失鲜」 | adversarial | **镜自己核验后判定设计是对的**，如实记录不算事故：`sdflow-ship/scripts/ship_gate.py` 的 `design_pathspecs()`（约 483-491 行）监视集只含 `proposal.md/design.md/tasks.md/specs/`，不含 `decision-memo.md`；且 B 收敛 checkpoint 发生在 `reviewed_sha` 落锚之前，锚都不存在，谈不上失鲜。另由 Claude-Eng 独立复核 `sdflow-ship/tests/test_gate_freshness.py:500` 确认同一结论。 |

---

## 核过无问题（说明检查了什么、为何没标 —— 避免「没找到问题」被误读为「没检查」）

**设计正确、经独立核验确认的**：

1. **D9（纪要落 change 目录而非 scratchpad）三条论证全部成立** —— CEO 镜确认本次运行的 scratchpad 路径确为 session 级（`.../<session-uuid>/scratchpad`）、「B 收敛时仓内零变更 → checkpoint 静默跳过」的推理也对。**这是四件套里最扎实的一条决策。**
2. **模型单价与百分比全对** —— Fable $50/M、Opus $25/M、Sonnet $15/M；`proposal.md:27`、`design.md:133` 的 -70%/-40% 逐条核对权威模型目录后正确。（错的是绝对值与基线，见 F-08。）
3. **`effort:` frontmatter 与 `model: inherit` 真实合法** —— 实测官方 `claude-security` 插件 7 个 agent 文件（`effort: xhigh` ×6 / `medium` ×1、`model: inherit` ×4）。proposal 假设①的**依据成立**（错的只是派发参数名，见 F-01）。
4. **`docs/subagent-definitions-plan.md §4.6` 与「7 个实例」数字准确** —— 接地镜核过。
5. **`disable-model-invocation` 是真实字段** —— `~/.claude/skills/grill-with-docs/SKILL.md:4` 实测。
6. **档位 ID 与 Agent 工具 `model` 枚举兼容** —— `model-tiers.md` 机读块 Claude 机队 = `opus/sonnet/haiku`，与枚举匹配；`resolve-models.sh` 有字符集校验 + `printf %q`。
7. **归属修正（superpowers → Matt Pocock）是对的** —— `~/.agents/skills/` 下确有 `grill-with-docs`/`grilling`/`domain-modeling`/`ask-matt`，官方 marketplace 无 superpowers 插件；`sdflow-init/assets/snippets/claude-section.md:118` 确实写着「来自 superpowers 插件」⇒ **tasks 3.1 的前提成立**。
8. **checkpoint slug 与 ship_gate 的 `TAG_RE` 不冲突** —— `ship_gate.py:1187` 要求含 `task<N>-`，SA-09 的相位 slug 不会被误计入实现完成集。
9. **`decision-memo.md` 不在 ship_gate 设计门监视集内** —— 见 X3。
10. **openspec CLI 1.5.0 的 `status`/`instructions` 接口存在且幂等只读** —— proposal「已实测」属实（`proposal.md:41` 把它列为证据锚而非假设，做得对）。
11. **`ff0-branch-guard.py:62` 按 `tool_name=="Bash"` 拦，对子代理同样生效** —— 是 F-11 之外的一层兜底，且 `:12` fail-open 不会因守卫自身故障阻断。
12. **`sync_principles.py` 的 `skills()` 用 `iterdir()` 自动发现、计数用 `len(targets())`，无硬编码数字地雷** —— 加两个投放面确实是小改动，tasks 1.3/1.4 的估计合理（**前提是按 glob 实现**，见 F-22）。
13. **tasks ↔ requirements 追溯：SA-01~SA-10 逐条被至少一个任务覆盖** —— 抽查无遗漏（**§4 验证段的标签有断裂**，见 F-09）。
14. **D8 的 fail-closed 边界划在 openspec CLI 上是对的** —— 产物契约单一源，降级阶梯与如实报告纪律齐全。
15. **`proposal.md` 的假设列表〔TG-22〕三条写得诚实且准确** —— agentType 未实测 ✓、省 token 未实测 ✓、CLI 幂等已实测 ✓。**这是本文档的亮点**（问题是 Non-Goals 里另有两条未登记的信念，见 F-01/F-08）。
16. **拷问覆盖率指标的诚实边界划得对** —— `proposal.md:28` 已如实标注「结构性改善而非机械保证……不冒充机械门」，不另开 finding（只在 F-09 建议里提了「把它落成一条会红的 grep 检查」）。
17. **BASE-01/14/17/18/19/22/24/27 逐条核过内容站得住** —— 领域镜汇总（场景四类覆盖合理、假设列表含失效影响、任务双向追溯完整、fold-vs-defer 归属合理、TG-10 序列图 + TG-14 组件图均存在且大体与正文一致）。
18. **`openspec validate add-sdflow-spec --strict` 当前通过** —— 结构合法（但这只说明结构，不消除运行期问题，见 F-03）。

---

## 独立性与降级 —— 如实标注（MUST NOT 假绿）

| 项 | 状态 |
|---|---|
| 子代理机制 | ✅ 可用（host=claude 免探针）；5 镜全部真派出并返回 |
| 双声 | ✅ 全开无降级（codex 0.145.0 三次 exit 0 + Claude 子代理三次返回 + hr-tg voice exit 0） |
| **⚠️ 独立性污染** | **对抗镜 A 与对抗镜 C 在评审中读到了 `gstack-review.md`**（它已落在 change 目录里，两镜读四件套时顺带看到）。两镜均**主动声明**了这一点并说明「重点放在 gstack-review 未覆盖的角度」；对抗镜 A 的 F1/F2 是独立核验（打开源文档、实跑命令），对抗镜 C 的 #1 是独立实测（`wc -c` 48 个归档）。**但它们不再是完全冷的上下文**，其「与广审收敛」的部分应打折看待。领域镜、对抗镜 B、接地镜未提及读它。**下一轮应把 Step1 产物移出子代理可见范围，或在 prompt 里显式禁读。** |
| **⚠️ autoplan 相位并行** | Eng 与 DX 相位**并行**跑（偏离 autoplan 的严格串行），DX 只带 CEO 上下文、未带 Eng 结论。未观察到因此漏项（DX 独家的 `/clear` 冲突与 Eng 的架构面无交集），但如实登记。 |
| **⚠️ 接地镜产出弱** | 跑在弱档（haiku），漏掉 F-01 这条致级事实错误（归类为「运行时核不了」）。**独立=0** 已如实落进度量锚。 |
| 机械覆盖（本报告自身） | `outside_voice_guard.py` ✅ exit 0 · `hr_tg_intersect.py` ✅ exit 0 · `lens_metric_emit.py` ✅ exit 0 · `anchor_lint.py` 见文末 |

---

## 锚行

<!-- sdflow:step1-broad-review v1 mode="native" -->

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

<!-- sdflow:hr-tg v1 hit="TG-08,TG-17" declared="TG-05,TG-08,TG-10,TG-14,TG-15,TG-17,TG-18,TG-19,TG-21,TG-22,TG-23,TG-24" evidence="TG-08=proposal.md:65 一次引入 openspec CLI/agent 定义解析/resolve-models.sh 三个外部依赖面；TG-17=design.md:98 researcher 白名单含 Bash+WebFetch+WebSearch，构成写权与出境通道，与 proposal.md:71『TG-17 不命中』相悖" -->

<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="29" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="6" truncated="false" -->

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="17" 采纳="15" 裁掉="1" defer="1" 独立="4" sev="致5/高6/中2/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="21" 采纳="19" 裁掉="1" defer="1" 独立="2" sev="致5/高6/中6/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="7" 采纳="7" 裁掉="0" defer="0" 独立="3" sev="致1/高1/中4/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="0" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="18" 采纳="16" 裁掉="1" defer="1" 独立="0" sev="致5/高6/中4/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="2" sev="致1/高3/中1/低0" -->

---

## 收敛口 · 是否建议进设计 HARD-GATE

**不建议直接进门。** 建议顺序：

1. **先修三条事实错误**（F-01 `subagent_type` / F-02 canonical 冲突四文件 / F-03 `validate` 结构门）+ **一条内部矛盾**（F-04 `design.md:94` 措辞）——这四条不需要拍板，是照着改就行的硬伤。
2. **拍 Q1–Q4 四个问题**（拆分 / `/clear` / 分发层级 / 纪要承载力实测）。
3. **补 F-05 的工作树前置检查**与 **F-11 的状态机**——这两条决定管线在真实使用中会不会当场出事故。
4. 其余 `高`/`中` 项按拍板结果一并回改四件套，改动处标 `[spec-review-amendment]`。
5. 回改完成后**跑一轮窄复核（只审增量）再拍板**——本报告的 findings 只针对 `7f221c9` 这个盘面。

> 拍板后，主 session MUST 立即把 `ship-gate.design_approved` + `reviewed_sha`（`git rev-parse HEAD` 完整 40 位）**同一次写入**本文件头部 frontmatter，并按 SR-M 最终化上方 lens-metric 锚。
> ⚠️ 若拍板前四件套相对 `7f221c9` 有实质改动，MUST 先**单独 checkpoint 提交**该修订、取得其 sha，**再**回写 `reviewed_sha`（否则第一次跑 gate 就会判设计失鲜、当场 `REFUSE_START` 自锁）。
