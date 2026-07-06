# Tasks — batch-triage-strategy

> 本 tasks 为 ff 阶段草稿；**grill → spec-review → 设计门**后由 `writing-plans` 细化为原子 TDD 清单。
> 开放设计问题由 grill 逐个定夺后回写。**Q-a 已定案 = 纯规则、无脚本 → 本 change 为纯 markdown 变更**。

## 0. 前置：grill 定夺开放问题

- [x] 0.1 **Q-a 已定案（grill）= 纯规则 checklist、不做判器脚本**（撞 roadmap 已证「pre-diff 不可脚本判语义」同一堵墙；issues 池低频人工/模型合批不值脚本）→ 无 scripts/、无 pytest
- [x] 0.2 **Q-b 已定案（grill）= 规模维 SHOULD 可调（≤~10 文件/~8 项起，标无基线可调）+ 含生成物硬 MUST 隔离（走独立再生 commit）**
- [x] 0.3 **Q-c 已定案（grill）= 硬 MUST 一项一 commit（item 粒度）**——允许 sweep 的安全前提，成本极低

## 1. issue 级判据规则（纯 checklist，pre-diff，fail-closed 纪律）

- [ ] 1.1 判据 checklist：输入面 = issue 描述 + 落点文件路径（pre-diff）；无逻辑面 ∧ 低危才放行（Req「fail-closed 纯规则纪律」「同类 Leg1」）
- [ ] 1.2 写「存疑即排除」为 MUST 纪律 + 显式声明「无脚本自动兜底、非机械保证」（Req「fail-closed 纯规则纪律」）
- [ ] 1.3 判据文档交叉引用 Leg1 `trivial_shape.py` 的无逻辑面标准，注明「同类判据、非同一脚本」（Req「同类 Leg1 非同一脚本」）

## 2. workflow 规则：大扫除批规范（bundle 权威源）

- [ ] 2.1 在 `sdflow-init/assets/workflow/` 新增大扫除批判据规则（如 `batch-triage.md`）：定义 + 硬边界（禁装逻辑面）（Req「硬边界」「分诊三分类」）
- [ ] 2.2 规则写入聚合上限：规模维 SHOULD 默认（≤~10 文件/~8 项、标可调）+ 含生成物硬 MUST 隔离（走独立再生 commit）（Req「聚合上限」）
- [ ] 2.3 规则写入 fail-closed「存疑即排除」MUST 纪律 + 显式声明「无脚本自动兜底」（Req「fail-closed 纯规则纪律」）
- [ ] 2.4b 规则写入「一项一 commit」硬 MUST（item 粒度，revert 独立性）（Req「大扫除批一项一 commit」）
- [ ] 2.4 `trigger-catalog.md` / workflow `INDEX.md` 同步登记新规则（Req「落 bundle 权威源」）

## 3. consolidation-plan 二分重划

- [ ] 3.1 `openspec/issues/consolidation-plan.md` 加大扫除批维度 + 每项批归属二分标注（相关批/大扫除批候选/单开）（Req「consolidation-plan 二分标注」）
- [ ] 3.2 顺带刷新 stale 状态（REC-1=gate-checkpoint-hardening、G7=sdflow-init-hardening 已 ship）（Req「consolidation-plan 二分标注」）
- [ ] 3.3 worked example：无逻辑面项（rec2 cosmetic T50/T41/T42 类）标候选、逻辑面项（T63/T64/T51/T52）标排除（Req「consolidation-plan 二分标注」，验收正反各 ≥1）

## 4. 回灌 + dogfood 生效

- [ ] 4.1 `openspec/INDEX.md` 登记 `batch-triage` capability（归档后 spec 同步）（Req「落 bundle 权威源」）
- [ ] 4.2 本仓 dogfood 跑 `setup.sh` 使 canonical 生效；确认 `sdflow-init update` 回灌路径无误（Req「落 bundle 权威源」）

## 5. 验收核对

- [ ] 5.1 逐 Requirement 核对：三分类互斥穷尽 / 硬边界 / fail-closed 误纳率 0 / 同类 Leg1 / 聚合上限 / consolidation 二分 / bundle 权威源 —— 各有可观察证据
- [ ] 5.2 code-review pass（冷主审，红线：不砍评审安全）
