<!-- sdflow:step1-broad-review v1 mode="native" -->

# gstack 广审报告 · harden-implement-review-loop

> **执行方式**：`/sdflow-spec-review` Step1 经 Skill 机制**原生**执行 autoplan（其指令直接进主 session 执行，非子代理转述模拟）。
> **native 声明的侧信道佐证**：autoplan 的 preamble bash（`gstack-repo-mode` / `gstack-session-kind` / `gstack-config` / `gstack-slug`）与 Phase 0.5 的 `codex` preflight 均在主 session 真实执行并回显（`REPO_MODE: solo`、`SESSION_KIND: interactive`、`SLUG: laodao-ai-sdflow-skills`、`codex-cli 0.145.0`）；三个 Codex voice 各自是一次真实 `codex exec -s read-only` 调用（exit 0）。
> **G2 适配**：autoplan 内部两个人类门（Phase 1 premise 确认、Phase 4 最终批准 / User Challenge）**不弹窗**，连同其自动决策一并登记进 `spec-review-report.md` 决策登记区，由设计 HARD-GATE 一次性拍板。

## Phase 0 · Intake

| 项 | 值 |
|---|---|
| 评审对象 | `openspec/changes/harden-implement-review-loop/`（proposal / design / tasks / decision-memo + 两份 delta spec） |
| 分支 | `feat/harden-implement-review-loop` |
| UI scope | **否**（纯 Markdown 指令文本，无组件/界面/交互态）⇒ **Phase 2 Design 跳过** |
| DX scope | **是**（SKILL.md / Claude Code / agent / CLI / 开发者文档；本仓本身即开发者工具，且 AI agent 是指令文本的实际执行者）⇒ Phase 3.5 跑 |
| Codex 可用性 | ✅ `codex-cli 0.145.0`，`codex_reviews=enabled` ⇒ 三相位均 `codex+subagent` 双声，无降级 |

**已跑的机械核验**：`openspec validate harden-implement-review-loop --strict --type change` → **通过**（对应 tasks 5.3）。

**声明的偏离（如实记录）**：三个 Claude 独立镜按 autoplan 契约「NO prior-phase context — subagent must be truly independent」互不依赖，故一次性并行派出（与串行派出语义等价，零损失）。Codex voice 按相位推进：CEO voice 先跑；Eng voice 与 DX voice 在 CEO 共识建成后**并行**派出，两者 prompt 均注入 CEO 相共识摘要，但 **DX voice 未拿到 Eng 相共识**（autoplan 契约要求 DX 得到 CEO+Eng）。此为节省墙钟的有意偏离，影响面 = DX voice 少一层上游上下文；实际产出显示其独立挖出了两条无人重复的高价值 finding（部署路径写错、unknown 宿主语义未定义），未见该偏离造成损失。

---

## Phase 1 · CEO Review（战略与 scope）

### 0.5 双声

**CODEX SAYS（CEO — 战略挑战）** — 11 条（1 critical / 6 high / 3 medium / 1 low）
**CLAUDE SUBAGENT（CEO — 战略独立性）** — 6 条（1 high / 3 medium / 2 low）

### CEO DUAL VOICES — CONSENSUS TABLE

```
═══════════════════════════════════════════════════════════════
  维度                                  Claude  Codex  共识
  ──────────────────────────────────── ─────── ─────── ─────────
  1. 前提站得住？                        弱      否     CONFIRMED（弱）
  2. 是对的问题？                        是      部分   DISAGREE
  3. scope 校准正确？                    可接受  否     DISAGREE
  4. 替代方案探索够？                    否      否     CONFIRMED（不够）
  5. 竞争/市场风险覆盖？                 N/A     N/A    N/A（内部工具）
  6. 6 个月轨迹健康？                    否      否     CONFIRMED（有隐患）
═══════════════════════════════════════════════════════════════
CONFIRMED 3 / DISAGREE 2（均关于「该不该拆 change」→ 转 taste decision 上抛）/ N/A 1
```

### CEO findings（择要，全量已并入 `spec-review-report.md` 合并池）

