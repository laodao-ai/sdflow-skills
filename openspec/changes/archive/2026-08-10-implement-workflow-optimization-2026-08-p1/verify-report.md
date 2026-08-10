---
ship-gate:
  verify: PASS
  reviewed_sha: a4824f4810dfc5890ca7d7c786d9d41724caf86e
---

# Verify Report — implement-workflow-optimization-2026-08-p1

## 逐需求核对表

### R-IS1: reopen 命令契约

| 需求点 | 判定 | 证据锚 |
|---|---|---|
| 1.1 `reopen` 子命令实现（守卫/状态/字段清理/M-2 原子序/reindex） | PASS | `sdflow-issues/scripts/issues_v2.py:612` (`cmd_reopen`) |
| 1.1 closed/ 限定守卫 | PASS | `issues_v2.py:627-628`（`location == "open"` → `_die`） |
| 1.1 pool/前缀一致守卫 | PASS | `issues_v2.py:634-635` |
| 1.1 `--reason` 必填 | PASS | `issues_v2.py:618`（`_reject_line_unsafe`）+ argparse `required=True` |
| 1.1 中断残留幂等恢复 | PASS | `issues_v2.py:641-651`（`residue` 分支：检测 closed/ 内非终态，跳过字段清理/历史行） |
| 1.1 状态默认 OPEN，`--to` 非终态白名单 | PASS | `issues_v2.py:609`（`REOPEN_TARGET_STATUSES = ("OPEN", "PROPOSED")`）+ `:637-638` |
| 1.1 三终态字段→null，原 closed_reason 进历史行 | PASS | `issues_v2.py:653-666` |
| 1.1 空 closed_reason 写「（无 closed_reason）」 | PASS | `issues_v2.py:654`（`if orig_closed_reason else "（无 closed_reason）"`） |
| 1.1 原子序：closed/ 原位写 → git mv | PASS | `issues_v2.py:668-697` |
| 1.1 命令内自动 reindex + 失败自愈提示 | PASS | `issues_v2.py:699-704` |
| 1.1 复用既有 mechanics，MUST NOT 依赖 sdflow_issues_core | PASS | `issues_v2.py:7-8`（docstring 声明不 import）；grep 确认无 `from sdflow_issues_core` / `import sdflow_issues_core` |
| 1.1 MUST NOT 改 set-status 守卫 | PASS | `test_issues_v2.py:682` (`test_cli_set_status_still_rejects_closed_after_reopen_command_exists`) |
| 1.2 往返契约测试 | PASS | `sdflow-issues/tests/test_issues_v2.py:472` (`test_cli_reopen_roundtrip_returns_issue_to_open_with_cleared_fields`) |
| 1.2 拒绝面三例 | PASS | `test_issues_v2.py:569` (open 项)、`:582` (缺 reason)、`:596` (终态 --to) |
| 1.2 中断残留幂等恢复用例 | PASS | `test_issues_v2.py:628` (`test_cli_reopen_recovers_from_interrupted_residue_without_duplicate_history`) |
| 1.2 reindex 对 closed/ 非终态告警 | PASS | `test_issues_v2.py:665` (`test_reindex_warns_on_closed_non_terminal_residue`) |
| 1.2 set-status 零回归 | PASS | `test_issues_v2.py:682` |
| 5.3 SKILL.md 补 reopen 用法块 | PASS | `sdflow-issues/SKILL.md:284-309`（reopen 段完整） |
| 5.3 「不可再改 status」措辞改为「不可经 set-status 再改」 | PASS | `sdflow-issues/SKILL.md:284`（「不可经 `set-status` 再改 status」） |

### R-WR1: per-镜实修率历史回算

