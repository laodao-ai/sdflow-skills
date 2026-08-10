# sdflow workflow 与 skill 优化调研（2026-08）

> **性质**：一次「第一性原理 + 业界最佳实践对照」的全量调研快照（2026-08-10），自足成文——
> 不依赖其它文档即可获取全部结论与证据。配套行动计划见
> `openspec/roadmaps/workflow-optimization-2026-08/`（roadmap 文档包）。
> **方法**：① 盘家底（retro 报告、issues 池、既有优化提案与 roadmap 的落地状态）→
> ② 联网调研业界共识（10 个已核验一手来源 + 若干搜索面来源，分档标注）→
> ③ 以「改进闭环的第一性原理」合并为缺口清单与优先级。

---

## 0. 总判断（先给结论）

**本仓不需要改架构方向；需要的是把自己的改进闭环走完最后一步。**

第一性原理视角：这套 workflow 是一座「产出已验证 change」的工厂，其改进闭环 =
**采集端**（lens-metric 落锚、checkpoint 时间戳、retro 聚合）→ **决策端**（依数据砍留镜、
重排优先级、重分诊）。调研发现：**采集端过剩、决策端欠账**——

- 数据采了：13 面镜出现轮数 ≥10 触发「待复评」阈值，retro 报告显著标出；
- 复评没人做：砍留所需的两个判据（token 维度量、实修率指标）至今是 open todo；
- 提案写了：2026-07 的 22 项优化建议书大半落地，但四条 P0 被一句与事实不符的理由批量关闭。

业界调研（§4）则确认：本仓的五根架构柱子（冷上下文独立评审、子代理隔离换独立性、
静态按步分档、人类门上移设计侧、机械活交脚本）全部被 2026 年的官方指导与文献再次背书，
**推倒重构没有依据**；业界增量收敛为 4 个净新增可吸收点（§5）。

---

## 1. 家底：已答过一轮的部分（避免重复发明）

### 1.1 既有优化提案（04 提案）及其落地状态

`docs/sdflow-fable5/04-optimization-proposal.md`（2026-07-10）已做过一次同题调研，产出
22 项建议、四方向（A 成本工程 / B 人类门减负 / C 评审可靠性校准 / D 结构增强），全部
曾入池为 T97–T128。落地状态逐项核对如下（2026-08-10 实况）：

| 04 提案项 | 对应 issue | 状态（2026-08-10） |
|---|---|---|
| #1 档位强制落地（advisory→enforced） | T97 | ✅ 已落地（wco P2，`add-codex-host-support`：双机队矩阵 + resolver + fail-closed） |
| #2 prompt 前缀缓存稳定化 | T98 | ⚠️ **被错关**（见 §2.2） |
| #3 确定性检查前置 fan-out 准入门 | T99 | ⚠️ **被错关**（见 §2.2） |
| #4 微变更快速通道 | T100 | ✅ 部分落地（wco P1 `adaptive-workflow-routing`：code-review 无逻辑面白名单免 Step2；全流程三档未做，关闭可接受） |
| #5 设计门报告三层摘要头 + 拍板三问 | T101 | ⚠️ **被错关**（见 §2.2） |
| #6 每镜 effort scaling 预算 + 输出封顶 | T103 | ⏳ open（在池未排期） |
| #7 retro 补 token 维度量 | T104 | ⏳ open |
| #8 裁决二元化 pass/fail + critique | T106 | ⏳ open（优先级应升，见 §2.3） |
| #9 位置去偏（HIGH 级换序重跑） | T107 | ⏳ open |
| #10 镜价值指标升级实修率（resolution rate） | T108 | ⏳ open |
| #11 「测试大改=红旗」硬规则 | T109 | ⏳ open |
| #12 高危路径升级例外 | T116 | ⏳ open |
| #13 spec 模版 EARS 句式 + 三必填槽 | T115 | ⏳ open |
| #14 明码自动决策原则清单 | T110 | ⏳ open |
| #15 tasks 依赖 DAG 化 + frontier 受限并行 | — | ✅ 已落地（wco 阶段 C，`sdflow-implement` frontier 宿主条件化并行） |
| #16 fog-of-war 进 roadmap 模版 | T119 | ✅ 实质落地（roadmap 模版「近细远雾」已是硬约束；T119 仍 open 可关） |
| #17 expand–contract 宽重构协议 | — | ✅ 实质落地（sdflow-implement 已有 expand-contract 迁移批次概念） |
| #18 规则条款元维护 | T114 | ⏳ open |
| #19 对抗镜措辞收紧 | T102 | ⚠️ **被错关**（见 §2.2） |
| #20 弱档 validator 复核层 | T112 | ⏳ open（优先级应升，见 §2.3） |
| #21 thinking/effort 预算按步分档 | T105 | ⏳ open（实现成本已降一个量级，见 §2.3） |
| #22 跨工件一致性机械检查 | T117 | ⏳ open |

