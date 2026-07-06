# hand-off — adaptive-workflow-routing

## ✅ 完成了什么（每条附机验锚）

**收敛版 A**：code-review 入口无逻辑面白名单免 Step2 多镜（Leg1-phase1 of roadmap `workflow-cost-optimization`）。

- **判器** `sdflow-init/assets/workflow/tools/trivial_shape.py`：读 git diff、语言感知判三白名单形状（代码注释/约定文档扩展名锚定/仅新增 tests/）、行为面路径护栏（bundle/SKILL.md/workflow.md/ship_gate.py 即便 markdown 也 NOT）、doc 扩展名锚定（裸 *.txt/docs 下源码/README 命名代码皆落 NOT）、mode/copy/空内容守卫、hunk-state 解析。**34 pytest 全绿**。commit `task1-impl` + `impl-review`。
- **SKILL 接入** `sdflow-code-review/SKILL.md:64-70`：Step2 前调判器，exit 0 免 fan-out / 1·2 照跑、缺失视同 NOT_EXEMPT。
- **spec** `spec-workflow` delta：「code-review 每次全跑」精确化为两层（Step1 恒跑 + Step2 仅无逻辑面白名单免），**沿用原标题**（保 OpenSpec 定位）。
- **评审历程（dogfood 价值实证）**：grill 8 决策 → spec-review 4 冷源（对抗×2+接地+codex）判定原前向大机制地基不成立 → 设计门 Q1=A 收敛 → code-review 1 冷镜抓 7 危险方向洞全修。verify PASS。

## ⏳ 未完成 / 延后
- **B5**（pre-existing，**非本 change**）：`test_contract_archived_corpus_anchor_hits` clean main 亦红，随任一 ship-gate change 顺手修。
- **T56**（新 todolist）：判器 F6 残余 + 更宽轻量化留档。低危。
- **激活**：merge 后须 **push → 运行 checkout `/sdflow-upgrade`**（判器/SKILL 属 bundle 权威源，`sdflow-init update` 推消费仓）方生效。
- **roadmap 后续**：Leg2（机械镜换快档+后台）、Leg3（批次策略）见 `openspec/roadmaps/workflow-cost-optimization/roadmap.md`（P2→P4）；承载变更 `plan-workflow-cost-optimization` 待 cross-review+归档。

## ▶ 下一阶段建议
1. **本 change**：archive → merge to main → push → `/sdflow-upgrade` 激活。
2. **紧随**：roadmap P2（机械镜换快档 + 全后台通知，收益最直接、不依赖本 change）。
3. B5 可在 P2 或任一 ship-gate change 顺手修。
