---
ship-gate:
  verify: PASS
  reviewed_sha: 3e2297c285f76f41318e8cb86b5bc233c0ebaf60
---

<!-- 🔴 补录声明（显式越权通道，git 留痕可审计）：本 frontmatter 由 /sdflow-done 的编排层
     在 merge 后补写，**非 verify 子代理亲写**——该子代理写了人读结论行「**结论：PASS**」与
     核验 SHA，但漏写了 gate 机判用的 frontmatter 锚，导致 ship_gate 判 UNKNOWN（fail-safe
     正确生效，未假绿）。此处两个字段均为**逐字转录**该报告正文已声明的内容：
     verify=PASS 取自正文「结论：PASS」，reviewed_sha 取自正文「核验 SHA：3e2297c…」。
     未新增、未改动任何结论。可复发缺陷已记 todo。 -->
# verify-report — harden-implement-review-loop

**结论：PASS**

- 核验 SHA：`3e2297c285f76f41318e8cb86b5bc233c0ebaf60`（分支 `feat/harden-implement-review-loop`）
- 核验方式：**冷启动、Do-Not-Trust**——不采信 `tasks.md` 复选框、不采信 `impl-reports/*.md` 与
  `code-review-report.md` 的措辞；每条 ✅ 独立打开代码 / 文本取锚，机械项**自己重跑一遍**。
- 独立复跑证据：
  - 全量 `/usr/bin/python3 -m pytest -q` → **2927 passed, 11 skipped, 3 xfailed**（295.66s）。
    注：收尾票 impl-report 记的是 `f22bc10` 上的 2922 passed；本次在 HEAD 复跑，仍全绿。
  - `openspec validate harden-implement-review-loop --strict --type change` → `is valid`。

---

## 1. 档位解析机制（tasks §1，12 项）

