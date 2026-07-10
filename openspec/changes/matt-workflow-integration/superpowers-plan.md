# superpowers-plan — matt-workflow-integration

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地 tickets 实现管线（新 skill `sdflow-implement` 双模式 + ship 条件路由 + config 键 + 机械 helper），并把 T126 三段分流/衔接契约、T127 grill 瘦跑写进 assets 权威源；本 change 自身走缺省 superpowers 管线（bootstrap）。

**Architecture:** ship_gate.py 零改动（外衣兼容 adr/0017）；路由 = config 键 → plan marker → 缺省 superpowers 三跳纯确定值（stdlib helper 固化）；sdflow-implement 由 ship 主 session inline 执行（D1，禁子代理派发）；规则改 sdflow-init/assets/ 权威源（adr/0003/0005）。

**Tech Stack:** Markdown skill + Python3 stdlib（零第三方依赖）+ pytest。

**注**：本 plan 追溯 tasks.md 20 项（映射见各 Task 标注）；plan 自身无 frontmatter（本 change 走 superpowers 管线，marker 缺席 = 缺省态，正是 D5 契约）。

## Global Constraints（design 领域约束逐字）

- `sdflow-ship/scripts/ship_gate.py` 及其既有测试**零改动**（含 :724/:750 emit 提示串——试验期失真以链序权威声明消歧，Phase B 根治）。
- matt / superpowers 任何 skill **内部零改动**（adr/0002）；语义以 sdflow-implement 内重述实现。
- 管线路由**零模型自动判断**：config 键（仅新出 ticket 时刻读一次）→ plan frontmatter marker（在途只读）→ 键/marker 缺席一律 superpowers；marker **在而非法/重复/损坏 → 停（UNKNOWN 语义）**不静默回退。gate 不读 config（零依赖不变量）。
- 出 ticket **落盘即返回**，MUST NOT 直通执行（保 gate fence/标题/重号三道校验插入点）。
- sdflow-implement 由 ship 主 session 经 Skill **inline 执行**，MUST NOT 作为子代理派发（子代理无法再派子代理）。
- 完成信号**后置双写**（F1）：implementer 实现期提交不带 `task<N>-` 标签；双轴审+修复环通过后由执行模式补打 `checkpoint(<change>:task<N>-<slug>)` + 勾全验收框——审过才算 done；resume 见「实现提交在、标签缺」进续审不重实现。
- plan 首次提交后结构不可变：禁重号/重排/删除/复用 Task 号，重规划只追加新号（F1）；tickets plan frontmatter 含且仅含 `impl-pipeline` 单键（F5）。
- 规则一律改 `sdflow-init/assets/workflow/` 权威源；改后 dev checkout 重跑 `bash setup.sh` 才测得到（adr/0005）；CLAUDE.md 托管块经 `init.py update --dev` 刷新，勿手改块内。
- 实现期 MUST NOT 改动本 change 的 proposal/design/tasks.md 与 specs/（设计失鲜 → gate REFUSE_START）；tasks.md 勾框归 done 归档阶段。
- 改 `scripts/` 必同步跑对应 `tests/`；每任务末 implementer 自己执行 checkpoint 命令（命名空间标签 = gate 完成判据主锚）。

**模式派发字面契约（F4 单一源——Task 1 与 Task 3 逐字共用此二串）**：

```
sdflow-implement mode=tickets-plan change={change}
sdflow-implement mode=tickets-exec change={change} done_tasks={逗号分隔任务号|none}
```

---

### Task 1: sdflow-implement/SKILL.md 双模式主体〔tasks 1.1–1.5；R2/R3/R4/R5/R6〕

**Files:**
- Create: `sdflow-implement/SKILL.md`
- Read first: `openspec/changes/matt-workflow-integration/{design.md,specs/impl-orchestration/spec.md}`、matt 语义源 `~/.claude/skills/{to-tickets,implement,code-review,tdd}/SKILL.md`（只读消费，adr/0002）

