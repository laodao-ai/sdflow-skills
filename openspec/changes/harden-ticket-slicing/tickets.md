---
impl-pipeline: tickets
---

## Global Constraints

以下逐字摘自本 change 的 `design.md`（Goals / Non-Goals / Migration Plan / Compliance），
是每张 ticket 的实现者与评审者共享的注意力透镜，**MUST NOT 转述或弱化**。

**Goals**（proposal 范围之内的设计级边界）：

- 全部改动落在**指令层与 bundle 规则文本**：`ship_gate.py` 及一切机械层脚本零改动；出票步位置、`plan_first_sha` 窗口、design 域失鲜监视集、gate 第四道 plan 校验原样保留。
- 拆分标准单一源放 bundle 的 `reference/`（随 `sdflow-init update` 铺给消费仓），三处消费点指针引用不复制文本。

**Non-Goals**（设计级排除；proposal 级排除见 proposal.md - Non-Goals）：

- 不引入「切片建议」的机械格式校验（节标题识别、票数比对等）——「偏离」无确定性信号（票数增减 ≠ 偏离），按基准 1 划为语义残余；引入解析器还会撞基准 5。
- 不改 `openspec instructions` 载荷或 openspec CLI 侧任何东西——切片建议 SHOULD 经 `ff-generation-constraints.md` 生效（该文件已是 sdflow-spec 相位 C 的生成约束源）。

**proposal.md - Non-Goals**（逐字）：

- 不搬出票步到 spec-review 之前（评审 amendments 几乎必落 ⇒ 每 change 白付一次出票；gate 契约重造爆炸半径大）。
- 不做「偏离草图」的机械判定（票数增减 ≠ 偏离，无确定性信号 ⇒ 必触发是指令层约束，诚实边界如实标注）。
- 不改 strong 档模型映射（fable 覆盖、版本钉死均不在本次范围；后者已确认是一行 config 的将来旋钮）。
- 不在 spec-review 侧加「切片同步核」审项（矛盾显形点在出票，单点兜住即达目标态）。

**Migration Plan**（逐字，第 2 条对实现者是硬约束）：

2. 无存量迁移：既有已归档 change 的 design.md 无切片建议节是历史事实，不补写；SHOULD 只约束目标态 producer（新 change）。

**Compliance**（逐字）：

- 遵守 `openspec/rules/doc-authoring.md`（DOC-1）：本文只写最终态，无演进史。
- 遵守 CLAUDE.md 基准 1/5：新增判定均为语义层（无确定性信号），不引入任何格式解析器。
- 遵守「勿手改 `sdflow:principles` 托管块」：本 change 触碰的 SKILL.md 均只改业务段。
- 遵守 workflow bundle 部署纪律（spec-workflow「改在权威源」Requirement）：只改 `sdflow-init/assets/workflow/`，不动消费仓副本。
- 无豁免项。

**本 change 特有的两条机械纪律**（出自 CLAUDE.md 与既有测试，实现者 MUST 遵守）：

- **托管块纪律**：`openspec/INDEX.md` 第 5–27 行是 `opsx-init:rules` 托管区块（「勿手改本区块」），其真相源是 `sdflow-init/assets/snippets/index-section.md`。要改该区块内容 ⇒ **改源 + 经注入路径刷新**，两侧都要动；只改一侧是静默漂移（仓内无 snippet↔INDEX 的 parity 守卫，下次 `update` 会以「你的修改被覆盖」反向暴露）。
- **async parity 纪律**：`hack/tests/test_async_branch_parity.py` 守 `sdflow-spec-review` / `sdflow-code-review` 两个 SKILL.md 的 async 调度 marker 段**逐字节相同**。改这两个 SKILL.md 时，编辑 **MUST NOT 落入 marker 段内**。

### Task 1: bundle 规则面成型（切片建议升档 + BASE-31 + 拆分标准单一源）

**Blocked-by:** none
**R-ID:** SA-17

让 workflow bundle 这一片「分解一致性面」一次成型：切片建议从可选升为有默认要求且缺席须给理由；
设计评审侧有一条专门审「切片建议存在性 / 缺席理由是否成立 / 切片内聚质量 / 草图票数与出票预算是否兼容」的
base 审项（归镜靠既有默认规则，不改任何镜表）；change 拆分标准成为 bundle 内**唯一一份**权威文本，
供后续票以指针方式引用而不复制。新增文件在本仓 INDEX 中可被发现，且其分类描述不与「三处规范引用它」的
事实相矛盾。

四个面属同一片一致性面（升档语义、审项、标准文、可发现性互为前提），**一票做完**——先落其中一半会
留下「规则指向一个尚不存在的文件」的中间态，不满足可独立验证。

