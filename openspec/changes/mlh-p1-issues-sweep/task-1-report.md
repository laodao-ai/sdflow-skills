# Task 1 报告 — `issues.py sweep` 原子子命令 + 测试

## 改了哪些文件

- `sdflow-issues/scripts/issues.py` — 新增 `cmd_sweep(args)` + `main()` 里注册 `sweep` 子命令
- `sdflow-issues/tests/test_issues.py` — 新增 `TestSweep` 测试类（7 个用例）+ 5 个测试 helper
  （`_run_sweep_raw` / `_run_sweep` / `_find_item_line` / `_item_cells` / `_item_status` / `_item_batch`）
- `openspec/changes/mlh-p1-issues-sweep/task-1-report.md`（本文件）

## `cmd_sweep` 关键实现

代码位置：`sdflow-issues/scripts/issues.py`，`cmd_sweep` 函数（`main()` 之前，新增的
"── sweep（Task 1，roadmap 阶段 1）──" 一节），`main()` 里 `sw = sub.add_parser("sweep", ...)` 注册。

**口径**：逐池调用 `{buglist.py|todolist.py} --root {root} scan --change {change} --open-ungrouped --json`
（源==change ∧ 非终态 ∧ 批次空，MUST NOT 用 `--status OPEN`——设计门 Q1=A 已拍板）。

**入口守卫（先于任何写盘）**：
```python
change = (args.change or "").strip()
if not change:
    _die("sweep --change 不可为空（防空 change 误纳孤儿）")
_reject_batch_key_unsafe(change)  # 拒 |/换行/ — /首尾空白
```
两道检查都在任何 subprocess 调用之前，双重覆盖（第一道给明确的空 change 错误文案，
第二道 `_reject_batch_key_unsafe` 复用既有函数覆盖 `|`/换行/em-dash/首尾空白）。

**全子步 subprocess CLI**：scan/triage/batch add/reindex 全部经 `subprocess.run([sys.executable, script, ...])`
调用完整 CLI（带全部必需参数），不直调 `cmd_batch_add`/`cmd_reindex` 等内部函数——避开
`getattr(args, "优先级")` 无默认值的 AttributeError 风险，以及 `_scan_pool` 硬编码
`scan --json`（无 `--change`/`--open-ungrouped` 过滤）的问题。

**逐项 triage fail-closed**：
```python
tagged = []
for script, pool, idkey in ((BUGLIST_SCRIPT,"bug","bugs"), (TODOLIST_SCRIPT,"todo","items")):
    ... scan ...
    for it in items:
        iid = it["id"]
        tp = subprocess.run([..., "triage", "--id", iid, "--批次", change], ...)
        if tp.returncode != 0:
            _die(f"sweep: triage 失败于 {pool} 第 {iid} 项 (rc={tp.returncode})；"
                 f"已 tag={tagged}: {tp.stderr.strip()}")
        tagged.append(iid)
```
每项查 returncode，非零立即 `_die`（打印 ERROR 到 stderr + `sys.exit(1)`），报文含
pool、失败的 id、已成功 tag 的 id 列表——满足"报明失败点位"的验收要求。

**幂等**：`batch add` 调用带 `--if-exists skip`（`ba = subprocess.run([..., "batch", "add", change, "--if-exists", "skip"], ...)`），
配合 triage 自身既有幂等（已 PROPOSED/终态 no-op）+ reindex 确定性重建，sweep 本身无状态、
可安全重跑。

**末步 reindex fail-closed**（区别于 `cmd_batch_rename` 的 warn-only）：
```python
ri = subprocess.run([sys.executable, __file__, "--root", root, "reindex"], ...)
if ri.returncode != 0:
    _die(f"sweep: reindex 失败 (rc={ri.returncode}): {ri.stderr.strip()}")
```

