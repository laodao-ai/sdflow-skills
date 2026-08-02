# Task 2: reindex 总项数只增不减守卫 — impl-report

## 改了什么

`sdflow-issues/scripts/issues.py`：

1. 新增 `_INDEX_OPEN_ROW_RE` / `_INDEX_CLOSED_SUMMARY_RE` 两个模块级正则 + `_count_index_items(index_path)` 函数（`_reindex_core` 之前）：
   - open：数 `_render_item_table` 渲染出的数据行（`^\|\s*[A-Z]\d+\s*\|`）——表头 `| ID | Pool | ... |`、分隔行 `|----|...` 均不匹配该模式，不会误计。
   - closed：`generate_index_md` 无条件写出的「共 N 项已闭合」聚合行（哪怕 N=0 也写），正则未命中即视为该文件不是本工具生成的合法 INDEX.md。
   - 文件不存在（`OSError`）或 closed 聚合行缺失 → 返回 0（"无旧基线"，守卫据此跳过校验）。
2. `_reindex_core` 写盘前调用 `_count_index_items(index_path)` 取旧总项数，与本次 `len(items)` 比较：`old_count > 0 and new_count < old_count` → `raise ReindexStageError("count-guard", ...)`，在 `atomic_write` **之前**拒绝覆盖（旧 INDEX.md 原样保留）。
3. `cmd_reindex` 已有的 `except RuntimeError as e: _die(str(e))` 无需改动——`ReindexStageError` 本就是 `RuntimeError` 子类，天然被现有捕获路径覆盖；`cmd_batch_rename` 经既有 `except ReindexStageError as exc: raise _rename_recovery_error(exc.stage, ...)` 路径同样自然覆盖新 `"count-guard"` stage。

`sdflow-issues/tests/test_issues.py`：新增两个测试类（插在 `TestReindexGeneratesIndexMd` 与既有 `TestReindexProblemsEcho` 之间）：

- `TestCountIndexItems`（5 个用例）：文件不存在返回 0、closed 聚合行缺失返回 0（格式损坏跳过校验）、open+closed 求和正确、open=0 时 closed 仍计入、表头/分隔行不误计。
- `TestReindexCountGuard`（4 个用例，对齐 brief 验收标准 3–6）：
  - 旧 INDEX 有 3 项、新扫描降到 1 项 → CLI 非零退出 + INDEX.md 字节级未变。
  - 旧 INDEX 只有 closed 项（open=0, closed=2）、新扫描丢了 closed 项 → 同上。
  - 首次建（旧文件不存在）→ 正常写入、不触发守卫。
  - 旧 INDEX 格式损坏（非本工具生成、无聚合行）→ `_count_index_items` 返回 0，reindex 照常重建覆盖。

## TDD 过程

先写 9 个测试（对着尚未实现的 `_count_index_items`/守卫断言），确认全部落在预期失败集合内：临时 `git stash` 掉 `issues.py` 的改动重跑，7/9 因 `AttributeError: module 'issues' has no attribute '_count_index_items'` 或守卫未生效而红（另 2 个是"不应触发守卫"的场景，逻辑上无论有没有实现都应为绿，属正常）。恢复实现后 9/9 转绿。

## 验证

| 层 | 命令 | 退出码 | SHA |
|---|---|---|---|
| unit | `/usr/bin/python3 -m pytest sdflow-issues/tests/ -x -v` | 0（680 passed, 7 skipped, 3 xfailed） | badfa5fb1656b3616783c170ca4f8be92927a044 |

## 备注（环境）

本次实现在 worktree `agent-a621597c61e094214` 内完成，该 worktree 的分支 `worktree-agent-a621597c61e094214` 基于提交 `badfa5f`（早于 `feat/harden-issues-read-write` 分支创建之前），worktree 内原本不存在 `openspec/changes/harden-issues-read-write/` 目录（只有委派 prompt 指向的 `impl-reports/task2-brief.md` 在主检出目录 `/Users/cheneyzhao/Documents/04-sdflow-skills/openspec/changes/harden-issues-read-write/` 下可读到）。已确认 `sdflow-issues/scripts/issues.py` 与 `sdflow_issues_core/__init__.py`（`ReindexStageError` 等既有基础设施）在本 worktree 内与主检出目录内容一致（Task 1 的前置依赖——跨池 read、`generate_index_md`、`ReindexStageError`——均已就地存在），因此本任务的实现与测试改动直接落在本 worktree 内进行；本 impl-report 按委派指令的相对路径写在本 worktree 下，未改动主检出目录。合并/落地该改动到 `feat/harden-issues-read-write` 分支需由上游编排方处理（本子代理无权跨 worktree 操作）。
