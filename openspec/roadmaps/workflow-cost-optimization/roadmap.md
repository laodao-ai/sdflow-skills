# workflow 成本优化 实施路线图

> 版本：v2（2026-07-06，吸收 plan-eng-review 交叉审：codex 冷审 30 条去重后 9 组采纳）
>
> 相关文档（均位于 `openspec/roadmaps/workflow-cost-optimization/`）：
> - 需求综述：`requirements.md` · 整体设计：`design.md` · 任务日志：`task-log.md`

## 概览

三腿并行、非强依赖（各自独立可交付）。**Leg 1（P1）已完成并激活**（change `adaptive-workflow-routing` 已 merge + `/sdflow-upgrade`）。Leg 2 收益最直接，但**先做 P0 阶段级基线采样**——没有基线就无法判断 P2/P3 的调度复杂度是否换来真收益（交叉审 #23/#24）。Leg 3 是策略/文档层，随时可做。

| 阶段 | 归属 | 依赖 | 里程碑 |
|---|---|---|---|
| **P1** · code-review 无逻辑面白名单免 Step2 | Leg 1 | —（已交付） | ✅ 三类形状免多镜 + 反误免可测（trivial_shape.py + 34 测试，已 merge） |
| **P0** · 阶段级墙钟基线采样 | Leg 2 前置 | 无 | checkpoint 时间戳收成 per-阶段/per-change 类型基线 + 设收益门槛（Leg2 前置，近乎免费） |
| **P2a** · 机械镜换快档 | Leg 2 | P0 | 机械镜跑快档、**fail-closed 退回强审**、墙钟对基线降 |
| **P2b** · fan-out 后台 + 通知 | Leg 2 | 无 | fan-out 后台派发、完成 ping、人不阻塞（调度机制改，与 P2a 风险不同故拆分） |
| **P3** · 接地镜流水线（放松串行纪律） | Leg 2 | P2a 后更稳 | 接地镜与 autoplan 并行、**autoplan 新增核验目标不漏** |
| **P4** · 批次策略：相关合批 + 大扫除批 | Leg 3 | 无 | consolidation-plan 重划 + 正交批安全判据**+ 聚合上限** |

> 每阶段开独立 OpenSpec 变更（`implement-workflow-cost-optimization-pN` 或语义名），完成归档后进下一个。
> **并行 caveat（交叉审 #29）**：P0/P1/P4 触及互斥文件可并行；**P2a/P2b/P3 均改 `sdflow-spec-review`/`sdflow-code-review` 的 SKILL.md，MUST 串行**（否则并行改同批规则→审查上下文错位 + merge 冲突）。开并行 leg 前先核文件集是否相交。

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

---

## 阶段 2a · 机械镜换快档（Leg 2，交叉审 #12/#15/#22/#25/#26）

### 前置条件
P0 基线（判该镜是否在关键路径、验收有基准）。

### 目标
把**纯机械查证类**镜（接地镜 / 历史镜）跑快档模型，压缩关键路径延迟。**判断镜（领域/对抗）绝不动。**

> **⚠️ 置信过滤剔出快档集（交叉审 #11/#26，采纳）**：置信过滤会**丢弃 findings**（<80），是安全关键路径，弱档=假绿——直接违反本设计"判断镜换快档禁"原则。故 P2a 的机械快档集**只含接地镜/历史镜**，置信过滤留强/中档。

### 子任务
- `sdflow-spec-review` / `sdflow-code-review` 的镜档位映射：接地/历史镜显式指快档；`model-tiers.md` 补「延迟也是选档理由（不只省钱）」+ **明确哪些任务绝不允许弱档（判断/裁决/置信过滤）+ 弱档输出必须带的证据**。
- **fail-closed（交叉审 #12/#22）**：无法确认实际运行档位 / 快档调用失败 → **退回强档强审**，不静默降级。

### 验收
- 机械镜实际跑快档（可查运行档位）；判断镜/置信过滤仍强/中档（不误降）。
- 快档不可用时可观测地退回强审（fail-closed 可测）。
- 该镜墙钟对 P0 基线下降（多轮同基线）。

### 交付物
两评审 skill 镜档位映射 + `model-tiers.md` 更新，`/sdflow-upgrade` 激活。

---

## 阶段 2b · fan-out 后台 + 通知（Leg 2，交叉审 #15）

### 前置条件
无（与 P2a 独立；但与 P2a/P3 同改 SKILL.md，须串行安排）。

### 目标
把 fan-out 子代理后台派发、完成 ping，把「人干等 5-10min」变非阻塞。**注意：这降的是人的阻塞感、不是 workflow 实际完成更快（交叉审 #10）**——与 P2a 的真墙钟收益分开记账。

### 子任务
- fan-out 默认后台派发 + 完成通知；主 session 综合仍等齐（屏障保留）。
- **失败回退（交叉审 #22）**：后台任务挂起/通知丢失/并行结果不一致 → 可观测退回，不让评审悄悄少跑一镜。

### 验收
- fan-out 后台跑、完成 ping；人阻塞时间降（非 workflow 墙钟，分开度量）。
- 后台异常有回退，不静默丢镜。

### 交付物
两评审 skill fan-out 调度段更新，`/sdflow-upgrade` 激活。

---

## 阶段 3 · 接地镜流水线（Leg 2，交叉审 #16/#17/#18）

### 前置条件
P2a 落地后（快档 + 观测在手，流水线更稳）。

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

## 阶段 4 · 批次策略：相关合批 + 大扫除批（Leg 3，交叉审 #7/#20/#21）

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

## 阶段依赖图

```
  P1 (Leg1) ✅ 已交付
  P0 (Leg2 基线采样) ──┬──▶ P2a (机械镜快档, fail-closed)
                       │          │
                       │          ▼
                       └──▶ P3 (接地镜流水线, P2a 后更稳)
  P2b (fan-out 后台) ──独立──▶ 交付   （但与 P2a/P3 同改 SKILL.md → 三者串行）
  P4 (Leg3 批次) ──独立──▶ 交付
```

- **P0 是 P2a/P3 的前置**（无基线不立项）。
- **P2a/P2b/P3 同改两评审 SKILL.md → MUST 串行**（并行 caveat #29）。
- P4 触及 `consolidation-plan.md`/`ff-generation-constraints.md`，与 P2/P3 文件互斥 → 可与之并行。

**建议次序：P0（基线，近乎免费）→ P2a（快档试点，收益最直接）→ P4（策略层，轻，可与 P2 并行）→ P2b（后台）→ P3（流水线，调度复杂度最高，压后）**。较原 v1「P2 整块提前」更稳——先建观测、再进调度复杂区（交叉审 #30）。
