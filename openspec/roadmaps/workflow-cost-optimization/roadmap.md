# workflow 成本优化 实施路线图

> 版本：v4（2026-07-07，进度同步：**P4（批次策略）已交付并归档**——change `batch-triage-strategy` merged `725caf3`；剩 P2/P3 待做）
> 版本：v3（2026-07-06，P0 基线收口：`sdflow-retro` 18-change 实测 → P2 墙钟杠杆证伪、重定位 token play、Leg3 提为墙钟主杠杆、砍镜闸门定案）
> 版本：v2（2026-07-06，吸收 plan-eng-review 交叉审：codex 冷审 30 条去重后 9 组采纳）
>
> 相关文档（均位于 `openspec/roadmaps/workflow-cost-optimization/`）：
> - 需求综述：`requirements.md` · 整体设计：`design.md` · 任务日志：`task-log.md`

## 概览

三腿并行、非强依赖（各自独立可交付）。**Leg 1（P1）已完成并激活**（change `adaptive-workflow-routing` 已 merge + `/sdflow-upgrade`）。**P0 基线已收口**（`sdflow-retro` 18-change 实测），并**改写了 leg 权重**：spec-review 占 43%（人类门 elapsed 主导）、code-review 仅 5%，故 **Leg2（P2 机械镜降档）的墙钟收益证伪、重定位为 token play**（墙钟不回归即可）；**聚合墙钟的真杠杆是 Leg3 降轮次**（少付几次人类门），战略权重上调 Leg3。详见 design §2.2 收口段 + D11/D12、requirements §5 门槛。

> **P2 价值域澄清（explore 2026-07-06，checkpoint 时间戳实测）**：评审成本占比**高度双峰**——大逻辑 change 评审只占 ~9%（生成 + 设计门人决策吃 88%），小 change 评审占到 **73%**（`drop-per-dir-review-stub` 27min 里 code-review 独占 19.8min）。**P2 的真实杠杆域 = 有逻辑面的小 change**（撞评审、且评审是它的大头），对大 change 是噪声。这正印证 roadmap 立项动机（小 change 付不成比例评审开销 → 逼合批）。P1 杀无逻辑面小 change，P2 杀有逻辑面小 change，互补。

| 阶段 | 归属 | 依赖 | 里程碑 |
|---|---|---|---|
| **P1** · code-review 无逻辑面白名单免 Step2 | Leg 1 | —（已交付） | ✅ 三类形状免多镜 + 反误免可测（trivial_shape.py + 34 测试，已 merge） |
| **P0** · 阶段级墙钟基线采样 | Leg 2 前置 | 无 | ✅ **已收口**（`sdflow-retro` 全 18-change 聚合 + 收益门槛定案，见下「阶段 0」+ requirements §5）；照妖镜结论：spec-review 43%（人类门主导）、code-review 5%、**P2 墙钟证伪→改 token play** |
| **P2** · 档位矩阵强制落地 + 机械镜降档 | Leg 2 | P0 ✅ | `model-tiers.md` 升 3档×运行时矩阵、SKILL fan-out **报档位不写死模型**、机械镜实降 light（**主收益=省 token**，墙钟**不回归**即可，见 D11）、fail-closed；含 P2b 后台小尾巴 |
| **P3** · 接地镜流水线（放松串行纪律） | Leg 2 | P2 后更稳 | 接地镜与 autoplan 并行、**autoplan 新增核验目标不漏** |
| **P4** · 批次策略：相关合批 + 大扫除批 | Leg 3 | —（已交付） | ✅ consolidation-plan 重划 + 大扫除批 3 硬 MUST + 聚合上限 + issue 级 Leg1 路径守卫（change `batch-triage-strategy` merged `725caf3`；规则**本仓-local**、发布 deferred，见阶段 4 状态段） |

> 每阶段开独立 OpenSpec 变更（`implement-workflow-cost-optimization-pN` 或语义名），完成归档后进下一个。
> **并行 caveat（交叉审 #29）**：P0/P1/P4 触及互斥文件可并行；**P2/P3 均改 `sdflow-spec-review`/`sdflow-code-review` 的 SKILL.md，MUST 串行**（否则并行改同批规则→审查上下文错位 + merge 冲突）。开并行 leg 前先核文件集是否相交。
> **P2b 降级说明（explore 2026-07-06）**：原独立「P2b fan-out 后台」已并入 P2 作**小尾巴**——挖下去发现后台化只在 **spec-review→设计门**（人须等报告拍板）那一段有值；**code-review 阶段三无人类门（P3e），人本就能走开、后台化几乎不加值**；且 harness 已有子代理完成通知（半免费）。不配独立阶段。

---

## 阶段 1 · code-review 无逻辑面白名单免 Step2（Leg 1，✅ 已交付）