另：返工轮次治理（后于 04 提案识别的「测试耗时真凶 = 返工轮次」三病灶）已实质吸收——
loop-breaker 判据 (b) 硬上限（同一文件累计 ≥3 轮命中即熔断，防「同一根因每轮换语法分支
绕过指纹」）、基准 5（无界语法禁手搓）下沉到出票层机械拦截、每轮增量限定 re-review，
均已焊进 `sdflow-implement/SKILL.md`（curb-rework-loop-cost / adr/0035）。

### 1.2 issues 池与 roadmap 现状

- 无在途 change；73 条 open todo + 1 open bug（B24，sdflow-architecture 扫描口径，与本题无关）。
- `issues-triage-2026-08` roadmap：B1–B16 清理批次全关（DONE/WONTDO），剩余 ~67 条全在
  「延后池」（评审编排大改 / implement 重构 / bundle 增强 / 度量 / Codex，条件触发）。
- 已归档 roadmap：workflow-cost-optimization（P0–P5 全交付）、mechanical-layer-hardening、
  high-value-issues-cleanup、openspec-1.7.0-followup。

---

## 2. 六缺口（本仓证据侧）

### 2.1 缺口①：镜组合复评——数据到阈值已久，判据缺位、无人执行（最高 ROI）

retro 报告（`openspec/retro/report.md`，69 change / 评审墙钟 ~595.6 hr / 50 个带真锚）
显著标出 **13 面镜出现轮数 ≥10 触发待复评**，注明「只提示不判断不自动砍——人读后自行
决定保留/降采样/淘汰」。该复评从未执行。关键镜位数据（per-镜 lens-metric 聚合）：

| layer | lens（host/runner/site） | 轮数 | Σfindings | 采纳率 | Σ独立 | 独立/轮 | 判读 |
|---|---|---|---|---|---|---|---|
| code-review | **history**（claude/claude） | 34 | 21 | 57% | 6 | **0.18** | 明显偏弱 |
| code-review | **broad**（claude/claude） | 31 | 18 | 72% | 8 | **0.26** | 偏弱 |
| code-review | adversarial（claude/claude） | 35 | 191 | 73% | 100 | 2.86 | 承重墙 |
| code-review | outside-voice（claude/codex/code-voice） | 31 | 105 | 81% | 51 | 1.65 | 承重墙 |
| code-review | outside-voice（claude/codex/hr-tg） | 16 | 54 | 75% | 23 | 1.44 | 强 |
| code-review | domain（claude/claude） | 33 | 77 | 70% | 25 | 0.76 | 中 |
| spec-review | adversarial（claude/claude） | 38 | 365 | 92% | 173 | 4.55 | 承重墙 |
| spec-review | broad（claude/claude） | 38 | 402 | 87% | 169 | 4.45 | 承重墙 |
| spec-review | domain（claude/claude） | 17 | 82 | 96% | 35 | 2.06 | 强 |
| spec-review | grounding（claude/claude） | 38 | 74 | 79% | 24 | 0.63 | 中 |
| spec-review | outside-voice（claude/claude/design-voice，同族） | 11 | 42 | 88% | 10 | 0.91（独立率 24%） | 偏弱 |
| spec-review | outside-voice（claude/codex/design-voice） | 30 | 202 | 79% | 41 | 1.37（独立率 20%，被裁 32 条全表最高） | 中偏弱 |
| spec-review | outside-voice（claude/codex/hr-tg） | 12 | 50 | 94% | 17 | 1.42 | 强 |

本仓既有实证与此互相印证：跨模型 voice 曾在单个 change 的 7 条采纳里独家贡献 6 条、
两条高危（安全门 fail-open / 全局 hook 绕过）同族镜全漏（add-sdflow-spec 代码审）；
业界文献支撑见 §4.3「popularity trap」。

**复评的两个前置判据仍未落地**：T104（retro 补 token 维——checkpoint 落 token 快照锚 + join）
与 T108（镜价值指标升级实修率——retro join 修复 commit，可对历史存量回算）。20260717 快照
（`docs/sdflow-fable5/20260717.md`）当时就指出「现在拍板只能拍感受」，至今未变。

