# superpowers-plan — rebuild-sdflow-roadmap-v2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** sdflow-roadmap 四件套→三件套 + 去 change 壳直写 + 讨论层分档（explore/wayfinder+footage）+ review 分档 + 近细远雾 + 消费约定双锚；存量迁移按 Q-C 前置受控延后。

**Architecture:** 纯 Markdown 指令与模板重写（零脚本改动、零 assets/workflow 改动〔adr/0003〕）；wayfinder/matt 套件零改动只消费（adr/0002）；tracker doc 单点注入 + CLAUDE.md 双锚制；每步 checkpoint 命名空间标签。

**Tech Stack:** Markdown；验证 = grep 锚点 + 一次真实 wayfinding 演练（TG-18 未命中，无自动化测试）。

**注**：plan 无 frontmatter（本 change 走 superpowers 管线；PIPELINE_RECEIPT 已回显 pipeline=superpowers）。tasks.md 15 项映射：1.1-1.4→T1；2.1-2.3→T2；3.1-3.2→T3；4.1→T4（主 session）；6.1→T5；6.2→T6；5.1-5.3→T7（前置判定+受控延后落档，主 session）。

## Global Constraints（design 领域约束逐字）

- **BREAKING 限定仅新产出**〔SR-1〕：存量四件套包（一切消费仓包）冻结为合法历史形态，skill 续跑 MUST 兼容（一行提示、不报错不强迁）；操作者显式要求保留独立 requirements.md 时遵从（逃生舱〔SR-7〕，头部注明非默认）。
- 三件套直写 `openspec/roadmaps/{name}/`，无 `plan-{topic}` change 壳；「review 处置完才算完」软门移入收尾 checklist **五项**（①Review 处置 ②引用完整·最小引用图判定+报行号 ③footage+memo 不被引用 ④wayfinder 闭环·frontier 空或显式放弃 ⑤CONTEXT-adr 讨论期增量核对）。
- 讨论分档**双判据**：起手显性信号（多阶段/跨天/多子系统）→ 直入 wayfinder chart；起手不明 → explore 起步 + **事中触发**（实际跨 session/压缩仍未收敛）升级——MUST NOT 出现事前轮数预估类措辞〔F11〕。
- 规则 3 两段式：三件套 MUST NOT 引用 `footage/`，也 MUST NOT 引用包根 `memo.md`；memo 保持包根落位不迁〔Q2〕；压缩前 flush 场景 memo 转必需〔SR-5〕。
- design 头部「需求与目标态」章**无编号章名、不占 `## N.` 序列**〔SR-15 级联位移规避〕。
- 命名权 skill 先定（kebab slug + 完整 map 路径**字面量**入调用语）；map 头部持久字段 `Tracker root:` / `Effort kind: roadmap`，续跑一律从 map 字段派生〔SR-3〕。
- 共享真相源写入纪律〔SR-4〕：wayfinder 票内 domain-modeling 调用 SHALL 声明「roadmap 探索期，决策未定稿」；收尾 checklist ⑤核对讨论期 CONTEXT.md/adr 增量与终稿一致。
- review 分档：默认 `/plan-eng-review`；野心信号（外部用户/变现/获客）才 `/autoplan`；跳过仅限人类操作者显式授权、状态记 review-waived〔SR-7〕；依赖失败留「未审待恢复」不静默〔XD3〕。
- 三个判定点（讨论分档/review 分档/收尾 checklist）MUST 对话显式陈述一行 + task-log 留痕；跳过类判定显著呈现（memory: grill-not-skippable）。
- 归档不可变：归档树与下游 change 快照不回改；docs/ 历史快照仅明显误导处加注。**「change 四件套」语境（如 openspec/specs/spec-workflow/spec.md 的 proposal/design/specs/tasks 之谓）MUST NOT 触碰**〔SR-6 撞词排除名单〕。
- 宿主中立探测〔SR-9〕+ 消费仓 tracker doc preflight（缺失 fail-closed 给初始化指引）〔SR-10〕；wayfinder 缺装/套件语义漂移 → 显式降级 explore+memo。
- adr/0015（不新增机器锚/不机读化）、adr/0003（零 assets/workflow 改动）、adr/0002（wayfinder/gstack 零改动）。
- 实现期 MUST NOT 改本 change proposal/design/tasks/specs（失鲜 REFUSE_START）；tasks.md 勾框归 done。
- **存量迁移（tasks 5.1-5.3）本轮 MUST NOT 执行**：Q-C 拍板前置②「首个新流程 roadmap 已走通端到端」未满足——受控延后，T7 落档排期。

