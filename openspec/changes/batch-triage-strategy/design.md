## Context

`sdflow` spec 工作流每次 change 走 ff→grill→spec-review→实现→code-review→done，评审重、慢；`sdflow-retro` 18-change 实测 spec-review 阶段占聚合墙钟 43%（人类门 elapsed 主导）。**降轮次**（少付几次人类门 + 生成）是聚合墙钟的真杠杆（roadmap design D11）。

现状工具 `openspec/issues/consolidation-plan.md` 只覆盖**相关合批**：按 BASE-18「fold-vs-defer 防吸积 AND 门」（同 capability ∧ 高耦合 ∧ 低增量）把相关项合一个 change（REC-1/2/3）。缺口：散落的**琐碎正交项**（typo / cosmetic / 注释订正 / 单点小健壮性）无归属规则——单开付固定循环成本，乱塞坏回退粒度。

红线（roadmap，不可妥协）：**降成本 MUST NOT 靠砍评审安全**。一条 dogfood 教训佐证——对聚焦 change 做 spec-review，4 个独立冷源抓出 grill 没抓到的地基级问题，证「独立冷镜层」load-bearing；故正交批的安全边界必须硬。

参照物 `trivial_shape.py`（Leg1，已激活于 `~/.sdflow/workflow/tools/`）：**post-diff** 判「无逻辑面白名单形状」（注释/文档路径/仅加 tests/纯展示常量）免 code-review Step2。P4 判据同类，但作用时机在 **issue 级 pre-diff**（合批决策时无 diff 可读）。

## Goals / Non-Goals

**Goals:**
- `consolidation-plan.md` 加「大扫除批」维度，与「相关合批」二分。
- workflow 规则集补大扫除批定义 + 硬边界（禁装逻辑面）+ 聚合上限（限规模）。
- 立 issue 级「无逻辑面/低危」近似判据，与 Leg1 白名单同类、可交叉引用、**fail-closed**。
- 对现有 debt 池给出 worked example（正/反各 ≥1）。

**Non-Goals:**
- 不执行任何大扫除批（只定策略/判据）。
- 不改 P2/P3、不改 roadmap 四件套、不推翻相关合批 AND 门。
- 判据不追求「语义完美分类」——只求**安全下界**（宁误排、不误纳）。

## Decisions

> 决策记录（TG-23 ADR 风格：选择 + 备选 + 理由）。标 ★ 者含未决子问题，交 grill（见 Open Questions）。

**D1 — 大扫除批 = 个体琐碎/低危正交项打一包，判据同类 Leg1 白名单。**
备选：允许任意正交合批（不设判据）。弃因：稀释评审注意力 + 无关改动挤一 commit 坏单独回退（roadmap D4）。选：判据只放行「每项个体琐碎/低危」，与 Leg1「无逻辑面」同源。

**D2 — issue 级判据 = 纯规则 checklist（human/model 应用），不做判器脚本。**〔grill 定案 Q-a〕
`trivial_shape.py` 靠 diff 形状（注释符/路径扩展名/tests 路径）机判「结构无行为面」、拿不准即 fail-closed；它**依赖 diff**。合批决策在 **issue 级 pre-diff**——此刻无 diff、只有 issue 描述 + 落点路径。让脚本从散文描述判「将来的改动无逻辑面」= roadmap memo 已判死的「实现前 × 脚本 × 判语义复杂度」三件套同一堵墙。能机判的仅「落点路径」一维（复用 trivial_shape 的 path 分支思路），而路径 obvious 的项人一眼也能判，脚本的确定性买不到增量。
备选（否决）：(b) 薄路径判器——脚本只判路径、语义 fail-closed 转人。弃因：issues 池 ~38 项、合批是**低频人工/模型**动作（非高频自动门），不值 data-class 脚本 + pytest 的维护面。
选：**纯规则**——判据是一份 workflow 规则文档里的 checklist，由做 consolidation-planning 的 human/model 应用。故本 change 塌缩为**纯 markdown 变更**（无 scripts/、无 pytest）。**是「同类判据、非同一脚本」**（roadmap 交叉审 #7）——同类于 Leg1 无逻辑面标准，但不是脚本、更非同一脚本。

