# Design: add-sdflow-architecture

## Context

设计方法论已在 `docs/sad/02-sad-skill-design.md` 收敛（自包含蓝本：目标与范围校准 §0、十节骨架 §2、质量判据 S1–S11 §3、人机分工 §4、五步流程与拆分规则集 R1–R11 §5、五组件架构 §6、文档生命周期 §7、生态位与端到端序列 §8；被否方案附录 A1–A3）。本 design 不复述蓝本结论，聚焦**实现层**决策：文件格式、脚本契约、状态机落地、失败处置。设计拍定过程另见 `docs/sad/00/01`（讨论考古层）。

利益相关方：操作者（人门拍板）、消费仓（SAD 落位与分家写入）、运行 checkout（安装分发）、下游 OpenSpec 管线（骨架 proposal 交棒）。

## Goals / Non-Goals

**Goals:**
- 五组件落地：SKILL.md 五步流程 + references 六件 + scripts 两件（外加共享 schema 常量）+ tests
- 机械层 v1 最小集可断言、fail-closed、输出诚实（结构通过 ≠ 语义核验）
- 状态机由脚本独占迁移权，反假绿锁 draft 生效

**Non-Goals:**（proposal Non-Goals 1–5 的实现层重申，均带可证伪假设，此处不复述）S1–S11 完整投影 / L2 环节 / 共变回检仪器 / roadmap design 瘦身 / brownfield 迁移编排。

## Decisions（决策记录，BASE-12）

方法论级决策（D1–D5、生态位、生命周期）已在蓝本拍定并含被否方案（`docs/sad/02` 附录 A1–A3），此处只登记**实现级新决策**：

