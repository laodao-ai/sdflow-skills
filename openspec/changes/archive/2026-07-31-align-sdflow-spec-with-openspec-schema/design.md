# Design · align-sdflow-spec-with-openspec-schema

## Context

`sdflow-spec` 与 openspec CLI 之间有两处结构性错位：

1. **防绕过住在别处**：阶段一「先拷问后成文」的约束写在 `CLAUDE.md` 与下游托管区块里，模型执行 `/opsx:ff` 时未必读到那一段。
2. **相位 C 与 CLI 的载荷契约对不齐**：`specs` 的 `resolvedOutputPath` 是字面 glob；零 delta change 需 `skip_specs` 才过 `validate`；`dependencies` 的实际形状是 dict 列表；而 CLI 依赖图里 `specs` 与 `design` 互不依赖——`sdflow-spec` 用 C.2 的**写死超集表**绕过了最后这条。

CLI 1.7.0 提供了 project-local schema 通道：`schema fork` 带出全部 `instruction`（`schema init` 不带），PR #1405 修掉了「官方 skill 内嵌套路盖过 custom schema instruction」的缺陷，且 `requires` 边与 `instruction` 文案均**原样透传**到 `openspec instructions`（均经实测，锚见 `decision-memo.md` C1–C3）。

## Goals

- 把阶段一防绕过从指令层下沉到 schema 层（**提示层加强，非机械保证**）。
- 相位 C 照 CLI 实际返回的形状消费载荷：glob 写入目标、`skipped` 态、`dependencies` 形状。
- 让 CLI 依赖图反映真实流程，使 C.2 的写死超集表**从唯一路径降级为 fallback**（schema 未切换、或未来回退时仍靠它保证正确性，故 MUST NOT 删除该分支）。
- 上述能力随 bundle 下发到消费项目，且**迁移零回归**。

## Non-Goals

见 `proposal.md` 的 Non-Goals 小节（不改 `disable-model-invocation`、不做委派的机械保证、不做 fork 漂移检测门、不为 `skip_specs` 建机械门、不含 roadmap 的 P2/P3）。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)；架构级取舍见 [`openspec/adr/0034-stage-one-entry-descends-to-project-local-schema.md`](../../adr/0034-stage-one-entry-descends-to-project-local-schema.md)〔TG-23〕。

## 组件清单〔TG-14 · BASE-25〕

| 组件 | 位置 | 本次变更 |
|---|---|---|
| fork schema（bundle 权威源） | `sdflow-init/assets/schemas/sdflow-spec-driven/` | **新增**：`schema.yaml` + `templates/` |
| fork schema（本仓实例） | `openspec/schemas/sdflow-spec-driven/` | **新增**（由 bundle 下发产生） |
| 相位 C 协议 | `sdflow-spec/SKILL.md` C.2 / C.3 / C.4 / 终审 | **改**：glob 分支、剥离委派、`skipped` 态、断言收紧、超集表退役 |
| 安装器 | `sdflow-init/scripts/init.py` | **改**：版本门、迁移补写、schema 纳入 `copy_bundle` |
| config 模版 | `sdflow-init/assets/workflow/config.template.yaml` | **改**：`schema:` 指向 fork 名 |
| 本仓 config | `openspec/config.yaml` | **改**：同上 |

```
                      ┌──────────────────────────────┐
                      │  sdflow-init/assets/         │  ← bundle 权威源（唯一）
                      │   ├ workflow/config.template │
                      │   └ schemas/sdflow-spec-driven│
                      └───────────┬──────────────────┘
                       copy_bundle │ 整删重拷（同 tools/）
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
      ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
      │ 本仓 openspec/│   │ 下游项目 A    │   │ 下游项目 B    │
      │  schemas/ +   │   │  （同左）     │   │  （版本门未过 │
      │  config.yaml  │   │               │   │   → 保持内置）│
      └───────┬───────┘   └───────────────┘   └───────────────┘
              │ config.schema
              ▼
      ┌─────────────────┐  instructions --json   ┌──────────────────┐
      │  openspec CLI   │───────────────────────▶│ sdflow-spec 相位C│
      │  (≥1.7.0)       │   instruction/requires │  剥离委派→生成   │
      └─────────────────┘                        └──────────────────┘
              │ 同一份 instruction（含委派段）
              ▼
      ┌─────────────────┐
      │ /opsx:ff 等官方 │ ← 读到委派段 → 停 → 提示人敲 /sdflow-spec
      │ 入口（不剥离）  │
      └─────────────────┘
```

## 委派段的双读者时序〔TG-10 · 序列图〕

同一份 `instruction` 被两类读者消费，**差别只在剥离**：

