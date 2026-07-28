---
impl-pipeline: tickets
---

## Global Constraints

以下为本 change `design.md` 的承重约束**逐字**摘录（非转述），作为每个 implementer / reviewer 子代理的共享注意力透镜。任一条与 ticket 描述冲突时，**以本节为准**。

### 关于本 plan 文件自身（🔴 执行期红线）

- 本 plan 落盘名为 `superpowers-plan.md`（出票时点的现役 gate/route 契约只认此名）。Task 3 落地共享 resolver 后，**本文件 MUST NOT 被改名为 `tickets.md`**。design Migration Plan 逐字：

  > 🔴 **MUST NOT 重命名任何在途 plan 文件**〔窄复核补:该风险首版未识别〕。理由不是"兼容性",是**完成判据窗口会被重置**:
  > `ship_gate.plan_first_sha()` 用 `git log --diff-filter=A -- <plan_rel>` 取窗口起点,而 `--diff-filter=A`
  > **不跟随重命名** ⇒ 改名后新路径的"首次新增"就是那次改名 commit ⇒ 窗口起点被推后 ⇒
  > **改名之前的全部 `checkpoint(<change>:task<N>-…)` 标签落在窗口外** ⇒ gate 少数 `done_tasks` ⇒
  > 已完成的 ticket 被判未完成、可能被重派。∴ 在途 plan **一律保留原文件名直到该 change 归档**,
  > grandfather 不是妥协、是正确性要求。(新开 change 从一开始就叫 `tickets.md`,无此问题。)

- 同理，**MUST NOT 同时创建 `tickets.md`**——两名并存 ⇒ resolver fail-closed 判 UNKNOWN，本 change 自锁。

### D1 / D1b：档位解析的对齐口径

> **对齐目标 = 四步语义,不是逐字复制**〔spec-review-amendment Q5 拍板〕:三份现存模板本就不一致(`done` 是裸 eval;`code-review` 与 `spec-review` 四步文案相同但"本步第 N 项"交叉引用不同,那是**依文件本地结构派生的量**),`sdflow-implement` 又没有编号起手步骤列表 ⇒ 逐字照抄必产悬空引用。∴ 跨文件交叉引用一律改**具名锚点**("见预检步"),并新增 `hack/tests/test_tier_resolution_parity.py` 对归一化核心段做逐字节比对。

> **[Risk] Codex 宿主下 `sdflow-implement` 不 fan-out 就跑不了任何 ticket**〔评审 H10/H11〕——与 `sdflow-code-review`"不 fan-out 只缩 roster"的降级路径**不同构**。**→ 处置**:`host=unknown`、或 Codex 宿主下能力探针判子代理不可用 ⇒ **fail-loud 硬停**并提示在受支持宿主下运行,MUST NOT 用空档位或默认值继续派发。

### D2b：`review-loop-breaker` 的两项机制修正

> - **身份键**:从"同 file:line + 同问题"改为"同文件 + 规范化问题指纹",**行号只作定位不作身份**——修复几乎必然移动行号,用行号当身份会让同一未解决问题被认成新 finding、轮次计数清零,`MUST NOT 无限循环` 兑现不了。
> - **互斥终态**:原三级处置只回答"finding 是否成立",而触发它的原因是"成立但连续修不掉" ⇒ 确认成立后既无新动作也无终态,可绕回原循环。改为三个互斥出口:不成立→关闭;成立且可修→strong 档 fixer 修复并**仅复验一次**;成立但不可修→进 buglist 并停。

### D3：测试范围与收尾票

> **D3**:每 feature ticket 测试范围收窄为"单元 + 本票 e2e 场景 + 本票 `Blocked-by` 链上模块的集成测试",MUST NOT 跑与本票无依赖关系的集成/e2e〔Q3 拍板:保留中间档,不用绝对禁令〕;出票模式新增不计入 3–6 预算的强制"实现验证"收尾 ticket。

### 收尾票的定位（design 专节，逐字）