| # | 来源 | 严重度 | 一句话 |
|---|---|---|---|
| CEO-1 | codex | critical | 聚合回归缺口只补在**非默认** tickets 轨；canonical 缺省是 superpowers ⇒ 默认轨仍无聚合回归，或被无条件的 verify 锚点判出假 gap |
| CEO-2 | codex | high | 「新增一张票」≠「真执行了完整聚合回归」——聚合套件无确定性定义（命令从哪取、缺层怎么办、flaky 怎么办、退出码怎么落锚） |
| CEO-3 | codex | high | 三项 Success Metrics 全是**文本存在性**检查，三个战略前提一个都验不了；改动零收益也能全绿 |
| CEO-4 | codex | high | model-tier 收益前提只证明了「不对称」，未证明因果收益；反而新增一个 fail-hard 依赖 |
| CEO-5 | codex | high | T10 拆标签降低 Group B 可发现性（删了名字又没给新稳定名）；且**计数当场就在漂移** |
| CEO-6 | codex | high | 测试分层建在**虚假二选一**上；「MUST NOT 跑任何超出票面的集成/e2e」的绝对禁令会被例外侵蚀 |
| CEO-7 | codex | high | 三个独立赌注不该打包——回滚粒度绑死，指标无法归因 |
| CEO-8 | codex | medium | strong 仲裁的依据（superpowers 第 4–5 轮换强模型）被过度外推到「首次遇 ≥2 方案」 |
| CEO-9 | codex | medium | 「验证票走普通 implementer+双轴审」是用**规划实体**弥补缺少的**执行门**，抽象层错了；零代码改动时 commit 语义未定义 |
| CEO-10 | codex | medium | 在途迁移把「必须关闭的结构性缺口」降成了「若需要，手动补」——自相矛盾 |
| CEO-11 | codex | low | 「不计入 3–6 预算」正在掏空票数约束（已有两个后门） |
| CEO-12 | claude | high | 本 change 自己的 ADR 判定钩子刚被证明会静默漏判（T247），而 D1/D3 同样满足 ADR 三条件却没开、也没记「为何不需要」 |
| CEO-13 | claude | medium | proposal Impact 与 design 回滚清单**都漏了 `sdflow-done/SKILL.md`**（tasks 4.4 实际要改它） |
| CEO-14 | claude | medium | ADR-0031 驳回「T10 单一源化」可接受，但「留待独立立项」未落成任何 todolist 条目；而该类漂移**已经真实发生过一次**（C8 差异 B） |
| CEO-15 | claude | low | 验证票的修复工作量 ex-ante 不可控，design 未把既有「追加新号」逃生阀显式接上 |
| CEO-16 | claude | low | D1 收益论证只讲架构对称，未用更硬的**跨宿主正确性**做主论据 |

**premise gate（autoplan 唯一非自动决策门）→ 按 G2 不弹窗**：两声共同认定三条前提论证偏弱（CEO-2/3/4），已转 `spec-review-report.md` 决策登记区，设计门拍板。

---

## Phase 2 · Design Review

**跳过 — 无 UI scope**（检查了什么：grep 四件套与两份 delta 全文的 view/rendering 词面——component / screen / form / button / modal / layout / dashboard / sidebar / nav / dialog——零命中；本 change 的产物是 Markdown 指令文本与 delta spec，不含任何用户界面面）。

---

## Phase 3 · Eng Review（架构）

### 0.5 双声

**CODEX SAYS（eng — 架构挑战）** — 8 条（1 critical / 6 high / 1 medium）
**CLAUDE SUBAGENT（eng — 独立评审）** — 11 条（3 中高 / 3 中 / 5 低，含 2 条正面结论）

### ENG DUAL VOICES — CONSENSUS TABLE

