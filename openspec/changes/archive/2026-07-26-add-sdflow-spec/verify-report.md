---
ship-gate:
  verify: PASS
  reviewed_sha: 3a80b17416681e2d2748b2a23180c23436275283
---

# add-sdflow-spec · verify 报告

- **日期**：2026-07-27
- **change**：`add-sdflow-spec`
- **reviewed_sha**：`3a80b17416681e2d2748b2a23180c23436275283`（`git rev-parse HEAD`）

## 结论：**PASS**

SA-01 ~ SA-14 全部 Requirement 均有可机验证据锚（测试名 / 文件:行 / commit）。三处「有据的不完整」
（阶段二外派回退、8.2 下游推广未做、两条 spec 措辞与实测不符）经独立核实，依据成立，按 Minor 记，
**不构成核心缺失**。

---

## 0. 本轮亲自跑过的验证

| 项 | 命令 | 结果 |
|---|---|---|
| 全量机械层 | `/usr/bin/python3 -m pytest -q`（仓根，rootdir 钉在 `pytest.ini`） | ✅ **2795 passed, 11 skipped, 3 xfailed in 285.61s**，exit 0 |
| 已知抖动用例 | `test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`（`sdflow-init/tests/test_outside_voice_job.py:3359`） | 本轮**绿**（无需标注降级） |
| SKILL.md 体量门 | `wc -l sdflow-spec/SKILL.md` | **600**（门 ≤600，恰在边界；软性见 Minor-4） |
| 全局铺设实况 | `ls -la ~/.claude/agents/` | 三个定义各一条软链，均 `readlink` 指向本仓 `sdflow-spec/agents/`；另有 `.sdflow-agents` manifest |
| 全局 skill 可见 | `ls -la ~/.claude/skills/ \| grep sdflow-spec` | `sdflow-spec -> …/04-sdflow-skills/sdflow-spec` 在册 |
| canonical 解析面 | `readlink ~/.sdflow/workflow` | `→ …/04-sdflow-skills/sdflow-init/assets/workflow`（**当前指开发 checkout**，见 Minor-5） |

> 本轮**未改动**除本报告以外的任何文件，**未 git add / commit**。
> 工作树既有一处未提交改动：`openspec/changes/add-sdflow-spec/tasks.md`（51 个复选框的 reconcile 勾选，
> 50 勾 1 留空 = 8.2），为 verify 前置步骤的产物，非本轮所为。

---

## 1. 逐需求核对表（SA-01 ~ SA-14）

