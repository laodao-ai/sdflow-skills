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
  change 名来源: 活动 changes/<name>/ + 归档 archive/<date>-<name>/ 剥日期前缀 → <name>
  对每个 <name>:
    ┌─ git log -- openspec/changes/<name>/  （查 pre-archive 路径, 非归档路径, 非 --follow）─┐
    │  拿到该 change 全生命周期提交 (sha, ts, subject)                                        │
    │  〔grill 实测: 旧路径一把捞全 7 条 grill→done-archive; 归档提交=删旧路径亦落此 log〕   │
    └───────────────────┬───────────────────────────────────────────────────────────────────┘
                        ▼
    subject 前缀能解析出阶段?  ──是──▶ 该提交归 (change, 阶段)
                        │
                        否（裸 checkpoint(spec-review) 等历史标签）
                        ▼
              归属 change 已由路径确定（不受裸标签影响）；
              阶段靠前缀词表映射（D3 词表），映射不出 → 标 "unknown 阶段"
                        ▼
    相邻提交 ts 差 = 该阶段墙钟（含人决策时间，诚实标注）
```

> **关键（绕开 ship_gate 契约，grill 实测确认）**：change **归属**靠 `git log -- openspec/changes/<name>/`（**pre-archive 路径**——归档是 `git mv` 删旧路径，该路径 log 含全生命周期含归档提交；查**归档路径**只得 1 条=错）。**不靠** tag 里的 change 名 → **零改 checkpoint-commit.sh、零碰 ship_gate 精确豁免**。tag 只映射**阶段**（前缀词表）。
>
> **边界模糊 case 默认〔grill Q1〕**（retro 是 view 非门禁，存疑标注即可、不过度设计）：
> - 两 change 同期 stacking（一个 `add -A` 扫到俩 change dir）→ 该提交进两者 log、共享时间戳，阶段按 subject 前缀。接受（罕见）。
> - change 名复用（同名先后两个）→ 旧路径 log 合并两者 → 标"边界存疑"降级。
> - 归档提交自身 → 前缀 `done-archive` 直接映射 done 收尾。

## 报告 schema（grill Q3b）+ 阶段词表族（D3 支撑）

**报告 schema**（`openspec/retro/report.md`，无 token 列）:
```
  ├── 顶部: 覆盖 N change / M 有镜锚 / K 边界不可解析
  ├── per-change 表: change | 总墙钟 | spec-rev Δ | impl Δ | code-rev Δ | #ckpt | hr-tg(none/TG号) | Σfindings | 采纳率 | 独立Σ
  ├── 聚合① 阶段占比: 整体时间花哪阶段
  ├── 聚合② 成本双峰: 散点(总墙钟 x, code-review占比% y)——小 change 高占比自显
  └── 聚合③ per-镜价值表: lens_metric_aggregate 输出内嵌(采纳率/独立率/出现轮数/N≥10 flag)
```

**阶段词表族**（checkpoint 前缀 → 阶段，family 映射；映射不出 → "unknown 阶段"桶）:
```
  ff                                              → ff
  grill                                           → grill
  spec-review / -autoplan / -rewrite / -gate      → spec-review
  task<N>-* / <change>:task<N>-* / *-impl         → impl
  impl-review                                      → code-review
  done-verify / done-archive                       → done
  propose / plan / roadmap / issues / *-cross-review → planning/other（非核心阶段，计入总墙钟）
```
> 词表是 **additive 约定**（OQ1 的 (c)）——未来新阶段前缀加一行映射即可，MUST NOT 改 checkpoint tag 格式。

## Decisions（ADR，TG-23）

| # | 决策 | 备选否决 | 状态 |
|---|---|---|---|
| D1 | change 边界靠 `git log -- openspec/changes/<name>/`（**pre-archive 路径**）+ 阶段词表(c)，不改 tag | 查归档路径(只得1条=错)/改 tag 格式嵌 change 名(撞 ship_gate `checkpoint(impl-review)` 精确豁免+改3处) | ✅ **grill Q1 定**（实测旧路径捞全 7 条、零 ship_gate 碰撞；三边界 case 按默认标注降级）|
| D2 | `lens_metric_aggregate.py` **移进** `sdflow-retro/scripts/`（skill 独占，不再 bundle 工具）| 留 bundle tools/ retro 引用——但调研证改后**唯一运行时消费者=retro**（maintain→薄指针；code/spec-review 仅 prose 提及），留 bundle 是延续"寄人篱下"反模式 + 消费仓白背派生工具 | ✅ **grill Q2 定**（唯一消费者判据）。附带：SR-K MODIFIED、init.py 删派生、test_init 改断言、3 SKILL prose 指针改指 retro、INDEX 更新 |
| D3 | **不做语义 change 类型分桶**；只报客观列 + hr-tg 客观 flag | 语义 3 分桶（琐碎/routine/HR-TG）——琐碎vs routine 要机判语义，正是 adaptive-routing 被否的"diff 前不可机判语义" | ✅ **grill Q3a 定**（双峰读客观轴：总墙钟/Σfindings/code-rev占比%；hr-tg 直接读锚 hit）|
| D4 | maintain 策略 B（薄指针）| A 全吸收（丢自动提醒）/ C 两处调聚合器（违吸收本意）| ✅ 已定（用户拍板）|
| D5 | 报告 view-only 再生、落 `openspec/retro/report.md`、**tracked（提交进 git）** | 增量手工维护（漂移）/ stdout 不持久 / gitignored（clone 看不到、每次重跑）| ✅ **grill Q4**：tracked 活文档（像 CHANGELOG）；诚实代价=归档新 change 后未跑 retro 前 report stale（锚/git log 才是真相源），跑 retro 即刷新，接受 |
| D6 | **不加 token 估算列** | 加 token 列——无 harness 数据、估算误导（同 adr/0009 诚实口径）| ✅ **grill Q3b 定** |
| D7 | 报告**含进行中 change**（活动 `changes/*/`，标 in-progress）| 只报已归档——藏当前工作 | ✅ **grill Q5 定**（部分生命周期成本仍有值；标 in-progress，价值维可能未落锚→标"无度量锚"）|

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
