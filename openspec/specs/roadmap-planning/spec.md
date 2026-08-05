# roadmap-planning Specification

## Purpose
TBD - created by archiving change rebuild-sdflow-roadmap-v2. Update Purpose after archive.
## Requirements
### Requirement: 三件套直写产出

roadmap 规划工作流 SHALL 将三件套（design.md / roadmap.md / task-log.md）直接写入 `openspec/roadmaps/{kebab-case-name}/`，MUST NOT 通过 OpenSpec 变更承载产出过程，MUST NOT 产出独立的 requirements.md 文件。**BREAKING 作用域限定〔spec-review-amendment SR-1〕**：三件套约定仅约束**新产出**的 roadmap 包；存量四件套包（本仓两个 + 一切消费仓存量——skill 全局 symlink 分发，接地镜证实跨仓存在 requirements.md 实质消费与四文件 MUST 场景）SHALL 视为合法历史形态，skill 续跑/更新存量包时 MUST 兼容其四件套结构（MUST NOT 报错、MUST NOT 强推迁移、MUST NOT 因存在 requirements.md 拒绝工作）。**缺件存量包〔spec-review-amendment SR-25〕**：存量包还存在**第三种形态——只有 `roadmap.md`、缺 design.md / task-log.md 的单文件包**（本仓 `openspec/roadmaps/issues-triage-2026-08/` 与 archive 下两包即此形态）。该形态同样 SHALL 视为合法历史形态：续跑时 MUST NOT 报错、MUST NOT 因缺件拒绝工作；收尾 checklist ② 的「三件套相互引用完整」对缺失文件 SHALL 判为不适用而非不通过，并输出一行「存量缺件包（缺 X），引用完整性仅对现存文件核验」提示；操作者要求补齐时按 continue 路径生成缺失文件。**逃生舱〔SR-7〕**：操作者显式要求保留独立 requirements.md 时 SHALL 遵从，并在 design.md 头部注明「非默认形态」。**包生命周期〔SR-3 · 本 change 判定时点前移〕**：同名包 create / continue / replan 判定 SHALL 在**相位 B 起手**完成（走拷问路径时）或**生成落盘前**完成（直接生成路径）——不存在 → create；存在 → 显式区分 continue（增量更新，保留既有 task-log/Review 处置）与 replan（重规划，先在 task-log 记录重规划决定再改写），MUST NOT 静默覆盖既有活文档。

#### Scenario: 产出直写目标目录

- **WHEN** sdflow-roadmap 完成讨论并进入生成阶段
- **THEN** 三件套文件直接创建于 `openspec/roadmaps/{name}/`，全程不执行 `openspec new change`，工作区不出现 `plan-{name}` 变更目录

#### Scenario: 需求内容不落独立文件

- **WHEN** 生成阶段需要记录痛点、目标态判据或 Non-Goals
- **THEN** 这些内容写入 design.md 的「需求与目标态」头部章，目录中不存在 requirements.md

#### Scenario: 存量四件套包续跑兼容〔spec-review-amendment SR-1〕

- **WHEN** 新版 skill 被用于更新一个含 requirements.md 的存量包（本仓或任何消费仓）
- **THEN** 按四件套既有结构继续工作，不删除、不迁移、不告警刷屏（至多一行「存量四件套形态，兼容模式」提示）

#### Scenario: 缺件存量包续跑与收尾判定〔spec-review-amendment SR-25 · 窄复核 NR-8〕

- **WHEN** 续跑一个只有 `roadmap.md`、缺 design.md / task-log.md 的存量包
- **THEN** 按现存文件继续工作、不报错、不因缺件拒绝；收尾 checklist ② 的「三件套相互引用完整」对缺失文件判**不适用**（而非不通过），并输出一行「存量缺件包（缺 X），引用完整性仅对现存文件核验」

#### Scenario: 同名包已存在〔spec-review-amendment SR-3〕

- **WHEN** 相位 B 起手（或直接生成路径的落盘前）发现 `openspec/roadmaps/{name}/` 已存在
- **THEN** 向操作者显式区分 continue / replan 并按其选择执行；replan 时在 task-log.md 先落一条重规划记录，MUST NOT 静默覆盖