**反向护栏（复评时 MUST 带上）**：「冷层」≠「弱镜」。本仓有两条实证——
① sdflow-retro 的致命 F1 由冷主审独家挖出；② harden-gate 的 4 条跨 ticket 缺口
（ADR 横跨多出口 / 契约横跨多报告 / 整块注释多票累积改动）六轮双轴审全漏、唯冷层全 diff
审出。复评砍的是「同族温镜的边际产出」，不是「冷启动独立视角」这个机制本身。

### 2.2 缺口②：四条 P0 被批量错关（数据完整性问题，重开成本极低）

T98 / T99 / T101 / T102 四条全部以同一句 `closed_reason: "wco roadmap P0-P5 全交付"` 关闭为
WONTDO，且 `resolved_by: null`。**但 wco roadmap 的实际里程碑（P1 白名单、P0 基线、P2 档位、
P3 接地镜流水线、P4 批次策略、P5 返工治理、阶段 C frontier）不含这四项的任何一项**；已逐条
grep 过评审 SKILL.md 正文确认：三层摘要头、fan-out 前确定性准入门、前缀缓存稳定化均不存在。

四条中三条在本次业界调研中拿到直接背书（详见 §4）：

| issue | 内容 | 业界背书 |
|---|---|---|
| T101 | 设计门报告三层摘要头 + 结构化拍板三问 | 直击最大墙钟块：设计审占评审墙钟 25%（收尾 27% 被离群 change 拉高后紧随其后），且人读报告主导；单 change 峰值：dedupe-issues-scripts-shared-layer 的 spec-review 段 955 分钟、fix-windows-encoding-crash 769 分钟、fix-probe-scan-precision 719 分钟、harden-implement-review-loop 758 分钟 |
| T102 | 对抗镜措辞收紧（只报影响正确性/明示需求的 gap） | Anthropic 官方最佳实践页点名 reviewer over-reporting，给出的解法与 T102 原文一致（§4.2） |
| T98 | prompt 前缀缓存稳定化 | prompt caching 为业界公认成本第一优先级，缓存部分 ~90% 降幅，代价即前缀 byte-stable 纪律（§4.4） |
| T99 | 确定性检查前置 fan-out 准入门 | 业界「全跑 vs 采样」主流答案 = 分层：机械检查全量前置、语义审在后（§4.4） |

**建议动作**：重开四条、以诚实理由逐条重分诊（哪怕结论仍是 WONTDO，理由也该是真的）。
分诊参考：T101/T102 低成本高背书，倾向做；T98 需先审计现有 dispatch prompt 的前缀构成；
T99 需处理「评审对象是 change 而 CI 绿否是仓级信号」的粒度错位。

### 2.3 缺口③：在池批次的优先级应重排（两个外部条件变了）

**条件一：置信过滤的地基被文献动摇。** 现行 code-review Step3 用「<80 置信硬滤」，
建立在镜的自报置信上——而 LLM judge 自报置信被证明系统性高估正确性（arXiv 2508.06225，
§4.3）。文献方向恰是 T106（二元 pass/fail + critique，弃连续置信分）+ T112（第二模型
validator 复核 findings 引用真实性），或至少把置信分降级为排序信号、改用 severity 三级
（Action Required / Recommended / Minor）做门。**这是全部缺口里唯一一处「现行机制的
正确性根基被外部证据削弱」的地方**，T106/T112 优先级应显著上调。

**条件二：宿主原生支持 per-agent effort 分档。** Claude Code 的 Agent 派发已支持
per-call `effort`（low/medium/high/…）与 agent 定义 frontmatter 的 `model`/`effort` 字段
（本仓 `sdflow-spec/agents/*.md` 已在用 `effort: low`）。T105（thinking/effort 按步分档）
与 T103（每镜 effort 预算 + 输出封顶）在 04 提案估算时需要自建机制，现在实现成本降了
一个量级——优先级应上调。

### 2.4 缺口④：宿主能力超前于工作流假设（条件记录，暂不动刀）

04 提案写于 2026-07-10。此后宿主长出的、与本仓「基准 1：一致性机械化优先」直接相关的原语：

- **Workflow 确定性编排**：确定性控制流（pipeline/parallel/barrier）+ schema 强制结构化
  输出 + token 预算控制。两个评审编排器目前是 663/546 行 SKILL.md 散文驱动主 session 做
  「单批 dispatch → barrier → 聚合」——控制流本身有确定性信号、属机械活；输出格式漂移
  现靠 anchor_lint / parity 门事后拦，schema 校验可把该面直接消灭。
