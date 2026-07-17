# ROADMAP — sdflow-skills 工作流演进登记表

> **活文档（living registry）**：登记从 `streamline-workflow-automation`（Phase A，已归档）派生的全部 phased / spawned change，及其状态、依赖、决策出处。
> 原始 3 相拆分（A/B/C）的详细「待迁任务与 Requirement」见归档 [changes/archive/2026-07-02-streamline-workflow-automation/ROADMAP.md](./changes/archive/2026-07-02-streamline-workflow-automation/ROADMAP.md)。
> 本文是其**前向续表**：承接 A/B/C + 登记后续 grill 中新派生的架构 change。

## 全部 change 登记

| change | 状态 | 覆盖 | 依赖 | 决策出处 |
|---|---|---|---|---|
| `streamline-workflow-automation`（Phase A） | ✅ 已归档 / merged | 三阶段连续化骨架 + 提交自动化 + bundle 骨架 + review UI 半归位(B1) | — | 归档 design G/P + `adr/0001`,`adr/0002` |
| `issues-pool-batch-mgmt`（Phase B） | ✅ 已归档 / merged | 债务池 issues 结构 + 批次管理（I1–I13） | A | 归档 design §8 + 本 change design + grill B-Q1 |
| `cross-model-outside-voice`（Phase C） | ✅ 已归档 / merged | 跨模型 outside voice（C1–C7）+ TG-26 + **T25 前置**（Step1 autoplan「模拟执行」修复——§6.3 要复用 autoplan 产物，前提是产物为真） | A | 归档 design §9 + 归档 ROADMAP「Phase C 待迁」+ `adr/0006`（混编机队下天然可得）+ 2026-07-04 explore（T25 并入） |
| `minimize-repo-footprint` | ✅ 已归档 / merged | 规则全局解析(resolver **脚本化**) + 消费仓最小副本 + checkpoint 全局 | A · `adr/0005` | **`adr/0003`**(+grill-amendment) · **`adr/0005`** · **`adr/0006`**(resolver 脚本化) |
| `sdflow-ship`（曾用名 `opsx-ship-orchestrator`） | ✅ 已归档 / merged | 阶段三窄编排 orchestrator（`sdflow-ship`） | A（阶段三链就位） | **`adr/0004`** + `adr/0006`（编排 prose→结构，弱主模型漏步兜底） |
| `sdflow-rebrand`（曾用名 `extract-sdflow-repo`） | ✅ 已归档 / merged | rescope/supersede：拆库半已发生（repo 已迁 `laodao-ai/sdflow-skills`，misc skills 留守 laodao-skills），剩余 scope = 品牌收拢——全量 `sdflow-` 前缀改名（9 改 3 留）+ 品牌字符串清扫（`VERSION`/marker/setup 输出） | 独立（用 footprint 定的 canonical） | footprint grill + sdflow 命名 + `adr/0007` |
| `workflow-metrics-loop` | ✅ 已归档 / merged | `lens-metric v1` 评审价值锚 + 聚合器；后续由 `sdflow-retro` 生成成本×价值报告，为镜子取舍供数、不自动裁决 | 独立 | archive `2026-07-05-workflow-metrics-loop` + `2026-07-06-sdflow-retro` |

> **2026-07-16 对账**：本表登记的 A/B/C 与派生 change 均已归档；新的实施优先级以 `openspec/roadmaps/` 和 `openspec/issues/INDEX.md` 为准，避免继续从本历史续表推断下一棒。
> 〔2026-07-03 adr/0006 调序〕原"先后随意"改为**建议序**：`minimize-repo-footprint` → `opsx-ship-orchestrator` → Phase C。依据 = 执行机队锚定（opus/sonnet/gpt-5.5，非开发时模型）：opsx-ship 把 15 步编排从 prose 固化进结构（弱主模型漏步兜底）、Phase C 在混编机队下天然可得且更必要——两者从"锦上添花"升为"弱模型兜底机制"。
> 〔2026-07-03 整体评估补〕`workflow-metrics-loop` 独立于建议序，随时可插（只读报告产物）；opsx-ship materialize 时须把 adr/0006 约束(b)写进其 proposal 硬约束——**步序推进用确定性台账（state 文件/脚本判"下一步/上步产物在否"），SKILL.md prose 只管每步内部判断**（否则是用 prose 协议治 prose 协议）。相关债：T9（"非平凡"硬定义）/ T10（阶段三自动选推荐判据，随 opsx-ship 落）/ T11（档位映射认领，opsx-ship 首选）。
> `minimize-repo-footprint` 已于 2026-07-03 materialize（explore 落骨架 → proposal/design/tasks/spec 就位，分支 `feat/minimize-repo-footprint`），进入 propose 阶段。
> `opsx-ship-orchestrator` 已改名并归档为 `sdflow-ship`；Phase C `cross-model-outside-voice` 也已于 2026-07-04 归档，T25 随其 scope 闭合。

