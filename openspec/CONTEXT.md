# Spec 工作流自动化 (Spec-Workflow Automation)

本项目的领域即 **spec 工作流本身**：一个 OpenSpec 变更从生成 → 设计审 → 实现 → 代码审 → 收尾 merge 的连续自动流水线，以及支撑它的评审机制、债务池、跨模型第二意见。此文件是该工作流的**统一术语表**（glossary），只定义语言，不放实现细节。

## Language

**假✅ (False Green)**:
verify / 评审报告把一条**根本没落实**的需求标成 ✅ 通过。是本工作流的头号失效模式——阶段三去人类门后，假✅ 会让不完整的活静默 merge，还被 hand-off 当"已完成"固化。
_Avoid_: 误判、错标（要专指"该红标绿"这一方向，不含"该绿标红"）

**假红 (False Red)**:
与假✅ 相反——确实做了、但因缺可机验痕迹被判成 gap。可当场补锚点纠正，后果远轻于假✅。

**证据锚点 (Evidence Anchor)**:
挂在一条 ✅ 判定上的**可机验凭据**：测试名 / commit hash / 文件行号。无锚点的 ✅ 一律降级为 gap。是堵假✅ 的机制核心。
_Avoid_: 证据、备注（要强调"可被机器/独立复核校验"）

**人类门 (HARD-GATE)**:
需要人类判断才能放行的阻塞点。本工作流刻意只保留在**阶段二设计门**（批设计）一处；阶段三过设计门后无任何阻塞人类门。
_Avoid_: 审批、确认（人类门特指"阻塞、非人不放行"，区别于异步非阻塞的 hand-off）

**verify 终门 (Verify Gate)**:
阶段三去人类门后，opsx-done 内的 verify 步成为**唯一**判定变更完整性的门。它不靠人盯，靠证据锚点硬约束 + 强模型冷启来自证可信。

**延后 / defer (Defer)**:
把"修不了 / 需拍板拿不准"的残差记进 buglist/todolist，本 change 不处理，交由 hand-off 引导另开清理 change。区别于"当场自动修"。

**镜 (Review Lens)**:
并行评审里一个**聚焦单一角度的独立 reviewer 子代理**。fan-out 时每个镜 fresh context、只审一个面向：领域镜（过某领域清单 R/CR 项）/ 对抗镜（从一个角度证明会爆）/ 接地镜（读真实代码核验 spec 主张，spec 侧专有）/ 历史镜（git blame + 旧 PR 意见，code 侧专有）。autoplan 的"四镜"（CEO/design/eng/DX）同源。英文原词 `review lens`（镜 = 镜头 = lens），价值在多镜盲区互补（瑞士奶酪的洞错开），比单 session 顺序审更独立。
_Avoid_: 镜子 / mirror（是"镜头 / lens"，聚焦单一角度，非映照）；reviewer（太泛——镜特指"一个角度"，非泛指审查者）

**Outside Voice（外部第二意见）**:
换**模型家族**（Claude ↔ GPT via codex）做的独立"找漏"评审——不是重跑清单，而是不受清单约束的整体第二意见。价值在跨家族盲区结构性错开。区别于同模型 fresh-context 子代理（只换上下文、盲区同处）。

**复用产出物 vs 依赖内部 (Reuse Output vs Depend on Internals)**:
自制 skill 与 gstack/superpowers 的合规边界线。**读它们产出的文件（output artifact，如 `gstack-review.md`）= 复用产出物，合法**；**调用它们的内部 bin / 探针 / config = 依赖内部，非法**（须自包含重写）。见 `adr/0002`。
_Avoid_: 笼统说"不依赖 gstack"（会误伤合法的产出物复用）

**自包含重写 (Self-contained Rewrite)**:
把某能力（如 codex outside-voice 的探针 / exec 包装 / prompt 模板）重写进自己仓的共享 helper，**只依赖外部 CLI 本身**（codex），不继承上游插件修复。是"依赖内部非法"的落地手段。

**反静默守卫 (Anti-silent Guard)**:
复用产出物、**或解析全局资源（全局 workflow bundle，见 `adr/0003`）**时，若读不到 / 解析不出 / 结果为 0 / **读到的是被本地旧副本遮蔽的陈旧版** → **显式降级 + 回落自带机制 + 告警**，绝不静默当"本次无此层"跑过。防"捞到 0 条 ≠ 本次真没有"这类假绿同构。

