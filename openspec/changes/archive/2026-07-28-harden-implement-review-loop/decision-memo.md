---
schema_version: 1
change: harden-implement-review-loop
branch: feat/harden-implement-review-loop
generated_at: 2026-07-27T13:10:13+00:00
decision_hash: ceda46709b0e
---

# 决策纪要 · harden-implement-review-loop

> 〔spec-review-amendment〕本文件在阶段二设计 HARD-GATE 拍板后按 Q1–Q6 裁决与采纳 findings 修订。
> 修订处标 `[spec-review-amendment]`。`decision_hash` 已随正文重算。

## 目标态

给 `sdflow-implement` 补齐与三个姊妹 skill 一致的宿主/档位解析(**并同步修掉 `sdflow-done` 自己的裸 `eval`**,四份拷贝由机械 parity 守卫锁住),让四类子代理按本机队 mid 档派发——这首先是一个**跨机队正确性**修复,其次才是架构对称。把 T10 按语义拆成两条**具名**规则(`T10-choice` / `review-loop-breaker`),各自的②仲裁步升 strong。把每 ticket 的测试执行范围从"结束前跑一次全套件"收紧为"单元 + 本票 e2e 场景 + 本票 `Blocked-by` 链上模块的集成测试",并在出票模式**末尾新增一张强制的「实现验证」收尾 ticket** 承担聚合回归(单元+集成+e2e);`sdflow-done` 的 verify **不扩张职责**,只把该票的 impl-report 作为「**实现期**聚合覆盖」的证据锚,且该锚**按管线条件化**。tickets 轨的计划文件更名 `tickets.md`。

〔spec-review-amendment L8〕本节此前写"把全量聚合回归**挪成 `sdflow-done` verify 新增的一类证据锚点**"——那是 C9 纠正**之前**的口径,与最终结论(放进收尾票、verify 不扩张职责)矛盾,已改正。

## 拍板决策

