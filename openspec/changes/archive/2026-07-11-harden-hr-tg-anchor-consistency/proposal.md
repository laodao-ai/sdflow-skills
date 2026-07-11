## Why

样本 #1（`mlh-p4-reason-code-validators`，SHIPPED 2026-07-11）冷层 `sdflow-code-review` 抓出 2 中危 fence-aware 假绿（已内修）+ hardening defer。本 change 把其中**「hr-tg 锚一致性机械化」这一件完整的事**一次做到目标态——`hr_tg_intersect` 出锚侧 + `anchor_lint` 校验侧，端到端零妥协。

**scope 纪律**〔decomposition standard〕：本 change = **一个完整内聚交付物**（hr-tg 锚一致性），不拆碎、不混做。原 mlh-p4 冷审 defer 里的 **T139（outside_voice_guard 双锚）是另一个 capability，已剥出**（留 todolist，另开自己的完整 change）；**T137（config 全局翻键）属用户意图裁断，非本功能**。grill 中发现的相关 todo（M-new：TG 存在性校验）**立即 fold 做掉、不 defer**。

**为何一次做完整**〔grill 教训〕：把「某条件机械化」拆成 T136/T138/T140 等 defer fragment，逐个捡起来时每个都触发「对现状提疑问 → 给妥协（WARN/grace/flag）」。锚目标态、一次做全、全 fail-closed，这些妥协根本不产生。

## What Changes

把 hr-tg 锚可确定性校验的一致性**一次机械化到位（面治）**，全 fail-closed，零妥协：

- **M3 严格解析（T138）· hr_tg_intersect**：`parse_tg_set`（`:54-62`）删「空 cell 静默过滤」（`:58`）——仅原始空串表空集，空 cell/前后逗号 → `EmitError`；成员抽取（`:14/:45` 宽松 `TG-\d+`）改词边界严格，`TG-04x` → `EmitError`。
- **M-new 存在性〔grill fold〕· hr_tg_intersect + anchor_lint**：declared/hit 的每个 TG MUST 存在于 trigger-catalog 定义的 TG 全集，否则 `EmitError`——catch 手误/幻觉 TG（如 `TG-16`→`TG-1` 合法 shape 但不存在，会被静默丢出 hit → 漏一个 HR-TG 命中）。有确定性信号（catalog 单一源），MUST 机械化。
- **M1/M2/M4 面治 · anchor_lint.check_hr_tg**（`:163-174`，接 `--trigger-catalog`）：
  - **M1** `declared=` **硬必填**，缺失 → 违规（**无永久 grace**）。
  - **M2**（=T136）重算 `declared∩HR-TG`、要求 `hit=` 逐元素一致（`none`⟺空交集），不一致/畸形 → 违规。
  - **M4** `hit≠none ⟹ evidence=` 在场且非空（spec:550 本就 MUST、从无机械守）。
- **`--trigger-catalog` 必需·fail-closed**〔零妥协〕：未传 → 非零退出，**MUST NOT** 降级 WARN 放行（fail-open 会让 M2/M4 静默没跑、门被架空；本 change 原子接线两个 SKILL 调用点，无未接线残留）。
- **spec-workflow:550 回灌〔grill Q1〕**：主 spec hr-tg 锚定义仍写 `hit=/evidence=`（无 declared），回灌为「`hit=` + `declared=`（脚本，canonical 必填）+ `evidence=`（人读，`hit≠none` 非空）」。
- **S1 语义残余（不机械化，合法）**：`declared` 本身是否=真命中集**无确定性信号** → 留模型判定 + evidence= 人读 + git 审计（adr/0018）；实现/文档 MUST NOT 冒充 tamper-proof。
- 经 `sdflow-init update` 推下游 + dev `setup.sh`；扩两工具 `tests/` 坏输入断言（含 whatever/declared 旧边界测试的**故意反转**）。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `hr-tg-intersection-check`：**ADDED** 一条 Requirement——命中 TG 集/成员行严格解析 + TG 存在性校验、畸形 fail-closed（M3+M-new）。
- `spec-workflow`：**MODIFIED** hr-tg 锚定义 Requirement（:550 回灌 declared= canonical 三字段）；**ADDED** 一条 Requirement——anchor_lint hr-tg 锚一致性机械化面治（M1 硬必填 + M2 重算 + M4 evidence 在场 + M-new 存在性 + `--trigger-catalog` 必需 fail-closed）。