**反静默压制 (Anti-silent Suppression)**:
热主 session 做对抗裁决时，对 reviewer 子代理的 finding **只能降级 / 批注、不得静默丢弃**；判"不成立"的也须连理由落入报告"已裁掉"区，供人类/审计复核。防热合成层在 finding 到达人眼前暗箱吞掉。

> **元原则（贯穿 假✅ / 反静默守卫 / 反静默压制）**：**任何一层评审覆盖不得无声蒸发。** 一层结论要么到达人眼、要么留下可审计痕迹；"没找到 / 被裁掉 / 没落实 / 悄悄用了旧的”都必须显形，绝不静默通过。见 `adr/0001`、`adr/0002`。

**批次 (Batch)**:
一组归到同一个"清理 change"里一起清的债务 item 的容器；本质是"一个还没出生的 change"。有独立生命周期 `PLANNED → IN_PROGRESS → DONE`，登记在 `batches.md`。是独立于"源"与"status"的第三维度。
_Avoid_: 把批次塞进 item 的 status 列（三维度须分家）

**三维度分家 (源 / 批次 / status)**:
一条债务 item 的三个正交字段：**源 change**（哪个 change 发现的，provenance，不可变）/ **批次**（归入哪个清理 change，triage 结果，可变）/ **status**（生命周期，回归干净、不塞批次；**词表按 recorder 各异**——bug: `OPEN→…→FIXED/WONTFIX`，todo: `OPEN→PROPOSED→DONE/WONTDO`）。混用是旧 smell 的根因。

**终态集 (Terminal Set)**:
一个 recorder 里表示"这条债不再挂着"的状态码集合——**buglist: {FIXED, WONTFIX}，todolist: {DONE, WONTDO}**（含 WONT\*：决定不修/不做也是合法闭合）。批次"完成"判据 = 成员**全部进入各自终态集**，reindex 据此判批次 DONE。存在的原因：两 recorder 词表不同，不能硬编码字面 "DONE"（bug 根本没有 DONE）。
_Avoid_: 用单个 "DONE" 指代所有完成（bug 侧是 FIXED；WONT\* 也是终态、不是"没做完"）

**分诊 / sweep (Triage / Sweep)**:
把 OPEN 债务 item 归入某批次并转 PROPOSED 的动作。挂在 opsx-done 生成 hand-off 那步，每 change 完成后**只诊本 change 新增**的 OPEN 项（老项各自 change 时已诊过）。

**reindex（重建索引）**:
从 dated 文件 + batches.md 重建 `issues/INDEX.md` 的命令。INDEX 只生成禁手改，杜绝第三漂移源；reindex 顺带**拿 item 池当 ground truth 同步批次状态**（成员全部进入各自 recorder 终态集→批次 DONE、不一致标出）。

**设计层连续 vs 编排层连续 (Design-level vs Orchestration-level Continuity)**:
工作流"连续"分两层。**设计层连续** = 去掉逼人重来的断点（`/clear`、阶段三人类门），让阶段之间**没有非做不可的中断**；已由本工作流达成。**编排层连续** = 各步不再靠人**逐个 copy prompt 手动触发**，而由一个 orchestrator 顺序驱动；阶段三的这层由 `opsx-ship` 补上（见 `adr/0004`）。二者正交：设计层扫清了"该不该停"，编排层扫清了"谁来按下一步"。
_Avoid_: 笼统说"工作流已连续"（要分清是"无强制中断"还是"无手动逐步触发"——前者早已达成，后者是 opsx-ship 才补的）

**开发 checkout vs 运行 checkout (Dev vs Runtime Checkout)**:
laodao-skills 的两个物理副本，把"改规则的人"与"用规则的人"隔开。**开发 checkout**（独立目录的 clone）= 编辑 skill/bundle、跑 workflow dogfood 自己的地方；它留本地规则副本，解析时 local-first 命中、吃自己**尚未发布**的编辑。**运行 checkout**（`~/.skills/laodao-skills`）= 只 `git pull` 已完成的 skill 并 `setup` 安装、充当全局 canonical 解析锚点的地方；只含**已发布**内容，自己不 run workflow on 自己。发布边界 = push（开发）→ pull（运行），不靠 resolver 逻辑绕、靠 checkout 边界物理隔。
_Avoid_: 把两者当"同一目录的两种模式"（是两个物理 clone）；把 dev/release 隔离归给 resolver（隔离来自 checkout 边界；resolver 只是让开发 checkout 能 local-first dogfood）

