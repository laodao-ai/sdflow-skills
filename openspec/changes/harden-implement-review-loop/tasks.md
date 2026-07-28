> 🔴 **定位一律用原文片段锚,MUST NOT 用绝对行号**〔spec-review-amendment H14〕:首版把 `203/271/282/545/490-493` 等绝对行号写死在任务里,而 §1 会在 `sdflow-implement/SKILL.md` **靠前处新增一整段**第零步 ⇒ 顺序执行时后续行号整体下移、按行号定位读到错位内容。本版全部改为「原文片段 + 所在小节」定位。design 的 scope-check 表保留行号**仅作阅读索引**,执行时以片段为准。

## 1. 档位解析机制(D1 / D1a / D1b)〔R:sdflow-implement 档位解析与声明 / R:模型档位映射〕

- [ ] 1.1 给 `sdflow-implement/SKILL.md` 新增"第零步:宿主/档位解析"四步(清脏→预检→捕获退出码→eval 后校验),**对齐 `sdflow-code-review`/`sdflow-spec-review` 的四步语义**;跨文件交叉引用一律用具名锚点(如「见预检步」),MUST NOT 写"本步第 N 项"这类依文件本地结构派生的序号
- [ ] 1.2 明确第零步在"一文件两入口"(`tickets-plan` / `tickets-exec`)结构中的**插入位置与适用范围**:置于文件最前、**两入口共用、无条件执行**——出票模式同样需要档位(粒度争议与一致性自扫的②步要派 strong 对抗镜),不是空转步〔spec-review-amendment M8/L9〕
- [ ] 1.3 定义 `host=unknown` 与子代理不可用两种态的处置:**fail-loud 硬停**并提示在受支持宿主下运行,MUST NOT 用空档位或默认值继续派发——`sdflow-implement` 不 fan-out 就跑不了任何 ticket,与 `sdflow-code-review`"缩 roster"的降级路径**不同构**〔spec-review-amendment H10〕
- [ ] 1.4 为第零步的失败分支定义统一 halt envelope 文案(至少覆盖:resolver 不存在 / 不可执行 / 非零退出 / 输出无法 eval / host 非法 / host 空 / tier 缺失 / host=unknown 八类,逐类给 problem+cause+fix);复用 `sdflow-implement` 既有五要素 halt envelope,其 ticket 号字段填「—(起手失败,无票上下文)」〔spec-review-amendment M9〕
- [ ] 1.5 在 implementer dispatch 段**新增一句档位声明**引用 `$SDFLOW_TIER_MID`(现状是纯 prose 清单,**没有可替换的内联模型名或 `model:` 参数模板**,故是新增不是替换)〔spec-review-amendment M14〕
- [ ] 1.6 Standards 轴 / Spec 轴 dispatch 段同样新增档位声明,引用 `$SDFLOW_TIER_MID`
- [ ] 1.7 fix 子代理:确认其**是否有独立 dispatch 段**;有则新增声明,无则在双轴审"裁决处置"段落显式补一句"fix 子代理同 mid 档",并在本任务记录实际落点,避免与 1.5/1.6 重复计数〔spec-review-amendment M14〕
- [ ] 1.8 **修 `sdflow-done/SKILL.md` 的 `### 0.4`**:现状是裸 `eval` 一行(V1 陷阱,见 C10),升级为与 1.1 同一套四步语义〔Q4 拍板〕
- [ ] 1.9 新增 `hack/tests/test_tier_resolution_parity.py`:对 `sdflow-implement`/`sdflow-done`/`sdflow-code-review`/`sdflow-spec-review` 四个 SKILL.md 的第零步归一化核心段做**逐字节比对**,仿 `hack/tests/test_async_branch_parity.py`(marker token 单行字面量匹配,有界;MUST NOT 演化成解析 Markdown 结构)
- [ ] 1.10 **变异实测防恒真锚**:逐个删除四个 skill 第零步中的任一步,确认 1.9 的测试**必红**;两种恒真成因都要排除(门被别的断言满足 / 压根没用例走到那行),把变异记录写进 impl-report〔Success Metric 2〕
- [ ] 1.11 `AGENTS.md` 与 `CLAUDE.md` 的"Codex 子代理授权"段把 `sdflow-implement` 补进授权范围,并同步改"仅限这两处"措辞;**同步更新 `sdflow-init/tests/test_codex_subagent_authorization.py`**(该测试机械断言 `"仅限这两处" in t`,不改即红)〔spec-review-amendment H11 / C13〕
- [ ] 1.12 `sdflow-ship/SKILL.md` 的"取值经各被链序调度的子 skill(spec-review/code-review/done)各自 eval"枚举补上 implement〔spec-review-amendment M12〕

