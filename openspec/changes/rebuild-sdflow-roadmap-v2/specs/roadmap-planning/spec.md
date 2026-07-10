# roadmap-planning Specification (Delta)

## ADDED Requirements

### Requirement: 三件套直写产出

roadmap 规划工作流 SHALL 将三件套（design.md / roadmap.md / task-log.md）直接写入 `openspec/roadmaps/{kebab-case-name}/`，MUST NOT 通过 OpenSpec 变更承载产出过程，MUST NOT 产出独立的 requirements.md 文件。**BREAKING 作用域限定〔spec-review-amendment SR-1〕**：三件套约定仅约束**新产出**的 roadmap 包；存量四件套包（本仓两个 + 一切消费仓存量——skill 全局 symlink 分发，接地镜证实跨仓存在 requirements.md 实质消费与四文件 MUST 场景）SHALL 视为合法历史形态，skill 续跑/更新存量包时 MUST 兼容其四件套结构（MUST NOT 报错、MUST NOT 强推迁移、MUST NOT 因存在 requirements.md 拒绝工作）。**逃生舱〔SR-7〕**：操作者显式要求保留独立 requirements.md 时 SHALL 遵从，并在 design.md 头部注明「非默认形态」。**包生命周期〔SR-3〕**：结晶落盘前 SHALL 判定同名包是否已存在——不存在 → create；存在 → 显式区分 continue（增量更新，保留既有 task-log/Review 处置）与 replan（重规划，先在 task-log 记录重规划决定再改写），MUST NOT 静默覆盖既有活文档。

#### Scenario: 产出直写目标目录

- **WHEN** sdflow-roadmap 完成讨论并进入结晶阶段
- **THEN** 三件套文件直接创建于 `openspec/roadmaps/{name}/`，全程不执行 `openspec new change`，工作区不出现 `plan-{name}` 变更目录

#### Scenario: 需求内容不落独立文件

- **WHEN** 结晶阶段需要记录痛点、目标态判据或 Non-Goals
- **THEN** 这些内容写入 design.md 的「需求与目标态」头部章，目录中不存在 requirements.md

#### Scenario: 存量四件套包续跑兼容〔spec-review-amendment SR-1〕

- **WHEN** 新版 skill 被用于更新一个含 requirements.md 的存量包（本仓或任何消费仓）
- **THEN** 按四件套既有结构继续工作，不删除、不迁移、不告警刷屏（至多一行「存量四件套形态，兼容模式」提示）

#### Scenario: 同名包已存在〔spec-review-amendment SR-3〕

- **WHEN** 结晶阶段发现 `openspec/roadmaps/{name}/` 已存在
- **THEN** 向操作者显式区分 continue / replan 并按其选择执行；replan 时在 task-log.md 先落一条重规划记录，MUST NOT 静默覆盖

### Requirement: design.md 需求与目标态伸缩头部章

design.md SHALL 以「需求与目标态」章开头，且该章 MUST NOT 占用 design 正文既有 `## N.` 数字编号序列（用无编号章名，规避历史「design §N」位置引用级联位移〔spec-review-amendment SR-15〕）。工作流/重构型项目该章 SHALL 至少包含痛点清单、目标态判据、**验收门槛**（可并入目标态判据小节的表格槽，承接旧 requirements §5 验收总纲职能〔SR-13〕）、Non-Goals 四个承载位；产品型项目 SHALL 追加受众与功能取舍小节（NFR 小节可选）；需求清单/优先级为可选占位槽（模板注释说明何时启用）〔SR-13〕。Non-Goals 中每条排除 SHALL 附可证伪假设，MUST NOT 写空泛的「超出范围」。二分判据不适用的混合/探索型项目 SHALL 走兜底：目标态判据允许写「待第 N 阶段验证」类**具名占位**（指明缺什么信息、何时补），MUST NOT 为满足格式硬编造判据〔SR-13〕。

#### Scenario: 探索型项目的兜底占位〔spec-review-amendment SR-13〕

- **WHEN** 项目目标态本身待发现（技术可行性探索类），无法起草可证伪的目标态判据
- **THEN** 判据小节写具名占位（缺失信息 + 预期补齐时点），不硬造数字，不留空泛「TBD」

#### Scenario: 工作流型项目的头部章

- **WHEN** 为技术重构 / 内部工具类项目生成 design.md
- **THEN** 文件首章为「需求与目标态」，含痛点清单、目标态判据、Non-Goals 三小节，且每条 Non-Goal 带失效条件描述

#### Scenario: 产品型项目的头部章

