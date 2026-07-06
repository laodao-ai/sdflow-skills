# batch-triage-strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 sdflow-skills 本仓立一套「大扫除批」分诊判据（纯 markdown 规则 + consolidation-plan 三元重划 + INDEX 登记），把散落琐碎正交项的合批规则化，且不砍评审安全、不进 bundle。

**Architecture:** 纯文档 change——无脚本、无 pytest（grill 定案 Q-a）。三份产物：①新建 `openspec/issues/batch-triage-rules.md`（判据 checklist + 3 硬 MUST + fail-closed + Leg1 路径守卫 + 聚合上限）；②重划 `openspec/issues/consolidation-plan.md`（加大扫除批维度 + 三元标注 + 刷新 stale + worked example）；③`openspec/INDEX.md` 登记 batch-triage capability。落点全在本仓 `openspec/issues/`，**MUST NOT** 进 `sdflow-init/assets/workflow/` bundle（Q2 定案）。

**Tech Stack:** Markdown only. 验证靠内容核对锚（grep 关键词 + 人读），非自动化测试。

## Global Constraints

> 每个 task 的 requirements 隐含包含本节，值逐字取自 design.md / spec.md。

- **本仓-local，禁进 bundle（Q2 定案 D6）**：所有新增/修改文件 MUST 落 `openspec/issues/`（或 `openspec/INDEX.md`）；MUST NOT 落 `sdflow-init/assets/workflow/`、MUST NOT 动 `trigger-catalog.md`/bundle INDEX snippet、MUST NOT 跑回灌。
- **红线：降成本 MUST NOT 靠砍评审安全**——判据只放行「无逻辑面 ∧ 低危 ∧ 非行为面路径」，逻辑面/行为面路径一律全审。
- **fail-closed（D4）**：判据存疑一律排除、退化为单开；规则 MUST NOT 声称有自动兜底门保证误纳率 0（纯规则纪律，非机械不变量）。
- **行为面路径硬排除（Q1 定案 D8）**：落点命中 Leg1 `BEHAVIOR_PATH_PATTERNS`（`SKILL.md`、`*/assets/workflow/*`、`*ship_gate.py`、`*trivial_shape.py`）的项 MUST 排除，无论描述多 cosmetic。
- **术语统一**：全文用「三元标注」（相关批 / 大扫除批候选 / 单开），勿用「二分」。
- **checkpoint 格式（gate TAG_RE 契约）**：每 task 收尾 commit 用
  `~/.sdflow/hack/checkpoint-commit.sh "task<N>-<slug>" "<中文描述>"`，落出 `checkpoint(task<N>-<slug>): …`，须匹配 `checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`。

---

### Task 1: 新建 `openspec/issues/batch-triage-rules.md`（判据规则文档）

覆盖 tasks.md 组 1（判据规则 1.1-1.4）+ 组 2（规则文档 2.1-2.5）。这是本 change 的核心产物：一份 pre-diff、纯规则的分诊判据 checklist。

**Files:**
- Create: `openspec/issues/batch-triage-rules.md`

**Interfaces:**
- Consumes: Leg1 `trivial_shape.py` 的 `BEHAVIOR_PATH_PATTERNS`（交叉引用，非复用）；BASE-18 AND 门定义（同 cap ∧ 高耦合 ∧ 低增量）。
- Produces: `consolidation-plan.md`（Task 2）会引用本文件的判据流 + 每项结构化判定记录格式 + 三元分类定义。

- [ ] **Step 1: 写文件头 + 定位 + 与 Leg1 的关系**

文件头须点明：本仓-local 规划纪律文档、非 workflow bundle 规则、pre-diff 应用、纯规则无脚本。须含一句显式 cross-ref：与 Leg1 `trivial_shape.py`「无逻辑面白名单」**同类判据、非同一脚本**（后者 post-diff 判形状、依赖 diff；本判据 pre-diff 仅凭 issue 描述 + 落点路径）。

grep 锚（Step 末验证）：`本仓-local`、`同类判据、非同一脚本`、`pre-diff`、`trivial_shape.py`

- [ ] **Step 2: 写三元分类定义（互斥穷尽）**

三分类 checklist，每类给判定条件：
- **相关合批**：满足完整 BASE-18 AND 门（同 capability ∧ 高耦合 ∧ **低增量**三腿皆满足）→ 走 REC-1/2/3 既有框架。注明「同 cap ∧ 高耦合但**高增量** MUST NOT 自动进相关合批（第三腿不满足）→ 归单开/拆分」。
- **大扫除批**：与其余项正交（非同 cap / 低耦合）∧ 经 issue 级判据判为无逻辑面 ∧ 低危 ∧ 非行为面路径。
- **单开 change**：其余；含「延迟绑定/搭便车」子态（暂缓、等未来碰这块的宿主 change 顺手带）。

