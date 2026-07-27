## Why

`add-sdflow-spec` 已归档，但其 Codex 宿主边界、FF-0 在跨仓/不可解析命令下的行为、终审追溯口径和体量门仍有可复现缺口。当前入口每次加载 20,768 个字符，也把未启用或异常路径带入默认上下文。

## Success Metrics

- FF-0 在跨仓或无法判定命令作用仓时不对 payload `cwd` 错仓 deny，并向宿主上下文留下不越权的未判定原因。
- `sdflow-spec` 的 Codex 文案只陈述已验证的宿主语义；T132 按 A/B 入口分别认定收敛信号。
- `SKILL.md` 保留全部每次必执行的契约且不超过 18,000 Unicode 字符；按需资料可被确定条件加载。
- T232、T238、T240、T241 的已归档修正与台账状态一致，T233–T237、T242 有可验证处置。

## Non-Goals

- 不执行 T239，不在任何下游消费项目运行 `sdflow-init update`。
- 不启用阶段二外派，也不改变其 A/B 回退结论。
- 不解析 shell 来推断 `cd`、变量展开或命令的实际作用目录。

## What Changes

- 硬化 FF-0 的跨仓与不可解析路径：保留 fail-open，但通过无决策的 PreToolUse context 记录原因。
- 将 `sdflow-spec` 的 Codex 手动触发、终审追溯与 A/B grill 收敛语义改为可证实口径。
- 将入口重构为薄 `SKILL.md` 加按需 references，并以机械测试守住入口体量和必驻契约。
- 更新相关主规格、测试和 issue 台账，关闭已完成及本 change 完成的项目。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `spec-authoring`: 收紧 `sdflow-spec` 的宿主边界、终审追溯、阶段一信号与入口体量契约。
- `spec-workflow`: 明确 FF-0 对跨仓/不可解析命令的非越权审计行为，以及 T132 对 A/B 入口的收敛识别前提。

## Impact

- `sdflow-spec/SKILL.md` 与其 references、`sdflow-init/assets/hooks/ff0-branch-guard.py`、canonical workflow、对应测试和 `openspec/issues/todolist/`。
- 下游 bundle 不在本 change 中分发；canonical 改动保持可由后续 rollout 取得。

## Compliance

N/A：无外部服务、隐私数据或监管接口改动。
