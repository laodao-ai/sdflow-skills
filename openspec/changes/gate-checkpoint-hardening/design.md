## Context

阶段三 gate 与 checkpoint 标签契约的 6 个硬化残项（T26/T35/T36/T37/T38/T43），源自 4 个已 ship 的 change 的评审 defer 池。本 change 按 fold-vs-defer（BASE-18）把它们合一处理。

现状接地：

- **gate 无状态**：`ship_gate.py` 零副作用、盘面即状态（committed 产物为账本，不落 state 文件）〔adr/0006〕。
- **新鲜度 committed-only**：`ship_gate.py:64-65` 已注明「新鲜度只看已提交盘面，不看工作树 dirty（T33 停置），是否纳入待议」——即 T35。
- **熔断靠 prose 计数**：`sdflow-ship/SKILL.md` 链序末「同一 invocation 内同一步重跑一次仍无锚行 → UNKNOWN」由编排器短时记数，非 gate 判定——即 T26。
- **派发文案两处复述**：`checkpoint-commit.sh <change>:task<N>-<slug>` 派发指令在 `workflow.md` + `sdflow-ship/SKILL.md` 各写一份——即 T36。
- **标签形状 doc 副本**：主 spec `spec-workflow` 的 Scenario 也 prose 复述标签形状（T37）、用词 `<当前change>` 有歧义（T38）；`checkpoint-commit.sh` 头注释是事实真相源。
- **模板样例带装饰**：producer 展示的机器锚样例带反引号/同行尾注，而主 spec 行 306 已 MUST「各模板把锚写在独占一行」——即 T43。

## Goals / Non-Goals

**Goals**：① 定夺 T35（dirty 新鲜度）、T26（熔断计数）两个未决设计点并登记理由；② 把 checkpoint 标签契约收敛到**单一真相源**（T36/T37/T38），消除 doc 副本漂移；③ producer 模板样例对齐既有「独占 bare line」spec（T43）；④ merge 后清 3 整批。

**Non-Goals**：不改 gate 的盘面即状态 / 零副作用 / ship 零跨步状态三条地基红线；不动 gate-anchor-line-scoped 的 T41/T42（人读体验，归 REC-2）；不重构 checkpoint-commit.sh 的标签生成逻辑（B4 已修，本 change 只收敛"复述"）。

## Decisions

> 每个 ADR 按三镜（系统/用户/开发循环）+ 主次判定评估（BASE-12，命中 TG-23 书面必填）。T35/T26 为真设计点，标 **[需设计门拍板]**；T36/T37/T38/T43 为一致性修复，走 TG-25 scope-check。

### ADR-1 [需设计门拍板]：T35 工作树 dirty 是否纳入新鲜度

- **背景**：T33 曾 WONTDO（committed-only 与"盘面即状态"一致）；T35 复议。
- **候选**：
  - **A 不纳入**（维持 committed-only）
  - **B 纳入 gate 判定**（gate 检工作树 dirty 作失鲜信号）
  - **C 不进 gate，改由 `sdflow-ship` 收尾软提示**（"工作树有未提交非-openspec 改动，gate 判定不含它们"）
- **三镜**：
  - 系统镜：A 维持单一真相源、零耦合；**B 与"盘面即状态"地基张力**，且开发中途工作树常 dirty → 高假阳；C 把提示放编排器、不污染 gate 判定。
  - 用户镜：B/C 能提醒未提交改动（低频价值）；A 靠用户自觉 commit。
  - 开发循环镜：A 零改动零维护；B 加检测+测试+误报调参（重）；C 一句软提示（轻）。
- **决策（grill 定稿）**〔grill-amendment〕：**C（gate 守 committed-only）+ 在 merge 边界给硬检查**——两层：
  - **gate 侧**：新鲜度 committed-only 正式化，T33/T35 gate 判定关 WONTDO（B 的工作树信号与"盘面即状态"张力且高假阳，不进门禁）。
  - **提示分强弱**：阶段流转全程 = `sdflow-ship` **软提示**（信息性，工作树有未提交非-openspec 改动时告知"gate 判定不含它们"）；**merge 边界** = `sdflow-done` merge 步**硬前置检查**——工作树有未提交非-openspec 改动则**停下问、不静默 merge**（防"忘 commit → 在缺了该随档提交之工作的盘面上 verify PASS 并 merge → 静默 ship 不完整活"）。
  - **grill 揭示**：T35 的真诉求不在"报告新鲜度"（committed-only 对报告是对的），而在 **verify→merge 边界漏 ship 未提交工作**；软提示会被忽略 = 假安全感，故 merge 边界必须有牙齿。硬检查是 merge 卫生前提、**不碰 gate 的盘面即状态**（落 sdflow-done 非 gate）。
