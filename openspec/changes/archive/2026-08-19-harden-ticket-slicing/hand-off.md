# Hand-off — harden-ticket-slicing

> 产出时点：verify 判定之后 / archive 之前。作**异步人类再入口 + 下个 change 种子**，随归档留档。
> 本文件的「完成」项**不直接搬运 verify 的 ✅**——每条已由主 session 独立复核锚点存在性（P3h-c）。

## ✅ 完成了什么

**一句话**：ticket 的切分判断从阶段三（弱受控、无独立审查的位置）**前移**到阶段一/二（强档产出 +
受审 + 人门可见），出票步降级为「物化已审草图」；同时把 change 拆分标准收成 bundle 单一源，
被三处消费点指针引用，T141 七周悬置收口。

| 交付 | 锚点（已独立复核存在） |
|---|---|
| 「切片建议」节 MAY→**SHOULD** + 缺席须写理由（「有节」或「有理由」二择一恒成立）+ 票数预算约束 | `sdflow-init/assets/workflow/ff-generation-constraints.md:38-47` |
| **BASE-31** 新审项（存在性 / 缺席理由成立性 / 切片内聚质量 / 票数与预算兼容；适用域限定 change 四件套的 design.md，roadmap 三件套 N/A） | `spec-checklists/spec-quality-base.md:55`；归镜靠既有默认规则（`sdflow-spec-review/SKILL.md:248`），**零镜表改动** |
| **change 拆分标准单一源**（4 规则 + why；与 BASE-18 互为指针不复制） | 新建 `workflow/reference/change-decomposition-standard.md` |
| 单一源在本仓 INDEX 可发现，且分类描述不与「三处规范引用它」矛盾 | `openspec/INDEX.md:25` ≡ `assets/snippets/index-section.md:20`（两侧逐字一致） |
| 出票消费语义：**默认采纳 + 偏离审计**（偏离逐条记 `planning-decisions.md`，行格式固定） | `sdflow-implement/SKILL.md:256-260` |
| `T10-choice` 复核**必触发三条件**（无草图∨实质偏离∨草图与正文矛盾）+ Q1-A 口径 + 三级协议出口 + 诚实边界句 | `sdflow-implement/SKILL.md:262-282` |
| 执行期**票外发现上报**（implementer MUST NOT 自行扩 scope；编排层按 BASE-18 AND 门判 fold/defer） | `sdflow-implement/SKILL.md:619-625`、`:650-673` |
| 三处消费点指针引用（相位 B scope 内聚检查 / roadmap 阶段拆分 / code-review defer 流） | `sdflow-spec/SKILL.md:372` + `:182` + `references/scope-cohesion-check.md`；`sdflow-roadmap/SKILL.md:215-218`；`sdflow-code-review/SKILL.md:403-405` |
| **T141 收口** | `openspec/issues/closed/todo/T141.md`（`status: DONE` / `resolved_by: harden-ticket-slicing` / evidence 指向单一源 + 五处引用）+ commit `c0b6eb2` |

**质量层实况**（供判断这份交付被审到什么程度）：

- 实现：5 张票（4 功能 + 1 实现验证收尾），**每票双轴审**（Standards + Spec）。Task 1 与 Task 3 各
  经 1 轮 fix 消解 finding（Task 3 那条是 **Critical**：SA-17 判据下沉 references 后未接回执行路径）。
- 聚合回归：`impl-reports/task5-impl-verify.md` —— 单元层 `2601 passed / 10 skipped` rc=0、托管块回归
  rc=0，两条通过行**锚同一 SHA `efc37b8`**（单一盘面，无拼接）；集成/e2e 记「未覆盖（本仓无此层）」+ 判定依据。
- 代码审：**六面镜全跑**（Step1 scope 审计 + 领域镜 + 对抗镜×2 + 历史镜 + 跨模型 voice），4 条采纳
  当场修复并过复审一轮，3 条 defer。详见 `code-review-report.md`。
- verify：强档 Do-Not-Trust 冷启，逐条对码，并在 HEAD `0fb6422` **独立复跑** pytest 与托管块门禁
  （补收尾票证据的时效缺口）。

## ⏳ 未完成 / 延后

本 change 新增、**未在本轮处理**的 6 项（均 `source_change = harden-ticket-slicing`，各见
`openspec/issues/open/todo/{ID}.md`）：