| 需求 | 代码出处（文件:行 / 测试名 / commit） | 状态 |
|---|---|---|
| **SA-01** 单一入口三相位管线，拷问前置且为内建默认路径 | `sdflow-spec/SKILL.md:1-12`（frontmatter 含 `disable-model-invocation: true`）· `:157-169`（三相位图 + 「B 不可跳过」+ 诚实边界原文「结构性改善，不是机械保证」）· `:244-251` A.2 提前收束禁止清单（「收束进的是 B，不是 C」）· 纪要机械门 `hack/tests/test_decision_memo_gate.py::test_missing_memo_is_red` / `::test_empty_required_section_is_red` / `::test_comment_only_section_is_red` / `::test_heading_inside_fenced_block_is_not_a_real_heading` · 体量门 600 行 · README:16-20,39 | ✅ 实现 |
| **SA-02** 判断不出主 session；外派分阶段引入 | 主 session 亲做：`SKILL.md:253-259` A.3（「判断永远不外派」逐项列举）· 阶段二资产齐备：三个 agent 定义 `sdflow-spec/agents/*.md`（231/258/212 行）· 派发阈值事后可复核形式 `SKILL.md:257`（「同类任务累计工具调用 > 5 次」+ 明禁「预计读取材料 ≳ 数百行」）· 生成子代理返回结构化 blocker `SKILL.md:479` + `agents/sdflow-spec-writer.md` · A/B 三路实测 `impl-reports/task5-ab-comparison.md`（原始 JSON 归档 `impl-reports/task5-logs/`，指标可逐位重算）· 论证密度人工比对同报告 §5（D0b「运行时指针」候选在 subagent 路整条消失，thin/legacy 留住） | ✅ 实现（**外派为未启用资产**，见 §3-1，spec 自身已把启用条件写在 `specs/spec-authoring/spec.md:25`） |
| **SA-03** 拷问技法、停止信号与可判定的相位转换判据 | `SKILL.md:238-242` A.1（一次一问 / 每问附推荐 / 事实自查）· `:373-380` B.3（优先攻承重约束 + 默认 refuted=true）· `:393-399` B.5 停止信号最小充分条件（「站稳」= file:line / 命令输出 / 人的明确确认记录；明禁「问了 N 轮」）· A.2 三条禁止清单 `:244-251` | ✅ 实现（判断质量属指令层，`tasks.md` 覆盖图已如实标「无机械覆盖」） |
| **SA-04** 决策纪要为承重件，增量落盘，`/clear` 无损 | `references/decision-memo-schema.md`（字段 schema + `decision_hash` 唯一算法 §2 + 必填判红表 §3 + 落盘时机 §4 + 与 design.md 关系 §5）· `SKILL.md:359-366` B.1④ 立即落最小草稿纪要 · `:382-391` B.4 增量落盘（含「全损窗口收窄到两次保存之间，MUST NOT 声称零损失」）· `:516` 纪要 MUST NOT 并入 design.md · 机械门：`test_decision_memo_gate.py::test_decision_hash_covers_every_line_the_gate_calls_body` / `::test_decision_hash_is_deterministic_and_frontmatter_independent` / `::test_schema_doc_and_gate_agree` / `::test_repo_memos_all_pass_the_gate` · `/clear` 无损抽检 `impl-reports/task3-stage1-acceptance.md` §4（fresh 子代理真冷读，非自评；N=1 声明在 `:331`、`:455`） | ✅ 实现 |
| **SA-05** 生成经 openspec CLI；完成态与合格态分开判定 | B 起手三步前移：`SKILL.md:322-357`（① `git status --porcelain` halt ② FF-0 三分支表 ③ `openspec new change` + 「MUST NOT 暂定名后改名」+ partial state 报告）· C.1 四判 `:425-441` · C.2 强制阅读清单显式写死 `:443-457`（含 CLI 实测依赖图 `design/specs.dependencies` 都只有 `[proposal]`）· C.3 逐产物协议 `:459-480`（自取载荷 / 最小 schema 断言五字段 / 路径 canonicalization + containment + 逐组件 symlink 拒绝 / 临时文件原子替换）· C.4 存在态 vs 合格态 `:482-498` · 机械门：`test_decision_memo_gate.py::test_intact_change_passes_strict_validate` / `::test_truncated_spec_delta_is_caught_by_strict_validate` / `::test_status_says_done_while_validate_says_red` / `::test_validate_strict_only_covers_delta_specs` · 故障注入固化 `hack/tests/test_sdflow_spec_failure_modes.py`（19 用例覆盖六种情形）· FF-0 hook `sdflow-init/assets/hooks/ff0-branch-guard.py`（三分支 + 一次性哨兵 + `ACK_TTL_SECONDS=600` 双边时效）+ `sdflow-init/tests/test_ff0_branch_guard.py`（27 用例） | ⚠️ 实现（**一条 Scenario 措辞错**，见 Minor-1 / T232） |
| **SA-06** 终审兜判断层，并核产物间一致性 | `SKILL.md:502-522`（纪要↔产物 / design↔specs 互相一致 / proposal·design·tasks 未截断人判 / 中间态判据「砍掉的候选 + 理由完全消失才算判断性偏差」/ 风格差异放过）· dogfood 终审记录 `impl-reports/task3-stage1-acceptance.md` §2.7 | ✅ 实现 |
| **SA-07** agent 定义承载角色，派发经 `subagent_type`，起手过实测门 | 三定义 frontmatter 实读：`agents/sdflow-local-researcher.md`（`model: inherit` / `effort: low` / `tools: Read, Glob, Grep, Bash`）· `sdflow-web-researcher.md`（`effort: low` / `tools: WebFetch, WebSearch` —— 无仓库读取、无 Bash）· `sdflow-spec-writer.md`（`effort: medium` / `tools: Read, Glob, Grep, Bash, Write`）· 派发用 `subagent_type`：`SKILL.md:281`、`:476-478`，机械守 `hack/tests/test_sdflow_spec_agents.py::test_skill_dispatches_by_subagent_type_for_all_three_agents` · GO/NO-GO 实测门判 **GO**：`impl-reports/task4-agents-step1.md` / `-step2.md` §4.1（全新 `claude -p` 独立复现）· 降级只到亲做：`::test_skill_degrades_to_doing_it_itself_not_to_a_generic_subagent` · 投放面 glob：`hack/sync_principles.py:60`（`AGENT_TARGETS`）+ `:77-83`（每次调用重新 glob）+ `:52-55` 注释说明为何不并进 `PROJECT_TARGETS`，守卫 `hack/tests/test_sync_principles.py`（13 用例）· `install_agents()`：`setup.sh:176-276` + `cleanup_agent_orphans()` `:280`，守卫 `hack/tests/test_install_agents.py`（9 用例：软链指向本仓 / 外部文件不覆盖进 `skipped[]` / 跨 checkout 接管 / 悬空清理 / 源目录整体消失照清 / 占位与只读降级 skip / 幂等）· 全局实况 `ls -la ~/.claude/agents/` 三链在册 | ⚠️ 实现（**一条措辞错**：`model` 填「具体模型 id」与实测枚举不符，见 Minor-2 / T238） |
| **SA-08** 降级阶梯、诊断契约与如实报告 | `SKILL.md:526-554`（三要素 problem+cause+fix，含反例；阶梯「降级方向只有一个：亲做」；`Agent type not found` 的两条 cause + 「名册在 session 启动时加载」实测）· `references/degradation-ladder.md:7-18`（三要素表 + 正例）· `:38-39`（总时间预算：单次 ≤3 分钟 / 相位内累计 ≤10 分钟；429/5xx 一次带 jitter 有界重试 2–5s）· 机械守 `test_sdflow_spec_agents.py::test_skill_documents_that_the_agent_roster_loads_at_session_start` · CLI 缺失/schema 不重试：`test_sdflow_spec_failure_modes.py::test_fault5_missing_cli_is_detected` / `::test_fault5_preflight_instruction_is_present` / `::test_fault6_no_retry_instruction_is_present` / `::test_fault6_malformed_payload_fails_closed` | ✅ 实现 |
| **SA-09** 出口序列、G1 例外与相位 checkpoint | `SKILL.md:567-581`（原样贴三步 + 只引两条理由 + 明禁「主审裁决需冷视角」）· `:558-563` checkpoint 纪律（每次前 `git status --porcelain`；拷问中 MUST NOT 提交）· canonical 侧 G1 具名例外：`sdflow-init/assets/workflow/workflow.md:101`、`reference/quality-layering.md:107` · 机械守 `hack/tests/test_canonical_entry_sync.py::test_workflow_md_g1_exception_cites_exactly_the_two_allowed_reasons` / `::test_workflow_md_g1_exception_forbids_the_cold_view_reason` / `::test_quality_layering_forbids_the_cold_view_reason` / `::test_quality_layering_checklist_carries_the_exception` · 相位 slug 归因 `sdflow-retro/scripts/retro_report.py:141` + `hack/tests/test_checkpoint_slug_coverage.py`（3 用例） | ✅ 实现 |
| **SA-10** ADR 与术语提议钩子（惰性，只提议不写） | `SKILL.md:401-406` B.6（三条件 + 明禁未经人确认自动写入）· `references/adr-and-glossary-templates.md`（三条件判据 / 提议措辞 / 格式真相源 = `openspec/adr/` 既有文件 / 目录空时最小模板 / 术语提议） | ✅ 实现（纯指令层，`tasks.md` 覆盖图已如实标「无验证」） |
| **SA-11** canonical 规则单一源同步（七处，不得留分叉） | ①`generation-process.md:51-95,117-118`（§四改为「两条分支」+ 四入口选择规则 + 检查清单首条）②`workflow.md:101`（G1 具名例外）③`reference/quality-layering.md:107,117`（同步例外，独立措辞）④`WORKFLOW-GUIDE.md:16-22`（重生成，含「阶段一·步骤 0 — `/sdflow-spec`」）⑤`openspec/specs/spec-workflow/spec.md:970-1002`（分支 A/B 共存与路由 + 两条 Scenario）⑥`snippets/claude-section.md:82-84,95,126`（入口规则 + grill 条款显式收窄到分支 B + 归属修正）⑦`ff-generation-constraints.md:14-30`（FF-0 三分支判定 + hook 逃生口两步化）· 机械守 `test_canonical_entry_sync.py` **30 用例**（含 `::test_generation_process_has_two_branches` / `::test_claude_section_scopes_the_grill_clause_to_branch_b` / `::test_spec_workflow_declares_coexistence_and_routing` / `::test_generated_guide_reflects_the_new_entry` / `::test_ff0_rule_is_three_way` / `::test_ttl_window_has_a_single_source`） | ⚠️ 实现（**源仓七处全同步**；下游推广 8.2 未做，见 Minor-3 / T239） |
| **SA-12** 信任边界与数据保护（TG-17） | **S1**：作用域语法**实测不生效**（`impl-reports/task4-agents-step2.md:105,117`：加括号后实际只剩 `Read`/`Bash`，`Glob`/`Grep` 一起丢）⇒ 走诚实声明备选，落 `agents/sdflow-local-researcher.md:215`（「`Bash` 非只读…属指令层非机械门」），机械守 `test_sdflow_spec_agents.py::test_no_agent_def_uses_scoped_tool_syntax` / `::test_bash_holders_carry_the_canonical_honest_disclaimer` · **S2**：检索拆二 + 复用既有扫描器 `SKILL.md:289-310`（预检 / `exit 0` 唯一放行 / `exit 3` 拒发禁 fallback / `exit 2` 没扫成≠干净 / **catch-all 其余非 0 一律拒发**），实现在 `sdflow-init/assets/hack/outside-voice.sh:226-282`（`secret_scan` + `secret_scan_or_exit`），守卫 `::test_secret_scan_rejects_a_query_carrying_a_key` / `::test_secret_scan_fails_closed_when_the_scanner_itself_fails` / `::test_sdflow_spec_does_not_ship_a_second_scanner` / `::test_outbound_scan_prechecks_the_helper_and_has_a_catch_all` · **S3**：`::test_web_content_is_declared_non_executable_data` / `::test_second_source_requirement_for_design_affecting_conclusions` · **S4**：`::test_s4_rejects_out_of_contract_targets` / `::test_s4_rejects_a_symlinked_target` / `::test_s4_rejects_a_symlinked_ancestor` / `::test_s4_rejects_a_symlinked_ancestor_above_the_change_root` / `::test_s4_rejects_a_change_root_outside_the_repo_root` · **S5**：`::test_every_definition_has_an_exclusive_description`（三定义 description 均含「仅由 `/sdflow-spec` 编排派发，其它场景 MUST NOT 选用」） | ✅ 实现（S1 按 spec 的备选分支交付；S3/S5 为指令层，SKILL.md `:270` 与 `task5` §7 均已如实标注「指令层、非机械门」） |
| **SA-13** 相位状态机与重入判定 | `SKILL.md:211-232`（0.3 重入探测三态分治表 + 明禁「拿有没有 memo 当探测前提」+ 明禁「只探 `isComplete=false`」；0.4 状态机 `absent→B-draft→B-finalized→C-partial→complete` + 回边 + `complete` 拒绝重生成）· C.1 身份四判 `:425-441`（含 `decision_hash` 重算、`generated_at` 呈现、「缺失 ≠ 不匹配」的分治）· 机械守 `test_sdflow_spec_failure_modes.py::test_fault4_fixtureA_intact_memo_is_admitted` / `::test_fault4_fixtureB_branch_mismatch_is_stale` / `::test_fault4_fixtureC_edited_after_finalize_is_stale` / `::test_fault4_fixtureD_missing_finalize_fields_is_undrafted_not_stale` / `::test_fault4_three_verdicts_are_distinguishable` / `::test_identity_keys_all_come_from_the_schema_doc` | ✅ 实现 |
| **SA-14** 四入口选择规则（写进 spec，不留自由文字） | **双落点齐备**——人读侧：`CLAUDE.md:213-263` + `AGENTS.md`（同段，`::test_two_human_carriers_are_verbatim_identical` 逐字守）；AI 读侧：`generation-process.md:85-88` §四四入口选择规则 + `spec-workflow/spec.md:970-1002` · sunset 阈值已在**阶段一**落定（`CLAUDE.md:244-263`：观察窗 = 6 个新 change 或 8 周先到者为准；采用率 ≥5/6；「未达标 ⇒ 删除 `sdflow-spec`」写明处置）· 机械守 `test_canonical_entry_sync.py::test_generation_process_states_entry_selection_rule` / `::test_entry_section_exists_in_both_human_carriers` / `::test_human_carriers_state_the_default_entry_and_the_model_ban` / `::test_human_carriers_state_the_sunset_thresholds_and_disposition` / `::test_human_side_and_canonical_use_the_same_wording` / `::test_ff0_entry_roster_includes_branch_a` | ✅ 实现 |

