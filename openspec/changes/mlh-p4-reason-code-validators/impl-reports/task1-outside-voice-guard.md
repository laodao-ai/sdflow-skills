# Task 1 impl report — outside_voice_guard 校验器（T80 / OVG）

## 做了什么

TDD 实现 outside-voice 复用守卫，落权威源：
- 实现：`sdflow-init/assets/workflow/tools/outside_voice_guard.py`
- 测试：`sdflow-init/assets/workflow/tools/tests/test_outside_voice_guard.py`（25 用例）

给定一份 outside-voice 产物（gstack-review.md）+ 一个 change 目录，按三前置**按序**（来源 mode > 新鲜度 fs-mtime > 结构 codex 段）确定性归约出**唯一** reason_code（六枚举）。纯 stdlib、无 subprocess、门控外置、坏输入 all-or-nothing fail-closed。承 4.C `lens_metric_emit.py` 形态（逐字复用 `EmitError` / `EXIT_OK=0,EXIT_FAIL=1` / stdlib-only / 无 import 跨模块）。

## 公共接口 / seam

CLI 契约（A12：对齐 tasks.md 1.2 与 `--change-dir`）：
```
outside_voice_guard.py --review-path <gstack-review.md> --change-dir <openspec/changes/<name>/>
```
核心归约函数（pytest 直调的 seam）：
- `classify(review_path, change_dir) -> str` —— 返回 reason_code；坏输入 raise `EmitError`。
- `parse_mode(text) -> str` —— 抓 `step1-broad-review` 锚 mode（我们的锚，严格：锚缺失/缺 mode/mode 非枚举 → `EmitError`）。
- `source_max_mtime(change_dir) -> float` —— 源文件（`proposal.md/design.md/tasks.md` + `specs/**` 递归）最大 fs-mtime；inclusion allowlist 天然排除评审产物自身；change_dir 缺失/无源文件 → `EmitError`。
- `parse_codex_findings(text) -> int|None` —— best-effort：优先 `sdflow:outside-voice v1 ... runner="codex" ... findings="N"` 锚求和；次选 adr/0002 `codex#N` 标签计数；解析不出 → `None`（→ `section-not-found`）。

常量：`REASON_CODES`（6 枚举本地常量，`lens_metric_emit.py:9` `VERDICTS` 先例）、`VALID_MODES=("native","simulated")`、`SOURCE_FILES`。

退出码语义：`none` → stdout `none` + exit 0（可复用）；其余五码 → stdout `<code>` + exit 1（不可复用，reason 载 stdout）；坏输入 → stderr `[outside_voice_guard] FAIL: <原因>` + exit 1 + **无 stdout**（all-or-nothing）。消费方以 stdout(reason)/stderr(FAIL) 分流区别「有效非复用判定」与「坏输入崩溃」（对齐 spec.md Scenario line 45）。

## 六枚举各自的测试正例（可复现）

| reason_code | 触发条件 | 测试 |
|---|---|---|
| `none` | mode=native + 产物新于源 + codex 段可解析且 findings>0 | `test_none_reusable` / `test_cli_none_exit0` |
| `simulated-source` | mode=simulated | `test_simulated_source` / `test_cli_simulated_exit_nonzero_stdout` |
| `stale` | 产物 fs-mtime 早于源文件最大 mtime | `test_stale` / `test_specs_file_counts_as_source_stale` / `test_cli_stale_exit_nonzero` |
| `section-not-found` | 无 codex 段（或畸形/非 codex runner） | `test_section_not_found` / `test_malformed_codex_findings_section_not_found` / `test_claude_fallback_runner_not_codex` |
| `zero-findings` | codex 段可解析但 findings=0 | `test_zero_findings` |
| `file-missing` | 产物路径不存在 | `test_file_missing` / `test_cli_file_missing` |

按序判定证据：`test_simulated_precedes_stale`（来源先于新鲜度）、`test_stale_precedes_structure`（新鲜度先于结构）。新鲜度排除评审产物自身：`test_review_artifacts_excluded_from_freshness`（更新的 `spec-review-report.md` / `.outside-voice/` 不触发 stale）。codex#N 次选路径：`test_codex_hash_label_fallback`。

## fail-closed 路径

- 锚缺失 → `EmitError`：`test_anchor_missing_fail_closed`
- mode 非枚举（`adapted`）→ `EmitError`：`test_mode_non_enum_fail_closed` / CLI `test_cli_bad_input_fail_closed_stderr_no_stdout`（exit≠0 + stderr FAIL + 无 stdout + 无 Traceback）
- change_dir 缺失/无源文件 → `EmitError`：`test_change_dir_missing_fail_closed` / `test_change_dir_no_sources_fail_closed`

## 纯 stdlib / 无 subprocess / 无 git

`os` 与 `subprocess` **均不 import**（用 `pathlib.Path.stat().st_mtime` 直比 fs-mtime，无 fork/exec 通路）。静态断言（comment/docstring 安全，AST 级）：`test_no_subprocess_no_os_import_ast`（import 集不含 subprocess/os）+ `test_no_exec_tokens_in_source`（源无 os.system/popen/fork/exec/Popen/check_output/check_call）。断言用 AST import 检查而非裸子串，避开 docstring 含 "git"/"subprocess" 的子串陷阱（memory `gate-substring-detection-dogfood`）。

## 全套件结果

```
python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -W error -q
125 passed in 0.47s
```
（新增 25 用例 + 既有 tools 套件全绿、0 warning。）

烟测：对真实归档产物 `archive/2026-07-08-mlh-p5-parser-cleanup/gstack-review.md` 跑 → 输出 `stale`、exit 1、无崩溃（checkout 重置 mtime 使产物≈旧于源，design Risks 已声明 fail-safe 朝 stale·重跑只成本）。task 5.3 dogfood 由后续 ticket 承接。

## Concerns

- **real 产物 mode="adapted" 会 fail-closed**：归档里存在 `mode="adapted"`（如 `mlh-p5-gate-frontmatter`），非 `native|simulated` 枚举 → 本守卫按 spec 严格 fail-closed（EmitError/exit1/stderr FAIL）。这是 spec.md Scenario line 43-45 的既定行为（我们的锚，严格），非缺陷；但 task 4.1 接入 `sdflow-spec-review/SKILL.md` 时消费方须把「exit≠0 + stderr FAIL」正确当作「回落自跑 outside voice」处理，不能把 FAIL 误读为某个 reason_code。已在退出码语义（stdout/stderr 分流）与本报告显式点明，供 task 4 接入参考。
- **codex 段解析口径**：real native 产物用 `outside-voice v1 ... runner="codex" findings="N"` 锚承载 codex 条数（本实现主解析路径）；adr/0002 的 `codex#N` 文字标签在现存 real 数据中未见（作次选 best-effort 路径保留）。若上游 autoplan 未来改锚格式，best-effort fail-closed 到 `section-not-found`（触发回落，可接受退化方向，对齐 adr/0002:21）。
