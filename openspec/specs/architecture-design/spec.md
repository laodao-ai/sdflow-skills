# architecture-design Specification

## Purpose
定义 `sdflow-architecture` skill 的系统架构设计文档（SAD）编排规范：为一个系统在给定时点产出/维护一份机器可校验的架构设计文档——事实三问采集（fail-closed 锁 draft）→ 子系统拆分规则集执行 + 反模式自检 → 候选仲裁与拍板 → 假设/数值显影与溯源 → 文档状态机（draft/skeleton-ready/validated）→ 冷走查与按信号升档评审 → skeleton-ready 交棒骨架 change → ADR/术语分家落位。一致性由 `sad_lint.py`（结构性只读校验，通过态诚实标注「语义未核验」）与 `sad_scaffold.py`（唯一合法写路径，迁移前对候选全文复检全量结构不变式 + 仓级互斥锁串行化写）机械化保障；关键判定与走查过程留痕入消费仓 `openspec/architecture/sad-log.md`（append-only）。本能力只管**空间轴**（一个系统当下如何切分子系统与 contract）；时间轴的分阶段规划由 `roadmap-planning` 能力承接。

## Requirements
### Requirement: 事实三问采集与 fail-closed 锁 draft

skill 采集步 SHALL 只询问事实类三问（一句话定位 / 外部系统清单含文档指针 / 硬约束含栈-平台-部署形态-存量-合规），价值类问题（质量取舍/风险承受度/Non-goals）MUST NOT 进入首轮问卷——后置到拍板步挂具体产物以选择题形态问。事实三问任一缺失时，SAD 文档状态 MUST NOT 升为 `skeleton-ready`（fail-closed 锁 `draft`）。`facts` 字段经 scaffold 显式参数写入且 SHALL 发生在人实际作答之后；其 `answered` 语义 = 「已记录人的回答」≠「回答质量已核验」——质量复核 SHALL 列入人门议程，SKILL.md SHALL 含此信任边界声明〔grill-amendment〕。**人门位置钉死**：冷走查洞处置后、scaffold 迁移前，固定议程 =（三问回答复核 / 假设逐条处置 / 走查洞处置确认）〔spec-review-amendment：DX 双镜命中「人门被引用却无流程位置」〕。锁 draft 前置复检 SHALL 与 lint 共用**同一正文实扫核心**（`assumptions_open` 为展示缓存，MUST NOT 作为门禁数据源——失鲜缓存可绕锁）〔spec-review-amendment〕。`sad_lint.py` SHALL 对已处于 `skeleton-ready`/`validated` 态的 SAD 持续断言 facts×status 不变式（非仅初次迁移时点检查）：三问事实键须全 `answered`，一旦回落缺失即以 `facts-status-invariant` reason_code fail-closed，指引经 `sad_scaffold.py transition --to draft` 回落或补答后重升〔impl-review-fix〕。

#### Scenario: 缺外部系统清单锁 draft
- **WHEN** 事实三问中「外部系统清单」未获得回答，操作者要求升级 skeleton-ready
- **THEN** `sad_scaffold.py` 拒绝状态迁移，退出码非 0，stderr 指明缺失的问项

#### Scenario: 三问齐备且假设处置完可升级
- **WHEN** 事实三问齐备、`[假设]` 逐条「显式接受 或 标待校准」
- **THEN** 状态迁移 `draft → skeleton-ready` 成功，frontmatter `status` 更新

### Requirement: SAD 十节骨架完整性（存在或显式 N/A）

生成的 SAD SHALL 含十节骨架（目标+质量属性 / 约束 / 外边界 / 策略+ADR 索引 / 子系统分解+contract+注意事项 / 运行场景 / 部署 / 横切概念 / 风险登记 / 词汇表引用），每节「有内容 或 显式 `N/A` + 一行理由」，MUST NOT 静默缺节。`sad_lint.py` SHALL 对缺节以非零退出 + reason_code 报告。十节标题、「骨架切片建议」节、附录等结构锚在 fence 外 MUST NOT 出现 ≥2 次——影子节可顶替真节骗过锁 draft/lint；`sad_lint.py` SHALL 以 fence-aware 扫描检测重复锚，命中以 `duplicate-section` reason_code fail-closed〔impl-review-fix〕。

