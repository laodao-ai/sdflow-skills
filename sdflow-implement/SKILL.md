---
name: sdflow-implement
description: >
  tickets 实现管线双模式编排器——由 /sdflow-ship 按 gate 判定编排调用；含出 ticket + 执行双模式：
  RUN_PLAN → 出 ticket 模式（从 design.md/tasks.md 产出 3-6 张 tracer-bullet 垂直切片 ticket，落盘
  即返回，不直通执行）；CONTINUE_IMPL(done_tasks) → 执行模式（按 Blocked-by frontier 串行派 fresh
  implementer 子代理 + 每 ticket 双轴审）。仅当仓 openspec/config.yaml 的 impl-pipeline 键（或在途
  plan 的 frontmatter marker）取值为 tickets 时，才由 sdflow-ship 链序以显式
  mode=tickets-plan|tickets-exec 字面参数派发；不要在此之外单独触发，也不要作为子代理派发调用。
---

# sdflow-implement — tickets 实现管线双模式编排器

<!-- sdflow:principles:start —— 真相源 sdflow-init/assets/hack/skill-principles.md，由 hack/sync_principles.py 注入，勿手改本区块 -->
## 🟢 四条通则（所有 sdflow skill 共用 · 违反即本次运行失败）

### ① 能查的自己查，能调研的自己调研

答案在**仓里 / 这台机器上 / 公开资料里** ⇒ **自己去拿**，查完**直接给结论**。
**MUST NOT 拿一个自己查得到的问题去占用人的注意力。**

❌「你们前端用什么测试框架？」（`package.json` 里写着）
❌「有没有 CI？」（`.github/workflows/` 看一眼）
❌「这个函数在哪调用？」（grep）

**给结论，不给过程**：「你们的集成测试是 `make integration`，我跑过了，绿」——
**而不是**「我看到 Makefile 里好像有个 integration target，你确认一下？」

**落笔前先证伪**；**引用必须真打开过**（不是「我记得它写着」）；动一个被多处消费的**常量 / 谓词 / 字符串**前，先 `grep` 谁在用它、有什么影响。

### ② 不确定的方案，先调研再给推荐 —— **MUST NOT 甩开放题**

拿不准的时候，**MUST NOT 把几个选项原样丢给人**——那是**把调研的活布置给了人**。
正确动作：**先把能查的查了，带着「推荐 + 依据 + 代价 + 备选」进人门，人只负责拍板。**
**本地无相关代码的设计方案，主动联网找权威最佳实践来调研。**

> ❌「Windows 包怎么产出？（买台机器？GitHub Actions？还是 non-goal？）」——三个选项，零调研，零推荐
> ✅「**建议走 GitHub Actions 的 windows runner。** 依据：① 本仓已有 workflows ② 工具链官方支持
> ③ 公开仓免费。**代价**：签名要证书，首版只能出未签名包。**备选**：降为 non-goal（后果：Windows
> 用户没有可用产物）。**要不要这么定？**」

**⇒ ①② 合起来的三分判据**（每个问句先归一次类）：

| 答案在哪 | 动作 |
|---|---|
| 仓 / 机器 / 公开资料 | **自己查** → 给结论。**不问**（①） |
| 查得到候选与依据（选型 · 路线 · 工具） | **调研 → 推荐 + 依据 + 代价 + 备选 → 人拍板**（②） |
| **只在人脑子里**（偏好 · 踩过的坑 · 拍板权 · 组织约束） | **问** —— **注意力该全花在这里** |

> **人做的是拍板，不是替你做调研。**
> 人的注意力是唯一消耗掉就补不回来的资源：每问一个「你们用什么测试框架？」，
> 就挤掉一个「你上次被这个东西坑到是什么事？」——**而后者只有人知道。**
>
> **「代价 / 后果」按决策三镜展开**：系统镜（耦合 / 依赖 / 复杂度 / 可回退）· 用户镜（体验 / 可感知行为 / 干扰）·
> 开发循环镜（心智负担 / 是否靠人 / 流程开销 / 复用）+ **一句主次判定**（详版 = `spec-checklists` 的 BASE-12 /
> spec-workflow spec；命中 TG-23 才 MUST 书面写满，琐碎决策不强制——避样板税）。

### ③ 以最终目标为准，MUST NOT 拿现状反驳目标

