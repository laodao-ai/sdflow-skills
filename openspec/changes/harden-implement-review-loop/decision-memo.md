---
schema_version: 1
change: harden-implement-review-loop
branch: feat/harden-implement-review-loop
generated_at: 2026-07-27T13:10:13+00:00
decision_hash: 1be2eeb35560
---

# 决策纪要 · harden-implement-review-loop

## 目标态

给 `sdflow-implement` 补齐与 `sdflow-code-review`/`sdflow-spec-review`/`sdflow-done` 一致的模型档位声明，把 T10 协议的"②派对抗镜复核"仲裁步升级为 strong（跨 `workflow.md` 单一源与 `sdflow-code-review` 的引用点同步），并把每 ticket 的测试执行范围从"结束前跑一次全套件"收紧为"单元+本票 e2e 场景"，把全量聚合回归（单元+集成+e2e）挪成 `sdflow-done` verify 新增的一类证据锚点。

## 拍板决策

- **D1 implementer / Standards轴 / Spec轴 / fix子代理 → 声明为 mid 档** — 依据:结构上对应 `sdflow-code-review`/`sdflow-spec-review` 的"领域镜/对抗镜"(`model-tiers.md` 明文定为 mid),下游 `sdflow-code-review` 冷层是完全独立的重审,能兜住 severity 误判风险;**砍掉的候选**:两 reviewer 提到 strong(理由:发明了 code-review/spec-review 都没有的新层级,且 tickets 严格串行×fix循环最多2轮会让成本翻倍,下游冷层已兜底,收益不足以抵成本)。**落地方式(无争议,显式记录避免 C 阶段漏机制)**:`sdflow-implement` 目前零第零步档位解析(C1),要拿到 `$SDFLOW_TIER_MID` 就必须补上跟 `sdflow-code-review`/`sdflow-spec-review`/`sdflow-done` 完全一致的"第零步:宿主/档位解析"四步(清脏→预检→捕获退出码→eval后校验),不是只改措辞——这是 Layer1 最初的诉求本体,必须在 design.md 里显式列出这一整段机制,不能只写"声明为 mid"这四个字。
- **D2a 阶段三"遇≥2方案自动选"场景(canonical T10,`workflow.md`/`sdflow-ship`/`sdflow-code-review`/`spec-workflow/spec.md` 共享同一语义)的②"派对抗镜复核"步升级为 strong** — 依据:该步只在无客观判据时才触发,低频高杠杆;superpowers 自身的 fix-loop 在第4-5轮同样"换更强模型"处理卡住的循环,是外部验证过的模式(见 C7)。**砍掉的候选**:维持不指定档位(理由:code-review 自己用此步时也未指定,实际落在 mid,等于同档互相打分,没有真正引入更强判断)。**范围**:改 `workflow.md`(canonical 定义)+ `sdflow-ship/SKILL.md` + `sdflow-code-review/SKILL.md` + `openspec/specs/spec-workflow/spec.md`(≥3处 Requirement,顺手补回被丢掉的"按三镜+主次"措辞,见 C8)——这4类落点描述的是同一件事,继续共享同一套(未单一源化的)复述架构,这次不改造该架构本身(通则③,不加宽)。
- **D2b `sdflow-implement` 熔断仲裁(同一发现连续2轮 re-review 仍未消解)场景的仲裁步独立升级为 strong,不再引用"T10"这个标签** — 依据:C8 核实这个场景与 D2a 的"≥2方案选择"触发条件本质不同(前者是"同一问题反复修不好要不要继续",后者是"多个候选方案选哪个"),只是处置形状相似(自动选/复核/defer);继续共用"T10"标签会让未来编辑者误以为改一处会同步影响另一处(这正是这次差点发生在我自己身上的错误)。**砍掉的候选**:维持沿用"T10"标签统一措辞(理由:掩盖两者触发条件不同的事实,且 C8 确认无机械工具依赖这个字面标签,脱钩零成本)。**范围**:只改 `sdflow-implement/SKILL.md` 自己的熔断处置段落,就地描述规则,不再提及 `workflow.md`/T10。
- **D3 每 feature ticket 测试范围收窄为"单元+本票e2e场景";出票模式新增一张强制的"实现验证"收尾 ticket,专门跑聚合套件(单元+集成+e2e)并按标准 fix 循环修复,不计入 3–6 张垂直切片预算(T120 式收尾票豁免)** — 依据:tracer-bullet 设计要求每票本身可 demo,故本票的 e2e 场景该在本票内验证;但聚合回归只在多票都存在时才有意义,该在全部功能票完成之后一次性做。现状链路里没有任何一步执行聚合回归(C3),这是新增覆盖,不是省成本。**这轮拷问纠正的关键点(见 C9)**:最初设想让 `sdflow-done` 的 verify 主动跑这个聚合套件,被指出 verify 定位是纯审计(核对已有证据锚,不主动执行、也没有 fix 机制)——若聚合套件失败,verify 无法像 implementer 那样进入 fix 循环。正解是把这个职责放进"实现验证 ticket":它和普通 ticket 一样走 implementer+双轴审+fix 循环全套机制(Spec 轴核验"聚合套件真的跑过且通过",Standards 轴核验"修复方式没有靠删/弱化断言蒙混过关"),`Blocked-by` 全部其它 ticket 号,`sdflow-done` verify 只需引用这张收尾票自己的 commit+报告作为聚合覆盖需求的证据锚,不需要扩张 verify 自身职责,也不碰 R6"无 warm final whole-branch review"的既有边界(那条挡的是代码审查,这张票做的是测试执行,不同轴)。**砍掉的候选**:①维持"结束前跑一次全套件"不分层(理由:e2e 通常慢,每票都付全量成本,且最多6票×fix循环最多2轮会重复跑很多次);②让 verify 主动执行聚合套件(理由:verify 现有定位是纯审计,没有 fix 机制,套件失败时无法处置,只会把这条需求永远判 gap,见 C9)。
- **D4(不做) 任务复杂度动态选 implementer 档位** — 依据:出票阶段已有的票 size 上限(单窗口消化)+ T120 宽重构例外已经把"这张票天生复杂"的相当一部分先验信号在出票阶段路由掉;重开 design D8"试点期变量控制"钉死 mid 的决定需要独立立项,不该这次顺手做;复杂度分类器本身是不确定地带,做糙了成本收益比不明。**砍掉的候选**:现在就做(理由同上三点)。

