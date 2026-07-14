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

**完成判定的盘面-判断切分 (Completion: On-disk Fact vs Judgment)** 〔spec-review-amendment · adr/0015 + 第三轮精化〕:
roadmap 子任务「完成」判定分两层——**确定性盘面**（对应 change 是否归档/merge/verify=PASS，机械可读，`ship_gate` 已用同款盘面）+ **是否满足验收标准 / 算不算完成 / 勾哪些复选框**（语义判断，现状人做、目标态仍人做）。现状实证：「某子任务算不算完成」从来不是机械读复选框，是人对照人写的 `### 验收标准` 判的；deferred（排后/放弃）更是纯规划判断，二值复选框 `[ ]` 根本不承载（`[ ]` 无法区分「未做」vs「显式放弃」）。把判断的一半硬做成机械聚合（如从复选框推 deferred enum）是**范畴错误**（`adr/0015` C2）。**第三轮精化：切分线精确落在「有无确定性信号」上**——「定位到 phase」有确定性信号（change 名前缀 `implement-{roadmap}-pN` 编码 roadmap+phase）故**机械**；「这个 change 勾该 phase 里**哪几行** / 算不算完成」无机械判据故**判断留人**。前两轮把整个「回写」当机械是过度机械化，把整个「定位」当判断则矫枉过正——定位到 phase（机械）、勾哪几行（判断）才是精确切分。
_Avoid_: 从二值复选框机械推「阶段是否 delivered / 某项是否 deferred」（那是判断，撞 C2 循环+无信号）；把「完成判定」整体当确定性盘面（只有「change 是否交付」是盘面，「算不算满足验收标准」是判断）；把「定位到具体行/勾哪几行」划机械侧（无确定性信号，是判断——助手只定位到 phase 候选行集）

**回填降摩擦助手 (Writeback Assist, not Auto-writeback)** 〔spec-review-amendment · adr/0015〕:
`sdflow-done` 收尾（hand-off 步）读**步2 已实现盘面**（verify=PASS/tasks 完成态/change 名/分支；archive/merge 是步3/步5 才有的未来锚 → 留占位不预填）生成人可确认的 roadmap **回填草稿**（该 phase 候选复选框行集 + task-log 完成总结骨架含机械锚），进 hand-off 提示人异步确认回填（同现状独立「回填对账」commit，从纯手写降为改草稿），并在 done 第六步摘要抬一行使 merge 时点可见（异步闭环残差已显式登记）。**判断留人**（勾哪几行/算不算完成/价值叙述/阶段状态/deferred），非无人干预自动回写——因完成判定本质含判断（见上条）。是「机械活交脚本、判断留模型」在 roadmap 回填的落点：自动化**机械搬运**（前缀解析定位到 phase + 盘面读取 + 骨架预填）、判断留人**确认**。关联 = change 名前缀 `implement-{roadmap}-pN` 主 + marker `#{phase}` 兜底（检测 fence-aware+行锚定+排除自身讨论区，防自指假阳）；roadmap 格式**实测分裂**（复选框式/表格式）→ 助手探测形态、非复选框式 fail-loud 留人工。**弃** scaffold 双向（撞 C1）/ enum 机械聚合（撞 C2）/ 编号统一归属镜像（粒度失配）/ 强制迁移。
_Avoid_: 把它做成无人干预机械镜像 tasks→roadmap（越界判断，撞 C1/C2）；用 scaffold 预建 roadmap 复选框（撞 openspec done 判定 + 孤儿认领）；阶段三给它加人类门（阶段三无 AskUserQuestion——草稿进 hand-off 让人异步确认，非弹窗）；把 archive 路径/merge 当步2 盘面预填（是预测值，跨零点漂/merge opt-out 记假事实）；朴素子串检测 marker（撞 change 自身含串的自指假阳）

