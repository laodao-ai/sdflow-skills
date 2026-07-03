# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这是什么

一个 **Claude Code + Codex 自建 Skills 集合仓库**（源项目 laodao-skills，本仓库建为 sdflow-skills）。
根目录下每个含 `SKILL.md` 的目录就是一个可安装的 skill；`setup.sh` 把它们装进两个 agent 运行时。
内容以 Markdown 为主（skill 指令 + OpenSpec 工作流规则），少数「数据类」skill 附带 Python 脚本 + pytest 测试。

## 常用命令

### 安装 / 更新 skills（本仓库的构建入口）

```bash
bash setup.sh
```

把每个含 `SKILL.md` 的顶层目录同时装到 `~/.claude/skills/` 和 `~/.codex/skills/`。
Unix 用**绝对路径 symlink**（改源即时生效，无需重装）；Windows 用 copy + `.laodao-skills` marker。
幂等，可反复运行。改动 skill 源码后一般无需重跑（symlink 场景）；仅在**新增/删除**顶层 skill 后重跑，
以建立新链接、清理源已删除的孤儿链接。

### 运行测试

没有根级 pytest 配置——测试各 skill **自包含**在 `<skill>/tests/`，用 pytest 直接跑：

```bash
pytest                                                  # 发现并运行全部 test_*.py
pytest buglist-recorder/tests/                          # 单个 skill
pytest buglist-recorder/tests/test_buglist.py::test_xxx -v   # 单个用例
```

带脚本+测试的 skill 仅这几个：`buglist-recorder`、`todolist-recorder`、`issues-recorder`、
`opsx-project-init`、`opsx-roadmap-planner`。其余为纯 Markdown 编排类，无自动化测试。

## 架构

### Skill 目录约定

每个 skill 是自包含目录：

- **`SKILL.md`**（必需）— frontmatter（`name` / `description`）+ 指令主体。**唯一被 `setup.sh` 识别为 skill 的标志**；
  `description` 决定触发，改它要顾及触发精度。
- **`scripts/`**（数据类才有）— 确定性 Python 脚本。设计取向是「机械活交脚本、模型只做判断」：
  脚本 owns 某类文件的读写与一致性（ID 不撞号、总览表与详细块双写一致等），别把不变量判断塞回模型。
- **`tests/`** — 脚本的 pytest 测试。改 `scripts/` 必须同步跑对应 `tests/`。
- **`assets/` / `references/`** — 模版与参考资料。

### 两类 skill

1. **编排类（纯 Markdown）**：`spec-review` / `impl-review` / `opsx-done` / `opsx-maintain` /
   `embedded-test-sop` / `openspec-upgrade` — 靠 SKILL.md 指令驱动主 session 调度子代理，无脚本。
2. **数据类（Markdown + Python）**：`*-recorder` / `opsx-project-init` / `opsx-roadmap-planner` —
   由 `scripts/` 保证确定性，SKILL.md 负责判断与编排。

### `setup.sh` 安装机制（核心，改动需谨慎）

- 遍历 `REPO_DIR/*/`，**仅含 `SKILL.md` 的目录才安装** → `openspec/`、`docs/`、`hack/` 不会被当 skill。
- 安全兜底：**绝不覆盖非本仓库拥有的同名目录**（只处理自己的 symlink / `.laodao-skills` marker copy）；
  清理源已删除的孤儿链接（用 `-e` 解析检查，保留有效链接）。
- 读 `REPO_DIR/VERSION` 显示版本；**当前仓库未包含 `VERSION`**，故安装摘要显示 `unknown`。

### OpenSpec 的双重角色（`openspec/`）

本仓库既**产出** OpenSpec 工作流资产、又**用**它管理自身变更（dogfooding）：

- **`opsx-project-init/assets/workflow/`** 是这套 spec 工作流 bundle 的**唯一权威源**——铺给其他项目的
  `openspec/workflow/` 都源于此。改规则**先改 assets、再 `opsx-project-init update` 推下游**，
  禁止只改某个下游项目的 `openspec/workflow/` 后忘记回灌。
