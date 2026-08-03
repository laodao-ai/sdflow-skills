### Task 3: 本仓数据迁移 + 旧文件清理 + 测试调整

**Blocked-by:** 2
**R-ID:** MIG-02, STOR-01

在本仓执行实际迁移，清理旧代码，调整测试。

**迁移执行**：
- 对本仓执行 `python3 sdflow-issues/scripts/issues.py migrate --root .`
- 验证 287 个 issue 全部迁移到 v2 格式（open/ + closed/ 文件数之和 = 287）
- reindex 后 INDEX.md/CLOSED.md 内容完整

**旧文件清理**：
- 删除旧文件：`buglist/`、`todolist/`、`batches.md`、`batch-triage-rules.md`、`consolidation-plan.md`
- 删除旧脚本：`buglist.py`、`todolist.py`、`sdflow_issues_core/`（2175 行包）、`migrate_legacy.py`

**测试调整**：
- 清理格式耦合的旧测试（表格解析、marker block 双写一致性等）
- 改造保留格式无关的不变量测试：`test_repo_root_identity_*`（仓根解析）、`test_task2_windows_local_fs_smoke`（Windows 编码）、`test_task6_coverage_gate`（覆盖率门禁）——改指向 v2 的 issues.py

- [ ] 迁移完成，open/ + closed/ 文件数之和 = 287
- [ ] INDEX.md 列出 open/ 中全部 issue，CLOSED.md 列出 closed/ 中全部
- [ ] 旧文件（buglist/、todolist/、batches.md 等）和旧脚本（buglist.py、todolist.py、sdflow_issues_core/、migrate_legacy.py）已删除
- [ ] 格式耦合的旧测试已清理
- [ ] 格式无关的不变量测试改造后通过（仓根解析、Windows 编码、覆盖率门禁）

