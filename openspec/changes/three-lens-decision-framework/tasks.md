# Tasks — 三镜决策框架焊进 workflow 源头（T46）

> 真相源 = design.md「三处落点精确编辑锚」。均改**权威源** `sdflow-init/assets/workflow/` + 自制 skill，非消费仓副本。
> 每个 commit 步 MUST 用 `bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task<N>-<slug>`（命名空间格式）。

## 1. BASE-12 增强（书面层，spec-quality-base.md）

- [ ] 1.1 改 `sdflow-init/assets/workflow/spec-checklists/spec-quality-base.md` BASE-12 检查点：「候选方案」补三镜评估法（系统 / 用户 / 开发循环）；「理由」补主次判定行；标注 **TG-23 触发时 MUST 三镜 + 主次**，否则 SHOULD（不下沉琐碎决策）
- [ ] 1.2 机械核对：三镜措辞与记忆 `decision-three-lens-framework.md` 一致；与「最小可行 + 理想架构」两句在同一槽内不打架；TG-23 引用与 `trigger-catalog.md` 一致
- [ ] 1.3 checkpoint：`bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task1-base12`

## 2. workflow.md G2 决策登记格式

- [ ] 2.1 改 `sdflow-init/assets/workflow/workflow.md` G2 段（约行 83）：决策登记「选项 + 推荐 + 两方后果」→「选项 + 推荐 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**」
- [ ] 2.2 设计门行（约行 72）同步措辞：「决策登记区已摊开选项 + 推荐 + 两方后果」→ 三面后果 + 主次判定
- [ ] 2.3 机械核对：与 spec-review SKILL 决策登记区格式、code-review Step4 台账口径一致（三处同口径）
- [ ] 2.4 checkpoint：`bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task2-g2`

## 3. sdflow-code-review SKILL.md Step 4

- [ ] 3.1 改 `sdflow-code-review/SKILL.md` Step 4（约行 96）：「≥2 方案有把握自动选推荐（记理由）」→「按**三镜 + 主次**记理由」
- [ ] 3.2 台账行格式（约行 143）补主次判定；确认与 spec-review 决策登记区、workflow.md G2 三处一致
- [ ] 3.3 checkpoint：`bash ~/.sdflow/hack/checkpoint-commit.sh three-lens-decision-framework:task3-step4`

## 4. spec delta + 部署 + 收尾

- [ ] 4.1 `specs/spec-workflow/spec.md` MODIFIED delta 已含两需求（评审决策登记 + outside-voice tension）——实现后按代码实况复核 delta 与三处落点措辞一致
- [ ] 4.2 `openspec validate three-lens-decision-framework`（delta 结构 / SHALL·MUST 合规）
- [ ] 4.3 **部署纪律**：开发 checkout 跑 `bash setup.sh` 让全局 canonical `~/.sdflow/workflow` 跟上（改 assets 才测得到；测完 / 合并后运行 checkout 重跑还原）
- [ ] 4.4 无新增 / 删除 bundle 规则文件 → 无 INDEX 规则块同步（确认，非动作）