**报告工具反静默方向 (Report-tool Anti-silent Direction)** 〔grill-amendment · adr/0016〕:
只读报告/对账工具（如 `maintain_scan` 的 set-diff）的 fail-closed 判据 MUST 锚在**「防假一致」方向**，非机械纠结「空 vs 畸形」。两方向失效危险度不对称：**解析读到 0 条 → 报全部差异**是**响亮自纠**（人一眼见幻影去查），**误读少读 → 漏报 → 报『一致』**才是**假绿同构**（该红报绿）。故：结构骨架可信但读 0 条 = **合法响亮态**（退出 0、不 fail）；结构骨架缺失 / 机器 marker 不配对 / 行畸形到解析器无法确信 = **fail-closed**（拒绝带半信半疑的解析输出「一致」）。区别于「门」的 all-or-nothing——报告工具不为「有差异」fail（有差异是正常产出），只为「无法自证解析可信」fail。是「反静默守卫」在只读报告层的方向化，呼应 `adr/0013` 记录维护 vs 正确性门。

**机械校验器输出诚实 (Validator Output Honesty)** 〔grill-amendment · adr/0018〕:
输出信号被下游决策消费的机械校验器，当裁决被**不可机械验证的输入**界定时，MUST 把该界定编码进信号本身，MUST NOT emit 与「已完整验证」不可区分的裸通过码——三形态：**暴露输入依据**（`hr_tg_intersect` 出 `none｜依据已声明:[...]` 使欠声明可审）、**在码里点名未核边界**（`review_disposition_check` 出 `section-ok-DISPOSITION-UNCHECKED` 而非裸 `present`）、**朝「漏判有害」方向 fail-safe**（`outside_voice_guard` 工作树 dirty→`stale-dirty-tree` 重跑，重跑只是成本、复用陈旧才是危害）。是「报告工具反静默方向」（adr/0016）从只读报告推广到**消费型信号校验器的输出诚实**、「假✅」防线在校验器自身输出的落点。区别于 fail-closed（坏输入→EXIT_FAIL）：**可读但不可验**的输入走信号内诚实，非崩溃非静默通过。
_Avoid_: 用裸二态码把不可验界定藏进消费方会过度信任的干净信号（假绿/假阴/假新鲜温床）；让脚本用子串/正则兜底完整性判断（制造新假阳假阴）——完整性强制（声明 vs 实际、逐条处置）属模型/spec-review，非机械校验器职责。
_Avoid_: 把报告工具 fail-closed 锚「畸形当空」（锚错方向，放过真正的「误读→假一致」）；把「读到 0 条」当失败（那是响亮自纠态）；照搬门的 all-or-nothing 到报告工具（有差异≠该 fail）

**maintain / init 的 INDEX 分治 (Maintain vs Init INDEX Division)** 〔grill-amendment · adr/0016〕:
`openspec/INDEX.md` 里「rules」撞两义须分治：**workflow bundle 规则**（`openspec/workflow/*.md`）索引在 `<!-- opsx-init:rules:start..end -->` **托管块**、归 **sdflow-init**（`update` 刷新）；**消费仓通用规则**（`openspec/rules/*.md`，可选目录，缺失=合法空）在托管块之外、归 **sdflow-maintain** 的 set-diff。maintain 解析 INDEX MUST **用机器锚行界定、跳过 init 托管块**（不跳则 bundle 条目被误当「已删未清理」+ 诱导越界改 init 领地）。maintain 依赖 init 两常量（`RULE_MARKERS`/`MARK_IDX`）：**canonical 留 `init.py`、maintain 保自包含副本 + 跨脚本一致性守卫 pytest**（跨 skill import 破自包含且运行时脆、物理单一源不可达）——T17 的真闭合 = 机验同步（守卫测试），非删到一份；跨语言副本（bash）难同守则 defer 登记。
_Avoid_: maintain set-diff 时把 init 托管块条目当自己领地（越界+误报）；跨 skill import 取「物理单一源」（破自包含、运行时脆）；把「删到只剩一份」当 T17 闭合（跨 skill 不可达，机验同步才是）

**footage（讨论过程考古层）** 〔grill-amendment · rebuild-sdflow-roadmap-v2〕:
roadmap 规划中「决策形成过程」的原始素材层，与「决策结晶」（三件套正文）相对——血统类比：footage 是毛片、design §决策是成片（词源即本仓 sdflow-roadmap 的既有措辞，非 matt 套件概念）。物理形态两种：**长档** wayfinder 的 map+tickets 落 `roadmaps/{name}/footage/` 目录；**短档**可选 memo 保持包根 `memo.md`（既有落位不迁）。引用纪律统一：三件套 MUST NOT 引用任何考古层内容（`footage/` 或 `memo.md`），有价值结论须精炼后写入正文。
_Avoid_: 把 footage 当 wayfinder 专属产物（它是考古层统称，memo 亦属之，短档没跑 wayfinder 也适用同一引用禁令）；「详见 footage/memo」类表述（考古层是草稿证据、非权威源）

