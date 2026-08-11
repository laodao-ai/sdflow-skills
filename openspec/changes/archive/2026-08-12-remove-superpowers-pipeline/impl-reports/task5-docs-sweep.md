# Task 5：docs 与全仓扫尾 — 实现报告

**Blocked-by**：1,2,3,4（均已 checkpoint PASS）
**R-ID**：R7

## 1. docs 收口

- `docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md`：头部加一行「已过时」标注，指向 `openspec/adr/0042-tickets-sole-impl-pipeline.md`。
- 现役视图文档（`docs/workflow-overview.md` / `docs/workflow-map.md` + `.html` / `docs/workflow-console.html` / `docs/criteria-mechanization-tracker.md`）：全部 mermaid 图、阶段表、黑盒 skill 清单、注入项定性表、ship_gate verdict 表里的 `writing-plans` / `subagent-driven-development` / `superpowers:*` 叙述改写为 `sdflow-implement`（mode=tickets-plan / tickets-exec，出票/执行两模式，每 ticket 双轴审 Standards+Spec）。`workflow-map.md` §5b「管线路由」判据行整体删除（路由已被 adr/0042 删除，无残留判据可跟踪，行号不回收注明理由）；`workflow-console.html` 的「外部黑盒」matrix 里两张 superpowers 卡片改为「自制编排器 · 阶段三实现」下的 `sdflow-implement` 单卡。保留的历史参考链接（[superpowers writing-plans](../workflow-skills/superpowers-writing-plans.md) 等）均加了「已退役，见 adr/0042」的显式标注，不再是运行时依赖。

## 2. ADR 互指

- `openspec/adr/0033-tickets-plan-filename-split-by-track.md` 头部加 `> **Superseded by [adr/0042](./0042-tickets-sole-impl-pipeline.md)**`。
- `openspec/adr/0042-tickets-sole-impl-pipeline.md` 头部加 `> Supersedes [adr/0033](./0033-tickets-plan-filename-split-by-track.md)`。
- 两文正文其余逐字不动（已核对 diff，仅新增指针行）。

## 3. CLAUDE.md 手写段修正

- `CLAUDE.md:215`（`sdflow-init 铺设托管区块`外的手写「反向窗口」段）：删除「已开 `impl-pipeline: tickets` 的仓」这一前提从句——tickets 现为无条件唯一管线，不再需要按键值分诊；改写为「窗口期触发 RUN_PLAN 会调不存在的 sdflow-implement（实现管线唯一为 tickets，无需判 `impl-pipeline` 键存在性）」。
- 与同文件 `CLAUDE.md:426`（托管区块内，任务1-4已正确写为「实现管线唯一 = tickets」）核对一致，无矛盾。

## 4. grep 扫尾（Success Metrics 判据）

`grep -rn "superpowers" --exclude-dir=archive --exclude-dir=.git .` 逐条分类核验，运行时路径（scripts / SKILL / bundle assets / specs 主文件）仅剩以下合法残留：

