# opsx:ff 起手强制规范（前置动作 FF-0 + 生成硬约束 D-1~D-6）

> **定位声明**：本规范是 `/opsx:ff` 起手强制项的**唯一权威定义源**——含前置动作 **FF-0（开分支）** 与生成硬约束 **D-1~D-6**。
> 所有调用方（`config.yaml` rules 自动注入、`workflow/workflow.md` 流程、各处对比表/判定速查）
> **只引用编号、不复制定义内容**。约束内容如有变更，只改本文件。
>
> 方法论定位：D 约束属于「生成时 × 外部接地」的预防型质量手段
> （见 [Spec_Quality_Methodology.md](./reference/Spec_Quality_Methodology.md) 原则 1）。

## 前置强制动作（FF-0：开 feature 分支）

> FF-0 是 ff **起手必做的非 D 动作**（VCS 前置，不是内容约束，故与 D-x 区分编号）。

**FF-0**：起手建 change（`/opsx:ff {change}`、或 `/sdflow-spec` 的相位 B 起手）时，**生成任何产物之前**必须过**三分支判定**——按当前分支恰好命中一条：

| 当前分支 | 动作 |
|---|---|
| **保护分支**（main / master / 默认分支） | `git checkout -b feat/{change}` |
| **已在 `feat/{本 change}`** | 跳过（**真幂等**，不重复建） |
| **其它 feature 分支**（前一个 change 的分支等） | 🔴 **halt 问人**：从当前切出 / 回 base 切出 / 就地继续，三选一 |

- 🔴 **MUST NOT 沿用「已在 feature 分支就跳过」的弱判据**——那会让第二个 change 的工件与 checkpoint 落在**前一个 change 的分支**上（stacking），使两个 change 的提交历史交错，`ship_gate` 的完成判据须靠 change-命名空间隔离才不被污染。
- `git checkout -b` 失败（分支已存在）→ fallback 到 `git checkout feat/{change}`；再失败即**如实报告**给人决定，MUST NOT 静默继续。
- 目的：`proposal/design/specs/tasks` 随 feature 分支落地，merge 后 PR 完整呈现「设计→审查→实现」变更故事。

调用方在 ff prompt 第一句注入：
`先过 FF-0 三分支判定（保护分支则 git checkout -b feat/{change}；已在本 change 分支则跳过；在其它 feature 分支则停下问我），再按 config + trigger-catalog 生成`。

> **硬强制已配套**：FF-0 分支守卫 hook（PreToolUse·Bash）拦 `openspec new change` 的所有入口（`/opsx:new`、`/opsx:propose`、`/opsx:ff`、`/opsx:onboard`、`/sdflow-spec`（分支 A，相位 B ③ 建 change 目录）殊途同归调它——**分支 A 与分支 B 同样受管辖**，没有哪条入口绕得过）。**全局安装一次**（`~/.claude/hooks/` + `~/.claude/settings.json`，由 sdflow-init init/update 幂等确保），跨所有项目生效；非 openspec 项目里命令不匹配即放行。
> hook 只在整条命令完整匹配**单条直接 literal** 创建 grammar 时，才把 payload `cwd` 当作作用仓执行三分支。
> 有限正向 grammar 仅含 `openspec new change <合法字面量>` 与 `openspec change new <合法字面量>`，容忍水平空白、单/双引号及单个 `--json` 变体。
> 原因码优先级：先排除换行；只有直接创建前缀位于命令起点（前面仅水平空白）、且 name expression 含有限动态 marker（`$` 统一覆盖参数展开与任意嵌套命令替换，另含反引号与 glob `*` / `?` / `[`）时，才记录 `change-name-unparseable`。
> wrapper 优先为 `cwd-ambiguous`，即使其内层使用相同动态表达式；目录切换、compound、换行、前置散文以及不含动态 marker 的后置散文也同样记录 `cwd-ambiguous`。单个无效 literal / option 仍记录 `change-name-unparseable`。
> 两种未判定均只输出 `additionalContext`，**MUST NOT 解析 shell**，也不设 `permissionDecision`；多处创建调用则先行 stacking deny。
> hook 实现同一条三分支判定：**保护分支 → deny**；**已在 `feat/{该 change}` → 放行**；**其它 feature 分支 → deny 并要求先问人**（人确认「就地继续」后**分两步**敲：先单独 `touch <仓根>/openspec/.ff0-ack`，**再重跑** `openspec new change <name>`——**MUST NOT 写成 `touch … && openspec …` 一条**：PreToolUse 在命令执行**前**判定，那一刻哨兵还不存在，守卫会把这条命令连同 touch 一起 deny，唯一逃生口变死循环。**该哨兵是给人拍板用的一次性逃生口：守卫读到即删、只对下一次调用生效，模型 MUST NOT 自行 touch 它**；判据只看文件在不在，MUST NOT 从命令串里认口令——命令串是无界的 shell 语法面）。
> **残留令牌是真实的绕过口，如实登记**：人若在自己的终端里敲 `openspec new change`（hook 根本不触发），哨兵**永不被消费**，会留在盘上静默放行下一次调用。缓解只做两件**有界**的事：① 哨兵带**有界时效**，超窗即失效并自动删除（把「常驻绕过口」压成一个短窗口）——窗口长度的**单一源** = hook 的 `ACK_TTL_SECONDS`，deny 文案按 `// 60` 自报分钟数，**本文与 hook 散文一律不写死数字**（手抄一份即与常量分叉、改常量不会红）；判据是**双边**的 `0 ≤ now − mtime ≤ TTL`——单边式在 mtime 落在未来（时钟回拨 / 从备份恢复保留 mtime）时恒真，窗口形同虚设；② `/openspec/.ff0-ack` 进 canonical runtime gitignore（`assets/snippets/runtime-gitignore.txt`），防 `checkpoint-commit.sh` 的 `git add -A` 把它提交入库、让每个 clone 都带一个。窗口内的残留仍是真洞，本 hook **MUST NOT 声称堵死它**——它从来不是安全边界，真正的防线是纪律 + review。
> Git 探测异常一律 silent fail-open；命令语义未判定则按上述无决策 context 诚实显形。文档级强制（调用方注入 + review 核对）作为补充层。