**ticket（实现分解单位）** 〔grill-amendment · matt-workflow-integration〕:
tickets 实现管线的实现分解单位 = **tracer-bullet 垂直切片**（一条打穿全层、可独立验证的行为级路径），英文原词不译。在 plan 文件与 ship_gate 契约中以 **Task 号**呈现（`### Task N:` 标题 / `checkpoint(<change>:task<N>-)` 标签），一 ticket = 一 Task 号；ticket 内验收复选框 = **实现期完成信号**（implementer 与 checkpoint 标签**双写**）。与既有两层复选框的分工：roadmap 复选框 = 规划粒度、归档后镜像回写；change tasks.md 复选框 = 需求追溯层（R-ID 载体，ticket 由它派生但不取代它）、**archive 阶段才勾**。matt 套件中 wayfinder 的讨论 ticket（map 的 issues/<NN>）是另一种 ticket（讨论单位，非实现分解），需限定词区分。
_Avoid_: 「票」「任务」混称（tasks.md 的「任务」与 ticket 勾选时机**相反**：归档期 vs 实现期，混称会让 ship-tasks-flip 失鲜坑换面目重现）；把 wayfinder 讨论 ticket 与实现 ticket 混为一谈

**SAD（系统架构设计文档 System Architecture Document）** 〔grill · add-sdflow-architecture，设计期〕:
消费仓 `openspec/architecture/sad.md` 的**项目级单例 live 文档**（per-system 非 per-effort——roadmap 包是 effort 的、SAD 是系统的：一仓可多 roadmap，系统真相只一份）。十节骨架承载 HOW-structure（子系统/contract/横切）；与 roadmap 三件套三分：design.md=WHY-product、SAD=HOW-structure、roadmap.md=WHEN，互引不复述。由 `sdflow-architecture` 产出，**直写不经 change 壳**（先例 = roadmap 规则 4 直写）。
_Avoid_: 把 SAD 当 roadmap design.md 的同义词（三分各有其职）；把 SAD 放 `roadmaps/{name}/` 包内（effort 归档了系统还活着）

**skeleton-ready** 〔grill · add-sdflow-architecture，设计期〕:
SAD 的交棒完成态——「**够切出骨架 change**」即合格；纸上 contract 全是假设，骨架真实调用验证之前**不存在 approved/定稿**。状态机 `draft → skeleton-ready → validated →（逐条）frozen`；升级门槛 = 事实三问齐 + 假设逐条处置。此 DoD 结构性降低对人的索取（价值类可占位）与文档完成度要求（contract 骨架前只强制语法/所有权/错误语义三层主干）。
_Avoid_: 「approved SAD / 定稿」（伪严谨、倒逼 day-0 过度索取——被否记录见 change 附录）

**骨架 change（Walking Skeleton Change）** 〔grill · add-sdflow-architecture，设计期〕:
SAD 之后的**第一个** change：穿过全部子系统 contract 的最细垂直切片。DoD = 每条 L1 contract 被一次真实调用穿过 + 部署链路走通——**交付物是被验证的 contract，功能薄到可笑才是对的**。ticket 的 tracer-bullet 同思想上移到系统层；骨架落地 → contract 逐条 draft→validated。
_Avoid_: 把骨架当 MVP/「第一个功能」（它验证边界不交付功能）；L2 子系统设计先于骨架全量展开（在未验证的 contract 上盖楼）

**骨架切片建议 (Skeleton Slice Suggestion)** 〔grill · add-sdflow-architecture，设计期〕:
SAD **唯一的暂态节**：升 skeleton-ready 时写入（contract 穿越点**引用** + 骨架 DoD + 建议 change 名），消费语义 = **建议非契约**（先例 = ff-generation-constraints 切片建议节）；人拍板后自行开骨架 change，skill MUST NOT 代开；骨架回写 validated 时移除该节（live 层当前态，历史归 git）。
_Avoid_: 独立 skeleton-draft 文件（必复述 §5、必失鲜）；把建议节当契约消费