## 2. T10 拆分——Group A `T10-choice`(≥2 方案自动选,②步升 strong)〔R:阶段三过设计门后连续自动跑到 merge / R:outside-voice tension 不静默采纳 / R:出ticket模式产出tracer-bullet ticket〕

> 落点清单与统一计数口径见 design「T10 scope-check」表(Group A 共 15 处规范性落点)。**"T10" 保留为历史别名**,分析类文档不扫改。

- [ ] 2.1 `sdflow-init/assets/workflow/workflow.md` canonical 定义(片段:「遇 ≥2 方案按三级决策协议〔T10〕」)②步补 strong 档限定 + 引入具名 `T10-choice`
- [ ] 2.2 `sdflow-ship/SKILL.md`(片段:「决策协议(T10 三级,替换"有把握自动选")」)②步补 strong;同段的台账行格式 `T10复核:` 同步改名
- [ ] 2.3 `sdflow-code-review/SKILL.md` 四处(frontmatter description 的「按 T10 三级协议自动选推荐」/ 概述段同措辞 / ②步展开段 / 台账行格式 `T10复核:`)统一改名并在②步展开段补 strong
- [ ] 2.4 `openspec/specs/spec-workflow/spec.md`「阶段三过设计门后连续自动跑到 merge」②步补 strong + **补回丢失的"按三镜+主次"措辞**(delta 已含,核对归档同步)
- [ ] 2.5 `openspec/specs/spec-workflow/spec.md`「outside-voice tension 不静默采纳」code-review 自动裁决②步补 strong(delta 已含,核对归档同步)
- [ ] 2.6 **确认不改** `openspec/specs/spec-workflow/spec.md` 的 Scenario 指针(片段:「判据定义引主 spec T10 需求,本需求不重定义」)——它属无关 Requirement,"T10" 作为历史别名仍解析得到,拉整条 Requirement 进 delta 不划算(见 design「别名保留」)
- [ ] 2.7 `openspec/specs/impl-orchestration/spec.md`「出 ticket 模式」的「粒度争议按 T10 三级决策协议处理」升 strong(delta 已含,核对归档同步)
- [ ] 2.8 `sdflow-implement/SKILL.md` 出票模式两处粒度争议(片段:「走 ship T10 三级决策协议(design D9)」与「粒度争议走 T10,不问用户」)升 strong
- [ ] 2.9 `sdflow-implement/SKILL.md` 一致性自扫两处(片段:「发现矛盾走 T10 三级决策协议」与出处说明「阶段三无人类门场景换成 T10 自主裁决」)升 strong
- [ ] 2.10 `sdflow-init/assets/workflow/ff-generation-constraints.md`(片段:「对切片粒度的争议走既有 T10 三级决策协议」)升 strong **〔M1 补漏〕**
- [ ] 2.11 `docs/workflow-overview.md` §6.1「阶段三三级决策协议(T10,取代「有把握自动选」)」——这是**人读的并列定义、非指针**,②步同样声明 strong **〔M1 补漏〕**

## 3. T10 拆分——Group B `review-loop-breaker`(熔断仲裁,独立成文)〔R:每ticket双轴审加修复环〕

- [ ] 3.1 `sdflow-implement/SKILL.md` 熔断段(片段:「连续 2 轮 re-review 仍未消解 → 停止循环,按 T10 三级决策协议处理」)独立改写:不再出现"T10"字样,就地命名 `review-loop-breaker`,写明触发条件与三级处置,②步注明 strong 档
- [ ] 3.2 **身份键改为跨轮稳定**:从"同 file:line + 同问题"改为"同文件 + 规范化问题指纹",明确**行号只作定位不作身份**〔spec-review-amendment H3〕
- [ ] 3.3 **三级处置改为互斥终态**〔spec-review-amendment H4〕:①不成立→关闭;②成立且可修→strong 档 fixer 修复并**仅复验一次**;③成立但不可修→进 buglist 并停。MUST NOT 停在"确认成立"而无后续动作
- [ ] 3.4 补一句说明 Group B 的①档(有客观判据自动选)**预期极少触发**及其原因(触发前提已是连续 2 轮不消解),保留而不删〔X2 裁决〕

## 4. 测试范围分层 + 实现验证收尾 ticket(D3 / D3b)〔R:执行模式串行工作frontier / R:出ticket模式产出tracer-bullet ticket〕

