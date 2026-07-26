# add-sdflow-spec · Design

## Context

阶段一现状：`opsx:explore`（思考伙伴，CLI 官方 skill）→ `opsx:ff`（四件套生成，CLI 官方 skill）→ `/grill-with-docs`（对抗拷问，Matt Pocock skills 集合 `~/.agents/skills`，非 git 管理）。三入口拼接的缺陷与动机见 proposal。

**既有权威源（本设计 MUST 与之对齐，不得另起一套）**〔spec-review-amendment F-02，原文遗漏这一整段；窄复核补齐为 **7 处**〕：`sdflow-init/assets/workflow/generation-process.md` §四（`:51` 起）已规定推荐流水线 = `explore→ff→grill`，且该文件 `:79-80` 载有同族防漂移警告「否则它会另起一套 `docs/adr/`……形成**第二套真相源**（正是我们一路在消除的漂移）」——原文出自 §六讨论 ADR/术语**路径约定**，此处为**同一原则的类比引用**，非该文件直接针对流水线顺序的警告；`workflow.md` §三决策 2 规定 **G1「全流程不用 `/clear`」**；`WORKFLOW-GUIDE.md` 是其生成物；`openspec/specs/spec-workflow/spec.md:968-994` 另有两条阶段一衔接 Requirement。另有 `reference/quality-layering.md`（G1 的第二处载体）、`snippets/claude-section.md` 的托管块（其中「ff 之后是 grill」条款）、`ff-generation-constraints.md:17`（FF-0「已在 feature 分支就跳过」的弱判据，与本设计的三分支判定冲突）。本仓运行时经 `resolve-workflow.sh` 解析到**全局 canonical**、仓内不留副本 ⇒ 不同步这七处，本仓 agent 读到的仍是旧规则。完整清单与处置见 SA-11。

本设计基于四路实证调研：①既有 fan-out 编排模式（dispatch 三要素、principles 注入、`resolve-models.sh` 档位变量）；②成本基线（retro 报告 + workflow-cost-optimization roadmap）；③openspec CLI 机制实测（**1.5.0**：`instructions --json` 幂等只读、单产物载荷 3.5-6KB）；④agent 定义文件调研（`docs/subagent-definitions-plan.md`）。外部权威输入：Anthropic multi-agent 研究（多代理 ≈15× token 溢价，仅子任务独立时划算）。

约束：产物契约不变（标准四件套 + openspec CLI + FF-0）；下游阶段三不动；通则托管单一源机制不可绕过；**canonical 规则单一源不可分叉**。

## Goals / Non-Goals

**Goals：**
- 单一入口管线：澄清 → 拷问 → 生成，拷问结构性前置于成文。
- 判断不出主 session；**阶段二起**检索与生成外派子代理（阶段一薄编排）。
- 决策纪要为承重件：对话中的 why 100% 落盘，`/clear` 无损；**Phase B 内增量落盘**。
- 档位相对化：主 session 档位人选，子代理经档位变量。
- **规则单一源不分叉**：本 change 与**七处**既有 canonical 源的冲突同 change 消除（清单见 SA-11）。

**Non-Goals：** 见 proposal Non-Goals（含可证伪假设，此处不重复）。

## 组件清单〔BASE-25〕

| 组件 | 阶段 | 类型 | 职责 | 依赖 |
|---|---|---|---|---|
| `sdflow-spec/SKILL.md` | 一 | 新增·编排指令 | 三相位管线、相位状态机、降级矩阵、出口序列（**体量控制见 D12**） | openspec CLI |
| `sdflow-spec/references/` | 一 | 新增·外置资料 | 降级阶梯表、ADR/术语最小模板、决策纪要字段 schema（表格型少判断内容外置，对齐 `code-checklists/domains` 模式）〔spec-review-amendment F-16〕 | — |
| `sdflow-init/assets/workflow/{workflow.md,generation-process.md}` | 一 | **修改**〔F-02〕 | G1 修订（Q2=A）+ 流水线分支 | 托管刷新机制 |
| `sdflow-init/assets/workflow/reference/quality-layering.md` | 一 | **修改**〔F-02·窄复核补〕 | G1 的第二处载体，同步例外 | 托管刷新机制 |
| `sdflow-init/assets/workflow/ff-generation-constraints.md` | 一 | **修改**〔窄复核补〕 | FF-0 弱判据 `:17` 改三分支判定，与 SA-05 对齐 | — |
| `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md` | 一 | **重生成**〔F-02〕 | 随源刷新 | `gen_workflow_guide.py` |
| `openspec/specs/spec-workflow/spec.md` | 一 | **修改**〔F-02〕 | 新旧入口共存与路由（`:968-994` 两条既有 Requirement） | — |
| `sdflow-init/assets/snippets/claude-section.md` | 一 | 修改 | 归属修正（superpowers → Matt Pocock，`:118`） | 托管区块刷新机制 |
| CLAUDE.md/AGENTS.md/README.md | 一 | 修改 | **非托管区**：使用路径 + **四入口选择规则** + 出口序列；删「15 个 SKILL.md」硬编码数字〔F-28〕 | — |
| `sdflow-spec/agents/sdflow-local-researcher.md` | 二 | 新增·agent 定义 | **仓内**检索供证（无网络） | 通则托管块 |
| `sdflow-spec/agents/sdflow-web-researcher.md` | 二 | 新增·agent 定义 | **联网**调研（无仓库读取、无 `Bash`；只收净化查询）〔BASE-28 S2〕 | 通则托管块 |
| `sdflow-spec/agents/sdflow-spec-writer.md` | 二 | 新增·agent 定义 | 四件套单产物生成（单一职责） | 通则托管块、openspec CLI |
| `setup.sh` | 二 | 修改 | **新写 `install_agents()`**（**不是**沿用 `install_into`，见 D11） | — |
| `hack/tests/test_install_agents.py` | 二 | 新增·测试 | 全仓首个 setup.sh 测试〔F-09〕 | pytest |
| `hack/sync_principles.py` + 其测试 | 二 | 修改 | agents **glob 发现**纳入投放面（非硬编码清单）+ `AGENT_TARGETS` 显式配 skill 味 `SOURCE`〔F-22〕 | 既有 `targets()`/`skills()` |

**组件/依赖图**〔TG-14〕：

