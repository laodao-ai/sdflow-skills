## MODIFIED Requirements

### Requirement: 出 ticket 模式产出 tracer-bullet ticket 并落盘即返回（tickets.md 单名）

sdflow-implement 出 ticket 模式 SHALL 从 design.md 与 tasks.md 产出 3-6 张 tracer-bullet 垂直切片 ticket（计数仅约束垂直切片；expand–contract 例外序列的迁移批次、以及下述「实现验证」收尾 ticket 均不占该预算〔spec-review-amendment E5〕）：每 ticket 为打穿全层、可独立验证的行为级描述，MUST NOT 预写实现代码或具体文件路径；每 ticket SHALL 声明显式 Blocked-by 阻塞边与 R-ID 需求标注；宽重构（单一机械改动 blast radius 扫全仓）SHALL 走 expand–contract 序列例外而非强行垂直切片。ticket 文件头部 SHALL 逐字携带 design 领域约束为 Global Constraints 节。

**切片建议消费语义 SHALL 为「默认采纳 + 偏离审计」**〔harden-ticket-slicing〕：出票起手 SHALL 读 design.md 的「切片建议」节；节存在时其初步 ticket 划分与阻塞边草图 SHALL 作为**默认切分方案**采纳（该草图已经阶段二评审与设计 HARD-GATE，是流程中唯一被强档模型审过、人门可见的切分判断），出票方对草图的每处**实质偏离**（增/删/合并票、改阻塞边、改切片边界）SHALL 逐条记入 `impl-reports/planning-decisions.md` 并附理由，行格式 = 「切片偏离: <偏离点> | <理由(三镜+主次)>」，MUST NOT 静默偏离；节缺席或偏离时按下述必触发条款复核。

**T10-choice 对抗镜复核 SHALL 必触发于三种情形之一**〔harden-ticket-slicing〕：① design.md **既无**「切片建议」节、**也无**成立的缺席理由（= SA-17 违规态；有成立缺席理由的合规缺席不触发本条——但缺席理由蕴含单票交付而实际出票 >1 张功能票 ⇒ 视同条件③矛盾触发〔spec-review-amendment Q1-A〕）；② 出票实质偏离草图（偏离后的方案须复核）；③ 草图与 design.md 正文矛盾（评审 amendments 只改其他节时，切片节可残留旧切分——文件级失鲜监视不覆盖节级一致性，此处是该缺口的唯一显形点）。任一命中即派 **strong 档**对抗镜复核切分方案，复核记录按既有行格式落 `impl-reports/planning-decisions.md`；既有「粒度争议」触发路径保留不变。复核结论 SHALL 按既有 `T10-choice` 三级协议出口处理：通过 ⇒ 按复核确认的方案出票；**复核不过或无从复核 ⇒ 停并上抛**（与下方一致性自扫段同口径），MUST NOT 以被证伪的切分方案继续出票〔spec-review-amendment〕。**必触发为指令层约束（「偏离/矛盾」的判定由出票方自报，无确定性信号），MUST NOT 被表述为机械保证。**

**验收标准的语法面有界性闸门 SHALL 在出票时施加**〔curb-rework-loop-cost〕：某条验收标准若要求对某种语法面**做机械判定**，出票方 SHALL 先判该语法面能否穷举——**有界**（如 CommonMark fence 变体、自有格式的机器锚行）⇒ 可写为机械门；**无界**（通用编程语言源码、YAML、make、shell）⇒ **MUST NOT 写成机械门**，SHALL 改为「让该工具自己回答」（真跑一遍看行为 / 调用该格式的权威解析器），或降级为 best-effort 展示且**不作判定依据**。该判据 SHALL 覆盖伪装形态——不仅匹配「扫描 / 识别 / 拒绝某形态 / 指纹」这类显式措辞，**还 SHALL 匹配「在某格式文件中定位 / 插入 / 修改某处」**（「只动一个键值」听起来不像解析，但「找到那个键」本身就要解析）。**本闸门是指令层约束，MUST NOT 被表述为机械保证。**

**计划文件名 SHALL 为 `tickets.md` 单名**〔adr/0042；adr/0033 的按轨分列语境成为历史〕。**在途 plan MUST NOT 被重命名**——完成判据窗口起点由 `git log --diff-filter=A -- <plan 路径>` 取得，该判据**不跟随重命名**，改名会把窗口起点推到改名 commit，使改名前的全部 checkpoint 标签落到窗口外、已完成 ticket 被判未完成并可能重派。∴ 在途 plan SHALL 保留原文件名直至该 change 归档。gate SHALL 经共享 resolver 定位计划文件：`tickets.md` 存在即用之；不存在则判 RUN_PLAN。

