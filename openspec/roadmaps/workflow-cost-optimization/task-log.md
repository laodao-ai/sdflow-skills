# workflow 成本优化 任务日志

> 按时间**倒序**记录 `roadmap.md` 中每个已完成子任务的状态、耗时、问题、调整。
>
> 相关文档（均位于 `openspec/roadmaps/workflow-cost-optimization/`）：
> - 需求综述：`requirements.md` · 整体设计：`design.md` · 实施路线图：`roadmap.md`

## 使用约定

每完成一个 roadmap 子任务追加一条（倒序、只记非琐碎与计划外情况）。

---

## 2026-07-07

### [阶段 4] 批次策略交付并归档（进度同步补记）
- **状态**: ✅ 完成（承载 change `batch-triage-strategy`，2026-07-06 archive + merge `725caf3`；本条为 roadmap 状态回填，实施发生在上一 session）
- **交付**（逐条对上 roadmap 阶段 4 交付物）:
  - `consolidation-plan.md` 按框架重划——相关项走 BASE-18 AND 门、散落琐碎正交项归「大扫除批」。
  - `openspec/issues/batch-triage-rules.md`（**新，本仓-local**）——大扫除批 3 硬 MUST + fail-closed + 聚合上限（文件数/目录跨度/生成物/CI 面积）+ issue 级近似判据（采纳 Leg1 行为面路径守卫，`SKILL.md`/`*/assets/workflow/*` 硬排除）。
  - INDEX 登记 `batch-triage` capability；spec 同步至 `specs/batch-triage`。
- **设计偏移（spec-review Q2 定案，须记档）**: roadmap 阶段 4 原写「workflow 规则补批次判据」（暗示进 bundle），实际 **Q2 定案=本仓-local**——判据 **MUST NOT 进 bundle、MUST NOT 部署下游**，向下游发布 **deferred** 到本仓 dogfood 验证后（对齐 Leg1）。冷源接地证实原「普通 update 回灌」是**事实性错误**（D6 修正）。判据为**纯规则 checklist、无 scripts/无 pytest**。
- **本仓 dogfood caveat**: 本仓多数 issues debt 落行为面文件（SKILL.md/bundle）→ 大扫除批**候选池薄**，本仓实际价值待 dogfood 实测（change §5.4 注记 + 后续 `0e07c35`）。
- **对 roadmap 的影响**: 概览表/阶段 4/依赖图/建议次序同步为 v4——P4 标 ✅，剩 P2/P3 走 Leg2 串行区（P2 先、P3 压后）。**Leg3（降轮次=墙钟主杠杆）首个阶段已落地。**

---

## 2026-07-06

### [explore] P0 分析收口 → 基线证伪 P2 墙钟杠杆、定收益门槛
- **状态**: ✅ 完成（`/opsx:explore`；P0 从「聚合器已交付」推进到「读基线→定门槛→判 P2」的分析闭环——原 P0 只落了 `sdflow-retro` 机器，未做分析）
- **数据源**: `sdflow-retro` 全 18-change 只读聚合 `openspec/retro/report.md`（真锚 3/18、边界不可解析 2、待复评无）。
- **基线结论**（改写 P2 价值主张）:
  - 阶段占比 **spec-review 43% / impl 29% / ff 11% / grill 6% / code-review 5% / done 0%**——Leg1(P1) 优化的 code-review 仅占 5%（零损失免镜仍值得，但撬不动总墙钟）。
  - spec-review 的 43% 是 **elapsed 口径、被人类门（读报告+拍板）主导**（离群 `checkpoint-tag-single-source` 单 spec-rev 678min = 人时间非算力）。
  - ⟹ **P2 机械镜 opus→light 的墙钟收益结构性趋零**（机械镜并行、非最慢镜、占人类主导 elapsed 的小片），但 **token 收益真** → P2 重定位 token play、墙钟降「不回归」。
  - **墙钟真杠杆在 Leg3 降轮次**（少付几次人类门），非 Leg2 每轮机械镜 → 战略权重上调 Leg3、P4 从「轻策略层」提为墙钟主杠杆、建议与 P2 并行。
  - **价值锚太薄禁砍镜**：3/18 有真锚、per-(层,镜) 轮数全<10、已测镜均高价值（接地镜独立率 75%）→ 现阶段一个镜都不够格降采样。
