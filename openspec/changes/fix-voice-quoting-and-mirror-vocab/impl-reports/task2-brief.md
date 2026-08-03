### Task 2: anchor_lint 枚举扩展 + 消费拷贝刷新

**Blocked-by:** none
**R-ID:** R2

`_FANOUT_MIRRORS` frozenset 加入 `"history"` token，同步 docstring 硬编码枚举，然后跑 `sdflow-init update` 刷新本仓消费拷贝。

- [ ] `anchor_lint.py:672` `_FANOUT_MIRRORS` 加 `"history"`
- [ ] `check_fanout_consistency()` docstring 的硬编码枚举同步更新
- [ ] 跑 `sdflow-init update` 刷新 `openspec/workflow/tools/anchor_lint.py`
- [ ] `_parse_mirrors("history")` 返回合法结果（非 unknown-token）
- [ ] 补 `test_anchor_lint.py` 功能测试：`history` token 接受 + `mirrors="domain,history"` 加 `subagents="unavailable"` 触发 `dead-fanout-multi-mirror`

