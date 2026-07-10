<!-- sdflow:step1-broad-review v1 mode="native" -->
# gstack-review — autoplan 广审（Step1，via sdflow-spec-review）

> mode=native 佐证（侧信道）：autoplan 经 Skill 机制原生执行；codex 双声真实调用事实——CEO 声 session `019f4c16-ae67-...`（gpt-5.6-terra，99,738 tokens，exit 0）、Eng 声（130,935 tokens，exit 0）、DX 声（72,823 tokens，exit 0）；Claude 独立声 3 个 fresh 子代理（138k/173k/130k tokens）。G2 适配：premises 门与最终批准门不弹窗，登记进 spec-review-report 决策区。
> Scope 判定：UI scope=否（Phase 2 跳过）；DX scope=是（Phase 3.5 已跑）。restore point = git dff6c95（四件套已 checkpoint，本审不改四件套）。

## Phase 1 CEO（策略与范围）

**Claude CEO 独立声（C1-C7）**：
- C1(high) 头牌卖点「token 砍 40-60%」无任何 token 指标度量；retro 工具零 token 能力；mid 档 ticket 实现器单价上升 vs 单元数下降从未互相轧账。
- C2(high) 与 wco roadmap 的判赢方法论矛盾：wco 同类决策定了数字门槛纪律（roadmap.md:19），本 change 却「定性无阈值」，且二者只交叉引用过一次（无方法论对账）。
- C3(med) 「打 31% 而非 39%」的最强证据（wco P0/P2 已实测证伪 spec-review 压缩杠杆）存在但**未被引用**——Why 一句带过。
- C4(med) 更低风险替代方案未评估：粗化旧管线步长（8-15→4-6）保留带码信任模型，可单独兑现杠杆②。
- C5(med) 静默误路由可无声污染 A/B 样本：无任务要求按 change 核对 marker 与 config 意图一致才计入样本。
- C6(med) matt/superpowers 双上游未 pin 未监控 + 本地语义重述零自动化测试（golden-file 缺）。
- C7(low-med) 删 quiz-the-user 后切片粒度唯一人工检查点变 MAY 建议节——与 C1/C4 复合。

**codex CEO 声（X1-X10，判「退回重写」）**：
- X1(crit) 31% 阶段占比 ≠「弱模型校准税」因果——复杂度/返工/评审积压皆可为主因，无归因分析。
- X2(crit) defer 机制会机械降低实现墙钟而把成本转移进 backlog——总成本未闭合（defer 后续处理墙钟/重开率不计）。
- X3(crit) 「零模型自动判断」不成立：路由仍由主 session prose 读 config/marker，gate next 仍指旧管线；建议确定性 router 提前进 Phase A。
- X4(crit) 试点无法产生可执行结论：手选样本+定性拍板+人工 config 选组 = 选择偏差+操作者偏差+误配污染；应冻结资格规则并记录全协变量。
- X5(high) 经济模型未闭合：串行 frontier + 每 ticket 双轴审+修复环，派发数只是估计；建议先做「精简旧管线」对照版验证 80% 收益是否无需换轨。
- X6(high) 实质是本地 fork matt 语义而不担 fork 治理（无版本锁/契约测试/退出策略）。
- X7(high) 「连续自动到 merge」与「BLOCKED 停并上抛」规格矛盾——作业终态未定义。
- X8(high) T126/T127 是 scope creep 且污染管线试验归因——建议拆 change。
- X9(med) Phase B 成债务停车场：无硬性毕业/删除日期。
- X10(med) 「3-6 张无码 ticket」只适合被筛选的中型逻辑 change——适用边界与拒绝条件未定义。

**CEO 共识表**：
| 维度 | Claude | Codex | 共识 |
|---|---|---|---|
| 前提有效？ | 质疑（31% 归因未引证） | 质疑（因果未证） | CONFIRMED-质疑 |
| 对的问题？ | 部分（证据存在未引用） | 未证 | CONFIRMED-需补因果证据 |
| 范围校准？ | 未标记捆绑问题 | T126/T127 scope creep | DISAGREE（→需拍板） |
| 替代方案穷尽？ | 缺「粗化旧管线」变体 | 同 | CONFIRMED-缺口 |
| 生态/上游风险？ | 未 pin 双上游 | fork 治理缺失 | CONFIRMED-缺口 |
| 6 月轨迹？ | token 主张不可证 | Phase B 停车场 | CONFIRMED-关切 |

