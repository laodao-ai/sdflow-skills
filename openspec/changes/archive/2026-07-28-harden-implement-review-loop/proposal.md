## Why

`sdflow-implement` 是阶段三 tickets 管线唯一没有做"宿主/档位解析"的编排 skill——`implementer`/Standards 轴/Spec 轴/fix 子代理全部继承主 session 当前模型。这不只是架构不对称：`model-tiers` Requirement 明写"MUST NOT 在 Codex 宿主下把 Claude 机队的模型名用于 Codex 机队子代理",而没有第零步就拿不到本机队档位 ⇒ **Codex 宿主下 `sdflow-implement` 是一个跨机队正确性缺口**,不是风格问题〔spec-review-amendment L7/X1〕。

同时,T10 三级决策协议在多个落点被当作"同一件事"复述,但实际比对发现 `sdflow-implement` 借用的"熔断仲裁"场景与其余落点的"≥2 方案选择"场景触发条件不同,继续沿用同一个标签会让未来编辑者误判"改一处等于改全部"。**注意本次拆标签只消除"跨语义误改"这一类风险;"同语义多落点漏改"由复述架构本身导致,本次不做单一源化 ⇒ 该风险原样保留,且 Group A 落点重新盘点后数量不降反升**〔spec-review-amendment H13——原措辞把两件事混为一谈〕。

此外,每 ticket "结束前跑一次全套件"未区分测试粒度,导致每票都要付全量 e2e/集成测试成本,而链路里又没有任何一步真正执行"全部票完成后的聚合回归",两头都不对。

最后,tickets 轨产出的计划文件沿用了 superpowers 轨的文件名 `superpowers-plan.md`——这是 superpowers-only 时期的历史遗留,在 tickets 轨里是错名〔spec-review-amendment · 用户拍板〕。

## What Changes

按优先级标注〔spec-review-amendment M13〕:

- **[P0]** 给 `sdflow-implement` 补齐"第零步:宿主/档位解析"(清脏→预检→捕获退出码→eval 后校验四步),`implementer`/Standards 轴/Spec 轴/fix 子代理声明为 mid 档。对齐目标是 `sdflow-code-review`/`sdflow-spec-review` 的**四步语义**(不是逐字复制,见下条);跨文件交叉引用一律用**具名锚点**,MUST NOT 用"本步第 N 项"这类依文件本地结构派生的序号。
- **[P0]** 修 `sdflow-done/SKILL.md` 的 `### 0.4` 裸 `eval`(现状无清脏/预检/退出码捕获/eval 后校验,正是模板明文警告的 V1 陷阱),升级为同一套四步——否则本次新增的是**第四份**已知不安全拷贝〔spec-review-amendment Q4 拍板:一起修〕。
- **[P0]** 新增机械 parity 守卫(`hack/tests/test_tier_resolution_parity.py`,仿 `test_async_branch_parity.py`),对四个 skill 的第零步归一化核心段做逐字节比对——"复制是必要的,但复制不能靠手"。
- **[P0]** `sdflow-implement` 的 Codex 宿主子代理授权:`AGENTS.md`/`CLAUDE.md` 的授权段现明文"仅限 `sdflow-spec-review`/`sdflow-code-review` 两处",而第零步会让 Codex 宿主成为字面支持的路径 ⇒ 补进授权范围,并同步 `sdflow-init/tests/test_codex_subagent_authorization.py`〔spec-review-amendment H11〕。
- **[P0]** 测试范围分层 + 强制收尾票:每 feature ticket 的测试执行范围从"结束前跑一次全套件"收窄为"单元测试 + 本票声明的 e2e 场景 + 本票 `Blocked-by` 链上模块的集成测试",MUST NOT 跑**与本票无依赖关系**的集成/e2e〔spec-review-amendment Q3 拍板:放宽绝对禁令,保留中间档〕;出票模式新增一张强制的"实现验证"收尾 ticket(`Blocked-by` 全部功能票,不计入 3–6 张垂直切片预算),运行聚合套件并走标准 implementer + 双轴审 + fix 循环。
- **[P1]** T10 协议拆成两条**具名**独立规则,不再共用同一个标签〔spec-review-amendment M10:给运行时消歧 aid〕:
  - **`T10-choice`**(Group A,"遇 ≥2 方案自动选")的"派对抗镜复核"步升级为 strong 档仲裁,落点见 design 的 scope-check 表。
  - **`review-loop-breaker`**(Group B,`sdflow-implement` 熔断仲裁)独立成文,不再引用"T10"标签;身份键改为**跨轮稳定指纹**(行号只作定位),三级处置改为**互斥终态**〔spec-review-amendment H3/H4〕。