- **`openspec/workflow/`**（仓库根）— 是 bundle 铺进本仓库自身的**实例**，也是 `spec-review` /
  `impl-review` / `opsx-done` 运行时读取的规则；它由 assets 权威源经 `opsx-project-init` 同步而来，勿单独改。
- **`openspec/{changes,specs,issues,config.yaml}`** — 本仓库自身的 OpenSpec 变更管理，
  流程走 propose → review → done → archive，强制规范见文末托管区块。
- **`.claude/skills/openspec-*` 与 `.codex/skills/openspec-*`** — openspec CLI（`@fission-ai/openspec`）
  init 时生成的官方 change-workflow skills，随仓库提交，**非本仓库维护的源**，勿在此手改。

### `hack/`

- `checkpoint-commit.sh` — 变更过程中的检查点提交脚本（由 `opsx-project-init` 引用并测试）。

## 修改本仓库的注意

- 新增/删除顶层 skill 后：更新 README「Skills 列表」保持一致，并重跑 `setup.sh` 建链接 / 清孤儿。
- 数据类 skill 改 `scripts/` → 必跑 `tests/`；纯 Markdown skill 改的是指令与触发。
- 审查顺序（下方托管区块有强制规范）不可颠倒：`/review`（本地 diff）→ push PR → `/code-review`（远程 PR）。

## 本仓库自身的 OpenSpec 工作流规范

下方为 `opsx-project-init` 铺设、`opsx-maintain` 维护的托管区块（**勿手改区块内部**），
是本仓库做变更时的强制流程，也是上文提到的规则真相源：

<!-- opsx-init:start —— 由 opsx-project-init 维护，勿手改本区块 -->
## OpenSpec 工作流（opsx-project-init 铺设）

端到端流程见 [openspec/workflow/workflow.md](./openspec/workflow/workflow.md)（真相源）。规则集在 `openspec/workflow/`：
`trigger-catalog.md`（触发单一源 TG）· `spec-checklists/`、`code-checklists/`（设计审/代码审）·
`ff-generation-constraints.md` · `design-diagrams.md` · `spec-review.md` · `generation-process.md`。
质量分层与升级安全见 `openspec/workflow/reference/quality-layering.md`。

**强制操作规范**

- **起手判触发**：收到 `opsx:ff` / `propose` / `explore`，先按 `trigger-catalog.md` 的 TG 判命中，
  据此激活对应的生成约束 / 领域清单 / 画图 / 模版必填槽（深度由触发决定，不分 S/M/L）。
- **审查顺序不可颠倒**：`/review`（本地 diff）→ push PR → `/code-review`（远程 PR）。
  子 agent 调度期间（subagent-driven-development / spec-review / impl-review 运行中）禁 `/clear`。
- **ff 开分支**：`opsx:ff` 若不在 feature 分支，先 `git checkout -b feat/{change}`（FF-0）。
- **INDEX 同步**：新增/删 `openspec/workflow/` 规则后，同步 `openspec/INDEX.md`。

**配套 skill（workflow 依赖，需先安装）** — 均来自 laodao-skills（`bash ~/.skills/laodao-skills/setup.sh` 装到 Claude+Codex）：

| skill | 在流程中的角色 |
|---|---|
| `/spec-review` | 设计审**主审**——并行多镜，按 `spec-checklists/domains` + 对抗 + 接地读码 |
| `/impl-review` | 代码审**主审**——并行多镜，按 `code-checklists/domains` + 对抗 + 置信过滤 |
| `/opsx-done` | **闭环**——verify → archive（delta 对码核验同步）→ commit → merge |

> 另有两个记录类配套 skill（按需）：`/buglist-recorder`（缺陷）、`/todolist-recorder`（改进收集池），
> 同样来自 laodao-skills，写入 `openspec/buglists|todolists/`。
<!-- opsx-init:end -->