---

## 2. tasks.md 复选框 vs 实际

51 条中 **50 勾 1 留空**，唯一留空 = **8.2**（下游推广），票面已带「⛔ 未执行（有据）」说明。
逐条抽验未发现「勾了但没做」的项；以下三条是本轮**重点独立复核**的：

- **1.8 机械核验**：票面点名「MUST NOT 用 `explore.*ff.*grill` 单行正则」——实读
  `test_canonical_entry_sync.py`，30 个用例均为按结构/关键词的独立断言，**未见该空判据**。✅
- **4.3 `validate --strict` 纳入机械核验**：票面自带实况订正，实交付形态为
  `::test_truncated_spec_delta_is_caught_by_strict_validate` + `::test_status_says_done_while_validate_says_red`
  + `::test_validate_strict_only_covers_delta_specs`（把覆盖边界机械钉住）。✅ 交付的是**可达形态**。
- **8.1 / 8.3 / 8.4**：虽挂在「阶段三（阶段二达标才做）」标题下、而阶段二判回退，实现方**知情偏离**
  并在 `impl-reports/task6-stage3-conditional.md` §0.0 显著写明「认账权在人 / 可 revert」，并登记 **T241**。
  8.3 的实跑捞出一个真洞（回滚**正序**会静默失效 —— 源目录整体消失时孤儿清理不跑），已修并由
  `test_install_agents.py::test_orphans_are_cleaned_even_when_the_whole_source_dir_is_gone` 守住。✅