> - 收尾票 = **实现期**聚合回归门。它回答的是"全部功能票实现完毕这一刻,聚合套件是否通过",**不声称**"最终代码通过聚合套件"。
> - **既有 Requirement「verify 为收尾最终门,位于所有修复之后」未被触碰**:verify 仍在 `sdflow-done`、仍在所有修复之后,本 change 不修改它。收尾票不是 verify、不替代 verify、不前移 verify。
> - code-review 之后的修复由 **code-review 自身的保障机制**覆盖(双轴/领域镜 + 置信过滤 + 对抗裁决 + 其自身的 fix 循环)。本 change 要解决的是**实现期间**的覆盖空洞,不是给 code-review 再加一层。
> - **残余风险如实登记**:"收尾票锚点相对 code-review 修复而言不是最新"是**已知且接受**的,五问分析见 `decision-memo.md`「接受的边角」。
> - **证据锚措辞 MUST 与该定位一致**:verify 引用该票时,锚的语义是"实现期聚合套件通过"而非"最终全量回归通过",MUST NOT 在 verify 报告里把它写成后者。

### 聚合套件的发现契约（D3b，逐字）

> `sdflow-implement` 要铺给**任意**下游项目,而"单元+集成+e2e 聚合套件"此前无契约。**MUST NOT 解析 Makefile / package.json 去找 target**——那是 `add-sdflow-devenv` 已经付过学费的路(脚本 562→119 行、7 个 fail-closed 罢工分支,`docs/sad/07` 附录 A21;基准 5)。契约:
>
> 1. **命令来源优先级**:① `openspec/config.yaml` 的 `test-suites.{unit,integration,e2e}` 显式配置;② 缺失则由收尾票的 implementer 从仓内既有约定(CI 配置、README、`devenv` 三层框架产物)判定并**在票报告里写明命令原文与判定依据**。
> 2. **"能不能跑"由工具自己判**:候选命令**真跑一遍**看退出码,MUST NOT 靠解析构建文件预判 target 是否存在。
> 3. **缺层不罢工**:仓内确无集成层或 e2e 层时,该层记「未覆盖(本仓无此层)」并附判定依据,**MUST NOT** fail-closed 停机——`sdflow-implement` 的承诺是"不管什么项目都能跑完实现管线",每个罢工分支都在背叛它。
> 4. **证据 schema(确定性,可机验)**:收尾票报告 MUST 含每层一行:`<层> | <命令原文> | <退出码> | <测试时 git rev-parse HEAD>`;未覆盖层写 `<层> | — | 未覆盖 | <依据>`。
> 5. **失败分类**:退出码非 0 时 MUST 分四类处置——① 本 change 引入的回归 → 进 fix 循环;② 仓内既有红测(改动前即红,用 base SHA 复跑确认) → 记录并放行,不阻塞;③ flaky(同命令复跑一次即绿) → 记录并放行;④ 环境故障(依赖缺失/网络) → halt envelope 停并上抛。**Standards 轴 MUST 核验修复方式未靠加 skip、改测试配置、删除或弱化断言蒙混过关**(原措辞只禁"删除或弱化断言",挡不住加 skip)〔spec-review-amendment H9〕。

### 收尾票与普通票的执行契约差异（逐字）

> 〔spec-review-amendment H9〕普通票强制 red-before-green 逐 slice 实现,而聚合套件一次绿则无 red、无 diff。∴ 收尾票 MUST 显式豁免/定制三点:
>
> - **豁免 red-before-green**:该票不写产品代码,验收物是**证据**不是 diff。
> - **证据落 report file,不依赖 commit**:`checkpoint-commit.sh` 在干净树上直接成功退出、不建 commit ⇒ "引用该票自身 commit"可能根本没有 commit。∴ 主证据锚 = 该票的 impl-report 文件路径 + 其内的 SHA 三元组;commit 存在时附之,不存在不判缺。
> - **R-ID 归属**:该票 `R-ID: all`,语义为"覆盖本 change 全部需求的聚合验证",Spec 轴据此核验而非逐条溯源〔spec-review-amendment M6〕。

### T10 scope-check 的统一计数口径（逐字）

> 〔spec-review-amendment M1/M2/M4〕**"落点"的定义**:一处**规范性** T10 引用(grep 命中行为单位,一行含一处算一处)。规范性 = skill 指令 / bundle 规则 / spec / 承载定义的文档;**不含**分析类与历史记录类文档。此前 proposal「4 处」/design「6 个、其余 5 处」/Success Metrics「6 个、其余 4 处」/设计图「9 处」/`adr/0031`「等 5 处」五种口径互不一致,以本表为唯一口径。
>
> **"T10" 保留为历史别名**:新增两条具名规则,CONTEXT.md 术语表登记别名关系 ⇒ 分析类文档提及"T10 三级协议"不算陈旧,无需扫改。

