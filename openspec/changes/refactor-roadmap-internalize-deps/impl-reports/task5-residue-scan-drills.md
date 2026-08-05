# Task 5 实现记录：残留扫描与存量包兼容演练

范围：`tasks.md` §6 的 6.1 / 6.4 / 6.5 / 6.8。依据 `tickets.md` Task 5。

---

## 6.1 全量 grep 残留扫描

命令（不带 `--include`，排除 `.git/` 与临时并行票 worktree `.claude/worktrees/`——后者是本次
`sdflow-implement` 派发出的临时并行工作树副本，非仓内容）：

```bash
grep -rlE 'wayfinder|office-hours|grilling|domain-modeling|openspec/matt|footage|三分支路由|Tracker root|结晶|产品/商业野心|野心信号' . \
  | grep -v '^\./\.git/' | grep -v '^\./\.claude/worktrees/' | sort
```

命中 **113 个文件**（与 brief 估计的「约 103」同量级，差值来自新增文件如本 change 的
`impl-reports/task4-*`、`openspec/adr/0037-*`、`openspec/changes/archive/2026-08-05-simplify-workflow/*`
等在 brief 撰写后才落盘）。逐条按七条规则化白名单 + 2 类同形异义/越域排除过滤，分类结果：

| 类别 | 文件数 | 说明 |
|---|---:|---|
| ⑥ `openspec/changes/archive/` | 56 | 历史归档 change，含 `2026-07-10-matt-workflow-integration`、`2026-07-10-rebuild-sdflow-roadmap-v2`、`2026-07-11-harden-hr-tg-anchor-consistency`、`2026-07-26-add-sdflow-spec`、`2026-07-28-harden-implement-review-loop`、`2026-08-05-simplify-workflow` 六个已归档 change 的产物 |
| ⑥ 本 change 目录 `refactor-roadmap-internalize-deps/*` | 22 | decision-memo / design / proposal / specs delta / tasks / tickets / gstack-review / spec-review-report / 各票 impl-reports |
| ③ `openspec/issues/`（open+closed 两态） | 12 | `CLOSED.md` + 10 个 closed/todo T-文件 + 1 个 open/todo（T129）历史决策引用 |
| ⑦ `docs/workflow-skills/*` | 3 | `grill-with-docs.md` / `matt-pocock-workflow.md` / `setup-matt-pocock-skills.md`，具名历史文档 |
| HOMONYM（同形异义，「结晶」泛义用法） | 2 | `docs/criteria-mechanization-tracker.md:17`「探索什么/何时**结晶**成 change」、`docs/fable5/opus48-agentic-instruction-system.md`×3 处「重复劳动**结晶**为可调用资产」——均为「凝结/固化」通用汉语义，与 roadmap 旧术语「结晶」（→改「生成」）无关，同 SR-7 对「野心」的同形异义处置口径 |
| ⑦ext 历史调研快照（未列入原七条，判断依据见下） | 2 | `docs/sdflow-fable5/README.md`、`docs/sdflow-fable5/04-optimization-proposal.md`——均属 2026-07-10「深度调研产出」快照集，仅 `02-module-reference.md` 自述「活文档（非冻结快照）」（SR-16 已据此单独更新，见下）；本两份未见类似自述，且其 wayfinder/matt 提及均是**引用第三方 Matt Pocock 工具调研**（`docs/workflow-skills/matt-pocock-workflow.md`，已属⑦），非描述本仓自身机制 |
| ⑤ `.claude/settings.local.json` | 1 | `"office-hours": "name-only"` 本机工具授权配置 |
| ④ 存量活跃 roadmap 包 | 1 | `openspec/roadmaps/issues-triage-2026-08/roadmap.md` |
| ⑥(roadmaps/archive) | 1 | `openspec/roadmaps/archive/workflow-cost-optimization/memo.md` |
| ⑥(演进史) | 1 | `sdflow-init/assets/workflow/workflow-history.md`——append-only 移除记录（含 A4 条目，Task 4 4.2 所加） |
| ⑥ext（ADR 历史决策记录，未列入原七条，判断依据见下） | 1 | `openspec/adr/0037-roadmap-discussion-layer-internalization-and-matt-removal.md`——ADR 定义上即永久性历史决策记录（自身职责就是用过去式描述被移除机制的动机），与「本 change 目录」同一豁免精神 |
| ② `wayfinder-resolved:` 前缀规则 | 1 | `sdflow-init/assets/workflow/ff-generation-constraints.md`（Task 4 4.1 已加 legacy 标注） |
| OOS（越域，非本仓 roadmap 机制） | 1 | `docs/sdflow-context-policy.md`——文档自述「本文不是 as-built 文档...状态：结论已定，规则改动未实施」（非当前实现描述）；`/grilling`/`/domain-modeling` 引用的是 `/grill-with-docs → /grilling` 这条**完全不同的第三方 skill 链**（用于 grill 设计方案，非 matt 的 issue tracker）；`wayfinder` 一处是对 `workflow.md`（另一 bundle，本 change 未触及）历史行文的分析引述，非本仓 sdflow-roadmap 自身机制的现状声明 |
| LEGIT — 已按本 change 其它票要求更新到位（含 `footage`/`历史存档`/`商业化信号` 等目标态术语的正确留用） | 9 | `CLAUDE.md`（:183-184 DOC-1 语境「考古层」原样、:190「存量 footage 冻结包」为目标态正确术语）、`openspec/CONTEXT.md`（5.2 三词条）、`openspec/INDEX.md`（5.5 摘要行）、`docs/sdflow-fable5/02-module-reference.md`（5.6 §4.6）、`docs/external-dependencies.md`（5.4，另见下方残留#2）、`sdflow-roadmap/references/long-flow-skill-paradigm.md`（2.3 历史注记）、`sdflow-roadmap/references/task-log-template.md`（2.2 术语改）、`sdflow-roadmap/SKILL.md`（1.x 重写，另见下方残留#1） |
| DEFERRED（明确不在本票范围） | 1 | `openspec/specs/roadmap-planning/spec.md`——**主 spec**（非本 change 的 delta 副本），delta 尚未经 `sdflow-done` archive 步合入，当前内容合法地仍是旧态；`tasks.md` 6.9 已明文将「归档后重扫此文件」列为独立后续任务，由 archive 步承接，本票不改 |

