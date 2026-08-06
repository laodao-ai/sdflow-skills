# spec-review-report · absorb-gstack-review

- 评审对象：`openspec/changes/absorb-gstack-review/` 四件套 @ 镜子审盘面 commit 3d28ded（评审后修订见「修订清单」，随本报告同批 checkpoint）
- 宿主/档位：host=claude · STRONG=opus（主 session 裁决）/ MID=sonnet（对抗镜、autoplan 子代理）/ LIGHT=haiku（接地镜）
- 触发判定：命中 TG-10/14/18/19/23/25（TG-27 目标态注记：由本 change 自身引入，现 catalog 无此成员，机械交集自然排除）
- 画图核验（design-diagrams）：命中 TG-10/14 → design.md「消费点依赖图」在场、经接地镜/Eng 镜逐边核验与实仓一致，未过时；无缺失图

<!-- sdflow:hr-tg v1 hit="none" declared="TG-10,TG-14,TG-18,TG-19,TG-23,TG-25" evidence="声明集与 HR-TG 子集{TG-04,06,07,08,09,16,17,26}零交集，本轮不开领域 cross-model" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

## Step1 广审（autoplan · 原生执行）

<!-- sdflow:step1-broad-review v1 mode="native" -->

autoplan 经 Skill 机制原生进主 session 执行（CEO → Eng → DX 三相位，Design 相位无 UI scope 跳过；
每相位 Claude 独立子代理 + Codex voice 双声，三次真实 `codex exec` 会话 id 记于 `gstack-review.md`
头部为侧信道佐证）。产物 `gstack-review.md` 已落盘 + checkpoint（36e67f7）。

**outside-voice 复用**：`outside_voice_guard.py` 判 `reason_code=none`（退出 0，三前置全过）→
**复用 autoplan outside voice 26 条**（三相位 codex findings），本轮不重开 design-voice。

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="26" truncated="false" -->

**站点 ↔ 后台作业记账**：本轮实际 dispatch 站点集 = ∅（design-voice 复用未派；hr-tg 交集空未派）——
与「应有锚站点集」`{design-voice}` 是两个集合，后者由上方 declared-sites 锚承载。

## 决策登记区

### [自动决策]（高置信，默认采纳、设计门可覆盖）

- **D1** autoplan mode=SELECTIVE EXPANSION（feature enhancement 缺省档）；premise ①②（gstack 依赖真实且行为冲突、五类 checklist 缺口真实）经三方读码证实接受；premise ③（「plan 发现残废」）方向证实、幅度未回测——已按 Q1 张力呈现。
- **D2** 20 条采纳 findings 已全部回写四件套（标 `[spec-review-amendment]`，见「修订清单」）——其中致命 1 条（delta 缺第二条 Requirement 修订）、高危 7 条、中危 7 条、低危 5 条。修订均为「补齐/钉死/显式化」性质，不改人已拍板的 D1/D2/D3 方向。
- **D3** 裁掉 7 条（连理由见「已裁掉区」）；defer 5 条（1 条进 issues todo、4 条为需拍板项）。

### [需拍板]（设计 HARD-GATE 一次拍板）

- **Q1 · User Challenge：是否拆 change / 补质量实证**〔Codex 三相位一致 + Claude CEO 子代理部分呼应；4 声〕
  Codex CEO/Eng/DX 一致主张：本 change 把「依赖移除」（有据）与「质量升级」（无历史回测/基准数据）混装，
  建议拆为 P0 仅依赖移除、checklist/TG/引文纪律按 shadow evaluation（20-30 归档 change 回放）另行立项，
  甚至改做 provider-neutral Review Evidence Protocol。
  **你说过的方向**：memo D1-D3 已拍板吸收方案 + 本仓拆分基准 4「一个 change 一个完整阶段结果、别拆碎」。
  **推荐：维持现 scope，不拆。** 依据：① 拆分基准 4 是你明立的仓级基准，Codex 的「按证据分立」正是
  基准 4 点名的碎片化根因形态；② 质量信号已有既有承载面（lens-metric 采纳率/独立率 + Q5 复评 +
  dogfood），无须为此新造 shadow-evaluation 基建；③ checklist 条目是数据资产，错了可低成本迭代（issues 池）。
  **代价**：系统镜——若新 Step1 真弱于 gstack，发现滞后到 retro 周期（可回退：revert 单 commit）；
  用户镜——无感知差异；开发循环镜——省一整轮 change 固定成本。主次：开发循环镜为主。
  **备选**：接受拆分（后果：两轮 change 固定成本 + 吸收件长期停在「未证实」状态）。
  **若我们错了，代价是**：吸收版 Step1 静默弱于 gstack 一段时间，靠 retro 数据事后发现。