> 🔴 **delta MUST 原样保留这两处的 "T10" 字样**〔spec-review-amendment H6〕:MODIFIED Requirement 归档是**整段替换**,首版 delta 把 `:60` 改成了"按 defer 或停处理",T10 被静默删除,与本表【不动】自相矛盾。

### 两处 Mitigation 声明为「必须实现,非可选」

> **→ Mitigation(必须实现,非可选)**:该 verify 锚 **MUST 按管线条件化**——仅当本 change 走 tickets 轨时才要求;superpowers 轨下该需求判"不适用",MUST NOT 判 gap。

> **→ Mitigation**:`ship_gate` 加**第四道 plan 校验**(tickets 轨:MUST 恰含一张收尾票,且其 `Blocked-by` ⊇ 全部功能票号)。这不是加宽——D3 的核心承诺是"链路里必有聚合回归执行点",无机械守则承诺不成立。

### 改名的共享字符串纪律（tasks.md §5 前言，逐字）

> 🔴 **两轨共用一个文件名(C14),MUST NOT 全局 sed**——superpowers 轨保持 `superpowers-plan.md`。改共享字符串前先不带 `--include` 全量 grep,测试断言 / 生成物 / docstring 全纳入。

### 定位纪律（tasks.md 首行，逐字）

> 🔴 **定位一律用原文片段锚,MUST NOT 用绝对行号**〔spec-review-amendment H14〕:首版把 `203/271/282/545/490-493` 等绝对行号写死在任务里,而 §1 会在 `sdflow-implement/SKILL.md` **靠前处新增一整段**第零步 ⇒ 顺序执行时后续行号整体下移、按行号定位读到错位内容。本版全部改为「原文片段 + 所在小节」定位。design 的 scope-check 表保留行号**仅作阅读索引**,执行时以片段为准。

### Compliance（逐字）

> N/A——纯指令文本、delta spec 与确定性脚本/测试,不涉及数据合规、隐私或安全边界变化。

### 执行期通用

- 权威工作清单 = 本 change 的 `tasks.md`（按小节号索引）；权威设计意图 = `design.md` / `proposal.md` / `specs/`。四件套在实现期**已定稿**：发现设计有问题走 `NEEDS_CONTEXT` / `BLOCKED` 上抛编排层，**MUST NOT 自行改盘**（改四件套会触发 `ship_gate` 的 design 域失鲜 → REFUSE_START）。
- 本机跑测试 MUST 用 `/usr/bin/python3 -m pytest`（裸 `pytest` 与默认 `python3` 均无该模块）。
- 票内验收标准若标注 `[e2e]`，即该票声明的 e2e 场景；未标注则该票无 e2e，只跑单元 + `Blocked-by` 链上模块的集成测试。

---

### Task 1: 四个编排 skill 的宿主/档位解析第零步 + 机械 parity 守卫

**Blocked-by:** none
**R-ID:** R-tier（sdflow-implement 档位解析与声明）, R-tiers-map（模型档位映射）

**交付的行为**：`sdflow-implement` 起手就能解出本机队档位并据此派发四类子代理（implementer / Standards 轴 / Spec 轴 / fix），解析失败一律 fail-loud 硬停而非用空档位继续；`sdflow-done` 的同一位置不再是裸 `eval`；四份第零步拷贝由一个机械守卫锁住，任何一方单边改动即判红。

工作清单权威见 `tasks.md` §1（1.1–1.12）与 §7.2、§7.7；需求见 delta `impl-orchestration` 的「sdflow-implement 档位解析与声明」与 `spec-workflow` 的「模型档位映射」。

要点提醒（皆已在 Global Constraints 展开）：四步语义对齐而非逐字复制；跨文件引用用具名锚点；第零步置于文件最前、两入口共用无条件执行；`host=unknown` 与三档任一为空 **分别**报错且都硬停；Codex 子代理授权清单与其机械断言测试同批改（不改即红）。

