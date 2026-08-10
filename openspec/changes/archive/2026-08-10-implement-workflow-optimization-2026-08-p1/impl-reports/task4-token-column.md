# Task 4 — retro token 列渲染：实现报告

## 范围

`sdflow-retro/scripts/retro_report.py` 新增 token-log.jsonl 读取 + 全局 session 跨 change Δ
归属计算 + per-change 表 tokens 列渲染（对应 tickets.md Task 4 全部 3 项：4.1 读取/Δ 归属、
4.2 列渲染、4.3 测试）。

## 4.1 token-log 读取与 Δ 归属计算

新增函数：

- `_parse_token_log_line(raw_line)` — 单行 JSON → 规范化 dict 或 `None`（等价 anchor=false，
  逐行跳过不抛）。只接受 `anchor is True`、`session`/`step` 非空字符串、`ts` 可解析、
  `usage` 四计数（input/output/cache_read/cache_creation）均为非负整数的行；其余（降级行、
  坏 JSON、截断半行、字段缺失/类型错、负值）一律判无效。
  **`ts` 用 `datetime.strptime(...,"%z")` 而非 `datetime.fromisoformat`**——真实生产者
  `token_snapshot.py` 用 `time.strftime("%Y-%m-%dT%H:%M:%S%z")` 产出「无冒号」偏移量
  （如 `+0800`），本仓当前活动 change 目录下真实存在的 `token-log.jsonl`（task3 已产出）
  实测证实该格式；`fromisoformat` 在本机 Python 3.9 上对此格式直接抛异常，若用它会把
  **全部真实数据**误判 anchor=false（静默丢失全部计数，且任何自造 `+08:00` 形态的合成
  测试语料都测不出——是在读真实文件时才发现的坑）。`strptime("%z")` 原生兼容两种偏移写法。
- `read_token_log(path)` — 读单个文件，逐行防御解析；文件缺失/IO 错误 → 空列表，不崩、
  不中断调用方。
- `compute_token_deltas(root, changes)` — 全局 Δ 归属：先按 change 名升序扫全部 change
  目录（`active_dir` + `archive_dir`）的 token-log.jsonl 读入全部合法行，按 `session`
  全局分组；组内全体行按 `ts` 稳定排序（同 ts 保留扫描顺序，即 change 名升序 + 文件内
  追加序，tie-break 确定性）；组内首行（该 session 全局最早合法行）全额计入其所在
  change，其余每行对紧邻前一行差分（Δ 负值钳 0，防御 usage 非严格单调场景）、归属自身
  所在 change。**跨 change 同 session 不双计数**（设计门 Q1=A）是此排序机制的自然结果：
  两个文件的行按 ts 排序后在时间线上自然相邻，无需额外的「文件边界」特判——B 文件首行
  紧邻 A 文件末行，天然对 A 末行差分。返回 dict 只含 ≥1 贡献行的 change（无 token-log
  的 change 不在 dict 中，调用方据此渲染「—」）。

## 4.2 per-change tokens 列渲染

- `_fmt_compact_count(n)` — 紧凑计数：≥1M 显 `X.XM`，≥1k 显 `X.Xk`（去掉多余 `.0`，如
  89000→`89k` 非 `89.0k`），否则原样整数。
- `format_tokens_cell(d)` — `out {..} / in {..} / cc {..} / cr {..}` 四计数紧凑串，
  MUST NOT 合成总分；`d` 为 `None`/空 dict → `"—"`。
- `build_report()` per-change 表新增 `tokens` 列（插在 `独立Σ` 与 `状态` 之间），恒附
  脚注 `_TOKEN_FOOTNOTE`：「tokens 列：数值为各会话累计口径聚合，tickets 管线下多为
  独立短会话的首行全额之和，非严格阶段增量。」（无条件追加，同 `surfacing_block`/
  hr-tg 空箱惯例——不可见即等于死列）。

## 4.3 测试

`sdflow-retro/scripts/tests/test_retro_report.py` 新增 18 个用例：