- **fold 决策**〔grill-amendment〕：merge 硬检查动 `sdflow-done`（本 change 原 scope 外）。**采 fold 而非 defer**——判据「同一问题（未提交工作漏 ship）不分多次实现」：软提示 + 硬检查是**同一诉求的两半**，拆开则同一问题跑两轮 workflow 循环、两次接地。**主次：开发循环镜主导**（循环固定成本 >> 多碰一个 skill 的耦合增量）；防吸积仍成立（同"未提交工作正确性"诉求、blast-radius 小、无需 sdflow-done 自身设计审）。
- **三镜**：系统镜——gate 纯洁保住，多碰 sdflow-done 一处 merge 前置（低耦合）；用户镜——merge 前挡一道，真正防漏 ship；开发循环镜——一次做完同一问题。**主次：ADR 决策取系统镜（gate 纯洁）为门槛、fold 取开发循环镜为准**。
- **当前方案代价**：merge 硬检查可能对"故意留着的无关未提交改动"误挡 → 需一句 opt-out / 或限定"非-openspec 改动"范围（实现期定精确判据）；阶段软提示仍可被忽略，但 merge 边界已兜底。

### ADR-2 [需设计门拍板]：T26 熔断重试计数是否脚本化下沉

- **背景**：熔断需"单 invocation 内同步重跑一次仍无锚行 → UNKNOWN"，现靠编排器 prose 记数。
- **候选**：
  - **A 维持 prose 计数**（登记为接受取舍）
  - **B 下沉到 gate 确定性判据**
  - **C 下沉到 ship 侧无状态 helper**
- **三镜**：
  - 系统镜：**"重跑无新产物"本质无盘面差异**——gate 零副作用地无法区分首跑 vs 重跑（B 技术上撞"盘面即状态"）；跨 turn 计数须持久化，撞"ship 零跨步状态"D9（C 撞红线）；A 的 prose 计数是单 invocation 短时、SKILL 熔断条款已声明与红线不冲突。
  - 用户镜：无感（内部防护）。
  - 开发循环镜：A 零维护；B/C 高复杂度且撞红线。
- **决策（grill 定稿）**〔grill-amendment〕：**持久化 = 不做（A 的一半），但熔断触发判据从"模糊计数"硬化为"具体盘面对照"**。
  - **持久化不可做**（irreducible）：失败重跑零 git 痕迹、零盘面差异；任何计数要么落 state 文件（撞盘面即状态）要么跨 invocation（撞 D9）。这条站得住。
  - **触发判据硬化**：熔断从"数我重试了几次"改为——编排器重跑一步**前**，检查 `HEAD` 与该步报告是否**自本 turn 上次跑后未推进**（HEAD 未移动 + 报告 mtime/sha 未变）；未推进即判无进展 → 停上抛人工。仍保留一个不可消除的 within-invocation "before 快照" bit，但**从"让 LLM 数数"降级成"让 LLM 做一次具体 git 对照"**。
  - **grill 揭示的张力**：`adr/0006(b)` 禁 prose 记忆步序（LLM 漂移），而熔断计数同属 prose 记忆——原 A 的"短时例外"说辞有走私嫌疑。硬化后：把最弱一环（LLM 计数，含 context 压缩即丢的失败面）换成较硬一环（LLM 做具体 HEAD/报告对照），漂移面显著缩小。1 bit before-快照不可消除是架构下限、非偷懒。
- **三镜**：系统镜——不破三红线（仍不持久化），判据具体化；用户镜无感；开发循环镜——后人照抄"HEAD 未推进检查"比照抄"数数"不易错。**主次：系统镜主导**。
- **T26 归口**：从"探索"关为**已探索 → 产出「触发判据硬化」具体改进 + 持久化 defer（撞三红线，登记接受取舍）**，非纯 WONTDO。
- **当前方案代价**：仍依赖编排器执行该对照（信任面不变），但触发从不可复核的计数变为可复核的 git 对照，风险面缩小。