**合计** 56+22+12+3+2+2+1+1+1+1+1+1+1 = 104（白名单/同形异义/越域/deferred 类，**13 项**）
+ 9（LEGIT，含 2 处发现并已修复的真残留）= **113** ✓

> 〔双轴审 Spec 轴 Important 订正〕原算式写作 `…+1+1 = 103`，只列了 **12** 个数——**漏掉 `DEFERRED` 那一项**
> （上表 14 行类别中除 LEGIT 外共 13 项），故 `103 + 9 = 112 ≠ 113`，自查 ✓ 在字面上站不住。
> 订正后：非 LEGIT 13 项求和 = 104，`104 + 9 = 113`，与总命中数一致。
> **总数 113 本身未受影响**——编排层已用 `git --no-pager grep -lIE '<同一词表>' | wc -l` 在当前 HEAD 独立复算得 113。
>
> ⚠️ 该总数会**随本 change 自身产物落盘而单调增长**（报告、review-package、brief 等文件本身含词表词），
> 属自指增长、非真实残留：Task 5 Standards 轴 reviewer 在更晚的时点复算得 115，差值即为扫描后新落盘的
> 两个文件。**复算时 MUST 记录复算时点的 HEAD**，否则数字对不上会被误判为漏记。

### 发现并已修复的真残留（2 条，均超出七条白名单，判定为需修复的悬空引用）

**残留 #1 — `sdflow-roadmap/SKILL.md:408` 悬空章节引用**（编排层已捞到、本票承接的跨票发现）：

原文：
> 三态路由收敛后**直写**三件套、**不经 change 生产路径**（`/sdflow-spec` · `opsx:ff`，两条都不经）——「wayfinder→ff 衔接契约」（`ff-generation-constraints.md`）属 change 生产路径，与本 skill 的直写路径互斥不叠加。

`grep -n "衔接契约\|wayfinder→ff" sdflow-init/assets/workflow/ff-generation-constraints.md` 零命中——该文件当前只有「前置强制动作（FF-0）」与「约束定义（D-1~D-6）」两类章节，无此名。已改为引用该文件真实存在的内容：

