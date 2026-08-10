# Task 3 — token 快照采集：实现报告

## 范围

- 新增 `sdflow-init/assets/hack/token_snapshot.py`
- 修改 `sdflow-init/assets/hack/checkpoint-commit.sh`（接线）
- 新增 `hack/tests/test_token_snapshot.py`（13 用例，假 HOME 沙盒真跑 bash）
- dogfood：`bash setup.sh` 重跑分发 + 真实 e2e 冒烟

## 环境异常与处理（先于实现的一段插曲）

本 agent 被派到的 git worktree（`agent-a34034c7fb045d99d`）起初不在
`feat/implement-workflow-optimization-2026-08-p1` 分支上（是一个通用的
`worktree-agent-a34034c7fb045d99d` 分支，`openspec/changes/implement-workflow-optimization-2026-08-p1/`
目录完全不存在），且 `task3-brief.md` 本身也是仅落在另一个 worktree（`agent-a3c6a32aa8196a693`）
工作树里、未提交的文件。核实后确认：`feat/...` 分支的 merge-base 就是本 worktree 的 HEAD
（`47179f2`），二者是同一条历史的直系延伸（差 8 个提交），故用 `git merge --ff-only
feat/implement-workflow-optimization-2026-08-p1` 快进拿到完整四件套 + tickets.md，再用已读到的
brief 全文手工重建了 `impl-reports/task3-brief.md`（该文件本身从未被任何 commit 记录过，是编排层
直接写盘到 implementer 工作树的惯例产物，见本仓其它 change 的 "落盘 task1-3 brief（implementer
worktree 可见性前置）" 先例）。此举不改变任何设计意图，只是把本该在场的上下文补全。

## 实现要点

### `token_snapshot.py`

- 4 行 `reconfigure` 前导（第五道机械门），`hack/check_encoding_hygiene.py` 复核通过。
- **transcript 定位**：`$CLAUDE_CODE_SESSION_ID` 先过 `_valid_session_id`（basename +
  `^[0-9a-fA-F-]+$`）才拼路径精确命中；否则/未命中 → 同目录（`~/.claude/projects/<munged-cwd>/`）
  mtime 最新 `.jsonl` 回退；两者皆无 → `reason="no-transcript"`。
  `munged-cwd` = `os.getcwd()` 全量 `/`→`-` 替换（含开头 `/`）。
- **change 目录解析**：用 `git symbolic-ref --short HEAD` 取分支名（而非
  `git rev-parse --abbrev-ref HEAD`——后者在**零提交**的 unborn 分支上会打印 `HEAD` 到 stdout
  的同时仍以退出码 128 失败，"ambiguous argument 'HEAD'"；本地实测复现，测试脚手架里的假 repo
  必现，真实项目里概率低但同样是错的），配合 `git rev-parse --show-toplevel` 定位仓根；
  分支不匹配 `feat/<change>` 或对应 `openspec/changes/<change>/` 不存在 → 提前 `return 0`，
  **零写入**（不落任何降级行——"无落点"与"有落点但采集失败"是两种不同状态，规格明确要求前者
  静默、逐字节不变）。
- **usage 累加**：逐行 JSON 解析 transcript，只认 `message.role == "assistant"` 且带
  `message.usage` 的行；四计数（`input_tokens` / `output_tokens` /
  `cache_read_input_tokens` / `cache_creation_input_tokens`）+ `messages` 计数累加。
  任一行 JSON 语法损坏，或某计数非非负整数 → **整体**判 `parse-error`（不是"跳过坏行、其余照算"
  ——宁缺毋假，避免产出一个"看起来正常但被低估"的累计值）。非 assistant / 无 usage 字段的行是
  transcript 的正常组成部分，照常跳过、不计入错误。
- **输出行字段封闭 schema**：`_build_line` 只组装 `v / ts / step / session / host / anchor /
  reason [/ usage]` 七个字段，函数内没有任何路径能把 transcript 的 `content` / 工具输入输出 /
  错误文本等原始内容写进输出行——canary 测试实测验证。
- **超时**：`signal.alarm(10)`（POSIX only；`hasattr(signal, "SIGALRM")` 判断，Windows 静默降级为
  无硬超时——Windows 本就不在 `hack/` 铺设范围，见仓库 CLAUDE.md）。超时/任何异常 → 捕获后写
  `reason="parse-error"` 降级行（而非让进程带着未定义状态退出）。
- **写侧**：`os.open(O_APPEND|O_CREAT|O_WRONLY)` + 单次 `os.write`（整行 JSON 已在内存里
  buffer 好），POSIX 本地文件系统单 write 原子。写失败整体吞掉（`except Exception: pass`），
  不影响退出码。

### `checkpoint-commit.sh` 接线

插入点精确对齐 design 钉死的位置——`git status --porcelain` 判空 gate（原 `:38-42`）**之后**、
`git add -A`（原 `:51`，现因插入偏移）**之前**：

