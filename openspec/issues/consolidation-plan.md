# Issues 合批路线图（按目标功能重切 + fold-vs-defer 合批建议）

> **定位**：`batches.md` 按「哪个 change 发现的」切批；本文件把待处理项按**目标功能域**重新聚拢，
> 找出「一个 change 清 2-3 批」的合批机会。判据 = BASE-18 fold-vs-defer 防吸积 AND 门
> （`同 capability ∧ 高耦合 ∧ 低增量` 三者皆满足才 fold）。
> 生成于 2026-07-05；数据源 = `todolist.py scan` + `batches.md`。待处理 38 项（bug 全 FIXED）。

## 一、当前待处理 38 项 · 按目标功能

| 功能域 | 项 | 数 | 现所在批 |
|---|---|---|---|
| **G1 记录三件套**（issues.py/recorder） | T1 T2 T3 T4 T5 | 5 | issues-pool-batch-mgmt |
| **G2 Toolkit 安装/解析**（setup.sh/resolver/hook/跨平台/软链） | T6 T12 T13 T14 T15 T16 T17 T18 · T23 T24 | 10 | minimize-repo-footprint · sdflow-rebrand |
| **G3 评审规则层**（spec/code-review/grill 规则） | T7 T8 T9 · T19 | 4 | minimize-repo-footprint · sdflow-rebrand |
| **G4 Gate & checkpoint 契约**（ship_gate.py + 标签） | T26 · T35 T36 · T37 T38 · T43 | 6 | sdflow-ship · ship-gate-hardening-2 · checkpoint-tag-single-source · gate-anchor-line-scoped |
| **G5 Outside-voice 层**（outside-voice.sh） | T30 T31 | 2 | cross-model-outside-voice |
| **G6 观测 & 人读体验**（阶段提示/时长/链接/图表/cosmetic） | T28 T29 · T41 T42 · T50 · T27 | 6 | cross-model-outside-voice · gate-anchor-line-scoped · three-lens-decision-framework · 无批 |
| **G7 init.py 健壮性** | T21 T22 T48 T49 | 4 | sdflow-init-hardening |
| **G8 前端 viewer**（engine.js） | T47 | 1 | review-tool-followups |

关键观察：**G4、G6 各横跨 3-4 个来源批**——合批机会所在（批按发现来源切，功能域把同类活重新聚拢）。

## 二、合批建议（fold-vs-defer AND 门）

| 建议 change | 吃掉的批 | 项 | AND 门 | 优先级 | 净效果 |
|---|---|---|---|---|---|
| ★**REC-1 gate & checkpoint 硬化**（=G4） | sdflow-ship + ship-gate-hardening-2 + checkpoint-tag-single-source **(3 整批)** + gate-anchor 的 T43 | 6 | 同cap(gate+标签契约)✓ 高耦合(同 ship_gate.py)✓ 低增量(6小项机械)✓ | **P1** | **一 change 清 3 批** |
| ★**REC-2 观测 & 人读体验**（=G6） | three-lens-decision-framework **(整批)** + cross-model 的 T28/T29 + gate-anchor 的 T41/T42 + 无批 T27 | 6 | 同cap(人读/观测输出)✓ 高耦合(跨 skill 收尾段)△ 低增量(UX)✓ | P3 | 清 1 整批 + 收编 3 批残片 |
| **REC-3 Toolkit 安装/解析硬化**（=G2） | minimize-repo-footprint(setup 8项) + sdflow-rebrand 的 T23/T24 | 10 | 同cap✓ 高耦合(T18/T24 同 install_into·T14/T23 同 Windows 分支)✓ 低增量✗(10项偏大) | P2 | 清 2 批(残)，**增量大建议再切两半** |

REC-1+REC-2 联手把 **gate-anchor-line-scoped 整批拆干净**（T43→REC-1，T41/T42→REC-2）、**cross-model-outside-voice 拆两半**（T28/29→REC-2，T30/31 留 G5）。

### 自足、不合（各一个小 change 或随手带）

- **G1 记录三件套**（issues-pool-batch-mgmt，P2·自足）
- **G7 init.py 健壮性**（sdflow-init-hardening，P2·刚建自足）
- **G3 评审规则层**（T7 T8 T9 T19，P3·跨 2 批规则微调，可单开小 change）
- **G5 outside-voice**（T30 T31，P3·自足小）
- **G8 viewer**（T47，单项·随任何前端触碰带）

## 三、主次 + 执行次序

**主 = REC-1**：①最高正确性优先级（含 checkpoint-tag 的 B4 元 bug 上下文 + T43 防 gate 误判，系统镜 silent 失效）②合批收益最大（一 change 清 3 整批）③AND 门三条最干净。

推荐次序：

1. **REC-1**（P1）— gate & checkpoint 硬化 ← 本轮起
2. **G1 / G7** 两个自足正确性批（P2）
3. **REC-3**（P2）— 但先只做 T18/T24、T14/T23 两对强耦合，其余按 observability vs 所有权/跨平台安全再切
4. **REC-2 + G3 + G5**（P3）— 体验 / 规则 / voice 打磨

## 四、REC-1 成员明细（本轮起的四件套 scope）

| 项 | 落点 | 摘要 |
|---|---|---|
| T26 | `sdflow-ship/SKILL.md` | 熔断重试计数脚本化方案探索（gate 零副作用约束下的计数下沉） |
| T35 | `ship_gate.py` | 新鲜度可选纳入工作树 dirty 状态（T33 停置延续） |
| T36 | `workflow.md + sdflow-ship/SKILL.md` | checkpoint 派发指令文案收敛为单一真相源（broad-F2） |
| T37 | spec-workflow delta | Scenario prose 复述标签形状——又一份需人工与 workflow.md/SKILL.md 保持一致的 doc 副本 |
| T38 | spec-workflow delta | Scenario 用词 `<当前change>` 易被误读为须用真实 slug，实际用任意占位 demo |
| T43 | gate producer 模板 | 机器锚收紧为独占 bare line（现带反引号/同行尾注），防未来报告照抄模板致 gate 误判 |
