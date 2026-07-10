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
   `~/.claude/skills/implement`、`~/.claude/skills/code-review`、`~/.claude/skills/tdd`。任一缺失 →
   **显式停**，报告缺失的具体路径；MUST NOT 降级到臆造替代语义、MUST NOT 静默跳过检查。
   config 未开 `impl-pipeline: tickets` 的仓本不会触发这条路径（缺省仓零暴露）。
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

### 落盘即返回

写完 `superpowers-plan.md` 后**立即返回编排层（ship）**，**MUST NOT** 在同一次调用内继续派发
implementer 或直通执行——必须保留 `ship_gate` 在"落盘之后 / 执行之前"对 fence / 标题 / 重号的三道
校验插入点，让 gate 重新裁决一次是否可以进入 `CONTINUE_IMPL`。

### 收尾：显式 checkpoint（B1 完成窗口锚）

plan 必须单独提交，建立 gate 的 `plan_first_sha` 窗口起点：

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "<change>:plan" "出 ticket 落盘（B1 窗口锚）"
```

这条 checkpoint 的 slug（`plan`）**不带 `task<N>-` 前缀，不计入任何 ticket 的完成数**——它只建立
`[sha, HEAD]` 闭区间的起点，供后续每张 ticket 的 `checkpoint(<change>:task<N>-<slug>)` 落在窗口内
被 gate 识别。

## 执行模式（`mode=tickets-exec`）

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
- 契约：TDD at pre-agreed seams（matt tdd 语义：先与实现者对齐测试的公共接口边界，再红→绿）、
  定期跑 typecheck、结束前跑一次全套件；
- **完成信号后置双写时序**：implementer **实现期提交 MUST NOT 带 `task<N>-` 完成标签**——普通
  commit 即可，标签延后到该 ticket 双轴审通过后才由执行模式补打；
- report file 路径契约：implementer **全量报告**写 `{change_dir}/impl-reports/task<N>-<slug>.md`，
  dispatch 的**返回值只带状态摘要**（四值状态词之一 + 一行摘要），**MUST NOT** 把全量报告贴进
  返回文本（上下文经济学：大产物一律走文件交接，不进 prompt/返回值）。

implementer 状态词表四值处置：

| 状态 | 处置 |
|---|---|
| `DONE` | 进入双轴审 |
| `DONE_WITH_CONCERNS` | 与 `DONE` 同路径进双轴审，implementer 所述 concerns **逐字**附给两轴审子代理〔F7〕 |
| `NEEDS_CONTEXT` | 编排层**仅从盘面**（design.md / specs/ / ticket 文本）自答；答不出 → 走 T10（defer 或停），**MUST NOT 编造**答案 |
| `BLOCKED` | 统一 halt envelope 停并上抛（见下），blocker 记录**落盘** `{change_dir}/impl-blockers.md`（git-tracked，防会话压缩蒸发）〔F7〕 |

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

- **Standards 轴**：仓内文档化标准 + Fowler smell 基线（同 matt code-review 语义），**且**把
  `code-checklists/domains/<命中栈>`（经 `~/.sdflow/hack/resolve-workflow.sh` 解析取得规则根）
  作为标准源注入——这是 dispatch 模板的**必填槽**，不是可有可无的 prose 叮嘱。resolver 非 0 退出
  / 规则根不可达 / 命中栈在 `domains/` 下无对应清单时，Standards 轴 **MUST NOT 宣称通过**：显式
  停，或在报告中记「领域清单未覆盖」并附降级原因〔F13〕——不得悄悄退化成"看着过"。
- **Spec 轴**：对照该 ticket 文本的验收复选框与 `R-ID:` 溯源需求，逐条核验是否真实做到。

裁决处置：

- Critical / Important 发现 → 派 fix 子代理修复 + re-review，循环直至通过；**不带着未修的
  Critical/Important 推进下一 ticket**。
- Minor 发现 → defer 进 todolist，**JSON 显式带 `"change"` 字段**（省略会被脚本自动挂到"当前活跃
  change"，多 change 并行时会挂错，坑见 sdflow-todolist 的 `change` 字段说明）。

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
