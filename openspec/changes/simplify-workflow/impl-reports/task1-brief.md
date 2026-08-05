### Task 1: 删除 embedded-test-sop skill 并清除 ship_gate.py RUN_SOP 逻辑

**Blocked-by:** none
**R-ID:** R2

删除 `embedded-test-sop/` skill 目录，并从 ship_gate.py 状态机中移除 RUN_SOP verdict 的全部实现：`tg02_hit()` 函数体及其调用、`RUN_SOP` verdict 定义行、`decide()` 中的 RUN_SOP 分支、`emit_windowed` 中的 RUN_SOP 调用点、所有 docstring/注释中的 RUN_SOP 引用（含"三个入口"计数改为"两个"）。测试文件中纯 RUN_SOP 专属测试删除，断言元组/fixture 里附带提及的测试编辑保留（改元组/注释，不删函数）。删除后 `pytest sdflow-ship/tests/` 全绿，`bash setup.sh` 清孤儿链接。

- [ ] `embedded-test-sop/` 整个目录已删除
- [ ] ship_gate.py 中 `tg02_hit()` 函数已删除
- [ ] ship_gate.py 中 RUN_SOP verdict 定义、decide() 分支、emit_windowed 调用点已删除
- [ ] ship_gate.py 中所有 docstring/注释的 RUN_SOP 引用已清理（含计数同步）
- [ ] 测试文件中纯 RUN_SOP 专属测试已删除，附带提及的测试已编辑保留
- [ ] `pytest sdflow-ship/tests/` 全绿
- [ ] `bash setup.sh` 运行正常，`~/.claude/skills/` 下无 `embedded-test-sop` 链接