- **Stop hook / `/goal` 四级 gate 阶梯**（§4.2）：turn 级机械 gate，比 SKILL.md 指令层
  MUST 更硬的载体——verify 反假绿、checkpoint 纪律的一部分可下沉。

**不立即做的理由**：这正是分诊 roadmap 延后池里的「评审编排大改」（设计级重构）；且
Codex 宿主无 Workflow 原语，做了就是双路径双维护。**动作 = 落一条 todo 记录条件变化，
下次评审编排必须动刀时一并重估**。

### 2.5 缺口⑤：SKILL.md 自身的 context 成本——考古层清理未覆盖 skill 正文

7/14 个 skill 的 SKILL.md 超 500 行（implement 819、roadmap 712、code-review 663、
done 565、architecture 562、spec-review 546、spec 528），每次触发全文进 context；
零个 skill 用 `references/` 渐进披露（仅 assets/ 模版类）。

**界线要划清**：本仓的内联是有意为之——通则托管块必须在场（防「不会想到要去查」的
失效模式），规则集已经外部化到全局 canonical 经 resolver 解析，这两块不该动。真正的
可减面是**考古层**：SKILL.md 正文里大量 `〔impl-review-fix xxx〕〔C4·R3〕〔mlh-p4 T81〕`
类修订标注是给评审者/历史读者的，不是给执行者的指令——DOC-1 判据（「只有读过上一版的
人才需要的句子，不属于正文」）完全适用。注意：DOC-1 规则文本（`openspec/rules/
doc-authoring.md`）从制定起即声明覆盖 SKILL.md——缺的是**审计执行**，不是规则扩面；
现行 T169 只管 change 四件套正文的清理动作，SKILL.md 从未被系统审计过。审计价值可留
git blame；留不留哪些锚是人的拍板。

### 2.6 缺口⑥：平台基线漂移（低成本，记录即可）

`docs/sdflow-fable5/` 整套调研以 Opus 4.8 为目标平台；2026-08-10 主力模型已切 Fable 5。
model-tiers 的成本假设、通则两源的措辞分档（项目味源按 Opus 5 精简陈述式、skill 味源
为下发子代理保持清单式）均建立在旧基线上。**动作 = 攒够 Fable 5 时代的 retro 数据后
重校一次**，现在不动。

---

## 3. 收尾/设计审墙钟数据备考

评审墙钟分布（69 change 口径）：收尾 27% + 设计审 25%（合计 52%）。注意：收尾占比被
离群 change `scoped-test-per-task`（done 段 8883.8 分钟、总 165.5 hr、仅 3 个 checkpoint，
归因质量本身是债）显著拉高；正常 change 的 done 段中位数在 7–15 分钟量级，**不构成
独立优化标的**。设计审 25% 由人读报告主导，是 T101 的立项依据。

---

## 4. 业界调研（2026-08-10；[已核验] = 逐页打开读过原文，[搜索面] = 仅经搜索结果核实存在与主旨）

### 4.1 Spec-driven development 业界现状

**共识结论：**

- **GitHub Spec Kit：从文档工具走向可扩展平台，重心在「skills 化分发 + gate 机械化」。**
  近半年（v0.15/v0.16）新增：agent-native 运行时 hooks（含 context injection）；Copilot
  集成默认改装 skills（`.github/skills/speckit-*/SKILL.md`）而非 commands；gate 步骤新增
  `verdict_input`（把 gate 判决绑定为 workflow 输入）；`specify init --extension` 扩展机制；
  一批安全加固（TOCTOU、stdin 上限等）。[已核验] https://github.com/github/spec-kit/releases
- **OpenSpec（本仓上游）：OPSX「artifact-guided fluid workflow」取代刚性 phase，并开始给
  流程做豁免阀。** 近期版本要点：`/opsx:update`（修订在途 change 并保持四件套 coherent）、
  `skip_specs: true`（非 spec 变更跳过 spec 产物）、archive 的 `retire_capabilities: true`、
  Stores（简化 specs/changes 组织）、30+ 工具统一走 skills 架构。[已核验]
  https://github.com/Fission-AI/OpenSpec/releases
