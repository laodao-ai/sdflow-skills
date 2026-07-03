# ROADMAP — laodao-skills 工作流演进登记表

> **活文档（living registry）**：登记从 `streamline-workflow-automation`（Phase A，已归档）派生的全部 phased / spawned change，及其状态、依赖、决策出处。
> 原始 3 相拆分（A/B/C）的详细「待迁任务与 Requirement」见归档 [changes/archive/2026-07-02-streamline-workflow-automation/ROADMAP.md](./changes/archive/2026-07-02-streamline-workflow-automation/ROADMAP.md)。
> 本文是其**前向续表**：承接 A/B/C + 登记后续 grill 中新派生的架构 change。

## 全部 change 登记

| change | 状态 | 覆盖 | 依赖 | 决策出处 |
|---|---|---|---|---|
| `streamline-workflow-automation`（Phase A） | ✅ 已归档 / merged | 三阶段连续化骨架 + 提交自动化 + bundle 骨架 + review UI 半归位(B1) | — | 归档 design G/P + `adr/0001`,`adr/0002` |
| `issues-pool-batch-mgmt`（Phase B） | 🔵 进行中（propose + grill） | 债务池 issues 结构 + 批次管理（I1–I13） | A | 归档 design §8 + 本 change design + grill B-Q1 |
| `cross-model-outside-voice`（Phase C） | ⚪ 待开 | 跨模型 outside voice（C1–C7）+ TG-26 | A | 归档 design §9 + 归档 ROADMAP「Phase C 待迁」 |
| `minimize-repo-footprint` | 🔵 进行中（propose + grill 收敛·2026-07-03） | 规则全局解析(resolver) + 消费仓最小副本 + checkpoint 全局 | A · `adr/0005` | **`adr/0003`**(+grill-amendment) · **`adr/0005`** |
| `opsx-ship-orchestrator` | ⚪ 待开（本轮 grill 新派生） | 阶段三窄编排 orchestrator（`opsx-ship`） | A（阶段三链就位） | **`adr/0004`** |
| `extract-sdflow-repo`（暂名） | ⚪ 待开（footprint grill 2026-07-03 派生） | 抽 workflow 集群（≈11 skill）入独立 repo **sdflow**（前缀 `sdflow-`、canonical `~/.sdflow/`、拆 setup、dev-runtime 落地）；laodao-skills 留 misc | 独立（用 footprint 定的 canonical） | footprint grill + sdflow 命名 |

> **待开的都暂不建目录**（避免 openspec 挂 stale pending change，同设计"反无声堆积"洁癖）；各自开工时再 materialize proposal/design/tasks/spec。B/C 互不依赖、与两个新 change 也互不依赖，均只依赖 A，先后随意。
> `minimize-repo-footprint` 已于 2026-07-03 materialize（explore 落骨架 → proposal/design/tasks/spec 就位，分支 `feat/minimize-repo-footprint`），进入 propose 阶段。

---

## 本轮 grill 新派生的两个 change（详情）

### `minimize-repo-footprint`（见 `adr/0003`）

把 opsx-project-init 的部署从"整 bundle 复制进消费仓"改为**按内容性质分层**，减少消费仓污染：

- **规则**（`workflow/*.md` + `spec-checklists/` + `code-checklists/`，≈28 文件）→ **全局唯一**，skills 全局解析、消费仓不复制。
- **review UI 机械**（`tools/` + `serve.sh` + `review.html`，≈5 文件）→ **留 `openspec/` 最小**（服务器根=openspec/ 约束，不落地即 404）。
- **`hack/checkpoint-commit.sh`** → **全局**（同 ff0-branch-guard / change-review-stub 两个全局 hook；顺带根治 `core.fileMode=false` 的 exec 位坑）。
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
- `CONTEXT.md` 新术语：**设计层连续 vs 编排层连续**（区分"无强制中断"与"无手动逐步触发"）；**终态集**（批次完成判据，B-Q1）；**开发/运行 checkout**（dev/release 物理隔，`adr/0005`）；**反静默守卫** 已扩到"全局 bundle 解析 + 陈旧遮蔽"（footprint grill）