- [x] 解析成功路径：`$SDFLOW_HOST ∈ {claude,codex}` 且三档非空时，四类 dispatch 均引用 `$SDFLOW_TIER_MID`，全文无内联模型名
- [x] 失败路径覆盖八类（resolver 不存在 / 不可执行 / 非零退出 / 输出无法 eval / host 非法 / host 空 / tier 缺失 / host=unknown），逐类给 problem+cause+fix，且沿用五要素 halt envelope（ticket 号字段填「—(起手失败,无票上下文)」）
- [x] `host` 空值与 `host=unknown` 报**不同**的 cause 与 fix，空值 MUST NOT 被吸进 unknown 路径
- [x] `sdflow-done` 的裸 `eval` 已升级为同一套四步语义
- [x] parity 守卫测试落地并通过，锁住四个 skill 的第零步归一化核心段（marker token 单行字面量匹配，MUST NOT 演化成解析 Markdown 结构）
- [x] **变异实测**：逐个删除四个 skill 第零步中的任一步，parity 测试**必红**；两种恒真成因（门被别的断言满足 / 压根没用例走到那行）都已排除，变异记录写进 impl-report
- [x] Codex 子代理授权段已含 `sdflow-implement`，其机械断言测试同步通过
- [x] `grep -n "SDFLOW_TIER" sdflow-implement/SKILL.md` 不再是零命中
- [x] `[e2e]` Success Metric 1 证据：Codex 宿主下实跑一次 `sdflow-implement` tickets-plan，记录四类 dispatch 解析到的 model id，确认全 ∈ Codex 机队缺省集、零命中 Claude 机队专名；**配额不可用时如实记「未验证」并留 todo，MUST NOT 用 Claude 宿主的运行冒充**
  - 🔴 该实跑 **MUST NOT 以本 change 为目标**（会覆盖本 plan 文件 = 毁掉完成判据窗口锚，见 Global Constraints）——用一次性 fixture change 或只走到档位解析步即止，二选一并在报告写明取哪种

---

### Task 2: T10 拆成 `T10-choice` 与 `review-loop-breaker` 两条具名规则

**Blocked-by:** 1
**R-ID:** R-stage3（阶段三过设计门后连续自动跑到 merge）, R-tension（outside-voice tension 不静默采纳）, R-tickets（出 ticket 模式产出 tracer-bullet ticket）, R-dualaxis（每 ticket 双轴审加修复环）

**交付的行为**：阶段三「≥2 方案自动选」与「同一发现反复未消解」两个语义不同的场景不再共用一个标签——前者具名 `T10-choice`（15 处规范性落点措辞统一、②步统一升 strong 档），后者具名 `review-loop-breaker` 独立成文（不再出现 "T10" 字样，身份键跨轮稳定，三级处置收敛到互斥终态）。术语表登记两条新规则与 "T10" 的历史别名关系。

工作清单权威见 `tasks.md` §2（2.1–2.11）、§3（3.1–3.4）、§6.3–6.4 与 §7.1；落点清单与统一计数口径见 `design.md`「T10 scope-check」表。

要点提醒：【别名保留】那 1 处**确认不改**；【不动】那 2 处的 "T10" 字样 **MUST 原样保留**（delta MODIFIED 是整段替换，极易静默删除）；行号只作阅读索引，定位一律用原文片段锚。

- [x] Group A 15 处规范性落点全部改名为 `T10-choice`，②步统一声明 strong 档，且「按三镜 + 主次」限定词在两处 spec 落点补回
- [x] `review-loop-breaker` 就地独立成文：不出现 "T10" 字样，写明触发条件、②步 strong 档仲裁
- [x] 身份键为「同文件 + 规范化问题指纹」，明写**行号只作定位不作身份**
- [x] 三级处置为互斥终态：不成立→关闭；成立且可修→strong 档 fixer 修复并**仅复验一次**；成立但不可修→进 buglist 并停；MUST NOT 停在「已确认成立」而无后续动作
- [x] Group B ①档保留并附一句「预期极少触发」的原因说明
- [x] `CONTEXT.md` 术语条目登记两条具名规则 + "T10" 别名关系；`adr/0031` 仅追加一行指针、正文不改
- [x] 全仓 `grep -rn "T10"`（不带 `--include`）复核：Group A 措辞一致、Group B 落点零 "T10" 字样、【不动】2 处与【别名保留】1 处**原样健在未被误删**

---

### Task 3: 计划文件名共享 resolver（机械核心，双存在 fail-closed）

**Blocked-by:** none
**R-ID:** R-tickets（出 ticket 模式产出 tracer-bullet ticket）, R-stage3（阶段三过设计门后连续自动跑到 merge）

