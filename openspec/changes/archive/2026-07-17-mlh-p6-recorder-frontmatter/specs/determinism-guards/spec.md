## MODIFIED Requirements

<!-- REQ: DG-RI-1 -->
### Requirement: recorder 镜像 helper 由「剥 docstring 后 AST 等价」一致性测试守护

三份 recorder（`buglist.py`/`todolist.py`/`issues.py`）为保持 skill 自包含而各自内联的真共享 helper MUST 由剥函数 docstring 后 `ast.dump` 相等的断言守护行为不漂移。frontmatter 目标态的三向组 SHALL 至少包含 `atomic_write`、`atomic_write_bytes`、`repo_root`、`recorder_lock`、`_canonical_id_key`、`_reject_line_unsafe`、`read_recorder_document`、`parse_recorder_document`、`render_recorder_namespace`；buglist↔todolist 两向组 SHALL 包含其共享的 change/doc/block/legacy/ID/定位 helpers，包括 `detect_change`、`normalize_doc_paths`、`auto_default_doc`、`split_sections`、`parse_table_rows`、`block_ranges`、`_find_item_file`、`_id_sort_key`、`validate_doc_paths`、`all_ids`、`next_id`、`_die`、`_load_json`。实现若为满足已批准 design 增减或重命名共享 helper，MUST 在同一提交中更新显式 roster 与本 requirement，MUST NOT 以动态发现所有同名函数替代人工审定的边界。

`[spec-review-amendment]` 因 `issues.py::read_rename_snapshot()` 必须直接解析两池 dated files 才能达成 whole-command read=1，legacy region discovery、semantic-ID/overlay merge、marker relation 与 envelope lexical scanner 升为三向**行为契约**。能用同签名纯 helper 表达的部分 SHALL 进入 THREE_WAY AST roster；pool-specific legacy 字段差异与 `read_rename_snapshot` 编排则用同一 canonical/pure-legacy/overlay fixture 做 golden equivalence：`issues.py` direct snapshot 的 effective items/problems 必须等于 bug+todo `scan --json` contract join，且额外保留 raw bytes/spans。`validate_scan_envelope` 是 issues consumer 独有 helper，须以坏 JSON/缺键/错型/缺 file contract tests 守护，不伪塞进三向 AST roster。

`_reject_cell_unsafe` 不再属于目标态 roster；`split_sections`/`parse_table_rows` 只作为 buglist↔todolist 的 legacy read 半场保留，MUST NOT 被新写路径调用。契约继续锁**行为等价层而非字面层**：docstring/注释按 recorder 语境分化合法，逻辑 AST 分叉才报红。测试 MUST NOT 抽公共运行时模块或建立 recorder 间 import。`PRIORITIES` 等非函数常量继续走独立值相等断言，不塞进函数 source harness。

#### Scenario: 三向 frontmatter/lock helper 逻辑分叉
- **WHEN** 三向 roster 中任一 helper 在 buglist/todolist/issues 三份剥 docstring 后 AST 不等
- **THEN** 一致性测试失败并指明 helper 与不一致 recorder，MUST NOT 因三条 CLI 当前样例恰好都绿而放行

#### Scenario: dated bytes helper 与 text helper 边界漂移 `[grill-amendment]`
- **WHEN** 任一 recorder 缺少 `atomic_write_bytes`/binary document helper，或 dated writer 回退调用 text `atomic_write`
- **THEN** mirror/call-graph 测试失败；生成型 INDEX/batches 继续使用 text helper不算漂移

#### Scenario: 两向 legacy/ID helper 逻辑分叉
- **WHEN** 两向 roster 中任一 helper 在 buglist 与 todolist 剥 docstring 后 AST 不等
- **THEN** 一致性测试失败；`[spec-review-amendment]` 已被 direct rename snapshot 提升为三向行为契约的 scanner/semantic/merge 规则不得继续只靠两向守护，pool-specific 展开以 golden equivalence 覆盖

#### Scenario: direct rename snapshot 与 recorder scan 语义漂移 `[spec-review-amendment]`
- **WHEN** 同一 canonical/pure-legacy/overlay fixture 分别经 issues direct snapshot 与 bug/todo `scan --json` contract 解析
- **THEN** effective items/problems 按 semantic key 完全等价，issues 结果另带 raw bytes/spans；任一方漏掉 lexical/marker/overlay/ID rule 时测试失败

#### Scenario: scan JSON consumer validator 不默认空池 `[spec-review-amendment]`
- **WHEN** producer JSON 缺 `bugs|items`/`problems`、类型错误或 item 缺 `file`
- **THEN** `validate_scan_envelope` 测试要求 issues fail-closed，MUST NOT 以 `.get(..., [])`/falsey fallback 继续

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
