# impl-report — Task 2: 三层共享逻辑单一物理源 + 三薄入口迁入 sdflow-issues/scripts/

**R-ID:** SC-R2, SC-R3, DG-M1 | **状态:** DONE

## 1. 做了什么（总览）

- **`sdflow_issues_core`（T1 建的唯一命名 package）** 从只含 POOL_SPEC schema，扩为承载全部
  THREE_WAY(37) + TWO_WAY(24) 共享 helper + pool-参数化数据 helper + cmd_* 共享 skeleton +
  `PoolStrategy` 策略钩子（Q2 残余）——**唯一物理编辑源**。
- **`sdflow-buglist/scripts/buglist.py` / `sdflow-todolist/scripts/todolist.py`** 删除；
  在 `sdflow-issues/scripts/` **新建**两个薄入口 `buglist.py`/`todolist.py`（解析 args →
  注入各自 `POOL_SPEC`+`PoolStrategy` → `from sdflow_issues_core import` → `run_cli`）。
- **`sdflow-issues/scripts/issues.py`** 就地改薄：共享 helper 全部 `from sdflow_issues_core import`；
  保留 issues 独占的跨池 reindex/batch/sweep/rename；sibling-spawn 常量改同目录；承重注释重写；
  委派状态经 core。
- **测试**：`sdflow-buglist/tests/` + `sdflow-todolist/tests/` 9 个文件迁入 `sdflow-issues/tests/`；
  `test_mirror_consistency.py` **删除**（单一物理源使三向/两向 AST 镜像守无对象，= T1 基线标注的 7 个
  intended-delete node）。
- **全套件绿**：仓根 `/usr/bin/python3 -m pytest -q` → **`2100 passed, 8 skipped, 3 xfailed`，exit 0**
  （T1 基线 2098 passed；净 +2，扣掉 mirror 7 node、加上 patch_discipline 参数化随迁入测试文件增多的
  ~9 param + 少量新守）。

## 2. THREE_WAY + TWO_WAY 上移对照 roster（test_mirror_consistency.py 的名单）

**THREE_WAY(37) 全部上移 core，逐字/等价搬迁**（pool-agnostic，无 spec 依赖）：
`atomic_write`·`atomic_write_bytes`·`repo_root`·`_reject_line_unsafe`·`canonical_id`·`semantic_id_key`·
`validate_prefix`·`_lock_path`·`_read_lock_metadata`·`_lock_conflict`·`validate_recorder_participant`·
`_write_all`·`recorder_lock`·`read_repository_snapshot`·`repository_semantic_occurrences`·
`recorder_child_env`·`_frontmatter_error`·`_validate_unicode_scalar`·`_json_object_no_duplicates`·
`_validated_recorder_model`·`_id_semantic_sort`·`render_recorder_namespace`·`_legacy_semantic_id_key`·
`_split_envelope`·`_find_recorder_span`·`_parse_recorder_namespace`·`_legacy_table_region_count`·
`parse_recorder_document`·`read_recorder_document`·`split_sections`·`_legacy_table_sections`·
`parse_table_rows`·`block_ranges`·`_match_marker_line`·`marker_block_ranges`·`_legacy_item_from_row`·
`_build_effective_snapshot`。

> `_build_effective_snapshot` 是唯一含 pool 分支的 THREE_WAY helper（`if expected_pool=="bug"`），
> 见 §3 重写。`read_repository_snapshot` 的两池 glob 从 POOL_SPEC 派生（单一源）。

**TWO_WAY(24) 全部上移 core**：`detect_change`·`normalize_doc_paths`·`auto_default_doc`·`_ids_in_files`·
`_find_row_file`(+spec)·`_id_sort_key`·`validate_doc_paths`·`all_ids`(+spec)·`next_id`·`_die`·`_load_json`·
`_canonical_document`·`_render_recorder_document`·`_display_title`·`_summary_blockquote`·
`_escape_user_markers`·`_canonical_from_key`·`_find_item_document`·`_legacy_block_range`·
`_splice_body_lines`·`_reject_document_mutation`·`_preflight_target_legacy_block`·`_promotion_insertions`·
`_validated_rendered_mutation`。

**pool-differ 数据 helper（不在 roster——本就按 pool 各异）参数化为 spec**：
`buglists_dir`/`todolists_dir`→`dated_dir(root,spec)`；`legacy_*_dir`→`legacy_dir(root,spec)`；
`list_files`→`list_files(root,spec)`；`today_str`/`this_month`→`_period_str(spec,override)`；
`file_for_date`/`file_for_month`→`file_for_period(root,spec,period)`；`ensure_file`→`ensure_file(root,spec,period)`；
`id_conflicts`→`id_conflicts(root,spec)`；`all_ids`/`next_id` 前缀经 spec.default_prefix。