- **upstream-watch 追踪目标**：`sdflow-upstream-watch/{SKILL.md,scripts/upstream_watch.py,tests/}`、`README.md`、`openspec/specs/upstream-watch/spec.md`、`openspec/upstream/*` —— superpowers 是被追踪的四个上游源之一，逻辑本身要保留。
- **superpowers 插件非管线技能引用**：`sdflow-roadmap/SKILL.md`（`/superpowers:brainstorming` 深度设计场景切换）、`openspec/CONTEXT.md`（gstack/superpowers 合规边界线，适用于任何第三方插件，非管线专属）。
- **docs 历史参考**：`docs/design-methodology.md`（案例记录当时真实发生的 scope 决策，改写=伪造审计）、`docs/sdflow-fable5/*`、`docs/skill-authoring-best-practices.md`（明确标注"提炼自 gstack/superpowers/grill"的设计灵感来源）、`docs/skill-namespace-research.md`、`docs/windows-pytest-remediation-inventory.md`、`docs/workflow-optimization-research-2026-08.md`、`docs/superpowers/plans/*`（历史 plan 归档）、`docs/workflow-skills/matt-pocock-workflow.md` / `superpowers-writing-plans.md` / `superpowers-subagent-dev.md`（旧管线详解文档本体，保留供了解设计脉络）。
- **adr 历史文本**：`openspec/adr/0002` / `0007` / `0017` / `0032`（未改，Global Constraints 保护）；`0033` / `0042` 仅加互指指针（见 §2）。
- **本 change 自身工件**：`openspec/changes/remove-superpowers-pipeline/{proposal,design,tasks,decision-memo,spec-review-report,tickets,token-log,impl-reports/*,specs/*}` —— 描述"删除 superpowers"这件事本身，理应大量提及该词。
- **issues/roadmaps 追踪记录**：`openspec/issues/{open,closed}/todo/*`、`openspec/issues/{INDEX,CLOSED}.md`、`openspec/roadmaps/workflow-optimization-2026-08/*` —— 历史追踪记录，不回改。
- **未归档主 specs（预期状态，非缺陷）**：`openspec/specs/impl-orchestration/spec.md`、`openspec/specs/spec-workflow/spec.md` 仍含旧双轨表述——这是 OpenSpec 工作流的正常状态：主 specs 只在 `openspec archive`（`/sdflow-done`）时按 delta 同步，本 change 尚未归档，提前手改主 specs 会绕过归档时的"delta 对码核验"步骤、制造未经验证的 spec 漂移。**非本票缺陷，留给后续 `/sdflow-done` 处理**。
- **测试文件内的迁移历史注释与刻意保留的 grandfather 夹具**：`hack/tests/test_checkpoint_slug_coverage.py`、`test_yq_wrapper_consistency.py`（迁移注释）、`sdflow-ship/tests/test_gate_*.py` / `test_plan_resolver.py`（测试单名 resolver 对遗留旧名的 fail-closed 兜底行为，属任务2设计范围内的正常测试逻辑）；`hack/tests/test_harden_sdflow_spec_followup_closure.py` 的 `PLAN = CHANGE / "superpowers-plan.md"` 常量按任务2 impl-report 的记录**刻意保留**（指向一个已归档、不可变的历史 change 的真实计划文件名，与本 change 的 gate resolver 逻辑无关）。
- **脚本内合法残留逻辑**：`sdflow-implement/scripts/impl_route.py`（删除路由的历史注释）、`sdflow-ship/scripts/ship_gate.py`（`LEGACY_PLAN_FILENAME` 遗留旧名兜底——任务2设计的 fail-closed 检测逻辑，非叙述残留）。
- **`sdflow-implement/SKILL.md`**：三处「借鉴 superpowers subagent-driven-development 的…」是design 灵感来源致谢（附录B出处说明），非声称该管线仍存在。

### 本票额外修复的 3 处真实缺陷（超出字面 grep "superpowers" 但属同一收口面）

grep 扫尾时发现以下内容虽不含字面 `superpowers` 但仍描述已删除的旧管线机制，按「面治优先于点补」一并修复：