### Requirement: design.md 需求与目标态伸缩头部章

design.md SHALL 以「需求与目标态」章开头，且该章 MUST NOT 占用 design 正文既有 `## N.` 数字编号序列（用无编号章名，规避历史「design §N」位置引用级联位移〔spec-review-amendment SR-15〕）。工作流/重构型项目该章 SHALL 至少包含痛点清单、目标态判据、**验收门槛**（可并入目标态判据小节的表格槽，承接旧 requirements §6 验收总纲职能〔SR-13〕）、Non-Goals 四个承载位；产品型项目 SHALL 追加受众与功能取舍小节（NFR 小节可选）；需求清单/优先级为可选占位槽（模板注释说明何时启用）〔SR-13〕。Non-Goals 中每条排除 SHALL 附可证伪假设，MUST NOT 写空泛的「超出范围」。二分判据不适用的混合/探索型项目 SHALL 走兜底：目标态判据允许写「待第 N 阶段验证」类**具名占位**（指明缺什么信息、何时补），MUST NOT 为满足格式硬编造判据〔SR-13〕。

#### Scenario: 探索型项目的兜底占位〔spec-review-amendment SR-13〕

- **WHEN** 项目目标态本身待发现（技术可行性探索类），无法起草可证伪的目标态判据
- **THEN** 判据小节写具名占位（缺失信息 + 预期补齐时点），不硬造数字，不留空泛「TBD」

#### Scenario: 工作流型项目的头部章

- **WHEN** 为技术重构 / 内部工具类项目生成 design.md
- **THEN** 文件首章为「需求与目标态」，含痛点清单、目标态判据、Non-Goals 三小节，且每条 Non-Goal 带失效条件描述

#### Scenario: 产品型项目的头部章

- **WHEN** 为含外部用户 / 商业目标的项目生成 design.md
- **THEN** 「需求与目标态」章在三小节之外追加受众、功能取舍（做/不做）小节

### Requirement: 讨论层三态路由

规划工作流 SHALL 在相位 A 收束时执行**两关独立**检查——gate-0（讨论充分度五项）与**商业化信号**检查（信号词表：外部用户、变现、获客、「用户画像未定」、「要不要做这个产品」；与 review 分档共用同一张词表）——并按三态路由进入后续相位，判定依据 SHALL 在对话中**单独一行显式陈述**（判定点①，不埋进长消息）；**留痕时点**〔spec-review-amendment SR-26〕：相位 A 收束时 `{name}` 尚未确定、包目录尚不存在，故该行 SHALL 在包目录建立后（B 起手第三步，或直接生成路径的落盘时）**补记**进 task-log.md，MUST NOT 要求在包尚不存在时写入该文件。**通过阈值〔impl-review-fix〕**：gate-0 SHALL 五项全部满足方算「过」，任一项不满足即「未过」（走三态路由第③态），MUST NOT 以「多数项通过」判过。三态路由为：① gate-0 通过 ∧ 无商业化信号 → 直接进入相位 C 生成；② gate-0 通过 ∧ 商业化信号命中 → 相位 B 裁剪到拷问维度①（需求真实性，startup 味逼问）后进入生成；③ gate-0 未通过 → 相位 B 按信号裁剪七维拷问后进入生成。MUST NOT 依赖事前轮数预估；MUST NOT 因 gate-0 五项全过而免除商业化信号检查（gate-0 验讨论充分度、不验需求真实性，两关独立）。想法尚未成形（需发散探索）不在本路由内：SHALL 建议先 `opsx:explore` 发散、成形后再触发本 skill（上游可选步，非 skill 内部分支）。拷问七维 = ①需求真实性 ②现状分析 ③阶段划分压力测试 ④最小可行首阶段 ⑤架构路线对比 ⑥术语/概念澄清 ⑦前提质疑；裁剪基准：技术重构 → ②③④⑤⑦ 为主；新产品/新项目 → ①②④⑤⑥⑦；商业化信号命中 → ① 加重；**类型不匹配以上两类时的兜底〔impl-review-fix〕**：按「存量演进 vs 从零起步」二选一归类——已有系统/工具/文档的演进（内部工具、基础设施、博客/文档工程等）→ 按技术重构行；从零起步的新事物 → 按新产品/新项目行，归类结果 SHALL 写进判定点①留痕行。信号词表与裁剪基准 SHALL 内联于 SKILL.md（skill 为独立分发单元）。**操作者覆盖**〔spec-review-amendment SR-41〕：操作者显式要求增删本次拷问维度（如「这次不用问⑦」「把⑤也加上」）时 SHALL 遵从，并把偏离与理由记入判定点①的留痕行——与 review 分档的「显式覆盖」先例同构。

