---
ship-gate:
  verify: PASS
---

# verify-report — fix-design-gate-freshness-proxy

**日期**：2026-07-20
**change**：`fix-design-gate-freshness-proxy`

## 结论

**PASS** — 两条 delta spec（`spec-workflow` MODIFIED「纯勾选框翻转不失鲜」系列 Scenario + `impl-orchestration` ADDED「dispatch 携带信号权威表」）的每条 AND 子句均找到可机验锚点；tasks.md 中 1.1a / 1.1b 两条被 code-review 推翻的字面约束已如实登记 `done-amendment`，其**目标**（豁免只在纯勾选时成立、取得到前后版 blob）经我独立端到端验证达成。全套件 2036 passed / 0 failed。仅 2 条 Minor 缺口（defer 项 T186 已被后续修复反超未回写；B19 属 code 域、可 defer 但需知会）。

---

## 逐需求核对表

### A. spec-workflow — 「纯勾选框翻转不失鲜」Scenario

| 需求/子句 | 代码出处 / 测试名 | 状态 |
|---|---|---|
| WHEN 帧内**落在 design 监视集内**的路径集恰为 `{tasks.md}`（触及监视集外路径不影响资格） | `ship_gate.py:253-266` `design_watched_subs()`；`ship_gate.py:622`；测试 `test_watched_subs_is_not_the_full_file_list`、`test_tasks_flip_plus_source_code_not_stale`（tasks 4.4e） | ✅ |
| THEN 归一化等值 ⇒ MUST NOT 判失鲜 | `ship_gate.py:576-595` `_tasks_content_exempt`；`test_tasks_only_checkbox_flip_not_stale` | ✅ |
| AND 归一化 MUST 锚定 task-list 行首（复用 `CHECKBOX_RE` 口径） | `ship_gate.py:533-534` 单一 pattern 源 `CHECKBOX_RE_PATTERN` + bytes 派生；`test_checkbox_re_bytes_derived_from_single_source`、`test_content_stale_on_table_and_inline_code_literals`、`test_content_stale_on_prose_literal_marker` | ✅ |
| AND MUST fence-aware（复用 `_line_scoped_hits` fence 口径） | `ship_gate.py:555-560` 共用 `FenceTracker`；`test_content_stale_on_fenced_code_block_flip`、`test_content_stale_on_tilde_fenced_code_block_flip`、`test_content_stale_on_four_backtick_fenced_flip`、`test_content_exempt_conservative_on_unbalanced_fence` | ✅ |
| AND 比较 MUST 按行位置对齐（zip），MUST NOT LCS | `ship_gate.py:593-595`（`len` 不等即 False + `zip`）；`test_content_stale_on_pure_line_reorder` | ✅ |
| AND 保真读取：MUST NOT 复用 `.strip()`/`text=True` 路径 | `ship_gate.py:241-250` `run_git_bytes`（原始字节）；`test_blob_pair_returns_raw_bytes_verbatim`、`test_blob_pair_preserves_crlf_and_trailing_newline_difference`、`test_content_stale_on_crlf_and_trailing_newline_and_edge_whitespace` | ✅ |
| AND 两侧读取显式检查 rc，任一侧失败 ⇒ 保守判失鲜 | `ship_gate.py:634-640`（`error`→`blob-unreadable`；`blob_pair` 的 `ok`）；`test_blob_pair_rc_failure_on_both_sides_is_not_equal_bytes`（专杀 `""==""`）、`test_blob_pair_rc_failure_on_one_side_is_conservative` | ✅ |
| AND MUST NOT 语义 diff / 完整 markdown 解析 | `_normalize_checkbox_lines` 为单 boolean toggle + 行首正则，无 AST | ✅ |
| AND 逐提交独立求值、不依赖工作树 | `is_stale` 全程 `git log`/`diff-tree`/`show`，零工作树读 | ✅ |

### B. spec-workflow — 「勾选框以外的一切 tasks.md 改动照判失鲜」

