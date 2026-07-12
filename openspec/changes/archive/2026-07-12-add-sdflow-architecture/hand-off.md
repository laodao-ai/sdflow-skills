# hand-off — add-sdflow-architecture

> 2026-07-12 · verify PASS（见 verify-report.md）· 阶段三全链：SDD 10 任务 + code-review 三波修 25 条 + verify

## ✅ 完成了什么

（引 verify-report 结论，逐条已复核锚点存在性——测试名在 `sdflow-architecture/tests/` 实存且 106/106 绿，commit 在 `git log 67d8966..HEAD` 实存）

- **sdflow-architecture skill 全量落地**：SKILL.md 五步编排（三问时序纪律/AP 自检前置/一轮打包拍板/冷走查+宿主降级+人门固定议程/交棒收尾行 + 信任边界声明 ×3）+ references 六件（sad-template 十节 / decomposition-rules R1–R11+AP1–4 / quality-criteria S1–S11 真相源 / review-lenses / intake-questionnaire / checklists×4）+ scripts 三件 + tests 106 用例。锚点样例：`test_missing_fact_locks_draft`（锁 draft fail-closed）、`test_duplicate_number_set_reconciliation`（集合对账拦计数假绿）、`test_b13_transition_skeleton_requires_walkthrough_log`（走查留痕迁移前置）。
- **机械层强化超原 spec 面**（code-review 三波 [impl-review-fix]，commits a07b1e9 / ce9b037 / 1a6ae6a）：fence CommonMark 子集语义 + 未闭合 fail-closed、附录畸形行/重复节锚/重名子系统/contract 全载荷捕获、迁移前目标态全量不变式复检（不落盘先验）、sad-log append-only 双破口闭合、仓级互斥锁 + 唯一 tmp（并发 adr-new 同号竞态闭合）、OSError/UTF-8 全边界、走查留痕存在性前置（REQ-7 机械投影）。
- **生态接线**：sdflow-roadmap description 反向指路（`sdflow-roadmap/SKILL.md:11`）、README Skills 列表条目、CLAUDE.md 脚本类 skill 清单同步、双宿主 symlink 生效（skill 已在本 session 注册可触发）。
- **SM 核对**：SM-1（e2e 演练 skeleton-ready SAD + lint exit 0，impl-verify-notes.md 附 transcript）/ SM-2（每类断言正负 ≥2，106 用例）/ SM-3 达标；SM-4 = 试点未启动占位豁免（设计门 Q1=c）。

## ⏳ 未完成 / 延后

- **批次 `add-sdflow-architecture`**（见 `openspec/issues/batches.md` + INDEX）：T143 frozen-diff lint（目标态，需 git 对比）/ T144 sad_schema→JSON schema 生成工件（跨语言证伪条件）/ T145 sdflow-roadmap 指路句触发精度观察（无法机械验证，试点期留意）/ T146 工具族并发策略统一（todolist.py/buglist.py 同为扫描-max+1 无锁老债，与 sad_scaffold 锁面对齐一次做）。
- **延后的 ≥2 方案决策**：并发锁面「本轮修 vs defer」经 T10 对抗复核证伪 defer 后已本轮修（见 code-review-report.md 台账）——无遗留未决；子系统 5.x 编号连续性断言未采纳（spec 只要求集合相等，连续性属增强，未登记）。
- **verify Minor 缺口 3 条**（均判可接受，见 verify-report.md）：走查无独立报告文件的 glob 专项测试（行为约束归 SKILL 层）/ 语义编排步无自动化（TG-18 诚实标注）/ 裸模版 lint 非 0（正确行为）。
- **spec-review defer 项**（F-D1–F-D4，spec-review-report.md）：共享镜阵编排核（证伪条件=一次三处同修）/ frozen-diff lint（=T143）/ JSON schema 工件（=T144）/ 复述检测硬槽全面化（S1–S11 完整投影目标态）。F-D1、F-D4 无独立 todolist 项——F-D1 有显式证伪条件自触发，F-D4 归 S1–S11 完整投影（proposal Non-Goal 1 既定目标态）。

## ▶ 下一阶段建议

1. **首个真实试点**（最高优先）：拿一个新项目走 `/sdflow-architecture` 全五步 → 产出 skeleton-ready SAD → 开骨架 change——这是 SM-4 证伪钟起点（Q1=c 回填点），也是 Non-Goals 1–5 假设与 T145 触发精度的检验场。
2. **L2 子系统设计方法论**（OQ1，大议题）：SAD 之后、change 之前的子系统级细化环节——docs/sad/00 的步骤二空档，试点跑通 L1 后再开。
3. **清理 change 候选**：T146（工具族并发统一）适合与任何下次触碰 todolist/buglist 脚本的 change 合并 fold；T143/T144 等各自证伪条件触发。
4. **S1–S11 完整投影**（目标态，proposal Non-Goal 1 的解除条件）：试点若暴露语义判据缺口，按 quality-criteria.md 真相源逐条机械化升级。