## Impact

- **文件**：`sdflow-init/assets/workflow/tools/{hr_tg_intersect,anchor_lint}.py` + 各 `tests/`；`sdflow-code-review/SKILL.md`+`sdflow-spec-review/SKILL.md`（anchor_lint 调用步补 `--trigger-catalog $RULES_ROOT/trigger-catalog.md`，M2 生效前提，原子接线）。
- **分发**：bundle 权威源改动 → `sdflow-init update` 推消费仓 `openspec/workflow/tools/` + 本仓 `setup.sh`。
- **不涉及** `ship_gate.py`、`outside_voice_guard.py`（T139 已剥出）、`review_disposition_check.py`、`config.yaml`（T137 剥出）。

## Success Metrics

- hr-tg 锚一致性机械化完整覆盖 — 基准 anchor_lint 只查字段在场、hr_tg_intersect 静默正规化坏输入 → 目标 M1/M2/M3/M4/M-new 全 fail-closed — 度量方式 两工具 `tests/` 覆盖：空 cell / 宽松成员 / 不存在 TG / 缺 declared / hit-declared 不一致 / hit≠none 缺 evidence，各断言非零退出或违规。
- 零妥协 fail-closed — 基准 fragment 视角曾拟 WARN 降级 + allow-legacy + grace → 目标 `--trigger-catalog` 缺失即非零退出、缺 declared 即违规（无 grace/flag） — 度量方式 anchor_lint tests 断言无 catalog → 非零、缺 declared → 违规。
- 诚实边界 — 基准 无 — 目标 「同改 hit+declared 一致但错 → 仍过」边界确认负例在测，证不冒充 tamper-proof — 度量方式 anchor_lint tests 含该负例。

## Non-Goals

- **不裁 T137**（config 全局翻键 blast radius）：用户意图裁断、非本功能。**可证伪假设**：若发现 config 键已在误路由某活跃 change 且已致害，则须并入处理。
- **不做 T139**（outside_voice_guard 双锚）：另一 capability，已剥出另开完整 change（todolist T139）。**可证伪假设**：若 T139 与本 hr-tg 面治被证实共享同一解析核心须同改，则重估合并。
- **declared 正确性属语义残余（S1），不冒充 tamper-proof**：无确定性信号，合法留语义。**可证伪假设**：若「命中哪些 TG」出现确定性机械来源（推翻 adr/0018 D3），则可进一步机械化。
- **不引第三方依赖、不改 `setup.sh`/`ship_gate.py`**：两工具续纯 stdlib。**可证伪假设**：若 M2/M-new 需超 stdlib（不会——集合运算 + 既有 catalog 解析），则重评。

## Assumptions〔TG-22〕

- **假设〔grill B3 已核验为真〕**：无既有流程重 lint 归档旧报告——`sdflow-spec-review`/`sdflow-code-review` 仅在评审生成当次 lint 各自 fresh 报告，`sdflow-done` 不重跑。**据此**：存量 evidence=-only 旧锚不触发硬失败，**无需内建永久 grace**（fail-closed 硬必填即可）。**失效影响**：若某消费仓引入重 lint 归档报告的迁移路径，届时才加一次性迁移开关（真需求才做，非现在预留）。

## Compliance

遵 `spec-workflow` 既有 Requirement「workflow bundle 改在权威源、经部署下发」：改动落 `sdflow-init/assets/workflow/tools/` 权威源，经 `sdflow-init update` 下发。不涉及数据/安全/外部服务合规——N/A（hr-tg 锚越权通道属评审自检完整性、git 留痕可审计，非应用安全/敏感数据边界，未命中 HR-TG，详 design 触发判定）。scope 遵 decomposition standard（一个完整内聚交付物、不拆碎不混做、相关 fold 立即做、仅缺失依赖 defer）。
