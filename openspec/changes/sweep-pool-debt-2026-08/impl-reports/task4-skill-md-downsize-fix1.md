# Task 4 fix1 — SKILL.md 压缩回归修复

## 背景

Task 4 把 `sdflow-spec/SKILL.md` 里执行到该步才需展开的判据表/背景细节下沉到
`references/execution-protocol-details.md`（commit `f22ede5`），本体从 17,934 字符压到 16,930。
下沉本身没问题，但 implementer 在压缩**留在 SKILL.md 本体**的措辞时，顺手改写了另外
两个契约测试文件的字面锚点，且只跑了 `test_sdflow_spec_resident_contract.py` 没跑全量，
导致合并后 `test_sdflow_spec_failure_modes.py` / `test_task3_phase_c_contract.py` 共 10 个用例回归。

本轮修复按通则③「以最终目标为准，MUST NOT 拿现状反驳目标」：**恢复 SKILL.md 的字面锚措辞**，
MUST NOT 改动这两个契约测试文件的任何断言。

## 恢复的措辞（4 处）

1. **C.1 处置句**（`test_fault4_dispositions_are_present_in_the_skill`）
   - 压缩版把「身份不符（判 3）或 hash 不符（判 4）⇒ 呈现旧 memo 摘要」压成了
     「判 3/判 4 不过 ⇒ 呈现旧 memo 摘要」，丢了「身份不符」「hash 不符」两个具名判据。
   - 恢复为：「身份不符（判 3）或 hash 不符（判 4）⇒ **呈现旧 memo 摘要 + `generated_at` 给人确认**」。

2. **C.2 强制阅读清单**（`test_phase_c_consumes_dependency_objects_and_has_schema_fallback`）
   - 压缩版把写死超集的具体清单（`proposal.md`+`design.md`+`specs/**`）整段下沉到
     reference 文件，SKILL.md 本体只剩一句指针，丢了字面锚 `` proposal.md`+`design.md`+`specs/** ``。
   - 恢复为在 C.2 本体里保留这句写死超集的具体清单（reference 链接仍保留，两者并存）。

3. **C.3 §2 最小 schema 断言**（影响 `test_declared_field_set_includes_the_confused_deputy_field` /
   `test_fault6_real_cli_payload_carries_every_documented_field` / 3× `test_fault6_malformed_payload_fails_closed` /
   `test_fault6_no_retry_instruction_is_present` / `test_phase_c_consumes_dependency_objects_and_has_schema_fallback`）
   - 压缩版把 `` `artifactId`(str) · `instruction`(str) · `template`(str) · `resolvedOutputPath`(str) · `dependencies`(list) ``
     的枚举式写法压成 `` `artifactId`/`instruction`/`template`/`resolvedOutputPath`(str) `` ——
     测试用正则 `` `name`\(type\) `` 抠取声明字段集，压缩后只能抠到 2 对（`resolvedOutputPath`,
     `dependencies`），低于测试要求的下限 5，导致 `documented_required_fields()` 直接
     `AssertionError`，级联打红全部 6 个依赖它的用例。
   - 同时丢了「`dependencies` **MUST 是对象列表**」（MUST 被溶解成纯类型标注）和
     「字段类型不符」被压成「类型不符」（丢「字段」二字，两处都是测试的字面锚）。
   - 恢复为原始的逐字段枚举写法 + 「`dependencies` MUST 是对象列表」+「字段类型不符」。

4. **C.3 §3 status 分支**（`test_phase_c_handles_glob_existing_outputs_and_skipped_status`）
   - 压缩版把「`status` 为 `skipped` 时跳过」压成「`skipped` 时跳过」，丢了「`status`为」。
   - 恢复为「生成前读 status；`status` 为 `skipped` 时跳过」。

## MUST NOT 改动确认

- `hack/tests/test_sdflow_spec_failure_modes.py`：**未改动**。
- `hack/tests/test_task3_phase_c_contract.py`：**未改动**。
- 已成功下沉到 `references/execution-protocol-details.md` 的其余内容（0.2/0.3/FF-0 grammar/
  C.2 依赖图表/C.4 已知限制等）**未撤回**——本轮只恢复被误压的字面锚，不逆转有效的下沉。

## 字符数

- Task 4 合并后：16,930
- 本轮修复后：**17,164**（`/usr/bin/python3 -c "len(open('sdflow-spec/SKILL.md').read())"`）
- 硬上限（`test_sdflow_spec_resident_contract.py`）：18,000 —— 仍有约 836 字符余量。

## 验证结果

### 目标契约（先跑）

```
$ /usr/bin/python3 -m pytest hack/tests/test_sdflow_spec_failure_modes.py \
    hack/tests/test_task3_phase_c_contract.py \
    hack/tests/test_sdflow_spec_resident_contract.py -q
.....................................                                    [100%]
37 passed in 3.08s
```

### 全量回归

```
$ /usr/bin/python3 -m pytest -q
........................................................................ [  2%]
... (省略中间进度行) ...
......................................................................   [100%]
2580 passed, 10 skipped in 376.56s (0:06:16)
```

**0 failed。** 10 个 skip 与本次改动无关（既有的环境依赖跳过，如 `openspec` CLI 未安装等条件跳过）。

## 结论

Task 4 的「判据下沉 references/」目标本身达成且保留；本轮修复的是下沉过程中误伤的本体措辞。
全量 pytest 绿，无需人拍板项。