**subparser 注册**：`sweep` 只加 `--change`（required），未重复定义 `--root`——`--root` 是
顶层 `p.add_argument("--root", ...)` 已有的全局参数（与 `reindex`/`batch` 两个既有子命令
的写法一致，调用形态是 `issues.py --root X sweep --change Y`），比 plan 骨架里"每个子命令
各自加 `--root`"更贴合本文件既有约定。

## 每个测试的断言要点

1. **`test_sweep_open_ungrouped`**：源==X 的 OPEN（B1/T1）与非 OPEN 非终态（B2=IN_PROGRESS）
   项全部被纳入 triage → 批次=chg-x、状态=PROPOSED；batches.md 建条目、INDEX.md 刷新。
2. **`test_sweep_idempotent`**：同 change 连跑两次，第二次 rc==0，batches.md/INDEX.md
   两次输出逐字节相同（无净变化），批次条目不重复。
3. **`test_sweep_rejects_empty_change`**：`""`/`"   "`/`"a — b"`/`"a|b"`/`"a\nb"` 五种非法
   change 均 rc!=0 且 stderr 非空；孤儿项（源为空）状态/批次不受影响，batches.md 不被
   凭空创建。
4. **`test_sweep_excludes_orphans`**：合法非空 change 下，源为空的孤儿项因不匹配
   `--change` 过滤天然不被纳入（批次仍为空、状态不变）。
5. **`test_sweep_triage_fail_closed`**：monkeypatch `issues_mod.subprocess.run`，仅拦截
   `triage ... B2` 这一条命令伪造 rc=1，其余调用透传真实 `subprocess.run`；断言
   `cmd_sweep` 抛 `SystemExit`（非 0），stderr 同时含失败 id（B2）、pool（bug）、已 tag
   列表（B1）；B1 已落盘 tag，batches.md 尚未创建（还没跑到 batch add 步）。
6. **`test_sweep_rerun_converges`**：同样注入 B2 triage 失败 → 首次 sweep 失败、B1 已
   tag、B2 未 tag；移除注入后用真实 CLI 子进程（独立进程，天然不受父进程 monkeypatch
   影响）重跑 → 全部收敛 tag（B1/B2 批次=chg-g、状态=PROPOSED），batches.md 建成、
   INDEX 刷新。
7. **`test_sweep_reindex_fail_closed`**：monkeypatch 拦截含 `"reindex"` 的调用伪造
   rc=1，triage/batch add 正常执行；断言 sweep 仍以非 0 退出（fail-closed，区别于
   `cmd_batch_rename` auto-reindex 的 warn-only），stderr 含 "reindex"；此时 B1 已
   tag、batches.md 已建成（前面步骤的写盘不因末步失败而回滚，符合"非原子"设计）。

## `pytest sdflow-issues/tests/` 实际输出尾巴

```
........................................................................ [ 73%]
..........................                                               [100%]
98 passed in 8.84s
```
（基线 91 passed + 新增 7 passed = 98 passed，全绿）

TDD 验证：临时 `git stash` 掉 `issues.py` 的改动后单独跑 `TestSweep`，6/7 用例
以 `AttributeError: module 'issues' has no attribute 'cmd_sweep'`（或 argparse 报错）
失败，仅 `test_sweep_rejects_empty_change` 因"未知子命令"巧合触发非 0 退出而通过——
确认测试在实现前处于红灯状态，实现后全部转绿。

## Checkpoint commit

```
98f3a66 checkpoint(task1-sweep): issues.py sweep 原子子命令 + 守卫/幂等/孤儿/fail-closed/收敛测试
```
（3 files changed, 449 insertions(+)；分支 `feat/mlh-p1-issues-sweep`）

## Concerns

- 无 BLOCKED 项。唯一偏离 plan 骨架的地方是 `sweep` subparser 未重复定义 `--root`
  （沿用顶层全局参数，与 `reindex`/`batch` 现有写法一致），已在上文说明理由，不影响
  任何验收 Scenario。