- **D1 implementer / Standards轴 / Spec轴 / fix子代理 → 声明为 mid 档,补第零步四步解析** — **主论据(修正)**〔spec-review-amendment L7/X1〕:不是"架构对称",而是**跨机队正确性**——`model-tiers` Requirement 明写"MUST NOT 在 Codex 宿主下把 Claude 机队的模型名用于 Codex 机队子代理",`sdflow-implement` 无第零步即拿不到本机队档位,这是正确性缺陷而非风格不一致。**次论据**:结构上对应 `sdflow-code-review`/`sdflow-spec-review` 的领域镜/对抗镜(`model-tiers.md` 明文定为 mid),下游冷层独立重审能兜住 severity 误判。**砍掉的候选**:两 reviewer 提到 strong(理由:发明了新层级,tickets 严格串行×fix 循环会让成本翻倍,下游冷层已兜底)。**落地方式**:必须补齐完整四步(清脏→预检→捕获退出码→eval 后校验),不是只改措辞。
- **D1a 对齐目标 = 四步语义,不是逐字复制;交叉引用改具名锚点;补机械 parity 守卫**〔spec-review-amendment Q5 拍板 · 五镜收敛证伪原措辞〕 — 依据:三份现存模板**本就不一致**——`sdflow-done` 是裸 eval(见 C10);`sdflow-code-review` 与 `sdflow-spec-review` 四步文案相同,但内部"本步第 N 项"交叉引用不同,那是**依文件本地结构派生的量,不是可搬运的常量**;而 `sdflow-implement` 根本没有编号起手步骤列表 ⇒ 逐字照抄必产悬空引用。∴ 措辞改"对齐四步语义",跨文件引用一律用具名锚点("见预检步")。**并补一条机械守**:仿 `hack/tests/test_async_branch_parity.py`,抽归一化核心段逐字节比对——本仓对同类问题**已有先例要机械化**,其理由原文即"复制是必要的,但复制不能靠手"(基准 1)。**砍掉的候选**:①只改措辞不加机械守(理由:tasks 无一条核验模板一致性,第四份拷贝的漂移无人守);②抽"共同算法契约"到 bundle 单一源(理由:更彻底,但属加宽,通则③)。
- **D1b `sdflow-done/SKILL.md` 的 `### 0.4` 裸 `eval` 一并修掉**〔spec-review-amendment Q4 拍板〕 — 依据:见 C10——它正是模板明文警告的 V1 陷阱,而本 change 要生成第四份拷贝,照它抄等于把已知不安全形态传播出去;这是**同一片一致性面**,此刻修最便宜(基准 3 面治优先于点补)。**砍掉的候选**:只改"对齐目标"措辞、`done` 本体另记 todo(理由:通则③不加宽——但用户拍板认定属顺手范围,以其为准)。
- **D2a `T10-choice`(Group A,阶段三"遇 ≥2 方案自动选")的②"派对抗镜复核"步升级为 strong** — **依据(重写)**〔spec-review-amendment H2/M16〕:🔴 **原依据"superpowers 自身的 fix-loop 在第 4–5 轮同样换更强模型(见 C7)"是错的,两重错**:① 该原文(`superpowers/6.2.0/subagent-driven-development/SKILL.md:174-175,328-333`)讲的是"**同一 task 反复修不好**换模型",那是 **Group B** 语义,已移到 D2b;② 标注的出处 C7 记的两条锚(禁并行派 implementer / per-task review 是 task 级门)**与该论据毫无关系**。**修正后的真实依据只有一条**:②档触发频率极低——40 余份归档 change 里只找到 1 次真实②档仲裁记录(`archive/2026-07-07-mlh-p5-gate-frontmatter/code-review-report.md:43`,且那次恰是 Group A 语义)⇒ 升档的**边际成本近零**;但**收益侧同样无实证**(无任何历史记录显示 mid 档在②档场景做出过错误裁决)。∴ 这是一个**成本低、收益未证的低风险决策**,不是被外部验证过的模式移植,措辞不得再声称后者。**适用边界**:strong 只加在②档(无客观判据时的仲裁),不扩到①档自动选。**砍掉的候选**:维持不指定档位(理由:实际落在 mid,等于同档互相打分)。**范围**:见 design 的 scope-check 表(Group A 共 15 处规范性落点)。
- **D2b `review-loop-breaker`(Group B,`sdflow-implement` 熔断仲裁)独立成文,不再引用"T10"标签,②步升 strong,并修两处机制缺陷** — 依据:C8 核实该场景与 Group A 触发条件本质不同(前者"同一问题反复修不好要不要继续",后者"多个候选方案选哪个"),只是处置形状相似;**superpowers 的 fix-loop 第 4–5 轮换更强模型正是本场景的外部印证(见 C11)——它属于这里,不属于 D2a**。两处机制修正〔spec-review-amendment H3/H4〕:
  - **身份键**:改为"同文件 + 规范化问题指纹",**行号只作定位、不作身份**。原"同 file:line + 同问题"有硬缺陷——修复几乎必然移动行号 ⇒ 同一未解决问题被认成新 finding、轮次计数清零 ⇒ `MUST NOT 无限循环` 兑现不了。
  - **互斥终态**:原三级处置只回答"finding 是否成立",而触发它的原因是"**成立但连续修不掉**" ⇒ 确认成立后既无新修复动作也无明确终态,可绕回原循环。改为三个互斥出口:不成立→关闭;成立且可修→strong 档 fixer 修复并**仅复验一次**;成立但不可修→进 buglist 并停。
  - **①档保留**〔X2 裁决〕:Group B 的①档(有客观判据自动选)预期极少触发(触发前提已是"连续 2 轮不消解",能客观判定的话第 1 轮就修好了),但保留成本近零(一句话),删掉反而制造"两组处置不对称"的新维护面(通则④)。design 补一句说明其预期低频。