## 3. 消除的 pool 分支（逐处，重写为 POOL_SPEC 取值）

| 位置（原） | 原形态 | 重写 |
|---|---|---|
| `_build_effective_snapshot`（THREE_WAY） `if expected_pool=="bug":`（缺 marker/缺详细块两处） | 三元字面 pool 比较 | `if POOL_SPEC[expected_pool].requires_block:`（**新增 schema 维 `requires_block`**：bug=True/todo=False） |
| `cmd_add` `pool=="bug"` snapshot 过滤（buglist:1508 / todolist:1451） | loop 变量 == 字面 | `pool == spec.pool`（attr，非字面） |
| `cmd_add`/`set_status`/`triage` 的 `"pool":"bug"` model 打标、`_validated_rendered_mutation(...,"bug",...)`、`_find_item_document(...,"bug")` | 散布的 pool 字面 | `spec.pool` |
| `_scan_snapshot` `if pool != "bug":` | loop 过滤字面 | `if pool != spec.pool:` |
| `_scan_snapshot`/`cmd_triage` `set(STATUS_CODES) - {"FIXED","WONTFIX"}` / `- {..,"PROPOSED"}` | 内联终态字面集 | `set(spec.status_values) - set(spec.terminal_set)` / `- set(spec.terminal_set) - {"PROPOSED"}` |
| `issues.py:1365` `items_key = "bugs" if pool=="bug" else "items"` | 三元 | `POOL_SPEC[pool].scan_output_key` |
| `issues.py:900/991/1001/1056` `document["pool"]=="bug"`（rename/retag 的 requires-block 判定） | subscript == 字面 | `POOL_SPEC[document["pool"]].requires_block` |

**core 无 pool 值条件分支已核验**：`grep` 确认 core 内 `"bug"`/`"todo"` 字面只出现于
①`POOL_SPEC` 数据定义 ②`validate_pool_spec` 的封闭 schema keys 断言 `{"bug","todo"}`（AD-3 明确允许的
schema 守）③注释。`pool == spec.pool` 用 attribute（非字面），过 Task 4 AST 守。

**POOL_SPEC schema 扩维**（T1 的 10 → 12）：新增 `pool`（身份，替 model 打标/本池定位的 "bug"/"todo" 字面）
+ `requires_block`（bug 强制块 / todo 可选块，替 `if expected_pool=="bug"`）。`POOL_SPEC_FIELDS` 注册表、
两池 POOL_SPEC 值同步更新；`test_pool_spec_schema.py` 动态比对 registry==fields 仍绿（15 用例全过）。
`RECORDER_POOL_CONFIG`/`TERMINAL_STATUSES` 改为**从 POOL_SPEC 派生**（消掉三脚本各一份的常量副本）。

## 4. 策略钩子例外说明（Q2：不可数据化的控制流残余，命名 + 限定签名）

`PoolStrategy`（封闭 dataclass，**非** POOL_SPEC 的一部分、**非**任意 callable 逃生口——具名字段，
加钩子须改 schema）承载 bug↔todo **genuine 控制流分岔**；薄入口选取本池实例（`BUG_STRATEGY`/
`TODO_STRATEGY`），**core 不按 pool 值在 strategy 间选择**（选取在薄入口，过 AST 守）。逐个例外：

| 钩子 | 为何不能纯数据化 | bug/todo 各跑同一 contract |
|---|---|---|
| `build_block` | bug 详细块**恒非空**（现象/根因/修复/影响 + optional）；todo 块**可选**（视 motivation/approach/note/显式 doc 返回 `""`）——块结构与建/不建的控制流各异 | 二者 add 后 `_validated_rendered_mutation` 同一关系自检 |
| `header` | bug canonical header 用 source/date（且 `_new_bug_body` 二次 reject source）；todo 用 project/month，无二次 reject | 同一 `_canonical_document` 组装 |
| `set_status` | bug FIXED 门禁**读块内根因**（`_has_rootcause`）→ 必须先解析块再门禁；todo 无此门禁、且对 frontmatter-owned-无块项**惰性建 minimal 块**、`require_marker` 动态算 | 同一 `_find_item_document`/`_promotion_insertions`/`_render_recorder_document` |
| `triage` | 同 set_status：bug require_marker 恒 True；todo 动态（`not frontmatter_owned or 有 marker or 有 history`） | 同上 |
| `add_output` | JSON 字段/顺序各异（todo 多 `block` 键，位置在 status 后） | 同一 stdout JSON 契约 |
| `scan_sort_key`/`scan_line`/`scan_empty_msg` | bug 按 (priority,id) 排、印 priority 列；todo 按 (status,id) 排、印 type 列 | 同一 `_scan_snapshot` envelope |
| `add_required_extra`/`specific_label`/`specific_values_ordered`/`source_field`/`add_time_fmt` | 纯数据差异（bug 多必填 phenomenon、优先级 vs 类型标签、有序枚举 join、source vs project、`%H:%M` vs `%Y-%m-%d %H:%M`）——放 strategy 数据字段（有序枚举因 frozenset join 顺序不定必须随策略走） | — |
| `period_flag`/`*_help`/`scan_has_type_filter`/`description` | CLI 装配差异（`--date` vs `--month`、todo scan 独有 `--type`、help 文案） | `build_parser(spec,strat)` 同一装配 |