- **WHEN** 为含外部用户 / 商业目标的项目生成 design.md
- **THEN** 「需求与目标态」章在三小节之外追加受众、功能取舍（做/不做）小节

### Requirement: 讨论层按规模分档路由

规划工作流 SHALL 按双判据路由讨论工具，MUST NOT 依赖事前轮数预估〔grill-amendment：对齐 spec-workflow F11 口径，事前「预估轮数」不可观测〕：①**起手显性信号**——请求自带长档特征（多阶段 roadmap、明示跨天推进、议题横跨多个子系统）→ 直接 wayfinder chart 铺图；②**事中触发**——起手不明则 `/opsx:explore` 起步，讨论实际跨 session/跨天、或经历上下文压缩/重置仍未收敛 → 升级切 wayfinder。map 的 destination SHALL 表述为「三件套定稿」。wayfinder 铺图判定无雾（单 session 装得下）时 SHALL 退回 explore 路径，MUST NOT 为无雾讨论维持 map。

#### Scenario: 起手长档信号直入 wayfinder

- **WHEN** 用户请求自带长档特征（如多阶段 roadmap、明示跨天推进）
- **THEN** 以 wayfinder chart 铺图，产生 map.md 与讨论票，逐票决议后进入结晶

#### Scenario: 事中触发升级

- **WHEN** explore 起步的讨论实际跨 session/跨天、或经历压缩仍未收敛
- **THEN** 升级切 wayfinder chart，已形成的结论写入 map 的 Decisions-so-far/Notes，后续逐票推进

#### Scenario: 无雾自降级

- **WHEN** wayfinder chart 的广度 grill 未扫出雾区
- **THEN** 不建 map，退回 explore 单 session 讨论后直接结晶；广度 grill 期间已产生的讨论要点 SHALL 转录进后续 explore 讨论或 memo，MUST NOT 因判定无雾而清零〔spec-review-amendment SR-11〕；chart SHALL 先以未持久化预检判雾再落盘，若已建文件则清理并留一行痕〔SR-11〕

#### Scenario: 跨 session 恢复

- **WHEN** 长档讨论经历上下文压缩或会话中断后重启
- **THEN** 新 session 从 map 的 Decisions-so-far 与 open 票恢复讨论进度，无需人工复述已决内容

#### Scenario: 压缩前抢救与触发判定来源〔spec-review-amendment SR-5〕

- **WHEN** explore 起步的讨论检测到上下文压缩将/刚发生（map 尚未建立）
- **THEN** 先把当前推理要点 flush 进 memo（此场景下 memo 转必需），再判定是否升级 wayfinder——避免「压缩后才触发升级、能抢救的已是有损摘要」；事中触发判定 SHALL 承认双来源：人类口述（「这事聊了好几天了」）或盘面信号（memo 存在且未收敛），MUST NOT 假装新 session 能凭空判定历史轮次

#### Scenario: 宿主不可用降级〔spec-review-amendment SR-9〕

- **WHEN** 当前宿主未装载 wayfinder（接地实测：matt 套件当前仅装 `~/.claude/skills/`，Codex 宿主无 wayfinder）
- **THEN** 按当前宿主路径中立探测（MUST NOT 以 Claude 路径存在代理全局可用性）；不可用则显式提示并降级 explore+memo（长档策略回旧制），流程不阻塞；起手 SHALL 同步校验消费仓 tracker doc 及其 Wayfinding 小节在场，缺失则给出确定的初始化指引并 fail-closed 不进 wayfinder〔SR-10〕

### Requirement: footage 落盘位置与引用边界

roadmap 类 effort 的 wayfinder map 与讨论票 SHALL 落盘于 `openspec/roadmaps/{name}/footage/`（map 为 `footage/map.md`，票为 `footage/issues/<NN>-<slug>.md`）。**命名权与身份持久化〔spec-review-amendment SR-3〕**：kebab-case `{name}` SHALL 由 sdflow-roadmap 在调用 wayfinder chart **之前**确定并以固定字面量（含完整 map 路径）写入调用语——wayfinder 的「Name the destination」步只精化 destination 的表述，MUST NOT 另起 slug；map.md SHALL 在头部持久化 `Tracker root:`（本 effort 的根目录字面量）与 `Effort kind: roadmap` 两个字段，后续任何 session 的续跑/新建票 SHALL 只从 map 已存字段派生路径，MUST NOT 重新语义判别（防双根分裂）。map.md 顶部 SHALL 留一行去向说明（footage=讨论考古层、三件套不引用它）〔SR-21〕。**map 再入〔SR-3〕**：同一包二次 chart（如远期阶段补细讨论）MUST NOT 覆写既有 map——先将旧 map 归档为 `footage/map-N.md`（或在单一 map 内按日期分批追加票，二选一由 SKILL.md 钉死一种），票号延续不复用。短档可选 memo SHALL 保持包根 `memo.md` 既有落位，MUST NOT 迁移〔grill-amendment Q2：拍板 A〕。三件套 MUST NOT 引用 `footage/` 下任何内容，也 MUST NOT 引用包根 `memo.md`（两者同为讨论过程考古层，物理位置不同、引用禁令相同）；考古层中有价值的结论 SHALL 精炼后写入三件套。