- [ ] 4.1 `sdflow-implement/SKILL.md`「每 ticket 派 fresh implementer」节的测试契约,从"结束前跑一次全套件"改为"单元测试 + 本票声明的 e2e 场景 + 本票 `Blocked-by` 链上模块的集成测试";禁令措辞为 **MUST NOT 跑与本票无依赖关系的集成/e2e**(不是绝对禁令)〔Q3 拍板〕
- [ ] 4.2 明确"本票声明的 e2e 场景"在 ticket 骨架里怎么表达:骨架现只有 `Blocked-by:`/`R-ID:`/行为描述/验收标准复选框 ⇒ 定义为「验收标准中标注为 e2e 的条目即本票 e2e 场景;未标注则本票无 e2e,只跑单元 + 链上集成」〔spec-review-amendment M7〕
- [ ] 4.3 出票模式新增"实现验证"收尾 ticket 规则:`Blocked-by` 全部功能票号,不计入 3-6 预算,`R-ID: all`,验收标准 = 聚合套件(单元+集成+e2e)按契约运行并全部通过〔含 M6〕
- [ ] 4.4 落地**聚合套件发现契约**(design「聚合套件的发现契约」节):命令来源优先级(config `test-suites.*` → implementer 判定并写明依据)、**真跑一遍让工具自己判**(MUST NOT 解析 Makefile/package.json 找 target)、缺层记「未覆盖」而非罢工〔Q6 拍板〕
- [ ] 4.5 定义收尾票**证据 schema**:每层一行 `<层> | <命令原文> | <退出码> | <测试时 git rev-parse HEAD>`,未覆盖层写 `<层> | — | 未覆盖 | <依据>`
- [ ] 4.6 定义**四类失败分诊**:本 change 回归 → fix 循环;既有红测(base SHA 复跑确认)→ 记录放行;flaky(复跑一次即绿)→ 记录放行;环境故障 → halt envelope 停并上抛
- [ ] 4.7 **收尾票与普通票的执行契约差异**〔spec-review-amendment H9〕:显式豁免 red-before-green;主证据锚 = impl-report 文件 + SHA 三元组(不依赖 commit——`checkpoint-commit.sh` 在干净树上直接成功退出、不建 commit);Standards 轴核验范围扩为"未靠**加 skip / 改测试配置 / 删除或弱化断言**蒙混过关"
- [ ] 4.8 `sdflow-done/SKILL.md` 补 verify 引用规则:引用收尾票 impl-report 作为「**实现期**聚合覆盖」证据锚,**锚语义 MUST NOT 写成"最终全量回归通过"**;**该锚按管线条件化**——仅 tickets 轨要求,superpowers 轨判"不适用"、MUST NOT 判 gap〔评审 C2 / Q2 定位〕
- [ ] 4.9 `sdflow-ship/scripts/ship_gate.py` 加**第四道 plan 校验**:**当且仅当计划文件名为 `tickets.md`** 时,MUST 恰含一张收尾票且其 `Blocked-by` ⊇ 全部功能票号;文件名为 `superpowers-plan.md` 时跳过并输出一行提示(同时覆盖 superpowers 轨与改名前的在途 tickets plan)。**gate 无需读 config/marker 即可执行本校验**——文件名在此只区分「新出 / 在途或他轨」,不是轨道路由〔spec-review-amendment H12 / M17〕
- [ ] 4.10 为 4.9 补测试:含收尾票的 plan 绿、**删掉收尾票必红**、`Blocked-by` 缺一张功能票必红、grandfather 路径不红

## 5. 计划文件改名 tickets.md(D5)〔R:出ticket模式产出tracer-bullet ticket / R:阶段三过设计门后连续自动跑到 merge〕

> 🔴 **两轨共用一个文件名(C14),MUST NOT 全局 sed**——superpowers 轨保持 `superpowers-plan.md`。改共享字符串前先不带 `--include` 全量 grep,测试断言 / 生成物 / docstring 全纳入。

