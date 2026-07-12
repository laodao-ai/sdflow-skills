---
ship-gate:
  verify: PASS
---

# Verify Report: add-sdflow-architecture

- 日期：2026-07-12
- Change：add-sdflow-architecture

## 结论

**PASS** —— 13 条 spec Requirement（architecture-design 12 + roadmap-planning 1）与 tasks.md 五组全部有可机验证据锚点落地。核心功能（脚手架/状态机/结构 lint/分家写入/五步编排/生态路由）齐备，106 个 pytest 全绿，开发 checkout symlink 已建，e2e 演练（SM-1/2/3）留痕齐全。仅 1 处 Minor 文档/测试措辞讨嫌（见缺口清单），不影响核心功能，判 PASS。

验证环境自查：`/usr/bin/python3 -m pytest sdflow-architecture/tests/ -q` → **106 passed**。

## 逐需求核对表

### architecture-design capability（12 条 Requirement）

| 需求/任务 | 代码出处（文件:行/测试名/commit） | 状态 |
|---|---|---|
| **REQ-1** 事实三问 fail-closed 锁 draft | `sad_scaffold.py:380 _precheck_skeleton`（facts 三键+假设对账走**正文实扫** `check_assumptions`，MUST NOT 读 `assumptions_open` 缓存作门禁）；缺项 exit 5 → `test_sad_scaffold.py::test_missing_fact_locks_draft`；齐备升级 → `::test_happy_path_to_skeleton_ready_inserts_slice`；人门位置钉死（走查洞后/迁移前）+ facts 时序纪律 → `SKILL.md:268` §4.4、`SKILL.md:115` 时序纪律加粗 | ✅ 实现 |
| **REQ-2** SAD 十节骨架完整性 | `sad_lint.py:35 _check_sections`（缺节→`missing-section`）；缺横切节 → `test_sad_lint.py::test_missing_section_reason_code`；十节全存在/N-A → `::test_pass_honest_code`；裸 N/A → `::test_na_without_reason` | ✅ 实现 |
| **REQ-3** 拆分规则集执行 + AP 自检前置 | `references/decomposition-rules.md`（R1–R11 L8-77 + AP1–AP4 L79-108，两轴正交提醒 L77）；SKILL.md §② `SKILL.md:138` AP 自检前置 + before/after 三行结构化痕；分解判据落 ADR → `sad_scaffold.py:278 _cmd_adr_new`（`test_adr_new_max_plus_one`）+ `SKILL.md:344` Edit 补写 ADR 正文指示。AP 拦截本身为语义判断（无确定性信号，诚实归模型+人门） | ✅ 实现 |
| **REQ-4** 候选数由仲裁分歧驱动 | `SKILL.md:153` §② 分歧驱动 + 单方案显式声明行 + log；上限 3 归并 `SKILL.md:156`；`references/decomposition-rules.md` R8 仲裁。候选真实性无确定性信号，SKILL.md 显式声明归人门（行为编排，无脚本门可锚，符合诚实边界） | ✅ 实现 |
| **REQ-5** 假设显影 + 数值溯源 | 集合双向相等+双侧无重号 → `sad_schema.py:224 check_assumptions`；未处置阻塞 → `test_sad_scaffold.py::test_unresolved_assumption_locks_draft`；缓存 mismatch 独立码 → `sad_lint.py:47`+`test_sad_lint.py::test_cache_mismatch_independent_code`；重号集合对账 → `::test_duplicate_number_set_reconciliation`；处置经 `--assumption` 人门后 → `sad_scaffold.py:600 _cmd_set_assumption`+`SKILL.md:274` 时序；数值溯源〔人拍/推荐待校准〕→ `SKILL.md:178` | ✅ 实现 |
| **REQ-6** 状态机 + frontmatter 机器可读 | 非法 status fail-closed → `sad_schema.py:154`+`test_sad_lint.py::test_enum_invalid_fail_closed`；schema 版本不匹配独立码+指引（不与坏输入 exit2 共用）→ `sad_lint.py:172`+`::test_schema_version_mismatch_not_fail_closed`；质量属性全序 → `sad_lint.py:60`+`::test_quality_attr_order`；文档级无 frozen（`STATUS_ENUM` `sad_schema.py:16`）；contract 成熟度标签 `CONTRACT_ENUM`；迁移表驱动 `sad_scaffold.py:372 TRANSITIONS`（表外拒 `::test_out_of_table_transition_refused`）；组合不变式 `sad_lint.py:79`（`::test_contract_invariant`） | ✅ 实现 |
| **REQ-7** 冷走查 + 评审升档 | 默认档冷走查 fresh 子代理 + 执行者字段留痕 → `SKILL.md:199` §4.1；机械前置（sad-log ≥1 行「走查」+「升档判定」缺→exit5）→ `sad_scaffold.py:405 _precheck_walkthrough_logs`+`test_sad_scaffold.py::test_b13_transition_skeleton_requires_walkthrough_log`；Codex 宿主 self-review-degraded → `SKILL.md:214`；outside voice 经 `~/.sdflow/hack/outside-voice.sh`（已存在可执行 7224B）分支表+显式降级不静默 → `SKILL.md:235` §4.3。走查执行/outside-voice v1 无自动化（诚实标注，TG-18 表末行） | ✅ 实现 |
| **REQ-8** skeleton-ready 交棒骨架切片建议节 | 交棒节完整（穿越点集==第5节子系统集）→ `sad_scaffold.py:380 _precheck_skeleton`+`test_sad_scaffold.py::test_happy_path_to_skeleton_ready_inserts_slice`、`::test_pierce_set_mismatch_refused`；落地移除节 → `sad_scaffold.py:438 remove_slice`+`::test_validated_removes_slice_and_fallback_logs_reason`；lint 按 status 分支断言 → `sad_lint.py:116 _check_slice_branch`+`test_sad_lint.py::test_slice_branch_assertions`、`::test_slice_pierce_set_mismatch`；收尾行 → `SKILL.md:329`；建议非契约/不代开 → `SKILL.md:301` | ✅ 实现 |
| **REQ-9** 分家落位 + 单一真相源 | 已存在不静默覆盖 exit4 → `sad_scaffold.py:222`+`test_sad_scaffold.py::test_singleton_no_silent_overwrite`；adr-new 编号 max+1/无法识别 fail-closed → `sad_scaffold.py:296`+`::test_adr_new_max_plus_one`、`::test_adr_new_unrecognized_pattern_fail_closed`；CONTEXT.md ## Language 同名不覆盖冲突报告 → `sad_scaffold.py:328 _cmd_context_add`+`::test_context_add_append_and_conflict`；preflight 两级 → `sad_scaffold.py:165`+`::test_preflight_no_openspec_fail_closed`、`::test_preflight_level2_first_create`；validated 回写豁免分流 → `SKILL.md:368` 迁移速查表；recorder 式直写 → `SKILL.md:20`；一仓多系统显式不支持 → `SKILL.md:100` | ✅ 实现 |
| **REQ-10** lint 输出诚实 | 通过码 `structure-ok-SEMANTICS-UNCHECKED` → `sad_schema.py:45 PASS_CODE`+`test_sad_lint.py::test_pass_honest_code`；坏输入 fail-closed `[sad_lint] FAIL:` 物理区分 → `sad_lint.py:25 _die`+`::test_bad_input_fail_closed`、`::test_non_utf8_fail_closed`；每 reason_code 带 next-step → `sad_schema.py:46 REASON_NEXT_STEP`+`test_sad_schema.py::test_every_reason_code_has_next_step` | ✅ 实现 |
| **REQ-11** 触发分工与互相指路 | sdflow-architecture description 含「时间轴规划→用 /sdflow-roadmap」+ 前置条件 → `sdflow-architecture/SKILL.md:8`；sdflow-roadmap description 含「先 /sdflow-architecture（消费仓需已 sdflow-init）」→ `sdflow-roadmap/SKILL.md:11`。两侧均注前置条件（消费仓需已 sdflow-init） | ✅ 实现 |
| **REQ-12** 判定留痕 + 走查矩阵落位 | append-only 留痕不改既有行 → `sad_scaffold.py:88 append_log`+`test_sad_scaffold.py::test_log_append_only_bytes`；step=N/候选快照/走查执行者字段 → `SKILL.md:378` 留痕总则 + continue 断点恢复 `SKILL.md:93`；走查矩阵内嵌 SAD 第6节、无独立 report → `SKILL.md:203`+`references/sad-template.md:108` 第6节矩阵槽 | ✅ 实现（见 Minor 缺口） |