| # | 决策 | 理由 | 被否备选 |
|---|---|---|---|
| DEC-1 | **共享 schema 常量模块 `scripts/sad_schema.py`**：frontmatter 字段名、status/成熟度枚举、十节标题锚、`[假设-N]` 标记正则，scaffold 与 lint 共同 import | SAD 格式是 scaffold（写）/lint（读）双方契约，硬编码两份必漂移（adr/0011 精神） | 各自硬编码（漂移实证先例多）；JSON schema 文件（Python 常量已够，避免引解析依赖） |
| DEC-2 | **frontmatter 用 YAML + 行锚定 fence-aware 解析** | 生态先例：gate 子串检测假阳教训——解析一律行锚定 + fence 感知，防正文示例代码误命中 | naive 子串/正则全文扫（已被生态否决） |
| DEC-3 | **假设双向锚**：正文 `[假设-N]` 内联标记 + SAD 附录假设清单表（编号/位置/内容/依据/处置∈{接受, 待校准, 未处置}）；lint 断言「内联标记数 == 清单行数 且 无未处置」 | 只有内联标记无法承载处置状态；只有清单无法定位正文位置；双向锚可机械对账 | 仅内联富标记 `[假设\|依据\|处置]`（行内过载难读）；仅清单（正文定位丢失） |
| DEC-4 | **状态迁移只由 `sad_scaffold.py` 执行**，模型/人不得手改 frontmatter 跳级；scaffold 迁移前重跑锁 draft 前置检查 | 状态是机械可守的不变量，交模型自觉必漂移（机械化优先） | SKILL 指令约束模型手改（散文约束弱形态） |
| DEC-5 | **lint 通过码 `structure-ok-SEMANTICS-UNCHECKED`**；坏输入（文件缺失/frontmatter 不可解析）fail-closed 非零 + stderr，与正常 reason_code 判定物理区分 | adr/0018 机械校验器输出诚实：防「lint 绿」被误读为「内容已审」 | 裸 `ok`/退出码 0（假绿高危） |
| DEC-6 | **升档多镜 = skill 自编排镜阵**（按自带 `review-lenses.md` fan-out fresh 子代理 + 对抗镜）；**outside voice 镜经自制 `~/.sdflow/hack/outside-voice.sh`** 调用（preflight 探测 → render-prompt 不可信上下文硬分隔 + secret 扫描 → `exec --timeout 600`；契约单一源 = 脚本头注释）〔grill-amendment 修正原「复用 spec-review 机制」表述〕 | 镜单是为 SAD 量身的资产（语义残余即镜位）；sdflow-spec-review 锚定 change 四件套，硬套则领域段空转、产物语义错配；outside-voice.sh 自包含零 gstack 内部依赖，自带探测/超时/密钥防出境 | 整体调用 sdflow-spec-review（工具错配）；skill 内裸调 codex CLI（绕开 secret 扫描与超时硬化，重复造轮） |
| DEC-7 | **消费仓 preflight fail-closed**：无 `openspec/` 布局 → 显式指引先跑 `sdflow-init`，MUST NOT 自造半套布局 | 半套布局是后续所有 sdflow skill 的隐性坑（dogfood 盲区先例） | 静默降级只写 SAD 文件（布局漂移） |
| DEC-8 | **文件写入一律原子写**（temp + rename） | 防半写损坏（生态既有纪律） | 非原子直接写 |
| DEC-9 | **SAD 产出直写 `openspec/architecture/`，不经 change 壳承载**〔grill-amendment〕 | SAD 是规划 live 文档非代码变更，delta/verify/archive 语义不适用；质量门内建（lint+冷走查+升档+人门），change 壳双重门禁纯增摩擦；先例：sdflow-roadmap 规则 4「产出直写，不经变更壳」（旧版变更壳已实证废弃）；第一个 change 壳 = 人拍板开的骨架 change | 用 openspec change 承载 SAD 生成过程（roadmap 已踩过并废弃的坑） |
| DEC-10 | **交棒物 = SAD 内嵌「骨架切片建议」节，非独立草案文件**〔grill-amendment〕 | 先例：ff-generation-constraints「切片建议」节（消费语义 = 建议非契约）；穿越点**引用** §5 条目不复述（独立文件必复述、必失鲜）；少一个文件；骨架回写 validated 时移除该节，live 层保持当前态 | 独立 `skeleton-change-draft.md` 文件（复述失鲜 + 多一文件）；skill 代开骨架 change（越权工作流决策，打穿「直写规划层 / 管线实施层」分界） |
| DEC-11 | **判定留痕落 `openspec/architecture/sad-log.md`（append-only，scaffold 追加）；走查矩阵内嵌 SAD 第 6 节正文，不生成独立走查报告**〔grill-amendment〕 | 对话不持久、commit 时机归用户（skill 不代 commit），留痕需显式文件；sad-log 角色类比 roadmap 的 task-log（DID），使消费仓三层完整成型：sad.md（live）+ adr/（decision）+ sad-log.md & git（history）；矩阵本就是第 6 节的内容形态，洞修复后即当前态 | 留痕靠 git commit message（时机不可控必丢）；留痕写进 SAD 本体（历史污染 live 层）；独立走查 report 文件（SAD 走查结果直接改文档本体，report 无消费场景） |
| DEC-12 | **收尾三细则**〔grill-amendment〕：①模型档位——主 session 与冷走查子代理**均强档**，无可下放弱档的步（机械活已全部脚本化，scaffold/lint 零模型；SKILL.md 记一行引 model-tiers.md）②lint 假设计数**以正文实扫为准**，frontmatter `assumptions_open` 仅为 scaffold 缓存，两者不一致 → 独立 mismatch reason_code ③`sad_schema.py` 节标题锚 v1 **中文单语** | ①冷层承重实证 + 带门禁步勿弱档教训 ②正文是真相、缓存不可采信 ③生态与消费仓全中文，为不存在的英文场景配双语锚违反刚好够 | ①冷走查降弱档（假绿放行）②采信 frontmatter 或静默取其一 ③双语锚 |

