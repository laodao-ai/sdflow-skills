---
ship-gate:
  verify: PASS
---

# Verify Report — rebuild-sdflow-roadmap-v2

> 日期：2026-07-11
> 验证方式：纯 Markdown change（TG-18 未命中，无代码无自动化测试）——以「措辞在场性 + 跨文件口径一致」为锚，每条 ✅ 附可机验锚点（文件:行 / grep 命中 / readlink / git diff）。Do-Not-Trust 冷核，不信任复选框与既有报告。

## 结论行

**PASS**——tasks 1-4 + 6（12 项）全部落地，锚点齐备；tasks 5.1-5.3 为 Q-C 拍板的受控延后（排期 T129，非缺口）；spec R1-R7 七条 Requirement 的 MUST 行为逐条在场。发现 1 处 Minor 跨文件口径不一致（task-log 模板示例用 `-phase-1`，与 SKILL MUST 规则冲突），不阻塞发布。

---

## 一、tasks.md 15 项逐条核对

| Task | 状态 | 核验锚点 | 判定 |
|---|---|---|---|
| 1.1 SKILL 主体重写（三件套/去 change 壳/收尾五项/兼容/逃生舱/生命周期） | [x] | SKILL.md 488 行（wc -l）；规则 4 直写不经壳 :75-79；产出模式（兼容 :92-98 / 逃生舱 :100-102 / create-continue-replan :104-116）；收尾五项 :346-354；grep `opsx:new plan-`/`plan-{name}`/`plan-{topic}` 全空（无 change 壳流程） | PASS |
| 1.2 讨论层分档改造（双判据/降级/宿主中立/preflight/gate-0/office-hours/路由对照表） | [x] | SKILL :142-196；双判据无轮数预估 :144；三分支 A/B/C :148-181；宿主中立探测 :163；tracker doc preflight fail-closed :167；gate-0 五项原样 :124-130 + 直接结晶依据一行 :134；路由对照表 6 例（≥4）:189-196 | PASS |
| 1.3 footage 规则（落盘/两段式/命名权先定字面量/持久字段/路标行/再入钉死一种） | [x] | SKILL :200-246；落盘 :206-207；命名权先定+字面量调用语模板 :212-220；持久字段 Tracker root/Effort kind :222-229；顶部路标行 :232-237；再入钉死「单 map 分批续用/满30票归档」:239-245 | PASS |
| 1.4 review 分档 + 近细远雾（整体 plan 话术/review-waived/未审待恢复/覆盖/近细远雾五节） | [x] | SKILL review :278-318（整体 plan 话术 :287-293；review-waived :299；未审待恢复 :308；显式覆盖 :302-304）；近细远雾 :322-338（近期理由必写 :324；远期缺 X 信息 :326；长周期例外 :330；补细重判 :334）；陷阱节同步 :391-447 | PASS |
| 2.1 删 requirements-template + design 头部伸缩章（无编号章名/兜底/验收门槛槽） | [x] | ls references/ 仅 5 文件无 requirements-template；design-template.md 「需求与目标态」章 :19-84（无编号章名注 :25，正文编号起于 `## 1.` :86）；痛点/目标态判据/验收门槛/Non-Goals(可证伪) 必填；SR-13 兜底注 :24,:37；受众/功能取舍/NFR :63-84 | PASS |
| 2.2 roadmap 模板近细远雾注释 + 远期骨架 | [x] | roadmap-template.md 近细远雾注 SR-14 :24-35；远期阶段 3/4 仅目标句+雾区备注、无子任务/验收节 :117-146；长周期依赖例外 :130-136 | PASS |
| 2.3 task-log/memo/paradigm 模板更新（Status 三态/flush 场景/长档由 footage 取代） | [x] | task-log-template Status: ACTIVE 三态 :19-20 + Review 处置三态 :62-74；memo-template 短档可选定位 :5 + 降级模式必需 :7 + SR-5 flush :11,:19；paradigm 短/中 memo 长档 footage 收敛四→三件套 :114-115 | PASS |
| 3.1 issue-tracker.md Wayfinding 小节（英文别名/`<root>` 分流/持久字段/重认领/再入/边界三条） | [x] | issue-tracker.md :22 标题「（Wayfinding operations）」；`<root>` 条件分流 :26；6 bullet 改 `<root>` :28-33；map 持久字段 :35-44；stale claim 重认领 :46-48；map 再入 :50-52；边界声明三条 :54-58 | PASS |
| 3.2 CLAUDE.md 双锚制 | [x] | 块内 Agent skills（Issue tracker 行补锚句）:150；块外结构性第二锚 :80-81「roadmap 类 wayfinding 落 openspec/roadmaps/{name}/footage/（长讨论考古层；三件套不引用）」 | PASS |
| 4.1 wayfinding 最小实测（真实调用起步/六操作+中断恢复/基线零增量/结果记归档材料） | [x] | impl-notes.md §4.1（演练 effort=drill-docs-site，从真实 /sdflow-roadmap 起步；判档表 9 行含 chart/claim/resolve/frontier/中断恢复；基线零增量；proposal 假设 1 消解 PASS） | PASS |
| 5.1 wco 包迁移 | [ ] | 受控延后：Q-C 拍板前置②「首个新流程 roadmap 已走通端到端」未满足；排期 T129；impl-notes §5.1-5.3 记前置核验 + 处置 | PASS（受控延后/deferred） |
| 5.2 mlh 包迁移 | [ ] | 同 5.1；impl-notes §5.1-5.3 | PASS（受控延后/deferred） |
| 5.3 两包迁移后总检 maintain_scan | [ ] | 同 5.1；impl-notes §5.1-5.3 | PASS（受控延后/deferred） |
| 6.1 全仓「四件套→三件套」+ :79 段 footage 锚句 + spec-workflow 零改动 | [x] | README.md:23 三件套直写不经 change 壳；CLAUDE.md:80-81 footage 锚句；docs/sdflow-fable5/01:153（三件套直写+分档 review）、02:205（4.6 节全段重写）；impl-notes §6.1 全仓 grep 156 命中七档处置；`git diff --stat openspec/specs/spec-workflow/spec.md` 为空 | PASS |
| 6.2 dev setup + 双宿主装载核验 | [x] | readlink ~/.claude/skills/sdflow-roadmap 与 ~/.codex/skills/sdflow-roadmap 均指向本仓；references/ 5 文件无孤儿；impl-notes §6.2 双宿主 wayfinder：claude 侧在场、codex 侧缺——与 SKILL「宿主中立探测」措辞一致 | PASS |

