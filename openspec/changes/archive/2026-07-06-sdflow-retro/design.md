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
  │                                     〔F3: 调脚本用绝对 skill 路径 ~/.claude/skills/sdflow-retro/scripts/…,
  │                                      禁 cwd 相对(cwd=消费仓根≠skill 目录);两运行时磁盘皆在〕
  ├── scripts/                          〔G1: 布局钉死——脚本与 tests/ 均在 scripts/ 下〕
  │   ├── retro_report.py               时间维 + 编排出报告（主脚本）
  │   │     ├─ change 边界检测           git log -- changes/<name>/ + seed剔除+0/1守卫+archive兜底(D-B)
  │   │     ├─ 阶段墙钟                   相邻 Δ; done 靠 path-rename(D-A); Δ<0 钳0(E)
  │   │     ├─ hr-tg flag                读锚 hit(D3: 不做语义分桶,只客观 flag; spec/code 双列 D-E)
  │   │     └─ join 镜价值                扫 active+archive 两源、spec+code 两报告分 layer(D-D)
  │   ├── lens_metric_aggregate.py       镜价值维（吸收；D2 移入本 scripts/）
  │   └── tests/                         〔G1: tests/ 在 scripts/ 下→test 的 parents[1]=scripts/ 成立〕
  │         ├── test_retro_report.py       边界检测/阶段Δ/hr-tg/join/原子写/报告 schema
  │         └── test_lens_metric_aggregate.py  （随聚合器迁入，parents[1] 校准）
  └── (报告写盘沿用 buglist/todolist 原子写 helper — D-H)
  产出: openspec/retro/report.md         view-only 再生, tracked 活文档, 全 change 复盘
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
    ┌─ git log -- openspec/changes/<name>/  （pre-archive 路径, 非 --follow）─┐
    │  拿到该 change 全生命周期提交 (sha, ts, subject)                        │
    └────────────────────┬────────────────────────────────────────────────────┘
                         ▼
    pre-archive 路径提交数 == 0?  ──是──▶ 兜底查 archive/<date>-<name>/ 路径〔D-B〕
    (seed change: 创世 mass 提交只碰 archive 路径)      │ 仍 0/1 → 标"边界不可解析"
                         │ 否                            ▼
                         ▼                         (计入顶部 K 计数)
    剔除 seed-mass 提交(一提交碰 ≥3 change dir, 如 db3c824 创世)〔D-B〕
                         ▼
    该提交是 archive rename?(git-mv changes/<name>→archive/, R 状态/删旧建新)
                         │──是──▶ 映射 done 阶段〔D-A: 靠 path-rename 非 subject 前缀,
                         │        因归档提交实测 14/15 是 chore/feat 非 checkpoint〕
                         否
                         ▼
    subject 前缀 → 阶段(D3 词表, 最长前缀匹配); 映射不出 → "unknown 阶段"桶
                         ▼
    相邻提交 ts 差 = 阶段墙钟(含人时间,诚实标注); Δ<0(ts 非单调) → 钳 0 + reorder-suspected〔E〕
                         ▼
    提交数 ==1 → 无相邻对,墙钟不可算,标注不崩〔D-B 守卫〕
```

> **关键（绕开 ship_gate 契约）**：change **归属**靠 `git log -- openspec/changes/<name>/`（pre-archive 路径），**不靠** tag → 零改 checkpoint-commit.sh、零碰 ship_gate 精确豁免（G4 确认 ship_gate.py:200 精确 `=="checkpoint(impl-review)"`）。
>
> **〔spec-review-amendment 边界引擎实测修订〕**——冷镜对全 17 归档语料实测，推翻 grill 单样本外推：
> - **D-A 归档/done 靠 path-rename 非 subject**：实测归档提交 14/15 是 `chore(openspec)`/`feat(...)` 非 `checkpoint(done-archive)`（只 adaptive-workflow-routing 1 个命中前缀）→ done 阶段须靠"提交把 change dir mv 进 archive/"的路径事件判定。
> - **D-B seed/0-1 守卫 + archive 兜底**：创世 `db3c824 chore:初始化` mass 提交铺 ≥3 change dir → 2 个 2026-07-02 seed change 的 pre-archive 路径 log = **0 条**（证伪原 A2"旧路径一把捞全"，那是单样本外推）；须 ①pre-archive 空则兜底 archive 路径 ②剔 seed-mass 提交 ③0/1 提交显式守卫（非只处理"无历史"）。
> - **同名复用**：产生两个 `<date>-<name>` archive 目录 → 检到即标"边界存疑"降级。

## 报告 schema（grill Q3b）+ 阶段词表族（D3 支撑）

**报告 schema**（`openspec/retro/report.md`，无 token 列；hr-tg 双列〔D-E〕）:
```
  ├── 顶部: 覆盖 N change / 有真锚 M / 边界不可解析 K〔D-D: M 须显性,实测仅 2/17 有锚,防 N=2 当趋势〕
  ├── per-change 表: change | 总墙钟 | spec-rev Δ | impl Δ | code-rev Δ | done Δ | #ckpt |
  │                  spec_hr_tg | code_hr_tg〔D-E: 拆两列,spec/code-review 各写一 hr-tg 锚,单列会 none 覆盖命中〕|
  │                  Σfindings | 采纳率 | 独立Σ | [in-progress 标记]
  ├── 聚合① 阶段占比: 整体时间花哪阶段
  ├── 聚合② 成本双峰: 散点(总墙钟 x, code-review占比% y)——小 change 高占比自显
  └── 聚合③ per-镜价值表: lens_metric_aggregate 输出内嵌(采纳率/独立率/出现轮数/N≥10 flag)