**交付的行为**：gate 与 route helper 经**同一份**共享 resolver 定位计划文件——按序探测新名与旧名，命中其一即用之，两者同时存在 **fail-closed 判 UNKNOWN**（不猜），都不存在判 RUN_PLAN。文件名只用于定位，**MUST NOT 参与轨道路由判定**（路由权威仍是 config 键 + frontmatter marker）。同时把「在途 plan 不可改名」这条正确性要求钉上机械用例。

工作清单权威见 `tasks.md` §5.1、§5.2、§5.3、§5.10 与 §5.7 的**新增用例**部分；决策依据见 `adr/0033`（本票不写 ADR，见 Task 4）。

要点提醒：resolver 是单一源，两处 import 同一份，**MUST NOT 手抄第二份**；`impl_route.py` docstring 里指向 archive 归档文件的两处实路径**不改**（它们指的是真实存在的历史文件）。

- [x] resolver 落地并被 gate 与 route helper 共同 import（无第二份手抄）
- [x] 双存在 ⇒ fail-closed UNKNOWN，提示人工删除其一
- [x] 仅旧名存在 ⇒ 照常识别（在途/他轨向后兼容）；两名皆无 ⇒ RUN_PLAN
- [x] `[e2e]` 改名窗口用例：造「改名前有 task1 checkpoint、改名后跑 gate」的 fixture，断言 gate **不会**漏数 task1（或断言该场景被显式拒绝）——`plan_first_sha` 用 `--diff-filter=A`，不跟随重命名
- [x] 既有 gate / route 测试全绿（本票不改测试里的文件名字面量，那属 Task 4）

---

### Task 4: 文件名措辞全量同步（宽重构迁移批次，不计入 3–6 预算）

**Blocked-by:** 3
**R-ID:** R-tickets（出 ticket 模式产出 tracer-bullet ticket）

**交付的行为**：tickets 轨在**指令、bundle 规则、文档、测试断言**四类面上一致地称呼新计划文件名，superpowers 轨的引用原样保留且可逐条归因；历史记录面（归档 change、issues 池、指向归档文件的 docstring 实路径）**一律不动**。

> 这是 `design.md` D5 的宽重构迁移批次：expand（两名并存的 resolver）已由 Task 3 落地，**本序列无 contract 阶段**——旧名对 superpowers 轨永久合法，不存在「删旧形态」这一步。

工作清单权威见 `tasks.md` §5.4、§5.5、§5.6、§5.7（既有测试断言同步）、§5.8、§5.9 与 §7.3。

要点提醒：**MUST NOT 全局 sed**；改共享字符串前先不带 `--include` 全量 grep，测试断言 / 生成物 / docstring 全纳入；`docs/*.html` 这类生成物若有源，改源重跑而非手改产物。

- [x] skill 指令面（出票落盘路径与全部文件名措辞、done 的引用）已同步
- [x] bundle 面已同步，且 `step6-writing-plans.md` 明确其**只管 superpowers 轨、文件名不变**；仓内托管副本同步
- [x] 文档面（overview / map / html / tracker / workflow-skills 三篇 / INDEX）已同步
- [x] 测试断言面已同步，全量 `/usr/bin/python3 -m pytest` 绿
- [x] **不动面**核验：归档 change 与 issues 池原样；`adr/0017` 只追加一行指针、正文不改；指向归档文件的 docstring 实路径未改
- [x] 全仓 `grep -rn "superpowers-plan"`（不带 `--include`）剩余命中**全部**可逐条归因为：① superpowers 轨合法引用 ② 明确标注的历史记录引用 ③ **本 change 在途 plan 文件自身**（在途禁改名，见 Global Constraints）

---

### Task 5: 每票测试范围分层 + 强制「实现验证」收尾票 + gate 第四道校验

**Blocked-by:** 3
**R-ID:** R-frontier（执行模式串行工作 frontier）, R-tickets（出 ticket 模式产出 tracer-bullet ticket）, R-tier（收尾票的双轴审定制）

**交付的行为**：每 feature ticket 的 implementer 只跑「单元 + 本票声明的 e2e 场景 + 本票 `Blocked-by` 链上模块的集成测试」，不再无差别付全套件成本；出票模式恒产出一张不计预算的「实现验证」收尾票承担聚合回归，其套件发现走**真跑一遍让工具自己判**的契约（MUST NOT 解析构建文件）、缺层记「未覆盖」而非罢工；收尾票的存在与位置由 `ship_gate` 的第四道校验机械保证，旧名 plan grandfather 跳过；`sdflow-done` 的 verify 按管线条件化地引用该票证据锚。

