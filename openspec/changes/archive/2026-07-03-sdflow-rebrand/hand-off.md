# hand-off — sdflow-rebrand

> 2026-07-03 · verify PASS 之后 / archive 之前产出 · 异步人类再入口 + 下个 change 种子

## ✅ 完成了什么（锚点已独立复核，非搬运 verify ✅）

- **两块坏地基前置修复**（设计门 Q1=A）：cleanup_orphans dangling 枚举（find 替代尾斜杠 glob，`TestCleanupOrphansDangling` 在场）+ inject() token 基 marker 迁移（`TestInjectMarkerMigration` DOC/IDX 双向在场）。
- **9 目录改名 + 3 保留**：`45ef162` 一次 git mv 保 blame（`git log --diff-filter=R` 复核在场）；`ls */SKILL.md` = 12。
- **触发等价**：39 条旧触发短语全保留，trigger-map.md 机械断言 `OVERALL: ALL PASS`（verify 亲自重跑）。
- **品牌收拢**：`sdflow-skills v0.9.0`（VERSION 真相源）；marker 名单制收窄（21 名三类断言全接线，`TestBrandAndMarkerNarrowing` 在场）；laodao 补轴断言（assert-log「laodao pattern 补轴」节 11 条 clean 带理由）。
- **零残留断言**：9+1 pattern 反向网 + 计数勘误两轮 + `opsx-init:` token 显式判定（assert-log.md，verify 重跑抽验在场）。
- **升级切换实测**（impl-review 对抗镜）：合并后首次切换 18 旧链精确清零、真·老式消费仓 token 迁移零重复区块、dangling canonical 窗口 resolver exit 2 显式降级、Codex sibling 不变量——四方向沙箱全过。
- 测试 224→233（逐 commit 账目吻合，零断言弱化——盲区镜程序化扫描在场）。

## ⏳ 未完成 / 延后

- **批次 `sdflow-rebrand`**（见 `openspec/issues/batches.md` + `INDEX.md`）：6 项 PROPOSED（T19–T24）。要点：**T24**（install_into 同名异物软链零所有权校验——已复现的安全设计债，与 T18 可见性问题不同轴，勿用"加提示"方案掩盖）；T19（grill 跳过条件重评估）/ T20（spec-review autoplan 先行串行纪律）是 workflow 机制债；T21-T23 为本 change 测试/边界小债。
- **自动裁决 1 项**（记理由于 code-review-report.md）：T24 defer 而非当场修——未改动行既有行为 + 迁移语义依赖，需专门设计"自属目标"判据。
- verify 无核心缺口；Minor 全部 = 上述 T 号。

## ▶ 下一阶段建议（含激活步骤，勿漏）

1. **合并后立即**：`git push` → **开新会话**跑 `/sdflow-upgrade`（本 session 的 skill 表还是旧名快照，勿再调旧名）——它在 canonical（`~/.skills/sdflow-skills`，REPO_NAME 匹配）pull+setup：9 条旧链清零 + 12 条新名链 + canonical 软链接管提示，一步完成真实激活。激活后抽 3 条真实语句验触发（"记一下这个 bug"→/sdflow-buglist、"帮我审设计"→/sdflow-spec-review、"收尾归档"→/sdflow-done）。
2. **消费仓迁移验收（带时限：各仓下次使用工作流前）**：跑 `sdflow-init update` → 确认托管区块引用新名且区块数=1（marker token 迁移自动处理旧区块）；未 update 的仓引用旧 slash 名会响性失灵（skill not found），update 即愈。
3. **用户全局 `~/.claude/CLAUDE.md`**（仓外，断言网结构性够不到）：其中 opsx-done/commit-message 等旧名示例请下次编辑时顺手更新（非强制，纯叙述）。
4. **下个 change**：按 ROADMAP 建议序 = `opsx-ship-orchestrator`（materialize 用新名 sdflow-*；写死 adr/0006 确定性台账约束；认领 T10/T11，顺路可清 T20）。批次 `sdflow-rebrand` 的 T21-T24 适合并入一个收尾小 change 或随 opsx-ship 顺手。
5. 归档注意（已转交 archive 步）：主 spec 已在本分支被 4.3 断言 sweep 过旧名，delta 对码时勿重复叠加。