```
人 ──触发──▶ SKILL.md（主 session·判断层）
                │
    ┌───────────┼──────────────┬─────────────────┬──────────────┐
    ▼           ▼              ▼                 ▼              ▼
 openspec CLI  local/web-researcher sdflow-spec-writer  checkpoint-  canonical 规则
 (new/status/  〔阶段二〕         〔阶段二〕          commit.sh    workflow.md
  instructions/ subagent_type 派发  subagent_type 派发 (全局)      generation-process.md
  validate)     阶段一=主session亲查 阶段一=主session亲写           WORKFLOW-GUIDE.md
                    ▲两个 agent 定义正文含通则托管块                spec-workflow/spec.md
                    │                                                    ▲
        sync_principles.py ──守──▶ hack/tests/                    本 change 同步修改〔F-02〕
                    ▲
        setup.sh install_agents() ──铺──▶ ~/.claude/agents/ ──守──▶ test_install_agents.py
```

## 三相位管线〔TG-10 序列图〕

```
人          主session(判断)        researcher〔阶段二〕  spec-writer〔阶段二〕  openspec CLI
│ 触发 ─────▶│
│            │ CLI 查上下文 ───────────────────────────────────────────────────▶│
│            │ 重入探测(见相位状态机) ── 命中在途 change ──▶ 问人:继续/新开
│◀─ 一次一问 │ (需证据时) ──派/亲查──▶│grep/读码/调研
│  每问附推荐│◀────结论+出处──────────│
│  …若干轮…  │
│            │ ══ Phase A→B：共识初成 ══
│            │ ══ Phase B 起手（前移三步，B-draft 才有落点〔窄复核 F-12〕）══
│            │ ①工作树前置检查(git status --porcelain)〔F-05〕──脏─▶ halt 问人
│            │ ②FF-0 三分支判定〔F-11〕──其它 feature 分支─▶ halt 问人
│            │ ③openspec new change（名由目标态定，见 D9）──────────────────▶│
│            │ 亲笔压缩共识为锚点纪要(对话内呈现,作拷问靶)
│◀─ 拷问(攻承重约束,一次一问)
│            │ ★每条承重约束站稳即增量落盘 memo 草稿到 change 目录〔F-12〕
│  …至共识+承重约束全站稳(判据见 SA-03 最小充分条件)…
│            │ ══ Phase B 收敛 ══
│            │ ④亲笔 decision-memo.md 定稿(补 change/branch/时间戳/决策 hash)
│            │ ⑤checkpoint
│            │ ══ Phase B→C ══
│            │ 起手核验 memo 有效性(存在+必填非空+身份对得上当前 change/branch)
│            │ ──串行逐产物(阶段二派 writer / 阶段一亲写)──▶│自调 instructions ─▶│
│            │                                              │+ schema 断言〔F-13〕
│            │                                              │读**强制阅读清单**〔F-14〕
│            │                                              │临时文件→原子替换→写
│            │◀─────────完成/失败────────────────────────────│
│            │ ⑥写后核验: status(存在态) + validate --strict(合格态)〔F-03〕
│            │    └─不过─▶ 重试/亲写阶梯(非"文件存在即跳过")
│            │ ⑦终审: 纪要↔产物一致性 + **design↔specs 互相一致**〔F-14〕
│            │ ⑧checkpoint
│◀─ 出口提示原样贴:/clear → 换档 → /sdflow-spec-review

  异常分支（原图只画 happy path，本次补齐〔spec-review-amendment F-26〕）：
    memo 缺失/身份不符 ─▶ 拒绝进 C，退回 B
    writer 失败 ─▶ 重试 1 次 ─▶ 主 session 亲写（报告标注）
    CLI 不可用/schema 不兼容 ─▶ fail-closed 中止（报实际版本 + 修复命令）
    agent 定义不可用 ─▶ **主 session 亲查/亲写**（不退通用子代理，见 D3）
    人在 B 中途放弃 ─▶ 分支内 memo 草稿保留，删分支即净（仅当工作树曾干净）
```

## 相位状态机〔spec-review-amendment F-11，原设计缺失〕

```
absent ──B起手(①②③)──▶ B-draft ──收敛(④⑤)──▶ B-finalized ──派/亲写──▶ C-partial ──全产物过 validate──▶ complete
   ▲                        │                        │                          │
   └────删分支即净───────────┘                        └──memo 身份不符───────────┘（退回 B-draft）
```

🔴 **`B-draft` 必须是可探测状态**〔窄复核 F-12〕：这正是把 ①②③ 从「B 收敛」前移到「B 起手」的理由——原设计里 `openspec new change` 在收敛点才跑，B 进行中既无 change 目录也无 feature 分支，SA-04 的「增量落盘」**无处可写**（而 `MUST NOT 存放于 session 级临时目录` 又堵死唯一替代），且状态机的 `B-draft` 结构上探测不到。前移后 memo 草稿从第一条约束站稳起就在 git 里，D9 否决 scratchpad 的理由不再反噬本方案自身。

- **重入 MUST 先探测**：当前分支名 + `openspec/changes/` 下是否有「含 `decision-memo.md` 但 `openspec status` 未完成」的 change。命中 → **问人**「继续该 change 还是新开」（两种意图导致实质不同产物，属通则③里必须确认的那类）。**该探测能看见 `B-draft`**（草稿 memo 已在 change 目录内）。
- **memo 身份字段**：`schema_version` / `change` / `branch` / 生成时间戳 / 决策 hash。C 起手核对不上即拒绝并呈现旧 memo 摘要给人确认，**MUST NOT 静默复用**（原设计只查「存在且必填非空」，对上一次废弃运行留下的 memo 是全绿的）。
- `complete` 态拒绝重生成。

## 数据模型与生命周期〔BASE-24〕：两类纪要

〔spec-review-amendment F-21：原文未定义「锚点纪要」与「决策纪要」的关系，且「并入 design.md」有双写漂移问题〕

| | 锚点纪要 | 决策纪要 `decision-memo.md` |
|---|---|---|
| 产出时机 | Phase A→B 交界 | Phase B 全程增量 + 收敛定稿 |
| 载体 | **对话内呈现**，不落盘 | change 目录，git 跟踪 |
| 作用 | 拷问的**文本靶**（供攻击/推翻） | 承重件，Phase C 输入，审计锚 |
| 关系 | 决策纪要是锚点纪要**被拷问后的存活残余 + 拷问产出**；二者非同一物 | |

