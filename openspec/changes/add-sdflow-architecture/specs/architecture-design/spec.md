# architecture-design Delta Spec

## ADDED Requirements

### Requirement: 事实三问采集与 fail-closed 锁 draft

skill 采集步 SHALL 只询问事实类三问（一句话定位 / 外部系统清单含文档指针 / 硬约束含栈-平台-部署形态-存量-合规），价值类问题（质量取舍/风险承受度/Non-goals）MUST NOT 进入首轮问卷——后置到拍板步挂具体产物以选择题形态问。事实三问任一缺失时，SAD 文档状态 MUST NOT 升为 `skeleton-ready`（fail-closed 锁 `draft`）。`facts` 字段经 scaffold 显式参数写入且 SHALL 发生在人实际作答之后；其 `answered` 语义 = 「已记录人的回答」≠「回答质量已核验」——质量复核 SHALL 列入人门议程，SKILL.md SHALL 含此信任边界声明〔grill-amendment〕。

#### Scenario: 缺外部系统清单锁 draft
- **WHEN** 事实三问中「外部系统清单」未获得回答，操作者要求升级 skeleton-ready
- **THEN** `sad_scaffold.py` 拒绝状态迁移，退出码非 0，stderr 指明缺失的问项

#### Scenario: 三问齐备且假设处置完可升级
- **WHEN** 事实三问齐备、`[假设]` 逐条「显式接受 或 标待校准」
- **THEN** 状态迁移 `draft → skeleton-ready` 成功，frontmatter `status` 更新

### Requirement: SAD 十节骨架完整性（存在或显式 N/A）

生成的 SAD SHALL 含十节骨架（目标+质量属性 / 约束 / 外边界 / 策略+ADR 索引 / 子系统分解+contract+注意事项 / 运行场景 / 部署 / 横切概念 / 风险登记 / 词汇表引用），每节「有内容 或 显式 `N/A` + 一行理由」，MUST NOT 静默缺节。`sad_lint.py` SHALL 对缺节以非零退出 + reason_code 报告。

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

候选分解数量 SHALL 由仲裁分歧驱动：存在真实判据分歧时每个分歧点产出真实候选对；四判据无分歧时允许单方案直出，但 MUST 显式声明一行「判据无分歧，单方案直出」（跳过类判定显著呈现）；MUST NOT 构造明显劣化的对照方案凑数。

#### Scenario: 无分歧单方案带显式声明
- **WHEN** 四判据流水线全程无仲裁分歧
- **THEN** 产出单方案，且对话与 SAD 留痕中含「判据无分歧，单方案直出」声明行

#### Scenario: 有分歧产出候选对
- **WHEN** R8 仲裁出现语言边界 vs 变化率的真实分歧
- **THEN** 拍板步收到 ≥2 个源于该分歧的真实候选及 tradeoff 说明

### Requirement: 假设显影与数值溯源

AI 推测/编造的内容 MUST 标 `[假设]`（含推测依据）并聚合进假设清单；每个数值 MUST 标来源（`人拍` / `推荐待校准`）；`sad_lint.py` SHALL 输出 `[假设]` 计数；存在未处置假设（未「显式接受或标待校准」）时 MUST NOT 升 skeleton-ready。

#### Scenario: 未处置假设阻塞升级
- **WHEN** SAD 含 3 处 `[假设]` 且其中 1 处未标处置
- **THEN** 状态迁移被拒绝，输出未处置假设的定位

#### Scenario: lint 报告假设计数
- **WHEN** 对含 N 处 `[假设]` 标记的 SAD 运行 `sad_lint.py`
- **THEN** 输出中含准确计数 N

### Requirement: 文档状态机与 frontmatter 机器可读

SAD frontmatter SHALL 含机器可读字段：`status: draft|skeleton-ready|validated|frozen`（文档级）；每条 contract SHALL 带成熟度标签 `planned|draft|validated|frozen`。状态迁移 SHALL 由 `sad_scaffold.py` 执行（模型/人不得手改跳级）；`sad_lint.py` SHALL 校验枚举合法性，非法值 fail-closed 非零退出。

#### Scenario: 非法 status 值 fail-closed
- **WHEN** frontmatter `status: approved`（非枚举值）
- **THEN** `sad_lint.py` 退出码非 0，stderr 打印原因（区别于正常 reason_code 判定）

#### Scenario: 质量属性排序存在性
- **WHEN** SAD 第 1 节质量属性列表无全序排序（存在并列或未排序）
- **THEN** `sad_lint.py` 以对应 reason_code 非零退出

### Requirement: 冷走查与评审升档

走查 MUST 由 fresh 子代理执行（生成 session MUST NOT 自查），产出场景×子系统×contract 覆盖矩阵；升档多镜按信号表判定（骨架验证慢贵 / 不可逆决策面大 / 不可控外部 contract 多 / 操作者显式要求），判定 SHALL 显式陈述一行并留痕；升档形态 = skill 按 `review-lenses.md` 自编排镜阵（MUST NOT 整体调用 sdflow-spec-review）；升档且 outside voice 可用时至少一面镜用跨模型，调用 SHALL 经 `~/.sdflow/hack/outside-voice.sh`（preflight → render-prompt → exec，遵其契约头注释），不可用时降级 Claude 镜 + 显式提示，MUST NOT 静默降级〔grill-amendment〕。

#### Scenario: 默认档冷走查留痕
- **WHEN** 升档信号全部未命中
- **THEN** 单 fresh 子代理执行走查，判定留痕含「未命中升档信号」一行

