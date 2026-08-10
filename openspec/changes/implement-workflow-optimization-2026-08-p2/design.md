# Design — implement-workflow-optimization-2026-08-p2

## Context

动机见 `proposal.md` §Why。设计输入：`decision-memo.md`（D1-D7 / C1-C8）+ `adr/0041`（裁决地基改造全文）+ retro 报告实测数据（`openspec/retro/report.md` 聚合③/④）。现状关键事实：

- code-review Step3 现行三段信号：数值置信 <80 硬滤 + 无引文封顶 ≤50 + 跨模型豁免矩阵直通（`sdflow-code-review/SKILL.md:328-342`）；spec-review 已是高/中/低分流无数值滤（`sdflow-spec-review/SKILL.md:309`）。
- `retro_report.py` 待复评区块纯轮数触发、无处置输入源（`retro_report.py:602-629`，C8）。
- lens-metric 锚无置信字段，三计数与二元裁决三态同构（C6）。
- `token_snapshot.py` 已具 `--step` + anchor 接口（C5）；sdflow-done 步序 = 0 确认 → 1 Verify（强档）→ 2 hand-off → 3 Archive（中档）→ 4 Commit（弱档）→ 5 Merge → 6 摘要。

## Goals / Non-Goals

**Goals（设计层边界）**：裁决协议改动收敛在两个评审 SKILL 的 Step3 段 + 一个新机械脚本；处置机制收敛在一个数据文件 + `retro_report.py` 一处消费；终态快照零新采集路径。

**Non-Goals**：不改 lens-metric 锚 schema；不动 anchor_lint 合法组合矩阵；不改 Step1/Step2 编排结构（roster 段只加派发条件行）；范围级 Non-Goals 见 proposal。

## Decisions

本 change 的 B 相位决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)；裁决地基改造见 `openspec/adr/0041`。以下为 design 相位定案（proposal §开放问题的三项 + 两项形态细化）：

### DD1 处置记录文件 = `openspec/retro/mirror-dispositions.yaml`

- **格式**：yaml 列表，每项 `{layer, lens, host, runner, site, disposition, condition, date, rationale}`；`disposition ∈ {保留, 降采样, 淘汰, 不适用}`（「不适用」用于回落路径产物这类非独立 roster 成员，见处置表草案）；`condition` 仅 `降采样` 必填（写机械可判派发条件原文）。
- **匹配键** = `(layer,lens,host,runner,site)`，与 `LMA.group_key` 同键（不另造口径）。
- **消费**：`retro_report.py` surfacing_block 读之——命中的镜行内追加 `→ 已处置: <disposition> (<date>)`；文件缺失 = 零注记照旧 flag（向后兼容）；yaml 坏 / disposition 非法 ⇒ fail-loud 非零退出（宁红勿静默，同报告工具反静默方向 adr/0016）；文件内含未命中任何锚组的键 ⇒ 告警不阻断（可能是已淘汰镜的存量记录）。
- **砍掉的候选**：处置写进 SKILL.md 注释（retro 读不到）；写进 retro 报告本身（view-only 再生即丢）。
- **落位理由**：`openspec/retro/` 已是 retro 域目录（report.md 所在）；yaml 承 adr/0036（yq 可操作）。

### DD2 「按条件跳过」锚表达 = 复用 `runner="none"` + findings=0，cause 枚举扩一值

条件化派发判「本轮不派」的镜 **MUST 照落锚行**（`runner="none"`、`findings=0`），并在 lens-metric contract 的 `runner="none"` 成因清单（现 host-unknown / secret-hit / fallback-unavailable）扩一值 `condition-not-met`，按 contract §enum 扩展治理升版本。**锚行必落 = 跳过可见**（grill-not-skippable：跳过类判定不能不可见）；出现轮数照计，处置追踪口径一致。**砍掉的候选**：不落锚行（「忘了派」与「条件跳过」不可区分，正是空箱纪律要杀的静默形态）；新 reason_code 字段（reason_code 属 outside-voice 锚语义，普通镜行引入 = 无谓扩面）。

### DD3 终态 token 快照 = done 第 3 步（Archive）起手前主 session 采一次

- `sdflow-done/SKILL.md` 第三步起手（派 archive 子代理**之前**、change 目录尚在原位）主 session 跑 `token_snapshot.py --step done-final`（anchor=true），追加进 change 目录 `token-log.jsonl`，随 archive 搬走。
- 覆盖 Verify（收尾最重步）+ hand-off；**残余尾巴 = archive/commit/merge 自身用量**，为接受边角（量级远小于 verify，且 archive 后 change 目录已搬、追加即写归档路径，复杂度不值）。
- 失败显式降级不挡收尾（同 token-snapshot-anchor 既有 Requirement 口径）。