- **[P1]** tickets 轨的计划文件更名为 `tickets.md`;superpowers 轨保持 `superpowers-plan.md`。gate 与 route helper 改用共享 resolver 探测两个文件名,**两个同时存在 ⇒ fail-closed UNKNOWN**(不可判,不猜)。文件名不参与轨道路由判定(路由权威仍是 config 键 + frontmatter marker),只用于定位〔见 `adr/0033`〕。
- **[P2]** `spec-workflow` 的"模型档位映射(model-tiers)"Requirement 里补上 `sdflow-implement`;`sdflow-ship/SKILL.md` 的"经各被链序调度的子 skill(spec-review/code-review/done)各自 eval"枚举同步补 implement〔spec-review-amendment M12〕。

## Capabilities

### New Capabilities

(无新增 capability)

### Modified Capabilities

- `impl-orchestration`: 新增"`sdflow-implement` 档位解析与声明"Requirement;"每 ticket 双轴审加修复环"Requirement 的熔断段改为 `review-loop-breaker` 具名规则(稳定身份键 + 互斥终态 + strong 仲裁);"执行模式串行工作 frontier"Requirement 补测试执行范围;"出 ticket 模式产出 tracer-bullet ticket"Requirement 补强制收尾票、聚合套件发现契约、计划文件名与收尾票的机械校验。
- `spec-workflow`: "阶段三过设计门后连续自动跑到 merge"Requirement 的 `T10-choice` ②步补 strong 档;"模型档位映射(model-tiers)"Requirement 补 `sdflow-implement`;计划文件名分轨语义同步。

## Impact

- **指令文本**:`sdflow-implement/SKILL.md`(第零步 + 四类 dispatch 档位声明 + `review-loop-breaker` 段改写 + Group A 四处升 strong + 测试范围改写 + 收尾票规则 + 计划文件名)、`sdflow-done/SKILL.md`(`### 0.4` 裸 eval 升四步 + verify 引用收尾票锚 + 计划文件名)、`sdflow-ship/SKILL.md`(`T10-choice` 复述补 strong + 子 skill 枚举补 implement)、`sdflow-code-review/SKILL.md`(`T10-choice` ②步复述补 strong)、`sdflow-init/assets/workflow/workflow.md`(canonical 定义补 strong + 计划文件名)、`sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`、`sdflow-init/assets/workflow/prompts/step6-writing-plans.md`(明确该 prompt 只管 superpowers 轨)、`openspec/workflow/WORKFLOW-GUIDE.md`(仓内托管副本同步)。
- **项目指令**:`AGENTS.md` / `CLAUDE.md` 的"Codex 子代理授权"段补 `sdflow-implement`〔H11〕。
- **脚本**(修正原"不改动任何脚本逻辑"的声称——本次**确有**脚本改动)〔spec-review-amendment Q5/Q6/H12 + 改名〕:
  - `sdflow-ship/scripts/ship_gate.py`:计划文件名 resolver(探两名 / 双存在 fail-closed)+ **第四道 plan 校验**(tickets 轨下 MUST 恰含一张收尾票且 `Blocked-by` ⊇ 全部功能票号)。
  - `sdflow-implement/scripts/impl_route.py`:同一 resolver(单一源 import,MUST NOT 手抄第二份)。
  - 测试:`sdflow-ship/tests/test_gate_impl_progress.py`、`sdflow-ship/tests/test_gate_freshness.py`、`sdflow-implement/tests/test_impl_route.py`、`hack/tests/test_checkpoint_slug_coverage.py`、`hack/tests/test_harden_sdflow_spec_followup_closure.py` 同步;新增 `hack/tests/test_tier_resolution_parity.py`。