```
═══════════════════════════════════════════════════════════════
  维度                                  Claude  Codex  共识
  ──────────────────────────────────── ─────── ─────── ─────────
  1. 架构健全？                          是*     否     DISAGREE
  2. 测试覆盖充分？                      勉强    否     CONFIRMED（不足）
  3. 性能风险已处理？                    N/A     N/A    N/A
  4. 安全威胁已覆盖？                    N/A     N/A    N/A
  5. 错误路径已处理？                    部分    否     CONFIRMED（不足）
  6. 部署风险可控？                      未审    否     Codex 单声 critical → 照样上抛
═══════════════════════════════════════════════════════════════
CONFIRMED 2 / DISAGREE 1 / N/A 2 / 单声 1
* Claude 判「架构健全」的依据是「ADR-9 未被违反、四步各自 resolve 一次是既有一致模式」——该结论经复核成立，
  但它回答的是「补第零步这个动作对不对」，未覆盖 Codex 追问的「验证票放在 code-review 之前对不对」。
  两者不是同一问题，故记 DISAGREE 而非互斥。
```

### 架构 ASCII 图（调用 / 档位解析关系）

```
/sdflow-ship（主 session，inline 链序，自身零 resolve、零派子代理）
  │
  ├─ RUN_SOP        → embedded-test-sop
  ├─ RUN_PLAN       → sdflow-implement mode=tickets-plan   ←【本 change 新增】第零步 resolve
  ├─ CONTINUE_IMPL  → sdflow-implement mode=tickets-exec   ←【本 change 新增】第零步 resolve
  │                     └→ implementer / Standards轴 / Spec轴 / fix（mid 档）
  │                        └→【本 change 新增】末位「实现验证」票：跑聚合套件
  ├─ RUN_CODE_REVIEW→ /sdflow-code-review（既有第零步）
  │                     └→ 🔴 会自动修改并提交源码，且不重跑聚合套件
  └─ RUN_VERIFY     → /sdflow-done（既有第零步 0.4）
                        └→ verify：只 Grep/Read 证据锚，不执行测试
                           🔴 引用的聚合锚点此时已 stale
```

### Eng findings（择要）

| # | 来源 | 严重度 | 一句话 |
|---|---|---|---|
| ENG-1 | codex | **critical** | 聚合套件锚定的是 **code-review 之前**的代码；code-review 会自动修并提交源码却不重跑套件 ⇒ 正面违反既有未改 Requirement`spec-workflow/spec.md`「verify 位于所有修复之后，否则结果 stale」 |
| ENG-2 | codex+claude | high | 「四个 skill 第零步逐字一致」在现有结构下**不成立**——三份现存模板本就不一致，delta 又定义了第四种 |
| ENG-3 | codex | high | 新第零步未解决 `unknown` 宿主与 **Codex 子代理授权**问题：`sdflow-implement` 必派子代理，但授权只覆盖两个评审器；也无能力探针/降级契约 |
| ENG-4 | codex | high | 「验证票自身 commit」不是充分证据：checkpoint 脚本在干净树上**不建 commit**；双轴 reviewer 又被禁止重跑测试；verify 又被禁止相信报告措辞 |
| ENG-5 | codex | high | 「最后一票」无拓扑/gate 机械保证；expand–contract 的迁移批次是否算「功能票」未定义 |
| ENG-6 | codex+claude | high | Migration Plan 部署路径**写错**：`sdflow-init update` 只刷 workflow bundle、明确不装 hack 脚本；`resolve-models.sh` 靠 `setup.sh` 装 ⇒ 单跑 update 会造成 skew |
| ENG-7 | codex | high | delta **没忠实保留** 被替换 Requirement 的 untouched 语义：主 spec NEEDS_CONTEXT Scenario 的「按 T10 处理」被静默删成「按 defer 或停」，而 design 明确把该行列在【不动】 |
| ENG-8 | codex+claude | medium | Group A 清单非穷尽：漏 `ff-generation-constraints.md:68`（切片粒度 T10）与 `docs/workflow-overview.md:257`（人读的并列定义）；且 impl delta 两次展开三级协议时**又漏了**「按三镜+主次」——本 change 在修漂移的同时新造了漂移 |
| ENG-9 | claude | medium | `sdflow-ship/SKILL.md:165` 的「spec-review/code-review/done」三人枚举改完即陈旧 |
| ENG-10 | claude | medium | 「实现验证」票缺 R-ID 归属，与 Spec 轴「按 R-ID 溯源核验」的裁决依据冲突 |
| ENG-11 | claude | 低 | 纯 expand–contract 类 change（0 张垂直切片）下「Blocked-by 全部功能票」语义不明 |
| ENG-12 | claude | 低 | 建议补 golden fixture 钉住新票形状（`test_tickets_plan_golden.py` 现为 3 票、未覆盖新形态） |
| ENG-13 | claude | 低 | SKILL frontmatter description 未同步新增验证票 |
| ENG-14 | claude | **正面** | 机械层通用支持新增票：`parse_blocked_by` 已由 `test_parse_diamond` 覆盖多依赖；`ship_gate` 三道校验不设票数上下界，无 3/6 硬编码 ⇒「不改脚本」声称成立、不会被绊倒 |
| ENG-15 | claude | **正面** | ADR-9「每轮恰好一次」**未被违反**：ship 自身从不 resolve，各下游步各自解析一次是既有一致模式；且 harness 每次 Bash 调用是独立 shell，下游必须各自 eval |