#### Scenario: gate-0 全过且无商业化信号

- **WHEN** 相位 A 收束时 gate-0 五项通过且商业化信号词表无一命中
- **THEN** 显式陈述「gate-0 五项已过 ∧ 无商业化信号，直接生成」一行并留痕 task-log.md，跳过相位 B 直接进入生成

#### Scenario: gate-0 全过但商业化信号命中

- **WHEN** gate-0 五项通过，但请求含外部用户/变现/获客类信号
- **THEN** 进入相位 B 且拷问裁剪到维度①（需求真实性），MUST NOT 以「讨论已充分」为由跳过该维度；维度①收敛后进入生成

#### Scenario: gate-0 未过的技术重构

- **WHEN** 技术重构类请求 gate-0 任一项未通过、无商业化信号
- **THEN** 进入相位 B，以维度②③④⑤⑦为主拷问（维度①⑥按需），收敛后进入生成

#### Scenario: gate-0 未过的新产品/新项目〔spec-review-amendment SR-34〕

- **WHEN** 新产品 / 新项目类请求 gate-0 任一项未通过
- **THEN** 进入相位 B 并跑**六个维度 ①②④⑤⑥⑦**（③ 阶段划分压力测试按裁剪基准对该类型不选入），MUST NOT 因「技术判断已清楚」而进一步只跑技术侧维度〔窄复核 NR-4：原文「跑满七维中的 ①②④⑤⑥⑦」自相矛盾，六维不是七维〕

#### Scenario: gate-0 未过且商业化信号命中时维度①加重〔spec-review-amendment SR-34〕

- **WHEN** gate-0 未通过（落在第③态）**且**商业化信号命中
- **THEN** 除按类型裁剪的维度外，维度①（需求真实性）SHALL 加重逼问——「①加重」跨②③两态共同适用，MUST NOT 只在第②态生效

#### Scenario: 路由判定显式留痕

- **WHEN** 三态路由任一判定做出（含「跳过相位 B」类判定）
- **THEN** 判定依据在对话中单独一行显式陈述（不埋长消息），并在包目录建立后补记进 task-log.md（含本次实际选入的拷问维度子集，供事后审计裁剪是否真的发生）〔spec-review-amendment SR-26 · SR-36〕

### Requirement: B 相位拷问与增量落盘

进入相位 B SHALL 起手完成三步：① 确定 kebab-case `{name}`；② 判定同名包 create / continue / replan（**包生命周期判定前移至 B 起手**）；③ 按判定结果落盘 memo.md——**create**（目录不存在）：建 `openspec/roadmaps/{name}/` 并落盘**全新**草稿 memo.md（头部含包名、日期、`状态：DRAFT`）；**continue / replan**（目录已存在）〔impl-review-fix〕：MUST NOT 重建、MUST NOT 覆盖既有 memo.md——它承载着此前累积的承重结论 / `## 未决项` / `[确认]` 全局写入记录，是本包的历史存档，覆盖即永久丢失；既有 memo 存在 ⇒ 续接追加本轮结论，并把头部状态位改回 `状态：DRAFT`（若此前为 `FINAL`），另起一行记明本轮重入原因与日期；既有 memo 不存在（存量包或前次中断）⇒ 按 create 落盘新 memo，并在首条记录注明「本包此前无 memo，自本轮起建立」。