### ADR-3：T36 checkpoint 派发文案单一真相源

- **候选**：A workflow.md 为源 / B SKILL 为源 / **C checkpoint-commit.sh 契约（头注释+`--help`）为唯一源，两处引用式**。
- **三镜**：系统镜——脚本头注释已是标签契约事实真相源（脚本自证 + B4 修复处），让 workflow.md/SKILL 指向它 = 真单源；A/B 仍留一处完整复述、仍会漂。用户镜无感。开发循环镜：C 后改契约只改一处。
- **决策（grill 定稿，Q4 接地修正）**〔grill-amendment〕：**格式/规则分治，各自单源；格式源 = TAG_RE（非 checkpoint-commit.sh）**——区分两样被重复的东西：
  - **格式串** `<change>:task<N>-<slug>` → 权威 = `ship_gate.py` TAG_RE（`checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`，enforcing parser，加 canonical-shape 头注释）+ `test_producer_parser_contract.py` 钉 producer↔parser 一致；**`checkpoint-commit.sh` format-agnostic（只裹 `checkpoint($step)`），不得引作格式源**；
  - **工作流规则**「plan 每任务 commit 步 MUST 用命名空间标签」→ 就地留 `workflow.md` **一处**（规则 bundle 的规则源，含格式串一次并标"形状由 TAG_RE 执行 / 契约测试钉死"）；
  - `sdflow-ship/SKILL.md` → **引用** workflow.md 该规则，不再复述整句，只留 ship 特有派发注记。
  - 净效果：格式一处（TAG_RE，测试钉）、规则一处（workflow.md）、SKILL 引用——各自单一、规则就地可读。
- **grill 揭示（两层）**：① 原 C"全引用式"把"每任务必须用"这条**工作流规则**推去脚本，是错配；② Q4 接地证 `checkpoint-commit.sh` format-agnostic（行29 `step="$1"`/行46），根本不认识 `task<N>-<slug>`——原以为它是"格式 producer 源"是**错的**，真正的格式契约在 TAG_RE（解析器/执行者）。
- **三镜**：系统镜——真单源、无 doc 副本漂移；开发循环镜——plan-writer 在 workflow.md 就地看到规则+格式。**主次：系统镜（防漂移）主导，但被开发循环镜"就地可读"约束修正——不为单源教条牺牲可读性**。

### ADR-4：T37/T38/T43 标签契约一致性（TG-25 → BASE-29 scope-check）

命中 TG-25（版本化多文件契约套件）。**Q4 接地修正：区分两个锚族**（原表混为一谈且 T43 落点找错）——

**锚族 A：checkpoint 标签**（commit subject `checkpoint(<change>:task<N>-<slug>)`，T36/T37/T38）

| 文档 | 载何契约 | 本 change 改 | 不改则理由 |
|---|---|---|---|
| `ship_gate.py` TAG_RE | 格式**权威/执行者** | ✅ 加 canonical-shape 头注释（ADR-3 格式源） | — |
| `test_producer_parser_contract.py` | producer↔parser 一致守卫 | ⬜ 不改 | 已钉一致，本 change 不改格式本身 |
| `workflow.md` | producer 指令 | ✅ 就地留规则一处、标"形状由 TAG_RE 执行"（T36） | — |
| `sdflow-ship/SKILL.md` | 派发指令复述 + 台账锚 | ✅ 改引用 workflow.md（T36） | — |
| `spec-workflow/spec.md` | Scenario 复述标签形状 + `<当前change>` 用词 | ✅ T37 标"样例非权威" + T38 `<当前change>`→`<change-slug>` | — |
| `sdflow-init/assets/hack/checkpoint-commit.sh` | **format-agnostic 透传** | ⬜ 不改（可选：`--help` 补一句"格式见 TAG_RE 契约"） | **非格式载体**——只裹 `checkpoint($step)`、不认识 task 格式，不得引作源 |
| `sdflow-code-review/SKILL.md` 台账锚 | 消费格式 | ⬜ 不改 | 台账锚是消费格式非标签源，无漂移面 |

**锚族 B：ship-gate 机器锚**（`<!-- ship-gate: X -->`，report 锚，**T43 真身**）