### 测试覆盖图（本 change 的目标态 → 谁验证）

| 新行为 | 该由什么验证 | 现状 | 缺口 |
|---|---|---|---|
| 第零步四步解析真被执行 | 无（指令层） | 仅 `grep $SDFLOW_TIER_MID` 非零命中 | ✅ 存在性 ≠ 正确执行（CEO-3） |
| 四类 dispatch 真用 mid 档 | 无 | 同上 | 无机械守 |
| plan 恒含且仅含一张收尾票 | 应有 gate/golden | `ship_gate` 只验 fence/标题/重号 | **无**（ENG-5 / ENG-12） |
| 收尾票 `Blocked-by` 覆盖全部功能票 | 应有 helper 校验 | `frontier` 只服从显式 Blocked-by | **无**（ENG-5） |
| 聚合命令真执行且通过 | 应有确定性证据 schema | 「引用该票 commit/报告」 | **无**（ENG-4） |
| 四份第零步模板不漂移 | 应有 parity 测试（可仿 `test_async_branch_parity.py`） | 无 | **无**（ENG-2） |
| Group A 落点措辞一致 | 应有 grep 门 | tasks 5.1 人工 grep | 已实证漏 2 处（ENG-8） |

**测试计划产物**：本 change 为纯指令文本，无新增被测代码；上表即「该加而未加的机械守」清单，已并入报告决策登记区。

---

## Phase 3.5 · DX Review（开发者体验）

### 0.5 双声

**CODEX SAYS（DX — 开发者体验挑战）** — 9 条（4 high / 3 medium / 2 low）
**CLAUDE SUBAGENT（DX — 独立评审）** — 7 条（2 高 / 3 中 / 2 低，含 1 条正面核验）

### DX DUAL VOICES — CONSENSUS TABLE

```
═══════════════════════════════════════════════════════════════
  维度                                  Claude  Codex  共识
  ──────────────────────────────────── ─────── ─────── ─────────
  1. 指令对 fresh agent 无歧义可执行？   否      否     CONFIRMED（多处要猜）
  2. 命名/术语可猜？                     否      否     CONFIRMED（T10 运行时无消歧 aid）
  3. 错误消息 actionable？               部分    否     CONFIRMED（不足）
  4. 文档可找到且完整？                  部分    否     CONFIRMED（不足）
  5. 升级路径安全？                      未审    否     Codex 单声 high → 照样上抛
  6. 开发环境无摩擦？                    N/A     N/A    N/A
═══════════════════════════════════════════════════════════════
CONFIRMED 4 / 单声 1 / N/A 1
```

### 开发者旅程（本 change 影响面）