#### Scenario: wayfinder 按约定落盘

- **WHEN** wayfinder 为某 roadmap effort 创建 map 或票
- **THEN** 文件落在该 roadmap 的 `footage/` 子目录下，而非 `openspec/matt/<effort>/`

#### Scenario: 续跑从 map 字段派生路径〔spec-review-amendment SR-3〕

- **WHEN** 新 session 仅凭 map.md 路径恢复某 roadmap effort 并需要新建一张票
- **THEN** 新票路径从 map 的 `Tracker root:` 字段派生（落 footage/issues/），MUST NOT 落回 `openspec/matt/<effort>/` 默认根

#### Scenario: 搁浅票重认领〔spec-review-amendment SR-16〕

- **WHEN** 某票 `Status: claimed` 但其 session 已中断（压缩/崩溃），后续 session 发现该票长期无进展
- **THEN** 允许在票尾追加一行重认领注记后改回可工作状态继续处理——claimed 票 MUST NOT 永久掉出 frontier 无人问津

#### Scenario: 误落默认根的票不被 triage 误吞〔spec-review-amendment SR-17〕

- **WHEN** 路由回退使 wayfinder 票落在 `openspec/matt/<effort>/` 且 triage/sweep 扫到带 wayfinder 词表（`Type:` research/prototype/grilling/task、`Status:` claimed/resolved）的文件
- **THEN** triage MUST NOT 对其贴五态标签或改写 Status 字段（两套状态机语义不兼容）；tracker doc 边界声明 SHALL 载明此排除规则

#### Scenario: 三件套引用检查

- **WHEN** 结晶阶段写三件套时需要引用讨论结论
- **THEN** 结论以精炼后的正文形式出现在三件套中，三件套全文不出现指向 `footage/` 或 `memo.md` 的链接、以及「详见 footage/memo」类表述

### Requirement: review 按项目野心分档

三件套完成后 SHALL 执行内容质量 review：默认单跑 `/plan-eng-review`；项目含产品/商业野心（外部用户、变现、获客类信号）时 SHALL 跑 `/autoplan` 三连审。**调用契约〔spec-review-amendment SR-7〕**：触发 review 时 SHALL 显式声明「把三件套（design/roadmap/task-log）视为一个整体 plan 来 review」并指定主入口文件（roadmap.md）——review skill 的 scope gate 与收尾门按单一 plan file 设计，缺此声明会退化为单文件审（现行 SKILL.md:265 话术的存活保证）。**跳过授权〔SR-7〕**：跳过 review 仅限人类操作者显式授权（agent 自身 MUST NOT 代决跳过），产物状态记 `review-waived` 不与已审混同；task-log.md 留「未做 review，风险自担」痕迹。**显式覆盖〔SR-7〕**：操作者显式要求覆盖默认分档（强制三连审 / 强制单审）时 SHALL 遵从并记录偏离理由。review 产出的每条 issue SHALL 在 task-log.md「Review 处置」小节标注 采纳/拒绝/延后 之一且附理由。review 依赖不可用/调用失败/无输出时 SHALL 显式留痕「未审待恢复」并提示修复步骤，MUST NOT 静默当已完成〔SR-7，失败模式表同步〕。

#### Scenario: 工作流型默认单审

- **WHEN** 技术重构类 roadmap 三件套完成且无产品野心信号
- **THEN** 触发 `/plan-eng-review` 单审（调用语含三件套整体声明），不强制 CEO/design 审

#### Scenario: 跳过 review 必留痕

- **WHEN** 人类操作者显式决定跳过 review
- **THEN** task-log.md 存在「未做 review，风险自担」条目、包状态记 review-waived，收尾 checklist 方可通过

#### Scenario: review 依赖失败不静默〔spec-review-amendment SR-7〕