grep 锚：`三元`、`互斥`、`穷尽`、`低增量`、`延迟绑定`

- [ ] **Step 3: 写 issue 级「无逻辑面 ∧ 低危」判据 + fail-closed 纪律 + 行为面路径硬排除**

- 判据输入面 = issue 描述 + 落点文件路径（pre-diff，无 diff）；无逻辑面 ∧ 低危才放行。
- **fail-closed MUST 纪律**：「当无法确认一项为琐碎/低危时，默认排除（退化为单开）」；显式声明「无脚本自动兜底、非机械保证——此为应用者纪律，非脚本可验证的机械不变量」。
- **行为面路径硬排除 MUST（Q1/D8）**：落点命中 Leg1 `BEHAVIOR_PATH_PATTERNS`（`SKILL.md`、`*/assets/workflow/*`、`*ship_gate.py`、`*trivial_shape.py` 等）→ **硬排除，无论描述多 cosmetic**。写清这是「同类 Leg1」的具体含义：不是"人看描述判 cosmetic 就放行"，而是继承 Leg1 路径守卫的保守偏 NOT_EXEMPT 立场。

grep 锚：`fail-closed`、`存疑`、`默认排除`、`无脚本自动兜底`、`BEHAVIOR_PATH_PATTERNS`、`硬排除`

- [ ] **Step 4: 写聚合上限（三类落法）+ 每项结构化判定记录格式**

聚合上限分三类（对齐 spec.md「大扫除批聚合上限」Requirement）：
- **有上限本身 = MUST**：MUST 规定文件数/项数上限，超限 MUST 拆分或书面说明理由。
- **上限数值 = SHOULD 可调**：≤ ~10 文件 / ~8 项、目录跨度（标「无实测基线，tunable」）；碰重型 CI 路径的项 SHOULD 排除出 sweep。
- **含生成物 = 硬 MUST 隔离**：碰生成物（再生 `retro/report.md`、重建 `INDEX.md`）的项 MUST NOT 混入，须单独走「再生 commit」。

**每项结构化判定记录格式（MUST，fail-closed 问责）**——给出可套用的字段模板：
`{item ID · 精确落点路径 · 为何无逻辑面 · 低危证据 · 生成物/CI/目录跨度检查结果 · 归属(候选/排除) + 排除理由}`。注明「落点路径宽泛（如『workflow bundle 多处』）或证据不足 → MUST 标『存疑→单开』」。

grep 锚：`聚合上限`、`~10 文件`、`SHOULD`、`含生成物`、`再生 commit`、`结构化判定记录`

- [ ] **Step 5: 写「一项一 commit」硬 MUST + 执行协议 + 验证锚**

- **一项一 commit = 硬 MUST（item 粒度，D7）**：sweep 作一个 change 走一轮评审（一 PR），内部 N item = N commit（item = 一个 issue/todo ID，非文件——同文件两 typo 仍两 commit）。
- **执行协议 MUST**（因 `checkpoint-commit.sh` 用 `git add -A`）：逐 item 严格串行——编辑一 item → 立即 checkpoint → 确认 `git status --porcelain` 干净 → 才碰下一项；MUST NOT 累积多 item 后才 commit（buglist B1 同根因爆过）。
- **验证锚 MUST**：verify/code-review 核对 `候选 item 数 == 独立 task 数 == 独立 commit 数`（三者相等；因 gate `TAG_RE` 只认 `task<N>` 不认 item ID，此核对靠 verify 显式做）。

grep 锚：`一项一 commit`、`item 粒度`、`git add -A`、`串行`、`候选 item 数 == 独立 task 数 == 独立 commit 数`

- [ ] **Step 6: 写落点纪律（本仓-local Q2）+ 发布 deferred**

- 规则落本仓 `openspec/issues/`，MUST NOT 进 bundle / 部署下游 / 涉回灌 / INDEX snippet / BASE-18 悬空。
- **发布 deferred MUST 记录**：向下游发布推迟到本仓 dogfood 验证之后（真跑 ≥1 大扫除批、有证据省了轮次未掉安全），才作未来独立 change 发布；候选池太薄可退化为注记不发布（亦为有效结论）。对齐 Leg1（验证后才进 bundle）。

grep 锚：`本仓-local`、`MUST NOT 进 bundle`、`发布 deferred`、`dogfood`

- [ ] **Step 7: 内容自检（无自动化测试，靠 grep 锚 + 人读）**

Run（逐条确认命中，全部非空即通过）：
```bash
cd "$(git rev-parse --show-toplevel)"
for kw in "同类判据、非同一脚本" "三元" "低增量" "fail-closed" "BEHAVIOR_PATH_PATTERNS" "硬排除" "聚合上限" "含生成物" "再生 commit" "结构化判定记录" "一项一 commit" "git add -A" "本仓-local" "发布 deferred"; do
  printf '%-40s' "$kw"; grep -c "$kw" openspec/issues/batch-triage-rules.md || true
done
```
Expected: 每个关键词计数 ≥ 1。