**盘面即状态 (State-on-Disk)**:
编排/索引类机制的进度与结论 MUST 从**已存在的产物盘面**推导（产物文件、git 历史、机器锚行），MUST NOT 另设可变 state 文件当第二真相源——第二真相源与盘面必然漂移（INDEX 手改漂移、SDD ledger gitignored 失联皆其实例）。机判锚点须是**确定性产出**（模板写死的机器注释行、checkpoint 标签约定），不押模型自由生成的自然语言措辞（grill 实证：结论行正则对真实存档全 miss）。实例：`reindex` 拿 item 池当 ground truth、`ship_gate` 以 change 产物+锚行+checkpoint 标签判步序。
_Avoid_: 把"状态文件"当省事方案（它是漂移源）；把自然语言行当机判契约（措辞属概率空间）

**机队锚定 (Fleet-anchored Model Baseline)**:
workflow 的能力目标按**实际执行机队**（opus / sonnet / gpt-5.5 等多家族混编）的最弱可靠档设定，**不按开发 workflow 时恰好在用的更强模型**。两条派生：①规则文件里"强/弱模型"一律是**相对机队的档位词**（强档跑 verify / 对抗裁决 / final 终审；中档跑领域镜 / 生成；弱档只跑纯机械步），"档位→模型"映射在消费仓 `config.yaml`；②凡机械 prose 协议（路径解析、回落链、步末固定动作）MUST 脚本化 / 结构化——弱档模型跑 prose 协议的典型失效 = **静默跳步**，与反静默守卫正面冲突且无痕迹。见 `adr/0006`。
_Avoid_: 用"强模型"指某个具体产品名（档位相对机队，机队会换血）；把脚本化当可选优化（在本工作流是硬约束，是「机械活交脚本、模型只做判断」的升格）

**机器锚行 (Machine Anchor Line)**:
评审/报告产物里由 SKILL 模板**逐字规定**的 HTML 注释行（如 `<!-- outside-voice: mode=… -->`），承载状态留痕的机判形态——「盘面即状态」在报告层的实例：叙述随模型写、锚行不许改，Success Metrics 与度量回路只 grep 锚行。区别于**证据锚点**：锚行记「这一层本次跑成什么形态」，锚点证「这一条 ✅ 凭什么成立」。
_Avoid_: 拿自然语言结论行当机判契约（措辞属概率空间，ship grill 实证正则全 miss）

**HR-TG（高风险触发子集）**:
trigger-catalog 附录维护的 TG 具名子集（做错会运行期爆炸/数据损坏/安全泄漏且难回退）。评审规划镜头判「命中 ∩ HR-TG ≠ ∅」→ 单开领域 cross-model。是 catalog 第五消费层（评审 cross-model）的判据源，不是新风险分级体系。
_Avoid_: 再造 R1~R6 式风险代号（触发一律具体行为描述）

## Flagged ambiguities

- 「门」曾笼统指一切停顿——已分 **人类门（阻塞、需人判断）** vs **verify 终门（自动、机验）** vs **hand-off（异步、非阻塞的人类再入口）** 三种，勿混（见 `adr/0001-phase3-no-gate-verify-anchors.md`）。
- 「✅」在评审/verify 语境下曾被无条件信任——现约束为**必附证据锚点**方成立，否则是假✅。
- 「镜」单字曾可能被误读成「镜子/mirror」——已钉死为「镜头/**review lens**」（聚焦单一角度的独立 reviewer 子代理），非映照。
- 「连续」曾笼统指"自动化程度高"——已分 **设计层连续（无强制中断）** vs **编排层连续（无手动逐步触发）**，前者早达成、后者靠 `opsx-ship`（见 `adr/0004-opsx-ship-stage3-orchestrator.md`）。
- 「强模型」曾隐含"开发 workflow 时所用的最强模型"——已钉为**相对执行机队的档位词**（机队锚定，见 `adr/0006`）；`adr/0001` 的"verify 用强模型、禁弱模型"按此重释 = 机队最强档（opus / gpt-5.5 级），sonnet 属中档不合格。
