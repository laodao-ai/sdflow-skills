# 部署 footprint：规则走全局、消费仓只留最小副本

opsx-project-init 曾把整个 workflow bundle（≈34 文件）复制进每个消费仓的 `openspec/workflow/`。规则文件从不按仓定制（定制只在 `config.yaml`），却在每个消费仓留一份可观的副本。改按"内容性质"分层部署，把纯机械/纯规则的部分收归全局，消费仓只留**本身需要在仓里**的最小集。

- **规则（`workflow/*.md` + `spec-checklists/` + `code-checklists/`，≈28 文件）→ 全局唯一**：skills（spec-review / impl-review / opsx-done / recorder / opsx-ship）从全局 toolkit 解析，消费仓**不再复制**。
- **review UI 机械（`tools/` + `serve.sh` + `review.html`，≈5 文件）→ 仍复制进 `openspec/`（尽量少）**：review 服务器根 = `openspec/` + 根相对 `/workflow/tools/`，不落地即 404（见 adr/其它 与决策表 B1 的服务器根锚模型）。故 tools/ 是唯一不得不留的机械副本。
- **`hack/checkpoint-commit.sh` → 全局**：纯 git 包装、无按仓定制、无 pin 价值，与 `ff0-branch-guard.py` / `change-review-stub.py` 两个全局 hook 同款，装一次跨仓生效。顺带根治 `core.fileMode=false` 致 exec 位丢失的坑（全局装时一次设好）。
- **`config.yaml` / `changes/` / `specs/` → 仓内**：本项目配置 + spec 内容本体，天然属仓。

**明确接受的代价**：消费仓**失去按仓 pin 工作流规则**——所有仓跟随全局 toolkit HEAD，规则一改即刻影响所有仓（不再靠 `update` 显式采纳）。用户明确选此方向（footprint 干净 > 按仓 pin）：规则是 dev 工作流、非构建产物，latest-is-fine 可接受。

## Considered Options

- **规则全局 + tools 最小副本 + hack 全局（选中）**：消费仓污染从 ≈34 → ≈5 文件；代价 = 失按仓 pin + skills 须能解析全局 bundle 路径。务实——tools 留副本免去重写 serve.sh。
- **复制全量（现状）**：按仓 pin + 自包含可读 + skills 仓相对路径最简；代价 = 每个消费仓持续背 ≈34 文件纯机械副本。
- **纯激进（连 tools 也不落地，自制全局路由 server）**：消费仓零 review 文件；代价 = 重写 serve.sh 弃 `python -m http.server`、review.html 项目名改由 server 注入。评估后取"tools 留最小副本"更务实（省 serve.sh 重写），故未选。

## Consequences

- skills 里所有 `openspec/workflow/...` 读点改为**全局解析 + 缺失显式降级**（不静默当"无此层"，同"反静默守卫"精神）。
- opsx-project-init：`copy_bundle` 去掉规则部分，只保留 tools/serve/review 复制 + `ensure_dirs` + `config`；`copy_hack` 改为全局安装（同 hooks 路径）。
- 消费仓 `update` 不再拉规则（规则全局自动最新），仍 `update` 刷 tools/。
- **失 pin = 已知限制**：若某仓需固定旧规则行为，本模型不支持（须显式 opt-out 或另法），记录在案。
- **未决实现细节（留落地 change 的 design 定）**：全局 bundle 路径解析机制——固定 `~/.skills/laodao-skills/...` 约定（CLAUDE.md 已把此当安装位）vs env var vs resolver；建议默认固定约定 + env var 覆盖。
- **落地 change**：`minimize-repo-footprint`（承 Phase A 的 G6 复制模型修正，不改归档 umbrella，新 change 的 design 引本 ADR）。

## 落地设计骨架（explore 2026-07-03 补）

本 ADR 原文只定了「分层」那一层（哪些走全局、哪些留仓）。落地 change 的 explore 又长出以下骨架，一并记入（design.md 展开、引本节）：