出 ticket SHALL 落盘即返回编排层（ship），MUST NOT 在同一调用内直通执行——保 ship_gate 在出 ticket 后/执行前的校验插入点。原版 to-tickets 的 quiz-the-user 人类步 SHALL 删除（阶段三无人类门），粒度争议按 `T10-choice` 三级决策协议处理（①有客观判据自动选并**按三镜 + 主次**记理由；②无客观判据派 **strong 档**对抗镜复核推荐切分方案，通过方自动选；③复核不过或无从复核 defer）〔spec-review-amendment M3：首版此处漏了「按三镜 + 主次」限定词〕。**出票模式的仲裁记录 SHALL 有确定性审计落点**：写入 `impl-reports/planning-decisions.md`（change 目录内、git-tracked，由出票落盘的同一次 checkpoint 一并提交），行格式 = 「`T10-choice` 复核: <方案> | 对抗镜结论 <通过/证伪> | <理由(三镜+主次)>」——出票模式无 code-review 报告产物，此前该仲裁结果**无处可落**〔spec-review-amendment M15〕。

**出 ticket 模式 SHALL 在全部功能垂直切片之后追加一张强制的「实现验证」收尾 ticket**，`Blocked-by` 声明为全部功能 ticket 号，`R-ID` 为 `all`（语义 = 覆盖本 change 全部需求的聚合验证，Spec 轴据此核验而非逐条溯源）〔spec-review-amendment M6〕，其验收标准 SHALL 为「按下述发现契约运行本 change 的聚合测试套件（单元+集成+e2e）并全部通过」。

**聚合套件发现契约（MUST NOT 解析构建文件）**〔spec-review-amendment Q6〕：① 命令来源优先级 = `openspec/config.yaml` 的 `test-suites.{unit,integration,e2e}` 显式配置 → 缺失则由该票 implementer 依仓内既有约定判定并在票报告写明命令原文与判定依据；② 「某命令能不能跑」SHALL 由**真跑一遍看退出码**回答，MUST NOT 靠解析 Makefile/package.json 预判 target 是否存在；③ 仓内确无某层时 SHALL 记「未覆盖（本仓无此层）」并附依据，**MUST NOT fail-closed 罢工**——`sdflow-implement` 的承诺是「不管什么项目都能跑完实现管线」，罢工分支直接背叛该承诺；④ 证据 SHALL 落确定性 schema，每层一行 `<层> | <命令原文> | <退出码> | <测试时 git rev-parse HEAD>`，未覆盖层写 `<层> | — | 未覆盖 | <依据>`；⑤ 退出码非 0 SHALL 分四类处置：本 change 引入的回归 → 进 fix 循环；仓内既有红测（以 base SHA 复跑确认）→ 记录放行；flaky（同命令复跑一次即绿）→ 记录放行；环境故障 → halt envelope 停并上抛。

**`test-suites` SHALL 支持成本分档**〔curb-rework-loop-cost〕：每层的值为**字符串**时 quick 与 full 两档同命令（今日形状，继续有效）；为**映射**时读 `quick` / `full` 两键——缺 `quick` 视为该层无 quick 档，缺 `full` 视为未分档（quick=full 同命令）。旧形状是新形状的合法子集，**未配置的消费仓行为 SHALL 等同于扩展前**，MUST NOT 要求下游同步改配置。`test-suites` 的具体命令因项目而异，**SHALL 由 `sdflow-devenv` 运行时调研项目测试基础设施后推荐写入**（已有配置时保留不覆盖），本 change 只定义 schema 与消费语义。

**中间 fix 轮与收口轮的测试范围 SHALL 分离，且范围 SHALL 由确定信息界定**〔curb-rework-loop-cost · adr/0035〕：

