## Why

降「轮次」是 workflow 聚合墙钟的真杠杆（`sdflow-retro` 18-change 实测：spec-review 占 43%，被人类门 elapsed 主导；少付几次「人类门 + 生成」= 降轮次才动得了这块——roadmap design D11/§2.3）。但现有 `consolidation-plan.md` 只覆盖「相关合批」（同 capability ∧ 高耦合 ∧ 低增量 的 BASE-18 AND 门）；散落各处的**琐碎正交项**（typo / cosmetic / 注释订正 / 小健壮性补丁）无规则可循——要么各自单开 change 付固定循环成本（评审重、慢），要么被随手塞进无关 change、坏 bisect/revert 粒度、稀释镜子注意力。P4 补齐「大扫除批」维度 + 安全判据，把「降轮次」规则化，且**MUST NOT 靠砍评审安全**换取（roadmap 红线）。

## What Changes

- **`consolidation-plan.md` 按框架重划**：在既有「相关合批」（AND 门）之外新增「大扫除批」维度，把待处理项二分——**相关项**（同 capability、高耦合）走 AND 门合批；**散落琐碎正交项**归大扫除批。
- **本仓判据规则补「大扫除批」规范**（Q2 定案=本仓-local，落 `openspec/issues/batch-triage-rules.md`，**非 bundle**；发布 deferred 至本仓 dogfood 验证后）：<!-- [impl-review-fix] F-H: 原写「补 workflow 规则集(bundle 权威源)」是 pre-Q2 残留,与 D6 本仓-local 定案矛盾 -->
  - 大扫除批**定义** + **硬边界**：正交批只装个体琐碎/低危项，**禁装有逻辑面的东西**（稀释评审注意力 + 无关改动挤一 commit 坏单独回退）。
  - **聚合上限**：每项低危 ≠ 聚合低危——限**文件数 / 目录跨度 / 是否含生成物 / CI 面积**，防 N 个散 typo 压垮 review 注意力 + 坏 bisect/revert 粒度。
- **新增 issue 级「无逻辑面/低危」近似判据**（grill 定=纯规则 checklist、非脚本；spec-review Q1 定=**采纳 Leg1 行为面路径守卫**）：与 Leg1 白名单**同类**（继承其 `BEHAVIOR_PATH_PATTERNS` 路径守卫——落 `SKILL.md`/`*/assets/workflow/*` 的项**硬排除，无论描述多 cosmetic**）、作用在 **issue 级 pre-diff**，不字面复用 `trivial_shape.py`（它需 diff）——「同类判据、非同一脚本」。
- **首个客场**：拿 `issues/` 池现有 debt 做 worked example——**T50/T41/T42 落 SKILL.md/bundle（行为面路径）→ 判据排除**（内容 cosmetic 但落点承载行为）；**逻辑面项（T63/T64/T51/T52）→ 排除**；真候选须落**非行为面路径**（纯 docs/README/注释/tests）。**诚实标注**：本仓多数 debt 落行为面文件 → 大扫除批**候选池薄**，dogfood 要实测其在本仓值不值。

## Capabilities

### New Capabilities
- `batch-triage`: issues 池待处理项分诊进「相关合批」vs「大扫除批」的规范性行为——相关批走 BASE-18 AND 门；大扫除批只纳个体琐碎/低危的正交项（issue 级 pre-diff 近似判据把关）+ 聚合上限；逻辑面项 fail-closed 排除。

### Modified Capabilities
<!-- 无：本 change 不改 spec-workflow 既有需求（三阶段连续化行为不变）。批次判据是其上游的新行为域，独立成 capability。bundle 规则文件新增不等于修改 spec-workflow 的既有需求。 -->

## Impact