### DD4 validator 复核层 = 机械脚本，不是弱档模型

T112 原文写「弱档 validator」，本设计升格为**纯机械脚本**（暂名 `findings_ref_check.py`，落 `sdflow-init/assets/workflow/tools/` 同类脚本旁，实施定名）：逐条核 finding 的 ① 引用路径存在 ② file:line 落在文件行数内 ③ 单行引文为目标文件子串（pre-emit 引文纪律已强制 findings 带单行引文或证据包，`sdflow-code-review/SKILL.md:318`）。三查全过 = pass；任一不过或无引文无证据包 = 机械落「已裁掉」区留痕。**引文与断言的语义对应不查**——那是强档二元裁决本来的活（基准 1 切分：有确定性信号的下沉脚本，语义残余留裁决）。spec-review 侧同脚本，核对象含四件套文档。输出遵循消费型信号校验器输出诚实（CONTEXT.md「信号内诚实」）。**砍掉的候选**：弱档子代理逐条核（模型做子串比对 = 把机械活交给会幻觉的层，且更贵）。

### DD5 历史重放 = 一次性 harness，不进常驻资产

重放脚本/流程落本 change 目录（`impl-reports/replay/`），对 3-5 份归档报告：`git worktree` checkout `reviewed_sha` → findings 逐条过 DD4 脚本 + 强档二元重裁 → 与历史裁决对表出报告（误杀率红线 = 0 才可部署；噪声重入率标「参考」）。不装进 bundle、不留运行时入口。

### DD6 处置表草案（13 面镜 · 依据 = 独立率 + 实修率(达标者) + 结构角色 · **终拍板 = 设计门**）

| # | layer | lens (host/runner/site) | 轮数 | 独立率/采纳率 | 实修率 | 草案处置 | 依据要点 |
|---|---|---|---|---|---|---|---|
| 1 | code-review | adversarial | 35 | 52%/73% | 33%（达标） | **保留** | 双率最高段，实修率达标 |
| 2 | code-review | domain | 33 | 32%/70% | 50%（达标） | **保留** | 实修率最高，TG 条件化本已存在 |
| 3 | code-review | broad（step1 scope 审计） | 31 | 44%/72% | — | **保留** | 产量低但为 scope-drift **守卫**，spec 钉死守卫时序，非产量逻辑 |
| 4 | code-review | history | 34 | 29%/57% | 50%（参考） | **降采样** | 双率最低段；条件：diff 含 rename/大规模改动既有文件（git 历史敏感形态，机械可判） |
| 5 | code-review | outside-voice codex/code-voice | 31 | 49%/81% | — | **保留** | 跨模型第二意见 spec 默认开；实战独家贡献实证（跨模型 voice 产出碾压同族温镜） |
| 6 | code-review | outside-voice codex/hr-tg | 16 | 43%/75% | — | **保留** | 本已 HR-TG 条件化，无进一步降采样空间 |
| 7 | spec-review | adversarial | 39 | 47%/93% | 无数据 | **保留** | 采纳率全场最高段 |
| 8 | spec-review | broad（strategy/plan-eng 广审） | 39 | 41%/87% | 0%（参考，n=2） | **保留** | 最大产出源（415 条） |
| 9 | spec-review | domain | 17 | 43%/96% | — | **保留** | 采纳率 96%，TG 条件化本已存在 |
| 10 | spec-review | grounding | 39 | 30%/73% | 0%（参考，n=3） | **降采样** | 独立率低段；条件：design 引用既有代码事实时才派（greenfield 无接地对象，机械可判：delta 是否触碰已存在文件） |
| 11 | spec-review | outside-voice claude/design-voice | 11 | 24%/88% | — | **不适用** | 此行是 codex 不可用时的**回落路径产物**，非独立 roster 成员，砍留随 voice 机制本体 |
| 12 | spec-review | outside-voice codex/design-voice | 31 | 19%/78% | — | **保留** | 独立率数字与实战印象有张力（历史独家高危 2 条），跨模型 spec 默认开；窗口期重点观察对象 |
| 13 | spec-review | outside-voice codex/hr-tg | 12 | 34%/94% | — | **保留** | 同 #6，本已条件化 |

草案净效果：2 降采样 + 1 不适用注记 + 10 保留，无淘汰（弱产出镜优先降采样是 roadmap 既定纪律）。**此表为草案，逐镜终拍板在设计 HARD-GATE 由人一次过**；拍板结果实施期写入 `mirror-dispositions.yaml` + SKILL roster 段。