---

## 3. 三处「有据的不完整」——核实结论

### 3-1. 阶段二外派回退 ⇒ 三个 agent 定义为「未启用资产」 —— **依据成立，不判缺口**

- delta spec 原文 `specs/spec-authoring/spec.md:25` 自己写着：「**外派的启用以阶段二起手的派发实测门
  （SA-07）与 A/B 对照结果为前提**」。⇒ 「阶段二起 SHALL 外派」是**条件式**的，前提未成立时不外派
  **不构成违背 spec**。
- 前提的两半已各自实测：**GO/NO-GO 门判 GO**（`task4-agents-step1/step2.md`，独立复现）；
  **A/B 对照判不达标**（subagent 路 $11.68 / 12.57M token vs thin 路 $9.06 / 8.81M token，
  冷审 Important findings 1 vs 0）。原始 JSON 已归档 `impl-reports/task5-logs/`，本轮抽查目录结构齐全
  （12 轮 `turn*.json` + 3 份 `review.json` + prompts + harness），指标可复算。
- `tasks.md:85` 的失败分支明写「回退到阶段一薄编排形态；agent 定义作为未启用资产保留或删除」。
  实际处置 = 保留，`SKILL.md:263-271` 已把「外派协议」整节标为「**当前 = 未启用资产**」，
  并诚实写出「未启用只约束本管线，定义照样铺在全局 `~/.claude/agents/`，挡误选的只有 description 的
  排他式声明（指令层、非机械门）」。
