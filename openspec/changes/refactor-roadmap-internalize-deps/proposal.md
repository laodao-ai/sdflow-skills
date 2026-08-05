# Proposal: refactor-roadmap-internalize-deps

## Why

`sdflow-roadmap` 的讨论层押在五个外部依赖上（wayfinder / grilling / domain-modeling /
office-hours / matt tracker doc），每个都拖着宿主探测、降级路径、语义漂移告警的维护面——
Codex 宿主接地实测无 wayfinder，降级路径常驻生效，「长档持久化保护」对半数宿主是空头承诺。
sdflow-spec 已实证「内化拷问 + 纪要增量落盘」能用一个文件消除长档持久化的全部外部依赖。
本次将讨论层能力内化、整体结构对齐 sdflow-spec 三相位；matt 套件随之在本仓失去全部活消费方
（sdflow-implement 的 matt 引用均为出处注释，无运行时依赖），一并移除。

## What Changes

- **SKILL.md 重写为三相位结构**：A 澄清（gate-0 + 商业化信号检查）→ B 七维拷问（按信号裁剪，
  memo 增量落盘）→ C 生成三件套。原三分支讨论层路由（explore / wayfinder / office-hours）
  替换为三态路由：gate-0 过∧无商业化信号 → 直接生成；gate-0 过∧信号命中 → B 裁剪到维度①；
  gate-0 未过 → B 按信号七维裁剪。explore 移为上游可选步（想法未成形先 `opsx:explore`）。
- **删除 wayfinder 全部机械**：分支 B、footage 落盘节、map 再入、tracker doc preflight、
  共享真相源基线记录、收尾 checklist ④、陷阱 7。存量 footage 冻结为合法历史形态
  （续跑不报错、不强推迁移、不新增票、不要求闭环）。
- **office-hours 内化**：六问按 roadmap 场景裁剪进 B 拷问维度（Q1→维度①需求真实性、
  Q2→维度②现状、Q3 作维度①追问弹药、Q4→维度④最小首阶段、Phase 4→维度⑤路线对比、
  Phase 3→维度⑦前提质疑）；不吸收 Cross-Model Second Opinion / Builder Mode / Visual Design。
- **domain-modeling 内化**：B 相位术语澄清环节 + ADR/术语提议制（未经人确认不写入，
  与 sdflow-spec B.6/B.7 同构）。
- **B 相位落盘协议**：B 起手即定名、判 create/continue/replan（判定前移）、建
  `openspec/roadmaps/{name}/` + 草稿 memo.md；重入探测（memo 存在且未定稿 ⇒ 问人续/新开）；
  拷问中途放弃删包目录（continue/replan 场景只删本次新增）。
- **术语改名**：「结晶」→「生成」（相位名对齐 sdflow-spec）；「产品/商业野心信号」→
  「商业化信号」（词表不变）；「考古层」（roadmap 语境）→「历史存档」（DOC-1 语境的
  「考古层」是另一概念，不改）。「相位 A/B/C」保留。
- **收尾 checklist 五项 → 四项**：①②③ 保留（③ 覆盖 memo.md + 存量 footage/），④ 删除，
  ⑤ 简化为 memo 对账（提议制写入记录逐条对照终稿，废弃 git 基线 diff）。
- **BREAKING（仓内配置面）**：移除 `openspec/matt/` 目录 + CLAUDE.md / AGENTS.md 的 matt
  区块（Issue tracker / Triage labels / Domain docs）。
- **bundle 同步**：`ff-generation-constraints.md` 的 `wayfinder-resolved:` 前缀禁混用规则
  保留 + 加 legacy 标注；`workflow-history.md` 追加移除记录。
- **模板与文档**：memo-template.md 重写为 B 相位纪要模板；design/roadmap 模板改术语；
  long-flow-skill-paradigm.md 的 wayfinder 段改历史注记；`docs/external-dependencies.md`
  更新（删 wayfinder/grilling/domain-modeling 依赖节）；SKILL.md frontmatter description
  重写（触发面去 wayfinder）。
- **配套治理**：ADR 一条（讨论层内化与 matt 移除）+ CONTEXT.md 词条两处（footage 词条
  重写为「历史存档」、新增「商业化信号」）；T134 关 OBSOLETE（前提消解）。