判断「该不该做 / 做到什么程度」**一律锚目标态**，**不受现有代码与设计的束缚**。

**MUST NOT** 用下面这些来论证「目标不该做 / 该缩水 / 可以妥协」：

- ❌「现在的代码不是这么写的」
- ❌「存量数据里没出现过这种情况」
- ❌「现状里这种情况很少见」
- ❌「现有设计不支持，所以改小一点」

> 迁移中「旧数据还没有新形态」是**必然**——拿它当风险基线，会把「**目标态才暴露的面**」
> 误判成「不存在」。这是**拿现状给目标松绑**。
>
> **正确的问法**：「**目标态下的 producer 会不会产出这种形态？**」
> **不是**：「现存文件里有没有？」

> 🔴 **评审类场景是本条的高发区**——评审时，**现状是唯一摆在眼前的东西**，
> 于是「它现在能跑 / 现在没出过事」极易被当成「它是对的 / 不用改」。
> **评审的基准是目标态，不是现状。**

### ④ 方案尽量简化，不为低概率小影响纠结完美方案

评估「做到什么程度」时，默认选**能达成目标态的最简方案**，不追求完美——可牺牲**低概率、影响小、且完美成本过高**的边角。

> ⚠️ **边界（与③）：简化只能砍「防御的深度」，MUST NOT 砍「目标的范围」。**
> 目标态 producer 会产出的**核心形态** MUST 处理（不因「存量少见」缩水，那是③管的）；
> 只有**边角失败模式**的完美防御，才可按 概率×影响÷完美成本 分诊，简化 + 记 todo。

撞到「要不要为这个问题做完美方案」的纠结，**先跑五问，别凭直觉钻**：
**根因**（根源是什么）· **概率**（多大）· **影响**（后果多大，按三镜：系统 / 用户 / 开发循环看）·
**完美成本**（能完美解决吗、成本是否过高）· **简化方案**（有没有成本大幅降、结果可接受的次优解）。

- **MUST NOT** 为一个低概率、影响小、甚至无法完美解决或完美成本过高的问题，反复来回纠结完美方案。
- **止损 / 反沉没成本**：方向一旦被证伪，**MUST 立即止损换向**，MUST NOT 在已被否定的方向上继续优化 / 加码
  （同一方向被纠正 ≥2 次 / 起手前提被推翻 → 停下重定方向，别在细节里打磨一个错的框架）。

### 🔴 传播纪律：**fan-out 子代理 / outside-voice MUST 原文带上这四条**

**子代理与 outside-voice 跑在 fresh context —— 它们看不见本文件。**

⇒ **每一个 fan-out 子代理的 prompt、每一份 outside-voice 的 context，MUST 把本区块
（`sdflow:principles` 从 `start` 到 `end`）原文整段复制进去。**
**MUST NOT 转述、MUST NOT 摘要、MUST NOT 只给指针。**

> **漏带的后果是确定的，不是概率的**：一个冷上下文的镜子，眼前只有现状，
> 它**必然**把「现在能跑」当成「是对的」，把「存量里没见过」当成「不会发生」——
> 而这正是 ③ 要杀的病。**冷是它的价值，也正是它的破绽。**

<!-- sdflow:principles:end -->

tickets 实现管线的唯一编排入口：出 ticket（从 design/tasks 产出可执行的垂直切片）与执行（frontier
串行 + 每 ticket 双轴审）共享一个 skill、两种互斥模式，由 gate 判定的 RUN_PLAN/CONTINUE_IMPL 两态
经 `/sdflow-ship` 链序以显式参数路由——两态的 gate 插入点力学与旧 writing-plans/subagent-dev 管线
等价（D1/D2）。

本 skill 由 ship 主 session 经 Skill **inline 执行**——**MUST NOT 作为子代理派发**：子代理无法再派
子代理，而执行模式需要派发 implementer / 双轴审子代理，这个能力只在主 session 位置成立。

`ship_gate.py` **零改动**——本 skill 只是产出 / 消费 gate 已识别的「试验期外衣」契约
（`superpowers-plan.md` 文件名 + `### Task N:` 标题集 + checkpoint 标签∪复选框双通道完成判据），
不触碰 gate 脚本本身，也不读 `openspec/config.yaml`（config 只在 ship 首跳读一次，见路由说明）。

## 模式派发契约（F4 单一源，与本 change plan 头部逐字共用）