工作清单权威见 `tasks.md` §4（4.1–4.10）、§6.1 与 §7.6。

要点提醒（皆已在 Global Constraints 逐字给出）：禁令是「MUST NOT 跑**与本票无依赖关系**的集成/e2e」的中间档、不是绝对禁令；收尾票三处执行契约定制（豁免 red-before-green / 证据锚不依赖 commit / Standards 轴核验范围含「加 skip」）；verify 锚语义 MUST NOT 写成「最终全量回归通过」，且 **MUST 按管线条件化**——superpowers 轨判「不适用」而非 gap。

- [x] 每票测试范围契约已改写，「本票声明的 e2e 场景」的表达方式已在 ticket 骨架层面定义（验收标准标注为 e2e 的条目即是；未标注则该票无 e2e）
- [x] 出票模式恒含「实现验证」收尾票的规则落地：`Blocked-by` 全部功能票号、不计入 3–6 预算、`R-ID: all`
- [x] 聚合套件发现契约五条（命令来源优先级 / 真跑一遍 / 缺层不罢工 / 证据 schema / 四类失败分诊）完整落地
- [x] 收尾票与普通票的三处执行契约差异已显式写明
- [x] `sdflow-done` verify 引用规则落地，锚语义限定为「实现期聚合覆盖」且**按管线条件化**
- [x] `ship_gate` 第四道校验落地：当且仅当计划文件名为新名时校验；旧名跳过并输出一行 grandfather 提示；**gate 无需读 config/marker 即可执行本校验**
- [x] `[e2e]` 第四道校验的测试：含收尾票绿、**删掉收尾票必红**、`Blocked-by` 缺一张功能票必红、grandfather 路径不红
- [x] `[e2e]` superpowers 轨回归（dogfood 盲区）：切到 superpowers 轨验证 gate 仍按旧名判 RUN_PLAN、verify 的聚合覆盖锚判「不适用」而非 gap
- [x] `adr/0032` 落地（含被砍候选：verify 主动执行 / 移到 code-review 之后；含接受的残余风险）

---

### Task 6: 实现验证（收尾票，不计入 3–6 预算）

**Blocked-by:** 1, 2, 3, 4, 5
**R-ID:** all（覆盖本 change 全部需求的聚合验证，Spec 轴据此核验而非逐条溯源）

**交付的行为**：全部功能票实现完毕这一刻，按聚合套件发现契约跑本仓的单元 / 集成 / e2e 三层并产出确定性证据；同时完成跨票才看得见的一致性核验（两份 delta 与实际改动逐条对码、`openspec validate`）。

> **定位（Global Constraints 已逐字给出）**：本票是**实现期**聚合回归门，**不声称**「最终代码通过聚合套件」；不是 verify、不替代 verify、不前移 verify。
>
> **执行契约定制**：豁免 red-before-green（本票不写产品代码，验收物是证据不是 diff）；主证据锚 = 本票 impl-report 文件 + 其内的 SHA 三元组，**不依赖本票产生 commit**；Standards 轴核验范围 = 修复方式未靠**加 skip / 改测试配置 / 删除或弱化断言**蒙混过关。

- [x] 聚合套件命令来源已按优先级判定（config `test-suites.*` 优先；缺失则依仓内既有约定判定并**在本票报告写明命令原文与判定依据**），且**未解析 Makefile / package.json 预判 target**
- [x] `[e2e]` 三层各跑一遍，证据按 schema 落本票 impl-report：每层一行 `<层> | <命令原文> | <退出码> | <测试时 git rev-parse HEAD>`；未覆盖层写 `<层> | — | 未覆盖 | <依据>`
- [x] 退出码非 0 者已按四类分诊处置（本 change 回归 → fix 循环；既有红测以 base SHA 复跑确认 → 记录放行；flaky 复跑一次即绿 → 记录放行；环境故障 → halt envelope 停并上抛）
- [x] `openspec validate harden-implement-review-loop --strict --type change` 通过
- [x] 两份 delta 归档后内容与各 SKILL.md / bundle 的实际改动**逐条对得上**（防 delta 与实现漂移）
- [x] 本票 impl-report 汇总四条 Success Metric 的证据落点（含 Metric 1 若未验证则如实记「未验证」+ todo 号）
