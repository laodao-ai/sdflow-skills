# workflow 成本优化 整体设计

> 版本：v1（2026-07-06）
>
> 相关文档（均位于 `openspec/roadmaps/workflow-cost-optimization/`）：
> - 需求综述：`requirements.md`
> - 实施路线图：`roadmap.md`
> - 任务日志：`task-log.md`

## 1. 架构概览

### 1.1 贯穿设计原则：成本优化的边界 = 逻辑面的有无

```
                        change 有逻辑面吗？
              ┌──────────────────┴──────────────────┐
             无（琐碎/结构零产出）                 有
              │                                    │
    怎么省都安全:                         省不了,最佳杠杆:
    · 跳镜(Leg1 白名单免Step2)            · 相关合批(Leg3, 摊薄+连贯审)
    · 正交大扫除批(Leg3)                  · 降每轮墙钟(Leg2, 机械镜快档/流水线/后台)
    · 机械镜快档(Leg2, 与逻辑面无关)       · 孤立逻辑项: 认命付全轮 + Leg2 提速
```

**为什么这条边界是对的**：一个刚跑完的 dogfood 直接证明——对一个聚焦 change 做 spec-review，4 个独立冷源抓出了 grill 漏掉的地基问题。评审层 load-bearing。故「省」只能落在**可证不损失评审价值**的地方：无逻辑面的东西，多镜跑了也零产出，免之无损；有逻辑面的东西，省镜=丢真 bug。

### 1.2 三腿拓扑

```
                  workflow 成本 = 每轮成本 × 轮次
                        ┌───────────┴───────────┐
                    每轮成本                    轮次
              ┌────────┴────────┐                │
           范围(做多少)      墙钟(多快)         批次策略
           Leg 1            Leg 2              Leg 3
```

## 2. 各 Leg 设计

### 2.1 Leg 1 — 降范围（只对可证零损失的缩审）

**HOW**：在 `sdflow-code-review` 入口加一个 **post-diff 机判「无逻辑面白名单形状」判器**——命中 → 免 Step2 多镜；Step1 恒跑守卫（抓伪装成注释的逻辑改）；行为面路径清单护 bundle 自身 markdown。

> **判据是带守卫的、不是路径裸判（交叉审 #2/#4/#6）**：本仓大量 markdown/规则/prompt 是**行为面**、非旁路文档，故白名单绝非"路径像文档就免"。实际守卫（已在 `trivial_shape.py` 落地）：①**行为面路径清单**优先命中即 NOT_EXEMPT（`SKILL.md`/`workflow.md`/`assets/workflow/*`/`ship_gate.py`/判器自身）；②文档判定**扩展名锚定**（挡 `requirements.txt`/`docs/conf.py`/`README_gen.py`）；③版本常量**收窄到 VERSION/CHANGELOG 文档路径**，拒代码里 load-bearing 的 `API_VERSION`；④仅加 tests **排除 `conftest.py`/`__init__.py`**（import 副作用）。

**WHY 这样、不那样**：
- **为何在 code-review 入口、不在 ff 前**：形状判定需要 diff；ff 阶段无 diff（原方案在 ff 前路由 → 时序矛盾，不可机判 → 冷审否决）。
- **为何只白名单形状、不判「非平凡」**：HR-TG 等语义复杂度**不可脚本化**（成员是 DB迁移/信任边界/并发等语义触发，今天由模型判非脚本）；只有「结构无行为面」是可机判的。
- **为何 Step1 恒跑**：白名单靠 diff 形状，伪装（`bar(); // x`、加错的测试）需 scope-drift 兜。

**落地 = change `adaptive-workflow-routing`（收敛版 A）**，已过 grill+spec-review+设计门 Q1=A，Leg1-phase1。

### 2.2 Leg 2 — 降每轮墙钟

**前置：先建基线（交叉审 #23/#24，采纳）**——P2/P3 前先做 **P0 阶段级墙钟基线采样**（用已有 checkpoint 时间戳，近乎免费）+ 定收益门槛。定位=**照妖镜**：explore（2026-07-06）实测 checkpoint Δ 已看出评审成本**双峰**——大逻辑 change 评审占 ~9%、小 change 占 73%。故 **P2 价值域 = 有逻辑面的小 change**（评审是它大头），对大 change 是噪声。

**HOW**：
1. **P2 档位矩阵强制落地（核心）**：`model-tiers.md` 升 `档位 × 运行时` 矩阵；SKILL fan-out **报档位、不写死模型**，主 session 经 resolver 按当前运行时列解析字面模型传 Agent `model=`。机械镜（接地/历史）实降 light（**省墙钟 + 省 token**），judgment/裁决/门禁不动。
   - **真相（explore）**：机械镜在 `model-tiers.md` 早已映射 light，但**无脚本强制**→ fan-out 不带 `model=` → 子代理**继承父 opus**。P2 不是"引入快档"，是把 advisory 变**强制**（opus→light 的 token 省下来比墙钟更实在）。
   - **置信打分 light→mid（交叉审 #11/#26）**：它丢弃 findings、有判断权重、会误杀真 finding，不配 light；用现有 mid 接住，**不新增档**。
   - **不写死 haiku（用户）**：档位是相对机队相对词（adr/0006）。**硬约束**：Agent `model=` 只吃 `{opus,sonnet,haiku,fable}`——codex 不在 enum，跨运行时只走 outside-voice.sh；矩阵「Codex 列」指工作流跑在 Codex host 时，非在 Claude host 里换某镜为 codex。