再确认 3 硬 MUST 齐全（禁逻辑面 / 生成物隔离 / 一项一 commit）：
```bash
grep -nE "禁.*逻辑面|MUST NOT 装.*逻辑面" openspec/issues/batch-triage-rules.md
grep -n "含生成物" openspec/issues/batch-triage-rules.md
grep -n "一项一 commit" openspec/issues/batch-triage-rules.md
```
Expected: 三条均有命中。

- [ ] **Step 8: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "task1-batch-triage-rules" "新建 batch-triage-rules.md 判据规则(3硬MUST + fail-closed + Leg1路径守卫 + 聚合上限)"
git status --porcelain   # 期望空
```
Expected commit subject: `checkpoint(task1-batch-triage-rules): …`

---

### Task 2: 重划 `openspec/issues/consolidation-plan.md`（加大扫除批维度 + 三元标注）

覆盖 tasks.md 组 3（3.1-3.3）。在既有「相关合批（AND 门）」框架旁增大扫除批维度，对项做三元标注，刷新 stale 状态，落 worked example。

**Files:**
- Modify: `openspec/issues/consolidation-plan.md`

**Interfaces:**
- Consumes: Task 1 的 `batch-triage-rules.md`（引用其判据流 + 结构化判定记录格式 + 三元分类）。
- Produces: 供 verify/code-review 核对三元标注 + worked example 正反例。

- [ ] **Step 1: 保留 REC 相关合批框架不动，增大扫除批维度节**

不推翻既有「二、合批建议（AND 门）」REC-1/2/3——已验证。新增一节「大扫除批候选维度」，cross-ref `batch-triage-rules.md` 判据。开头明确重划 = 增维度，非重构 AND 门（守广审 B1：勿重 litigate REC 设计）。

grep 锚：`大扫除批`、`batch-triage-rules.md`

- [ ] **Step 2: 刷新 stale 状态（限状态订正，勿重 litigate）**

订正过期状态：REC-1（=gate-checkpoint-hardening）已 ship、G7（=sdflow-init-hardening）已 ship。**仅**改状态标注，MUST NOT 改动 REC 的设计建议内容（广审 B1 守卫）。

grep 锚：`已 ship`、`gate-checkpoint-hardening`、`sdflow-init-hardening`

- [ ] **Step 3: 对项做三元标注 + worked example（Q1 路径守卫落地）**

- 每个待处理项标三元归属（相关批 / 大扫除批候选 / 单开），每个大扫除批候选落一条 Task 1 定义的结构化判定记录。
- **worked example（MUST 正反齐全）**：
  - T50/T41/T42 标**排除**——内容 cosmetic 但落点 `SKILL.md`/workflow bundle（命中 `BEHAVIOR_PATH_PATTERNS`）。
  - 逻辑面项 T63/T64/T51/T52 标**排除**。
  - 真候选须落**非行为面路径**（纯 `docs/`/`README`/代码注释/`tests/`）；本仓无则显式记「候选池空/薄」。
- **诚实标注 MUST**：记一句「本仓大扫除批候选池薄」——本仓多数 debt 落 SKILL.md/scripts/workflow（行为面），严格路径守卫后真正安全候选可能个位数；此薄度是 dogfood 要实测回答「值不值」的关键信号。

> 注：核对 `todolist.py scan` 现有项，确认 T63/T64/T51/T52 存在且为逻辑面（若 ID 有出入，以实际逻辑面项替代，保持「≥1 逻辑面排除例」不变）。

grep 锚：`T50`、`排除`、`候选池薄`、`非行为面路径`

- [ ] **Step 4: 内容自检（grep 锚 + 人读）**

Run：
```bash
cd "$(git rev-parse --show-toplevel)"
grep -n "大扫除批" openspec/issues/consolidation-plan.md          # 维度已加
grep -n "已 ship" openspec/issues/consolidation-plan.md            # stale 已刷新
grep -nE "T50.*排除|排除.*T50" openspec/issues/consolidation-plan.md  # 行为面路径排除例
grep -n "候选池薄" openspec/issues/consolidation-plan.md           # 诚实标注
grep -n "三元" openspec/issues/consolidation-plan.md               # 术语统一
```
Expected: 各条均有命中；正（真候选或「候选池空/薄」显式记）反（T50/T41/T42 + 逻辑面项排除）worked example 齐全。

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "task2-consolidation-plan" "consolidation-plan 加大扫除批维度+三元标注+刷新stale+worked example"
git status --porcelain   # 期望空
```
Expected commit subject: `checkpoint(task2-consolidation-plan): …`

