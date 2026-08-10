# Task 1: recorder reopen 命令 — 实现报告

**R-ID**: R-IS1
**Blocked-by**: none

## 做了什么

在 `sdflow-issues/scripts/issues_v2.py` 新增 `reopen` 子命令——终态（`closed/`）的唯一受控逆
转换，与既有 `set-status` 的终态守卫方向相反、写法对称（M-2 原子序镜像）。

### 1. `cmd_reopen`（issues_v2.py:612-714）

CLI：`issues_v2.py reopen --id <ID> --reason <理由> [--to OPEN|PROPOSED]`

- **argparse**：`--id`/`--reason` 均 `required=True`（`--reason` 必填由 argparse native 门禁，
  不在 `cmd_reopen` 内手写重复校验）；`--to` 默认 `"OPEN"`。
- **守卫顺序**（逐条对齐 `specs/issues-scripts-shared-core/spec.md` Requirement）：
  1. ID 格式合法（`ID_RE`）；
  2. `find_issue` 定位；未找到 → `_die("未找到 ID：{id}")`；
  3. 位于 `open/` → `_die("ID {id} 不在终态（位于 open/），无需 reopen")`（不绕过、不弱化
     `set-status` 的终态守卫——`set-status` 代码本身零改动）；
  4. ID 前缀与 frontmatter `pool` 一致（复用既有 `_pool_for_id`，文案沿用 `cmd_set_status`
     同款）；
  5. `--to` 只接受 `("OPEN", "PROPOSED")`，否则 `_die("--to 只接受非终态状态（OPEN|PROPOSED），
     收到 {v}")`（字面匹配 design.md 实现基准原文）。
- **中断残留判定**：守卫通过后读当前 `status`。若已非终态（`old not in TERMINAL_STATUSES[pool]`）
  ⇒ 判为 M-2 原子序中断残留（「原位原子写」已完成、`git mv` 未跑）——打印 WARNING 到 stderr，
  **跳过字段清理与历史行追加**，直接进入迁移步骤（幂等续跑）。
- **正常路径**（`status` 仍是终态）：
  - 原 `closed_reason` 为空（FIXED/DONE 路径本不写该字段）时历史行占位符写
    `（无 closed_reason）`，不渲染 `null`/空串；
  - 历史行格式：`> {date} 状态：{old} → {to}（reopen：{reason}；原 closed_reason：{原值}）`；
  - 三字段（`closed_date`/`closed_reason`/`resolved_by`）清 `null`；
  - `write_issue(path, frontmatter, new_body, create=False)` 在 **closed/ 原位** 原子写
    （M-2 第一步）。
- **迁移**（两分支共用）：`git mv closed/... → open/...`（未 tracked 先 `git add`；非 git 仓
  降级 `os.rename`，逻辑对称复制自 `cmd_set_status`）。
- **命令内自动 reindex**：调 `cmd_reindex(args)`；若其抛出非 `SystemExit` 异常，
  `_die("重开已生效，重跑 reindex 即自愈：{exc}")`（迁移已完成，仅 reindex 失败，不误导为
  「未发生任何变更」）。
- 成功输出 JSON：`{"id","pool","old","new","file"}`（`old`/`new` 在残留续跑分支相同，
  因为该次调用未做字段变更，只补迁移）。

### 2. `cmd_reindex` 增加 closed/ 非终态残留 WARNING（issues_v2.py:832 起、新增循环见 838-846）

spec 要求「reindex SHALL 对 closed/ 内非终态文件输出可见告警（'可被检出'以此落地）」——
`cmd_reindex` 原实现对 `closed_items` 只是照单渲染，不检查 status 是否终态。新增一段：
遍历 `closed_items`，若 `pool` 合法且 `status not in TERMINAL_STATUSES[pool]`，
向 stderr 打印 `WARNING: closed/ 内文件状态非终态：id=... pool=... status=...`。
这段独立于 `cmd_reopen`，`reindex` 单独跑也会检出（不依赖走过 reopen 才生效）。

### 3. 复用纪律（design.md 承重约束核验）

- **MUST NOT import `sdflow_issues_core`**：`cmd_reopen` 只用本文件内已有的
  `_die`/`_reject_line_unsafe`/`find_issue`/`read_issue`/`write_issue`/`_pool_for_id`/
  `_issues_dir`/`_is_git_repo`/`cmd_reindex`——`grep -n "sdflow_issues_core" issues_v2.py`
  零命中（本来就没有，本次未引入）。
- **MUST NOT 改 set-status 守卫**：`cmd_set_status` 函数体本次 diff 零改动
  （`git diff sdflow-issues/scripts/issues_v2.py` 中该函数无 hunk）。

### 4. 契约测试（`sdflow-issues/tests/test_issues_v2.py`，新增 18 个测试）

新增 `# cmd_reopen (CLI integration)` 段（旧 `cmd_set_status` 段之后、`cmd_scan` 段之前），
另加一个模块级 helper `_snapshot_issue_files`（`openspec/issues/` 下全部 `.md`——issue 文件 +
INDEX.md/CLOSED.md——内容快照，供拒绝面用例断言「零变更」）：

