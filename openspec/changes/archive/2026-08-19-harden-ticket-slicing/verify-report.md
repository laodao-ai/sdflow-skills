---
ship-gate:
  verify: PASS
  reviewed_sha: 0fb64224cd98de9bd5212ea321313176c9ead9f0
---

# Verify Report — harden-ticket-slicing

**日期**：2026-08-19
**Change**：`harden-ticket-slicing`
**审查基准 SHA**：`0fb64224cd98de9bd5212ea321313176c9ead9f0`（当前 HEAD）

## 结论

**PASS**

全部需求（3 个 capability 的 1 MODIFIED + 2 ADDED，以及 tasks.md 全部 11 条）均在实际文本中落地并可锚定到
`文件:行`。实现期聚合覆盖需求的证据存在且各通过层锚同一 SHA。代码审阶段 4 条自动修复（`966e4d2`）对
delta spec 的修订与实际落地文本三方口径一致。无核心缺口；1 条 Minor（已知且被 spec 显式接受的证据时效
缺口），且本轮 verify 已在 HEAD 上独立复跑两条命令将其实质补齐。

**复选框说明**：本 change 的 `tasks.md` 复选框由收尾期批量勾选，无证据价值；下表每一行的判定均来自对
文件实际内容的直读/grep，不依赖复选框与任何既有报告的措辞。

## 逐需求核对表