- [ ] 5.1 实现共享 **plan 文件名 resolver**(单一源,`impl_route.py` 与 `ship_gate.py` 两处 import 同一份,MUST NOT 手抄第二份):按序探测 `tickets.md` / `superpowers-plan.md`;**两者同时存在 ⇒ fail-closed UNKNOWN**;都不存在 ⇒ RUN_PLAN
- [ ] 5.2 `sdflow-ship/scripts/ship_gate.py` 改用 resolver(含 docstring 契约表与完成判据窗口段的文件名措辞)
- [ ] 5.3 `sdflow-implement/scripts/impl_route.py` 改用 resolver;**docstring 中引用 archive 历史文件路径的两处不改**(它们指的是真实归档文件)
- [ ] 5.4 `sdflow-implement/SKILL.md` 出票模式落盘路径与全部文件名措辞改 `tickets.md`
- [ ] 5.5 `sdflow-done/SKILL.md` 的文件名引用同步
- [ ] 5.6 bundle 侧:`sdflow-init/assets/workflow/workflow.md`、`.../WORKFLOW-GUIDE.md` 同步;`.../prompts/step6-writing-plans.md` **明确其只管 superpowers 轨、文件名不变**;`openspec/workflow/WORKFLOW-GUIDE.md` 仓内托管副本同步
- [ ] 5.7 测试同步:`sdflow-implement/tests/test_impl_route.py`、`sdflow-ship/tests/test_gate_impl_progress.py`、`sdflow-ship/tests/test_gate_freshness.py`、`hack/tests/test_checkpoint_slug_coverage.py`、`hack/tests/test_harden_sdflow_spec_followup_closure.py`;新增 resolver 的双存在 fail-closed 用例
- [ ] 5.8 文档同步:`docs/workflow-overview.md`、`docs/workflow-map.md`、`docs/workflow-map.html`、`docs/workflow-console.html`、`docs/criteria-mechanization-tracker.md`、`docs/workflow-skills/{impl-pipeline-matt-vs-superpowers,superpowers-writing-plans,superpowers-subagent-dev}.md`、`openspec/INDEX.md`
- [ ] 5.9 **不动**:`openspec/changes/archive/**` 与 `openspec/issues/**` 的历史记录原样保留(改写即伪造审计);`openspec/adr/0017` 只**追加一行**指向 `adr/0033`,正文不改;`impl_route.py` docstring 里指向 archive 归档文件的两处实路径不改
- [ ] 5.10 🔴 写明 **MUST NOT 重命名在途 plan** 并补测试:`plan_first_sha` 用 `git log --diff-filter=A`(**不跟随重命名**),改名会把完成判据窗口起点推到改名 commit ⇒ 改名前的 checkpoint 标签全部落窗口外 ⇒ 已完成 ticket 被判未完成、可能重派。用例:造一个「改名前有 task1 checkpoint、改名后跑 gate」的 fixture,断言 gate **不会**漏数 task1(或断言该场景被显式拒绝)

## 6. ADR 与术语同步

- [ ] 6.1 新增 `openspec/adr/0032-*.md`:收尾票承担聚合回归的执行点选择(含被砍候选:verify 主动执行 / 移到 code-review 之后;含接受的残余风险)
- [ ] 6.2 新增 `openspec/adr/0033-*.md`:计划文件名按轨分列 + 双存在 fail-closed(含被砍候选:全局统一新名 / 只改文档;含回滚代价)
- [ ] 6.3 `openspec/CONTEXT.md` 的 T10 术语条目改为登记两条具名规则(`T10-choice` / `review-loop-breaker`)+ "T10" 别名关系
- [ ] 6.4 `openspec/adr/0031` 追加一行指向具名规则与 design 的 scope-check 表(**正文不改**)

## 7. 一致性收尾核验 + Success Metrics 证据

- [ ] 7.1 全仓 `grep -rn "T10"`(不带 `--include`)复核:Group A 15 处措辞一致(含"按三镜+主次"限定词)、Group B 落点不再出现"T10"字样、**`sdflow-implement` 的 NEEDS_CONTEXT 尾部引用与 `impl-orchestration/spec.md` 对应 Scenario 两处的 "T10" 字样原样保留未被误删**〔spec-review-amendment H6〕
- [ ] 7.2 `grep -n "SDFLOW_TIER" sdflow-implement/SKILL.md` 确认不再是零命中(对照 C1 现状)
- [ ] 7.3 全仓 `grep -rn "superpowers-plan"`(不带 `--include`)复核:非 archive、非 issues 路径的剩余命中**全部**可逐条归因为 superpowers 轨的合法引用〔Success Metric 4〕
- [ ] 7.4 `openspec validate harden-implement-review-loop --strict --type change` 通过
- [ ] 7.5 全量 `pytest` 通过(本机须用 `/usr/bin/python3 -m pytest`)
- [ ] 7.6 **superpowers 轨回归**:临时把 config 切到 `impl-pipeline: superpowers`(或用 fixture)验证——gate 仍按旧名判 RUN_PLAN、verify 的聚合覆盖锚判"不适用"而非 gap〔评审 C2 的 dogfood 盲区,源仓默认 tickets 轨照不到〕
- [ ] 7.7 **Success Metric 1 证据**:Codex 宿主下实跑一次 `sdflow-implement` tickets-plan,记录四类 dispatch 解析到的 model id,确认全 ∈ Codex 机队缺省集、零命中 Claude 机队专名。**配额不可用时 MUST 如实记"未验证"并留 todo,MUST NOT 用 Claude 宿主的运行冒充**
- [ ] 7.8 手动核对两份 delta 归档后内容与各 SKILL.md / bundle 的实际改动逐条对得上(防 delta 与实现漂移)
