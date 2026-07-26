# add-sdflow-spec

## Why

阶段一目前由三个分离入口拼接（opsx:explore 想事 → opsx:ff 生成 → grill-with-docs 拷问），存在三个实证过的结构性缺陷：①grill 只能人手动触发、极易静默跳过（memory: grill-not-skippable），跳过即把未拷问的设计送进设计审；②拷问发生在四件套成文**之后**，每轮命中都要回改四份文档，且草稿锚定效应让拷问退化为「框架内找茬」（dedupe-issues 实证：候选表建在被证伪 premise 上活过了成文）；③全程主 session 亲做，文件 dump 灌满上下文、四件套按主 session 档位输出价计费——强档模型（Fable 5/Opus 5）的判断力被大量花在机械活上。三个入口中两个是 openspec CLI 生成物、一个是仓外第三方集合（Matt Pocock skills，`~/.agents/skills`，非 git 管理、更新即覆盖），流程规范无法焊进它们。

## What Changes

**交付按三阶段推进，阶段间有验收门**〔spec-review-amendment · 设计门 Q1〕——**同一个 change 内**（scope = 一个完整内聚阶段结果「阶段一 spec 生产管线」，符合基准 4「不按同批来源拆」），但**归因由阶段门提供**：阶段二是否启用取决于阶段二自己的 A/B 结果，不预先押注。

### 阶段一 · 可靠性（无 subagent，主 session 亲写 = D2 的「薄编排」合法形态）

- **新增顶层 skill `sdflow-spec`**：单一入口「澄清 → 拷问 → 生成」管线，替代阶段一的三入口**使用路径**（三个原 skill 保留不动）。判断（澄清对话、对抗拷问、锚点纪要、决策纪要、终审）全部在主 session；**本阶段生成也由主 session 亲写**。
- **决策纪要 `decision-memo.md` 为承重件**：**Phase B 起手**即建 change 目录（FF-0 + `openspec new change` 前移，见 SA-05），Phase B 内部**增量落盘**（每条承重约束站稳即追加），B 收敛点定稿 + checkpoint。〔spec-review-amendment F-12 + 窄复核订正：原写「B 收敛落盘」，导致 B 进行中无落点、增量落盘无法执行〕
- **canonical 规则单一源同步**〔spec-review-amendment F-02 · 本阶段 P0，不可 defer〕——本 change 与**七处**既有权威源冲突，MUST 同 change 消除（完整清单与处置见 SA-11）：
  | 文件 | 冲突 | 处置 |
  |---|---|---|
  | `sdflow-init/assets/workflow/generation-process.md`（§四 推荐流水线） | 规定 `explore→ff→grill` | 加分支：已装 sdflow-spec 的仓走单入口；未装沿用三步 |
  | `sdflow-init/assets/workflow/workflow.md`（§三 关键设计决策 2 = **G1「全流程不用 `/clear`」**） | 与本 change 出口序列的 `/clear` 正面冲突 | **修订 G1**，见下方决议 |
  | `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md` | 生成物，继续教旧流程 | 改源后重生成 |
  | `openspec/specs/spec-workflow/spec.md:968-994` | **已有两条正式 Requirement** 涉阶段一衔接 | 见 Modified Capabilities |
  | `reference/quality-layering.md` | G1 的第二处载体（措辞不同，须单独处理） | 同步例外 |
  | `snippets/claude-section.md` 托管块 | 「ff 之后是 grill」条款仍要求 ff 后提示 grill | 加分支或显式声明保留 |
  | `ff-generation-constraints.md:17` | FF-0「已在 feature 分支就跳过」弱判据 | 改为三分支判定 |