- **WHEN** plan-eng-review / autoplan 未安装、调用失败或返回空
- **THEN** 显式提示 + task-log 留「未审待恢复」痕迹 + 给出修复/重试步骤，MUST NOT 把包当作已完成收尾

### Requirement: 收尾 checklist 软门

规划工作流收尾 SHALL 执行 checklist 确认五项〔spec-review-amendment SR-2/SR-4/SR-12 扩三为五〕：① task-log.md「Review 处置」小节不存在未处置条目；② 三件套相互引用完整——判定标准钉死为最小引用图：roadmap.md 每个已细化阶段至少回指 design.md 对应决策一次、task-log.md 每条完成记录关联 roadmap.md 阶段、design 头部章与决策段无同值重复（只准互相引用）；不通过时 SHALL 报出具体文件与行号，MUST NOT 笼统宣称「完整/不完整」；③ footage（如有）与 memo.md 无被三件套引用；④ **wayfinder 闭环**（如走了长档）：frontier 为空或每张未 resolve 票已显式放弃并留痕，map 标注 closed——MUST NOT 带着 open/claimed 票宣告定稿；⑤ **共享真相源核对**：本次讨论期间 CONTEXT.md / `openspec/adr/` 的新增与改动逐条对照三件套终稿——被终稿推翻的标 superseded 或回退，MUST NOT 让讨论期临时判断以定稿姿态留存全局共享文件。checklist 任一项不通过 SHALL 提示补齐后再收尾，MUST NOT 静默跳过。收尾通过后 SHALL 提示将包纳入版本控制（软提示，与 recorder 先例对齐）〔SR-12〕。

#### Scenario: 有未处置 review 条目

- **WHEN** 收尾时「Review 处置」小节存在无状态标注的条目
- **THEN** 收尾暂停并列出未处置条目，补齐处置状态后方可完成

#### Scenario: frontier 未空即要求结晶〔spec-review-amendment SR-2〕

- **WHEN** 操作者在 map 仍有 open/claimed 票时要求写三件套
- **THEN** 列出未决票清单，要求逐张 resolve 或显式放弃留痕后才结晶；操作者坚持越过时在 task-log 记录「带 N 张未决票结晶」与理由（显式越权留痕），并显示一行直接结晶依据

#### Scenario: 讨论期 ADR 与终稿冲突〔spec-review-amendment SR-4〕

- **WHEN** 结晶核对发现讨论期间 domain-modeling 写入的某 adr 条目与三件套最终结论不一致（先例：adr/0010 判据中途被目标态复核推翻）
- **THEN** 该 adr 标 superseded（或 revert）并在 task-log 记一行，MUST NOT 静默留存

### Requirement: roadmap.md 近细远雾分层

roadmap.md SHALL 只对近期 1-2 个阶段写满五节（前置条件/目标/子任务/验收标准/交付物）；近期取 1 还是 2 个 SHALL 写明选择理由（并行依赖/交付节奏）〔spec-review-amendment SR-14〕；更远阶段 SHALL 只写阶段目标一句与雾区备注——雾区备注 SHALL 写明「缺什么信息才能细化」而非空泛「待细化」〔SR-14〕，MUST NOT 预写子任务分解与验收细节。**长周期依赖例外〔SR-14〕**：远期阶段涉及长交付周期前置（采购/合规/外部契约类）时，允许且应当提前写「前置条件」一节，其余四节仍留雾。远期阶段 SHALL 在其成为下一个待实施阶段时补全五节。**补细重判〔SR-8〕**：补细内容若命中产品/商业野心信号、或改变范围/不可逆承诺/验收判据，SHALL 重新过一遍 review 分档判定（非强制重跑三连审），判定结果记 task-log。

#### Scenario: 生成时远期阶段形态

- **WHEN** 结晶阶段生成含 4 个以上阶段的 roadmap.md
- **THEN** 阶段 1-2 含完整五节，阶段 3 及以后仅含目标句与「待 frontier 到达后细化——缺 X 信息」备注

#### Scenario: frontier 推进时补细

- **WHEN** 某远期阶段的前序阶段全部交付（或残余子任务均已终局处置）、该阶段进入待实施
- **THEN** 该阶段补全五节（可经一次短讨论），补全动作与 review 分档重判结果记入 task-log.md

#### Scenario: 前序阶段部分放弃不阻塞推进〔spec-review-amendment SR-8〕

- **WHEN** 前序阶段某子任务被终局判定放弃（非未完成、非延后）
- **THEN** 该放弃记入 task-log.md 后视为已处置，SHALL 计入「前序交付」判定，不永久阻塞 frontier 推进