---

## 二、spec R1-R7 Requirement 逐条核对

| 需求 | MUST 行为锚点 | 判定 |
|---|---|---|
| **R1 三件套直写产出** | 直写 openspec/roadmaps/{name}/（SKILL 规则 1 :56-60、规则 4 :75-79）；MUST NOT 经 change 壳（grep `plan-` 流程空）；MUST NOT 产 requirements.md（默认路径 :102）；存量四件套兼容 :92-98；逃生舱 :100-102；生命周期 create/continue/replan MUST NOT 静默覆盖 :104-116 | PASS |
| **R2 design 伸缩头部章** | design-template「需求与目标态」章不占 `## N.` 序列 :19-25（正文起 `## 1.` :86）；工作流型痛点/目标态判据/验收门槛/Non-Goals 必填；产品型追加受众/功能取舍 :63-77；SR-13 探索型具名占位兜底 :24,:37 | PASS |
| **R3 讨论层分档路由** | 双判据不依赖轮数预估 SKILL :144；起手显性信号→wayfinder :156；事中触发升级双来源 :157；destination=三件套定稿 :219；无雾自降级+要点不清零+未持久化预检 :161；office-hours 第三分支 :173-181；宿主中立探测+preflight :163-167 | PASS |
| **R4 footage 落盘与引用边界** | 落盘 footage/map.md + footage/issues/ :206-207；命名权先定字面量 :212-220；map 持久字段续跑派生 :222-229；map 再入不覆写钉死一种 :239-245；三件套 MUST NOT 引用 footage/memo 规则 3 :68-73；tracker doc 分流+重认领+边界三条 issue-tracker.md :26-58；误落默认根票不被 triage 误吞 :58 | PASS |
| **R5 review 按野心分档** | 默认 plan-eng-review / 野心信号 autoplan :284-286；整体 plan 调用契约含主入口 roadmap.md :287-293；跳过仅人类授权记 review-waived :295-300；显式覆盖记偏离理由 :302-304；依赖失败留「未审待恢复」MUST NOT 静默 :306-308；每 issue 采纳/拒绝/延后 :310-318 | PASS |
| **R6 收尾 checklist 软门** | 五项 SKILL :346-354（①Review 处置无遗留+缺失视不通过 ②最小引用图+报行号 ③考古层未被引用 ④wayfinder 闭环 frontier 空/显式放弃 ⑤CONTEXT-adr 逐条对照标 superseded）；任一不通过 MUST NOT 静默跳过 :344；软提示纳入版本控制 :356；基线记录支撑⑤ :169 | PASS |
| **R7 roadmap.md 近细远雾** | 近期 1-2 阶段五节+选择理由必写 :324；远期仅目标句+雾区备注写明缺 X 信息 :326 MUST NOT 预写子任务/验收；长周期依赖例外提前写前置节 :330；frontier 补细+野心信号重判分档 :334；前序放弃视为已处置 :338；模板远期骨架同步 roadmap-template :117-146 | PASS |

