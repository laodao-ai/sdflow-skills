## Why

本仓的评审工作流（ff→grill→spec-review→实现→code-review→done→merge）跑了十几个 change，但**没有一处回看"它自己跑得怎么样"**——每轮成本落哪（阶段墙钟）、哪些镜真抓到东西（价值）、优化该投哪，全靠临时手算。本 session 为定 P2 优先级，手动扒 checkpoint 时间戳 + lens-metric 锚才拼出"评审成本双峰（小 change 评审占 73%、大 change 占 9%）"这个判断——**这类复盘应该是可复用工具，不是一次性手活**。

同时，评审价值度量回路（`workflow-metrics-loop` 建的 lens-metric 锚 + `sdflow-maintain` 步骤 5 的聚合 surfacing）只有**镜价值半边**，缺**时间/成本半边**；且镜价值 surfacing 当初"寄居"在 INDEX 维护 skill 上，没有正主。本 change 建 `sdflow-retro` 作为 workflow 复盘/评估的正主，把两个半边合成完整的成本×价值视图。

## What Changes

- **新 skill `sdflow-retro`**：跑脚本收成"全项目所有 change 复盘报告"（`openspec/retro/report.md`，view-only 每次从源再生）——per-change 阶段墙钟 + 镜 findings/采纳率 + 双峰/占比聚合。
- **时间维脚本**（新）：从 git 历史提取每个 change 的阶段墙钟（checkpoint Δ），自动切 change 边界。
- **镜价值维**：吸收现有 `lens_metric_aggregate.py`（镜采纳率/独立率聚合）。
- **`sdflow-maintain` 瘦身（策略 B）**：步骤 5 的 lens-metric 聚合 surfacing 塌成一行**薄指针**「跑 `/sdflow-retro` 看完整复盘」——maintain 回归 INDEX.md 维护本职；镜价值单一真相源移到 retro，但保留 maintain 归档后的自动提醒指路。
- **checkpoint 阶段可解析性**：让未来 checkpoint 数据能被 retro 稳定按 change × 阶段归属（**具体机制见开放问题 OQ1——不预判**）。

## Capabilities

### New Capabilities
- `workflow-retro`: workflow 复盘/评估——从 git 历史 + 归档评审报告，只读再生"全项目 change 成本×价值复盘"，供 roadmap 优先级 / 镜去留决策提供数据（不自动决策，只呈现）。

### Modified Capabilities
- `workflow-metrics`（两条 MODIFIED）:
  - **SR-A surfacing 正主迁移**：需求「数据驱动反馈供数不供裁决」的 surfacing 机械点由绑 `/sdflow-maintain` 改为绑 `/sdflow-retro`；`/sdflow-maintain` 保留**薄指针**不丢归档后自动提醒（策略 B）。
  - **SR-K 聚合器位置**〔grill Q2〕：`lens_metric_aggregate.py` 由 bundle `sdflow-init/assets/workflow/tools/`（随 `sdflow-init update` 派生消费仓）**移进 `sdflow-retro/scripts/`**（skill 独占，全局安装即用，不再派生）——因调研证改后唯一运行时消费者 = retro。
- （OQ1 已 grill 定为"不改 tag" → 不触及 `spec-workflow` checkpoint 需求。）

## Impact

- **新增**：`sdflow-retro/`（SKILL.md + scripts/ + tests/）；`openspec/retro/report.md`（生成物）。
- **迁移〔grill Q2 + spec-review 修订〕**：`git mv lens_metric_aggregate.py`（+ 其 tests）`sdflow-init/assets/workflow/tools/` → `sdflow-retro/scripts/`；连带：`sdflow-init/init.py` **仅移源文件——`ignore_patterns("tests")` 通用排除 MUST 保留**（还护 `trivial_shape.py` 测试，F5/G2）；`test_init.py` 断言（line 119+126）**改指 trivial_shape 非删**（保 tests-exclusion 覆盖）；**4 处** SKILL prose 指针（code-review:132 / spec-review:105 / **spec-review:120** / maintain:78）+ `docs/workflow-skills/sdflow-code-review.md:57` 改指 retro；`openspec/INDEX.md` 加 retro/ 条目 + 聚合器路径更新。
- **修改**：`sdflow-maintain/SKILL.md` 步骤 5（瘦身为薄指针）。**不改** `checkpoint-commit.sh`/`spec-workflow`（OQ1 grill 定不碰 tag）。
- **共享生产者风险**：`checkpoint-commit.sh` 被所有 workflow skill 使用，且其 tag 格式是 `ship_gate.py` 的解析契约（`spec-workflow` spec.md:335-398 命名空间隔离 + `checkpoint(impl-review)` 精确豁免）——任何 tag 格式改动 MUST 不破坏 ship_gate（见 OQ1）。
- **部署**〔spec-review-amendment B1〕：本 change 触及 bundle（聚合器**移出** `assets/workflow/tools/` + init.py 派生逻辑改）+ 新 skill；**不改** `checkpoint-commit.sh`（OQ1 定）。merge 后须 push → 运行 checkout `/sdflow-upgrade` 激活。