#### Scenario: 缺横切概念节且无 N/A 标注
- **WHEN** SAD 缺第 8 节（横切概念）且无「N/A + 理由」行
- **THEN** `sad_lint.py` 退出码非 0，reason_code 指明缺失节编号

#### Scenario: 十节全部存在或显式 N/A
- **WHEN** 十节各自「有内容」或「N/A + 一行理由」
- **THEN** 节存在性断言通过

### Requirement: 拆分规则集执行与反模式自检前置

推荐步 SHALL 按拆分规则集（R1–R11：原料提取 → 语义聚类 → 物理边界先行 → 四判据精修 → 仲裁与终止 → 全景占位 → 留痕 schema）执行，且反模式黑名单（AP1 entity-service / AP2 流程式 / AP3 技术分层 / AP4 God-hub）自检 MUST 先于候选交人；拆分判据与被否切法 SHALL 记为消费仓 `openspec/adr/` 下的第一条分解 ADR。

#### Scenario: 技术分层形态被自检拦截
- **WHEN** 候选分解呈「UI 层/业务层/存储层」形态（AP3）
- **THEN** 自检标记 AP3 并按修正动作重新聚类后才交人拍板，自检结果留痕

#### Scenario: 分解判据落 ADR
- **WHEN** SAD 子系统分解定稿
- **THEN** 消费仓 `openspec/adr/` 存在分解判据 ADR（含按什么切 + 被否切法 + 后果）

### Requirement: 候选数由仲裁分歧驱动

候选分解数量 SHALL 由仲裁分歧驱动：存在真实判据分歧时每个分歧点产出真实候选对；四判据无分歧时允许单方案直出，但 MUST 显式声明一行「判据无分歧，单方案直出」（跳过类判定显著呈现）；MUST NOT 构造明显劣化的对照方案凑数。整体方案数上限 3——超出按分歧维度归并后呈现〔spec-review-amendment：防拍板面爆炸〕。**信任边界声明**：候选真实性（是否凑数）无确定性信号，归人门与冷走查复核（同 facts 口径）〔spec-review-amendment〕。拍板步 SHALL 一轮打包呈现全部选择题（分组单条消息），数值项不否决即采纳推荐〔spec-review-amendment DX 双声〕。

#### Scenario: 无分歧单方案带显式声明
- **WHEN** 四判据流水线全程无仲裁分歧
- **THEN** 产出单方案，且对话与 SAD 留痕中含「判据无分歧，单方案直出」声明行

#### Scenario: 有分歧产出候选对
- **WHEN** R8 仲裁出现语言边界 vs 变化率的真实分歧
- **THEN** 拍板步收到 ≥2 个源于该分歧的真实候选及 tradeoff 说明

### Requirement: 假设显影与数值溯源

AI 推测/编造的内容 MUST 标 `[假设-N]`（含推测依据）并聚合进假设清单；每个数值 MUST 标来源（`人拍` / `推荐待校准`）；`sad_lint.py` SHALL 输出假设计数——计数**以正文实扫为准**，frontmatter `assumptions_open` 仅为 scaffold 展示缓存，两者不一致时 SHALL 输出独立 mismatch reason_code（MUST NOT 静默采信任何一方）〔grill-amendment〕；对账口径 = **编号集合双向相等且双侧无重复编号**，MUST NOT 以计数相等替代（重号+错位可使计数相等而双向锚已破）〔spec-review-amendment〕；假设处置 SHALL 经 scaffold 显式参数（`--assumption <N>=接受|待校准`）写入且 SHALL 发生在人门步操作者逐条确认之后（与 facts 同款信任边界——补齐处置动作的操作路径与归属步骤）〔spec-review-amendment〕；存在未处置假设时 MUST NOT 升 skeleton-ready。附录假设清单数据行格式（`|` 分隔 5 列、半角字符）MUST 合法——全角空格 U+3000 等畸形字符混入会使该行同时从正文扫描与清单扫描中蒸发、假绎通过 `assumption-unresolved` 判定；`sad_lint.py` SHALL 检测畸形附录行并以 `malformed-appendix-row` reason_code fail-closed〔impl-review-fix〕。

