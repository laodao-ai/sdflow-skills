# spec-review-report.md — ship-gate-hardening 设计评审

> 阶段二编排评审：Step1 autoplan 广审（CEO/Eng 双镜 + codex design-voice）→ Step2 多镜（HR-TG codex cross-model + 对抗-核验镜）→ Step3 合并去重 + 对抗裁决。**中途不打断**，决策登记本区，人工设计门一次拍板。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="TG-09" evidence="D3 是 change 生命周期终态修复;gate 误判(尤其 D3 假 SHIPPED)=假✅头号失效模式,难回退" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->

## 镜阵与覆盖（规划镜头判定）

- **TG 命中**：TG-09（状态机）· TG-12（决策逻辑）· TG-18（测试）· TG-19/22/23。**领域镜=0**（TG-01/02/03 未命中，纯 Python 编排脚本，显式记录非静默跳过）。
- **HR-TG**：命中 ∩ HR-TG = {TG-09} ≠ ∅ → 单开 codex 领域 cross-model（site=hr-tg）。
- **实跑镜**：autoplan CEO 镜 + Eng 镜（活体 git/pathlib 实验）+ codex design-voice + codex hr-tg + 对抗-核验镜。**规划适配（显式）**：原计划 3 对抗镜的空间已被 autoplan eng 声 + 双 codex 饱和覆盖（防重叠 1.4），改为 1 对抗-核验镜独立复现/证伪 HIGH 发现——防假阳性驱动设计改动。
- 21 条原始 finding → 去重 12 条（BR-1..12）→ 对抗裁决 + 核验镜四条 CONFIRMED。

---

## 决策登记区

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │ [需拍板] Q1  BR-3  完成判据 count vs 集合归属(真实假✅,超 B1/B2/B3 scope) │ 当场修 vs defer
  │ [需拍板] Q2  BR-1  B2 豁免凭生产者非改动类型(重开 grill 已拍的接受取舍)   │ 加分岔 vs 维持
  │ [需拍板] Q3  D3 硬化 bundle(BR-2+BR-4+HRTG-1/2/3/4,改 grill 拍的 D3)     │ 全采纳 vs 讨论
  │ [自动决策] A1-A6  BR-5/6/7/8/9/10 clear-cut 收敛(已直接落 design/tasks)   │ 默认接受可覆盖
  │ [需知悉] N1  BR-12 已知不覆盖债台账(本批次净增3条绕过面)                 │ 设计门过一遍
  │ [已裁掉] X1  「BR-1 是设计盲点」——核验镜证 BR-1 已 grill 登记接受,非盲点  │ 降级为需知悉
  └────────────────────────────────────────────────────────────────────────┘
