<!-- sdflow:step1-broad-review v1 mode="native" -->

# autoplan 广审 — parallelize-grounding-mirror

> 双声（Claude CEO + Claude Eng 子代理），原生执行。佐证：两个独立子代理分别前台顺序执行，
> 各自返回结构化 findings，主 session 汇总。

## 自动决策

| # | 决策 | 依据 | 分类 |
|---|------|------|------|
| D1 | UI scope = 否，跳过 Design Review | 改动仅 SKILL.md prose 条款，无 UI | 机械 |
| D2 | DX scope = 否，跳过 DX Review | 改动仅 SKILL.md prose 条款，非开发者工具接口 | 机械 |

## CEO 审（战略/范围）

### Finding C-1 — CRITICAL：decision-memo D1 与母 roadmap 已采纳的验收标准直接矛盾

roadmap `workflow-cost-optimization` 阶段 3（`roadmap.md:143`）已采纳「边界守卫强化（交叉审 #16/#17）」：
> Step3 裁决 MUST diff autoplan amendment 的新增 + 改动两类核验对象，**新增目标触发接地镜补跑**，不得只做改动增量核对。

本 change 的 decision-memo D1 选了「永不补跑」（A），且只对比 A/B（不补跑 vs 无条件全量重跑），
**从未提及或反驳 roadmap 已给出的第三条折中方案**（仅新增目标补跑）。
spec delta Scenario 4 写 `SHALL NOT 被要求补跑`，与 roadmap 验收标准正面矛盾。

**建议**：要么补上"新增目标判定 + 条件补跑"机制（roadmap 已设计好的路径），
要么在 decision-memo 正面对照 roadmap 原文说明偏离理由，并升级为需人拍板的 Q 决策。

### Finding C-2 — CRITICAL：声称的兜底机制「code-review 的 grounding 镜」不存在

proposal:28、decision-memo:31、design:64、spec:25 四处引用「由 sdflow-code-review 的 grounding/history 镜兜底」。
但 `sdflow-code-review/SKILL.md:597` 明确声明：
> 代码即 ground truth：直接读 diff 与真实代码，**不设接地镜**（与 sdflow-spec-review 的唯一结构差异，换历史镜）

历史镜做的是 `git blame` + 读历史 PR 评论（`sdflow-code-review/SKILL.md:260`），
核验的是"这块以前修过/revert 过吗"，**不是**"函数名/字段/API 路径是否真实存在"。
`mirrors=` 锚借用 `grounding` token 只是跨层共用词表的记号复用，SKILL.md:245-248 **明确声明「非声称这是接地镜」**。

**建议**：把所有"grounding 镜兜底"改为准确描述，或如实承认该兜底无对口机制。

### Finding C-3 — HIGH：收益"≈ autoplan 持续时间"被高估，无基线验证

P0 基线（18-change 聚合，roadmap design.md D11）已指出机械镜"在 fan-out 里并行、多半不是最慢镜"。
接地镜是弱档（haiku），领域/对抗镜是中档，大概率更慢 → 提前调度接地镜省下的墙钟趋近于零（不是"≈ autoplan 持续时间"）。
Success Metrics 三条全是"机制对不对"，**没有一条测量"墙钟是否真的降了"**。

### Finding C-4 — MEDIUM：声称 P3 交付但只做了 1/3 子任务

roadmap 阶段 3 列了 3 个子任务：①串行纪律精化 ②边界守卫强化 ③成本诚实/token 核算。
本 change 只做了 ①，却在 proposal 声称是「P3 的交付」。

### Finding C-5 — MEDIUM：备选方案被过快否决

decision-memo D1 把"仅新增目标补跑"这条折中方案用"完美成本过高"打发，
但本 SKILL 别处（HR-TG 判定 `SKILL.md:205`）已在用同款低成本模式（主 session 判定 + 脚本交集）解决同构问题。

## Eng 审（架构/边界）

### Finding E-1 — HIGH：design/tasks 未指定"真并行"所需的 async dispatch 机制

change 的唯一收益是接地镜与 autoplan 并行省墙钟，但 design 只画了示意图，
未锁定 SKILL.md 已有的「async dispatch 派出即返回」惯用法（`SKILL.md:191,205`）。
若实现者写成阻塞式调用，SKILL.md 文字看起来对了但实际仍是串行，收益归零。

**建议**：design/tasks 应显式借用既有 async dispatch 惯用法措辞。

### Finding E-2 — HIGH：核心证据"实测 7 个 change"查无实据

C1 和 D1 的置信度建立在"实测 7 个 change 的 amendment 以设计约束为主"上，
但仓内无任何文件记录这 7 个是哪些、怎么测的。
全仓搜索只命中 decision-memo 和 design 自身。违反 `openspec/rules/premise-verification.md`。

### Finding E-3 — MEDIUM：spec scenario 未覆盖两个边界方向

1. 缺"host=codex 且提前探针失败 → 接地镜降级"的 Scenario
2. 缺"接地镜提前跑出的 finding 因 autoplan amendment 改掉旧文本 → 假阳性"方向的讨论

### Finding E-4 — MEDIUM：能力探针提前到 Step1 可能给 autoplan 引入未记录的小串行段

host=codex 时探针是同步等待（`SKILL.md:211-212`），提前到 Step1 开头 = autoplan 起跑被推迟。
design:54 把它归入"不动的面"，分类不准。

### Finding E-5 — LOW：fanout-capability 锚在两阶段 dispatch 下的写入时点未被 tasks 核对

## 双声共识表

| # | 维度 | CEO | Eng | 共识 |
|---|------|-----|-----|------|
| 1 | roadmap 验收标准一致性 | C-1 CRITICAL | E-1 印证 | **CONFIRMED：直接矛盾** |
| 2 | 兜底机制事实性 | C-2 CRITICAL | E-2 验证 | **CONFIRMED：不存在** |
| 3 | 收益量化可信度 | C-3 HIGH | — | 单声 HIGH |
| 4 | 核心证据可查性 | — | E-2 HIGH | 单声 HIGH |
| 5 | async 机制锁定 | — | E-1 HIGH | 单声 HIGH |
| 6 | spec 覆盖完整性 | — | E-3 MEDIUM | 单声 MEDIUM |

[gstack-amendment]
