# Task 1 Spec 轴审查 — project-local schema 契约

## 结论

**PASS**

审查对象为当前工作树中的 Task 1（`R-ID: SW-SCHEMA`）。本审查只覆盖 Spec 轴；未修改生产代码、`tickets.md` 或其他实现文件。

## 审查输入与证据

- `impl-reports/task1-brief.md`
- `impl-reports/task1-project-local-schema.md`
- `tickets.md` 中的 Global Constraints 与 Task 1
- `design.md` 的目标、决策与组件清单
- `specs/spec-authoring/spec.md`
- `specs/spec-workflow/spec.md`
- 当前实现：`sdflow-init/assets/schemas/sdflow-spec-driven/` 与 `openspec/schemas/sdflow-spec-driven/`

独立复核结果：

- `openspec schema validate sdflow-spec-driven`：exit 0，schema valid。
- `openspec validate align-sdflow-spec-with-openspec-schema --strict`：exit 0，change valid。
- 对 `proposal`、`specs`、`design`、`tasks` 分别运行 `openspec instructions ... --schema sdflow-spec-driven --json`，四个 artifact 均返回；四者均包含成对的 `sdflow:delegation` 标记。
- project-local schema 与内置 `spec-driven` 的四个 artifact `id` / `resolvedOutputPath` 模式一致：`proposal/proposal.md`、`specs/specs/**/*.md`、`design/design.md`、`tasks/tasks.md`。
- project-local schema 的 `specs` 依赖为 `proposal, design`，`tasks` 依赖为 `proposal, design, specs`；CLI JSON 载荷确认了对象依赖链。
- bundle authority 与 dogfood schema 及四个 template 的 SHA-256 均逐文件一致；`schema.yaml` SHA-256 为 `7F75F12F8D11AD3305A1D912101ADA1BAA239A05814D6AABC7C546C08B202B3C`。
- 实现报告记录 schema 是通过 `openspec schema fork spec-driven sdflow-spec-driven` 产生，而非 `schema init`（`task1-project-local-schema.md:35`）。

## R-ID 与 Task 1 验收项

| 验收项 | 证据 | 级别 | 判定 |
|---|---|---:|---|
| schema 由 `schema fork` 产出，而非 `schema init` | 实现报告明确记录 fork 命令；schema 含完整 `instruction` 字段；`openspec schema validate` 通过 | — | 通过 |
| 四个 artifact 的 `id` 与 `generates` 保持内置契约一致 | CLI 对两种 schema 返回相同的四组 `id` / 输出模式；当前 schema 定义四项为 `proposal`, `specs`, `design`, `tasks` | — | 通过 |
| 四个 artifact 均带成对委派标记，并提示 `/sdflow-spec` | 四个 `instructions --json` 载荷均同时包含 `<!-- sdflow:delegation:start -->` 与 `<!-- sdflow:delegation:end -->`，内容要求停止并提示人工调用 `/sdflow-spec` | — | 通过 |
| `specs` 与 `tasks` 的 `requires` 符合目标依赖图，design 无条件生成 | CLI JSON 返回 `specs=[proposal,design]`、`tasks=[proposal,design,specs]`；design instruction 明确 `Always create design.md` | — | 通过 |
| CLI schema validate 通过 | `openspec schema validate sdflow-spec-driven` exit 0 | — | 通过 |

## 已批准设计目标态对照

### 1. schema 层承载阶段一委派约束

设计目标要求把“先拷问后成文”的约束下沉到 project-local schema，而不是只依赖外部指令文档。四个 artifact instruction 均有相同的成对委派块，且 CLI 实际返回该 instruction；满足 `specs/spec-workflow/spec.md` 中“出现在 instructions 载荷内”的目标。

### 2. 真实依赖图进入 CLI 载荷

当前 schema 将 `specs` 从内置依赖扩展为 `proposal, design`，将 `tasks` 扩展为 `proposal, design, specs`。这与 `task1-brief.md`、`tickets.md` Task 1 和设计中的目标依赖图一致；没有发现仅修改静态 YAML、而 CLI 不可见的情况。

### 3. artifact 输出模式保持兼容

四个 artifact 的标识及输出模式保持内置 schema 的兼容形态，`specs` 仍是 glob 模式而不是被改成单一文件路径。该结果与设计中“保留 OpenSpec artifact 契约、由后续相位处理 glob”一致。

### 4. bundle authority 与 dogfood 副本一致

权威 bundle 路径和仓内 dogfood 路径的 schema/template 文件逐文件哈希一致，符合设计规定的单一权威源与下游只读副本目标。Task 1 只要求建立契约；installer、consumer、迁移和回归测试属于后续任务，当前不构成 Task 1 缺口。

## Findings

无 Critical、Important 或 Minor finding。

实现报告中的 `tickets.md` checkbox 未勾选与本次审查结论不冲突：用户明确要求本审查不得修改 `tickets.md`，且 Task 1 报告说明未创建 checkpoint tag；本报告只依据实际实现和独立 CLI 结果判断规格符合性。

## 双轴审查边界

本文件是按 `sdflow-implement` 双轴契约中的 **Spec 轴**产出的 Task 1 审查报告，结论仅表示“实现满足 Task 1 的 R-ID、验收项和已批准设计目标态”。未在本文件中替代 Standards 轴，也未对后续 Task 2–7 作通过声明。
