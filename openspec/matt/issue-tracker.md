# 工作项跟踪：本地 Markdown

本仓库的工作项和 PRD 使用本地 Markdown，不使用 GitHub 或 GitLab Issues。

## 路径约定

- 工作项根目录：`openspec/matt/`
- 一个功能对应一个目录：`openspec/matt/<feature>/`
- 功能 PRD：`openspec/matt/<feature>/PRD.md`
- 实现工作项：`openspec/matt/<feature>/issues/<NN>-<slug>.md`，从 `01` 开始编号
- 在工作项文件顶部用 `Status:` 记录 triage 状态；状态词见 `triage-labels.md`
- 讨论和补充按时间追加到文件末尾的 `## Comments` 区块

## Skill 操作规则

当 `to-tickets`、`triage`、`to-spec` 或 `qa` 需要发布、读取或更新工作项时：

- 在 `openspec/matt/<feature>/` 下创建、读取或更新 Markdown 文件；必要时先创建目录。
- 接收已给出的功能目录、文件路径或工作项编号作为定位依据。
- 不调用 `gh` 或 `glab`，也不将外部 PR 作为 triage 输入。

## Wayfinding 约定

`wayfinder` 使用一个 map 文件和多个子工作项文件：

- map：`openspec/matt/<effort>/map.md`，记录 Notes、Decisions-so-far 和 Fog。
- 子工作项：`openspec/matt/<effort>/issues/<NN>-<slug>.md`。顶部使用 `Type:` 记录 `research`、`prototype`、`grilling` 或 `task`，使用 `Status:` 记录 `claimed` 或 `resolved`。
- 依赖：顶部以 `Blocked by: NN, NN` 列出依赖；列出的工作项全部为 `resolved` 后才解除阻塞。
- frontier：在 `issues/` 中查找未阻塞、未领取且未解决的工作项，按编号优先。
- claim：先写入 `Status: claimed` 并保存，再开始工作。
- resolve：在 `## Answer` 下追加答案，写入 `Status: resolved`，再把上下文指针追加至 `map.md` 的 Decisions-so-far。