> **连带：误纳率口径改诚实（D4 见）**。纯规则无机械门 → 不能*保证*误纳率 0；它是「判据默认排除」的**纪律**，非机械兜底（同 lens-metric SR-M 的 best-effort 口径）。

**D3 — 聚合上限：规模维 SHOULD 可调 + 含生成物硬 MUST 隔离。**〔grill 定案 Q-b〕
每项低危 ≠ 聚合低危，须限规模。维度（roadmap D4）分两类落法：
- **规模维 = SHOULD 可调默认**（无实测基线，诚实标 tunable，规避「拍脑袋」假精确）：
  - 文件数：SHOULD ≤ ~10 文件 / ~8 项（够容最大自然候选簇——rec2 cosmetic/观测群，又不压垮注意力）。
  - 目录跨度：不设硬数，跨越越多越倾向拆（人判）。
  - CI 面积：碰重型 CI 路径的项排除出 sweep（sweep 应是「跑一遍轻 CI 即过」量级）。
- **含生成物 = 硬 MUST 隔离**（非规模调参，是正确性/可审计边界）：碰生成物的项（如 `retro/report.md` 再生、`INDEX.md` 重建）MUST 不混进大扫除批——单独走「再生 commit」，否则 reviewer 分不清手写 vs 再生、坏 diff 可读性。
备选（否决）：(i) 全硬 MUST 数值——无基线支撑、假精确；(iii) 只列维度不给数——太软、ROI 抽空。选 (ii) 折中：可操作又不假装权威。

**D4 — fail-closed 默认排除（纪律，非机械保证）。**
备选：判不准时默认纳入（fail-open）。弃因：违反红线——误纳一个逻辑面项进大扫除批 = 稀释评审 + 埋雷。选：**判据存疑一律排除**（退化为单开 change），损收益不损安全。
**口径（诚实，接 D2）**：判据是纯规则，无机械门；「误纳率 0」是**应用判据者遵守『存疑即排除』的纪律目标**，不是脚本能验证的机械不变量。规则文档 SHALL 把「存疑即排除」写成 MUST 纪律，但不谎称有自动兜底。

**D5 — `consolidation-plan.md` 二分重划，保留 REC 相关合批不动。**
重划 = 在既有「二、合批建议（AND 门）」旁增「大扫除批候选」维度 + 二分标注；顺带刷新 stale 状态（REC-1/G7 等已 ship）。相关合批框架已验证，仅加维度。

**D6 — bundle 权威源纪律。**
批次判据规则落 `sdflow-init/assets/workflow/`（唯一权威源），改后 `sdflow-init update` 回灌下游 + `INDEX.md` 同步；禁只改某下游副本。

**D7 — 大扫除批内「一项一 commit」硬 MUST（item 粒度）。**〔grill 定案 Q-c〕
备选：SHOULD（允许攒几个极琐碎项一 commit）。弃因：允许 sweep 的**安全前提**就是"坏了能单独回退"（roadmap 红线在回退面的落法）；SHOULD 破防。选：sweep 作一个 change 走一轮评审（一 PR），内部 N item = N commit（item = 一个 issue/todo ID，非一文件——同文件两 typo 仍两 commit，revert 粒度对齐「项」）。成本极低、买断"一坏项污染整批"。

### 判据决策流（issue → 批归属，ASCII）

```
issue 池待处理项
      │
      ▼
 ┌──────────────────────────────┐ 是 ┌──────────────────────────┐
 │ 完整 BASE-18 AND门:            ├───▶│ 相关合批                  │
 │ 同cap∧高耦合∧**低增量** 三腿? │    │  REC-1/2/3 既有框架        │
 └───────────┬──────────────────┘    └──────────────────────────┘
             │ 否（正交；或同cap高耦合但高增量→单开/拆）
             ▼（正交继续下判）
             ▼
 ┌─────────────────────────┐   否（有逻辑面/存疑）
 │ issue级判据: 无逻辑面∧低危?├──────────────┐
 └───────────┬─────────────┘               ▼
             │ 是                    ┌──────────────────┐
             ▼                       │ 排除 → 单开change │ ← D4 fail-closed
 ┌─────────────────────────┐        └──────────────────┘
 │ 聚合上限内?(文件/目录/   │   否
 │  生成物/CI面积)          ├──────▶ 另起一包 / 拆分
 └───────────┬─────────────┘
             │ 是
             ▼
      大扫除批（一轮过）
```