- **G1 修订（设计门 Q2 决议 = 选项 A）**〔spec-review-amendment〕：**保留 `/clear` 出口序列，同 change 修订 G1** —— 在 `workflow.md` §三决策 2 与 `reference/quality-layering.md` 为「阶段一→阶段二」这一段写明例外与理由。**例外的依据只有两条**（cache 按模型隔离 + 产/审错档纪律），**G1 未覆盖它们**（G1 的论证只针对「独立性」，没谈成本与档位）；原 D6 的第三条依据「主审裁决需冷视角」**MUST 删除**——它已被 G1 正面回答（独立性由 fan-out 的 fresh 子代理提供，不由 `/clear` 提供）。
- **拷问不可跳过的诚实收窄 + 机械审计信号**〔spec-review-amendment F-04〕：消除 proposal/design 间的强度矛盾；D1 备选表补入 **T132**（`openspec/issues/todolist/2026-07-todolist.md:232`，OPEN，2026-07-11：「spec-review 起手机械核验 grill 已收敛信号，无信号→REFUSE_START」）并说明为何仍需本 skill。
- **本仓阶段一规范双通道改写**：①归属错误修正（「grill-with-docs 来自 superpowers 插件」实为 Matt Pocock skills 集合）改真相源 `sdflow-init/assets/snippets/claude-section.md`（`:118`）+ 经托管机制刷新本仓区块；②`sdflow-spec` 使用路径、**四入口选择规则**〔spec-review-amendment F-17〕与出口序列写入本仓 CLAUDE.md/AGENTS.md **非托管区**。
- **README skills 列表**更新 + 重跑 `setup.sh`。

### 阶段二 · 成本实验（agent 定义 + 外派，起手先过实测门）

- **新增三个 agent 定义** `sdflow-spec/agents/`〔窄复核订正：原写「两个」，与 TG-17 处置要求的 local/web 拆分自相矛盾〕：`sdflow-local-researcher`（仓内检索，无网络）、`sdflow-web-researcher`（联网调研，无仓库读取与 `Bash`）、`sdflow-spec-writer`（四件套单产物生成，`effort: medium`）；`model: inherit`，派发时填 `resolve-models.sh` 解析出的**具体模型 id**。
- 🔴 **起手 GO/NO-GO 实测门**〔spec-review-amendment F-01〕：写任何 producer 前先实测一次 `subagent_type: sdflow-local-researcher` 派发（**不是 `agentType`**——后者是 Workflow JS 的参数，`docs/subagent-definitions-plan.md:136-137` 明记该路径不采纳）。NO-GO 即红，**MUST NOT** 用「失败就验 fallback」把门变成恒绿。
- **`setup.sh` 扩展**：新写 `install_agents()` 铺 `~/.claude/agents/`（**不是**沿用 `install_into`，见 design F-10）。
- **`sync_principles.py` 投放面扩展**：agent 定义正文纳入通则托管块（**glob 发现**，非硬编码清单）+ `hack/tests/` 守卫同步更新。
- **A/B 三路对照实测**：legacy（旧三入口）/ thin（阶段一薄编排）/ subagent（阶段二），量**总** token、美元、墙钟、人工返工、阶段二 findings 数与采纳率。

### 阶段三 · 产品化（阶段二达标才做）

- **agent 定义分发层级 = 全局 `~/.claude/agents/`**（设计门 Q3 决议）〔spec-review-amendment〕。design D3 MUST 补明反驳 `docs/subagent-definitions-plan.md:303-308`「先放本仓验证」倾向的理由，并给三个 agent 的 `description` 写成**排他式**（仅由 `/sdflow-spec` 编排派发）——因为 SKILL 的 `disable-model-invocation` 挡不到 agent 定义，全局 agent 会进入每个 session 的可选名册，而 `sdflow-spec-writer` 持有 `Write`。
- 〔窄复核订正：**sunset 条件已前移到阶段一** —— 阶段二失败恰是新旧并存最久的分支，把退出条件挂在「阶段二达标才做」的阶段三下会使其永久搁浅。见 tasks 3.4〕按阶段一已落定的阈值判定旧入口是否进入 sunset。
- bundle 下游推广（`sdflow-init update` 推 canonical 改动至消费项目）。

## Capabilities

### New Capabilities
- `spec-authoring`: 阶段一 spec 生产管线——澄清/拷问/生成三相位的行为契约、判断与机械的外派分工线、决策纪要承重件（/clear 无损）、相位状态机与重入、错误降级与 Codex 宿主降级、出口衔接序列。

### Modified Capabilities
〔spec-review-amendment F-02 · 原写「无」，理由「现有 specs 的 requirement 层不含阶段一入口约定」**与事实不符**〕

