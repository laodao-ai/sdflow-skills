# Tasks: streamline-workflow-automation　【本 change = Phase A】

> 追溯：任务追溯到 design.md 决策 ID（G/P）。`design.md` 是三相共享真相源、不裁剪。
> **〔grill-amendment〕本 change 只交付 Phase A**（连续化 + 提交自动化 + bundle 骨架）。
> **Phase B（§5 issues 池 / §3.3 sweep / §8.2 / §8.5）、Phase C（§6 跨模型 voice / §7.5 TG-26 / §8.3 / §8.4）
> 的 § 已移出本 change**——完整任务清单 + 移出的 spec Requirement 见 [ROADMAP.md](./ROADMAP.md)「Phase B/C 待迁」，
> 待各自 change dir 开工时并入。B/C 依赖 A 落地，A merge 后各开新 change（Approach 1）。

## 1. 阶段二：spec-review 编排器（laodao-skills）　【Phase A ✓】

- [x] 1.1 `spec-review` 改为编排器：Step1 内跑 autoplan（吃其 findings）、Step2 spec-review fan-out、Step3 合并成**一份** report〔P2〕（outside-voice 复用属 Phase C，已标〔Phase C 补〕占位）
- [x] 1.2 删中途 `AskUserQuestion`，改**报告决策登记区**（自动决策/需拍板，带选项+推荐+两方后果）〔G2〕
- [x] 1.3 评审 fan-out 以 fresh 子代理 dispatch，去掉对 `/clear` 的依赖〔G1〕
- [x] 1.4 写入防重叠说明：autoplan 已含 eng 镜，spec-review 不重复跑 eng〔design §4.2〕
- [x] 1.5 内部 2 次 checkpoint 提交（autoplan 子步、spec-review 子步）〔P2c〕
- [x] 1.6 收敛口：结尾建议是否进设计 HARD-GATE

## 2. 阶段三：impl-review 编排器（laodao-skills）　【Phase A ✓】（outside-voice 接入属 Phase C·见 ROADMAP §6.4）

- [x] 2.1 `impl-review` 定为**每次全跑·独立冷视角·强制**主审；skill 描述从"高风险才跑"改写〔P3c〕
- [x] 2.2 并入 gstack/review（scope-drift + 完成度）作为编排器一环〔P3c〕
- [x] 2.3 fresh 子代理替代 `/clear`；能修的自动修 `[impl-review-fix]`、修不了/需拍板的 → buglist/todolist(defer) + 汇总 `code-review-report.md`〔G1/P3e〕
- [x] 2.4 保留注入点B（domain 附 subagent-dev 终审）——写清"它有即时 fix+re-review 闭环、事后审无此"的存在理由，防后人优化掉〔P3b/design §7.2〕
- [x] 2.5 阶段三**无人类门**：≥2 方案有把握自动选推荐(记理由)、拿不准 defer〔P3e〕

## 3. opsx-done 改造（laodao-skills）　【Phase A：3.1/3.2/3.4 ✓｜3.3 → ROADMAP·Phase B】

- [x] 3.1 verify 保持在 opsx-done（所有修复之后，不前移进 impl-review）〔P3f〕；加 P3h 防假✅（证据锚点 + Do-Not-Trust + 禁弱模型）
- [x] 3.2 新增 **hand-off.md 产出步**：verify 之后、archive 之前；内容=done/not-done + 延后项 + 下阶段建议；随归档留档〔P3g〕
- [x] 3.4 弃用官方 `/code-review` 作为独立 step（保留插件能力供历史镜/置信过滤内部借用）〔P3d〕
- ~~3.3 issues sweep 步~~ → **移出至 [ROADMAP.md](./ROADMAP.md)·Phase B**〔I5/I6〕

## 4. 提交自动化（laodao-skills：checkpoint 脚本源 + step prompt + hook 源）　【Phase A ✓】

