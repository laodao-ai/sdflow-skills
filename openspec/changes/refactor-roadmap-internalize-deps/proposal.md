# Proposal: refactor-roadmap-internalize-deps

## Why

`sdflow-roadmap` 的讨论层押在五个外部依赖上（wayfinder / grilling / domain-modeling /
office-hours / matt tracker doc）。**两类性质不同，分开说**〔spec-review-amendment SR-31〕：

- **wayfinder / grilling / domain-modeling / matt tracker doc** —— 拖着宿主探测、降级路径、
  语义漂移告警的维护面。Codex 宿主接地实测**无**这三个 skill，降级路径常驻生效，
  「长档持久化保护」对半数宿主是空头承诺。
- **office-hours** —— **双宿主皆可用**（实测 `~/.codex/skills/gstack-office-hours` 存在），
  且现行 SKILL.md 的 office-hours 分支**没有任何宿主探测/降级逻辑**。
  它被内化的理由是**另一个**：结构对齐三相位 + 维护面精简（六问在 roadmap 场景本就要裁剪，
  裁剪后的执行体就是 B 相位的拷问维度，外置一个 skill 只多一层调用）。

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
  拷问中途放弃：create 场景先复述路径再删包目录，**continue/replan 场景不自动删、只记 task-log 一行**
  〔spec-review-amendment SR-5：「本次新增」在 append-only 的 memo 上无可执行归属判据〕。
- **术语改名**：「结晶」→「生成」（相位名对齐 sdflow-spec）；「产品/商业野心信号」→
  「商业化信号」（词表不变）；「考古层」（roadmap 语境）→「历史存档」（DOC-1 语境的
  「考古层」是另一概念，不改）。「相位 A/B/C」保留。
- **收尾 checklist 五项 → 四项**：①②③ 保留（③ 覆盖 memo.md + 存量 footage/），原 ④（wayfinder 闭环）删除，
  ⑤ 简化为 memo 对账并**收编为新的 ④**——含三件事：提议制写入记录逐条对照终稿（废弃 git 基线 diff，
  改用 memo 内的**版本锚**做归属核验〔SR-11〕）+ **未决项闭环**〔SR-4·设计门 Q2〕。
- **未决项清单**〔设计门 Q2 拍板〕：memo 增 `## 未决项` 小节，承接被删 wayfinder frontier 的**清单**职能
  （维度「显式延后」终态 + 拷问中冒出不解决的问题，各附再触发条件）；
  **不承接** `Blocked-by` 依赖图与 `claimed` 并发语义（单人场景不需要，如实声明）。
- **BREAKING（仓内配置面）**：移除 `openspec/matt/` 目录 + CLAUDE.md / AGENTS.md 的 matt
  区块（Issue tracker / Triage labels / Domain docs）。
- **bundle 同步**：`ff-generation-constraints.md` 的 `wayfinder-resolved:` 前缀禁混用规则
  保留 + 加 legacy 标注；`workflow-history.md` 追加移除记录。
- **模板与文档**：memo-template.md 重写为 B 相位纪要模板；design/roadmap 模板改术语；
  long-flow-skill-paradigm.md 的 wayfinder 段改历史注记；`docs/external-dependencies.md`
  更新（删 wayfinder/grilling/domain-modeling 依赖节）；SKILL.md frontmatter description
  重写（触发面去 wayfinder）。
- **配套治理**：ADR 一条（讨论层内化与 matt 移除）+ CONTEXT.md 词条**三处**〔spec-review-amendment
  SR-15：footage 词条重写为「历史存档」、新增「商业化信号」、**`ticket` 词条**里的
  「matt 套件中 wayfinder 的讨论 ticket…需限定词区分」改历史存档语境〕；
  T134 关 **`WONTDO`**〔SR-3：`OBSOLETE` 非合法状态码〕。
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
- `openspec/CONTEXT.md`（词条**三处**〔SR-15〕）、`openspec/adr/`（新增一条）、
  `sdflow-init/assets/workflow/config.template.yaml`（陈旧 wayfinder 引用订正〔SR-13〕）、
  `docs/sdflow-fable5/02-module-reference.md` §4.6（活文档，非豁免历史文档〔SR-16〕）、
  `openspec/issues/`（T134 处置）、`docs/external-dependencies.md`、
  `docs/drafts/roadmap-refactor-handoff.md`（实现后删除）
