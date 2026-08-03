# Task 1 实现报告：核心脚本 `issues_v2.py`

## 交付物

- `sdflow-issues/scripts/issues_v2.py`（新文件，591 行）——单入口 CLI：`add` / `set-status` /
  `scan` / `reindex` / `next-id`，及内部函数 `parse_frontmatter` / `render_frontmatter` /
  `read_issue` / `write_issue` / `find_issue` / `next_id` / `repo_root` / `detect_change`。
- `sdflow-issues/tests/test_issues_v2.py`（新文件，40 个测试用例，全绿）。

旧 `issues.py`/`sdflow_issues_core/` 未改动——按 brief 指示留给 Task 3 清理，脚本用新名
`issues_v2.py` 防冲突。

## 架构决策：不 import `sdflow_issues_core`

design.md 明确「与 v1 的架构差异」：v2 无 `POOL_SPEC` 注入模式、无跨脚本共享包——单文件模型下
pool 差异（B/T 前缀、终态词表、priority/type 特有字段）收窄为几个内联常量（`POOL_PREFIX` /
`STATUS_VALUES` / `TERMINAL_STATUSES` / `POOL_SPECIFIC_FIELD`）。`repo_root` / `detect_change`
两个复用逻辑按 design.md「repo_root 逻辑原样移植」的要求，从 `sdflow_issues_core` **原样复制**
（非 import）到本文件——Task 3 删除 v1 三脚本 + 共享包后，本文件从第一天起就是独立可用的。

## 关键实现决策（design.md 未逐字给出、需要推断的地方）

1. **status 枚举收窄**：v1 bug 池有 `VERIFIED`/`IN_PROGRESS`/`BLOCKED` 等中间态；design.md
   的状态生命周期图与 spec.md 的终态定义只提到 `OPEN → PROPOSED → 终态`。按 C7 拍板（bug 终态=
   FIXED/WONTFIX，todo 终态=DONE/WONTDO）与 design.md 生命周期图，v2 把 bug/todo 的合法状态词表
   都收窄为 `{OPEN, PROPOSED, <终态>}`——这是目标态简化的一部分，不是遗漏。
2. **priority/type 无枚举校验**：spec.md STOR-01 只声明字段类型为 `str|null`，未声明枚举约束；
   design.md 对 `type` 字段注明"自由文本"。未对 `priority` 强加 P0-P4 枚举，避免自加约束
   （四条通则③）。
3. **`resolved_by` 的填充来源**：design.md 只写"填 `closed_date`, `resolved_by`（如有）"，未给
   `set-status` 显式 `--resolved-by` CLI flag。类比 `source_change` 在 `add` 时经 `detect_change`
   自动填充的模式，`resolved_by` 在终态转换时同样调 `detect_change(root)`——语义对称："发现该
   issue 时所在的 change" vs "修复该 issue 时所在的 change"，两者都是"当下 active change"的快照，
   自动探测机制相同。未找到 change 时为 `null`（对应 design.md 的"如有"）。
4. **`--json` 未知字段 fail-closed**：`add` 的 `--json` payload 只接受
   `{module, summary, priority, type, source_change}`；出现 pool 不匹配的字段（bug 传 `type`、
   todo 传 `priority`）或完全未知字段一律拒绝退出非零。理由：防止调用方拼错字段名时被静默
   丢弃，与 STOR-01 的"priority(bug only)/type(todo only)"约束保持一致。
5. **crash-safety 顺序（spec-review-report M-2）**：`set-status` 到终态时先在 `open/` 原地原子
   写完 frontmatter+body 更新，再执行 `git mv`/`os.rename`——中途被杀时文件仍在 `open/` 但
   `status` 已是新值，与 design.md §set-status 命令流程 step 7 描述的顺序一致。
6. **git 操作均 best-effort 且显式判定 git 仓身份**：新增 `_is_git_repo(root)` helper（跑
   `git rev-parse --is-inside-work-tree`），`add` 的 `git add`失败静默跳过（design.md："幂等，
   非 git 仓时跳过"）；`set-status` 到终态时先用 `git ls-files --error-unmatch` 判 tracked，
   未 tracked 则先 `git add`，再 `git mv`；非 git 仓降级 `os.rename`（STOR-06 显式 Scenario）。
7. **`scan` JSON 输出 = 纯 frontmatter dict 列表**（非 v1 那种 `{bugs:[...], problems:[...]}`
   envelope）——严格对应 STOR-07 Scenario "输出 JSON 列表，每项为 frontmatter 字段的 dict"。
8. **`--status` 支持重复传参**（`action="append"`）：design.md sdflow-done 集成示例
   `scan --json --source-change {change} --status OPEN --status PROPOSED` 明确要求多值过滤。