- `openspec/issues/consolidation-plan.md`（重划：加大扫除批维度 + 三元标注 + 每项判定记录）。
- `openspec/issues/batch-triage-rules.md`（新，**本仓-local**——判据 checklist + 3 硬 MUST + fail-closed 记录）。**Q2 定案=本仓-local**：MUST NOT 进 bundle、MUST NOT 部署下游；**无回灌/INDEX snippet/trigger-catalog** 那一整套（冷源接地证实 D6 原「普通 update 回灌」事实性错误）。
- 判据=纯规则（grill Q-a），**无 scripts/、无 pytest**。
- **发布 deferred**：向下游发布是**验证后的未来独立 change**（对齐 Leg1：本仓验证有效才进 bundle）。
- **不碰**评审安全层（多镜/对抗/接地/outside-voice 一律不动）；判据只放行「非行为面路径 ∧ 个体琐碎/低危」。

## Success Metrics

- `consolidation-plan.md` 有明确「相关批 vs 大扫除批」二分标注。
- workflow 规则有正交批安全判据 + 聚合上限数值，且与 Leg1「无逻辑面」判据**同类、可交叉引用**。
- 判据对现有 debt 池能正确二分（≥1 个 worked example：无逻辑面项→候选、逻辑面项→排除）。
- **误纳率 0 是纪律目标，非机械不变量**〔impl-review-fix，对齐 D4 + spec.md「MUST NOT 声称有自动
  兜底门」〕：判据是纯规则 checklist，无判器脚本、无自动兜底门；"逻辑面项不被误纳入大扫除批"
  靠的是应用判据者遵守「存疑即排除」（fail-closed）纪律，不是脚本/gate 可验证的机械性质。本
  change MUST NOT 声称有自动化机制保证误纳率恒为 0——若发生误纳，责任归执行分诊的 human/model
  未遵守纪律，而非"门失效"。

## Non-Goals

- **不实际执行任何大扫除批**——P4 只定策略/判据；具体清 debt 由后续 change 按判据分批驱动。
- 不动 P2（机械镜降档）/ P3（接地镜流水线）——它们改 review SKILL、与本 change 文件集不相交但属不同 leg。
- 不改 roadmap 四件套本身（P4 是独立 implement change，roadmap 是规划真相源）。
- 不推翻既有「相关合批 AND 门」——已验证，只做增量（加大扫除批维度）。

## Compliance

- **本仓-local 落点纪律**（Q2/D6）：判据落本仓 `openspec/issues/`，**MUST NOT 进 bundle `sdflow-init/assets/workflow/`、不部署下游、无回灌**；本仓 git commit 即生效。发布下游是验证后的未来独立 change。<!-- [impl-review-fix] F-H: 原「bundle 权威源纪律…回灌」是 pre-Q2 残留,与本仓-local 定案矛盾 -->
- **审查顺序不可颠倒**：`/review`（本地 diff）→ push → `/code-review`（远程 PR）。
- **红线**：降成本 MUST NOT 靠砍评审安全（判据只作用于「无逻辑面/低危」，逻辑面一律走全审）。

## 需求优先级（TG-19）

- **P2**（战略权重高——retro 收口后 Leg3 提为「墙钟主杠杆」；但非阻塞正确性缺陷，故 P2 非 P1）。

## 开放问题（TG-21，交 grill 压测，proposal 不预决）

- **Q-a｜issue 级判据形态**：脚本化（issue-level 判器，data-class + pytest，可复用为 gate）vs 纯规则（markdown checklist，人/模型应用）？trade-off = 确定性/可测 vs 轻量/低维护。负责人：grill 阶段；截止：spec-review 前定。
- **Q-b｜聚合上限具体度量**：文件数上限取值？目录跨度如何量？含生成物是否一票否决？CI 面积怎么估？负责人：grill / spec-review；截止：设计门前定。

## 假设（TG-22）

- **A1**：issues 池项的「无逻辑面/低危」可在 **pre-diff**（仅凭 issue 描述 + 落点文件路径）近似判定。**失效影响**：描述不足以判语义时，判据 **fail-closed 排除**、退化为单开 change——损收益、不损安全（可接受）。
- **A2**：现有 REC-1/2/3 相关合批框架无需重构，仅加维度。**失效影响**：若重划发现 AND 门本身有缺陷，扩为独立 followup，不在本 change 强行修。