**Interfaces（Produces）:** SKILL.md 中引用 Task 2 的 helper CLI：`python3 sdflow-implement/scripts/impl_route.py route --root <仓根> --change <change>`（出 PIPELINE_RECEIPT）与 `... frontier --plan <plan路径> --done <1,2|none>`（出 next-ready ticket 号）。

- [ ] **Step 1**：写 frontmatter：`name: sdflow-implement`；`description` 含「由 /sdflow-ship 按 gate 判定编排调用；含出 ticket + 执行双模式」收窄触发；**无** `disable-model-invocation`（假设表②，Task 8 实测确认）。
- [ ] **Step 2**：写「模式派发契约」节——上方两条字面串逐字入文 + 「skill 内不自判模式：RUN_PLAN→出 ticket、CONTINUE_IMPL(done_tasks)→执行」。
- [ ] **Step 3**：写「出 ticket 模式」节，契约全项：从 design.md+tasks.md 出 **3–6 张 tracer-bullet 垂直切片**（行为级、MUST NOT 预写实现代码/具体文件路径；expand–contract 宽重构例外〔T120〕：expand→迁移批次（各 Blocked-by expand）→contract（Blocked-by 全部批次），**迁移批次不占 3–6 预算**〔E5〕）；每 ticket 显式 `Blocked-by:` + R-ID 标注 + 验收复选框；头部 Global Constraints 逐字节；外衣 = `{change_dir}/superpowers-plan.md` + `### Task N: <ticket 名>` 标题 + frontmatter 含且仅含 `impl-pipeline: tickets` 单键（无注释/示例/第二块〔F5〕）；plan 结构不可变条款〔F1〕；design「切片建议」节 = 建议输入非契约（无则自主出 ticket，争议走 T10）〔D9〕；无 quiz-the-user；起手检查 matt 语义源目录（`~/.claude/skills/to-tickets` 等）缺装→显式停；**落盘即返回 + 收尾显式 checkpoint**（命令原文：`bash ~/.sdflow/hack/checkpoint-commit.sh "<change>:plan" "出 ticket 落盘（B1 窗口锚）"`——slug 无 `task<N>-` 前缀不计完成数）。
- [ ] **Step 4**：写「执行模式」节：frontier 严格串行（MUST NOT 并行 implementer），next-ready 由 Task 2 frontier CLI 计算〔F8〕；fresh implementer/ticket（dispatch 模板含：ticket 全文+Global Constraints、TDD at pre-agreed seams、定期 typecheck、末尾全套件、**实现期提交不带 task 标签**、report file 路径契约）；完成信号后置双写时序（审后补 `checkpoint(<change>:task<N>-<slug>)`+勾框）；状态词表四值处置（DONE→双轴审；DONE_WITH_CONCERNS→同 DONE 进双轴审、concerns 逐字附两轴〔F7〕；NEEDS_CONTEXT→编排层仅从 design/specs/ticket 文本自答、答不出走 T10/停、MUST NOT 编造；BLOCKED→统一 halt envelope〔错误码/ticket 号名/已核证据/已写盘副作用/精确恢复步骤〕停并上抛 + blocker 落盘 `{change_dir}/impl-blockers.md`（git-tracked）〔F7〕）；文件交接〔T125〕：implementer 全量报告写 `{change_dir}/impl-reports/task<N>-<slug>.md` 只返回状态摘要，reviewer 输入 = `git diff <before>..<after> > {change_dir}/impl-reports/task<N>-review-package.diff` 式文件传递，MUST NOT 大产物贴 prompt；Reviewer ⚠️ cannot-verify-from-diff 项编排层亲自消解，预算上界 = 需触碰 >3 文件或盘面不可解 → 按「确认缺口退回 implementer」〔F7〕。
- [ ] **Step 5**：写「每 ticket 双轴审」节：Standards 轴（仓内文档化标准 + Fowler smell 基线 + **`code-checklists/domains/<命中栈>` 经 `~/.sdflow/hack/resolve-workflow.sh` 解析注入 = dispatch 模板必填槽**；resolver 失败/规则根不可达/命中栈无清单 → MUST NOT 宣称通过，显式停或报告记「领域清单未覆盖」+降级原因〔F13〕）∥ Spec 轴（ticket 验收复选框 + R-ID 溯源）；各 <400 词封顶；Critical/Important → fix 子代理 + re-review 环直至通过；Minor → todolist defer（JSON **显式带 `"change"` 字段**）；**无 warm final whole-branch review**（冷层承接）。
- [ ] **Step 6**：写「裁剪边界声明」节，三项各一句去向：无 warm 终审（冷层 sdflow-code-review 紧随承接）、无 progress ledger（gate done_tasks resume 结构性承接）、无 task-brief（行为级 ticket 文本即 brief）——防未来好心加回〔R6〕。
- [ ] **Step 7**：自检（tasks 1.1–1.5 验证条款）：`grep -c "disable-model-invocation" sdflow-implement/SKILL.md` = 0；全文无「出 ticket 后继续执行」路径；派发契约串与本 plan 逐字一致；含 halt envelope 五要素、双写时序、report 路径契约、必填槽措辞、三项裁剪去向。
- [ ] **Step 8**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "matt-workflow-integration:task1-implement-skill" "sdflow-implement SKILL.md 双模式主体(1.1-1.5)"`

### Task 2: route/拓扑机械 helper + pytest〔tasks 2.3；R1/R4〕

**Files:**
- Create: `sdflow-implement/scripts/impl_route.py`（stdlib-only，不 import yaml，不读不改 ship_gate.py）
- Create: `sdflow-implement/tests/test_impl_route.py`

**Interfaces（Produces）:**
- `read_config_pipeline(root) -> (pipeline, note)`：读 `openspec/config.yaml` 顶层 `impl-pipeline:` 行（文本行解析，允许引号值）；缺失/空 → `("superpowers","absent")`；`tickets`/`superpowers` → `(值,"ok")`；其他值 → `("superpowers","unknown-value:<v>")`（F12 区分缺省 vs 非法，非法回显提示行）。
- `read_plan_marker(plan_path) -> str|None`：文件缺 → `None`；无 frontmatter 或无键 → `"superpowers"`（旧管线产物，不嗅探内容）；首块 frontmatter 含 `impl-pipeline: tickets|superpowers` 单值 → 该值；**键重复/值非法/frontmatter 未闭合 → raise RouteStop**（UNKNOWN 语义，防两管线混跑）。
- `parse_blocked_by(plan_text) -> dict[int,set[int]]` + `next_ready(deps, done:set) -> list[int]`：按 `### Task N:` 分段解析 `Blocked-by:`（`none`/逗号号列）；环/自环/引用不存在号 → raise TopoError。
- CLI：`impl_route.py route --root R --change C` → 打印一行 `PIPELINE_RECEIPT change=<c> config=<val|absent> marker=<val|absent|none> pipeline=<selected> plan_sha=<7位|->`，exit 0；RouteStop → stderr 原因 exit 6。`impl_route.py frontier --plan P --done 1,2|none` → 打印 next-ready 号列，TopoError → exit 6。

