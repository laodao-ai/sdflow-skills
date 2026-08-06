# Task 5 impl-report：提示词与全量文档同步到自持 scope 审计的新提法

## 做了什么

把工作流文档、质量分层参考、编排器提示词、以及 `docs/` 下的技能说明 / 外部依赖说明 / 工作流总览 /
HTML 控制台页里，把 `sdflow-code-review` Step1 描述为「借道第三方 gstack `/review` skill 原生执行」的
地方，一律改述为「自持 scope 审计（fresh 子代理，以本 change 四件套为确定性意图源做 scope-drift +
完成度）」——措辞对齐 Task 3 在 `sdflow-code-review/SKILL.md` 中定下的提法。第三方 `/review` 说明文档
（`docs/workflow-skills/gstack-review.md`）保留，定位改述为「非运行时依赖的第三方 skill 参考」。

改动文件（10 个，均在本票文件所有权边界内）：

1. `sdflow-init/assets/workflow/workflow.md`（3 处：编排器描述 §三.B / 代码侧质量层 §三.6 / checklist 勾选项 §六）
2. `sdflow-init/assets/workflow/reference/quality-layering.md`（4 处：表格两行 §二 / 结构描述 §五 / checklist 勾选项 §六）
3. `sdflow-init/assets/workflow/prompts/step8-code-review.md`（唯一一行提示词）
4. `hack/tests/test_workflow_split.py`（needle fingerprint 同步；见下方 TDD 自检）
5. `docs/workflow-skills/sdflow-code-review.md`（技能说明：一句话 / mermaid 节点 / 步骤表 / 内部调度表 / 建议式-强制表 / 小结，共 6 处）
6. `docs/workflow-skills/gstack-review.md`（第三方 skill 说明文档：定位改述 + §1 契约表 + §5/§6 历史化标注，共 5 处）
7. `docs/workflow-overview.md`（工作流总览：外部黑盒清单拆分 / 步骤表第 8 步 / 黑盒边界表删行，共 3 处）
8. `docs/workflow-console.html`（HTML 控制台页：删 gstack/review 卡片 + 更新 sdflow-code-review 角色描述，共 2 处）
9. `docs/external-dependencies.md`（评审流程依赖表删行 + 加降级说明 / 内部依赖树改述，共 2 处）
10. `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`（生成物，`python3 hack/gen_workflow_guide.py --write` 同步再生，非手改）

`CLAUDE.md` 无 code-review 侧 gstack 提法（`grep -n "gstack" CLAUDE.md` 零命中），无需改动。

## 7 条验收标准逐条证据

1. **工作流主文档三处** —— `workflow.md`：
   - 编排器描述：`编排器：**每次全跑·独立冷·强制主审**〔P3c〕。Step1 自持 scope 审计（scope-drift + 完成度审计）+ 领域镜 + ...`
   - 代码侧质量层：`事后 **sdflow-code-review 编排器每次全跑**（Step1 自持 scope 审计 scope-drift+完成度，P3c ...`
   - checklist 勾选项：`sdflow-code-review 是否**每次全跑**（Step1 自持 scope 审计 scope+完成度、领域 code-checklists、对抗、置信过滤）？`
   - `grep -n "gstack" sdflow-init/assets/workflow/workflow.md` → 零命中。

2. **质量分层参考同步** —— `quality-layering.md`：表格两行（spec 合规 / scope-drift 计划完成度）、
   §五结构描述、§六 checklist 勾选项均已改述；`grep -n "gstack" .../reference/quality-layering.md` → 零命中。

3. **编排器提示词 + needle 断言** —— `prompts/step8-code-review.md` 唯一行改为
   `/sdflow-code-review 独立审查 {change dir} 的代码变更（Step1 自持 scope 审计的 scope-drift+完成度审计；...）`；
   `hack/tests/test_workflow_split.py` fingerprint 同步为 `"Step1 自持 scope 审计的 scope-drift"`。
   **TDD 自检**（改断言前先破坏、确认红）：改完提示词、改断言前先跑
   `/usr/bin/python3 -m pytest hack/tests/test_workflow_split.py -v` → 2 个测试红
   （`test_guide_is_in_sync_with_its_sources` + `test_prompts_are_not_inlined_back_into_the_table`，
   后者报 `prompts/step8-code-review.md 丢了特征串「并入 gstack/review 的 scope-drift」`）——
   证明该 needle 确实在盯这处改动。随后同步 fingerprint + 跑
   `python3 hack/gen_workflow_guide.py --write` 再生 `WORKFLOW-GUIDE.md`，复跑同一测试文件 → **5 passed**。

