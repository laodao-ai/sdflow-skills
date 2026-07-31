# align-sdflow-spec-with-openspec-schema

## Why

阶段一「产 spec 必须先经拷问」这条约束目前**全靠指令层自律**——`CLAUDE.md` 与下游托管区块里各有一句「模型 MUST NOT 自行选 `opsx:ff` 绕过拷问」，它住在**另一个文件**里，而这套流程要防的失效模式恰恰包含「不会想到要去查它」。同时 `sdflow-spec` 相位 C 与 openspec CLI 的载荷契约已经对不齐：CLI 1.7.0 起 `specs` 的 `resolvedOutputPath` 是**字面 glob**（不是文件路径），零 delta change 必须声明 `skip_specs` 才能过 `validate`，而相位 C 对这两件事都无处置。

CLI 1.7.0 同时打开了一条 schema 层通道（`openspec schema fork` 带出全部 `instruction`，且 PR #1405 修掉了「官方 skill 内嵌套路盖过 custom schema instruction」的缺陷），使这条约束可以下沉到模型**正在处理的任务载荷**里。两件事共用同一片改动区域（相位 C 的 C.2/C.3/C.4 与终审），故合并为一个 change（决策与理由见 `decision-memo.md`，架构取舍见 `openspec/adr/0034-stage-one-entry-descends-to-project-local-schema.md`）。

## What Changes

- **新增 project-local schema `sdflow-spec-driven`**（由 `openspec schema fork spec-driven` 产出，落 `openspec/schemas/`）：其 `instruction` 前置一段以 `<!-- sdflow:delegation:start -->` / `<!-- sdflow:delegation:end -->` 包裹的委派文案（拦截 + 提示人敲 `/sdflow-spec`）；其 `specs.requires` 改为 `[proposal, design]` 且 **design 在本 fork 内转为无条件产物**。
- **`sdflow-spec` 相位 C 照 CLI 实际形状对齐**：C.3 增加 glob 分支（`resolvedOutputPath` 为 glob 时按 `instruction` 选具体路径、改写既有文件时取 `artifactPaths.<id>.existingOutputPaths`）；C.3 应用载荷前**机械剥离**委派区块；C.3 的 `dependencies` 断言收紧到实际形状（dict 列表）；相位 C 认 `status: "skipped"` 并 **MUST NOT** 为该产物创建文件。
- **C.2 的写死超集表由唯一路径降级为 fallback**：fork 后 CLI 依赖图已密，清单以 schema 声明的 `requires` 为准；但 fallback 分支 **MUST NOT 删除**（内置 schema 与未来回退时的正确性底座）。终审第 2 条（design↔specs 双向核对）相应由「唯一防线」降为「兜底」。
- **采纳 `skip_specs`**：判据写进 bundle 供人读，判断发生在相位 B 并落进 `decision-memo.md`；相位 C 只认 CLI 自报的 `status`，不做自由裁量。
- **`sdflow-init` 随 bundle 下发该 schema**：`config.template.yaml` 的 `schema:` 指向 fork 名；schema 目录纳入 `copy_bundle` 托管刷新（与 `tools/` 同构，下游整删重拷、禁止在下游手改）。
- **新增 CLI 版本门（≥1.7.0）**：不满足则不铺 schema、config 保持 `spec-driven`、fail-loud 报一行。
- **新增迁移步**：切 config **之前**扫 `openspec/changes/*/`，给缺 `.openspec.yaml` 的在途 change 补写 `schema: spec-driven`（幂等）。**顺序不可颠倒**。

## Capabilities

### New Capabilities

（无——本次不引入新能力，改动落在两个既有能力的需求上。）

### Modified Capabilities

- `spec-authoring`: 相位 C 的载荷消费契约变更——glob artifact 的写入目标解析、`skipped` 态处置、委派区块剥离、`dependencies` 断言形状；强制阅读清单由「写死超集」改为「依赖 schema 声明的依赖图」；生成所用 schema 由内置 `spec-driven` 改为 project-local fork。
- `spec-workflow`: bundle 下发面新增 schema 目录的托管刷新；新增消费仓迁移前置步（补写在途 change 的 `.openspec.yaml`）与 CLI 版本门的降级契约。

## Impact

- **代码 / 资产**：`sdflow-spec/SKILL.md`（C.2 / C.3 / C.4 / 终审）；`sdflow-init/scripts/init.py`（版本门、迁移补写、schema 目录纳入 `copy_bundle`）；`sdflow-init/assets/workflow/config.template.yaml`；新增 `sdflow-init/assets/schemas/sdflow-spec-driven/`（bundle 权威源）与本仓 `openspec/schemas/`；`openspec/config.yaml` 的 `schema:` 键。
- **依赖**：新依赖 openspec CLI 的 **experimental** schema 接口（`schema fork` / `schema validate`），并要求 **CLI ≥ 1.7.0**。
- **下游**：所有已铺 bundle 的消费项目在下次 `sdflow-init update` 时切换 schema；不满足版本门者保持现状。
- **不影响**：已归档 change（CLI 不再对其 status/validate）；`sdflow-spec` 的相位 A/B 协议；`disable-model-invocation` 属性保持不变。