| 情形 | 测试名 | 状态 |
|---|---|---|
| ① 标记外任何字符变化 | `test_content_stale_on_flip_plus_same_line_wording`、`test_content_stale_on_whitespace_only_change`、`test_e2e_tasks_wording_change_still_stale` | ✅ |
| ② 增/删 `### Task <n>:` 段 | `test_content_stale_on_flip_plus_task_section_added` / `_removed` | ✅ |
| ③ 行重排 | `test_content_stale_on_pure_line_reorder` | ✅ |
| ④ fence/表格/行内反引号/散文字面量 | `test_content_stale_on_fenced_code_block_flip`、`test_content_stale_on_table_and_inline_code_literals`、`test_content_stale_when_second_marker_on_same_line_flips_back`（4.4h） | ✅ |
| ⑤ 同帧还触及 proposal/design/specs | `test_e2e_flip_plus_design_edit_still_stale`（`mixed-paths`） | ✅ |
| ⑥ 新建/删除/`git mv` 迁走 | `test_blob_pair_added_in_this_commit_is_conservative` / `_deleted_` / `_renamed_away_`；**端到端** `test_git_mv_tasks_is_stale_end_to_end` | ✅ |
| ⑦ 状态位不合格（rename/copy/类型/mode） | `ship_gate.py:325-339` `_plain_modification_from_raw`（`status=="M" and src_mode==dst_mode`）；`test_blob_pair_chmod_only_is_conservative`、`test_blob_pair_type_change_to_symlink_is_conservative`、`test_raw_line_rejects_mode_only_change` | ✅ |
| AND 资格判定读 git raw 状态位与 mode，MUST NOT 仅凭 `--name-only` | `ship_gate.py:295-296` `diff-tree -m -r --raw --no-renames -z --root`；`test_frame_paths_include_rename_source`、`test_frame_paths_preserve_tab_unquoted` | ✅ |

### C. spec-workflow — 优先级 / 反声明式 Scenario

| 子句 | 锚点 | 状态 |
|---|---|---|
| ① subject 精确匹配 MUST 在读任何 blob **之前**短路 | `ship_gate.py:731`（位于 `frame_touched_paths` 调用之前）；`test_exact_subject_short_circuits_before_any_blob_read`（monkeypatch 证明未触 blob 读）+ 判别性对照 `test_non_exact_subject_does_reach_blob_read` | ✅ |
| ② 任何 subject 均可凭内容判据获豁免 | 真值表 8 格 `test_tt_*`（精确/变体/空/普通 × 纯勾选/语义）全在 | ✅ |
| AND 豁免判据取自内容本身，MUST NOT 用 plan 存在性/其他 subject 形态 | `test_content_criterion_takes_only_content`、`test_content_channel_verdict_independent_of_subject`（参数化 subject） | ✅ |
| AND 既有 BR-7 精确式逐字保留（tasks 1.4） | `ship_gate.py:731` 逐字未改；回归 `test_impl_review_exempt_bare_and_colon` / `test_impl_review_evil_suffix_stale` / `test_impl_review_fix_variant_stale` / `test_interleaved_impl_review_and_normal_stale` 全绿（tasks 4.5） | ✅ |

### D. spec-workflow — 失鲜诊断 Scenario（tasks §2）

| 子句 | 锚点 | 状态 |
|---|---|---|
| reason MUST 指明触发提交 + 文件 | `ship_gate.py:940-950` `_stale_trigger_hint` + `1221-1224` emit；`test_stale_trigger_category_*` ×4 | ✅ |
| MUST 携带分类原因（四类 + 枚举失败共 5 类） | `ship_gate.py:600-608` `STALE_CATEGORIES`；`test_frame_enum_failed_is_registered_category` | ✅ |
| 机读与人读**同源** | `_stale_trigger_hint(trigger)` 与 JSON `stale_trigger` 同取 `design_res.trigger`（`ship_gate.py:1220-1224`），无二次拼装 | ✅ |
| 默认处置只推「重跑设计门」，`checkpoint(impl-review)` MUST NOT 出现 | `ship_gate.py:1221-1223`；**双向机械守** `test_default_disposition_recommends_rerun_design_gate_only` | ✅ |
| 纯诊断，不改退出码/判据（tasks 2.3、4.4p） | `StaleResult` 是 2-tuple 子类（`ship_gate.py:659-684`）；`test_is_stale_result_stays_two_tuple_compatible`、`test_code_domain_freshness_string_unchanged_and_no_trigger` | ✅ |