**cmd_add / cmd_scan / cmd_next_id / build_parser / run_cli 是共享 skeleton**（差异全经 spec+strat 注入，
无 pool 分支）；只有 set_status/triage 因控制流真分岔整函数落 strategy（**未默认整体退回多写**——skeleton
+ 子 helper 全共享，仅门禁/惰性建块的编排各一份）。

## 5. 三薄入口 sys.path 处理 + sibling-spawn 常量改动

- 三入口顶部均 `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` 后 `from sdflow_issues_core import`
  ——令多数用 `importlib.spec_from_file_location`（不设 sys.path）按文件加载入口的测试仍能解 package import（AD-1/R4）。
- **leaf API 薄绑定**：`next_id`/`list_files`/`all_ids`/`id_conflicts`/`today_str`(bug)/`this_month`(todo)/`cmd_scan`
  在薄入口绑定本池 spec 后暴露 root-only 签名（tests 直接 root-only 调用）；`STATUS_CODES`/`PRIORITIES`/`TYPE_TAGS`/
  `DEFAULT_PREFIX` 为 POOL_SPEC 的列表/有序投影（兼容测试按名访问）。
- **issues.py sibling-spawn（AD-2）**：`SKILLS_ROOT`/上两级 join 删除；`BUGLIST_SCRIPT`/`TODOLIST_SCRIPT` =
  `os.path.join(SCRIPT_DIR, "buglist.py"/"todolist.py")`（同目录）；`:59-65` 承重注释重写去掉「安装后 sibling
  skill 目录/上两级」前提（DOC-1：正文即最终态）。**reindex/sweep 实测仍正确 spawn 子进程**（cross-pool
  INDEX 重建、sweep scan→triage 链路均绿）。
- **委派状态单一源**：`_ACTIVE_RECORDER_TOKEN`/`_ACTIVE_RECORDER_CHAIN` + `recorder_child_env` 上移 core；
  issues.main 设 `_core._ACTIVE_RECORDER_TOKEN`，`_scan_pool` 读 `_core._ACTIVE_RECORDER_TOKEN`。

## 6. 测试迁移清单

**迁入 sdflow-issues/tests/（git mv）**：test_buglist.py·test_todolist.py·test_frontmatter_dual_reader.py·
test_repo_root_identity_buglist.py·test_repo_root_identity_todolist.py·test_task2_semantic_lock.py·
test_task2_windows_local_fs_smoke.py·test_task3_frontmatter_writer.py·test_task5_delivery_contract.py。
**删除**：test_mirror_consistency.py（7 node，T1 基线 intended-delete）。

**改动分两类**：
1. **纯路径/import（大多数）**：`sdflow-buglist/scripts/buglist.py`→`sdflow-issues/scripts/buglist.py`（同 todolist）；
   `parent.parent/"scripts"` 相对路径迁移后自然指向 sdflow-issues/scripts（无改）；pre-existing 的
   test_issues.py/test_task4 的 `"sdflow-buglist"/"scripts"` 常量改 `"sdflow-issues"`。