- **用户决定**: 认可收益门槛整表（P2 主指标=token / P2 墙钟=不回归 / 误免率恒0+fail-closed / 砍镜闸门=轮数≥10∧独立率<20%∧采纳率<50% 连续2窗）。砍镜阈值为保守起始值、积累后可校。
- **落点**: design §2.2 补「P0 基线实测收口」段 + 决策表 D11（P2 重定位）/D12（砍镜闸门）；requirements §5 补「P0 定案收益门槛」表 + Leg2 验收改 token 主收益；roadmap 概览/P0 段（收口结论）/P2 里程碑·目标·验收/依赖图建议次序全部同步。**未动 change 产物**（纯 roadmap 活文档）。

### [explore] P0+P2 接地深挖 → P2 章节重构（v2→含矩阵）
- **状态**: ✅ 完成（`/opsx:explore` 只摊不写，产出固化进 roadmap/design 活文档）
- **接地发现**（改了 P2 的认知）:
  - **档位是 advisory、零脚本强制**：`model-tiers.md` 说机械镜→light，但 fan-out 不带 `model=`、子代理继承父 opus → "文档说 light 实跑 opus"。P2 真实内容 = 把 advisory 变强制（+ opus→light 省 token，比墙钟更实在）。
  - **评审成本双峰**（checkpoint 时间戳实测 6 change）：大逻辑 change 评审占 ~9%、小 change 占 73%（`drop-per-dir-review-stub`）。→ **P2 价值域 = 有逻辑面小 change**，大 change 噪声。纠正上轮"P2 天花板低"的单样本误判。
  - **P2b 后台价值窄**：仅 spec-review→设计门段有值；code-review 阶段三无人类门（P3e）人本就能走开、不加值；harness 通知半免费 → P2b 降为 P2 小尾巴，不配独立阶段。
- **用户决定**:
  - 档位不写死模型 → 升 `3 档 × 运行时` 矩阵（Claude Code/Codex 列，config.yaml 可覆盖）；resolver 按运行时列解析字面模型。
  - 置信打分 light→mid（丢弃 findings、有判断权重，不配 light；不新增档）。
  - 升级档（Fable/主力档动态升级 sonnet→opus 应对超复杂）**当前无需求 → 延后留档**（见 todolist）。
  - 硬约束记档：Agent `model=` enum 不含 codex，跨运行时只走 outside-voice。
- **落点**: roadmap 概览+阶段2 重写（P2a/P2b 合并为 P2、矩阵、双峰价值域、P2b 降级）+ 依赖图；design §2.2 + 决策记录 D5 精化/D7 被 D10 修正/补 D8 矩阵·D9 价值域·D10 P2b 降级。

### [阶段 0 / 规划] roadmap 文档包产出
- **状态**: ✅ 完成
- **产出**: `openspec/roadmaps/workflow-cost-optimization/` 下 requirements/design/roadmap/task-log/memo 五件。
- **来源**: 一轮深度对话（本 session），从「G1+G2 能不能合批」起、经 change `adaptive-workflow-routing` 的 grill+4冷源 spec-review、收敛出「成本优化边界=逻辑面有无」的贯穿洞察 → 三腿 roadmap。
- **备注**:
  - **P1 由 change `adaptive-workflow-routing` 承载**（名不同：该 change 原为大机制、设计门 Q1=A 收敛为 Leg1 白名单判器，名保留未改）。**已 merge + `/sdflow-upgrade` 激活**（trivial_shape.py 在 `~/.sdflow/workflow/tools/`）。
  - 本 roadmap 在独立分支 `feat/plan-workflow-cost-optimization`（rebase 到含 P1 的最新 main），不与 A 分支纠缠。

### [交叉 review] roadmap 四件套 → v2
- **状态**: ✅ 完成（`/plan-eng-review` 取其实质：codex 冷模型 outside voice + 四维工程审）
- **产出**: codex 冷审回 30 条 → 主 session 叠加四维审 + 对抗裁决去重为 15 组 → 用户批「全采纳 9 组」→ roadmap v2 + design/requirements 同步。

