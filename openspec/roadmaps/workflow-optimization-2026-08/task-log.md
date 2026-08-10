# workflow-optimization-2026-08 任务日志

> 本文件按时间**倒序**记录 `roadmap.md` 中每个已完成子任务的状态、耗时、问题、调整。
>
> 状态：ACTIVE
>
> 相关文档（全部位于 `openspec/roadmaps/workflow-optimization-2026-08/` 下）：
> - 整体设计：`design.md`
> - 实施路线图：`roadmap.md`

## 使用约定

每完成一个 roadmap.md 中的子任务（或子任务组），追加一条记录：

```markdown
## YYYY-MM-DD

### [阶段 X / 任务 X.Y.Z] <任务标题>
- **状态**: ✅ 完成 / ⚠️ 部分完成 / 🔄 已回滚 / ⏸ 暂停
- **实际耗时**: <N>h（估时 <M>h）
- **遇到的问题**: …
- **下一步**: …
- **备注**: …
```

**什么时候要记**：子任务状态变更；与设计预期不一致；需要调整 roadmap/design/specs；
跨阶段经验教训。**不用记**：纯配置微调、不涉决策的机械执行、笔误修复。
日期倒序，每天最多一个 `## YYYY-MM-DD` 标题；大阶段完成时补「阶段 N 完成总结」。

---

## Review 处置

<!-- review（roadmap 自持双镜 strategy/plan-eng + outside voice）产出的每条 issue 在此逐条追加，
     状态 ∈ ✅ 采纳 / ❌ 拒绝 / ⏭ 延后；voice 留痕行 runner=<runner> reason_code=<code>。 -->

voice 留痕：`runner=codex reason_code=ok`（跨模型第二意见，gpt-5.6-sol，非降级）

2026-08-10 初审（strategy + plan-eng 双镜并行 + sync voice，findings 去重后 11 组）：

- [V1·high] 1.A.1「重开已关 issue」违反 recorder 终态契约（`issues_v2.py` 拒改 `closed/`） ✅ 采纳 —— roadmap.md 1.B.4 新增 `reopen` recorder 增强（带契约测试 + reindex 一致性验收），1.A.1 改为依赖其交付并禁手工搬文件；design.md 新增假设 A3
- [V2+P1·high/Important] checkpoint 级 token 锚撑不起逐镜决策，且采集机制未定（checkpoint 脚本无 token 路径；自报≠机械捕获） ✅ 采纳（两条同题合并）—— design.md 新增假设 A2（机械 vs 自报两路径、逐镜 token 不做机械承诺）+ 验收门槛改写；roadmap.md 1.B.2 改「先定采集机制再实现」、阶段 2 目标改「实修率+独立率为主，token 为 per-change 趋势参考」
- [V3·high] 实修率历史回算缺可确定 join 的事实键（历史报告存在多对多聚合） ✅ 采纳 —— design.md 假设 A1 + 风险清单加强（MUST 输出可判定/未知/覆盖率三数，未达样本量阈值不入砍留依据）；roadmap.md 1.B.1 + 阶段 2 前置条件同步
- [V4·medium] roster 与裁决协议同 change 一轮 dogfood 无法归因、整体 revert 双撤 ✅ 采纳（简化形态：独立 commit 分别 revert + 预定义指标分别判读；全量历史语料重放降为 p2 设计相位候选——五问：完美成本高、简化方案可接受）—— design.md 决策 2 + §3.3 回滚表；roadmap.md 2.A.1 + 阶段 2 验收
- [S1·Important] 5 条决策命中 TG-23 但缺 BASE-12 强制的三镜+主次判定 ✅ 采纳 —— design.md 决策 1-5 各补「三镜代价 + 主次判定」段
- [S2·Minor] BASE-14 显式假设列表缺失 ✅ 采纳 —— design.md 新增「显式假设」小节（A1-A3）
- [S3·Minor]「DOC-1 扩面到 skill 正文」措辞与规则事实不符（DOC-1 本已覆盖 SKILL.md） ✅ 采纳 —— roadmap.md 1.A.2 与 `docs/workflow-optimization-research-2026-08.md` 同步改为「落实 DOC-1 审计」
- [P2·Minor] 附录 A 依赖图阶段 3 连线与「无边」注记矛盾 ✅ 采纳 —— 依赖图重画，阶段 3 独立成行零连线
- [P3·Important] 痛点 5 无对应目标态判据/验收 ✅ 采纳 —— design.md 目标态判据补占位判据（阶段 4 frontier 时排期反映实测基线）
- [P4·Minor] 小时级估时无推导依据（仓内 roadmap 先例均无小时估时） ✅ 采纳（取「删除数字」选项）—— 概览表与附录 B 回定性口径

