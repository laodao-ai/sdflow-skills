# ROADMAP: streamline-workflow-automation 拆分执行〔grill-amendment〕

> **由来（OQ1 定案）**：本 change 跨 4 大块 / ~30 任务。grill Q6 确认**拆成 3 个 phased change 串行执行**——理由：块间是有向依赖 DAG（不是干净独立），B/C 都长在 A 造出的地基上；小 change 审查面小、能 dogfood、细回退点，且符合本设计 §8 自己鼓吹的"模块化 cleanup change"哲学。
>
> 本文件本身是这次拆分的**登记表**（同 `batches.md` 同构）——把 Phase B/C 当"已登记的 PLANNED change"记下，拆开后不会有哪一相被忘掉。

## 机制约定（拆法，非重跑设计）

- **`design.md` 是三相共享真相源**：全量 G/P/I/C/B 决策 + 3 个 ADR（`adr/0001`、`adr/0002`）+ `CONTEXT.md` 术语都留在此，A/B/C **反向引用、不复制**。
- **当前 change 目录先执行 Phase A**（沿用 umbrella 名 `streamline-workflow-automation`，A 是核心地基，名副其实）。`proposal.md`/`tasks.md` 暂保全量作 umbrella spec；`tasks.md` 各 § 已打 **【Phase A/B/C】** 标。
- **B/C 在 A merge 后各开新 change dir**，各自 proposal/tasks 从本目录相关 § 精炼迁入，**dogfood A 造出的新流水线**。现在**不建** B/C 目录（避免 openspec 里挂长期 stale 的 pending change，违背本设计"反无声堆积"洁癖）。

## 三相

| Phase | 待开 change 名 | 覆盖块 / tasks § | 依赖 | 交付自洽态 |
|---|---|---|---|---|
| **A 流水线骨架**（本 change） | `streamline-workflow-automation` | 块1 连续化(G/P) + 块2 提交(G4/G5) + 块7 bundle 源骨架；§1 §2 §3.1/3.2/3.4 §4 §7.1(骨架)/7.2/7.3/7.4 | 无（地基） | 工作流连续跑 + checkpoint 提交 + review UI 归位；**无** issues 池、**无** outside voice |
| **B issues 池** | `issues-pool-batch-mgmt`（暂名） | 块5(I1–I13) + sweep 步 3.3；§5 §3.3 | A 的 opsx-done hand-off 步就位 | 债务池 + 批次注册表 + reindex 状态同步就位 |
| **C 跨模型 voice** | `cross-model-outside-voice`（暂名） | 块6(C1–C7) + TG-26；§6 §7.5(TG-26) | A 的 spec/impl-review 编排器就位 | outside voice 接入 + HR-TG 判定 + fallback |

- **B、C 互不依赖**：先后随意，都只依赖 A。
- 待开 change 名为暂名，真开时定稿。

## 拆开必须守的 3 条约束（否则会踩 Q6 画的 DAG 坑）

1. **`workflow.md`（§7.1）被 A/B/C 各增量改一次**——A 写连续化骨架 + checkpoint/hand-off 引用；B 追加 sweep 步引用；C 追加 outside-voice 步引用。**A 不能一次写完**（不能引用还不存在的 sweep/voice 步）。
2. **验证（§8）与 INDEX 同步（§7.5）按相分摊**——每相各自验本相产物自洽（A 验 §8.1 决策落点无悬空；B 验 §8.2 reindex 一致；C 验 §8.3/8.4 fallback 冒烟 + gstack 边界），各相收尾同步 `openspec/INDEX.md` 本相规则变更（TG-26 属 C）。
3. **下游采纳（§9）不在任何相内**（各消费仓 routine）——但采纳节奏随之分相：A 后拉新流水线 bundle、B 后迁 issues 数据、C 后开 voice；各消费仓可分相采纳或等三相全落后一次性 `update`。

## 执行顺序

```
  Phase A（本 change）──merge──▶ Phase B ─┐
                                          ├─▶（B、C 先后随意，均依赖 A）
                              Phase C ────┘
```

先跑完 Phase A（本 change 现有 §1/§2/§3.1·3.2·3.4/§4/§7 骨架），merge 后再各开 B、C。

---

## Phase B/C 待迁任务与 Requirement（从本 change 移出，各自 change 开工时并入）

> 本 change 只交付 Phase A。以下 tasks §（沿用原 tasks.md 编号）+ spec Requirement 从本 change 移出、暂存此处，
> 待 Phase B/C 各开 change dir 时迁入其 `tasks.md` / spec delta。`design.md` 决策（I\*/C\*）仍是它们的共享真相源。

### Phase B — issues 池与批次管理（依赖 A 的 opsx-done hand-off 步）

tasks（原 §5 全 + §3.3 + §8.2 + §8.5）：