- [ ] **Step 1**：TDD 先写失败测试——路由矩阵：config 缺失/空值/`tickets`/`superpowers`/拼错值/带引号值；marker 缺文件/无 frontmatter/合法单键/键重复→RouteStop/非法值→RouteStop/未闭合 frontmatter→RouteStop；receipt 行格式断言。拓扑：线性链/菱形/环→TopoError/自环→TopoError/缺依赖号→TopoError/`done` 集过滤。
- [ ] **Step 2**：`pytest sdflow-implement/tests/ -v` 确认全 FAIL（模块未实现）。
- [ ] **Step 3**：实现 `impl_route.py`（纯 stdlib：re/argparse/pathlib/subprocess 仅取 plan_sha 用 `git log -1 --format=%h`；plan_sha 取不到时输出 `-`）。
- [ ] **Step 4**：`pytest sdflow-implement/tests/ -v` 全绿；`pytest` 仓级回归无新增失败。
- [ ] **Step 5**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "matt-workflow-integration:task2-route-helper" "route/拓扑 stdlib helper + 路由矩阵/拓扑 pytest(2.3)"`

### Task 3: ship 链序条件路由〔tasks 2.1；R1/W1〕

**Files:**
- Modify: `sdflow-ship/SKILL.md`（:3 description、:29 链序 RUN_PLAN/CONTINUE_IMPL 两映射、SHIPPED 摘要模板）

- [ ] **Step 1**：`:3` description 的「writing-plans/subagent-dev」表述改管线中性（如「实现管线」），保触发词与其余文字零改动。
- [ ] **Step 2**：`:29` 链序仅改两处映射（其余链序段逐字不动）：
  - `RUN_PLAN→`：先跑 `python3 sdflow-implement/scripts/impl_route.py route --root "$(git rev-parse --show-toplevel)" --change {change}` 取 PIPELINE_RECEIPT（回显进对话）；`pipeline=tickets` → 按字面契约派 `sdflow-implement mode=tickets-plan change={change}`（inline 执行，MUST NOT 子代理派发）；`pipeline=superpowers` → superpowers:writing-plans（原文保留，含 TAG_RE 派发要求）；helper exit 6 → 按 UNKNOWN 停上抛。
  - `CONTINUE_IMPL→`：一律按 plan marker 路由（route CLI 同上，首跳 config 值不再参与）；marker=tickets → `sdflow-implement mode=tickets-exec change={change} done_tasks={JSON done_tasks|none}`；marker 缺席 → subagent-driven-development（原文保留）。
  - 紧随两映射加**试验期权威声明**：「此二态 skill 路由以本链序为权威；gate JSON `next` 在此二态仍输出 writing-plans/subagent-dev，仅信息性（emit 串 Phase B 根治）。『照 next 跑』指令仅约束 RERUN_STALE/STEP_IN_PROGRESS。」
- [ ] **Step 3**：SHIPPED 摘要模板「链:」行加 `pipeline={superpowers|tickets}`（来源 = plan marker）〔F12〕。
- [ ] **Step 4**：自检：路由三跳全为确定值判断（grep 无「合适/判断哪个管线」类模型裁量措辞）；两条派发串与 plan/Task1 逐字一致；`pytest sdflow-ship/tests/` 全绿（authority 测试若 pin 链序 token 需同步则一并改）。
- [ ] **Step 5**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "matt-workflow-integration:task3-ship-routing" "ship 链序条件路由+权威声明+SHIPPED pipeline 字段(2.1)"`