**memo 头部与定稿标记〔spec-review-amendment SR-2 · 窄复核 NR-1 订正写入时机〕**：memo.md 头部 SHALL 记包名 + 日期，并 SHALL 保留一行**状态标记** `状态：DRAFT` / `状态：FINAL`——**该行即「定稿标记」判据的唯一实现载体**，重入探测与本 Requirement 全部「未定稿」表述一律以它为准。**写入时机**：B 起手写 `DRAFT`；**该包 `memo.md` 存在时**〔impl-review-fix〕，🔴 **`FINAL` SHALL 只在收尾 checklist 四项全过之后写入**（附定稿日期），**MUST NOT 在 B 收敛时就改写**——B 收敛之后还要走相位 C 生成与 review 处置，此间中断（如三件套只写出 1-2 个）若已置 `FINAL`，重入探测（只扫 `DRAFT`）就再也认不出这个半成品包。换言之 `DRAFT` 覆盖「B 拷问中 / C 生成中 / review 待处置」全部未完成态；「B 已收敛」这件事由 memo 正文的收敛记录表达，**不占用状态位**。**memo.md 不存在时本项判「不适用」**〔impl-review-fix〕：MUST NOT 为满足本条而现造一个 memo，也 MUST NOT 因缺文件报错阻塞收尾——该形态只可能来自三态路由第①态（直接生成路径），此时该包没有定稿标记，第零步重入探测对它恒不可见；走拷问路径（第②③态）的包恒有 memo，不受本例外影响。除此之外 memo **无 frontmatter、无 hash、无 schema 机械核验字段**（状态位不是机械核验层）。重入探测扫到 **≥2 个** `状态：DRAFT` 的包时 SHALL 逐个呈现由操作者选择其一；操作者选「新开」时既有 draft **SHALL 原样保留**（MUST NOT 静默删除或改写），并提示其后续可再次重入。

拷问期间每条站稳的承重结论与拍板决策 SHALL 当场追加写入 memo.md（增量落盘），MUST NOT 等收敛后一次性落盘；中断损失窗口 = 两次落盘之间，SHALL 如实声明、MUST NOT 声称零损失。

**停止条件〔spec-review-amendment SR-6〕**：B 相位 SHALL 以「**最小充分条件**」收敛，MUST NOT 用形容词、MUST NOT 以「问了 N 轮」为判据——本次**被裁剪进来的每一个维度**都 SHALL 落一个终态：`已决`（有证据或操作者拍板）/ `显式延后`（须附再触发条件）/ `不适用`（须附一句理由）；全部选入维度均有终态时方可进入相位 C。终态逐条记入 memo.md。

**未决项清单〔spec-review-amendment SR-4 · 设计门 Q2 拍板 A〕**：memo.md SHALL 含一个 `## 未决项` 小节，承接被删除的 wayfinder frontier 的**清单职能**——凡① 维度终态为 `显式延后` 者、② 拷问中冒出但本次不解决的问题，SHALL 逐条落入该小节并附**再触发条件**（什么信息到位 / 什么时点应重新处理它）。该小节 MUST NOT 因「三件套已写完」而被清空，它随包长期存在、跨 session 可读。**承接边界（如实声明）**：本小节承接的是「当前还剩什么没决定」的**清单**，**MUST NOT** 被表述为等价于 wayfinder 票据模型——后者的 `Blocked-by` 依赖图与 `claimed` 并发语义**本 change 明确不承接**（roadmap 为单人操作场景，不需要）。

