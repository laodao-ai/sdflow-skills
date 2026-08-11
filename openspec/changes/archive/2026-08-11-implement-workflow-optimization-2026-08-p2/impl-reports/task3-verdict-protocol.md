# Task 3 — 裁决协议重写 + 联动核查（impl-report）

## 范围回顾

Blocked-by 1（validator `findings_ref_check.py`，已由 task1 落地于 `sdflow-init/assets/workflow/tools/`）、
2（roster/dispositions，task2）。本票交付 tasks.md 1.5 描述的三部分：

- **A**：`sdflow-code-review/SKILL.md` Step3 重写。
- **B**：`sdflow-spec-review/SKILL.md` Step3 对齐。
- **C**：`spec-workflow` 主 spec 联动核查（grep 全仓「置信过滤 / <80 / 豁免」消费点，逐处改齐或确认不动）。

## A. sdflow-code-review Step3 重写

`sdflow-code-review/SKILL.md`：

- 删除：<80 数值滤（原「置信过滤」步骤全段）、置信封顶 ≤50 条款（pre-emit 引文纪律里的「两者皆无 ⇒
  自报置信 MUST ≤50」）、跨模型豁免矩阵条款（outside-voice 豁免〔R4·D8〕整段）。
- 新增：Step3 重写为「机械引用核前置（三态 pass/fail/uncheckable + 脚本级 degraded 降级）→ 二元裁决
  （采纳/裁掉/defer + critique）→ 置信仅排序」三层；机械引用核调
  `python3 $RULES_ROOT/tools/findings_ref_check.py --input <构造的f> --root <repo_root>`；
  合并池 >100 条时分批（每批 ≤50，批间携带已裁清单防重复采纳/裁决）。
- 「已裁掉」区新增 `[ref-check]` 来源标记，区分机械裁掉与二元裁决裁掉。
- frontmatter description Step3 括注改「机械引用核+二元裁决」，显式删「(<80 滤除)」字样。
- Step2 各镜 prompt 输出契约改为强制结构化字段 `{file, line, quote}` / `evidence_pack`（+ 自报置信仅供排序）。
- 报告格式区、模型选择表（弱档不再含「置信过滤」职责）、与官方 code-review 分工表、末尾「注意」区同步改齐。

## B. sdflow-spec-review Step3 对齐

`sdflow-spec-review/SKILL.md`：

- Step3 裁决动作层接入同一机械引用核前置（脚本、契约与 A 相同；核对象含四件套文档 + 代码），>100 条同样
  分批。
- 保留既有「高/中/低置信分流 → 对抗裁决 → 决策登记区」三分路由，显式重申与置信数字脱钩（spec-review 本
  就无数值滤，此处只是把这一事实与 code-review 同期退役的数值滤/跨模型豁免矩阵对齐说明）。
- 决策登记区格式新增 `[ref-check]` 已裁掉行样例。
- Step2 输出契约（含 broad-mirror-def 共享源 `sdflow-init/assets/snippets/broad-mirrors.md`，同时投放
  `sdflow-spec-review` 与 `sdflow-roadmap`）同步改结构化字段，已跑
  `python3 hack/sync_principles.py --apply` 回填两个投放面（`--check` 复核绿）。

## C. spec-workflow 主 spec 联动核查

`grep -rn "置信过滤\|<80\b\|跨模型豁免\|封顶.*50"` 全仓扫描，按「SKILL / bundle 规则 / spec / 测试」
（tasks.md 1.5 括注的四类范围）逐处核查处置：

**已改齐**：
- `sdflow-code-review/SKILL.md`、`sdflow-spec-review/SKILL.md`（见 A/B）。
- `sdflow-implement/SKILL.md`（收尾票段引用 code-review 保障机制描述）。
- `sdflow-init/assets/workflow/workflow.md`（bundle 权威源，两处描述 + 自检清单项）→ 重跑
  `python3 hack/gen_workflow_guide.py --write` 重生成 `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`
  → `cp` 同步至仓内唯一落地副本 `openspec/workflow/WORKFLOW-GUIDE.md`（`gen_workflow_guide.py --check` 绿）。