> **outside voice 工具链真相源注记〔grill-amendment〕**：wrapper 真相源 = `sdflow-init/assets/hack/outside-voice.sh`，由 setup.sh **拷贝**至 `~/.sdflow/hack/`（运行时调用路径；非 symlink，改真相源须重跑 setup）。配套三前置校验器 `outside_voice_guard.py` 真相源 = `sdflow-init/assets/workflow/tools/`（消费仓经 `resolve-workflow.sh` 解析 `$RULES_ROOT/tools/`）——其职责是**复用既有 outside-voice 产物**时的来源/新鲜度/结构校验；v1 每次升档均为新调用、无产物复用，guard 不进默认路径；未来若缓存/复用走查产物，SHALL 以 guard 校验后方可复用。

## 数据模型与生命周期（BASE-24，TG-05）

**SAD frontmatter（machine-readable，schema 单一源 = `sad_schema.py`）**：

```yaml
---
sad_status: draft            # draft | skeleton-ready | validated | frozen
facts:                       # 事实三问回答状态（锁 draft 的判据）
  positioning: answered      # answered | missing
  external_systems: answered
  hard_constraints: missing
assumptions_open: 2          # 未处置假设数（scaffold 聚合回写，lint 复核）
---
```

**facts 字段信任边界〔grill-amendment〕**：`answered` 语义 = **「已记录到人的回答」**（scaffold 经显式参数 `--fact <key>=answered` 写入，SKILL 指令要求发生在人实际作答之后）**≠「回答质量已核验」**——质量核验归人门（议程固定含「三问回答复核」条）；lint 只查枚举与 frontmatter 一致性。机械/语义切分：有无记录到回答 = 确定性信号（机械），回答是否真实充分 = 无确定性信号（语义归人）。

**contract 成熟度标签**（SAD 第 5 节每条 contract 行内）：`planned | draft | validated | frozen`——`planned` 为 R10 全景占位（后期阶段子系统），`validated` 由骨架 change 落地后回写，`frozen` 改动须关联新 ADR。

**假设标记**：正文 `[假设-N]` ↔ 附录清单行（DEC-3）。**数值溯源**：数值后缀 `〔人拍〕`/`〔推荐待校准〕`（v1 由 SKILL 指令要求 + 走查核对，lint 不查——目标态再机械化）。

**生命周期**：SAD = live 层永远当前态；决策进 `openspec/adr/`（不可变 + supersession）；历史归 git。「骨架切片建议」节是 SAD **唯一的暂态节**——skeleton-ready 时由 scaffold 写入、骨架 change 回写 validated 时移除（DEC-10）。

## 状态机图（BASE-19，TG-09，含异常转换）

```
             事实三问齐 + 假设无「未处置」
  ┌───────┐ ──────────────────────────────▶ ┌──────────────────┐
  │ draft │                                  │  skeleton-ready  │──── 交棒：骨架 proposal
  └───────┘ ◀────────────────────────────── └──────────────────┘
      ▲       异常回落：事实答案被推翻 /              │ 骨架 change 落地，
      │       骨架否决 contract 大面积                │ contract 逐条 draft→validated
      │       （scaffold 记回落原因行）               ▼
      │                                     ┌──────────────────┐
      │                                     │    validated     │
      │                                     └──────────────────┘
      │                                              │ 逐条 contract 显式冻结
      │                                              ▼
      │                                     ┌──────────────────┐
      └──── 任何非法跳级：scaffold 拒绝 ──── │  frozen(per-合约) │
            （如 draft→validated）           └──────────────────┘
  违规检测（非状态转换）：frozen contract 有 diff 但无新 ADR 关联 → lint 报错
```

## 序列图（TG-10，含分档决策点 TG-12）