**决策纪要字段**：目标态一句话 · 拍板决策[]（决策 + 依据 + **砍掉的候选 + 砍的理由**）· 承重约束[]（约束 + 验证方式/证据锚）· 接受的边角[]（通则④，风险 + 为何接受）· 三镜代价（仅命中 TG-23 的方案选择）· **身份字段**（见状态机）。

**生命周期**：Phase B **起手**建 change 目录（前移 ①②③）→ B 进行中增量追加（每条承重约束站稳即写）→ B 收敛定稿 + checkpoint → Phase C 作为每个生成步的输入 → **终审后不并入 design.md，design.md 的 Decisions 只留指针**〔spec-review-amendment F-21 决议：采纳「不并入」〕。

理由：① `openspec instructions design --json` 实跑核验，design 原生 Sections = `Context / Goals-Non-Goals / Decisions / Risks-Trade-offs / Migration Plan / Open Questions` —— **「承重约束[]」没有对应槽位**，而它是 D1/SA-03 里最承重的东西；② SA-04 的验收不变式（`/clear` 后 why 100% 可得）**单靠 memo 就已满足**（它在 change 目录、spec-review 读得到）⇒「保留 + 并入」的双写成本全部是白付的，且失配时无优先级规则；③ 指针式引用符合 DOC-1 的查表式定位。

**验收 = /clear 无损**：纪要在 git 内，session 崩溃/换 session 重入不丢；清上下文后阶段二若丢失任何 why，即管线 bug。

## 安全与数据保护〔BASE-28 · TG-17〕

〔spec-review-amendment F-06 · hr-tg voice V-2/V-4/V-5：**原设计判 TG-17 不命中，本段整块为新增**〕

**判定**：TG-17 **命中**。原设计的单体 researcher 工具面同时持有仓库读取、`Bash`、`WebFetch`/`WebSearch`；`sdflow-spec-writer` 持有 `Bash`、`Write`。

| # | 面 | 处置 |
|---|---|---|
| S1 | **`Bash` 不是只读** —— 原 D3 断言「六者皆只读、不破无写权边界」是事实错误（可 `>` 重定向、`rm`、`git commit`、`curl -X POST`；工具 allowlist 不能限制 Bash 子命令）。⚠️ 该断言带 `[grill-amendment]` 标记，即拷问轮把一个错误论断固化成了 SHALL 级描述 | **首选**：用作用域参数收窄（`docs/subagent-definitions-plan.md:223-224` 实测 `tools` 支持作用域参数）→ `Bash(git log:*), Bash(rg:*), Bash(grep:*)` 之类白名单集。**备选**（作用域语法未实测通过时）：如实改称「工具集为**检索取向**；`Bash` 非只读，只读性由 agent 正文角色纪律约束，**属指令层非机械门**」 |
| S2 | **出境通道无 secret scan** —— researcher 同时握仓库读取与联网工具，仓内私有内容可经 `WebFetch`/`WebSearch` 外流 | **拆两个 agent**：`local-researcher`（无网络）/ `web-researcher`（无仓库读取、无 `Bash`，只接收主 session 生成的**最小净化查询**）。任何外发参数 MUST 先过 secret scan（**复用** `openspec/specs/host-adaptive-execution/spec.md:82-96` 既有的 secret scan + 读围栏 + 拒发语义，MUST NOT 新造），命中即拒发且**禁 fallback** |
| S3 | **间接 prompt injection** —— 外部页面内容可驱动一个同时持有仓库读取与 `Bash` 的 agent | Web 内容一律定义为**不可执行数据**（指令性文字视为数据）；网络 agent 禁 `Bash`/仓库读取；主 session 只消费带来源的事实摘要；影响设计决策的结论须第二来源或官方来源复核 |
| S4 | **`resolvedOutputPath` confused deputy** —— 第三方 CLI 的 JSON 输出被直接提升为写入目标，无路径穿越/绝对路径/symlink 逃逸防护 | 由确定性 wrapper 解析并验证 JSON；对目标做 canonicalization，要求严格位于 `openspec/changes/<name>/`、匹配预期 artifact allowlist、拒绝 symlink 逃逸，再把净化后的路径交给写入方 |
| S5 | **全局 agent 名册暴露** —— `~/.claude/agents/` 对所有项目可见，`sdflow-spec-writer` 持 `Write`，而 `disable-model-invocation` 只挡 SKILL、挡不到 agent 定义 | 两个 agent 的 `description` 写成**排他式**（「仅由 `/sdflow-spec` 编排派发，其它场景 MUST NOT 选用」），把误选风险压到最低（见 D3） |

## Decisions〔TG-23·BASE-12〕

**D1 拷问前置于生成**（备选：①现状式先生成后拷问；②Spec Kit 式生成初稿再 clarify；③**T132 式机械门**〔spec-review-amendment F-04 新增〕）。改想法比改四份成文便宜；锚定效应实证（dedupe-issues：错误 premise 活过成文）。
**关于备选③**：`openspec/issues/todolist/2026-07-todolist.md:232`（T132，OPEN，2026-07-11）已设计好「spec-review 起手机械核验 grill 已收敛信号（checkpoint-commit 或 `<!-- sdflow:grill-done -->` 锚），无信号→REFUSE_START」，载体与 fail-closed 语义齐备，成本低两个数量级。**它与本 change 不互斥、且应当照做** —— 因为它覆盖的是「人直接敲 `opsx:ff`」那条本 skill**够不着**的路径（本 skill 声明 `disable-model-invocation: true`，模型唤不起）。本 change 解决的是另一半：**拷问发生在成文之前**（T132 只保证「拷问发生过」，不保证「在成文之前」）。
🔴 **诚实收窄**〔spec-review-amendment F-04〕：原文「跳过风险**结构性消灭**」与 `proposal.md` 自认的「非机械保证」矛盾，**改为**：「拷问是管线的**内建默认路径**，跳过须主动偏离指令；这是结构性改善，不是机械保证」。
三镜：系统镜——管线更长但无回改循环，可回退；用户镜——拷问体验不变，免手动衔接；开发循环镜——省整轮「成文→拷问→回改」返工。主次：**开发循环镜主导**（返工是实证痛点）。