## Phase 3 Eng（架构与边界）

**Claude Eng 独立声（E1-E8，全部读码接地，含一条证实）**：
- E1(high) 「双写 MUST NOT 单边」不可执行：gate :744 是**并集**语义（T34 刻意设计），JSON 不暴露通道构成；要么执行模式自查双通道并回填（脚本化），要么降格 SHOULD。
- E2(high) Blocked-by/frontier 零机械执行：gate 全文无依赖边概念；expand→migrate→contract 误序（resume 后先派 contract）对 gate 不可见——建议 stdlib 拓扑 helper。
- E3(med) checkpoint 标签格式串第三处复述风险：tasks 1.3「含双写命令原文」违背 checkpoint-tag-single-source 已有测试纪律（test_workflow_authority）。
- E4(med) frontmatter 非受保护命名空间：_parse_plan 扫全文件，marker 块内杂行（示例 Task 标题/复选框）会被计为幻影任务——须冻结 header 语法为唯一键。
- E5(med) 「3-6 张」预算 vs expand-contract 批次数无界的关系未定义。
- E6(med) TG-18 「未命中」低估了廉价回归测试机会：producer→parser 边界正是本仓 test_producer_parser_contract 已有先例——golden-file 测试应加进 sdflow-ship/tests/。
- E7(med) 路由 fail-safe 方向未被机械保证（幻觉「键存在」会误入新管线）——键读取脚本化应从 Phase B 提前。
- E8(med) NEEDS_CONTEXT 阻塞 frontier 的停摆率不在判赢指标里。
- **E-verify(证实)**：frontmatter 对 gate 解析确实惰性（_parse_plan 无 `---` 概念）——外衣主张在最小 marker 情形成立。

**codex Eng 声（XE1-XE7）**：
- XE1(crit) 同 E1（并集语义；现有回归测试明确允许单通道过——test_gate_impl_progress:141/162）。
- XE2(high) 同 E2 + BLOCKED 无落盘则 resume 后消失、重派同一 ticket——blocker 记录是不可省略的持久状态。
- XE3(high) ticket 重号/重排会复活旧 checkpoint 假完成（窗口锚 :536 + 按号匹配 :544）——plan 首提交后结构不可变（只可追加新号）须成文。
- XE4(high) 同 E4，补齐边界 fixture 清单（header 内 Task 文本/未闭合 fence/重复 marker）。
- XE5(med) impl-pipeline 键无 lint 无确定性读取器——共享 stdlib enum reader + config-lint 诊断。
- XE6(high) 链文本手术回归保护不足：建议抽小型可测 route helper + 保留既有文本契约测试（test_workflow_authority/test_model_tiers 易被误伤）。
- XE7(high) 宣称的 rollback 不能恢复在途 change：须分开定义「停止新试点」与「迁移在途」（原子步骤）。

**Eng 共识表**：
| 维度 | Claude | Codex | 共识 |
|---|---|---|---|
| 双写可执行？ | 否（并集） | 否（并集+测试实证） | CONFIRMED-Critical |
| Blocked-by 机械执行？ | 无→脚本化 | 无→schema+持久 blocker | CONFIRMED |
| frontmatter 边界？ | 未冻结 | 未冻结+fixture | CONFIRMED |
| 测试面（TG-18）？ | golden-file 应加 | route/矩阵测试应加 | CONFIRMED（TG-18 判定应翻转） |
| 架构（双模式）？ | 成立但派发契约欠 | 成立但 router 欠 | CONFIRMED-带条件 |
| 回滚语义？ | 未查 | 在途迁移未定义 | CODEX 独家（照规则仍上抛） |

## Phase 3.5 DX（操作者与 agent 契约）