- 不涉及：服务/固件/前端（TG-01/02/03 均不命中）；review 层 skill 接口

## Success Metrics

- 重构后 `sdflow-roadmap/` 目录内 grep `wayfinder|office-hours|grilling|domain-modeling|matt`
  仅剩历史注记（存量兼容条款、long-flow-skill-paradigm 历史注记），无活跃调用路径。
- `openspec/matt/` 不存在；CLAUDE.md / AGENTS.md 无 matt 区块；全仓无 `openspec/matt` 活引用
  （docs/ 历史文档除外）。
- `/usr/bin/python3 -m pytest` **相对 merge-base 无新增失败**〔spec-review-amendment SR-18：
  baseline 已有 1 个先于本分支存在的无关红（`test_harden_sdflow_spec_followup_closure`），
  故不能写「全仓绿」〕；`python3 hack/sync_principles.py --check` 绿（SKILL.md 重写保留托管块）。
- `openspec validate refactor-roadmap-internalize-deps --strict --type change` 通过。
- **构造 fixture** 的 footage 冻结演练通过〔SR-4：本仓无任何 `footage/` 目录，
  原定演练对象 `issues-triage-2026-08` 只有一个 `roadmap.md`，是恒真锚〕；
  真实单文件包（`issues-triage-2026-08`）的缺件兼容演练通过。

> 🔴 **本节的诚实边界**〔spec-review-amendment SR-19〕：以上四条量的是「残留字符串清干净了 /
> 门禁绿 / 结构合法」，**都不检验规划器行为是否正确**。`sdflow-roadmap` 无 `scripts/`、无 `tests/`
> ⇒ 三态路由、七维裁剪、增量落盘、重入、放弃清理这些**本次真正的改动面没有任何自动化测试**。
> Success Metrics 全绿 **MUST NOT** 被读作「新流程可用」——那一层的唯一防线是终审人读 + **tasks 6.8 的场景核对清单**（三路由 × create/continue/replan ×
> 中断/放弃 的逐格矩阵）〔窄复核 NR-7：原文指向 `tasks 6.6`，而 6.6 是「保留」节逐句核对，
> 与场景矩阵无关——该清单当时**根本不存在**，现已补为 6.8〕。

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

- **下游消费仓**〔spec-review-amendment SR-14：原表述「bundle 改动需 `sdflow-init update` 推送」
  与实际机制不符，改写〕：skill 与 bundle 规则**走同一条通道**——运行 checkout `git pull` + `setup.sh`
  之后，`~/.sdflow/workflow/` 软链即指向新内容，消费仓经全局 canonical 解析立即拿到。
  `sdflow-init update` 在消费仓**默认只刷新 `tools/` 子树**（`init.py:213`），**不推送规则文件**。
  ⇒ 真正会滞后的是**持有本地 `openspec/workflow/` 规则副本（pin）的消费仓**：它遮蔽全局且
  `update` 不刷新，由既有「陈旧遮蔽」告警（`init.py:329`）提示，本 change 不新增机制。
  存量 wayfinder footage 由冻结条款兼容。
- **gstack review skills**（`/plan-eng-review`、`/autoplan`）：调用契约不变，零影响。
- **matt 套件**：本仓移除配置面；全局安装与其他项目使用不受影响。

## 假设〔TG-22〕

- **假设**：没有消费仓存在「进行中的 wayfinder 长档讨论」（半途 map 未收敛）。
  **失效影响**〔spec-review-amendment SR-20：原称「有明确兜底路径」，实为**无自动化兜底**，如实改写〕：
  该仓续跑时长档分支已不存在，走「包已存在 → continue」进 B 相位**从零拷问**——
  `footage/map.md` 里的历史讨论**对执行 agent 不可见**（spec 的冻结 Requirement 只说「不报错、不迁移」，
  没有任何一句要求 agent 去读 map 提炼要点）。
  ⇒ **靠操作者自己记得手工转录**，无工程化兜底。影响：一次重复讨论；不阻塞，但不该说成「有明确兜底路径」。
  **可选收紧**（未采纳，记此备查）：spec 补一条 Scenario——「包含 `footage/` 但无三件套 ⇒ continue 判定前
  SHALL 提示操作者是否先摘要 map 要点写入 memo」。

## Compliance

N/A（本仓无用户数据、敏感信息或合规约束涉及面）。
