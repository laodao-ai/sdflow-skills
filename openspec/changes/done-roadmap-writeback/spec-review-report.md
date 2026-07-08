# Spec Review Report — done-roadmap-writeback

> 阶段二设计评审（sdflow-spec-review 编排）。7 路并行冷审：广审(broad·simulated) + 对抗×3(adversarial) + 接地(grounding) + workflow哲学(domain) + codex outside-voice(design-voice)。中途不打断，决策登记进本报告，人工设计 HARD-GATE 一次拍板。

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
> Step1 广审为 simulated 降级（子代理跑 CEO/design/eng/DX 视角，未原生调 gstack autoplan skill）；据此 outside-voice 复用守卫判 `simulated-source` → 回落自跑 design outside-voice（codex，见 gstack-review.md 佐证）。

## 概要

**7 镜收敛度极高**，findings 聚成一个**设计级根因** + 若干实现期缺口。核心裁决：本设计的机械机制（机器锚行 / 机械-判断切分 / 反静默双落盘意图）延续本仓成熟范式，但**整个自动化可靠性系于「人/AI 起手记得写正确的锚」这一 producer 契约，而该契约无任何机械强制或检测**——这是 2 个致命 + 多个高危 finding 的共同根因，且踩中本仓 adr/0006「机械 prose 协议 MUST 脚本化，否则 = 静默跳步」的靶心。

**接地镜 9 条代码事实全部核实一致**（design 对 sdflow-done 六步/两模板/§2.1 sweep/范式脚本叙述准确），设计非架空——问题在机制完备性，不在事实错误。

---

## 决策登记区

```
┌────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  关联锚 producer 契约无机械闭环（致命·多镜共识·根因） │
│ [需拍板] Q2  锚 subtask 集起手写死 ≠ 实际交付集 → 误勾（致命）      │
│ [需拍板] Q3  6 件全量 scope vs 最小可行版 + 正路径无真实 dogfood   │
│ [自动决策] D1-D10  修法已定，设计门默认接受（详见下）              │
│ [已裁掉]  无（findings 质量均高，无静默丢弃；1 条弱证据自排除见末）  │
└────────────────────────────────────────────────────────────────┘
```

### [需拍板] Q1 — 关联锚 producer 契约无机械闭环（致命·根因）

**命中镜**：哲学镜[Major] + 对抗1[致命] + 广审[高] + codex[高] + 对抗2[中高]（5 镜共识）。

**问题**：L1/L2 全靠 grep proposal 里的 `<!-- roadmap: … -->` 锚，但「起手 MUST 带锚」只是 `task 1.2` 的纯 prose 声明，**无 lint/gate 校验锚是否真被写入**（对比本仓 `config_lint`/`batch lint` 先例——同类"prose 契约必须脚本化校验"问题的既有解法，本设计的 P0 项偏没配）。哲学镜的锋利判定：我 grill 时把 L1 从"解析自然语言"纠正到"读机器锚"只走了一半——**"producer 会带锚"这个目标态假设本身若无机械支撑，就是把 adr/0011 目标态论证（解析器语义）误套到"人是否遵守无门禁 prose MUST"（行为合规），恰是 adr/0006 点名的静默跳步**。

**三个选项**：

| 选项 | 内容 | 系统镜 | 用户镜 | 开发循环镜 |
|---|---|---|---|---|
| **A 补机械闭环** | ①ff/spec-review 阶段加 lint「proposal 提及某 roadmap 名/该 change 是 roadmap 驱动 但缺锚 → 拦」②`roadmap-link` 写锚时校验 subtask id 真存在于 roadmap ③"有锚但 name 解析不到目录" → fail-closed 非静默 | 锚全生命周期机械闭环，真落地 adr/0006 | 起手漏锚被 gate 拦、当场补 | scope 再增（+lint），但根治 |
| **B 换关联判据** | 不靠"起手写锚"，改双向：roadmap 侧维护「子任务 ↔ change 名」映射（producer 集中在 roadmap.md 维护，比每个 change proposal 写锚更少遗漏面），done 拿本 change 名反查 | 关联信号集中一处、漏面小 | 无需起手记得写锚 | roadmap.md 附录 C 已有"阶段→建议 change 名"雏形；但"建议名"≠实际名，需契约化 |
| **C 降级为诚实辅助** | 承认这是记录维护辅助非正确性门，接受"漏锚→退化手动回填"，但**必须显式化漏锚检测**（spec-review 加人工审查项「roadmap 驱动 change 必带锚」），删掉 design/proposal 里"真漏会被 hand-off 提示"的不实承诺 | 不假装根治、诚实收窄 | 漏锚有人工审查兜 | scope 最小，但自动化价值打折 |

