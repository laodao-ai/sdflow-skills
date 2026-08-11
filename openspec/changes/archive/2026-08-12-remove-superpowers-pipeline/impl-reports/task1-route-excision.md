# Task 1: 路由切除与保留半场回归 — 实现报告

## 概述

从 `sdflow-implement/scripts/impl_route.py` 整体切除「管线路由三跳」（config 键 →
plan frontmatter marker → 缺省）相关的全部函数、类与 `route` 子命令，文件头注释改写为
tickets 调度 helper 自述。同步退役 `test_impl_route.py` 的 route/config/marker 参照系用例，
`test_yq_wrapper_consistency.py` 成员表去 `impl_route` 条目。保留半场（`frontier` /
`task-text` 子命令、`parse_blocked_by`、`_detect_cycle`、`next_ready`、`extract_task_text`、
`TopoError`、`BLOCKED_BY_RE`）接口与行为逐字不变，回归绿。

## 改动清单

### `sdflow-implement/scripts/impl_route.py`

删除：
- 文件头「管线路由三跳」+ `[shared-yaml-subset-parser]` 两段说明性 docstring 段落，改写为
  「tickets 调度 helper」自述（保留 `[impl-review-fix F4]` 围栏词法单一源说明段，未改动）。
- `_yq_bin` / `_yq()`（yq subprocess 薄封装，唯一调用点在被删的 `read_config_pipeline` /
  `read_plan_marker` 内）。
- `LEGAL_PIPELINES`、`_PIPELINE_KEY_RE`、`_FRONTMATTER_DELIM`。
- `RouteStop` 异常类。
- `read_config_pipeline()`（① config 键读取）。
- `read_plan_marker()`（② plan frontmatter marker 读取）。
- `resolve_pipeline()`（③ 路由合成）。
- `_get_plan_sha()`（route CLI 专用的 plan_sha 取值）。
- `_cmd_route()` 及 `build_parser()` 里的 `route` 子命令 subparser。
- sibling-import 块中的 `resolve_plan_path` / `PlanNameConflict` / `PLAN_FILENAMES`
  三个符号（design.md :62「唯一调用点全在被删路由函数内」〔设计门 Q2 拍板〕已核实：三者
  在 impl_route.py 内的唯一消费点全在 `_cmd_route()` 内部，随其一并删除；保留
  `FenceTracker` sibling-import，`parse_blocked_by`/`extract_task_text` 仍依赖）。
- 不再被任何保留函数使用的 `json` / `shutil` / `subprocess` 三个 import（均只服务
  `_yq()` 与 `_get_plan_sha()`）。

保留（接口与行为逐字不变，未作任何改动）：
- `frontier` / `task-text` 子命令（`_cmd_frontier` / `_cmd_task_text`）
- `parse_blocked_by` / `_detect_cycle` / `next_ready` / `extract_task_text`
- `TopoError` / `BLOCKED_BY_RE` / `TASK_HEADER_RE` / `BLOCKED_BY_VARIANT_RE`
- `EXIT_ROUTE_STOP`（虽命名沿用旧路由术语，但为 frontier/task-text 共用的通用退出码，
  brief 未列入删除清单，且改名超出本票范围，予以保留——不改名不算「加宽」也不算「缩水」，
  是最小 diff 原则的直接应用）
- `_FenceTracker` sibling-import 与其 fail-closed 兜底（`_FENCE_IMPORT_ERR`）

`build_parser()` 顶层 `description` 从「sdflow-implement 路由/拓扑 stdlib helper（只读，
不改 ship_gate.py）」改为「sdflow-implement tickets 调度 stdlib helper（只读，不改
ship_gate.py）」。`main()` 里的 `route` 分支同步删除。

验证：改动后 `python3 -c "import impl_route; print(dir(impl_route))"` 公开符号表已不含
`route`/`RouteStop`/`resolve_pipeline`/`read_config_pipeline`/`read_plan_marker`/`_yq`/
`LEGAL_PIPELINES`/`_get_plan_sha`/`_resolve_plan_path`；保留符号全部存在。

### `sdflow-implement/tests/test_impl_route.py`

退役（route/config/marker 参照系，断言目标态已不存在的行为）：
- `read_config_pipeline` 全部用例（缺失/空值/tickets/superpowers/拼错值/引号值/BOM/
  冒号前空格/损坏引号/注释行/缩进提及，14 条）
- `read_plan_marker` 全部用例（缺文件/无 frontmatter/合法单键/键重复/非法值/未闭合
  frontmatter/BOM/冒号前空格/损坏引号，11 条）
- CLI `route` 全部用例（PIPELINE_RECEIPT 格式、路由合成、marker 锁定、RouteStop 退出码、
  plan_sha、双名冲突 fail-closed 等，14 条）
- `test_resolve_plan_path_single_source_used_by_route`（核验 `ir._resolve_plan_path` 身份，
  该符号本票已删除）
- 辅助函数 `_write_config` / `_mkchange` / `_run_route`（仅服务上述已退役用例）