- [x] 「切片建议」在生成约束中的档位由 MAY 升为 SHOULD，缺席时要求在 design.md 写明一句为何不需要，措辞使「有节或有理由」二择一恒成立
- [x] 同处补票数预算兼容提示：草图票数须落 3–6 张垂直切片预算内，或在节内注明 expand–contract 例外依据
- [x] 新增一条 base 审项（编号 BASE-31），覆盖存在性 + 缺席理由成立性 + 切片内聚质量 + 草图票数与出票预算兼容；条文显式限定适用域 = change 四件套评审的 design.md（roadmap 三件套无切片建议契约，该场景 N/A）
- [x] BASE-31 未改动任何镜表 / 路由文件（靠「未列明的新增 base R 项默认归 strategy 镜」既有规则生效）
- [x] 新增 change 拆分标准单一源文件（4 规则 + why）：一个 change/phase = 一个完整阶段结果；不按来源批次或凑票拆；相关发现 fold 优先；defer 判定入口 = BASE-18 防吸积 AND 门（任一不满足即 defer；真独立 / 扩容大 / 需自身设计审查 / 高 blast-radius 天然落 defer）
- [x] 标准文中「缺依赖模块 → 占位 + 记 todo」写为 related 语境下的经典 defer 形态，**MUST NOT** 写成与 AND 门并列矛盾的「唯一合理 defer」绝对句
- [x] 标准文与 BASE-18 互为指针、不复制文本（标准文讲 why 与完整规则，BASE-18 是评审判定入口）
- [x] 本仓 INDEX 可发现新增文件：**改托管块的真相源 snippet + 经注入路径刷新仓内 INDEX**，两侧一致（直接手改 `openspec/INDEX.md` 托管块内部即违规）
- [x] 消解分类矛盾：新标准文被三处 spec 引为**执行必需**的规范单一源，而其所在目录当前被描述为「说明类（可删不影响执行）」——修正该描述使二者不打架（改一行 snippet 即可，落点仍在 `reference/`，不换目录）
- [x] `ship_gate.py` 及任何机械层脚本零改动（`git diff --stat` 自验）

### Task 2: 出票侧消费语义与必触发复核

**Blocked-by:** 1
**R-ID:** 出 ticket 模式产出 tracer-bullet ticket（MODIFIED）· 执行期票外发现上报（ADDED）

让出票模式对已过人门的切分草图从「参考建议」变为「默认采纳 + 偏离审计」，并让对抗镜复核在三种高风险
情形下**必然**发生而非仅凭粒度争议触发；同时给执行期的 implementer 定死「撞到票外问题只上报、不自行扩
scope」的纪律。全部改动落在实现管线编排器的指令文本内。

- [ ] 切片建议消费语义改为：节存在时其划分与阻塞边草图作为**默认切分方案**采纳；每处**实质偏离**（增/删/合并票、改阻塞边、改切片边界）逐条记入 `impl-reports/planning-decisions.md` 并附理由，行格式 =「切片偏离: <偏离点> | <理由(三镜+主次)>」，MUST NOT 静默偏离
- [ ] `T10-choice` 复核必触发三条件写入：① 既无切片建议节也无成立的缺席理由；② 出票实质偏离草图；③ 草图与 design 正文矛盾
- [ ] 条件①取 Q1-A 口径：**合规缺席（有成立理由）不触发**；但缺席理由蕴含单票交付而实际出票 >1 张功能票 ⇒ 视同条件③矛盾触发
- [ ] 既有「粒度争议」触发路径保留不变，与必触发三条件并存
- [ ] 复核结论接三级协议出口：通过 ⇒ 按复核确认的方案出票；**证伪或无从复核 ⇒ 停并上抛**，MUST NOT 以被证伪的切分方案继续出票
- [ ] 附诚实边界句：必触发为**指令层约束**（偏离/矛盾的判定由出票方自报，无确定性信号），MUST NOT 被表述为机械保证
- [ ] 新增「票外发现上报」段：implementer 撞到与本 change 相关但在本票验收范围之外的 bug/改进点时 MUST 上报编排层，**MUST NOT 自行扩 scope 顺手修**；编排层按 BASE-18 AND 门（同 capability ∧ 高耦合 ∧ 低增量）判 fold/defer，判定与去向记一行入该票 impl-report
- [ ] fold 的时序边界写清：该票尚未进入双轴审 ⇒ 可并入当前票验收标准；已在双轴审途中或已完成 ⇒ 追加进后续 ready 票或新增一张 Blocked-by 当前票的票，**MUST NOT 中途改动已在双轴审途中的票的验收标准**
- [ ] implementer dispatch 模板同步带上该上报指令（子代理是 fresh context，未声明即等同未约束）
- [ ] `sdflow:principles` 托管块零改动（只动业务段）

### Task 3: 三处消费点以指针方式引用拆分标准

