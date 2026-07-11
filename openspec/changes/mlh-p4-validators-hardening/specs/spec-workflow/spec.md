## ADDED Requirements

### Requirement: anchor_lint hr-tg 锚内部一致性重算 + 旧格式向后兼容 grace〔T136/T140〕

`anchor_lint` 校验 `sdflow:hr-tg` 锚时 SHALL 不止查 `hit=`/`declared=` **字段在场**，还对**新格式**锚（含 `declared=`）重算 `declared ∩ HR-TG 子集`（复用 `hr_tg_intersect` 的成员解析口径 + 严格 tg-set 解析、从 `--trigger-catalog` 单一源读成员），并要求锚 `hit=` 与重算结果**逐元素一致**（含 `hit=none` ⟺ 空交集）；不一致 / `declared` 畸形 / `hit` 畸形 → 判违规、非零退出。

校验器 MUST NOT 校验 `declared` 本身是否为「真命中集」——「命中哪些 TG」无确定性信号（adr/0018），脚本只校验 `hit` 对 `declared` 的**确定性派生**。故本校验堵「手改**单字段** `hit=none declared=TG-04`（TG-04∈HR-TG）」的内部矛盾，**堵不住**同时改 hit+declared 成「一致但错」；实现与文档 MUST NOT 宣称使 hr-tg 锚 tamper-proof（诚实边界，adr/0018）。

对**旧格式**锚（含 `evidence=` 且无 `declared=`，即 mlh-p4 前形态）SHALL 给迁移 grace：缺 `declared` 降级 WARN（human 行提示旧格式、跳过重算）而非 exit1；纯 `hit=` 无 evidence 无 declared 的畸形锚仍按缺字段违规。`--trigger-catalog` 未传时 SHALL 降级为「仅字段在场检查 + WARN 未重算」，MUST NOT 使既有未接线调用点硬失败。

> 〔为何〕mlh-p4 的 `check_hr_tg` 只查字段在场（docstring 明写「不校验 CSV 内容」），手改 `hit=none declared=TG-04` 能过 lint、静默跳过必开的领域 cross-model；且令 `declared=` 破坏性必填、无 grace，旧格式锚重 lint 会 exit1。重算是把「肉眼核 hit 对不对」这一**确定性可算却留给人/静默**的机械活下沉（adr/0006(b)），未越 adr/0018「命中判定归模型」边界（`declared` 仍由模型给）。

#### Scenario: 新格式锚 hit 与 declared∩HR-TG 一致
- **WHEN** hr-tg 锚 `hit="TG-04" declared="TG-04,TG-19"`，HR-TG 子集含 TG-04 不含 TG-19，`--trigger-catalog` 已传
- **THEN** 重算 `declared∩HR-TG = {TG-04}` 与 `hit` 一致，判通过

#### Scenario: 手改单字段内部不一致判违规
- **WHEN** hr-tg 锚 `hit="none" declared="TG-04"`（TG-04∈HR-TG），`--trigger-catalog` 已传
- **THEN** 重算 `declared∩HR-TG = {TG-04}` ≠ `hit=none`，判违规、非零退出

#### Scenario: 同改两字段一致但错——不宣称能挡（诚实边界确认）
- **WHEN** hr-tg 锚 `hit="none" declared="none"`，而真实命中含某 HR-TG 成员（模型/人已篡改 declared）
- **THEN** 重算 `none∩HR-TG = none` 与 `hit=none` 一致，判**通过**——本校验不校验 declared 正确性，此为已声明的诚实边界（非假绿：declared 正确性归模型 + git 审计）

#### Scenario: 旧格式锚缺 declared 降级 grace
- **WHEN** hr-tg 锚含 `hit=` + `evidence=` 但无 `declared=`（mlh-p4 前旧格式），重 lint `--layer spec-review`
- **THEN** 降级 WARN（提示旧格式跳重算）、退出码不因缺 declared 而 exit1

#### Scenario: --trigger-catalog 未传降级不硬失败
- **WHEN** 调用 `anchor_lint` 未传 `--trigger-catalog`
- **THEN** hr-tg 锚仅做字段在场检查 + WARN「未重算」，MUST NOT 使调用点硬失败（渐进接线）