- **中间 fix 轮** SHALL 只跑 **unit 全层**（整层跑、不做用例筛选；若该层配了 `quick` 则取 `quick`，**无 `quick` 则取 `full`——unit 层 MUST NOT 因缺 quick 档被跳过**）**加上轮失败的具体用例（⊂ unit 层）**；集成与 e2e SHALL 整体推迟到收口。中间轮的结果**仅供诊断，SHALL NOT 作为最终报告的通过证据**。
- **收口时**（双轴审判通过、打完成标签之前）SHALL 跑一次全量（各层取 `full`），报告中所有判「通过」的行 SHALL 锚**同一个最终 SHA**（= 最后一次修复之后的 `git rev-parse HEAD`）。**单一盘面语义不变**〔原 impl-review-fix FIX-4〕：`unit@A → integration@B` 拼接式的「全部通过」依旧非法。
- 🔴 **范围 MUST NOT 由「哪层受影响」的判断界定**——e2e 按定义端到端、集成测试跨模块，任何改动都可能影响它们，「本次不影响某层」是不可靠判断，把它放进关键路径等于把 fail-open 写进条款。**要求实施者为该判断写明依据不构成缓解**：要求解释一个不可靠判断，只会得到一个有说服力的错误判断。

**该票 SHALL 走跟普通 ticket 相同的 implementer + 双轴审 + fix 循环**，但 SHALL 定制三处执行契约〔spec-review-amendment H9〕：① **豁免 red-before-green**（该票不写产品代码，验收物是证据不是 diff）；② **主证据锚 = 该票 impl-report 文件 + 其内的 SHA 三元组，MUST NOT 依赖该票产生 commit**（`checkpoint-commit.sh` 在干净树上直接成功退出、不建 commit，聚合套件一次绿时可能根本无 commit）；③ Standards 轴核验范围 SHALL 为「修复方式未靠**加 skip / 改测试配置 / 删除或弱化断言**蒙混过关」（原措辞只禁删除或弱化断言，挡不住加 skip）。

**`sdflow-done` 的 verify SHALL 引用该票 impl-report 作为「实现期聚合覆盖」需求的证据锚，不扩张 verify 自身职责**；**锚的语义 SHALL 限定为「实现期结束时聚合套件通过」，MUST NOT 表述为「最终代码通过全量回归」**——该票执行于 `sdflow-code-review` 及其自动修复循环之前，code-review 之后的修复由其自身保障机制覆盖，此证据时效缺口是已知且接受的残余风险〔spec-review-amendment Q2〕。**该锚为无条件要求**（tickets 为唯一实现管线〔adr/0042〕）。

**收尾票的存在与位置 SHALL 有机械保证**〔spec-review-amendment H12〕：`ship_gate` 的 plan 校验 SHALL 含一道——该 plan MUST 恰含一张「实现验证」收尾 ticket 且其 `Blocked-by` ⊇ 全部功能 ticket 号，不满足即判非 0〔adr/0042：旧名 grandfather 条款随双名退役删除〕。

出票落盘前 SHALL 做一次全 ticket 语义一致性自扫（拓扑之外的语义矛盾，如某票假设的接口形状被另一票废弃）；发现矛盾按 `T10-choice` 三级决策协议处理（①有客观判据自动选并**按三镜 + 主次**记理由；②无客观判据派 **strong 档**对抗镜复核；③复核不过或无从复核则停并上抛），不批量问人，仲裁记录同样落 `impl-reports/planning-decisions.md`。

**出票时 SHALL 评估并行安全性**〔spec-review-amendment〕：对 `Blocked-by` 声明使得 `next_ready` 可能同时返回的一组 ticket（即它们的 `Blocked-by` 集合是 `done` 集的子集，会同时出现在 ready 列表中），出票方 SHALL 确认——① 它们的行为边界不重叠（不改同一模块的同一接口）；② 一个的产出不是另一个的输入；③ 有疑问时 SHALL 保守声明依赖（宁可串行不可误并行）；④ 若产出多张 `Blocked-by` 覆盖全部其余票号的 ticket，SHALL 让后者追加声明对前者的 `Blocked-by`，确保收尾节点唯一（`next_ready` 只返回一个收尾候选）。该约束为指令层语义约束（出票方的模型判断）；兜底为 worktree 隔离下 `git merge --no-ff` 的原生冲突检测（真正的 fail-loud）——即使出票判断失误（两票改同一文件），各自 commit 到独立 worktree 分支，merge 回主分支时 git 正常冲突检测会 fail-loud（见「执行模式宿主条件化受限并行工作 frontier 并以文件交接」需求）。

#### Scenario: 并行安全的 ticket 不声明互相 Blocked-by

