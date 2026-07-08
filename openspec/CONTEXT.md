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

**目标态论证 (Target-state Reasoning)**:
迁移期评估某设计（尤其解析/门禁语义）的安全性时，判据 MUST 锚在 **producer 契约下的目标稳态**，MUST NOT 用迁移中途的**现状快照/当前语料是否触发**当风险基线——迁移中「旧数据当然还没新形态」，拿它论「不可达」会把「目标态才暴露的面」误判为「不存在」，即以现状否定设计目标。落地手段：问「目标态 producer 会/不会产出该形态」（锚 SKILL 模板契约），而非「现存文件里有没有」。与「盘面即状态」正交——后者说真相源是盘面，本条说**迁移期的「盘面」要取目标态、非当前快照**。见 `adr/0011`。
_Avoid_: 用「现存 N 份里 0 触发」证不可达（迁移现状非稳态）；把「共用核心改返回语义」只在一个调用方/一个时态论证（须 producer 契约 + 目标态、每个调用方各验）

**HR-TG（高风险触发子集）**:
trigger-catalog 附录维护的 TG 具名子集（做错会运行期爆炸/数据损坏/安全泄漏且难回退）。评审规划镜头判「命中 ∩ HR-TG ≠ ∅」→ 单开领域 cross-model。是 catalog 第五消费层（评审 cross-model）的判据源，不是新风险分级体系。
_Avoid_: 再造 R1~R6 式风险代号（触发一律具体行为描述）

**Stacking（变更摞叠）**:
在**已有 feature 分支**上再 `openspec new change` 建第二个变更，使两个 change 的工件与 checkpoint 提交交错落在同一分支历史里。**FF-0 只拦 `main`/`master` 上建 change，不拦 feature 分支上 stacking**（实证 `ff0-branch-guard.py`）——故它可达但非常规。是 `ship_gate` 完成判据跨 change 污染（同号 task 互相计入 → 假✅）的唯一触发入口；gate 对此取**防御纵深**立场（change-命名空间标签隔离，见 ship-gate-hardening-2），**MUST NOT 用"每 change 独立分支是纪律"作缓解**——该纪律若成立则污染不可达、隔离本身失去意义（立论自否），gate 恰取"纪律可能破"立场才使隔离有价值。
_Avoid_: 把 stacking 当"被 FF-0 禁止"（FF-0 不拦它）；用"独立分支纪律"给 stacking 残留兜底（自否）

**度量回路 (Metrics Loop)**:
把每轮评审的**价值**结构化落锚、跨 change 只读聚合成表、据累积数据**人决**评审架构（保留 / 降采样 / 收紧触发 / 淘汰低价值镜）的反馈回路。**供数不供裁决**——给维度不给结论，砍哪镜是人读表后的决定。ROADMAP 暂名 `workflow-metrics-loop`；价值半由 lens-metric 锚承载，成本半（时长）另立、粒度更粗（见下）。
_Avoid_: 合成价值分 / 自动砍镜（回路只供数）；把聚合表当持久态（它是可重生 view，锚才是真相源）

**独立贡献 (Independent Contribution)**:
一个评审镜「**单独抓到且被采纳、无其他镜共抓**」的发现量——衡量它**不可替代**的非冗余价值。与采纳率（精度）并存答两个不同问题：采纳率高但独立=0 = 冗余镜（该砍），二者俱高 = 不可替代。是「淘汰哪镜」的真轴。对去重合并粒度敏感（「同一问题」无 ground truth），故作 **N 轮噪声 flag**、非单轮自动砍依据。
_Avoid_: 拿采纳率单独判「该不该留镜」（会误留 100% 采纳但全冗余的镜）

**价值度量 vs 成本度量粒度分界 (Value/Cost Metric Grain Split)**:
评审**价值**可测到**镜级**（per-lens，从报告锚导出）；**时长/成本**只能测到**层/阶段级**（per-phase，从 checkpoint 时间戳导出——harness 不暴露子代理耗时，见 `adr/0009`）。两者数据源与粒度不同，**不能相除成 per-lens value/cost 比**。
_Avoid_: 给单一镜算「性价比」（成本无镜级数据源，per-agent 计时不可行）

**计数归约 vs 分类判断 (Count Reduction vs Classification Judgment)** 〔grill-amendment · adr/0012〕:
lens-metric 度量原「数值一致性 = 主 session 信任边界（自做去重又写锚、非机械可验）」被 `lens_metric_emit` 一分为二：**计数归约**（把已分类的结构化 findings 折叠成 per-镜 `findings/采纳/裁掉/defer/独立` + `sev` rollup）是**确定性机械活**，下沉给脚本、不再是信任边界；**分类判断**（每条 finding 归哪镜/裁决/几级——去重、对抗裁决、严重度定级）是 judgment、保留给模型，成为**残余**信任边界。脚本只保证「计数是所给输入的正确归约」，MUST NOT 谎称「输入忠实反映合并池」。是「机械活交脚本、模型只做判断」在度量回路的精确切分——把一个笼统的「信任边界」拆成「机械可下沉的半」与「judgment 必留的半」。
_Avoid_: 说 emitter「消灭了信任边界」（只收窄——分类判断仍是残余边界）；把计数归约当 judgment 留给模型手数（那是被本 change 下沉掉的机械活）

