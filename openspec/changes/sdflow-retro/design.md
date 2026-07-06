## Context

评审价值度量回路现状：`workflow-metrics-loop` 在评审报告落 `<!-- sdflow:lens-metric v1 ... -->` 锚（per-镜 findings/采纳/独立/sev）；`lens_metric_aggregate.py`（`sdflow-init/assets/workflow/tools/`）只读聚合归档报告的锚成多列表；`sdflow-maintain` 步骤 5 归档后跑该聚合器 + surfacing「≥10 待复评」提示。**缺口**：只有镜价值维，无时间/成本维；且聚合 surfacing 寄居在 INDEX 维护 skill 上无正主。

关键既有契约（本 change MUST NOT 破坏）：`ship_gate.py` 解析 checkpoint tag——任务标签 `checkpoint(<change>:task<N>-<slug>)` 命名空间隔离（`spec-workflow` spec.md:394-398），设计门新鲜度**精确豁免** `subject == "checkpoint(impl-review)"`（spec.md:358-359）。故任何 checkpoint tag 格式改动都踩这个契约。

本 session（explore）已手动验证：checkpoint Δ 能切阶段墙钟、评审成本双峰（小 change 73% / 大 change 9%）——本 change 把该手活固化为 `sdflow-retro`。

## Goals / Non-Goals

**Goals:**
- 一条命令再生"全项目 change 成本×价值复盘"（`openspec/retro/report.md`，view-only）。
- 合并时间维（新）+ 镜价值维（吸收 `lens_metric_aggregate.py`），成完整评估。
- `sdflow-maintain` 回归纯 INDEX.md（策略 B：步骤 5 塌成薄指针）。
- change 边界全自动检测：历史 best-effort、未来稳定可解析，**且不碰 ship_gate tag 契约**。

**Non-Goals:**
- 不自动决策（砍镜/降采样/优先级一律人决）。
- 不追 per-镜耗时（adr/0009，只到阶段级）。
- 不改评审行为、不做常驻 dashboard。

## 组件清单（BASE-25，TG-14）

```
  sdflow-retro/                         新 skill（数据类：脚本 owns 机械活）
  ├── SKILL.md                          编排：判断+调脚本→再生报告；描述触发
  ├── scripts/
  │   ├── retro_report.py               时间维 + 编排出报告（主脚本）
  │   │     ├─ change 边界检测           git log -- changes/<name>/（见决策图）
  │   │     ├─ 阶段墙钟                   相邻 checkpoint Δ，按前缀映射阶段
  │   │     ├─ change 类型分类            琐碎/routine/HR-TG（判据见 D3）
  │   │     └─ join 镜价值                调 lens_metric_aggregate（OQ2）
  │   └── lens_metric_aggregate.py       镜价值维（吸收；位置见 D2）
  └── tests/
        ├── test_retro_report.py         边界检测/阶段Δ/分类/报告 schema
        └── test_lens_metric_aggregate.py  （若移入，随迁其测试）
  产出: openspec/retro/report.md         view-only 再生，全 change 复盘
  改动: sdflow-maintain/SKILL.md 步骤5→薄指针
```

## 数据流图（TG-11）

```
  git log --                 ┌─────────────────┐
  changes/<name>/  ─────────▶│ change 边界检测   │──▶ [(change, [sha,ts,stage...]), ...]
  (+ archive 路径)           └─────────────────┘         │
                                                         ▼
  checkpoint 前缀 ──映射阶段──▶ ┌──────────────┐   per-change 阶段墙钟 Δ
                              │ 阶段墙钟计算  │──▶ (grill/spec-review/impl/…: Δmin)
                              └──────────────┘         │
  archive/**/*-review-report.md                        ▼
  的 lens-metric 锚 ──▶ lens_metric_aggregate ──▶ per-镜 采纳率/独立率
                                                         │
                                                         ▼
                                            ┌────────────────────────┐
                                            │ 合成 report.md（view）  │
                                            │ per-change 行 + 双峰聚合 │
                                            └────────────────────────┘
```

## change 边界检测（决策图，TG-12）

