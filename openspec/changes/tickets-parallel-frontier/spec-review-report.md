# spec-review-report.md — tickets-parallel-frontier

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-20" evidence="本 change 改 sdflow-implement SKILL.md 执行模式 prose，命中 TG-20（sdflow 工作流改进）" -->

## 评审概要

- **对象**：`openspec/changes/tickets-parallel-frontier/`
- **内容**：tickets 管线执行模式从严格串行改为受限并行
- **改动面**：仅 `sdflow-implement/SKILL.md` 一个文件的 prose 条款
- **评审镜**：autoplan 广审（CEO 双声 Claude+Codex）+ 接地镜 + 领域镜（sdflow workflow）+ 对抗镜×2（隐藏假设/失败模式）+ design-voice fallback（同族）
- **代码事实**：接地镜全部 6 条核验通过（`next_ready` 多返回 ✅、`ship_gate.py:1797-1800` 窗口 ✅、`SKILL.md:260` 禁写 ✅、`SKILL.md:547` 禁标签 ✅、checkpoint 补打 ✅、D4/Non-Goal 归档存在 ✅）

---

## Findings（按严重度排序，去重合并后）

### S1 [critical · 6 镜收敛 · 已实测复现] 并行 implementer 共享 `.git/index` 竞态——`git add <file>` 不是事务边界

**命中镜**：CEO-Claude、CEO-Codex、领域镜 F2、对抗镜1 假设1、对抗镜2 F2/F3、Design-voice F4

并行 `git add <file>` + `git commit` 在共享 `.git/index` 上竞态。即使两个 implementer 修改完全不同的文件，`git add` 只是把当前磁盘内容原样写入**共享的** `.git/index`，不区分调用者；随后的 `git commit` 提交**整个 index**。两个并发进程的 add/commit 序列没有互斥屏障——A-add → B-add → A-commit（把 B 的文件一并提交）→ B-commit（报 "nothing to commit"）是完全可能的交错。

**CEO Claude 子代理实测复现**：两个并发进程（~150ms 差异），ticket A 的 commit 消失，改动被吸进 ticket B 的 commit。

**后果**：
- D2（`git add` 按文件名）只防通配误暂存，不防这种竞态
- D3（review-package 隔离）依赖的 commit 归属从根上被打破
- C3（BLOCKED 可安全 revert）也受影响——revert 被污染的 commit 会连带删掉另一票的合法改动

**decision-memo 里 "fail-loud 兜底" 的表述是对 git 语义的误判**（4 镜独立指出）：`git add <file>` 在两个进程各自编辑不同内容后调用**不会**产生任何冲突或非零退出——"fail-loud" 这道防线**根本不存在**。

**修复方案**（按成本排序）：
1. **最小修复**：dispatch prompt 要求 implementer 的 `git add` + `git commit` 用 `flock` 串行化关键区（编辑/测试仍并行，只有提交串行）
2. **中间方案**：implementer 不提交，留 working-tree diff，编排层收集后串行提交
3. **重新评估 Non-Goal**：per-ticket worktree 隔离

**置信度**：高（实测复现 + 6 镜独立收敛）。**建议**：设计门前修订。

---

### S2 [high · 5 镜收敛] review-package commit 归属机制未定义——D3 机制地基缺失

**命中镜**：CEO-Claude、领域镜 F1、对抗镜1 假设2、对抗镜2 F1、Design-voice F2

design.md 写"从 git log 识别其 commit"但未说明**如何**映射 commit 到 ticket。implementer commit 没有 ticket 标签（`SKILL.md:547` 禁止），只在双轴审后补打。`<ticket_commits>` 从何而来完全空白。

D3 砍掉"按 SHA 范围切"（因交错不可靠），改用文件范围隔离——但文件范围隔离的**输入**（"该票改了哪些文件"）本身就依赖 commit 归属识别，而归属未定义。

**额外问题**（Design-voice 独家）：`git diff --name-only <ticket_commits>` 当 `<ticket_commits>` 是不连续 hash 集合时不是合法 git diff 语法——需要对每个 commit 单独 `git show --name-only`。

**修复**：要求 implementer 在报告文件里记录自己的 commit SHA 列表或触碰的文件列表。编排层据此隔离 diff。

**置信度**：高。**建议**：设计门前修订 D3 + 扩展 implementer 报告契约。

---

### S3 [high · Design-voice 独家] `checkpoint-commit.sh` 用 `git add -A`——并行场景下会吞入其他票的脏改动

**命中镜**：Design-voice F1（独家）

`~/.sdflow/hack/checkpoint-commit.sh:51` 使用 `git add -A`（已验证）。并行批次中某票 BLOCKED 且已写盘但未提交时，给另一票打 checkpoint 标签的 `git add -A` 会把 BLOCKED 票的半成品**一并扫进 checkpoint commit**。

