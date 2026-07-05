# 三镜决策框架焊进 workflow 源头（T46）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把「三镜决策框架（系统/用户/开发循环 + 定主次）」+「fold-vs-defer scope-triage 判据」焊进 workflow bundle 权威源与自制 skill 的 6 处落点，并同步 spec delta，令决策纪律跨 session/子代理/checkout 自包含生效。

**Architecture:** 纯 markdown 规则/skill 文本编辑 + OpenSpec spec delta。无代码、无 pytest。每任务的"测试"= **机械 grep 核对**（旧措辞已替换、无残留、六处口径对齐 workflow.md G2 基准）；收尾 `openspec validate` + `setup.sh` 部署。

**Tech Stack:** Markdown、OpenSpec CLI、bash（grep 核对 + checkpoint-commit.sh）。

## Global Constraints

- 所有编辑均在**权威源** `sdflow-init/assets/workflow/` 与自制 skill 目录（`sdflow-code-review/` `sdflow-spec-review/` `sdflow-ship/`），**禁改消费仓副本** `openspec/workflow/`。
- **对齐基准**：六处决策后果/登记格式一律以 workflow.md G2「**三面后果（系统 / 用户 / 开发循环）+ 主次判定**」为准（Task 1 先落基准，后续对齐它）。
- 每任务 commit 步 **MUST 显式**用：`bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task<N>-<slug> "<描述>"`（命名空间标签，gate 只认本 change 标签）。
- **③ 的 T10 对齐**：照 `sdflow-ship/SKILL.md:23` 的 canonical T10 措辞抄，MUST NOT 臆造 T10 变体；改后 code-review 全文**无残留「有把握自动选」**。
- **docs/ 镜像不改**（Out of Scope，另 change 刷）。核对残留时只查 6 个权威源文件，排除 `docs/`。
- 三镜措辞真相源 = 记忆 `decision-three-lens-framework.md`；fold-vs-defer 真相源 = 记忆 `change-fold-vs-defer-cycle-cost.md`。

---

### Task 1: ② workflow.md G2 决策登记格式（canonical 基准，先做）

**Files:**
- Modify: `sdflow-init/assets/workflow/workflow.md`（HARD-GATE 行 ~72 + 关键设计决策 #3 ~行83）

**Interfaces:**
- Produces: 「三面后果（系统 / 用户 / 开发循环）+ 主次判定」这一 canonical 措辞——Task 3/4/5 对齐它。

- [ ] **Step 1: 改 HARD-GATE 行的决策后果措辞**

在 `workflow.md` 找到 HARD-GATE 表行（含 `决策登记区已摊开选项+推荐+两方后果`），替换：
- old: `（决策登记区已摊开选项+推荐+两方后果）`
- new: `（决策登记区已摊开选项+推荐+三面后果(系统/用户/开发循环)+主次判定）`

- [ ] **Step 2: 改关键设计决策 #3 的决策后果措辞**

找到「3. 中途 AskUserQuestion → 决策全登记进报告（G2）」段，替换：
- old: `写进报告决策登记区（选项+推荐+两方后果），继续跑完`
- new: `写进报告决策登记区（选项+推荐+三面后果(系统/用户/开发循环)+主次判定），继续跑完`

- [ ] **Step 3: 机械核对**

Run: `grep -n "两方后果" sdflow-init/assets/workflow/workflow.md`
Expected: 无输出（两处均已替换）。
Run: `grep -n "三面后果(系统/用户/开发循环)+主次判定" sdflow-init/assets/workflow/workflow.md`
Expected: 2 行命中。