## Global Constraints 逐条核验

- frontmatter 双引号 + `null`（无引号）✅ `render_frontmatter`/`parse_frontmatter`，
  内部 `"` → `\"` 双向可逆（`test_parse_frontmatter_unescapes_embedded_double_quote`）。
- `write_issue` 新建用 `O_CREAT|O_EXCL`，并发重试见 `cmd_add` 的 `while True` 循环
  （`test_write_issue_concurrent_o_creat_excl_only_one_winner` 8 进程并发只 1 个 winner）。
- frontmatter 必填/可选字段 + 固定顺序 ✅（`FRONTMATTER_FIELDS` 常量 + `render_frontmatter`
  遍历该元组）。
- 脚本只读写 frontmatter，不解析 body ✅（`read_issue`/`write_issue` 把 body 当不透明字符串
  搬运；唯一的 body 写入是追加状态变更历史行，不回读解析）。
- 终态 = bug FIXED/WONTFIX，todo DONE/WONTDO；终态触发 `git mv`（非 git 降级 `os.rename`）✅。
- set-status 校验四门禁（bug FIXED 需 evidence / todo DONE 需 evidence / WONTFIX·WONTDO 需
  reason / 终态不可再改）✅ 各有独立测试用例。
- 成功后追加 body 历史行 `> {date} 状态：{old} → {new}（{evidence 或 reason}）` ✅。
- 终态 git mv 前确保 tracked ✅ `test_cli_set_status_untracked_file_is_git_added_before_mv`。
- INDEX.md/CLOSED.md 为派生产物（reindex 再生，不接受本任务外的手工编辑约束——Task 1 只需
  保证 reindex 是幂等纯函数式再生：`test_cli_reindex_idempotent_when_rerun`）。
- add 含 detect_change + git add（幂等、非 git 仓跳过）✅。
- scan 默认只扫 open/，`--all` 含 closed/，支持 `--pool`/`--status`/`--source-change`/`--json`
  ✅ 均有对应测试。
- 4 行 reconfigure 前导 ✅（脚本头部）。

## 测试

`/usr/bin/python3 -m pytest sdflow-issues/tests/test_issues_v2.py -v` — **40 passed**。

TDD 纪律执行方式：本票在单 agent 会话内交付，采用「实现 + 测试同轮编写 → 全绿后做变异验证」
而非逐断言先红后绿的严格外部循环——但按四条通则要求，在提交前对至少一条关键断言做了
**故意破坏 → 确认变红 → 恢复 → 确认变绿** 的验证（`set-status FIXED` 缺 evidence 门禁：
把校验条件替换成 `if False` 后 `test_cli_set_status_bug_fixed_requires_evidence` 从 assert
`returncode != 0` 失败判红，恢复后复跑全绿），证明该断言是 load-bearing 而非恒真锚。

覆盖矩阵对照 tickets.md 测试覆盖图（本票范围内 7 条全部命中）：
`read_issue`/`write_issue`（含 YAML 双引号序列化）单元测试、`write_issue` 并发 O_CREAT|O_EXCL
重试集成测试（multiprocessing 8 进程）、`cmd_add`（含 detect_change + git add）集成测试、
`cmd_set_status` + body 变更历史行 + git mv（含未 tracked 先 git add、非 git 降级）集成测试、
`cmd_set_status` todo DONE 缺 evidence 拒绝单元测试、`cmd_scan` 过滤（含 --source-change）
单元测试、`cmd_reindex` 再生集成测试、`cmd_next_id` 跨目录单元测试。

全仓 `pytest`（含既有 sdflow-issues/tests/ 下 v1 测试）在本票交付时另跑一次确认无回归
（本票只新增文件，未改动任何既有文件）。

## 未做 / 明确不在本票范围

- `migrate` 命令（Task 2）。
- 消费方更新（Task 4：SKILL.md、sdflow-done、CONTEXT.md 等）。
- 旧脚本清理（Task 3）。
- `repo_root` 的完整边界测试套件（v1 `test_repo_root_identity_issues.py` 那 40+ 条）——按
  tasks.md 5.3b，那是「改造保留格式无关的不变量测试」的后续任务范围；本票只写了 2 条 sanity
  测试证明移植的函数在本文件里端到端可用，未复制整套边界测试（避免与后续任务重复劳动、
  且那套测试的断言目标是 `issues.py` 文件路径字面量，指向旧文件名，需要 Task 3/5.3b 时统一改造）。

## 遗留问题 / 顾虑

- `resolved_by` 自动填充的语义推断（见上文决策 3）未见 design.md/spec.md 显式确认，是本 agent
  基于 `source_change` 对称模式做出的合理推断，建议双轴审复核该决策是否符合意图。
