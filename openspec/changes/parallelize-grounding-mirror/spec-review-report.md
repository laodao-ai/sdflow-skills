# spec-review-report — parallelize-grounding-mirror

## 诚实边界（§0.0）

- 能力探针：host=claude，免探，恒 `subagents="available"`。探针结果由主 session 自己观察并落锚——无可信脚本捕获路径，MUST NOT 声称这是机械门。
- lens-metric findings 数值一致性 = 主 session 信任边界，非机械可验。
- roster 完备性与 findings JSON 誊写准确性同属主 session 信任边界。

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="none" declared="" -->

## Step1 广审（autoplan · native）

<!-- sdflow:step1-broad-review v1 mode="native" -->

双声（Claude CEO 子代理 + Claude Eng 子代理），原生执行 autoplan。
佐证：两个独立子代理分别前台顺序执行，各自返回结构化 findings。

CEO 5 条 findings（2 CRITICAL + 1 HIGH + 2 MEDIUM），Eng 7 条（2 CRITICAL + 2 HIGH + 2 MEDIUM + 1 LOW）。
核心命中：`code-review 无接地镜`（C-2）、`与 roadmap P3 验收标准矛盾`（C-1）双声共识 CONFIRMED。

详见 `gstack-review.md`（Step1 产物，已 checkpoint b49d279）。

## Step2 并行多镜 fan-out

**镜头规划**：
- 命中 TG 集 = 空（纯工作流规则 prose 条款改写，无技术栈触发）
- 领域镜：**无命中**（无 backend/embedded/frontend 触发）→ 不开
- 对抗镜：2 个（普通风险）—— 角度 1 隐藏假设 / 角度 2 失败模式与乐观估计
- 接地镜：1 个（代码事实核验）
- HR-TG：none → 不开 cross-model

**实际 fan-out**：对抗镜 ×2 + 接地镜 ×1，一条消息并行派出，各子代理 fresh context。

## Outside Voice

outside-voice 复用守卫：`reason_code=section-not-found`（gstack-review.md 无 codex outside-voice 段）→ 回落自跑设计 outside voice（仅补偿 outside-voice 切片，广审其余镜仍在 gstack-review.md 中）。

design-voice 经 `~/.sdflow/hack/outside-voice.sh` async·harness 分支 dispatch，exit 0（`reason_code="ok"`），3 条 findings 进池。

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

## Step3 综合 + 对抗裁决

### 合并去重

5 个独立视角（autoplan CEO + autoplan Eng + 对抗镜 1 + 对抗镜 2 + 接地镜）+ 1 个 outside-voice（design-voice）共产出 ~30 条 raw findings，去重合并为 10 条 canonical findings。

### Findings（去重后，按严重度排序）

#### R-1 · CRITICAL — 声称的兜底机制「code-review 的 grounding 镜」不存在（事实性错误）

**命中镜**：CEO, Eng, Adv1, Adv2, Grounding（5 镜独立确认）

proposal:28 / decision-memo:31 / design:64 / spec:25 四处引用「由 sdflow-code-review 的 grounding/history 镜兜底」。
但 `sdflow-code-review/SKILL.md:597` 明确声明：「代码即 ground truth：直接读 diff 与真实代码，**不设接地镜**」。
历史镜做的是 `git blame` + 读历史 PR 评论（:260），核验"这块以前修过/revert 过吗"，**不是**"函数名/字段/API 路径是否真实存在"。
`mirrors=` 锚借用 `grounding` token 只是跨层共用词表的记号复用（:245-248 明确声明「非声称这是接地镜」）。

D1（不补跑）的整个风险接受逻辑建立在这个不存在的兜底之上。兜底不存在 ⇒ 该残余风险变成永久漏检。

**建议**：把所有「grounding 镜兜底」改为准确描述（如「该残余风险目前无对口兜底机制，接受」），或落地 R-2 的补跑机制作为真实兜底。

#### R-2 · CRITICAL — 与母 roadmap P3 已采纳验收标准直接矛盾

**命中镜**：CEO, Eng, Adv1, Adv2（4 镜独立确认）

本 change 自称交付 roadmap `workflow-cost-optimization` P3。但 `roadmap.md:143` 已采纳「边界守卫强化（交叉审 #16/#17）」：
> Step3 裁决 MUST diff autoplan amendment 的新增 + 改动两类核验对象，**新增目标触发接地镜补跑**，不得只做改动增量核对。

decision-memo D1 只对比 A（永不补跑）/ B（无条件全量重跑），**从未提及或反驳 roadmap 已给出的第三条折中方案**。
spec delta Scenario 4 写 `SHALL NOT 被要求补跑`，与 roadmap 验收标准正面矛盾。
tasks.md:5（1.3）删除了旧条款的手动核对兜底，拿掉了已有的（弱）防线却没有换上 roadmap 指定的（强）防线。

