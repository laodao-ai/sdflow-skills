# add-sdflow-spec

## Why

阶段一目前由三个分离入口拼接（opsx:explore 想事 → opsx:ff 生成 → grill-with-docs 拷问），存在三个实证过的结构性缺陷：①grill 只能人手动触发、极易静默跳过（memory: grill-not-skippable），跳过即把未拷问的设计送进设计审；②拷问发生在四件套成文**之后**，每轮命中都要回改四份文档，且草稿锚定效应让拷问退化为「框架内找茬」（dedupe-issues 实证：候选表建在被证伪 premise 上活过了成文）；③全程主 session 亲做，文件 dump 灌满上下文、四件套按主 session 档位输出价计费——强档模型（Fable 5/Opus 5）的判断力被大量花在机械活上。三个入口中两个是 openspec CLI 生成物、一个是仓外第三方集合（Matt Pocock skills，`~/.agents/skills`，非 git 管理、更新即覆盖），流程规范无法焊进它们。

## What Changes

- **新增顶层 skill `sdflow-spec`**：单一入口「澄清 → 拷问 → 生成」管线，替代阶段一的三入口**使用路径**（三个原 skill 保留不动）。主 session 只做判断（澄清对话、对抗拷问、决策纪要、终审），检索/调研与四件套生成外派子代理。
- **新增 agent 定义文件** `sdflow-spec/agents/`：`sdflow-researcher`（检索供证，effort low、只读工具白名单）、`sdflow-spec-writer`（四件套生成，effort medium）；`model: inherit`，调用时经 `resolve-models.sh` 传档位变量。
- **`setup.sh` 扩展**：agents 定义铺设到 `~/.claude/agents/`（沿用 symlink/copy 机制）。
- **`sync_principles.py` 投放面扩展**：agent 定义正文纳入四条通则托管块 + `hack/tests/` 守卫同步更新。
- **本仓阶段一规范双通道改写** [grill-amendment]：①归属错误修正（「grill-with-docs 来自 superpowers 插件」实为 Matt Pocock skills 集合）改真相源 `sdflow-init/assets/snippets/claude-section.md` + 经托管机制刷新本仓区块（纯事实纠错，下游随 update 自然获得）；②`sdflow-spec` 使用路径与出口序列（`/clear` → 换档 → `/sdflow-spec-review`）写入本仓 CLAUDE.md/AGENTS.md **非托管区**；托管块「ff 之后是 grill」保留（管旧路径，三原 skill 并存），下游推广另 change。
- **README skills 列表**更新 + 重跑 `setup.sh`。

## Capabilities

### New Capabilities
- `spec-authoring`: 阶段一 spec 生产管线——澄清/拷问/生成三相位的行为契约、判断与机械的外派分工线、决策纪要承重件（/clear 无损）、错误降级与 Codex 宿主降级、出口衔接序列。

### Modified Capabilities

（无——现有 specs 的 requirement 层不含阶段一入口约定；`spec-workflow` 只在场景措辞中引用 grill 上下文，其需求不变。）

## Success Metrics

- **四件套生成环节输出成本** — 基准：全部按主 session 档位输出价（Fable $50/M、Opus $25/M）→ 目标：生成环节按 mid 档价（$15/M，降 ≥40%）— 度量：dogfood change 中生成子代理的 usage 归属；粗粒度用 `/usage` 前后对比并如实标注精度。
- **拷问覆盖率** [grill-amendment] — 基准：grill 人工触发、可静默跳过（已实证发生）→ 目标：拷问为管线内建默认路径（跳过须主动偏离指令；结构性改善而非机械保证——指令层约束由执行方自报，按诚实边界纪律不冒充机械门）— 度量（机械审计信号）：`decision-memo.md` 存在 + design.md 决策记录节含「砍掉的候选 + 理由」条目（可 grep 抽查）；若 dogfood 发现跳过实际发生，另 change 补机械门禁。
- **阶段二冷启动无损率** — 基准：部分决策 why 滞留对话上下文 → 目标：`/clear` 后 spec-review 所需 why 100% 可从落盘产物获得 — 度量：dogfood change 的 spec-review 报告中「上下文缺失/需回问」类 finding = 0。

## 需求优先级〔TG-19〕

- **P0**：skill 本体（三相位管线 SKILL.md）· agents 定义 × 2 · setup.sh 铺设 · sync_principles 投放面纳入（防漂移，与 skill 同 change 落地不可拆）
- **P1**：本仓 CLAUDE.md/AGENTS.md 阶段一规范改写 · grill-with-docs 归属错误修正 · README 列表
- **P2**：checkpoint 阶段锚（补 retro 数据阶段一无独立打点的缺口）