| 需求/任务 | 代码出处(文件:行/测试) | 状态 |
|---|---|---|
| **T1.1** ff-generation-constraints §切片建议 MAY→SHOULD + 缺席理由 + 「有节或有理由」二择一恒成立 | `sdflow-init/assets/workflow/ff-generation-constraints.md:38-41`（「**SHOULD** 含」「节缺席时决策区 **MUST** 写明一句为何不需要——二择一恒成立，不存在两者皆缺的合规态」） | ✅ |
| **T1.1(续)** 票数预算兼容提示（3–6 张垂直切片 / expand–contract 例外依据） | 同上 `:43-47`（「草图票数须落 **3–6 张垂直切片**预算内；超出该预算须在节内注明 expand–contract 例外依据」+ 单票交付并列例外） | ✅ |
| **T1.2** BASE-31 新增（存在性 + 缺席理由成立性 + 切片内聚质量 + 票数预算兼容） | `sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md:55`（四项判据齐全，末列 `R`） | ✅ |
| **T1.2(续)** BASE-31 显式限定适用域 = change 四件套 design.md，roadmap 三件套 N/A | 同上 `:55`（「适用域 = change 四件套评审的 design.md；roadmap 三件套无切片建议契约，本项 N/A」） | ✅ |
| **T1.2(续)** 归镜靠既有默认规则、不改任何镜表 | 同上 `:55` 末句；`git diff --stat` 未触碰 `sdflow-spec-review/SKILL.md` 镜表（默认规则见 `sdflow-spec-review/SKILL.md:248,252`） | ✅ |
| **T1.3** 新增 `change-decomposition-standard.md`：拆分 4 规则 + why | `sdflow-init/assets/workflow/reference/change-decomposition-standard.md:12-37`（规则 1 完整阶段结果 / 规则 2 不按来源批次凑票 / 规则 3 fold 优先且判定入口 = BASE-18 AND 门 / 规则 4「缺依赖模块」是经典 defer 形态 + Why 两段） | ✅ |
| **T1.3(续)** 「唯一合理 defer」绝对句被显式否定〔D6〕 | 同上 `:22-25`（「不是与规则 3 的 AND 门并列的『唯一合理 defer』绝对句……不得被写成排除其它 defer 理由的绝对句」） | ✅ |
| **T1.3(续)** 与 BASE-18 互为指针不复制正文 | 同上 `:9-10` + `:20-21`（「本文不复述」）；`spec-quality-base.md:55` 反向指回 | ✅ |
| **T1.4** INDEX 同步登记新增 reference 文件（两侧一致） | `openspec/INDEX.md:25-26` 与 `sdflow-init/assets/snippets/index-section.md:20-21`，两侧同文本（diff 仅在托管块之外的本仓专属章节） | ✅ |
| **T2.1** 出票起手：切片建议消费语义「建议输入」→「默认采纳 + 偏离审计」 | `sdflow-implement/SKILL.md:256-260`（「作为**默认切分方案**采纳——**不是**参考输入」；行格式「切片偏离: <偏离点> \| <理由(三镜+主次)>」落 `impl-reports/planning-decisions.md`，「MUST NOT 静默偏离」） | ✅ |
| **T2.2** T10-choice 必触发三条件（含 Q1-A 口径：合规缺席不触发、缺席理由与出票矛盾视同条件③） | `sdflow-implement/SKILL.md:262-268`（条件 1/2/3 逐条列出；条件 1 内嵌「有成立缺席理由的合规缺席不触发本条——但……>1 张功能票 ⇒ 视同条件 3 矛盾触发」） | ✅ |
| **T2.2(续)** 保留既有粒度争议路径 + 三级协议出口（证伪/无从复核 ⇒ 停并上抛）+ 诚实边界句 | 同上 `:262`（「既有『粒度争议』触发路径保留不变，与下列三条件并存」）、`:271-272`（「证伪或无从复核 ⇒ 停并上抛，**MUST NOT** 以被证伪的切分方案继续出票」）、`:274-275`（「指令层约束，MUST NOT 被表述为机械保证」）、`:280-282`（粒度争议同走 T10-choice、记录同落 planning-decisions.md） | ✅ |
| **T2.3** 执行模式「票外发现上报」段：MUST NOT 自行扩 scope、编排层按 BASE-18 AND 门判 fold/defer、判定记一行入 impl-report | `sdflow-implement/SKILL.md:650-673`（AND 门 `:653-656`；fold 时序边界 `:664-670`；defer 显式带 `change` 字段 `:671-672`；「判定与去向 SHALL 记一行入该票 impl-report」`:673`） | ✅ |
| **T2.3(续)** implementer dispatch 模板同步加上报指令 | `sdflow-implement/SKILL.md:619-625`（dispatch 必含项，含 `## 票外发现` 小节 + `[has-off-ticket-finding]` 标注） | ✅ |
| **T3.1** sdflow-spec B.7 收敛前检查新增 scope 内聚检查（引单一源、偏离呈现给人拍板不静默调整） | `sdflow-spec/SKILL.md:372`（B.7 第 3 项，「MUST 读 `references/scope-cohesion-check.md`……MUST NOT 静默调整范围」）+ `sdflow-spec/SKILL.md:182`（按需资料路由清单，保证该文件会被加载）+ `sdflow-spec/references/scope-cohesion-check.md`（判据指针引用、处置、示例） | ✅ |
| **T3.2** sdflow-roadmap 阶段拆分处加拆分标准指针 | `sdflow-roadmap/SKILL.md:215-218`（经 `resolve-workflow.sh` 解析、「指针引用 MUST NOT 复制标准文本」、三条 MUST NOT 与 spec 逐条对应） | ✅ |
| **T3.3** sdflow-code-review Step4 defer 流加 fold/defer 判定指针 | `sdflow-code-review/SKILL.md:403-405`（related finding 先过 BASE-18 AND 门；完整规则与 why 见单一源） | ✅ |
| **T4.1** T141 set-status DONE（resolved_by + evidence 指向单一源与三处引用） | `openspec/issues/closed/todo/T141.md` frontmatter `status: "DONE"` / `resolved_by: "harden-ticket-slicing"` / `closed_date: "2026-08-19"`；正文末行 evidence 列出单一源 + 五处引用行号；commit `c0b6eb2` | ✅ |
| **T4.2** 回归验证（全仓 pytest + `sync_principles.py --check`）并贴输出 | `impl-reports/task5-impl-verify.md:5-15`（证据块 + 输出摘要）；本轮 verify 在 HEAD `0fb6422` 独立复跑：`/usr/bin/python3 -m pytest -q` → `2601 passed, 10 skipped in 380.36s`，rc=0；`python3 hack/sync_principles.py --check` → `✅ 27 个投放面全部与真相源一致`，rc=0 | ✅ |
| **spec-authoring / SA-17**：相位 B scope 内聚检查 | 同 T3.1 锚点（`sdflow-spec/SKILL.md:372` + `references/scope-cohesion-check.md`） | ✅ |
| **spec-authoring / SA-17**：相位 C 遵循「切片建议」SHOULD 语义（有节或有理由二择一） | 生成侧规范落 `ff-generation-constraints.md:38-47`；相位 C 经 `openspec instructions --json` 的 rules/context 消费该规则（`sdflow-spec/SKILL.md:436-437` 要求 workflow 引用经 resolver 解析后全文读；`openspec/config.yaml:10` 与 `sdflow-init/assets/workflow/config.template.yaml:26` 的 context 已把该文件自述扩为「D-1~D-6 + 切片建议」，可发现性闭合） | ✅ |
| **roadmap-planning**：阶段拆分锚定 change 拆分标准（ADDED） | 同 T3.2 锚点（`sdflow-roadmap/SKILL.md:215-218`） | ✅ |
| **impl-orchestration**：出 ticket 模式（MODIFIED）—— 消费语义 + 必触发三条件 + 单票交付并列例外 | `sdflow-implement/SKILL.md:256-288`；三方口径一致核验见下「代码审修订一致性核验」 | ✅ |
| **impl-orchestration**：执行期票外发现上报（ADDED）—— 上报通道比照 `DONE_WITH_CONCERNS` 形状 | `sdflow-implement/SKILL.md:619-625`（写入侧）+ `:658-662`（读取契约：MUST Read 小节全文，MUST NOT 仅凭一行摘要判定），与 spec `:138` 逐句对应 | ✅ |
| **impl-orchestration**：执行期新增票补齐强制字段与闸门〔impl-review-fix〕 | `sdflow-implement/SKILL.md:668-670`（`Blocked-by` / `R-ID` / 验收复选框 / 语法面有界性闸门，或显式列出豁免哪些、为何） | ✅ |
| **实现期聚合覆盖（无条件要求，`R-ID: all` 收尾票）** | `openspec/changes/harden-ticket-slicing/impl-reports/task5-impl-verify.md`：单元层 `/usr/bin/python3 -m pytest -q` rc=0 @ `efc37b8d3f7c0ff5c5e869ff56cba4b998dc1d4c`；托管块回归 `python3 hack/sync_principles.py --check` rc=0 @ **同一 SHA**；集成层/e2e 层记「未覆盖（本仓无此层）」并附判定依据（`:28-38`）。收尾票在 `tickets.md:120-121`（`Blocked-by: 1,2,3,4` / `R-ID: all`）。**锚语义 = 实现期结束时聚合套件通过** | ✅ |