## 数据模型与生命周期〔TG-05〕

**`mirror-dispositions.yaml`**（新）：创建于本 change 实施期（拍板后）→ 追加/修订于未来复评轮（同镜新处置 = 覆写该键条目，git 史即审计链）→ 无删除路径（淘汰的镜保留条目作历史注记）。消费方唯一：`retro_report.py`。
**`token-log.jsonl` 新行形态**：`step="done-final"` + `anchor=true`，生命周期与既有行一致（只追加、随 archive 搬迁）。
**评审报告「已裁掉」区新增来源标记**：validator 机械裁掉项标 `[ref-check]` 与裁决裁掉项区分（重放与 retro 可辨来源）。

## 组件与依赖图〔TG-13/14〕

```
                    ┌─ 裁决协议面（commit B）─────────────────────────┐
 Step2 各镜 findings ─▶ findings_ref_check.py（机械前置，弱档档位不再介入） │
                    │        │ pass            │ fail → 已裁掉区[ref-check]│
                    │        ▼                                        │
                    │  强档二元裁决（采纳/裁掉/defer + critique，       │
                    │  置信只作排序；spec-review 侧保留「拿不准→决策登记区」）│
                    └───────┬──────────────────────────────────────┘
                            ▼
              lens_metric_emit.py（输入兼容，锚 schema 不动）
                            ▼
 ┌─ roster 面（commit A）──────────────┐      lens-metric 锚（archive）
 │ SKILL roster 段：per-镜派发条件行     │             ▼
 │ 跳过轮 → 锚行 runner="none"          │      retro_report.py ◀── mirror-dispositions.yaml
 │   findings=0 (condition-not-met)    │      （待复评区块行内注记）
 └────────────────────────────────────┘
 sdflow-done 第3步起手 ─▶ token_snapshot.py --step done-final ─▶ token-log.jsonl
```

组件清单：`findings_ref_check.py`（新，机械）｜两评审 SKILL Step3+roster 段（改）｜`mirror-dispositions.yaml`（新，数据）｜`retro_report.py` surfacing 注记（改）｜`sdflow-done/SKILL.md` 第 3 步接线（改）｜lens-metric contract cause 枚举（改，升版本）｜重放 harness（一次性，不入 bundle）。

## Risks / Trade-offs

- [强档裁决输入量增大（无 <80 预滤）] → validator 机械前置先杀引用失实项对冲；C4 实证数值滤独立击杀本就极少，净变化小；per-change token 维已可观测（p1），窗口期看趋势。
- [误杀历史上会被采纳的 finding] → 部署前历史重放误杀率红线 = 0；出现即逐条追查，不部署。
- [降采样条件误判（该派没派）] → 锚行必落（DD2）使跳过可审计；前瞻窗口漏检归因 roster，独立 commit revert（C3）。
- [处置表草案数据薄（11 面无达标实修率）] → 草案仅 2 降采样、无淘汰，保守方向；设计门人工逐镜复核（D1 fallback 既定）。
- [重放语料的裁掉项原文缺失] → 噪声重入率降级「参考」，接受边角（memo §接受的边角）。
- [contract 枚举升版本牵连消费方] → cause 清单是文档层散文枚举（非机读块），实耗为 grep 消费方 + 文档同步，面小。

## Migration Plan

1. **commit B（裁决协议面）**：`findings_ref_check.py` + 两 SKILL Step3 重写 + contract cause 枚举 + emitter 输入兼容——bundle 权威源（`sdflow-init/assets/workflow/`）先改。
2. **历史重放**（部署门）：误杀率 = 0 通过后才进 3。
3. **commit A（roster 面）**：设计门拍板后的处置表 → `mirror-dispositions.yaml` + SKILL roster 段派发条件 + `retro_report.py` 注记。
4. **done 终态快照**（独立小 commit）。
5. 下游：`sdflow-init update` 推消费仓；运行 checkout `git pull` + `setup.sh`。
6. **回滚**：commit A / B 互相独立可分别 revert（C3）；快照 commit 删一行即净。前瞻窗口（3 change）为 roadmap 层残项，不阻塞本 change 归档。

## Open Questions

无——proposal 三项开放问题已由 DD1-DD3 定案。

## Compliance

遵守：四条通则（范围锚 roadmap 阶段 2 原文，无自加约束）；DOC-1（本文正文即最终态）；premise-verification（代码事实均实读核验，见 Context 引用行号）；lens-metric contract §enum 扩展治理（DD2 升版本）；报告工具反静默方向 adr/0016（DD1 fail-loud / DD2 锚行必落）。无豁免项。