skill 内**不自判模式**——管线选择完全是外部确定值（config 键 → plan marker → 缺省一律 superpowers，
零模型自由裁量），本 skill 只认调用时传入的显式字面参数，不重新判断 RUN_PLAN/CONTINUE_IMPL 语义：

```
sdflow-implement mode=tickets-plan change={change}
sdflow-implement mode=tickets-exec change={change} done_tasks={逗号分隔任务号|none}
```

`RUN_PLAN` → 出 ticket 模式（`mode=tickets-plan`）；`CONTINUE_IMPL(done_tasks)` → 执行模式
（`mode=tickets-exec`，`done_tasks` 原样透传，不重算不猜测）。以上两串与
`openspec/changes/matt-workflow-integration/superpowers-plan.md` 头部 Global Constraints 节逐字
一致——改一处两处一起改，禁止任一侧漂移出独立措辞。

## 依赖的确定性 helper（machine-verifiable，本 skill 不重新发明判断逻辑）

路由与拓扑判断一律走 stdlib-only 脚本，本 skill 只消费其输出，不自行解析 config/plan 结构：

- **route**（由 ship 在派发本 skill **之前** 调用，产出 `PIPELINE_RECEIPT` 决定要不要派发本 skill；
  本 skill 内部不重复调用）：
  ```
  python3 sdflow-implement/scripts/impl_route.py route --root <仓根> --change <change>
  ```
- **frontier**（由本 skill **执行模式内部**每轮调用，解析 `Blocked-by` 拓扑 + 已完成号集，算出
  下一批 next-ready ticket 号）：
  ```
  python3 sdflow-implement/scripts/impl_route.py frontier --plan <plan路径> --done <1,2|none>
  ```

## 出 ticket 模式（`mode=tickets-plan`）

### 起手检查

1. **matt 语义源目录**必须已装（只读消费其语义，不改内部，adr/0002）：`~/.claude/skills/to-tickets`、
   `~/.claude/skills/implement`、`~/.claude/skills/code-review`、`~/.claude/skills/tdd`。**目录存在
   不够**——须逐一 Read 其 `SKILL.md` 头部（frontmatter `description`），核验语义关键词在场：
   `to-tickets` → 含 ticket/切片类词；`implement` → 含 implement/TDD 类词；`code-review` → 含
   review 类词；`tdd` → 含 test 类词。任一目录缺失，或 `description` 与预期语义明显不符（同名空壳、
   被改版成无关用途）→ **显式停**，报告缺失的具体路径 / 具体不符点；MUST NOT 降级到臆造替代语义、
   MUST NOT 静默跳过检查。config 未开 `impl-pipeline: tickets` 的仓本不会触发这条路径（缺省仓零
   暴露）。
   > matt 套件官方仅发 Claude 侧（`~/.claude/skills/`），Codex 运行时未验证——Codex 宿主缺装即走
   > 上述显式停路径，属已知范围收窄非遗漏。〔impl-review-fix〕
2. 读 `{change_dir}/design.md` 与 `{change_dir}/tasks.md`。design.md 若含「切片建议」节，作为
   **建议输入**参考其初步 ticket 划分与阻塞边草图；**无该节则完全自主出 ticket**——粒度争议不问
   用户，走 ship T10 三级决策协议（design D9）。

### 产出：3–6 张 tracer-bullet 垂直切片

- 每张打穿全层（行为级、可独立验证、demoable），**MUST NOT 预写实现代码或具体文件路径**——ticket
  只描述"交付什么行为"，不描述"改哪个文件/写什么代码"（文件路径写死会很快过期，且抢了
  implementer 的判断权）。
- 每 ticket 显式声明 `Blocked-by:`（阻塞它的其他 ticket 号，逗号分隔，或 `none`）与 `R-ID:`（该
  ticket 对应的需求编号，源于本 change 自身 delta spec 的 Requirement ID 缩写）。
- 每 ticket 含验收标准复选框（`- [ ] ...`）。

**宽重构例外〔T120〕**：单一机械改动、blast radius 扫全仓的宽重构（批量改名、改共享类型签名等）
**MUST NOT** 强行拆成垂直切片；改走 **expand–contract** 序列：
1. 1 张 expand ticket（新旧形态并存，不破坏任何调用点）；
2. 若干迁移批次 ticket（各自 `Blocked-by: <expand ticket 号>`，按包/目录切批，批数由 blast radius
   决定，可任意多张）；