---

### Task 1: sdflow-roadmap/SKILL.md 主体重写〔tasks 1.1-1.4；R1-R7〕

**Files:** Modify `sdflow-roadmap/SKILL.md`（430 行主体重写）。Read first：`openspec/changes/rebuild-sdflow-roadmap-v2/{specs/roadmap-planning/spec.md,design.md,proposal.md,tasks.md}`（R1-R7 逐条为契约源；tasks 1.1-1.4 的验证条款 = 本任务验收）+ 现行 SKILL.md 全文（保留仍有效骨架：office-hours 分支、充分度 gate-0 五项 checklist :68-78 原样搬入、整体 plan 话术 :265 存活、规则 5 不实施边界）。

- [ ] **Step 1**〔1.1〕：三件套产出与直写、frontmatter/description 同步「三件套」、去规则 4 change 壳；收尾 checklist 五项（Global Constraints 所列①-⑤逐字要点）；存量四件套包兼容模式 + requirements.md 逃生舱 + 包生命周期 create/continue/replan（同名包不静默覆盖）。
- [ ] **Step 2**〔1.2〕：讨论层分档双判据 + 事中触发双来源（口述/盘面）+ 压缩前 flush 进 memo（该场景 memo 转必需）〔SR-5〕；无雾自降级退 explore 且广度 grill 要点转录不清零 + chart 未持久化预检〔SR-11〕；宿主中立探测 + tracker doc preflight〔SR-9/SR-10〕；充分度 gate-0 沿用现行五项 checklist 原样搬入 + 直接结晶依据一行〔SR-2〕；office-hours 保留为讨论层第三分支（野心信号→前置验证，与 review 分档共用信号词表〔Q-D〕）；wayfinder Task 票限定可行性验证 scope〔SR-16〕；**示例开场白→期望路由对照表 ≥4 例**〔D12〕。
- [ ] **Step 3**〔1.3〕：footage 规则（落盘位置/规则 3 两段式/命名权先定/map 持久字段/顶部路标行/再入约定钉死一种——归档 map-N 或单 map 分批，选定后写死）；调用语模板含字面量路径。
- [ ] **Step 4**〔1.4〕：review 分档 + 整体 plan 调用话术（「三件套视为整体 plan、主入口 roadmap.md」存活验收〔SR-7/D5〕）+ review-waived/显式覆盖记偏离/依赖失败未审待恢复；近细远雾章节（近期 1-2 阶段五节全写含选择理由、远期仅目标句+雾区备注「缺什么信息」、长周期依赖例外提前写前置节、frontier 到达补细+命中野心信号重判分档、前序子任务终局放弃视为已处置〔SR-8/SR-14〕）；陷阱节同步。
- [ ] **Step 5**：自检（tasks 1.1-1.4 验证条款逐条）：全文无 requirements.md 产出指令、无 `opsx:new plan-` 流程、无「预估轮数」；五项 checklist/兼容/逃生舱/生命周期/对照表/整体 plan 话术逐字在场；grep「四件套」零残留（本文件）。
- [ ] **Step 6**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "rebuild-sdflow-roadmap-v2:task1-skill-rewrite" "SKILL.md 主体重写：三件套直写+分档+footage+近细远雾(1.1-1.4)"`

### Task 2: 模板层〔tasks 2.1-2.3；R2/R4/R7〕

**Files:** Delete `sdflow-roadmap/references/requirements-template.md`；Modify `design-template.md`、`roadmap-template.md`、`task-log-template.md`、`memo-template.md`、`long-flow-skill-paradigm.md`。

- [ ] **Step 1**〔2.1〕：删 requirements-template.md（git rm）；design-template.md 头部增「需求与目标态」伸缩章骨架（无编号章名；工作流型必填：痛点/目标态判据/验收门槛槽/Non-Goals 每条附可证伪假设；需求清单/优先级可选占位；产品型追加受众/功能取舍+NFR 占位注释；混合/探索型兜底：判据允许具名占位不硬造〔SR-13〕）+ 导航块去 requirements；模板注释说明伸缩判据与兜底。
- [ ] **Step 2**〔2.2〕：roadmap-template.md 近细远雾分层注释 + 远期阶段骨架（目标句+「缺 X 信息」雾区备注示例；近期选择理由槽；长周期依赖例外注释）+ 导航块更新；远期阶段示例不含子任务/验收节。
- [ ] **Step 3**〔2.3〕：task-log-template.md（:20,:69 导航）、memo-template.md（:23,:27,:117 定位改「短档可选、footage 语境」+ 压缩前 flush 场景）、long-flow-skill-paradigm.md 表述复核（footage/memo 语境）。
- [ ] **Step 4**：自检：`ls sdflow-roadmap/references/` 无 requirements-template；grep references/ 无「四件套」残留；memo 模板明示长档由 footage 取代 + flush 场景在场。
- [ ] **Step 5**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "rebuild-sdflow-roadmap-v2:task2-templates" "模板层：删 requirements-template+design 头部章+近细远雾注释(2.1-2.3)"`