## Risks / Trade-offs

- **[判据 pre-diff 语义不可判]**（A1 失效：issue 描述不足以判是否含逻辑面）→ **D4 fail-closed 排除**兜底；judge 只需保证「放行的确实琐碎」，不需保证「排除的都非琐碎」。
- **[聚合上限阈值拍脑袋]**（Q-b 无实测基线）→ 先给保守小上限占位 + 标「实测可调」；宁可初期偏保守（大扫除批小一点、多分几包）。
- **[consolidation-plan 已 stale]**（REC-1=gate-checkpoint-hardening、G7=sdflow-init-hardening 已 ship）→ D5 重划顺带 refresh，避免拿过期建议误导。
- **[脚本化判据反成维护负担]**（Q-a 若选脚本）→ grill 权衡：判据逻辑若足够简单（路径/关键词模式），纯规则可能够用；脚本仅在「需确定性 gate 复用」时才值。
- **[大扫除批坏 bisect]**（多无关项一 commit）→ **D7 硬 MUST 一项一 commit** + 聚合上限兜底。

## Migration Plan

- 纯新增 + 文档重划，无运行时迁移。
- bundle 改动经 `sdflow-init update` 推下游；本仓 dogfood 跑一次 `setup.sh` 使 canonical 生效。
- 回滚 = revert 规则文件 + consolidation-plan（判据未被任何自动门强依赖，回滚零副作用）。

## Compliance

- 遵守 bundle 权威源纪律（改 assets/workflow → update 回灌）。
- 遵守审查顺序（/review → push → /code-review）。
- 遵守红线：判据只作用「无逻辑面/低危」，逻辑面全审；不改任何评审安全层。

## Open Questions

- ~~**Q-a（D2）**：判据形态？~~ **已定案（grill）= 纯规则 checklist、不做脚本**；本 change 塌缩为纯 markdown 变更。
- ~~**Q-b（D3）**：聚合上限阈值？~~ **已定案（grill）= 规模维 SHOULD 可调（≤~10 文件/~8 项起）+ 含生成物硬 MUST 隔离**。
- ~~**Q-c**：一项一 commit 硬规则 vs SHOULD？~~ **已定案（grill）= 硬 MUST，item 粒度**（D7）。

> **三个开放问题（Q-a/b/c）grill 已全部定案回写。** 无残留未决。
>
> **〔spec-review 收敛，见 `spec-review-report.md`〕**：冷镜（对抗×3+接地+codex）大丰收——
> **2 项需设计门拍板**：Q1（worked example/判据「同类 Leg1」口径矛盾——推荐采纳 Leg1 行为面路径守卫、换示例、诚实标本仓候选池薄）、
> Q2（batch-triage = 本仓-local vs bundle-published——推荐本仓-local；D6 回灌故事经接地证实整体破裂：copy_bundle full=False/INDEX 指错 index-section.md/BASE-18 下游悬空/trigger-catalog 错接入点）。建议**先 Q2 后 Q1**。
> **6 项已采纳 amendment（[spec-review-amendment] 回写 specs）**：A1 D7 执行协议+验证锚 · A2 三分类补低增量第三腿 · A3 延迟绑定作单开子态 · A4 聚合上限有牙升MUST+每项判定记录 · A5 cross-ref spec-workflow · A6 术语统一三元标注。
> 拍板后回写 specs 最终版 + SR-M lens-metric 最终化 + `ship-gate: design-approved` 锚。
> **Q-d（grill 收敛检验）**：塌成纯 markdown 后价值是否仍在、是否值独立 change？**定案 = 是**——3 条硬 MUST（禁逻辑面/生成物隔离/一项一 commit）为具体安全栏非「小心点」；对真实 backlog 做真分诊、解锁 rec2 cosmetic/观测群一轮扫；改 bundle 权威源 + 立 spec capability + 属安全判据（dogfood 教训：冷审 load-bearing 区）→ **独立 change + 保留全 spec-review，不因「只是 markdown」降路径**。