```
操作者        主session(skill)      sad_scaffold      冷走查子代理        lint         openspec管线
  │  简单需求      │                      │                │              │               │
  │──────────────▶│ ①事实三问            │                │              │               │
  │◀──三问────────│                      │                │              │               │
  │──答(可缺)────▶│──scaffold 建骨架────▶│ 原子写+状态draft │              │               │
  │               │ ②规则集跑候选(R1–R11+AP自检)           │              │               │
  │               │   ├─无分歧→声明行「单方案直出」         │              │               │
  │◀─候选+场景化二选一(③挂产物拍板)──────│                │              │               │
  │──拍板────────▶│ ④派冷走查───────────────────────────▶│ 场景×子系统×contract 矩阵      │
  │               │   ├─升档判定(信号表,显式一行)：命中→spec-review 多镜(codex 可用→outside voice 镜) │
  │               │◀──矩阵+洞───────────────────────────│              │               │
  │               │──lint──────────────────────────────────────────────▶│ reason_code   │
  │               │──scaffold 迁移 skeleton-ready(锁draft前置复检)─▶│    │               │
  │               │ ⑤交棒：SAD 内嵌「骨架切片建议」节──────────────────────────────────────────▶│
```

## 组件清单（BASE-25，TG-14）与依赖图

| 组件 | 职责 | 依赖 |
|---|---|---|
| `SKILL.md` | 五步流程编排 + 分工 rule + 门禁指令 | references 全部、scripts |
| `references/sad-template.md` | 十节骨架 + 标记语法 + frontmatter 骨架 | sad_schema 锚（节标题一致） |
| `references/decomposition-rules.md` | R1–R11 + AP1–AP4 | — |
| `references/quality-criteria.md` | S1–S11 + 拆解表（**真相源**） | — |
| `references/review-lenses.md` | 镜单（投影，条目带 S 编号） | quality-criteria |
| `references/intake-questionnaire.md` | 事实三问 + 追问提示 | — |
| `references/checklists/` | 横切模板/质量属性候选库/外部依赖典型集/R4 变化类别表 | — |
| `scripts/sad_schema.py` | 格式常量单一源（DEC-1） | — |
| `scripts/sad_scaffold.py` | 脚手架/状态机迁移/标记聚合 | sad_schema |
| `scripts/sad_lint.py` | v1 结构断言 + reason_code | sad_schema |
| `tests/` | 两脚本 pytest（正/负路径） | scripts |

```
SKILL.md ─▶ intake-questionnaire ─▶ sad_scaffold ─▶ sad-template
    │                                    │  ▲
    ├─▶ decomposition-rules              ▼  │ import
    ├─▶ review-lenses ◀─S编号─ quality-criteria
    └─▶ sad_lint ──import──▶ sad_schema ◀──┘
```

## 失败模式表（BASE-06，TG-08）+ 可观测性（BASE-11，TG-15）

| 失败模式 | 表现 | 处置（D-4：超时/回滚） |
|---|---|---|
| codex 不可用/超时/密钥命中 | 升档 outside voice 不可用 | `outside-voice.sh preflight` 非 ready → 降级；`exec --timeout 600` 超时（退出 124）→ 降级；secret-hit（退出 3）→ **拒发并报人工**；降级一律 Claude 镜 + **显式提示不静默**；read-only ephemeral 无回滚需求（D-4 声明） |
| codex 输出不可解析 | findings 段缺失 | 复用 `outside-voice-reuse-guard` 三前置校验（fail-closed 到 reason_code） |
| scaffold 写入中断 | 半写文件 | 原子写 temp+rename（DEC-8），中断只留 temp 可清理 |
| lint 坏输入 | frontmatter 损坏/文件缺失 | fail-closed 非零 + `[sad_lint] FAIL:` stderr，与正常判定物理区分（DEC-5） |
| 冷走查子代理失败 | 无矩阵产出 | 重派一次；再失败 → 显式报告缺口，MUST NOT 无走查静默过人门 |
| 消费仓无 openspec 布局 | 分家无 home | preflight fail-closed → 指引 `sdflow-init`（DEC-7） |
| SAD 单例已存在 | 二次触发 | continue/replan 显式区分，MUST NOT 静默覆盖（spec 需求） |

**可观测性**：全部关键判定落 grep 可及的留痕行，**家 = `openspec/architecture/sad-log.md`**（append-only，scaffold 追加；DEC-11）——「判据无分歧，单方案直出」/ 升档判定一行 / 降级提示一行 / scaffold 状态迁移记录（含回落原因）/ 走查轮次与洞数；lint reason_code 走进程输出。无需额外日志设施。