3. 1 张 contract ticket（`Blocked-by:` 全部迁移批次号，删旧形态）。

**迁移批次 ticket 不占 3–6 张垂直切片预算**〔E5〕——只有 expand 与 contract 两端计入预算。

### 外衣（ship_gate.py 既有完成判据契约，零改动兼容）

- 落盘路径固定 `{change_dir}/superpowers-plan.md`。
- frontmatter **含且仅含** `impl-pipeline: tickets` 单键——**MUST NOT** 加注释行、示例值，或第二个
  frontmatter 块（杂行 / 第二块会被 gate 的 fence-aware 解析算成幻影任务，或触发 UNKNOWN）〔F5〕。
- 每 ticket 以 `### Task N: <ticket 名>`（N 从 1 连续编号）为标题——与验收复选框、`Blocked-by:`
  共同构成 gate 可解析的完成判据。
- frontmatter 之后、首个 `### Task 1:` 之前，**逐字**携带该 change design.md 的领域约束——从
  design.md 摘出 MUST / MUST NOT / SHALL 类硬约束与 Compliance 条款，逐字（非改写转述）写成一节
  `## Global Constraints`，作为每个 implementer / reviewer 子代理 dispatch 的共享注意力透镜。
- **plan 首次提交后结构不可变**：**MUST NOT** 重号 / 重排 / 删除 / 复用已出的 Task 号；后续若需
  重新规划，只能**追加新号**〔F1〕。

骨架示例（仅示意结构，不是真实 ticket 内容）：

```markdown
---
impl-pipeline: tickets
---

## Global Constraints

<逐字摘自该 change design.md 的 MUST/MUST NOT/SHALL 硬约束与 Compliance 条款>

### Task 1: <ticket 名>

**Blocked-by:** none
**R-ID:** R2

<端到端行为描述，从用户/系统可观察结果角度写，不含文件路径与实现代码>

- [ ] 验收标准 1
- [ ] 验收标准 2

### Task 2: <ticket 名>

**Blocked-by:** 1
**R-ID:** R3, R4

...
```

**无 quiz-the-user**：不做人工粒度确认这一步（matt 原版 to-tickets 有此人类步，本 skill 删除——
阶段三无人类门；粒度争议走 T10，不问用户）。

### 落盘 → checkpoint → 返回（显式三步序列，B1 完成窗口锚）〔impl-review-fix〕

出 ticket 模式收尾按固定顺序执行——**返回发生在 checkpoint 之后**，不是「落盘即返回」；模型读到
「立即返回」不得跳过第②步：

1. **写盘**：完成 `superpowers-plan.md`（结构见上「外衣」节）。
2. **立即执行 checkpoint 命令**：plan 必须单独提交，建立 gate 的 `plan_first_sha` 窗口起点——
   不依赖「首 ticket add -A 捎带提交」的巧合自愈〔adr/0017〕：
   ```bash
   bash ~/.sdflow/hack/checkpoint-commit.sh "<change>:plan" "出 ticket 落盘（B1 窗口锚）"
   ```
   这条 checkpoint 的 slug（`plan`）**不带 `task<N>-` 前缀，不计入任何 ticket 的完成数**——它只
   建立 `[sha, HEAD]` 闭区间的起点，供后续每张 ticket 的 `checkpoint(<change>:task<N>-<slug>)`
   落在窗口内被 gate 识别。
3. **返回编排层（ship）**：checkpoint 提交完成后才返回，**MUST NOT** 在同一次调用内继续派发
   implementer 或直通执行——必须保留 `ship_gate` 在"落盘之后 / 执行之前"对 fence / 标题 / 重号的
   三道校验插入点，让 gate 重新裁决一次是否可以进入 `CONTINUE_IMPL`。

## 执行模式（`mode=tickets-exec`）

### 起手复核（跨会话语义源二次核验）〔impl-review-fix〕

出 ticket 与执行可能跨会话 / 跨天——执行模式起手（frontier 计算前）MUST 重跑与出 ticket 模式
起手检查同款的语义源核验（同上「matt 语义源目录」四项：逐一 Read SKILL.md 头部核验语义关键词
在场），缺失 / 不符 → 显式停，报告具体路径 / 不符点。**MUST NOT** 凭记忆臆造 `tdd` /
`code-review` 的语义（跨会话记忆不可靠，须重新读盘核验）。