本小节无未处置条目。

---

## 2026-08-10

### [阶段 1 完成总结] 度量补全 + 池对账全部完成

- **状态**: ✅ 完成
- **产出**:
  - 1.A.1 重分诊六条（T97/T98/T99/T100/T101/T102，含 roadmap 未列的 T97/T100）：
    T97→DONE（resolve-models.sh 已落地）；T98→PROPOSED（排入阶段 4）；
    T99→WONTDO（粒度错位，verify 已兜底）；T100→WONTDO（收益不抵复杂度）；
    T101→PROPOSED（排入阶段 5）；T102→PROPOSED（fold 进阶段 2）
  - 1.A.2 新增 T275（SKILL.md DOC-1 审计）入池 OPEN
  - 1.A.3 新增 T276（评审编排大改条件更新）入池 OPEN
  - 1.A.4 T119→DONE（fog-of-war 已是 sdflow-roadmap SKILL.md 硬约束）
- **验收**: `grep -c "wco roadmap P0-P5 全交付" CLOSED.md` = 0 ✅；全部四项验收标准通过
- **下一步**: 阶段 2 可起手——阶段 1 产出的实修率 + token 维判据已就绪

### [阶段 1 / 任务 1.B] 度量补全四子任务交付完成（change `implement-workflow-optimization-2026-08-p1`）

- **状态**: ✅ 完成
- **实际耗时**: —（定性口径，见附录 B P4 采纳「删除数字」）
- **产出**:
  - 1.B.1 T108 实修率指标：`sdflow-retro/scripts/retro_report.py` 新增聚合④「per-镜实修率
    （历史回算）」——窄文法从归档评审报告机械提取 fix-status 三态 + lens 归属，按
    (layer,lens) 输出可判定/实修/未修/defer/未知/覆盖率/实修率/佐证；`FIXRATE_MIN_SAMPLE=5`
    阈值，未达阈值标「（参考）」不入砍留依据（design.md 假设 A1 落地）
  - 1.B.2 T104 token 维度量：定案自报路径（`token_snapshot.py` 写 checkpoint 级 token 快照
    锚，`anchor` 字段区分真实/降级），非机械 hook 路径（宿主无 per-子代理 token 捕获能力，
    design.md 假设 A2 已记）
  - 1.B.3 retro 报告模版增列：per-change 表新增 `tokens` 列（`out/in/cc/cr` 四计数紧凑串，
    MUST NOT 合成总分），跨 change 同 session 按 ts 排序差分不双计数；存量 change 无
    token-log 显式「—」
  - 1.B.4 recorder 增强：`sdflow-issues/scripts/issues_v2.py` 新增 `reopen` 命令
    （closed→open 原子迁移 + 终态字段清理 + 历史追加 + reindex），带契约测试，是 1.A.1
    重开 T98/T99/T101/T102 的前置依赖
- **验证**:
  - 全仓 `/usr/bin/python3 -m pytest -q`：2513 passed, 10 skipped
  - `openspec/retro/report.md` 再生（`retro_report.py --root .`）：聚合④实修率段在场
    （7 行 (layer,lens) 数据，低样本量格标「（参考）」）+ per-change tokens 列在场
    （本 change 显真实四计数，存量 change 显「—」），已提交
- **下一步**: 阶段 1 剩余 1.A 池对账（1.A.1 依赖本任务 1.B.4 交付的 `reopen` 命令，可开始
  执行）；阶段 2 前置条件（实修率样本量阈值判定）已具备可用数据源