- [x] 4.1 新增 `hack/checkpoint-commit.sh`：接步骤名参数，`git add -A` + 固定 Conventional message；规避本机三坑（禁 `\`+heredoc / core.fileMode / CRLF）〔G4〕
- [x] 4.2 workflow.md 各 step prompt 末尾追加"完成后 checkpoint-commit"（skill 之间边界）〔G4/P1〕
- [x] 4.3 grill 多轮中途**不**提交，仅收敛后一次〔P1〕
- [ ] 4.4 ⊘ **跳过**（可选）：SessionEnd/Stop 警告 hook（检测未提交产物只告警）——用户决定跳过，随时可加〔G4 §5.3〕
- [x] 4.5 不 squash（opsx-done commit 步兼容"实现期已逐 commit"）〔G5〕

## 7. workflow bundle 源改写（laodao-skills `opsx-project-init/assets/`，非消费仓副本）　【Phase A 骨架 ✓】

> 〔grill-amendment〕**7.1 `workflow.md` 被 A/B/C 各增量改一次**（A 骨架 + checkpoint/hand-off 引用；B 追加 sweep 步引用；C 追加 outside-voice 步引用）。**7.5 的 TG-26 部分属 Phase C**（→ ROADMAP）。见 [ROADMAP.md](./ROADMAP.md) 约束 1/2。

- [x] 7.1 改写 `assets/workflow/workflow.md`：三阶段连续化**骨架**、step 表更新、去 2 个 `/clear`、去 step14、加 checkpoint/hand-off（sweep/outside-voice 引用留 B/C 增量加）〔全 G/P；G6〕
- [x] 7.2 改写 `assets/workflow/reference/quality-layering.md` §五：impl-review 从"高风险冷抽查"→"每次全跑独立强制主审"〔P3c〕
- [x] 7.3 **review UI 半归位**：源 `assets/review-tool/tools/` → `assets/workflow/tools/`；改 opsx-project-init 部署逻辑（`openspec/tools/` → `openspec/workflow/tools/`）+ review-stub.html/两 producer 路径引用；serve.sh + 根 review.html 留 openspec/ 根〔B1·grill-amendment〕
- [x] 7.4 checkpoint 脚本源进 `assets/hack/`（随 bundle 部署到消费仓 hack/）〔G4〕（可选 SessionEnd hook 见 4.4·跳过）
- [x] 7.5（workflow 规则变更部分）同步 laodao-skills `openspec/INDEX.md` 注入片段的 workflow 描述（去 /clear）；**TG-26 部分 → ROADMAP·Phase C**〔Compliance〕

## 8. 验证（不改实现，仅核对本 change 产物自洽）　【Phase A：8.1 ✓｜8.2/8.3/8.4/8.5 → ROADMAP·B/C】

- [x] 8.1 决策表 Phase A 的 G/P/B 每条在 bundle/skill 改动中有对应落点，无悬空（收尾自检通过；I\*/C\* 属 B/C）
- ~~8.2 reindex INDEX 一致~~ → **ROADMAP·Phase B**
- ~~8.3 outside voice fallback 冒烟~~ → **ROADMAP·Phase C**
- ~~8.4 gstack 原生 voice 未触碰~~ → **ROADMAP·Phase C**
- ~~8.5 其它项目迁移影响确认（OQ3）~~ → **ROADMAP·Phase B**

## 9. 下游消费仓采纳（**不在本 change 内**，仅登记；各消费仓 update 后各自做）　【routine，A merge 后】

- [ ] 9.1 〔下游〕消费仓跑 `opsx-project-init update` 重拉新 bundle（workflow/tools 归位、新 step prompt、hack/checkpoint-commit.sh）
- [ ] 9.2 〔下游·Phase B 后〕迁移各仓 `openspec/{buglists,todolists}/` 数据 → `issues/{buglist,todolist}/`，跑 `reindex` 建 INDEX/batches（走 destructive-commands 规则）
- [ ] 9.3 〔下游〕改各仓 `config.yaml` / `CLAUDE.md` 的 issues·tools 路径引用