### Task 4: config 键注释段〔tasks 2.2；R1〕

**Files:**
- Modify: `sdflow-init/assets/workflow/config.template.yaml`（metrics 段前加注释段）
- Modify: `openspec/config.yaml`（同段同位；**本仓暂不开键**——试点期才翻）

- [ ] **Step 1**：两文件各加（沿 model-tiers 注释段风格，:52-57 先例）：
  ```yaml
  # impl-pipeline（可选键）——阶段三实现管线路由：tickets | superpowers。
  # 缺省请勿填（缺失/非法值一律 superpowers 旧管线）；仅在新出 ticket 时刻读一次，
  # 在途 change 以 plan frontmatter marker 为准，改本键不影响已出 ticket 的 change。
  # impl-pipeline: tickets
  ```
- [ ] **Step 2**：回归：`python3 sdflow-init/scripts/init.py config-lint --root .` 干净；临时把本仓键打开为 `impl-pipeline: tickets` 再 lint 一次仍放行（init.py:295-299 不拒未知顶层键）后还原注释态；`pytest sdflow-init/tests/` 全绿。确认 update 不注入存量仓（update 不动 config.yaml，:238-239 已固化，测试有覆盖即引用）。
- [ ] **Step 3**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "matt-workflow-integration:task4-config-key" "config.template+本仓 config 增 impl-pipeline 可选键注释段(2.2)"`

### Task 5: golden-file 回归测试〔tasks 4.3；R3〕

**Files:**
- Create: `sdflow-ship/tests/fixtures/tickets_plan_golden.md`（frontmatter 单键 `impl-pipeline: tickets` + 3 张 `### Task N:` ticket + 各含 `Blocked-by:` 行与验收复选框，Task 1 勾满、2/3 未勾）
- Create: `sdflow-ship/tests/fixtures/tickets_plan_fence_dangling.md`、`tickets_plan_fenced_header.md`（fence 内伪 `### Task 9:`）
- Create: `sdflow-ship/tests/test_tickets_plan_golden.py`（import 先例 = test_producer_parser_contract）

