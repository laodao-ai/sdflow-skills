# Task 1 Spec Review — strict dual-reader

## 首轮审查（保留）

结论：**FAIL**。

- Critical：overlay shadow 按 literal ID；跨文件重复 ID 未 fail-closed。
- Important：fatal diagnostic 缺 path；真实 `scan` 未由单次 document parse 承载；三 recorder parity/golden 不完整；坏输入矩阵不足。
- Minor：实现报告错误声称 literal shadow 符合目标态。

## Re-review — HEAD `42bcd2a`

结论：**FAIL**。

首轮两项 Critical 已修：overlay 现按 semantic key shadow，跨文件 semantic duplicate 现 fatal；path diagnostic 与真实 parser call-count 已补，三向 helper roster也扩大。定向验证 `27 passed`，但目标态仍有以下阻断项。

### Critical

1. **canonical 文档仍会把自由 prose 中任意 `| ID |` 表提升成 legacy 索引。** `parse_recorder_document()` 无论 format 都调用 `split_sections/parse_table_rows`，`cmd_scan()` 也无论 format 都把 `rows` 放入 `legacy_owned` 并输出。最小复现：canonical `B1` marker 内放一个 8 列示例表行 `B99`，parser 返回 `rows=['B99']`，scan 会把 `B99` 当 item。目标态要求 canonical 只读 frontmatter，且自由 prose 不制造机器索引。见 `sdflow-buglist/scripts/buglist.py:309-317,928-960`、`sdflow-todolist/scripts/todolist.py:287-295,902-925`。新增测试只放了 2 列表并仅断言 exit 0，未断言 payload/problems，因而漏检：`sdflow-buglist/tests/test_frontmatter_dual_reader.py:290-311`。

### Important

1. **shared-envelope ownership 检测过宽，拒绝合法 opaque 外部值。** `_find_recorder_span()` 只要任意行包含字节串 `sdflow-issues` 且不是以 `sdflow-issues:` 开头就 fatal；合法的 `other: sdflow-issues is text`、space-indented value、甚至 column-0 comment 都被误判 ownership ambiguity。lexical profile 明确允许这些外部 bytes。见 `sdflow-buglist/scripts/buglist.py:215-229`（三份镜像）。

2. **一次 document parse 产物合同仍只部分闭合。** table/block 切分已移入 parser，但 semantic merge、effective owner partition、relation validation 与最终 problems 仍在 `cmd_scan()` 二次编排；parser 未产出目标要求的 `items + blocks + problems + format`。见 `sdflow-buglist/scripts/buglist.py:286-318,891-960`。

3. **三 recorder golden 与坏矩阵仍不完整。** 新 golden 仅比较 canonical model/marker；没有对三份 recorder 比较 pure-legacy/overlay 的 effective items/problems。marker 缺对/错配/嵌套/重复、lone CR/非法 UTF-8、surrogate、null/empty-map/缺字段/枚举越域等批准矩阵仍无对应新增证据。`⚠️ cannot-verify-from-diff`：后续 Task 4 的 effective snapshot 尚未实现，不能为 Task 1 假通过。见 `sdflow-buglist/tests/test_frontmatter_dual_reader.py:229-349`。

### Minor

- `read_recorder_document()` 把 `; file: ...` 追加在 `fix` 之后，偏离批准的严格三段式；建议把 path 放入 problem/cause 内。见 `sdflow-buglist/scripts/buglist.py:321-327`。

修复 Critical/Important 并补最小反例后，Task 1 才可 PASS。
