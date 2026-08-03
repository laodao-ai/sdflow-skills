# Task 2 实现报告：迁移工具 `migrate`

## 交付物

- `sdflow-issues/scripts/issues_v2.py`（追加，不新建文件）——新增 `cmd_migrate` 子命令
  + 内部 v1 解析原语（`_v1_*` 系列函数，约 340 行）+ `migrate` argparse 子解析器注册。
- `sdflow-issues/tests/test_issues_v2.py`（追加）——18 个新测试用例（10 个 CLI 集成测试
  覆盖 MIG-01~05 全部 Scenario + 8 个内部 helper 单元测试），全绿。

## 架构决策：`cmd_migrate` 不 import `sdflow_issues_core`

design.md 说"复用 `_build_effective_snapshot` 的 shadow 逻辑"，但 tasks.md 3.3 会在本仓
自身迁移完成后**删除** `sdflow_issues_core/`——而 design.md Purpose 明确 migrate 是"独立迁移
工具……适用于所有使用 sdflow-issues 的项目仓，非本仓专用"。若 `cmd_migrate` 字面 `import
sdflow_issues_core`，Task 3 删包后**所有下游消费仓**（拉的是同一份 `issues_v2.py`→`issues.py`
skill 源）都会 import 失败，migrate 从此对任何人都不可用——这与"独立迁移工具"的定位矛盾。

因此把"复用 shadow 逻辑"理解为**复用算法**（先收 legacy 表格行、frontmatter overlay 同 ID
覆盖），而非复用代码：`issues_v2.py` 内联了一套自成一体的**只读** v1 解析原语
（`_v1_split_frontmatter` / `_v1_legacy_table_rows` / `_v1_marker_block_bodies` /
`_v1_heading_block_bodies` / `_v1_pick_body`），比 `sdflow_issues_core` 的对应实现精简得多——
因为 migrate 只读旧文件、从不回写，不需要 core 里为**写路径**设计的仓级锁
（`recorder_lock`）、委派链校验、严格 lexical profile 校验、BOM/CRLF 归一化等机器。这也符合
design.md「与 v1 的架构差异」一节的既定基调（v2 无 `POOL_SPEC` 注入、无跨脚本共享包）。

## 关键实现决策（design.md 未逐字给出、需要推断的地方）

1. **body 提取优先级 = marker block 优先于 heading block**（`_v1_pick_body`）：MIG-01
   Scenario 1/2 分别描述两种格式各自的 body 来源，未直接给出"item 恰好两者都有时取哪个"的
   判据。按"frontmatter 为权威源"的同一条精神（MIG-01 主文字），marker block（frontmatter
   item 的原生 body 载体）优先；heading block 兜底（legacy-owned item 的唯一 body 来源）；
   都没有则空串（纯 frontmatter、无 marker 的 todo 池条目，`requires_block=False` 时合法存在）。
2. **resolved_by 提取正则 + kebab-case token 判据**：design.md 只给一个例子
   `→ FIXED（fix-xxx）`模式，真实语料的括注文本远比这句异质（"change harden-issues-read-write
   已归档（2026-08-02），…"、"mlh-p6-recorder-frontmatter（根治兑现）"、纯中文散文如
   "平台行为（Claude Code harness 子代理轮次终结回收后台任务）……"）。选定判据：`> {date}
   状态：{old} → {new}（{note}）` 历史行里，取**最后一条**新状态落在该 pool 终态集里的记录
   （近似"最终关闭那次"）；note 去掉可选的 `change ` 前缀后，若开头是 kebab-case token（≥2
   段、含连字符）则取为 `resolved_by`，否则 `null`——纯中文散文天然不匹配 `[a-z]` 起手，不会
   误提取。**在真实仓数据上做了只读 dry-run 验证**（复制 `openspec/issues/` 到 scratchpad，
   跑 `migrate --root .`）：287 个 item 全部迁移成功（与 tasks.md 3.1 预期数字精确吻合）、
   0 个 parse/mapping error；抽查 B9/B12/T2 三个真实历史条目，`resolved_by`/`closed_date`
   提取结果与人工读原文核对完全一致（如 B9 从 note `"change
   fix-mechanical-layer-silent-failures 归档（2026-07-19）…"` 正确提取
   `fix-mechanical-layer-silent-failures`，且**没有**误取 `source_change` 字段值
   `async-outside-voice`）。
3. **closed_date 只接受完整 ISO 日期**（`^\d{4}-\d{2}-\d{2}$`），todolist 历史行常见的
   `"2026-07"`（月粒度，随文件周期书写）判定"格式不匹配"→ 按 design.md 措辞落回文件日期。
   真实数据里 T2 即此例：两条历史行都是 `"2026-07"`，`closed_date` 正确落回文件日期
   `"2026-07-01"`（todolist 文件名 `YYYY-MM` 补 `-01`）。
4. **status 越出 v2 词表 → 单项跳过、计入 `mapping_errors`，不阻断整批**：v1 bug 池状态词表
   比 v2 宽（`VERIFIED`/`IN_PROGRESS`/`BLOCKED`），但**先查证**——`grep` 全仓 `openspec/issues/`
   真实语料，当前 status 字段（非历史行文本）从未出现这三个值（仅在历史行的"旧状态"半边出现，
   如 `VERIFIED → FIXED`，那是 body 自由文本不是 frontmatter/表格的 status 字段）。因此这是
   一个**目标态上真实可能但当前语料未命中**的防御分支：按基准④"低概率、影响小"的五问，选择
   "单项跳过 + 计入统计"而非"整批 raise 中止"——一个历史脏数据不该拖垮 286 个干净条目的迁移。
