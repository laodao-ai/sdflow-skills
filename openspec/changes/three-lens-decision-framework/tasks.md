# Tasks — 三镜决策框架焊进 workflow 源头（T46）

> 真相源 = design.md「五处落点精确编辑锚」〔spec-review 完整性镜校准：原 3 → 5 落点〕。均改**权威源** `sdflow-init/assets/workflow/` + 自制 skill，非消费仓副本。
> **统一对齐基准**〔broad-review F2〕：五处落点的决策后果/登记格式**一律以 workflow.md G2「三面后果（系统/用户/开发循环）+ 主次判定」为准**，勿把某处对齐到另一处的旧格式。
> 每个 commit 步 MUST 用 `bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task<N>-<slug>`（命名空间格式）。

## 1. BASE-12 增强（书面层，spec-quality-base.md）— 落点①

- [ ] 1.1 改 `sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md` BASE-12（行 31）检查点：「候选方案」补三镜评估法（系统 / 用户 / 开发循环）；「理由」补主次判定行；标注 **TG-23 触发时 MUST 三镜 + 主次**，否则 SHOULD。**三镜为新挂入 ADR 结构**（此文件无「两方后果」串，非 grep-replace）
- [ ] 1.2 机械核对：三镜与「最小可行 + 理想架构」两套评估维度在同一槽**正交共存不打架**（design 已判为互补：前者定生成哪些候选、后者定如何评估每候选）；措辞拧清；TG-23 引用与 `trigger-catalog.md` 一致
- [ ] 1.3 checkpoint：`... three-lens-decision-framework:task1-base12`

## 2. workflow.md G2 决策登记格式 — 落点②（**canonical 基准**）

- [ ] 2.1 改 `sdflow-init/assets/workflow/workflow.md` G2 段（行 83）：「选项 + 推荐 + 两方后果」→「选项 + 推荐 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**」
- [ ] 2.2 设计门行（行 72）同步：「决策登记区已摊开选项 + 推荐 + 两方后果」→ 三面后果 + 主次判定
- [ ] 2.3 此格式即后续所有落点的对齐基准（③④⑤ 均对齐到此，非互相对齐）
- [ ] 2.4 checkpoint：`... three-lens-decision-framework:task2-g2`

## 3. sdflow-code-review SKILL.md — 落点③

- [ ] 3.1 改 `sdflow-code-review/SKILL.md`：frontmatter（行 7-8）、导语（行 30）、Step 4（行 96）的「记理由」→「按**三镜 + 主次**记理由」；对齐 G2 基准
- [ ] 3.2 台账行（行 143「附理由」/ 行 144「T10复核」）补主次判定
- [ ] 3.3 **对齐 T10**〔Q1 采 A / ADR-4〕：frontmatter 7-8 / 导语 30 / Step4 96 的「≥2 方案有把握自动选」→ T10 三级协议，**照 `sdflow-ship/SKILL.md:23` canonical 措辞抄**（有客观判据→自动选/无→对抗镜复核/复核不过→defer；MUST NOT 以「有把握」为唯一依据）；消除 96 与自身台账 144 的自相矛盾。机械核对：改后 code-review 全文无残留「有把握自动选」
- [ ] 3.4 checkpoint：`... three-lens-decision-framework:task3-codereview`

## 4. sdflow-spec-review SKILL.md — 落点④〔spec-review F1/CV1 补齐；决策登记区实际执行入口〕

- [ ] 4.1 改 `sdflow-spec-review/SKILL.md`：frontmatter（行 8）、正文（行 24）「两方后果」→ 三面后果 + 主次判定
- [ ] 4.2 TENSION（行 77）「两方视角 + 推荐 + 后果」→「两方视角 + 三面后果 + 主次判定」；决策登记区 ASCII 格式块（行 89）「选项A/B + 推荐 + 各自后果」→ 三面后果 + 主次判定
- [ ] 4.3 checkpoint：`... three-lens-decision-framework:task4-specreview`

## 5. sdflow-ship SKILL.md 台账同步 — 落点⑤〔完整性镜补齐〕

- [ ] 5.1 改 `sdflow-ship/SKILL.md`（行 23 T10 台账「T10复核: … | 一句理由」，与 code-review:144 同串）：同步补主次判定，与 code-review 台账一致
- [ ] 5.2 checkpoint：`... three-lens-decision-framework:task5-ship`

## 6. BASE-18 fold-vs-defer scope-triage 判据 — 落点⑥〔设计门追加 / ADR-5〕

- [ ] 6a.1 改 `sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md` BASE-18（行 42）：在「分解检查」补 fold-vs-defer 判据——**workflow 循环固定成本高，勿反射式拆 change**；新发现工作按对当前 change 影响判（related+低影响→fold，真独立/扩容大→defer 另开）；走三镜、开发循环镜主导；防吸积=「同 capability+高耦合+低增量」齐才 fold
- [ ] 6a.2 机械核对：与 decision-three-lens-framework 口径一致（此判据是三镜在 scope 决策上的应用）；不与 BASE-10 YAGNI / BASE-18 原文冲突（是补充非推翻）
- [ ] 6a.3 checkpoint：`... three-lens-decision-framework:task6a-base18`

## 7. spec delta + 部署 + 收尾

- [ ] 7.1 `specs/spec-workflow/spec.md` MODIFIED delta——实现后按代码实况复核 delta 与**六处落点**措辞一致（对齐 G2 基准）；tension 需求判据对齐 T10〔Q1 采 A〕、「≥2 方案」与「事实核验」分列〔CV4〕、fold-vs-defer scenario 与 BASE-18〔落点⑥〕一致
- [ ] 7.2 `openspec validate three-lens-decision-framework`（delta 结构 / SHALL·MUST 合规）
- [ ] 7.3 **部署纪律**：开发 checkout 跑 `bash setup.sh` 让全局 canonical `~/.sdflow/workflow` 跟上（改 assets 才测得到；测完 / 合并后运行 checkout 重跑还原）
- [ ] 7.4 无新增 / 删除 bundle 规则文件 → 无 INDEX 规则块同步（确认，非动作）
- [ ] 7.5 defer 残差入 todolist：docs/ 镜像刷新〔F3〕、trigger-catalog「≥2 方案」判例〔X2〕（「有把握」→T10、fold-vs-defer 判据均已纳入本 change，不再 defer）