## wayfinder→ff 衔接契约（条件：change 源于 wayfinder map）

> 本节是**条件契约**，非 D-1~D-6 硬约束——只在 change 源于 wayfinder map 时生效，不占用 D 编号
> （按下文「约束集设计判据」④：无关变更应条件触发，命中才注入）。
> 调用方（`config.yaml` rules 自动注入、`workflow/workflow.md` ff 步骤）**只引用本节标题「wayfinder→ff 衔接契约」，
> 不复制条款文本**——与 D-1~D-6 的单一源纪律同构。

change 若源于 wayfinder map（即由 wayfinder chart 铺图逐 ticket 决议收敛后触发 `opsx:ff`），ff 起手须遵守：

1. **逐区读 map**：
   - Destination → 喂 proposal 动机与 Success Metrics（D-5）；
   - Decisions-so-far → **逐 ticket zoom 到决议全文**，MUST NOT 只读摘要行（防 ff「prefer making reasonable decisions」对已决项重新决歪）；zoom 设上界 **≤8 张展开全文**，超出按与本 change 的相关性截断，并在 proposal 中注明截断；
   - Out-of-scope → 喂 Non-Goals 可证伪假设（D-3）。
2. **TG 判命中前置**：TG（触发目录）判命中前置到 chart 阶段，写入 map Notes；此为**增强非转移**——ff 起手判触发纪律不变（Notes 有则核对、无则照常全判），Notes 缺失不构成失败态、不硬卡。
3. **回链**：proposal SHALL 回链 map 供溯源；design 决策段源自已决 ticket 的 SHALL 内联回链该 ticket——
   机器可 grep 的锚格式：`〔wayfinder-resolved: <map路径>#ticket-<N>〕`（固定前缀 `wayfinder-resolved:`）。
   **锚的用途只有溯源**（这个决策当初是在哪个 ticket 上决的）。
   > 🔴 **MUST NOT 用它给 grill 减负**：grill 是**独立**审视，**一律全深度**，
   > **MUST NOT** 因为「上游 wayfinder 已经决过」就瘦跑或跳过某条分支。
   > 拿上游产出给自己松绑，grill 就从「二次审视」退化成「盖章」——而它的全部价值就是那个二次。

**边界**：本契约只约束「wayfinder → opsx:ff 出 change」路径；roadmap 结晶直写 requirements/design/roadmap/task-log 四件套不经 ff，不受此节约束。

## 切片建议（条件：仓 `impl-pipeline: tickets`）

> 本条款与上节条件不同，勿混——上节条件是「change 源于 wayfinder map」，本条款条件是
> 「仓 `openspec/config.yaml` 顶层键 `impl-pipeline: tickets`」，两者互不蕴含。

仓已开 `impl-pipeline: tickets` 时，design.md 决策区 **MAY** 含「切片建议」节（初步 ticket 划分 + 阻塞边草图）。
出 ticket 模式（`sdflow-implement`）消费该节的语义是**建议，非契约**——节缺席时自主出 ticket；
对切片粒度的争议走既有 T10 三级决策协议。

切片建议内容 **MUST NOT** 使用 `wayfinder-resolved:` 前缀（两类「ticket」语义须物理区分——本节的
「切片建议 ticket」与上节 wayfinder map 的「已决 ticket」不是一回事，混用会让溯源指向错误的出处）。

## 背景

