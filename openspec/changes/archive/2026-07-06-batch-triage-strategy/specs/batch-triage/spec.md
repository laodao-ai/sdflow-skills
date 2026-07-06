## ADDED Requirements

### Requirement: 待处理项分诊三分类
分诊过程 SHALL 把每个 issues 池待处理项归入且仅归入以下之一：**相关合批**（走完整 BASE-18 AND 门 = 同 capability ∧ 高耦合 ∧ **低增量**三腿皆满足）、**大扫除批**（无逻辑面 ∧ 低危的正交项）、**单开 change**（其余；含「延迟绑定/搭便车」子态——暂缓、等未来碰这块的宿主 change 顺手带，省固定循环成本）。分类 MUST 互斥且穷尽。**注意**：同 cap ∧ 高耦合但**高增量**的项 MUST NOT 自动进相关合批（第三腿不满足），归单开或拆分（REC-3 先例：低增量✗仍列候选是偏差，重划须订正）。

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
- **THEN** 它是本仓 `openspec/issues/` 下一份规则文档的 checklist，不引入任何判器脚本或 pytest

### Requirement: 判据同类 Leg1 白名单且非同一脚本
issue 级判据 SHALL 与 Leg1 `trivial_shape.py` 的「无逻辑面白名单」判据**同类**（同一「无逻辑面/低危」语义标准），但 MUST NOT 字面复用 `trivial_shape.py`（后者需 diff、post-diff 判形状，本判据 pre-diff）。判据规则文档 SHALL 与 Leg1 白名单交叉引用。

**行为面路径硬排除（MUST，Q1 定案——采纳 Leg1 路径守卫）**：判据 MUST 把「item 落点命中 Leg1 `BEHAVIOR_PATH_PATTERNS`（`SKILL.md`、`*/assets/workflow/*`、`*ship_gate.py`、`*trivial_shape.py` 等）」作为**硬排除**信号——**无论 item 描述多 cosmetic，落点在行为面文件即排除出大扫除批**（这些文件承载行为，markdown 改动也可能改行为，机判分不清；同 Leg1 的保守偏 NOT_EXEMPT 立场）。这是「同类 Leg1」的具体含义：不是"人看描述判 cosmetic 就放行"，而是继承 Leg1 的路径守卫。

#### Scenario: 判据不依赖 diff、且交叉引用 Leg1
- **WHEN** 审阅 issue 级判据规则
- **THEN** 它不依赖任何 diff（pre-diff 即可应用），且其文档显式交叉引用 Leg1 `trivial_shape.py` 的无逻辑面标准、注明「同类判据、非同一脚本」

#### Scenario: 行为面路径项即便描述 cosmetic 也被排除
- **WHEN** 一个 item 描述是 cosmetic（如「决策区边框」「可点击链接」），但落点是 `SKILL.md` 或 `*/assets/workflow/*`
- **THEN** 判据 MUST 排除它出大扫除批（命中 Leg1 `BEHAVIOR_PATH_PATTERNS`），归单开或相关合批

### Requirement: 大扫除批聚合上限
即使每项个体低危，大扫除批 SHALL 受聚合上限约束，分三类落法：
- **有上限本身（MUST）**：规则 MUST 规定一个文件数/项数上限，超限 MUST 拆分或书面说明理由——**「存在上限且超限须拆」是 MUST**（不是建议），防 30 个散项照样一批。
- **上限数值（SHOULD 可调）**：具体数值（如 ≤ ~10 文件 / ~8 项、目录跨度）无实测基线，SHOULD-默认、标「可调」（守 grill Q-b 口径）；碰重型 CI 路径的项 SHOULD 排除出 sweep。
- **含生成物（硬 MUST 隔离）**：碰生成物（如再生的 `retro/report.md`、重建的 `INDEX.md`）的项 MUST NOT 混入大扫除批，须单独走「再生 commit」。

**每项结构化判定记录（MUST，fail-closed 问责机制）**：每个大扫除批候选 MUST 在 `consolidation-plan.md` 落一条判定记录——{item ID · 精确落点路径 · 为何无逻辑面 · 低危证据 · 生成物/CI/目录跨度检查结果 · 含排除理由}。**落点路径宽泛（如「workflow bundle 多处」）或证据不足 → MUST 标「存疑→单开」**（纯规则无脚本兜底，此记录是 fail-closed 的可审计落盘，防「口头纪律」）。

#### Scenario: 规模超保守默认宜拆
- **WHEN** 一个大扫除批候选的规模超过 SHOULD 默认（如 > ~10 文件）
- **THEN** 分诊 SHOULD 将其拆分为多包

#### Scenario: 含生成物的项被隔离
- **WHEN** 一个待处理项会改动生成物（再生/重建产物）
- **THEN** 它 MUST NOT 进大扫除批，改走独立的再生 commit

### Requirement: 大扫除批一项一 commit（含执行协议 + 验证锚）
大扫除批作为一个 change 走一轮评审（一 PR），其内部实现 MUST 每个 item（一个 issue/todo ID）单独一个 commit（item 粒度，非文件粒度——同文件的两个 item 仍两 commit），以保证任一坏项可独立 revert。

