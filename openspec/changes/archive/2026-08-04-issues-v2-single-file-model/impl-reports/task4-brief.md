### Task 4: 消费方全部更新 + 全仓 pytest 绿

**Blocked-by:** 3
**R-ID:** STOR-01, STOR-05, STOR-06, STOR-07

更新全部 11 个消费方引用，确保全仓一致：

1. `sdflow-issues/SKILL.md`：数据模型文档（单文件 schema、open/closed 目录）+ 命令文档（issues.py CLI）
2. `sdflow-issues/SKILL.md`：路由逻辑、触发判据（从三脚本路由改为单脚本）
3. `sdflow-done/SKILL.md` §2.1：sweep 改为只读 `scan --source-change` + hand-off 改列 ID
4. `hack/tests/test_harden_sdflow_spec_followup_closure.py`：`TODO_SCRIPT` 路径改为 `issues.py`
5. `CLAUDE.md` / `README.md`：命令示例和路径引用
6. `AGENTS.md`：issues 路径引用（buglist|todolist → open/|closed/）
7. `sdflow-init/assets/snippets/claude-section.md`：同上（推给消费仓的模版）
8. `openspec/CONTEXT.md`：领域术语更新（三脚本→单脚本、目录结构、终态词表）
9. `openspec/specs/spec-workflow/spec.md`：补 MODIFIED delta（batch/sweep/buglist.py 断言）
10. `openspec/specs/determinism-guards/spec.md`：补 MODIFIED/REMOVED delta
11. `openspec/specs/recorder-root-resolution/spec.md`：补 MODIFIED delta（三薄入口→单入口）
12. `.github/workflows/windows-recorder-smoke.yml`：更新硬编码测试路径

- [ ] sdflow-issues/SKILL.md 更新完成（数据模型 + 命令文档 + 路由/触发逻辑）
- [ ] sdflow-done/SKILL.md §2.1 重写完成（sweep → scan --source-change + hand-off 列 ID）
- [ ] hack/tests/ 中 TODO_SCRIPT 路径更新
- [ ] CLAUDE.md / README.md 命令示例更新
- [ ] AGENTS.md / claude-section.md / CONTEXT.md 路径引用更新
- [ ] spec-workflow/determinism-guards/recorder-root-resolution 三个 spec 的 delta 补完
- [ ] windows-recorder-smoke.yml 测试路径更新
- [ ] 全仓 `pytest` 绿（无红测）

