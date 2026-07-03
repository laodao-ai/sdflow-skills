# verify-report — issues-pool-batch-mgmt（Phase B）

日期：2026-07-03
change：`issues-pool-batch-mgmt`

## 结论：PASS

方法：Do-Not-Trust cold start——不采信 `code-review-report.md`/`spec-review-report.md` 的结论文字，
逐条需求重新在代码 + 测试里找可机验证据锚点；`python3 -m pytest buglist-recorder/tests/
todolist-recorder/tests/ issues-recorder/tests/ -q` 实测重跑，**160 passed**（非转述）。

## 逐需求核对表

### Requirement 1：债务池统一为 issues 结构且 INDEX 只生成

| 需求 | 代码出处(文件:行/测试) | 状态 |
|---|---|---|
| 目录统一 `openspec/issues/{buglist,todolist}/` | `buglist-recorder/scripts/buglist.py:171-172`（`buglists_dir`）、`todolist-recorder/scripts/todolist.py:164-165`（`todolists_dir`） | ✅ |
| item 三维度（源/批次/status）分记 | `buglist.py:215`（表头 8 列含「批次」独立列）、`cmd_scan` `buglist.py:563-570` 输出 `change`/`batch`/`status` 三个独立字段；测试 `test_add_writes_批次_column_at_end`（buglist_test.py:167, todolist_test.py:208） | ✅ |
| `INDEX.md` 只由 `reindex` 从 dated 文件重建生成、禁手改 | `issues.py:200`（`INDEX_BANNER = "<!-- GENERATED ... DO NOT EDIT -->"`）、`generate_index_md`（`issues.py:228-288`）docstring 明示"禁读旧 INDEX（D3）——只以 items 为唯一输入源，不看磁盘上已有内容"；测试 `test_index_first_line_is_generated_banner`（issues_test.py:305）+ `test_reindex_is_idempotent_byte_identical_on_rerun`（issues_test.py:362） | ✅ |
| reindex 摊清 open×批次 + 标出已闭合项 | `generate_index_md` 分组逻辑 `issues.py:240-286`；测试 `test_open_items_grouped_by_batch_and_unbatched_group_separate`（issues_test.py:315）、`test_terminal_items_excluded_from_open_board_but_counted_in_closed_summary`（issues_test.py:337） | ✅ |
| status 回归干净、批次不塞入 status 字面量 | `buglist.py` `STATUS_CODES`（56 行）与批次列（215/382 行）物理分离，`cmd_set_status`/`cmd_triage` 从不写批次值进 status 单元格 | ✅ |
| 源change（provenance）不可变 | `cmd_triage`（`buglist.py:477-527`）只写 `cells[7]`（批次列）和 `cells[4]`（状态列），从不碰 `cells[6]`（关联Change列） | ✅ |

### Requirement 2：批次注册表与 reindex 被动同步状态

| 需求 | 代码出处(文件:行/测试) | 状态 |
|---|---|---|
| `issues/batches.md` 注册表，`PLANNED→IN_PROGRESS→DONE` | `issues.py:339`（`BATCH_STATUSES`）、`cmd_batch_add`/`cmd_batch_set_status`（`issues.py:574-644`） | ✅ |
| sweep 以 `源==本change` 为界只诊本 change 新增 OPEN 项，孤儿不归本次 sweep | `opsx-done/SKILL.md:118-121`（显式 `--change {change_name}`）+ `:141`（"孤儿项…不归本 sweep 管"） | ✅（流程文档，非脚本；`--change` 过滤本身有 `buglist.py` `cmd_scan` `args.change` 分支 `buglist.py:574-575` 实测） |
| reindex 拿 item 池当 ground truth，成员全部进各自终态集（bug FIXED/WONTFIX，todo DONE/WONTDO）→ 批次判 DONE | `issues.py:204-207`（`TERMINAL_STATUSES`）、`sync_batches_md` D1 判据 `issues.py:568`（`is_complete = len(members) >= 1 and all(_is_terminal(it) for it in members)`）；测试 `test_all_members_fixed_or_done_marks_batch_done`（issues_test.py:678）+ `test_all_members_terminal_via_wont_variants_marks_done`（issues_test.py:699） | ✅ |
| 0 成员批次 MUST 保持 PLANNED，防 vacuous-truth 假 DONE | `issues.py:568` 的 `len(members) >= 1` 显式排除 0 成员；测试 `test_zero_member_batch_not_marked_done`（issues_test.py:719） | ✅ |
| 状态与成员不一致只标出纠正，不越权改人写状态值 | `_sync_one_entry`（`issues.py:453-516`）：`is_complete` 为假时"绝不改这个值"，只追加 `⚠️ 不一致` 警告；测试 `test_appends_warning_but_keeps_human_done_value_unchanged`（issues_test.py:736） | ✅ |
| orphan 批次 tag 报警不静默生成 ghost | `sync_batches_md`（`issues.py:550-559`）stderr 报警且不新建条目；测试 `test_orphan_batch_tag_warns_on_stderr_without_creating_ghost_entry`（issues_test.py:754） | ✅ |
| 不做逾期主动催办 | `sync_batches_md` docstring 与 `issues.py` 全文搜索无"逾期"/"催办"计算逻辑（只有 open×批次被动摊清）；spec.md:5 明确"早前旧稿标题曾含逾期主动催办，已按 Q5 删除" | ✅ |
| sweep 显式传 `--change`，不靠 `detect_change` 猜 | `opsx-done/SKILL.md:118-121`（`scan --status OPEN --change {change_name}` 命令示例，标注〔D4〕） | ✅ |
| reindex 接入 sweep 末尾 | `opsx-done/SKILL.md:135-137`（"末尾跑 reindex（D3）——必须在上面 triage/batch add 之后跑"） | ✅ |
| 跨池 ID 撞号检测（D9 防护网，B/T 前缀互斥为规范条款） | `cross_pool_id_conflicts`（`issues.py:153-165`）+ `read_pool` 抛 `CrossPoolIDConflict`（`issues.py:184-191`）；`buglist-recorder/SKILL.md:212-218` 显式规范条款；测试 `test_reindex_raises_on_cross_pool_id_conflict`（issues_test.py:376） | ✅ |
| 原子写 | `atomic_write`（`issues.py:68-94`，temp+os.replace，权限对齐） | ✅ |