- **D3 测试范围分层 + 强制"实现验证"收尾 ticket** — 依据:tracer-bullet 设计要求每票本身可 demo,故本票的 e2e 场景该在本票内验证;聚合回归只在多票都存在时才有意义。现状链路里没有任何一步执行聚合回归(C3),这是**新增覆盖,不是省成本**。三项修正:
  - **禁令放宽保留中间档**〔spec-review-amendment Q3 拍板〕:原措辞"MUST NOT 跑全量 e2e/集成套件"是**虚假二选一**,会把"受影响模块的集成测试"这类便宜且高信号的检查一并禁掉,implementer 会因"超出票面"跳过。改为:MUST NOT 跑**与本票无依赖关系**的集成/e2e;本票 `Blocked-by` 链上的模块集成测试**可跑**。代价:"该跑什么"的判定从机械变判断——接受(开发循环镜收益为主)。
  - **定位澄清:收尾票 = 实现期聚合回归门,不是最终完整性门**〔spec-review-amendment Q2 拍板 · 回应评审 C1〕:既有 Requirement「verify 为收尾最终门,位于所有修复之后」**未被触碰**,verify 仍在 `sdflow-done`、仍在所有修复之后。收尾票回答的是"全部功能票实现完毕这一刻聚合套件是否通过",不声称"最终代码通过"。code-review 之后的修复由 code-review 自身保障机制覆盖。残余风险见「接受的边角」。
  - **verify 锚按管线条件化**〔评审 C2〕:canonical 缺省是 superpowers 轨(见 C12),收尾票只由 tickets 轨产出 ⇒ 无条件锚会让默认轨的仓被判假 gap。锚 MUST 条件化,superpowers 轨下判"不适用"。
  - **砍掉的候选**:①维持"结束前跑一次全套件"不分层(理由:e2e 慢,每票全量,最多 6 票×2 轮 fix 会重复很多次);②让 verify 主动执行聚合套件(理由:verify 定位是纯审计,无 fix 机制,套件失败时只会把该需求永远判 gap,见 C9);③把收尾票整体移到 code-review 之后(理由:破坏"ticket 只在 implement 阶段产出"的既有边界,且改动面更大——用户拍板维持现状)。
- **D3b 聚合套件的发现方式:让工具自己回答,不解析构建文件**〔spec-review-amendment Q6 拍板〕 — 依据:`sdflow-implement` 要铺给**任意**下游仓,而"聚合套件"此前无契约(命令从哪取、缺层怎么办、flaky 怎么判、证据怎么落锚全无定义) ⇒ 模型会生成一张"文字正确、执行范围错误"的票,而现有三道 gate 与旧 Success Metrics 全部放行。**复用 `sdflow-devenv` 的既有答案**:候选命令**真跑一遍**看退出码,MUST NOT 解析 Makefile/package.json 找 target(`add-sdflow-devenv` 已付学费:脚本 562→119 行、7 个 fail-closed 罢工分支,`docs/sad/07` 附录 A21;基准 5)。**缺层记「未覆盖」而非罢工**——每个罢工分支都在背叛"不管什么项目都能跑完"的核心承诺。证据 schema 与四类失败分诊见 design。**代价**:要新增一点机械层,与原"本次不改脚本"的声称冲突 ⇒ 该声称已在 proposal 修正。
- **D4(不做) 任务复杂度动态选 implementer 档位** — 依据:出票阶段的票 size 上限 + T120 宽重构例外已过滤大部分先验信号;重开 design D8"试点期变量控制"需独立立项;复杂度分类器本身是不确定地带。**砍掉的候选**:现在就做。
- **D5 tickets 轨计划文件更名 `tickets.md`,superpowers 轨保持 `superpowers-plan.md`**〔spec-review-amendment · 用户拍板〕 — 依据:`superpowers-plan.md` 是 superpowers-only 时期的遗留,在 tickets 轨里是错名。**关键事实(见 C14)**:该文件名当前**两轨共用**,`ship_gate.py:1419` 与 superpowers 轨的 `step6-writing-plans.md` 都用它 ⇒ 不能简单全局 sed。**选中方案**:分轨命名 + gate/route 共享 resolver 探两名,**双存在 fail-closed UNKNOWN**;文件名**不参与轨道路由判定**(路由权威仍是 config 键 + frontmatter marker),只用于定位——避免新增一个会与 marker 冲突的冗余信号。**砍掉的候选**:①全局统一改一个中性新名(如 `impl-plan.md`)(理由:用户明确指定 `tickets.md`,且会波及 superpowers 轨的既有 prompt 契约);②只改文档不改脚本(理由:gate 按字面名读文件,不改即失效)。见 `adr/0033`。

## 承重约束