- **解析 resolver（三步链，一条规则覆盖两类仓）**：skills 读规则的顺序 =
  1. 仓内**有规则文件**（`workflow.md` / `spec-checklists/` / `code-checklists/`）→ 用本地；
  2. 否则 → 全局 canonical bundle → 外部消费仓跟 released HEAD；
  3. 全局也缺 → **显式降级**通用评审 + 告警（不静默当"无此层"）。
  - **关键细节**：第 1 步查**规则文件本体**、不查 `openspec/workflow/` 目录——因 `tools/` 使该目录在每个仓都存在，查目录会让每个消费仓误命中"本地 pin"。
  - 第 1 步天然覆盖两个正牌用户：**toolkit 源仓自己**（有本地副本，dogfood 在用端，不吃未发布编辑）+ 消费仓的**显式 pin 逃生口**。故 toolkit **无需 config flag 声明"我是源仓"**——本地副本的存在即声明。

- **全局钉法（A3：提根 + canonical 软链）**：把 workflow bundle 从 `opsx-project-init/assets/workflow/` **提到仓根**（如 `<repo>/workflow/`），给它一个不隶属任何单一 skill 的公共家；`setup.sh` 装一个稳定 canonical 位（暂名 `~/.sdflow/workflow`，agent 中立、命名留 impl）软链 → 仓根 bundle，所有 skill 解析这一个固定路径。
  - 动因：change 后 5+ skill 都解析进 bundle，若留在 `opsx-project-init/assets/`（某 skill 私有资产）是"公共依赖伪装成私有资产"的耦合味；且 `setup.sh` 用 `$REPO_DIR`（clone 到哪算哪）安装，硬编码 `~/.skills/laodao-skills/...` 不可靠。
  - **不破 dev/release 隔离**：提根只搬**源的家**（assets/→仓根），toolkit 自己的 in-use dogfood 副本 `openspec/workflow/` 原地不动、仍由 `opsx update` 刷新（发布闸不变）。

- **迁移（opt-in 删，永不自动删）**：存量消费仓已有 ≈28 规则文件；`update` **停止复制规则**（只留 `tools/` 5 个），检测到残留旧规则 → **告警**"它遮蔽全局且不再更新——删=跟全局 / 留=显式 pin"，**绝不自动删**（安全 + 免去分辨源/消费仓 + 老仓平滑迁移）。附带把 ADR 的"反静默"从"缺失降级"扩到"陈旧遮蔽告警"。

- **未决收敛**：原文"未决实现细节（全局路径解析机制）"已由上面 A3 定向（canonical 软链，命名留 impl）；剩余纯实现细节（各 skill 读点清单、Windows 无软链兜底、`hack/checkpoint-commit.sh` 全局化 + `core.fileMode` exec 位）交 design/tasks。

## grill-amendment（2026-07-03，逐决策死磕后）

explore 那节经 grill 修正四处（design.md 已同步）：

- **撤销"提根"**：**不**把 bundle 从 `opsx-project-init/assets/workflow/` 提到仓根。canonical 软链/指针的间接层已把 assets/ 布局藏住（skill 只见 `~/.sdflow/workflow`），提根买不到额外解耦，却要重写"唯一权威源"约定 5 处（SKILL.md×4 / init.py / config.yaml / CHANGELOG）+ 动 tests——不划算。**`assets/workflow/` 仍是唯一权威源，原封不动**。
- **canonical 机制细化（非纯"软链"）**：Unix/Mac = 软链 `~/.sdflow/workflow` → 运行 checkout 的 bundle（透明）；Windows = 指针文件 `~/.sdflow/workflow-path`（平台无软链）；skill 解析 = "试 `~/.sdflow/workflow/` 目录 → 否则读 `~/.sdflow/workflow-path`" 回落链（平台无关）。两者都由 `setup` 从 `$REPO_DIR` 写，robust to clone 位置。
- **checkpoint 全局化 ≠ "同两个全局 hook 同款"（假类比修正）**：两个 hook 靠 `~/.claude/settings.json` **事件注册**（Claude 独有，`~/.codex/hooks` 不存在）；`checkpoint-commit.sh` 是步末 **bash 调用**的**跨-agent** 工具。故其家 = agent 中立的 canonical 根 `~/.sdflow/hack/checkpoint-commit.sh`（**拷贝**，两平台，白拿 `core.fileMode` exec 位根治），**不进** `~/.claude/hooks`；`workflow.md` line62 的 `[checkpoint]` 单点约定改指它。
- **dev/release 隔离另立 `adr/0005`**：本 ADR 只管**消费仓**部署 footprint；toolkit **自身**"开发 vs 运行 checkout"拓扑见 `adr/0005`，本 ADR 的 resolver local-first 正为其开发 checkout（与消费仓 pin）服务。