## 交叉证据（重跑，非转述）

```
$ python3 -m pytest buglist-recorder/tests/ todolist-recorder/tests/ issues-recorder/tests/ -q
160 passed in 7.47s
```

- `issues-recorder/SKILL.md` 实际存在（108 行，非 stub）——code-review-report 提到的 Task 13 Critical
  修复（setup.sh 装/下游 sweep 找得到 issues.py）经查确已落地，不是残留承诺。
- `openspec/workflow/workflow.md:52` + `opsx-project-init/assets/workflow/workflow.md:52-53,75` 均已
  引用 issues sweep 子步（Task 4.3）。
- `workflow/tools/engine.js` grep 无 `buglists`/`todolists`/`issues` 硬编码路径，佐证 Task 5.1 "no-op"
  结论属实、非漏做。
- Defer 项 T1–T5 已真实落在 `openspec/issues/todolist/2026-07-todolist.md`（非承诺占位），状态 OPEN、
  来源 `issues-pool-batch-mgmt`，与 code-review-report 的 Defer 表一一对应。
- 本仓当前无 `openspec/buglists`/`openspec/todolists` 旧目录（`find openspec -iname "buglist*" -o
  -iname "todolist*"` 只命中新路径），与 design.md 的迁移前提陈述一致；dual-read 逻辑面向下游消费仓
  （OQ3），本仓不构成回归风险。
- `openspec/changes/issues-pool-batch-mgmt/openspec/issues/{INDEX.md,batches.md}` 尚未生成——**符合
  预期**：本 change 自身的 sweep/reindex 步在 opsx-done archive 阶段才跑（verify 早于 archive），
  tasks.md 6.2 已相应留空未勾并注明"opsx-done archive 步做"。

## 缺口清单

无 Critical/Important 缺口。以下均为已知 Minor、不影响 PASS 判定：

- **T1**（可观测性）：`reindex` 未回显子进程 `scan` 的 `problems` 到 stderr——独立跑 `reindex` 时看不到
  表↔块不一致提示（需另跑 `scan` 才可见）。已记入 todolist，非本 change 核心功能缺失。
- **T2**（代码质量，pre-existing 系统性问题）：字段含 `｜` 会破坏 markdown 表解析，未做转义/拒绝。
  跨越 Phase A 遗留代码路径，非本 change 引入的新缺陷。
- **T3–T5**（代码质量/功能增强）：终态集跨脚本一致性守卫测试缺失、`batch add --if-exists`/`rename`
  后自动 reindex 未做、部分分支测试与定位逻辑重复未消除——均为增强项，不影响 spec 2 条 Requirement
  的核心行为正确性。

tasks.md `6.2`（spec delta 归档并入 `openspec/specs/spec-workflow/`）按设计属于 opsx-done archive
步骤职责，非实现阶段缺口。

## 结论

PASS——spec-workflow delta 的 2 条 ADDED Requirement（债务池统一 issues 结构且 INDEX 只生成；批次注册表
与 reindex 被动同步状态）及其全部 6 条 Scenario，逐条找到代码文件:行 + 通过测试的双重可机验证锚点；
160 个测试实测重跑真绿；已知 Minor 缺口（T1-T5）均已按约定落在 todolist 池，未被静默丢弃。
