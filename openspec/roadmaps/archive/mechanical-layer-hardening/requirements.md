# workflow 机械层固化 需求综述

> 版本：v1（2026-07-07）
> 作者：cheneyzhao（+ AI 协作）
> 状态：DRAFT
>
> 相关文档（均位于 `openspec/roadmaps/mechanical-layer-hardening/`）：
> - 整体设计：`design.md`
> - 实施路线图：`roadmap.md`
> - 任务日志：`task-log.md`
>
> 承载变更：`plan-mechanical-layer-hardening`（归档后见 `openspec/changes/archive/`）
>
> （`memo.md` 是考古备忘，**四件套不引用**——本节故意不列它。）

## 1. 背景与愿景

### 1.1 项目定位

本仓（sdflow-skills）的领域即 **spec 工作流本身**。本 roadmap 是这条工作流的**机械层固化长期规划**——把当前「靠模型跑 prose 协议 / 靠模型手数 / 靠字符串编码嵌 markdown 正文」的机械活，逐步固化成**确定性脚本 + 结构化状态**，让「机械活交脚本、模型只做判断」从口号落成硬约束。

它与姊妹 roadmap `workflow-cost-optimization` 正交：那条优化**成本**（token/墙钟/轮次），这条固化**正确性/可靠性**（消灭静默跳步、字符串解析歧义、手数误差、镜像漂移）。

### 1.2 为什么需要做

**根契约已声明、只是没执行完**：`openspec/CONTEXT.md` 的 adr/0006 已把「凡机械 prose 协议（路径解析、回落链、步末固定动作）**MUST 脚本化 / 结构化**」定为**硬约束**（不是可选优化，是「机械活交脚本、模型只做判断」的升格）。动机是**反静默元原则**——弱档模型跑 prose 协议的典型失效 = **静默跳步**，与反静默守卫正面冲突且不留痕迹。本 roadmap 就是这条已声明契约的**完整执行面**。

四类实证痛点（不是假想）：

1. **字符串编码致解析歧义 → P1 gate bug**：ship-gate 状态锚 inline 嵌报告正文，逼 gate 堆一整套 fence-aware + 独占行 + line-scoped 解析去区分「正文提及 vs 真标记」。已出两个实证 bug——B4（`anchors_in` 子串命中正文描述句 → 设计门假过）、B5（契约测试用子串当 ground-truth 撞 prose-inline → 误红）。B5 的聚合不变量补丁是旧架构里绕过，非根治。
2. **模型手数 → 自认「信任边界」**：lens-metric 逐镜计数（`findings/采纳/裁掉/独立`）由模型手折叠 + 手写锚，两审 SKILL 反复声明「数值一致性 = 主 session 信任边界、自核无独立性」——即承认会错，只是没脚本兜底。
3. **镜像漂移无守卫**：三 recorder（buglist/todolist/issues）间 ~10 个 verbatim helper「逐字同款、刻意不互相 import」（D4 红线），只靠 docstring 注释「镜像 buglist」维系，**无一致性测试**（仅终态集有）——改一处忘另一处即静默漂移。
4. **手循环 / 无 schema 兜底**：done sweep 的 issues 分诊是模型手跑 4 步 bash 循环（SKILL 自认「纯机械 bash」）；`config.yaml` 无任何 validator（消费仓打错 `model-tiers` 子键/坏 yaml 无兜底）。

### 1.3 愿景

- **机械活归脚本**：确定性的判据（枚举/集合/正则/时间戳比较/子串匹配/表↔文件 set-diff）一律脚本 own，模型不再手 grep、手数、手循环。
- **机器状态归结构**：整块、有正文歧义风险、有专门解析机的机器状态迁 YAML frontmatter，正文再怎么提及锚串都不会被误当标记，整类解析机器可删。
- **判断权留人/模型**：脚本只做机械归约，「是不是同一条 finding、这需求代码有没有真实现、几级、方案取舍、砍哪镜」永远留给模型/人——每个候选都显式切出判断部分保留。
- **反静默是红线**：固化 MUST NOT 引入新的静默面（如 LLM 写坏 YAML 被 `safe_load` 静默吞）——失败要响亮、fail-closed。

## 2. 核心需求（做什么）

两条腿，同归 adr/0006：