- **Q2 · 度量可比性**〔CEO-X5/ENG-X5/DX-X6，3 声收敛〕：raw 名直接替换后新旧 Step1 在锚数据里同为
  `broad`，无法按 raw 区分。**推荐：维持 memo D3④（直接替换不共存）。** 依据：切换点是已知 change——
  retro 聚合按归档时间以本 change 为分界分段即可区分新旧（时间维度天然承载 producer 代际），无须升
  v2 加 origin 维度。**代价**：broad 桶内 autoplan 与 scope-audit 仍混计（既有事实，非本 change 引入）。
  **备选**：契约升 v2 加 origin 字段（代价：契约版本涟漪 + 所有生产者/聚合器同步改）。
- **Q3 · XSS 检查点落点**〔ENG-X7 + 对抗镜3 ADV2，2 声〕：CR-BE-02 的 XSS 例证含
  `dangerouslySetInnerHTML`/`v-html`（客户端框架），但纯前端改动只命中 TG-03、不加载 backend domain，
  且 code-checklists 无 frontend.md ⇒ 这半边例证路由不可达，「吸收后残值归零」对 XSS 一项名不副实。
  **推荐：保留 CR-BE-02 落点（服务端模板渲染 html_safe/|safe 场景），Non-Goals 补一句「客户端框架
  XSS 待 frontend domain 建立后补」。** 依据：挪 base 会让每个非前端 change 都过 XSS 项（噪声）；
  memo C7 是你确认过的映射，改落点应由你拍板。**备选**：挪 `code-review-base.md`（覆盖全但增噪）。
- **Q4 · `docs/workflow-skills/gstack-review.md` 去留**〔DX-8〕：tasks 5.3 现留白给实现期。
  **推荐：现在拍板删除**（code-review 零 gstack 后该详解文档无编排器引用，DOC-1 精神）。备选：保留并
  改述为「未使用第三方 skill 参考」。

### [已裁掉区]（反静默压制：原始发现 + 裁掉理由，供复核「裁得对不对」）

- **X1**〔grounding F2〕memo C4 引用主 spec:68 行号将随归档漂移 → 裁掉：纪要锚定拍板时盘面，行号引用属当时事实，纪要惯例不回改。
- **X2**〔grounding F4〕outside-voice-reuse-guard spec 不在 bundle 内 → 裁掉：接地镜自证无机械问题，C1 表述本就正确。
- **X3**〔CEO-C2〕五态审计与 sdflow-done verify 重叠未做成本论证 → 裁掉：重叠是分层设计意图（informational shift-left 提早发现 + verify 终审权威），F-F 修订已把边界钉死（不勾 tasks、不替代 verify）。
- **X4**〔CEO-X2〕「Step1 替代非能力等价（抓不到计划本身错误）」→ 裁掉：「计划本身错误」由阶段二设计评审（本流程）负责，Step1 定位即 scope/完成度地板，广义代码审由 Step2 多镜承载——按目标态分工无缺口。
- **X5**〔CEO-X4〕「自持化=换成难观测宿主行为依赖」→ 裁掉：自报锚的诚实边界既有体系已显式声明（§0.0 残余语义层 + host 分组事后可发现性），非本 change 新增面。
- **X6**〔CEO-X10〕外部竞争风险（官方 code review 产品化吞没本地体系）→ 裁掉（一行留痕）：仓库级战略议题，超本 change scope；供 roadmap 参考，不改四件套。
- **X7**〔grounding F5〕「并入 CR-BE-02」vs「检查点追加」措辞差 → 裁掉：同义（design 3.2「检查点追加」为准），非实质差异。

### 低置信项（一行带过，不静默滤）

- 〔对抗镜1 ADV5〕gstack Search-before-recommending 能力去留——已并入 F-N 的 Non-Goals 显式放弃句处理。
- 〔CEO-C4〕spec-review 侧姊妹依赖 defer 无优先级信号——已有 tasks 6.3 todo 承载，优先级由 issues 池分诊。
- 〔CEO-C5〕新 checklist 措辞自身无复评检查点——lens-metric 采纳率天然覆盖（checklist 产出的 finding 被采纳与否可见），不另设机制。

## 各镜 findings 与裁决（合并去重后 32 条：采纳 20 · 裁掉 7 · defer 5）