### Task 3: 消费仓约定〔tasks 3.1-3.2；R4〕

**Files:** Modify `openspec/matt/issue-tracker.md`（Wayfinding 小节）；Modify `CLAUDE.md`（Agent skills 托管块内 Issue tracker 行——直接 Edit，接受 setup-matt 重跑同批覆盖，此即双锚制①「就近可见」）。

- [ ] **Step 1**〔3.1〕：issue-tracker.md Wayfinding 小节：标题补「（Wayfinding operations）」；小节头加 `<root>` 条件分流（roadmap 类 effort → `openspec/roadmaps/{name}/footage/`，判别 = 调用语字面量声明 or 由 sdflow-roadmap 发起；其余默认 `openspec/matt/<effort>/`）；6 条 bullet 改 `<root>` 表达；加 map 持久字段约定（Tracker root/Effort kind，续跑从字段派生）、stale claim 重认领规则（中断票追加注记后可重认领）、map 再入约定（与 Task 1 Step 3 钉死的同一种，口径一致）；尾加边界声明三条（footage 不进 triage 扫描 / 三件套不引用 footage / 误落默认根的 wayfinder 票 MUST NOT 被 triage 贴五态改 Status〔SR-17〕）。沿现文件中文 bullet 风格。
- [ ] **Step 2**〔3.2①〕：CLAUDE.md「## Agent skills」块 Issue tracker 行后补锚句一句（roadmap 类 wayfinding 落 `openspec/roadmaps/{name}/footage/`，详见 tracker doc）——与 3.1 措辞一致；托管块其余不动（块外 :79 结构性锚归 Task 5）。
- [ ] **Step 3**：自检：分流判据与 SKILL.md 口径一致（grep 双向比对字面）；bullet 风格一致。
- [ ] **Step 4**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "rebuild-sdflow-roadmap-v2:task3-tracker-doc" "tracker doc 条件分流+持久字段+边界三条+CLAUDE 块内锚句(3.1/3.2)"`

### Task 4: wayfinding 最小实测〔tasks 4.1；R3/R4〕——**主 session 亲执行**（需真实 Skill 调用与跨会话模拟）

- [ ] **Step 1**：dev checkout `bash setup.sh`（让新 SKILL.md/模板经全局 symlink 生效——知情临时指 dev，adr/0005）；记 `git diff --stat openspec/CONTEXT.md openspec/adr/` 基线〔SR-4〕。
- [ ] **Step 2**：从**真实 `/sdflow-roadmap` 调用起步**（演练议题，让路由判档自然发生、非预供目的地路径〔SR-16/E8〕）：期望命中长档信号 → preflight（宿主探测+tracker doc 在场）→ 命名权定 slug（`_drill` 前缀避开——TAG 无关但按新约定 kebab）→ chart 建 map+2 票（1 条 Blocked by）→ 核对 map 持久字段落盘 + footage/ 落位正确（不落 openspec/matt/）。
- [ ] **Step 3**：claim → resolve 回写 Decisions-so-far → frontier 判定解锁；模拟中断：留一张 claimed 票，以「新会话」姿态仅凭 map 路径续跑——验证 stale claim 重认领 + 新建票从 map 字段派生路径。
- [ ] **Step 4**：收尾删演练目录 + 核对 CONTEXT.md/adr 增量与基线 diff，演练噪声 revert〔SR-4〕；结果（六操作+中断恢复逐项判定表）写入 `openspec/changes/rebuild-sdflow-roadmap-v2/impl-notes.md`；失败则按 proposal 假设 1 记录降级并回炉 Task 1 措辞。
- [ ] **Step 5**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "rebuild-sdflow-roadmap-v2:task4-wayfinding-drill" "wayfinding 六操作+中断恢复最小实测(4.1)"`

### Task 5: 全仓表述同步〔tasks 6.1；R1/R4〕