1. **`sdflow-init/assets/workflow/workflow.md`**（bundle 权威源，任务4.2 清单内文件，但当时遗漏此文件内 4 处 `subagent-dev` 字面量）：§三.6「代码侧」判据段落把「生成期已三层审 + 注入点B」的旧 SDD 机制改写为「sdflow-implement 每 ticket 双轴审（Standards 轴 + Spec 轴）+ Standards 轴必填槽注入领域清单」；检查清单与附录A的 3 处 `subagent-dev / sdflow-implement` 并列表述精简为单一 `sdflow-implement`。**改动后必须重跑 `python3 hack/gen_workflow_guide.py --write` 重新生成 `WORKFLOW-GUIDE.md`**（它是从 `workflow.md` + `prompts/*.md` 机械生成的产物，手改源后必须重生成，否则 `test_workflow_split.py::test_guide_is_in_sync_with_its_sources` 会红——首轮全仓 pytest 已实测踩到这个坑，见 §5 验证记录）。
2. **`sdflow-init/assets/snippets/claude-section.md`**（任务4.2 清单内文件，遗漏一处）+ 本仓 `CLAUDE.md:420` / `AGENTS.md:229`（三处均为该 snippet 的下游注入副本）：「子 agent 调度期间（`subagent-driven-development` / sdflow-implement / …）禁 `/clear`」精简为「（`sdflow-implement` / …）」。
3. **`sdflow-init/assets/workflow/reference/quality-layering.md` §一/§二**：任务4的 impl-report（`task4-bundle-config.md:126-129`）明确记录「未动 §一/§二（生成期三层 review 的 superpowers 具体机制描述）——brief 明确只要求退役"注入点 A/B"与"用 superpowers 跑实现时"清单节两处，§一/§二属 tasks.md 5.2 全仓 grep 扫尾范围」——本票按此移交把 §一/§二 的内部机制描述（`superpowers:subagent-driven-development` 内三层 review 流水线）改写为 `sdflow-implement` 的实际机制（implementer TDD → 双轴审并行判决 → fix 循环 → 出票收尾一致性自扫），并把「领域规则」判据从「❌ 通用 rubric 盲区」更正为「✅ Standards 轴必填槽已注入」（Standards 轴把 `code-checklists/domains/<栈>` 作为 dispatch 模板必填槽，已核实于 `sdflow-implement/SKILL.md`「每 ticket 双轴审」节）。
4. **`sdflow-init/assets/workflow/prompts/step7-subagent-dev.md`**：全文引用已删除的 `/subagent-driven-development` skill，且经全仓 grep 确认零引用点（`workflow.md` 阶段三入口只指向 `step5-ship.md`，"子步骤 A/B/C" 均为内联 prose、不再指针到 step7/8/9）——与已被任务4.1删除的同源文件 `step6-writing-plans.md` 同构（写票/执行成对），判定为任务4.1 遗漏的配对文件，一并删除。删除不影响 `MIN_CALLSITES`（该文件无 `checkpoint-commit.sh` 调用样例）与 `test_workflow_split.py`（该文件本就不被 workflow.md 指针引用）。

**`openspec/workflow/WORKFLOW-GUIDE.md`**（仓内 `sdflow-init update` 托管刷新的追随副本）与 canonical 源 `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md` 存在 3 处漂移（正是「部署副本漂移只在 update 时暴露」的复现）——`sdflow-init update` 命令因**预置存在的、与本票无关的缺陷**（见下）无法正常执行，改用直接 diff 校验 + `cp` 同步（仅限这一个文件，diff 只有预期的 3 处 hunk，风险可控）。

## 5. 全仓 pytest

```
$ /usr/bin/python3 -m pytest -q
```

- **首轮**：`1 failed, 2559 passed, 10 skipped`（`test_workflow_split.py::test_guide_is_in_sync_with_its_sources` 因手改 `workflow.md` 后未重生成 `WORKFLOW-GUIDE.md` 而红）。
- 修复：`python3 hack/gen_workflow_guide.py --write` 重生成 canonical `WORKFLOW-GUIDE.md`，重新 `cp` 同步 `openspec/workflow/WORKFLOW-GUIDE.md`。
- **复跑**：`2560 passed, 10 skipped in 358.38s`（全绿；skip 数与首轮一致，均为既有、与本票无关的 skip）。

### Success Metrics 第三条（ship 直连 e2e）标注