后果：审查过的 diff 和最终被打标签的 commit 内容**不是同一份东西**——commit 比被审过的 diff 多了未审代码。直接击穿 C1（gate 完成窗口零改动）的证据链。

**修复**：Task 2 补 checkpoint 阶段暂存改为按文件名 `git add`（而非 `-A`），或在打标签前核实工作树无非本票残留。

**置信度**：高（代码验证）。**建议**：设计门前修订。

---

### S4 [high · 4 镜收敛] Non-Goal 2 驳回理由事实错误——"收益相同"不准确

**命中镜**：CEO-Claude、CEO-Codex、对抗镜1、Design-voice F5

"per-ticket worktree 隔离——gate 契约重写成本过高，**收益相同**但成本高"——worktree 隔离结构性消除 S1 的竞态 + 让 S2 的归属问题变平凡（每个 worktree 分支天然只含该票 commit），收益**严格高于**当前方案。

Design-voice 指出：git worktree 各自有独立 index 和 HEAD，不存在共享工作树竞态。可行路径：每票 `git worktree add <path> -b ticket<N>`，全部返回后 `git merge --no-ff` 回主分支。

**修复**：改措辞为"收益更高但成本过高（gate 扫描假设纯线性历史）"或重新评估成本。

**置信度**：高。**建议**：设计门决策（见决策登记区 Q1）。

---

### S5 [medium-high · 对抗镜1 独家] Codex 宿主并行派发语义未验证

**命中镜**：对抗镜1 假设3（独家）

本仓已有记录 Codex 与 Claude 在并发原语上不同构（memory: `codex-reaps-spawned-processes-per-command`）。本次 design/spec 全部条款是宿主无关的通用表述，未讨论 Codex 下 Agent 并行调用是否真并发。若 Codex 实际串行，"并行派发"静默退化为串行——只交学费（review-package 隔离复杂度）不拿收益。

**置信度**：中（推理外插，未实测）。**建议**：design 补宿主条件化声明或显式接受为残余风险。

---

### S6 [medium · 领域镜独家] Tasks 遗漏 SKILL.md 另外两处"串行"表述

**命中镜**：领域镜 F3

tasks.md 只列了 frontier 段改动，但 SKILL.md 至少还有两处残留"串行"表述：
- `SKILL.md:6` frontmatter description（「frontier 串行派 fresh implementer」）
- `SKILL.md:155-158` 正文引言（「frontier 串行 + 每 ticket 双轴审」）

CLAUDE.md 明确要求 description 改时要顾及触发精度。

**置信度**：高。**建议**：Task 2 增加子项同步这两处。

---

### S7 [medium · 2 镜] review-package 模板 Commits/Stat 段未收窄

**命中镜**：Design-voice F3、领域镜 F4（相关）

design.md 只给出 Diff 段的文件范围收窄写法，但 `## Commits`（`git log`）和 `## Files changed`（`git diff --stat`）仍用全批次范围。reviewer 看到头部声称 "scoped to Task N"，但 Commits/Stat 段自相矛盾。

**置信度**：高。**建议**：Task 2 补收窄这两段。

---

### S8 [medium · 2 镜] Phase A "判赢"证据薄且同日产出

**命中镜**：CEO-Claude、CEO-Codex

tickets-pilot-log.md 详细记录 n=1，样本 2-6 只有名字列表。判定与本 proposal 同天产出。墙钟判据明示"无回归信号"且被同期变更混淆。

**置信度**：高。非阻塞（人已拍板），但建议风险登记区如实记录。

---

### S9 [medium · 2 镜] proposal 墙钟公式过于乐观

**命中镜**：CEO-Claude、CEO-Codex

proposal 写 `墙钟 ≈ T1 + max(T2,T3,T4) + T5`，design 自己的公式是 `max(impl) + sum(审)`——review 串行仍是 sum。应对齐 design 公式。

---

### S10 [medium-low · 2 镜] BLOCKED 场景处理顺序 spec 措辞模糊

**命中镜**：领域镜 F5、对抗镜2 F6

spec.md Scenario 未显式写死"完成态票据正常走完审+checkpoint，不因兄弟票 BLOCKED 而搁置"。

**建议**：spec 明确选项 a（完成的正常审，BLOCKED 的逐个处理）。

---

### S11 [low-medium · 对抗镜1 独家] 多收尾 ticket 可能导致并行收尾

**命中镜**：对抗镜1 假设4

出票机械强制"至少一张收尾 ticket"，但不禁止多张。多张全阻塞收尾票会被 `next_ready` 同时返回为并行候选。

**建议**：出票约束补"收尾节点唯一"。