### 状态
**已完成并激活**。change `adaptive-workflow-routing` 已过 grill + spec-review + 设计门 Q1=A + code-review（1 冷镜抓 7 危险方向洞 F1-F7 全修）+ merge + `/sdflow-upgrade`。判器 `trivial_shape.py`（9012 字节）已在 `~/.sdflow/workflow/tools/` 激活。

### 交付内容
- 无逻辑面形状判器（语言感知 + **行为面路径豁免** + **load-bearing 版本常量守卫收窄 VERSION/CHANGELOG**）+ 34 pytest。
- `sdflow-code-review/SKILL.md` Step2 接入。
- spec-workflow code-review 需求 MODIFIED（两层措辞：Step1 恒跑 + Step2 白名单免）。

### 交付验收（已达成）
- 纯注释/约定文档路径/仅加 tests（排除 conftest/__init__）/纯展示 VERSION/CHANGELOG → 命中免 Step2、仍产报告。
- 改 `SKILL.md`/`workflow.md`/`ship_gate.py`/判器自身一行（形状似 markdown）→ **行为面路径命中 → 照跑多镜**。
- `requirements.txt`/`docs/conf.py`/`README_gen.py`/`API_VERSION=2`/`conftest.py` → 不误入白名单。
- 伪装成注释的逻辑改 → Step1 scope-drift 揭穿 → 照跑。

---

## 阶段 0 · 阶段级墙钟基线采样（Leg 2 前置，交叉审 #23/#24/#30）

### 前置条件
无。**这是 P2/P3 的前置**——没基线无法证明调度复杂度换来真收益，否则可能优化非瓶颈镜、墙钟无实际变化（呼应 adr/0009：无 per-镜耗时）。

### 目标
用**已有的近乎免费原料**（checkpoint commit 时间戳）建立 per-阶段（grill/spec-review/实现/code-review/done）× per-change 类型的墙钟基线，并**定收益门槛数值**，作为 P2/P3 立项与验收的判据。

### 子任务
- 脚本：扫归档 change 的 checkpoint commit 时间戳，聚合出各阶段墙钟分布（median/p90）+ 分 change 类型（琐碎/routine/HR-TG）统计。
- 定门槛：P2/P3 值得做的最低收益（如"spec-review 阶段 median 降 ≥X%"或"误免率恒为 0"），写进 requirements 验收总纲。

### 验收
- 有一份 per-阶段基线数据（哪怕粗粒度）+ 明确的收益门槛数值。
- P2/P3 的"实测下降"验收改为**对基线的相对值 + 多轮同基线**（非单次对比，抗排队/缓存/网络噪声，交叉审 #14）。

### 交付物
基线采样脚本 + `requirements.md` 验收总纲补收益门槛。

### ✅ 收口结论（2026-07-06，`sdflow-retro` 全 18-change 聚合 `openspec/retro/report.md`）
- **基线数据**：阶段占比 spec-review 43% / impl 29% / ff 11% / grill 6% / code-review 5% / done 0%。成本双峰印证（大 change 评审占比低、小 change 高）。
- **门槛定案**：见 requirements §5 表——**P2 主指标 = token 下降**（非墙钟）；P2 墙钟降级为「不回归」；安全「误免率恒 0 + fail-closed」；砍镜闸门「出现轮数≥10 ∧ 独立率<20% ∧ 采纳率<50% 连续 2 窗」。
- **对下游的改写**（design D11/D12）：① P2 从「省墙钟+token」收窄为 token play（机械镜非聚合墙钟关键路径、且被人类门 elapsed 淹没）；② 墙钟真杠杆归 Leg3；③ 价值锚太薄（3/18、轮数全<10），现阶段**禁砍任何镜**，接地镜独立率 75% 尤须 fail-closed 保护。

---

## 阶段 2 · 档位矩阵强制落地 + 机械镜降档（Leg 2，交叉审 #11/#12/#15/#22/#25/#26 + explore 2026-07-06）

### 前置条件
P0 基线（判机械镜是否在关键路径、验收有基准）。

### 目标
把 `model-tiers.md` 从**单列 3 档**（只有 canonical 缺省）升成 **`档位 × 运行时` 矩阵**，并让 SKILL fan-out **报档位、不写死模型名**——机械镜实降到 light 档（**主收益 = 省 token**；墙钟**不回归**即可，P0 基线证伪其墙钟杠杆，见 D11），judgment 镜/裁决/门禁不动。

> **explore 挖出的真相（2026-07-06）**：机械镜（接地/历史）在 `model-tiers.md` 里**早已映射到 light**，但**无任何脚本强制**——SKILL fan-out 不带 per-镜 `model=`，Agent 子代理**继承父 session（opus）**。故"文档说 light、实际大概率跑 opus"。P2 的真实内容**不是"引入快档"，是把 advisory 档位变成强制落地**（顺带把 opus→light 的 token 省下来，这比墙钟收益更实在）。