2. **P2b 后台（降级为 P2 小尾巴，非独立阶段）**：**仅 spec-review→设计门**那段值得后台化（人须等报告拍板）；**code-review 阶段三无人类门（P3e），人本就能走开→几乎不加值**；harness 已有完成通知（半免费）。故不配独立阶段（explore 修正原 D7 的"P2 拆 2a/2b 并列"）。
3. **P3 接地镜流水线**：放松串行纪律——接地镜核代码事实、不依赖 autoplan 设计 findings，可与 autoplan 并行提前起跑。**边界：autoplan amendment 可新增核验目标（非仅改动），提前跑的镜对新增是"从没看过"，须补跑（交叉审 #16/#17）。**

**WHY**：一轮墙钟 = max(各镜) + 综合屏障（不可删）。可降的是关键路径上的机械镜（降档缩延迟 + 省 token）+ 串行段（流水线）。**判断镜/置信打分/裁决降档=假绿**，禁。
**约束（诚实）**：adr/0009——harness 不暴露子代理耗时，只测阶段级时长（checkpoint 时间戳）。关键路径靠推断非数据，故 P0 基线 + 多轮同基线对比是验收前提，非单次墙钟（交叉审 #14）。

### 2.3 Leg 3 — 降轮次（批次策略）

**HOW**：
- **相关合批**（已有）：`consolidation-plan.md` 按 BASE-18 AND 门（同 capability ∧ 高耦合 ∧ 低增量）合批（REC-1/2/3）。不只摊薄成本、审得更连贯。
- **大扫除批**（新增）：散落各处的**琐碎正交项**（typo/小健壮性补丁/注释订正）打一包过一轮。
- **硬边界**：正交批 MUST NOT 装有逻辑面的东西——稀释镜子注意力（刚才冷审在聚焦 change 上都差点漏）+ 无关改动挤一 commit 坏了没法单独回退。**安全正交批判据 = 每项个体琐碎/低危**（与 Leg1 白名单同类）。

**WHY**：固定编排开销是「摊薄」的对象，但评审工作量随 surface 走。批只在**固定开销占比大**（琐碎项）时净赚；有逻辑面的批 = 用省的钱买漏 bug 的险。

## 3. 关键决策记录

| # | 决策 | 备选否决 |
|---|---|---|
| D1 | 成本优化边界 = 逻辑面有无 | 「按 change 大小/风险分级自适应」——冷审证不可机判、且大小非好代理 |
| D2 | Leg1 只做 code-review 入口白名单形状 | 前向自适应路由（时序矛盾/HR-TG不可脚本化/门核正交/ROI抽空，4冷源否决） |
| D3 | 机械镜换快档只对机械镜 | 全镜换快档——判断镜换弱档=假绿 |
| D4 | 正交批只装琐碎项 + 聚合上限 | 任意正交合批——稀释评审、回退耦合；每项低危≠聚合低危，须限文件数/目录跨度/生成物/CI 面积 |
| D5 | 置信打分 light→mid（上移，不新增档）| 留 light——它丢弃 findings、有判断权重、会误杀真 finding，light=假绿（交叉审 #11/#26） |
| D6 | P0 基线先行、定收益门槛 | 直接进 P2/P3 调度复杂区——无基线无法判是否优化了瓶颈、收益是否值得复杂度（交叉审 #23/#24） |
| D7 | ~~P2 拆 P2a 快档 / P2b 后台~~ **被 D10 修正** | （原：并列两阶段；explore 发现后台只在 spec-review 段有值、code-review 无人类门不加值 → P2b 降为 P2 小尾巴）|
| D8 | P2 核心 = 档位 `矩阵×运行时` 强制落地（SKILL 报档位、resolver 按运行时解析、不写死模型）| 单列表 + 硬编码 haiku——机队会换血/工具可能是 codex（adr/0006）；且 advisory 不强制=文档说 light 实跑 opus（explore） |
| D9 | P2 价值域 = 有逻辑面**小** change | 认为 P2 普适——checkpoint 实测双峰：大 change 评审占 9%（P2 噪声）、小 change 占 73%（P2 真杠杆）（explore 2026-07-06） |
| D10 | P2b 后台降为 P2 小尾巴（仅 spec-review 段）| 独立阶段——code-review 阶段三无人类门（P3e）人本就能走开、后台不加值；harness 通知半免费（explore） |

## 4. 放弃项（留档，防后人重蹈）

**「有逻辑面 routine change 轻量化」不做**——原 change `adaptive-workflow-routing` 初版尝试过，spec-review 4 冷源判定其在「省成本发生的前置阶段」不可实现（谓词 diff 派生但路由在 diff 前；HR-TG 语义不可脚本）、且门核正交/calibrator 幸存者偏差/ROI 被 D4/D6 抽空。详见该 change 的 `spec-review-report.md`。**教训写进原则 §1.1：有逻辑面省不了。**

## 5. Compliance

- 承 adr/0004 设计门红线、adr/0006 机队锚定（快档=相对机队）、adr/0009 计时粒度约束、`grill-not-skippable`。
- 全 Leg 的「省」均落在可证零损失处，符合元原则「任何一层评审覆盖不得无声蒸发」。