**建议**：要么实现"新增目标判定 + 条件补跑"（roadmap 已设计好，且本 SKILL 的 HR-TG 判定 :205 是同构低成本模式），要么在 decision-memo 正面对照 roadmap 原文说明偏离理由，并升级为 Q 决策交人拍板。

#### R-3 · HIGH — 收益"≈ autoplan 持续时间"被高估，无基线验证

**命中镜**：CEO, Adv2

现状 Step2 是"一条消息内全部并发派出"（:232），接地镜（弱档/haiku）大概率不是 `max(domain, adversarial, grounding)` 里最慢的——领域/对抗镜（中档）更慢。提前调度接地镜省下的墙钟 ≈ `max(0, grounding_duration − max(domain_duration, adversarial_duration))`，正常场景下趋近于零。

design.md Success Metrics 三条全是"机制对不对"，没有一条测量"墙钟是否真的降了"。

**建议**：把收益表述改实事求是（"消除接地镜自身运行时长在 Step2 里的可能叠加，具体数值待验证"），或补一条 Success Metric 测量真实墙钟变化。

#### R-4 · HIGH — "实测 7 个 change"查无实据

**命中镜**：Eng, Adv1, Adv2（3 镜独立确认）

decision-memo C1 和 D1 的置信度建立在"实测 7 个 change 的 amendment 以设计约束为主"上，但全仓搜索只命中 decision-memo 和 design 自身。违反 `openspec/rules/premise-verification.md`。

**建议**：补上可核验的抽样记录（哪 7 个 change、检索命令），或把 C1/D1 的措辞降级为未验证假设。

#### R-5 · HIGH — async dispatch 机制未锁定，"真并行"无机械保证

**命中镜**：Eng, Adv1

design/tasks 只画了示意图和"MAY 并行"，未锁定 SKILL.md 已有的 async dispatch 惯用法（"派出即返回 + Step3 barrier collect"，见 :191, :205）。若实现者写成阻塞式调用，SKILL.md 文字看起来对了但实际仍串行，收益归零，且无机械检验。

**建议**：tasks 应新增任务明确要求接地镜 dispatch 借用 :191/:205 已有的 async 惯用法措辞。

#### R-6 · MEDIUM — 接地镜并行读取无稳定快照，可能产生混合盘面 findings

**命中镜**：OV design-voice

接地镜与 autoplan 并行读取 design/specs，autoplan 的 `[gstack-amendment]` 会修改这些文件。接地镜可能读到 amendment 前后的混合盘面。

**建议**：明确接地镜审查快照为"dispatch 时刻的盘面"，在报告中标明；或接受为可容忍的低风险（amendment 多改措辞不改代码事实引用，参考 C1 前提）。

#### R-7 · MEDIUM — spec scenario 未覆盖边界（探针失败/假阳性）

**命中镜**：Eng, OV

spec 的 4 个 Scenario 缺：① host=codex 提前探针失败 → 接地镜降级；② 接地镜提前跑出的 finding 因 amendment 改掉旧文本 → 假阳性。

**建议**：补一条探针失败降级 Scenario；假阳性方向可在 Risks 表补一行。

#### R-8 · MEDIUM — 能力探针前移，共用窗口从近零拉长到 autoplan 墙钟时长

**命中镜**：Eng, Adv2

design 已自认低风险（"极低概率/低影响/无需额外缓解"），符合通则④。

**裁决**：可接受残余风险，不阻塞。

#### R-9 · MEDIUM — MAY vs MUST/SHOULD 语义不一致

**命中镜**：Adv2

spec/tasks 写"接地镜 MAY 并行"，但 design 又写"并行是默认行为"。若是默认行为应为 SHOULD（配具名例外），MAY 暗示可随意不走。

**建议**：改为 SHOULD（配 host=unknown 等例外条件）。

#### R-10 · MEDIUM — 声称 P3 交付但只做 1/3 子任务

**命中镜**：CEO

roadmap P3 有 3 个子任务（①串行纪律精化 ②边界守卫强化 ③成本核算），本 change 只做了 ①。

**建议**：proposal 改措辞为"P3 的部分交付（子任务①）"，或把 ②③ fold 进来。

### 已裁掉（附裁掉理由，反静默压制）