```
官方入口路径                          sdflow-spec 相位 C 路径
─────────────                        ──────────────────────
/opsx:ff                             C.3 步骤1
   │                                    │
   ├─ instructions <a> --json           ├─ instructions <a> --json
   │     ↓ instruction =                │     ↓ 同一份载荷
   │   [delegation:start]               │
   │   🔴 STOP …敲 /sdflow-spec         ├─ 步骤2 前：**剥离** start..end 区块
   │   [delegation:end]                 │     ↓ 得到干净原文
   │   Create the proposal…             │
   │                                    ├─ 步骤3 路径净化（glob 分支）
   ├─ 读到 STOP → 停止                  ├─ 步骤4 原子写入
   └─ 提示人敲 /sdflow-spec ────────────▶ 由人发起（模型唤不起，见 ADR-0034）
```

🔴 **剥离发生在「应用载荷」之前**：若晚于步骤 2，委派文案已进入生成约束，相位 C 会自我劝退。

## 迁移与版本门的判定流〔TG-12 · 决策图〕

```
sdflow-init init/update
        │
        ▼
  openspec --version ≥ 1.7.0 ?
        │
   ┌────┴────┐
   │ 否      │ 是
   ▼         ▼
不铺 schema   扫 openspec/changes/*/
config 保持   （仅在途，archive/ 不扫）
spec-driven        │
fail-loud 一行     ▼
（降级=今天）  每个 change 有 .openspec.yaml ?
                   │
              ┌────┴────┐
              │ 否      │ 是
              ▼         ▼
        补写 schema:   跳过（已钉死）
        spec-driven          │
              └────┬─────────┘
                   ▼
          铺 schemas/ + 切 config.schema
             （🔴 顺序不可颠倒）
```

**为什么顺序不可颠倒**：补写方读的是「当前解析到的 schema」。先切 config 再补写，补进去的就是新 schema 名，等于把在途 change 钉在它从未使用过的 schema 上。

## 数据模型与生命周期〔TG-05 · BASE-24〕

**`schema.yaml` 的承重字段**（仅列本次触及的）：

| 字段 | 取值约束 | 依据 |
|---|---|---|
| `artifacts[].id` | MUST ∈ {`proposal`,`specs`,`design`,`tasks`}，不增不改 | C.3 路径净化 allowlist 硬编码（C14） |
| `artifacts[].generates` | MUST 与内置一致（`proposal.md` / `specs/**/*.md` / `design.md` / `tasks.md`） | 同上 |
| `artifacts[].requires` | `specs` → `[proposal, design]`；**`tasks` → `[proposal, design, specs]`**；其余保持 | E2（C2 实测透传） |

> 🔴 **两条边都要改，只改 `specs` 那条不足**：内置 `tasks.requires` 是 `[specs, design]`，**不含
> `proposal`**（实测）。若只改 `specs`，C.2 超集表仅退役一半——「tasks 读 proposal」仍得靠超集。
> 这是 D6「改 `requires` 边」的实现细化，非决策变更。
| `artifacts[].instruction` | 前置 `sdflow:delegation` 区块；design 段去掉条件语 | E1 / D6 |

**生命周期**：

```
fork（一次性，从 spec-driven 快照）
   │
   ├─▶ 分发：assets/ → copy_bundle → 各消费仓（整删重拷，下游只读）
   │
   ├─▶ 使用：config.schema 指向它 → new change 时把 schema 名钉进 change 的 .openspec.yaml
   │        （此后该 change 的解读不再受 config 变动影响——C13）
   │
   └─▶ 漂移：上游 spec-driven 更新 ⇒ 本 fork **不自动跟**，且无机械门提醒
            处置 = 人工重新 fork + 重打两处改动（记 roadmap 遗留 todo，本次不解决）
```

## 失败模式与可观测性〔TG-08 / TG-15 · BASE-06 / BASE-11〕

| # | 失败模式 | 触发条件 | 是否静默 | 处置 |
|---|---|---|---|---|
| F1 | 委派被官方入口忽略 | 模型未遵守 STOP 文案 | **静默** | 接受——退回今天的状态；MUST NOT 声称机械保证 |
| F2 | 相位 C 自我劝退 | 剥离未生效 / 标记不成对 | 显式（相位 C 停下） | 剥离步失败 ⇒ fail-closed 报 problem+cause+fix，MUST NOT 带着未剥离载荷继续 |
| F3 | 下游 CLI <1.7.0 委派失效 | 版本门缺失或误判 | **静默** | 版本门 fail-loud 一行；不铺即降级到今天 |
| F4 | 在途 change 被按新 schema 重解读 | 缺 `.openspec.yaml` 且先切了 config | **静默**（`blocked` 不报错，只是卡住） | 迁移补写 + 顺序约束 |
| F5 | 写入目标是 glob 字面量 | `resolvedOutputPath` 为 glob 而未走 glob 分支 | 半静默（可能造出含 `*` 的文件） | C.3 glob 分支 + 路径净化拒非常规名 |
| F6 | fork 漂移于上游 | 上游更新后未 rebase | **静默** | **本次不解决**（记 todo）；影响可控——停在旧版 = 今天的状态 |
| F7 | schema 目录被下游手改 | 违反托管纪律 | 静默 | `copy_bundle` 整删重拷会覆盖（与 `tools/` 同构，纪律一致） |

