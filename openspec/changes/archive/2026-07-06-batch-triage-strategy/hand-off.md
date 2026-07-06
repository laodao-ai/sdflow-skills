# hand-off — batch-triage-strategy

> 日期 2026-07-07。异步人类再入口 + 下个 change 种子。verify=PASS 后 / archive 前产出，随归档留档。

## ✅ 完成了什么（每条附机验锚点）

- **`openspec/issues/batch-triage-rules.md`（新建）** — 本仓-local、pre-diff、纯规则的大扫除批分诊判据 checklist：三元分类（互斥穷尽 + 低增量第三腿 + 延迟绑定子态）· 硬边界禁逻辑面 · fail-closed 无兜底诚实声明 · 同类 Leg1 + 行为面路径硬排除（`BEHAVIOR_PATH_PATTERNS` 代码块）· 聚合上限三类落法 + 每项结构化判定记录 · 一项一 commit 执行协议 + 验证锚。锚：commit `7e62d8f`；verify-report 逐条 file:line。
- **`openspec/issues/consolidation-plan.md`（重划）** — 加大扫除批维度 + 全项三元标注 + 刷新 stale（REC-1/G7 已 ship）+ worked example 正反：T50/T41/T42/T56/T57 行为面路径排除、T63/T64/T51/T52 逻辑面排除、**T13 唯一候选**、**候选池薄=1 诚实标注**。锚：commit `71eedee`+`02f9117`+`627640f`。
- **`openspec/INDEX.md`（登记）** — batch-triage capability 登记于 spec 索引区（L34，`opsx-init:rules:end` 之后、非托管块）。锚：commit `6c20dc6`；verify 机验 `grep batch-triage`。
- **bundle 零污染机验** — `grep -rl batch-triage sdflow-init/assets/workflow/` 退出码 1（零命中），坐实 Q2 本仓-local 不进 bundle。

## ⏳ 未完成 / 延后

- **code-review defer = 0** — 多镜主审（领域×1 + 对抗×2 + 历史×1 + codex OV）的 8 项 finding 全**当场自动修** [impl-review-fix]（无拿不准/修不了项）；issues sweep 扫本 change 新增 OPEN 项 = 空（无 buglist/todolist 残差、无新批次）。
- **发布 deferred（D6 设计决策，非缺陷）** — 向下游消费仓发布 batch-triage 判据是**验证后的未来独立 change**：须本仓 dogfood 真跑 ≥1 个大扫除批、证明省了评审轮次且未掉安全，才泛化去本仓依赖 + BASE-18 落 bundle + 修 4 部署机制 + workflow.md 加 issues-sweep 钩子。**候选池薄=1（仅 T13）** 是关键信号——若 dogfood 证明价值边际，可退化为 consolidation-plan 一句注记、不发布（亦有效结论）。
- **X1 archive 后核查项（转本步 → 已在 archive 解决）** — INDEX L34 指向 `openspec/specs/batch-triage/spec.md`，该路径由 archive 步同步创建；archive 完成后应确认它已存在、INDEX 行不再悬空（本次 archive 走 happy path 即解）。
- **verify Minor**：无核心缺口；「候选数==task数==commit数」验证锚是给未来 sweep 的规则内容、非本 change 自核指标（本 change 非 sweep）。

## ▶ 下一阶段建议

1. **dogfood 大扫除批（最高价值下一步）** — 拿唯一候选 T13（`sdflow-init/tests/` 补断言）真跑一个大扫除批 change，实测「一项一 commit 执行协议 + 生成物隔离（新加的 `__pycache__` gitignore 防线）+ 验证锚」是否顺、是否真省轮次。这是回答「大扫除批在本仓值不值」+ 决定「发布 vs 注记」的唯一实据来源。优先级 P2。
2. **候选池扩容观察** — 候选池薄=1 反映本仓多数 debt 落行为面文件（SKILL.md/scripts/workflow）。后续新 debt 若落纯 docs/tests，按判据归大扫除批候选，攒够一簇再跑第二次 sweep 验证聚合上限（≤~10 文件/~8 项）的实际手感。
3. **判据本身的 dogfood 反馈** — 应用判据时若发现某维度（如「书面说明理由」软化上限、tests 候选比 Leg1 宽）需收紧/放宽，回写 batch-triage-rules.md（本仓-local 迭代零部署成本）。
