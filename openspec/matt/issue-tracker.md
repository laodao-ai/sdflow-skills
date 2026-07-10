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

## Wayfinding 约定（Wayfinding operations）

`wayfinder` 使用一个 map 文件和多个子工作项文件；下文路径统一用 `<root>` 表示落盘根目录。

**`<root>` 条件分流**：若调用语以固定字面量声明了 map 路径（形如 `openspec/roadmaps/{name}/footage/map.md`），或本次 wayfinder 由 `sdflow-roadmap` 发起并指定该路径——该 effort 属 **roadmap 类**，`<root>` = `openspec/roadmaps/{name}/footage/`；其余情况 `<root>` 默认 = `openspec/matt/<effort>/`。

- map：`<root>map.md`，记录 Notes、Decisions-so-far 和 Fog。
- 子工作项：`<root>issues/<NN>-<slug>.md`。顶部使用 `Type:` 记录 `research`、`prototype`、`grilling` 或 `task`，使用 `Status:` 记录 `claimed` 或 `resolved`。
- 依赖：顶部以 `Blocked by: NN, NN` 列出依赖；列出的工作项全部为 `resolved` 后才解除阻塞。
- frontier：在 `<root>issues/` 中查找未阻塞、未领取且未解决的工作项，按编号优先。
- claim：先写入 `Status: claimed` 并保存，再开始工作。
- resolve：在 `## Answer` 下追加答案，写入 `Status: resolved`，再把上下文指针追加至 `<root>map.md` 的 Decisions-so-far。

### map 持久字段

`<root>map.md` 头部持久化两个字段，续跑（新 session 续用某 effort）一律从字段派生路径，不重新做语义判别。roadmap 类 effort（`<root>` = `openspec/roadmaps/{name}/footage/`）字面为：

```
Tracker root: openspec/roadmaps/{name}/footage/
Effort kind: roadmap
```

`<root>` 落在默认根（`openspec/matt/<effort>/`）时同样持久化 `Tracker root:` 字段（写默认根字面量），`Effort kind:` 按实际 effort 类型填写。

### stale claim 重认领

发现某票 `Status: claimed` 但其 session 已中断（压缩/崩溃），长期无进展：在票尾追加一行中断注记后即可重认领、改回可工作状态继续处理——claimed 票不得永久掉出 frontier 无人问津。

### map 再入约定

同一 effort 二次 chart（如远期阶段补细讨论）不得覆写既有 `<root>map.md`：钉死为**单 map 分批续用**——同一个 `map.md` 在其生命周期内允许多批次追加票，无需每次讨论都新开 map；**满 30 票时**归档当前 map 为 `<root>map-N.md`（`N` 从 1 起算）并新起一份 `map.md`，新 map 头部记一行「承接自 map-(N-1).md」，票号不复用（从旧 map 最大编号 +1 续起）。

### 边界声明

- footage/ 下内容不进 triage 扫描。
- 三件套（design.md / roadmap.md / task-log.md）MUST NOT 引用 footage/ 下任何内容。
- 路由回退误落默认根（`openspec/matt/<effort>/`）的 wayfinder 票 MUST NOT 被 triage 贴五态标签或改写 Status 字段（两套状态机语义不兼容）。