**Claude DX 独立声（D1-D8）**：
- D1(crit) ship→sdflow-implement 的**模式派发字面契约**没人写：1.1 与 2.1 是两个任务、无共享契约——须钉死 Skill args 字面串。
- D2(high) BLOCKED 停机无消息格式/无落盘产物/无 resume 语义（与 BLOCKED_UPSTREAM 的类比无代码对应——gate :766 只认 code_review frontmatter）。
- D3(high) config 键拼错静默回退**无任何可见通知**——试点样本计数会静默失真；须区分「键缺席」vs「键在但值错」并回显一行。
- D4(med-high) gate next 字段试点期**主动错误** + SHIPPED 摘要模板无管线字段（scope-check 表漏了此行）。
- D5(med) 哨兵回退无执行者/无节奏——「每个试点 change SHIPPED 后、选下一个前跑 retro」应成为必需步。
- D6(med) DONE_WITH_CONCERNS 在状态表里但零处置定义。
- D7(med) 外衣文件混淆的廉价缓解：生成的 plan 正文顶部加一行 HTML 注释自解释（不必等 Phase B 改名辩论）。
- D8(low-med) cannot-verify-from-diff 消解是全设计唯一无预算上界的步——给 N 文件/不可从盘面解决即回退 implementer 的规则。

**codex DX 声（XD1-XD6）**：
- XD1(严重) 跨版本兼容契约缺失：旧版 ship（运行 checkout 未升级）会忽略 marker 把 tickets plan 交给旧实现器——须版本核验/不兼容拒发。
- XD2(high) 消费仓升级窗口无主：无 rollout manifest/批次/核验，全局 skill 与 bundle 可长期错配。
- XD3(high) 试点首跑无成功凭据：应产出 PIPELINE_RECEIPT（读到的键值/选的管线/marker/plan sha/gate 状态）。
- XD4(high) 单文件堆全部状态机对 mid 档 agent 不可执行：应改状态决策表+填槽模板+「mid 档首读跑一票」验收演练。
- XD5(high) 除 BLOCKED 外其余停机路径同样无错误 UX 标准：统一 halt envelope（错误码/phase/证据/副作用/恢复步骤）。
- XD6(high) 人工越权 marker 通道是唯一在途逃生口却藏在规范角落且禁止 skill 建议——建 break-glass 文档并从配置注释链接。

**DX 共识表**：
| 维度 | Claude | Codex | 共识 |
|---|---|---|---|
| 模式派发契约？ | 缺（crit） | （经 halt envelope 呼应） | CLAUDE 主导-CONFIRMED |
| 静默回退 UX？ | 需回显 | 需 RECEIPT | CONFIRMED |
| 停机错误标准？ | BLOCKED 缺 | 全路径缺 | CONFIRMED |
| SKILL.md 弱档可执行性？ | 1.1-1.5 有缝 | 状态表+演练 | CONFIRMED |
| 版本/发布兼容？ | 未查 | 跨版本缺契约（严重） | CODEX 独家（上抛） |
| 外衣混淆缓解？ | HTML 注释 | break-glass 文档 | 互补采纳候选 |

## 自动决策（audit trail，G2 登记制）

| # | Phase | 决策 | 分类 | 原则 | 理由 |
|---|---|---|---|---|---|
| AD1 | 0 | UI scope=否/DX scope=是（Phase2 跳过、3.5 跑） | 机械 | — | 词面检测零/多命中 |
| AD2 | 1 | codex「退回重写」结论不中止评审、全量登记进决策区由设计门裁 | taste→登记 | P6 | G2：中途不弹窗；user sovereignty |
| AD3 | 1 | premises 确认门 → 决策区 [需拍板]（Q-P1 因果前提） | 例外（不可自动决） | — | autoplan 例外①premises |
| AD4 | 1 | T126/T127 拆分挑战：Claude 未标记、codex 独判 → taste 非 User Challenge | taste→登记 | 分类规则 | 双模型未一致，用户原方向为缺省 |
| AD5 | 3 | E-verify 证实项记入（frontmatter 惰性）平衡负面发现 | 机械 | P5 | 反静默也反漏报正向证据 |

NOT-in-scope / What-already-exists / 假设登记：见 proposal.md Non-Goals・Impact・假设表（本审引用不复制）；Error/Failure registry 由 design.md §4 失败模式表承载，缺口见 XD5/D2。
