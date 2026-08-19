## 1. bundle 规则面（对应切片建议 T-a）

- [ ] 1.1 `sdflow-init/assets/workflow/ff-generation-constraints.md` §切片建议：MAY→SHOULD，加缺席理由要求（缺席须在 design.md 写一句为何不需要）与「有节或有理由」二择一恒成立措辞；另加票数预算兼容提示——草图票数须落 3–6 张垂直切片预算、或在节内注明 expand–contract 例外依据〔spec-review-amendment D1〕〔R: SA-17〕
- [ ] 1.2 `sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md` 新增 BASE-31（切片建议存在性 + 缺席理由成立性 + 切片内聚质量 + 草图票数与出票预算兼容〔3–6 张垂直切片或 expand–contract 例外〕〔spec-review-amendment D1〕；条文显式限定适用域 = change 四件套评审的 design.md——roadmap 三件套无切片建议契约，该场景 N/A〔spec-review-amendment D4〕；归镜靠既有默认规则，不改任何镜表）〔R: SA-17〕
- [ ] 1.3 新增 `sdflow-init/assets/workflow/reference/change-decomposition-standard.md`：拆分 4 规则 + why（一个 change/phase = 一个完整阶段结果；不按来源批次/凑票拆；相关发现 fold 优先，defer 判定入口 = BASE-18 防吸积 AND 门——任一不满足即 defer，真独立/扩容大/需自身设计审查/高 blast-radius 天然落 defer；缺依赖模块 → 占位 + 记 todo 是 related 语境下的经典 defer 形态，MUST NOT 写成与 AND 门并列矛盾的「唯一合理 defer」绝对句〔spec-review-amendment D6〕）；与 BASE-18 互为指针不复制（标准文讲 why 与完整规则，BASE-18 是评审判定入口）〔R: SA-17 / 阶段拆分锚定 change 拆分标准 / 执行期票外发现上报〕
- [ ] 1.4 `openspec/INDEX.md` 同步登记新增的 reference 文件〔R: —（CLAUDE.md 既有 INDEX 同步纪律）〕

## 2. 出票侧（对应切片建议 T-b）

- [ ] 2.1 `sdflow-implement/SKILL.md` 出票模式起手检查段：消费语义「建议输入」→「默认采纳 + 实质偏离逐条记 `impl-reports/planning-decisions.md`（行格式「切片偏离: <偏离点> | <理由(三镜+主次)>」）」〔R: 出 ticket 模式产出 tracer-bullet ticket（MODIFIED）〕
- [ ] 2.2 `sdflow-implement/SKILL.md` 同段：T10-choice 复核必触发三条件（无切片建议 ∨ 实质偏离 ∨ 草图与 design 正文矛盾），保留既有粒度争议路径，附诚实边界句（指令层约束非机械保证）；复核结论接三级协议出口——证伪/无从复核 ⇒ 停并上抛，MUST NOT 以被证伪的切分方案继续出票〔spec-review-amendment D2〕〔R: 出 ticket 模式产出 tracer-bullet ticket（MODIFIED）〕
- [ ] 2.3 `sdflow-implement/SKILL.md` 执行模式：新增「票外发现上报」段——implementer MUST NOT 自行扩 scope，上报编排层按拆分标准（BASE-18 AND 门）判 fold/defer，判定记一行入该票 impl-report；implementer dispatch 模板同步加上报指令〔R: 执行期票外发现上报编排层按拆分标准判 fold/defer（ADDED）〕

## 3. 三处消费点引用（对应切片建议 T-c）

- [ ] 3.1 `sdflow-spec/SKILL.md` B.7 收敛前检查：新增 scope 内聚检查（引拆分标准单一源，发现偏离呈现给人拍板不静默调整）〔R: SA-17〕
- [ ] 3.2 `sdflow-roadmap/SKILL.md`：阶段拆分处加拆分标准指针引用（每阶段 = 一个完整阶段结果，不拆散不混拼）〔R: 阶段拆分锚定 change 拆分标准（ADDED）〕
- [ ] 3.3 `sdflow-code-review/SKILL.md` Step4 defer 流：加 fold/defer 判定指针（related 发现先过 BASE-18 AND 门再定去向，对齐 spec-workflow 既有 fold-vs-defer 条款）〔R: —（SKILL 层对既有 spec 条款的对齐，无新 delta）〕

## 4. 收尾（对应切片建议 T-d）

- [ ] 4.1 T141 set-status DONE：用开发 checkout 脚本（`sdflow-issues/scripts/`，勿用 ~/.claude/skills symlink），resolved_by = harden-ticket-slicing，evidence 指向 1.3 的单一源文件与三处引用〔R: —（issues 池纪律）〕
- [ ] 4.2 回归验证：`/usr/bin/python3 -m pytest`（全仓）+ `python3 hack/sync_principles.py --check`（确认被改 SKILL.md 的托管块未损）；贴输出〔R: 全部〕