### frontier 严格串行

- 调用 frontier helper，用透传的 `done_tasks` 算出下一批 next-ready ticket 号：
  ```
  python3 sdflow-implement/scripts/impl_route.py frontier --plan {change_dir}/superpowers-plan.md --done {done_tasks}
  ```
- **严格串行**——同一时刻至多一个 implementer 子代理在工作，**MUST NOT** 并行派发多个
  implementer（首版红线，design D4/Non-Goal）。next-ready 若一次给出多个候选，仍按号序逐个派发、
  逐个走完双轴审再派下一个。

### 每 ticket 派 fresh implementer

dispatch prompt 必含：

- 该 `### Task N:` 段落全文（含验收复选框）；
- plan 头部 `## Global Constraints` 节全文（逐字，implementer 与 reviewer 共享同一份注意力透镜）；
- **🔴 本 SKILL.md 顶部的「四条通则」区块全文**（`sdflow:principles` 从 start 到 end，**整段复制，不转述、不摘要**）——
  子代理是 fresh context，**看不见本 SKILL.md，也看不见 CLAUDE.md**。漏带 ⇒ implementer 眼前只有现状代码，
  **必然**把「现有代码不是这么写的」当成「那就按现状来」（通则③）。**双轴审的两个 reviewer 子代理同样必带。**
- **🔴 信号权威表**（必填槽，**原文携带**，非可省的 prose 叮嘱）——子代理是 fresh context，
  **未声明即等同未约束**。正面陈述归属（不是禁令清单：禁令只挡列举到的那一种越界形态，
  权威表挡的是整个范畴）：

  | 范畴 | 权威在哪 | 谁写 |
  |---|---|---|
  | **本票完成信号** | ① `superpowers-plan.md` 里该 `### Task N:` 段的验收复选框（段内**须有**复选框**且**全勾才计入——空段不计入）<br>② 提交 subject 上的 `checkpoint(<change>:task<N>-<slug>)` 标签 | **双轴审通过后由执行模式补打**——implementer 实现期 **MUST NOT** 自行勾框或打完成标签 |
  | **本票工作产物** | 实现代码、测试、`{change_dir}/impl-reports/task<N>-<slug>.md` | implementer 自己写 |
  | **设计意图（需求 / 设计 / 规格 / 任务清单）** | `proposal.md` · `design.md` · `specs/` · `tasks.md` | **设计阶段已定稿，实现期不是它们的作者**——发现设计有问题走 `NEEDS_CONTEXT` / `BLOCKED` 上抛编排层，由编排层裁决，**不自行改盘** |

  > 这两行归属**与设计门实际消费的判据一一对应**：`ship_gate.py` 的完成集 = checkpoint 标签通道
  > （窗口 `[plan 首次提交 sha, HEAD]` **闭区间**内、命名空间精确等于本 change 的 `TAG_RE` 命中）
  > **∪** 复选框通道（`_parse_plan` fence-aware 按 `### Task <n>:` 分段绑定、段内全勾）；
  > 设计工件那一行对应 gate 的 design 域失鲜监视集（`proposal` / `design` / `tasks.md` / `specs/`）。
  > **MUST NOT** 在表里声明 gate 并不读取的信号源（如 ledger 文件、返回值里的口头「done」）——
  > 声明了 gate 也不认，只会诱导 implementer 把完成信号写到无人消费的地方。

- 契约：TDD at pre-agreed seams（matt tdd 语义：先与实现者对齐测试的公共接口边界，再红→绿）、
  定期跑 typecheck、结束前跑一次全套件；
- **完成信号后置双写时序**：implementer **实现期提交 MUST NOT 带 `task<N>-` 完成标签**——普通
  commit 即可，标签延后到该 ticket 双轴审通过后才由执行模式补打；
- report file 路径契约：implementer **全量报告**写 `{change_dir}/impl-reports/task<N>-<slug>.md`，
  dispatch 的**返回值只带状态摘要**（四值状态词之一 + 一行摘要），**MUST NOT** 把全量报告贴进
  返回文本（上下文经济学：大产物一律走文件交接，不进 prompt/返回值）。fix 轮次的 implementer
  报告写 `{change_dir}/impl-reports/task<N>-<slug>-fix<轮次>.md`（不覆盖首轮报告，保留审计
  轨迹）。〔impl-review-fix〕