## 承重约束

- **C1 `sdflow-implement` 当前完全没有模型档位声明** — 验证方式:`grep -n "model-tier\|strong\|mid\b\|opus\|sonnet\|haiku\|档" sdflow-implement/SKILL.md`;**证据锚**:命中仅两行且均为无关上下文(`sdflow-implement/SKILL.md:453,460`,属 Standards 轴"repo overrides"治理规则,非档位声明)。
- **C2 T10 协议本身未规定仲裁档位,`sdflow-code-review` 自己用 T10② 也未指定档位** — 验证方式:读 `workflow.md:106` 与 `sdflow-code-review/SKILL.md:283`;**证据锚**:两处"②无客观判据→派对抗镜复核推荐项"均无档位字样。
- **C3 阶段三链路当前没有聚合套件回归执行点** — 验证方式:读 `sdflow-ship/SKILL.md`(链序 embedded-test-sop→sdflow-implement→sdflow-code-review→sdflow-done)、`gstack/review/SKILL.md`("Analyze...for structural issues that tests don't catch",不跑测试)、`sdflow-done/SKILL.md`(verify 锚点模型=逐条需求配锚,非聚合套件锚);**证据锚**:`sdflow-done/SKILL.md:13-14,205,213`。
- **C4 现有"结束前跑一次全套件"未分测试粒度** — 验证方式:读 `sdflow-implement/SKILL.md:345-346`;**证据锚**:原文"定期跑 typecheck、结束前跑一次全套件",无单元/集成/e2e 区分。
- **C5 冷层 `sdflow-code-review` 与双轴审非重复,是实证承重墙** — 验证方式:读 `sdflow-implement/SKILL.md` R6 裁剪边界声明;**证据锚**:"这是实证承重墙(独立冷视角能抓循环内被 controller 说服放过的真问题),不是可省的重复层"。
- **C6 Standards/Spec reviewer 自判 severity,权重比 code-review 领域镜更重(接受、不升档)** — 验证方式:读双轴审"裁决处置"段落,对比 code-review Step2/Step3 分层;**证据锚**:`sdflow-implement/SKILL.md:487-495`(裁决处置直接按 Critical/Important/Minor 分流,无独立复核层)对比 `sdflow-code-review` Step3(置信过滤+对抗裁决独立于领域镜)。**为何接受**:severity 误判风险由下游冷层完全独立重审兜底,不依赖 implement 阶段标签。
- **C7 superpowers 源码验证:task 执行严格串行是 upstream 既定设计,per-task review 与 final review 并列非重复** — 验证方式:读 superpowers 6.2.0 `subagent-driven-development/SKILL.md` 原文;**证据锚**:"Never dispatch multiple implementation subagents in parallel (conflicts)"(line 230)+ "Per-task reviews are task-scoped gates. The broad review happens once, at the final whole-branch review. Never skip the task review"(line 258-259)。
- **C8 "T10" 是历史 todo 追踪 ID 借来的代号,不是单一源协议;6 个落点比对出 2 类真实差异,且无机械工具依赖这个字面字符串** — 验证方式:溯源 `openspec/changes/archive/2026-07-03-sdflow-ship/`(proposal.md:14/design.md:76/tasks.md:18/verify-report.md:46,与 T11/T20 同批的 todo 追踪条目);逐字比对 `workflow.md:106`/`sdflow-ship/SKILL.md:164`/`sdflow-code-review/SKILL.md:283`/`sdflow-implement/SKILL.md:490-493`/`spec-workflow/spec.md`(~29/~83/~638)/`impl-orchestration/spec.md:60` 六处措辞;grep 全仓 `*/scripts/`、`*/tests/` 确认无机械依赖(命中均为巧合时间戳或示例性 fixture 文本,如 `sdflow-issues/tests/test_batch_lint.py:118`)。**证据锚**:差异 A(触发条件)= `sdflow-implement` 是"熔断"、其余 4 处是"≥2方案";差异 B(措辞丢字)= `spec-workflow/spec.md` ~83 行丢失"按三镜+主次"限定词,对比 `workflow.md` canonical 版本更松。
- **C9 `sdflow-done` 的 verify 现有定位是纯审计,没有主动执行或 fix 机制** — 验证方式:读 `sdflow-done/SKILL.md` 对 verify 的定位描述;**证据锚**:"每条 ✅ 必附机验锚点(测试名/commit/文件:行),无锚点 ✅ 降级 gap"——这是"核对已有证据是否存在"的审计动作,不含"执行命令产生新证据"或"发现失败后派 fix 子代理修复"的机制;verify 若发现聚合套件锚点不存在,只能判该需求为 gap,无法像 implementer 那样进入修复循环。

