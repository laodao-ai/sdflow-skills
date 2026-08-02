### Task 2: P3 sdflow-done archive 步现代化

**Blocked-by:** none
**R-ID:** archive-json-warnings, fallback-ladder-slim, archive-recognizes-skipped

改 `sdflow-done/SKILL.md` 第三步 archive 子代理 prompt：(a) 将 `openspec archive {change_name} -y 2>&1 | tail -30` 改为 `openspec archive {change_name} -y --json`；(b) 完整重写成功/失败判据为基于 JSON 结构的版本（成功=exit 0 且 `archive` 非 null，失败=exit≠0 或 `archive` 为 null）；(c) 新增对 `skip_specs` change 的处理（specs status=skipped 时无 delta 是正常的，不走 fallback）；(d) 确认现有 fallback 文本不提及 REMOVED abort（grep 实证零命中即通过）。

验收标准：
- [ ] archive 命令已改为 `openspec archive {change_name} -y --json`
- [ ] 成功/失败判据基于 JSON 字段（`archive` 非 null=成功，`archive.warnings` 展示警告，`archive` 为 null=失败走 fallback）
- [ ] 旧文本匹配判据（`"archived as ..."` / `"Validation error"` / `"incomplete task(s)"`）已全部替换
- [ ] archive 子代理 prompt 含对 skip_specs 的处理路径（specs status=skipped 时无 delta 不算异常）
- [ ] `grep -c "REMOVED" sdflow-done/SKILL.md` 返回 0（确认无 REMOVED abort 描述）