- `sdflow-init/assets/workflow/spec-review.md`（code-review/spec-review 裁决动作层不对称表，改为反映
  「共享机械引用核，仅裁决层对纯判断分歧的去向不同」）。
- `sdflow-init/assets/workflow/reference/quality-layering.md`（一处描述）。
- `openspec/specs/spec-workflow/spec.md`：
  - 新增 **ADDED Requirement**「评审裁决协议为机械前置 + 二元裁决 + 置信降排序」+ 6 条 Scenario——
    与本 change 的 delta spec（`openspec/changes/implement-workflow-optimization-2026-08-p2/specs/
    spec-workflow/spec.md`，phase-C 已生成、经 spec-review-report.md 审过）逐字一致，作为其余
    Requirement 的交叉引用锚点。
  - **MODIFIED**「outside-voice tension 不静默采纳」：同样对齐该 delta 的 MODIFIED 文本（含全部
    Scenario 集合，替换旧的「置信过滤豁免」段落 + 3 条置信阈值相关 Scenario）。
  - `sdflow-code-review 为每次全跑的独立强制主审` Requirement 的 Step2 枚举短语同步改齐（含
    `〔adr/0041〕` 标注，与 delta 一致）。
  - `代码审 finding 须引出触发行原文（pre-emit 引文纪律）` Requirement——**该 Requirement 不在本 change
    delta 的 MODIFIED 列表内**（delta 只新增/修改了另外三个 Requirement），但其正文原引用「Step3 置信
    过滤 SHALL 滤出主结论」「自报置信 MUST ≤50」等已失效表述，按 1.5 的 grep-残留核查职责一并改齐：
    引文字段结构化（`{file,line,quote}`/`evidence_pack`）、机械核验边界拆两层（① 引文位置真实性=
    machine-verified via `findings_ref_check.py`；② 「是否真属非局部类」自报分类=仍无核验，产出纪律
    非机械门），Scenario 改为「机械裁掉 + `[ref-check]` 标记」。
- `openspec/specs/host-adaptive-execution/spec.md`：两处（禁止自审 Scenario 的示例枚举、「锚行合法组合
  矩阵…」Requirement 正文的下游 consumer 引用）改为不再点名「置信过滤豁免」这一已退役 consumer，同时
  **矩阵定义本身逐字未动**（C7 边界：`anchor_lint` 矩阵保留）。
- `hack/check_async_branch_parity.py` 头注释一处（解释 `Step3` 术语跨两 SKILL 成立的理由）。

**确认不动（历史record/已知边界，非本票消费点）**：
- `adr/0041` 本身——历史决策记录，其「validator …（弱档…）」括注同步属 tasks.md 5.1（task 5），非本票。
- `README.md` / `CLAUDE.md` / `AGENTS.md` / `sdflow-init/assets/snippets/claude-section.md` 的技能一览表
  行——tasks.md 5.1 明写「README/INDEX 若涉及则同步」，属 task5 范围，非 1.5（SKILL/bundle规则/spec/测试）
  四类列举范围。
- `docs/**`（`workflow-map.md`、`workflow-overview.md`、`workflow-skills/*.md`、
  `criteria-mechanization-tracker.md`、`skill-authoring-best-practices.md`、
  `opus-agentic-instruction-system.md`、`workflow-optimization-research-2026-08.md`、`sdflow-fable5/*`）——
  同样超出 1.5 括注的四类范围（不属 SKILL/bundle规则/spec/测试）；其中多份为带时间戳的调研/建议快照
  （本 change 的输入源，如 04-optimization-proposal.md 即 T112 的提案出处），按 DOC-1 判据不追溯改写。
  建议：若需要保持这套人读文档集与新协议同步，另开一次面向 `docs/` 的文档同步 pass（不在本票 scope）。