- **Kiro (AWS)：spec 引导化 + 自动执行 + hooks 全局化。** `/spec new` 起草前先访谈式追问
  （与本仓相位 A/B 同构）；plan 批准后直接自动执行；`~/.kiro/hooks/` 全局 hooks；Powers
  支持开放 Agent Plugin 格式跨工具共享。[已核验] https://kiro.dev/changelog/ 。另有「从
  EARS 需求提取可测性质生成 property-based tests」的机制描述。[搜索面]
  https://builder.aws.com/content/3DbBI7LQgNIcs6UUj7IPPvqFHOp/aws-kiro-the-agentic-ide-that-makes-specs-the-unit-of-work
- **Tessl：把 spec 生态化——「usage specs」注册表。** Framework（spec 作为代码库长期记忆，
  `@generate`/`@describe` 双向）+ Spec Registry（10,000+ 开源库的「怎么用」规范，治 agent
  幻觉 API / 版本混淆）。方向是 spec 不只描述「要建什么」，还描述「依赖怎么用」。[已核验]
  https://tessl.io/blog/tessl-launches-spec-driven-framework-and-registry/

**对本仓启示**：四件套 + 机械 gate 已站在主流方向上；可借鉴的增量是 OpenSpec 的
`skip_specs` 式小变更豁免阀（对应业界对样板税的反弹，见 §4.5）和 Spec Kit 的
`verdict_input`（gate 判决作为结构化输入喂给下游步骤，与本仓 hand-off.md 思路同构，
可考虑机械化绑定）。

### 4.2 Anthropic 官方最新指导

**共识结论（均出自官方文档/工程博客，[已核验]）：**

- **「给 Claude 一个可跑的 check」被升格为第一条最佳实践，且给出四级 gate 阶梯**：
  prompt 内自验 → `/goal`（每 turn 后独立 evaluator 复查）→ **Stop hook**（脚本 gate
  阻止 turn 结束，8 次连续 block 后 override）→ **verification subagent / 二次意见**
  （fresh 模型试图**反驳**结果，「干活的不给自己打分」）。
  https://code.claude.com/docs/en/best-practices
- **官方明确警告 reviewer over-reporting**：被要求找 gap 的 reviewer 即使工作没问题也会
  报 gap，追着每条 finding 修会导致过度工程（多余抽象层、防御代码、不可能场景的测试）——
  解法是限定「只报影响 correctness 或 stated requirements 的」。同页。
- **Context engineering 三大长任务技术**：compaction（可用 CLAUDE.md 定制保留项）、
  structured note-taking（context 窗口外持久化 NOTES/todo）、sub-agent 架构（子代理只回传
  1000–2000 token 浓缩）；总原则 = attention budget 有限，just-in-time 检索优于预载。
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **多 agent 系统的量化边界**：orchestrator-worker 比单 Opus 提升 90.2%，但耗 15× token；
  token 用量解释 80% 性能方差；**强依赖、需共享全量上下文的任务（如大多数编码）不适合
  多 agent 并行**——可并行读任务（研究/评审）才适合。给 subagent 的任务必须含目标、
  输出格式、工具指引、边界，否则重复劳动或漏关键信息。
  https://www.anthropic.com/engineering/multi-agent-research-system
- **新原语**：`/btw`（侧问不进 context）、rewind +「Summarize from here」局部 compaction、
  agent teams（多 session 共享任务/消息 + team lead）、auto mode（分类器审批替代逐条点击）。
  https://code.claude.com/docs/en/best-practices

**对本仓启示**：本仓多数实践（fresh 子代理评审、脚本 gate、浓缩回传）已与官方对齐甚至
更严。可能未吸收的三点：① Stop hook / `/goal` 把 verify 从「流程步骤」下沉为「turn 级
机械 gate」（比 SKILL.md 指令层约束更硬）；② reviewer prompt 里显式加「只报影响正确性/
既定需求的 finding」约束——与置信过滤互补，从源头抑制 over-reporting 而非事后滤（= T102）；
③ compaction 定制指令（CLAUDE.md 写明 compact 时必保留什么，与 T256 PreCompact hook 同题）。

### 4.3 多 agent 评审/验证的研究结论

**共识结论：**

- **LLM judge 的自报置信度系统性高估正确性（overconfidence）**——「predicted confidence
  significantly overstates actual correctness」；论文提出 TH-Score 量化偏差、LLM-as-a-Fuser
  集成框架做校准，核心主张是从「追求判断准确率」转向「confidence-driven, risk-aware」评估。
  [已核验] https://arxiv.org/abs/2508.06225