**D2 判断/机械分层外派，且分阶段验证**〔spec-review-amendment · 设计门 Q1〕（备选：薄编排=主 session 全做；重管线=全阶段大 roster fan-out）。判断（澄清/拷问/纪要/终审）**永远**不出主 session。检索与生成的外派**分阶段引入**：
- **阶段一 = 薄编排形态**（主 session 亲写）—— 原文已承认这是「本方案的合法降级形态」，现将其提升为**阶段一的正式交付形态**；
- **阶段二 = 引入外派**，起手过 GO/NO-GO 实测门（D3），并用 legacy/thin/subagent **三路 A/B** 判定是否保留。
依据：官方 lead+subagent 实证 90.2%；15× 溢价警告 → 子代理少而定向、单一职责短命。
🔴 **未被原设计正视的反证**〔spec-review-amendment F-15/Q4〕：写 design 会发现架构缺口、写 spec 会发现不可验收表述——**这些发现本身就是判断工作**，而 writer 被禁止询问用户 ⇒ 遇缺口只能猜/漏写/失败，主 session 再读回修正 = **双写**。另：`archive/2026-07-18-async-outside-voice/design.md` 的 **6 条 ADR 里 3 条**（ADR-3/5/6）带 `[grill]` + `[spec-review-amendment]` 等复合标记 ⇒ 其最终形态依赖多轮跨阶段输入，**不是一份 5 字段纪要能压缩的**。⇒ 这正是分阶段的理由：阶段二的 A/B **MUST 用一个真实复杂 change**（非玩具需求），并人工比对「纪要驱动的 design.md」vs「有完整拷问上下文的 design.md」的**论证密度**（Q4 决议）。writer 遇未决判断 MUST 返回结构化 blocker，MUST NOT 自行补全。
三镜：系统镜——多一层纪要中间件与 dispatch 面，每件独立可测，且阶段门使其可回退到阶段一；用户镜——生成阶段等待略增；开发循环镜——复用既有 dispatch 模式，但成本收益未证实、由阶段二判定。主次：**系统镜主导**（可归因性是分阶段的首要收益，成本是待验假设）。

**D3 agent 定义文件承载角色（阶段二），派发用 `subagent_type`，全局分发**（备选：纯 prompt 内联）：
- 🔴 **派发参数 = `subagent_type`，不是 `agentType`**〔spec-review-amendment F-01〕。依据：`docs/subagent-definitions-plan.md:114-145` 把三条路径分清——①Agent 工具（参数 `subagent_type`）②agent 定义文件（载体）③Workflow `agent()`（参数 `agentType`），而同文 `:136-137` 明记 **③ 不采纳**（需用户每次显式授权）。本仓三处先例（`.claude/skills/openspec-archive-change/SKILL.md:69` 等）均用 `subagent_type`，15 个 SKILL.md 无一用 `agentType`。
- **三个** agent 定义〔窄复核订正：原写「两个」，与 BASE-28 S2 的拆分要求自相矛盾〕：**`sdflow-local-researcher`**（`model: inherit`·`effort: low`·仓内检索，无网络）、**`sdflow-web-researcher`**（`model: inherit`·`effort: low`·联网调研，**无仓库读取、无 `Bash`**）、**`sdflow-spec-writer`**（`model: inherit`·`effort: medium`·`tools: Read, Glob, Grep, Bash, Write`）。工具面见 BASE-28 的 S1/S2，**不再声称「全只读」**。
- 🔴 **fallback 不是等价降级，改为亲查/亲写**〔spec-review-amendment F-01 · hr-tg V-3〕：原设计的「agent 定义不可用 → 通用子代理 + prompt 内联通则」**撤掉了唯一的工具权限边界 = 降级即提权**（`docs/subagent-definitions-plan.md:116-123`：直接 Agent 路径无法限制工具集），且 agent 正文承载的角色纪律（researcher 的「材料不回传」、writer 的「自调 instructions / 禁 AskUserQuestion」）在 fallback 下全部消失。**改为**：researcher 不可用 → 主 session **亲查**；writer 不可用 → 主 session **亲写**。MUST NOT 用权限更宽的通用子代理当安全 fallback。**副作用（正向）**：消灭了双路径 parity 问题（原本需要 `check_async_branch_parity.py` 那种字节等值门才能守住）。
- **分发层级 = 全局 `~/.claude/agents/`**（设计门 Q3 决议）。**MUST 声明反驳理由**〔spec-review-amendment F-19〕：`docs/subagent-definitions-plan.md:303-308` 倾向「先放本仓验证」，但**仓内 `.claude/agents/` 无法服务跨项目使用**——本 skill 的价值恰在其它项目里跑，故直接全局。**代价照单收**：全局命名空间污染（缓解 = 排他式 `description`，见 BASE-28 S5）+ Windows 守卫不可实现（见 D11）。附注：官方 `claude-plugins-official/plugins/feature-dev` 的打包方式是 `<plugin>/agents/`（与插件同包），本决定与之不同，理由同上。
- 收益：通则传播从指令变机制 + 每次派发省 ~2KB 重复注入 + `effort` 分档。代价：投放面 +2 必须纳入 sync_principles（见 D11）。
三镜：系统镜——新增 `~/.claude/agents/` 铺设面与全局命名空间；用户镜——无感（排他 description 后）；开发循环镜——effort 分档与通则免重复注入双收益，且 fallback 简化为亲做后无双路径维护。主次：**开发循环镜主导**。

**D4 档位相对化**（备选：SKILL.md 写死 Fable 5）。主 session = 人选档；子代理引用 `$SDFLOW_TIER_MID`/`$SDFLOW_TIER_LIGHT`。
🔴 **档位解析 MUST 照既有加固协议，不得自造简写**〔spec-review-amendment F-06(Eng)〕：`sdflow-spec-review/SKILL.md` 第零步第 3 项的 (a) unset 清脏 →(b) `[ -x ]` 预检 fail-loud →(c) 捕获退出码再 eval →(d) eval 后校验枚举与非空，**四步一步不少**（裸 `eval "$(…)"` 会被脚本缺失静默吞，且旧值留存 ⇒ 拿旧宿主假绿；`resolve-models.sh:61/74/209` 三种失败面都 exit 0 只在 stderr 告警）。
🔴 **传递方式**：harness 每次 Bash 调用是独立 shell，`export` **不跨调用存活**（本次评审运行中已亲身撞到：voice preflight 首次报 `SDFLOW_VOICE_RUNNER 未设置`）。⇒ 主 session 从该次工具输出里读到**具体模型 id**，再把**字面值**填进派发的 `model` 参数；SKILL.md 正文写变量名（不内联 id），二者不矛盾。
三镜〔窄复核补齐：F-27 是面治，D4/D7 同样带备选〕：系统镜——复用既有 resolver，不新增机制，可回退（写死模型名随时可改回）；用户镜——人可按 change 价值自选主 session 档位；开发循环镜——档位随机队自动解析，换机器/换宿主无需改 skill。主次：**开发循环镜主导**（可移植性是档位相对化的首要收益）。

