# Task 1 Standards Review — strict dual-reader

结论：**FAIL（HEAD `42bcd2a` re-review）**

## 首轮问题与复核结论

| 首轮问题 | re-review |
|---|---|
| overlay `A007/A7` 按 literal shadow | **已修复**：按 semantic key shadow；对抗 fixture 只返回 `A7` |
| 跨文件 semantic duplicate 非 fatal | **已修复**：`A007@file1 + A7@file2` non-zero，stdout 为空并列出位置 |
| indented ownership 变体回退 legacy | **已修复原例**：`  sdflow-issues:` fatal |
| 任意 prose table 被计作 legacy region | **部分修复，仍有 Critical/Important，见下** |
| scan 未形成单次 document parse | **已修复**：一次 `parse_recorder_document` 返回 rows/blocks/markers，真实 scan 计数=1 |
| fatal diagnostic 缺 path | **已修复**：stderr 带 dated file path |
| 三 recorder parity/golden 不足 | **已修复核心证据**：三向 AST roster 与 renderer/parser golden 已覆盖 |

## Critical

1. `sdflow-buglist/scripts/buglist.py:309-317,883-929`（三份 parser/两份 scan 镜像）canonical 仍无条件运行 `split_sections()`；而 `split_sections()` 只找正文首个 `| ID |`，不验证 `## 状态总览`，也不按 format 禁止 legacy merge。实测 canonical marker prose 内放一个合法 8-column 示例表，会把 prose row `X1` 输出成第二个机器 item（exit 0），直接违反“新 item 索引仅 frontmatter / canonical 只读 frontmatter”。

## Important

1. `sdflow-buglist/scripts/buglist.py:281-306` 的 legacy-region regex 不识别 Markdown fence。实测 canonical marker prose 的 fenced 示例中包含 `## 状态总览` + `| ID |` 时，被误判为 `mode-structure mismatch` fatal；详情 prose 按目标态可自由包含 heading/table/fence。

2. `sdflow-buglist/scripts/buglist.py:209-229`（三份镜像）用 `b"sdflow-issues" in line` 判 ownership 歧义，越过了顶层 key 边界。合法外部 entry 的 indented block value 或 comment 只要提到文字 `sdflow-issues` 就被拒绝；实测 `other: |` 下的 `documentation mentions sdflow-issues` fatal，违反 namespace 外 opaque bytes 合同。

## Minor

1. `sdflow-buglist/tests/test_frontmatter_dual_reader.py:290-312` 的 prose-table 回归只断言 returncode=0，未断言输出 items/problems；因此实际 ghost item/arity problem 没有拉红。fenced overview 与外部 opaque token 也无回归。

## Verification

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_frontmatter_dual_reader.py sdflow-buglist/tests/test_mirror_consistency.py` → `27 passed`。
- 独立复现：canonical prose 产出 ghost `X1`；fenced overview false fatal；合法 external opaque token false fatal。
- backend/embedded domain checklist：无命中，未作领域清单假通过。