## Review 处置

> 交叉 review 已跑（plan-eng-review 实质：codex 独立冷审 30 条 + 主 session 四维工程审）。每条 findings 显式标注 采纳/延后/裁掉，无「未处置」。

**✅ 采纳（9 组，已改进 roadmap v2 / design / requirements）**

| # | 源 | 处置 | 落点 |
|---|---|---|---|
| A1 | #1 | P1 状态自相矛盾（在途 vs 已 merge）→ 订正为「✅ 已交付」 | roadmap 概览/阶段1/依赖图、design §2.1、task-log |
| A2 | #11/#26 | 置信过滤丢弃 findings 是安全关键路径，剔出机械快档集 | roadmap 阶段2a、design §2.2 + D5 |
| A3 | #23/#24/#30 | 缺阶段级基线 + 收益门槛 → 新增 P0 基线采样（Leg2 前置，用 checkpoint 时间戳）| roadmap 阶段0、design §2.2 + D6、requirements §5 |
| A4 | #15 | P2 太大（快档=策略改 vs 后台=调度机制改）→ 拆 P2a/P2b | roadmap 阶段2a/2b、design D7 |
| A5 | #12/#22/#25 | 缺 fail-closed + 弱档准入前提 → 补 P2a/P2b 验收 | roadmap 阶段2a/2b、requirements §5 |
| A6 | #16/#17 | P3「接地镜不依赖 autoplan」不稳：amendment 可新增核验目标 → 强化边界（新增+改动两类，非仅增量）| roadmap 阶段3、design §2.2 |
| A7 | #20/#21 | P4 正交批缺聚合上限（每项低危≠聚合低危）→ 补文件数/目录跨度/生成物/CI 面积上限 | roadmap 阶段4、design D4 |
| A8 | #2/#4/#6 | design §2.1 措辞过松（"纯文档路径/纯展示版本常量"）→ 引用 P1 实际守卫（行为面路径/扩展名锚定/VERSION收窄/conftest排除）| design §2.1 |
| A9 | #29 | "P1/P2/P4 可并行" 需加注同文件冲突（P2a/P2b/P3 均改两评审 SKILL.md 须串行）| roadmap 概览/依赖图 |

**⏭ 延后（记档，未来 implement 阶段处理）**

| # | 源 | 延后理由 |
|---|---|---|
| D1 | #3 | fixtures/golden/snapshot 残留 → 交叉引用已有 **T56**（trivial_shape F6 残留），P1 后续清理 change 处理 |
| D2 | #7 | P4 判据不能**字面**复用 trivial_shape（它需 diff、P4 是 issue 级 pre-diff）→ P4 真正设计时立 issue 级近似判据（已在 roadmap 阶段4 记明「同类非同脚本」）|
| D3 | #28 | /sdflow-upgrade 未验收消费仓实际加载新 skill 非缓存 → 次要，P2/P3 交付时带上验收项 |

**⚪ 裁掉（反静默压制，记原始发现 + 裁掉理由，供后人复核裁得对不对）**

| # | 源 | 原始发现 | 裁掉理由 |
|---|---|---|---|
| X1 | #5 | 跳 Step2 后 Step1 变单点守门 | 设计**显式接受**：Step1 恒跑正是白名单兜底（trigger scope-drift 揭穿伪装逻辑改），非疏漏——非新问题 |
| X2 | #8 | "有逻辑面省不了"是错误二分（可更窄镜/证据复用/缓存/局部重审）| D1 的**刻意简化**；列举项是超本 roadmap scope 的未来探索方向，非当前漏洞（记为未来探索，不阻塞本 roadmap）|
| X3 | #9/#10/#19 | dogfood 一次不能证明所有 change 需同等强度 / 墙钟≠不干等 / P4 文档层低估行为风险 | 轻度稻草人——设计未做被反驳的强主张（只主张冷镜层 load-bearing）；#10「墙钟≠人不阻塞」、#19「P4 有行为风险」两点措辞提醒已分别并入 A4(P2b分开记账)/A7(P4聚合上限)，非独立裁掉 |