保留并回归绿（35 条，全绿）：
- `parse_blocked_by` / `next_ready` 拓扑用例（线性链/菱形/环/自环/缺依赖/done 过滤）
- fence-aware 解析 + 标题正则收紧用例（含 3 个跨脚本 golden fixture 回归）
- Blocked-by 三态 fail-closed 用例（缺失/重复/大小写变体/全角冒号/行内形态）
- CLI `frontier` 全部用例（含 2 个 golden fixture 回归）
- 围栏词法单一源核验（`ir._FenceTracker is sg.FenceTracker` 身份断言 + 嵌套围栏跨脚本一致性）
- `extract_task_text` 用例 + CLI `task-text` 全部用例

模块 docstring 改写为仅描述保留半场覆盖范围，并留一段指向 design.md 的退役说明。

### `hack/tests/test_yq_wrapper_consistency.py`

`TARGETS` 成员表删除 `sdflow-implement/scripts/impl_route.py` 条目（`_yq` 随路由半场整体
切除退出消费面），消费点数从 6 份改为 5 份。同步修正：
- 顶部 docstring 的计数陈述与差异登记段（`text=` 支持「其余 4 份」→「其余 3 份」，
  `--header-preprocess` 「其余 5 份」→「其余 4 份」，F3 多文档防御名单去 `impl_route.py`，
  `object_pairs_hook` 「其余 5 份」→「其余 4 份」）
- `test_all_six_targets_are_distinct_files` 重命名为 `test_all_five_targets_are_distinct_files`，
  断言 `== 6` 改 `== 5`
- `yq_sources` fixture docstring 「6 份」→「5 份」
- `test_non_zero_exit_branch_fails_loud_not_silently` docstring 「6 份」→「5 份」

未改动：本仓其余 5 份 `_yq()` 消费点脚本本身、以及它们各自的测试。

## 测试结果

```
/usr/bin/python3 -m pytest sdflow-implement/tests/test_impl_route.py -v
→ 35 passed

/usr/bin/python3 -m pytest hack/tests/test_yq_wrapper_consistency.py -v
→ 17 passed

/usr/bin/python3 -m pytest sdflow-ship/tests/test_gate_closing_ticket.py -v
→ 10 passed（含 Task 2 待退役的 2 条 grandfather 用例——Task 1 未触碰 ship_gate.py，
  两条用例仍按现行 grandfather 行为断言，回归绿，不在本票退役范围内）
```

合并核验（三处一次跑）：

```
/usr/bin/python3 -m pytest sdflow-implement/tests/ sdflow-ship/tests/test_gate_closing_ticket.py hack/tests/test_yq_wrapper_consistency.py -x -q
→ 66 passed in 1.49s
```

（`sdflow-implement/tests/` 目录内除 `test_impl_route.py` 外无其它测试文件，故该目录整体
跑等价于单独跑 `test_impl_route.py`。）

未跑全仓 `/usr/bin/python3 -m pytest`——超出本票范围（Task 5 明确把「全仓 pytest 全绿」列为
自己的验收项，需等 Task 2-4 落地后才有意义）；本票验收面（brief 列出的三个文件 + gate
sibling-import 回归）已按上述命令覆盖完整。

## 保留半场核验

- `parse_blocked_by` / `TopoError` / `BLOCKED_BY_RE` 源码逐字未改动（仅其上下文中已删除的
  `RouteStop`/路由函数被移走，函数体本身零改动，`git diff` 可核）。
- `ship_gate.py` 的 `_load_parse_blocked_by()` sibling-import `parse_blocked_by`/`TopoError`
  路径未受影响——`test_gate_closing_ticket.py` 全部 10 条用例（含 sibling-import 依赖的
  收尾票校验用例）回归绿，证实 sibling-import 未断裂。
- `ship_gate.py` :1335 提及 `impl_route.resolve_pipeline` 的注释句现指向已删符号——本票
  Global Constraints 明确该文件是 Task 2 的改动范围（`Blocked-by: 1`），本票不改动
  该文件；该注释句失效属预期的跨票中间态，由 Task 2 收口（design.md :63 已登记）。

## 范围声明

严格按 tickets.md Task 1 与 brief 执行：只改 `impl_route.py` 本体、
`test_impl_route.py`、`test_yq_wrapper_consistency.py` 三个文件。未触碰 `ship_gate.py`、
`test_plan_resolver.py`、`test_superpowers_track_regression.py`、任何 SKILL.md 或
bundle 资产——均属 Task 2/3/4/5 范围。`_resolve_plan_path`/`PlanNameConflict`/
`PLAN_FILENAMES` 三个 sibling-import 符号虽未被 brief 文字逐一点名，但其在 impl_route.py
内的唯一消费点（`_cmd_route`）已随本票删除，design.md :62 已就此给出「唯一调用点全在被删
路由函数内」的设计门拍板依据，故一并删除；未改动 `ship_gate.py` 侧同名符号的定义与实现
（那是 Task 2 的范围）。