拷问中的术语与 ADR SHALL 走提议制：命中 ADR 三条件（难逆转 + 缺上下文会意外 + 有真实权衡）或术语冲突时向操作者提议，未经确认 MUST NOT 写入 `openspec/CONTEXT.md` / `openspec/adr/`。**写入时机与留痕〔spec-review-amendment SR-9 · SR-10 · SR-11〕**：经确认的条目 SHALL **先记入 memo.md**、待**相位 C 三件套生成并经操作者确认终稿后**才写入全局文件——B 相位中途 MUST NOT 直写全局（否则被放弃的规划会把临时判断永久留在全局真相源里，而收尾对账只发生在三件套完成后，覆盖不到中途放弃）。memo 中的每条全局写入记录 SHALL 以可辨识固定前缀落行（`[提议]` / `[确认]`）并记全 **目标路径 + 精确条目名 + 写入前版本锚**——收尾对账（checklist ④）SHALL 只对**版本锚仍匹配**的条目执行 supersede / revert，不匹配即停下交操作者裁决，MUST NOT 盲改。**版本锚的取值与边界**〔窄复核 NR-3〕：目标文件**已存在**时取其 `git log -1 --format=%h -- <路径>` 输出；目标**尚不存在**（如本次要新建的 ADR）时 SHALL 记显式 sentinel `新建`，收尾时以「该路径此前确实不存在」为匹配条件。🔴 **诚实边界**：该锚**只检测已提交的改动**——工作树内未提交的修改不会让它变化，故它 **MUST NOT 被表述为并发修改保护**，只是「本次讨论期间该条目有没有被别的提交动过」的弱信号；真并发写同一文件仍属 decision-memo 已显式接受的边角。

**重入**：新 session 触发本 skill 时 SHALL 探测未定稿 memo（`openspec/roadmaps/*/memo.md` 存在且状态标记为 `DRAFT`），命中则呈现包名 + memo 摘要由操作者选择「继续 B / 新开」，MUST NOT 静默复用。

**放弃**：拷问中途操作者放弃时——**create 场景** SHALL 删除本次新建的包目录（半途包不留），**删除前 SHALL 向操作者复述将被删除的完整路径**〔SR-39〕；**continue / replan 场景 SHALL NOT 自动删除任何内容**〔spec-review-amendment SR-5〕——「本次新增」在 append-only 的 memo 上无可执行的归属判据，自动删除会退化成猜测性地删既有内容；改为在 `task-log.md` 记一行「本次 B 放弃（日期 + 原因）」，残留内容由下次重入探测呈现给操作者处置（与既有「半途包不设自动清扫」口径一致）。

#### Scenario: B 起手建包与生命周期判定

- **WHEN** 三态路由判定进入相位 B 且 `openspec/roadmaps/{name}/` 已存在
- **THEN** 起手即向操作者显式区分 continue / replan 并按其选择执行，之后才开始拷问；MUST NOT 拷问收敛后才发现同名包

#### Scenario: create 主干——目录不存在时起手即建包与草稿〔spec-review-amendment SR-8〕

- **WHEN** 三态路由判定进入相位 B 且 `openspec/roadmaps/{name}/` **不存在**
- **THEN** 在**开始第一轮拷问之前**即创建该目录并落盘 memo.md（含包名、日期、`状态：DRAFT` 三项），MUST NOT 拖到拷问收敛后才建；此后每条站稳结论追加写入该文件

#### Scenario: 全部选入维度落定后方可进 C〔spec-review-amendment SR-6〕

- **WHEN** 本次裁剪选入的某个拷问维度既无结论、也未被显式延后或判为不适用
- **THEN** 相位 B 不得收敛、MUST NOT 进入相位 C；列出未落定的维度并继续拷问或由操作者显式延后

#### Scenario: 提议确认后先记 memo、终稿确认后才写全局〔spec-review-amendment SR-9 · SR-10〕

- **WHEN** 拷问中某 ADR/术语提议获操作者确认
- **THEN** memo.md 追加一行 `[确认]` 前缀记录（含目标路径、精确条目名、写入前版本锚），`openspec/CONTEXT.md` / `openspec/adr/` **此时仍无新增**；直到相位 C 三件套终稿经确认后才实际写入

#### Scenario: continue 场景中途放弃不自动删除〔spec-review-amendment SR-5〕

- **WHEN** continue 或 replan 场景拷问中途操作者决定放弃本次规划
- **THEN** 不删除任何既有或本次新增文件，在 task-log.md 记一行「本次 B 放弃」及原因；残留内容留待下次重入探测呈现

#### Scenario: 承重结论增量落盘

- **WHEN** 拷问中一条承重结论拿到证据或操作者拍板
- **THEN** 当场追加写入 memo.md，不等收敛；后续上下文丢失（压缩/中断）时已落盘内容无损