**事实三问 (Three Fact Questions)** 〔grill · add-sdflow-architecture，设计期〕:
sdflow-architecture 采集步的**全部**问卷：一句话定位 / 外部系统清单（含文档指针）/ 硬约束（栈-平台-部署形态-存量-合规）。任一缺 → fail-closed 锁 draft。配套纪律「**事实前置、价值后置**」：价值类（质量取舍/承受度/Non-goals）不进问卷，后置到拍板步挂具体产物以选择题问——「A/B 选哪个」优于「描述你的取舍」一个量级。
_Avoid_: day-0 问抽象价值题（人答不出是问法错，非人无法提供）；把 `facts=answered` 读成「回答质量已核」（只表「已记录人答」，质量归人门）

**假设显影 (Assumption Surfacing)** 〔grill · add-sdflow-architecture，设计期〕:
防「幻觉架构文档」机制——AI 从薄需求也能产出**看起来权威**的完整 SAD，危险恰在权威感。推测/编造 MUST 标 `[假设-N]`（正文内联 ↔ 附录清单**双向锚**，处置 ∈ {接受, 待校准, 未处置}）；数值带溯源（人拍 / 推荐待校准）；lint 计数**以正文实扫为准**（frontmatter 仅缓存）；存在未处置 → 不得升 skeleton-ready。
_Avoid_: 带 30 个未确认假设的「完整」SAD 当成品（那是 30 个洞的 draft）；采信 frontmatter 缓存计数（正文实扫为准，不一致报 mismatch）

**留白 (Blank) / ⚠️ 待定 (Pending)** 〔grill · add-sdflow-devenv，设计期〕:
`sdflow-devenv` 核心承诺「三层×五槽**一层都不许留白**」中的**留白**，钉为「**该问的没问出口**」——**不是**「格子里没字符串」。
故 **`⚠️ 待定` 是合法产物**（副驾问了、人当场答不上来，如实落它），schema 放行，**即便 15 格全待定**。
_Avoid_: 把「不许留白」读成「机械保证填满」（那只保证「有字符串」，trivial，且会**奖励空话、惩罚诚实**——拦一个空的 `strength` 不会让模型写出好的 `strength`，只会让它写出一句话）。

**副驾 (Co-pilot)** 〔grill · add-sdflow-devenv，设计期〕:
`sdflow-devenv` 的身份定调——**辅助人搭建环境 + 提醒人别忘了考虑什么**。**不是**替人开车的生成器，**也不是**查人岗的审计官。
由此定死：**「防漏」的形态是「问」，不是「拦」**（`SKILL.md` 逐条问 + `references/` 清单，非 lint fail-closed）；**代价可见 > 机械拦截**（渲染横幅「⚠️ 本框架 12/15 格待定，尚不构成一份可用的测试策略」+ 收尾报告逐条列）。
_Avoid_: 为「保证模型真的问了」发明机械——**「问没问」与「跑没跑」同构，agent session 里模型是唯一执行者，机械上不可区分 ⇒ 属防伪，机械层不管**（`07` §0.0）。

**层 (Layer) —— 保真度刻度** 〔grill · add-sdflow-devenv，设计期〕:
`sdflow-devenv` 三层框架里的**层**（`单元` / `集成` / `e2e`），钉为**保真度刻度**——**一条泳道归哪层，由「它穿过哪些真实边界」判定**（单元 = 不穿任何真实外部边界 · 集成 = 穿过部分 · e2e = 端到端全穿），**不由它用什么测试框架判定**。
故：vitest 组件测试不连真实依赖 ⇒ **单元层**（哪怕它渲染了 DOM）；`assert-bindings` 结构门禁读真的生成物文件 ⇒ **集成层**。
_Avoid_: 把「层」当**测试类型分类法**（「vitest 算 unit 还是 integration」是二十年没吵清的问题，模型每次会给不同答案且无法复核）；把「层」与 `lane-patterns` 的**依赖形态阶梯**当两个轴（**形态决定你有哪些真实边界，边界决定泳道落在哪个刻度——是同一个轴**）。

