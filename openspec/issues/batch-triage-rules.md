# 大扫除批分诊判据（batch-triage-rules）

> **定位**：本文件是 **sdflow-skills 仓自有**的规划纪律文档（**本仓-local**），
> 不是 `sdflow-init/assets/workflow/` 那套经 `resolve-workflow.sh` 解析、随 `sdflow-init update`
> 回灌下游消费仓的 workflow bundle 规则。它只服务本仓 `openspec/issues/` 的 issues 池分诊，
> 应用时机是 **pre-diff**（做 consolidation-planning 时，手头只有 issue/todo 描述 + 落点文件
> 路径，尚无任何实现 diff 可读）。判据形态是**纯规则 checklist**，供 human/model 应用——
> 本文件不引入、也不打算引入任何判器脚本或 pytest（`batch-triage-strategy` 本身即因此塌缩为
> 纯 markdown 变更）。
>
> **与 Leg1 `trivial_shape.py` 的关系（显式 cross-ref）**：`sdflow-init/assets/workflow/tools/trivial_shape.py`
> 是 code-review 阶段的「无逻辑面白名单」判器——它 **post-diff** 工作（吃真实 diff 的文件形状：
> 注释符改动/文档扩展名/仅新增 tests/纯展示常量等），机判后放行免过 code-review Step2。本文件
> 的判据与它是**同类判据、非同一脚本**：语义标准同源（都判「无逻辑面/低危」），但本判据
> **pre-diff**——issue 分诊时没有 diff 可读，只能凭 issue 描述 + 预期落点路径做近似判定，
> 因此不能、也不打算字面复用 `trivial_shape.py`。凡本文件提到「同类 Leg1」，均指这层语义同源
> 关系，不代表调用同一份代码。

---

## 一、三元分类（互斥穷尽）

每个 issues 池待处理项，分诊时 MUST 归入且仅归入以下三类之一——三元分类 **互斥且穷尽**，
不允许「都不占」或「都占一点」的模糊态：

### 1. 相关合批

满足**完整** BASE-18 AND 门——**同 capability ∧ 高耦合 ∧ 低增量**三腿**皆**满足，走
`consolidation-plan.md` 既有 REC-1/2/3 框架处理。

> **注意（第三腿不可省）**：同 capability ∧ 高耦合但**高增量**的项 **MUST NOT** 自动归入
> 相关合批——AND 门三腿必须全满足，低增量这一腿不满足就不算数（REC-3 先例：低增量✗仍被列为
> 候选是一次偏差，重划时须订正）。这类项改归**单开 change** 或**拆分**后再各自判。

### 2. 大扫除批

与其余待处理项**正交**（非同 capability，或虽同 cap 但低耦合）∧ 经**二、issue 级判据**判定为
**无逻辑面 ∧ 低危** ∧ **非行为面路径**（见下方硬排除）的项。

**硬边界（MUST）**：大扫除批只装个体琐碎/低危的正交项——**禁装任何含逻辑面的项**，即
**MUST NOT 装有逻辑面的东西**进大扫除批。此边界优先于任何合批收益考量：降成本红线是 MUST
NOT 靠砍评审安全换取，一旦发现某项含逻辑面，无论它能省多少轮次，都必须被移出大扫除批。

### 3. 单开 change

其余所有情况——包括：
- 含逻辑面的项（无论描述看起来多琐碎）；
- 落点命中行为面路径的项（即便内容 cosmetic）；
- 判据存疑、无法确认为琐碎/低危的项（fail-closed 默认排除的落点）；
- 同 cap ∧ 高耦合但高增量、AND 门第三腿不满足的项。

**含「延迟绑定/搭便车」子态**：单开不等于「必须立刻单开一个 change」——允许暂缓，等未来
恰好有 change 触碰同一块代码时，顺手把这项带上（省一次固定循环成本）。这是单开类目下的一个
延迟绑定子态，不是第四个分类；判定仍是「单开」，只是执行时机延后。

**互斥穷尽自检**：任给一项，先问「AND 门三腿是否全满足」——是则相关合批，结束；否则问
「是否正交 ∧ 无逻辑面 ∧ 低危 ∧ 非行为面路径」——是则大扫除批候选，结束；否则单开（含延迟
绑定子态）。三问链覆盖所有输入，任一步「是」即终止，不存在既非相关合批又非大扫除批又非
单开的第四态。

---

## 二、issue 级「无逻辑面 ∧ 低危」判据

### 判据输入面

判据只能吃两样东西（因为 pre-diff）：
1. issue/todo 的文字描述；
2. 该项预期的落点文件路径。

没有 diff、没有实现细节可读。只有「无逻辑面 ∧ 低危」都成立，才放行进入大扫除批候选。

### fail-closed MUST 纪律

- **当无法确认一项为琐碎/低危时，默认排除**（退化为单开）——这是 MUST 纪律，不是 SHOULD
  建议。存疑一律标「存疑→单开」，不允许「先纳入、以后再看」。
