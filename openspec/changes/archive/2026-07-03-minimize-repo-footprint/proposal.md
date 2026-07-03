# Proposal: minimize-repo-footprint

> 承 Phase A（`streamline-workflow-automation`，已归档）的 G6 复制模型修正派生。
> 决策真相源 = [`adr/0003`](../../adr/0003-deploy-footprint-global-rules-minimal-repo-copy.md)（含 explore「落地设计骨架」+ **grill-amendment 2026-07-03**）+ [`adr/0005`](../../adr/0005-dev-runtime-checkout-split.md)（dev/runtime checkout 分离）。本 change 的 design 引该 ADR，不复制其决策。

## Why

`opsx-project-init` 现把整个 workflow bundle（≈34 文件）复制进**每个**消费仓的 `openspec/workflow/`。这些规则文件**从不按仓定制**（定制只在 `config.yaml`），却在每个消费仓留一份可观副本——纯机械/纯规则的东西在每个仓重复堆积，且随全局 toolkit 演进会与源漂移（连 toolkit 源仓自己那份 dogfood 副本都会与 `assets/` 出现正常的 dev/release 时间差）。

## What Changes

把部署从「整 bundle 复制」改为**按内容性质分层**，消费仓只留「本身必须在仓里」的最小集：

| 类别 | 内容 | 现状 | 改后 · 消费仓 |
|---|---|---|---|
| 规则 | `workflow/*.md` + `spec-checklists/` + `code-checklists/`（≈28） | 全复制 | **0**（全局唯一，skills 解析） |
| UI 机械 | `tools/` + `serve.sh` + `review.html`（≈5） | 复制 | **5**（服务器根=openspec/ 逼留） |
| hack | `checkpoint-commit.sh`（1） | 复制进仓 hack/ | **0**（全局，同两个全局 hook） |
| 本体 | `config.yaml` / `changes/` / `specs/` | 仓内 | 仓内（天然属仓） |

- **解析 resolver**：skills 读规则改为「仓内有规则文件 → 用本地；否则 → 全局 canonical bundle；全局也缺 → 显式降级 + 告警」（三步链，见 design）。〔model-baseline-amendment / `adr/0006`〕三步链由**全局脚本 `~/.sdflow/hack/resolve-workflow.sh` 确定性执行**，SKILL.md 只调用——不写成模型逐步照做的 prose 协议（执行机队 = opus/sonnet/gpt-5.5，prose 协议在弱档模型上静默跳步）。
- **全局钉法**〔grill-amendment〕：**不提根**——bundle 留 `opsx-project-init/assets/`；`setup.sh` 建 canonical（Unix 软链 `~/.sdflow/workflow` / Windows 指针 `~/.sdflow/workflow-path`）藏住 assets/ 布局，skills 走"试目录→否则读指针"回落链解析，锚点 = 运行 checkout（`adr/0005`）。
- **checkpoint 全局化**〔grill-amendment〕：`checkpoint-commit.sh` 移到 agent 中立的 canonical 根 `~/.sdflow/hack/`（**非** `~/.claude/hooks`——它是跨-agent bash 工具、不是 Claude 事件 hook），顺带根治 `core.fileMode=false` exec 位丢失。
- **迁移**：`update` 停止复制规则、检测残留旧规则则**告警**（删=跟全局 / 留=pin），**绝不自动删**。

## Success Metrics

- 新 init 的消费仓 `openspec/workflow/` 只含 `tools/`（≈5 文件），规则文件数 = 0。
- skills（spec-review / impl-review；opsx-done / recorders 实扫无读点，opsx-ship 待其 change 落地后追加〔spec-review-amendment〕）在**无本地规则副本**的消费仓能正确解析全局规则并跑通——**验收锚点 = 5.7 激活验证的真实调用输出**，非"文本已改"；全局缺失时**显式降级 + 告警**（非静默）。
- toolkit 源仓自身 dogfood 不受影响（本地副本 local-first 命中，仍吃"在用端"而非未发布编辑）。
- 存量消费仓 `update` 后不丢功能：留旧副本照旧能跑、且收到"遮蔽全局"告警。

## Non-Goals