### roadmap-planning capability（1 条 Requirement）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 新项目起步架构先行指路 | `sdflow-roadmap/SKILL.md:11` description 含「新项目起步尚无架构设计（SAD）时，先 /sdflow-architecture（消费仓需已 sdflow-init）」——指路句 + 前置条件双备 | ✅ 实现 |

### tasks.md 五组核对

| 组 | 关键锚点 | 状态 |
|---|---|---|
| 1 共享 schema 与 scaffold 内核（1.1–1.6） | `sad_schema.py`（枚举/正则/reason 映射/解析函数同置 fence-aware）、`sad_scaffold.py`（init/preflight/状态机迁移表/假设对账/单例/adr-new/context-add）、`test_sad_scaffold.py`（正负路径全覆盖） | ✅ 实现 |
| 2 lint v1 最小机械集（2.1–2.5） | `sad_lint.py` 节/假设/排序/枚举/版本/不变式/建议节分支 + 输出诚实；`test_sad_lint.py` 每类正负 ≥2 | ✅ 实现 |
| 3 references 六件（3.1–3.6） | sad-template / decomposition-rules(R1-11+AP1-4) / intake-questionnaire(三问+追问) / quality-criteria(S1-11) / review-lenses(S 引用+BASE-29+升档信号) / checklists 四件 | ✅ 实现 |
| 4 SKILL.md 编排（4.1–4.7） | frontmatter+触发；五步流程主体；骨架切片建议节；分家指令+二次触发编排；信任边界×3（原两条已扩至三条）；触发分工双侧；模型档位一行引 model-tiers.md | ✅ 实现 |
| 5 收尾与端到端验证（5.1–5.4） | README 条目 `README.md:23`；setup.sh symlink（`~/.claude/skills`+`~/.codex/skills` 双装已验）；e2e 演练 + SM-1/2/3 逐条核对留痕 `impl-verify-notes.md`；106 pytest 绿；frozen-diff/JSON schema 落 todolist（proposal 已登记） | ✅ 实现 |