**推荐 = A（主）+ C 的诚实收窄（次）**。理由：Q1 是整个 change 价值的地基——若锚无机械闭环，回写自动化的可靠性等于"人不忘写锚"的概率，与原痛点（人不忘手动回填）同构，价值存疑（广审/对抗共识）。A 用 lint 补闭环、真落地 adr/0006（与本仓 config_lint/batch lint 一脉）；同时采纳 C：无论如何删掉"真漏会被提示"的不实承诺（哲学镜证其在当前机制下不可兑现）。**主次**：先补 A 的锚存在性 lint（P0，闭合根因），B 的双向映射作为 A 之上的加固备选（若 lint 仍嫌不足再上）。

### [需拍板] Q2 — 锚 subtask 集起手写死 ≠ 实际交付集 → 误勾（致命）

**命中镜**：对抗3[致命，独立贡献]。

**问题**：锚在 change **起手**写死 `subtask: 3.A,3.B`（真实先例 mlh-p3 合批 3.A+3.B），若实现期 defer 掉其中一项（如 4.D.4 被 defer 的先例），"全定位→勾全部"的机械逻辑（MUST NOT 解析自然语言、只判"能否定位到复选框行"）会**把从未交付的子任务机械勾成 `[x]`**——污染"复选框=项目真相源"核心不变量，且回写在 archive 后自动发生、无人工卡点。这比 design 唯一关注的"漏标注"严重（假阳性）。

**选项**：①勾选真相以**本 change 的 tasks.md 完成态**为准（脚本交叉核对 tasks.md 对应任务是否 `[x]`），锚只定"关联哪些"、不定"完成哪些"；②回写前要求人工/模型确认实际交付集（引入判断）；③锚在归档时按实际完成**重写** subtask 字段再回写。

**推荐 = ①**。理由：tasks.md 复选框是本 change 内已有的"实际完成"确定性盘面（done 第 0.3 步已做 tasks 复选框对账），脚本"勾 roadmap 子任务 ⟺ 对应 change 任务在 tasks.md 已 `[x]`"是机械可判、无需判断，且堵死"锚声明≠实际交付"的假阳。系统镜：复选框真相源不被污染；开发循环镜：复用已有的 tasks 对账盘面，零新判断。

### [需拍板] Q3 — 6 件 scope vs 最小可行版 + 正路径无真实 dogfood

**命中镜**：广审[中·CEO] + 对抗1[高·dogfood]。

**问题**：①6 件 scope（含改 sdflow-roadmap 生成格式 + 迁 2 roadmap）服务的既有基数只有 **2 个 roadmap**（1 个高频），边际收益存疑；②本 change 自身无锚 → 只能 dogfood"无关联跳过"分支，**best-effort 回写正路径的真实端到端编排（子代理判断 + archive/commit 时序 + git add 收纳）在整个 change 生命周期从未真实跑过一次**，只 fixture 单测——正是 MEMORY「emitter dogfood 独家挖出致命 F1」教训的反面（主动放弃对正路径的冷 dogfood）。

**选项**：①全量 6 件 + 补 Q1/Q2 闭环（scope 最大、根治）；②最小可行版（先做 done 消费端认新格式 + 关联锚 lint，旧 2 roadmap 暂人工回填，等第 3 个 roadmap 或 mlh 阶段 5/6 再迁移生成侧）；③全量但**必须**加一个真实 roadmap 驱动 change 走一次完整 dogfood（如给某个 mlh 剩余子项起 change 时带锚、真跑一次回写）。

**推荐 = ② + ③的 dogfood 要求**。理由：CEO 视角 2 样本撑不起 6 件全量的边际投入；最小可行版先落"关联锚 lint + done 消费端"（闭合 Q1 根因、价值最高的 P0），生成侧模板优化/迁移待真实需求触发。无论选哪个 scope，正路径 MUST 有一次真实 dogfood（③），不留"首次生效在未来某 change 归档、设计者上下文已消散"的盲区。

### [自动决策]（设计门默认接受，可覆盖）