| 项 | 证据锚 | 判定 |
|---|---|---|
| 1.1 第零步四步 | `sdflow-implement/SKILL.md:169` 起 `## 第零步：宿主/档位解析`，`:177` 含 (a) 清脏 unset → (b) `[ -x ]` 预检 → (c) 捕获退出码 + `EVAL_RC` → (d) eval 后校验 | ✅ |
| 1.2 插入位置 | 标题在 `:169`，早于 `## 模式派发契约`(`:215`)、`## 出 ticket 模式`(`:245`)、`## 执行模式`(`:447`)；`:171` 明写「两入口共用、无条件执行」 | ✅ |
| 1.3 unknown / 子代理不可用硬停 | `SKILL.md:180-192`（Codex 能力探针 + 不可用硬停不缩 roster）、`:194`（`host=unknown` fail-loud，与 host 空值分列） | ✅ |
| 1.4 八类 halt envelope | `SKILL.md:206-213` 八行表（resolver 不存在 / 不可执行 / 非零退出 / 输出无法 eval / host 非法 / host 空值 / tier 缺失 / host=unknown），逐行 problem+cause+fix | ✅ |
| 1.5 implementer 档位声明 | `SKILL.md:469` `model: $SDFLOW_TIER_MID` | ✅ |
| 1.6 双轴审档位声明 | `SKILL.md:593` `均派发 Agent model: $SDFLOW_TIER_MID` | ✅ |
| 1.7 fix 子代理落点 | `SKILL.md:644-646`「fix 子代理**无独立 dispatch 段，就地在此声明**」+ `$SDFLOW_TIER_MID`，并注明不重复计数 | ✅ |
| 1.8 sdflow-done 0.4 | `sdflow-done/SKILL.md:195` `### 0.4`，`:197-199` 为 marker 圈住的同一段四步（与其余三处逐字节相同） | ✅ |
| 1.9 parity 守卫 | `hack/check_tier_resolution_parity.py`（`SITES` 四项、`START_LINE_PREFIX`/`END_LINE` 单行字面量）+ `hack/tests/test_tier_resolution_parity.py`；独立跑 → **37 passed** | ✅ |
| 1.10 变异实测防恒真 | **本次 verify 自己重做了变异**（scratchpad 副本，不污染工作树）：baseline `compare rc=0`；分别删掉 (a)/(b)/(c)/(d) 任一步 → `rc=1` ×4，全部必红 | ✅ |
| 1.11 Codex 授权段 | `AGENTS.md:284-285` / `CLAUDE.md:439-440` / `sdflow-init/assets/snippets/claude-section.md:111` 均含 `sdflow-implement` 且措辞已改「**仅限这三处**」；`sdflow-init/tests/test_codex_subagent_authorization.py:58` 断言同步为 `"仅限这三处"`（随全量 pytest 绿） | ✅ |
| 1.12 ship 枚举补 implement | `sdflow-ship/SKILL.md:165`「各被链序调度的子 skill（spec-review/code-review/done/**implement**）」 | ✅ |

**四站点 marker 实测在场**：`sdflow-implement:176/178`、`sdflow-done:197/199`、
`sdflow-code-review:199/201`、`sdflow-spec-review:175/177`。

---

## 2. `T10-choice`（Group A，tasks §2，11 项）

逐点打开取锚（`strong` 与「三镜 + 主次」限定词逐条核）：

| 落点 | 锚 | strong | 判定 |
|---|---|---|---|
| 2.1 bundle canonical | `sdflow-init/assets/workflow/workflow.md:110` | ✅ 含「派 **strong 档**对抗镜」+「按三镜 + 主次记理由」 | ✅ |
| 2.2 ship | `sdflow-ship/SKILL.md:164`（含台账行 `` `T10-choice`复核: ``） | ✅ | ✅ |
| 2.3 code-review 四处 | `sdflow-code-review/SKILL.md:7` / `:170` / `:289` / `:532`（台账格式行） | ✅（`:289` 展开段） | ✅ |
| 2.4 主 spec 阶段三 | `openspec/specs/spec-workflow/spec.md:83` | ✅ + 「按三镜 + 主次」已补回 | ✅ |
| 2.5 主 spec outside-voice | `openspec/specs/spec-workflow/spec.md:638` | ✅ + 「按三镜 + 主次记理由」 | ✅ |
| 2.6 **确认不改**的指针 | `openspec/specs/spec-workflow/spec.md:29` 仍为裸 `T10`（历史别名解析得到） | — | ✅ 按设计保留 |
| 2.7 主 spec 出票模式 | `openspec/specs/impl-orchestration/spec.md:27` 含「无客观判据档派 **strong 档**对抗镜」 | ✅ | ✅ |
| 2.8 implement 粒度争议两处 | `sdflow-implement/SKILL.md:251`、`:421` | ✅ | ✅ |
| 2.9 implement 一致性自扫两处 | `sdflow-implement/SKILL.md:432-433`、`:715` | ✅ | ✅ |
| 2.10 ff 生成约束 | `sdflow-init/assets/workflow/ff-generation-constraints.md:68` | ✅ | ✅ |
| 2.11 workflow-overview §6.1 | `docs/workflow-overview.md:257` 标题 + `:265` mermaid「② 派 strong 档对抗镜复核推荐项」 | ✅ | ✅ |

**§7.1 反向核**（不该被误删的两处「T10」原样在）：
`sdflow-implement/SKILL.md:526`（NEEDS_CONTEXT 状态词表尾部）、
`openspec/specs/impl-orchestration/spec.md:60`（对应 Scenario）——两处均保留 ✅。

---

## 3. `review-loop-breaker`（Group B，tasks §3，4 项）

`sdflow-implement/SKILL.md:649-662` 独立成段：

- 3.1 就地命名 `review-loop-breaker`，明写「MUST NOT 引用 `T10-choice` 标签」，段内不再出现裸 `T10` ✅
- 3.2 身份键 =「同文件 + 规范化问题指纹」，「**行号只作定位、MUST NOT 作为身份键的组成部分**」✅
- 3.3 三级互斥终态：①关闭 ②strong 复核 →（不成立→关闭 / 成立且可修→strong fixer 修 + **仅复验一次** / 否则转③）③defer buglist 并停；明写「MUST NOT 停在『已确认成立』而无后续动作」✅
- 3.4 ①档「**预期极少触发**」及理由（触发前提已是连续 2 轮不消解）在场 ✅

---

## 4. 测试范围分层 + 收尾票（tasks §4，10 项）

| 项 | 证据锚 | 判定 |
|---|---|---|
| 4.1 测试契约收窄 | `sdflow-implement/SKILL.md:497-499`「单元测试 + 本票声明的 e2e 场景 + 本票 `Blocked-by` 链上模块的集成测试」，禁令措辞为「MUST NOT 跑与本票**无依赖关系**的集成/e2e」 | ✅ |
| 4.2 e2e 场景表达 | `SKILL.md:270-273`：验收标准复选框标 `[e2e]` 者即本票 e2e；无标注 ⇒ 该票无 e2e | ✅ |
| 4.3 收尾票规则 | `SKILL.md:285` 起小节；`:295` `R-ID: all`；`:299` 验收标准；`:407` 起票模板（Task N: 实现验证，不计入 3–6 预算） | ✅ |
| 4.4 聚合套件发现契约 | `SKILL.md:312-318`：①命令来源优先级（`config.yaml` `test-suites.{unit,integration,e2e}` → implementer 判定并写依据）②「真跑一遍看退出码，MUST NOT 解析构建文件」③缺层不罢工 | ✅ |
| 4.5 证据 schema | `SKILL.md:321-323` 逐字 `<层> \| <命令原文> \| <退出码> \| <测试时 git rev-parse HEAD>`，未覆盖层 `<层> \| — \| 未覆盖 \| <依据>` | ✅ |
| 4.6 四类失败分诊 | `SKILL.md:325-327`：本 change 回归→fix 循环 / 既有红测（base SHA 复跑）→放行 / flaky→放行 / 环境故障→halt envelope | ✅ |
| 4.7 三处执行契约差异 | `SKILL.md:337-345`：豁免 red-before-green；主证据锚 = impl-report + SHA 三元组、不依赖 commit；Standards 轴扩为「加 skip / 改测试配置 / 删除或弱化断言」 | ✅ |
| 4.8 done verify 引用规则 | `sdflow-done/SKILL.md:223` 起「实现期聚合覆盖需求（tickets 轨专属，按管线条件化）」；`:239` tickets 轨找 `R-ID: all` 报告；`:249` 锚语义限定为实现期、不写成最终全量回归；`:251` superpowers 轨判「不适用」**MUST NOT 判 gap**；`:234-236` 明确按 config/marker 判轨而非文件名 | ✅ |
| 4.9 gate 第四道校验 | `sdflow-ship/scripts/ship_gate.py:1491` `plan_closing_ticket_check`；`:1497` 当且仅当 `plan.name == "tickets.md"` 才校验，否则返回 grandfather 提示；`:1510-1529` 缺票 / 多票 / `Blocked-by` 未覆盖三种判否；docstring 契约表 `:55`/`:65-67` 同步 | ✅ |
| 4.10 gate 测试 | `sdflow-ship/tests/test_gate_closing_ticket.py` 10 用例，其中 `test_missing_closing_ticket_is_unknown` / `test_closing_ticket_missing_functional_dependency_is_unknown` / `test_duplicate_closing_tickets_is_unknown` 走**端到端 gate**（断 `code==6 and verdict=="UNKNOWN"`）、`test_grandfather_old_name_without_closing_ticket_not_rejected` 断不红 | ✅ |

**本次 verify 的独立行为实测**（直接调 `ship_gate.plan_closing_ticket_check`，非读报告）：

```
good           -> (True,  '')
no closer      -> (False, 'plan 不含「实现验证」收尾 ticket…')
missing dep    -> (False, '收尾 ticket（Task 3）的 Blocked-by 未覆盖全部功能 ticket 号，缺: [2]')
grandfather    -> (True,  "在途 plan 未含收尾票校验（grandfathered：文件名 'superpowers-plan.md'…")
```

---

## 5. 计划文件改名（tasks §5，10 项）

| 项 | 证据锚 | 判定 |
|---|---|---|
| 5.1 共享 resolver 单一源 | `ship_gate.py:1238` `PLAN_FILENAMES`、`:1245` `resolve_plan_path`、`:1241` `PlanNameConflict`（双存在 raise）；`impl_route.py:52-56` **sibling-import** `resolve_plan_path` / `PLAN_FILENAMES`，`:456-461` import 失败即 fail-closed，`:470-472` 明确无 `"tickets.md"` 兜底常量 | ✅ 真单一源，无手抄第二份 |
| 5.2 ship_gate 改用 resolver | `ship_gate.py:46`/`:55`/`:57` docstring 契约表与完成判据窗口段措辞同步 | ✅ |
| 5.3 impl_route 改用 resolver | 同上；docstring 里指向 archive 历史文件的两处（`:5`、`:21`）原样未改 | ✅ |
| 5.4 出票落盘路径 | `sdflow-implement/SKILL.md:360`「落盘路径固定 `{change_dir}/tickets.md`」+ `:428` 写盘步；`:371` gate 校验说明用新名；`:453`/`:464` helper 调用同步 | ✅ |
| 5.5 done 文件名同步 | `sdflow-done/SKILL.md` 含 `tickets.md`（2 处）且旧名引用限定为 superpowers 轨/在途 | ✅ |
| 5.6 bundle 同步 | `sdflow-init/assets/workflow/workflow.md:94`（步骤 6 行明写「**本步骤只管 superpowers 轨，产出文件名不变**」+ tickets 轨改名说明）、`assets/workflow/WORKFLOW-GUIDE.md:105/108`、`openspec/workflow/WORKFLOW-GUIDE.md:105/108`、`prompts/step6-writing-plans.md:1`（「superpowers 轨固定用此名；tickets 轨改用 `tickets.md`…不走本 prompt」） | ✅ |
| 5.7 测试同步 | diff 内含 `sdflow-implement/tests/test_impl_route.py`、`sdflow-ship/tests/test_gate_impl_progress.py`、`test_gate_freshness.py`、`hack/tests/test_checkpoint_slug_coverage.py`；新增 `sdflow-ship/tests/test_plan_resolver.py`（含 `test_resolve_plan_path_both_present_raises_conflict` + `test_both_plan_names_present_gate_fails_closed_unknown`）。`hack/tests/test_harden_sdflow_spec_followup_closure.py:39` 的 `PLAN = CHANGE / "superpowers-plan.md"` **未改且不该改**——它锚的是已归档 `add-sdflow-spec` 的真实历史文件名（同 §5.9 纪律），全量 pytest 绿即证 | ✅ |
| 5.8 文档同步 | 实改：`docs/workflow-overview.md`、`docs/criteria-mechanization-tracker.md`、`docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md`、`openspec/INDEX.md`。**未改且无需改**：`docs/workflow-map.md`/`.html`、`docs/workflow-console.html`、`docs/workflow-skills/superpowers-{writing-plans,subagent-dev}.md`——独立核实这 5 份**全文零命中 `tickets` 与 `sdflow-implement`**，其 `superpowers-plan.md` 引用纯属 superpowers 轨描述 | ✅ |
| 5.9 不动区 | `git diff --stat origin/main...HEAD -- openspec/changes/archive` → **空**；`openspec/issues/**` 仅 todolist 追加（+143，新记 defer），无改写；`adr/0017` 仅追加一行（`:39`）指向 `adr/0033`，正文未改 | ✅ |
| 5.10 在途改名 | 旧启发式 `plan_was_renamed()` 已被冷层审证伪并**整体替换**为精确判据 `stray_done_tag_commits()`（`ship_gate.py:1285` 注释 + `:1661` 调用点）；测试落在「该场景被显式拒绝」分支：`test_plan_resolver.py` 的 `test_mode2_two_step_rename_is_detected`、`test_mode3_rename_with_heavy_edit_is_detected`，配三条负例（`test_mode1_lookalike_plan_in_another_change_is_not_flagged`、`test_legacy_bare_tags_outside_window_do_not_trigger`、`test_other_change_namespaced_tags_outside_window_do_not_trigger`）防误报自锁 | ✅ 断言方向正确 |

---

## 6. ADR 与术语（tasks §6，4 项）

- 6.1 `openspec/adr/0032-closing-ticket-aggregate-regression-checkpoint.md`（新增，36 行）✅
- 6.2 `openspec/adr/0033-tickets-plan-filename-split-by-track.md`（新增，23 行）✅
- 6.3 `openspec/CONTEXT.md:299` 登记 `T10-choice` / `review-loop-breaker` 两条具名规则 + 「"T10" 保留为历史别名」+「分析类文档不算陈旧、无需扫改」✅
- 6.4 `openspec/adr/0031` 正文未改、末尾追记一行指向两条具名规则与 design 的 scope-check 表 ✅

---

## 7. 一致性收尾（tasks §7，8 项）

| 项 | 结果 |
|---|---|
| 7.1 全仓 `T10` 复核 | 本次独立跑 `grep -rno "T10[-a-z]*"`（不带 `--include`，排 `.git`/`__pycache__`/`archive`）：规范性落点全为 `T10-choice`；剩余裸 `T10` 全在**分析类文档**（`docs/sdflow-fable5/*`、`docs/workflow-skills/*`、`docs/skill-authoring-best-practices.md`、`docs/criteria-mechanization-tracker.md:94`、`docs/workflow-console.html:515`）与两处**按设计保留**的指针（`spec-workflow/spec.md:29`、`impl-orchestration/spec.md:60`、`sdflow-implement/SKILL.md:526`）——与 CONTEXT.md 的别名条款一致 ✅ |
| 7.2 `SDFLOW_TIER` 非零命中 | `grep -c "SDFLOW_TIER" sdflow-implement/SKILL.md` → **6**（对照 C1 现状的 0）✅ |
| 7.3 `superpowers-plan` 归因 | 本次独立跑全量 grep：非 archive / 非 issues / 非本 change 目录的剩余命中共 21 个文件，逐条属①superpowers 轨合法引用（`step6-writing-plans.md`、两份 WORKFLOW-GUIDE、`workflow.md:94`、5 份纯 superpowers 文档、`sdflow-done`/`sdflow-implement` 的轨道分列说明）或②resolver / gate / 测试中的**旧名候选常量与 grandfather 分支**（`ship_gate.py`、`impl_route.py`、5 份测试）或③历史归档锚（`test_harden_sdflow_spec_followup_closure.py:39`、`adr/0017`）。tickets 轨零残留 ✅ |
| 7.4 openspec validate | `Change 'harden-implement-review-loop' is valid` ✅ |
| 7.5 全量 pytest | **2927 passed, 11 skipped, 3 xfailed**（本次在 HEAD `3e2297c` 复跑）✅ |
| 7.6 superpowers 轨回归 | `sdflow-ship/tests/test_superpowers_track_regression.py` 4 用例：config 切 superpowers 时路由正确、gate `RUN_PLAN` 不受 config 影响、旧名 plan 无收尾票仍推进、`plan_closing_ticket_check` **只读文件名不读 config**。verify 侧「不适用而非 gap」为 `sdflow-done/SKILL.md:251` 的指令层约束（非机械门，如实登记）✅ |
| 7.7 Success Metric 1 | **部分验证，已如实降级**——见下方 Minor-1 |
| 7.8 delta 对码 | 本次逐条对码复核了两份 delta 的全部 ADDED/MODIFIED 与实现：档位解析、`review-loop-breaker`、测试范围分层、收尾票 + 聚合契约、文件名分轨 + resolver + gate 第四道、`planning-decisions.md` 审计落点（`impl-reports/planning-decisions.md` 实际存在，`SKILL.md:252`/`:434` 引用）——逐条对得上 ✅ |

---

## Minor 缺口（**不影响 PASS**）

**Minor-1 · Success Metric 1 只做到档位解析层，未实跑完整 `tickets-plan`。**
`tasks.md §7.7` 要求「Codex 宿主下实跑一次 `sdflow-implement` tickets-plan，记录四类 dispatch
解析到的 model id」。实际做法（`impl-reports/task1-tier-resolution.md:119-135`）是在**真实 Codex
宿主进程内**（`env -u CLAUDECODE codex exec`，规避 `CLAUDECODE=1` 继承导致的信号冲突）执行
`eval "$(resolve-models.sh)"`，读到 `HOST=codex / STRONG=gpt-5.6-sol / MID=gpt-5.6-terra /
LIGHT=gpt-5.6-luna`，零命中 Claude 机队专名；未跑完整出票流程的理由是「会写 plan 文件、触发本
change 自身 `plan_first_sha` 窗口锚风险」，已在原报告写明。
⇒ 机制层（档位怎么解析出来）已实证，**编排层（四类 dispatch 真派子代理时取到什么）未实证**。
`task6-implementation-verification.md:93` 的「四条 Metric **全部**有证据落点，无「未验证」项」措辞
略乐观，应读作「Metric 1 部分验证」。属可观测性 / 证据完备度层面，非核心功能缺失。

**Minor-2 · 收尾票证据锚的 SHA 早于 HEAD 两个提交。**
`task6-implementation-verification.md:31` 的 unit 行锚 `f22bc10`，其后仍有
`5587d07`（冷层代码审自动修复）与 `3e2297c`（报告）两个提交。这**正是 delta 明写并接受的残余风险**
（「锚语义限定为『实现期结束时聚合套件通过』，MUST NOT 表述为『最终代码通过全量回归』」），
且本次 verify 已在 HEAD 独立复跑全量 pytest 全绿，缺口实际闭合。

**Minor-3 · integration / e2e 两层记「未覆盖」。**
`task6-implementation-verification.md:32-33` 按契约第③条记「本仓无独立可调用的集成层 / 无 e2e 层」
并附依据——这是设计允许且要求的形态（`MUST NOT fail-closed 罢工`），非缺口。

---

## 备注：非缺口的三件事（已核实，不重复报）

1. **本 change 自己的 plan 仍叫 `superpowers-plan.md`** —— design Migration Plan 明写「MUST NOT
   重命名任何在途 plan」（改名会把 `plan_first_sha` 窗口起点推到改名 commit、重置完成判据），
   gate 对它走 grandfather 分支并输出提示。实测 `plan_closing_ticket_check` 对该名返回
   `(True, "…grandfathered…")` ✅ 是设计要求。
2. **`openspec/specs/**` 与 delta 的差异** —— delta-at-archive 纪律。已确认 Task 2 按 `tasks.md`
   §2.4/2.5/2.7 主动改过的 3 处主 spec（`spec-workflow/spec.md:83`、`:638`、
   `impl-orchestration/spec.md:27`）确已落地；其余差异（如收尾票不占 3–6 预算的括注、计划文件名
   分列段、`model-tiers` 列入 `implement`）留待归档同步，不判 gap。
3. **`sdflow-spec/SKILL.md` 被改** —— 冷层代码审按「面治优先于点补」查出的**第五处** `eval` 退出码
   同缺陷（不在 parity 守卫 `SITES` 名单内、机械门照不到）。实测 `sdflow-spec/SKILL.md:207-208`
   已含 `eval "$MODELS_ENV"; EVAL_RC=$?` 与「`EVAL_RC` 非 0 → fail-loud 硬停」。
   属有据外溢修复，非 scope 泄漏。

---

## MUST 如实登记（不影响 PASS/FAIL）

### scope drift（会随合并进 main 的无关提交）

分支相对 `origin/main` 携带 **2 个与本 change 无关的提交**（`git log --oneline origin/main..HEAD` 实证）：

| commit | subject | 性质 |
|---|---|---|
| `0296ca0` | `checkpoint(workflow-rules): G1 收窄：撤回「全流程不用 /clear」的过度泛化，改为阶段内部禁、两处阶段交界 SHALL 清` | 工作流规则改动，与本 change 无关 |
| `e5426e8` | `checkpoint(todolist): 记 T256：PreCompact 落盘调研（挂 main，非本 change）` | subject 自述「挂 main，非本 change」 |

**未自动摘除的理由**：摘除需重写历史，而 `rebase` 会击穿归档报告的 `reviewed_sha` 审计锚
（gate 契约字段，SHA 重写即静默断链）。∴ 保留并在此登记，由人决定是否单独处置。

### defer 残差

- **T259 / T260 / T261** —— 本轮冷层代码审 defer（已入 `openspec/issues/todolist/2026-07-todolist.md`）。
- **T257** —— 因标的消失判 **WONTDO**。

---

## 判定

7 个任务组、59 条 tasks 全部取到可机验证据锚；两份 delta 的 ADDED/MODIFIED 需求逐条对码成立；
机械层（parity 守卫变异、gate 第四道校验、resolver 双存在 fail-closed）本次 verify **自己重跑并
独立复现**，非采信报告。**无核心功能缺失。**

**PASS**
