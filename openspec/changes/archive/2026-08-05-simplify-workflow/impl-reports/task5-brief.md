### Task 5: 更新 snippets、CLAUDE.md、AGENTS.md、本地 pin 与 companion 文档

**Blocked-by:** 4
**R-ID:** R1

更新 `sdflow-init/assets/snippets/claude-section.md`：删分支 B/wayfinder/grill-with-docs/手动限制段落，加 sdflow-spec 自动触发规则，更新 impl-pipeline 缺省描述，从编排类 skill 列表移除 embedded-test-sop。更新本仓 `CLAUDE.md`：删「四入口选择规则」段、「旧入口 sunset 条件」段（≈40 行）、grill-with-docs 引用段落，更新编排类/使用路径/impl-pipeline 描述，删手动限制引用。更新 `AGENTS.md`：删旧双轨/手动触发/ff→grill 引用。处理 `openspec/workflow/` 本地 pin：删除规则文件恢复全局解析或同步刷新。同步 companion 文档：`docs/workflow-map.md`、`docs/workflow-overview.md`、`docs/criteria-mechanization-tracker.md`、`docs/sdflow-fable5/02-module-reference.md` 中的 RUN_SOP/embedded-test-sop/wayfinder/分支 B 引用。更新 README.md Skills 列表移除 embedded-test-sop。

- [ ] `claude-section.md` 已更新为单轨描述
- [ ] `CLAUDE.md` 已删除四入口选择规则段、sunset 条件段、grill-with-docs 段
- [ ] `AGENTS.md` 已删旧双轨/手动触发/ff→grill 引用
- [ ] `openspec/workflow/` 本地 pin 已处置（删除或同步）
- [ ] companion 文档中 RUN_SOP/embedded-test-sop/wayfinder/分支 B 引用已清理
- [ ] README.md Skills 列表无 embedded-test-sop

