---
ship-gate:
  verify: PASS
---

# verify-report — mlh-p4-maintain-scan

- 日期：2026-07-09
- change：mlh-p4-maintain-scan
- **结论：PASS**

证据基线：`sdflow-maintain/tests/` 全绿 **38 passed**；dogfood `python3 sdflow-maintain/scripts/maintain_scan.py --root .` **rc=0**、报告输出「一致，无差异」、retro-report 未误报「已删未清理」、`git status` 快照前后无变更（纯读）。

## 逐需求核对表

| 需求/任务 | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| R1 双向 set-diff（新增未索引 / 已删未清理） | `maintain_scan.py:232` `set_diff` + `run_scan:249`；`test_new_unindexed_spec` / `test_stale_indexed_rule` / `test_fully_consistent` | ✅ |
| R1 join-key=链接路径（specs/{n}/spec.md、rules/{n}.md，非首列名） | `_SPEC_LINK:35` / `_RULE_LINK:36` / `parse_index_entries:103`；`test_parse_index_entries_table_row_positive_regression` | ✅ |
| R1 非-spec/rule 链接不误纳（②b retro-report 静默排除） | `parse_index_entries:143`（elif 后不入集）；`test_non_spec_link_row_excluded` / `test_non_spec_link_still_excluded_not_fail` | ✅ |
| R1 散文行内偶然链接不误当已索引（限定表格行） | `parse_index_entries:124`（startswith `|` ∧ ≥2 `|`）；`test_parse_index_entries_prose_link_not_indexed` | ✅ |
| R1 托管块排除（token 子串、fence-aware） | `split_managed_block:65` + `_is_marker_line:60`；`test_managed_block_entries_not_stale` / `test_index_marker_inside_fence_not_treated_as_real` / marker_consistency `test_end_to_end_real_index_managed_block_skipped` | ✅ |
| R1 M8 疑似 spec 误置托管块内→告警 | `split_managed_block:95`（`_SPEC_LINK.search(block)`）；`test_mgr_warns_not_consistent` | ✅ |
| R2 CLAUDE.md 过时引用（fs 存在性判定） | `scan_claude_refs:175`（直查 `name in fs_specs/fs_rules`）；`test_claude_stale_ref_reported` / `test_claude_ref_deleted_from_fs_and_index_reported` | ✅ |
| R2 匹配契约（排围栏/行内 code/占位符/泛指） | `_REF:155` / `_PLACEHOLDER:157` / 剥 code+fence `194-196`；`test_claude_placeholder_generic_fence_not_reported` / `test_placeholder_in_specs_domain_not_reported` | ✅ |
| R3 陈旧遮蔽（RULE_MARKERS + checkpoint 孤儿） | `scan_stale_shadow:214` / `RULE_MARKERS:211`；`test_stale_shadow_workflow_body` / `test_stale_shadow_only_tools_clean` / `test_stale_shadow_checkpoint_orphan` | ✅ |
| R-guard RULE_MARKERS==init | `test_marker_consistency.py:test_rule_markers_equal`（init.py:169 vs maintain:211 均 `("workflow.md","spec-checklists","code-checklists")`） | ✅ |
| R-guard token==init.MARK_IDX[0].split()[1] | `test_managed_token_matches_init_mark_idx`（init MARK_IDX:45 → `opsx-init:rules:start` == MANAGED_TOKEN_START:31） | ✅ |
| R-guard 加载失败 hard-fail 非 skip | `test_marker_consistency.py:_load`（path-assert + exec_module 抛异常，无 try/except-skip） | ✅ |
| R4 INDEX 缺失→非零 | `_read_index:241`；`test_index_missing_nonzero` | ✅ |
| R4 marker 不配对→非零 | `split_managed_block:89`；`test_managed_marker_unpaired_fails` | ✅ |
| R4 ③真少读（链接语法存活抽不出路径）→fail | `parse_index_entries:130-135`；`test_broken_link_target_fails` / `test_broken_link_target_unclosed_fails` | ✅ |
| R4 结构行/表头/分隔不误 fail（①类跳过） | `parse_index_entries:124-127`；`test_fully_consistent`（含表头正常一致） | ✅ |
| R4 fence 未闭合→fail-closed（三处状态机） | `split_managed_block:82` / `parse_index_entries:144` / `scan_claude_refs:202`；`test_index_unclosed_fence_fails` / `test_split_managed_block_unclosed_fence_fails` / `test_parse_index_entries_unclosed_fence_fails` / `test_claude_unclosed_fence_fails` | ✅ |
| R4 0 条合法→退出 0 报全新 | `run_scan`（无 fail 路径）；`test_zero_entries_index_is_ok_not_fail` | ✅ |
| R4 specs/ 缺失→非零；rules/ 缺失→0 空集 | `scan_fs_specs:42`（raise）/ `scan_fs_rules:52`（return set）；`test_specs_dir_missing_nonzero` / `test_rules_dir_missing_is_ok` | ✅ |
| R4 可选输入缺失=空集 benign（CLAUDE/workflow/hack） | `_iter_claude_files:160`（os.walk 无则空）/ `scan_stale_shadow` os.path 判存在；dogfood rc=0 佐证 | ✅ |
| R5 四类分节报告 + 空节占位 | `build_report:260`；`test_stale_shadow_present_not_reported_consistent`（告警不与「一致」并存） | ✅ |
| R5 只读零写（快照前后逐字节等） | `test_readonly_no_file_writes`（os.walk 字节快照）+ dogfood git status 无变更 | ✅ |
| T7.1/7.2 SKILL.md 集成（调脚本+守卫机验表述） | `sdflow-maintain/SKILL.md:17-25` | ✅ |
| T7.3(a)(b)(c) 分类文档三处订正 | CLAUDE.md:36（数据类名单）+ CLAUDE.md:54-55（两类 skill 移入数据类）+ README.md:29-30 | ✅ |

## 缺口清单

### 核心缺口
无。全部 R1–R5 + R-guard 的 Requirement 与 Scenario 均有代码出处 + 测试锚点，且实跑通过。

### Minor 缺口 / 已知接受残差（deferred，可接受）
- **散文化少读残差（H2/Q1 选项 A 只关③类）**：链接语法被整体破坏、退化为无 `[..](..)` 的散文行且对应 spec 已删时仍会假『一致』——spec 已显式登记为已知接受残差，唯一补法（N 对账 B）已被否决并 defer 记 todolist，非本 change scope。可接受。
- **告警文案漂移（M3/D6）**：maintain 抄 init 告警文案 + checkpoint 孤儿路径（第三处跨脚本复述），R-guard 不机验文案（文案守卫脆），已显式 defer 记 todolist。语义等价（遮蔽全局/pin 二选）已满足。可接受。
- **resolve-workflow.sh bash 第 3 份 RULE_MARKERS 副本（4b.3）**：跨语言难同守，本 change 不扩 scope，defer 记 todolist。可接受。
- **T96 正则字符集残差**：`<name>` 限定 `[a-z0-9-]+`，含大写/下划线的边缘 spec 名不匹配——deferred，属已知正则字符集残差，非核心功能缺失。可接受。

## 结论

PASS —— 核心功能（R1 双向 set-diff 全判据、R2 匹配契约、R3 陈旧遮蔽、R-guard 一致性守卫、R4 坏输入 fail-closed 全分层、R5 只读不变量）逐条落实并有机验锚点；38 测试全绿、dogfood rc=0 且零写文件、retro-report 无假阳。残差均为已显式登记、defer 的已知接受项，不阻断。