- [ ] §5.1 定义 issues 结构标准写进两 recorder skill "约定速查"段（唯一真相源）：`issues/{buglist,todolist}/` + 生成 `INDEX.md` + `batches.md`；bug 按日/todo 按月；命名；sweep 协议；批次生命周期〔I1/I13〕
- [ ] §5.2 recorder 表加 `批次` 列；源/批次/status 三维度分家；status 回归干净（不塞批次）〔I3〕
- [ ] §5.3 recorder 脚本：路径默认 `issues/{buglist,todolist}/`；scan 加 `--源/--批次/--open-ungrouped`；加 `triage`（赋批次+转 PROPOSED）〔I4/I9〕
- [ ] §5.4 `reindex` 命令 → 生成 `issues/INDEX.md`（禁手改；摊清 open×批次+标 DONE；同步批次状态：成员全 DONE→批次 DONE、不一致标出；**不做逾期催办**）〔I2/I12·grill-amendment〕
- [ ] §5.5 `issues/batches.md` 注册表 + `batch` 命令（add/set-status，跨 bug+todo，PLANNED→IN_PROGRESS→DONE，条目薄）〔I11〕
- [ ] §5.6 per-file 状态总览表保留；旧文件无 `批次` 列兼容留空〔I8〕
- [ ] §5.7 review UI（`workflow/tools/engine.js`、`review.html`）读 `issues/` 新路径（可选改读 INDEX.md）〔I10〕
- [ ] §3.3 opsx-done 加 **issues sweep 步**（`scan --status OPEN --源 {本change}` → 分诊入批次 → `batches.md`(PLANNED) → hand-off 引用）〔I5/I6〕；workflow.md **追加 sweep 步引用**（ROADMAP 约束1）
- [ ] §8.2 `reindex` 生成 INDEX.md 与 dated 文件 + batches.md 一致（表↔块↔INDEX 三处自检）
- [ ] §8.5 其它使用 laodao-skills 项目的迁移影响已确认（OQ3）

spec Requirement（并入 B 的 spec delta）：

- 债务池统一 issues 结构且 INDEX 只生成〔I1/I2〕
- 批次注册表 + reindex 状态同步〔I11/I12〕 —— ⚠️ 原 spec.md 该条标题为"批次注册表与**逾期主动催办**"，是 **Q5 前旧稿**（Q5 已删逾期催办）；迁入时**须改写为被动版**：批次注册表 + INDEX 被动摊清 + reindex 拿 item 池当 ground truth 同步批次状态，**不做逾期主动催办**。

### Phase C — 跨模型 outside voice（依赖 A 的 spec/impl-review 编排器）

tasks（原 §6 全 + §7.5 的 TG-26 部分 + §8.3 + §8.4）：

- [ ] §6.1 codex outside-voice **共享 helper**（自包含重写不引用 gstack）：preflight 探针 + exec 包装(5min) + "找漏"+文件系统边界 prompt 模板 + off-switch〔C1/C6〕
- [ ] §6.2 fallback 到原生 Task 子代理（非 ready/报错/超时；5min 封顶；非阻塞）〔C6〕
- [ ] §6.3 spec-review 接入：复用 autoplan 产出的 `gstack-review.md` outside-voice findings + **反静默守卫**（缺失/0 条→显式降级+回落自跑 codex）+ 命中 HR-TG 单开领域 cross-model〔C2/C7〕
- [ ] §6.4 impl-review 接入：自带 code outside voice + 命中 HR-TG 单开领域 cross-model〔C3〕
- [ ] §6.5 两 skill 规划镜头步加 **HR-TG 判定**（∩{TG-04/06/07/08/09/16/17/26}≠∅）+ 报告留痕〔C4〕
- [ ] §6.6 tension 适配：spec→报告决策登记、impl→自动裁决/defer；守 user sovereignty〔C5〕
- [ ] §6.7 `trigger-catalog.md`（bundle 源）新增 **TG-26 并发/共享可变状态**（回填四列 + 各消费方引用）〔C4〕
- [ ] §6.8 gstack 边界守恒：不动 autoplan/gstack review 原生 outside voice；自制机制只驱动自制 skill〔C7〕
- [ ] §7.5(TG-26 部分) 同步 laodao-skills `openspec/INDEX.md` 的 TG 计数 + trigger-catalog 引用（TG-26 加入后）
- [ ] §8.3 outside voice 在"无 codex/无 gstack"下回落 Claude 子代理、审查不中断（fallback 冒烟）
- [ ] §8.4 gstack 原生 outside voice 未被触碰（C7 边界核验）
- [ ] workflow.md **追加 outside-voice 步引用**（C 增量改，ROADMAP 约束1）

spec Requirement（并入 C 的 spec delta）：

- 跨模型 outside voice 默认开且可 fallback〔C1/C6/C7〕
- 高风险由 HR-TG 子集判定〔C4〕