| ID | 需求 | 优先级 | 归属腿 |
|---|---|---|---|
| R1 | **机械活脚本化**：把编排 SKILL 里模型手做的确定性步下沉给脚本（sweep / anchor-lint / 镜像一致性测试 / config·batches lint / 日志判定 等） | P1 | Leg 1（脚本化） |
| R2 | **去字符串化机器状态**：整块+歧义风险+有解析机的字符串状态迁结构化（家族① gate 锚 → frontmatter；家族② recorder 索引 → frontmatter） | P1（S1）/ P3（S2） | Leg 2（去字符串化） |
| R3 | 贯穿：每个候选**显式切出判断部分保留给模型/人**，脚本只 own 机械归约；固化不引入新静默面 | P0 | 全局原则 |

## 3. 不做什么（Non-Goals）

- **不搬位置相关的逐条 inline tag（家族③）**——`[impl-review-fix]` / `〔TG-N〕` / `task<N>-` checkpoint / item ID：语义绑定所在句/所在行或载体是 git commit subject（非 markdown 正文），frontmatter 不适用。
- **不搬模版槽位占位（家族④）** `<待填>` 等——占位符必须在其结构位置上，本就是待人填的正文槽。
- **不迁已半结构化的度量锚**（lens-metric / outside-voice / hr-tg / step1-broad-review）——已是 HTML 注释内严格 KV + fence 护栏压住歧义，迁 frontmatter 净收益远低于家族①；只补**产出侧 lint**（属 Leg 1），不改载体。
- **不脚本化真判断步**——「这是不是同一条 finding（去重）/ 对抗裁决 / 置信打分 / 这需求代码有没有真实现 / 砍哪镜」是模型/人的活，不是机械活。
- **不动 retro 的「供数不供裁决」停手点**——`retro_report.py` 只列不砍是**设计正确的停手**，非 gap。
- **不追求「一次全做完」**——按就绪度/ROI/爆炸半径分阶段，每阶段一次 change 归档后再进下一个。

## 4. 受众

- **主**：跑本工作流的开发者（本人）——直接受益于少手数/少漏步/少静默腐蚀。
- **次**：未来在消费仓用这套 bundle 的项目 + 维护 bundle 的 AI 助手（尤其消费仓 `config.yaml` lint 直接护他们）。

## 5. 验收总纲（各阶段细化见 roadmap.md）

- **Leg 1（脚本化）**：每个下沉候选——① 脚本 own 的判据是确定性的（枚举/集合/正则/set-diff）且有 pytest 覆盖；② 判断部分显式保留给模型/人（不被脚本越权）；③ 失败 fail-closed 不静默。首批 P1（`issues.py sweep`）+ P2（anchor-lint）就绪即可交付。
- **Leg 2（去字符串化）**：
  - **S1（家族① gate 锚，就绪需先评 ROI）**：先核实 `ship_gate.py` 真实铺设路径（现只在 `sdflow-ship/scripts/`，不在 T65 假设的 bundle 路径 → 爆炸半径可能被高估）；迁移后 gate **删得掉** `_line_scoped_hits` 那套解析机器、正文提及锚串不再误判；**57 篇归档报告 inline 锚的 dual-read 兼容窗口**明确；LLM 写坏 YAML 有 fail-closed 兜底（不比缺 inline 锚更糙）。
  - **S2（家族② recorder 索引，north-star）**：**不排期**——ROI 触发器 =「recorder 持续出腐蚀 bug，或想在数据上建工具」满足才立项（ADR 0010 已决）。达标标志：结构化后腐蚀类蒸发 + 删掉 recorder ~40 处/文件表解析与双写一致机械。
- **全局（R3）**：任一固化不得引入「异常被静默吞 + exit 0」的新静默面；新脚本/结构对坏输入 fail-closed 且可观测。

## 6. 参考文档

- **`design.md`** — 架构（两腿 × adr/0006 根契约）、决策、候选清单全表、风险与回滚、Q&A 已决议
- **`roadmap.md`** — 阶段划分（Leg1 脚本化优先 → Leg2 去字符串化就绪度分级）× 每阶段前置/目标/子任务/验收
- **`task-log.md`** — 实施过程日志（初始记规划产出本身）
- **`openspec/changes/archive/<date>-plan-mechanical-layer-hardening/`** — 本 roadmap 产出时的 SDD 变更盒子（已归档）
- **根契约**：`openspec/CONTEXT.md`（adr/0006 机械 prose MUST 脚本化/结构化 · 盘面即状态 · 反静默元原则）、`openspec/adr/0010`（家族② reject-over-restructure 的低成本前置桥 + Path B defer）