**镜名册 (Lens Roster)** 〔grill-amendment · adr/0012〕:
一轮评审**跑了哪些镜**的显式清单，独立于每镜是否有 finding。emitter 需它才能为「跑了但零 finding」的镜落全零行——该信息**无法从 findings 集反推**（零贡献镜在 findings 里不现身）。是「反静默」在度量层的落点：跑了没抓到 ≠ 没跑，前者须落零行留痕（同 hr-tg 空箱、grill 跳过类判定的显形纪律）。
_Avoid_: 从 findings 推 roster（推不出零贡献镜）；零-finding 镜省略落行（把「跑了没抓到」静默吞）

**关联锚 (Roadmap Link Anchor)** 〔grill-amendment · adr/0013〕:
roadmap-驱动 change 起手在 proposal 写的机器注释行 `<!-- roadmap: {name} phase: {PN} subtask: {id,...} -->`，是 `sdflow-done` 回写步定位「回写哪个 roadmap 的哪些子任务」的**确定性单一源**。L1（关联哪个 roadmap）grep `name`、L2（哪些子任务）读 `subtask` 列表——**均读锚字段、不解析 proposal 自然语言引用**（引用形态自由、措辞属概率空间、正则半数 miss，同 gate frontmatter / lens-metric 弃自然语言）。无锚→按无关联静默跳过（producer 违约 fail-safe）。是「盘面即状态 / 机器锚行」在 roadmap 关联判定上的落点。
_Avoid_: 从 proposal 自然语言引用推关联（现状实证 2/6 全路径、余别名/缺失，非稳态）；把 L2 当模型判断（锚带 subtask id→机械读）

**roadmap 索引层 vs 叙述层 (Index Layer vs Narrative Layer)** 〔grill-amendment · adr/0013〕:
roadmap 文档的两层信息。**索引层**=机器要消费的状态（子任务复选框、阶段状态 enum、里程碑进度、task-log 机器锚）→ 生成侧**结构化**让 done 回写机械定位；**叙述层**=人读的（目标/设计理由/完成总结叙述/里程碑句）→ 留散文。优化 roadmap 生成格式 = 结构化索引层、叙述层保人读，同 recorder「总览表(索引)+详细块(叙述)」、gate「frontmatter(状态)+正文(叙述)」。结构化投入放**生成侧摊销**（生成一次、回写多次），非压在回写侧适配散文（半个现状快照）。
_Avoid_: 全 frontmatter 化 roadmap（损叙述层人读）；在回写侧硬适配现状散文（把结构化复杂度错放消费侧）

**记录维护回写 vs 正确性门 (Bookkeeping Writeback vs Correctness Gate)** 〔grill-amendment · adr/0013〕:
两类「写盘面」的失效容忍分野。**正确性门**（verify / gate / lens-metric emitter）：错=假✅ / 放不完整的活，零容忍 → **fail-closed** all-or-nothing 正当。**记录维护回写**（roadmap 回写）：漏=记录陈旧、可事后补、非正确性缺陷 → **best-effort + 降级标注**（三级：全写 / 部分写+标注未做项 / 完全做不了才留人工），fail-closed 只在末级。roadmap 回写误用 emitter 的 all-or-nothing 会为一个 id 定位不到就丢弃本可回写的部分，记录反更差。best-effort+标注 = 反静默守卫（降级+告警）在记录维护的应用，非放松纪律。
_Avoid_: 拿 fail-closed all-or-nothing 套记录维护回写（过度严格、丢可回写部分）；把 best-effort 当「允许静默漏」（未做项 MUST 降级标注显形）