- [ ] **Step 1**：TDD 写断言：golden → `plan_task_ids`=={1,2,3}、`plan_unbalanced_fence`==False、`plan_has_duplicate_task`==False、`checkbox_done_ids`=={1}（frontmatter 行不产幻影任务〔F5〕）；fenced_header → task_ids 不含 9；fence_dangling → `plan_unbalanced_fence`==True。（重复 marker 的停判归 Task 2 路由矩阵，此处不跨界 import。）
- [ ] **Step 2**：跑 → 若 golden 断言失败即 fixture 与 gate 契约不符，修 fixture 不修 gate（gate 零改动铁律）。
- [ ] **Step 3**：`pytest sdflow-ship/tests/ -v` 全绿 + 仓级 `pytest` 不回归。
- [ ] **Step 4**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "matt-workflow-integration:task5-golden-file" "tickets 外衣 golden-file 过 gate 三道校验回归(4.3)"`

### Task 6: workflow.md 三段分流 + grill 瘦跑 + 阶段三脚注〔tasks 3.1/3.3/3.4；W1/W2/W3/R4〕

**Files:**
- Modify: `sdflow-init/assets/workflow/workflow.md`（:13-21 图、:68 explore 行、:70 grill 行、:34 与 :74-75 阶段三行、:82、:117）
- Modify: `sdflow-init/assets/snippets/claude-section.md`（禁 /clear 句）
- 刷新托管块：`python3 sdflow-init/scripts/init.py update --root . --dev`（勿手改 CLAUDE.md 托管块）

- [ ] **Step 1**〔3.1〕：阶段一图与 :68 行改三段分流：问题清晰→直接 ff / 单 session 可收敛模糊→opsx:explore / **事中判定**超单 session（已跨 session/跨天、或经历 /clear/压缩仍未收敛）→ wayfinder chart 铺图逐 ticket 决议；wayfinder 缺装（`~/.claude/skills/wayfinder` 不存在）→ 显式降级 explore；wayfinder 行写 TG 前置义务（**增强非转移**：主 session 判 TG 命中写入 map Notes；ff 起手判触发纪律不变——Notes 有则核对、无则照常全判，缺失不硬卡）〔D6/F11，禁「事前预估轮数」措辞〕。
- [ ] **Step 2**〔3.3〕：:70 grill 行派发 prompt 增瘦跑句（逐字要点）：「上游 wayfinder 已决分支：引 resolution 快速核对（决议 vs 代码 ground truth 仍一致）即过；新生成/未决部分照常死磕；design 决策无内联 ticket 回链锚的分支一律全深度，MUST NOT 语义模糊匹配定『已决』；MUST NOT 整跳 grill。」
- [ ] **Step 3**〔3.4〕：:34 与 :74-75 阶段三行加脚注「实现管线可经 `openspec/config.yaml` 可选键 `impl-pipeline: tickets` 路由至 sdflow-implement（缺省不变=writing-plans→subagent-dev），路由细则见 sdflow-ship/SKILL.md 链序」——**不改默认口径**；:82 与 :117 禁 /clear 句在 subagent-driven-development 处并列 sdflow-implement。
- [ ] **Step 4**〔3.4〕：claude-section.md:13 禁 /clear 句同样并列 sdflow-implement → 跑 `python3 sdflow-init/scripts/init.py update --root . --dev` 刷新本仓托管块 → `git diff CLAUDE.md` 确认托管块与 snippet 源一致、块外零变化。
- [ ] **Step 5**：自检：三档判据全部事中可观察；grep workflow.md 无「预估轮数」；瘦跑句限定 resolved ticket 分支。
- [ ] **Step 6**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "matt-workflow-integration:task6-workflow-mainflow" "三段分流+grill 瘦跑+阶段三 config 脚注+禁clear 并列(3.1/3.3/3.4)"`

