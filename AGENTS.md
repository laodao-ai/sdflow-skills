# AGENTS

本文件为项目级 AI 指令。

## 项目概览

本仓库是面向 Claude Code 与 Codex 的 `sdflow-skills` 集合，也是 OpenSpec 工作流 bundle 的权威源，并使用自身的 `openspec/` 目录管理变更。

- 每个根目录下含 `SKILL.md` 的目录都是可安装 skill；可选的 `scripts/`、`tests/`、`assets/`、`references/` 由该 skill 自行维护。
- `sdflow-init/assets/workflow/` 是下游 `openspec/workflow/` 规则的唯一权威源。修改工作流规则时先改这里，再通过 `sdflow-init update` 更新下游；不要仅修改下游副本。
- 本仓的 `openspec/workflow/` 只保留工具文件，运行时规则由全局 canonical bundle 解析。不要把规则副本重新放回该目录。
- 面向用户的新增或更新文档默认使用中文；命令、路径、文件名、产品名和代码标识符保持原文。

## 常用命令

```bash
bash setup.sh                                      # 安装或刷新 Claude 与 Codex 的 skills
pytest                                             # 运行全部测试
pytest <skill>/tests/                              # 运行单个数据类 skill 的测试
pytest <skill>/tests/test_file.py::test_name -v    # 运行单个用例
git diff --check                                   # 提交前检查空白错误
```

## 修改约定

- 修改数据类 skill 的 `scripts/` 时，必须同时维护并运行该 skill 的 `tests/`；纯 Markdown skill 则重点检查指令、触发条件和引用路径。
- 新增或删除顶层 skill 时，更新 `README.md` 的 Skills 列表，并运行 `bash setup.sh` 以创建新链接或清理孤儿链接。
- Unix 下 skill 目录通过绝对路径 symlink 安装，通常修改源文件后立即生效；但新增/删除顶层 skill，以及修改 `sdflow-init/assets/hack/` 中会复制到 `~/.sdflow/hack/` 的脚本后，必须重新运行 `bash setup.sh`。
- 保持 `SKILL.md` frontmatter 与目录职责一致；不要跨 skill 引用其内部脚本来实现运行时依赖，优先保持 skill 自包含。
- 修改变更管理、规则或生成资产时，遵循下方 OpenSpec 托管区块定义的触发、审查和归档流程。

<!-- opsx-init:start —— 由 sdflow-init 维护，勿手改本区块 -->
## OpenSpec 工作流（sdflow-init 铺设）

端到端流程见 workflow 规则集 `workflow.md`（真相源；本仓有 `openspec/workflow/` 规则副本则用之，否则在全局 `~/.sdflow/workflow/`）。规则集在 `openspec/workflow/`：
`trigger-catalog.md`（触发单一源 TG）· `spec-checklists/`、`code-checklists/`（设计审/代码审）·
`ff-generation-constraints.md` · `design-diagrams.md` · `spec-review.md` · `generation-process.md`。
质量分层与升级安全见 `openspec/workflow/reference/quality-layering.md`（本仓有 `openspec/workflow/` 规则副本则用之，否则在全局 `~/.sdflow/workflow/`）。

**强制操作规范**

- **起手判触发**：收到 `opsx:ff` / `propose` / `explore`，先按 `trigger-catalog.md` 的 TG 判命中，
  据此激活对应的生成约束 / 领域清单 / 画图 / 模版必填槽（深度由触发决定，不分 S/M/L）。
- **审查顺序不可颠倒**：`/review`（本地 diff）→ push PR → `/code-review`（远程 PR）。
  子 agent 调度期间（subagent-driven-development / sdflow-implement / sdflow-spec-review / sdflow-code-review 运行中）禁 `/clear`。
- **ff 开分支**：`opsx:ff` 若不在 feature 分支，先 `git checkout -b feat/{change}`（FF-0）。
- **INDEX 同步**（仅规则副本 pin 仓/toolkit 源仓适用）：新增/删 `openspec/workflow/` 规则后，同步 `openspec/INDEX.md`。

**配套 skill（workflow 依赖，需先安装）** — 均来自 sdflow-skills（`bash ~/.skills/sdflow-skills/setup.sh` 装到 Claude+Codex）：

| skill | 在流程中的角色 |
|---|---|
| `/sdflow-spec-review` | 设计审**主审**——并行多镜，按 `spec-checklists/domains` + 对抗 + 接地读码 |
| `/sdflow-code-review` | 代码审**主审**——并行多镜，按 `code-checklists/domains` + 对抗 + 置信过滤 |
| `/sdflow-done` | **闭环**——verify → archive（delta 对码核验同步）→ commit → merge |

> 另有两个记录类配套 skill（按需）：`/sdflow-buglist`（缺陷）、`/sdflow-todolist`（改进收集池），
> 同样来自 sdflow-skills，写入 `openspec/issues/buglist|todolist/`。
<!-- opsx-init:end -->
## Agent skills

### Issue tracker

工作项使用本地 Markdown，存放在 `openspec/matt/<feature>/`；外部 PR 不作为 triage 输入。详见 `openspec/matt/issue-tracker.md`。

### Triage labels

使用默认的五种 triage 标签：`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`。详见 `openspec/matt/triage-labels.md`。

### Domain docs

单一上下文布局：`openspec/CONTEXT.md` 与 `openspec/adr/`。详见 `openspec/matt/domain.md`。
