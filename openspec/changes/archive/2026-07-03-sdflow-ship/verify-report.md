# verify-report — sdflow-ship

- **日期**：2026-07-04
- **change**：sdflow-ship
- **验证方式**：evidence-anchored（每条 ✅ 附测试名 / commit / 文件:行；无锚点判 gap）；活证 `python3 -m pytest sdflow-ship/tests/ -q -W error` → 44 passed；全仓 `python3 -m pytest -q` → 277 passed。

## 结论：PASS

<!-- ship-gate: verify=PASS -->

## 逐需求核对表

### R-SS-1 阶段三编排台账确定性（ship_gate，ADDED）

| 需求/任务 | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| 契约头注释：D2 双输出 + 退出码 0/3/4/5/6（6=UNKNOWN 独立语义）+ verdict×exit×next 全枚举表 + D5 锚行集 + D11 已知不覆盖声明 + 只读零副作用（T1.1） | ship_gate.py:1-45（头注释）；退出码常量 :61；`emit` 双输出 :107-115 | ✅ |
| 三报告模板补 ship-gate 锚行，单测双向一致（T1.4） | test_anchor_contract.py::test_gate_header_lists_all_anchors、::test_skill_templates_carry_same_literals；assert-log #4/#5/#6 | ✅ |
| §三决策图全逻辑：pre-flight → 5.5(TG-02 字面子串) → 6/7(窗口内 checkpoint 主锚+复选框辅) → 8 → 9 → final(分支已并) + 多锚冲突 UNKNOWN（T1.2） | ship_gate.py `decide` :192-299；`pick_exclusive` 冲突→UNKNOWN :118-128；窗口 `plan_first_sha`/`done_task_ids` :147-167；`branch_state` :178-189 | ✅ |
| 冲突锚并存 → UNKNOWN 点名冲突行〔D4〕 | test_gate_preflight.py::test_verify_conflict_anchors_unknown；ship_gate.py:121-123 | ✅ |
| plan 标题命中 0 → UNKNOWN〔D7〕 | test_gate_impl_progress.py::test_plan_zero_titles_unknown；ship_gate.py:228-230 | ✅ |
| pytest 全盘面态（tmp_path + git init 序）（T1.3） | test_gate_preflight(5) + test_gate_tail(7) + test_gate_impl_progress(12) 覆盖拒跑/过门/TG-02/plan缺/标签集/双通道/blocker/verify | ✅ |
| D9 新鲜度分域实现〔Q1=B/Q3=A〕（T1.5） | ship_gate.py `is_stale` :77-96（design 域盯四件套 / code 域盯 openspec/ 外 / 未提交→uncommitted） | ✅ |
| 陈旧 FAIL 不卡死 resume | test_gate_freshness.py::test_stale_fail_reruns_not_exit5；ship_gate.py:271-276 | ✅ |
| 干预后陈旧 PASS 不放行 | test_gate_freshness.py::test_stale_pass_reruns_not_ship | ✅ |
| design-approved 不因实现提交失鲜 + 四件套改则失鲜 | test_gate_freshness.py::test_design_anchor_survives_impl_commits、::test_design_anchor_stale_on_design_edit；ship_gate.py:90-93,206-211 | ✅ |
| 未提交报告 fresh + freshness=uncommitted | test_gate_freshness.py::test_uncommitted_report_is_fresh；ship_gate.py:85-86 | ✅ |
| 窗口污染态（预埋 main 遗留标签 + merge 外部标签，断言窗口不吃污染） | test_gate_impl_progress.py::test_window_excludes_legacy_and_merge、::test_merged_branch_inner_commits_do_enter_window | ✅ |
| git 健全性前置检查（非 git 仓 → UNKNOWN） | test_gate_impl_progress.py::test_non_git_root_unknown；ship_gate.py:196-198 | ✅ |
| 非 UTF-8 报告不崩 | test_gate_preflight.py::test_gbk_report_no_crash；ship_gate.py:103,138,143 errors="replace" | ✅ |

### R-SS-2 模型档位映射（model-tiers，ADDED）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 新建 model-tiers.md（三档+职责+canonical 缺省 opus/sonnet/haiku+adr/0006(c)）（T3.1） | sdflow-init/assets/workflow/model-tiers.md（全文）；test_model_tiers.py::test_tiers_file_is_truth_source | ✅ |
| config.template.yaml 加可选覆盖段 model-tiers（缺省勿填）（T3.2） | config.template.yaml:55-62；test_model_tiers.py::test_config_overlay_section | ✅ |
| 四 SKILL 引用句 + 全文零裸模型名（无白名单口子）（T3.3） | test_model_tiers.py::test_skills_zero_inline_model_names（全文断言，BARE 正则）；live grep 四 SKILL 零裸名；SKILL 引用行 sdflow-ship:24 等 | ✅ |
| 消费仓无覆盖用 canonical 缺省 / verify 档来自映射 | model-tiers.md 铁律行「带门禁步 MUST NOT 降档」+ 强档=verify 终门 | ✅ |

