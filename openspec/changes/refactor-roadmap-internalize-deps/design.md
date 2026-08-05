# Design: refactor-roadmap-internalize-deps

## Context

现状（动机见 proposal.md · Why，不复述）：

- `sdflow-roadmap/SKILL.md` 635 行，讨论层为三分支路由（explore / wayfinder 长档 /
  office-hours 前置验证），其中 wayfinder 机械（footage 落盘、map 再入、tracker preflight、
  基线记录、checklist ④、陷阱 7）约 150+ 行，且携带宿主探测 + 三层降级路径。
- 同构参照 = `sdflow-spec/SKILL.md` 的三相位结构（A 澄清 → B 拷问 + 纪要增量落盘 → C 生成），
  其「B 轮数无上界 ⇒ 增量落盘收窄中断损失」的结构已在 change 生产路径实证。
- 正式契约面 = `openspec/specs/roadmap-planning/spec.md`（176 行），4 个 Requirement 锚定
  被删机制（承重约束 C2）。
- 决策与约束的单一源 = 本 change `decision-memo.md`（D1–D14 / C1–C10），本文不复述其内容。

约束：SKILL.md 重写 MUST 保留 `sdflow:principles` 托管块原样（`sync_principles.py --check`
是 setup.sh 门禁）；「考古层」在 DOC-1 语境另有语义，改名仅限 roadmap 语境（C5）；
bundle 文件改动受 dev checkout 纪律约束（改后重跑 setup.sh，经 `sdflow-init update` 推下游）。

## Goals / Non-Goals

**Goals（设计层）：**

- 新 SKILL.md 的相位协议与 sdflow-spec 逐节同构（起手判定 → 增量落盘 → 收敛定稿 → 生成 →
  收尾门），差异只保留在「产物形态」（三件套直写 vs 四件套经 CLI）与「无 ship gate ⇒ memo
  轻量化」两处（D4）。
- 所有被删机制在 spec delta 中成对处理（删机制 = 删/改对应 Requirement + Scenario），
  不留悬空 SHALL。
- 存量兼容零告警刷屏：requirements.md 兼容模式与 footage 冻结共用同一条款结构（至多一行提示）。

**Non-Goals（设计层，proposal Non-Goals 之外）：**

- 不为 memo 设计机械核验门（D4 已拍板轻量化，无 hash/schema 断言脚本）。
- 不设计存量 footage → memo 的自动转录工具（冻结即可，手工转录是重入时的例外路径）。

## 组件与依赖〔TG-14 · BASE-25〕

### 外部依赖图（before → after）

```
before:
  sdflow-roadmap ──┬─▶ /opsx:explore（分支 A）
                   ├─▶ wayfinder（分支 B）──┬─▶ /grilling（票内）
                   │                        ├─▶ /domain-modeling（票内）
                   │                        └─▶ openspec/matt/issue-tracker.md（preflight）
                   ├─▶ /office-hours（分支 C）
                   └─▶ /plan-eng-review · /autoplan（review 层）

after:
  （上游可选：/opsx:explore，想法未成形时先发散——非 skill 内部分支）
  sdflow-roadmap ──▶ /plan-eng-review · /autoplan（review 层，唯一保留的外部 skill 依赖）
```

### 改动组件清单

| 组件 | 动作 | 要点 |
|---|---|---|
| `sdflow-roadmap/SKILL.md` | 重写 | 三相位骨架，见下方「新 SKILL.md 骨架」 |
| `sdflow-roadmap/references/memo-template.md` | 重写 | B 相位纪要模板（头部包名+日期，承重约束/拍板决策小节） |
| `references/design|roadmap|task-log-template.md` | 术语改 | 商业化信号/生成/历史存档；结构不动 |
| `references/long-flow-skill-paradigm.md` | 局部改 | wayfinder 段落改历史注记 |
| `openspec/specs/roadmap-planning/spec.md` | delta | 4 ADDED / 3 MODIFIED / 3 REMOVED（机制替换与更名走删+增） |
| `openspec/matt/`（4 文件） | 删除 | D2；无其他运行时消费方（C1） |
| CLAUDE.md / AGENTS.md | 删区块 | matt 三区块 + roadmaps 目录描述行去 footage |
| `sdflow-init/assets/workflow/ff-generation-constraints.md` | 加注 | `wayfinder-resolved:` 前缀标 legacy（D10） |
| `sdflow-init/assets/workflow/workflow-history.md` | 追加 | 一条移除记录 |
| `openspec/CONTEXT.md` | 词条 | footage → 历史存档定义；新增商业化信号（D14） |
| `openspec/adr/` | 新增 | 讨论层内化与 matt 移除（D14） |
| `openspec/issues/`（T134） | 关闭 | `WONTDO` + `--reason`（D11；`OBSOLETE` 非合法状态码〔SR-3〕） |
| `docs/external-dependencies.md` | 更新 | 删 wayfinder/grilling/domain-modeling 节 |