- [ ] **Step 4: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task1-workflow-g2 "落点②: G2 决策登记 两方后果→三面后果+主次判定(canonical 基准)"
```

---

### Task 2: ① BASE-12 三镜 + ⑥ BASE-18 fold-vs-defer（同文件，合并一任务）

**Files:**
- Modify: `sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md`（BASE-12 行31 + BASE-18 行42）

**Interfaces:**
- Consumes: 三镜定义（系统/用户/开发循环）与 Task 1 的 canonical 主次判定概念。
- Produces: BASE-12 书面三镜门（TG-23 触发 MUST）；BASE-18 fold-vs-defer 判据。

- [ ] **Step 1: 改 BASE-12（行31，三镜为新挂入 ADR 结构、非替换旧串）**

替换整行：
- old:
  `| BASE-12 | **备选方案记录 / ADR** | 2-3 方案对比（含最小可行 + 理想架构）；关键决策按 ADR 结构落盘：**背景 / 候选方案 / 决策 / 理由 / 当前方案代价**；被否决方案与否决理由记录在决策记录节 | T+R |`
- new:
  `| BASE-12 | **备选方案记录 / ADR（三镜决策）** | 2-3 方案对比（含最小可行 + 理想架构），**每个候选按三镜评估：系统镜（耦合/依赖/复杂度/可回退）· 用户镜（体验/可感知行为/干扰）· 开发循环镜（心智负担/是否靠人/流程开销/复用）**；关键决策按 ADR 结构落盘：**背景 / 候选方案 / 决策 / 理由（含一句主次判定：对当前决策三镜哪个更重要、为何据此选定，不只罗列）/ 当前方案代价**；被否决方案与否决理由记录在决策记录节。**命中 TG-23（≥2 合理方案 / 非显然设计）时，三镜 + 主次判定 MUST 书面写入；琐碎决策（无 ≥2 合理方案）不强制（避样板税）** | T+R |`

- [ ] **Step 2: 改 BASE-18（行42，补 fold-vs-defer；注意与 BASE-12 同文件，先改 BASE-12 再改 BASE-18 避免行号漂移干扰）**

替换整行：
- old:
  `| BASE-18 | **分解检查** | 变更是否聚焦单一 capability？触碰多个独立功能域则拆为多个 change | R |`
- new:
  `| BASE-18 | **分解检查 / fold-vs-defer** | 变更是否聚焦单一 capability？触碰多个**独立**功能域则拆为多个 change。**过程中（评审/grill）新发现的需求/修复是否并入当前 change：workflow 循环固定成本高，勿反射式以「单一职责」教条拆——related + 低影响（紧耦合 / 同 capability / 一致性修复 / blast-radius 小）→ fold 进当前 change；真独立 / 扩容大 / 需自身设计审查 / 高 blast-radius → defer 另开。此判定走三镜、开发循环镜（增量审查成本 vs 一整轮 change 固定成本）通常主导；防吸积 = 「同 capability + 高耦合 + 低增量」三者齐才 fold** | R |`

- [ ] **Step 3: 机械核对**

Run: `grep -n "三镜评估\|开发循环镜\|fold" sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md`
Expected: BASE-12 行含「三镜评估」「开发循环镜」、BASE-18 行含「fold」。
Run: `python3 -c "import re; [print(f'BASE-12 dup 列数异常') for l in open('sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md') if l.startswith('| BASE-12') and l.count('|')!=5]"` 或人工确认两行仍是合法 4 列表格行（`|`×5）。
Expected: 无异常（表格结构未破）。

- [ ] **Step 4: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task2-base12-base18 "落点①⑥: BASE-12 挂三镜(TG-23 MUST) + BASE-18 补 fold-vs-defer 判据"
```

---

### Task 3: ③ code-review SKILL 三镜 + T10 对齐

**Files:**
- Modify: `sdflow-code-review/SKILL.md`（描述 ~行7-8 / P3e 导语 ~行30 / Step4 ~行95-96 / 台账 ~行143-144）

**Interfaces:**
- Consumes: Task 1 的 canonical 三面后果+主次；`sdflow-ship/SKILL.md:23` 的 canonical T10 措辞。

- [ ] **Step 1: 改描述（~行7-8）**

- old: `Step4 **能修的自动修**（标 [impl-review-fix]）、≥2 方案有把握自动选推荐（记理由）、修不了/拿不准的 defer`
- new: `Step4 **能修的自动修**（标 [impl-review-fix]）、≥2 方案按 T10 三级协议自动选推荐（按三镜 + 主次记理由）、修不了/拿不准的 defer`

- [ ] **Step 2: 改 P3e 导语（~行30）**

- old: `**≥2 方案有把握自动选推荐（记理由）**`
- new: `**≥2 方案按 T10 三级协议自动选推荐（按三镜 + 主次记理由）**`

- [ ] **Step 3: 改 Step4 正文（~行95-96），照 ship:23 canonical T10 抄**

- old:
  `- **≥2 方案有把握**：自动选推荐项（**记理由**入报告），不问人。`
- new:
  `- **≥2 方案（T10 三级协议，替换旧「有把握自动选」）**：①有客观判据（测试/断言/基准可判）→ 自动选并**按三镜 + 主次记理由**入报告；②无客观判据 → 派对抗镜复核推荐项，通过才自动选（复核记录写台账）；③复核不过/无从复核 → defer。**MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。** 不问人。`

