# spec-workflow Specification (delta)

> 本 delta = `minimize-repo-footprint`，把 `spec-workflow` 既有的**部署下发**规范从「整 bundle 复制进消费仓」改为「按内容性质分层 + 规则全局解析」。
> 决策真相源 = [`adr/0003`](../../../adr/0003-deploy-footprint-global-rules-minimal-repo-copy.md)（分层 + explore 2026-07-03「落地设计骨架」节）+ [`adr/0006`](../../../adr/0006-execution-model-baseline-fleet-anchored.md)（机队锚定 → resolver 脚本化）+ 本 change [design.md](../../design.md)。
> **MODIFIED** 复述既有「workflow bundle 改在权威源、经部署下发」的**完整新版**（"改在权威源"不变，"消费仓全量副本"改为"分层 + resolver 解析"）。

## MODIFIED Requirements

### Requirement: workflow bundle 改在权威源、经部署下发

workflow bundle（`workflow/*.md` / `trigger-catalog.md` / `spec-checklists/` / `code-checklists/` / review UI / hooks / checkpoint 脚本）与自制 skill 的改动 MUST 在权威源（laodao-skills 的 bundle 公共家与 skill 目录）进行，MUST NOT 只改消费仓副本。部署 SHALL **按内容性质分层**，而非整 bundle 复制：

- **规则**（`workflow/*.md` + `spec-checklists/` + `code-checklists/`）MUST **不再复制进消费仓**，改由 skills 从全局 canonical bundle 解析（见「规则解析 resolver」需求）。
- **review UI 机械**（`tools/` + `serve.sh` + `review.html`）SHALL 仍复制进消费仓 `openspec/`（服务器根=openspec/ 约束逼留，尽量少）。
- **`checkpoint-commit.sh`** MUST 全局安装到 agent 中立的 canonical 根 `~/.sdflow/hack/`（**非** `~/.claude/hooks`——它是跨-agent bash 工具、非 Claude 事件 hook）、不再进消费仓 `hack/`。
- **`config.yaml` / `changes/` / `specs/`** 天然属仓，仍仓内。

消费仓的规则副本 SHALL 经 `opsx-project-init update` 采纳最新（改后 update 对规则改为"停复制 + 陈旧遮蔽告警"，见「迁移」需求），MUST NOT 直接编辑部署副本。

#### Scenario: 修改 workflow 规则
- **WHEN** 需要修改 workflow.md
- **THEN** 改 laodao-skills 权威源 `opsx-project-init/assets/workflow/workflow.md`（不提根，仍是唯一权威源），消费仓经全局 canonical 自动跟随 released HEAD，不直接编辑消费仓副本

#### Scenario: 新 init 的消费仓不含规则副本
- **WHEN** 对一个新项目跑 `opsx-project-init init`
- **THEN** 消费仓 `openspec/workflow/` 只含 `tools/`（≈5 文件），规则文件数 = 0；`checkpoint-commit.sh` 全局安装、不进仓 `hack/`

## ADDED Requirements

### Requirement: 规则全局解析 resolver（本地优先 → 全局兜底 → 显式降级）

skills（spec-review / impl-review / opsx-done / recorders / opsx-ship）读取 workflow 规则 MUST 走统一三步 resolver：① 仓内**有规则文件本体**（`workflow.md` / `spec-checklists/` / `code-checklists/`）→ 用本地；② 否则 → 全局 canonical bundle；③ 全局也缺 → **显式降级**通用评审并告警，MUST NOT 静默当"无此层"。步①的存在判据 MUST 查**规则文件本体**、MUST NOT 查 `openspec/workflow/` 目录（`tools/` 使该目录在每个仓恒存在，查目录会令每个消费仓误命中本地 pin）。步②的 canonical 解析 MUST 平台无关回落：先试 `~/.sdflow/workflow/`（Unix 软链目录，透明），否则读 `~/.sdflow/workflow-path`（Windows 指针文件）取 bundle 路径。步③的"显式降级 + 告警"即 CONTEXT 术语『反静默守卫』的缺失面（见 `adr/0003`）。

〔model-baseline-amendment / `adr/0006`〕上述三步链 MUST 由确定性脚本 **`~/.sdflow/hack/resolve-workflow.sh`** 实现（stdout = 规则根路径；全局缺失 → 非零退出 + stderr 固定告警文案）。skills MUST 通过调用该脚本解析规则路径，MUST NOT 把三步链作为指令文本交由执行模型逐步照做（执行机队 = opus/sonnet/gpt-5.5 机队锚定，prose 协议在弱档模型上的失效形态 = 静默跳步）；调用方 MUST NOT 静默吞脚本非零退出码。