### R-SS-3 阶段三连续+决策协议（MODIFIED）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 新建 sdflow-ship/SKILL.md：触发词收窄（避让 gstack /ship）+ 每步前后 MUST 调 gate + 门禁上抛 + D8 零 git + merge 透传 + SHIPPED 模板 + 不越两人类点 + D9 resume 节（T2.1） | sdflow-ship/SKILL.md:3(触发) :12(gate 铁律) :20(零git) :21(透传) :37(SHIPPED) :31-35(resume)；test_skill_text.py::test_gate_discipline_present、::test_zero_git_and_passthrough、::test_trigger_words_scoped | ✅ |
| D3 决策协议节（T10）：三级协议 + 禁自评置信 + 复核记录格式（T2.2） | sdflow-ship/SKILL.md:23；test_skill_text.py::test_fuse_and_resume | ✅ |
| 熔断：同步同步重跑一次仍无锚行 → UNKNOWN 上抛，禁无限循环 | sdflow-ship/SKILL.md:29（熔断句）；test_skill_text.py::test_fuse_and_resume | ✅ |
| workflow.md 加编排入口行 + 决策4 去"有把握自动选" + 步6 task<N>- 标签约定（T2.3） | assets/workflow/workflow.md:64(入口) :74(task<N>- 注入 plan 层)；test_workflow_authority.py::test_orchestrator_entry_row、::test_decision4_no_self_confidence、::test_step6_tag_contract；assert-log #1 | ✅ |

### R-SS-4 阶段二串行纪律（MODIFIED，T20）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| sdflow-spec-review Step2 加 MUST 串行句 + 历史并行补救句（T4.1） | sdflow-spec-review/SKILL.md（「MUST 待 Step1」句）；test_serial_discipline.py::test_step2_serial_must_sentence；assert-log #3 | ✅ |

### 收尾与债务闭环（第5/6节）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 全量 pytest 全绿无 warning（T5.1） | live：全仓 277 passed；sdflow-ship 子集 44 passed（-W error） | ✅ |
| grep 断言留档 assert-log.md（T5.2） | assert-log.md（7 主 +1 附加，含第5条真实"失败→修→转绿"闭环） | ✅ |
| instance 同步 openspec/workflow/（model-tiers.md + workflow.md） | diff assets↔instance workflow.md 为空（已同步）；model-tiers.md 双份 955B 一致 | ✅ |
| README/ROADMAP/adr 收尾（T6.1） | 见下方缺口清单（未逐项机验，Minor） | ⚠️Minor |
| T10/T11/T20 set-status DONE + reindex（T6.2） | todolist 2026-07-todolist.md:125/144/229「DONE(change sdflow-ship, 3d0b546; 文件:行)」；commit 3d0b546 存在 | ✅ |
| T6.3 update --dev + hand-off 预置（未勾） | 设计上待「收尾第二步」产出后勾选（verify 时点未到）→ deferred，非门禁缺口 | ⚠️Minor |

## 缺口清单

### 核心缺口
无。R-SS-1/2/3/4 的每条需求与全部 Scenario 均有机器可验证锚点（测试名 / commit 3d0b546 / 文件:行），44 个 ship 用例活证全绿。

### Minor / 可接受 / deferred
1. **T6.1 README/ROADMAP/adr 文档收尾**：未逐项机器核验（无自动化测试覆盖文档类改动）。属可观测性/文档层，不影响核心功能 → 判 PASS 注明。
2. **T6.3 未勾选**：`update --dev` 已完成于 task10；hand-off 预置按设计在「收尾第二步（archive 阶段）」产出后勾选，verify 时点尚未到达该步，属正常 deferred，非功能缺失。
3. **已知不覆盖（头注释已声明，接受并记录）**：openspec/workflow/ 规则漂移不触发陈旧；rebase/--amend 可伪造保鲜（实现禁 --first-parent，措辞留痕）。设计层显式接受。
4. **deferred 债务**：T25（autoplan 原生执行 vs 模拟）、T26（熔断计数脚本化）已在 todolist 记 OPEN 挂 sdflow-ship，属 hand-off 引导的后续 change，非本 change 门禁项。

---

PASS