## Success Metrics

1. 本仓与至少一个下游项目切到 `sdflow-spec-driven` 后，`openspec instructions <artifact> --json` 的 `dependencies` 反映新依赖图（`specs` 含 `design`），且 `sdflow-spec` 相位 C 全程不因委派区块自我劝退（**一次完整走通产四件套**即达标）。
2. 走 `/opsx:ff` 时模型**停下并提示改敲 `/sdflow-spec`**，不自行写产物。
3. 迁移零回归：切换后**在途 change** 的 `openspec status` 各 artifact 状态与切换前一致（用切换前后快照比对）。
4. CLI <1.7.0 的环境下 `sdflow-init` 不铺 schema、报一行原因，且 change 创建与产出行为与今天完全一致。
5. `sdflow-spec` 相位 C 处置 `skipped` 态时**不创建** specs 文件，且 `openspec validate --strict` 通过。

## 需求优先级〔TG-19〕

- **P0**（不做则本 change 无意义或有害）：委派区块的机械剥离（否则相位 C 自指死锁）；CLI 版本门（否则 <1.7.0 下游委派静默失效）；迁移补写 + 顺序约束（否则在途 change 静默变形）；glob 写入目标处置。
- **P1**（核心价值）：fork schema 及其 instruction 委派文案；`requires` 边改密 + design 转无条件；`skipped` 态处置；随 bundle 下发。
- **P2**（清理，可随后跟进）：C.2 超集表退役与终审第 2 条降级措辞；`dependencies` 断言收紧；`existingOutputPaths` 替代自行 glob。

## 利益相关方与外部依赖〔TG-20〕

- **下游消费项目**（外部影响方）：它们的 `openspec/config.yaml` 与在途 change 会被 `sdflow-init update` 改动。缓解 = 版本门 + 迁移补写 + 下游整删重拷的既有托管纪律。
- **openspec CLI（Fission-AI）**：外部依赖，schema 子命令自标 experimental，接口可能变；且 fork 是快照，上游 `spec-driven` 更新不自动跟。
- **走官方入口的使用者**：`/opsx:ff`、`/opsx:propose`、`/opsx:continue` 的行为会被委派文案改变（拦截 + 转人）。

## 假设〔TG-22〕

| 假设 | 失效影响 | 现状 |
|---|---|---|
| 模型读到 STOP 文案后会真的停下并提示人 | 委派失效，退回今天的状态（不会更糟） | **无实测锚**，属提示层而非机械保证 |
| 官方 `ff`/`propose` 不会剥离或忽略未知 HTML 注释标记 | 委派文案可能不被展示 | 未实测；风险低（instruction 是纯文本透传，marker 透传已验） |
| 下游在 `sdflow-init update` 时的在途 change 数量可控 | 迁移补写面变大，但逻辑幂等，影响仍可控 | 未测量 |

## 开放问题〔TG-21〕

| 问题 | 负责人 | 截止 |
|---|---|---|
| 委派在 **Codex 宿主**下是否成立（其 skill 执行面与 `disable-model-invocation` 语义未验） | 实现期 owner | 实现期首个 ticket 前 |
| schema 的 artifact 自身 `description` 是否进 `instructions` 载荷（决定「字段分离」备选是否可行，当前已按不可行处理） | 实现期 owner | 仅在需要回退委派形态时才需回答 |
| 上游 `spec-driven` 更新时如何发现 fork 已漂移（本次不解决，已记 roadmap 遗留 todo） | — | 下一批 |

## Non-Goals

- **不改** `sdflow-spec` 的 `disable-model-invocation` 属性（有意设计，见 ADR-0034）。
- **不做**「委派被遵守」的机械保证——它是提示层加强，MUST NOT 表述为自动回流。
- **不做** fork 漂移的机械检测门（记 todo，下一批）。
- **不为** `skip_specs` 的「够不够格」建机械门（无确定性信号可锚，属合法语义残余）。
- **不动** stores、CodeArts / Hermes / ZCode 三个新宿主适配（见 roadmap「明确不做」）。
- **不含** roadmap 里的 P2（prevention 层扩到 apply/archive）与 P3（`sdflow-done` archive 现代化）。

## Compliance

- **通则③**：范围严格锚 roadmap 的 P1 定义（A1–A4 + E1–E3），未顺手扩到 P2/P3；「不推下游」这一自加约束已在相位 A 撤销。
- **分析基准 1（机械化优先）**：委派区块剥离、迁移补写、版本门均为确定性操作；`skip_specs` 的「够不够格」判断**显式留为语义残余**（D10），不伪装成机械门。
- **DOC-1**：本文只写最终态；决策演进与被砍候选留在 `decision-memo.md` 与 ADR-0034。
- **术语纪律**：委派标记名不含 `gate`——`openspec/CONTEXT.md` 已把 gate 确立为正确性门专名，而本机制是提示层。
- **CONTEXT.md「盘面即状态」**：schema 归属判定读 change 自己的 `.openspec.yaml`（确定性盘面），不另设第二真相源。
