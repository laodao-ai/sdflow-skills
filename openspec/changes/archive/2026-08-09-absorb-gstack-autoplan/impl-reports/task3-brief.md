### Task 3: 守卫脚本退役与矩阵 golden 迁移

**Blocked-by:** 1,2
**R-ID:** R-outside-voice-reuse-guard, R-host-adaptive-execution

守卫脚本删除 + 矩阵全笛卡尔 golden 迁移到 anchor_lint 单工具测试:

1. 原 `test_outside_voice_guard.py` Step 5 跨工具全笛卡尔用例迁移/改造进 anchor_lint 测试侧(枚举域仍读契约机读块,分类逐条断言符合矩阵定义)——**在 guard 文件删除之前完成迁移**。
2. 删除 `sdflow-init/assets/workflow/tools/outside_voice_guard.py` 及其 tests。
3. 全仓 `/usr/bin/python3 -m pytest` 绿。

- [ ] 矩阵全笛卡尔 golden 已迁移到 anchor_lint 测试(含 mutation/边界)
- [ ] outside_voice_guard.py + tests 已删除
- [ ] 全仓 pytest 绿(guard 残留引用归零)