### 新 SKILL.md 骨架

frontmatter（触发面重写，去 wayfinder）→ principles 托管块（原样）→ 定位与层级表（保留）→
三相位总览 + 判定留痕总则（三判定点重编号）→ 硬性规则 1–5（规则 3 改「历史存档」）→
产出模式（存量兼容 ×2 / 逃生舱 / create·continue·replan——判定前移至 B 起手）→
相位 A（澄清 + gate-0 + 商业化信号检查 → 三态路由，判定点①）→
**第零步：重入探测**（独立标题、置于三态路由之前，与 sdflow-spec 同构）〔SR-36〕→
相位 B（起手**三步** / 七维拷问与裁剪表 / 术语·ADR 提议制 / 增量落盘 / 停止条件 / 放弃清理）→
相位 C（生成三件套 / 近细远雾，保留）→ review 分档（判定点②，仅改术语）→
收尾 checklist 四项（判定点③）→ 命名规范 / 下游阶段实施（保留）→ 常见陷阱（删 7、改 3）→
CLAUDE.md 配合（去 footage 行）→ 参考模板。

## 三态路由决策图〔TG-12〕

```
入口（人触发 /sdflow-roadmap；想法未成形 ⇒ 建议先 opsx:explore 再回来）
  │
  ▼
相位 A：澄清 → gate-0 五项 + 商业化信号检查（两关独立，判定点①显式留痕）
  │
  ├─ gate-0 过 ∧ 无商业化信号 ──────────────▶ 相位 C 直接生成（此路径才在生成时建目录）
  ├─ gate-0 过 ∧ 商业化信号命中 ─▶ 相位 B（裁剪到维度①，Q3 作追问弹药）─▶ 相位 C
  └─ gate-0 未过 ──────────────▶ 相位 B（按信号裁剪七维）──────────────▶ 相位 C
                                    技术重构 → ②③④⑤⑦ 为主
                                    新产品/新项目 → ①②④⑤⑥⑦ 全跑
                                    商业化信号命中 → ① 加重（startup 味逼问）
```

七维 = ①需求真实性 ②现状分析 ③阶段划分压力测试 ④最小可行首阶段 ⑤架构路线对比
⑥术语/概念澄清 ⑦前提质疑（吸收映射见 proposal · What Changes；词表内联 SKILL.md，D13）。

## 包与相位状态机〔TG-09 · BASE-19〕

```
                    ┌────────────（放弃 ⇒ 删包目录；continue/replan 场景只删本次新增）
                    │
absent ──A收束，B起手：定名 + 生命周期判定(create/continue/replan) + 建目录 + 草稿memo──▶ B-draft
                                                                                        │
   （直接生成路径：absent ──gate-0过∧无信号──▶ 生成中(建目录) ──▶ 三件套就绪）          │拷问收敛
                                                                                        ▼
定稿包 ◀──收尾四项过（判定点③）── review+处置（判定点②）◀── 三件套就绪 ◀──C生成── memo定稿
```

- **重入**（异常转换）：新 session 探测 `openspec/roadmaps/*/memo.md` 存在且无定稿标记 ⇒
  呈现包 + memo 摘要，问人「继续 B / 新开」——续则回 B-draft，不静默复用。
- **既有包**（continue/replan）：生命周期判定在 B 起手完成（前移，D9），replan 先落
  task-log 重规划记录再动文件（现行条款保留）。

### 与 sdflow-spec 的实际分叉表〔spec-review-amendment SR-35〕

原文曾称「逐节同构，差异只保留在两处」——实测**至少五处**，成表如下（读过 sdflow-spec 的人按此对照，
避免带错误心智模型来用 roadmap）：

