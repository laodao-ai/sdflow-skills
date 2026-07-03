# 设计：issues 债务池与批次管理（Phase B）

> **本 change = `streamline-workflow-automation` 拆分的 Phase B**（见归档 [ROADMAP.md](../archive/2026-07-02-streamline-workflow-automation/ROADMAP.md)）。
> **决策真相源 = 归档 umbrella [design.md](../archive/2026-07-02-streamline-workflow-automation/design.md) §八「阶段三配套：债务池与批次管理」+ 决策速查表 I1–I13**。
> 本文只做「Phase B 落地导航 + 与 umbrella 的 delta」，**不重复推导**已 grill 到共识（✅ 定）的决策；I* 决策若需追溯，读 umbrella §8 / 决策速查表。

## 一、依赖与前置

- **依赖 Phase A**：sweep 挂靠点 = opsx-done 生成 hand-off 那步（I5）。Phase A 已 merge，`opsx-done` SKILL 留有〔Phase B 补〕占位，Phase B 落地时填。
- **本仓当前无 issues 数据**（`openspec/buglists`/`todolists` 均不存在）→ laodao-skills 自身无一次性迁移负担；迁移影响主要在下游消费仓（§Non-Goals：routine，不在本 change）。

## 二、命中触发（TG，起手判定）

| TG | 命中点 | 落地要求（真相源） |
|---|---|---|
| **TG-05** 数据对象 + 生命周期 | issues item 三维度 schema（源/批次/status）+ batch 实体 | 数据模型见 umbrella §8.2 结构 / §8.3 三维度分家 |
| **TG-09** 多状态生命周期 | item `OPEN→PROPOSED→DONE` · batch `PLANNED→IN_PROGRESS→DONE` | 状态机见 umbrella §8.3（item）/ §8.5（batch，含 reindex 同步）——**已画 ASCII，本 change 不重画** |
| **TG-19** 多需求 | I1–I13 | 见 tasks.md 分节 |
| **TG-20** 外部影响方 | laodao-skills 共享 toolkit → 其它项目迁移 | 见 proposal Stakeholders（OQ3） |

- **TG-23（≥2 合理方案）**：I* 系列的方案取舍已在 umbrella design + `adr/` 记录，**Phase B 不新增 ADR**（架构级 ADR `0003`/`0004` 属另开 change，非本 change）；本 change grill 只**补 umbrella 未钉死处**（B-Q1 终态集 §4.1、B-Q2 命令归属 §五），就地记入 design/spec，不升 ADR。

## 三、决策（引用 umbrella §8 / 速查表 I1–I13，不复制）

落地遵循已定：结构 **I1**（`issues/{buglist,todolist}/` + `INDEX.md` + `batches.md`）· INDEX 只生成禁手改 **I2** · 三维度分家 **I3** · 批次 key = 清理 change 名 **I4** · sweep 时机 = opsx-done hand-off 步 **I5** · sweep 范围 = 只本 change 新增 **I6** · cadence bug按日/todo按月 **I7** · per-file 表保留 **I8** · 生效 = toolkit 新标准 **I9** · 连带 review UI/脚本 **I10** · batches.md 第一类身份 **I11** · 标准归属 = recorder 约定段 **I13**。

## 四、Phase B 唯一须显式守住的 delta（别回退）

**I12 债务闭环 = 被动 + reindex 同步状态〔grill-amendment / Q5〕**——这是本 change 最易被"优化回旧稿"的一条：

- ❌ **不做「逾期主动催办」**：早前旧稿曾想让 INDEX 主动标记逾期 PLANNED 批次（原 spec 需求标题一度含"逾期主动催办"，是 **Q5 前旧版**）；grill Q5 判「逾期」判据难定、且属投机机器，**删除**。
- ✅ **改被动**：`INDEX.md` 只把 open 项 × 批次**摊清、标 DONE**，剩下的 open 项在**下次清 bug/todo 时自然纳入**；不设逾期计算、不主动喊。
- ✅ **reindex 同步批次状态**（焊死 `batches.md` 状态漂移）：reindex 填成员时**拿 item 池当 ground truth** 校验/同步批次 `状态`——成员**全部进入各自 recorder 终态集** → 批次判/标 `DONE`；仍有成员未进终态却手标 `DONE` → reindex **标不一致纠正**（不静默信手写状态）。`PLANNED→IN_PROGRESS` 仍由人起 cleanup change 时设。

### 4.1 终态集定义〔grill-amendment: B-Q1〕

两 recorder **状态词表不同**,批次完成判据不能硬编码字面 "DONE":

| recorder | 全部 STATUS_CODES | **终态集**（进入即"这条债不再挂着"） |
|---|---|---|
| buglist | OPEN·VERIFIED·PROPOSED·IN_PROGRESS·FIXED·WONTFIX·BLOCKED | **FIXED, WONTFIX** |
| todolist | OPEN·PROPOSED·DONE·WONTDO | **DONE, WONTDO** |