**Blocked-by:** 1
**R-ID:** SA-17 · 阶段拆分锚定 change 拆分标准（ADDED）

让拆分标准在三个真正做分解判断的位置生效：产 spec 的收敛前检查、roadmap 的阶段拆分、代码审的
defer 流。三处**一律指针引用**单一源，不复制标准文本（grep 可验无复制）。

- [ ] 产 spec 的相位 B 收敛前检查新增 **scope 内聚检查**：按拆分标准核目标态范围 = 一个完整内聚的阶段结果（砍窄 / 加宽 / 混拼不相关功能均为偏离）；发现偏离连同拆分或合并建议**呈现给人拍板**，MUST NOT 静默调整范围
- [ ] roadmap 的阶段拆分处加指针引用：每阶段 = 一个完整阶段结果（未来恰好一次 change 可交付）；MUST NOT 按来源批次 / 顺手凑票拆分，MUST NOT 把一个内聚交付物拆散跨多阶段，MUST NOT 把不相干功能混入同一阶段
- [ ] 代码审的 defer 流加 fold/defer 判定指针：related 发现先过 BASE-18 AND 门再定去向，对齐既有 fold-vs-defer 条款
- [ ] 三处均为指针引用，**未复制**标准文本（自验方式：grep 标准文的特征句，命中只应有单一源一处）
- [ ] 代码审 SKILL 的编辑**未落入** async 调度 marker 段内（`hack/tests/test_async_branch_parity.py` 守两站点逐字节一致，落进去即红）
- [ ] `sdflow:principles` 托管块零改动（只动业务段）

### Task 4: T141 收口（issues 池状态与证据链闭合）

**Blocked-by:** 1,2,3
**R-ID:** —（issues 池纪律；对应 proposal「Impact - issues 池：T141 关闭」）

T141（把 change 拆分标准融入 workflow 三处触发）开了七周未收口，本 change 的 Task 1–3 已交付其全部
实质内容，此票负责让 issues 池的状态与事实一致：把 T141 置为 DONE，`resolved_by` 指向本 change，
证据指向 Task 1 产出的单一源文件与 Task 3 的三处引用。

- [ ] T141 状态由 OPEN 变为 DONE，`resolved_by` = 本 change 名
- [ ] evidence 指向拆分标准单一源文件 + 三处指针引用的落点（可被后续读者按图索骥）
- [ ] **用开发 checkout 的 issues 脚本操作**（本仓 `sdflow-issues/scripts/`），MUST NOT 用 `~/.claude/skills` 下的 symlink（那指向运行 checkout 的旧版 writer）
- [ ] 操作后 T141 已不在 open 池、在 closed 池中，且全仓 issues 相关测试仍绿

### Task 5: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4
**R-ID:** all

按「聚合套件发现契约」运行本 change 的聚合测试套件（单元+集成+e2e）并全部通过，证据落
`impl-reports/task5-<slug>.md`（每层一行 `<层> | <命令原文> | <退出码> | <SHA>`）。

**命令来源（已核，走发现契约第②路径）**：`openspec/config.yaml` **无** `test-suites` 键 ⇒ 由本票
implementer 依仓内既有约定判定并写明判定依据。本机既有约定（逐字带入，MUST NOT 重新猜）：

- 单元层 = `/usr/bin/python3 -m pytest`（全仓）。**裸 `pytest` 命令在本机不存在，默认 `python3` 亦未装 pytest** ——
  必须用 `/usr/bin/python3 -m pytest`。
- 托管块回归 = `python3 hack/sync_principles.py --check`（本 change 改了多个 SKILL.md 业务段，确认 `sdflow:principles` 托管块未损）。
- 集成层 / e2e 层：按发现契约判定；仓内确无该层则记「未覆盖（本仓无此层）」+ 判定依据，**MUST NOT fail-closed 罢工**。

**执行契约差异（本票专属，与普通票不同）**：① 豁免 red-before-green（本票不写产品代码，验收物是
证据不是 diff）；② 主证据锚 = 本票 impl-report 文件 + 其内 SHA，**MUST NOT 依赖本票产生 commit**；
③ Standards 轴核验范围 = 「修复方式未靠**加 skip / 改测试配置 / 删除或弱化断言**蒙混过关」。

**收口盘面单一**：所有判「通过」的行 MUST 锚**同一个最终 SHA**（= 最后一次修复之后的
`git rev-parse HEAD`）；拼接不同盘面的「全部通过」非法。

- [ ] 单元测试证据齐全并通过（命令原文 + 退出码 + SHA 三元组）
- [ ] 托管块回归证据齐全并通过（`sync_principles.py --check` 退出码 0）
- [ ] 集成测试证据齐全并通过（或记「未覆盖（本仓无此层）」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖（本仓无此层）」+ 判定依据）
- [ ] 所有通过行锚同一最终 SHA