implementer 状态词表四值处置：

| 状态 | 处置 |
|---|---|
| `DONE` | 进入双轴审 |
| `DONE_WITH_CONCERNS` | 与 `DONE` 同路径进双轴审，implementer 所述 concerns **逐字**附给两轴审子代理〔F7〕 |
| `NEEDS_CONTEXT` | 编排层**仅从盘面**（design.md / specs/ / ticket 文本）自答；答不出 → 走 T10（defer 或停），**MUST NOT 编造**答案 |
| `BLOCKED` | 统一 halt envelope 停并上抛（见下），blocker 记录**落盘** `{change_dir}/impl-blockers.md`（git-tracked，防会话压缩蒸发）〔F7〕 |

> `DONE_WITH_CONCERNS` 澄清〔impl-review-fix〕：dispatch 返回值仍只带一行摘要（不违反上文
> 「返回值只带状态摘要」的契约）；执行模式收到该状态后 MUST Read 该票 report file
> （`{change_dir}/impl-reports/task<N>-<slug>.md`）的 Concerns 小节取**全文**，逐字附给两轴审
> 子代理——「逐字」的来源是 report file 全文，不是 dispatch 返回值里的那一行摘要。

**halt envelope 五要素**（`BLOCKED` 与其他一切停机——依赖缺失、gate 拒绝——统一用这个形状呈现，
不是自由散文）：

1. 错误码；
2. ticket 号与名；
3. 已核实证据（implementer 实际做过什么核验）；
4. 已写盘副作用（哪些文件已经改动/新建，防重跑时误判"从零开始"）；
5. 精确恢复步骤（下一步具体要做什么，不是"请检查一下"这种空泛话）。