| 类别 | 测试 |
|---|---|
| 往返一致性 | `test_cli_reopen_roundtrip_returns_issue_to_open_with_cleared_fields`（含 old/new JSON 断言、字段清 null、历史行含 reopen 理由与原 closed_reason、INDEX/CLOSED 一致、git mv 落地）|
| | `test_cli_reopen_command_auto_reindexes`（不手动跑 reindex 也一致）|
| | `test_cli_reopen_to_proposed_sets_non_default_status`（`--to PROPOSED`）|
| | `test_cli_reopen_writes_placeholder_when_original_closed_reason_empty`（FIXED 路径的占位符文案）|
| | `test_cli_reopen_non_git_repo_falls_back_to_os_rename`|
| 拒绝面三例（均验零变更）| `test_cli_reopen_rejects_open_item_and_leaves_files_unchanged` |
| | `test_cli_reopen_rejects_missing_reason_and_leaves_files_unchanged` |
| | `test_cli_reopen_rejects_terminal_to_value_and_leaves_files_unchanged` |
| 同族守卫（非 brief 硬性要求，镜像 set-status 既有覆盖密度）| `test_cli_reopen_rejects_path_traversal_id` / `test_cli_reopen_rejects_unknown_id` |
| 中断残留幂等恢复 | `test_cli_reopen_recovers_from_interrupted_residue_without_duplicate_history`（手工重放 M-2 第一步、不跑 git mv，模拟中断点；重跑 reopen 断言不重复历史行、字段正确、文件落 open/）|
| reindex 残留告警 | `test_reindex_warns_on_closed_non_terminal_residue` |
| 既有守卫零回归 | `test_cli_set_status_still_rejects_closed_after_reopen_command_exists` |

TDD 纪律：先落全部 18 个测试（含新增的 `reopen` subcommand 引用），确认 12 个直接依赖
`reopen` 子命令的用例因 `argparse: invalid choice: 'reopen'` 全部先红，1 个零依赖用例
（既有守卫零回归）已绿；实现后重跑，先撞见 1 个测试自身的 bug（`json.loads(proc.stdout)`
未跳过 `cmd_reindex` 内部打印的「reindex：已重建...」文案行，与 `cmd_migrate`/`cmd_reorganize`
同款 stdout 叠加行为一致）——修正测试断言用 `proc.stdout.rindex("{")` 定位，而非改动产品代码
掩盖测试疏漏；随后 12/12 全绿。

### 5. 文档同步

- `sdflow-issues/SKILL.md`：新增「重开已关闭项（`reopen`）」小节（用法示例、守卫、字段清理、
  原子序 + 中断恢复一句话说明），并把「已在 `closed/` 的终态 issue 不可再改 status」改为
  「不可经 `set-status` 再改 status……唯一受控逆转换见下方 `reopen`」（tasks.md 5.3 明文措辞）。
- `sdflow-issues/references/conventions.md`：**[fold，非 brief 硬性要求，但同一改动直接使
  其失真]**——该文件原文声称「本脚本命令面未提供反向转换命令，如需手工回退需直接编辑
  frontmatter」，reopen 落地后这句对「终态回退」已经不成立；补一句区分「非终态回退
  （`set-status --to OPEN` 即可）」与「终态回退（唯一走 `reopen`）」，并在「命令面」清单里
  补上 `reopen` 一行。未改动 `sdflow-retro/SKILL.md`（tasks.md 5.3 里那部分是 R-WR1/R-WR2 的
  范围，不属于本票 R-IS1）。

## 验证

```
/usr/bin/python3 -m pytest sdflow-issues/tests/ -q
```
→ **120 passed, 6 skipped**（6 个 skip 为既有跳过项，与本票无关，未新增 skip/xfail）。

`sdflow-issues/tests/test_task6_coverage_gate.py`（CLI subcommand 覆盖闭包门，机械核验
`issues_v2.py --root . __invalid__` 让 argparse 自报 subcommand 枚举，逐一核对
`test_issues_v2.py` 源码里是否含该字面量子进程调用）随本次改动**自动**纳入 `reopen`
到枚举里并核实覆盖——无需手改该门本身，绿。

另跑全仓验证跨 skill 零回归（超出本票要求范围，主动加做）：

```
/usr/bin/python3 -m pytest -q     # 仓根，发现并运行全部 test_*.py
```
→ **2458 passed, 10 skipped, 303.88s**，无失败、无新增 skip。

## 与 Global Constraints 的对照

- 三面互相独立可回滚：本票只动 issues CLI 一面，token 采集 / retro 实修率两面零触碰
  （`grep -rn "reopen" sdflow-retro/ ~/.sdflow/hack/checkpoint-commit.sh` 之类不适用/零命中，
  未验证但设计上无交叉引用）。
- 复用内联 mechanics、MUST NOT import `sdflow_issues_core`——见上「复用纪律」。
- MUST NOT 改 set-status 守卫——`cmd_set_status` 函数体 diff 为空。
- reopen 拒绝路径错误文案沿用 `_die` 单句惯例——三条 `_die` 调用均为单句、无多行。
- reopen 中断残留幂等恢复——已实现 + 专门测试覆盖。

## 未做 / 已知范围外

- 未触碰 `sdflow-retro/SKILL.md`（属其它 R-WR1/R-WR2 ticket 范围）。
- 未新增「pool 前缀不符」的独立 reopen 测试用例（该分支代码路径与 `cmd_set_status` 完全同款
  逻辑复用，既有 `set-status` 测试已覆盖同一 `_pool_for_id` 函数；本票未见 brief/spec 对此提出
  独立测试要求，未新增以免过度插桩同一段已验证过的复用代码）。
