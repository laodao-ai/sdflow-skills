# workflow 成本优化 需求综述

> 版本：v1（2026-07-06）
> 作者：cheneyzhao（+ AI 协作）
> 状态：DRAFT
>
> 相关文档（均位于 `openspec/roadmaps/workflow-cost-optimization/`）：
> - 整体设计：`design.md`
> - 实施路线图：`roadmap.md`
> - 任务日志：`task-log.md`
> - 讨论备忘：`memo.md`（考古用，四件套不引用）
>
> 承载变更：`plan-workflow-cost-optimization`（归档后见 `openspec/changes/archive/`）

## 1. 背景与愿景

### 1.1 项目定位

本仓（sdflow-skills）的领域即 **spec 工作流本身**：一个 OpenSpec 变更 ff→grill→spec-review→实现→code-review→done→merge 的连续自动流水线。本 roadmap 是这条流水线的**成本优化长期规划**——在不牺牲评审安全的前提下，把每次跑工作流的代价降下来。

### 1.2 为什么需要做

每轮评审重、慢，逼出「合批摊薄固定成本」的诱惑，进而诱发「往一个 change 塞太多」的反模式。三类成本痛点：

1. **token / 模型成本**：每轮 fan-out 多个子代理，强档模型贵。
2. **时间 / 墙钟**：一轮 spec-review/code-review 跑 5-10 min，人常干等。
3. **轮次**：一个改动一个 change，每个 change 付一整套 ff→…→merge 的固定编排开销。

### 1.3 愿景

- **成本随「逻辑面」自适应**：琐碎/无逻辑面的东西怎么省都安全；有逻辑面的东西省不了、但能摊薄+提速。
- **安全是红线**：一个刚跑完的 dogfood 教训——4 个独立冷源抓出了 grill 阶段漏掉的地基级问题，**证明「独立冷镜层」load-bearing**。降成本 MUST NOT 靠砍评审安全。

## 2. 核心需求（做什么）

| ID | 需求 | 优先级 | 归属 Leg |
|---|---|---|---|
| R1 | 对**机判可证零损失**的形状免多镜（不砍安全的「跳」） | P1 | Leg 1 |
| R2 | 降每轮**墙钟**（机械镜换快档 / 接地镜流水线 / 全后台通知） | P1 | Leg 2 |
| R3 | 用**批次策略**降轮次（相关合批 + 琐碎正交大扫除批） | P2 | Leg 3 |
| R4 | 贯穿：一切优化以「逻辑面有无」为安全边界，不稀释评审 | P0 | 全局原则 |

## 3. 不做什么（Non-Goals）

- **不做**「有逻辑面的 routine change 轻量化」——已证不成立（diff 前无法机判语义复杂度、HR-TG 语义不可脚本化；见 `design.md` §放弃项 + change `adaptive-workflow-routing` 的 spec-review-report Q1）。
- **不砍**任何 load-bearing 评审层（grill / 独立冷镜 / verify 终门 / 设计门）。
- **不**把正交批当筐——正交批只装个体琐碎/低危项，禁装逻辑面。
- **不**追求 per-镜耗时数据驱动调优——harness 不暴露（adr/0009），只到阶段级。

## 4. 受众

- **主**：跑本工作流的开发者（本人）——直接受益于更快/更省的评审轮。
- **次**：未来在消费仓用这套 bundle 的项目 + 维护 bundle 的 AI 助手。

## 5. 验收总纲（各阶段细化见 roadmap.md）

- Leg 1：三类无逻辑面形状免 Step2 且反误免（改 SKILL.md/load-bearing 常量不误免）可测。✅ 已交付。
- Leg 2（前置）P0 基线：有 per-阶段墙钟基线（checkpoint 时间戳收成）+ **明确收益门槛数值**（如"某阶段 median 降 ≥X%"/"误免率恒 0"），作为 P2/P3 立项与验收判据。
- Leg 2：接地/历史镜跑快档（**置信过滤/判断镜不降档**）、接地镜可提前、fan-out 可后台——墙钟**对 P0 基线多轮下降**（非单次对比）；快档失败/后台异常**可观测 fail-closed 退回强审**，不静默丢镜。
- Leg 3：`consolidation-plan.md` 按「相关合批 + 大扫除批」重划，且有正交批安全判据 **+ 聚合上限（文件数/目录跨度/生成物/CI 面积）**。