〔spec-review-amendment〕契约补强：步① 判据粒度 MUST 为 **any-of**（三顶层单元任一存在即判本地 pin），部分残留时 MUST 输出专门告警（提示补齐或删净），MUST NOT 隐式选择 any/all 语义；脚本 MUST 支持 `--root <仓根>`（缺省 `git rev-parse --show-toplevel`）与 `${SDFLOW_HOME:-$HOME/.sdflow}` 环境覆盖（测试隔离）；步② 命中后 MUST 做最小健全性检查（workflow.md 非空 + 三顶层单元存在，不过检按缺失处理）；调用方 MUST 先以 `[ -x ]` 判脚本自身存在——脚本缺失（未跑 setup）与步③ bundle 缺失是**两个不同告警**，MUST NOT 混同。

#### Scenario: 迁移期部分残留判 pin 且告警
- **WHEN** 某消费仓 `openspec/workflow/` 只残留 `spec-checklists/`（`workflow.md`、`code-checklists/` 已删）
- **THEN** resolver 按 any-of 判本地 pin（stdout=本地路径），同时 stderr 输出部分残留专门告警（补齐或删净）；MUST NOT 静默混合解析、MUST NOT 静默落全局

#### Scenario: 消费仓无本地规则副本走全局
- **WHEN** 一个消费仓 `openspec/workflow/` 只有 `tools/`、无规则文件，skill 要读 workflow.md
- **THEN** resolver 步① 未命中（有 tools/ 目录但无规则文件）→ 落步② 从全局 canonical bundle 解析，跟随 released HEAD

#### Scenario: toolkit 源仓与显式 pin 命中本地
- **WHEN** toolkit 源仓（自身有 `openspec/workflow/` 规则 dogfood 副本）或某消费仓显式保留了本地规则副本，skill 要读规则
- **THEN** resolver 步① 命中本地副本（无需任何"我是源仓"config flag——本地副本存在即声明），源仓 dogfood 吃在用端而非未发布编辑

#### Scenario: 全局缺失显式降级不静默
- **WHEN** 仓内无规则副本且全局 canonical bundle 也不可达
- **THEN** skill MUST 降级为通用评审并**显式告警**缺失，MUST NOT 静默当作"本项目无此评审层"

#### Scenario: canonical 解析平台回落
- **WHEN** skill 在 Windows 上解析全局 bundle（平台无软链）
- **THEN** 先试 `~/.sdflow/workflow/` 目录未果 → 回落读 `~/.sdflow/workflow-path` 指针取 bundle 路径；Unix 上则 `~/.sdflow/workflow/` 软链目录直接命中（透明）；平台判断发生在 `resolve-workflow.sh` 内，skill 不判平台

#### Scenario: resolver 由脚本执行而非模型 prose
- **WHEN** 任一 skill 在任一执行模型（opus / sonnet / gpt-5.5 等）上需要解析规则路径
- **THEN** 它调用 `~/.sdflow/hack/resolve-workflow.sh` 并使用其 stdout 路径；脚本非零退出时 skill 显式降级并转发脚本告警文案，不自行在指令内重实现三步链

### Requirement: 存量消费仓迁移不自动删、陈旧遮蔽须告警

`opsx-project-init update` 对存量消费仓的规则副本 MUST 改为"停止复制"，MUST NOT 自动删除仓内既有规则文件（安全红线 + 免分辨源/消费仓 + 老仓平滑迁移）。当检测到仓内残留的旧规则文件**遮蔽**全局 canonical bundle 时，update MUST **显式告警**（说明它遮蔽全局且不再被刷新，删=跟全局 / 留=显式 pin），MUST NOT 静默让其陈旧。此告警即 CONTEXT 术语『反静默守卫』的**陈旧遮蔽**变体（元原则清单已补“悄悄用了旧的”，见 `adr/0003`）。

〔spec-review-amendment〕告警触发点 = **update 内联为主 + `opsx-maintain` 兜底扫描**（覆盖常年不跑 update 的仓）；检测范围 MUST 同时覆盖旧版仓内 `hack/checkpoint-commit.sh` **孤儿副本**（checkpoint 全局化后不再被任何机制刷新），并给对称提示（删=用全局 / 本地 workflow.md 副本仍引用它则勿删）。

#### Scenario: update 不删残留规则、给出遮蔽告警
- **WHEN** 一个 pre-change 的存量消费仓（已有 ≈28 规则副本）跑 `update`
- **THEN** update 只刷 `tools/`、保留旧规则文件不删，并告警"这些规则遮蔽全局且不再更新——删=跟全局最新 / 留=显式 pin"

#### Scenario: 留旧副本仍能跑（pin 逃生口）
- **WHEN** 用户读到告警后选择保留本地规则副本
- **THEN** 该仓 resolver 步① 继续命中本地副本、照旧能跑（即显式 pin 行为），不因 change 而丢功能
