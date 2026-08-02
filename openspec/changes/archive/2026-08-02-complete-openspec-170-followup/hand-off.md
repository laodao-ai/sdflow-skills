# Hand-off: complete-openspec-170-followup

## ✅ 完成了什么

- **P2 config 层注入**：`openspec/config.yaml` 与 `config.template.yaml` 均新增 `operations.archive.guidance`（两条硬约束字符串数组）和 `rules.specs` 的 `## Purpose` 规则。锚: `openspec/config.yaml:69-73`, `sdflow-init/assets/workflow/config.template.yaml:107-113`
- **P3 sdflow-done archive 现代化**：archive 命令改为 `--json`，成功/失败判据全部基于 JSON 结构，新增 skip_specs 状态检查。锚: `sdflow-done/SKILL.md:374-393`
- **Q2 amendment 双向 coherence**：amendment 写回段覆盖四件套，引用双向原则。锚: `sdflow-spec-review/SKILL.md:298-300`
- **Roadmap 回写**：P2/P3/Q2 状态已更新。锚: `openspec/roadmaps/openspec-1.7.0-followup/roadmap.md:50-53`
- **聚合测试**：1711 passed（1 pre-existing 红测，非本 change 引入）。锚: `impl-reports/task5-verify-all.md`

## ⏳ 未完成 / 延后

- 无本 change 新增 buglist/todolist 项（sweep 0 项）
- 代码审发现 1 个 Minor（task5 退出码管道掩盖）已自动修复
- **Pre-existing 红测**：`test_no_unbraced_variable_before_non_ascii[setup.sh]`（setup.sh:530 `$yqv` 紧跟中文逗号未加花括号）——非本 change 引入，建议另开 change 修

## ▶ 下一阶段建议

- openspec 1.7.0 跟进 roadmap 全部阶段（P1/P2/P3/Q1/Q2）已完成，本批收尾
- 遗留 todo：`fork 漂移无机械门`（todolist T264）——上游 `spec-driven` 更新时无提醒；优先级低，不急
- pre-existing 红测 `$yqv` 可顺手修（改 `${yqv}` 即可），建议 fold 进下个 change 或单独小修
- 未检测到 roadmap 关联标记；本 change 系 roadmap `openspec-1.7.0-followup` 的 P2+P3+Q2，回填已在 Task 4 直接更新 roadmap 阶段切分表完成