- `spec-workflow`: `openspec/specs/spec-workflow/spec.md:968-994` 已有两条正式 Requirement 涉及阶段一衔接（雾量三段分流的 wayfinder→ff 衔接契约、grill 对已决分支瘦跑）。本 change MUST 声明新入口与它们如何**共存与路由**，不得留空。

## Success Metrics

〔spec-review-amendment F-08：原指标 #1 测的是**单价表常量**（只要派到 Sonnet 就必然「达标」），测不出「这次重构是否让阶段一变便宜」——已改为总成本口径〕

- **阶段一总成本** — 基准：A/B 三路对照里的 legacy 与 thin 两路实测值 → 目标：subagent 路的**总** token 与总美元均不劣于 thin 路 — 度量：一次 A/B 覆盖 **legacy / thin / subagent** 三路跑同一个真实需求，计入 researcher + writer + memo 往返 + 终审读回的**全部**开销。⏰ 8/31 前的测量须按 Sonnet 稳态价 $15/M 折算（现有 $10/M 促销价到期，否则高估约 33%）。
- **下游成本不回归** — mid 档生成的 change，其阶段二 spec-review 的 findings 数与采纳率不显著劣于强档亲写的历史基线（retro 脚本已在算此量，边际成本近零）。若 findings 涨幅吃掉生成侧节省，D2 退回薄编排。
- **拷问覆盖率** — 基准：grill 人工触发、可静默跳过（已实证发生）→ 目标：拷问为管线内建默认路径（跳过须主动偏离指令；**结构性改善而非机械保证**——指令层约束由执行方自报，按诚实边界纪律不冒充机械门）— 度量（机械审计信号）：`decision-memo.md` 存在 + 必填小节非空的 **grep 门**（会红的检查，非人工抽查）〔spec-review-amendment F-09〕。
- **阶段二冷启动无损率** — 基准：部分决策 why 滞留对话上下文 → 目标：`/clear` 后 spec-review 所需 why 100% 可从落盘产物获得 — 度量：dogfood change 的 spec-review 报告中「上下文缺失/需回问」类 finding = 0。**样本 N=1 且为自评**，报告须如实标注「非统计显著」〔spec-review-amendment F-09〕。

## 需求优先级〔TG-19〕

〔spec-review-amendment · 设计门 Q1：改为三阶段口径〕

- **阶段一 P0**：skill 本体三相位管线（薄编排形态）· 决策纪要与增量落盘 · **canonical 七处同步（含 G1 修订）** · **入口选择规则（SA-14）与旧入口 sunset 条件** · 相位状态机与工作树前置检查 · 机械审计信号（memo grep 门 + `openspec validate --strict`）
- **阶段一 P1**：本仓 CLAUDE.md/AGENTS.md 规范改写（含四入口选择规则）· 归属错误修正 · README 列表
- **阶段二 P0**（阶段一验收后启动）：`subagent_type` GO/NO-GO 实测门 · agents 定义 × 3 · `install_agents()` + 首个 setup.sh pytest · sync_principles glob 投放面 · A/B 三路对照
- **阶段三 P0**（阶段二达标后启动）：全局分发定案 · 旧入口 sunset 条件 · bundle 下游推广
- **P2**：checkpoint 相位锚——**提高阶段一的墙钟归因率**〔spec-review-amendment F-20：原理由「补 retro 数据阶段一无独立打点的缺口」**与仓内数据矛盾**，`openspec/retro/report.md:77,79` 有 `ff 9%` / `grill 2%` 打点且已参与聚合；真实缺口是 `unknown` 桶占 56%（`report.md:74`）〕

## 假设〔TG-22〕

