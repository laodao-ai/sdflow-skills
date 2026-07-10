# roadmap-planning Specification (Delta)

## ADDED Requirements

### Requirement: 三件套直写产出

roadmap 规划工作流 SHALL 将三件套（design.md / roadmap.md / task-log.md）直接写入 `openspec/roadmaps/{kebab-case-name}/`，MUST NOT 通过 OpenSpec 变更承载产出过程，MUST NOT 产出独立的 requirements.md 文件。

#### Scenario: 产出直写目标目录

- **WHEN** sdflow-roadmap 完成讨论并进入结晶阶段
- **THEN** 三件套文件直接创建于 `openspec/roadmaps/{name}/`，全程不执行 `openspec new change`，工作区不出现 `plan-{name}` 变更目录

#### Scenario: 需求内容不落独立文件

- **WHEN** 结晶阶段需要记录痛点、目标态判据或 Non-Goals
- **THEN** 这些内容写入 design.md 的「需求与目标态」头部章，目录中不存在 requirements.md

### Requirement: design.md 需求与目标态伸缩头部章

design.md SHALL 以「需求与目标态」章开头。工作流/重构型项目该章 SHALL 至少包含痛点清单、目标态判据、Non-Goals 三个小节；产品型项目 SHALL 追加受众与功能取舍小节（NFR 小节可选）。Non-Goals 中每条排除 SHALL 附可证伪假设，MUST NOT 写空泛的「超出范围」。

#### Scenario: 工作流型项目的头部章

- **WHEN** 为技术重构 / 内部工具类项目生成 design.md
- **THEN** 文件首章为「需求与目标态」，含痛点清单、目标态判据、Non-Goals 三小节，且每条 Non-Goal 带失效条件描述

#### Scenario: 产品型项目的头部章

- **WHEN** 为含外部用户 / 商业目标的项目生成 design.md
- **THEN** 「需求与目标态」章在三小节之外追加受众、功能取舍（做/不做）小节

### Requirement: 讨论层按规模分档路由

规划工作流 SHALL 按讨论规模路由讨论工具：单 session 可收敛的讨论用 `/opsx:explore`；预估超出单 session（>30 轮、跨天、或跨上下文重置）的讨论 SHALL 用 wayfinder chart 模式铺图，map 的 destination SHALL 表述为「三件套定稿」。wayfinder 铺图判定无雾（单 session 装得下）时 SHALL 退回 explore 路径，MUST NOT 为无雾讨论维持 map。

#### Scenario: 长讨论走 wayfinder

- **WHEN** 启动检查判定讨论规模为长档（预估 >30 轮或需跨天）
- **THEN** 以 wayfinder chart 铺图，产生 map.md 与讨论票，逐票决议后进入结晶

#### Scenario: 无雾自降级

- **WHEN** wayfinder chart 的广度 grill 未扫出雾区
- **THEN** 不建 map，退回 explore 单 session 讨论后直接结晶

#### Scenario: 跨 session 恢复

- **WHEN** 长档讨论经历上下文压缩或会话中断后重启
- **THEN** 新 session 从 map 的 Decisions-so-far 与 open 票恢复讨论进度，无需人工复述已决内容

### Requirement: footage 落盘位置与引用边界

roadmap 类 effort 的 wayfinder map 与讨论票 SHALL 落盘于 `openspec/roadmaps/{name}/footage/`（map 为 `footage/map.md`，票为 `footage/issues/<NN>-<slug>.md`）。三件套 MUST NOT 引用 footage/ 下任何内容（含旧 memo 形态）；footage 中有价值的结论 SHALL 精炼后写入三件套。

#### Scenario: wayfinder 按约定落盘

- **WHEN** wayfinder 为某 roadmap effort 创建 map 或票
- **THEN** 文件落在该 roadmap 的 `footage/` 子目录下，而非 `openspec/matt/<effort>/`

#### Scenario: 三件套引用检查

- **WHEN** 结晶阶段写三件套时需要引用讨论结论
- **THEN** 结论以精炼后的正文形式出现在三件套中，三件套全文不出现指向 `footage/` 的链接或「详见 footage」类表述

### Requirement: review 按项目野心分档

三件套完成后 SHALL 执行内容质量 review：默认单跑 `/plan-eng-review`；项目含产品/商业野心（外部用户、变现、获客类信号）时 SHALL 跑 `/autoplan` 三连审。跳过 review SHALL 在 task-log.md 留「未做 review，风险自担」痕迹。review 产出的每条 issue SHALL 在 task-log.md「Review 处置」小节标注 采纳/拒绝/延后 之一且附理由。

#### Scenario: 工作流型默认单审

- **WHEN** 技术重构类 roadmap 三件套完成且无产品野心信号
- **THEN** 触发 `/plan-eng-review` 单审，不强制 CEO/design 审

#### Scenario: 跳过 review 必留痕

- **WHEN** 作者决定跳过 review
- **THEN** task-log.md 存在「未做 review，风险自担」条目，收尾 checklist 方可通过

### Requirement: 收尾 checklist 软门

规划工作流收尾 SHALL 执行 checklist 确认：task-log.md「Review 处置」小节不存在未处置条目、三件套相互引用完整、footage（如有）无被三件套引用。checklist 任一项不通过 SHALL 提示补齐后再收尾，MUST NOT 静默跳过。

#### Scenario: 有未处置 review 条目

- **WHEN** 收尾时「Review 处置」小节存在无状态标注的条目
- **THEN** 收尾暂停并列出未处置条目，补齐处置状态后方可完成

### Requirement: roadmap.md 近细远雾分层

roadmap.md SHALL 只对近期 1-2 个阶段写满五节（前置条件/目标/子任务/验收标准/交付物）；更远阶段 SHALL 只写阶段目标一句与雾区备注，MUST NOT 预写子任务分解与验收细节。远期阶段 SHALL 在其成为下一个待实施阶段时补全五节。

#### Scenario: 生成时远期阶段形态

- **WHEN** 结晶阶段生成含 4 个以上阶段的 roadmap.md
- **THEN** 阶段 1-2 含完整五节，阶段 3 及以后仅含目标句与「待 frontier 到达后细化」备注

#### Scenario: frontier 推进时补细

- **WHEN** 某远期阶段的前序阶段全部交付、该阶段进入待实施
- **THEN** 该阶段补全五节（可经一次短讨论），补全动作记入 task-log.md