- **C1 `sdflow-implement` 当前完全没有模型档位声明** — 验证方式:`grep -n "model-tier\|strong\|mid\b\|opus\|sonnet\|haiku\|档" sdflow-implement/SKILL.md`;**证据锚**:命中仅两行且均为无关上下文(`sdflow-implement/SKILL.md:453,460`,属 Standards 轴"repo overrides"治理规则)。
- **C2 T10 协议本身未规定仲裁档位,`sdflow-code-review` 自己用 T10② 也未指定档位** — 验证方式:读 `workflow.md:106` 与 `sdflow-code-review/SKILL.md:283`;**证据锚**:两处"②无客观判据→派对抗镜复核推荐项"均无档位字样。
- **C3 阶段三链路当前没有聚合套件回归执行点** — 验证方式:读 `sdflow-ship/SKILL.md` 链序、`gstack/review/SKILL.md`(不跑测试)、`sdflow-done/SKILL.md`(verify 锚点模型 = 逐条需求配锚,非聚合套件锚);**证据锚**:`sdflow-done/SKILL.md:13-14,205,213`。
- **C4 现有"结束前跑一次全套件"未分测试粒度** — 验证方式:读 `sdflow-implement/SKILL.md:345-346`;**证据锚**:原文"定期跑 typecheck、结束前跑一次全套件",无单元/集成/e2e 区分。
- **C5 冷层 `sdflow-code-review` 与双轴审非重复,是实证承重墙** — **证据锚**:`sdflow-implement/SKILL.md` R6 裁剪边界声明原文"这是实证承重墙(独立冷视角能抓循环内被 controller 说服放过的真问题),不是可省的重复层"。
- **C6 Standards/Spec reviewer 自判 severity,权重比 code-review 领域镜更重(接受、不升档)** — **证据锚**:`sdflow-implement/SKILL.md:487-495`(裁决处置直接按 Critical/Important/Minor 分流,无独立复核层)对比 `sdflow-code-review` Step3(置信过滤 + 对抗裁决独立于领域镜)。**为何接受**:下游冷层完全独立重审兜底。
- **C7 superpowers 源码验证:task 执行严格串行是 upstream 既定设计,per-task review 与 final review 并列非重复** — **证据锚**:`subagent-driven-development/SKILL.md:230` "Never dispatch multiple implementation subagents in parallel (conflicts)" + `:258-259` "Per-task reviews are task-scoped gates. The broad review happens once, at the final whole-branch review. Never skip the task review"。
  🔴 **本条与"第 4–5 轮换更强模型"无关**〔spec-review-amendment H2〕——D2a 原先引 C7 支撑升档是**引错了出处**,那句话在 C11。
- **C8 "T10" 是历史 todo 追踪 ID 借来的代号,不是单一源协议;落点比对出 2 类真实差异,且无机械工具解析这个字面字符串** — 验证方式:溯源 `archive/2026-07-03-sdflow-ship/`(与 T11/T20 同批的 todo 追踪条目);逐字比对各落点措辞;grep 全仓 `*/scripts/`、`*/tests/`。**证据锚**:差异 A(触发条件)= `sdflow-implement` 是"熔断"、其余是"≥2 方案";差异 B(措辞丢字)= `spec-workflow/spec.md:83` 丢失"按三镜+主次"限定词。
  🔴 **措辞更正**〔spec-review-amendment M19〕:原文称 grep 命中"均为巧合时间戳或示例性 fixture 文本"——**被证伪**:`sdflow-done/scripts/roadmap_writeback_draft.py:88` 是真实**生产代码注释**引用一次历史 T10 裁决。核心结论("无机械依赖")**仍成立**(该注释不解析字符串,脱钩零成本),但"均为巧合"这个**验证性声明**不成立,已改为"无机械工具**解析**这个字面字符串"。