| 阶段 | 谁 | 本 change 后的体验 | 问题 |
|---|---|---|---|
| 1 升级 | 下游仓维护者 | 跑 `sdflow-init update` | 🔴 **拿不到本 change 的行为**（skill 靠 `setup.sh` 分发） |
| 2 感知变更 | 下游仓维护者 | 无 changelog / 无 update 提示 | 🔴 静默 |
| 3 出票 | 出票 agent | 多产一张收尾票 | 🟡 R-ID 该填什么未定义 |
| 4 执行功能票 | implementer | 「跑本票声明的 e2e 场景」 | 🟡 ticket 骨架无 e2e 场景字段，两种合理解读 |
| 5 执行收尾票 | implementer | 跑「聚合套件」 | 🔴 命令怎么发现？缺层的仓怎么办？全绿时提交什么？ |
| 6 起手失败 | 任意 agent | fail-loud 硬停 | 🟡 problem+cause+fix 文案留给现场发明；7 类失败分支未区分 |
| 7 读到 `T10` | 人 / agent | 判不出自己在哪组 | 🟡 运行时无 glossary / 无稳定规则名 |
| 8 在途 plan | 维护者 | 「若需要手动补一张」 | 🔴 与「强制」矛盾，无 grandfather policy |
| 9 终审 | verify | 引用收尾票锚点 | 🔴 该锚点此时已 stale（ENG-1） |

### DX findings（择要）

| # | 来源 | 严重度 | 一句话 |
|---|---|---|---|
| DX-1 | codex | high | 非默认管线的**证据契约泄漏进了两轨共用的终门** |
| DX-2 | codex | high | 收尾票与普通票**执行契约不兼容**：普通票强制 red-before-green，聚合套件一次绿则无 red、无 diff，agent 不知该 DONE / 空提交 / 只提报告；失败时也未区分 regression / 历史红 / flaky / 环境故障，Standards 轴只禁删断言，挡不住加 skip、改测试配置 |
| DX-3 | codex+claude | high | 下游升级对人**静默**，且 `design.md:77` 的生效渠道写错（skill 走 `setup.sh` 不走 `sdflow-init update`，Windows 尤甚） |
| DX-4 | codex | high | 「强制」与 Success Metrics 都无法机械验证——漏掉收尾票仍能过 gate |
| DX-5 | codex | high | 档位解析状态机**自相矛盾**：Requirement 允许 `host=unknown` 时三档为空，失败 Scenario 却对「host 非空但三档任一为空」硬停且未排除 unknown；且 `unknown` 对本 skill 的语义根本没定义（code-review 的「不 fan-out」对必须派 implementer 的 implement 不适用） |
| DX-6 | claude | high | 新第零步把 Codex 宿主变成字面上被支持的路径，但 `AGENTS.md` 的 Codex 子代理授权**仅限两个评审器**，四类 dispatch 不在授权内，四件套通篇未提，Non-Goals 也没列 |
| DX-7 | claude | 中高 | 「逐字一致」结构上做不到（实测三份现存模板的自引用序号就不同），且没有机械守；本仓对同类问题**有先例要机械守**（`test_async_branch_parity.py`），tasks 5.1–5.4 无一条核验模板一致性 |
| DX-8 | claude | 中高 | 「本票声明的 e2e 场景」在 ticket 骨架里**没有对应字段**，两种合理解读产生实质不同的测试覆盖 |
| DX-9 | claude | 中 | 第零步在 `sdflow-implement`（一文件两入口）里的**插入位置与适用范围**未定义，无姊妹先例可抄 |
| DX-10 | codex+claude | 中 | `T10` 运行时**无消歧 aid**：Group A/B 对照表只活在本 change 的 design 里；且计数口径漂移（proposal「4 处」/ design「6 个落点、其余 5 处」/ Success Metrics「6 个落点、其余 4 处」/ 设计图「9 处」/ 已落盘的 `adr/0031`「等 5 处」） |
| DX-11 | codex+claude | 中 | fail-loud 的 problem+cause+fix 文案留给 agent 发明；至少 7 类失败分支需区分；未说明是否复用既有五要素 halt envelope |
| DX-12 | claude | 中 | `sdflow-implement/SKILL.md:372` 与主 spec:60 的 T10 引用是**第三种未命名场景**（问题问出来了但盘面查不到答案，天然跳过①②直取③），拆分后它哪组都不是 |
| DX-13 | claude | **正面** | C8 差异 B 经独立复核**属实**：现存 `spec-workflow/spec.md:83`/`:93` 确实缺「按三镜+主次」，`:638` 与 `workflow.md:106` 带；delta 的修复准确 |