### Task 7: ff 衔接契约 + 切片建议条款 + 双注入通道〔tasks 3.2；W2〕

**Files:**
- Modify: `sdflow-init/assets/workflow/ff-generation-constraints.md`（FF-0 之后增两节）
- Modify: `openspec/config.yaml` rules 段 + `sdflow-init/assets/workflow/config.template.yaml` rules 段（模板源同步，新铺仓才带；update 不动存量 config——存量仓靠人工按 CHANGELOG 合并，注记于节内）
- Modify: `sdflow-init/assets/workflow/workflow.md` 步骤表 ff 行（原 :69，Task 6 后行号可能漂移，按内容锚定「| 一 | 2 | /opsx:ff |」）

- [ ] **Step 1**：ff-generation-constraints.md 增节「wayfinder→ff 衔接契约（条件 = change 源于 wayfinder map）」三条：① ff 起手逐区读 map——Destination→proposal 动机+Success Metrics（D-5）；Decisions-so-far **逐 ticket zoom 决议全文**（MUST NOT 只读摘要行；zoom 上界 ≤8 张全文，超出按与本 change 相关性截断并在 proposal 注明）；Out-of-scope→Non-Goals 可证伪假设（D-3）。② TG 判命中前置到 chart 阶段写 map Notes。③ proposal 回链 map；design 决策段源自已决 ticket 者内联回链该 ticket（机械 grep 锚，同 R-ID 模式，供 grill 瘦跑判定）。附边界句：「本契约只约束 wayfinder→opsx:ff 出 change 路径；roadmap 结晶直写三件套不经 ff，不受此节约束。」
- [ ] **Step 2**：同文件**独立**增条款「切片建议（条件 = 仓 `impl-pipeline: tickets`，与上节条件不同勿混）」：design 决策区 MAY 含切片建议节（初步 ticket 划分+阻塞边草图）；出 ticket 模式消费语义 = **建议非契约**（无则自主出 ticket）〔D9〕。
- [ ] **Step 3**：双注入通道〔F2〕：config.yaml（+模板）`rules:` 的 proposal 与 design 条目各加一行「change 源于 wayfinder map 时：按 @openspec/workflow/ff-generation-constraints.md『wayfinder→ff 衔接契约』逐区读 map（Destination/Decisions-so-far 逐 ticket zoom/Out-of-scope），proposal 回链 map、design 已决项内联回链 ticket」；workflow.md ff 行 prompt 加「若 change 源于 wayfinder map：调用语显式携带 map 路径并按衔接契约逐区读取」。
- [ ] **Step 4**：实测注入：`openspec instructions proposal --change matt-workflow-integration --json | grep -c "衔接契约"` ≥1（rules 逐字进 instructions）。
- [ ] **Step 5**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "matt-workflow-integration:task7-ff-contract" "wayfinder→ff 衔接契约+切片建议条款+双注入通道(3.2)"`

### Task 8: harness 实测 + 最小演练〔tasks 4.1/4.2；R2/R3/R4〕——**主 session 亲执行**（需 Skill tool 与真实 gate 演练）

**Files:**
- Create: `openspec/changes/matt-workflow-integration/impl-notes.md`（归档材料：4.1/4.2 结论）
- 演练场：`<scratchpad>/drill-tickets/`（独立 git 仓，不触本仓）

- [ ] **Step 1**〔4.1〕：`grep -n "disable-model-invocation" ~/.claude/skills/grill-with-docs/SKILL.md` 确认旗标在 → 结合本 session 实证（主 session Skill tool 调用 grill-with-docs 被 harness 以 disable-model-invocation 拒绝）→ 结论「**阻断**」→ 维持 sdflow-implement 不写旗标（假设表②路径）；结论一句+依据写 impl-notes.md。
- [ ] **Step 2**〔4.2〕：scratchpad 建演练 git 仓：`openspec/config.yaml`（schema+rules 四子键+`impl-pipeline: tickets`）、`openspec/changes/_drill/`（最小 proposal/design/tasks + spec-review-report.md 含 `ship-gate:\n  design_approved: true` frontmatter，人机同权手写合法）。
- [ ] **Step 3**：按 sdflow-implement 出 ticket 模式契约产出 `_drill/superpowers-plan.md`（2 张 ticket：task1 建文件、task2 Blocked-by 1；marker 单键 frontmatter）→ checkpoint plan → `python3 ~/.claude/skills/sdflow-ship/scripts/ship_gate.py --change _drill --root <演练仓>` → 断言 `CONTINUE_IMPL done_tasks=[]`（三道校验过）。
- [ ] **Step 4**：执行 ticket1：实现提交**不带标签** → 双轴审（演练内主 session 亲核，对象是时序非深度）→ 补打 `checkpoint(_drill:task1-hello)` + 勾框 → gate 断言 `done_tasks==["1"]`；中途插测 resume 语义：补标签**前**跑一次 gate，断言 task1 不在 done_tasks（审前中断=续审）。全程 gate 零 UNKNOWN。结果记 impl-notes.md；失败则按假设表①记录降级并回炉 Task 1 措辞。
- [ ] **Step 5**：演练仓整目录留 scratchpad 不入本仓；impl-notes.md 记演练路径与关键输出。Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "matt-workflow-integration:task8-harness-drill" "disable-model-invocation 实测(阻断→不写旗标)+出ticket→gate→执行最小演练(4.1/4.2)"`