- **C9 `sdflow-done` 的 verify 现有定位是纯审计,没有主动执行或 fix 机制** — **证据锚**:"每条 ✅ 必附机验锚点(测试名/commit/文件:行),无锚点 ✅ 降级 gap"——这是"核对已有证据是否存在"的审计动作,不含"执行命令产生新证据"或"派 fix 子代理修复"。verify 若发现锚点不存在,只能判 gap。
- **C10 `sdflow-done` 自己的第零步是裸 `eval`,即模板明文警告的 V1 陷阱**〔spec-review-amendment · 主审实测〕 — 验证方式:读 `sdflow-done/SKILL.md:195-197`;**证据锚**:`### 0.4 宿主/档位解析` 是独立子标题,但其正文只有一行 `eval "$(~/.sdflow/hack/resolve-models.sh …)"`——**无** unset 清脏、**无** `[ -x ]` 预检、**无**退出码捕获、**无** eval 后校验。而 `sdflow-code-review`/`sdflow-spec-review` 的模板明文警告"V1:裸 `eval` 会被脚本缺失静默吞……`eval ""` 返回 0 且上一轮的 `SDFLOW_*` 旧值原样留存 ⇒ 拿旧宿主假绿"。∴"与三个姊妹逐字一致"这个前提**不成立**,照 `done` 抄会产出第四份不安全拷贝。
- **C11 superpowers 的 fix-loop 升档语义 = Group B(同一 task 反复修不好),不是 Group A**〔spec-review-amendment H2〕 — 验证方式:读 superpowers 6.2.0 原文;**证据锚**:`subagent-driven-development/SKILL.md:174-175` 与 `:328-333` 的 "Fix-loop escalation (rounds 4-5): use a model at least one tier above the implementer that got stuck"——触发条件是"the implementer that got stuck",即同一任务反复未消解,与 `sdflow-implement` 熔断仲裁同构,与"多候选选一个"不同构。
- **C12 阶段三实现管线的 canonical 缺省是 superpowers 轨,不是 tickets 轨** — 验证方式:读 `openspec/specs/spec-workflow/spec.md:83`;**证据锚**:"缺省 `writing-plans → subagent-dev`……缺省/非法值一律 superpowers"。本仓 `openspec/config.yaml:64` 恰为 `impl-pipeline: tickets` ⇒ **源仓自测照不到默认轨的洞**(dogfood 盲区)。
- **C13 Codex 子代理授权当前明文"仅限"两个评审 skill,且有机械断言守** — 验证方式:读 `AGENTS.md:282-284` / `CLAUDE.md` 同段;**证据锚**:原文"**仅限这两处**——不是对任意 skill 无限制放开 `spawn_agent`",且 `sdflow-init/tests/test_codex_subagent_authorization.py:53,55,75` 机械断言 `"仅限这两处" in t`。∴ 补 `sdflow-implement` 必须同时改指令文本与该测试,否则测试红。
- **C14 计划文件名 `superpowers-plan.md` 当前为两轨共用,且被脚本按字面读** — 验证方式:`grep -rn "superpowers-plan"`;**证据锚**:`sdflow-ship/scripts/ship_gate.py:1419,1423`(gate 按字面名判 RUN_PLAN)、`sdflow-implement/scripts/impl_route.py:439`(route 按字面名取 marker)、`sdflow-init/assets/workflow/prompts/step6-writing-plans.md:1`(**superpowers 轨**的 prompt 也指定该名)。∴ 改名不是文档改字,是契约改动;且不能全局 sed(会把 superpowers 轨也改成 `tickets.md`,语义不通)。

## 接受的边角