**层状态 —— 投影，非声明** 〔grill · add-sdflow-devenv，设计期〕:
层**没有自己的状态**——它从 `lanes[]` **投影算出**（全 `planned` ⇒ `planned`；有 `scaffolded` 无 `verified` ⇒ `scaffolded`；有 `verified` ⇒ `verified`）。**唯一需要人拍的层状态是 `不适用`**（零泳道 + 理由 + **后果**），它是价值判断。
**`已实现` / `人工` 两词已废弃**：`已实现` 实指「有脚手架」（其定义只要求泳道 ≥ `scaffolded` = 写了但**没验**）⇒ 用户读到「集成测试：已实现」会以为它跑得起来，**这个词在装**；`人工` 与泳道的 `executor: human` **双写**。
_Avoid_: 手写层状态（它是投影，手写即可伪造可漂移）；用「已实现」描述一个从未跑绿的层。

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
- 「回填助手切分线」第三轮 spec-review 再精化〔`adr/0015` P-1..P-5〕：最小核仍残 **2 致命 + 3 高**（4 镜 + 广审 + outside-voice 高度收敛），根因=**切分线画错位置**——`定位哪些复选框` 被误划机械侧（实为判断）+ 时序矛盾（步2 读步3/步5 才存在的盘面）+ 异步无闭环 + 格式实测分裂 + dogfood 自指坑。修法：**定位到 phase**（change 名前缀 `implement-{roadmap}-pN` 确定性信号 → 机械）、**勾哪几行**（判断留人）；archive/merge 留占位不预填（P-1）；格式分形态 fail-loud（P-3，两存量 roadmap 格式实测 grep 54 vs 0）；异步闭环第六步摘要抬一行 + 残差登记（P-4）；detection fence-aware 防自指（P-5）。**元教训**：点驱动修补（前两轮杀机械回写点）会留相邻面（定位/时序/闭环）——面治需系统扫，非逐条补丁。
- 「留白」曾指「格子里没字符串」——已钉为「**该问的没问出口**」：`⚠️ 待定` 是合法产物（人答不上来的如实记录），**15 格全待定亦过 schema**；承诺的兑现靠 **A 层提问清单 + 代价可见**（渲染横幅 + 收尾报告），**不靠机械兜底**（`07` §0.1 / 附录 A23）。
- 「防漏」曾隐含「用 lint 拦住空槽」——已按副驾身份改判为「**逐条问出口 + 空槽显眼呈现**」；机械层只拦**人看不见**的（`status` 拼成 `verifed`、路径穿越），**人一眼看得见的（五槽留白）只报不拦**。
- 「层」曾在 `sdflow-devenv` 里含混（既像测试类型分类法、又要与依赖形态阶梯对齐）——已钉为**保真度刻度**（判据 = **穿过哪些真实边界**），与形态阶梯**合成一个轴**（见 `07` §2.2 / 附录 **A25**）。
- 「已实现」曾是层状态之一——**已废弃**：其定义（泳道 ≥ `scaffolded`）允许「从未跑绿」的层自称已实现，**这个词在装**（`07` §0.0：「跑不绿是合法状态，跑不绿却装作跑得绿不是」）。层状态改为**从泳道投影**，`不适用` 是唯一人拍的（见 `adr/0021` 的同源原则：**让坏事没法发生，而不是发生后抓它**）。
- 「skill 的落地物」曾以**文件类型**列举（Makefile target / CI / harness…），其中 **Makefile 被写成「门禁逻辑在此」**——**已废弃**：`sdflow-devenv` 承诺「不管什么项目」，而「用什么跑测试」是**模型看着项目现场决定的**（Rust 用 cargo / Node 用 `package.json` / 很多项目一条裸命令就够）。落地物改按**风险**分两类（**新建 / 改已有**），见 `07` 附录 **A24**。
- 「skill 删源」曾是归位模式的一个动作——**已禁**（`adr/0022`）：**skill MUST NOT 删除用户的任何文件**（爆炸半径不受控，引用可能在仓外）。**可改内容**：整体失效 → 顶部加标记内容留着；部分失效 → **真删那段**（失效范围须由「不存在」界定）。