---

## 三、缺口清单

### 核心缺口（R1-R7 MUST 行为缺失）

无。

### Minor 缺口

| # | 描述 | 锚点 | 处置建议 |
|---|---|---|---|
| M-1 | task-log 模板「下一步」示例用 `implement-<roadmap-name>-phase-1`，与 SKILL.md:80/380 及 roadmap-template.md:171 明令的命名 MUST 用 `-p<N>`（非 `-phase-N`）冲突——该示例教用户错误命名，会导致 sdflow-done 回填解析器 `PREFIX_RE` 命中失败（`NO_ASSOCIATION`） | references/task-log-template.md:96 vs SKILL.md:380 / roadmap-template.md:171 | 建议改为 `-p1`。非 R1-R7 核心，不阻塞发布；可 fold 进本 change 收尾或独立小改 |

### 受控延后（deferred，非缺口）

| 项 | 依据 | 排期锚 |
|---|---|---|
| tasks 5.1（wco 迁移）/ 5.2（mlh 迁移）/ 5.3（总检 maintain_scan） | Q-C 拍板前置②「首个新流程 roadmap 已走通端到端」未满足——新流程本 change 才落地，尚无真实 roadmap 走通端到端；4.1 演练为 wayfinding 操作实测非完整 roadmap。impl-notes §5.1-5.3 记前置核验 + 处置 | T129（openspec/issues/todolist/2026-07-todolist.md:137，显式挂 rebuild-sdflow-roadmap-v2；触发条件 = 首个新流程 roadmap SHIPPED 且目标包无在飞 change） |

> 另 impl-notes 附录登记 T130（ff-generation-constraints.md:43 术语同步）、T131（workflow.md 宿主中立探测口径同步）——均属 assets/workflow 权威源，本 change Compliance 声明零 assets 改动故未扫，已 defer 至 todolist（:138-139）。非本 change 缺口。

---

PASS —— R1-R7 七条 MUST 行为逐条在场且锚点齐备；tasks 12 项落地、3 项受控延后已排期 T129；spec-workflow/spec.md 零改动；双宿主 symlink 即时生效。唯一 Minor（M-1 命名口径不一致）不阻塞发布。

> M-1 后记（2026-07-11，verify 后收尾 fold 修复）：task-log-template.md:96 `-phase-1` 示例已改 `-p1` 并附契约句——Minor 清零。