- **收尾票的聚合结果相对 `sdflow-code-review` 的自动修复不是最新**〔spec-review-amendment Q2 拍板 · 通则④五问〕 — **根因**:收尾票在 implement 阶段执行,而 code-review 在其后会改并提交源码且不重跑聚合套件,`sdflow-done` verify 只读证据不执行。**概率**:每次 code-review 产生自动修复时都发生(常见)。**影响**:三镜——系统镜:终门引用的聚合锚点在时间上早于最终代码,是一个已知的证据时效缺口;用户镜:无感知;开发循环镜:无额外成本。**完美成本**:在 code-review 修复循环之后再加一个聚合回归执行门,需定义该门的证据 schema 并改动链序,改动面显著扩大,且与本 change"解决实现期问题"的范围不符。**简化方案(选中)**:维持机制位置,**把锚的语义限定为"实现期聚合套件通过"**,不声称"最终代码通过";code-review 之后的质量由 code-review 自身保障机制(双轴/领域镜 + 置信过滤 + 对抗裁决 + 其 fix 循环)覆盖。**为何接受**:用户拍板——本 change 要解决的是实现期间的覆盖空洞;既有 Requirement「verify 位于所有修复之后」管的是 verify 自身位置,verify 未前移,该 Requirement 未被违反。
- **"不计入 3–6 预算"的两个后门**〔spec-review-amendment L1,defer〕 — expand–contract 迁移批次 + 收尾票都不计入,票数约束正被掏空。**概率**:每个含宽重构的 change;**影响**:票数上限失去约束力,但每票 size 上限仍在;**完美成本**:改为约束"总执行单元"或"总 frontier 成本"需重新定义计量口径;**为何接受**:本次不做,已记 todo。
- **Standards/Spec reviewer 的 severity 判断权重比对标的 code-review 领域镜更重(见 C6)** — 概率:每票都会发生;影响:误判会导致发现被不当 defer 或不当触发 fix 循环,但下游冷层兜底;完美成本:消除需新增独立强档复核层,每票多付一次 strong;**为何接受**:下游冷层独立重审,风险敞口已被结构性覆盖。
- **任务复杂度动态选 implementer 档位不做(D4)** — 概率:多数票已被 size 上限 + T120 过滤;影响:意外复杂的票可能多触发几轮 fix 乃至熔断,但 D2b 已捕获熔断后的升档路径;完美成本:可靠复杂度分类器是独立调研量级;**为何接受**:D2b 已捕获高价值那一半。
- **跨票 e2e/集成回归的发现时间推迟到末尾聚合票** — 概率:随 `Blocked-by` 依赖边数量而定;影响:排查成本增加,但范围有界(仅本 change 3-6 张票的 commit 集合);**简化方案**:Q3 保留的中间档(`Blocked-by` 链上模块集成测试可跑)把一部分跨票问题拉回当票,收尾票复用完整 fix 循环;**为何接受**:现状的"立即发现"是执行方式的意外副产品而非设计出来的早期预警。
- **`T10-choice` 的"同语义多落点漏改"风险原样保留** — 根因是复述架构本身(手抄进多文件、无 lint 兜底),拆标签只消除"跨语义误改";且 Group A 落点重新盘点后**从 6 处增至 15 处**,人工核对负担更重。**完美成本**:单一源 + 指针引用是更大的架构改造(通则③加宽);**为何接受**:本次 Non-Goal,由 tasks 的全仓 grep 复核兜一次,并已记 todo。

## 三镜代价

命中 TG-23(D1/D2/D3/D5 均为 ≥2 合理方案的设计选择):

- **系统镜**:D1/D1a/D1b 把四份第零步拷贝的漂移风险**机械封住**(parity 守卫),并修掉 `sdflow-done` 的已知不安全形态,漂移面收敛而非扩张;D2a/D2b 拆成两条具名规则,消除"改一处等于改全部"的误判,代价是牺牲"一个标签查全部引用点"的便利;D3/D3b 在链路里补上**此前完全缺失**的聚合回归执行点,并为"聚合套件"定了确定性发现契约与证据 schema,代价是新增一点机械层(gate 第四道校验)+ 一处已知的证据时效缺口(见接受的边角);D5 把一个错名改对,代价是 gate/route 多一个 resolver 与一条 fail-closed 分支。
- **用户镜**(套用本工作流的开发者):D1 保持 mid 换来更快响应;D2 只在低频②档触发,日常无感知;D3 把 e2e 成本从"每票全量"收窄到"票级相关 + 末尾一次聚合",单票等待时间下降,但整个 change 末尾多一张票的执行时间;D5 对在途 plan 有一次"两名并存则停"的可感知中断(概率低,Migration Plan 已给处置)。
- **开发循环镜**:D1 省下两倍 strong 调用;新增的 parity 守卫与 gate 校验是一次性成本、长期省;D3b 的契约让下游仓不必每次现场发明"聚合套件是什么";主要新增负担是 Group A 落点从 6 增至 16,一致性核对靠一次全仓 grep(未机械化,已记 todo)。
- **主次判定**:主要驱动力是**系统镜**——修跨机队正确性缺口、堵聚合测试执行的结构性空洞、把四份拷贝的漂移机械封住。用户镜与开发循环镜的代价都是可接受的边际增量,非决定性因素。
  〔spec-review-amendment L8〕本节原文写"D3 给 `sdflow-done` verify 新增一类证据锚点""verify 模板多维护一类锚点定义"——那是 C9 纠正**前**的口径(当时设想 verify 主动跑套件),已按最终结论改写。