4. **docs 下代码审技能说明 / 外部依赖说明 / 工作流总览 / HTML 控制台页** —— 见上方改动文件 5/7/8/9；
   `docs/workflow-skills/sdflow-code-review.md` 复扫 `grep -n "gstack"` → 零命中（原 6 处全清）。

5. **第三方 review skill 说明文档保留，定位改述** —— `docs/workflow-skills/gstack-review.md` 未删除，
   顶部改为：
   ```
   > **定位：非运行时依赖的第三方 skill 参考**——`sdflow-code-review` 编排器的 Step1（scope-drift + 完成度）
   > 已改为自持 fresh 子代理实现（见 [sdflow-code-review 详解](./sdflow-code-review.md)），不再原生调用本 skill。
   > 本文保留作为 `/review` 自身设计的参考资料。
   ```
   §1 契约表「谁调它」行改为「无（本仓当前无 skill 运行时调用它...）」；§5 标题加「（历史，已不适用）」
   并加历史化说明块；§6 小结第三条明确「非运行时依赖的第三方 skill 参考」定位。

6. **全量 grep 复扫 + 逐条判定表** —— 见下方完整表格（不带 `--include` 限定，覆盖 `.md`/`.py`/`.sh`/`.html`）。

7. **与 Task 3 提法对照** —— 见下方对照表，措辞逐字一致。

## 与 Task 3 提法对照表

| 维度 | Task 3（`sdflow-code-review/SKILL.md`） | Task 5（本票，docs/workflow 侧） |
|---|---|---|
| 步骤标题 | `## 第一步：自持 scope 审计（fresh 中档子代理，恒跑守卫）` | `Step1 自持 scope 审计（fresh 中档子代理）` / `Step1 自持 scope 审计` |
| 一句话摘要 | `Step1 自持 scope 审计（scope-drift + 完成度）→ Step2 并行多镜...` | `Step1 自持 scope 审计（fresh 中档子代理，以本 change 四件套为确定性意图源做 scope-drift + 完成度）→ Step2 并行多镜...` |
| 机制描述 | `不借道第三方 skill 的原生执行，而是自己派一个 fresh 子代理，以本 change 目录的四件套为确定性意图源` | `以四件套为确定性意图源，做 scope-drift + 完成度审计` |
| 锚行 mode 枚举 | `mode="subagent\|main-session"`（新枚举，`native\|simulated` 退役） | 同步改用 `mode="subagent\|main-session"`（`sdflow-code-review.md` 步骤表 / 建议式-强制表两处） |
| 报告落款 | `Step1 自持 scope 审计: scope-drift/完成度 结论`（命中范围行） | 未涉及报告模板本体（不在本票文件所有权边界内） |
| 度量锚描述 | `broad（Step1 自持 scope 审计）` | 未改动（`lens-metric-contract.md` 属 Task 2 所有权，本票未触碰） |

措辞核对方法：`grep -n "自持 scope 审计\|scope-drift" sdflow-code-review/SKILL.md` 逐行核对后手工对齐，
未发现本票新造与 Task 3 冲突的措辞。

## 全量 grep 复扫 + 逐条判定表

命令：`grep -rln "gstack" . --exclude-dir=.git --exclude-dir=archive --exclude-dir=.claude`
（不带 `--include`，覆盖全部文件类型；`--exclude-dir=.claude` 排除另一 ticket 遗留的 worktree 副本
`.claude/worktrees/agent-*/`，其内容与仓根重复、非本票所有权范围）。

改动后剩余 **65** 个文件（含本票自身新增的 3 份产物：`task5-brief.md` / `task5-docs-sync.md` /
`task5-review-package.diff`，它们讨论 gstack 故字面命中）。〔impl-review-fix：原写「改动前 68 →
改动后 62」，双轴审 Spec 轴独立复扫实测为 65，本行汇总数字与判定表不符——**判定表本身逐条完整
准确、无遗漏无多余**，仅此汇总句算术有误，已订正。数字随产物增减而变，以上方命令实跑为准。〕
本票清除的 6 个：`sdflow-init/assets/workflow/workflow.md`、
`.../reference/quality-layering.md`、`.../prompts/step8-code-review.md`、`hack/tests/test_workflow_split.py`、
`docs/workflow-skills/sdflow-code-review.md`，以及生成物 `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`）。

