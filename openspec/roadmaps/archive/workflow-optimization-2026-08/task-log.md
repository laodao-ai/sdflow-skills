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

## 2026-08-12

### [阶段 4] 成本工程剩余——全部完成

- **状态**: ✅ 完成（change `implement-workflow-optimization-2026-08-p4`，归档 SHA `e202feb`）
- **交付**：effort 分档全链（model-tiers 机读块 + resolver 9 变量 + 5 agent 定义 + 四 SKILL 派发）、ship_gate B25/B26 双门（锚存在 + defer 对账）、render-review-prefix.sh 段① 渲染器、四 SKILL 三段组装序 + defer 当场入池改造
- **测试**：2639 passed, 0 failed；新增 89 测试（resolver 12 + gate 32 + prefix 14 + agents 14 + lint 15 + parity 2）
- **code-review**：零 findings（四镜全清，历史+voice 因上下文预算省略如实降级记录）
- **B25/B26 断链修复**：诊断=emitter 未调用（SKILL Step5 系统性跳过）；修复=Step7 独立步 + gate 机械门双保险
- **池状态**：B25→FIXED、B26→FIXED、T105→DONE、T103→DONE、T98→DONE、T124→DONE
- **备注**：阶段 1-4 全部完成，仅阶段 5（人类门减负）待 frontier

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

## 2026-08-12

### [阶段 2 / 验收 3] dogfood 观察窗口判读完成（3/3，roster 与裁决协议双 PASS）

- **状态**: ✅ 完成（阶段 2 最后一个验收框收口；纯读数活，未开 change）
- **窗口样本**: p2（样本 1）→ p3 → remove-superpowers-pipeline（3/3 齐，p3/rsp 已证实
  跑在新协议下：报告结构为「已采纳/已裁掉/defer 台账」三段式，rsp spec-review 显式记录
  `findings_ref_check` 15/15 pass、p3 spec-review 23/23 pass）
- **判读（按 hand-off D4 预定义指标分别归因）**:
  - **漏检 → roster**：无——三样本归档后 issues 池零新增缺陷；rsp 68 文件大 diff 正确
    触发 history 镜条件化派发（fanout 锚 `mirrors="domain,adversarial,history,broad"`）。
    ⇒ roster 改动（history 降采样等）**PASS，保留**
  - **采纳率偏移 → 裁决协议**：spec-review 侧 p3 ≈96%（21-22/23）、rsp 100%（15/15，
    含 4 条 defer 终裁转采纳），≥ 基线 87-93%；code-review 侧表面 43-46%（rsp 3/7、
    p3 6/13）vs 基线 73%，但**口径不同构**——旧协议置信硬滤在入池前静默丢弃、新协议
    全量入池显式裁掉；裁掉项逐条复核全部合法（X1 Speculative Generality、X2/X3 实查
    证伪、X4 非问题），无「该采未采」证据。⇒ 裁决协议 **PASS，无需回滚**
  - **T102 重判**：按阶段 2 遗留段预定规则 → **WONTDO**（二元裁决已足够压噪；对抗镜
    为 rsp spec 当轮最高产镜：10 findings 全采纳、独立 5）
- **附带发现（与 p2 改动无关的既有断链，判读中顺带坐实）**:
  - **B25**（P1）：code-review 报告机械层落盘自 08-07 起 6 个 change 连续静默缺失——
    lens-metric 锚为 0（`metrics.enabled=true`、SKILL 条款在、无 emitter 报错记载）、
    机械引用核亦无落盘痕迹；spec-review 侧两者均正常。聚合③ code-review 镜数据自此
    冻结，直接威胁未来 roster 复评判据
  - **B26**（P1）：code-review defer 入池通道 3/3 断——p3 两条标「待入」未入、rsp 一条
    报告写「已入 todolist」实未入（自述与事实不符）
  - 漏记 defer 已人工补录：T278（advance 绑定强度）/ T279（superpowers 采集器噪声）/
    T280（spec-review SKILL 收敛口 writing-plans 残留）
- **下一步**: 阶段 4 起手（`/sdflow-spec implement-workflow-optimization-2026-08-p4`）——
  前置条件已满足（token 基线 4 change 累积），窗口已收口故 effort 改动不再有归因混杂；
  B25/B26 与阶段 4 同属评审编排面，是否 fold 进 p4 由相位 B 拷问定
- **备注**: T98 重分诊时写的「与 T105 共享验收基线」在探索中已细化为分面归因——
  面 A（effort 分档）看质量不退（D4 同款指标），面 B（prompt 构造）看 token-log 的
  cache_creation/cache_read 比例趋势（真机械信号）

---

## 2026-08-11

### [阶段 3 / 实现完成] 上游套件吸收机制五票交付（change `implement-workflow-optimization-2026-08-p3`）

<!-- [impl-review-fix] 阶段 3 里程碑回填 -->