- **agent 定义经 `subagent_type` 派发 + `effort` frontmatter 生效**〔spec-review-amendment F-01：原写 `agentType`，那是 Workflow JS 的参数（`docs/subagent-definitions-plan.md:320`），而同文 `:136-137` 明记该路径不采纳；本仓三处先例均用 `subagent_type`〕——`effort`/`model: inherit` 的合法性依据为 claude-security 官方插件 7 实例静态核验（`docs/subagent-definitions-plan.md §4.6`，已复核准确），**但派发链路本仓未实测**。失效影响：阶段二起手门判 NO-GO，管线停在阶段一（薄编排）——**不静默降级为 fallback**（见下条）。
- **fallback 的工具边界等价性——已被证伪，改为不假设**〔spec-review-amendment F-01/hr-tg V-3〕：原设计把「agent 定义缺失 → 通用子代理 + prompt 内联通则」当等价降级，但 `docs/subagent-definitions-plan.md:116-123` 明确直接 Agent 路径**无法限制工具集** ⇒ 该 fallback **撤掉了唯一的工具权限边界 = 降级即提权**。改为：无法证明等价时，researcher 降级为**主 session 亲查**、writer 降级为**主 session 亲写**，MUST NOT 用权限更宽的通用子代理当安全 fallback。
- **总成本方向未实测**〔spec-review-amendment F-08〕——原写「省 token 30-40%」混淆了 token 数与单价：串行 fresh-context writer 重复读 instructions/memo/依赖产物、主 session 终审读回四件套，**总 token 很可能上升**。失效影响：阶段二 A/B 判不达标，停在阶段一；质量收益（拷问前置 / `/clear` 无损）独立成立。
- **mid 档生成不抬高下游评审成本**〔spec-review-amendment F-08，原未登记〕。失效影响：见 Success Metrics 第二条，D2 退回薄编排。
- **并存无触发面冲突**的真实风险方向〔spec-review-amendment F-04，原未登记〕：风险不是「误触发抢占」，而是**新入口模型唤不起、旧入口模型唤得起** ⇒ 动机①（grill 可绕过）未被本 skill 解决。缓解只能来自阶段一的 canonical 规则更新 + T132 类机械门。
- **openspec CLI 行为在版本升级后保持稳定——不假设**〔spec-review-amendment F-13〕：**最后验证版本 = 1.5.0**；npm registry 最新已是 **1.6.0（2026-07-10 发布）**，且 `openspec-upgrade/SKILL.md:192` 装 `@latest`、仓内无 pin。⇒ 生成子代理自调 `instructions --json` 时 MUST 做最小 schema 断言（必需字段存在性 + 类型），不兼容即 fail-closed 并报告实际版本。
- **openspec CLI `instructions` 幂等只读、载荷 3.5-6KB**——已实测（1.5.0），非假设，列此为证据锚。

## 开放问题〔TG-21〕

〔spec-review-amendment F-31：三条统一补负责人 + 截止〕

- **A/B 三路对照的实测基线**：阶段二起手前由人跑一次 legacy/thin/subagent 对照（负责人：用户；截止：**阶段一验收门通过后、阶段二动工前**）。
- **agent 定义是否纳入 `sdflow-init` 铺设物随 bundle 分发**：v1 定为全局 `~/.claude/agents/`（设计门 Q3 已决）；是否改为随 bundle 分发待阶段三决策（负责人：用户；截止：阶段三启动时）。
- **bundle canonical 改动的下游推广时机**：阶段一改源，阶段三经 `sdflow-init update` 推下游（负责人：用户；截止：阶段三）。

## 成本估算〔TG-24〕

〔spec-review-amendment F-08：原写「40 轮对话、四件套 ~65KB 量级」，全仓 `grep` **除本文件外零命中**、无出处；实测 48 个归档 change 的四件套字节数**中位数 42,536 字节**（65KB 在第 85 百分位），**本 change 自己实测 42,351 字节**〕

按 42KB 中位数（≈20–25K output tokens）折算，**生成环节**的档位下调节省上限约 **$0.9**（Fable 主 session）/ **$0.25**（Opus 主 session）——占单次阶段一成本的个位数百分比。**真正的成本大头是主 session 的多轮 input 与 thinking 输出**，而本方案（拷问前置 + 亲笔锚点纪要）**增加**主 session 轮次。⇒ **成本不是本 change 的主要收益**；主要收益是「拷问前置」与「`/clear` 无损」两条质量项。绝对值目标由阶段二 A/B 实测给出，本文不预设。

## Non-Goals

