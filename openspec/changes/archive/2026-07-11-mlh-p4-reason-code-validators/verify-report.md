---
ship-gate:
  verify: PASS
---

# Verify Report — mlh-p4-reason-code-validators

- 日期：2026-07-11
- change：mlh-p4-reason-code-validators
- **结论：PASS**

三校验器（outside_voice_guard / hr_tg_intersect / review_disposition_check）+ anchor_lint 扩字段
已在权威源 `sdflow-init/assets/workflow/tools/` 完整实现，测试 190 passed（`-W error` 零 warning），
三个消费方 SKILL 真的把手做步换成调校验器，bundle 下游 4 脚本与权威源逐字一致、下游无 tests/。
每条 ✅ 均附可机验锚点（测试名 / 文件:行 / commit）。

## 逐需求核对表

### capability: outside-voice-reuse-guard（T80）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 三判归约唯一 reason_code、六枚举 | `outside_voice_guard.py:12-13` REASON_CODES + `classify():107-130` 按序; test `test_reason_codes_are_six_enum:75` | ✅ |
| Scenario simulated-source | `classify():119`; test `test_simulated_source:50` | ✅ |
| Scenario 产物早于源→stale + 排除评审产物自身 | `classify():122` + `source_max_mtime():65-82` SOURCE_FILES allowlist; test `test_stale:55` / `test_review_artifacts_excluded_from_freshness:125` / `test_specs_file_counts_as_source_stale:135` | ✅ |
| Scenario codex 段不可解析→section-not-found | `classify():126-127` + `parse_codex_findings():85-104`; test `test_section_not_found:60` / `test_malformed_codex_findings_section_not_found:150` / `test_fenced_codex_anchor_not_counted_findings:166` | ✅ |
| Scenario findings=0→zero-findings | `classify():128-129`; test `test_zero_findings:65` | ✅ |
| Scenario 文件缺失→file-missing | `classify():110-111`; test `test_file_missing:70` | ✅ |
| Scenario 三判全过→none exit0 | `classify():130` + `main():145`; test `test_none_reusable:45` | ✅ |
| fs-mtime 直比、纯 stdlib、无 subprocess、不读 config | `classify():122` os.stat 直比、无 subprocess import; test `test_no_subprocess_no_os_import_ast:185`（AST 静态断言） | ✅ |
| 坏输入 fail-closed（锚缺失/mode 非枚举）非零退出+stderr | `parse_mode():51-62` EmitError + `main():141-143`; test `test_anchor_missing_fail_closed:84` / `test_mode_non_enum_fail_closed:92` / `test_change_dir_no_sources_fail_closed:104` | ✅ |
| 判定序（来源>新鲜度>结构） | test `test_simulated_precedes_stale:113` / `test_stale_precedes_structure:118` | ✅ |

### capability: hr-tg-intersection-check（T81）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 模型传入命中集 ∩ HR-TG，输出带「依据模型判定」不 emit 裸 none | `hr_tg_intersect.py:73-90` intersect+render; test `test_hit_members:38` / `test_no_intersection:47` / `test_empty_declared_set:54` | ✅ |
| Scenario 命中 HR-TG 成员 + sorted 确定序 | `_dedup_sorted():69-70` sorted(set); test `test_hit_members:44` / `test_dedup_and_sorted_numeric:63` | ✅ |
| Scenario 无交集→none、空集→none（依据可见） | test `test_no_intersection:47` / `test_empty_declared_set:54` | ✅ |
| HR-TG 单一源读、禁硬编码 | `load_hr_tg_subset():25-51`; test `test_single_source_mutability:89` / `test_reads_real_catalog_members:99` / `test_no_hardcoded_member_list:188` | ✅ |
| --trigger-catalog 入参、禁 __file__ 推导（A3） | `main():98-99` argparse; test `test_no_file_derived_catalog_path:180`（AST 断言无 __file__） | ✅ |
| 单一源损坏 fail-closed、不静默空子集 | `load_hr_tg_subset():38-50` EmitError; test `test_missing_catalog:109` / `test_missing_hr_tg_section:115` / `test_missing_member_line:123` / `test_empty_member_line:131` / `test_malformed_tg_token:151` | ✅ |
| 纯 stdlib 无 subprocess | test `test_no_subprocess_no_os_import_ast:159` / `test_no_exec_tokens_in_source:173` | ✅ |
| anchor_lint 认 declared= 字段 | `anchor_lint.py:160` HR_TG_REQUIRED_FIELDS + `check_hr_tg():163`; test `test_hr_tg_declared_present_ok:164` / `test_hr_tg_missing_declared_violation:174` | ✅ |