```
  对每个 change（名取自 changes/ 活动目录 + changes/archive/<date>-<name>/）:
    ┌─ git log --follow -- openspec/changes/<那个路径>/ ─┐
    │  拿到该 change 所有提交 (sha, ts, subject)          │
    └───────────────────┬────────────────────────────────┘
                        ▼
    subject 前缀能解析出阶段?  ──是──▶ 该提交归 (change, 阶段)
                        │
                        否（裸 checkpoint(spec-review) 等历史标签）
                        ▼
              按提交落在该 change 路径 → 归属 change 确定；
              阶段靠前缀词表映射（D3 词表），映射不出 → 标 "unknown 阶段"
                        ▼
    相邻提交 ts 差 = 该阶段墙钟（含人决策时间，诚实标注）
```

> **关键（绕开 ship_gate 契约）**：change **归属**靠 `git log -- <change 路径>`（提交碰哪个 change 目录），**不靠** tag 里的 change 名。故**无需改 checkpoint-commit.sh tag 格式**（OQ1 → (a)）。tag 只用来映射**阶段**（前缀词表）。

## Decisions（ADR，TG-23）

| # | 决策 | 备选否决 | 状态 |
|---|---|---|---|
| D1 | change 边界靠 `git log -- changes/<name>/` 路径，不靠 tag 嵌 change 名 | 改 tag 格式嵌 change 名——撞 ship_gate `checkpoint(impl-review)` 精确豁免 + 需改 3 处；标准化阶段词表(c)作补充 | **推荐 (a)+(c)，待 grill 拍** |
| D2 | `lens_metric_aggregate.py` 归属 | (i) 移进 `sdflow-retro/scripts/`：retro 独占、maintain 纯文字指针；(ii) 留 bundle `tools/` retro 引用：仍 canonical。移动改 resolver 路径 + 影响消费仓 | **待 grill**（倾向 (ii) 留 bundle：它是评审期工具、resolver 已解析，移动 blast radius 大） |
| D3 | change 类型分类判据（琐碎/routine/HR-TG）| 纯按墙钟/文件数机判 vs 复用 trivial_shape 形状判 vs 读 change 的 HR-TG 锚 | **待 design 细化**（倾向读评审报告已有的 hr-tg 锚 + 阶段Δ，不新造判据）|
| D4 | maintain 策略 B（薄指针）| A 全吸收（丢自动提醒）/ C 两处调聚合器（违吸收本意）| ✅ 已定（用户拍板）|
| D5 | 报告 view-only 再生、落 `openspec/retro/report.md` | 增量手工维护（漂移）/ stdout 不持久（不满足"全项目复盘活文档"）| ✅ 已定 |

## 可观测性（BASE-11）+ 失败模式表（BASE-06，TG-15）

| 失败模式 | 触发 | 处理（fail-safe 非 fail-silent）|
|---|---|---|
| change 目录无提交历史 | rebase/squash 抹掉 | 该 change 标"边界不可解析"，报告列出、不静默漏 |
| checkpoint 前缀映射不出阶段 | 非常规 tag | 归"unknown 阶段"桶，计入总墙钟、报告标注 |
| lens-metric 锚缺失/config off | 该 change 无锚 | 镜价值维留空 + 标注"无度量锚"，不阻塞时间维 |
| 归档报告解析失败 | fence 污染/格式坏 | 复用聚合器既有 fence-aware + 越域标记，跳过坏行不崩 |
| git log 输出畸形 | 特殊字符/编码 | `core.quotePath=false` + errors=replace（承 trivial_shape 硬化口径）|

- 可观测性：报告顶部打"覆盖 N change、M 有镜锚、K 边界不可解析"计数，让缺口显性（不假装全覆盖）。

## Risks / Trade-offs

- **阶段墙钟含人决策时间**：checkpoint Δ 混了人读/拍板/生成时间，非纯 agent 耗时（adr/0009）。→ 诚实标注"阶段级 elapsed（含人）"，不假装是 fan-out 延迟；双峰/占比仍有决策价值。
- **共享生产者零改动是目标但 OQ1 未定**：若 grill 推翻 D1 选了改 tag，blast radius 骤增（ship_gate + spec-workflow 联改）。→ 强烈倾向 D1(a)，把改 tag 列为下策。
- **吸收 maintain 步骤 5 的 cadence 损失**：策略 B 保留薄指针缓解，但自动提醒从"跑聚合器出结果"降为"提示去跑 retro"——多一跳。接受（换来单一真相源）。
- **报告再生成本**：每次全扫 archive + git log，change 多了会慢。→ 可接受（复盘低频、view-only），必要时加增量缓存（Non-Goal 本期）。