- **review 层不动**：`/plan-eng-review` + `/autoplan` 外部依赖与降级路径原样保留。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `roadmap-planning`：①「讨论层按规模分档路由」Requirement 重写为三态路由（删 wayfinder /
  office-hours 分支与其全部 Scenario）；②「footage 落盘位置与引用边界」Requirement 重写为
  「历史存档与存量 footage 冻结」（引用禁令保留、产出机制删除）；③「收尾 checklist 软门」
  Requirement 由五项改四项（④ 删除、⑤ 简化为 memo 对账）；④「review 按项目野心分档」
  Requirement 改术语（商业化信号）、外部依赖契约不变；⑤ 新增「B 相位落盘与重入」Requirement
  （包目录时机 / memo 协议 / 重入探测 / 放弃清理）。

## Impact

- `sdflow-roadmap/SKILL.md`（635 行，主体重写）+ `references/` 5 个模板
- `openspec/specs/roadmap-planning/spec.md`（delta：4 ADDED / 3 MODIFIED / 3 REMOVED——
  路由与 footage 为机制替换、review 分档因 Requirement 名含旧术语，均以删+增承接）
- `openspec/matt/`（整目录删除）；CLAUDE.md / AGENTS.md（matt 区块删除、
  roadmaps 目录描述行去 footage）
- `sdflow-init/assets/workflow/ff-generation-constraints.md`、`workflow-history.md`
  （bundle 改动，改后按 dev checkout 纪律重跑 setup.sh 并推下游）
- `openspec/CONTEXT.md`（词条两处）、`openspec/adr/`（新增一条）、
  `openspec/issues/`（T134 处置）、`docs/external-dependencies.md`、
  `docs/drafts/roadmap-refactor-handoff.md`（实现后删除）
- 不涉及：服务/固件/前端（TG-01/02/03 均不命中）；review 层 skill 接口

## Success Metrics

- 重构后 `sdflow-roadmap/` 目录内 grep `wayfinder|office-hours|grilling|domain-modeling|matt`
  仅剩历史注记（存量兼容条款、long-flow-skill-paradigm 历史注记），无活跃调用路径。
- `openspec/matt/` 不存在；CLAUDE.md / AGENTS.md 无 matt 区块；全仓无 `openspec/matt` 活引用
  （docs/ 历史文档除外）。
- 全仓 `python3 -m pytest` 绿；`python3 hack/sync_principles.py --check` 绿
  （SKILL.md 重写保留 `sdflow:principles` 托管块）。
- `openspec validate refactor-roadmap-internalize-deps --strict --type change` 通过。
- 存量包续跑演练（`issues-triage-2026-08`）不报错、至多一行冻结提示。

## Non-Goals

- review 层内化或简化（D1 拍板保留外部依赖）。
- 「相位」「阶段」等既有结构词的全仓改名（「环节」候选如要做，另开 change）。
- 存量 roadmap 包结构迁移（T129 维持受控延后；存量 footage 只冻结不迁移）。
- `docs/workflow-skills/` 等 docs/ 历史文档追改（非规则源）。
- wayfinder / matt 套件在 `~/.claude/skills/` 的全局安装本体（其他项目可能在用，本仓只退订）。

## 需求优先级〔TG-19〕

- **P0**：SKILL.md 三相位重写（三态路由 + 七维拷问 + memo 落盘协议）+ roadmap-planning
  spec delta——不成对完成即出现 spec/实现矛盾。
- **P1**：matt 移除（目录 + CLAUDE/AGENTS 区块）+ 术语改名全消费面 + 模板重写 + bundle 标注
  ——与 P0 同 change 内完成，避免半改状态。
- **P2**：ADR + CONTEXT.md 词条 + T134 处置 + external-dependencies.md 更新 + handoff 清理
  ——治理收尾，全部在本 change 内做完，仅执行顺序靠后。

## 利益相关方与外部依赖〔TG-20〕

- **下游消费仓**：skill 经全局 symlink 即时生效（运行 checkout pull + setup.sh）；bundle
  改动需 `sdflow-init update` 推送。存量 wayfinder footage 由冻结条款兼容。
- **gstack review skills**（`/plan-eng-review`、`/autoplan`）：调用契约不变，零影响。
- **matt 套件**：本仓移除配置面；全局安装与其他项目使用不受影响。

## 假设〔TG-22〕

- **假设**：没有消费仓存在「进行中的 wayfinder 长档讨论」（半途 map 未收敛）。
  **失效影响**：该仓续跑时长档分支已不存在——按存量 footage 冻结条款处置，讨论要点从 map
  手工转录进 memo 继续；影响小、有明确兜底路径，不阻塞。

## Compliance

N/A（本仓无用户数据、敏感信息或合规约束涉及面）。