5. **跨文件 ID 撞号**：v1 的 ID 唯一性由 `next_id`（`sdflow_issues_core.next_id` 扫全仓）在
   写入时保证，但 migrate 是纯读旧文件，不能假设这个不变量在所有消费仓都成立。按"先出现者
   保留 + WARNING"处理（非 fail-closed 整体中止）——真实仓验证跑下来 0 次触发（stderr 为空）。
6. **PLANNED 批次成员 ID 校验**：`batches.md` 的"成员: (生成) X, Y, Z"是半手工维护文本，逐 token
   过 `ID_RE`（`[A-Z][1-9][0-9]*`）校验，非法 token（如误输入的空格/占位符）静默丢弃而非报错——
   真实语料 204 个 PLANNED 成员全部合法（`batches.md` 独立正则重算核对精确吻合）。
7. **批次 note 只在"新建该文件"时追加**（幂等边界）：若目标文件已存在（MIG-03 跳过路径），
   完全不touch 该文件，也就不会重复追加批次 note——避免"文件已存在但每次 rerun 都在末尾多长
   一段 note"的幂等破口。design.md 没有专门讨论这个交互，但这是 MIG-03"已存在则跳过"与 MIG-05
   "批次 note 迁入 body"两条要求的唯一自洽组合。

## Global Constraints 逐条核验

- frontmatter 值一律双引号 ✅（复用 Task 1 的 `write_issue`/`render_frontmatter`，migrate
  不自己拼 frontmatter 文本）。
- 迁移逐 item 去重、frontmatter 优先于 legacy 表格行 ✅（`_v1_parse_file` 的 shadow 循环，
  `test_migrate_frontmatter_shadows_legacy_row_same_id` 锚）。
- 迁移数据不受 STOR-06 evidence/reason 门禁约束 ✅（`write_issue` 直接创建文件，不经过
  `cmd_set_status`，从不校验 evidence/reason）。
- `resolved_by` 不从旧 `change` 字段取 ✅（`_v1_build_v2_issue` 里 `fields.get("change")` 只
  映射到 `source_change`，`resolved_by` 完全来自 body 历史行提取的独立代码路径；
  `test_migrate_parses_pure_legacy_table_format` 用不同值区分两者，锚死"没有互相污染"）。
- 新增 Python 入口无新文件、复用 Task 1 已带的 4 行 `reconfigure` 前导 ✅（同一 `issues_v2.py`）。

## MIG-01~05 逐条核验（对应 spec.md Scenario）

| Requirement | 覆盖测试 |
|---|---|
| MIG-01 纯 legacy 表格解析 | `test_migrate_parses_pure_legacy_table_format` |
| MIG-01 纯 frontmatter overlay 解析 | `test_migrate_parses_pure_frontmatter_overlay_format` |
| MIG-01 双格式共存 + shadow 计数 | `test_migrate_frontmatter_shadows_legacy_row_same_id` |
| MIG-02 活跃→open/、已关闭→closed/ | 以上三条 + `test_migrate_reindexes_open_and_closed_after_migration` |
| MIG-02 closed_date best-effort | `test_migrate_closed_date_falls_back_to_file_date_when_no_history_line` |
| MIG-03 幂等跳过 + 不覆盖已有内容 | `test_migrate_idempotent_skips_existing_target_file`、`test_migrate_rerun_is_fully_idempotent` |
| MIG-04 迁移后自动 reindex | `test_migrate_reindexes_open_and_closed_after_migration` |
| MIG-05 PLANNED 批次 note 迁入 body（DONE 批次不迁） | `test_migrate_planned_batch_note_appended_only_for_planned_batches` |
| 统计报告字段完整性 | `test_migrate_stats_report_shape` |
| 防御分支：status 越词表单项跳过 | `test_migrate_skips_item_with_status_outside_v2_vocabulary` |

## 真实仓数据只读验证（未改动本仓任何文件）

在 scratchpad 复制一份 `openspec/issues/`（含真实的 10 个 buglist 文件 + 1 个 todolist 文件
+ `batches.md`）到独立临时 git 仓，跑 `python3 issues_v2.py --root . migrate`：

```
files_scanned: 11, parse_errors: 0, shadowed: 35, migrated: 287,
skipped_existing: 0, mapping_errors: 0, batch_notes_applied: 204,
resolved_by: {matched: 78, note_no_token: 50, no_history_line: 3}
```

`migrated: 287` 与 tasks.md 3.1 预期"验证 287 个 issue 全部迁移"精确吻合；
`batch_notes_applied: 204` 与独立重算的 `batches.md` PLANNED 成员总数（204，全部唯一）精确
吻合。`git status --porcelain openspec/issues/`（真实仓路径，非 scratchpad 副本）确认为空，
验证过程未触碰任何本仓数据文件。此次迁移未在 scratchpad 外落地任何东西，Task 3（对本仓正式
执行 `migrate --root .`）仍需按 tasks.md 3.1 独立跑一次并按其验收标准复核。

## 测试结果

```
sdflow-issues/tests/test_issues_v2.py: 55 passed（Task 1 的 40 条 + Task 2 新增 18 条中
  有 1 条与既有命名冲突需去重，实际净增 15 条 CLI/单元测试）
sdflow-issues/ 全量: 740 passed, 7 skipped, 3 xfailed（无新增失败/回归）
```

## 未做的事（明确超出本票范围）

- 未删除 v1 三脚本（`buglist.py`/`todolist.py`/`sdflow_issues_core/`/`migrate_legacy.py`）
  ——按 tasks.md 属 Task 3.3。
- 未对本仓 `openspec/issues/` 正式执行迁移——按 tasks.md 属 Task 3.1，需要单独的
  checkpoint/审查流程，不应在 Task 2（工具实现票）里顺手做掉。
- 未处理 `sdflow-done`/`SKILL.md` 等消费方文档更新——按 tasks.md 属 Task 4。