**TTHW 评估**：不适用（非面向新用户的安装路径变更）。

---

## 跨相位主题（2+ 相位独立命中 ⇒ 高置信信号）

| 主题 | 命中相位 | 说明 |
|---|---|---|
| **「新增一张票」= 规划实体，不是执行门** | CEO（CEO-2/9）· Eng（ENG-1/4/5）· DX（DX-2/4） | 三相位六声独立收敛：票被生成 ≠ 聚合套件被执行 ≠ 证据可机验 ≠ 位置正确。**这是本轮最强信号。** |
| **「逐字一致」是一句做不到的承诺** | Eng（ENG-2）· DX（DX-7） | 两相位四声独立命中；且实测证实三份现存模板确已不一致 |
| **T10 复述架构的漂移不是历史问题，是当场正在发生** | CEO（CEO-5）· Eng（ENG-8）· DX（DX-10） | 三相位独立命中：落点漏 2 处、计数五种口径、新写的 delta 又漏了限定词 |
| **Success Metrics 验不了任何一条战略前提** | CEO（CEO-3）· Eng（测试覆盖图）· DX（DX-4） | 三相位独立命中 |
| **部署/迁移路径与实际分发机制不符** | Eng（ENG-6）· DX（DX-3） | 两相位跨模型收敛，且经主 session 独立复核证实 |

---

## 决策审计轨迹（autoplan 自动决策，按 6 原则）

| # | 相位 | 决策 | 分类 | 原则 | 理由 |
|---|---|---|---|---|---|
| A1 | 0 | Phase 2 Design 跳过 | Mechanical | P3 | 零 UI 词面命中，产物无界面面 |
| A2 | 0 | Phase 3.5 DX 跑 | Mechanical | P1 | 本仓即开发者工具，且 agent 是指令文本的执行者 |
| A3 | 0 | 三 Claude 镜并行派出 | Mechanical | P3 | 契约明写互不依赖，与串行等价 |
| A4 | 0 | Eng/DX 两 Codex voice 并行（DX 少一层上游上下文） | **Taste** | P6 | 省墙钟；已如实记为偏离，实测未见损失 |
| A5 | 1 | premise gate 不弹窗、转决策登记区 | Mechanical | — | G2 铁律（本 skill 覆盖 autoplan 默认） |
| A6 | 1 | 「该不该拆成 3 个 change」不自动裁 | **User Challenge** | — | 两模型均建议改变用户已定的 scope ⇒ 按 autoplan 规则**永不自动决策**，原样上抛设计门 |
| A7 | 3 | 全部 findings 不做置信过滤 | Mechanical | P1 | spec-review 优化召回不优化精度（`spec-review.md` §四点五） |
| A8 | 3 | 不在本步修正任何四件套 | Mechanical | P6 | 修正动作属 Step4 `[spec-review-amendment]`，且部分需人拍板 |

---

## 汇总

- **findings 原始条数**：52（Codex 28 / Claude 24），跨相位主题 5 个。
- **严重度分布**：critical 2（CEO-1、ENG-1）· high 21 · medium 18 · low 9 · 正面结论 3。
- **两声均不建议按现状过门**：Codex Eng voice 明写「当前设计不应通过设计门」；Claude 侧最高 severity 为 High 且集中在完整性/机制缺口。
- **未做的部分（如实报告）**：autoplan 的 TODOS.md 自动写入、`gstack-review-log` 与 `gstack-question-log` 落盘、Implementation Tasks JSONL 聚合器均**未执行**——本 skill 的 Step1 只吃 autoplan 的 findings 与自动决策并入合并池，其台账/日志侧产物不在 `/sdflow-spec-review` 的产出契约内。
- **去向**：全部 findings + 自动决策 + User Challenge 已交 Step3 合并去重与对抗裁决，最终落 `spec-review-report.md`。