- ⇒ **SA-02 / SA-07 判 ✅**：能力齐备且经实测，启用状态按 spec 自带的条件句正确置于「未启用」。

### 3-2. 8.2 下游推广未做 —— **Minor 缺口 · 已登记 T239**

条件句（阶段三 · 阶段二达标才做）生效。残余已登记 **T239**（`openspec/issues/todolist/2026-07-todolist.md:99`），
写明**何时**（本 change merge 后）/ **由谁**（人择机）/ **怎么推**（每个已铺 bundle 的消费项目跑
`sdflow-init update`，核验其 `generation-process.md` 已含分支 A/B、`workflow.md` 与
`quality-layering.md` 已含 G1 具名例外）。源仓七处 canonical **已全部同步**，SA-11 的
「同一个 change 内消除分叉」针对的是**源**（spec 自带 Scenario「下游获得方式：本 change 只改源不代下游执行」）。

### 3-3. 两条 spec 措辞与实测不符 —— **spec 文本错，非实现缺口 · 已登记，archive 随 delta 订正**

| 条 | spec 措辞 | 实测事实 | 登记 |
|---|---|---|---|
| SA-05 Scenario「半截产物不被判完成」 | 截断 **design.md** ⇒ `validate --strict` 不过 | `openspec validate --strict`（CLI 1.5.0）**只读 `specs/*/spec.md`**，截断的 design.md 恒判 valid（三方独立复现；`::test_validate_strict_only_covers_delta_specs` 已把该边界机械钉住） | **T232**（`:92`，OPEN） |
| SA-07「`model` 参数 SHALL 填具体模型 id」 | 具体模型 id | Agent 工具的 `model` 是**枚举** `sonnet\|opus\|haiku\|fable`，完整版本化 id 被 `InputValidationError` 当场拒 | **T238**（`:98`，OPEN） |