| # | 维度 | `sdflow-spec` | `sdflow-roadmap`（本设计） | 是否有意为之 |
|---|---|---|---|---|
| 1 | 产物形态 | 四件套经 OpenSpec CLI | 三件套直写 | ✅ 有意（规则 4） |
| 2 | memo 机械层 | frontmatter + `decision_hash`（身份 + 状态双职责） | 仅 `状态：DRAFT/FINAL` 一行状态位，无身份核验 | ✅ 有意（D4），**但状态位不可再砍**（SR-2） |
| 3 | B 相位可否跳过 | **不可跳过** | 三态路由第①态可跳过（gate-0 过 ∧ 无商业化信号） | ✅ 有意（D6） |
| 4 | 重入探测覆盖面 | 全部在途 change | 仅未定稿 memo——**不覆盖直接生成路径的半成品**（见 Risks） | ⚠️ 已知缺口 |
| 5 | 指令密度策略 | 5 个 `references/*.md` 按需加载，主文件只留骨架 | 骨架全内联 | ⚠️ 分叉，未论证 |
| 6 | 提议制防线层数 | B.6 惰性钩子 **+** B.7 收敛前逐条回扫（原文自述「B.6 漏掉的在此兜底」） | 仅一层（B 相位提议制） | ⚠️ 从两层退化为一层，未论证 |

## Decisions

本 change 的决策全文、依据与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)
（D1–D14，承重约束 C1–C10，三镜代价见其「三镜代价」节）。

## 失败模式表〔TG-08 · BASE-06 · spec-review-amendment SR-21〕

| 码路 / 状态 | 会出什么错 | 操作者看到什么 | 处置 | 有测? |
|---|---|---|---|---|
| B 起手建目录 | 目录建成、草稿 memo 写失败 | 下次重入探测扫不到（无 `状态：DRAFT` 行）⇒ 呈现为「已存在的空包」，走 continue/replan 分支 | 接受（见 decision-memo「接受的边角」） | N |
| B 增量落盘 | 两次落盘之间中断 | 已落盘内容无损，中间讨论丢 | 已声明「非零损失」 | N |
| 重入探测 | 命中 ≥2 个 `状态：DRAFT` 包 | 逐个呈现，操作者选其一；未选的原样保留 | spec 已定义（SR-2） | N |
| 重入探测 | memo 存在但无状态行（旧格式） | 视为未定稿，按 DRAFT 处置 | 兼容路径 | N |
| C 生成部分失败 | 三件套只写出 1-2 个 | ⚠️ **不被重入探测覆盖**（该路径 memo 可不存在） | **接受的已知缺口**，见 Risks | N |
| 两 session 同名并发 | 后写覆盖前写 | 无提示 | **接受**（无锁；概率低、git 可追溯、完美成本=引入锁） | N |
| B 中途放弃（create） | — | 先复述完整路径再删目录 | spec 已定义（SR-39） | N |
| B 中途放弃（continue/replan） | 「本次新增」不可判定 | 不自动删，task-log 记一行 | spec 已定义（SR-5） | N |
| review 依赖不可用 | 未审 | 「未审待恢复」+ 修复步骤，**阻塞收尾** | spec 已定义（SR-12） | N |
| 存量 footage 包续跑 | — | 至多一行冻结提示 | spec 已定义 | 6.4 fixture |
| 存量四件套包续跑 | — | 至多一行兼容提示 | spec 已定义 | N |
| 存量**缺件**包续跑 | 收尾 ② 引用完整性必然缺项 | 一行「缺件包，仅对现存文件核验」 | spec 已定义（SR-25） | 6.5 |
| 全局写入版本锚不匹配 | 条目被他人/并发改过 | 停下交操作者裁决 | spec 已定义（SR-11） | N |

## 可观测性〔TG-08 · BASE-11 · spec-review-amendment SR-21〕

本 skill 无服务、无日志/指标/追踪面。**它的全部可观测面 = 三个人读留痕点**，如实列出：

1. **判定点①②③的显式陈述行**（对话中单独一行 + 补记 task-log.md）——唯一能事后看出「路由怎么走的、
   裁剪选了哪几维、review 分了什么档、收尾四项过没过」的地方。
2. **memo.md 的增量落盘**——B 相位的过程可观测面；`[提议]`/`[确认]` 前缀行是全局写入的审计线索。
3. **task-log.md 的状态字段**（`ACTIVE` / `review-waived` / `未审待恢复`）+「Review 处置」小节。