- **不做纯激进**（连 `tools/` 也全局、重写 `serve.sh` 弃 `python -m http.server`）——ADR 已评估，务实取"tools 留最小副本"。footprint 归零留未来。
- **不改按仓 pin 为默认**——明确接受"消费仓跟全局 HEAD"的代价；pin 仅作显式逃生口（留本地副本）。
- **不动归档 umbrella**（`streamline-workflow-automation`）；承其 G6 修正但不回改。
- **不重排/重命名 `config.yaml` 契约**、不动 `changes/` `specs/` 本体结构。
- **不提根**〔grill-amendment〕：bundle 留 `opsx-project-init/assets/`，canonical 间接层已解耦，提根买不到额外收益却要重写"唯一权威源"5 处约定。
- **不含"移无关 skill（≈17）"**〔grill-amendment〕：独立卫生 change，失败模式/验证方式与本 change 不同。
- **Windows bash 解释器依赖沿现状**〔spec-review-amendment〕：`~/.sdflow/hack/*.sh` 在 Windows 依赖 Git-Bash/WSL 执行，本 change 不解决；2.2 的"根治"仅指 git exec 位追踪丢失。

## Impact

- **代码**：`opsx-project-init/scripts/init.py`（`copy_bundle` 去规则、`copy_hack` 改全局装）、`setup.sh`（建 canonical 软链/指针 + 装 checkpoint 与 **resolve-workflow.sh** 到 `~/.sdflow/hack/`）、新增 `resolve-workflow.sh`（resolver 执行主体〔adr/0006〕）、各 skill SKILL.md 的规则读点（改**调 resolver 脚本**）、`workflow.md` line62 checkpoint 约定改指全局。〔grill-amendment:不提根，bundle 留 `assets/`〕
- **spec**：MODIFY 既有「workflow bundle 改在权威源、经部署下发」（下发模型变）；ADD「规则全局解析 resolver」。
- **测试**：`opsx-project-init/tests/`（init/checkpoint/hook 现有测试须跟部署模型改）。
- **已知代价**：消费仓失去按仓 pin 规则（跟全局 HEAD，规则一改即刻影响所有仓）——ADR 已拍板接受。

## Stakeholders & External Dependencies（TG-20）

- **外部影响方 = 所有消费仓**：本 change 改变它们与 toolkit 的耦合方式（从"显式 update 采纳"变"跟随全局 HEAD"）。存量消费仓通过 opt-in 迁移平滑过渡，不强制。
- **双 agent**：skills 装在 `~/.claude/skills` 与 `~/.codex/skills` 两处，canonical 位须 agent 中立。
- **平台**：Unix 走符号链接、Windows 走拷贝（无软链），canonical 装法须两平台兜。

## Open Questions（TG-21）

1. canonical 前缀命名（`~/.sdflow/` grill 暂用，低风险，可改）。
2. ~~Windows 无软链兜底~~ → **已定**：指针文件 `~/.sdflow/workflow-path`（grill 2026-07-03）。
3. ~~各 skill 规则读点的完整清单~~ → **已定**〔spec-review-amendment，接地镜实扫〕：spec-review 3 处 + impl-review 4 处；opsx-done / recorders = 0 处；opsx-ship 待其 change 落地后追加（移出本次验收）。
4. ~~迁移告警的具体触发点与文案~~ → **已定**〔spec-review-amendment D4〕：update 内联为主 + `opsx-maintain` 兜底扫描；范围含 checkpoint 孤儿副本。
5. ~~运行 checkout 迁移归属~~ → **已定**〔设计门拍板 2026-07-03，Q1=A〕：本 change 认领——fresh clone 至 `~/.skills/sdflow-skills/` + setup.sh（tasks 0.1），并新增 `sdflow-upgrade` skill（tasks §7）；旧 laodao-skills checkout 保留，处置归 `extract-sdflow-repo`。

## Compliance

- **规则/边界合规**：本 change 不引入跨产品共享数据模型（D-6 不适用）、无 DB 迁移（D-2 不适用）、无外部计费服务（TG-24 不适用）。
- **安全**：迁移涉及消费仓既有文件——严守"绝不自动删"（提示人工删），符合项目安全红线。
