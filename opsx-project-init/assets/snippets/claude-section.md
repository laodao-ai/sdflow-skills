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
