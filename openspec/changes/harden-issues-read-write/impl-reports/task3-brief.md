### Task 3: sweep 路径 triage 状态解耦 + 文档同步

**Blocked-by:** none
**R-ID:** R3

给 `_bug_triage` / `_todo_triage` 加 `promote` 参数（默认 `True`）。`promote=False` 时跳过 `open_untriaged` 推进逻辑（`new_status = old_status`）。`triage` CLI 子命令新增 `--batch-only` flag 映射到 `promote=False`。`cmd_sweep` 的子进程调用改为 `triage --batch-only`。SKILL.md 同步更新 triage/sweep 文档。

- [ ] `_bug_triage` 加 `promote` 参数（默认 True），`promote=False` 时 `new_status = old_status`
- [ ] `_todo_triage` 加 `promote` 参数（默认 True），`promote=False` 时 `new_status = old_status`
- [ ] `triage` CLI 新增 `--batch-only` flag → args 传递到 `_cmd_triage` → `promote=False`
- [ ] `cmd_sweep` 子进程调用改为 `triage --batch-only --id X --批次 Y`
- [ ] 测试：直接 triage OPEN 项（无 --batch-only）→ 断言 status 变为 PROPOSED（原行为不变）
- [ ] 测试：triage --batch-only OPEN 项 → 断言 status 仍为 OPEN + batch 已更新
- [ ] 测试：cmd_sweep 端到端 → 断言被 sweep 项 status 保持原样
- [ ] SKILL.md:495-496 triage 命令表：补充 `--batch-only` 说明
- [ ] SKILL.md:505 sweep 协议描述：注明 sweep 使用 `--batch-only`