Success Metrics「阶段三过设计门后连续自动跑到 merge，全程直连 `sdflow-implement`，无路由分支」——**本票不产出该锚**。理由：路由删除（Task1）、gate 单名收口（Task2）、SKILL 文案收口（Task3）均已完成并各自 checkpoint PASS，但真实 e2e（`/sdflow-ship` 从设计门跑到 merge）需要一次**真实的、独立于本 change 的**未来 change 走满全程才能产出机验锚点——本 change 自身走 `/sdflow-ship` 归档时会是第一次真实验证，但那发生在本 change 的 `sdflow-done` 步骤，不在 Task5 实现期职责内。**事后锚——由下一真实 change 的 `/sdflow-ship` 首跑承接**，MUST NOT 在此留白冒充已验证，也 MUST NOT 假造一次 e2e 记录。

## 6. 已知预置缺陷（发现但明确不在本票范围内，未修复）

- **`sdflow-init/scripts/init.py::_marker_schema()` 不兼容双键 marker**：本仓 `openspec/changes/remove-superpowers-pipeline/.openspec.yaml` 含 `schema:` + `created:` 两个键，而 `_marker_schema()` 要求 marker 文件"恰好一个 `schema` 键"，导致 `python3 sdflow-init/scripts/init.py update --root .` 在本仓当前状态下无法执行（`RuntimeError: schema marker 不可解析`）。该缺陷与本票（superpowers 移除）无关，任务4的 impl-report（`task4-bundle-config.md:123-124`）已记录并建议"另开 todo 处理"。本票同样未修复，只是绕过其影响（§4 末段的直接 diff+cp 同步）。**建议**：另开 todo 让 `_marker_schema()` 兼容 `/sdflow-spec` 当前会写入的 `created` 字段，或让 `/sdflow-spec` 停止写入该字段——两者选一，不在本票判断范围内。

## 7. 与 Global Constraints 的核对

- 未动任何 archive 历史件。
- 未动既有 ADR 正文（仅 0033/0042 按 brief 明示的例外加互指指针，逐字未动其余内容）。

## 8. 文件清单

改动（15 个已跟踪文件 + 1 个删除）：

```
M  AGENTS.md
M  CLAUDE.md
M  docs/criteria-mechanization-tracker.md
M  docs/workflow-console.html
M  docs/workflow-map.html
M  docs/workflow-map.md
M  docs/workflow-overview.md
M  docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md
M  openspec/adr/0033-tickets-plan-filename-split-by-track.md
M  openspec/adr/0042-tickets-sole-impl-pipeline.md
M  openspec/workflow/WORKFLOW-GUIDE.md
M  sdflow-init/assets/snippets/claude-section.md
M  sdflow-init/assets/workflow/WORKFLOW-GUIDE.md
D  sdflow-init/assets/workflow/prompts/step7-subagent-dev.md
M  sdflow-init/assets/workflow/reference/quality-layering.md
M  sdflow-init/assets/workflow/workflow.md
```

未由本票改动、但在working tree中观察到的既有差异（非本票产生，如实披露）：

```
M  openspec/changes/remove-superpowers-pipeline/tickets.md（Task 4 六个复选框 [ ]→[x]，
   非本票所改；HEAD 的 task4 checkpoint commit 042e0f5 未包含此改动，推测是执行模式在
   双轴审通过后补打、尚未随 checkpoint 提交的正常台账状态，本票未触碰 Task 5 自身的
   复选框——按信号权威表由执行模式在双轴审通过后补打）
```

## 9. 待办事项清单（tasks.md 5.1-5.6）核对

- [x] 5.1 `impl-pipeline-matt-vs-superpowers.md` 头部已加 obsolete 标注
- [x] 5.2 grep 扫尾：运行时路径仅剩合法残留清单（见 §4，含 3 处主动补修的真实缺陷 + 1 个孤儿文件删除）
- [x] 5.3 全仓测试绿：`2560 passed, 10 skipped`；Success Metrics 第三条已显式标注「事后锚」
- [x] 5.4 `CLAUDE.md:215` 手写段已修正
- [x] 5.5 现役视图文档已同步去 superpowers 管线叙述
- [x] 5.6 ADR 0033/0042 已互加指针