- **同族模型 ensemble 存在「popularity trap」**：训练分布相近的模型会收敛到同样「句法
  可信但语义错」的答案，多数投票反而滤掉少数派的正确解；diversity-based 选择可恢复接近
  独立 ensemble 的收益。judge 间一致性本身很低（SOTA judges Fleiss' Kappa ≈ 0.3）。
  [搜索面] 综述：https://arxiv.org/pdf/2510.24367 （LLM-as-a-Judge for Software Engineering）
- **对抗式二次验证获官方背书**：Anthropic 明确推荐「fresh 模型尝试反驳结果」的
  verification subagent 模式，理由是 fresh context 不带产出方的推理偏置。[已核验]
  https://code.claude.com/docs/en/best-practices
- **公认无效**：裸自报置信当机械信号、同族模型多数投票、无 evidence 锚的 judge 结论。
  **公认有效**：跨模型 diversity、校准后置信、finding 绑 evidence、severity 分级输出。

**对本仓启示**：「跨模型 outside-voice 独家产出碾压同族温镜」的本仓实测与 popularity trap
研究互相印证——预算紧时保 voice 砍同族镜有文献支撑。风险点：**<80 置信过滤建立在自报
置信上，而自报置信正是被证明 miscalibrated 的那个量**——业界方向是用第二个模型做
fuser/校准，或至少把置信过滤降级为「排序信号」而非「硬门」（= T106 + T112 的立项依据）。

### 4.4 成本控制

**共识结论：**

- **Prompt caching 是公认第一优先级**：对有稳定前缀（system prompt、工具定义、长静态
  context）的 agent，缓存部分成本降约 90%，长 session 实测总成本降 ~89%；代价是维护前缀
  稳定性（「don't break the cache」——中途改 system prompt/工具集会击穿缓存）。[搜索面]
  https://www.growthaccelerationpartners.com/blog/ai-cost-optimization-and-the-problem-of-runaway-token-costs ；
  https://arxiv.org/pdf/2601.06007
- **Model tiering 是公认第二手法**：强模型留给 planning 与 review（判断密集），弱模型做
  机械执行——与 Anthropic「model choice 是性能方差三因素之一」一致。[搜索面]
  https://www.augmentcode.com/guides/ai-coding-cost-analysis-agent-token-spend ；
  [已核验] https://www.anthropic.com/engineering/multi-agent-research-system
- **「全跑 vs 采样」的业界主流答案是分层，不是二选一**：机械/静态检查全量跑；语义审按
  风险路由（低风险快速通道、高风险深审）；severity 分级输出（Action Required / Recommended /
  Minor）防关键问题被噪声淹没；部分团队对有强测试+回滚保护的变更试验 merge-first-review-later。
  [已核验] https://addyo.substack.com/p/code-review-in-the-age-of-ai ；
  https://www.qodo.ai/blog/5-ai-code-review-pattern-predictions-in-2026/ ；[搜索面]
  https://blog.codacy.com/code-review-is-dead-why-ai-generated-code-needs-verification-not-human-approval
- **但同时有反向共识：agent 产量越大，独立 gate 越重要**，不能因成本把冷审优化掉。
  [搜索面] https://www.oreilly.com/radar/agentic-code-review/
- **Token 遥测是正确的锚**：token 用量解释 80% 性能方差 ⇒ per-任务 token 记账既是成本
  工具也是质量诊断工具（= T104 的立项依据）。[已核验] Anthropic multi-agent 一文。

**对本仓启示**：本仓「每次全跑冷审」与业界「风险采样」表面冲突，但本仓有冷层独家抓
fatal 的实证，且业界的采样针对的是**人类**审查带宽瓶颈——**机器审全跑 + 人类 gate
只看报告**恰是业界推荐的分层形态，不必改向；真正可吸收的是 severity 三级输出（替代或
补充置信分）与 fan-out 前审计 cache 前缀稳定性（多镜共享的规则/checklist 前缀应尽量
byte-stable 以吃满 cache，= T98）。

### 4.5 公认反模式

**共识结论：**

- **Anthropic 官方点名五大失败模式**：kitchen-sink session（不相关任务混 context）、
  反复纠正污染 context（≥2 次纠正后应 `/clear` 重写 prompt 而非继续纠）、over-specified
  CLAUDE.md（太长导致规则被忽略，判据 =「删掉这行会不会出错」）、trust-then-verify gap
  （无验证就信 plausible 实现）、无界探索吃光 context。[已核验]
  https://code.claude.com/docs/en/best-practices
- **Reviewer over-reporting → over-engineering 螺旋**：被要求找 gap 的 reviewer 必报 gap，
  逐条照修产出多余抽象/防御代码/不可能场景的测试。[已核验] 同上
