# Task 1 impl-report — Validator 机械脚本（findings_ref_check.py）

## 落位

- `sdflow-init/assets/workflow/tools/findings_ref_check.py`（新，纯 stdlib，无 subprocess）
- `sdflow-init/assets/workflow/tools/tests/test_findings_ref_check.py`（新，20 用例）

## 实现摘要

按 `task1-brief.md` + `design.md` DD4 + `specs/spec-workflow/spec.md` Requirement「评审裁决协议为机械前置 + 二元裁决 + 置信降排序」实现：

- **输入契约**：只吃结构化 JSON（顶层裸 list 或 `{"findings": [...]}`），每条 finding 带 `{file, line, quote}` 或 `evidence_pack`；MUST NOT 解析 markdown 散文（脚本无任何 markdown 解析代码路径）。
- **三查**（`classify_finding`）：① `Path(root) / file` 是否为存在文件 ② `line`（严格正整数或纯数字字符串，其余判非干净单行形态）是否落在文件总行数内 ③ `quote.strip()` 是否为所报行文本的子串（**只核该单行**，不做整文件子串核，堵住 spec-review-amendment 指出的绕过口）。
- **三态输出**：`pass` / `fail`（含 4 个 reason：`path-not-found` / `line-out-of-bounds` / `quote-mismatch` / `no-quote-no-evidence`，另有边缘 `file-unreadable`）/ `uncheckable`（3 个 reason：`evidence-pack` / `design-reference`〔有引文无 file/line〕/ `line-range-form`〔`line` 非干净单行，如区间字符串 `"12-18"`、list、浮点〕）。
- **崩溃显式降级**：JSON 语法错误、顶层结构非预期（`findings` 非 list）、findings 列表内混入非对象条目（`process_batch` 内 `.get` 自然抛 `AttributeError`）——均整批降级为 `{"result":"degraded","code":"[ref-check-unavailable]","results":[]}`，不吐半截结果。正常态输出 `{"result":"ok","results":[...]}`——两态在 JSON 顶层字段值上互斥可辨，调用方读 JSON 内容即可区分，不依赖退出码（信号内诚实）。
- **CLI**：`--input <findings.json> --root <repo-root>`，dual output（human 摘要 stderr + 机读 JSON stdout），exit 0=ok / 1=degraded。

## TDD 记录

先写 20 用例（`test_findings_ref_check.py`）覆盖 brief 的 7 条验收复选框，跑一次确认全红（脚本文件不存在），再实现脚本至全绿：

```
/usr/bin/python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_findings_ref_check.py -q
20 passed in 0.20s
```

全仓回归（干净未中断跑批，非本次改动引入任何红）：
```
/usr/bin/python3 -m pytest -q
2533 passed, 10 skipped in 373.39s (0:06:13)
```

## 验收复选框对照（task1-brief.md）

- [x] 正例返回 pass — `test_pass_valid_reference`
- [x] 三种失败态各返回 fail — `test_fail_path_not_found` / `test_fail_line_out_of_bounds` / `test_fail_quote_mismatch`
- [x] 无引文且无证据包返回机械裁掉信号 — `test_fail_no_quote_no_evidence`（+ 空白 quote 变体）
- [x] uncheckable 态返回 uncheckable — `test_uncheckable_evidence_pack` / `test_uncheckable_design_reference_no_file_line` / `test_uncheckable_line_range_form_string` / `test_uncheckable_line_range_form_list`
- [x] 脚本级崩溃显式降级标 `[ref-check-unavailable]` — `test_degrade_malformed_json_syntax` / `test_degrade_findings_not_list_or_wrapped_dict` / `test_degrade_unexpected_exception_non_dict_entry`
- [x] 输出码形态符合信号内诚实 — `test_output_honesty_degraded_distinguishable_from_ok` / `test_no_bare_pass_code_when_script_never_ran_checks`
- [x] pytest 覆盖上述场景 — 20 用例（另含批量整合 + CLI 契约 + 纯 stdlib 静态断言）

## 未做/边界说明

- 本票范围只交付 validator 本身；两评审 SKILL 的 Step3 接线（消费本脚本）是 tasks 1.2/1.3，不在本票范围内（brief 未列，未做）。
- `line` 类型只接受 `int` 或纯数字字符串；浮点行号（如 `10.0`）判非干净单行形态（`line-range-form`）——JSON 数字通常按整数写入，此边界为已知简化（基准 4，未见 brief/design 要求覆盖浮点行号形态）。

## 状态

DONE