```diff
- 三态路由收敛后**直写**三件套、**不经 change 生产路径**（`/sdflow-spec` · `opsx:ff`，两条都不经）——「wayfinder→ff 衔接契约」（`ff-generation-constraints.md`）属 change 生产路径，与本 skill 的直写路径互斥不叠加。
+ 三态路由收敛后**直写**三件套、**不经 change 生产路径**（`/sdflow-spec` · `opsx:ff`，两条都不经）——`ff-generation-constraints.md` 定义的生成硬约束（FF-0 开分支 + D-1~D-6）属 change 生产路径专属机制，与本 skill 的直写路径互斥不叠加。
```

**残留 #2 — `docs/external-dependencies.md:77-78` 行号引用漂移**（扫描 LEGIT 类文件时顺手发现，同一批 SKILL.md 重写导致的同类缺陷，按 fold 判据当场修，未另开）：

原文引用 `sdflow-roadmap/SKILL.md:426`（`/autoplan`）与 `:425`（`/plan-eng-review`）——这两个行号是 SKILL.md 旧版（635 行）的位置，重写后（Task 1）内容整体挪位，`grep -n "plan-eng-review\|autoplan" sdflow-roadmap/SKILL.md` 实测这两处现位于 `:460` / `:459`（"### 分档判据"节）。已订正：

```diff
- | **gstack `/autoplan`** | 设计审的广审层（CEO/Eng/Design 三连） | `sdflow-spec-review/SKILL.md`、`sdflow-roadmap/SKILL.md:426` | 显式提示 + 留「未审待恢复」痕迹 |
- | **`/plan-eng-review`** | roadmap 的技术评审（默认档） | `sdflow-roadmap/SKILL.md:425` | 同上 |
+ | **gstack `/autoplan`** | 设计审的广审层（CEO/Eng/Design 三连） | `sdflow-spec-review/SKILL.md`、`sdflow-roadmap/SKILL.md:460` | 显式提示 + 留「未审待恢复」痕迹 |
+ | **`/plan-eng-review`** | roadmap 的技术评审（默认档） | `sdflow-roadmap/SKILL.md:459` | 同上 |
```

（额外核实：`openspec/adr/0013-*.md:25` 也引用了一处旧 `sdflow-roadmap/SKILL.md:195`——ADR 属永久历史决策记录，其行号引用是「撰写当时的状态快照」，不追随目标文件演进，故不改。）

**结论**：过滤 + 修复后，**非白名单残留为零**（6.1 验收标准达成）。

---

## 6.4 构造 footage fixture 演练（续跑 / 重入 / 收尾三条路径）

全仓实测 `find . -type d -name footage` 零命中（含 worktrees 内也为零），`issues-triage-2026-08/`
只有 `roadmap.md`——直接拿存量包演练证不到「含 footage 的存量包」这条冻结分支，属恒真锚。故按
tasks.md 6.4 要求构造临时 fixture。

### fixture 构造

临时目录 `openspec/roadmaps/_task5-footage-fixture/`（真实落在 `openspec/roadmaps/` 下，使
「扫描 `openspec/roadmaps/*/memo.md`」类指令可用真实 `find`/`grep` 命令验证，而非纯手推）：

```
_task5-footage-fixture/
├── design.md          # 占位三件套（无 memo.md ——模拟旧版 wayfinder 长档路径产出：
├── roadmap.md          #   决策形成过程落在 footage/，而非 memo.md）
├── task-log.md         #   含非空「## Review 处置」小节
└── footage/
    ├── map.md           # 头部 Tracker root / Effort kind，旧版 wayfinder chart 产物
    └── issues/
        └── 01-legacy-open-ticket.md   # Status: open
```

### 路径 1：第零步重入探测（对应 SKILL.md `:277-285`）

```bash
find openspec/roadmaps -maxdepth 2 -name "memo.md"
```

实测：fixture 目录不在结果列表中（无 `memo.md`）。依据 SKILL.md `:277`「扫描
`openspec/roadmaps/*/memo.md`，寻找状态标记为『状态：DRAFT』的未定稿包」——fixture 无 memo.md，
第零步「未命中」，**不会被误判为半成品/未定稿包**，直接放行进入相位 A（`:283`「未命中→直接进入相位A」）。

### 路径 2：续跑（对应 SKILL.md 规则 3 `:216-223` + 包生命周期 `:261-273`）

