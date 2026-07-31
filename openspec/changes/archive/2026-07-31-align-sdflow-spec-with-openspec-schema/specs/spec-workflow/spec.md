## ADDED Requirements

### Requirement: project-local schema 随 bundle 下发，受 CLI 版本门与迁移前置约束

阶段一使用的 openspec workflow schema SHALL 由 bundle 以 project-local schema 形式下发，使「产 spec 必须先经拷问」这条约束出现在模型消费的 `instructions` 载荷内，而非仅存在于项目指令文件。

**权威源与分发** —— schema（`schema.yaml` + `templates/`）的权威源 SHALL 唯一位于 `sdflow-init/assets/schemas/<name>/`，随 `copy_bundle` **整删重拷**下发到消费仓 `openspec/schemas/<name>/`（与 `tools/` 同构的收敛语义：拷贝前若目的地已存在先整删再整拷，防上游删文件后消费仓残留孤儿）。消费仓副本 SHALL 视为只读，改动 MUST 回灌权威源后经 `sdflow-init update` 下发；MUST NOT 为 schema 另建独立于 bundle 的第二条分发路径。

**schema 内容约束** —— 该 schema SHALL 由 `openspec schema fork spec-driven <name>` 产出（**MUST NOT 用 `schema init`**：其产物不含 `instruction` 字段，而相位 C 将 `instruction` 列为必需字段、缺失即 fail-closed）。fork 产物 SHALL 保持四个 artifact 的 `id` 与 `generates` 路径与内置一致（`proposal.md` / `specs/**/*.md` / `design.md` / `tasks.md`）——相位 C 的路径净化 allowlist 是硬编码字面量，任一 `generates` 改动都会使写入被拒。schema 的合法性 SHALL 由 `openspec schema validate <name>` 判定，MUST NOT 手写 YAML 解析器代为判断。

**CLI 版本门** —— `sdflow-init` 在铺设 schema 前 SHALL 判定 `openspec --version` **≥ 1.7.0**。不满足时 SHALL 不铺 schema、consumer 的 `config.yaml` 的 `schema:` 保持内置值、并 **fail-loud 输出一行原因**；此时 change 创建与产出行为 SHALL 与未引入本能力时完全一致。理由：1.7.0 之前官方 workflow 内嵌的硬编码 spec-driven 套路会**静默盖过** custom schema 的 `instruction`（上游 PR #1405 修复），且其触发条件正是「custom schema 复用了熟悉的 artifact 名」——而复用同名恰是上一段的强制约束，故在旧版 CLI 上失效是必然而非概率。

**迁移前置与顺序** —— change 所属 schema 钉在其自身 `.openspec.yaml`；缺该文件的 change 才跟随 `config.yaml` 解析。因此 `sdflow-init` 在**切换 `config.yaml` 的 `schema:` 之前** SHALL 扫描 `openspec/changes/*/`（**仅在途，MUST NOT 扫 `changes/archive/`**），对缺 `.openspec.yaml` 的 change 补写其当前实际所属的 schema 名。该补写 SHALL 幂等（已存在则跳过）。**顺序 MUST NOT 颠倒**：先切 config 再补写，补写方读到的已是新 schema 名，等于把在途 change 钉在它从未使用过的 schema 上。若跳过本步，缺该文件的在途 change 会在切换后被按新 schema 重新解读（实测：其 `specs` 由 `ready` 变为 `blocked`），**且该失效是静默的**——`blocked` 不报错，只是不再前进。

**可观测性** —— 版本门与迁移补写 SHALL 各输出一行结论（铺/不铺及原因、补写了几个 change）并进入 `sdflow-init` 既有动作汇总。

#### Scenario: CLI 版本不足时不铺 schema 且行为等同今天
- **WHEN** 消费仓所在机器的 `openspec --version` 为 1.6.x，跑 `sdflow-init update`
- **THEN** 不铺 `openspec/schemas/`、`config.yaml` 的 `schema:` 保持内置 `spec-driven`、输出一行说明版本不足；该仓的 `openspec new change` 与相位 C 产出行为与引入本能力前完全一致

#### Scenario: 切换前补写在途 change 的 schema 归属
- **WHEN** 某消费仓有一个在途 change 目录不含 `.openspec.yaml`，随后跑 `sdflow-init update` 且 CLI 版本满足
- **THEN** update 先为该 change 补写 `schema: spec-driven`，再铺 schema 并切换 `config.yaml`；切换前后该 change 的 `openspec status` 各 artifact 状态**保持一致**

#### Scenario: 补写幂等且不触归档
- **WHEN** 同一消费仓连续跑两次 `sdflow-init update`，且 `changes/archive/` 下存在若干无 `.openspec.yaml` 的历史归档 change
- **THEN** 第二次运行对已补写的在途 change 为 no-op；归档目录全程不被扫描、不被写入

#### Scenario: 下游手改 schema 被整删重拷收敛
- **WHEN** 某消费仓直接编辑了 `openspec/schemas/<name>/schema.yaml`，随后跑 `sdflow-init update`
- **THEN** 该目录被整删重拷为权威源版本，本地改动不保留；若该改动确有必要，SHALL 回灌 `sdflow-init/assets/schemas/` 后重新下发

#### Scenario: schema 产出方式受限于 fork
- **WHEN** 维护者需要新建或重建该 project-local schema
- **THEN** 使用 `openspec schema fork spec-driven <name>` 并以 `openspec schema validate <name>` 校验；MUST NOT 使用 `openspec schema init`（其产物 `instruction` 为空，会使相位 C 的最小 schema 断言 fail-closed）