- **不改 openspec CLI 与四件套 schema**——可证伪假设：现有 `instructions --json` 载荷足以驱动生成子代理产出合格产物（已实测载荷 3.5-6KB **于 1.5.0**；若 dogfood 中产物质量不合格且归因于载荷缺失，此假设被证伪）。
- **不动阶段三（ship 链）**——阶段二 spec-review 本体不改，但**其上游 canonical 规则（G1）本 change 要改**〔spec-review-amendment F-02〕。
- **不删除/修改 opsx:explore、opsx:ff、grill-with-docs、grilling、domain-modeling**——但**阶段三 MUST 给出 sunset 条件**〔spec-review-amendment F-17〕；无退出条件的永久并存已被评审判为「维护成本永久叠加」。
- **不做 Codex 宿主适配（agent 定义对应物）**——可证伪假设：Codex 下降级为主 session 亲做可接受。⚠️ 附带未核项：`disable-model-invocation: true` 在 Codex 宿主的语义未验证，而本仓已有该字段非直觉行为的实测（`openspec/changes/archive/2026-07-10-matt-workflow-integration/impl-notes.md:3-14`）〔spec-review-amendment F-32〕。
- **不做 per-子代理 token 归因度量**——但阶段二 A/B **MUST** 量总 token 与总美元（粗粒度 `/usage` 前后对比不足以支撑方向性结论，这一点已被 roadmap P2 的未闭环实证：`openspec/roadmaps/workflow-cost-optimization/roadmap.md:84`）〔spec-review-amendment F-08〕。

## Impact

- **新增**：`sdflow-spec/SKILL.md`、`sdflow-spec/references/`、`sdflow-spec/agents/{sdflow-local-researcher,sdflow-web-researcher,sdflow-spec-writer}.md`（阶段二）、`hack/tests/test_decision_memo_gate.py`（阶段一）、`hack/tests/test_install_agents.py`（阶段二，全仓首个 setup.sh 测试）
- **修改**：`setup.sh`（新 `install_agents()` 段）、`hack/sync_principles.py` + `hack/tests/test_sync_principles.py`（glob 投放面）、`sdflow-init/assets/snippets/claude-section.md`（归属修正 + 托管块 grill 条款）、**`sdflow-init/assets/workflow/{workflow.md,generation-process.md,WORKFLOW-GUIDE.md,reference/quality-layering.md,ff-generation-constraints.md}`** + `assets/hooks/ff0-branch-guard.py`〔spec-review-amendment F-02 + 窄复核补齐至七处〕、`openspec/specs/spec-workflow/spec.md` 的衔接 Requirement、`CLAUDE.md`/`AGENTS.md`（非托管区 + 删「15 个 SKILL.md」硬编码数字，改由脚本自报）〔spec-review-amendment F-28〕、`README.md`
- **依赖**：openspec CLI（**最后验证 1.5.0**，1.6.0 未验证，须 schema 断言）；Claude Code agent 定义解析（`~/.claude/agents/`，阶段二起手实测门把关）；`resolve-models.sh` 档位变量（既有）
- **技术栈标注**〔TG-01/02/03 判定〕：纯 Markdown 编排 + Python/Bash 构建脚本，不命中 backend/embedded/frontend 领域清单
- **不受影响**：阶段三编排器、openspec CLI 生成的官方 skills、`~/.agents/skills` 第三方集合

## Compliance

〔spec-review-amendment F-06：**TG-17 改判命中**，原写「不命中」〕

**TG-17（信任边界 / 敏感数据）命中** —— 原设计单体 researcher 的工具面同时含仓库读取、`Bash`（**非只读**：可 `>` 重定向、`rm`、`git commit`、`curl -X POST`；工具 allowlist 不能限制 Bash 子命令）与 `WebFetch`/`WebSearch`（出境通道）。⇒ design MUST 补 **BASE-28「安全与数据保护」**段，覆盖：① Bash 权限收窄或诚实边界声明；② 出境 secret scan（复用 `openspec/specs/host-adaptive-execution/spec.md:82-96` 既有的 secret scan + 读围栏 + 拒发语义，MUST NOT 新造）；③ Web 内容一律作**不可执行数据**（间接 prompt injection 防线）；④ `resolvedOutputPath` 的 canonicalization 与 change-root containment（第三方 CLI 输出直接当写入目标 = confused deputy）。

其余边界合规（adr/0005 dev-runtime checkout 纪律、通则托管单一源机制、host-adaptive-execution「skill 引用档位变量不内联模型名」、**workflow.md G1**〔spec-review-amendment Q2，原漏核〕）在 design.md 按 D-6 逐条声明。