- **显式声明（诚实口径）**：本判据是纯规则、**无脚本自动兜底**，也**非机械可验证的不变量**。
  「误纳率恒为 0」这个目标，靠的是应用判据者遵守「存疑即排除」的纪律，不是任何脚本/gate
  能保证的机械性质。本文件不得、也未声称有自动化门禁替应用者兜底判断——判断的责任在
  执行分诊的 human/model 身上。

### 行为面路径硬排除（MUST，Q1 定案——采纳 Leg1 路径守卫）

判据 MUST 把「item 落点命中 Leg1 `BEHAVIOR_PATH_PATTERNS`」当作**硬排除**信号，与内容是否
cosmetic **无关**：

```
BEHAVIOR_PATH_PATTERNS = (
    "sdflow-init/assets/workflow/*",
    "*/assets/workflow/*",
    "SKILL.md", "*/SKILL.md",
    "workflow.md", "*/workflow.md",
    "*ship_gate.py",
    "*trivial_shape.py",
)
```

即：落点是 `SKILL.md`、`*/assets/workflow/*`、`workflow.md`、`*ship_gate.py`、
`*trivial_shape.py` 等的项——**无论 item 描述多 cosmetic**（比如「决策区加个边框」「链接可
点击」这种听起来纯展示的改动）——只要落点命中上述路径模式，**一律硬排除**出大扫除批，归
单开或相关合批。

**这是「同类 Leg1」的具体含义**（避免被弱化误读）：不是「人看一眼描述、觉得是 cosmetic
就放行改 SKILL.md」，而是**继承 Leg1 路径守卫本身的保守偏 NOT_EXEMPT 立场**——这些文件
承载行为（markdown 改动也可能悄悄改变行为契约，机器/人眼都分不清「纯展示」与「行为」的
边界在哪一行），所以路径命中即排除，不做例外协商。这一条是本判据里最容易被打折的一条，
必须当硬排除执行。

---

## 三、大扫除批聚合上限（三类落法）

即使每项个体低危，聚合起来不必然低危——大扫除批 SHALL 受聚合上限约束。上限分三类落法，
严格程度不同，不可混为一谈：

### 1. 有上限本身 = MUST

规则 **MUST** 规定一个文件数/项数上限；一旦候选规模**超限**，**MUST** 拆分成多包，或书面
写明理由后才可保留原样。「存在上限、超限须拆」这件事本身是 MUST（不是建议）——防止 30
个散项照样打包成一批、稀释评审注意力。

### 2. 上限数值 = SHOULD 可调

具体数值目前**无实测基线**，标注为可调（tunable）默认值，非硬性精确值：
- 文件数：SHOULD ≤ 约 **~10 文件 / ~8 项**；
- 目录跨度：不设硬数，跨度越大越倾向拆分（人工判断）；
- CI 面积：碰**重型 CI 路径**的项 **SHOULD** 排除出 sweep——大扫除批应是「跑一遍轻量 CI
  即过」的量级，不该背上重型 CI 触发面。

### 3. 含生成物 = 硬 MUST 隔离

任何触碰**生成物**（如再生的 `openspec/retro/report.md`、重建的 `openspec/INDEX.md`）的项
**MUST NOT** 混入大扫除批——这类项须单独走**「再生 commit」**，不与手写改动的大扫除批混在
一起提交。理由：生成物 diff 与手写 diff 混在一批里，reviewer 无法分辨哪些是手改、哪些是
再生副作用，直接坏 diff 可读性；这不是规模调参问题，是正确性/可审计边界，不打折扣。

### 每项结构化判定记录（MUST，fail-closed 问责机制）

每个大扫除批候选 **MUST** 在 `consolidation-plan.md` 落一条**结构化判定记录**，字段模板：

```
{item ID · 精确落点路径 · 为何无逻辑面 · 低危证据 · 生成物/CI/目录跨度检查结果 · 归属(候选/排除) + 排除理由}
```

- `item ID`：issue/todo 池的唯一 ID（如 `T50`）；
- `精确落点路径`：具体文件路径，不是模糊描述；
- `为何无逻辑面`：一句话依据；
- `低危证据`：为何判定低危；
- `生成物/CI/目录跨度检查结果`：三项聚合上限检查各自结论；
- `归属`：候选 或 排除，排除须附理由。

**MUST**：若落点路径宽泛（如笼统写「workflow bundle 多处」而未列出精确文件）或证据不足，
一律标「**存疑→单开**」——纯规则无脚本兜底，这条结构化判定记录就是 fail-closed 纪律的可
审计落盘，防止判据退化成一句「口头纪律」而无从核查。

---

## 四、一项一 commit（硬 MUST，item 粒度）+ 执行协议 + 验证锚

### 一项一 commit = 硬 MUST

大扫除批作为**一个 change** 走**一轮评审**（一个 PR）；但其内部实现 **MUST** 每个 item
（一个 issue/todo ID）对应**独立一个 commit**——**item 粒度，非文件粒度**：同一份文件里的
两个不同 item（比如同文件两处 typo，分属两个 issue ID）仍然是**两个 commit**，不得因为
「同一个文件」就合并成一个 commit。目的是保证任一坏项都能被单独 revert，不牵连其余项。