> 完整原始 findings 见 `gstack-review.md`（广审层 26+19 条）与本节合并池。命中镜集合已折叠到
> canonical lens（broad=autoplan 三相位 Claude 子代理、outside-voice=autoplan codex 三 voice（复用）、
> adversarial=对抗镜×3、grounding=接地镜）。

**采纳（已全部回写产物）**：

| # | finding | 镜集合 | 置信/严重度 | 回写落点 |
|---|---|---|---|---|
| F-A | 主 spec 第二条 Requirement「广审层原生执行」（spec.md:684-693）点名 gstack /review + mode=native\|simulated，delta 未触碰 ⇒ 归档后 living spec 自相矛盾 | adversarial（独家） | 高/**致命** | delta 补第二段 MODIFIED（收窄为 spec-review 侧） |
| F-B | Step1 异步派发 × Step2 EXEMPT 前置判定竞态：迟到的 scope-drift 揭穿换不回已跳过的多镜，spec 安全网空转（旧同步设计下成立、新设计拆掉时序前提） | adversarial×3 独立收敛 | 高/高 | delta Step2 bullet + design D1：EXEMPT 候选阻塞、非白名单才并行 |
| F-C | 能力探针定义在 Step2 内部而 Step1 dispatch 需其结果，且 fanout-capability 锚每轮恰一条 ⇒ 双锚被拦/时序倒挂/静默重排三难 | broad+voice+adversarial（5 声） | 高/高 | delta Step1 bullet + design D1 + tasks 1.1：探针挪 Step0、共用一次结果 |
| F-D | 双向 bundle skew：新 SKILL（symlink 瞬时）× 消费仓旧 pin tools（惰性 update）⇒ 每轮评审末步 `mirrors-unknown-token`/未知 raw 名 fail-closed，整轮成本报废、报错无修法；既有 skew 探测只探旧信号 | broad+voice+adversarial | 高/高 | design「skew 探测信号扩展」+ tasks 2.5（两新信号 + 报错文案带 `sdflow-init update` 指引） |
| F-E | design/tasks 把 `scope-audit` 写进 roster.lens——契约 schema 规定 roster MUST canonical、raw 只进 hits[].raw；照字面实现 emitter 当场 EmitError | adversarial（独家，逐行读码证实） | 高/高 | design §3 + tasks 1.4 改述 |
| F-F | 五态审计：PARTIAL/NOT DONE 无判据、finding 类型枚举漏 CHANGED、无逐 task 证据表、与 verify 关系未钉死（NOT DONE 可被置信过滤吞掉） | broad+voice（5 声） | 高/高 | delta 五态 Scenario + design D1 输出段 + tasks 1.2 |
| F-G | Step1 审的是 Step4 自动修**前**的 diff，修复 diff 的越界改动无 scope 复核 | voice+adversarial | 中/中 | design：Step4 后复审一轮纳入 scope-drift 维度 |
| F-H | 单行引文一刀切误杀缺失/跨文件/时序类 finding，与 CR-11「必须读 diff 外代码」自相矛盾；措辞疑似波及 Step1 | voice（3 声） | 高/高 | delta ADDED Requirement + design §6：可复核证据包 + 仅约束 Step2 |
| F-I | TG-27：「锚行 parse」例证正中本仓自身工具链（高频假阳污染 Q5 样本）；TG-27→llm.md 消费规则未写进 SKILL 领域选择段（llm.md 孤儿风险）；spec-checklists 侧缺位未注明 | broad+voice | 高/高 | design §5 + tasks 1.4/3.4：排除句、消费行、code-review-only 注记 |
| F-J | `_FANOUT_MIRRORS` 单常量身兼合法集+计数集，naive 加 broad 污染计数集 | broad+adversarial（5 声） | 高/中 | tasks 2.2 点破拆两常量 |
| F-K | dogfood 打在运行 checkout 旧代码（本机 readlink 实测）⇒ Success Metrics 假绿 | broad+adversarial（实测复现） | 高/中 | tasks 6.4 补全局窗口前置步 |
| F-L | golden 无 mode="subagent" 用例，「lint 不校验 mode」不变量无回归守护 | broad | 高/中 | tasks 2.3 扩为四用例 |
| F-M1 | docs/workflow-console.html 多处 gstack 叙述未列入 P2 | broad | 高/中 | tasks 5.3 点名 + grep 扫描含 .html |
| F-M2 | README「选用规则」示例块未同步 TG-27 行 | broad | 高/低 | tasks 3.5 新增 |
| F-M3 | TG-27 无 spec-checklists 侧 domain 未注明（frontend 反向先例） | broad | 高/低 | design §5 + tasks 3.4 行内注 |
| F-M4 | Success Metrics「历史注记除外」三处口径不一致（tasks 6.2 丢豁免、design 承诺 DOC-1 零残留） | adversarial | 高/低 | proposal + tasks 6.2 统一为 DOC-1 严格口径 |
| F-M5 | 「gstack 不在场」Scenario 无对应验证任务（静态 grep 证成的推理未显式化） | adversarial | 中/低 | tasks 6.2 显式化证明方式 |
| F-N | gstack Prior Learnings（本机有真实学习记录）与 Search-before-recommending 两项附带能力被静默丢弃、未过五问 | adversarial（独家） | 中/中 | proposal Non-Goals 显式放弃句 |
| F-O1 | gstack SKILL 实为 1852 行（proposal 写 1853） | grounding | 高/低 | proposal 校正 |
| F-O2 | needle 新措辞未明确 | grounding | 中/低 | tasks 2.4 补口径 |

**defer**：孤儿副本清理（→ tasks 6.3 todo ③）+ Q1-Q4（上方需拍板区）。

## 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="12" 采纳="11" 裁掉="0" defer="1" 独立="6" sev="致1/高4/中4/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="14" 采纳="10" 裁掉="1" defer="3" 独立="4" sev="致0/高4/中4/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="5" 采纳="2" 裁掉="3" defer="0" 独立="2" sev="致0/高0/中0/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="12" 采纳="6" 裁掉="3" defer="3" 独立="1" sev="致0/高5/中1/低0" -->

（emitter exit 0 产出；分类正确性 / roster 完备性 / findings 誊写准确仍是主 session 信任边界；
门前草稿值，拍板回写时按 SR-M 最终化。）

## 修订清单（[spec-review-amendment]，已全部落盘）

- `specs/spec-workflow/spec.md`：Step1 bullet 探针 Step0 化；Step2 bullet 守卫时序钉死；五态 Scenario 判据/落盘物/verify 关系；ADDED 引文纪律证据包 + Step2-only；**新增第二段 MODIFIED Requirement「广审层原生执行」收窄为 spec-review 侧**
- `design.md`：D1 dispatch 时序钉死；五态判据 + 逐 task 表 + verify 关系 + Step5 复审口径；§3 roster 契约修正 + skew 探测信号扩展；§5 TG-27 排除句/消费行/code-review-only；§6 证据包口径；Risks 双向 skew 改述
- `tasks.md`：1.1 探针挪位；1.2 五态补齐；1.4 raw 落点修正 + TG-27 消费行；2.2 拆常量；2.3 四用例；**新增 2.5 skew 信号**；2.4 needle 口径；**新增 3.5 README 示例块**；3.4 排除句；5.3 console.html；6.2 口径统一 + 证明显式化；6.3 第三条 todo；6.4 全局窗口前置
- `proposal.md`：1852 行校正；Success Metrics DOC-1 严格口径；Non-Goals 补 Prior Learnings/Search-before-recommending 显式放弃

## 反馈回路免责声明

本报告只落锚，不做聚合、不做复评判断、不主动 surfacing——跨 change 锚聚合与镜效能复评一律由
`/sdflow-retro` 只读聚合；是否保留/降采样/收紧触发/淘汰某镜一律人决。

## 收敛口

**建议进设计 HARD-GATE**：致命/高危 findings 已全部以 amendment 收口（F-A 的 delta 补齐消除归档自相矛盾、
F-B/F-C 的时序钉死消除三对抗镜收敛的结构性竞态、F-D 的 skew 信号消除消费仓必炸窗口）；余下 Q1-Q4 为
方向级拍板项（推荐已附），不阻塞批准。人工过本报告：勾 Q1-Q4 → 批准设计 →（若有二次修订，先单独
checkpoint 再回写锚）→ 拍板回写 `ship-gate.design_approved` + `reviewed_sha` frontmatter → `/clear` → `/sdflow-ship`。

⚠️ 拍板前流程纪律：本报告的 findings 针对镜子审时盘面（3d28ded）；amendment 已产出新盘面（随本报告
checkpoint）。amendment 均源自本轮镜审结论本身（增量已被本报告覆盖），若你在拍板前**另行**修改四件套，
须先跑窄复核（只审增量）再拍板。