## Success Metrics

- `sdflow-retro` 一条命令再生出全项目复盘报告：每个已归档 change 有阶段墙钟行 + 镜价值行；聚合出双峰/阶段占比。
- 手动扒数据（本 session 那种 ad-hoc python）被工具取代，可重复、无漂移（view-only 再生）。
- `sdflow-maintain` 回归单一职责（纯 INDEX.md），lens-metric 聚合不再两处实现。
- 历史 change 边界 best-effort 归属可用；未来 change 边界稳定可解析（OQ1 落地后）。

## Non-Goals

- **不自动决策**：复盘只呈现成本×价值，"砍哪个镜/降采样/调优先级"一律人决（承 lens-metric 反馈回路的 user-sovereignty）。
- **不追 per-镜耗时**：harness 不暴露子代理耗时（adr/0009）——时间维只到**阶段级**（checkpoint Δ，含人决策时间），不假装能拆到单镜 fan-out。
- **不改评审行为**：retro 是只读观测，不改 spec-review/code-review 怎么跑（那是 P2/P3 的事）。
- **不做实时监控/dashboard**：一次性再生的 markdown 报告，非常驻服务。

## Open Questions

- **OQ1（头号·碰撞风险）checkpoint 阶段归属机制**：retro 要把 checkpoint 归到 (change, 阶段)。三条路：
  - **(a) 不改 tag，用 `git log -- openspec/changes/<change>/`**：提交路径天然界定 change 生命周期（活动期在 `changes/<name>/`、归档后在 `changes/archive/<date>-<name>/`），阶段靠现有 checkpoint 前缀（grill/spec-review/impl-review/…）映射。**绕开 tag 契约、零共享生产者风险。当前倾向。**
  - (b) checkpoint-commit.sh 给**所有** tag 嵌 change 名：**撞碎 ship_gate 的 `checkpoint(impl-review)` 精确豁免（spec.md:359）+ 需同步改 ship_gate + spec-workflow**，blast radius 大。
  - (c) 只**标准化阶段词表**（固定 ff/grill/spec-review/impl-review/done-verify/done-archive 词汇，文档约定、不改格式）：additive、无碰撞，作为 (a) 的补充让前缀映射稳。
  - → grill 定夺。(a)+(c) 组合看起来兼顾稳与零风险。
- **OQ2 `lens_metric_aggregate.py` 归属**：移进 `sdflow-retro/scripts/`（retro 独占、maintain 薄指针纯文字）vs 留 `bundle tools/` 由 retro 引用（仍是 canonical 工具、经 resolver 解析）。移动改解析路径 + 影响消费仓；引用则 retro 依赖 bundle。
- **OQ3 报告 schema**：per-change 行字段（阶段 Δ / 镜 findings 数 / 采纳率 / change 类型）+ 聚合段（双峰散点 / 阶段占比）——具体列与 change 类型分类判据（琐碎/routine/HR-TG 怎么机判）待 design 定。

## Assumptions

- **A1**〔spec-review 修订〕checkpoint 前缀映射**阶段**信号——**仅对生成期阶段可靠**（grill/spec-review/impl-review 是 checkpoint 前缀）；**归档/收尾提交前缀不可靠**（实测 14/15 是 `chore/feat` 非 `checkpoint(done-archive)`）→ done 阶段改靠 path-rename（D8），不靠前缀。
- **A2**〔spec-review 修订·原过度断言〕`git log -- changes/<name>/`（pre-archive 路径）**多数** change 能界定生命周期，但**非全部**：创世 mass 提交（`db3c824`）致 2 个 2026-07-02 seed change 的 pre-archive 路径 0 提交（原"每个 change 提交都碰其目录/一把捞全"是单样本外推，已证伪）→ 须 archive 路径兜底 + seed 剔除 + 0/1 守卫（D9）。失效影响：早期 seed change 边界 best-effort/不可解析，标注不崩。
- **A3**〔spec-review 修订·原过度断言〕lens-metric 锚**仅最近 2/17 change 有真锚**（`workflow-metrics-loop`、`adaptive-workflow-routing`；metrics-loop 之前的时代无锚）→ 镜价值维对历史 88% 空。失效影响：per-镜聚合 N=2 近乎无统计意义（顶部显性"有真锚 M"防误当趋势）；**retro 真价值在向前**（新 change 有锚），历史 best-effort。

## Compliance

- 承 adr/0009（计时粒度只到阶段级）、lens-metric 反馈回路的 user-sovereignty（只呈现不决策）、`grill-not-skippable`。
- 〔spec-review 修订·域轴2〕report.md 是**可重生 view**（锚/git 历史为 state 真相源），零新持久可变**状态**——report 文件本身 tracked（活文档）但非 state，故与 `lens_metric_aggregate.py` "不写持久文件"的 stdout-view 契约口径统一为"零新 state"而非"零文件写"。
- 触及 bundle → 权威源改动 + 部署下发（spec-workflow「workflow bundle 改动须在权威源」需求）。