#### Scenario: outside voice 不可用显式降级
- **WHEN** 升档条件命中且 `outside-voice.sh preflight` 返回非 `ready`
- **THEN** 该镜以 Claude 执行，输出显式降级提示（非静默）

### Requirement: skeleton-ready 交棒——SAD 内嵌「骨架切片建议」节〔grill-amendment〕

状态升 skeleton-ready 时 SAD SHALL 含「骨架切片建议」节：contract 穿越点（**引用**第 5 节条目，MUST NOT 复述）+ 骨架 DoD 文案（每条 L1 contract 被一次真实调用穿过 + 部署链路走通）+ 建议 change 名。消费语义 = **建议非契约**；skill MUST NOT 代开骨架 change（工作流扳机归操作者）。骨架 change 落地、contract 回写 validated 时该节 SHALL 移除（live 层当前态，历史归 git）。

#### Scenario: 交棒节完整
- **WHEN** SAD 升为 skeleton-ready
- **THEN** SAD 含「骨架切片建议」节，节内含全部子系统的 contract 穿越点引用、骨架 DoD 与建议 change 名

#### Scenario: 骨架落地后移除建议节
- **WHEN** 骨架 change 落地且 contract 回写 validated
- **THEN** scaffold 移除「骨架切片建议」节（历史由 git 保留）

### Requirement: 分家落位与单一真相源

skill SHALL 将 ADR 写入消费仓 `openspec/adr/`（不可变 + supersession 链）、术语写入 `openspec/CONTEXT.md`，SAD 本体只索引/引用 MUST NOT 复述内容；SAD 落位固定为消费仓 `openspec/architecture/sad.md`（项目级单例），已存在时 MUST NOT 静默覆盖（区分 continue/replan 向操作者确认）。SAD 产出为 **recorder 式直写**，MUST NOT 以 openspec change 壳承载生成过程（先例：sdflow-roadmap 规则 4）〔grill-amendment〕。

#### Scenario: 已存在 SAD 不静默覆盖
- **WHEN** 消费仓 `openspec/architecture/sad.md` 已存在且 skill 被再次触发
- **THEN** skill 显式向操作者区分 continue（增量）与 replan（重规划留痕）后才写入

#### Scenario: 一仓多系统声明显式不支持〔grill-amendment〕
- **WHEN** 操作者声明消费仓为一仓多系统
- **THEN** skill 显式提示「v1 仅支持单系统单例（演进路径 `architecture/{system}/` 已预留）」并留痕，MUST NOT 硬造多系统布局

### Requirement: 触发分工与互相指路（生态路由）〔grill-amendment〕

本 skill 的 description SHALL 聚焦架构词面（架构设计 / 子系统划分 / contract / SAD）并含与 sdflow-roadmap 的分工指路句（本 skill 管空间轴，时间轴规划指向 sdflow-roadmap）；`sdflow-roadmap/SKILL.md` 的 description SHALL 增加一句指路：「新项目起步尚无架构设计（SAD）时，先 `/sdflow-architecture`」——消解两 skill 在「新项目起步」入口的现役触发冲突。

#### Scenario: 两侧 description 均含分工指路
- **WHEN** 检查两个 skill 的 SKILL.md description 文本
- **THEN** sdflow-architecture 侧含「时间轴规划 → sdflow-roadmap」指路句，sdflow-roadmap 侧含「尚无 SAD 先 /sdflow-architecture」指路句

### Requirement: 判定留痕与走查矩阵落位〔grill-amendment〕

关键判定（单方案声明 / 升档判定 / 降级提示 / 状态迁移与回落原因 / 走查轮次与洞数）SHALL 追加写入消费仓 `openspec/architecture/sad-log.md`（append-only，scaffold 负责追加，MUST NOT 改写既有行）；走查矩阵 SHALL 内嵌 SAD 第 6 节正文，MUST NOT 生成独立走查报告文件。

#### Scenario: 状态迁移追加留痕
- **WHEN** scaffold 执行任一状态迁移或回落
- **THEN** `sad-log.md` 追加一行记录（时间 + 迁移 + 原因），既有行不被修改

#### Scenario: 走查产出收敛进 SAD
- **WHEN** 冷走查（或升档镜阵）完成
- **THEN** 矩阵更新在 SAD 第 6 节、洞转化为正文修订或假设条目，无独立 report 文件产生；轮次与洞数记入 sad-log.md

### Requirement: lint 输出诚实（结构通过 ≠ 语义核验）

`sad_lint.py` v1 SHALL 只断言结构性条件（十节存在性 / 假设计数与处置标记 / 排序存在 / frontmatter 枚举），通过态输出码 MUST 携带「语义未核验」标识（如 `structure-ok-SEMANTICS-UNCHECKED`），防止「lint 绿」被误读为「内容已审」；坏输入（文件缺失 / frontmatter 不可解析）SHALL fail-closed 非零退出 + stderr 原因，MUST NOT 静默归约为某个正常 reason_code。

#### Scenario: 通过态携带语义未核标识
- **WHEN** 全部结构断言通过
- **THEN** 退出码 0 且输出码为 `structure-ok-SEMANTICS-UNCHECKED`

#### Scenario: frontmatter 不可解析 fail-closed
- **WHEN** SAD 文件 frontmatter 损坏不可解析
- **THEN** 退出码非 0，stderr 打印 `[sad_lint] FAIL: <原因>`