## 协议文档套件 scope-check 表（BASE-29，TG-25）

quality-criteria 为真相源、三处投影带 S 编号引用，改动牵连核对：

| 改动点 | 牵连文件 | 同步核对方式 |
|---|---|---|
| S 条目增/删/改 | review-lenses.md（S 编号引用）、sad_lint.py（注释 S 编号）、SKILL.md 人门清单 | v1：tasks 内人工 checklist；目标态：S 编号引用扫描脚本 |
| sad-template 节结构变更 | sad_schema.py 节标题锚、sad_lint 节断言、tests | 改模板必跑 tests（节锚常量共享，DEC-1 兜底） |
| frontmatter 字段/枚举变更 | sad_schema.py（唯一改点）→ scaffold/lint 自动继承 | tests 覆盖枚举正负路径 |
| 标记语法变更（`[假设-N]`） | sad_schema.py 正则（唯一改点）+ sad-template 示例 | tests + 模板示例同步 |

## Risks / Trade-offs

- [十节模版仍显重、吓退轻量项目] → §0.3 深度分层已内嵌模版注释（低风险节一句话/N/A 合法 + 留痕），试点观察上手摩擦
- [AI 候选仍溜进反模式] → AP 自检强制前置 + 人门对比面；残余靠冷走查 S3 镜
- [SAD 与 roadmap design.md 双写] → 职责已切（HOW vs WHY）；试点若现双写即触发 Non-Goal 4 的瘦身 change
- [「lint 绿」误读为全绿] → DEC-5 输出诚实 + SKILL 指令含信任边界声明行（师承 review_disposition_check 先例）
- [骨架切片建议质量依赖 SAD 第 5/6 节质量] → 建议节含穿越点引用硬槽（引用 §5 条目），缺穿越点即结构性可见

## Migration Plan

无数据迁移。发布 = merge → 运行 checkout `git pull` + **立即** `setup.sh`（新增顶层 skill 反向窗口纪律）→ README Skills 列表随本 change 提交。回滚 = 运行 checkout 检出上一 good commit + 重跑 setup.sh（既有纪律，skill 无持久状态）。消费仓无需动作（触发 skill 时才创建 `openspec/architecture/`）。

## Open Questions

见 proposal OQ1–OQ3（L2 方法论 / contract 机械化档位 / S1–S11 完整投影排期），均不阻塞本 change。

## Compliance

- **D-6 边界/ADR 逐条**：`adr/0002`（只复用产出不复用内部）——outside voice 走既有 spec-review 机制，**遵守**（DEC-6）；`adr/0011`（共享解析核心逐消费方语义）——sad_schema 常量共享、scaffold 写侧/lint 读侧各自校验，**遵守**（DEC-1）；`adr/0018`（机械校验器输出诚实）——`-SEMANTICS-UNCHECKED` 尾缀 + 坏输入 fail-closed 分离，**遵守**（DEC-5）；`adr/0019`（锚 schema 一致性机械化）——frontmatter/标记语法单一 schema 源，**遵守**；`adr/0003`（全局规则最小仓内副本）——不向消费仓拷任何规则副本，SAD 是项目自身文档非规则，**遵守**；`adr/0005`（dev/runtime checkout 纪律）——开发本仓改动后需跑 setup.sh 方可测，已入 tasks，**遵守**。跨模块共享 schema（SAD 格式）未越既有边界——为全新契约面，由 sad_schema.py 单源持有，**确认未越界**。
- **D-1**：本 design 引用的既有事实（setup.sh 发现机制、adr 文件名、outside-voice-reuse-guard 需求、resolve-workflow.sh 路径）均已在本 session 实读核验，非记忆写入。
- 规则/边界合规：不触 `openspec/workflow/` 与 `sdflow-init/assets/`；无凭证/敏感数据面。
