# Tasks — batch-triage-strategy

> 本 tasks 经 grill + spec-review + 设计门定案回写；实现由 `writing-plans` 细化为原子清单。
> **grill**：Q-a 纯规则无脚本 / Q-b 上限 / Q-c 一项一commit。**spec-review 设计门**：Q1 采纳 Leg1 行为面路径守卫 / Q2 本仓-local（发布 deferred）+ 6 amendment。**本 change = 纯 markdown、本仓-local、不进 bundle**。

## 0. 前置：grill 定夺开放问题

- [x] 0.1 **Q-a 已定案（grill）= 纯规则 checklist、不做判器脚本**（撞 roadmap 已证「pre-diff 不可脚本判语义」同一堵墙；issues 池低频人工/模型合批不值脚本）→ 无 scripts/、无 pytest
- [x] 0.2 **Q-b 已定案（grill）= 规模维 SHOULD 可调（≤~10 文件/~8 项起，标无基线可调）+ 含生成物硬 MUST 隔离（走独立再生 commit）**
- [x] 0.3 **Q-c 已定案（grill）= 硬 MUST 一项一 commit（item 粒度）**——允许 sweep 的安全前提，成本极低

## 1. issue 级判据规则（纯 checklist，pre-diff，fail-closed 纪律）

- [x] 1.1 判据 checklist：输入面 = issue 描述 + 落点文件路径（pre-diff）；无逻辑面 ∧ 低危才放行（Req「fail-closed 纯规则纪律」「同类 Leg1」）
- [x] 1.2 **〔Q1〕行为面路径硬排除**：落点命中 Leg1 `BEHAVIOR_PATH_PATTERNS`（SKILL.md/*/assets/workflow/*/ship_gate.py 等）MUST 排除，无论描述多 cosmetic（Req「同类 Leg1」）
- [x] 1.3 写「存疑即排除」为 MUST 纪律 + 显式声明「无脚本自动兜底、非机械保证」（Req「fail-closed 纯规则纪律」）
- [x] 1.4 判据文档交叉引用 Leg1 `trivial_shape.py` 的无逻辑面标准，注明「同类判据、非同一脚本」（Req「同类 Leg1 非同一脚本」）

## 2. batch-triage-rules.md（本仓-local，openspec/issues/，不进 bundle）

- [x] 2.1 新建 `openspec/issues/batch-triage-rules.md`：大扫除批定义 + 硬边界（禁装逻辑面）（Req「硬边界」「分诊三分类」）
- [x] 2.2 写聚合上限：**有上限本身 MUST + 超限 MUST 拆**（数值 SHOULD 可调 ≤~10 文件/~8 项）+ 含生成物硬 MUST 隔离（Req「聚合上限」）
- [x] 2.3 写 fail-closed「存疑即排除」MUST + 无兜底声明 + 每项结构化判定记录格式（Req「fail-closed」「聚合上限」）
- [x] 2.4 写「一项一 commit」硬 MUST + 执行协议（逐 item 串行→立即 checkpoint→确认干净）+ 验证锚（候选数==task数==commit数）（Req「一项一 commit」）
- [x] 2.5 **不进 bundle**：MUST NOT 落 `sdflow-init/assets/workflow/`、MUST NOT 动 trigger-catalog/INDEX snippet；文档记「发布 deferred 至本仓验证后」（Req「本仓-local」）

## 3. consolidation-plan 三元重划

- [x] 3.1 `consolidation-plan.md` 加大扫除批维度 + 每项**三元标注**（相关批/大扫除批候选/单开）+ 每候选落结构化判定记录（Req「三元标注」「聚合上限」）
- [x] 3.2 刷新 stale 状态（REC-1=gate-checkpoint-hardening、G7=sdflow-init-hardening 已 ship）——限状态订正，勿重 litigate REC 设计（广审 B1 守卫）
- [x] 3.3 **〔Q1〕worked example**：T50/T41/T42 标**排除**（行为面路径）；逻辑面 T63/T64/T51/T52 标排除；真候选须落非行为面路径（无则显式记「候选池薄/空」+ 一句本仓候选池薄说明）（Req「三元标注」）

## 4. 本仓-local dogfood 生效

- [x] 4.1 `openspec/INDEX.md` 登记 `batch-triage` capability（归档后 spec 同步，本仓 spec 非 bundle）
- [x] 4.2 **不跑回灌**（Q2 本仓-local，无 bundle 部署）；判据 commit 即生效（dev/runtime pull 后皆有）

## 5. 验收核对

- [x] 5.1 逐 Requirement 核对：三分类互斥穷尽(含低增量腿) / 硬边界 / 行为面路径守卫 / fail-closed 纪律 / 聚合上限有牙 / 一项一commit执行协议+验证锚 / 三元标注 / 本仓-local不进bundle —— 各有可观察证据
- [x] 5.2 code-review pass（冷主审，红线：不砍评审安全）