D-1~D-5 原本以纯文本形式内嵌在早期工作流文档的 `/opsx:ff` 命令 prompt 单元格里
（在多个 ff 调用点各一份完整复制），其余多处（工作流概览、对比表、附录模板、判定速查）
仅以裸编号引用、不含定义。

根本问题：**定义无单一权威源**——1 份定义被复制成 2 份 + 4 处裸引用。
2026-06-27 新增 D-5（commit b60f21b）时，只更新了两处完整定义，未同步裸引用处的编号清单，
导致对比表/附录/速查仍写「D-1/D-3/D-4」漏掉 D-5，定义与引用漂移。本规范抽出单一源以根除漂移。

## 约束集设计判据（一条约束凭什么占 D 的位置）

D 约束是稀缺资源——塞太多会触发过载。
**一个候选要升为 D 硬约束，必须四条全中**：

| 判据 | 含义 | 不满足时应去哪 |
|------|------|--------------|
| ① 需要生成时的**主动行为** | grep / 交叉核对 / 阻塞，而非能被动填的槽位 | 能填的 → 下沉为 spec/design 模板槽位 |
| ② 守**高成本、事后难逆**的失效 | 会暴雷（事故/返工），不是「不好看」 | 仅美观/风格 → review 检查项 |
| ③ 锚**外部真相** | 代码库 / ADR / 利益相关方（模板焊不住的那半边） | 纯内部一致 → 模板或 review |
| ④ 对当前 change **相关** | 无关的约束应**条件触发**，命中才注入 | 领域特定 → 条件触发 |

判据①是关键：D-1「先 grep 再写」要求一个动作，无法退化成槽位——这是金标准。
能退化成槽位的（如假设列表、开放问题、NFR 数字化），应走**模板杠杆**，不占 D。

**接地真相覆盖检查**（确保不偏斜）：

```
  ① 代码库      → D-1, D-2        ✅
  ② 行业标准    → (走模板/checklist，不占 D)
  ③ 既有决策/ADR → D-6            ✅（项目不可违反的硬边界，必须有 D 守）
  ④ 利益相关方   → D-5            ✅
```

## 规则

### 约束定义（D-1~D-6）

| 编号 | 约束内容 | 作用产物 | 防止的失效 | 接地真相 |
|------|----------|----------|-----------|---------|
| **D-1** | 代码事实（函数名 / DB 字段 / API 路径）**先 grep 验证再写入**，禁止从记忆直接写入 | design.md | 「从记忆编造代码事实」（Accurate 失守） | ① 代码库 |
| **D-2** | design.md 须含 **v_old / v_new 完整列清单**（列名 + 类型 + 约束 + 默认值 + nullable） | design.md | DB schema 迁移漏列、类型/约束变更未对照 | ① 代码库 |
| **D-3** | 每处「不在范围内」**附可证伪假设**，不得写空泛的「超出范围」 | design.md | 模糊 scope 排除等于谎言 | 内部自洽 |
| **D-4** | 外部依赖（DB / 缓存 / 第三方 API）**声明超时时间**；写操作**说明回滚路径** | design.md | 外部依赖无超时、无回滚 | 内部自洽 |
| **D-5** | proposal.md 须含 **Success Metrics 节**（1-3 条可量化指标，格式：`指标 — 基准 → 目标 — 度量方式`）。留空或只写注释模板 → **阻塞**，不得继续生成后续产出物 | proposal.md | 「方向不可验证」（无成功指标） | ④ 利益相关方意图 |
| **D-6** | 生成前逐条核对**项目既有的设计强制规范 / ADR / 架构边界**，声明遵守或显式豁免；**若变更涉及跨产品或跨模块共享的数据模型 / schema 边界，须显式确认未越界，否则阻塞** | design.md / spec | 悄悄违反不可逆的架构 / 边界约定（最高级违规） | ③ 既有决策 / ADR |

### 触发条件表

本 rule **不区分 S/M/L 路径**——每条约束由**变更的实际内容**触发，与路径无关。
路径只决定「是否消费本 rule」：轻量变更可整体跳过本 rule；其余变更按下表逐条判定，命中即注入。

| 约束 | 触发条件（具体行为，不用代号） |
|------|------------------|
| D-1 | design.md 写入任何**代码事实**（函数名 / DB 字段 / API 路径）时 |
| D-3 | design.md 含**「不在范围内」声明**时 |
| D-5 | 生成 **proposal.md** 时 |
| D-2 | 变更涉及 **DB schema 迁移**（新增/删除/修改列、索引、约束、字段类型）时 |
| D-4 | 变更**引入或修改外部依赖**（DB / 缓存 / 第三方 API / 跨服务网络调用）时 |
| D-6 | 变更涉及**受架构边界约束的数据模型 / schema**（如跨产品或跨模块共享的边界）时 |