#### Scenario: 未定稿 memo 重入

- **WHEN** 新 session 触发本 skill，某包存在未定稿 memo.md
- **THEN** 呈现该包名与 memo 摘要，由操作者选择继续拷问或新开，MUST NOT 静默复用也 MUST NOT 忽略

#### Scenario: ADR 提议未确认不写入

- **WHEN** 拷问中某拍板决策命中 ADR 三条件，操作者尚未回应提议
- **THEN** `openspec/adr/` 无新增文件，提议内容仅存在于对话与 memo 中

#### Scenario: create 场景中途放弃

- **WHEN** create 场景拷问中途操作者决定放弃本次规划
- **THEN** 先向操作者复述将被删除的完整路径，再删除本次新建的 `openspec/roadmaps/{name}/` 目录，工作区不留半途包〔spec-review-amendment SR-39〕

### Requirement: 历史存档引用边界与存量 footage 冻结

**历史存档** = 包根 memo.md 与存量 `footage/` 目录的统称（决策形成过程的记录，与三件套定稿正文相对）。三件套 MUST NOT 引用历史存档的任何内容（含「详见 memo / footage」类表述）；历史存档中有价值的结论 SHALL 精炼后写入三件套正文。memo.md SHALL 保持包根落位，MUST NOT 迁移。**存量 footage 冻结**：本 skill 不再产出 footage（wayfinder 路径已移除）；含 `footage/` 的存量包 SHALL 视为合法历史形态——续跑时 MUST NOT 报错、MUST NOT 强推迁移、MUST NOT 新增票或要求票闭环，`footage/issues/` 中未决票视为历史遗留，至多输出一行「存量 footage，历史存档冻结」提示，不告警刷屏。

#### Scenario: 三件套引用检查

- **WHEN** 生成阶段写三件套需要引用讨论结论
- **THEN** 结论以精炼后的正文形式出现在三件套中，三件套全文不出现指向 `footage/` 或 `memo.md` 的链接、以及「详见 footage/memo」类表述

#### Scenario: 存量 footage 包续跑

- **WHEN** 新版 skill 续跑一个含 `footage/`（map + 票）的存量包
- **THEN** 按现行结构继续工作，不报错、不迁移、不新增票，至多一行冻结提示

#### Scenario: 存量未决票不阻塞收尾

- **WHEN** 存量包 `footage/issues/` 中存在 `open`/`claimed` 状态的票
- **THEN** 视为历史遗留，不要求 resolve 或 abandoned，收尾 checklist 不因此不通过

### Requirement: review 按商业化信号分档

三件套完成后 SHALL 执行内容质量 review：默认单跑 `/plan-eng-review`；项目命中**商业化信号**（外部用户、变现、获客类信号，与讨论层三态路由共用同一张词表）时 SHALL 跑 `/autoplan` 三连审。**调用契约**：触发 review 时 SHALL 显式声明「把三件套（design/roadmap/task-log）视为一个整体 plan 来 review」并指定主入口文件（roadmap.md）——review skill 的 scope gate 与收尾门按单一 plan file 设计，缺此声明会退化为单文件审（整体 plan 调用话术的存活保证）。**跳过授权**：跳过 review 仅限人类操作者显式授权（agent 自身 MUST NOT 代决跳过），产物状态记 `review-waived` 不与已审混同；task-log.md 留「未做 review，风险自担」痕迹。**显式覆盖**：操作者显式要求覆盖默认分档（强制三连审 / 强制单审）时 SHALL 遵从并记录偏离理由。review 产出的每条 issue SHALL 在 task-log.md「Review 处置」小节标注 采纳/拒绝/延后 之一且附理由。review 依赖不可用/调用失败/无输出时 SHALL 显式留痕「未审待恢复」并提示修复步骤，MUST NOT 静默当已完成。**该状态阻塞收尾**〔spec-review-amendment SR-12〕：包状态为 `未审待恢复` 时 SHALL 阻塞收尾 checklist，MUST NOT 因「Review 处置小节无未处置条目」（该小节此时本就是空的）而误判可以收尾；只有 review 成功执行、或人类操作者显式授权 `review-waived` 两种状态方可进入 checklist。

