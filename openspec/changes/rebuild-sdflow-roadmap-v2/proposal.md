# Proposal: rebuild-sdflow-roadmap-v2

## Why

sdflow-roadmap 现行五阶段流程的仪式成本与产出价值错配，且有实证：change 壳对纯文档产出近乎空转（两个真实案例壳仅 52/55 行 vs 文档包 1333 行，归档零实施引用消费 requirements.md）；四件套重复面导致一次收口更新需同步 4 处（wco task-log 自证），漂移已实发（mlh-p2 code-review F8）；讨论阶段是最脆弱环节（memo.md 补丁对抗 compaction，跨 session 即断）；roadmap.md 远期阶段全写五节，中途被目标态复核推翻（adr/0010 复核实例）。同时 2026-07-10 探索会已拍板引入 Matt Pocock wayfinder 承载长讨论（盘面即状态的上位解），本次一并落地。

## What Changes

- **BREAKING（约定层）** 四件套 → **三件套**：requirements.md 并入 design.md（头部新增「需求与目标态」伸缩章：工作流/重构型写痛点/目标态判据/Non-Goals 三小节；产品型展开受众/功能取舍/NFR 可选段）。PRD 独立文件退役——需求契约职能已由 change 级 specs → `openspec/specs/` 链承载（requirements-template.md:59-60 自认「本文件只做功能清单级描述」）。
- **去 change 壳**：roadmap 文档包产出改为 recorder 式直写 `openspec/roadmaps/{name}/`（先例 = buglist/todolist 直写 `openspec/issues/`），不再要求 `plan-{topic}` 变更承载；「review 处置完才算完」软门从 archive 时刻移到 skill 收尾 checklist（两个世界均无机械门，载体不变仍在 task-log.md）。
- **讨论层分档改造**：短（单 session 收得住）→ `/opsx:explore` 不变；长（>30 轮/跨天/跨 clear）→ **wayfinder chart**（map destination = 三件套定稿），map+tickets 落 `openspec/roadmaps/{name}/footage/`；memo.md 从「长档强制」降为短档可选（footage 即结构化 footage，取代 memo 的考古职能）。
- **规则 3 扩展**：「正式文档不引用 memo」扩展为「三件套不引用 footage/ 内容」（footage 与 memo 同为讨论过程考古层）。
- **roadmap.md 近细远雾**：近期 1-2 阶段写满五节（前置/目标/子任务/验收/交付），远期阶段只写目标一句 + 雾区备注，到 frontier 才补细（fog-of-war 判据：能否现在精确表述）。
- **review 分档**：默认单跑 `/plan-eng-review`；有产品/商业野心才 `/autoplan` 三连审。
- **本仓消费约定**：`openspec/matt/issue-tracker.md` Wayfinding 小节加根目录条件分流（roadmap 类 effort → `openspec/roadmaps/{name}/footage/`，其余默认 `openspec/matt/<effort>/`）+ 标题补英文别名；CLAUDE.md Agent skills 托管块补 footage 约定一句作第二锚（防 setup-matt-pocock-skills 重跑覆盖回默认）。
- **存量迁移**：两个在飞 roadmap 包（workflow-cost-optimization、mechanical-layer-hardening）requirements 并入 design + 包内节级引用修补（各 6-7 处）；归档树按「归档不可变」不回改，合并文件头加考古注记。
- **文档同步**：仓内「四件套」表述（sdflow-roadmap/SKILL.md、5 份 references/ 模板导航块、CLAUDE.md、docs/sdflow-fable5/02-module-reference.md 等，grep 穷举）。

## Capabilities

### New Capabilities

- `roadmap-planning`: roadmap 规划工作流的规范性行为——三件套产出与直写位置、讨论层分档路由（explore/wayfinder）、footage 落盘与引用边界、review 分档、近细远雾阶段分层、收尾 checklist 软门。

### Modified Capabilities

（无——`spec-workflow` 只覆盖 change 三阶段评审规范，本次不触碰其需求；roadmap 规划此前无 capability 覆盖。）

## Success Metrics

| 指标 | 基准 → 目标 | 度量方式 |
|---|---|---|
| 产出仪式阶段数 | 5（讨论/开壳/产四件套/三连审/归档）→ 3（讨论/结晶直写/分档审+收尾 checklist） | SKILL.md 工作流章节数 + 下一次真实 roadmap 产出的实际步骤计数 |
| 同一结论的跨文件同步面 | 4 处（requirements §5 + design §2.2 + roadmap 概览 + roadmap 阶段节，wco task-log.md:40 实证）→ ≤2 处（design 单源 + roadmap 概览引用） | 三件套模板中标注的「单一源块」清单；下次收口更新实测同步处数 |
| 长讨论决策存活性 | 0（explore 结论 session 结束即蒸发，memo 靠自觉）→ 100% 落盘可续 | wayfinder map+tickets 在 footage/ 存在；下次长讨论跨 session 恢复实测 |

## Non-Goals（不在本次范围）