两条**实现侧均已是正确形态**：`SKILL.md:494-498` 把 validate 的真实覆盖面写成显式诚实边界并明禁
「声称 validate 挡得住半截 design.md」；`SKILL.md:282-286` 写明枚举边界与「MUST NOT 猜一个别名顶上」，
机械守 `::test_skill_records_the_model_enum_measured_limit`。**不判 FAIL**。

---

## 4. 缺口清单

### 核心缺口（FAIL 项）

**无。**

### Minor 缺口（可接受 / deferred，全部已登记）

1. **Minor-1 · T232**：SA-05 一条 Scenario 的 validate 断言对 `design.md` 恒假。实现侧已按可达形态交付 +
   诚实边界成文。⇒ **archive 阶段随 delta 同步订正 spec 措辞**。
2. **Minor-2 · T238**：SA-07 的「具体模型 id」与 harness 枚举不符。SKILL.md 侧已是可执行的正确措辞。
   ⇒ **archive 阶段随 delta 同步订正**。
3. **Minor-3 · T239**：canonical 七处只落源仓，下游消费项目仍读旧入口规则。条件句生效，
   ⇒ merge 后由人跑 `sdflow-init update` 推下游。
4. **Minor-4 · T242**：SKILL.md ≤600 行体量门以 `wc -l` 计，可由重排软换行规避 ⇒ 对该文件已无实际约束力，
   且**无机械覆盖**（只有 tasks 2.10 一句人跑）。本轮实测正好 600 行（在门内）。修法候选需人拍板。