- **批次完成判据 = 全部成员 ∈ 各自终态集**（含 WONT\*——WONTFIX/WONTDO 是"决定不修/不做"的**合法闭合**,批次里没有还 OPEN/PROPOSED/IN_PROGRESS/BLOCKED 的活就算清完）。
- reindex 按 **per-recorder 终态集**判,不写死 "DONE"（对 bug 根本不成立）。
- WONT\* item 同 FIXED/DONE 一样从 INDEX open 板消失,批次成员记录留 `batches.md` 作历史。

> 落地口径见 umbrella §8.5（grill-amendment）+ 决策速查表 I2/I12。spec delta 第 2 条 Requirement 已固化此被动版 + 终态集判据。B-Q1 是本 Phase B grill 对 umbrella 未钉死处的补充（umbrella §8.3 只写 `OPEN→PROPOSED→DONE/FIXED`,未覆盖 WONT\* 对批次完成的语义）。

### 4.2 sweep 界定"本 change 新增"〔grill-amendment: B-Q3〕

sweep（I6）以 **`源==本change ∧ status∈OPEN ∧ 批次==∅`** 为界，**只圈本 change 自己新增的未分诊项**：

- 源 = **别的 change** 的老 OPEN 项 → `--源` 过滤排除（各自 change 已诊，不重诊）。
- 源 = **`""`**（多 change 并行、`detect_change`(buglist.py:50) 探不出）的孤儿项 → **不归本次 change 的 sweep 管**；由**独立的通用「清 bug/todo」工作流**（`scan --open-ungrouped` → `triage` → 另开 cleanup change）兜底。
- 故 sweep 保持**窄而确定**（只碰能确定归属的）。全池未分诊项的安全网是**独立的通用清理流程**，不是 per-change sweep——两条路分工：孤儿不因 sweep 窄而无声蒸发，"不得无声蒸发"由通用清理路径守（非靠把 sweep 变宽）。

## 五、reindex / batch 命令归属〔grill-amendment: B-Q2〕

接地事实：`buglist.py`（buglist-recorder）与 `todolist.py`（todolist-recorder）是**两个独立 skill 的独立脚本**，各管自己一类。但 `reindex` / `batch` 是**跨 bug+todo**（join 两池 + 维护 `issues/INDEX.md` + `issues/batches.md`）。umbrella §8.6 只说"新增 reindex/batch 跨 bug+todo"，**未定归属**——grill 补：

- **新增一个共享 issues 层脚本**（`issues.py`，或薄 skill `issues-recorder`）**独占跨类型命令**（`reindex` / `batch`）+ owns `issues/INDEX.md` + `issues/batches.md`。
- **per-type 脚本（`buglist.py` / `todolist.py`）保持只管各自** add / scan / set-status / triage（+ 批次列 + 路径默认改 `issues/`）。
- **职责分层**：per-type = 记录（provenance 流水账）；跨-type = 索引 + 批次（物化板 + 注册表）。避免把 todo 命令藏进 bug 脚本、或两脚本各实现一份（双真相源，违 I2/I13）。
- **与 `minimize-repo-footprint` 的交集**：共享脚本**物理落点**（全局装 vs 随 recorder）届时随该 change 的脚本全局化一并定；本 change 先定"**独立共享层**"这一结构决策，落点留交集处理。

## 六、ROADMAP 约束落地（拆开必守）

- **约束1（workflow.md 增量改一次）**：本 change 给 `workflow.md` **只追加 sweep 步引用**，不碰 Phase A 写的连续化骨架、不预写 Phase C 的 outside-voice 步。
- **约束2（验证按相分摊）**：本 change 只验本相产物自洽 = §8.2「reindex 生成 INDEX + dated 文件 + batches.md 三处一致」（表↔块↔INDEX 自检）；不验 A/C 的产物。
- **约束3（下游采纳不在相内）**：消费仓迁移 issues 数据是下游 routine（proposal Non-Goals）。

## 七、不做（Phase B Non-Goals，见 proposal）

不含连续化（A 已交付）/ 跨模型 outside voice（C）；不清空既有债务（迁移结构即可）；不逾期催办（I12）；不含消费仓采纳（下游）；不另起 rules 文件（I13）。

## 八、spec-review 补强〔spec-review-amendment〕

阶段二多镜审（见 [spec-review-report.md](./spec-review-report.md)）一致命中**机制层欠规格**。**D1–D9 为自动决策**（就地补入设计）；**Q1–Q3 为需拍板**（设计门裁，见报告决策登记区，未在此定）。

