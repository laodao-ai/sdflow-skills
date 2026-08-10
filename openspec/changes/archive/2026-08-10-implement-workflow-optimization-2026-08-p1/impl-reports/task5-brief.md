### Task 5: 收尾集成与文档同步

**Blocked-by:** 1,2,3,4
**R-ID:** R-IS1, R-WR1, R-WR2

全仓聚合验证 + 报告再生 + 文档同步。

行为描述：
- 全仓 pytest 绿（`/usr/bin/python3 -m pytest`）：sdflow-issues/tests/ + sdflow-retro/scripts/tests/ + hack/tests/ + 仓根 conftest 全量
- `openspec/retro/report.md` 再生提交（`python3 sdflow-retro/scripts/retro_report.py --root .`）：聚合④实修率段在场 + per-change tokens 列在场（存量 change 显「—」）
- roadmap `task-log.md` 追加 1.B 交付记录
- CONTEXT.md「实修率」词条按用户拍板结果处置（未确认 MUST NOT 写入）
- `sdflow-retro/SKILL.md` 补聚合④实修率段与 per-change tokens 列的一句说明

- [ ] 全仓 pytest 绿
- [ ] report.md 再生并验证聚合④与 tokens 列在场
- [ ] roadmap task-log.md 追加 1.B 交付记录
- [ ] SKILL.md 文档同步（sdflow-retro）

