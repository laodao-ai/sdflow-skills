# workflow 成本优化 实施路线图

> 版本：v1（2026-07-06）
>
> 相关文档（均位于 `openspec/roadmaps/workflow-cost-optimization/`）：
> - 需求综述：`requirements.md` · 整体设计：`design.md` · 任务日志：`task-log.md`

## 概览

三腿并行、非强依赖（各自独立可交付）。**Leg 1 已在途**（change `adaptive-workflow-routing`）。Leg 2 收益最直接、最易落，建议紧随。Leg 3 是策略/文档层，随时可做。

| 阶段 | 归属 | 优先级 | 依赖 | 里程碑 |
|---|---|---|---|---|
| **P1** · code-review 无逻辑面白名单免 Step2 | Leg 1 | P1 | 无（在途） | 三类形状免多镜 + 反误免可测 |
| **P2** · 机械镜换快档 + 全后台通知 | Leg 2 | P1 | 无 | 机械镜跑快档、fan-out 后台，墙钟降 |
| **P3** · 接地镜流水线（放松串行纪律） | Leg 2 | P2 | P2 后更稳 | 接地镜与 autoplan 并行、串行段缩 |
| **P4** · 批次策略：相关合批 + 大扫除批 | Leg 3 | P2 | 无 | consolidation-plan 重划 + 正交批安全判据入规则 |

> 每阶段开独立 OpenSpec 变更（`implement-workflow-cost-optimization-pN` 或语义名），完成归档后进下一个。P1 已用 `adaptive-workflow-routing` 承载（名不同，历史原因，见 task-log）。

---

## 阶段 1 · code-review 无逻辑面白名单免 Step2（Leg 1，在途）

### 前置条件
无（change `adaptive-workflow-routing` 已过 grill+spec-review+设计门 Q1=A）。

### 目标
让**机判可证零产出**的三类形状免 code-review Step2 多镜，Step1 恒跑守卫。

### 子任务（= 该 change 的 tasks）
- 无逻辑面形状判器（语言感知 + 行为面路径豁免 + load-bearing 版本常量守卫）+ pytest
- `sdflow-code-review/SKILL.md` Step2 接入
- spec-workflow code-review 需求 MODIFIED（原标题）

### 验收
- 纯注释/纯文档路径/仅加 tests/纯展示版本号 → 命中免 Step2、仍产报告。
- 改 `SKILL.md`/`workflow.md`/`ship_gate.py` 一行（形状似 markdown）→ 行为面路径命中 → 照跑多镜。
- `API_VERSION=2`/`conftest.py` → 不误入白名单。
- 伪装成注释的逻辑改 → Step1 scope-drift 揭穿 → 照跑。

### 交付物
change `adaptive-workflow-routing` merge + `/sdflow-upgrade` 激活。

---

## 阶段 2 · 机械镜换快档 + 全后台通知（Leg 2）

### 前置条件
无。

### 目标
把机械查证类镜（接地/历史/置信过滤）跑快档模型，并把 fan-out 后台化，压缩每轮墙钟与人等待。

### 子任务
- `sdflow-spec-review` / `sdflow-code-review` 的镜档位映射：机械镜显式指快档；`model-tiers.md` 补「延迟也是选档理由」的说明（不只省钱）。
- fan-out 子代理默认后台派发 + 完成通知（把「人干等」变非阻塞）；主 session 综合仍等齐（屏障保留）。

### 验收
- 机械镜实际跑快档（可查运行档位）；判断镜仍强/中档（不误降）。
- fan-out 后台跑、完成 ping；一轮墙钟对照实测下降（同一 change 前后对比，粗粒度阶段级时长）。

### 交付物
两评审 skill + `model-tiers.md` 更新，`/sdflow-upgrade` 激活。

---

## 阶段 3 · 接地镜流水线（Leg 2）

### 前置条件
P2 落地后（后台机制在手，流水线更稳）。

### 目标
放松「fan-out 必等 Step1 autoplan 完」的串行纪律**仅对接地镜**——它核代码事实、不依赖 autoplan 的设计 findings，可提前并行起跑。

### 子任务
- `sdflow-spec-review` 串行纪律精化：区分「依赖 autoplan amendment 的镜」（领域/对抗，仍等）vs「不依赖的接地镜」（可与 autoplan 并行）；对码核验对象取 change 产物 + 真实代码（autoplan 不改这些）。
- 边界守卫：若 autoplan amendment 改到了接地镜要核的代码事实，Step3 裁决 diff 增量核对（承现有「历史并行则增量核对」条款）。

### 验收
- 接地镜可与 autoplan 并行起跑，串行等待段实测缩短。
- amendment 改到代码事实的场景，增量核对不漏。

### 交付物
`sdflow-spec-review/SKILL.md` 串行纪律条款更新。

---

## 阶段 4 · 批次策略：相关合批 + 大扫除批（Leg 3）

### 前置条件
无。

### 目标
把「降轮次」的批次判据规则化：相关合批（已有 AND 门）+ 新增琐碎正交「大扫除批」+ 正交批安全边界。

### 子任务
- `consolidation-plan.md` 按今天的框架重划批次：相关项走 AND 门；散落琐碎正交项归「大扫除批」。
- workflow 规则（`ff-generation-constraints.md` 或 fold-vs-defer 判据处）补「大扫除批」定义 + 硬边界（正交批只装个体琐碎/低危、禁装逻辑面、判据同 Leg1 白名单类）。
- （可选）issues 层记「大扫除批」为一种批次类型。

### 验收
- consolidation-plan 有明确的「相关批 vs 大扫除批」划分。
- 规则文件有正交批安全判据，且与 Leg1「无逻辑面」判据同源、可交叉引用。

### 交付物
`consolidation-plan.md` 重划 + workflow 规则补批次判据。

---

## 阶段依赖图

```
  P1 (Leg1, 在途) ──独立──▶ 交付
  P2 (Leg2 快档+后台) ──▶ P3 (Leg2 流水线, P2后更稳)
  P4 (Leg3 批次) ──独立──▶ 交付
```

P1/P2/P4 互不阻塞，可并行推进；P3 建议在 P2 后。**建议次序：P1（收尾在途）→ P2（收益最直接）→ P4（策略层，轻）→ P3**。