**说明**：
- D-1 / D-3 / D-5 的触发条件几乎对每个正常变更都成立，实践中近似「常驻」；但仍以条件表述，口径统一。
- D-2 / D-4 / D-6 是窄条件，只在命中时注入，避免无关样板。
- 触发条件**一律写具体行为描述，不写 triage 风险代号（R1~R6）**——本 rule 自包含，不依赖外部代号表。
- 历史变更：D-4 原为无条件注入，2026-06-28 改为「引入/修改外部依赖时」条件触发。

### 调用方引用方式

调用方（如 `workflow/workflow.md`）**不得复制上表定义文本**，只能写形如：

```
/opsx:ff {change}。按 @openspec/workflow/ff-generation-constraints.md 注入：
默认 D-1/D-3/D-5；本变更涉及 <DB schema 迁移 / 外部依赖 / 产品 model>，
追加对应条件约束 <D-2 / D-4 / D-6>。
```

完整可注入的 prompt 文本见下方「附：可直接注入的 prompt 片段」。

## 反模式 vs 正模式

### 反模式：定义复制进每个调用点

```
# 早期文档在多个调用点各写一份完整 D 定义，
# 对比表/附录/速查又各写一遍裸编号清单
调用点 A: D-1 代码事实先 grep... D-3 ... D-4 ... D-5 ...（完整文本）
对比表  : D-1/D-3/D-4          ← 新增 D-5 后忘了同步，漂移
```

**为什么是反模式**：定义有 ≥2 份副本 + 多处裸引用，改一处必漏其余，已实证发生 D-5 漂移。

### 正模式：单一源 + 编号引用

```
# 定义只在本 rule 文件一处
# 所有调用方：按 @openspec/workflow/ff-generation-constraints.md 注入 D-x
调用点: 按 rule 注入默认 D-1/D-3/D-5，涉及 DB schema/外部依赖/共享 model 时追加 D-2/D-4/D-6
```

**为什么是正模式**：新增/修改约束只改本文件一处，全仓库引用自动生效。

## 附：可直接注入的 prompt 片段

> 调用方若需把完整约束文本贴进 ff prompt，从此处复制（保持与上表同步）：

**默认 / 常驻片段（D-1 / D-3 / D-5）**：

```
生成 design.md 须遵守：
D-1 代码事实（函数名/DB字段/API路径）先 grep 验证再写入，禁止从记忆直接写入；
D-3 每处"不在范围内"附可证伪假设，不得写空泛的"超出范围"；
D-5 proposal.md 须含 Success Metrics 节（1-3 条可量化成功指标，
    格式：指标 — 基准 → 目标 — 度量方式），留空或只写注释模板则视为阻塞，
    不得继续生成后续产出物。
```

**条件片段（按变更实际涉及内容追加，可叠加）**：

```
〔涉及 DB schema 迁移时追加 D-2〕
D-2：design.md 须含 v_old/v_new 完整列清单（列名+类型+约束+默认值+nullable）。

〔引入/修改外部依赖时追加 D-4〕
D-4：外部依赖（DB/缓存/第三方API/跨服务调用）声明超时时间，写操作说明回滚路径。

〔涉及受边界约束的数据模型 / schema 时追加 D-6〕
D-6：逐条核对项目设计强制规范 + 相关架构 / 边界 ADR，声明遵守或显式豁免；
    若涉及跨产品 / 跨模块共享 model 须显式确认未越界，否则阻塞。
```

## 检查清单

修改本规范或调用方时**必须逐项确认**：

- [ ] D 约束的定义文本是否只在本文件出现一份？
- [ ] 各调用方（`workflow/workflow.md` 等）是否均为编号引用，无定义复制？
- [ ] 触发条件表与「附：prompt 片段」是否一致（同步修改）？
- [ ] 新增 D-x 后，触发条件表和所有调用方编号清单是否都已覆盖？
- [ ] 触发条件是否写**具体行为描述**，未使用 triage 风险代号（R1~R6）？
- [ ] 新增候选是否通过「约束集设计判据」四条全中？否则应下沉模板或降为 review 项。

## 历史

- 2026-06-28（二次修订）：新增 **D-6**（边界/ADR 合规，锚定既有决策真相）；**D-4 由路径默认改为条件触发**（仅在引入/修改外部依赖时）；所有触发条件从 triage 代号（R1）改写为**具体行为描述**，使 rule 自包含。新口径：默认 D-1/D-3/D-5，按实际涉及内容条件追加 D-2/D-4/D-6。补充「约束集设计判据」一节。
- 2026-06-28：从早期工作流文档内嵌文本抽出，建立单一权威源。修正历史上 D-5 未同步到对比表/附录/速查导致的定义漂移。
- 2026-06-27：D-5（Success Metrics 阻塞约束）加入 ff prompt（commit b60f21b），仅更新两处完整定义，遗漏裸引用处——本次抽取的直接动因。