---

### Task 3: `openspec/INDEX.md` 登记 batch-triage capability（本仓-local 生效）

覆盖 tasks.md 组 4（4.1-4.2）。登记新 capability 索引；显式不跑回灌。

**Files:**
- Modify: `openspec/INDEX.md`

**Interfaces:**
- Consumes: Task 1/2 产物（batch-triage capability 的 spec 归档后同步）。
- Produces: 无下游。

- [ ] **Step 1: 在 spec 索引区加 batch-triage 行**

在 `### spec-workflow` 表（`openspec/INDEX.md:26-33` 一带的 spec 索引区，**非** `opsx-init:rules` 托管区块内）加一行登记 batch-triage capability。行内容点明：issues 池待处理项分诊三分类（相关合批/大扫除批/单开）+ 大扫除批硬边界 + issue 级 pre-diff fail-closed 判据 + Leg1 路径守卫 + 聚合上限 + 一项一 commit + 本仓-local 不进 bundle。

> 归档后 `sdflow-done` 会把 delta spec 同步进 `openspec/specs/batch-triage/spec.md`；本 INDEX 行指向该路径。本仓 spec 非 bundle。
> **MUST NOT** 动 `<!-- opsx-init:rules:start … end -->` 托管区块（那是 sdflow-init 维护的 bundle 规则索引，与本仓-local capability 无关）。

grep 锚：`batch-triage`、`本仓-local`

- [ ] **Step 2: 确认不跑回灌（Q2 本仓-local）**

不执行任何 bundle 部署动作——判据 commit 即生效（dev/runtime pull 后皆有）。确认无文件落 bundle：
```bash
cd "$(git rev-parse --show-toplevel)"
git status --porcelain | grep -E "sdflow-init/assets/workflow" && echo "❌ 误碰 bundle" || echo "✓ 无 bundle 改动"
git status --porcelain   # 应只有 INDEX.md（及尚未 commit 的本 change 文件）
```
Expected: `✓ 无 bundle 改动`。

- [ ] **Step 3: 内容自检**

Run：
```bash
cd "$(git rev-parse --show-toplevel)"
grep -n "batch-triage" openspec/INDEX.md
```
Expected: 命中新增行，且该行在 spec 索引区（非托管区块内）。

- [ ] **Step 4: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "task3-index-register" "INDEX 登记 batch-triage capability(本仓-local,不跑回灌)"
git status --porcelain   # 期望空
```
Expected commit subject: `checkpoint(task3-index-register): …`

---

## 验收核对（映射 tasks.md 组 5，由 ship 的 code-review + done 阶段承担，非独立实现 task）

逐 Requirement 核对（各有可观察证据）：
- **三分类互斥穷尽（含低增量第三腿 + 延迟绑定子态）** → Task 1 Step 2 grep 锚 `三元/互斥/穷尽/低增量/延迟绑定`。
- **硬边界禁装逻辑面** → Task 1 Step 3 + 自检 grep `禁.*逻辑面`。
- **行为面路径守卫** → Task 1 Step 3 `BEHAVIOR_PATH_PATTERNS/硬排除` + Task 2 T50/T41/T42 排除例。
- **fail-closed 纪律（无自动兜底声明）** → Task 1 Step 3 `无脚本自动兜底`。
- **聚合上限有牙（有上限 MUST + 数值 SHOULD + 生成物 MUST 隔离）+ 每项判定记录** → Task 1 Step 4。
- **一项一 commit 执行协议 + 验证锚** → Task 1 Step 5。
- **三元标注 + worked example 正反** → Task 2 Step 3。
- **本仓-local 不进 bundle** → Task 1 Step 6 + Task 3 Step 2 `✓ 无 bundle 改动`。
- **code-review pass（冷主审，红线：不砍评审安全）** → ship RUN_CODE_REVIEW 阶段。

## Self-Review

- **Spec coverage**：spec.md 的 8 个 Requirement 全部映射到 Task 1（判据/边界/fail-closed/同类Leg1/聚合上限/一项一commit/本仓-local）+ Task 2（三元标注）+ Task 3（INDEX 生效）。无遗漏。
- **Placeholder scan**：文档任务无代码占位；每 Step 给了具体 section 内容要点 + grep 锚，无「TBD/见上文」。
- **Type consistency**：checkpoint slug 命名一致（`task1-batch-triage-rules` / `task2-consolidation-plan` / `task3-index-register`）；三元分类术语全程「三元标注」。
- **注意点**：Task 2 Step 3 的逻辑面项 ID（T63/T64/T51/T52）需实现时用 `todolist.py scan` 核对；若 ID 变动，以实际逻辑面项替代，保持「≥1 逻辑面排除例」不变。