**诚实边界**：以上三者**全部由执行 agent 自己写**，无任何机械捕获路径（本 skill 无脚本）。
⇒ 「判定有没有真做」在事后不可机械核验，只能靠留痕行是否在场做弱推断。这是**合法的残余划分**，
MUST NOT 被表述为「有可观测性保证」。

## 契约文档套件 scope-check 表〔TG-25 · BASE-29 · spec-review-amendment SR-22〕

> BASE-29 强调：**未列入**（清单里根本没有该文件）比**未完成**更危险——下次升级仍不会被想起。
> 故本表枚举**全套**，包括不改的，且不改必须给理由。

| 文件 | 本 change 是否改 | 不改的理由 |
|---|---|---|
| `sdflow-roadmap/SKILL.md` | ✓ 重写 | — |
| `references/memo-template.md` | ✓ 重写（**保留 `状态：DRAFT/FINAL` 行**） | — |
| `references/design-template.md` | ✓ 核对 | 实测零命中待改术语，仅核对不改 |
| `references/roadmap-template.md` | ✓ 术语改（`:27`/`:123` 两处「产品/商业野心信号」） | — |
| `references/task-log-template.md` | ✓ 术语改（`:86`「考古层」→「历史存档」） | — |
| `references/long-flow-skill-paradigm.md` | ✓ wayfinder 段改历史注记 | — |
| `openspec/specs/roadmap-planning/spec.md` | ✓ delta 覆盖 8 个 Requirement 中的 6 个 | 「design.md 需求与目标态伸缩头部章」与「新项目起步的架构先行指路」**不引用任何被删机制**，维持不动 |
| `openspec/matt/`（4 文件） | ✓ 整体删除（**待 Q1 拍板**） | — |
| `CLAUDE.md` / `AGENTS.md` | ✓ 删 matt 三区块（**待 Q1**） | — |
| `sdflow-init/assets/workflow/ff-generation-constraints.md` | ✓ 加 legacy 标注 | 前缀规则本身保留（D10：消费仓存量 footage 仍可能被溯源） |
| `sdflow-init/assets/workflow/workflow-history.md` | ✓ 追加一条 | — |
| **`sdflow-init/assets/workflow/config.template.yaml`** | ✓ **订正**〔SR-13〕 | 原为**未列入**——`:41`/`:51` 引用的「wayfinder→ff 衔接契约」章节已不存在；且它是消费仓 config 的**生成模版**，会注入每个新下游仓 |
| `openspec/CONTEXT.md` | ✓ **三处**词条（footage / 商业化信号 / ticket） | — |
| `openspec/INDEX.md` | ✓ `:52` 整句重写 | — |
| `openspec/adr/` | ✓ 新增 `0037-` | — |
| `openspec/issues/open/todo/T134.md` | ✓ 关 `WONTDO` | — |
| `docs/external-dependencies.md` | ✓ 删 §5 + 同步 §8 依赖图 | — |
| **`docs/sdflow-fable5/02-module-reference.md`** | ✓ **§4.6 更新**〔SR-16〕 | 原为**未列入**——`:6` 自述「本文是活文档（非冻结快照）」，不属 Non-Goals 豁免的历史文档 |
| `docs/drafts/roadmap-refactor-handoff.md` | ✓ 删除 | — |
| `docs/workflow-skills/*` | ✗ | D13：历史文档、非规则源，明确不追改 |
| `openspec/roadmaps/*`（存量包） | ✗ | 冻结条款覆盖；Non-Goals 明列「存量包结构不迁移」（T129 受控延后） |
| `.claude/settings.local.json` | ✗ | `"office-hours": "name-only"` 是本机工具授权，与本 skill 的 office-hours 分支无关 |
| `openspec/issues/`（T134 之外） | ✗ | 历史决策引用，非现役契约 |

## Risks / Trade-offs

- **[同串双语义误替换]**「考古层」（DOC-1 语境）被连带改名 → 改名操作按 C5 范围限定逐文件做，
  完成后 grep `考古层` 核对：`openspec/rules/`、BASE-30、T169、CLAUDE.md:183-184 必须原样。
- **[SKILL.md 重写破坏托管块]** principles 区块被动 → 重写以「区块外全重写、区块内零字节不动」
  执行，收尾跑 `python3 hack/sync_principles.py --check`（setup.sh 门禁同款）。
- **[bundle 窗口期]** assets/workflow 改动后未重跑 setup.sh ⇒ 全局 canonical 陈旧 →
  实施任务显式含「dev checkout 跑 `bash setup.sh`」步骤（CLAUDE.md 纪律）。