- **包生命周期判定**（`:263-267`）：`openspec/roadmaps/_task5-footage-fixture/` 已存在 → 非
  create，是 continue 或 replan（本次假设操作者选择「continue，增量更新」）。
- **footage 处置**（`:223`，规则 3「存量 footage 冻结」）：
  > 含 `footage/` 的存量包 **SHALL** 视为合法历史形态——续跑时 **MUST NOT** 报错、**MUST NOT**
  > 强推迁移、**MUST NOT** 新增票或要求票闭环，`footage/issues/` 中未决票视为历史遗留，至多输出
  > 一行「存量 footage，历史存档冻结」提示，不告警刷屏
- 逐条验证：
  - **不报错**：`:223` 显式 `MUST NOT 报错`。
  - **不迁移文件**：`:223` 显式 `MUST NOT 强推迁移`；实测续跑动作只会追加/更新 design.md /
    roadmap.md / task-log.md 受影响章节（`:228`「continue：保留既有 task-log/Review 处置」），
    `footage/` 目录路径不受触碰。
  - **不新增票**：`:223` 显式 `MUST NOT 新增票`。
  - **未决票不阻塞收尾**：`:223` 显式 `MUST NOT 要求票闭环`；且收尾四项（`:503-517`）逐项通读
    未见任何一项以 footage 票状态为判据（① Review 处置小节仅关涉 review 流程 issue、②③④
    分别是引用完整性/历史存档未引用/memo 对账，均与 `footage/issues/` 内票状态无关）——`01-*`
    票保持 `open` 不影响任一收尾项。
  - **至多一行冻结提示**：`:223` 逐字「至多输出一行『存量 footage，历史存档冻结』提示，不告警
    刷屏」。

### 路径 3：收尾 checklist 四项（对应 SKILL.md `:499-517`）

对 fixture 三件套内容执行核对：

- **①** `task-log.md` 含非空「## Review 处置」小节（fixture 已放 1 条 ✅采纳记录）——通过。
- **②** 三件套相互引用完整——fixture 为占位内容，本项非本次演练焦点（与 footage 无关，跳过细判）。
- **③ 历史存档未被引用**（`:511`）：`grep -n "footage\|memo\.md" design.md roadmap.md task-log.md`
  实测零命中（design.md 正文仅占位说明，未出现「详见 footage/…」类引用）——通过。
- **④ memo 对账 + 未决项闭环**（`:513-515`）：fixture 无 `memo.md`，checklist ④ 的两个子判据
  （`[确认]` 前缀行对账、`## 未决项` 小节闭环）均以「memo.md 中存在……」为前提——无 memo.md 时
  两者均为 0 条目的退化情形，天然满足（无条目需处置）。**观察**：SKILL.md 对「memo.md 完全不
  存在」这一退化情形没有像检查项③那样显式加注「（如有）」，但结论无歧义（0 条目 = 自动满足），
  且发生场景窄（仅限从未经过相位 B、纯 footage 产出的存量包），**判定为低概率低影响的文档措辞
  留白，非行为缺陷**，不在本票修复范围内（按 CLAUDE.md 基准④五问：根因=旧版检查项③已有
  「如有」先例未在④复用；概率低；影响小（结论不受影响、无歧义）；完美成本=改动一处收尾文案；
  简化方案=如实记录，留给后续 review 决定是否补「（如有）」）。

### 反恒真自查

按 brief 要求逐条自问「如果 SKILL.md 里那条冻结条款根本不存在，这条断言会不会仍然通过？」——
若删去规则 3（`:216-223`「历史存档引用边界与存量 footage 冻结」），SKILL.md 全文只剩 memo-based
产出模式描述，一个照文本执行的 agent 面对「无 memo.md 但有 footage/」的包，缺乏任何『不报错/不
迁移/不新增票』的指令依据，大概率会因结构不认识而报错、或尝试把 footage 内容强行迁移/转录进
memo.md 体系。**断言非恒真**，锚点确实落在被测条款上。

### fixture 清理

```
rm -rf openspec/roadmaps/_task5-footage-fixture
```

`git status --short openspec/roadmaps/` 演练后确认目录已恢复为演练前状态（仅 `archive/` 与
`issues-triage-2026-08/` 两个既有子目录，无残留）。

---

## 6.5 缺件存量包演练（真实单文件包 `issues-triage-2026-08/`，MUST NOT 修改）