- **spec delta**:`openspec/specs/spec-workflow/spec.md`、`openspec/specs/impl-orchestration/spec.md`。
- **ADR**:已落 `adr/0031`(T10 标签拆分);本次新增 `adr/0032`(收尾票承担聚合回归的执行点选择)、`adr/0033`(计划文件名按轨分列)〔spec-review-amendment H15:ADR 判定口径统一,见 design「ADR 判定」节〕。
- **文档**:`docs/workflow-overview.md`(含 `:257` 的 T10 并列定义,属 Group A 落点)、`docs/workflow-map.md`、`docs/workflow-map.html`、`docs/workflow-console.html`、`docs/criteria-mechanization-tracker.md`、`docs/workflow-skills/{impl-pipeline-matt-vs-superpowers,superpowers-writing-plans,superpowers-subagent-dev}.md`、`openspec/INDEX.md`、`openspec/CONTEXT.md`(T10 术语条目改为两条具名规则)。
- **不改**:`openspec/changes/archive/**` 与 `openspec/issues/**` 的历史记录**原样保留**(它们记录的是当时事实,改写即伪造审计);`openspec/adr/0017` 只**追加一行**指向 `adr/0033`,正文不改。
- **下游影响**:消费仓拉取新版 bundle 后,tickets 轨执行模式多出一张"实现验证"收尾票,并改用 `tickets.md`。**部署渠道见 design 的 Migration Plan——skill 本体走 `setup.sh`,不是 `sdflow-init update`**〔spec-review-amendment H5〕。

## Success Metrics

原三条全是**文本存在性检查**(grep 到变量 / 措辞一致 / plan 含收尾票),三项改动零收益也能全绿〔spec-review-amendment H8〕。改为可证伪口径:

1. **跨机队正确性(D1 的真实收益)**:在 Codex 宿主下实跑一次 `sdflow-implement` tickets-plan,四类 dispatch 解析到的 model id 全部 ∈ Codex 机队缺省集,零命中 Claude 机队专名(opus/sonnet/haiku)。证据 = 该次运行的 impl-report 中 `$SDFLOW_TIER_MID` 实解值。**Codex 配额不可用时 MUST 如实记"未验证"并留 todo,MUST NOT 用 Claude 宿主的运行冒充。**
2. **parity 守卫非恒真锚**:`test_tier_resolution_parity.py` 绿,且**定点删除四个 skill 中任一处第零步的任一步 → 该测试必红**(两种恒真成因都要排除:门被别的断言满足 / 压根没用例走到那行)。证据 = 变异实测记录。
3. **收尾票产生真实执行证据**:本 change 自身走 tickets 轨,其收尾票的 impl-report 含「聚合套件命令原文 + 退出码 + 测试时 `git rev-parse HEAD`」三元组;`ship_gate` 第四道校验对"删掉收尾票的 plan"必判非 0。
4. **改名无残留**:非 archive、非 issues 路径下 `grep -rn "superpowers-plan"` 的剩余命中**全部**可逐条归因为两类之一——① superpowers 轨的合法引用;② 明确标注为历史记录的引用(`adr/0017` 的正文、脚本 docstring 里指向归档文件的实路径)。**tickets 轨零命中。**

## Non-Goals

- 不把 `T10-choice` 的"各处复述"架构重构成真正的单一源 + 指针引用——继续复述,只是拆清楚哪些复述描述的是同一件事、哪些不是。**该架构导致的"同语义多落点漏改"风险本次不消除**(已记 todo)。
- 不做任务复杂度动态选 implementer 档位(D4)。
- 不改动 design D8"implementer 档位钉死 mid"的既有试点期变量控制决定本身。
- 不追加"熔断前先 resume 原 implementer 做一次同档重试"这类 superpowers 式额外中间步。
- **不改动 `sdflow-done` verify 的"纯审计"定位**:verify 仍不主动执行测试,只引用收尾票的证据锚(且该锚**按管线条件化**,见 C2 修正)。
- **不修改既有 Requirement「verify 为收尾最终门,位于所有修复之后」**〔Q2 拍板〕:收尾票是**实现期**聚合回归门,不是最终完整性门;verify 仍在 `sdflow-done`、仍在所有修复之后,该 Requirement 未被触碰。code-review 之后的修复由 code-review 自身的保障机制覆盖;由此产生的"收尾票锚点相对 code-review 修复而言不是最新"是**已知且接受的残余风险**,见 `decision-memo.md`「接受的边角」。
- 不把 superpowers 轨的计划文件一并改名(叫 `tickets.md` 语义不通),不做"用文件名替代 frontmatter marker 做轨道路由"的机制改造。

## Compliance

N/A——本次改动为指令文本、delta spec 与确定性脚本/测试,不涉及数据合规、隐私或安全边界变化。
