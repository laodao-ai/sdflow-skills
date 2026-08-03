# Task 2 impl report — anchor_lint 枚举扩展 + 消费拷贝刷新

## 改动

- `sdflow-init/assets/workflow/tools/anchor_lint.py:672`
  `_FANOUT_MIRRORS = frozenset({"domain", "adversarial", "grounding"})`
  → `frozenset({"domain", "adversarial", "grounding", "history"})`。
- 同文件 `check_fanout_consistency()` docstring（约 L702）硬编码枚举同步：
  `∈{domain,adversarial,grounding}` → `∈{domain,adversarial,grounding,history}`。
- 跑 `python3 sdflow-init/scripts/init.py update --dev` 刷新本仓消费拷贝
  `openspec/workflow/tools/anchor_lint.py`（两处枚举与源一致）。
  该次 `--dev` 整刷同时带出两处**与本票无关的预存漂移**（`openspec/workflow/config.template.yaml`
  新增 `test-suites`/`operations` 段落说明、`Token_Saving_Strategies.md` 尾随空格规范化）——
  这是 bundle 整刷的既有机制副作用（源已比消费拷贝新），不是本票引入，未回滚。

## 测试

`sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 新增两条（紧邻既有
`test_fanout_unavailable_multi_mirror_blocked` 之后）：

- `test_parse_mirrors_history_token_valid`：直接单测 `_parse_mirrors("history")` →
  `(["history"], None)`，非 `unknown-token`。
- `test_fanout_unavailable_history_multi_mirror_blocked`：
  `mirrors="domain,history"` + `subagents="unavailable"` → 命中 `dead-fanout-multi-mirror`。

## 验证

```
/usr/bin/python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -q
```

143 passed / 2 failed（`test_yq_not_installed_fails_loud`、
`test_yq_identity_check_rejects_non_mikefarah`）。经 `git stash` 回退到改动前重跑同两条用例
确认**改动前已同样失败**（本机装的是 `kislyuk/yq` 而非 `mikefarah/yq`，环境问题，与本票无关）。

按 `-k "fanout or mirror"` 单独跑：29 passed，0 failed。

## MUST NOT 事项核对

未勾 `tasks.md`/`tickets.md` 验收复选框，未打 checkpoint 标签（该目录在本 worktree 不可见，见下）。

## 已知限制

本 agent 运行在 git worktree 隔离环境
（`/Users/cheneyzhao/Documents/04-sdflow-skills/.claude/worktrees/agent-a68de0084d0ac600e`），
该 change 目录（`proposal.md`/`design.md`/`tasks.md`/`tickets.md`/`decision-memo.md` 等）在共享
主 checkout 中处于**未 track 状态**，worktree 天然看不到未 track 文件——本报告及测试改动只落在
本 worktree 的文件系统里，需由上游编排把该 worktree 的产物合并回主 checkout。