5. **Minor-5 · T240 / T241**（两条流程性文档缺口，均须 archive 阶段做）：
   - **T240**：design Migration Plan 的回滚第①步写「先跑 uninstall 分支」，而 `setup.sh` 从来没有
     uninstall 开关（全文零命中，task6 实测）。等价可执行动作 = 删 `sdflow-spec/agents/` 后**仍在新版
     installer 上**跑一次 `setup.sh`（已由 `::test_orphans_are_cleaned_even_when_the_whole_source_dir_is_gone` 守）。
   - **T241**：`tasks.md:100` 的阶段三验收门**只有 ✅ 分支、无 ❌/回退分支** ⇒ 「回退形态下可否进
     `/sdflow-done`」在票面上无书面出处。须补该分支。
6. **Minor-6 · 环境状态（非代码缺口，须在 merge 后处置）**：本机 `~/.claude/skills/sdflow-spec`、
   `~/.claude/agents/sdflow-*.md`、`~/.sdflow/workflow` 当前**均指向开发 checkout**
   （`/Users/cheneyzhao/Documents/04-sdflow-skills`）。这是 CLAUDE.md「dev/runtime checkout 纪律」
   允许的**知情临时状态**（为测试而在开发 checkout 跑过 `setup.sh`）；
   `impl-reports/task3-stage1-acceptance.md:508-509` 已声明「合并后须在运行 checkout
   （`~/.skills/sdflow-skills`）重跑 `setup.sh` 还原」。**hand-off 须带上这一条。**

### 已知未核项（阶段一即登记，与本 change 成败无关）

- **T233**：`disable-model-invocation: true` 在 **Codex 宿主**下的语义未实测（Claude 宿主已有两次实证）。
- **T234**：T132 的信号载体枚举与行号锚已被本 change 改过时，实现前须先按四入口现状重列。

---

## 5. code-review 收口状态（旁证，非本轮独立复核）

`code-review-report.md`（frontmatter `code_review: pass`，`reviewed_sha: a9e62d4c…`）报 7 条置信 ≥80 findings
（F1 出境安全门 fail-open / F2 FF-0 只解析首个 change 名 / F3 跨 checkout 废弃定义永久残留 /
F4 S4 漏 change root 及上级 symlink / F5 裸 `ln -snf` + `set -e` 中止整个 setup / F6 重入状态机漏两态 /
F7 deny 文案未 quoting），**全部标「已修 `[impl-review-fix]`」（commit `a9e62d4`）**。
本轮对其中可机验的几条做了对码抽查：F1 的 catch-all 在 `outside-voice.sh:276-282` 与
`SKILL.md:306-310` 双侧在场；F3 的 installer-owned manifest 在 `~/.claude/agents/.sdflow-agents` 实际存在；
F4 的逐组件 symlink 检查在 `SKILL.md:472` 与 `::test_s4_rejects_a_symlinked_ancestor_above_the_change_root`；
F5 的面治在 `setup.sh:42-44` 注释 + 全量 pytest 绿；F6 的 B.1④ 与 0.3 三态分治在 `SKILL.md:359-366`、`:211-225`。

---

PASS