`ls openspec/roadmaps/issues-triage-2026-08/` 实测只有 `roadmap.md`，无 `design.md` /
`task-log.md`——本票全程只读，未对该目录做任何写操作（`git status --short` 全程干净）。

SKILL.md `:249-254`「缺件存量包兼容模式」**直接点名本包为例**：

> 存量包还存在**第三种形态**——只有 `roadmap.md`、缺 `design.md` / `task-log.md` 的单文件包
> （如本仓 `openspec/roadmaps/issues-triage-2026-08/`）。该形态同样 **SHALL** 视为合法历史形态：
> - 续跑时 **MUST NOT** 报错、**MUST NOT** 因缺件拒绝工作
> - 收尾 checklist ②「三件套相互引用完整」对缺失文件 **SHALL** 判为**不适用**（而非不通过），
>   并输出一行「存量缺件包（缺 X），引用完整性仅对现存文件核验」提示
> - 操作者要求补齐时按 continue 路径生成缺失文件

continue 判定推演：

1. **命名与存在性**：`{name}` = `issues-triage-2026-08`，目录已存在 → 非 create。
2. **continue/replan 判据**（`:271`「改动只影响未细化/未验收阶段、不推翻既有决策→倾向
   continue」）：假设操作者只是想续跑/补齐该包（非推翻既有 roadmap.md 内容）→ continue。
3. **不报错、不因缺件拒绝**：`:253` 显式条款——continue 路径下允许在 design.md/task-log.md
   缺失的情况下继续工作（生成缺失文件走 continue 路径，`:255`）。
4. **收尾 ② 判定**（对照 checklist ②正文 `:509`）：
   > **缺件存量包**（见「产出模式」节）判定标准对缺失文件（design.md / task-log.md）记
   > 「不适用」而非「不通过」，并输出一行「存量缺件包（缺 X），引用完整性仅对现存文件核验」
   > 提示——`N/A` 为合法第三态。

   即：design.md、task-log.md 两项记 `N/A`（不适用），只对现存的 `roadmap.md` 做适用范围内的
   自查（如有的话），整体判定不因缺件判「不通过」。

**结论**：6.5 两条验收断言（不报错 / 收尾②对缺失文件判「不适用」）均在 SKILL.md 中有逐字对应
条款，且该条款显式以本包路径为例证——非恒真（若删去「缺件存量包兼容模式」整节，检查②的通用
判据「roadmap.md 每个已细化阶段至少回指 design.md 对应决策一次」在 design.md 不存在时无法满足，
会退化为「不通过」而非「不适用」，两者结论不同，故该节是承重条款）。全程未修改
`openspec/roadmaps/issues-triage-2026-08/roadmap.md`。

---

## 6.8 终审场景核对清单：6×3 逐格核对

逐格标注 SKILL.md 中的明确依据（行号）。「同左」的格沿用同行左侧格的依据不重复展开理由，但仍
单独确认该依据在该列场景下依旧成立。