---

## 已裁掉

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | 对抗镜2 F4：读时序耦合（implementer 读到另一票中间态） | 与 S1 同根（共享工作树），且概率低、影响可控（审阶段可发现），不额外记录 |
| X2 | 对抗镜2 F5：fix 轮 diff 沾染兄弟票 | S2 的下游放大效应，解决 S2 后此项自然消解 |
| X3 | Design-voice F7：白跑成本样本量单薄 | 人已明确接受此边角（decision-memo 有签），非设计缺陷 |
| X4 | Design-voice F8：`next_ready` 无并行上限 | 出票 3-6 张预算已约束实际并行数，非实质风险 |
| X5 | 接地镜 注记：D4/Non-Goal 引用链层级 | 文档结构优化项，不影响逻辑完整性 |

---

## 决策登记区

### [自动决策] D1 接地镜核验通过
autoplan 与接地镜确认 `next_ready` 多返回、`ship_gate.py:1797-1800` 窗口算法、`SKILL.md:260/547` 约束均真实存在且一致。默认接受。

### [需拍板] Q1 是否重新评估 per-ticket worktree 隔离（Non-Goal 2）

S1/S2/S3/S4 四条 high+ findings 共同指向"共享工作树"是这份设计的根本薄弱点。当前方案（prose 约束 + flock 串行化 commit 关键区）可以闭合 S1 的竞态，但 S2/S3 仍需额外机制（implementer 报告 SHA + checkpoint 改按文件 add）。worktree 隔离一次性解决全部四条，但引入 merge commit（需验证 gate 是否假设纯线性历史）。

**选项 A**：保持共享工作树 + 补 flock/SHA 报告/checkpoint 改造（当前方案 + 三个补丁）
- 系统：改动面小，但留下语义层残余风险（出票判断失误时无机械兜底）
- 用户：无感
- 开发循环：三个独立补丁，Task 2 scope 增加但仍可控

**选项 B**：改为 per-ticket worktree 隔离（重新评估 Non-Goal 2）
- 系统：结构性消除竞态+归属问题，但需验证 gate 对 merge commit 的兼容性
- 用户：无感
- 开发循环：设计改动较大，需重写 D2/D3 + 验证 gate

**推荐**：A（④ 最简方案闭合关键竞态，scope 不加宽）。但 S4 的事实纠正（措辞改"收益更高但成本过高"）无论选哪个都须做。

### [需拍板] Q2 commit 归属机制选择

S2 要求定义 implementer 如何向编排层报告自己的 commit。两个候选：
- **a）implementer 报告 SHA 列表**：在报告文件加一个 `## Commits` 段，列出本轮产生的 commit SHA。编排层据此做 `git show --name-only` 取文件列表。
- **b）编排层在 dispatch 前后各取一次 HEAD**：dispatch 前记 `BEFORE_SHA=HEAD`，该 implementer 返回后记 `AFTER_SHA=HEAD`——但并行场景下这不可靠（其他 implementer 也在提交）。

**推荐**：a（implementer 自报 SHA，确定性可靠）。

### [需拍板] Q3 checkpoint-commit.sh 的 `git add -A` 在并行场景下是否需要改

S3 指出 `git add -A` 在 BLOCKED 票有脏改动时会污染 checkpoint。两个选项：
- **a）改 checkpoint 为按文件 add**：需要编排层传"本票文件列表"给 checkpoint 脚本（依赖 Q2 解决后的 SHA 归属机制）
- **b）串行审前先清理 BLOCKED 票的脏改动**：`git checkout -- <BLOCKED 票文件>` 恢复，再开始串行审+checkpoint

**推荐**：b（最简——编排层在串行审之前扫工作树脏改动并恢复，不改 checkpoint 脚本本身）。

---

## 收敛口

本份设计的方向正确（并行 impl 减墙钟）、scope 精确（2 tasks, 1 file），代码前提全部核验通过。但有一条 **critical**（S1, 6 镜收敛+实测复现）和三条 **high**（S2/S3/S4），全部指向"共享工作树 + 现有兜底描述不成立"这一根本面。

**建议**：在设计门拍板前修订 design/decision-memo/spec，至少需要：
1. 闭合 S1（commit 关键区串行化方案）
2. 定义 S2（commit 归属机制）
3. 处理 S3（checkpoint 脏改动清理）
4. 纠正 S4 措辞
5. 补 S6/S7 的 tasks 遗漏项

修订后建议进设计 HARD-GATE 拍板。

---

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="claude" reason_code="not-installed" findings="8" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

## 度量锚

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="2" sev="致1/高2/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="2" sev="致1/高2/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="1" sev="致1/高1/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="claude" site="design-voice" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="1" sev="致1/高3/中1/低0" -->