| ID | 摘要 | 为何这轮不做 |
|---|---|---|
| **T289** | 收尾票机械门只校验唯一 `R-ID: all` + `Blocked-by` 覆盖，**不校验该票确为实现验证票**——任意普通票伪标 `R-ID: all` 即可绕过聚合回归 | 跨模型 voice 报出，属实。但这是**既有** gate 弱点（早于本 change），且本 change 的 Goals 明写「`ship_gate.py` 及一切机械层脚本零改动」⇒ 修它=越界。**这是 6 项里最值得优先做的一条**——它是个真的绕过口。 |
| **T290** | 新增的「切片偏离」审计行格式落 `planning-decisions.md` 后**全仓零消费方**（grep 仅命中定义处本身） | proposal 措辞已诚实（只承诺「可 git 审计」未承诺「被审计」），不构成假保证；但「给它接一个消费方」（如并进 code-review Step1 输入清单做偏离-diff 对账）是另一片面的设计决策 |
| **T287** | `sdflow-spec/SKILL.md` 体量逼近 18,000 字符门（现 17,934，**余 66**），下一次加内容即撞门 | 本轮已被它逼着做过一次「判据下沉 + 无损压缩」；根治要么继续下沉、要么重新设计这个门 |
| **T288** | 新建的 `scope-cohesion-check.md` 未注册进 `REFERENCE_ROUTES` 类契约测试（该字典非封闭清单，故不红） | 要不要给它机械守是取舍，不是缺陷 |
| **T286** | BASE-18 表格单元格过长（已含两级判定 + AND 门 + 双向指针） | 纯可读性 |
| **T291** | `workflow-rules-guide.html` 里 `ff-generation-constraints.md` 的「198 行」计数与实际（现 207）不符 | 历次改动累积的历史遗留漂移，与本轮无因果；顺手修=自加范围 |

**被延后的 ≥2 方案决策**（当时自动选了什么 / 为何）：

- **出票期 `T10-choice`（切分方案）**：对抗镜（opus）**证伪**了首个推荐方案（把 T141 收口并入契约
  收尾票），指名改用备选 B。已按复核确认的方案出票，记录在 `impl-reports/planning-decisions.md`。
  **无遗留待决项。**
- **代码审期 F1（单票交付 vs 3–6 预算）**：走 `T10-choice` **有客观判据档 ①** 自动选——依据
  `decision-memo.md` 的 D2 明写「单文件小修强制产草图是样板税」。**无遗留待决项。**
- **F2（切片建议落在 D 编号体系外）**：在「扩摘要口径」与「编 D-7」之间选了前者，依据是后者要动
  D 表/触发条件表/prompt 片段/检查清单四处结构、爆炸半径超本次范围。**若日后有人认为切片建议
  就该是一条 D 约束，这是个可以重开的口子**——重开时请连带处理那四处结构。

**verify 的 Minor 缺口**（均判可接受）：

1. 收尾票证据锚在 `efc37b8`，未覆盖其后 4 个提交——这是 delta spec 明写并接受的残余风险；verify
   已在 HEAD 独立复跑补齐事实。
2. 相位 C 的「切片建议」规则经 `openspec instructions` 的 context 间接加载，属**指令层约束非机械
   保证**——本轮已把 `openspec/config.yaml` 等四处摘要口径扩为「D-1~D-6 + 切片建议」消除漏读诱因，
   但**仍无机械门**。这是本 change 的核心诚实边界。

## ▶ 下一阶段建议

**Roadmap 回填**：— 无关联（`roadmap_writeback_draft.py` exit=3 `NO_ASSOCIATION`，本 change 非
roadmap 驱动，未产草稿）。

**建议的下一个 change（按优先级）**：

1. **收紧收尾票机械门（T289）** —— 唯一一条「真绕过口」性质的遗留项。本 change 因 Goals 锁死
   「机械层零改动」而不能碰它，那个约束在下一个 change 里不成立。做的时候注意：给收尾票加的
   格式约束**必须落在有界语法面上**（自有格式的机器锚行可以；别去解析验收标准的自然语言）。
   可与 **T290** 合并做——两者都是「新引入的信号/门缺一个真消费方或真判据」，同一片面。
2. **`sdflow-spec/SKILL.md` 体量门治理（T287）** —— 余量 66 字符意味着**下一个碰它的 change 一定
   会被迫做压缩**。与其每次现场挤，不如一次性决定：继续下沉到 `references/`，还是重新设计这个门。
   顺带可清 **T288**（给新 references 补契约测试）。
3. **文档漂移清理（T286 / T291）** —— 低优先，适合与别的 change 顺手 fold。T291 的修法按仓内既有
   惯例是**删掉硬编码数字**（让工具自己报），别再手工对齐。

**给下一个人的两句提醒**：

- 本 change 的交付物全是**指令文本**，仓内没有守其措辞的机械门（硬造断言文本的脆弱测试会撞
  CLAUDE.md 基准 5「无界语法禁手搓」）。∴ 它是否真的生效，**取决于执行方读到并遵守** ——
  这是已声明的诚实边界，评估其效果时别把「规则写下了」当成「规则生效了」。
- 本轮代码审里，**4 条采纳有 1 条独家来自跨模型 voice、且是最实质的那条执行分叉**（F1），
  2 条独家来自对抗镜，`broad` 与 `history` 本轮零产出。预算紧时的取舍参考。