#### Scenario: 未处置假设阻塞升级
- **WHEN** SAD 含 3 处 `[假设-N]` 且其中 1 处未标处置
- **THEN** 状态迁移被拒绝，输出未处置假设的定位

#### Scenario: 缓存与正文不一致报 mismatch〔grill-amendment〕
- **WHEN** frontmatter `assumptions_open` 与正文实扫计数不一致
- **THEN** `sad_lint.py` 以独立 mismatch reason_code 非零退出

#### Scenario: 编号重复时集合对账拦截〔spec-review-amendment〕
- **WHEN** 正文出现两个 `[假设-1]`、清单含 假设-1/假设-2 两行（计数 2==2）
- **THEN** `sad_lint.py` 以对账 reason_code 非零退出（集合对账拦截计数假绿）

### Requirement: 文档状态机与 frontmatter 机器可读

SAD frontmatter SHALL 含机器可读字段：`sad_schema: <int>`（版本——lint 版本不匹配 → **独立 reason_code + 升级指引**，与损坏 fail-closed 物理区分〔spec-review-amendment hr-tg〕）与 `sad_status: draft|skeleton-ready|validated`（文档级，**无 frozen**——冻结仅 contract 级〔spec-review-amendment：消撞名与语义空转〕）；每条 contract SHALL 带成熟度标签 `planned|draft|validated|frozen`（标签扫描 SHALL 限定第 5 节 span 内，防节外文本误判；未闭合 `contract[` 标签 MUST 以 `contract-invariant-violation` reason_code fail-closed，不得逃逸枚举校验）。状态迁移 SHALL 由 `sad_scaffold.py` 执行（模型/人不得手改跳级），合法迁移以 design 显式迁移表为准、表外拒绝；文档态×contract 态组合不变式（validated ⇒ 非 planned contract 全 ∈ {validated,frozen}，planned 豁免）由 lint 断言〔spec-review-amendment〕；`sad_lint.py` SHALL 校验枚举合法性，非法值 fail-closed 非零退出；全序与 N/A 的机械文本形态以 `sad_schema.py` 锚定（有序列表连续无重号；`N/A — <非空理由>`）〔spec-review-amendment〕。任一状态迁移落盘前，`sad_scaffold.py` SHALL 对迁移完成后的候选全文（status 已改、切片节已插/删）复用 `sad_lint.py` 读侧检查核心跑一次全量结构不变式复检，命中任何违规即 fail-closed（exit 5）拒绝写盘——目标态导向：validated 不得留 `contract[draft]`、回落 draft 不得残留 `contract[validated]`/`contract[frozen]`，均在此拦截，不允许先落盘再事后发现〔impl-review-fix〕；`sad_scaffold.py` 的一切写路径（状态迁移 / `set-fact` / `set-assumption` / `adr-new` / 切片写入等）SHALL 经仓级互斥锁（`openspec/.sad-scaffold.lock`，`O_CREAT|O_EXCL` 独占获取）串行化，并以唯一命名临时文件 + 原子替换写入目标文件，防并发调用互相踩踏或留下半写文件〔impl-review-fix〕。

#### Scenario: 非法 status 值 fail-closed
- **WHEN** frontmatter `sad_status: approved`（非枚举值）
- **THEN** `sad_lint.py` 退出码非 0，stderr 打印原因（区别于正常 reason_code 判定）

#### Scenario: schema 版本不匹配给升级指引〔spec-review-amendment〕
- **WHEN** 存量 SAD 的 `sad_schema` 版本低于脚本支持版本
- **THEN** `sad_lint.py` 输出版本不匹配的独立 reason_code + 升级指引，不与「frontmatter 损坏」共用出口

#### Scenario: 质量属性排序存在性
- **WHEN** SAD 第 1 节质量属性列表无全序排序（存在并列或未排序）
- **THEN** `sad_lint.py` 以对应 reason_code 非零退出

### Requirement: 冷走查与评审升档