- **D1 反静默口子修法**〔对抗2+哲学+codex+广审〕：①"有锚但 name 解析不到目录/四件套不完整" → **fail-closed 留人工，非静默跳过**（与"真无锚"分流不同分支）；②降级标注**落 task-log**（在 roadmaps/，持久、随第四步 commit），**不落 hand-off（见 D2）、不只落 stdout 摘要**（spec 三处措辞"task-log/摘要"须统一为"MUST 落 task-log"）。
- **D2 hand-off 时序修**〔codex 独家〕：`hand-off.md` 在第二步生成、第三步随 archive **移入 `changes/archive/`**——回写在 3.5 步（archive 后）已无 active `{change_dir}/hand-off.md`。故降级标注 MUST 落 **task-log**（回写目标本体、不随归档移走），不落 hand-off。spec/design/tasks 三处"写 hand-off"改"写 task-log"。
- **D3 定位鲁棒**〔对抗2+3+codex〕：勾选定位 MUST **行首锚定** `^- \[ \] {id}\b`（防命中散文层 id 提及如 roadmap.md:111，本仓 P3 F1/F3 同款正则过匹配坑）；概览表状态列更新 MUST 用结构化表解析（防 cell 内 `|`/加粗错位），插入后校验列数与表头一致；task-log 插入点定位 MUST 处理重复日期 H2（真实有两个 `## 2026-07-08`）。补对应 spec Scenario + pytest。
- **D4 判断切分重划**〔codex+对抗3+哲学〕：阶段状态 enum **可机械化**（codex 给函数：无完成子任务=planned/部分=in-progress/全非deferred完成=delivered/显式放弃=deferred，从该 phase 全子任务复选框聚合）——移出"判断"、归脚本；**里程碑散文句**才是真判断（跨 6 阶段综述，roadmap.md:12 一整段），"判断收窄两处"修正为"里程碑句一处 + 完成总结叙述一处"。design D-2/D-5 补 enum 机械判定规则。
- **D5 SKILL:195 误引删/弱化**〔广审+哲学+codex〕：`sdflow-roadmap/SKILL.md:195` 原文是"`/opsx:verify` 接 post-hook 校验 task-log Review 处置**穷尽性**"（校验≠写入、verify≠done），与本 change 回写不同。删掉 adr/0013/design/proposal 三处"设计原意兑现"强断言，改谦抑措辞或直接用 fold 判据（不需误引背书）。
- **D6 3.5 步 model 档位**〔广审+哲学〕：回写步含判断（完成总结/里程碑句），MUST 显式定档——建议**并入第三步 archive 中档子代理**（仿 §2.1 sweep 折进第二步先例，省一个子代理编排成本）。补 tasks 5.1 + 模型选择表。
- **D7 bundle 纪律**〔广审〕：关联锚契约/起手规范是 workflow 规则 → MUST 改 `sdflow-init/assets/workflow/`（权威源，已核实 ff-generation-constraints.md/trigger-catalog 无 roadmap 字样）再 `sdflow-init update` 推下游，**不只改仓内 openspec/workflow/**（dogfooding 红线）。tasks 1.2 显式点名目标文件 + 加回灌步。
- **D8 幂等键**〔对抗3+codex〕：task-log 机器锚幂等键 = 每 `(change, subtask)` 一条锚（模型叙述可合并、脚本锚逐 subtask 校验）；勾选对已 `[x]`+标注行的重跑行为 MUST 定义（行首锚定 `- [ ]` 天然对已勾行 no-op，写进 spec）。
- **D9 enum 值集单一源**〔哲学〕：`{planned,in-progress,delivered,deferred}` MUST 纳入 D-1 同一份机读契约（roadmap-template + 回写脚本都从该文件读，不各自硬编码）——同 lens-metric-contract 单一源纪律。
- **D10 阶段状态漂移对账**〔哲学〕：阶段状态 enum 是从复选框派生的缓存值，人工编辑 roadmap 后会漂移、无 `reindex` 式回读校验兜底 → 在 Non-Goals/Open Questions **显式记一笔"暂不做漂移对账，风险接受"** + todolist 存 backlog，不留白（反第二真相源）。

---

## 各镜 findings 汇总（按簇）

| 簇 | finding | 命中镜 | 置信 | sev | 裁决 |
|---|---|---|---|---|---|
| **A 锚无闭包** | A1 锚 MUST 无 lint 校验存在（违 adr/0006） | 哲学/对抗1/广审/codex | 高 | 致 | Q1 |
| | A2 subtask id 不校验存在于 roadmap | 对抗1/codex | 高 | 高→并Q1 | Q1 |
| | A3 锚 subtask 集≠交付集→误勾 | 对抗3 | 高 | 致 | Q2 |
| **B 反静默** | B1 降级标注落点三处矛盾、可只写 stdout | 对抗2 | 高 | 高 | D1 |
| | B2 hand-off 时序：3.5 步 hand-off 已随归档移走 | codex(独家) | 高 | 高 | D2 |
| | B3 "有锚但 name 错/roadmap 缺"=无锚同分支静默吞 | 对抗2/codex/广审/哲学 | 高 | 高 | D1 |
| **C 定位** | C1 subtask id 散文层误命中、写坏叙述层 | 对抗2 | 高 | 高 | D3 |
| | C2 概览表 enum 列插入无健壮表解析 | 对抗2/3/codex | 中高 | 中 | D3 |
| | C3 task-log 自由格式(重复日期H2)插入点 | 对抗3 | 中高 | 中 | D3 |
| **D 切分** | D-a 里程碑句实为跨6阶段综述、判断被低估 | 对抗3/codex | 高 | 高 | D4 |
| | D-b enum 判定函数缺失(可机械化) | codex/哲学 | 高 | 高→D4 | D4 |
| | D-c enum 4值表达力不足+双列漂移(端态A已定) | 对抗3/对抗2/广审 | 高 | 中 | D4/D10 |
| **E 接地** | E1 SKILL:195 误引撑非越界 | 广审/哲学/codex | 高 | 高 | D5 |
| **F scope** | F1 正路径无真实 dogfood | 对抗1 | 高 | 中 | Q3 |
| | F2 6件服务2roadmap边际收益存疑 | 广审(CEO) | 中 | 中 | Q3 |
| | F3 merge中止时roadmap在main仍旧值 | 对抗2 | 中 | 低 | 记风险 |
| | F4 并行分支放大roadmap merge冲突面 | 对抗1 | 中 | 低 | 记风险 |
| | F5 关联锚规则须改assets/workflow(bundle纪律) | 广审 | 中 | 中 | D7 |
| **G 杂** | G1 3.5步无model档位 | 广审/哲学 | 高 | 中 | D6 |
| | G2 幂等键未定义 | 对抗3/codex | 中 | 中 | D8 |
| | G3 enum值集缺单一源 | 哲学 | 中 | 低 | D9 |
| **接地** | 9 条代码事实全部核实一致 | grounding | — | — | ✓无异常 |

**[已裁掉/自排除]**：对抗2 自查排除"issues sweep 与回写并发写 openspec/"（单会话内两步严格串行、非真并发）——非静默丢弃，记录于此备审。

---

## 度量锚（lens-metric v1）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="10" 采纳="10" 裁掉="0" defer="0" 独立="2" sev="致2/高4/中3/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="7" 采纳="7" 裁掉="0" defer="0" 独立="1" sev="致1/高2/中4/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="—" findings="8" 采纳="8" 裁掉="0" defer="0" 独立="2" sev="致1/高3/中3/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="0" sev="致1/高4/中1/低0" -->

<!-- sdflow:outside-voice v1 site="design-voice" guard="simulated-source" runner="codex" reason_code="reused-source-simulated" findings="6" truncated="false" -->

<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG-12/14/18/19/20/22/23 均不在 HR-TG 子集{TG-04/06/07/08/09/16/17/26}；文档回写编排、误写可 git 回退，非运行期爆炸/数据损坏难回退类" -->

> **残余信任边界声明**：findings 分类（归哪镜/裁决/sev）、roster 完备性、JSON 誊写准确性仍是主 session 信任边界；emitter 只保证给定输入的确定性归约。`采纳/裁掉/defer` 为设计门拍板前临时值，拍板时最终化（SR-M，best-effort）。

---

## 收敛口

**不建议直接进设计 HARD-GATE 批准原设计。** 本轮抓出 **2 致命 + 5 高**，且核心（Q1 锚无机械闭环、Q2 误勾）是**设计级方向问题、非实现期顺手补的缺口**。建议设计门按此序拍板：

1. **先决 Q1**（锚机械闭环方向：A补lint / B换判据 / C诚实降级）——它是价值地基，决定后续是否值得投入。
2. **决 Q2**（误勾修法，推荐①交叉核对 tasks.md 完成态）——堵真相源污染。
3. **决 Q3**（scope 全量 vs 最小可行版 + 强制一次正路径真实 dogfood）。
4. Q1-Q3 定向后，**D1-D10 作为 amendment 一并落**（多为实现约束/spec Scenario 补充），重写 design/specs/tasks 标 `[spec-review-amendment]`。

拍板后按 D2 起手规范补齐、按 A 补锚 lint，此设计方可成熟进实现。**这是本仓「冷层 load-bearing」的又一实证**——7 镜在实现前拦下了一个"接地事实全对、但机械闭环有系统性缺口"的设计。

<!-- 设计门拍板后：主 session 在此文件头部 prepend frontmatter ship-gate.design_approved=true（拍板前不写） -->