- **不改主流程 explore→ff→grill 的三段分流与 wayfinder→ff 衔接契约**（已记 T126/T127）。可证伪假设：roadmap 场景的 wayfinder 结晶目标是直写三件套、不经 opsx:ff，故衔接契约非本次依赖；若实施中发现 roadmap 结晶需要 ff 参与，此假设证伪、需先做 T126。
- **不实现 wayfinding 六操作的机械校验（lint/脚本）**。可证伪假设：模型按 tracker doc 散文约定执行落盘/状态词足够可靠；若首次实测出现落盘位置错误或状态词漂移，假设证伪 → 补 anchor_lint 式校验（届时另开 change）。
- **不动 sdflow-done 回填助手**（roadmap_writeback_draft.py）。可证伪假设：该脚本按 adr/0015 适配现状散文、只读 roadmap.md/task-log.md（roadmap_writeback_draft.py:349 已核），三件套合并不触其读点；若 design 阶段 grep 发现它读 requirements.md 或依赖被删节名，假设证伪 → scope 扩入本 change。
- **不做 recorder tracker 后端可插拔**（T123 池内待议）。
- **不深化产品型 PRD 展开段的具体形制**。可证伪假设：伸缩段骨架（受众/功能取舍/NFR 占位）足以覆盖首个产品型 roadmap 的起步需求；若首个产品型 roadmap 实测骨架不够用，届时按实例补节。

## 需求优先级

- **P0**：三件套合并（SKILL.md + design-template 头部章 + 删 requirements-template）；去 change 壳 + 收尾 checklist；tracker doc footage 分流 + CLAUDE.md 第二锚。
- **P1**：讨论层分档（wayfinder chart 接入 + memo 降级）；roadmap 近细远雾模板注释；review 分档措辞。
- **P2**：存量两包迁移；全仓「四件套」表述同步。

## 假设（失效影响）

| 假设 | 失效影响 |
|---|---|
| wayfinder 六操作（map/child/blocking/frontier/claim/resolve）在本仓 local-markdown tracker 上真实可跑（未实测，仅约定核读） | 长档讨论路由不可用，退回 explore+memo 现状；不阻塞其余交付 |
| setup-matt-pocock-skills 重跑的人在环确认 + CLAUDE.md 第二锚足以防 footage 约定被种子模板覆盖 | 约定被覆盖回默认 → wayfinder 落盘走 `openspec/matt/`，footage 分流失效，需手工恢复小节 |
| plan-eng-review 单审足以守工作流/重构型 roadmap 质量（autoplan 三连审仅产品野心场景需要） | 单审漏产品盲区 → 由 roadmap 消费期（实施 change 的 spec-review）兜底暴露，成本后移 |

## 开放问题

| 问题 | 负责人 / 截止 |
|---|---|
| 「roadmap 类 effort」的判别提示语在 tracker doc 里的最终措辞（隶属声明由谁写：sdflow-roadmap 发起时登记 vs 人工指认） | 设计门前，design.md 给出推荐 |
| 产品型伸缩段保留哪些 NFR 小节（性能/安全/成本全保 vs 精简） | 首个产品型 roadmap 出现时按实例定（本次仅留占位注释） |

## Impact

- **改**：`sdflow-roadmap/SKILL.md`（主体重写）；`sdflow-roadmap/references/design-template.md`、`roadmap-template.md`、`task-log-template.md`、`memo-template.md`（导航块与注释）；`openspec/matt/issue-tracker.md`；`CLAUDE.md`（Agent skills 托管块一句 + 「四件套」表述）；`openspec/roadmaps/{workflow-cost-optimization,mechanical-layer-hardening}/{design.md,roadmap.md}`（存量合并与引用修补）；`docs/sdflow-fable5/02-module-reference.md` 等 docs 表述。
- **删**：`sdflow-roadmap/references/requirements-template.md`；存量两包的 `requirements.md`（内容并入各自 design.md）。
- **依赖**：新增对 matt 套件（wayfinder → grilling/domain-modeling）的跨 skill 运行时依赖——失败模式与降级见 design.md（D-4）。
- **脚本零波及**：无 `sdflow-roadmap/scripts/`；`roadmap_writeback_draft.py` 只读 roadmap.md/task-log.md（已核，见 Non-Goals 假设 3）。技术栈 TG-01/02/03 均不命中（纯 Markdown，无领域清单选用）。

## Compliance（合规声明）

- **adr/0015**（回填助手：判断留人，MUST NOT 强制 roadmap 机读化/存量迁移）：遵守——三件套合并保持散文格式、不新增机器锚、不做机读化迁移；存量迁移仅为文档合并（requirements 并入 design），非 0015 禁止的「机读化迁移」。
- **adr/0002**（gstack 边界：复用输出不改内部）：遵守——review 分档仅改变调用哪个 gstack skill（plan-eng-review / autoplan）的推荐，不触其内部。
- **adr/0003**（部署足迹：全局规则最小仓内副本）：遵守——本次只改 skill 本体与仓内消费约定（openspec/matt/），不动 assets/workflow 规则 bundle。
- **adr/0005**（dev/runtime checkout 分治）：遵守——tasks 含「dev checkout 跑 setup.sh 后实测」步。
- **敏感数据/信任边界（TG-17）**：不适用（N/A）——纯文档流程变更。
