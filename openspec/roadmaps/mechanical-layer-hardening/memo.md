# workflow 机械层固化 讨论备忘

> 日期：2026-07-07
> 状态：FINAL
>
> ⚠️ **本文件仅作参考**：记录决策形成过程的对话式痕迹。正式文档（requirements/design/roadmap/task-log）**不引用本文件**。
>
> 阅读指引：想看最终决策 → `design.md` §决策 + §已决议档案；想看阶段计划 → `roadmap.md`；本文件保留考古现场感。

## 1. 摘要

从「去字符串化机器状态层」一个窄主题出发，经用户追问「workflow 还有哪些能结构化+脚本化」+ 3 镜并行 survey，收敛成一个**双腿 roadmap**（脚本化 + 去字符串化），同归 adr/0006「机械 prose 协议 MUST 脚本化/结构化」硬约束。

## 2. 问题陈述

起点：ADR 0010 和上一轮 hand-off 把「去字符串化机器状态层」预定义为两阶段（T65 gate 锚 + Path B recorder 索引）。但接地发现：
- T65 就绪（B4/B5 实证）但备注自己说「够格作 workflow-cost-optimization 一个阶段」+「别在清理惯性里反应式开工，先评 ROI」。
- Path B（家族②）**没有 todolist 条目**，只在 ADR 0010 作被明确 defer 的概念，ROI 触发器未满足。
- 即：原始 scope 只 ~1.5 个就绪阶段，且首阶段高仪式——单独起 4 件套偏空（roadmap 陷阱 1）。

## 3. 探索过程

### 3.1 第一次拍板（roadmap 边界）

问：新建 roadmap / 折进已有 / 只写 T65？→ 用户选 **新建 + 就绪度分级**（S1 就绪、S2 north-star）。理由：主线成立值得独立真相源，诚实标 S2 触发式非排期避免空洞。

### 3.2 用户追问触发 survey

用户：「还要调研一下，当前这个 workflow，还有哪些地方可以结构化+脚本化」。派 3 只读 Explore 镜并行盘点：
1. **机器状态字符串编码盘点**（家族①②③④ + gate 锚 + 度量锚 → 迁移适宜性）
2. **skill 可脚本化机械活盘点**（编排 SKILL 里模型手做的确定性步）
3. **现有脚本边界与缺口盘点**（脚本停手点 + 缺守卫不变量 + 半手结构化文件）

### 3.3 survey 关键认知

- **两条腿浮现**：去字符串化（改状态表示，家族①②）+ 机械活脚本化（活下沉给脚本，C1-C9 + 脚本 gap）。二者**都归 adr/0006 同一硬约束**（CONTEXT.md 已把「脚本化/结构化」并列）。
- **脚本化半更就绪、ROI 更高、爆炸半径更低**：P1（issues.py sweep）SKILL 自认「纯机械 bash」、P2（anchor-lint）复用现成纯函数；而去字符串化首阶段 T65 高仪式、S2 已 defer。
- **共享锚层**：anchor-lint（度量锚）与 anchor-frontmatter（gate 锚）是同一层两种动作——分家会割裂推理。
- **⚠️ ship_gate.py 只在 `sdflow-ship/scripts/`**，不在 T65 假设的 bundle 路径 → 爆炸半径可能被高估（关键计划外事实）。
- **度量锚（lens-metric/outside-voice/hr-tg/step1）已半结构化**（注释内严格 KV + fence 护栏），迁 frontmatter 净收益低 → 只补 lint 不换载体。

### 3.4 第二次拍板（scope）

问：守窄只做去字符串化 / 拓宽成双腿 / 两个独立 roadmap？→ 用户选 **拓宽成双腿**。理由：adr/0006 本把两者并列；共享锚层一起推理；首批可执行阶段落在就绪的脚本化项，roadmap 不空。改名「机械层固化」。

## 4. 核心决策（快照，完整见 design.md §3）

- **D1** 两腿同一 roadmap（不拆两个、不并入 cost-optimization）。
- **D2** Leg1 脚本化先于 Leg2 去字符串化（就绪/ROI/爆炸半径三维排序）。
- **D3** 去字符串化只搬家族①②；度量锚只补 lint 不迁载体。
- **D4** 家族③④ 留 inline（位置即语义 / git subject）。
- **D5** 每脚本化候选切出判断留模型/人。
- **D6** S1 预置 dual-read 窗口 + LLM 坏 YAML fail-closed。
- **D7** recorder 镜像用一致性测试兜底（不破 D4 禁 import 红线）。

## 5. 决策汇总

| 议题 | 决策 | 状态 |
|---|---|---|
| roadmap 边界 | 新建 + 就绪度分级 | ✅ 已定 |
| scope | 双腿（脚本化 + 去字符串化） | ✅ 已定 |
| 命名 | mechanical-layer-hardening | ✅ 已定 |
| 阶段顺序 | Leg1（P1-P4）→ Leg2 S1（P5，前置 ROI 门）→ S2（P6，north-star） | ✅ 已定 |
| S1 是否真开工 | 前置 ROI 评估门（现数据点 B4/B5），S1 起手先评 | ⏳ 未决（留 change 起手） |
| ship_gate 铺设路径 | S1 起手第一步核实 | ⏳ 待核 |
| S2 触发 | 被动，ROI 触发器满足才起 | ⏳ 不排期 |

---

## 附录：为什么保留这份文件

- 记录「原始窄 scope（只去字符串化）→ 用户追问 → survey → 拓宽双腿」的演化，未来若问「为什么脚本化和去字符串化在一个 roadmap」，这里是答案。
- 保留 ship_gate 路径这个计划外事实的发现语境（T65 备注写错了 bundle 路径）。
- 三镜 survey 的完整候选清单已精炼进 design.md §候选全表；本 memo 只留决策演化，不重复清单。
- 如未来 design.md §决策 完全吸收本 memo，可删。