#### Scenario: 工作流型默认单审

- **WHEN** 技术重构类 roadmap 三件套完成且无商业化信号
- **THEN** 触发 `/plan-eng-review` 单审（调用语含三件套整体声明），不强制 CEO/design 审

#### Scenario: 跳过 review 必留痕

- **WHEN** 人类操作者显式决定跳过 review
- **THEN** task-log.md 存在「未做 review，风险自担」条目、包状态记 review-waived，收尾 checklist 方可通过

#### Scenario: review 依赖失败不静默

- **WHEN** plan-eng-review / autoplan 未安装、调用失败或返回空
- **THEN** 显式提示 + task-log 留「未审待恢复」痕迹 + 给出修复/重试步骤，MUST NOT 把包当作已完成收尾

#### Scenario: 未审待恢复阻塞收尾，修复重试后放行〔spec-review-amendment SR-12〕

- **WHEN** 包状态为 `未审待恢复`，操作者直接要求走收尾 checklist
- **THEN** 收尾拒绝启动并指出该状态 + 修复步骤；操作者按提示装好依赖重跑 review 成功后，状态转正常，收尾方可继续

#### Scenario: 整体 plan 调用话术存活〔spec-review-amendment SR-38〕

- **WHEN** 触发 `/plan-eng-review` 或 `/autoplan`
- **THEN** 调用语中出现「把三件套（design/roadmap/task-log）视为一个整体 plan 来 review」的显式声明且指定主入口 `roadmap.md`；缺此声明即视为该次 review 未按契约执行，SHALL 重新触发

### Requirement: 收尾 checklist 软门

规划工作流收尾 SHALL 执行 checklist 确认**四项**〔本 change 由五项收编：④ wayfinder 闭环随 wayfinder 移除删除，⑤ 简化为 memo 对账〕：① task-log.md「Review 处置」小节不存在未处置条目；② 三件套相互引用完整——判定标准钉死为最小引用图：roadmap.md 每个已细化阶段至少回指 design.md 对应决策一次、task-log.md 每条完成记录关联 roadmap.md 阶段、design 头部章与决策段无同值重复（只准互相引用）；不通过时 SHALL 报出具体文件与行号，MUST NOT 笼统宣称「完整/不完整」；③ 历史存档（包根 memo.md 与存量 footage/，如有）无被三件套引用；④ **memo 对账**：相位 B 期间经提议制确认的全局写入条目——即 memo.md 中带 `[确认]` 固定前缀、记有目标路径 / 精确条目名 / 写入前版本锚的那些行〔spec-review-amendment SR-9〕——逐条对照三件套终稿：与终稿一致者此时才实际写入 `openspec/CONTEXT.md` / `openspec/adr/`；被终稿推翻者标 superseded（或 revert）并在 task-log.md 记一行，MUST NOT 让讨论期临时判断以定稿姿态留存全局共享文件。**归属核验**〔SR-11〕：对已存在的条目执行 supersede / revert 前 SHALL 先比对其**版本锚是否仍匹配**，不匹配（说明该条目在本次讨论期间被他人或并发流程改过）SHALL 停下交操作者裁决，MUST NOT 盲改。未经提议制的写入不在本项核对范围（指令层约束的诚实边界，SHALL 如实声明而非宣称机械保证）。**未决项闭环**〔spec-review-amendment SR-4 · 设计门 Q2〕：memo.md 的 `## 未决项` 小节非空时，SHALL 逐条标 `已决` / `显式延后`（附再触发条件）/ `放弃`（附理由）之一——**MUST NOT 带未处置的未决项宣告定稿**；操作者坚持越过时 SHALL 在 task-log.md 记一行「带 N 条未决项定稿」+ 理由（显式越权留痕），MUST NOT 静默通过。checklist 任一项不通过 SHALL 提示补齐后再收尾，MUST NOT 静默跳过。收尾通过后 SHALL 提示将包纳入版本控制（软提示，与 recorder 先例对齐）〔SR-12〕。

#### Scenario: 有未处置 review 条目