## 缺口清单

### 核心缺口（FAIL 项）

无。

### Minor 缺口（可接受 / deferred）

1. **【可接受·措辞】tasks.md 2.5 提到「走查后无独立 report 文件（glob 断言）」，实际无该专项 glob 断言测试。** 现有 glob 断言覆盖的是原子写 tmp 残留（`test_atomic_no_temp_residue`）与 ADR 文件名（`test_adr_new_*`）。REQ-12「MUST NOT 生成独立走查报告文件」本质是 SKILL.md/子代理的行为约束——lint 只读单个 `sad.md`，脚本层无从对「未生成的外部文件」做机验断言；该 MUST NOT 由 SKILL.md §4.1 指令 + 模版第 6 节内嵌矩阵结构性承接。属诚实边界内的行为约束，非脚本可门禁项，不构成核心功能缺失。

2. **【预期·deferred】outside voice 升档降级、走查 fresh 子代理执行、AP 自检拦截、候选真实性等 SKILL.md 行为编排步 v1 无自动化测试。** 这些是无确定性信号的语义/编排行为（TG-18 测试覆盖图末行已诚实标注「外部 CLI，v1 无自动化——诚实标注」），符合本仓「机械化优先 + 残余诚实归语义」基准；机械可锚的前置（走查/升档判定 log 存在性）已由 `_precheck_walkthrough_logs`（B13）机械守住。可接受。

3. **【预期·非缺口】新鲜脚手架模版 lint 非 0（quality-attr-order-broken 等）。** 实测 `init` 直出的裸模版含占位内容、第 1 节尚无有序质量属性列表，lint 报 `quality-attr-order-broken`——这是**正确行为**：模版是待操作者填充的骨架，非完成态 SAD。完成态 e2e（`impl-verify-notes.md` transcript 第 26-27 行）lint 退出 0 + `structure-ok-SEMANTICS-UNCHECKED`，SM-1 达成。

---

PASS