走查 MUST 由 fresh 子代理执行（生成 session MUST NOT 自查），产出场景×子系统×contract 覆盖矩阵；走查留痕行 SHALL 含**执行者字段**（子代理标识 / self-degraded），供审计区分冷走查与自查〔spec-review-amendment〕；**宿主中立**：宿主无 fresh 子代理原语（如 Codex CLI 宿主——setup.sh 双宿主分发无 opt-out）时 SHALL 显式降级——走查由主 session 执行并 MUST 标 `walkthrough=self-review-degraded` 入 sad-log（响亮留痕 + 建议换宿主复跑），MUST NOT 佯装冷走查〔spec-review-amendment：对抗镜 critical〕。升档多镜按信号表判定（骨架验证慢贵 / 不可逆决策面大 / 不可控外部 contract 多 / 操作者显式要求），判定 SHALL 显式陈述一行并留痕；升档形态 = skill 按 `review-lenses.md` 自编排镜阵（MUST NOT 整体调用 sdflow-spec-review）；升档且 outside voice 可用时至少一面镜用跨模型，调用 SHALL 经 `~/.sdflow/hack/outside-voice.sh`（preflight → render-prompt → exec，遵其契约头注释）；wrapper 文件不可执行/不存在（区别于 preflight 非 ready）同走显式降级〔spec-review-amendment〕；不可用时降级 Claude 镜 + 显式提示，MUST NOT 静默降级〔grill-amendment〕。`sad_scaffold.py transition --to skeleton-ready` 落盘前 SHALL 前置核验 sad-log 留痕**存在性**：复检 append-only 日志中 ≥1 行含「走查」关键字 + ≥1 行含「升档判定」关键字，缺失任一即 fail-closed（exit 5）拒绝迁移；该核验仅锚存在性，MUST NOT 被误读为内容真实性已核验——走查/人门是否真实发生机械不可证，内容真伪仍归人门复核〔impl-review-fix〕。

#### Scenario: 默认档冷走查留痕
- **WHEN** 升档信号全部未命中
- **THEN** 单 fresh 子代理执行走查，判定留痕含「未命中升档信号」一行

#### Scenario: outside voice 不可用显式降级
- **WHEN** 升档条件命中且 `outside-voice.sh preflight` 返回非 `ready`
- **THEN** 该镜以 Claude 执行，输出显式降级提示（非静默）

### Requirement: skeleton-ready 交棒——SAD 内嵌「骨架切片建议」节〔grill-amendment〕

状态升 skeleton-ready 时 SAD SHALL 含「骨架切片建议」节：contract 穿越点（**引用**第 5 节条目，MUST NOT 复述）+ 骨架 DoD 文案（每条 L1 contract 被一次真实调用穿过 + 部署链路走通）+ 建议 change 名。消费语义 = **建议非契约**；skill MUST NOT 代开骨架 change（工作流扳机归操作者）。骨架 change 落地、contract 回写 validated 时该节 SHALL 移除（live 层当前态，历史归 git）。升 skeleton-ready 后 skill SHALL 在对话输出一行收尾（状态 + 建议 change 名 + 下游命令 + 纳入版本控制软提示）——交棒不得只埋在文件里〔spec-review-amendment DX 双声〕。lint SHALL 按 `sad_status` 分支断言建议节：skeleton-ready ⇒ 节存在且穿越点引用集 == 第 5 节子系统集；validated ⇒ 节不存在〔spec-review-amendment：两条纯结构断言成本极低，堵「移除逻辑漏了/穿越点缺漏只靠人眼」〕。集合比对前 SHALL 先查重名：第 5 节子系统名、切片穿越点各自 MUST NOT 出现重复项（同名折叠会让一条穿越点同时满足两个子系统、绕过集合比对），命中以 `duplicate-subsystem` reason_code fail-closed，早于 `slice-pierce-set-mismatch` 判定；集合比对与写入前 SHALL 做 Unicode NFC 归一（防 NFD/NFC 同形异码令「看着一样却报不一致」）〔impl-review-fix〕。

#### Scenario: 交棒节完整
- **WHEN** SAD 升为 skeleton-ready
- **THEN** SAD 含「骨架切片建议」节，节内含全部子系统的 contract 穿越点引用、骨架 DoD 与建议 change 名

#### Scenario: 骨架落地后移除建议节
- **WHEN** 骨架 change 落地且 contract 回写 validated
- **THEN** scaffold 移除「骨架切片建议」节（历史由 git 保留）