**可观测性**：版本门与迁移补写 MUST 各输出一行结论（铺/不铺、补写了几个 change），进入 `sdflow-init` 既有的动作汇总；相位 C 的剥离步在**未命中标记**时不报错（正常路径：内置 schema 无该标记），仅在**标记不成对**时 fail-closed。

## 协议文档套件 scope-check〔TG-25 · BASE-29〕

改一处契约牵连的**全部**落点（改任一项须同步核对本表）：

| 落点 | 依赖什么 | 若不同步的后果 |
|---|---|---|
| `sdflow-spec/SKILL.md` C.3 步骤 3 allowlist | artifact `generates` 路径字面量 | 写入被 fail-closed 拒绝 |
| `sdflow-spec/SKILL.md` C.2 强制阅读表 | schema 的 `requires` 边 | 超集表与真实依赖图分叉 |
| `sdflow-spec/SKILL.md` C.3 剥离步 | `sdflow:delegation` 标记字面量 | 委派段进入生成约束 → 自我劝退 |
| `config.template.yaml` 的 `schema:` | fork schema 名 | 下游铺了 schema 却不启用 |
| 本仓 `openspec/config.yaml` 的 `schema:` | 同上 | 本仓 dogfood 不生效 |
| `init.py` 的 `copy_bundle` 目录清单 | schema 目录名 | schema 不下发 / 不刷新 |
| `init.py` 版本门阈值 | CLI 版本 `1.7.0` | 委派在旧 CLI 上静默失效 |

## 边界合规声明〔TG-06 · D-6〕

fork schema 是**跨项目共享的契约定义**。边界纪律沿用 bundle 既有约定，不新造：
**权威源唯一** = `sdflow-init/assets/schemas/`；下游副本**只读**，改动一律回灌权威源再 `sdflow-init update` 下发；下游手改会被整删重拷覆盖（F7）。本 change **不**为 schema 引入独立于 bundle 的第二条分发路径。

## Risks / Trade-offs

- **依赖 experimental 接口**（CLI 自标）：接口变更会同时影响 fork 产出与 `schema validate`。缓解 = 回退路径明确（config 一行 + 删目录），且降级后行为等同今天。
- **收益账在拷问中变薄**：委派降为提示层、依赖图修密的实际收益缩为「少一段文字 + 概念一致」。已在 `decision-memo.md` D6 与 ADR-0034 中如实记录，人在知情下选择继续。
- **逆转成本随下游数量线性增长**：回滚需逐仓改回 config。
- **fork 漂移无机械门**：已知缺口，本次不解决。

## Migration Plan

1. 在 bundle 权威源产出 fork schema（`schema fork spec-driven sdflow-spec-driven` → 打两处改动 → `schema validate`）。
2. `init.py` 增版本门与迁移补写（**先补写、后切 config**）。
3. 本仓 dogfood：跑 `sdflow-init`，核对本仓 `openspec/changes/*/` 在途 change 的 status 快照**切换前后一致**。
4. `sdflow-spec/SKILL.md` 相位 C 改动（glob 分支、剥离、`skipped`、断言、超集表退役）。
5. 下游随下次 `sdflow-init update` 自然切换；未过版本门者保持现状。
   🔴 **[spec-review-amendment R1]**：`handle_config()` 现有 update 模式对 `config.yaml` 整段跳过（`init.py:311-316`），本步需补设计说明 `schema:` 键的机械改写机制——见 spec-review-report.md R1。
- **回滚**（**[spec-review-amendment R3]** 重写为无歧义顺序）：① 枚举所有在途 change 的 `.openspec.yaml` 中 `schema` 字段 ② 仍指向 fork 名的逐个改回 `spec-driven`（或等待归档） ③ 确认零引用后删 `openspec/schemas/` 目录 ④ 改 `config.yaml` 与 `config.template.yaml` 的 `schema:` 回 `spec-driven`。已归档的 change 不受影响。

## Open Questions

见 `proposal.md` 的开放问题表（Codex 宿主下委派是否成立 / `description` 字段是否进载荷 / fork 漂移如何发现）。

## Compliance

- **分析基准 1**：剥离、补写、版本门均确定性实现；`skip_specs`「够不够格」显式留为语义残余，不伪装机械门。
- **分析基准 5（无界语法不手搓）**：不解析 `schema.yaml` 语义——fork 与校验一律调 `openspec schema fork` / `schema validate` 让 CLI 自己回答；剥离只做**定界标记的字符串切分**（有界），MUST NOT 演化成解析 instruction 的 Markdown 结构。
- **通则③**：范围锚 roadmap P1，未扩到 P2/P3；相位 A 撤销了「不推下游」这一自加约束。
- **DOC-1**：正文即最终态，演进史在 `decision-memo.md` 与 ADR-0034。
- **术语纪律**：标记名不含 `gate`（CONTEXT.md 已将 gate 确立为正确性门专名）。
- **代码事实核验**：本文引用的 `SKILL.md:3`（`disable-model-invocation`）、C.3 allowlist、`init.py:581`（hook 为 copy 安装）均经实跑或直接读取核验，非凭记忆。