- **WHEN** 某 change 有 3 张功能 ticket，T2 改脚本 A，T3 改脚本 B，T4 改 SKILL.md 的不同段，三者均只 Blocked-by T1
- **THEN** 出票方判定三者行为边界不重叠、产出不互为输入，保留 `Blocked-by: 1` 不加互相依赖

#### Scenario: 有数据流依赖时保守声明串行

- **WHEN** T2 新增一个函数，T3 的验收标准调用该函数
- **THEN** 出票方 SHALL 让 T3 声明 `Blocked-by: 1,2`，确保 T3 在 T2 完成后才执行

#### Scenario: 出 ticket 后 gate 先行校验再执行

- **WHEN** 出 ticket 模式完成落盘并返回
- **THEN** ship 重跑 ship_gate，plan 文件经 fence/标题/重号**及收尾票**四道校验后才发出 CONTINUE_IMPL，执行模式才被派发

#### Scenario: 宽重构走 expand–contract

- **WHEN** 某 tasks.md 条目是重命名共享符号类宽重构
- **THEN** 出 ticket 为 expand ticket → 迁移批次 ticket（各自 Blocked-by expand）→ contract ticket（Blocked-by 全部迁移批次），不产出「一 ticket 打穿全仓」的伪垂直切片

#### Scenario: 出票模式恒含实现验证收尾票

- **WHEN** 出 ticket 模式产出 N 张功能垂直切片（3≤N≤6）
- **THEN** `tickets.md` 额外含一张「实现验证」收尾 ticket，`Blocked-by` 全部 N 张功能票号，`R-ID: all`，不计入 3–6 预算计数

#### Scenario: 缺少收尾票的 plan 被 gate 拒绝

- **WHEN** `tickets.md` 不含收尾票，或其 `Blocked-by` 漏了某张功能票号
- **THEN** ship_gate 判非 0 并指出缺失项

#### Scenario: 仓内无 e2e 层时记未覆盖而非罢工

- **WHEN** 收尾票 implementer 判定本仓确无 e2e 层
- **THEN** 证据行记 `e2e | — | 未覆盖 | <判定依据>`，该票仍可通过双轴审，MUST NOT 因缺层停机

#### Scenario: 无切片建议且无缺席理由时复核必触发〔spec-review-amendment Q1-A〕

- **WHEN** design.md 既无「切片建议」节、也无成立的缺席理由，出票方自主决定切分方案（无论是否存在多个候选）
- **THEN** 出票方 SHALL 派一个 strong 档对抗镜复核该切分方案，不问用户；仲裁结论按行格式落 `impl-reports/planning-decisions.md`

#### Scenario: 合规缺席（有理由）的小修不触发必复核〔spec-review-amendment Q1-A〕

- **WHEN** design.md 无「切片建议」节但写明了成立的缺席理由（如「单票交付，无切分必要」），出票产出与理由一致（1 张功能票）
- **THEN** 不触发条件① 复核；若实际出票 >1 张功能票（与缺席理由矛盾），出票方 SHALL 视同条件③ 派 strong 档对抗镜复核，仲裁结论落 `planning-decisions.md`

#### Scenario: 粒度争议派 strong 档复核并落审计

- **WHEN** 出票过程中出现粒度争议（≥2 个合理切分候选）且无客观判据可判
- **THEN** 派一个 strong 档对抗镜复核推荐的切分方案，不问用户；仲裁结论按行格式落 `impl-reports/planning-decisions.md`（既有触发路径，与必触发三条件并存）

#### Scenario: 有切片建议且未偏离时默认采纳、不派复核

- **WHEN** design.md 含「切片建议」节，出票产出的票划分与阻塞边与草图一致（无实质偏离），且无粒度争议
- **THEN** 出票方按草图物化 tickets.md，`planning-decisions.md` 无偏离行，无须派 T10-choice 复核（草图已经阶段二评审与人门）

#### Scenario: 偏离草图须记录并触发复核

- **WHEN** design.md 切片建议为 4 张票，出票方判断其中两张应合并为一张
- **THEN** 出票方 SHALL 在 `planning-decisions.md` 记一行「切片偏离: 合并票 X/Y | <理由(三镜+主次)>」，并派 strong 档对抗镜复核偏离后的方案；MUST NOT 静默按己意出票

#### Scenario: 草图与 design 正文矛盾时触发复核

