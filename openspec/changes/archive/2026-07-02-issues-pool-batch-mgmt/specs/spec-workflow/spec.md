# spec-workflow Specification (delta)

> 本 delta = `streamline-workflow-automation` 拆分的 **Phase B**，向既有能力 `spec-workflow` 追加**债务池与批次管理**的规范性行为。
> 决策真相源 = 归档 umbrella [design.md](../../../archive/2026-07-02-streamline-workflow-automation/design.md) §八 / 决策速查表 I1–I13。
> 〔grill-amendment / Q5〕第 2 条 Requirement 为**被动版**（reindex 同步状态，**不做逾期主动催办**）——早前旧稿标题曾含"逾期主动催办"，已按 Q5 删除。
> 〔grill-amendment / B-Q1〕批次"完成"判据 = 成员全部进入**各自 recorder 的终态集**（bug: `FIXED`/`WONTFIX`；todo: `DONE`/`WONTDO`），不硬编码字面 "DONE"（两 recorder 词表不同，bug 无 DONE）。

## ADDED Requirements

### Requirement: 债务池统一为 issues 结构且 INDEX 只生成

recorder 债务池 SHALL 统一为 `openspec/issues/{buglist,todolist}/` 结构，每个 item MUST 分**源change(provenance,不可变) / 批次(triage,可变) / status(生命周期)** 三维度记录；`issues/INDEX.md` MUST 只由 `reindex` 命令从各 dated 文件重建生成、禁止手改，SHALL NOT 成为独立的手维护真相源（杜绝第三漂移源）。

#### Scenario: reindex 从 dated 文件重建 INDEX
- **WHEN** 对 issues 池运行 `reindex`
- **THEN** 它从各 dated 文件（`buglist/` 按日、`todolist/` 按月）重建 `issues/INDEX.md`，摊清 open item × 批次并标出已闭合（终态）项，不读取也不信任任何手改的 INDEX 内容

#### Scenario: 三维度分家、status 回归干净
- **WHEN** 一个 item 被分诊到某清理批次
- **THEN** 批次写入独立的「批次」列，status 保持各 recorder 干净生命周期（bug: `OPEN→…→FIXED/WONTFIX`；todo: `OPEN→PROPOSED→DONE/WONTDO`）不被塞入批次，源change 维度保持不可变

### Requirement: 批次注册表与 reindex 被动同步状态

批次 SHALL 有第一类身份记录于 `issues/batches.md`（`PLANNED→IN_PROGRESS→DONE`，条目薄，批次 key = 清理 change 名）；每个 change 收尾时 sweep MUST 以 `源==本change` 为界只分诊本 change 新增的 OPEN 项入批次（源为空的孤儿项不归本次 sweep，交独立的通用 `--open-ungrouped` 清理流程处理）；`reindex` MUST 拿 item 池当 ground truth 同步批次状态——批次**成员数 ≥ 1 且全部进入各自 recorder 的终态集**（bug: `FIXED`/`WONTFIX`；todo: `DONE`/`WONTDO`，含 WONT\* 合法闭合）→ 批次判 `DONE`（0 成员批次 MUST 保持 `PLANNED`，防 vacuous-truth 假 DONE〔spec-review-amendment: D1〕），状态与成员不一致则标出纠正〔grill-amendment: B-Q1〕，MUST NOT 主动计算逾期或催办（改为被动摊清 + open 项下次清理自然纳入）。

#### Scenario: sweep 只分诊本 change 新增项
- **WHEN** 一个 change 在 opsx-done 生成 hand-off 那步运行 sweep
- **THEN** 它把本 change 新增的 OPEN 项分诊入批次、在 `batches.md` 登记 `PLANNED`，并由 hand-off 引用；已在各自 change 分诊过的老项不被全量重诊

#### Scenario: reindex 同步批次状态且不主动催办
- **WHEN** 某批次的成员 item 全部进入终态集（`FIXED`/`WONTFIX`/`DONE`/`WONTDO`），但 `batches.md` 仍标 `PLANNED`/`IN_PROGRESS`
- **THEN** reindex 依 item 池把该批次同步为 DONE 并留完成日志；对未完成批次仅被动摊清 open×批次，MUST NOT 计算逾期或主动催办

#### Scenario: 0 成员批次不被 vacuous 判 DONE〔spec-review-amendment: D1〕
- **WHEN** 一个批次已 `batch add` 登记（PLANNED）但尚无任何 item 打上其批次 tag（成员数 = 0）
- **THEN** reindex MUST 保持该批次 `PLANNED`，MUST NOT 因"全部成员进终态集"对空集永真而判 DONE