**归属镜像投影 (Membership-mirror Projection)** 〔adr/0014；**superseded by adr/0015**——第二轮 spec-review C1（scaffold 撞 openspec「文件存在=done」短路产出链）/C2（阶段 enum deferred 无机器信号、不可机械聚合）揭穿机械镜像越界判断，回填改最小核助手、判断留人；本条留档备史〕:
roadmap 子任务完成态 = change tasks 完成态的**盘面投影**，真相源 = **归档实况盘面**（tasks 完成态，done 第 0.3 步已对账），非起手锚固化快照。对齐机制经第二轮 grill 精化为**「change 归属 roadmap 子任务 + roadmap 借结构化格式」**、**非「tasks 号 = roadmap 号」的强编号统一**——实证粒度失配：roadmap 复选框 `4.C.1` = 一次 change 粒度、change tasks `1.1~7.x` = 该 change 内部实现分解、天生细一层。落地：**roadmap 保规划粒度**（子任务 = change 级交付点），**仅借鉴** tasks 复选框 `- [ ]` + 层级编码 `N.X.Y` **格式**（机械可镜像）、**MUST NOT 下沉到 tasks 实现步粒度**；change scaffold 机械写**归属锚** `<!-- roadmap: {name} subtasks: 4.D.1,… -->`（关联范围）+ change tasks 顶层组借 roadmap 子任务号作归属标签；`sdflow-done` 归档**镜像** change tasks 归属组完成态 → roadmap 同号复选框（合批 defer 组未完成→留 `[ ]`）。实际勾选 = **归属范围（锚）∩ tasks 盘面完成**。
_Avoid_: 起手锚写死 subtask 集当**完成**真相（锚只声明关联范围、完成看盘面；起手≠归档实况，混用致 defer 误勾）；把「编号统一」当「tasks 号=roadmap 号」强统一（粒度失配——会拖 roadmap 到实现步或压平 change 功能分组）；让 roadmap 借 tasks 的**粒度**（只借复选框/编码**格式**，roadmap 保规划粒度）

**producer 机械生成链 (Producer Mechanical Generation Chain)** 〔adr/0014；**superseded by adr/0015**——scaffold 双向生成撞 C1（openspec done 判定），回填改最小核助手；本条留档备史〕:
把「靠人写对」升级为「producer 机械产出」的确定性链条——roadmap 结构化生成 → change **scaffold**（从 roadmap 抄编号 + 机械写 name 锚 + proposal 引用）→ 实现勾 tasks → 镜像回写。每环确定性、不靠自觉。是「机械 prose 协议 MUST 脚本化」（`adr/0006`）+「目标态论证」（`adr/0011`）的合流落地：评估目标态安全性时锚「producer 契约会不会机械产出」，**MUST NOT** 降格为「人/AI 起手会不会记得遵守一条无门禁 prose MUST」（后者是 `adr/0006` 点名的静默跳步，被 spec-review 哲学镜揭穿为「目标态论证误套行为合规」）。
_Avoid_: 把「起手 MUST 带锚/编号」当目标态达成（无机械生成 = 靠自觉 = 静默跳步）；用「现状 producer（opsx:ff）不可改」限制目标（目标态应加确定性生成环，非迁就现状流程）

**完成判定的盘面-判断切分 (Completion: On-disk Fact vs Judgment)** 〔spec-review-amendment · adr/0015〕:
roadmap 子任务「完成」判定分两层——**确定性盘面**（对应 change 是否归档/merge/verify=PASS，机械可读，`ship_gate` 已用同款盘面）+ **是否满足验收标准 / 算不算完成 / 勾哪些复选框**（语义判断，现状人做、目标态仍人做）。现状实证：「某子任务算不算完成」从来不是机械读复选框，是人对照人写的 `### 验收标准` 判的；deferred（排后/放弃）更是纯规划判断，二值复选框 `[ ]` 根本不承载（`[ ]` 无法区分「未做」vs「显式放弃」）。把判断的一半硬做成机械聚合（如从复选框推 deferred enum）是**范畴错误**（`adr/0015` C2）。
_Avoid_: 从二值复选框机械推「阶段是否 delivered / 某项是否 deferred」（那是判断，撞 C2 循环+无信号）；把「完成判定」整体当确定性盘面（只有「change 是否交付」是盘面，「算不算满足验收标准」是判断）

**回填降摩擦助手 (Writeback Assist, not Auto-writeback)** 〔spec-review-amendment · adr/0015〕:
`sdflow-done` 收尾读**确定性盘面**（change 归档/verify=PASS/merge/tasks 完成态/验证数字）生成人可确认的 roadmap **回填草稿**（候选复选框 + task-log 完成总结骨架含机械锚），进 hand-off 提示人异步确认回填（同现状独立「回填对账」commit，从纯手写降为改草稿）。**判断留人**（算不算完成/勾哪些/价值叙述/阶段状态/deferred），非无人干预自动回写——因完成判定本质含判断（见上条）。是「机械活交脚本、判断留模型」在 roadmap 回填的落点：自动化**机械搬运**（盘面读取 + 骨架预填）、判断留人**确认**。**弃** scaffold 双向（撞 C1）/ enum 机械聚合（撞 C2）/ 编号统一归属镜像（粒度失配）/ 强制迁移——roadmap/tasks 保现状散文格式，助手适配、不要求机读化。
_Avoid_: 把它做成无人干预机械镜像 tasks→roadmap（越界判断，撞 C1/C2）；用 scaffold 预建 roadmap 复选框（撞 openspec done 判定 + 孤儿认领）；阶段三给它加人类门（阶段三无 AskUserQuestion——草稿进 hand-off 让人异步确认，非弹窗）