```

### [需拍板] Q1 — BR-3：完成判据 count vs 集合归属（**最高优先**）
- **裁决**：CONFIRMED（对抗-核验镜活体实跑）。`decide()` 用 `len(done) < n` 按**基数**判齐（`ship_gate.py:233`），不校验 done 任务号 ⊆ plan 任务号。plan=task1/task2（N=2）、只完成 task1、另有计划外 `checkpoint(task9-stray)`（错号/遗留/merge 内提交均可产生）→ done={"1","9"}，len=2 不 <2 → **实测输出 RUN_CODE_REVIEW，task2 从未完成却过完成门**。既有 `test_merged_branch_inner_commits_do_enter_window` 已证 task9 会进 done_tasks，"只差补 task1 即成灾"。
- **为何需拍板**：这是**真实假✅**（gate 完成门自身给错，非约定层），但 **D1-D4 完全不修**、超出 B1/B2/B3 原 scope（是第 4 个缺陷）。核验镜特别指出：四条里唯此条"沉默假✅ 且设计未触及"，优先级应最高。
- **选项**：**A（推荐）当场纳入本 change 修**——判据改 `plan任务号集 ⊆ done_ids`（或 `len(done_ids ∩ plan_ids) >= n`），补 task1+task9 缺 task2 红测。理由：与 D1 同函数（`done_task_ids`/`decide` 进度逻辑）、D1 纳入 sha 自身 task 会**放大**此假✅、修法小（解析 plan 任务号交集）、证据新鲜。**B）defer 进 buglist 另开 change**——保持本 change scope 纯净（只 B1/B2/B3），但把一个已知活体假✅ 留在 main 上直到下轮。
- **后果**：选 B 则 gate 完成门带一个已复现的假✅ 继续服役；选 A 则本 change scope 从「3 缺陷」扩为「4 缺陷」（blast radius 内、<1 天，符合 boil-the-lake）。

### [需拍板] Q2 — BR-1：B2 豁免凭生产者/subject 而非改动类型
- **裁决**：CONFIRMED 真机制，**但已是 design 自陈的 accepted known-gap**（grill Q2 记入 design.md:118 + 头注释）。核验镜明示"不驱动新设计改动，除非团队想推翻该取舍"。
- **为何仍需拍板**：codex-design + CEO-F1 + CEO-F6 **三声独立**指出该取舍的 soundness 洞——豁免认 subject 前缀不认"改的是措辞还是语义"，而 code-review 本职就会对 design.md 做语义修正 → 语义级设计改动被静默豁免 → 未经二审随档 ship = gate 头号失效模式（静默假✅）。这**重开了你 grill 亲手拍的接受取舍**，不能静默反转，交你定。
- **选项**：**A）维持现取舍**（约定级安全边界 + 已登记窗口，grill Q2 结论）——成本零，接受"经 impl-review 豁免的语义改动静默 ship"窗口。**B）加改动类型分岔**（CEO 推荐）——语义改 design.md → 走重申锚 `design-reaffirmed`/回落重跑 spec-review；纯勾选/措辞 → impl-review 豁免。用"改动类型"而非"生产者"分叉，把 CEO-F6 指出的"重申锚可 grep 审计 + 前移基线"增益拿回。代价：扩契约面（新锚行 × 头注释 × SKILL 模板 × 契约测试），且"如何机判语义 vs 措辞"本身是难题（回到 D2-c hunk 分析的复杂度）。
- **推荐**：倾向 **A 维持**——B 的"机判语义 vs 措辞"落不了地（除非人工标注，那就不是自动门），CEO 的分岔在"纯装饰 vs 语义"的判定上会撞回 D2-c 已弃的 hunk 复杂度；但增益（可审计）真实。**这条是你的取舍，我不替你反转，列出供你定**。

### [需拍板] Q3 — D3 硬化 bundle（BR-2 + BR-4 + HRTG-1/2/3/4）
- **裁决**：BR-2/BR-4 CONFIRMED（域原语层活体实证，D3 尚未落码，可在实现时一并修）。这些**改的是 grill 拍的 D3**（change 域判据被评"本批次质量最高"，但评审发现它**不完整**）。
- **子项（建议全采纳）**：
  - **BR-2 + HRTG-1（假✅ 高危）**：D3 短路判 SHIPPED 只凭"archive 在 base 树"，**不读 archived 的 verify=PASS 锚**；反例：手工 `mkdir` 空壳目录 commit+merge → 假 SHIPPED。且 active 存在时 final SHIPPED 路径（`:287` `handoff && archived && merged`）也能被旧/垃圾 archive glob 触发。→ **SHIPPED 前追读 archived `verify-report.md` 的 `verify=PASS` 锚**（CLI 归档必携带，近零漏报）；active 存在时 archived 谓词收紧（或 fail-safe UNKNOWN）。与「盘面即状态、锚即 ground truth」一致——D3 在终态却弃锚改信目录存在性，自相矛盾。
  - **BR-4（发现域 ≠ 判据域）**：发现用文件系统 glob（工作树域），判据用 `ls-tree base`（git 域）。两向失效均实跑：从早于归档的分支查已 ship change → 工作树无目录 → 假 REFUSE；未跟踪垃圾目录 → 假 RUN_VERIFY。→ **发现也走纯 git 域**：`git ls-tree HEAD` ∪ `git ls-tree <base>` 列 archive 子项，在 base → SHIPPED、仅 HEAD → RUN_VERIFY、皆无 → REFUSE。工作树无关、天然忽略未跟踪垃圾。
  - **HRTG-2**：`run_git()` 把 git 错误与"路径不在树"都折叠成空串 → 无法区分「base 不存在→UNKNOWN」vs「ls-tree 空→RUN_VERIFY」。→ 加返回码可见 git helper + 单一 `base_ref()`（main/master 优先级 + 缺失语义）。
  - **HRTG-3**：detached HEAD 契约冲突——状态机说 detached→UNKNOWN，但 change 域判据下 detached 对 D3 已无关。→ 调和：D3 用 change 域后 detached 不阻断 D3，更新 UNKNOWN 契约 + 补 detached+archived=SHIPPED 测试。
  - **HRTG-4**：`--change` 未校验，`* ? []` 会被当 glob 元字符（active 查找当字面、archive 查找当模式，两域不一致）。→ 入口强制 change 为 slug（`[a-z0-9][a-z0-9-]*`）或 `re.escape(change)` fullmatch 替 glob。
  - **BR-9**：同名 change 多次 ship（多个日期前缀归档）→ glob 多命中，`<dir>` 取哪个未定义。→ 纯 git 域方案天然解决：**匹配集任一在 base → SHIPPED**。
- **选项**：**A（推荐）全采纳**，实现 D3 时按上述落码（task 3.1/3.2 已标待此拍板修订）。**B）逐条讨论**（若你对某子项有异议）。
- **后果**：不采纳 BR-2 = D3 带一个假 SHIPPED 面上线（与它要修的 B3 同类）；不采纳 BR-4 = grill 的"change 域跨分支也对"主张名不副实。

### [自动决策] A1-A6（已直接落 design/tasks/spec，标 [spec-review-amendment]）
- **A1 BR-7**：D2 豁免用精确式 `== "checkpoint(impl-review)" or startswith("checkpoint(impl-review):")`（裸闭合前缀仍收 `)evil` 尾串）。→ design D2 / tasks 2.2-2.3 / spec Scenario〔B2〕。
- **A2 BR-8**：D1 头注释窗口块 `:30-32` + CONTINUE_IMPL reason 串 `:241` 同步为闭区间（契约漂移收口）。→ tasks 1.4（新增）。
- **A3 BR-5**：豁免 token 加与 checkpoint-commit.sh step 名双向钉死的契约测试。→ tasks 2.5（新增）。
- **A4 BR-6**：is_stale 护栏「MUST NOT 加 --no-merges/--first-parent」+ 空 subject 帧测试 + 多提交交错测试（分帧 bug 杀伤方向=假豁免）。→ tasks 2.2-2.3。
- **A5 BR-10**：契约表 RUN_VERIFY 行补「归档未并 base」变体。→ tasks 3.3。
- **A6 BR-9**：glob 多命中改「任一在 base 树→SHIPPED」（并入 Q3 纯 git 域）。→ tasks 3.3 注 + Q3。

### [需知悉] N1 — BR-12：已知不覆盖债台账（CEO-F7）
本批次向头注释「已知不覆盖」净增 3 条凭约定信任的绕过面（①伪造/手工 impl-review subject ②经豁免的语义改动静默 ship ③精确同名旧档假 SHIPPED）。模式=每消一个假阳性就加一条绕过面，确定性真、可靠性被掏空。**设计门建议对每条问「若是真实攻击/事故路径，能否从 git 留痕发现」**：「发现不了」的（如②静默语义改动）必须升级处置（加审计锚，即 Q2-B）；「发现得了」的（rebase 伪造 log 可查）方可接受。BR-11（D3 next=sdflow-done 对 archived-unmerged 入口的链假设）转 hand-off/done 侧确认。

---

## 各镜 findings（带置信/严重度，escalate-not-drop）

| ID | 来源 | 严重 | 置信 | 裁决 | 一句 |
|---|---|---|---|---|---|
| BR-1 | codex-design#2/CEO-F1/F6 | high | 高 | CONFIRMED(已登记接受) | B2 凭生产者非改动类型,语义改静默豁免 → Q2 |
| BR-2 | codex-design#2/#3/CEO-F2/HRTG-1 | high | 高 | CONFIRMED | D3 SHIPPED 不读 verify 锚 + active 存在 final 路径旧档触发 → Q3 |
| BR-3 | codex-design#1/核验镜 | high | 高 | CONFIRMED(活体) | 完成判据 count 非集合归属,计划外号顶替 → Q1 |
| BR-4 | Eng-F2/核验镜 | medium | 高 | CONFIRMED(双向实跑) | 发现工作树域 vs 判据 git 域不一致 → Q3 |
| BR-5 | CEO-F3 | medium | 高 | 采纳 | impl-review token 无契约测试 → A3 |
| BR-6 | CEO-F4/Eng-F3 | medium | 中 | 采纳 | is_stale 双scope重构:code域对称+--no-merges+分帧测试缺口 → A4 |
| BR-7 | codex-design#4 | medium | 高 | 采纳 | 闭合前缀仍收 )evil 尾串 → A1(精确式) |
| BR-8 | Eng-F1 | medium | 高 | 采纳 | D1 头注释窗口块/reason 串漂移无任务 → A2 |
| BR-9 | Eng-F4 | low-med | 中 | 采纳 | 锚死 glob 多命中 <dir> 未定义 → A6/Q3 |
| BR-10 | Eng-F5 | low | 高 | 采纳 | 契约表 RUN_VERIFY 行未更新 → A5 |
| BR-11 | Eng-F6 | low | 中 | 转下游 | D3 next=done 对 archived-unmerged 链假设 → N1 |
| BR-12 | CEO-F7 | medium | 高 | 需知悉 | 已知不覆盖债台账净增3条 → N1 |
| HRTG-2/3/4 | codex-hrtg | medium | 中-高 | 采纳 | base_ref/run_git 返回码 · detached 契约 · change slug 校验 → Q3 |

**确认无发现（多声正面确认）**：D1 窗口机制（sha 非 merge、set 去重）· D3 base 树可达性判据（change 域分类，评"本批次质量最高修订"）· D3 短路顺序 · 锚死 glob 后缀精度 · D2 精确式拒 -fix/X · 既有 SHIPPED 测试不扰动 · 三修复代码路径两两互不交叠 · prose/脚本备选否决站得住。

**已裁掉（反静默压制，留痕）**：
- **X1**：「BR-1 是设计盲点/未考虑」——裁掉。对抗-核验镜证 BR-1 是 grill Q2 已显式权衡（D2-c/D2-b 均弃后）记入 design.md:118 + 头注释的**接受取舍**，非盲点。降级为 Q2「是否推翻既有取舍」而非「补一个漏掉的洞」。

---

## 收敛口

评审揪出 3 条需拍板 + A1-A6 clear-cut 收敛。已过设计 HARD-GATE。

## 拍板记录区（设计门 · 用户 AskUserQuestion 批准）

- **Q1 = 当场纳入本 change 修**（BR-3）→ 落 design **D5**（完成判据集合归属 `plan_ids ⊆ done_ids`）+ tasks **§4 B4**（5.1-5.3→4.1-4.3）+ spec Scenario〔B4〕；scope 从 3 缺陷扩为 **4 缺陷**。
- **Q2 = 维持 B2 现取舍**（BR-1）→ D2 不动（约定级安全边界 + 已登记窗口）；proposal 记「Q2 维持」理由（机判语义 vs 措辞落不了地，撞回已弃 D2-c）。
- **Q3 = D3 硬化 bundle 全采纳**（BR-2/BR-4/HRTG-1/2/3/4）→ 落 design **「D3 硬化 bundle」H1-H6** + tasks 3.1（×10 用例）/3.2（按 H1-H6 落码）+ spec Scenario〔B3+D3 硬化〕。
- **A1-A6**（BR-5/6/7/8/9/10）clear-cut 已直接落 design/tasks/spec。
- **N1**（BR-12 债台账）+ **BR-11**（done archived-unmerged 入口）→ 转下游 hand-off/todolist 关注，非本 change 阻塞。

设计门拍板已发生，主 session 回写机判锚（下行）：

<!-- ship-gate: design-approved -->

**下一步**：按用户 standing 指令，自动接 `/sdflow-ship` 跑阶段三到 merge。
