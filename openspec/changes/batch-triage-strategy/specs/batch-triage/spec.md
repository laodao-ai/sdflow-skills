## ADDED Requirements

### Requirement: 待处理项分诊三分类
分诊过程 SHALL 把每个 issues 池待处理项归入且仅归入以下之一：**相关合批**（同 capability ∧ 高耦合，走 BASE-18 AND 门）、**大扫除批**（无逻辑面 ∧ 低危的正交项）、**单开 change**（其余）。分类 MUST 互斥且穷尽。

#### Scenario: 相关项归相关合批
- **WHEN** 一组待处理项满足 BASE-18 AND 门（同 capability ∧ 高耦合 ∧ 低增量）
- **THEN** 分诊将其归入相关合批（沿用 REC-1/2/3 既有框架），不进大扫除批

#### Scenario: 琐碎正交项归大扫除批
- **WHEN** 一个待处理项与其余项正交（非同 capability/低耦合），且经 issue 级判据判为无逻辑面 ∧ 低危
- **THEN** 分诊将其归入大扫除批候选

#### Scenario: 逻辑面项归单开
- **WHEN** 一个待处理项含逻辑面（如 init fence-aware collapse、merge untracked baseline、voice helper 硬化）
- **THEN** 分诊 MUST NOT 将其归入大扫除批，归入单开 change 或相关合批

### Requirement: 大扫除批硬边界——禁装逻辑面
大扫除批 SHALL 只装个体琐碎/低危的正交项；它 MUST NOT 装任何含逻辑面的项。此边界优先于任何合批收益考量（红线：降成本不砍评审安全）。

#### Scenario: 逻辑面项被拒纳入
- **WHEN** 尝试把一个含逻辑面的项加入某大扫除批
- **THEN** 该操作被判据拒绝，项被移出大扫除批

### Requirement: issue 级判据 fail-closed（纯规则纪律）
issue 级「无逻辑面 ∧ 低危」判据 SHALL 是一份 workflow 规则文档里的 checklist（**纯规则、非脚本**），作用于 **pre-diff**（仅凭 issue 描述 + 落点文件路径，无 diff），由做 consolidation-planning 的 human/model 应用。规则文档 SHALL 把「**当无法确认一项为琐碎/低危时，默认排除**（退化为单开）」写为 MUST 纪律。此为应用者遵守的纪律，**非脚本可验证的机械不变量**——规则 MUST NOT 声称有自动兜底门保证误纳率为 0。

#### Scenario: 描述不足判据存疑则排除
- **WHEN** 一个待处理项的描述不足以确认其无逻辑面（判据存疑）
- **THEN** 应用判据者默认排除该项、不纳入大扫除批，标注「存疑→单开」

#### Scenario: 判据是规则文档而非脚本
- **WHEN** 审阅 issue 级判据的落地形态
- **THEN** 它是 `sdflow-init/assets/workflow/` 下一份规则文档的 checklist，不引入任何判器脚本或 pytest

### Requirement: 判据同类 Leg1 白名单且非同一脚本
issue 级判据 SHALL 与 Leg1 `trivial_shape.py` 的「无逻辑面白名单」判据**同类**（同一「无逻辑面/低危」语义标准），但 MUST NOT 字面复用 `trivial_shape.py`（后者需 diff、post-diff 判形状，本判据 pre-diff）。判据规则文档 SHALL 与 Leg1 白名单交叉引用。

#### Scenario: 判据不依赖 diff、且交叉引用 Leg1
- **WHEN** 审阅 issue 级判据规则
- **THEN** 它不依赖任何 diff（pre-diff 即可应用），且其文档显式交叉引用 Leg1 `trivial_shape.py` 的无逻辑面标准、注明「同类判据、非同一脚本」

### Requirement: 大扫除批聚合上限
即使每项个体低危，大扫除批 SHALL 受聚合上限约束，分两类：
- **规模维（SHOULD 可调）**：规则 SHOULD 给保守起始默认（文件数 ≤ ~10 文件 / ~8 项、目录跨度越大越倾向拆、碰重型 CI 路径的项排除出 sweep），并标注「无实测基线、可调」。超默认宜拆。
- **含生成物（硬 MUST 隔离）**：碰生成物（如再生的 `retro/report.md`、重建的 `INDEX.md`）的项 MUST NOT 混入大扫除批，须单独走「再生 commit」。

#### Scenario: 规模超保守默认宜拆
- **WHEN** 一个大扫除批候选的规模超过 SHOULD 默认（如 > ~10 文件）
- **THEN** 分诊 SHOULD 将其拆分为多包

#### Scenario: 含生成物的项被隔离
- **WHEN** 一个待处理项会改动生成物（再生/重建产物）
- **THEN** 它 MUST NOT 进大扫除批，改走独立的再生 commit

### Requirement: 大扫除批一项一 commit
大扫除批作为一个 change 走一轮评审（一 PR），其内部实现 MUST 每个 item（一个 issue/todo ID）单独一个 commit（item 粒度，非文件粒度——同文件的两个 item 仍两 commit），以保证任一坏项可独立 revert。

#### Scenario: 每 item 独立 commit
- **WHEN** 实现一个含 N 个 item 的大扫除批
- **THEN** 产出 N 个 commit（每 item 一个），任一 item 可被单独 revert 而不动其余

### Requirement: consolidation-plan 二分标注
`openspec/issues/consolidation-plan.md` SHALL 对每个待处理项标注批归属（相关批 / 大扫除批候选 / 单开），并至少含一个 worked example（无逻辑面项→候选、逻辑面项→排除）。

#### Scenario: consolidation-plan 含正反 worked example
- **WHEN** 读 `consolidation-plan.md`
- **THEN** 它含大扫除批维度 + 二分标注，且至少一个无逻辑面项标为候选、至少一个逻辑面项（如 T63/T64/T51/T52）标为排除

### Requirement: 批次判据规则落 bundle 权威源
批次判据规则 SHALL 落在 `sdflow-init/assets/workflow/`（bundle 唯一权威源），并经 `sdflow-init update` 推下游；`openspec/INDEX.md`（或 workflow INDEX）SHALL 同步登记新规则文件。MUST NOT 只改某下游 `openspec/workflow/` 副本。

#### Scenario: 规则新增后 INDEX 同步且在 bundle 源
- **WHEN** 新增大扫除批判据规则文件
- **THEN** 文件位于 `sdflow-init/assets/workflow/` 下、且 INDEX 含对应登记条目