- **D1 0 成员批次不判 DONE**：§4.1 完成判据加前置「**成员数 ≥ 1**」；0 成员批次 reindex 保持 PLANNED（防 vacuous-truth 假 DONE）。
- **D2 批次列追加表末**：「批次」列加**表末尾**（源/关联Change 之后），不插「状态」前（否则错位现有 `cells[N]` 位置解析）；沿用 `len(cells)>N` 防御式解析，旧列文件兼容留空。
- **D3 reindex 接入 sweep + INDEX banner**：reindex 接入 **sweep 步末**（tasks 4.1）保 INDEX 新鲜；`issues/INDEX.md` 首行 `<!-- GENERATED by issues.py reindex — DO NOT EDIT -->`，reindex 覆盖前弱校验告警。
- **D4 sweep 显式传 `--change`**：opsx-done 运行时知道本 change，sweep 显式传 `--change` 而非靠 `detect_change` 猜，从源头减少假孤儿。
- **D5 失败模式表**：见 §8.1。
- **D6 恢复模型 + 原子写**：reindex 对 `INDEX.md` = **全量确定性重建**（幂等、可安全重跑收敛）；所有文件写用 **temp + `os.replace` 原子写**（现有 recorder 是非原子 `open(w)+writelines`，本 change 收紧）；跨 INDEX+batches 无事务，靠"再跑一次 reindex 收敛"。
- **D7 幂等**：reindex 连跑两次结果相同；`triage` 对已 PROPOSED 的 item **no-op**（不非法跳转）。补 spec Scenario。
- **D8 并发假设边界**：工具**假定单机单进程串行调用、不加锁**（umbrella 自认 **TG-26 并发/共享可变状态**属 HR，但 TG-26 要 Phase C 才落地；Phase B 显式声明串行假设、不实现锁，真需并发留后续 change）。
- **D9 跨池 ID 前缀互斥**：B(bug)/T(todo) 前缀互斥升为**显式规范条款**（写进 recorder 约定段，tasks 1.2）；`issues.py` reindex 加**跨池 ID 冲突检测**，撞号报错不静默 join。

> **需拍板（设计门裁）**：Q1 迁移策略/ID 撞号 · Q2 批次命名/对账 · Q3 batches.md 格式契约 + 纠正语义。见 report。

### 8.1 失败模式表〔spec-review-amendment / D5〕

| 场景 | 检测 | 处理 | 可见性 |
|---|---|---|---|
| dated 文件表结构损坏（`split_sections` 返 None） | 解析判空 | 跳过该文件 + 报警，不崩、不静默 | reindex 输出显式列出 |
| item 批次 tag 指向 batches.md 不存在的 key（orphan） | reindex join 时 | 报 orphan 警告，**不静默生成 ghost 批次**（并入 Q2） | reindex 输出 |
| batches.md 状态引用不存在的成员 | reindex 对账 | 标不一致 | reindex 输出 |
| INDEX.md 被手改 | banner 校验（D3） | 无条件覆盖重建 + 告警 | reindex 输出 |
| 写入中途中断（半写） | temp+`os.replace` 原子写规避（D6） | 原文件不损，重跑收敛 | — |

### 8.2 Q1–Q3 临时裁决〔spec-review-amendment · **provisional，待设计门用户确认**〕

设计门 AskUserQuestion 超时（用户暂离），按推荐选项作**临时裁决**推进，用户回来可覆盖：

- **Q1 迁移/ID 撞号 = 加固版**：迁移仍算下游 routine，但 **Phase B 必须**交付：① 过渡期 **dual-read**（`next_id`/`scan` 新旧路径都扫再取 max，避免撞号）；② **ID 撞号检测**（跨路径同 ID 报错）；③ proposal **诚实记硬切风险**。不交付完整 migrate 命令（那扩 scope），但堵住"零无声堆积"漏洞。
- **Q2 批次命名/对账 = 保守简化**：sweep **永远新建 1 个批次、key = 本 change 名、禁跨 change 合并**（不做主题聚类判断）；`batch` 加 **rename** 命令（人真开 cleanup change 用不同名时重命名）；reindex 对 "item 有批次 tag 但 batches.md 无此 key" 的 orphan **显式报警、不静默生成 ghost 批次**。
- **Q3 batches.md 格式契约 = 精确 patch**：定**字段级 grammar**（哪些行 reindex 生成〔状态/成员〕、哪些人写〔计划/优先级/一句范围〕，明确分隔）；reindex **只精确 patch 生成行、绝不覆写人写行**；"标不一致纠正" = reindex **只追加警告标注、绝不越权改人写状态值**（防吃手写 + 防人写⇄reindex 震荡）。

> 三条均 provisional。用户设计门可改任一为其它选项（Q1 完整 migrate / 纯硬切；Q2 主题聚类；Q3 全量重建）；改了则同步 design/spec/tasks + 对应任务。