| # | 场景 | create | continue | replan |
|---|---|---|---|---|
| ① | gate-0 过 ∧ 无信号（直接生成） | **建包时机**：`:263`「同名包判定…在相位 C 生成落盘前完成（直接生成路径，此时无相位 B 可依托）」+ `:267` 表「直接生成三件套（直接生成路径）」——建包与生成同一动作、无独立建包步骤。**memo 建不建**：`:415`/`:627`「memo.md（走拷问路径必产出；**直接生成路径可不产出**）」——不建 | 同一时点判据（`:263`「生成落盘前完成」不区分 create/continue，continue 判定同样在此刻完成） | 同左（`:267` replan 行「先在 task-log.md 落一条重规划记录再改写」，时点仍锚在生成落盘前） |
| ② | gate-0 过 ∧ 信号命中（B 裁剪到维度①） | **顺序**：`:277`（第零步先扫描）→ `:289`（相位 A 澄清）→ `:311-320`（三态路由第②态显式列出）→ `:342-348`（相位 B 起手三步：1.定名 2.判 create/continue/replan 3.建目录+落盘草稿 memo）——顺序对齐骨架 | **起手即判**：`:273`「起手即判，**MUST NOT** 拷问收敛后才发现同名包」 | **task-log 先落记录**：`:269` 表 replan 行「**先**在 task-log.md 落一条重规划记录（原因+时间），**再**改写受影响文件」 |
| ③ | gate-0 未过（B 按类型裁剪） | **裁剪基准**：`:354-359` 表——技术重构「②③④⑤⑦为主，①⑥按需」（5 主+2 按需）、新产品/新项目「①②④⑤⑥⑦（六维；③不选入）」——「六维/五维」均有literal 依据 | 同左（裁剪基准与包生命周期状态无关，仅取决于场景类型） | 同左 |
| — | 中断（B 拷问中） | **已落盘内容在**：`:373-375`「拷问期间每条站稳的承重结论…当场追加写入 memo.md，**MUST NOT** 等收敛后一次性落盘」。**重入认得出**：`:277-285` 第零步扫描 memo.md 状态标记，`:348`「建目录并落盘草稿 memo.md（含…状态：DRAFT 三项）…在开始第一轮拷问之前完成」——DRAFT 状态在拷问全程存在，中断后仍可被扫到 | 同左（起手三步第 3 步对 continue/replan 同样适用于「进入相位 B」这一动作本身，memo.md 的 DRAFT 写入与落盘机制不因包已存在而不同） | 同左 |
| — | 放弃 | **先复述路径→删目录**：`:395-397`「create 场景：**先向操作者复述将被删除的完整路径**，再删除本次新建的包目录」 | **不自动删、记 task-log**：`:398`「continue/replan 场景：**MUST NOT** 自动删除任何内容…改为在 task-log.md 记一行『本次 B 放弃（日期+原因）』」 | 同左（`:398` 同句覆盖 continue 与 replan 两态） |
| — | 中断（C 生成中，只写出 1-2 件） | **memo 仍 DRAFT ⇒ 重入认得出**：`:517`「**MUST NOT** 在相位 B 收敛时就提前改写：B 收敛之后还要走相位 C 生成与 review 处置，此间若中断（如三件套只写出 1-2 个）而已置 FINAL，重入探测（只扫状态：DRAFT）就再也认不出这个半成品包」——FINAL 只在收尾四项全过后才写（`:517` 首句），故 C 相位中断时 memo 必然仍是 DRAFT，第零步可识别 | 同左（同一 `:517` 条款不区分 create/continue/replan，只要该包本轮走过相位 B 产出了 memo） | 同左 |

**注**：本表 6 行中的③④⑤⑥四行（中断-B / 放弃 / 中断-C）在 SKILL.md 中的条款本身是「按
create/continue/replan 分支书写」或「统一适用不分支」，与 6.8 表格「同左」标注一致，未发现
「读起来像有、实则找不到明确文字」的空格。**18 格全部在 SKILL.md 中有可引用的明确条款**，无
需补写。

（附：直接生成路径〔①态〕本身若在相位 C 写到一半中断，memo 可不存在 ⇒ 不被第零步覆盖——这是
design.md Risks 已如实声明的**已知接受缺口**，非本表覆盖范围内的场景，6.8 表格的「中断（C 生成
中）」行特指**走过相位 B、留有 memo** 的路径，两者不冲突。）

---

## 小结

- 6.1：113 处命中，103 处经七条白名单+同形异义/越域判断排除（不属残留），2 处真残留（`SKILL.md:408`
  悬空章节引用、`docs/external-dependencies.md:77-78` 行号漂移）已定位并修复，1 处
  （`openspec/specs/roadmap-planning/spec.md`）明确记为 deferred 交 6.9/archive 步承接。修复后
  非白名单残留为零。
- 6.4：footage fixture 构造→续跑/重入/收尾三路径逐条对应 SKILL.md 条款验证通过，反恒真自查确认
  断言非平凡真，fixture 已清理、`git status` 确认无残留。
- 6.5：真实单文件包 `issues-triage-2026-08/` continue 判定逐条对应 SKILL.md 明文条款（含该文件
  被直接点名为例），全程未修改该包。
- 6.8：6×3=18 格逐格核对，均有 SKILL.md 行号级依据，无未覆盖格。

本票改动文件：`sdflow-roadmap/SKILL.md`（1 处悬空引用修复）、`docs/external-dependencies.md`
（2 处行号引用修复）。均为普通改动，未打 `checkpoint(...)` 完成标签，未勾选 `tickets.md` 复选框。