### E. impl-orchestration — dispatch 信号权威表

| 子句 | 锚点 | 状态 |
|---|---|---|
| dispatch prompt 必填槽含信号权威表 | `sdflow-implement/SKILL.md:255`；`test_dispatch_carries_signal_authority_table` | ✅ |
| 正面陈述非禁令清单 | SKILL.md:255 起「原文携带」三范畴表 | ✅ |
| 表内容与 gate 实读判据一致（plan 复选框 + checkpoint 标签） | `test_authority_table_matches_gate_consumed_criteria` | ✅ |
| fix 轮次同样携带 | `SKILL.md:355`；`test_fix_dispatch_also_carries_authority_table` | ✅ |
| 缺席不得静默降级 | `SKILL.md:359`；`test_authority_table_absence_not_silently_degraded` | ✅ |
| 机械守在场（tasks 3.3） | `sdflow-implement/tests/test_dispatch_signal_authority.py` 4 例 | ✅ |

### F. tasks.md 中被推翻的两条（重点核）

| 条目 | 判定 |
|---|---|
| **1.1a**（原：MUST NOT 重构成帧级两遍预扫描） | ✅ **偏离已诚实登记**。tasks.md:4 的 `done-amendment` 注记写明：code-review F1 查出 `git log --name-only` 对 merge 提交不输出文件、且 rename 吞源路径（两条 fail-open），故必须改帧级 `diff-tree`。代码侧同样留档（`ship_gate.py:269-293` 完整记 F1-a/b/c 三洞与新协议逐 flag 理由）。**目标达成**——我端到端验证：evil-merge 与 `git mv` 两个原 fail-open 面现在都判 stale（见下） |
| **1.1b**（原：扩 `git log --format=%H`） | ✅ **偏离已诚实登记**。tasks.md:5 注记：`-z` 的 NUL 与 `--format` 帧分隔符互相污染，故分帧与取路径拆两跳。实际实现 `ship_gate.py:708` 仍用 `--format=%H%x1f%s` 分帧（用 `\x1f` 消歧，覆盖「subject 可含空格/冒号」），路径由 `frame_touched_paths` 逐帧取。**「取得到 blob」的目的达成**——`test_frame_sha_parsed_from_subject_with_spaces_and_colons` 锁定 |

> 两条均**未**假勾放行：字面约束失效的理由、替代机制、目标是否达成三者都写进了 tasks.md 与源码注释，且替代机制有独立测试。判 **不构成 gap**。

---

## 亲自跑的验证

### 验证 1 — `_tasks_content_exempt` 十形态直测

```
$ /usr/bin/python3 v1.py
1 pure flip           -> True (expect True)
2 reverse flip        -> True (expect True)     # 4.4d 对称
3 fence ``` flip      -> False (expect False)   # 4.4f
4 fence ~~~ flip      -> False (expect False)
5 indented code flip  -> False (expect False)   # impl-review-fix F3
6 html comment flip   -> False (expect False)   # impl-review-fix F3
7 flip+wording        -> False (expect False)   # 4.2
8 line reorder        -> False (expect False)   # 4.4i 位置对齐非 LCS
9 CRLF                -> False (expect False)   # 4.4j 保真读取
10 unbalanced fence   -> False (expect False)   # 保守回落
```

10/10 与 spec 一致。

### 验证 2 — 端到端真 git 仓（三例，我自建 fixture，非复用仓内 fixture）

```
$ /usr/bin/python3 v3.py
A evil-merge design.md hidden in merge tree: (True, 'stale')
    {'sha':'d3cbdc4','subject':'merge b1','paths':['design.md'],'category':'mixed-paths'}
B git mv tasks.md:                            (True, 'stale')
    {'sha':'9badba2','subject':'rename tasks','paths':['tasks.md'],'category':'shape-unfit'}