| 文档 | 载何 | 本 change 改 | 不改则理由 |
|---|---|---|---|
| `sdflow-spec-review/SKILL.md:102` | design-approved 锚模板（**带反引号**） | ✅ T43 去反引号、改独占裸行 | — |
| `sdflow-code-review/SKILL.md:149-150` | code-review 锚模板（**带同行尾注**） | ✅ T43 尾注移出锚行（照抄尾注会让 gate `strip()≠字面` 漏判，真 bug） | — |
| `sdflow-done/SKILL.md:80-81` | verify 锚模板 | ⬜ 核验即可 | 已裸行；核验其确为独占行 |
| `ship_gate.py` | 匹配的锚字面（权威） | ⬜ 不改 | 匹配逻辑 B4 已修（行级+fence-aware） |
| `spec-workflow/spec.md` 行306 | 「各模板 MUST 独占行」MUST | ⬜ 不改 | 既有需求；T43 是让实现对齐它 |

- **主次**：系统镜（防漂移、一致性修复）主导；T37/T38/T43 均低增量、同"锚契约一致性"主题 → fold 一处理。
- **grill 揭示**：原表把 T43 写成"脚本/测试内 producer 模板"、把 spec-review 标"不改"——全错。T43 真身是 `<!-- ship-gate: -->` 锚在 SKILL 模板的展示卫生（spec-review:102 反引号 / code-review:149-150 尾注），照抄它们的报告会让 gate 行级匹配 miss。

### ADR-5：为何 6 项合一个 change（fold-vs-defer 自证）

同 capability（gate+checkpoint+锚 契约面）∧ 高耦合（同 `ship_gate.py` / 同契约面）∧ 低增量 → AND 门三条齐，fold 成立。主次：开发循环镜主导——3 批各走一轮 workflow 循环固定成本 >> 合并后的增量审查成本。

**grill 后复核（scope 涨到 ≈8-9 文件 / 5 skill）**〔grill-amendment〕：**仍保持一个 change**。「低增量」判据 = 每项工作量 + 是否需独立设计审，**非裸文件数**——本 change **无任何一项需自己的设计审**（皆注释/措辞/模板卫生/一个 merge 前置检查），逐项低成本；① gate/merge 行为（T26/T35）与 ② 契约一致性（T36/T37/T38/T43）共享同一 gate/checkpoint/锚**契约面**（T43 锚卫生与 T36 标签单源本质同一件"契约载体别漂"），拆开 = 同一契约面跑两轮循环、两次接地。**防吸积边界**〔grill 定〕：merge 硬检查（Q2）是最后一次扩容，**就此打住不再 fold 第三批**，后续相关项一律 defer。

## Risks / Trade-offs

- **[T35 软提示遗漏]** → 软提示非门禁，用户可能忽略；接受（gate 判定纯洁性优先，见 ADR-1 代价）。
- **[T26 负结果被误读为"没做"]** → hand-off/spec 明写"已探索·结论=不下沉·理由"，附三红线，避免后人重开。
- **[引用式文案降低就地可读性]** → 派发格式从"就地可抄"变"跳去看契约"；以 checkpoint-commit.sh `--help` 稳定接口缓解。
- **[spec delta 与主 spec 遗留中文格式冲突]** → 归档时按 sdflow-done 的 `--skip-specs` fallback 处理（既有流程）。

## Migration Plan

1. 改 `assets/workflow/workflow.md`、`assets/hack/checkpoint-commit.sh` 后，开发 checkout 跑 `bash setup.sh` 使全局 canonical 生效（否则测不到）。
2. 改 `ship_gate.py`（T35 关 WONTDO 注释 / 无逻辑变更）+ 跑 `sdflow-ship/tests/` 确认零回归。
3. merge 后运行 checkout 跑 `/sdflow-upgrade` 还原 canonical。
4. **回滚**：本 change 无破坏性逻辑变更（T35/T26 均为"维持现状 + 登记"），回滚 = `git revert` 文案/spec 提交。

## Open Questions

- ADR-1（T35）与 ADR-2（T26）的推荐（C / A）待**设计门拍板**确认；grill 会逐分支压测。
- T43 的 producer 模板样例具体在 `checkpoint-commit.sh` 内注释还是测试 fixture——实现期接地定位（接地镜/spec-review 核）。