| # | 原始发现 | 来源 | 裁掉理由 |
|---|---------|------|---------|
| X-1 | `:197` 未改——源代码仍是旧版本 | Grounding | 当前在设计审阶段，实现尚未开始，预期行为 |
| X-2 | autoplan CRITICAL findings 未回写 decision-memo | Adv1, Adv2 | decision-memo 是 sdflow-spec 相位 B 产物（先于 autoplan），autoplan findings 在此处 surfacing 给设计门拍板，是流程设计而非缺陷 |
| X-3 | 能力探针复用假设可用性不变 | Adv2 | design 已显式记录并接受为低风险（通则④），不另加防御 |

## 决策登记区

### [自动决策]

| # | 决策 | 依据 | 来源 |
|---|------|------|------|
| D1 | UI scope = 否，autoplan 跳过 Design/DX Review | 纯 prose 条款改写，无 UI/DX | autoplan |
| D2 | 领域镜 = 无命中（不开） | 无技术栈触发（TG 空集） | 镜头规划 |
| D3 | 对抗镜 = 2（普通风险） | 非高风险变更 | 镜头规划 |
| D4 | R-8 可接受残余 | design 已自认低风险，符合通则④ | 裁决 |
| D5 | X-1 不成立 | 设计审阶段未实现是预期 | 裁决 |
| D6 | X-2 不成立 | 流程设计（decision-memo 在 autoplan 之前） | 裁决 |

### [需拍板]

| # | 问题 | 选项 + 推荐 | 三面后果 | 主次判定 |
|---|------|-------------|---------|---------|
| Q-1 | R-1 + R-2 是阻塞性的。decision-memo D1（不补跑）建立在虚假兜底上 + 与 roadmap 验收矛盾。**如何处置？** | **A（推荐）**：修订四件套——把"grounding 镜兜底"改为如实描述 + 在 decision-memo 正面对照 roadmap 说明偏离理由 + 升级为 Q 决策 **B**：实现 roadmap 已设计的"新增目标条件补跑"机制 **C**：接受现状（明知兜底不存在且偏离 roadmap） | **系统**：A 最简，不加机制只修措辞；B 加机制但 roadmap 对齐；C 留永久漏检缺口。**用户**：A/B 无感知差异。**开发循环**：A 改 4 文件措辞 ~30min；B 加判定逻辑到 SKILL.md ~2h；C 零成本但技术债 | **主**：系统镜（漏检缺口 vs 措辞诚实）；**次**：开发循环镜（成本差异） |
| Q-2 | R-3 收益量化被高估。要不要补一条真实墙钟 Success Metric？ | **A（推荐）**：降级收益措辞为"边际收益" + 补一条墙钟观测指标 **B**：保持现有措辞 | **系统**：A 诚实，可验证；B 不可证伪。**用户**：无感知差异。**开发循环**：A 改 2 处措辞 | **主**：开发循环镜（收益可观测性） |
| Q-3 | R-4 核心证据查无实据。是否需要补锚？ | **A（推荐）**：补上 7 个 change 的检索命令 + 结果摘要 **B**：降级为"未验证假设" | **系统**：A 可核验；B 透明但不可回溯。**开发循环**：A ~15min | **主**：系统镜（premise 可验证性） |
| Q-4 | R-10 是否接受部分交付 P3？ | **A（推荐）**：改 proposal 措辞为"P3 部分交付（子任务①）" **B**：把 ② fold 进来一起做 | **系统**：A 诚实声明范围；B 完整交付但 scope 扩大。**开发循环**：A ~5min；B ~2h | **主**：开发循环镜（本次 scope 控制） |

### TENSION（outside-voice 与主审分歧）

| # | 站点 | voice 视角 | 主审视角 | 推荐 | 三面后果 + 主次 |
|---|------|-----------|---------|------|----------------|
| T-1 | design-voice | R-6（混合盘面）应显式固定快照 SHA | 可接受残余（amendment 多改措辞不改代码事实，与 C1 前提一致） | **主审**——低概率低影响，通则④ | 系统：固定快照增加 SKILL.md 复杂度，收益微；用户：无感知；开发循环：不值得加机制。主=开发循环镜 |

## 度量锚

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="1" sev="致2/高3/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="7" 采纳="7" 裁掉="0" defer="0" 独立="1" sev="致2/高3/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致1/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="2" sev="致0/高1/中2/低0" -->

## 收敛

**10 条 findings 采纳（2 CRITICAL + 3 HIGH + 5 MEDIUM），3 条裁掉，0 条 defer。**

**建议进设计 HARD-GATE？**——**条件进入**。R-1 和 R-2 是阻塞性的（事实性错误 + roadmap 矛盾），须在拍板前修订四件套（至少修正"grounding 镜兜底"措辞 + 正面回应 roadmap 偏离），修订后做一次窄复核再拍板。

[spec-review-amendment]