### Requirement: 分家落位与单一真相源

skill SHALL 将 ADR 写入消费仓 `openspec/adr/`（不可变 + supersession 链）、术语写入 `openspec/CONTEXT.md`，SAD 本体只索引/引用 MUST NOT 复述内容；**分家写入机械化**〔spec-review-amendment：分家是全 skill 唯一无脚本写入路径，违机械化优先〕：ADR 编号分配 SHALL 由 scaffold `adr-new` 子命令执行（扫描既有文件名最大数字前缀 +1；无法识别编号模式 → fail-closed 留人工指定）；CONTEXT.md 并入语义 = 追加 `## Language` 末尾、同名术语不覆盖、冲突显式报告留人裁决。SAD 落位固定为消费仓 `openspec/architecture/sad.md`（项目级单例），已存在时 MUST NOT 静默覆盖（区分 continue/replan 向操作者确认）；**validated 回写豁免分流**：回写为骨架落地后的既定后续动作（continue 回写入口），不属「重新触发生成」、不经 continue/replan 确认（显式排除，消除双入口门禁不一致）〔spec-review-amendment〕。preflight 两级：无 `openspec/` → fail-closed 指引 sdflow-init（含完整命令）；有布局但缺 `adr/`/`CONTEXT.md` → 显式「首次创建」最小初始化〔spec-review-amendment〕。SAD 产出为 **recorder 式直写**，MUST NOT 以 openspec change 壳承载生成过程（先例：sdflow-roadmap 规则 4）〔grill-amendment〕。

#### Scenario: 已存在 SAD 不静默覆盖
- **WHEN** 消费仓 `openspec/architecture/sad.md` 已存在且 skill 被再次触发
- **THEN** skill 显式向操作者区分 continue（增量）与 replan（重规划留痕）后才写入

#### Scenario: 一仓多系统声明显式不支持〔grill-amendment〕
- **WHEN** 操作者声明消费仓为一仓多系统
- **THEN** skill 显式提示「v1 仅支持单系统单例（演进路径 `architecture/{system}/` 已预留）」并留痕，MUST NOT 硬造多系统布局

### Requirement: 触发分工与互相指路（生态路由）〔grill-amendment〕

本 skill 的 description SHALL 聚焦架构词面（架构设计 / 子系统划分 / contract / SAD）并含与 sdflow-roadmap 的分工指路句（本 skill 管空间轴，时间轴规划指向 sdflow-roadmap）；`sdflow-roadmap/SKILL.md` 的 description SHALL 增加一句指路：「新项目起步尚无架构设计（SAD）时，先 `/sdflow-architecture`」——消解两 skill 在「新项目起步」入口的现役触发冲突（roadmap 侧 delta 见 `specs/roadmap-planning/spec.md`〔spec-review-amendment〕）。两侧指路句均 SHALL 注明前置条件（消费仓需已 `sdflow-init`）——防绿地新项目被路由后首触即 preflight 拒绝的体验断崖〔spec-review-amendment〕。

**过程轴下游指路（本 change 新增）**：本 skill 的 description SHALL 增加**过程轴分流句**——「建 dev/test 环境 / 定测试策略 → `/sdflow-devenv`」，与既有的时间轴分流句（→ `sdflow-roadmap`）并列，使三轴路由在 description 层完整（空间轴=本 skill · 时间轴=roadmap · 过程轴=devenv）。

**交棒话术改写（本 change 新增）**：skeleton-ready 交棒时的「过程轴文档指路」SHALL 从**「指出不代写 + 给模板路径」**改为**指向下游 skill `/sdflow-devenv`**——过程轴此前无下游、只能给锚与模板路径；`sdflow-devenv` 落地后该空缺已填补，继续只给模板路径会把操作者留在手搓状态。改写后 SHALL 保留「本 skill 不代写过程轴文档」的边界（architecture 仍是**指路者**，MUST NOT 代写 environments/testing-strategy，亦 MUST NOT 将其内容写进 SAD——违 `quality-criteria.md` 边界总则），并 SHALL 继续给出可投影的 SAD 锚（工具链锚=§2 约束 · **依赖形态锚=§3 外边界** · 集成测试点锚=§5 contract · 部署锚=§7 · 配置项锚=§8），供下游 skill 消费。