- **Rubber-stamp / 假绿**：开发者无法解释自己提交的 AI 代码；AI 使 PR 增大 ~18%、每 PR
  事故 +24%；解法共识 =「证据先于断言」——测试日志/截图/复现步骤作为 PR 合同必要条件
  （与本仓 verify 反假绿锚点同构）。[已核验] https://addyo.substack.com/p/code-review-in-the-age-of-ai
- **SDD 自身的样板税与 spec drift**：把全流程套在一切变更上（含 bug fix）的团队「一个
  季度内被 overhead 烧尽」；更隐蔽的是 spec 偏离 intent 后，spec 与 code 一致地错（机械
  检查只能抓 code-vs-spec 漂移，抓不了 spec-vs-intent 漂移）；以及「BDUF 换皮复辟」的
  文化风险。[搜索面]
  https://dev.to/krlz/spec-driven-development-in-2026-what-it-is-the-tooling-and-how-teams-actually-use-it-2fk2 ；
  https://medium.com/@tojosphine/spec-driven-development-what-i-wish-i-knew-before-i-started-1213d485a244

**对本仓启示**：置信过滤、对抗裁决、evidence 锚已对症前三条；最值得警惕的是第四条——
per-change 固定流程成本是业界点名的头号 SDD 反模式，与本仓「fold-vs-defer 循环成本」
「测试耗时真凶 = 返工轮次」的自测互证；上游已给 `skip_specs` 豁免阀，可评估对 trivial
变更开等价轻量通道。另外「spec-vs-intent 漂移机械门抓不到」正是本仓拷问相位（grill）
承担的角色——**这是 grill 不可被机械化替代的文献级理由，成本优化不许动它**。

---

## 5. 业界带来的净新增候选（六缺口之外）

1. **上游演进加速 ⇒ T264 概率项变大**：上游已上线 `skip_specs`、`/opsx:update`、Stores、
   30+ 工具 skills 化。(a) `skip_specs` 是上游对「per-change 固定成本」反模式的官方豁免阀，
   本仓 trivial 通道可对齐评估；(b) T264（project-local schema fork 快照无漂移机械门）——
   上游动得越快，一次性 fork 快照烂得越快，优先级应升。
2. **Spec Kit `verdict_input`**：gate 判决作为结构化输入喂给下游步骤，而非只 pass/fail——
   与 hand-off.md 同构，可评估把 verify 判决机械化绑定进下游（低优先级）。
3. **compaction 定制**：CLAUDE.md 可写明 compact 时必保留什么——与 T256（PreCompact hook
   落盘易失状态）是同一题的两半，合并考虑。
4. **一条「不做」的确认**：spec-vs-intent 漂移无机械门可抓（文献明示）⇒ grill 相位的
   不可替代性拿到外部背书；grill 不可轻跳的既有纪律维持，不进任何成本优化的砍单。

### 5.1 上游 skill 套件吸收机制（用户点名目标，2026-08-10 并入）

本仓参考吸收了三个外部 skill 套件的机制精华，均为**一次性调研 + 一次性吸收 change**，
无任何「上次吸收到哪」的锚与后续跟踪：

| 套件 | 本机安装形态 | 已吸收（实证收益） | 跟踪现状 |
|---|---|---|---|
| **gstack** | `~/.claude/skills/gstack*`（skill 目录，`gstack-upgrade` 管更新）+ `~/.gstack` 数据仓 | absorb-gstack-autoplan、absorb-gstack-review（autoplan 6 决策原则、review 双轴等，均 SHIPPED）；T267（python.md checklist domain）为 Pass-2 剩余 | 无锚、无跟踪 |
| **superpowers** | `~/.claude/plugins/cache/claude-plugins-official/superpowers`（官方插件，marketplace 更新） | SDD 机制（loop-breaker 对齐、model 显式指定等）；T245/T246 为手工发现的待吸收项 | 无锚、无跟踪 |
| **matt 套件** | `~/.claude/skills/{to-tickets,wayfinder,ask-matt}` + `setup-matt-pocock-skills`（源 = GitHub `mattpocock/skills`） | matt-workflow-integration（tickets 管线 + wayfinder，SHIPPED） | `setup-matt-pocock-skills/triage-labels.md` 已有半成品 label 映射表，但无版本锚 |
| **OpenSpec CLI**（上游工具，同属此面） | npm `@fission-ai/openspec` + project-local schema fork | schema fork 快照（align-sdflow-spec-with-openspec-schema） | T264 已记录「fork 漂移无机械门」 |