### capability: roadmap-review-reconcile（T82）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 小节存在+非空断言、三 reason_code | `review_disposition_check.py:115-122` classify; test `test_ok_real_mlh:29` / `test_empty_real_template:31` / `test_missing_real:32` | ✅ |
| Scenario 小节缺失→section-missing 非零（不真空通过） | `classify():117-119` + `main():145`; test `test_missing_real:32` / `test_cli_missing_exit_nonzero:192` | ✅ |
| Scenario 仅脚手架/空→section-empty | `_has_entity_content():92-112`; test `test_section_only_html_comments:67` / `test_section_only_whitespace:72` / `test_section_only_thematic_break:77` / `test_section_empty_fence_only_markers:106` | ✅ |
| Scenario 有内容→section-ok-DISPOSITION-UNCHECKED exit0 | `classify():122`; test `test_ok_real_mlh:29` / `test_section_fence_with_body_is_ok:112` | ✅ |
| 信任边界：不断言逐条、禁裸子串「未处置」、fence/结构感知 | `_annotate_lines():36-67` fence-aware + docstring:19-25 声明; test `test_no_naive_substring_match_on_weichuzhi:52` | ✅ |
| Scenario 收尾声明句不假阳（真实 in-repo 负例） | test `test_closing_declaration_not_false_positive_mlh:37` / `_wco:42` / `test_closing_declaration_bracket_variant_double_corner:47` | ✅ |
| Scenario 不冒充逐条完整性 | 输出码尾缀 -DISPOSITION-UNCHECKED (`:19`); docstring 显式声明 | ✅ |
| fence trap（伪标题在 fence 内）→missing | `find_section_body():70-89`; test `test_fence_trap_section_inside_code_fence_is_missing:60` | ✅ |
| 文件不可读 fail-closed | `main():131-143` EmitError; test `test_cli_missing_file_fail_closed:167` / `test_cli_directory_path_fail_closed:173` | ✅ |
| 不读 config | test `test_does_not_read_config_file:232` | ✅ |

### 组 4 SKILL 接入

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 4.1 spec-review 接 outside_voice_guard | `sdflow-spec-review/SKILL.md:40` 调 `outside_voice_guard.py --review-path … --change-dir …` | ✅ |
| 4.2 spec-review + code-review 接 hr_tg_intersect（--tg-set） | `sdflow-spec-review/SKILL.md:56` + `sdflow-code-review/SKILL.md:75` 调 `hr_tg_intersect.py --tg-set … --trigger-catalog …` | ✅ |
| 4.2 anchor_lint 认 declared= | `anchor_lint.py:160,164`（见上表） | ✅ |
| 4.3 roadmap 接 review_disposition_check + 信任边界声明 | `sdflow-roadmap/SKILL.md:346-349` 调 `review_disposition_check.py --task-log …` + 显式信任边界声明行 | ✅ |

### 组 5 bundle 回灌 + 验收

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 5.1 下游 4 脚本与权威源逐字一致、下游无 tests/ | `diff` outside_voice_guard/hr_tg_intersect/review_disposition_check/anchor_lint 全 IDENTICAL；`openspec/workflow/tools/tests/` 不存在 | ✅ |
| 5.2 pytest -W error 全绿 | `python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -W error -q` → 190 passed | ✅ |
| 5.3 本仓 dogfood 真实产物只读核对 | `.outside-voice/` 产物存在（code-voice-*）；T82 真实 task-log 负例 fixtures 入测（`test_closing_declaration_not_false_positive_mlh/_wco`） | ✅ |

## 缺口清单

- 核心缺口（FAIL）：**无**。三校验器逻辑、测试覆盖、SKILL 接入、bundle 一致性全部落地并有可机验锚点。
- Minor / deferred：5 项 hardening 已 defer 到 todolist **T136-T140**（code-review-report 已记），属已知延后改进、非本 change 核心需求缺口，不影响 PASS。中间态 fence-aware 假绿已由冷层代码审修复（commit 6ef7d45 + 8f455c8），当前代码为准已全绿。

---

PASS