- **WHEN** 评审 amendments 废弃了 design 正文中的某机制，而切片建议节仍含一张以该机制为交付物的票
- **THEN** 出票方 SHALL 判「草图与 design 正文矛盾」，派 strong 档对抗镜复核修正后的切分方案，仲裁结论落 `planning-decisions.md`；MUST NOT 照旧草图出票

#### Scenario: 必触发复核证伪时停并上抛〔spec-review-amendment〕

- **WHEN** 任一必触发情形派出的 strong 档对抗镜将切分方案判「证伪」，且无可自动修正的替代方案
- **THEN** 出票流程停并上抛，MUST NOT 以被证伪的切分方案继续出票；仲裁结论仍按行格式落 `impl-reports/planning-decisions.md`

#### Scenario: 一致性自扫发现矛盾派 strong 档复核

- **WHEN** 全 ticket 语义一致性自扫发现某票假设的接口形状被另一票明确废弃，且无客观判据可自动选
- **THEN** 派一个 strong 档对抗镜复核该矛盾的处置方案，复核不过或无从复核则停并上抛，不批量问人，仲裁结论落 `impl-reports/planning-decisions.md`

#### Scenario: 中间 fix 轮不跑集成与 e2e

- **WHEN** 收尾票的聚合套件在某轮失败，implementer 修复后进入下一轮
- **THEN** 该轮只跑 unit 全层加上轮失败的具体用例（⊂ unit 层），集成与 e2e 不跑；该轮报告中集成/e2e 层 SHALL NOT 出现「通过」证据行

#### Scenario: 收口轮跑全量且所有通过行锚同一 SHA

- **WHEN** 双轴审判定该票通过、准备打完成标签
- **THEN** 各层取 `full` 命令跑一次全量，报告中所有判「通过」的行锚同一个最终 SHA；若某层的通过行锚在更早的 SHA 上，该报告 SHALL 判不合格

#### Scenario: 未配 quick 档的消费仓行为不变

- **WHEN** 某消费仓的 `test-suites.unit` 仍是字符串形状（未分档）
- **THEN** quick 与 full 两档均取该字符串命令，行为等同于扩展前，MUST NOT 因缺 quick 档报错或罢工

#### Scenario: 验收标准要求解析无界语法面时被出票闸门拦下

- **WHEN** 某待出 ticket 的验收标准写作「静态门须能识别私有 Tab/focus trap 指纹」或「窄范围 patch 逻辑只动 YAML 的某单键值」
- **THEN** 出票方 SHALL 判该语法面无界并改写该验收标准——改为让该工具自己回答（真跑一遍 / 调权威解析器），或降级为不作判定依据的展示；MUST NOT 原样出票

## ADDED Requirements

### Requirement: 执行期票外发现上报编排层按拆分标准判 fold/defer〔harden-ticket-slicing〕

执行模式中 implementer 撞到**与本 change 相关但在本票验收范围之外**的 bug/改进点时，SHALL 上报编排层处置，**MUST NOT 自行扩 scope 顺手修**（绕过双轴审的 scope 契约，票的验收边界失效）。编排层 SHALL 按 change 拆分标准（单一源 `openspec/workflow/reference/change-decomposition-standard.md`，经 resolver 解析；判定入口 = BASE-18 防吸积 AND 门：同 capability ∧ 高耦合 ∧ 低增量）判定——三者皆满足 ⇒ **fold**（该票尚未进入双轴审 ⇒ 可并入当前票验收标准；已在双轴审途中或已完成 ⇒ 追加进后续 ready 票、或新增一张 Blocked-by 当前票的票——MUST NOT 中途改动已在双轴审途中的票的验收标准〔spec-review-amendment〕；均走正常 implementer + 双轴审）；任一不满足 ⇒ **defer**（recorder 落 issues 池，显式带 `change` 字段）。判定与去向 SHALL 记一行入该票 impl-report。

#### Scenario: implementer 撞到相关票外 bug 上报而非顺手修

- **WHEN** implementer 实现某票时发现相邻函数一个与本 change 一致性相关的 bug，修复约 5 行
- **THEN** implementer 在返回中上报该发现，MUST NOT 直接改动票外代码；编排层按 AND 门判定（同 capability、高耦合、低增量皆满足）后 fold 进当前 change 的后续票

#### Scenario: 不满足 AND 门的发现 defer 进 issues 池

- **WHEN** implementer 发现一个真独立、需自身设计审查的改进点
- **THEN** 编排层判 defer，经 recorder 落 todolist（显式带 change 字段），该票不因此扩 scope