- **状态**: ✅ 实现完成（5/5 ticket；code-review 修复中，尚未 archive/merge）
- **相位 B 拷问**: decision-memo.md D1–D3 拍板——D1 scope 边界（只建机制，T264 一关三留：
  T264→DONE、T245/T246/T267 原地保留作首轮报告 seed）；D2 触发节奏（手动命令 +
  `/sdflow-upgrade` 收尾轻提醒，>30 天默认阈值）；D3 上游观察面（superpowers 盯
  marketplace 仓、matt 盯上游全量 + `.skill-lock.json` 辅助）；过 spec-review HARD-GATE
- **产出**:
  - Task 1 脚手架：SKILL.md + `scripts/upstream_watch.py`（cwd 守卫 + anchors.yaml 三态
    读写，yq mikefarah 探测）+ `openspec/upstream/` 目录
  - Task 2 四源采集器：gstack（既有 checkout）/ matt（bare 缓存）/ superpowers
    （marketplace.json `source.sha` 序列追踪）/ openspec（版本对照 + schema fork sha256
    drift）+ facts JSON + advance 报告+facts 双参数绑定门
  - Task 3 SKILL 编排层：collect→模型写报告→advance→呈报全路径 + 首轮 seed 条款
    （T245/T246/T267）+ 入池衔接模板 + `sdflow-upgrade` 第 5 步提醒段 + README 登记
  - Task 4 首轮真实 dogfood：四源真实网络 collect + 报告落盘 + advance 建锚；
    T264→DONE（evidence=schema drift 采集器实现+测试）
  - Task 5 验证收尾：全仓 pytest 2607 passed, 10 skipped（SHA `7e1e06d`）；集成/e2e
    判定「本仓无该层」，Task 4 手工验收作旁证
- **验证**: verify PASS（task5-verify-all.md）；code-review 采纳 6 项 finding 并当场修复
  （advance 报告读取异常保护、schema drift OSError 不再丢版本数据、错误消息路径脱敏、
  SKILL.md 缓存路径模板改真实路径、`_observed_anchor` 拒绝 null 锚 + 新增 2 项契约测试、
  本文件与 roadmap.md 回填），修复后 60/60 skill 内测试绿
- **下一步**: 本轮 fix 完成后重跑双轴审 → `sdflow-done`（verify/archive/merge）；归档后
  阶段 3 状态改「✅ 完成」并回填归档日期
- **备注**: 阶段 4/5 仍为雾区，待各自 frontier 到达后走相位 B 补细

### [阶段 2 完成总结] 镜 roster 复评 + 裁决地基改造全部完成（change `implement-workflow-optimization-2026-08-p2`）

- **状态**: ✅ 完成（5/5 子任务；验收 3 观察窗口 1/3 进行中，不阻塞）
- **产出**:
  - 2.A.1 roster 复评（commit A 独立）：`openspec/retro/mirror-dispositions.yaml`
    13 面镜处置——11 保留 + history 降采样（条件化：diff ≥200 行 / 含 rename 才派）+
    1 不适用；SKILL roster 段条件化 + `retro_report.py` 处置注记
  - 2.A.2 T106 裁决协议改造（commit B 独立）：D2 合成形态（`openspec/adr/0041`）——
    机械前置门 → 二元裁决（采纳/裁掉/defer + critique）→ 置信降级为排序信号；
    删 <80 硬滤/置信封顶/跨模型豁免矩阵；历史重放部署门 5 报告 49 findings ③类=0
  - 2.A.3 T112 复核层：`findings_ref_check.py` 机械引用核（三查三态+崩溃降级，20 pytest）
  - 2.A.4 lens-metric contract v2 + anchor_lint CLEAN + retro 再生冒烟
  - 2.A.5 评估结论=做：`sdflow-done` §3.0 done-final token 快照 + host 判定补丁
- **验证**: verify PASS（6 tasks / 40+ reqs）；全仓 pytest 2549 passed, 10 skipped；
  code-review 5 面镜 + code-voice（2 项自动修 + 3 defer + 6 裁掉）
- **计划外**:
  - **T102 fold 未执行**——阶段 1 拍板「fold 进阶段 2」，但 p2 scope 未纳入对抗镜措辞
    收紧；处置改挂验收 3 观察窗口结论后重判（已记 roadmap 阶段 2「遗留」段），池状态
    保持 PROPOSED
  - hand-off 残项 D1–D5（docs 同步 / ref-check 路径穿越 / done-final 降级确认 /
    前瞻窗口判读 / 一行描述更新），见 p2 归档 hand-off.md
- **池对账**: T106→DONE、T112→DONE（evidence = adr/0041 + findings_ref_check.py，
  见本日 recorder 操作）
- **下一步**: 阶段 3（上游吸收机制）——雾区补细走
  `/sdflow-spec implement-workflow-optimization-2026-08-p3` 相位 B grill

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