**D5 吸收技法、锚仓内格式、运行时零第三方 skill 依赖**（备选：运行时调用 grilling/domain-modeling/grill-with-docs）。三者均在仓外非受控（更新即覆盖）；grilling 全文 ~12 行已全吸收；domain-modeling 只吸收触发判据，写入格式真相源 = 仓内既有 `openspec/adr/*.md` 与 CONTEXT.md 现状。唯一运行时外部依赖 = openspec CLI。
三镜〔spec-review-amendment F-27 补齐〕：系统镜——切断对仓外非受控资产的运行时依赖，可回退（技法是文本，随时可再吸收）；用户镜——无感，拷问体验由 SKILL.md 承载；开发循环镜——第三方更新不再打断本流程，代价是技法更新须手动跟进。主次：**系统镜主导**（供应链可控性）。

**D6 出口序列 `/clear` → 换档 → `/sdflow-spec-review`，且同 change 修订 G1**〔spec-review-amendment · 设计门 Q2 决议 = 选项 A〕（备选：B 放弃 `/clear`、冷由 spec-review 自己的 fan-out 提供；C 保留 `/clear` 但不动 canonical——**已否决**，那会留下两条互相矛盾的阶段一规范）。
🔴 **原设计的三重依据里，第三条 MUST 删除**：「主审裁决冷视角」**已被 G1 正面回答**（`reference/quality-layering.md:101-107`：sdflow-code-review 的裁决冷靠独立编排器 + fresh 子代理 fan-out，不靠 `/clear`），拿它当依据是漏查。
**保留的两条依据（G1 未覆盖，故构成合法例外）**：① **cache 按模型隔离** —— 拖着旧上下文切档 = 全价重付；② **产/审错档纪律** —— 阶段一与阶段二的合适档位不同，换档是本例外的真实动因。G1 的论证只针对「独立性」，**没谈成本与档位** ⇒ 例外成立。
**同 change 动作**：在 `workflow.md` §三决策 2 与 `reference/quality-layering.md` 为「阶段一→阶段二」这一段写明例外与上述两条理由，使规则单一源与本 change 不再互相矛盾。出口提示 MUST 原样贴序列（对齐「ff 后贴 grill prompt」的既有强制模式）。
三镜：系统镜——G1 从「无例外」变为「带一处具名例外」，规则复杂度 +1 但单一源保持；用户镜——多敲一次 `/clear` 与一次换档；开发循环镜——cache 成本与档位纪律双收益。主次：**开发循环镜主导**。

**D7 命名 `sdflow-spec`**（备选：sdflow-forge/sdflow-explore）。与 sdflow-spec-review 构成「产 spec → 审 spec」对仗；explore 只覆盖第一相位职责。前缀重叠经查无触发面冲突。
三镜〔窄复核补齐〕：系统镜——与既有 `sdflow-*` 命名空间一致，无冲突，改名成本仅限文档；用户镜——名字自解释「产 spec」，与 `sdflow-spec-review` 成对好记；开发循环镜——前缀一致使 `/sdflow-` 补全即可列出全家族。主次：**用户镜主导**（命名的唯一产出就是可记性）。