**失效模式**（与 T264 同构）：吸收是快照式的，上游持续演进（§4.1 显示 OpenSpec 半年内上了
`skip_specs`/Stores/`/opsx:update`；superpowers/gstack/matt 均活跃）——没有锚就没有 delta，
每次想「再吸收一轮」都得全量重看，实际结果是从不重看。docs/workflow-skills/ 下的 8 份调研
详解全部冻结在 2026-07。

**推荐方案**（机制细节留给实施 change 的 grill 拍板）：新建一个轻量数据类 skill
（暂名 `sdflow-upstream-watch`）——
- **机械层脚本**：维护 `openspec/upstream/anchors.yaml`（每源：类型 git-repo/plugin/
  skill-dir/npm、位置或远端、上次吸收锚 SHA/version/date）；运行时对每源收集锚点以来的
  delta（git log / changelog / 版本对比），输出材料包；源不可达 fail-loud。
- **模型层**：读 delta → 按「与本仓同类面对照」分诊值得吸收的机制 → 产出吸收报告，
  采纳项经人拍板后 recorder 入 issues 池（显式 `change=null`）。
- **触发**：手动 + 周期提醒（如月度，或挂 `/sdflow-upgrade` 后提示）。
- **依据**：三次一次性吸收全部 SHIPPED 且有实证收益（吸收这件事本身 ROI 已验证）；
  T264/T245/T246/T267 四条 open todo 都是这个缺口的散点症状，一个机制统一收口。
- **代价**：三源形态异构，采集器每源一个适配分支；「何为精华」无确定性信号，属模型
  判断 + 人拍板（诚实边界，合法残余）。
- **备选**：(a) 并入 sdflow-maintain——否，maintain 的域是 openspec 目录一致性，混域；
  (b) 维持现状手动全量重看——否，实证是「从不重看」。

---

## 6. 合并优先级（行动向导，具体排期见 roadmap 文档包）

| 优先级 | 事项 | 类型 | 依据强度 |
|---|---|---|---|
| 1 | 落 T104（token 维）+ T108（实修率）→ 开「镜 roster 复评」 | 执行欠账 | 本仓数据 + popularity trap 文献 |
| 2 | 重开 T98/T99/T101/T102 诚实重分诊 | 数据完整性 | 官方最佳实践直接背书其中三条 |
| 3 | T106+T112 升优先级（置信过滤地基被文献动摇），与复评同 change | 可靠性 | arXiv 2508.06225 |
| 4 | T105/T103 升优先级（宿主原生 effort 分档，实现成本降一个量级） | 成本 | 宿主能力变化 |
| 5 | 上游套件吸收机制（gstack/superpowers/matt/OpenSpec 统一 watch，§5.1；吸掉 T264/T245/T246/T267 散点） | 上游对齐 | 用户点名 + 三次吸收 SHIPPED 实证 |
| 6 | 评估 `skip_specs` 对齐（可并入第 5 项的 OpenSpec 源分诊） | 上游对齐 | OpenSpec releases |
| 7 | 新 todo：SKILL.md 考古层清理（对 SKILL.md 落实 DOC-1 审计——规则本已覆盖 SKILL.md，此前未系统审计） | context 成本 | 本仓规则自洽推论 |
| 8 | 新 todo：记录「Workflow 原语 + Stop hook 已可用」，评审编排大改时重估 | 延后池条件更新 | 宿主能力变化 |

**明确不做**：架构五柱不动（冷上下文独立评审、子代理隔离、静态分档、人类门上移、机械活
交脚本——全部有外部背书）；grill 不砍；冷层独立审不砍；评审编排大改不在本轮（条件记录
待重估）；平台基线重校等 Fable 5 retro 数据攒够再做。

---

## 附录 · 核验说明

标 [已核验] 的 10 个 URL 逐一打开读过原文；标 [搜索面] 的仅经搜索结果确认存在与主旨，
引用时以链接内原文为准。搜索结果中大量 2026 年 Spec Kit 二手评测（jamesm.blog、
dailyaiworld 等）质量存疑已弃用，Spec Kit / OpenSpec / Kiro 结论均改从官方
releases/changelog 取证。本仓侧数据（retro 表、issue 状态、SKILL.md 行数、wco 里程碑）
均为 2026-08-10 实查（`openspec/retro/report.md`、`openspec/issues/`、
`openspec/roadmaps/`、各 `SKILL.md` 行数统计）。