## 接受的边角

- Standards/Spec reviewer 的 severity 判断权重比对标的 code-review 领域镜更重(见 C6)——概率:每票都会发生(reviewer 必须判);影响:误判会导致该发现被不当 defer 或不当触发 fix 循环,但下游冷层兜底,实际漏网概率低;完美成本:消除此权重差异需新增独立强档复核层,每票多付一次 strong 调用,成本过高;**为何接受**:下游 `sdflow-code-review` 是独立重审、不依赖该标签,风险敞口已被结构性覆盖。
- 任务复杂度动态选 implementer 档位不做(D4)——概率:多数票已被出票阶段 size 上限 + T120 过滤,真正"意外复杂"的票占比低;影响:若确有意外复杂的票被误判为普通 mid 档处理,可能多触发几轮 fix 乃至 T10 熔断,但 D2 已捕获熔断后的升档路径(反应式那一半价值);完美成本:构建可靠复杂度分类器是独立调研量级,做糙了会双向出错(过度保守或漏判);**为何接受**:D2 已捕获这条路径的高价值那一半,开工前预判的增量收益不确定,且重开 design D8 需要独立立项。
- 跨票 e2e/集成回归的发现时间从"当票发生时立即发现"推迟到"末尾聚合验证票才发现"(见 D3)——概率:随 `Blocked-by` 依赖边数量而定,有依赖关系的票之间较易发生;影响:排查成本增加,但排查范围有界(仅限本 change 自身 3-6 张票的 commit 集合,非全代码库);完美成本:要保留"当票立即发现"这个副作用,唯一办法是维持"每票全套件",那正是 D3 要优化掉的成本;简化方案:聚合验证票复用完整的 implementer+双轴审+fix循环+D2b 熔断升档机制,不是无处置能力的黑洞;**为何接受**:现状的"立即发现"是执行方式的意外副产品而非设计出来的早期预警,用它反对省成本的方案理由不够强,且下游有完整 fix 机制兜底。

## 三镜代价

命中 TG-23(D1/D2/D3 均为 ≥2 合理方案的设计选择):

- **系统镜**:D1 不升档 = 不额外增加 strong 调用面,依赖"下游冷层独立重审"这条既有耦合关系兜底;D2 升档改动集中在 `workflow.md` 单一源,同步牵动 `sdflow-code-review` 的引用点,避免协议内部产生歧义分叉;D3 给 `sdflow-done` verify 新增一类证据锚点,填补了链路里聚合回归执行点缺失的结构性空洞。
- **用户镜**(套用本工作流的开发者):D1 不升档换来更快的响应(mid 通常比 strong 快);D2 只在熔断这种低频场景触发,对日常流程无感知干扰;D3 把 e2e 成本收窄到票级相关场景 + 末尾一次聚合,减少每票等待时间,但要求开发者在 verify 报告里多认一类新的证据锚点。
- **开发循环镜**:D1 不升档省下显著的 token/时间成本(不必两倍 strong 调用);D2 集中在一份协议定义里改,维护面不增加;D3 让 `sdflow-done` 的 verify 模板多维护一类锚点定义,略增维护面,换来的是覆盖率的真实提升。
- **主次判定**:本次改动的主要驱动力是系统镜(填补架构不对称、修复 T10 仲裁盲区、堵上聚合测试执行的结构性空洞),用户镜与开发循环镜的代价都是可接受的边际增量,非决定性因素。