2. **单一源化的必要接线改（逐条，断言意图不变）**——这些是「共享逻辑移入 core」的直接连带，非放宽守护：
   - **collaborator monkeypatch 改指 core**：薄入口 `from core import *` re-export 的名与 core 内部调用是**两个**绑定，
     patch 入口名不影响 core 内部调用 → 改 patch `module._core.X`：`_ACTIVE_RECORDER_TOKEN/CHAIN`
     （semantic_lock/windows_smoke/delivery_contract）、`parse_recorder_document`（dual_reader real_scan）、
     `atomic_write_bytes`（semantic_lock cli_writer_fault）。
   - **source/AST 守改指 core（逻辑移居 core）**：repo_root 单点解析/诊断/argparse 默认（repo_root_identity ×3 文件，
     `owners==["main"]`→`["run_cli"]`；issues 保留自身 main 守、仅诊断指 core）；dated-writer call-graph（task3）；
     helper golden-behavior（task3 → `module._core`）；legacy-table read-promotion + human-scan 字串（task5 → core 源）。
   - **单一源守替 3-copy 一致性守**（同 mirror 退役同理）：终态字面一致性 ×4（test_issues → 断
     `core.POOL_SPEC[pool].terminal_set == issues.TERMINAL_STATUSES[pool]` + core 源用 `spec.terminal_set` 派生）。
   - **premise 翻转（adr/0027 反转 D4 自包含前提）**：self-contained 守放行**唯一**共享源 `sdflow_issues_core`
     import（仍禁 yaml 与其它跨 skill import）。
   - **allowlist 扩容**：patch_discipline `INTENTIONAL_WHOLESALE_PATCHES` 补 buglist/todolist repo_root_identity
     的 4 处 whole-module subprocess patch（镜像既有 issues 条目——它们随迁入进了被扫描目录）。

## 7. 全套件实际输出

```
/usr/bin/python3 -m pytest -q  （仓根，pytest 8.4.2）
2100 passed, 8 skipped, 3 xfailed in 146.80s   exit 0
```
- **行为等价直证**：新旧脚本对同一 add/set-status/triage 命令序列产出 **byte-identical** openspec 树
  （bug 与 todo 各一轮，`diff -r` 无差异，见实现期 smoke）。
- CLI 全 subcommand 触达：add / scan --json / set-status / triage / reindex / batch add|set-status|rename|lint /
  next-id / sweep 均实测通过（reindex 跨池 INDEX 重建、cross-pool next-id `T2` 正确）。

## 8. 留给 Task 5 的 handoff（下游托管引用——本票未动）

以下引用旧目录名/脚本路径/slash，属 AD-5 下游同步（Task 5），本票 fail-closed 未改，全仓 pytest 未照到
（都是文档/CI/bundle 面）：`README.md`·`CLAUDE.md`/`AGENTS.md`·`sdflow-init/assets/{snippets,workflow}`·
`sdflow-done/SKILL.md`·`ship_gate.py`·`sdflow-retro`/`sdflow-implement`/`sdflow-init` SKILL.md slash prose·
`.github/workflows/windows-recorder-smoke.yml`·`sdflow-init/tests/test_setup_sdflow.py`·主 spec 两 delta·
`hack/tests/test_sync_principles.py` 计数 17→15·机械引用守卫 test。

**⚠️ 注意**：`test_task5_delivery_contract.py::test_upgraded_install_known_consumer_smoke` 与
`test_setup_sdflow.py` 等**安装/交付契约**测试目前仍绿（它们读运行 checkout 的 `~/.claude/skills` 或断言
install 面，未被本票的源码移动照到），但 setup.sh 尚未跑（新增/删 skill 目录是 Task 3）——Task 3 删
`sdflow-buglist`/`sdflow-todolist` 目录 + 跑 setup.sh 后，`test_setup_sdflow.py` 的建链断言会转红，须由
Task 5.6 改断言。本票范畴内它们绿。

## 9. 本票未做（分工边界，非缺陷）

- **不删 `sdflow-buglist/`/`sdflow-todolist/` 目录**（Task 3）——只迁 scripts+tests，两目录留 SKILL.md 等
  （scripts/ 与 tests/ 目录现为空）。
- **不造 determinism-guards NEW 守**（AST 级无 pool 分支守 / thinness 同一性守 / golden 降级 / schema 守
  的 Task 4 部分）——那是 Task 4。本票只删旧镜像守 + 达成单一源 + CLI 等价。
- **未记 AD-6/AD-7 defer 的 todo 占位**（tasks.md 7.1/7.2）——非本票 R-ID。

## Concerns

无阻断。一个需评审留意的边界：**§6.2 的测试接线改超出「纯路径/import」**——因为「共享逻辑移入 core」
在结构上使一批 source-inspection / collaborator-monkeypatch / 3-copy-一致性守的**被守对象**变了位置或被
单一源消解。我一律选择**保留守护意图、改指单一源**（而非删守或放宽），并逐条在 §6.2 标注理由，供双轴审
核验未削弱守护力（尤其 self-contained 的 premise 翻转、终态一致性的单一源改写）。
