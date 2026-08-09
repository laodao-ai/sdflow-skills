### Task 1: Bundle 机械层同步与 retro 归属修正

**Blocked-by:** none
**R-ID:** R-workflow-metrics, R-host-adaptive-execution, R-spec-workflow

Bundle 机械层资产全部对齐新结构,retro 归属语义修正,确保全仓 pytest 绿:

1. `lens-metric-contract.md` fold 块:将 `autoplan-ceo/design/eng/dx: broad` 四行替换为 `strategy: broad` + `plan-eng: broad`(直接替换不共存);散文段同步(「跨模型性」段 autoplan 例名换新 raw 名,双实现表述改为 anchor_lint 单实现)。
2. `anchor_lint` golden 测试补用例:spec-review 报告 `mirrors=` 含 `broad` token 的场景、`step1-broad-review` 锚 `mode="subagent"` 与 `mode="main-session"` 两枚举值(枚举常量零改动,只补用例覆盖新形态)。
3. `sdflow-retro` `stage_walltimes`:相邻提交差由 attribute-to-previous 改为 attribute-to-next;`is_archive_rename` 判定对象由 cur 换 nxt;修正 `("sdflow-spec-generate","ff")` 映射;补新旧序列回归测试(单 checkpoint 新序列 + 含 `spec-review-autoplan` 中间标签的历史序列);`openspec/retro/report.md` 重跑再生。
4. `anchor_lint.py` `_MIRRORS_UPGRADE_HINT` 失效指引修复:`sdflow-init update` → 「回运行 checkout 跑 `bash setup.sh`」。

- [ ] fold 表四行替换为两行,fold 散文与注记同步
- [ ] anchor_lint golden 补 broad mirrors 与 step1 mode 两枚举用例
- [ ] retro stage_walltimes attribute-to-next 实现 + is_archive_rename 判定对象翻转
- [ ] retro 新旧序列回归测试通过
- [ ] retro report.md 重跑再生(49 归档 change 新口径)
- [ ] _MIRRORS_UPGRADE_HINT 指引修复
- [ ] 全仓 `/usr/bin/python3 -m pytest` 绿

