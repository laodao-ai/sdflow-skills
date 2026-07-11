# Task 2 impl report — hr_tg_intersect 校验器

**状态：** DONE
**R-ID：** HRT · **Blocked-by：** none

## 做了什么

TDD（红→绿）实现 T81 HR-TG 交集校验器，权威源落盘：
- 校验器：`sdflow-init/assets/workflow/tools/hr_tg_intersect.py`
- 测试：`sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py`（23 用例）

承 4.C `lens_metric_emit.py` / 同批 Task 1 `outside_voice_guard.py` 形态：`EmitError` + `EXIT_OK/EXIT_FAIL=0,1`、
纯 stdlib（仅 `argparse, re, sys, pathlib`，无 `os`/`subprocess`）、门控外置（不读 config）、
all-or-nothing fail-closed、跨模块口径重实现不 import。

## 公共接口 seam（CLI 契约 + 核心函数）

CLI：`hr_tg_intersect.py --tg-set <CSV> --trigger-catalog <path>`
- `--tg-set`：模型判好的命中 TG 集，逗号分隔；**空集传空串 `""`**（`required=True` 仅要求 flag 在场，空值合法）。
- `--trigger-catalog`：HR-TG 单一源路径，**由入参给定**（无 `__file__` 推导、无 default）。

核心函数（测试直调，非仅 CLI）：
- `load_hr_tg_subset(catalog_path) -> set` —— 从 `## …HR-TG…` 段 `> 成员：` 行 parse 成员集。
- `parse_tg_set(raw) -> list` —— CSV → token 列表，逐 token 严格校验 `^TG-\d+$`。
- `intersect(declared_tokens, hr_tg_subset) -> (hits, declared)` —— 均 `sorted(set(...))` 数值序。
- `render(hits, declared) -> str` —— 两行：结果行 + 规范锚串。

**输出契约（两行 stdout）：**
```
hit:[TG-04,TG-16]｜依据模型判定:[TG-04,TG-16,TG-19]
<!-- sdflow:hr-tg v1 hit="TG-04,TG-16" declared="TG-04,TG-16,TG-19" -->
```
none 态：`none｜依据模型判定:[...]` + `hit="none"` 锚。空集：`none｜依据模型判定:[]` + `declared=""`。
锚沿用既有 `<!-- sdflow:hr-tg v1 hit="…|none" … -->`（`anchor_lint.py:15`），**扩 `declared=` 字段**（design D3）；
`evidence=` 仍归 SKILL（模型手填），校验器只出 hit/declared。

**退出码：** hit 与 none 均为合法判定 → `EXIT_OK`（spec 场景「无交集 → 退出码 0」）；
仅坏输入/单一源损坏 → `EXIT_FAIL` + stderr FAIL、无 stdout。（区别于 T80：T80 none 亦非零；T81 none 是有效结果。）

## 三类正例证据（CLI 实跑 against 真实 catalog）

| 场景 | `--tg-set` | 结果行 | exit |
|---|---|---|---|
| 命中 HR-TG 成员 | `TG-04, TG-16, TG-19` | `hit:[TG-04,TG-16]｜依据模型判定:[TG-04,TG-16,TG-19]` | 0 |
| 无交集 | `TG-01, TG-19` | `none｜依据模型判定:[TG-01,TG-19]` | 0 |
| 空集 | `""` | `none｜依据模型判定:[]` | 0 |

TG-19 不属 HR-TG 故不在 hit、但在「依据模型判定」可见（adr/0018 不可验输入信号里可见）。
确定序：`test_dedup_and_sorted_numeric` 断言乱序 + 重复输入 `TG-16,TG-08,TG-08,TG-04` → `[TG-04,TG-08,TG-16]`
（数值序，非字典序 '8'>'1'）。

## 单一源可变性测试（证明非硬编码）

- `test_single_source_mutability`：构造成员集仅 `TG-99` 的 catalog 夹具 → `load_hr_tg_subset` 返回 `{TG-99}`，
  且 `TG-04` 在此 catalog 下**不再命中**（真实清单里 TG-04 属 HR-TG）。改单一源即改行为。
- `test_reads_real_catalog_members`：从真实 `trigger-catalog.md` 读，成员 = 文档声明的 8 个
  `{TG-04,06,07,08,09,16,17,26}`。
- `test_no_hardcoded_member_list`：静态断言脚本源码不含 `TG-04/TG-16/TG-26` 串（无硬编码副本）。

## fail-closed 路径

- `test_missing_catalog_fail_closed` —— catalog 文件不存在 → EmitError。
- `test_missing_hr_tg_section_fail_closed` —— 无 `## …HR-TG…` 段 → EmitError。
- `test_missing_member_line_fail_closed` —— HR-TG 段内无 `> 成员：` 行 → EmitError。
- `test_empty_member_line_fail_closed` —— 成员行存在但无 TG 记号（`**（暂无）**`）→ EmitError（**不静默按空子集放行**）。
- `test_member_line_in_other_section_not_leaked` —— 别的段有 `> 成员：` 而 HR-TG 段没有 → EmitError（段边界严格，不跨段借用）。
- `test_malformed_tg_token_fail_closed` —— `--tg-set` 含 `banana` → EmitError。
- CLI 层：`test_cli_corrupt_source_fail_closed_stderr_no_stdout` 断言坏输入时 stdout 空、stderr 含 `[hr_tg_intersect] FAIL`、无 `Traceback`。

段边界解析：定位 `HR-TG` level-1/2 标题后，扫描至下一 level-1/2 标题为段界（`### ` level-3 不终止），
段内首个 `> 成员：` 行用 `re.findall(r'TG-\d+')` 抽 token（容忍 `**bold**`/空格）。

## 静态约束断言（随测试）

- `test_no_subprocess_no_os_import_ast`：AST 断言未 import `subprocess`/`os`。
- `test_no_exec_tokens_in_source`：源码无 `os.system/os.popen/Popen/check_output/git` 等 token。
- `test_no_file_derived_catalog_path`：AST 断言代码无 `__file__` 名字节点（docstring prose 提及不计），catalog 路径纯入参。

## 全套件结果

`python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -W error -q` → **148 passed, 0 warning**
（本 task 新增 23 用例，其余存量校验器套件全绿）。

## concerns

1. **TG 编号匹配为精确字符串相等**：catalog 现用零填充二位（TG-04…TG-26）。若模型传 `TG-4`（未填充）而 catalog 写 `TG-04`，
   二者字符串不等 → 不命中（false negative）。当前未做规范化，因规范化需臆测 catalog 填充位、有引入假命中的风险；
   依赖 SKILL 接入步指示模型用 catalog 规范 ID。数值序排序对填充/未填充均正确，仅**匹配**受影响。低风险（现役成员全二位），记录备查。
2. `render` 的分隔符为全角 `｜`（U+FF5C），逐字取自 design D3 / spec 场景；结果行与锚串已 CLI 实跑核对字节一致。