| 需求点 | 判定 | 证据锚 |
|---|---|---|
| 2.0 真语料试算前置 | PASS | `impl-reports/task2-fixrate.md`（记录试算结果） |
| 2.1 fix-status 三态精确 needle | PASS | `retro_report.py:343`（`_FR_NEEDLE = "已修[impl-review-fix]"`）+ `:393-403`（`_fr_classify_status`） |
| 2.1 裸串/处置动词不命中 needle → 未知桶 | PASS | `retro_report.py:401`（`"unknown_disposal"` 分支） |
| 2.1 封闭 lens 关键词表（LENS_ENUM 同源六值） | PASS | `retro_report.py:352-357`（`_FR_LENS_MAP`，6 个 canonical 值 + `域` 别名） |
| 2.1 仅有界来源记号内匹配（表格来源列 / 〔〕/【】） | PASS | `retro_report.py:427-433`（`_FR_BRACKET` + `_fr_table_cols`）+ `:439`（仅 `regions` 内匹配） |
| 2.1 0/多命中 → 未知桶 | PASS | `retro_report.py:440`（`len(hits) == 1 else None`） |
| 2.1 复用 `_fence_aware_lines` | PASS | `retro_report.py:422` |
| 2.2 聚合④段渲染 | PASS | `retro_report.py:1003-1007`（`fixrate_aggregate` + `render_fixrate_table`） |
| 2.2 阈值 5 单一源常量 | PASS | `retro_report.py:341`（`FIXRATE_MIN_SAMPLE = 5`）+ `:542`（使用处） |
| 2.2 <5 标「参考」 | PASS | `retro_report.py:542-543` |
| 2.2 commit 佐证 flag | PASS | `retro_report.py:445-461`（`_change_has_fix_commit`）+ `:544`（渲染） |
| 2.3 合成语料用例 | PASS | `sdflow-retro/scripts/tests/test_retro_report.py:668-846`（14+ fixrate 专项测试） |
| 2.3 围栏示范锚不入计 | PASS | `test_retro_report.py:729` (`test_fixrate_fenced_sample_anchor_not_counted`) |
| 2.3 fix-status 变体进未知桶 | PASS | `test_retro_report.py:704` + `:712`（disposal 信号歧义） |
| 2.3 自由文本关键词不构成归属 | PASS | `test_retro_report.py:719` (`test_fixrate_free_text_keyword_not_bounded_no_attribution`) |
| 2.3 真仓再生冒烟 | PASS | `openspec/retro/report.md:262`（聚合④段在场） |
| 5.3 sdflow-retro SKILL.md 补说明 | PASS | `sdflow-retro/SKILL.md:215-217` |

### R-TS1/TS2/TS3: token 快照采集

| 需求点 | 判定 | 证据锚 |
|---|---|---|
| 3.1 `token_snapshot.py` 新增 + 4 行 reconfigure 前导 | PASS | `sdflow-init/assets/hack/token_snapshot.py:27-29` |
| 3.1 transcript 定位序（session-id → mtime → no-transcript） | PASS | `token_snapshot.py:90-105`（`_locate_transcript`） |
| 3.1 session-id 文法校验 | PASS | `token_snapshot.py:81-87`（`_valid_session_id`：basename + UUID 字符集） |
| 3.1 usage 四计数累加 + 非负整数校验 | PASS | `token_snapshot.py:153-194`（`_accumulate_usage`）+ `:145-150`（`_non_negative_int`） |
| 3.1 parse-error 降级 | PASS | `token_snapshot.py:240` |
| 3.1 change 目录由分支名解析 | PASS | `token_snapshot.py:122-142`（`_resolve_change_dir`） |
| 3.1 v1 行 schema + 字段封闭 | PASS | `token_snapshot.py:197-210`（`_build_line`） |
| 3.1 O_APPEND 单次写 | PASS | `token_snapshot.py:213-220`（`_append_line`） |
| 3.1 内部自设执行超时 | PASS | `token_snapshot.py:41-73`（SIGALRM 10s）+ `:256-257`（`_Timeout` 捕获） |
| 3.1 全程 try/except 到降级行 | PASS | `token_snapshot.py:254-266` |
| 3.2 checkpoint-commit.sh 接线（gate 后、add 前） | PASS | `sdflow-init/assets/hack/checkpoint-commit.sh:47`（`python3 ~/.sdflow/hack/token_snapshot.py --step "$step" || true`，位于 `git status --porcelain` 判空之后、`git add -A` 之前） |
| 3.3 正常采集入同 commit 测试 | PASS | `hack/tests/test_token_snapshot.py:139` (`test_normal_collection_lands_in_same_commit`) |
| 3.3 mtime 回退测试 | PASS | `test_token_snapshot.py:174` |
| 3.3 无 transcript 写 no-transcript 测试 | PASS | `test_token_snapshot.py:200` |
| 3.3 helper 缺席 checkpoint 照常 | PASS | `test_token_snapshot.py:221` |
| 3.3 helper 崩溃 checkpoint 照常 | PASS | `test_token_snapshot.py:233` |
| 3.3 无 change 落点零写入 | PASS | `test_token_snapshot.py:247` + `:262` |
| 3.3 连续 checkpoint 只追加且累计单调不减 | PASS | `test_token_snapshot.py:277` |
| 3.3 干净树 + helper 在场仍 no-op | PASS | `test_token_snapshot.py:314` (`test_clean_tree_with_helper_present_is_still_noop`) |
| 3.3 canary transcript 不泄漏 | PASS | `test_token_snapshot.py:335` (`test_canary_content_does_not_leak_into_output_surface`) |
| 3.3 malformed JSON 降级 parse-error | PASS | `test_token_snapshot.py:385` |
| 3.3 负数 usage 降级 parse-error | PASS | `test_token_snapshot.py:409` |
| 3.3 路径穿越 session-id 拒绝 | PASS | `test_token_snapshot.py:428` |
| 3.4 dogfood 真实 checkpoint 产出 anchor=true 行 | PASS | `openspec/changes/implement-workflow-optimization-2026-08-p1/token-log.jsonl:1`（8 行 anchor=true 真实数据，session=`9f4636c0-...`） |

