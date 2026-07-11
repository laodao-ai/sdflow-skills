## MODIFIED Requirements

### Requirement: 高风险领域 cross-model 由 HR-TG 子集判定并留痕

两评审 skill 的规划镜头步 SHALL 顺带判定：本变更命中的 TG 集合 ∩ HR-TG 子集 {TG-04, TG-06, TG-07, TG-08, TG-09, TG-16, TG-17, TG-26} 是否非空；非空则单开领域专属 cross-model（聚焦命中的高风险域，「找领域镜漏的」）。判定结果无论正反 MUST 写入报告（可审计）。

机器锚行 SHALL 为 `<!-- sdflow:hr-tg v1 hit="…|none" declared="…" evidence="…" -->`〔grill-amendment Q1：回灌 declared= canonical〕，三字段语义分工：`hit=`/`declared=` 由 `hr_tg_intersect` 脚本 emit（`declared=` 承模型判定的完整命中集、canonical 必填，`hit=` = `declared ∩ HR-TG`），`evidence=` 为并存人读复核字段——`hit≠none` 时 MUST 给判据触发点且非空（哪处变更对应哪个 TG，30 秒可人工复核）。HR-TG 子集清单以 trigger-catalog 为单一源，SKILL 只引用 ID。

> 〔为何三字段〕`declared=`（脚本、机器可重算）与 `evidence=`（人手、给复核）正交并存：`declared` 使模型判定的完整命中集显式可见（adr/0018），`evidence` 承人读判据。mlh-p4 加 `declared=` 于码却未回灌本 requirement（仍写 evidence= 单字段），本次回灌统一。

#### Scenario: 命中 HR-TG 单开领域 cross-model
- **WHEN** 规划镜头判定命中 TG-08（外部依赖）
- **THEN** 单开一次领域 cross-model（codex，失败照常回落），报告记「命中 TG-08 → 已跑领域 cross-model」；锚 `hit=` 含 TG-08、`declared=` 含模型判定全集、`evidence=` 非空

#### Scenario: 未命中则不开且留痕
- **WHEN** 命中集 ∩ HR-TG = ∅
- **THEN** 不开领域 cross-model，报告记「HR-TG 判定：未命中」；锚 `hit="none"`、`declared=` 承模型判定集（可为空）

## ADDED Requirements

### Requirement: anchor_lint 机械化 hr-tg 锚一致性面治（M1/M2/M4/M-new，零妥协）〔grill 目标态导向〕

`anchor_lint` 校验 `sdflow:hr-tg` 锚时 SHALL 把可确定性校验的一致性一次机械化到位、全 fail-closed，MUST NOT 停留在字段在场检查、MUST NOT 留 WARN 降级/迁移旁路等妥协：

- **`--trigger-catalog` 必需**：校验 hr-tg 锚 SHALL 要求 `--trigger-catalog`，未传 → 非零退出（fail-closed），MUST NOT 降级为「仅字段在场 + WARN 放行」（WARN 放行 = fail-open，M2/M4/M-new 静默没跑而报告过关，架空本门）。
- **M1 declared= 硬必填**：每个 fence 外 hr-tg 锚 MUST 含 `declared=`，缺失 → 违规、非零退出。MUST NOT 内建任何常驻 grace 或 `--allow-legacy` 迁移旁路——归档旧报告不被任何流程重 lint（无需旁路）。
- **M2 hit⟺declared∩HR-TG 重算**：重算 `declared ∩ HR-TG 子集`（复用 `hr_tg_intersect` 成员解析 + 严格 tg-set 解析、单一源读成员），要求锚 `hit=` 与之逐元素一致（`hit=none` ⟺ 空交集），不一致 / `declared` 畸形 / `hit` 畸形 → 违规。
- **M4 evidence= 在场性**：`hit≠none` 时 MUST 含 `evidence=` 且非空，缺/空 → 违规。
- **M-new TG 存在性**：`declared=`/`hit=` 的每个 TG MUST 存在于 trigger-catalog 定义的全 TG 集（同 `hr_tg_intersect` 出锚侧口径），不存在 → 违规。

校验器 MUST NOT 校验 `declared` 本身是否为「真命中集」——「命中哪些 TG」无确定性信号（adr/0018），属语义残余（模型判定 + `evidence=` 人读 + git 审计）。M2 堵「手改单字段 `hit=none declared=TG-04` 内部矛盾」，**堵不住**「同改 hit+declared 一致但错」；实现与文档 MUST NOT 宣称使 hr-tg 锚 tamper-proof——此为完整机械化后剩下的合法机械/语义边界，非缺口、非妥协。

#### Scenario: 未传 trigger-catalog fail-closed（零妥协）
- **WHEN** 调用 `anchor_lint` 校验含 hr-tg 锚的报告但未传 `--trigger-catalog`
- **THEN** 非零退出 + stderr，MUST NOT 降级 WARN 放行

#### Scenario: 锚缺 declared 违规（M1，无 grace/旁路）
- **WHEN** fence 外 hr-tg 锚含 `hit=`/`evidence=` 但无 `declared=`
- **THEN** 判违规、非零退出（`missing-field`）；无 `--allow-legacy` 之类豁免

#### Scenario: declared 含不存在的 TG 违规（M-new）
- **WHEN** 锚 `declared="TG-99"`（shape 合法但 catalog 无定义）
- **THEN** 判违规（TG 未定义），非零退出

#### Scenario: hit 与 declared∩HR-TG 一致（M2）
- **WHEN** 锚 `hit="TG-04" declared="TG-04,TG-19"`，HR-TG 含 TG-04 不含 TG-19，`--trigger-catalog` 已传
- **THEN** 重算 `{TG-04}` 与 hit 一致，判通过

#### Scenario: 手改单字段内部不一致判违规（M2）
- **WHEN** 锚 `hit="none" declared="TG-04"`（TG-04∈HR-TG），`--trigger-catalog` 已传
- **THEN** 重算 `{TG-04}` ≠ `hit=none`，判违规（`hit-declared-mismatch`）

#### Scenario: 同改两字段一致但错——不宣称能挡（诚实边界）
- **WHEN** 锚 `hit="none" declared="none"`，而真实命中含某 HR-TG 成员（declared 已被篡改）
- **THEN** 重算一致，判通过——不校验 declared 正确性，此为已声明的语义残余边界

#### Scenario: hit≠none 缺 evidence 判违规（M4）
- **WHEN** 锚 `hit="TG-04" declared="TG-04"` 但无 `evidence=` 或 `evidence=""`
- **THEN** 判违规（`evidence-missing`）