- `openspec/changes/archive/**`、`openspec/roadmaps/archive/**` 下的历史报告/规格——归档即冻结历史记录，
  不回改。
- `sdflow-init/assets/workflow/tools/tests/fixtures/task_log_review_ok_wco.md`——从
  `openspec/roadmaps/archive/workflow-cost-optimization/task-log.md` 逐字摘录的历史 fixture（供
  `test_review_disposition_check.py` 测结构分类，非语义断言），命中的「置信过滤丢弃 findings」是被摘录
  文档里的历史决策描述，非当前协议断言。
- `openspec/issues/{INDEX.md,CLOSED.md,open/todo/T112.md}`——T112「弱档 validator 复核层：置信过滤后复核
  findings 引用真实性」与本 change 的 DD4（validator = 纯机械脚本，非弱档模型）实质相关但取向不同（DD4
  明确砍掉「弱档子代理逐条核」这一候选）；是否据此关闭/改写 T112 不在 tasks.md 1.5 列举范围内（该项无
  R-裁决/R-voice/R-全跑 tag），留给 issues 池的常规分诊处理，本票不越权代为处置。

## 验证

- `python3 hack/sync_principles.py --check` → ✅ 22 个投放面全部与真相源一致。
- `python3 hack/gen_workflow_guide.py --check` → ✅ 与单一源一致。
- `python3 hack/check_async_branch_parity.py` → ✅ 2 处 async host 调度段逐字节一致（确认 Step3 术语改动
  没有误触碰 `sdflow:async-branch` marker 段内文本）。
- 全仓 `grep -n "置信过滤\|<80\b\|跨模型豁免\|封顶.*50"` 复核：`sdflow-{code,spec}-review/SKILL.md` 内
  仅剩解释「取代了什么」的回顾性引用（非现行条款残留）；`openspec/specs/{spec-workflow,host-adaptive-
  execution}/spec.md` 同理。SKILL / bundle 规则 / spec / 测试四类范围内无遗漏残余消费点。
- `/usr/bin/python3 -m pytest -q`（全仓）：见下方「测试结果」。

### 测试结果

`/usr/bin/python3 -m pytest -q`（全仓）：**2548 passed, 10 skipped in 358.63s**，0 failed。本票未修改任何
Python 脚本本体，改动全为 Markdown/spec 文本 + 一次性的 `gen_workflow_guide.py --write` 重生成 +
`broad-mirrors.md` 源改动 → `sync_principles.py --apply` 回填；与全仓测试无耦合，跑绿符合预期。

## 未做 / 已知边界

- `docs/` 目录下的人读参考文档集（workflow-map / workflow-overview / workflow-skills 详解等）仍含旧术语
  「置信过滤 / <80」，按 1.5 的四类范围（SKILL/bundle规则/spec/测试）判定超出本票 scope，未改。这些文档
  的头部普遍自陈「视图文档，非真相源，源码变更后需同步」——建议后续开一次专门的文档同步 pass。
- `T112`（`openspec/issues/open/todo/T112.md`）未处置，留待常规 issues 分诊。
- `README.md`/`CLAUDE.md`/`AGENTS.md`/`claude-section.md` 的技能一览表行未改，按 tasks.md 5.1 归属 task5。

## 状态

DONE——A/B/C 三部分与 tickets.md 验收标准 7 条全部完成；机械门（`sync_principles.py --check`、
`gen_workflow_guide.py --check`、`check_async_branch_parity.py`）全绿；全仓 pytest 2548 passed / 10
skipped / 0 failed。「未做」节列出的三类项（docs/ 同步、T112 处置、README/CLAUDE/AGENTS 一览表）经
tasks.md 1.5 括注范围（SKILL/bundle规则/spec/测试）与 5.1 任务分工核实均不属本票 scope，非本票遗漏。