### 「实现期聚合覆盖」SHA 单一盘面核验

两条判「通过」的证据行均锚 `efc37b8d3f7c0ff5c5e869ff56cba4b998dc1d4c`，无跨 SHA 拼接；该 SHA 对应
`efc37b8 checkpoint(harden-ticket-slicing:task4-t141-closure)`，位于全部 4 张功能票完成之后、收尾票执行
当时，符合「全部功能票实现完毕这一刻」的语义。未覆盖层（集成/e2e）按契约不参与本核验。

### 代码审修订一致性核验（步骤 5，本轮特有）

`966e4d2`（`[impl-review-fix]`，4 条自动修复）同时改了 delta spec 与落地文本，逐条核对：

1. **单票交付例外三方口径** —— spec `specs/impl-orchestration/spec.md:5`（「design.md 写明成立的『单票交付』
   缺席理由且出票确为 1 张功能票时，是与 expand–contract 并列的合法例外，同样不受该预算约束」）
   / bundle `ff-generation-constraints.md:43-47`（「不足预算也有一条与 expand–contract 并列的合法例外……
   该例外不需要额外注明依据，缺席理由本身即依据」）/ SKILL `sdflow-implement/SKILL.md:286-288`
   （「与下方 expand–contract（超出预算）例外并列，不视为违反本预算」）—— **三方一致**。
2. **票外发现上报通道契约** —— spec `:138`（写入 `## 票外发现` 小节 + 摘要标 `[has-off-ticket-finding]`；
   编排层 MUST Read 全文，MUST NOT 仅凭摘要判定）与 SKILL `:619-625` / `:658-662` 逐句对应，Scenario `:143`
   亦与 SKILL 措辞一致 —— **一致**。
3. **fold 新增票的出票期治理** —— spec `:138` 括号内新增句 vs SKILL `:668-670` —— **一致**。
4. **ff-generation-constraints 自述范围扩为「+ 切片建议」（四处摘要口径）** —— `openspec/INDEX.md:17` /
   `sdflow-init/assets/snippets/index-section.md:12` / `openspec/config.yaml:10` +
   `sdflow-init/assets/workflow/config.template.yaml:26` / `workflow-rules-guide.html`，另加文件自身定位声明
   `ff-generation-constraints.md:3` —— **全部已扩，无遗漏**。

## 缺口清单

### 核心缺口（FAIL 项）

无。

### Minor 缺口（可接受 / deferred）

1. **聚合覆盖证据的时效缺口（已知且被 spec 显式接受）**：收尾票证据锚在 `efc37b8`，其后的
   `7e53407` / `664d2f2` / `966e4d2` / `0fb6422` 未被该票覆盖 —— 这正是
   `specs/impl-orchestration/spec.md:31` 明写的残余风险（锚语义限定为「实现期结束时聚合套件通过」，
   code-review 之后的修复由其自身机制覆盖）。**本轮 verify 已在 HEAD `0fb6422` 独立复跑两条命令，
   均 rc=0**（pytest `2601 passed, 10 skipped`；sync_principles `27 个投放面全部一致`），该缺口在事实上
   已补齐；spec 层面的锚语义保持不变，不因此改写。
2. **相位 C「切片建议」规则的加载路径是间接的**：`sdflow-spec/SKILL.md` 本身不出现「切片建议」字样，
   相位 C 靠 `openspec instructions --json` 的 rules/context 拉到 `ff-generation-constraints.md` 全文。
   `966e4d2` 已把 context 自述从「D-1~D-6」扩为「D-1~D-6 + 切片建议」，可发现性闭合；仍属指令层约束
   而非机械保证。可接受，无需改动（再加一处硬编码引用反而制造第二个漂移面）。