- **[存量包续跑回归]** 冻结条款写漏某接触点（如 checklist ③ 未覆盖 footage/）→ 以
  `issues-triage-2026-08` 包做一次续跑演练（Success Metrics 第 5 条）。
- **[下游分发链路——原风险模型是错的，已订正〔spec-review-amendment SR-14〕]**
  原文假设「bundle 改动经 `sdflow-init update` 推下游」，与实际机制不符：
  `sdflow-init/scripts/init.py:213` 明写「**默认只铺 `tools/` 子树**（规则经全局 canonical 解析，
  不复制进消费仓）；`full=True` 整 bundle 铺设**仅供 toolkit 源仓 `update --dev`**」
  ⇒ 消费仓跑 `update` **根本收不到** `ff-generation-constraints.md` / `workflow-history.md` /
  `config.template.yaml` 的改动；它们经 `~/.sdflow/workflow/`（软链到运行 checkout）解析，
  **与 skill symlink 走同一条通道** ⇒ 「skill 即时 vs bundle 手工」的非原子窗口**在默认拓扑下不存在**。
  **真正的风险面是另一个**：持有本地 `openspec/workflow/` 规则副本（pin）的消费仓——它遮蔽全局
  且 `update` 不刷新（`init.py:329` 的「反静默守卫·陈旧遮蔽」正为此而设）。这类仓会长期停在旧规则上。
  处置：前缀规则保留只加注（D10）两态兼容；pin 仓由既有陈旧遮蔽告警提示，本 change 不新增机制。
- **[直接生成路径的半成品无人认领]** gate-0 过 ∧ 无商业化信号的路径允许 memo 不存在，而重入探测
  只扫未定稿 memo ⇒ C 相位写到一半中断留下的残包不被任何机制发现（见失败模式表）。
  **接受**：概率低（C 相位是连续写盘、无人类往返）、影响可逆（残包可见、可手删）、
  完美成本 = 给直接生成路径也强制建 memo（与 D6「直接生成」的轻量意图冲突）。如实声明，不称已覆盖。
- **[七维 B 相位的摩擦增量未量化〔SR-40〕]** 新增七维拷问对「gate-0 未过」的请求是净增交互轮次，
  四件套未给出任何量化或体感评估。**接受**：目标态本就要求把 office-hours 的验证能力内化，
  摩擦是该能力的成本而非缺陷；但收尾时应回看一次实际轮次，若显著超预期则调裁剪基准。
- **[术语改名遗漏]** 「野心/结晶」残留 → 收尾 grep 不带 `--include` 全量扫（含 .py/.sh/.yml），
  历史文档（docs/、archive/）白名单排除。

## Migration Plan

实施顺序（同 tasks 相位展开）：

1. SKILL.md 重写 + references 模板（skill 面先成形）。
2. roadmap-planning spec delta（契约面跟上，与 1 同 change 内成对）。
3. matt 移除：删 `openspec/matt/` + CLAUDE.md/AGENTS.md 区块。
4. bundle 两文件（legacy 标注 + 演进记录）→ dev checkout 跑 `bash setup.sh`。
5. 治理收尾：ADR + CONTEXT.md 词条 + T134 关闭 + external-dependencies.md 更新 +
   INDEX.md 摘要行 + handoff 草稿删除。
6. 验证：全仓 pytest + sync_principles --check + 全量 grep 残留扫描 + 存量包续跑演练。

**回滚**：单分支未合并前 `git checkout main` 即净；合并后回滚 = revert merge commit
（matt 目录、CLAUDE.md 区块随 revert 恢复，无不可逆动作；全局 `~/.claude/skills/` 为
symlink，源恢复即恢复）。

## Open Questions

（无——可安全后置的未知项没有；全部决策已在相位 B 拍板。）

## Compliance

- 遵守 `openspec/rules/doc-authoring.md`（DOC-1）：本文正文只写目标态，演进过程在
  decision-memo（本 change 的过程件）。
- 遵守 `openspec/rules/premise-verification.md`：承重断言均有 C1–C10 证据锚。
- 遵守 CLAUDE.md 设计基准 1–5：无新增机械门（基准 1 的残余划分——收尾 checklist ① 的
  既有脚本门不动）；目标态导向（C6 三态路由不照 handoff 缩水）；无手搓解析器。
- 无豁免项。