---

## 本轮 grill 新派生的两个 change（详情）

### `minimize-repo-footprint`（见 `adr/0003`）

把 opsx-project-init 的部署从"整 bundle 复制进消费仓"改为**按内容性质分层**，减少消费仓污染：

- **规则**（`workflow/*.md` + `spec-checklists/` + `code-checklists/`，≈28 文件）→ **全局唯一**，skills 全局解析、消费仓不复制。
- **review UI 机械**（`tools/` + `serve.sh` + `review.html`，≈5 文件）→ **留 `openspec/` 最小**（服务器根=openspec/ 约束，不落地即 404）。
- **`hack/checkpoint-commit.sh`** → **全局**（同 ff0-branch-guard 全局 hook；顺带根治 `core.fileMode=false` 的 exec 位坑）。
- **`config.yaml` / `changes/` / `specs/`** → 仓内（本体）。
- **明确接受的代价**：消费仓失去按仓 pin 工作流规则（跟随全局 HEAD）。
- **未决（留其 design 定）**：全局 bundle 路径解析机制——固定 `~/.skills/laodao-skills/…` 约定 vs env var；建议默认约定 + env var 覆盖。
>
> **grill 收敛（2026-07-03）**——上面若干点已被逐决策死磕修正（详见 change design.md + `adr/0003` grill-amendment + `adr/0005`）：①**撤提根**（canonical 间接层已解耦，"唯一权威源"约定不动）；②canonical = Unix 软链 `~/.sdflow/workflow` / Windows 指针 `~/.sdflow/workflow-path` + 回落链（原"未决路径机制"已定）；③checkpoint 全局家 = agent 中立 `~/.sdflow/hack/`、**非** `~/.claude/hooks`（修正"同两个 hook"假类比）；④dev/release 靠**两个物理 checkout** 隔（`adr/0005`）；⑤ workflow 集群抽为独立 repo **sdflow**（前缀 `sdflow-`、canonical `~/.sdflow/`，dev/runtime 两 checkout）= 派生 change `extract-sdflow-repo`；laodao-skills 留 misc grab-bag。

### `opsx-ship-orchestrator`（见 `adr/0004`）

补**编排层连续**（设计层连续 Phase A 已达成）：新 skill `opsx-ship`（暂名，备选 opsx-deliver / opsx-run），**窄 scope = 阶段三 5.5→9 一次驱动到 merge**。

- **边界**：不跨 grill（step 3）/ 设计门（step 5）两个人类点；orchestrator 只从**过设计门后**起跑。
- **尊重子步门禁**：`opsx-done` verify FAIL / `impl-review` 真 blocker → 停并上抛；仅"能修自动修 / 拿不准 defer"才继续（防假✅）。
- **meta-orchestrator**：chain `embedded-test-sop`(条件)→`writing-plans`(→subagent-dev)→`impl-review`→`opsx-done`，**不取代**它们；`workflow.md` 阶段三 step 表即其内部序列。

---

## 相关决策记录（ADR）与术语

- `adr/0003-deploy-footprint-global-rules-minimal-repo-copy.md` — 部署 footprint 分层（+grill-amendment 2026-07-03：撤提根 / canonical 软链+指针 / checkpoint 修正）
- `adr/0004-opsx-ship-stage3-orchestrator.md` — opsx-ship 阶段三窄编排
- `adr/0005-dev-runtime-checkout-split.md` — 开发/运行 checkout 分离（toolkit 自身 dev/release 靠两 clone 物理隔）
- `adr/0006-execution-model-baseline-fleet-anchored.md` — 执行模型能力基线锚定机队（opus/sonnet/gpt-5.5，非开发时模型）：prose 协议脚本化硬约束、强/弱措辞相对机队、resolver 脚本化 + ROADMAP 调序的依据
- `adr/0007-sdflow-naming-consolidation.md` — sdflow 品牌收拢命名决策：全量 `sdflow-` 前缀 + 三保留名单（`embedded-test-sop`/`openspec-upgrade`/`sdflow-upgrade`）；已评估未选 = plugin 冒号命名空间（Codex 无 plugin）、半量改名（品牌分裂）、留旧名 stub（no-stub 维持）
- `CONTEXT.md` 新术语：**设计层连续 vs 编排层连续**（区分"无强制中断"与"无手动逐步触发"）；**终态集**（批次完成判据，B-Q1）；**开发/运行 checkout**（dev/release 物理隔，`adr/0005`）；**反静默守卫** 已扩到"全局 bundle 解析 + 陈旧遮蔽"（footprint grill）