### 档位矩阵（3 档 × 运行时，取代单列表）

```
        │ Claude Code │ Codex     │ config.yaml 可 per-repo 覆盖任一格
────────┼─────────────┼───────────┼──────────
strong  │ opus        │ gpt-5-high│  裁决/门禁/verify/终审（永不降）
mid     │ sonnet      │ gpt-5     │  判断镜/对抗镜/生成/实现 + 置信打分（★light→mid 上移）
light   │ haiku       │ gpt-5-mini│  机械查证需读懂：接地镜/历史镜
```

- **置信打分 light→mid（交叉审 A2/#11/#26，采纳）**：它**丢弃 findings**（<80）、有判断权重、会误杀真 finding——不配 light，用现有 mid 接住（**不新增档**）。
- **不写死 haiku（用户 #1）**：档位是相对机队的相对词（adr/0006）；SKILL 只报「light 档」，主 session 经 resolver 查矩阵 → 按**当前运行时列** → 解析字面模型 → 传 Agent `model=`。config.yaml `model-tiers` 段可覆盖任一格。
- **硬约束（explore 边界）**：Claude Code 的 Agent `model=` 只吃 `{opus,sonnet,haiku,fable}` 字面名——**codex 不在此 enum**。矩阵「Codex 运行时」列指**整个工作流跑在 Codex host 时**镜子用什么，**不是**"在 Claude host 里把某镜换成 codex"（跨运行时只能走 outside-voice.sh 子进程路，非普通镜档位）。
- **升级档延后**：曾想加一个更高档（Fable/主力档动态升级 sonnet→opus 应对超复杂）——当前无需求，留档（见 todolist），不进本矩阵。

### 子任务
- `model-tiers.md` 重构为矩阵 + 补「延迟也是选档理由（不只省钱）」+ **明确哪些任务绝不允许 light（判断/裁决/置信打分）**。
- `sdflow-spec-review` / `sdflow-code-review` fan-out：mechanical 镜显式**报档位**，主 session resolver 解析运行时列后传 `model=`（永不硬编码模型名）。
- **fail-closed（交叉审 #12/#22）**：无法确认实际运行档位 / 降档调用失败 → **退回强档强审**，不静默降级。
- **P2b 后台小尾巴（原独立阶段，已降级）**：**仅 spec-review→设计门**那段值得后台化（人须等报告拍板）；**code-review 阶段三无人类门（P3e）人本就能走开，不做**；harness 已有完成通知（半免费），只需把 spec-review fan-out 派成不阻塞主 session。

### 验收
- 机械镜实际跑 light 档（可查运行档位）；判断镜/置信打分/裁决仍 mid/strong（不误降）。
- 降档不可用时可观测地退回强审（fail-closed 可测）。
- **主验收 = token 实测降**（opus→light，per-镜 token/轮下降）；墙钟对 P0 基线**不回归**即可（不设下降门槛，P0 收口 D11：机械镜非聚合墙钟关键路径）。

### 交付物
`model-tiers.md` 矩阵重构 + 两评审 skill fan-out 档位报告/解析 + config.yaml 覆盖段说明，`/sdflow-upgrade` 激活。

---

## 阶段 3 · 接地镜流水线（Leg 2，交叉审 #16/#17/#18）

### 前置条件
P2 落地后（档位矩阵 + 观测在手，流水线更稳）。

### 目标
放松「fan-out 必等 Step1 autoplan 完」的串行纪律**仅对接地镜**——它核代码事实、不依赖 autoplan 的设计 findings，可提前并行起跑。

### 子任务
- `sdflow-spec-review` 串行纪律精化：区分「依赖 autoplan amendment 的镜」（领域/对抗，仍等）vs「不依赖的接地镜」（可与 autoplan 并行）。
- **边界守卫强化（交叉审 #16/#17，采纳）**：autoplan amendment 不只**改动**已有代码事实，还可能**新增核验目标**（新 scope/新需求）——提前跑的接地镜对新增目标是"从没看过"、非"漏了增量"。Step3 裁决 MUST diff autoplan amendment 的**新增 + 改动**两类核验对象，新增目标触发接地镜补跑，不得只做改动增量核对。
- **成本诚实（交叉审 #18）**：提前跑的接地镜若被 amendment 作废需补跑——省墙钟可能增 token，P0 门槛须含 token 侧，净收益为正才落地。

### 验收
- 接地镜可与 autoplan 并行起跑，串行等待段对基线缩短。
- amendment **新增**核验目标的场景，接地镜补跑不漏（非仅改动增量）。

### 交付物
`sdflow-spec-review/SKILL.md` 串行纪律条款更新。

