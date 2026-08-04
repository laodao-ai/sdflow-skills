### Task 3: T6 Codex 降级告警

**Blocked-by:** none
**R-ID:** —

`ensure_global_hooks()` 末尾检测 `~/.codex/` 存在时追加告警行，消除 Codex 会话下 branch-guard 静默不生效的信息盲区。告警文案弱化（CR-5）。

- [ ] `ensure_global_hooks()` 末尾检测 `os.path.isdir(~/.codex/)` 时追加告警行
- [ ] 测试：mock `~/.codex/` 存在，验证输出含 `⚠` 告警；不存在时无告警