- **备注**: CONTEXT.md「实修率」词条按 tasks.md 明文要求未写入（未经用户确认）

### [阶段 0 / 规划] workflow-optimization-2026-08 roadmap 文档包产出完成

<!-- 阶段 0 记录关联 roadmap.md 概览节（规划期无实施阶段可挂，属 checklist ② 的声明式例外）。 -->

- **状态**: ✅ 完成
- **实际耗时**: ~2h（含全量调研：本仓证据盘点 + 联网业界对照）
- **产出**:
  - `openspec/roadmaps/workflow-optimization-2026-08/design.md` — 整体设计（需求与目标态 + 5 决策 + 风险权衡 + Q&A）
  - `openspec/roadmaps/workflow-optimization-2026-08/roadmap.md` — 实施路线图（5 阶段：近期 2 阶段全五节 + 3 雾区）
  - `openspec/roadmaps/workflow-optimization-2026-08/task-log.md` — 任务日志（本文件）
  - 证据基础另见 `docs/workflow-optimization-research-2026-08.md`（自足调研快照，非本包成员）
- **判定点①补记**: gate-0 五项全过（受众清楚 / 做不做已划清 / 关键路径有候选对比 /
  阶段划分有构思 / 权衡风险已识别）∧ 无商业化信号 → **三态路由第①态：直接生成路径**
  （不产出 memo）；拷问维度不适用（未进相位 B）。包生命周期判定 = create（目录原不存在）。
- **关键决策回顾**（完整档案见 `design.md` §2 和 §4）:
  - 复评前先补判据（token 维 + 实修率），不凭感受砍镜
  - 复评与裁决地基改造同 change（同片一致性面）
  - 上游吸收走统一 watch 机制（新数据类 skill，四源含 gstack/superpowers/matt/OpenSpec）
  - 评审编排大改不做，条件记录入池
  - 错关四条重开重分诊，理由归真
- **下一步**:
  - 阶段 1 起手：`/sdflow-spec implement-workflow-optimization-2026-08-p1`（1.B 四项，含
    reopen 增强）；1.A.2–1.A.4 可先行 recorder 操作，1.A.1 待 1.B.4 交付后执行
- **备注**:
  - 用户中途点名的「三套件上游吸收机制」已并入（design 决策 3 + roadmap 阶段 3）

### [阶段 0 / review + 收尾] 初审完成 + 收尾 checklist 通过

- **状态**: ✅ 完成
- **review 执行**: strategy/plan-eng 双镜（`model=sonnet`，整体 plan 契约声明已含）并行
  + sync voice（`runner=codex reason_code=ok`）与双镜重叠启动；findings 去重后 11 组，
  处置见上方「Review 处置」小节，全部当场采纳修入三件套与调研文档
- **判定点②（收尾 checklist 四项，显式陈述）**:
  - ① Review 处置无遗留：**通过**——`review_disposition_check.py` 判
    `section-ok-DISPOSITION-UNCHECKED`（exit 0；脚本只断言小节存在+非空），逐条复核
    11 组均已处置、无遗留（人工判定部分）
  - ② 三件套相互引用完整：**通过**——roadmap 阶段 1/2/3 均含「（见 design.md 决策 N）」
    回指；task-log 阶段 0 记录关联 roadmap 概览节（规划期声明式例外）；design 头部章与
    决策段无同值复述
  - ③ 历史存档未被引用：**通过**——本包无 memo.md/footage/（直接生成路径），
    `.outside-voice/` 为 gitignore 覆盖的调试留档、三件套未引用
  - ④ memo 对账 + 未决项闭环：**不适用**——直接生成路径未产出 memo（skill 明文允许），
    无 `[确认]` 全局写入条目待对账；相应地本包无 `状态：FINAL` 定稿标记、重入探测不可见
    （设计已接受的代价，如实声明）
- **备注**:
  - 全量调研快照（业界十源 + 本仓证据）另落 `docs/workflow-optimization-research-2026-08.md`，
    非本包成员、不受三件套引用规则约束