```
> **D-D 价值维双源双报告**：per-change join 须扫 **active `changes/*/` + archive 两处**的 `spec-review-report.md` **与** `code-review-report.md` **两份**（每 change 两份、各带 layer 锚），按 layer 分归属——否则有锚的活动 change 被误标"无锚"(codex C3)、且漏 code/spec 一半锚(域轴4-1)。

**阶段词表族（D-C: 最长前缀匹配 + family 归并；archive/done 走 path-rename 非本表）**：
```
  ff                                                    → ff
  grill                                                 → grill
  spec-review*(-autoplan/-rewrite/-gate) / design-gate  → spec-review〔design-gate 是人类门,归 spec-review 段〕
  writing-plans / model-baseline / task<N>* / *-impl    → impl
  impl-review* / final-review* / sdd-final-review        → code-review〔-fix 后缀归并同族〕
  【done 不靠前缀】                                       → 靠 path-rename 检测(D-A)
  propose / plan* / roadmap* / issues / *-cross-review    → planning/other（计入总墙钟）
  匹配语义: 最长前缀匹配(impl-review 优先于 review)；-fix/-gate/-autoplan/-rewrite 归并到主族；不命中 → unknown
```
> 词表 additive（OQ1 的 (c)）——新前缀加一行；MUST NOT 改 checkpoint tag 格式。实测遗漏前缀（design-gate/writing-plans/final-review/model-baseline，对抗2 C）已补入。
> 词表是 **additive 约定**（OQ1 的 (c)）——未来新阶段前缀加一行映射即可，MUST NOT 改 checkpoint tag 格式。

## Decisions（ADR，TG-23）

| # | 决策 | 备选否决 | 状态 |
|---|---|---|---|
| D1 | change 边界靠 `git log -- openspec/changes/<name>/`（**pre-archive 路径**）+ 阶段词表(c)，不改 tag | 查归档路径(只得1条=错)/改 tag 格式嵌 change 名(撞 ship_gate `checkpoint(impl-review)` 精确豁免+改3处) | ✅ **grill Q1 定**（实测旧路径捞全 7 条、零 ship_gate 碰撞；三边界 case 按默认标注降级）|
| D2 | `lens_metric_aggregate.py` **移进** `sdflow-retro/scripts/`（skill 独占，不再 bundle 工具）| 留 bundle tools/ retro 引用——但调研证改后**唯一运行时消费者=retro**（maintain→薄指针；code/spec-review 仅 prose 提及），留 bundle 是延续"寄人篱下"反模式 + 消费仓白背派生工具 | ✅ **grill Q2 定**。附带〔spec-review-amendment 修正〕：SR-K MODIFIED、**init.py 仅移源文件——`ignore_patterns("tests")` 通用排除 MUST 保留**（还护 trivial_shape 测试，F5/G2 双镜；照字面"删派生"会重演 CF-6）、test_init 断言**改指 trivial_shape 非删**（保 tests-exclusion 覆盖，line 119+126）、**4 处** SKILL prose 指针 + docs/ 改指 retro、INDEX 更新 |
| D3 | **不做语义 change 类型分桶**；只报客观列 + hr-tg 客观 flag | 语义 3 分桶（琐碎/routine/HR-TG）——琐碎vs routine 要机判语义，正是 adaptive-routing 被否的"diff 前不可机判语义" | ✅ **grill Q3a 定**（双峰读客观轴：总墙钟/Σfindings/code-rev占比%；hr-tg 直接读锚 hit）|
| D4 | maintain 策略 B（薄指针）| A 全吸收（丢自动提醒）/ C 两处调聚合器（违吸收本意）| ✅ 已定（用户拍板）|
| D5 | 报告 view-only 再生、落 `openspec/retro/report.md`、**tracked（提交进 git）** | 增量手工维护（漂移）/ stdout 不持久 / gitignored（clone 看不到、每次重跑）| ✅ **grill Q4**：tracked 活文档（像 CHANGELOG）；诚实代价=归档新 change 后未跑 retro 前 report stale（锚/git log 才是真相源），跑 retro 即刷新，接受 |
| D6 | **不加 token 估算列** | 加 token 列——无 harness 数据、估算误导（同 adr/0009 诚实口径）| ✅ **grill Q3b 定** |
| D7 | 报告**含进行中 change**（活动 `changes/*/`，标 in-progress）| 只报已归档——藏当前工作 | ✅ **grill Q5 定**（部分生命周期成本仍有值；标 in-progress，价值维可能未落锚→标"无度量锚"）|
| **D8** | 归档/done 边界靠 **path-rename** 检测（提交把 change dir mv 进 archive/），非 subject 前缀 | 靠 `done-archive` 前缀——实测 14/15 归档提交是 chore/feat 非 checkpoint，done 阶段 93% 测不出 | ✅ **spec-review 定**（对抗2 A+接地 G6+codex C2 三方实测）|
| **D9** | 边界检测 seed-mass 剔除 + 0/1 提交守卫 + pre-archive 空则 archive 兜底 | 假设"旧路径一把捞全"——创世 mass 提交致 2 seed change pre-archive 0 提交（证伪 A2）| ✅ **spec-review 定**（对抗2 B 实测）|
| **D10** | hr-tg 拆 `spec_hr_tg`/`code_hr_tg` 双列 | 单列——spec/code-review 各写一 hr-tg 锚，单列 none 覆盖命中/丢 TG | ✅ **spec-review 定**（codex C4）|
| **D11** | 价值维扫 active+archive 两源、per-change join 跨 spec+code 两份报告分 layer | 只扫 archive、只一份——有锚活动 change 误标无锚 + 漏半锚 | ✅ **spec-review 定**（codex C3+域轴4-1）|
| **D12** | "显著呈现"锚定机械契约（报告顶部 ⚠️ 待复评区块 + 前缀），非形容词 | 留"显著"形容词——≥4 处不可机验，死列风险自我复现（grill-not-skippable 教训）| ✅ **spec-review 定**（域轴5）|
| **D13** | report.md 写盘沿用 buglist/todolist **原子写** helper + 对应测试 | 裸写——偏离本仓数据类 skill 写盘硬化口径（parent-dir/覆盖保权限/无残留 tmp/replace 失败原文件不变）| ✅ **spec-review 定**（域轴2附）|

## 可观测性（BASE-11）+ 失败模式表（BASE-06，TG-15）

| 失败模式 | 触发 | 处理（fail-safe 非 fail-silent）|
|---|---|---|
| pre-archive 路径 0 提交 | seed change（创世 mass 提交只碰 archive 路径）| 兜底查 archive 路径〔D9〕；仍 0/1 → 标"边界不可解析"计入 K |
| **恰好 1 提交**（无相邻对）| seed / 单步 change | 显式守卫：墙钟不可算、标注不崩〔D9，非只处理"无历史"〕|
| seed-mass 提交污染 | `db3c824 chore:初始化` 铺 ≥3 change dir | 识别并剔除（一提交碰 ≥3 change dir）〔D9〕；否则创世在途 change 墙钟起点被钉死 |
| 归档提交非 checkpoint 前缀 | 14/15 是 chore/feat | done 靠 path-rename 检测〔D8〕，不落 unknown |
| 相邻 Δ<0（ts 非单调）| rebase/cherry-pick 重排 | 钳到 0 + 标 reorder-suspected〔E〕（当前语料无实例，潜在守卫）|
| checkpoint 前缀映射不出阶段 | 非常规 tag | 归"unknown 阶段"桶，计入总墙钟、报告标注 |
| lens-metric 锚缺失/config off | 该 change 无锚（实测 15/17）| 镜价值维留空 + 标注"无度量锚"，不阻塞时间维 |
| 归档报告解析失败 | fence 污染/格式坏 | 复用聚合器既有 fence-aware + 越域标记，跳过坏行不崩 |
| git log 输出畸形 | 特殊字符/编码 | `core.quotePath=false` + errors=replace（承 trivial_shape 硬化口径）|

- 可观测性：报告顶部打"覆盖 N change、**有真锚 M（实测仅 2/17）**、K 边界不可解析"计数，让缺口显性（不假装全覆盖）。

## Risks / Trade-offs

- **阶段墙钟含人决策时间**：checkpoint Δ 混了人读/拍板/生成时间，非纯 agent 耗时（adr/0009）。→ 诚实标注"阶段级 elapsed（含人）"，不假装是 fan-out 延迟；双峰/占比仍有决策价值。
- **共享生产者零改动是目标但 OQ1 未定**：若 grill 推翻 D1 选了改 tag，blast radius 骤增（ship_gate + spec-workflow 联改）。→ 强烈倾向 D1(a)，把改 tag 列为下策。
- **吸收 maintain 步骤 5 的 cadence 损失**：策略 B 保留薄指针缓解，但自动提醒从"跑聚合器出结果"降为"提示去跑 retro"——多一跳。接受（换来单一真相源）。
- **报告再生成本**：每次全扫 archive + git log，change 多了会慢。→ 可接受（复盘低频、view-only），必要时加增量缓存（Non-Goal 本期）。
