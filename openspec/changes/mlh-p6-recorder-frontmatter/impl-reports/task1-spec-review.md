# Task 1 Spec Review — strict dual-reader

结论：**FAIL**

审查基准：`SW-RI-1`、`SW-RI-4`、`DG-RI-1`，以及 `superpowers-plan.md` Task 1。测试通过不能替代下列目标态缺口。

## Critical

1. **overlay shadow 仍按 literal ID，而不是 semantic ID。** `shadowed` 与 `legacy_owned` 都直接用字符串集合判断；legacy `A007` 与 frontmatter `A7` 会同时进入输出，且重复汇总也按 raw string 分桶。目标态要求同文件按 `(ASCII prefix, decimal integer)` 合并并由 frontmatter 唯一 shadow legacy snapshot。见 `sdflow-buglist/scripts/buglist.py:875-876,899-900,934-945`、`sdflow-todolist/scripts/todolist.py:852-853,873-874,899-909`。

2. **跨文件重复 ID 没有 fail-closed。** 重复只被追加到 `problems`，随后 `scan --json` 仍正常打印 payload 并 exit 0；`SW-RI-4` 明确要求跨文件语义重复无论 strict 与否都致命且不得生成新 snapshot。见 `sdflow-buglist/scripts/buglist.py:933-957`、`sdflow-todolist/scripts/todolist.py:898-926`。

## Important

1. **fatal diagnostics 缺文件定位。** `read_recorder_document()` 未捕获并补充 `path`，parser 生成的 schema/encoding/lexical 错误也不携带路径，顶层仅原样打印异常；不满足“涉及文件时必须带定位”。新增测试同样只断言 reason，从未断言 path。见 `sdflow-buglist/scripts/buglist.py:276-303,1038-1042`、`sdflow-buglist/tests/test_frontmatter_dual_reader.py:135-150`。

2. **单次 document parse 的产物合同未实现。** `parse_recorder_document()` 只返回 body/model/span；`cmd_scan()` 随后再次分别执行 `split_sections`、table parse、legacy block parse、marker parse、merge 与 relation validation。Task 1 要求一次 document parse 直接产出 format/items/blocks/problems；现有计数测试只直接测 `read_recorder_document()` 的一次 `open`，没有覆盖真实 `scan` 或 `parse_recorder_document` 调用次数。见 `sdflow-buglist/scripts/buglist.py:276-303,858-930`、`sdflow-buglist/tests/test_frontmatter_dual_reader.py:153-168`。

3. **三 recorder parity/golden 未覆盖实际 dual-reader 行为。** `issues.py` 只有基础 namespace helpers；semantic overlay merge、legacy region、marker relation 没有三向实现或 canonical/pure-legacy/overlay golden equivalence，`marker_block_ranges` 也未进入三向守卫。当前 AST equality 只能证明复制的低层函数相同，不能证明三个 recorder 的 effective items/problems 一致。见 `sdflow-buglist/tests/test_mirror_consistency.py:62-76`、`sdflow-issues/scripts/issues.py:64-315`。`⚠️ cannot-verify-from-diff`：后续 Task 4 的 `read_rename_snapshot()` 尚不在本 diff，不能为本 Task 1 验收兜底。

4. **坏输入与 golden fixture 矩阵不足。** 现有 13-case 文件未覆盖重复 namespace/JSON key/ID、缺字段与类型/枚举越域、raw NEL/LS/PS、lone CR/非法 UTF-8、overlay 区域重复、marker 缺对/错配/嵌套/重复、semantic alias shadow、跨文件 fatal、真实 scan 的 read/parse 计数及三 recorder golden parity；因此报告中的“严格失败矩阵/三 recorder parity”没有可审计证据。见 `sdflow-buglist/tests/test_frontmatter_dual_reader.py:1-222`。

## Minor

- 实现报告写“overlay 同文件 literal ID 由 frontmatter shadow”，这本身暴露了与批准目标态 semantic ID shadow 的偏差；`Concerns: 无` 不成立。见 `openspec/changes/mlh-p6-recorder-frontmatter/impl-reports/task1-strict-dual-reader.md:8,27-29`。

Task 1 必须修复 Critical/Important 并补齐对应回归证据后才能 PASS。