**D8 失败降级阶梯 + 诊断契约**（备选：fail-closed 整体中止）。检索败 → 主 session 亲查；生成败 → 重试一次 → 主 session 亲写；每级降级 MUST 如实报告。openspec CLI 不可用/**schema 不兼容**是唯一 fail-closed（产物契约单一源）。
🔴 **报告必须 actionable**〔spec-review-amendment F-18〕：降级/失败报告 SHALL 含 **problem + cause（exit code / 缺失文件 / 实际版本）+ 可执行的下一步**（如「回运行 checkout 跑 `bash setup.sh`」「跑 `/openspec-upgrade`」）。否则安装问题会长期隐藏在「能跑但更贵、更慢」的降级模式里。
🔴 **外部检索的退避与错误分类**〔spec-review-amendment F-25〕：规定总时间预算；仅对 429/5xx 做一次带 jitter 的有界重试；认证/schema 错误立即 fail-closed；**降级前确认替代路径不复用同一故障依赖**（原文「宿主管理超时 → 主 session 亲查」可能再次调用同一故障依赖，不构成真降级）。
「重试一次」的次数〔spec-review-amendment F-30〕：无强依据，**按通则④判为可接受边角**；改写为「按失败类型判断——瞬时错误重试一次，schema/契约错误不重试直接降级」，不为此单独返工。
三镜〔F-27 补齐〕：系统镜——阶梯每级独立可测，fail-closed 边界收窄到 CLI 一处；用户镜——降级可见、有修复指引；开发循环镜——避免整体中止造成的重跑成本。主次：**用户镜主导**（诊断质量决定人能否自救）。

**D9 纪要落盘 change 目录、FF-0 与 `openspec new` 前移至 B 起手**〔窄复核订正：原写「前移至 B **收敛**」，导致 B 进行中无落点、增量落盘无法执行〕（备选：scratchpad 暂存 + Phase C 起手建 change——被否：①scratchpad 为 per-session 目录，session 崩溃即丢承重件；②B 收敛 checkpoint 时仓内零变更，`checkpoint-commit.sh` 静默跳过；③即使纪要进仓，feature 分支 Phase C 才建，B checkpoint 落错分支）。
🔴 **原论证的盲点已修**〔spec-review-amendment F-12〕：否决 scratchpad 的理由（「session 崩溃即丢」）**对本方案的 B 收敛前窗口完全同样成立**——只是把丢失窗口从「到 C 起手」挪到「到 B 收敛」，而 SA-03 明确禁止用固定轮数当停止条件 ⇒ **首次落盘无有限上界**。**处置**：Phase B **增量落盘**（每条承重约束站稳即追加写 memo 草稿），把全损窗口收窄到「两次保存之间」。
🔴 **「删分支即净」补条件限定**〔spec-review-amendment F-05〕：**当且仅当 B 收敛时工作树是干净的**。否则 FF-0 的 `checkout -b` 会把用户的脏改动带上新分支，`checkpoint-commit.sh:51` 的无条件 `git add -A` 再把它们全部提交 ⇒ 删分支会连用户被裹挟进来的活一起删。
**为什么 change 名可以在 B 起手就定**〔窄复核〕：SA-03 的相位 A 收束禁止清单已含「**目标态一句话尚写不出**」⇒ 进入 B 时必然已能写出目标态 ⇒ change 名此时即可定。原本「B 尾信息才足够」的顾虑被该判据消解。**且 openspec CLI 无 rename change 命令**（实查 `openspec --help`：仅 `new change` / `archive`，无 rename）⇒ 「先用暂定名、收敛时改名」不可行，手工 `git mv` + 改 `.openspec.yaml` 等于手搓 change 目录结构（SA-05 禁止）。
代价：拷问若推翻目标态导致名字不再贴切，就留一个名字略偏的 change 目录——**按通则④判为可接受边角**（在 feature 分支内，删分支即净）；拷问后放弃同理。
三镜〔F-27 补齐〕：系统镜——承重件进 git，可重入与审计双得，代价是 change 目录可能留空壳；用户镜——中途放弃的损失从「全损」降到「上次保存点」；开发循环镜——B checkpoint 落对分支，retro 归因可用。主次：**系统镜主导**（承重件持久化是 `/clear` 无损的前提）。

**D10 canonical 规则单一源同 change 同步**〔spec-review-amendment F-02 · 新增决策〕（备选：defer 到「下游推广另 change」——**已否决**）。本 change 与**七处**既有权威源冲突（清单见 SA-11），而本仓运行时经 `resolve-workflow.sh` 解析到**全局 canonical**、仓内不留副本 ⇒ 不同步即：**人看 README 得到新入口，AI 从 bundle 得到旧入口，且二者对 `/clear` 直接矛盾**。`generation-process.md:79-80` 载有同族防漂移警告（原文针对 ADR/术语路径约定，此处类比引用）。defer 掉的是收益不是成本。
三镜：系统镜——规则单一源保持不分叉，代价是本 change 要动 bundle（下游随 `sdflow-init update` 获得）；用户镜——不会读到互相矛盾的两套流程；开发循环镜——省掉「另一个 change 才修」期间所有人踩坑的成本。主次：**系统镜主导**。

**D11 `install_agents()` 新写，不沿用 `install_into`**〔spec-review-amendment F-10 · 新增决策〕（备选：沿用 `install_into` —— **不可行**）。
实证：`setup.sh:38-39` 只认**顶层目录**且必须含 `SKILL.md`，`sdflow-spec/agents/` 是二级目录、散装 `.md` 进不了该循环；`setup.sh:27-32` 的 `is_our_marker_copy()` 判据 `[ -f "$1/.sdflow-skills" ]` 对散装文件是**路径谬误、恒 false**；`setup.sh:106` 的判据 `[ ! -d "$REPO_DIR/$entry_name" ]` 对 `sdflow-local-researcher.md` **恒真**；`setup.sh:211` 的 `cleanup_orphans` 只对两个 skills 目录调用；`setup.sh:60` 会无条件替换任何同名 symlink。
**设计**：Unix 逐文件 `ln -snf`；所有权守卫 = 「**只接管软链、且 `readlink` 指向本仓**，其余一律 skip 并计入 `skipped[]`」。⚠️ **这比既有 idiom 更严，不是复用**〔窄复核订正〕：`setup.sh:128-136` 处理 `$sdflow/workflow` 时只区分「软链 vs 真目录」，`readlink` 的结果仅用于**打印告警**、**不作为守卫判据**（是软链即无条件 `ln -snf` 覆盖，无论原指向谁）。⇒ `install_agents()` 的 readlink 归属校验须**新增**，MUST NOT 声称沿用现状。
🔴 **Windows 分支明写取舍**：散装 `.md` 无 marker 落点 ⇒ **Windows 下不铺 agents，走主 session 亲查/亲写路径**，并在 `skipped[]` 报一行。MUST NOT 写「copy + 所有权守卫」这种做不出来的东西。
🔴 **`--check` 的真实性质**〔spec-review-amendment F-29〕：`setup.sh:261-266` 的 `if !` 结构使 `set -e` 不触发、**退出码恒 0** ⇒ 它是**提示不是门**。真正会红的是 `hack/tests/`。spec 措辞按此如实写。
三镜：系统镜——新增独立安装协议，与 skills 路径解耦；用户镜——Windows 用户得到明确降级而非静默失败；开发循环镜——需补全仓首个 setup.sh 测试（`test_install_agents.py`），一次性成本。主次：**系统镜主导**。

**D12 SKILL.md 体量控制：表格型内容外置到 `references/`**〔spec-review-amendment F-16 · 新增决策〕（备选：单文件全承载 —— 原设计的隐含选择）。
实测基线：本仓 15 个 SKILL.md 为 168–633 行 / 10.7–75.5KB；最重两个（`sdflow-code-review` 572 行/75.5KB、`sdflow-spec-review` 490 行/72.7KB）都是**单一职责**编排器。本 skill 行为面更宽（三相位 + 状态机 + dispatch + 降级阶梯 + 出口序列 + ADR 钩子），单文件大概率突破 700-800 行。失效模式：lost-in-the-middle、提前宣告阶段完成、漏掉降级报告、重入走错分支——**一次 happy-path dogfood 抓不到**。
**设计**：降级阶梯表、ADR/术语最小模板、决策纪要字段 schema 这类「表格型、少判断」内容拆到 `sdflow-spec/references/`；SKILL.md 主体只留三相位编排逻辑与判断指引（对齐 `sdflow-code-review` 外置 `code-checklists/domains` 的既有模式）。
三镜：系统镜——多一层文件引用；用户镜——无感；开发循环镜——降低执行 AI 的遵从度衰减风险。主次：**开发循环镜主导**。

## 失败模式表〔BASE-06·TG-08/15〕

〔spec-review-amendment F-05/F-11/F-03/F-13：原表六行全是工具失败，本次补入四行状态/环境类失败〕

| 失败模式 | 检测 | 处置 | 超时/回滚〔D-4〕 |
|---|---|---|---|
| **工作树不洁进入 B 收敛**〔F-05，本仓已真实发生过：`openspec/issues/buglist/2026-07-04-buglist.md:26-28`〕 | B 收敛前 `git status --porcelain` | **halt 报告给人**（stash / 先提交 / 确认带过来）；MUST NOT 静默 `add -A` | 未提交，无需回滚 |
| **人在 B 中途放弃**〔F-05/F-12，D9 把它变成常态可达〕 | 无（人主动） | memo 草稿留在分支内；删分支即净（**仅当工作树曾干净**） | 删分支 |
| **在其它 feature 分支上开新 change**〔F-11〕 | FF-0 三分支判定（保护分支 / `feat/{本 change}` / 其它） | 「其它」→ **halt 问人**（从当前切出 / 回 base 切出 / 就地继续） | 未建目录，无需回滚 |
| **`git checkout -b` 失败（分支已存在）**〔F-11〕 | 命令 exit code | fallback 到 `git checkout feat/{change}`（存在则复用）；否则如实报告让人决定 | — |
| **陈旧 `decision-memo.md`**〔F-11〕 | C 起手核 memo 身份字段（change/branch/时间戳/决策 hash）对不上当前盘面 | 拒绝进 C，呈现旧 memo 摘要给人确认；MUST NOT 静默复用 | — |
| **writer 写半截/垃圾**〔F-03〕 | **`openspec validate <change> --strict`**（合格态）+ status（存在态）——**二者分开** | validate 不过即判该产物**未完成**，进重试/亲写阶梯（**非**「文件存在即跳过」）；写入用临时文件 + 原子替换 | 按 preimage hash 精确回滚该文件 |
| **CLI schema 漂移（版本对、行为变）**〔F-13〕 | 自调 `instructions --json` 后做最小 schema 断言（必需字段存在性 + 类型） | **fail-closed 中止**，报实际版本 + 修复命令 | 未写产物 |
| agent 定义解析失败（未跑 setup / Windows / Codex 宿主） | 派发报错 | **主 session 亲查/亲写**（不退通用子代理，见 D3）；报告标注 | 无状态 |
| researcher 超时/失败 | Agent 工具错误返回 + 错误分类（429/5xx vs 认证/schema） | 429/5xx 一次带 jitter 重试；其余立即主 session 亲查；**确认替代路径不复用同一故障依赖** | 总时间预算，见 D8 |
| spec-writer 失败/产物缺失 | 写后核验（validate + status） | 按失败类型：瞬时错误重试一次 → 亲写；报告标注降级 | 产物可 git checkout 丢弃 |
| openspec CLI 不可用/报错 | 命令 exit code | **fail-closed 中止**，报错给人（含版本与修复命令） | `new change` 前后记录 change 目录快照，非零退出后核 `.openspec.yaml`/status，**精确报告 partial state，不假定原子性** |
| 生成中断（部分产物完成） | status + validate 对账 | 如实报告完成/未完成清单；按相位状态机重入 | 分支内 git 状态即真相 |
| 纪要缺失/不完整进入 Phase C | C 起手核验存在 + 必填字段非空 + **身份匹配** | 拒绝进入生成，退回 Phase B | — |

## 可观测性〔BASE-11〕

- 各相位完成打 checkpoint commit（全局 `checkpoint-commit.sh`，slug 含相位名）——补 retro **归因率**缺口（`unknown` 桶现占 56%）。
- 降级事件（亲查/亲写/重试/fail-closed）MUST 出现在对人的完成报告中，**含 problem + cause + fix**（D8），不静默。
- 三个外部依赖各自失败时，报告 MUST 能定位到**是哪个依赖、哪个版本、怎么修**〔TG-08 · BASE-11〕。
- token 观测：阶段二 A/B 量**总** token 与总美元（三路对照），非 `/usage` 粗粒度前后差。

## NFR 数字化〔BASE-16〕

〔spec-review-amendment F-08：删去「65KB/40 轮」基线（全仓无出处，实测中位数 42KB）与由其推出的绝对值目标〕

| NFR | 数字 |
|---|---|
| 生成环节输出单价 | 主档价 → mid 档价（Fable $50/M → Sonnet $15/M；Opus $25/M → $15/M）。⚠️ **这是单价表常量，不是本 change 的产出**——不作为成功指标 |
| 生成环节节省上限 | 按 42KB 中位数（≈20–25K output tokens）折算：**≈$0.9**（Fable 主）/ **≈$0.25**（Opus 主），占单次阶段一成本的个位数百分比 |
| 单次阶段一总成本 | **由阶段二 A/B 三路实测给出，本文不预设**（原绝对值 $15-20→$10-13 无推导支撑） |
| 拷问覆盖率 | 管线内建默认路径（**非机械保证**）；机械审计信号 = `decision-memo.md` 必填小节非空的 **grep 门**（会红） |
| /clear 无损 | 阶段二「上下文缺失」finding = 0（**N=1 自评，非统计显著**） |
| dispatch 开销阈值 | 〔F-23〕改为**事后可复核**形式：主 session 直接查同类任务累计工具调用 > 5 次 → 下次同类改派。原「预计材料 ≳ 数百行」在派发**前**不可判定 |
| SKILL.md 体量 | 主体 ≤ **600** 行（表格型内容外置 `references/`，见 D12）。⚠️ 500 行曾被考虑但偏紧——既有单一职责编排器已 490/572 行，本 skill 行为面更宽，过紧会把内容硬挤进 `references/` 反致割裂〔窄复核订正〕 |

## Risks / Trade-offs

- [mid 档成文质量低于强档亲写] → 纪要下发承载 why + 终审兜判断层 + 阶段二 spec-review 安全网；**且由 D2 的阶段门把关**——A/B 不达标即停在阶段一薄编排。
- [`subagent_type` 派发机制未在本仓实测] → 阶段二**起手门**判 GO/NO-GO；NO-GO 即停在阶段一，**不静默走 fallback**（fallback 已被证明是提权路径，见 D3）。
- [终审只核「纪要↔产物」，抓不到「纪要漏记的对话 nuance」] → 纪要由主档亲笔 + 增量落盘；终审**增核 design↔specs 互相一致**〔F-14〕；`/clear` 无损验收使漏记在阶段二显性化。
- [新增全局 `~/.claude/agents/` = 新漂移面 + 命名空间污染] → `install_agents()` 只接管自属软链（D11）；排他式 `description`（BASE-28 S5）；通则块由 sync_principles **glob** 机械守。
- [15× token 溢价风险] → 子代理单一职责、短 context、外派阈值；生成串行非大 fan-out；**且由阶段二 A/B 实测把关**。
- [canonical 改动影响下游消费项目] → 阶段一只改源，阶段三经 `sdflow-init update` 推下游；改动是「加分支 + 加具名例外」，非删除既有路径。

## Migration Plan

部署：merge 后在**开发 checkout** 跑 `setup.sh`（铺 agents + 校验 sync `--check`）；运行 checkout 走 `/sdflow-upgrade`（pull + setup 原子路径）。

🔴 **已知窗口（如实点名，不依赖读者联想）**〔spec-review-amendment F-17/X2〕：
- 本 change 新增顶层 skill，属 `CLAUDE.md:177,182` 记载的**反向窗口**场景（pull 后软链须 setup 才存在）。因 `disable-model-invocation: true`，唯一后果是「敲命令提示不存在」，**无静默误调风险**（不同于 `impl-pipeline: tickets` 那例）。
- **从开发 checkout 跑 `setup.sh` 会把全局 skill 链接整体指向 WIP checkout**（`setup.sh:38,68`），不只是测新 skill。测完 MUST 在运行 checkout 重跑 setup 还原。

🔴 **回滚（如实改写）**〔spec-review-amendment F-10〕：原文称「revert + 重跑 setup.sh，孤儿清理自动移除 agents 链接」——**不成立**：revert 会把 `install_agents()` **连同其清理逻辑一起撤掉**，重跑时没有代码去看 `~/.claude/agents/`，两个悬空软链**永久留下**。（与 skills 不同：skills 的 `cleanup_orphans` 是通用的、不随单个 skill 被 revert。）
**正确顺序**（`setup.sh` 无 uninstall 分支——`grep -ic uninstall setup.sh` = 0；实际落地动作见 `install_agents()` 注释：删源目录 + 重跑新版 setup 即可，无需另造开关）：① **仍运行新版 installer**（含 `install_agents`/`cleanup_agent_orphans`）时，先删除 `sdflow-spec/agents/` 源目录（或其下 `.md` 文件），重跑 `setup.sh`——命中 `install_agents()` 的「源目录消失 ⇒ 不铺设但清理照跑」分支（`if [ ! -d "$src_dir" ]; then cleanup_agent_orphans "$dest" ""`），把 `~/.claude/agents/` 下已铺的软链清掉；② 再 revert commit（此时 `install_agents`/`cleanup_agent_orphans` 与源 `.md` 一起撤走，但全局软链已在①清空，不留悬空）；③ 重跑 setup.sh（旧版逻辑，agents 相关为空操作）。顺序不可颠倒——若先 revert 再 setup，`install_agents()` 连同其清理逻辑一起消失，`~/.claude/agents/` 下的软链永久悬空（`impl-reports/task6-stage3-conditional.md` 回滚演练 C 组反向对照实跑：先 revert 再 setup ⇒ 3 条悬空链、exit 0、零告警）。canonical 规则区改动随 revert 还原（本仓源），下游需重跑 `sdflow-init update`。三个原 skill 未动，回滚后旧流程原样可用。

## Open Questions

见 proposal〔TG-21〕：A/B 三路实测基线（人，阶段一验收后 / 阶段二动工前）；agent 定义是否改为随 bundle 分发（阶段三）；canonical 改动的下游推广时机（阶段三）。

## Compliance〔D-6〕

- **adr/0005 dev/runtime checkout 纪律**：遵守——setup.sh 改动在开发 checkout 验证，测完在运行 checkout 重跑还原（Migration Plan 已点名该窗口）。
- **通则托管单一源**：遵守——agent 定义正文的通则块由 `sync_principles.py` 以 **skill 味源**渲染（受众为下发子代理），MUST NOT 手改块内部；投放面用 **glob 发现**（非硬编码清单，否则 SA-07 的「新增未纳入即变红」场景做不出来），并新增 `AGENT_TARGETS` 显式配 `SOURCE`（`PROJECT_TARGETS` 固定用 `SOURCE_PROJECT`，直接加进去会注入错误味源）。
- **host-adaptive-execution「档位按机队分列、skill 引用变量不内联模型名」**：遵守——agents `model: inherit`；SKILL.md 正文写变量名，派发时填该次解析出的具体 id（D4）。档位解析走既有四步加固协议。
- **workflow.md G1「全流程不用 `/clear`」**〔spec-review-amendment Q2 · 原文漏核〕：**带具名例外地遵守**——本 change 为「阶段一→阶段二」这一段增加一处例外，依据是 G1 未覆盖的两条（cache 按模型隔离 + 产/审错档），并**同 change 修订 G1 文本**使单一源不分叉（D6/D10）。MUST NOT 只改本仓非托管区而留 canonical 说反话。
- **DOC-1（正文即最终态）**：遵守——本文无考古层；`[spec-review-amendment]` 标记附于被修正处，说明「改成什么 + 为什么」，非演进史叙述。
- **跨模块共享数据模型边界**：决策纪要为本 skill 私有中间产物（**不并入 design.md**，见 BASE-24）；唯一跨界产物是标准四件套，契约未变。
- **TG-17 信任边界**〔spec-review-amendment F-06 · 原判「不命中」为误判〕：**命中**，处置见 BASE-28 五项（S1 Bash 权限 / S2 出境 secret scan / S3 injection / S4 路径 containment / S5 全局名册）。
- **基准 5（无界语法禁手搓）**：遵守——不解析任何 Markdown/YAML 语法面。⚠️ **但原文对本基准的引用是误用**〔spec-review-amendment F-03〕：原写「产物存在性与**完成态**一律问 openspec CLI（让工具自己回答）」——CLI 源码实证（`dist/core/artifact-graph/state.js:25-29`）其判据是**文件存在性**，回答的是「存在吗」而非「合格吗」。**改为**：存在态问 `status`，**合格态问 `validate --strict`**，MUST NOT 手搓 Markdown 解析器——三者分开写。