## Flagged ambiguities

- 「门」曾笼统指一切停顿——已分 **人类门（阻塞、需人判断）** vs **verify 终门（自动、机验）** vs **hand-off（异步、非阻塞的人类再入口）** 三种，勿混（见 `adr/0001-phase3-no-gate-verify-anchors.md`）。
- 「✅」在评审/verify 语境下曾被无条件信任——现约束为**必附证据锚点**方成立，否则是假✅。
- 「镜」单字曾可能被误读成「镜子/mirror」——已钉死为「镜头/**review lens**」（聚焦单一角度的独立 reviewer 子代理），非映照。
- 「连续」曾笼统指"自动化程度高"——已分 **设计层连续（无强制中断）** vs **编排层连续（无手动逐步触发）**，前者早达成、后者靠 `opsx-ship`（见 `adr/0004-opsx-ship-stage3-orchestrator.md`）。
- 「强模型」曾隐含"开发 workflow 时所用的最强模型"——已钉为**相对执行机队的档位词**（机队锚定，见 `adr/0006`）；`adr/0001` 的"verify 用强模型、禁弱模型"按此重释 = 机队最强档（opus / gpt-5.5 级），sonnet 属中档不合格。
- 「lens-metric 折叠表」曾只活在契约 prose（无代码单一源），grill 揭穿 aggregator 只 group 不 fold——已机读化为契约 `lens-metric-fold` 块作折叠单一源（见 `adr/0012`）；「数值一致性=信任边界」已拆为**计数归约（机械下沉）vs 分类判断（残余边界）**两半，勿再当一个笼统边界。
- 「已并 / merged」曾被 `ship_gate.branch_state()` 隐式当作"**当前 HEAD 分支**有没有并进 base"（全局分支态）——已钉为 **change 域可达性**：一个 change 是否 merged，判据是「它的归档目录在不在 base(main/master) 的树里」（`git ls-tree <base>`），**与当前 HEAD 在哪条分支无关**（ship-gate-hardening D3 grill）。是「盘面即状态」在终态判定上的落地：判据必须锚在「这个 change 的产物落没落 base」这一确定性盘面，不用"当前分支"这个和 change 无关的全局近似。全局近似只在 change 自身分支上恰好成立，跨无关分支查已并 change 会误判"待收尾"。
- 「roadmap 回写失败」曾拟套 lens-metric emitter 的 all-or-nothing fail-closed——已钉为**记录维护回写**（best-effort + 降级标注三级），区别于正确性门的零容忍 fail-closed（见 `adr/0013`）；「L1 关联判据」曾拟解析 proposal 自然语言引用（现状快照谬误）——已锚 producer **关联锚**机器行（见「关联锚」/`adr/0013`）。
- 「roadmap 回写真相源」曾拟锚**起手锚固化的 subtask 集**（`adr/0013`）——spec-review 揭穿其为可变状态写死的第二真相源（起手≠归档实况致误勾）+ 无机械闭环（靠人写对锚 = `adr/0006` 静默跳步），已重构为**归属镜像投影**（真相源=归档 tasks.md 完成态）+ **producer 机械生成链**（scaffold 机械产出编号/锚），`adr/0014` 部分 supersede `adr/0013`。
- 「roadmap↔tasks 对齐」第二轮 grill 精化：曾拟「tasks 号 = roadmap 号」强编号统一——实证粒度失配（roadmap 复选框=change 粒度、tasks=实现分解、细一层），已改为**归属镜像**（roadmap 保规划粒度、仅借复选框/编码**格式**；change 归属 roadmap 子任务；勾选=归属范围∩tasks 盘面完成），roadmap 与 tasks **MUST NOT 互相拖到对方粒度**（见「归属镜像投影」/`adr/0014`）。
- 「roadmap 回填自动化」三轮收敛终局〔`adr/0015`〕：机械回写骨架（起手锚 `adr/0013` → 编号统一 → 归属镜像+scaffold `adr/0014`）经两轮 spec-review **全被揭穿**（C1 scaffold 撞 openspec「文件存在=done」短路产出链、C2 阶段 enum deferred 无机器信号不可机械、defer 重现原痛点、ROI 失衡）；现状实证「**完成判定含判断**」（人对照验收标准判、非机械读复选框）——已收敛为**回填降摩擦助手**（盘面搬运机械、判断留人确认），`adr/0015` supersede `adr/0013`+`adr/0014`。