### Task 9: 试点判赢材料 + 消费仓缺省验证〔tasks 5.1/5.2；R1/R7〕

**Files:**
- Create: `openspec/changes/matt-workflow-integration/pilot-briefing.md`
- Modify: `openspec/roadmaps/workflow-cost-optimization/roadmap.md`（补 Phase C 占位：目标句+雾区备注〔F9/B6〕）

- [ ] **Step 1**：pilot-briefing.md 写：①候选池 3-5 个（从 `openspec/issues/todolist/` 与 roadmap 池挑**有逻辑面中型**项，列名+一句理由）；②选样拒绝条件成文（跨模块宽重构/接口高度不确定/纯文档琐碎类不入样）；③判据三条+对照分桶口径（retro impl Δ 方向下降 / 冷层 Critical 与 verify FAIL 不升 / 哨兵：冷层捕获「本应被每 ticket 审拦住」严重项占比不恶化→恶化即熔断回退）——**定性人读、无数字阈值**；④PIPELINE_RECEIPT 逐 change 留档+计入样本前核对（误路由剔样）；⑤NEEDS_CONTEXT 停摆率与阶段一上下文成本观测项、token 尽力采集；⑥每试点 SHIPPED 后先 `python3 sdflow-retro/scripts/retro_report.py --root .` 再生核对哨兵再选下一个；⑦implementer 档位钉死 mid。
- [ ] **Step 2**〔5.2〕：选本机消费仓（如 `~/Documents/10-michi`）：确认其 `openspec/config.yaml` 无 `impl-pipeline` 键 → `python3 sdflow-implement/scripts/impl_route.py route --root <该仓> --change probe` → 断言 `pipeline=superpowers`（缺省路径 = writing-plans 不变；gate 零改动故 RUN_PLAN emit 本就未变）→ **零写入该仓**；结果记 pilot-briefing.md（完整阶段三试点归试点期）。
- [ ] **Step 3**：wco roadmap 补 Phase C 占位（目标一句：受限并行 frontier 依赖本 change 判赢为硬前置；雾区备注：缺每 ticket 分支可见性契约设计信息）。
- [ ] **Step 4**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "matt-workflow-integration:task9-pilot-material" "试点判赢材料+消费仓缺省路径验证+wco Phase C 占位(5.1/5.2)"`

### Task 10: 发布同步〔tasks 6.1/6.2/6.3；R1〕

**Files:**
- Modify: `README.md`（Skills 列表 :20 邻位加行）
- Modify: `CLAUDE.md`（**托管块外**「dev/runtime checkout 纪律」节加反向窗口句）
- 执行: dev checkout `bash setup.sh`

- [ ] **Step 1**：README 表加行：`| 编排（阶段三） | \`sdflow-implement\` | tickets 实现管线双模式：出 ticket（tracer-bullet 垂直切片）→ 执行（frontier 串行+每 ticket 双轴审）；由 /sdflow-ship 按 config 键/plan marker 条件路由 |`；「纯 Markdown 编排类」句核对（sdflow-implement 带 scripts/ 属数据类口径→按现文风归类调整一句）。活文档全量表述同步显式留 Phase B——记入 impl-notes.md 供 hand-off 引用〔6.1〕。
- [ ] **Step 2**：CLAUDE.md 块外发布边界句〔6.3 前半〕：「反向窗口：pull 后既有 SKILL 路由（如 ship 链序）即生效（symlink 即时），而新增 skill 的链接须 setup 后才存在——已开 `impl-pipeline: tickets` 的仓在窗口期触发 RUN_PLAN 会调不存在的 sdflow-implement；故 pull 与 setup 之间勿跑阶段三。」
- [ ] **Step 3**〔6.2〕：dev checkout `bash setup.sh` → `readlink ~/.claude/skills/sdflow-implement` 与 `readlink ~/.codex/skills/sdflow-implement` 均指向本仓；setup 输出无异常、无孤儿误删。
- [ ] **Step 4**〔6.3 后半·发布边界步〕：运行 checkout 还原属 **merge+push 后**动作：push 后立即 `/sdflow-upgrade`（运行 checkout pull→setup）→ `readlink ~/.claude/skills/sdflow-ship` 指回 `~/.skills/sdflow-skills`——本步在 done 之后执行，结果补记 hand-off（时序已获用户授权：自动 merge&push+upgrade）。
- [ ] **Step 5**：仓级 `pytest` 终态全绿。Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "matt-workflow-integration:task10-release-sync" "README+CLAUDE 发布边界句+dev setup 建链(6.1/6.2/6.3前半)"`

---

## Self-Review 记录

- **Spec 覆盖**：R1→T1/T2/T3/T4/T9；R2→T1/T8；R3→T1/T5/T8；R4→T1/T2/T8；R5→T1；R6→T1；R7→T9/T4；W1→T3/T6；W2→T6/T7；W3→T6。tasks.md 20 项全映射（1.1-1.5→T1；2.1→T3；2.2→T4；2.3→T2；3.1/3.3/3.4→T6；3.2→T7；4.1/4.2→T8；4.3→T5；5.1/5.2→T9；6.1/6.2/6.3→T10，其中 6.3 运行 checkout 还原为 post-push 发布边界步）。
- **占位符扫描**：无 TBD/TODO；契约串/命令/断言均给定字面值。
- **类型一致性**：`impl_route.py` 的 `route`/`frontier` CLI 与 receipt 字段在 T1/T2/T3/T9 四处引用一致；派发契约二串在 T1/T3 引用 plan 头部单一源。