**Files:** Modify `CLAUDE.md`（:79 一带「dev/runtime checkout 纪律」之前的 sdflow-roadmap 描述段——**托管块外**）、`README.md`（sdflow-roadmap 行）、`docs/sdflow-fable5/01-goals-and-rationale.md`（:153 一带）、`docs/sdflow-fable5/02-module-reference.md`（:205 一带）。

- [ ] **Step 1**：CLAUDE.md 块外 sdflow-roadmap 段（原 :79「roadmap 文档包（长期真相源）」段）重写：四件套→三件套 + 去壳 + **必须含结构性第二锚句「roadmap 类 wayfinding 落 `roadmaps/{name}/footage/`」**〔Q4 双锚制②，setup-matt 重跑碰不到的存活比对源〕。
- [ ] **Step 2**：README sdflow-roadmap 行、docs/sdflow-fable5 两处 → 三件套/去壳/footage 表述。
- [ ] **Step 3**：全仓 `grep -rn "四件套\|4 件套" --include="*.md"` **逐命中判语境**：roadmap 语境改「三件套」；**「change 四件套」语境（proposal/design/specs/tasks 之谓，如 openspec/specs/spec-workflow/spec.md、workflow 规则、CLAUDE.md 托管块内）一律不触碰**；归档树/docs 历史快照不回改（明显误导处仅加注）；处置清单落 impl-notes.md（每命中一行：文件:行/语境判定/动作）。
- [ ] **Step 4**：自检：活文档 roadmap 语境零残留；:79 段含 footage 锚句；`git diff openspec/specs/spec-workflow/spec.md` 为空。
- [ ] **Step 5**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "rebuild-sdflow-roadmap-v2:task5-terminology" "全仓四件套→三件套逐语境同步+:79 第二锚(6.1)"`

### Task 6: 双宿主核验 + setup〔tasks 6.2；R1〕

- [ ] **Step 1**：dev checkout `bash setup.sh`（模板文件删除后清孤儿，adr/0005）；输出无异常、无孤儿误删；`readlink ~/.claude/skills/sdflow-roadmap` 与 `~/.codex/skills/sdflow-roadmap` 指向本仓。
- [ ] **Step 2**：核验两宿主 wayfinder 装载现状：`ls ~/.claude/skills/wayfinder`（应在）与 `ls ~/.codex/skills/wayfinder`（接地实测应不在→Codex 宿主降级路径常驻）——与 SKILL.md 宿主中立探测措辞比对一致（措辞如实，不夸大不隐瞒）〔SR-9/XE5〕；结果记 impl-notes.md。
- [ ] **Step 3**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "rebuild-sdflow-roadmap-v2:task6-host-verify" "dev setup 清孤儿+双宿主 wayfinder 装载核验(6.2)"`

### Task 7: 存量迁移前置判定与受控延后落档〔tasks 5.1-5.3；R1/R2〕——**主 session 亲执行**

- [ ] **Step 1**：前置状态机械核验并记录 impl-notes.md：①两包在飞实施 change 状态（`openspec list` + roadmap 阶段表：wco 剩 P2/P3+Phase C 占位、mlh 剩 P4 残项+P6）；②「首个新流程 roadmap 走通端到端」= 未发生（新流程本 change 才落地）→ **前置②不满足，5.1-5.3 本轮不执行**（Q-C 拍板的时序约束，非缺口）。
- [ ] **Step 2**：迁移排期落档：todolist 登记一条（module=sdflow-roadmap，显式 change 字段=rebuild-sdflow-roadmap-v2）——内容含触发条件（首个新流程 roadmap SHIPPED 且目标包无在飞 change）+ 操作序列指针（tasks.md 5.1-5.3 + design Migration step3 全文有效：全节清点表/考古注记四要素/编号不位移/清点表落盘随 commit/per 包 maintain_scan）。
- [ ] **Step 3**：Commit：`bash ~/.sdflow/hack/checkpoint-commit.sh "rebuild-sdflow-roadmap-v2:task7-migration-defer" "存量迁移前置核验+受控延后排期落档(5.1-5.3, Q-C)"`

---

## Self-Review 记录

- **Spec 覆盖**：R1→T1/T5/T7；R2→T2（+T7 指针）；R3→T1/T4；R4→T1/T2/T3/T4/T5；R5→T1；R6→T1/T4；R7→T1/T2。tasks.md 15 项全映射（5.1-5.3 为受控延后落档，Q-C 前置②）。
- **占位符扫描**：无 TBD；各任务验证条款来自 tasks.md 原文。
- **一致性**：footage 分流判据/再入约定/持久字段在 T1(Step3)/T3(Step1) 双向比对步锁定；双锚句措辞 T3(块内)/T5(块外) 同源。