---

## 阶段 4 · 批次策略：相关合批 + 大扫除批（Leg 3，交叉审 #7/#20/#21，✅ 已交付）

### 状态
**已完成并归档**。change `batch-triage-strategy`（plan → impl 3 → code-review 8 自修 → verify → archive + merge `725caf3`）交付全部子任务。
- **设计偏移（spec-review Q2 定案）**：判据规则**未进 bundle**——落 `openspec/issues/batch-triage-rules.md`（**本仓-local**），冷源接地证实原「workflow 规则/bundle 回灌」是事实性错误；**向下游发布 deferred**（对齐 Leg1：本仓 dogfood 验证有效才进 bundle）。判据=**纯规则 checklist、无 scripts/无 pytest**。
- **本仓 dogfood caveat**：本仓多数 issues debt 落行为面文件（SKILL.md/bundle）→ 大扫除批**候选池薄**，其在本仓实际价值待 dogfood 实测（见 change §5.4 注记）。

### 前置条件
无。

### 目标
把「降轮次」的批次判据规则化：相关合批（已有 AND 门）+ 新增琐碎正交「大扫除批」+ 正交批安全边界**+ 聚合上限**。

### 子任务
- `consolidation-plan.md` 按框架重划：相关项走 AND 门；散落琐碎正交项归「大扫除批」。
- workflow 规则补「大扫除批」定义 + **硬边界（交叉审 #20/#21，采纳）**：
  - 正交批只装个体琐碎/低危项，禁装逻辑面（判据**同类于** Leg1 白名单——但**注意 #7**：P4 是 issue 级 pre-diff，不能**字面**复用 `trivial_shape.py`（它需 diff）；是"同类判据、非同一脚本"，P4 设计时另立 issue 级近似判据）。
  - **聚合上限**：每项低危≠聚合低危——限**文件数 / 目录跨度 / 是否含生成物 / CI 面积**，防 30 个散 typo 压垮 review 注意力 + 坏 bisect/revert 粒度。

### 验收
- consolidation-plan 有明确「相关批 vs 大扫除批」划分。
- 规则文件有正交批安全判据 + 聚合上限，且与 Leg1「无逻辑面」判据同类、可交叉引用。

### 交付物
`consolidation-plan.md` 重划 + workflow 规则补批次判据。

---

## 阶段 C · tasks 受限并行 frontier（占位，待启）

> 目标：让 tickets 管线的工作 frontier 从首版严格串行放宽为受限并行（T118 受限并行部分），以 `matt-workflow-integration` 试点判赢（Phase A 判据三条过，见其 `pilot-briefing.md`）为硬前置。
> 雾区备注：具体设计信息目前空缺——每 ticket 分支下 gate 完成窗口的可见性契约尚未设计（当前 gate 完成窗口 = 当前分支 `[plan_first_sha, HEAD]` 闭区间，受限并行下每 ticket 分支的 checkpoint 标签在合回主分支前不可见、`done_tasks` 系统性少算，是契约级改动；`matt-workflow-integration` proposal Non-Goals 已声明此缺口）。具体设计留待启动时另行 explore，本 roadmap 不在此展开。

---

## 阶段依赖图

```
  P1 (Leg1) ✅ 已交付
  P0 (Leg2 基线/照妖镜) ──┬──▶ P2 (档位矩阵强制落地 + 机械镜降档, 含 P2b 后台小尾巴, fail-closed)
                          │          │
                          │          ▼
                          └──▶ P3 (接地镜流水线, P2 后更稳)
  P4 (Leg3 批次) ──独立──▶ ✅ 已交付（batch-triage-strategy merged 725caf3）
```

- **P0 是 P2/P3 的前置**（无基线不立项；且 P0 双峰数据可能直接告诉你 P2 只对小 change 值得）。
- **P2/P3 同改两评审 SKILL.md → MUST 串行**（并行 caveat #29）。
- P4 触及 `consolidation-plan.md`/`ff-generation-constraints.md`，与 P2/P3 文件互斥 → 可与之并行。

**建议次序（v4 更新，P4 已交付）：~~P4~~ ✅ 已归档 → 余 P2（档位矩阵，主收益 token）先做 → P3（流水线，调度复杂度最高，压后）**。原 v3 建议「P4 ＋ P2 并行」中的 **P4 已由 `batch-triage-strategy` 独立交付**（P0 数据把 Leg3 从「随时可做的轻策略层」提为「墙钟主杠杆」，故先落）；剩 P2/P3 走 Leg2 串行区——P2 先（档位矩阵 + 观测在手），P3 压后（先有 P2 观测/矩阵再进串行调度区，交叉审 #30）。**注意 P2/P3 同改两评审 SKILL.md，MUST 串行。**
