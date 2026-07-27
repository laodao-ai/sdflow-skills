# Task 1：FF-0 单一未判定审计

## 改动摘要

- FF-0 hook 只在完整匹配单条直接 literal 创建 grammar 时，才使用 payload `cwd` 执行既有三分支判定。
- 单调用未命中该 grammar 时统一输出 `command-unverifiable` 的无决策 `additionalContext`；删除 `undecided_reason`、动态 marker 与两套旧原因码分类。
- 保留多处可识别创建调用优先 deny 的 stacking 防护；同步 canonical workflow 与 `/sdflow-spec` 入口说明。

## RED / GREEN 证据

- RED：先把公共 PreToolUse stdin/stdout seam 的代表性非 direct 命令断言改为单一 `command-unverifiable`，并将 canonical 同步断言改为同一边界。旧实现执行 focused suite 后 19 failed、65 passed；失败输出仍含 `cwd-ambiguous` 或 `change-name-unparseable`。
- GREEN：最小实现后相同 focused suite 为 84 passed，直接 grammar 的空白、单双引号与单个 `--json` 变体仍走原三分支；`cd`、wrapper、compound、换行、decoy、变量、命令替换与 glob 均仅输出无决策审计。

## 命令与结果

```bash
uv run --with pytest pytest sdflow-init/tests/test_ff0_branch_guard.py hack/tests/test_canonical_entry_sync.py
```

结果：`84 passed in 4.83s`。

## 自审

- 验证审计 JSON 只含 `hookEventName` 与 `additionalContext`，没有 `permissionDecision`。
- 验证所有旧原因码、动态 marker 与分类器已从本票涉及的 hook、测试和两处叙述载体移除。
- 未修改 proposal、design、specs、tasks、superpowers-plan 或 spec-review-report；未勾验收框，未创建 checkpoint 标签。

## Concerns

- 无。本票仅运行 focused pytest；全量验证、全局 hook 安装同步与 checkpoint 由后续管线负责。