- **WHEN** 收尾时「Review 处置」小节存在无状态标注的条目
- **THEN** 收尾暂停并列出未处置条目，补齐处置状态后方可完成

#### Scenario: 讨论期 ADR 与终稿冲突

- **WHEN** 收尾 memo 对账发现相位 B 经确认写入的某 adr 条目与三件套最终结论不一致
- **THEN** 该 adr 标 superseded（或 revert）并在 task-log 记一行，MUST NOT 静默留存

#### Scenario: 带未处置的未决项不得定稿〔spec-review-amendment SR-4 · 设计门 Q2〕

- **WHEN** 收尾时 memo.md 的 `## 未决项` 小节存在既未标 `已决`、也未标 `显式延后` 或 `放弃` 的条目
- **THEN** 收尾暂停并列出这些条目，逐条处置后方可完成；操作者坚持越过时在 task-log.md 记一行「带 N 条未决项定稿」与理由

#### Scenario: 存量包收尾不含 wayfinder 闭环项

- **WHEN** 对含存量 footage/ 的包执行收尾 checklist
- **THEN** checklist 为上述四项，不含票闭环检查；存量未决票按「历史存档引用边界与存量 footage 冻结」Requirement 处置，不阻塞收尾

### Requirement: roadmap.md 近细远雾分层

roadmap.md SHALL 只对近期 1-2 个阶段写满五节（前置条件/目标/子任务/验收标准/交付物）；近期取 1 还是 2 个 SHALL 写明选择理由（并行依赖/交付节奏）〔spec-review-amendment SR-14〕；更远阶段 SHALL 只写阶段目标一句与雾区备注——雾区备注 SHALL 写明「缺什么信息才能细化」而非空泛「待细化」〔SR-14〕，MUST NOT 预写子任务分解与验收细节。**长周期依赖例外〔SR-14〕**：远期阶段涉及长交付周期前置（采购/合规/外部契约类）时，允许且应当提前写「前置条件」一节，其余四节仍留雾。远期阶段 SHALL 在其成为下一个待实施阶段时补全五节。**补细重判〔SR-8〕**：补细内容若命中商业化信号、或改变范围/不可逆承诺/验收判据，SHALL 重新过一遍 review 分档判定（非强制重跑三连审），判定结果记 task-log。

#### Scenario: 生成时远期阶段形态

- **WHEN** 生成阶段产出含 4 个以上阶段的 roadmap.md
- **THEN** 阶段 1-2 含完整五节，阶段 3 及以后仅含目标句与「待 frontier 到达后细化——缺 X 信息」备注

#### Scenario: frontier 推进时补细

- **WHEN** 某远期阶段的前序阶段全部交付（或残余子任务均已终局处置）、该阶段进入待实施
- **THEN** 该阶段补全五节（可经一次短讨论），补全动作与 review 分档重判结果记入 task-log.md

#### Scenario: 前序阶段部分放弃不阻塞推进〔spec-review-amendment SR-8〕

- **WHEN** 前序阶段某子任务被终局判定放弃（非未完成、非延后）
- **THEN** 该放弃记入 task-log.md 后视为已处置，SHALL 计入「前序交付」判定，不永久阻塞 frontier 推进

### Requirement: 新项目起步的架构先行指路〔spec-review-amendment〕

`sdflow-roadmap/SKILL.md` 的 description SHALL 含指路句「新项目起步尚无架构设计（SAD）时，先 `/sdflow-architecture`」，并 SHALL 注明前置条件（消费仓需已 `sdflow-init`）——与 sdflow-architecture 侧的反向指路（时间轴规划 → sdflow-roadmap）构成双侧分工，消解「新项目起步」入口的现役触发冲突（对应 architecture-design capability 的 REQ「触发分工与互相指路」；本 delta 使 roadmap-planning 侧文本有 spec of record，archive 对码核验可锚）。

#### Scenario: description 含指路句与前置条件
- **WHEN** 检查 `sdflow-roadmap/SKILL.md` 的 frontmatter description 文本
- **THEN** 含「先 `/sdflow-architecture`」指路句及「需已 sdflow-init」前置条件提示