#### Scenario: 两侧 description 均含分工指路
- **WHEN** 检查两个 skill 的 SKILL.md description 文本
- **THEN** sdflow-architecture 侧含「时间轴规划 → sdflow-roadmap」指路句，sdflow-roadmap 侧含「尚无 SAD 先 /sdflow-architecture」指路句

#### Scenario: description 含过程轴分流句
- **WHEN** 检查 `sdflow-architecture/SKILL.md` 的 description 文本
- **THEN** 其中含「建 dev/test 环境 / 定测试策略 → /sdflow-devenv」分流句，与时间轴分流句并列

#### Scenario: 交棒指向下游 skill 而非模板路径
- **WHEN** SAD 升为 skeleton-ready 并输出过程轴文档指路
- **THEN** 指路内容指向 `/sdflow-devenv`（含前置说明），而非仅给出模板文件路径让操作者自行手搓

#### Scenario: 交棒仍不代写过程轴文档
- **WHEN** SAD 升为 skeleton-ready
- **THEN** skill 给出可投影的 SAD 锚（§2/§3/§5/§7/§8）并指向下游 skill，但 MUST NOT 代写 environments.md 或 testing-strategy.md，亦 MUST NOT 将其内容写入 SAD

### Requirement: 判定留痕与走查矩阵落位〔grill-amendment〕

关键判定（单方案声明 / 升档判定 / 降级提示 / 状态迁移与回落原因 / 走查轮次与洞数 / **步骤到位 `step=N reached` / 候选摘要快照 / 走查执行者**〔spec-review-amendment：断点恢复——候选只活在对话里则 session 断即丢；continue 时 SKILL SHALL 先读 sad-log 定位断点〕）SHALL 追加写入消费仓 `openspec/architecture/sad-log.md`（append-only，scaffold 负责追加，MUST NOT 改写既有行）；走查矩阵 SHALL 内嵌 SAD 第 6 节正文，MUST NOT 生成独立走查报告文件。

#### Scenario: 状态迁移追加留痕
- **WHEN** scaffold 执行任一状态迁移或回落
- **THEN** `sad-log.md` 追加一行记录（时间 + 迁移 + 原因），既有行不被修改

#### Scenario: 走查产出收敛进 SAD
- **WHEN** 冷走查（或升档镜阵）完成
- **THEN** 矩阵更新在 SAD 第 6 节、洞转化为正文修订或假设条目，无独立 report 文件产生；轮次与洞数记入 sad-log.md

### Requirement: lint 输出诚实（结构通过 ≠ 语义核验）

`sad_lint.py` v1 SHALL 只断言结构性条件（十节存在性 / 假设集合对账与处置标记 / 排序存在 / frontmatter 枚举与版本 / 组合不变式 / 建议节分支断言），通过态输出码 MUST 携带「语义未核验」标识（如 `structure-ok-SEMANTICS-UNCHECKED`），防止「lint 绿」被误读为「内容已审」；坏输入（文件缺失 / frontmatter 不可解析 / 正文扫描到 EOF 仍处于未闭合 fence）SHALL fail-closed 非零退出 + stderr 原因，MUST NOT 静默归约为某个正常 reason_code（未闭合 fence 可把未处置假设/影子节整段藏入 fence 假象、绕过锁 draft 与结构断言，故与其余坏输入同归 fail-closed 出口）〔impl-review-fix〕；每个 reason_code SHALL 携带一行 next-step 提示（修什么 + 用什么命令），pytest 断言其存在〔spec-review-amendment DX 双声：报错三件套「问题+原因+下一步」〕。

#### Scenario: 通过态携带语义未核标识
- **WHEN** 全部结构断言通过
- **THEN** 退出码 0 且输出码为 `structure-ok-SEMANTICS-UNCHECKED`

#### Scenario: frontmatter 不可解析 fail-closed
- **WHEN** SAD 文件 frontmatter 损坏不可解析
- **THEN** 退出码非 0，stderr 打印 `[sad_lint] FAIL: <原因>`