### 执行协议 MUST（因 `checkpoint-commit.sh` 用 `git add -A`）

由于本仓 checkpoint 脚本内部执行 **`git add -A`**，会把工作区里**所有**未提交改动一并纳入
当次 commit——这意味着一旦累积多个 item 的编辑再一起 commit，`git add -A` 会静默把它们
裹进同一个 commit，破坏 item 粒度（`buglist` 里的 `B4`/`B1` 一类同根因问题已经真实爆过）。
因此实现 MUST 严格串行执行：

1. 编辑**一个** item；
2. **立即** checkpoint（commit）；
3. 确认 `git status --porcelain` 输出为空（工作区干净）；
4. 确认干净后，才动手碰下一个 item。

**MUST NOT** 先累积多个 item 的编辑、之后才统一 commit。

sweep 的实现 plan **MUST** 为每个 item 生成一个独立的 `### Task N: <itemID> …`，checkpoint
的 slug/描述里须带上 item ID，方便回溯每个 commit 对应哪个 item。

### 验证锚 MUST

verify / code-review 阶段 **MUST** 核对：

```
候选 item 数 == 独立 task 数 == 独立 commit 数
```

三者须**相等**。之所以靠 verify 显式核对而非 gate 自动检查，是因为 `ship_gate.py` 的
`TAG_RE` 目前只识别 `task<N>` 这种任务标签，不识别 item ID，机器无法自动核对这条不变量——
这条核对责任落在 verify 这一步的人工/模型显式动作上，不是机械保证。收尾自检可直接跑：

```bash
git log --oneline <base>..HEAD | wc -l   # 应等于候选 item 数、等于 plan 独立 task 数
```

数不相等，视为违反 item 粒度，须回溯拆分修正，不得直接放行。

---

## 五、落点纪律（本仓-local）+ 发布 deferred

### 本仓-local 落点

本判据规则 **落在本仓 `openspec/issues/`**（与 `consolidation-plan.md` 相邻），是
sdflow-skills 仓自有的规划纪律文档，**MUST NOT** 拷进 `sdflow-init/assets/workflow/` 那份
bundle，**MUST NOT** 部署到任何下游消费仓。因为它不是经 `~/.sdflow/hack/resolve-workflow.sh`
解析的 workflow 规则，所以**不涉及**回灌纪律、不涉及 `openspec/INDEX.md` 的 `index-section.md`
渲染 snippet、也不涉及 BASE-18 定义悬空的问题——这些都是 bundle 部署机制才要操心的事，本
文件绕开它们，纯粹是本仓自用产物。

### 发布 deferred（MUST 记录）

向下游消费仓发布这套判据，**推迟到本仓 dogfood 验证之后**——必须先在本仓真跑至少一个大
扫除批，拿到「省了评审轮次、且未掉安全」的实证，才能作为**未来的独立 change** 去发布（届时
要做的事包括：泛化掉本仓依赖、把 BASE-18 定义落进 bundle、修复本次发现的 4 处部署机制问题、
给 `workflow.md` 加 issues-sweep 钩子、并 cross-ref `spec-workflow` 里「workflow bundle
改动须走权威源」的既有 Requirement）。

若 dogfood 验证发现候选池太薄、或价值边际不划算，**可以退化为**在 `consolidation-plan.md`
里记一句注记、**不发布**——这同样是一个有效结论，不是失败结果。此纪律对齐 Leg1 的先例：
`trivial_shape.py` 本身也是先在本仓验证有效之后，才进入 bundle 铺给下游。

---

## 六、判据决策流（速查，ASCII）

```
issue 池待处理项
      │
      ▼
 ┌──────────────────────────────┐ 是 ┌──────────────────────────┐
 │ 完整 BASE-18 AND门:            ├───▶│ 相关合批                  │
 │ 同cap∧高耦合∧低增量 三腿?     │    │  REC-1/2/3 既有框架        │
 └───────────┬──────────────────┘    └──────────────────────────┘
             │ 否（正交；或同cap高耦合但高增量→单开/拆）
             ▼
 ┌─────────────────────────┐   否（有逻辑面/存疑/命中行为面路径）
 │ issue级判据: 无逻辑面∧低危 ├──────────────┐
 │ ∧ 非行为面路径?           │               ▼
 └───────────┬─────────────┘        ┌──────────────────┐
             │ 是                    │ 排除 → 单开change │ ← fail-closed
             ▼                       │（含延迟绑定子态） │
 ┌─────────────────────────┐        └──────────────────┘
 │ 聚合上限内?(文件/目录/   │   否
 │  生成物/CI面积)          ├──────▶ 另起一包 / 拆分
 └───────────┬─────────────┘
             │ 是
             ▼
      大扫除批（一轮过，item 粒度一项一 commit）
```
