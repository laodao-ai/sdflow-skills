# hand-off — sdflow-ship

> 2026-07-04 · verify=PASS（见 verify-report.md，每 ✅ 附测试名/文件:行锚点）· 阶段二拍板痕迹见 spec-review-report.md 决策登记区（Q1=B 新鲜度分域 / Q2 窗口 sha+--no-merges / Q3=A 未提交=fresh）。

## ✅ 完成了什么（锚点复核后收录，非搬运 verify）

- **ship_gate.py 确定性台账**（R-SS-1）：决策图全逻辑 + 五锚行字面契约 + 退出码 0/3/4/5/6 + Q2 窗口主锚 + D9 分域新鲜度 + git 健全前置——锚点：`sdflow-ship/scripts/ship_gate.py:1-45` 契约头注释（复核在）、`sdflow-ship/tests/` 44 用例 `-W error` 全绿（复核跑过 277 全仓）。
- **/sdflow-ship SKILL**（R-SS-3）：gate 纪律/零 git+透传/T10 三级协议（T10 已 DONE）/熔断+例外边界声明/resume 人机同权——锚点：`sdflow-ship/SKILL.md`（test_skill_text 4 断言在）。
- **model-tiers 单一真相源**（R-SS-2，T11 已 DONE）：`assets/workflow/model-tiers.md` + config 覆盖段 + 四 SKILL 全文零裸模型名——锚点：test_model_tiers 三断言（白名单口子已删）+ instance diff 为空。
- **T20 串行纪律**（R-SS-4，已 DONE）：`sdflow-spec-review/SKILL.md` Step2 MUST 句——锚点：test_serial_discipline。
- 评审链留档：spec-review-report.md（3Q+12 自动决策）、code-review-report.md（13 findings 全修 [impl-review-fix] + 6 裁掉留痕，锚行 `code-review=pass` 首用）、assert-log.md（8/8 含真实修因闭环）。

## ⏳ 未完成 / 延后

- **批次 `sdflow-ship`**（见 `openspec/issues/batches.md` + INDEX）：**T25**（spec-review Step1 autoplan / impl-review Step1 gstack-review 的原生化——本轮 impl-review Step1 仍为模拟降级模式，报告已显式留痕）、**T26**（熔断重试计数脚本化——当前靠主 session 短时计数，SKILL 已落例外边界声明；长期需解 D1 零副作用与计数落盘的矛盾）。
- 延后的 ≥2 方案决策：熔断计数处置当时按 T10 一级协议自动选"显式例外声明"（客观判据 = D1 拍板约束排除 gate 写状态）——若未来 gate 允许受控副作用，此决策应重开。
- verify Minor 缺口：6.1 文档收尾无自动化断言（人工抽验过）；6.3 hand-off 预置即本文件（随本步闭合）。

## ▶ 下一阶段建议

1. **真实激活（第一优先）**：merge + push 后**新会话**跑 `/sdflow-upgrade`（运行 checkout git pull + setup.sh 建 `sdflow-ship` 等新链——SKILL 内 gate 主路径 `~/.claude/skills/sdflow-ship/...` 当前 404 属预期，激活后消失）。激活后抽验：`python3 ~/.claude/skills/sdflow-ship/scripts/ship_gate.py --change <任意> --root <仓>` 能跑通。
2. **首次真实 ship 演练**：挑批次 `sdflow-rebrand` 的 T21-T24 收尾小 change 当试车对象——过设计门后用 `/sdflow-ship {change}` 全程驱动，重点观察 gate 判定被弱模型遵守情况与锚行契约实际命中。
3. 之后按批次清债：`sdflow-ship` 批次（T25/T26）可与 gstack 复用层（Phase C）合并规划。