C pure flip + src code same commit:           (False, 'fresh')  trigger=None
```

- **A** 正是任务书点名的用例：把未批准的 `design.md` 改动只藏在 merge 提交 resolve 出的树里（两 parent 都没这份改动）。旧 `git log --name-only` 协议下该帧文件列表为空 → 静默 `continue` → 判 fresh（fail-open）。现判 **stale**，且触发点精确指向 `design.md`。**这一条直接证明 1.1a 的机制偏离是必要的、且新机制真的堵上了洞。**
- **B** `git mv tasks.md x.md` 判 **stale/shape-unfit**（`--no-renames` 让源路径进枚举，spec 情形 ⑥ 落实）。
- **C** 反向对照：纯勾选翻转 + `git add -A` 打包源码（真实 checkpoint 形态）判 **fresh**，豁免真的会触发——即 4.4e 要防的「豁免永不触发」没有发生。

### 验证 3 — 全套件

```
$ /usr/bin/python3 -m pytest -q      # 仓根，未改 pytest.ini / conftest.py
2036 passed, 8 skipped, 3 xfailed in 131.35s (0:02:11)
```

0 failed、0 error、无新增 warning 段。tasks 4.8 达成。

---

## 缺口清单

### 核心缺口（FAIL 项）

**无。**

### Minor 缺口（可接受 / 已 deferred）

1. **T186 已被后续修复反超但未回写状态**（Minor，登记卫生）。T186 记于 14:17，述「merge 帧在 live 路径取不到文件列表 → 逐 parent 豁免分支不可达」；而 58cef16 的 F1 修复（改帧级 `diff-tree -m`）已使 merge 帧被正常枚举——我的验证 A 与仓内 `test_merge_frame_is_actually_enumerated` / `test_merge_frame_pure_flip_is_exempt_end_to_end` 均证实该分支现已可达。建议 done 阶段的 issues sweep 把 T186 标 DONE（evidence=58cef16），而非留 OPEN 误导后人。**不影响本 change 功能，判 Minor。**
2. **B19（code 域仍走 `git log --name-only` ⇒ evil-merge 漏检）defer 属边界判断，需知会**（Minor）。同族 fail-open、同一文件，按「相关 bug 立即 fold」的基准可以争论应当 fold。但：① 本 change 的 delta spec 只治理 **design 域**新鲜度；② tasks 4.4p 明确要求 code 域行为**逐字不变**并有回归锁（`test_code_domain_freshness_string_unchanged_and_no_trigger`）；③ 改 code 域会改变 code-review 结论的失鲜语义，属另一条 Scenario 的修订。**结论：defer 合理，但 B19 是真 fail-open，建议尽快单开 change 处理，勿沉底。**

### defer 项落盘核对

| ID | 落盘位置 | 属「不该在本 change 内做」? |
|---|---|---|
| B19 | `openspec/issues/buglist/2026-07-20-buglist.md:8` + 详细块 33-47 | ⚠️ 边界（见 Minor-2），判可 defer |
| B20（git 二进制缺失 → FileNotFoundError 逸出契约退出码集） | 同上 :9 + 块 49-63 | ✅ 环境健壮性，与本 change 判据无关 |
| T186 | `openspec/issues/todolist/2026-07-*-todolist.md` | ✅ 已落盘（但见 Minor-1，其实已修） |
| T187（测试 helper flag-argument smell） | 同上 | ✅ 测试可读性，非功能 |
| T188（仓根 pytest 同 basename 收集中断无机械守） | 同上 | ✅ 基础设施，跨 skill 面 |
| T189（基准 5 警号：`_normalize_checkbox_lines` 第 4 轮补语法分支，应反转白名单） | 同上 | ✅ 架构级重构，超出本 change scope；已正确识别为基准 5 警号 |
| T190（`run_git*` 无 timeout） | 同上 | ✅ 全脚本面基础设施 |
| T191（评审 diff 包被 `git add -A` 带进版本库） | 同上 | ✅ 流程/仓库卫生，非本 change 功能 |

8 条 defer 项**全部真实落盘**（frontmatter item + marker 详细块双写）。除 B19 为边界判断外，其余属正当 defer。

---

PASS