- [ ] **Step 4: 改台账两行（~行143-144）**

- old（行143）: `自动修 N 项[impl-review-fix]；自动选推荐 M 项(附理由)；defer K 项 → buglist/todolist`
- new（行143）: `自动修 N 项[impl-review-fix]；自动选推荐 M 项(按三镜+主次附理由)；defer K 项 → buglist/todolist`
- old（行144）: `T10复核: <方案> | 对抗镜结论 <通过/证伪> | <一句理由>   ← 无客观判据的 ≥2 方案自动选必附`
- new（行144）: `T10复核: <方案> | 对抗镜结论 <通过/证伪> | <理由(三镜+主次)>   ← 无客观判据的 ≥2 方案自动选必附`

- [ ] **Step 5: 机械核对（无残留「有把握自动选」是硬门）**

Run: `grep -n "有把握" sdflow-code-review/SKILL.md`
Expected: 无输出（三处「有把握自动选」全清）。
Run: `grep -n "T10 三级协议\|按三镜 + 主次\|三镜+主次" sdflow-code-review/SKILL.md`
Expected: 多行命中（描述/导语/Step4/台账）。

- [ ] **Step 6: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task3-codereview "落点③: code-review 记理由按三镜+主次 + 「有把握自动选」对齐 T10(照 ship:23)"
```

---

### Task 4: ④ spec-review SKILL 决策登记区执行入口

**Files:**
- Modify: `sdflow-spec-review/SKILL.md`（描述 ~行8 / 铁律 ~行24 / tension ~行77 / 决策登记区 ASCII 格式块 ~行89）

**Interfaces:**
- Consumes: Task 1 的 canonical 三面后果 + 主次判定。

- [ ] **Step 1: 改描述（~行8）**

- old: `（选项 + 推荐 + 两方后果），人工在设计 HARD-GATE 一次性过报告拍板`
- new: `（选项 + 推荐 + 三面后果(系统/用户/开发循环) + 主次判定），人工在设计 HARD-GATE 一次性过报告拍板`

- [ ] **Step 2: 改铁律段（~行24）**

- old: `一次性过报告拍板。评审 findings 互相独立不级联，攒到报告一次决即可（且报告摊开两方后果，比中途弹窗看得全）。`
- new: `一次性过报告拍板。评审 findings 互相独立不级联，攒到报告一次决即可（且报告摊开三面后果 + 主次判定，比中途弹窗看得全）。`

- [ ] **Step 3: 改 tension（~行77）**

- old: `tension（voice 与主审分歧）→ 决策登记区 TENSION 条目（两方视角 + 推荐 + 后果），绝不静默采纳（user sovereignty）。`
- new: `tension（voice 与主审分歧）→ 决策登记区 TENSION 条目（两方视角 + 推荐 + 三面后果(系统/用户/开发循环) + 主次判定），绝不静默采纳（user sovereignty）。`

- [ ] **Step 4: 改决策登记区 ASCII 格式块 Q1 行（~行89）**

- old: `  │ [需拍板]  Q1  ≥2 方案: 选项A/B + 推荐 + 各自后果       │  人工设计门时勾`
- new: `  │ [需拍板]  Q1  ≥2 方案: 选项A/B + 推荐 + 三面后果 + 主次判定 │  人工设计门时勾`

（ASCII 框 `│` 收尾对齐尽量保持；宽度不必逐字符对齐，但保留行首 `  │` 与行尾 `│`，保持可读。）

- [ ] **Step 5: 机械核对**

Run: `grep -n "两方后果\|两方视角\|各自后果" sdflow-spec-review/SKILL.md`
Expected: 无输出（四处全清）。
Run: `grep -n "三面后果\|主次判定" sdflow-spec-review/SKILL.md`
Expected: 多行命中。

- [ ] **Step 6: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task4-specreview "落点④: spec-review 决策登记区/tension/格式块 两方后果→三面后果+主次"
```

---

### Task 5: ⑤ ship SKILL 台账同步

**Files:**
- Modify: `sdflow-ship/SKILL.md`（T10 台账格式串，~行23）

**Interfaces:**
- Consumes: Task 3 code-review:144 的台账新格式（须与之一致）。

- [ ] **Step 1: 改 ship:23 内的台账格式串**