| 文件 | 判定 | 依据 |
|---|---|---|
| `docs/external-dependencies.md` | **本票已改** | 代码审侧运行时依赖表行 + 内部依赖树，见上文 |
| `docs/workflow-console.html` | **本票已改** | task5-brief 5.3 明确点名防 .html 漏扫 |
| `docs/workflow-overview.md` | **本票已改** | brief 明确点名「工作流总览」 |
| `docs/workflow-skills/gstack-review.md` | **本票已改（保留+改定位）** | 验收标准 5：第三方文档保留、改述为非运行时依赖参考 |
| `docs/workflow-skills/sdflow-code-review.md` | **本票已改** | brief 明确点名「代码审技能说明」 |
| `hack/tests/test_workflow_split.py` | **本票已改** | needle fingerprint 同步 |
| `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md` | **本票已改（生成物）** | `gen_workflow_guide.py --write` 再生同步，非手改 |
| `sdflow-init/assets/workflow/prompts/step8-code-review.md` | **本票已改** | 编排器提示词本体 |
| `sdflow-init/assets/workflow/reference/quality-layering.md` | **本票已改** | brief 明确点名「质量分层参考」 |
| `sdflow-init/assets/workflow/workflow.md` | **本票已改** | brief 明确点名「工作流主文档三处」 |
| `docs/sdflow-fable5/01-goals-and-rationale.md` | 合法保留 | `docs/sdflow-fable5/` 明确列入「已实测的分布」历史文档白名单（2026-07-10 深度调研文档集），DOC-1 演进史进 archive 类比 |
| `docs/sdflow-fable5/02-module-reference.md` | 合法保留 | 同上；含旧六步流描述（`gstack/review 原生并入`），是该调研文档的历史快照，非当前流程真相源 |
| `docs/sdflow-fable5/04-optimization-proposal.md` | 合法保留 | 同上；引用 gstack pre-emit gate 作设计灵感来源，非描述当前依赖关系 |
| `docs/sdflow-fable5/20260717.md` | 合法保留 | 同上；日期戳快照（2026-07-17 会话记录），历史事实陈述 |
| `docs/skill-authoring-best-practices.md` | 合法保留 | 从 gstack 设计中提炼「可迁移做法」的横向总结文档，不描述 Step1 当前运行时依赖 |
| `docs/superpowers/plans/2026-07-08-lens-metric-emit.md` | 合法保留 | `docs/superpowers/` 明确列入历史文档白名单；含旧 fold 名 `gstack-adv: broad`，是该规划文档的历史快照 |
| `docs/workflow-skills/gstack-autoplan.md` | 合法保留（Non-Goals） | 设计审侧 autoplan 依赖，proposal Non-Goals 明写不动 |
| `docs/workflow-skills/gstack-document-generate.md` | 合法保留 | 无关的第三方 skill（文档生成），与代码审 Step1 无关 |
| `docs/workflow-skills/matt-pocock-workflow.md` | 合法保留 | 仅作对比参照（frontmatter 风格两极对比），非描述 Step1 依赖 |
| `docs/workflow-skills/sdflow-spec-review.md` | 合法保留（Non-Goals） | 设计审侧 autoplan 依赖及其产物 `gstack-review.md`（autoplan 落盘文件名，非本票范围） |
| `openspec/adr/0002-gstack-boundary-reuse-output-not-internals.md` | 合法保留 | ADR，归档决策记录 |
| `openspec/adr/0012-lens-metric-fold-machine-readable-and-emitter-input-roster.md` | 合法保留 | ADR，归档决策记录 |
| `openspec/adr/0037-roadmap-discussion-layer-internalization-and-matt-removal.md` | 合法保留 | ADR，与 roadmap/matt 相关，与代码审 Step1 无关 |
| `openspec/changes/absorb-gstack-review/*`（decision-memo/design/proposal/specs/tasks/tickets/gstack-review.md/spec-review-report.md/impl-reports/*） | 合法保留（禁改） | 本 change 自身四件套 + 决策纪要 + 评审报告 + 其它 task 的 impl-report，均是本 change 的工作产物本体（讨论「吸收 gstack」正是其主题），brief 明确「不要改四件套」 |
| `openspec/CONTEXT.md` | 合法保留 | 记录「读 gstack 产出物合法、调内部非法」的合规边界原则，非描述 Step1 当前依赖 |
| `openspec/issues/CLOSED.md` `openspec/issues/closed/todo/T20.md` `T25.md` | 合法保留 | 已关闭 issue 台账，历史记录 |
| `openspec/specs/{issues-scripts-shared-core,outside-voice-reuse-guard,spec-workflow,workflow-metrics}/spec.md` | 合法保留（archive 时机） | 主 specs 仅在 `sdflow-done` 归档时由 delta 同步刷新；本 change 尚在实现期，`openspec/changes/absorb-gstack-review/specs/*.md` 才是当前权威 delta（Task 1 所有权），不在本票范围 |
| `openspec/workflow/lens-metric-contract.md` `openspec/workflow/WORKFLOW-GUIDE.md` | 合法保留（预期漂移） | repo-root pin 副本，仅 `sdflow-init update` 时从 `sdflow-init/assets/workflow/` 权威源刷新；已核实权威源（Task 2 已改 `gstack-adv→scope-audit`）正确、repo-root 副本按纪律预期滞后，非本票范围 |
| `openspec/workflow/tools/outside_voice_guard.py` | 合法保留（Non-Goals） | proposal 显式「不动 `outside_voice_guard.py`」（spec-review 姊妹依赖，记 todo 另行处置） |
| `sdflow-init/assets/hack/outside-voice.sh` | 合法保留 | 注释「零 gstack 内部依赖」，描述本脚本自身零依赖这一事实，非 Step1 依赖 |
| `sdflow-init/assets/workflow/design-diagrams.md` | 合法保留 | 引用 gstack `plan-eng-review` 的画图纪律作设计灵感，与代码审 Step1 无关 |
| `sdflow-init/assets/workflow/lens-metric-contract.md` | 合法保留（权威源已改） | Task 2 已改 `gstack-adv→scope-audit`；复核 `grep -n "gstack-adv" .../lens-metric-contract.md` 零命中，仅保留在「历史注记」括注中提及旧名作对照，合规 |
| `sdflow-init/assets/workflow/reference/Spec_Quality_Collaboration.md` | 合法保留 | superpowers vs gstack 的对比分析文档，历史调研性质 |
| `sdflow-init/assets/workflow/tools/{anchor_lint,lens_metric_emit,outside_voice_guard}.py` `.../tests/test_{anchor_lint,hr_tg_intersect,lens_metric_emit,outside_voice_guard}.py` | 合法保留（Task 1/2 已完成/Non-Goals） | 工具脚本与其测试，brief 明确「不要改 tools/*.py」 |
| `sdflow-init/assets/workflow/workflow-history.md` | 合法保留 | 演进史文件本身（DOC-1 附录承载体），按定义应含历史提法 |
| `sdflow-init/tests/test_resolve_workflow.py` | 合法保留 | 注释引用一处历史 bug 编号（"gstack 5.3 缺口"），与 Step1 依赖无关 |
| `sdflow-retro/SKILL.md` | 合法保留 | 引用 gstack `retro`（团队周度复盘会，完全不同的 gstack 子 skill），非本票范围 |
| `sdflow-spec-review/SKILL.md` | 合法保留（Non-Goals） | autoplan 依赖 + 产物落盘文件名 `gstack-review.md`，proposal Non-Goals 明写不动 |

## 跑过的测试

```
/usr/bin/python3 -m pytest hack/tests/test_workflow_split.py -v
# 改断言前（TDD 自检）：2 failed, 3 passed
# 改断言 + 再生 WORKFLOW-GUIDE.md 后：5 passed

python3 hack/gen_workflow_guide.py --check
# ✅ WORKFLOW-GUIDE.md 与单一源一致

/usr/bin/python3 -m pytest
# 2466 passed, 10 skipped in 298.50s
```

## Concerns

- `docs/workflow-skills/sdflow-code-review.md` 尾部「接地基线」脚注引用的 SKILL.md 行号
  （如 `trivial_shape 前置 :62-70`）未核对是否因 Task 3 改动而漂移——**不在本票验收标准范围内**
  （与 gstack 提法无关，属该文档另一处独立的接地基线维护问题），未动。
- `openspec/specs/*` 主 specs 目录仍保留旧 gstack/review 提法（见判定表），这是归档时机问题而非
  遗漏——待 `sdflow-done` 归档本 change 时由 delta 同步刷新，非本票（也非任何实现期票）职责。
- `openspec/workflow/`（repo-root pin 副本）与其权威源 `sdflow-init/assets/workflow/` 存在已知预期
  漂移（本仓 memory 已记录此模式：`deployed-copy-drift-surfaces-only-on-update.md`），仅 `sdflow-init update`
  时刷新，非本票范围。
