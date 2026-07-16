## MODIFIED Requirements

<!-- REQ: DG-RI-1 -->
### Requirement: recorder 镜像 helper 由「剥 docstring 后 AST 等价」一致性测试守护

三份 recorder（`buglist.py`/`todolist.py`/`issues.py`）为保持 skill 自包含而各自内联的真共享 helper MUST 由剥函数 docstring 后 `ast.dump` 相等的断言守护行为不漂移。frontmatter 目标态的三向组 SHALL 至少包含 `atomic_write`、`atomic_write_bytes`、`repo_root`、`recorder_lock`、`_canonical_id_key`、`_reject_line_unsafe`、`read_recorder_document`、`parse_recorder_document`、`render_recorder_namespace`；buglist↔todolist 两向组 SHALL 包含其共享的 change/doc/block/legacy/ID/定位 helpers，包括 `detect_change`、`normalize_doc_paths`、`auto_default_doc`、`split_sections`、`parse_table_rows`、`block_ranges`、`_find_item_file`、`_id_sort_key`、`validate_doc_paths`、`all_ids`、`next_id`、`_die`、`_load_json`。实现若为满足已批准 design 增减或重命名共享 helper，MUST 在同一提交中更新显式 roster 与本 requirement，MUST NOT 以动态发现所有同名函数替代人工审定的边界。

`_reject_cell_unsafe` 不再属于目标态 roster；`split_sections`/`parse_table_rows` 只作为 buglist↔todolist 的 legacy read 半场保留，MUST NOT 被新写路径调用。契约继续锁**行为等价层而非字面层**：docstring/注释按 recorder 语境分化合法，逻辑 AST 分叉才报红。测试 MUST NOT 抽公共运行时模块或建立 recorder 间 import。`PRIORITIES` 等非函数常量继续走独立值相等断言，不塞进函数 source harness。

#### Scenario: 三向 frontmatter/lock helper 逻辑分叉
- **WHEN** 三向 roster 中任一 helper 在 buglist/todolist/issues 三份剥 docstring 后 AST 不等
- **THEN** 一致性测试失败并指明 helper 与不一致 recorder，MUST NOT 因三条 CLI 当前样例恰好都绿而放行

#### Scenario: dated bytes helper 与 text helper 边界漂移 `[grill-amendment]`
- **WHEN** 任一 recorder 缺少 `atomic_write_bytes`/binary document helper，或 dated writer 回退调用 text `atomic_write`
- **THEN** mirror/call-graph 测试失败；生成型 INDEX/batches 继续使用 text helper不算漂移

#### Scenario: 两向 legacy/ID helper 逻辑分叉
- **WHEN** 两向 roster 中任一 helper 在 buglist 与 todolist 剥 docstring 后 AST 不等
- **THEN** 一致性测试失败；issues.py 不在该两向比较中，除非该 helper 被 design 明确提升为三向共享

#### Scenario: docstring 与注释差异不报漂移
- **WHEN** 某共享 helper 的可执行 AST 等价，但 docstring/注释按 bug/todo/issues 语境不同
- **THEN** 一致性测试通过，不把合法说明差异误报为行为漂移

#### Scenario: roster helper 被删除或改名
- **WHEN** 某 recorder 删除/改名一个仍在显式 roster 的 helper而未同步契约
- **THEN** 测试因 source lookup 失败而红，MUST NOT 动态跳过不存在的名字

#### Scenario: 已退役 table-cell helper 不再被强制存在
- **WHEN** 实现按 SW-RI-1 删除三份 `_reject_cell_unsafe`
- **THEN** mirror test 不因该旧 helper 缺失而失败，且 source/调用图检查确认新索引写路径无其引用；Markdown 单行安全由 `_reject_line_unsafe` 独立守护

#### Scenario: legacy parser 只读边界
- **WHEN** 新 canonical/overlay item 经 add/set-status/triage/batch rename 写入
- **THEN** 调用跟踪显示 `split_sections`/`parse_table_rows` 仅在 legacy read/overlay merge 中执行，writer 不渲染或修改 legacy table row

#### Scenario: PRIORITIES 常量跨脚本一致性
- **WHEN** `issues.py` 声明的 `PRIORITIES` 与 `buglist.py` 值不相等
- **THEN** 独立列表值相等断言报红；该断言不进入 `inspect.getsource` 函数 harness

#### Scenario: mirror guard 不建立运行时耦合
- **WHEN** 一致性测试加载三个 recorder
- **THEN** 它以测试期 importlib/inspect 读取源码完成比较，生产脚本之间没有新增 Python import，独立安装/调用仍成立