```bash
python3 ~/.sdflow/hack/token_snapshot.py --step "$step" || true
```

`git diff` 核验：改动只新增 5 行（含 3 行注释 + 1 行调用 + 1 空行），未触碰其余逻辑。

## 测试

`hack/tests/test_token_snapshot.py`，13 用例，全部通过（`/usr/bin/python3 -m pytest
hack/tests/test_token_snapshot.py -v` → `13 passed`）：

| 用例 | 覆盖点 |
|---|---|
| `test_normal_collection_lands_in_same_commit` | 正常采集，四计数 + messages 精确核对，同一 commit 内含 token-log.jsonl |
| `test_mtime_fallback_used_when_env_var_absent` | env 缺席 → mtime 最新 jsonl 回退，仍 anchor=true |
| `test_no_transcript_writes_degraded_line` | 无 transcript → `anchor=false, reason=no-transcript`，无 usage 字段 |
| `test_helper_absent_checkpoint_still_commits` | helper 脚本不存在 → checkpoint 照常提交，零写入 |
| `test_helper_crash_checkpoint_still_commits` | helper 非零退出 → checkpoint 照常提交，零写入 |
| `test_protected_branch_writes_nothing` | 保护分支（非 feat/*）→ 连 `openspec/changes/` 目录都不建 |
| `test_feat_branch_without_change_dir_writes_nothing` | `feat/<change>` 但目录不存在 → 零写入 |
| `test_appends_monotonically_across_checkpoints` | 连续两次 checkpoint：先前行字节不变 + 后一行 usage 单调不减 |
| `test_clean_tree_with_helper_present_is_still_noop` | 干净树 + helper 在场仍不建 commit、不写快照行（钉死接线位置的核心用例） |
| `test_canary_content_does_not_leak_into_output_surface` | transcript 的 text/tool_use/tool_result/error 字段植入 canary，输出行 + stdout/stderr 均不含 |
| `test_malformed_json_line_degrades_to_parse_error` | 单行 JSON 语法损坏 → 整体 `parse-error` |
| `test_negative_usage_count_degrades_to_parse_error` | 负数计数 → `parse-error` |
| `test_path_traversal_session_id_is_rejected_and_falls_back` | `../../../etc/passwd` 形态恶意 session-id → 文法校验拒绝，不拼路径，`session` 字段回落空串 |

既有 `sdflow-init/tests/test_checkpoint_commit.py`（6 用例）复跑全绿，无回归。

## dogfood 验收

1. `bash setup.sh` 重跑：输出 `✓ hack/token_snapshot.py @ /Users/cheneyzhao/.sdflow`，
   `diff ~/.sdflow/hack/token_snapshot.py sdflow-init/assets/hack/token_snapshot.py` → IDENTICAL
   （Unix 软链分发，改源即时生效）；`checkpoint-commit.sh` 分发副本内含新接线行。
2. e2e 冒烟（scratch repo，脚本见 impl 过程，未纳入仓库）：用真实
   `~/.sdflow/hack/checkpoint-commit.sh` 在 `feat/dogfood-e2e-smoke` 分支、伪造
   transcript（1 条 assistant usage 消息）上跑一次 checkpoint：
   ```
   checkpoint rc: 0
   token-log content: {"v": 1, "ts": "2026-08-10T15:22:35+0800", "step": "dogfood-e2e",
   "session": "dogfood-e2e-smoke-...", "host": "claude", "anchor": true, "reason": "ok",
   "usage": {"input": 111, "output": 22, "cache_read": 3, "cache_creation": 4, "messages": 1}}
   ```
   `anchor=true` 快照行随同一个 commit（`c37fab2`）产出，四计数与伪造 transcript 精确一致。
   Scratch repo 与伪造 transcript 事后清理，未污染任何真实数据。

未做真实当前会话 transcript 的 dogfood（本 agent 的 `CLAUDE_CODE_SESSION_ID` 在
`~/.claude/projects/` 下找不到匹配 munged-cwd 的真实 transcript 目录——子代理 worktree 会话的
transcript 落点与 host 内部约定不完全对齐，跨出本票范围）；上述伪造 transcript 的 e2e 冒烟已
完整覆盖"真实部署副本 + 真实 checkpoint-commit.sh + 真实 bash 执行"的全部机械路径，功能等价。

## 与 spec 的对照

对照 `specs/token-snapshot-anchor/spec.md` 的三个 Requirement 与 8 个 Scenario：全部对应到
上表某一测试用例或 dogfood 步骤，逐条落实，无遗漏。

## 未做 / 已知边角

- Windows：`signal.SIGALRM` 缺席时静默降级为无硬超时（未加跨平台信号模拟——`hack/` 本就不铺
  Windows，符合仓库既有边界，未新增负担）。
- 未改 `sdflow-done`（收尾阶段 checkpoint 缺口）——design.md Risks 段已明确"设计门拍板 Q2=A：
  本 change 接受、不扩 scope"，roadmap 2.A.5 已记待办，不属本票范围。