| 用例 | 覆盖点 |
|---|---|
| `test_parse_token_log_line_no_colon_offset_matches_real_producer_format` | **载荷用例**：真实生产者「无冒号」`+0800` 偏移量必须能解析（及 `+08:00` 兼容） |
| `test_parse_token_log_line_rejects_anchor_false` | anchor=false 行判无效 |
| `test_parse_token_log_line_rejects_negative_usage` | usage 负值判无效 |
| `test_parse_token_log_line_rejects_malformed_json` | 坏 JSON 判无效 |
| `test_read_token_log_missing_file_returns_empty` | 缺文件 → 空列表不崩 |
| `test_read_token_log_skips_corrupted_and_degraded_lines_without_crashing` | 混合截断行/坏JSON/降级行/负值行/合法行，只保留合法行 |
| `test_compute_token_deltas_single_change_first_row_full_then_delta` | 单 change 内首行全额+Δ |
| `test_compute_token_deltas_cross_change_session_no_double_count` | **载荷用例**：跨 change 同 session 不双计数，双方之和=末次累计值 |
| `test_compute_token_deltas_anchor_false_rows_excluded` | 降级行不入计数，不打断"首行全额"判定 |
| `test_compute_token_deltas_missing_token_log_no_entry` | 无 token-log 的 change 不在返回 dict 中 |
| `test_compute_token_deltas_multiple_sessions_independent` | 多 session 互不干扰、各自求和 |
| `test_compute_token_deltas_reads_archive_dir_too` | 归档 change（只有 `archive_dir`）同样能读到 |
| `test_fmt_compact_count` | 紧凑格式边界（500/12.3k/4.5k/89k/1.2M） |
| `test_format_tokens_cell_examples` | 渲染串精确匹配 design 示例；`None`/`{}` → `—` |
| `test_build_report_tokens_column_and_footnote` | 集成：表头+数据行+脚注三者俱在 |
| `test_build_report_tokens_dash_when_no_token_log` | 存量 change 无 token-log → tokens 列显式「—」（区分聚合②同前缀行的定位技巧：按行尾状态列锚定） |
| `test_token_deltas_real_repo_smoke_no_crash` | **全仓再生冒烟**：真仓 `compute_token_deltas` 对 active+archive 全部 change 跑通不崩，四计数均非负整数 |
| `test_build_report_real_repo_tokens_column_smoke` | **全仓再生冒烟**：`build_report(真仓)` 含 tokens 表头+脚注 |

## 验证结果

```
/usr/bin/python3 -m pytest sdflow-retro/scripts/tests/ -q
128 passed

/usr/bin/python3 -m pytest -q   （全仓）
2513 passed, 10 skipped in 350.33s
```

新增 18 个测试全部通过，既有 110 个 sdflow-retro 测试与全仓其余测试零回归。

## 与 spec 的对照

对照 `specs/workflow-retro/spec.md`「per-change token 维 join」Requirement 的 5 个
Scenario：全部对应到上表某一测试用例，逐条落实，无遗漏——
「有锚 change 呈现四计数」→ `test_compute_token_deltas_single_change_...`；
「存量无锚 change 显式标注」→ `test_build_report_tokens_dash_when_no_token_log`；
「跨 change session 不双计数」→ `test_compute_token_deltas_cross_change_session_no_double_count`；
「降级行不入计数」→ `test_compute_token_deltas_anchor_false_rows_excluded`；
「损坏行不拖垮报告」→ `test_read_token_log_skips_corrupted_and_degraded_lines_without_crashing`
+ 全仓冒烟两例（真仓语料含真实数据，非纯合成）。

## 偏离/决策记录

- **ts 解析用 `strptime` 而非 `fromisoformat`**：brief 与 design.md 文档示例均手写
  `"2026-08-10T11:30:00+08:00"`（带冒号），但真实生产者 `token_snapshot.py` 用
  `time.strftime("%z")` 产出无冒号形态。本仓当前活动 change 目录（本 change 自身）
  已因 task3 落地产出真实 `token-log.jsonl`，读取时直接暴露此形态差异。属于「按目标态
  producer 实际产出校验」而非「按文档字面猜测」的基准③应用，非范围变更。
- **未修改 `openspec/retro/report.md`**：该 view-only 再生文件的提交是 tasks.md Task 5.1
  的职责（「全仓 pytest 绿 + report.md 再生提交」），不在本票（Task 4）范围内，遵循
  task2/task3 报告的既有先例（同一「留给 Task 5」的边界划分）。
- **tokens 列位置**：design/spec 未钉死列在表中的具体位置，落地选择「独立Σ 之后、状态
  之前」——紧邻其余度量列，状态列殿后收尾，与既有列序风格一致；不影响任何 Scenario 的
  可验证行为（值语义，非位置语义）。

## 未做 / 已知边角

无。Global Constraints 三项（不改 `lens_metric_aggregate.py` 签名 / 逐行防御解析 /
token 列不合成总分）与 TDD 纪律均已遵守，`git diff` 已核验改动范围精确限定在
`sdflow-retro/scripts/retro_report.py` 与其测试文件。
