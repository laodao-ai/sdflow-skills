# Task 1 Standards Review — strict dual-reader

结论：**FAIL**

## Critical

1. `sdflow-buglist/scripts/buglist.py:875-900,921-931`（镜像：`sdflow-todolist/scripts/todolist.py:852-874,887-896`）overlay shadow、owner 分区和重复检测仍按 literal string，而不是 `(ASCII prefix, decimal integer)` semantic key。实测同文件 legacy `A007` + frontmatter `A7` 返回两个 item 且 `problems=[]`；这直接违反 SW-RI-1 的唯一当前值/semantic ID 合同，并会把错误 snapshot 交给 reindex 等 consumer。

## Important

1. `sdflow-buglist/scripts/buglist.py:204-226`（三份镜像）lexical scanner 把任何 space-indented 行都当 continuation，却不要求前面已有合法 column-0 entry。于是顶层写成 `  sdflow-issues:` 的坏 namespace 被当成 namespace absent，并回退 legacy；实测返回 `format=legacy`。这违反“ownership 变体/坏 namespace fail-closed”。

2. `sdflow-buglist/scripts/buglist.py:272-295`（三份镜像）用任意 `^| ID |` 行计数 legacy 状态总览区域，未绑定 `## 状态总览` 区域。canonical marker prose 中合法出现 fenced/example `| ID | ... |` 会被误判为 `mode-structure mismatch`；目标态允许详情 prose 自由包含 Markdown，不能把普通内容提升成 legacy owner evidence。

3. `sdflow-buglist/scripts/buglist.py:276-303,858-864`（todo 镜像）`parse_recorder_document` 只解析 envelope/model，`cmd_scan` 随后又分别执行 `split_sections`、`parse_table_rows`、`block_ranges`、`marker_block_ranges`。这没有做到“一次 document parse 产出 items/blocks/problems/format”，且现有测试 `test_frontmatter_dual_reader.py:170-184` 只统计 `open()`，无法证明 parse=1。

4. `sdflow-buglist/scripts/buglist.py:300-303,1038-1044`（todo 镜像）fatal parse error 没在 `read_recorder_document` 附加 path，main 只打印裸 `ValueError`。实测坏 schema stderr 不含 dated file；不满足新增 fatal diagnostic 必须点名 file/reason 的错误契约。

## Minor

1. `sdflow-buglist/tests/test_frontmatter_dual_reader.py:44-222` 仅覆盖少量 happy path/5 个坏样例；没有覆盖 semantic `A007/A7` shadow、indented ownership、raw NEL/LS/PS、surrogate、JSON duplicate key、空字段/null、marker 缺对/错配/嵌套/重复/orphan，也没有对 `issues.py` 跑独立 golden/parity。当前 20 个定向测试全绿，但不能支撑报告中的完整坏矩阵与“三 recorder parity/golden”声明。

## Verification

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_frontmatter_dual_reader.py sdflow-buglist/tests/test_mirror_consistency.py` → `20 passed`。
- 独立对抗复现确认上述 semantic shadow、indented ownership fallback、prose table false positive、missing-path 四项均存在。
- backend/embedded domain checklist：本 change 无命中，未作领域清单假通过。