## 假设〔TG-22〕

- **agent 定义 `agentType` 派发 + `effort` frontmatter 在 dispatch 中生效**——依据为 claude-security 官方插件 7 个实例的静态核验（docs/subagent-definitions-plan.md §4.6），本仓未实测过派发链路。失效影响：降级为 prompt 内联通则路径（SKILL.md 已内置 fallback），收益打折但管线不阻塞。
- **省 token 量级估算（~30-40% vs 强档全包）未实测**——基于官方定价推算。失效影响：成本目标不达，但质量收益（拷问前置/上下文卫生）独立成立。
- **openspec CLI `instructions` 幂等只读、载荷 3.5-6KB**——已实测（本 change 调研），非假设，列此为证据锚。

## 开放问题〔TG-21〕

- **token 实测基线**：首个 dogfood change 跑完后由人比对 `/usage`（负责人：用户；截止：本 change merge 后首个新 change）。
- **agent 定义的分发层级**：v1 由 setup.sh 装 `~/.claude/agents/`（全局）；是否纳入 `sdflow-init` 铺设物随 bundle 分发，待 dogfood 验证后另 change 决策。
- **bundle workflow.md 阶段一规范的下游推广**：本 change 只改本仓自身流程约定（dogfood 先行）；`sdflow-init/assets/` 源与下游推广另 change。

## 成本估算〔TG-24〕

单次阶段一运行（40 轮对话、四件套 ~65KB 量级，API 价折算）：强档（Fable）全包 ~$15-20；本方案 Fable 主 session + mid 档外派 ~$10-13；Opus 主 session + 外派 ~$5-6（≈或低于现状 Opus 全包 $6-8）。主 session 档位由人按 change 价值选择，skill 不写死模型。

## Non-Goals

- **不改 openspec CLI 与四件套 schema**——可证伪假设：现有 `instructions --json` 载荷足以驱动生成子代理产出合格产物（已实测载荷 3.5-6KB；若 dogfood 中产物质量不合格且归因于载荷缺失，此假设被证伪，需另 change 补充生成上下文）。
- **不动阶段二/三（spec-review / ship 链）**——可证伪假设：产/审错档纪律用出口提示承载即可，无须改 spec-review 本体（若 dogfood 中人反复忘记换档，此假设被证伪，需机械层承接）。
- **不删除/修改 opsx:explore、opsx:ff、grill-with-docs、grilling、domain-modeling**——可证伪假设：并存无触发面冲突（新 skill `disable-model-invocation: true` 仅人触发；若实际出现误触发抢占，假设被证伪）。
- **不做 Codex 宿主适配（agent 定义对应物）**——可证伪假设：Codex 下降级为主 session 亲做可接受，因阶段一在 Codex 宿主的运行频率低（若 Codex 阶段一成为常态用法，假设被证伪，需另 change）。
- **不做 per-子代理 token 归因度量**——可证伪假设：`/usage` 粗粒度前后对比足以验证成本方向（若数据无法区分方向性结论，假设被证伪，需补细粒度打点）。

## Impact

- **新增**：`sdflow-spec/SKILL.md`、`sdflow-spec/agents/{sdflow-researcher,sdflow-spec-writer}.md`
- **修改**：`setup.sh`（agents 铺设段）、`hack/sync_principles.py` + `hack/tests/test_sync_principles.py`（投放面 +2）、`sdflow-init/assets/snippets/claude-section.md`（仅归属修正）、`CLAUDE.md`/`AGENTS.md`（非托管区新增；托管块经刷新机制同步归属修正）、`README.md`
- **依赖**：openspec CLI ≥1.5（`new`/`status --json`/`instructions --json`，均已实测）；Claude Code agent 定义解析（`~/.claude/agents/`，带 prompt 内联 fallback）；`resolve-models.sh` 档位变量（既有）
- **技术栈标注**〔TG-01/02/03 判定〕：纯 Markdown 编排 + Python/Bash 构建脚本，不命中 backend/embedded/frontend 领域清单
- **不受影响**：阶段二/三编排器、openspec CLI 生成的官方 skills、`~/.agents/skills` 第三方集合

## Compliance

无涉敏感数据/信任边界变更（TG-17 不命中）。项目既有边界合规（adr/0005 dev-runtime checkout 纪律、通则托管单一源机制、host-adaptive-execution「skill 引用档位变量不内联模型名」）在 design.md 按 D-6 逐条声明。