- old: `行格式 = 「T10复核: <方案> | 对抗镜结论 <通过/证伪> | <一句理由>」`
- new: `行格式 = 「T10复核: <方案> | 对抗镜结论 <通过/证伪> | <理由(三镜+主次)>」`

（**只改台账格式串**；ship:23 的 T10 三级协议定义本身已 canonical，不动。）

- [ ] **Step 2: 机械核对（ship 与 code-review 台账一致）**

Run: `grep -n "理由(三镜+主次)" sdflow-ship/SKILL.md sdflow-code-review/SKILL.md`
Expected: 两文件各命中（台账格式已对齐）。

- [ ] **Step 3: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task5-ship "落点⑤: ship T10 台账格式补主次(与 code-review:144 同步)"
```

---

### Task 6: spec delta 复核 + openspec validate

**Files:**
- Read/复核: `openspec/changes/three-lens-decision-framework/specs/spec-workflow/spec.md`（已含两 MODIFIED 需求 + fold-vs-defer scenario）
- 对照: 上述六落点最终措辞

- [ ] **Step 1: 按代码实况复核 delta 与六落点一致**

Read spec delta，逐条核：
- 「评审决策登记进报告」的三面后果措辞 ↔ workflow.md G2 / spec-review SKILL 一致；
- 「≥2 方案」（TG-23，走三镜）与「事实核验」（Q2，不走三镜）已分列；
- 「fold-vs-defer」scenario ↔ BASE-18 措辞一致；
- tension 需求判据「有客观判据/无则复核/复核不过 defer」↔ code-review T10 一致；
- delta 内**无残留「有客观判据」与「有把握」并存的矛盾**（Task spec-review 已修，此处确认）。
若发现 delta 与实际落点措辞不符，**以落点实况为准改 delta**。

- [ ] **Step 2: openspec validate**

Run: `openspec validate three-lens-decision-framework`
Expected: `Change 'three-lens-decision-framework' is valid`

- [ ] **Step 3: Commit（仅当 Step1 改了 delta）**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task6-delta "delta 按落点实况复核对齐 + validate 通过"
```
（若 delta 无需改动，跳过 commit，本任务无产物变更。）

---

### Task 7: 部署（setup.sh）+ 全局残留终检

**Files:**
- 无源编辑；执行部署 + 跨六落点残留核对

- [ ] **Step 1: 跑 setup.sh 让全局 canonical 跟上**

Run: `bash setup.sh`
Expected: 正常结束（软链 + `~/.sdflow/workflow` canonical 刷新；改 assets 才测得到）。
说明：本仓为**开发 checkout**——此步让全局 canonical 指向本 checkout 的 assets；合并后由运行 checkout `/sdflow-upgrade` 还原（不在本 change 内做）。

- [ ] **Step 2: 六权威源残留终检（排除 docs/）**

Run:
```bash
grep -rn "两方后果\|两方视角\|各自后果\|有把握自动选" \
  sdflow-init/assets/workflow/workflow.md \
  sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md \
  sdflow-code-review/SKILL.md \
  sdflow-spec-review/SKILL.md \
  sdflow-ship/SKILL.md
```
Expected: **无输出**（六权威源旧措辞全清；docs/ 镜像不在本次范围，不查）。

- [ ] **Step 3: Commit（部署无源变更则跳过；setup.sh 若改动 deployed 副本则 checkpoint）**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task7-deploy "setup.sh 部署 + 六落点残留终检通过"
```
（若 setup.sh 未产生仓内 git 变更，本步无产物、跳过 commit。）

---

## Self-Review

**1. Spec coverage:** 六落点（①BASE-12 ②G2 ③code-review ④spec-review ⑤ship ⑥BASE-18）各有任务（Task 1/2/3/4/5）；spec delta 复核（Task 6）；部署（Task 7）。design.md 六落点表逐条覆盖。✓

**2. Placeholder scan:** 无 TBD/TODO；每处编辑给了精确 old/new 串；每任务给了 grep 核对命令与期望输出。✓

**3. Consistency:** 六处决策后果措辞统一为「三面后果（系统/用户/开发循环）+ 主次判定」（对齐 Task 1 基准）；③⑤ 台账统一「理由(三镜+主次)」；③ T10 照 ship:23 canonical。✓ ①⑥同文件合并 Task 2（先 BASE-12 后 BASE-18），避免双编辑冲突。✓