### 完成信号双写补打（双轴审通过后）

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "<change>:task<N>-<slug>" "<一句话描述>"
```

等价产出 commit message `checkpoint(<change>:task<N>-<slug>): <一句话描述>`，随后同步勾满该 ticket
的验收复选框——**审过才算 done**，两个信号缺一不可。

> **踩坑提示**：`<slug>` 必须真实存在且含横杠（如 `task3-fix-auth`）——`ship_gate.py` 的 `TAG_RE`
> 要求 `task<N>-` 后紧跟至少一个字符，写成 `checkpoint(<change>:task3)`（无尾随横杠）不会被匹配，
> gate 的完成数会卡在 0/N。

resume 时若发现"实现提交在、完成标签缺"，视为**审前中断**——进入续审，**不重新实现**。

**双信号核对（机械可执行契约，执行模式启动或 resume 时 MUST 跑）**〔impl-review-fix〕：对 gate
传入的 `done_tasks` **每个**任务号 N，逐个核对完成标签是否真实存在于提交历史，不信任 gate 返回
的并集（gate 的复选框通道直读工作树，勾框未提交即可能被计入 done）：

```bash
git log --oneline | grep "checkpoint({change}:task<N>-"
```

- 复选框已勾但查无对应标签提交 → 判定「未审半态」：**撤销**该票的验收复选框勾选（恢复盘面与
  提交历史一致）→ 该票从本轮 done 集中**剔除** → 进入续审（重新走每 ticket 双轴审），而非信任
  gate 并集。
- 方向声明：宁可重复审一轮（假阴安全），**MUST NOT** 把仅勾框、查无对应标签提交的票当作已审
  通过处理。

### 文件交接〔T125〕

- reviewer 的 diff 输入以文件传递：
  ```
  git diff <before-sha>..<after-sha> > {change_dir}/impl-reports/task<N>-review-package.diff
  ```
  dispatch prompt 携带该文件路径，**MUST NOT** 把大 diff 贴进 prompt 正文。
- reviewer 报出的 `⚠️ cannot-verify-from-diff` 项（需求活在未改动代码里，或要跨 ticket 才能验证）
  由**编排层亲自消解**：直接从盘面（design.md / specs/ / ticket 文本）核验。**预算上界**——需触碰
  **超过 3 个文件**，或盘面**不可直接解答** → 按「确认缺口退回 implementer」处理，**MUST NOT**
  无限深挖下去〔F7〕。

## 每 ticket 双轴审

implementer 报 `DONE` / `DONE_WITH_CONCERNS` 后，并行派两个评审子代理（各 **<400 词**封顶）：

> **🔴 两个评审子代理的 prompt（以及 implementer / fix 子代理的 prompt）MUST 原文携带本 SKILL.md 顶部的「四条通则」区块**
> （`sdflow:principles` 从 start 到 end，整段复制，不转述、不摘要）——**子代理是 fresh context，看不见本 SKILL.md**。
> **Spec 轴尤其吃通则 ③**：它的判据是「**ticket 声明的目标态**做到没有」，**不是**「现有代码本来就是这样，那就算了」。
>
> **🔴 fix 子代理的 dispatch prompt 同样 MUST 原文携带上文「每 ticket 派 fresh implementer」节的
> 信号权威表**——fix 轮次同为 fresh context，其完成信号与设计工件的权威归属与首轮完全一致
> （fix 也 MUST NOT 自行勾框 / 打完成标签 / 改四件套）。

**权威表缺席不得静默降级**：若因 SKILL 裁剪、模板漂移或上下文预算取舍导致某次 dispatch 未携带
信号权威表，**MUST 显式停并报告缺失**，**MUST NOT** 以「设计门（`ship_gate.py`）已经兜住失鲜后果」
为由默默放行——gate 的监视集分流只消解**失鲜误判**，并不阻止 implementer 写脏设计工件；
本约束与 gate 侧的失鲜判据**各自独立成立**，任一方在场都不使另一方可省。

- **Standards 轴**：仓内文档化标准 + Fowler smell 基线（同 matt code-review 语义），**且**把
  `code-checklists/domains/<命中栈>`（经 `~/.sdflow/hack/resolve-workflow.sh` 解析取得规则根）
  作为标准源注入——这是 dispatch 模板的**必填槽**，不是可有可无的 prose 叮嘱。resolver 非 0 退出
  / 规则根不可达 / 命中栈在 `domains/` 下无对应清单时，Standards 轴 **MUST NOT 宣称通过**：显式
  停，或在报告中记「领域清单未覆盖」并附降级原因〔F13〕——不得悄悄退化成"看着过"。
- **Spec 轴**：对照该 ticket 文本的验收复选框与 `R-ID:` 溯源需求，逐条核验是否真实做到。

裁决处置：

- Critical / Important 发现 → 派 fix 子代理修复 + re-review，循环直至通过；**不带着未修的
  Critical/Important 推进下一 ticket**。**熔断**〔impl-review-fix〕：同一发现（同 file:line +
  同问题）连续 2 轮 re-review 仍未消解 → 停止循环，按 T10 三级决策协议处理（有客观判据自动选 /
  无客观判据派对抗镜复核 / 复核不过或无从复核则 defer 进 buglist 并停上抛），**MUST NOT**
  无限循环。
- Minor 发现 → defer 进 todolist，**JSON 显式带 `"change"` 字段**（省略会被脚本自动挂到"当前活跃
  change"，多 change 并行时会挂错，坑见 sdflow-issues 的 todo 池 `change` 字段说明）。

**无 warm final whole-branch review**——本模式不追加分支级终审步；全部 ticket 完成、gate 判进
`RUN_CODE_REVIEW` 后直接交给冷层 `/sdflow-code-review` 承接（独立冷视角 + 实测捕获承重墙，见下节
去向说明）。

## 裁剪边界声明（防未来好心加回）〔R6〕

三项被砍机制，各自去向明示——如后续有人提议"加回"，先读这节：加回前须先证伪对应去向已失效，而不是
默认"更完整更好"。

- **无 warm final whole-branch review** → 去向 = 冷层 `sdflow-code-review` 在全部 ticket 完成后
  紧随承接分支级终审；这是实证承重墙（独立冷视角能抓循环内被 controller 说服放过的真问题），不是
  可省的重复层。
- **无 progress ledger** → 去向 = 完成态唯一真相源是 gate 的 checkpoint∪复选框双通道；
  `CONTINUE_IMPL` 的 `done_tasks` resume 已结构性覆盖会话中断/压缩失忆，不需要再维护一份跨会话
  状态文件（多一份 ledger = 多一个可能漂移的真相源）。
- **无 task-brief 抽取层** → 去向 = 行为级 ticket 文本（禁代码/文件路径）本身已经足够精简，dispatch
  直接携带 ticket 全文即等价于 brief，不需要再单独抽取一层。