### R-WR2: per-change token 维 join

| 需求点 | 判定 | 证据锚 |
|---|---|---|
| 4.1 读 token-log.jsonl + 全局 session 分组 | PASS | `retro_report.py:716-757`（`compute_token_deltas`） |
| 4.1 跨 change 同 session 差分不双计数 | PASS | `retro_report.py:744-756`（排序后天然相邻差分）+ `test_retro_report.py:996` (`test_compute_token_deltas_cross_change_session_no_double_count`) |
| 4.1 全局首行全额计入 | PASS | `retro_report.py:750-751` |
| 4.1 anchor=false 不入计数 | PASS | `retro_report.py:666`（`_parse_token_log_line` 过滤 anchor!=true）+ `test_retro_report.py:1020` |
| 4.1 无法解析行逐行跳过不中断 | PASS | `retro_report.py:660-663`（try/except → None）+ `test_retro_report.py:964` |
| 4.2 四计数紧凑串（out/in/cc/cr） | PASS | `retro_report.py:775-780`（`format_tokens_cell`） |
| 4.2 MUST NOT 合成总分 | PASS | `retro_report.py:776` 注释 + 渲染分列输出 |
| 4.2 无锚显「—」 | PASS | `retro_report.py:778` + `test_retro_report.py:1098` |
| 4.2 累计口径脚注 | PASS | `retro_report.py:760-761`（`_TOKEN_FOOTNOTE`）+ `:964`（渲染） |
| 4.3 多 session 测试 | PASS | `test_retro_report.py:1043` (`test_compute_token_deltas_multiple_sessions_independent`) |
| 4.3 跨 change 不双计数测试 | PASS | `test_retro_report.py:996` |
| 4.3 降级行测试 | PASS | `test_retro_report.py:1020` |
| 4.3 缺文件测试 | PASS | `test_retro_report.py:1035` |
| 4.3 含损坏行不崩测试 | PASS | `test_retro_report.py:964` |
| 4.3 全仓再生冒烟 | PASS | `openspec/retro/report.md:31`（tokens 列在场）+ `test_retro_report.py:1113` + `:1123` |

### 收尾任务

| 需求点 | 判定 | 证据锚 |
|---|---|---|
| 5.1 全仓 pytest 绿 | PASS | `impl-reports/task6-verify.md`（2513 passed, 10 skipped @ SHA `6f46320c`）；实现期结束时聚合套件通过 |
| 5.1 report.md 再生提交 | PASS | `impl-reports/task5-integration.md`（commit `9297e50`） |
| 5.2 roadmap task-log.md 追加 1.B 交付记录 | PASS | `openspec/roadmaps/workflow-optimization-2026-08/task-log.md:58`（「阶段 1 / 任务 1.B」段） |
| 5.2 CONTEXT.md 实修率词条未确认 MUST NOT 写入 | PASS | `impl-reports/task5-integration.md`（§4 明确记录「未写入」） |
| 5.3 SKILL.md 文档面同步 | PASS | 见 R-IS1 和 R-WR1 各自 SKILL.md 段 |

## 实现期聚合覆盖（tickets 轨）

- `openspec/config.yaml` 确认 `impl-pipeline: tickets`（:64）。
- 聚合验证 ticket = task6-verify.md（R-ID 覆盖全部）。
- 证据 schema：单元层 `/usr/bin/python3 -m pytest` 退出码 0，2513 passed, 10 skipped。集成/e2e 层按仓内约定记「未覆盖」+ 判定依据（仓内无独立集成/e2e 测试基础设施）。
- 单元测试 SHA（`6f46320c`）是测试执行时的 HEAD；后续 checkpoint 提交（文档同步、task-log 追加等）不含生产代码变更。

## 缺口清单

无核心功能缺失。

### Minor 备注

1. **聚合验证 SHA 与当前 HEAD 不一致**：task6-verify.md 记录的测试 SHA 是 `6f46320c`，当前 HEAD 是 `a4824f48`。差异是后续 checkpoint 提交（spec-review 回写、设计门 frontmatter 等），不含生产代码或测试变更。判 PASS——不构成核心功能缺口。

## 结论

PASS