**执行协议（MUST，因 `checkpoint-commit.sh` 用 `git add -A`）**：sweep 实现 MUST 逐 item 严格串行——编辑一个 item → 立即 checkpoint（commit）→ 确认 `git status --porcelain` 干净 → 才碰下一项。MUST NOT 累积多 item 编辑后才 commit（`git add -A` 会把它们裹进一个 commit，静默破坏 item 粒度；buglist B1 同根因已真爆过）。sweep 的 plan MUST 为每个 item 生成一个独立 `### Task N: <itemID> …`，checkpoint slug/描述含 item ID。

**验证锚（MUST）**：verify/code-review MUST 核对 `候选 item 数 == 独立 task 数 == 独立 commit 数`（三者相等；`ship_gate.py` 的 `TAG_RE` 现只认 `task<N>` 不认 item ID，故此核对靠 verify 显式做，非 gate 自动）。

#### Scenario: 每 item 独立 commit + 串行协议
- **WHEN** 实现一个含 N 个 item 的大扫除批
- **THEN** 产出 N 个 commit（每 item 一个，逐 item 编辑→立即 commit→确认干净→下一项），任一 item 可被单独 revert 而不动其余

#### Scenario: 收尾计数自检
- **WHEN** 大扫除批实现完成
- **THEN** 核对的是 **item 实现 checkpoint commit 数**（`git log --oneline <base>..HEAD` 里 subject 匹配 item-checkpoint 形状/含 item ID 的提交，按 item ID 去重计数）—— **非** `base..HEAD` 区间的 raw 总 commit 数（该区间还含 ff/plan/review-fix 等非 item commit）〔impl-review-fix，订正计数公式不精确〕；该数 == 候选 item 数 == plan 独立 task 数，不等即视为违反 item 粒度、须拆

### Requirement: consolidation-plan 三元标注
`openspec/issues/consolidation-plan.md` SHALL 对每个待处理项做**三元标注**批归属（相关批 / 大扫除批候选 / 单开），并至少含一个 worked example（真无逻辑面项→候选、行为面路径/逻辑面项→排除）。（术语统一：全文用「三元标注」，勿用「二分」——终态有三个。）

**Q1 定案落地（行为面路径守卫）**：**T50/T41/T42 MUST 标「排除」**——它们内容虽 cosmetic，但落点是 `SKILL.md`/`workflow bundle`（命中 Leg1 `BEHAVIOR_PATH_PATTERNS`）。候选示例 MUST 换成真正落**非行为面路径**（纯 `docs/`/`README`/代码注释/`tests/`）的琐碎项。**诚实标注（MUST）**：consolidation-plan SHALL 记一句「本仓大扫除批候选池薄」——本仓多数 debt 落 SKILL.md/scripts/workflow（行为面），严格路径守卫后真正安全的候选可能个位数；此薄度是 dogfood 要实测回答"大扫除批在本仓值不值"的关键信号（见 proposal「验证后发布」排序）。

#### Scenario: consolidation-plan 含正反 worked example
- **WHEN** 读 `consolidation-plan.md`
- **THEN** 它含大扫除批维度 + 三元标注；T50/T41/T42 标排除（行为面路径）；至少一个真落非行为面路径的无逻辑面项标候选（若本仓无则显式记「候选池空/薄」）；至少一个逻辑面项（如 T63/T64/T51/T52）标排除

### Requirement: 批次判据规则落点——本仓-local（Q2 定案）
批次判据规则 SHALL 落在**本仓 `openspec/issues/`**（`consolidation-plan.md` 及旁边的 `batch-triage-rules.md`），作为 sdflow-skills 仓自有的规划纪律文档，**MUST NOT 拷进 bundle `sdflow-init/assets/workflow/`、MUST NOT 部署到下游消费仓**。这是一份本仓自用产物（非经 `resolve-workflow.sh` 解析的 workflow 规则），故**不涉回灌/INDEX snippet/BASE-18 悬空**等 bundle 部署机制。

**发布 deferred（MUST 记录）**：向下游发布**推迟到本仓 dogfood 验证之后**——真跑 ≥1 个大扫除批、有证据证明省了评审轮次且未掉安全，才作为**未来独立 change** 发布（届时须泛化去本仓依赖 + BASE-18 定义落 bundle + 修 4 部署机制 + workflow.md 加 issues-sweep 钩子 + cross-ref `spec-workflow` 的「workflow bundle 改在权威源」Requirement）。若 dogfood 证明候选池太薄/价值边际，可退化为 consolidation-plan 一句注记、不发布（亦为有效结论）。对齐 Leg1（`trivial_shape.py` 亦是本仓验证后才进 bundle）。

#### Scenario: 规则落本仓 issues/、不进 bundle
- **WHEN** 新增大扫除批判据规则
- **THEN** 它位于 `openspec/issues/`（非 `sdflow-init/assets/workflow/`），本仓 `git` 提交即生效（dev/runtime checkout pull 后皆有），无任何文件进入部署下游的 bundle

#### Scenario: 发布是验证后的未来 change
- **WHEN** 考虑把 batch-triage 铺给下游消费仓
- **THEN** 它 MUST 是本仓 dogfood 验证有效之后的独立 change，而非本 change 的一部分
