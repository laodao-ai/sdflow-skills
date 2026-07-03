# Hand-off — streamline-workflow-automation（Phase A）

> 日期：2026-07-02　·　异步人类再入口 + 下个 change 种子。verify 判 PASS 后、archive 前产出，随归档留档。
> 〔P3h-c〕以下"完成"项均已复核证据锚点存在性，不直接搬运 verify 的 ✅。

## ✅ 完成了什么（Phase A：三阶段连续化 + 提交自动化 + bundle 骨架）

锚点已核（commit + 文件在）：

- **spec-review → 阶段二设计评审编排器**（`a8796f1`）：autoplan→并行多镜→一份报告；删中途 AskUserQuestion 改决策登记区 + 已裁掉区；去 /clear 依赖；内部 2×checkpoint。
- **impl-review → 阶段三代码评审编排器**（`f0a52a4`）：每次全跑·独立冷·强制主审；并入 gstack/review；能修自动修/修不了 defer；注入点B 共存理由。
- **opsx-done verify 防假✅ + hand-off 步**（`c2fa9dc`）：verify 证据锚点硬约束 + Do-Not-Trust + 禁弱模型；新增本 hand-off 步（verify 后/archive 前）。
- **checkpoint-commit.sh + hack/ 部署**（`a1d7e2b`）：焊死本机三坑；init.py 加 copy_hack。
- **workflow.md 三阶段连续化骨架 + quality-layering §五改写**（`a9c0a80`）：去 2 个 /clear、去 step14 人类门、去官方 code-review step；impl-review 每次全跑（否决旧"缩成残差"）。
- **review UI 半归位 B1**（`618c021`）：tools/→openspec/workflow/tools/，serve.sh + 根 review.html 留根（服务器根模型）。
- **INDEX 注入片段同步去 /clear**（`f3fc631`）。
- **冷独立 impl-review + [impl-review-fix]**（`08d2a95`）：无 blocker；补 copy_hack/checkpoint 脚本测试（py 21→29）。
- 测试：py 29 passed + js 18 passed；`openspec validate --strict` 通过；9 条 spec Requirement 同步进 `openspec/specs/spec-workflow/`。

## ⏳ 未完成 / 延后

- **impl-review defer 项**：无（本 change 代码面冷审无 blocker、无修不了/需拍板残差；见 code-review-report.md「已裁掉」区亦空）。
- **4.4 可选 SessionEnd 警告 hook**：用户主动**跳过**（非核心；随时可加）。
- **Phase B（issues 池与批次管理，I\*）**：已移出本 change → `ROADMAP.md`。依赖本 change 的 opsx-done hand-off 步（现已就位）。
- **Phase C（跨模型 outside voice + TG-26，C\*）**：已移出本 change → `ROADMAP.md`。依赖本 change 的 spec/impl-review 编排器（现已就位）。
- **laodao-skills 自身 dogfood 副本刷新**：本仓 `openspec/workflow/`、`openspec/tools/`、`openspec/review.html` 仍是旧部署副本（verify 已确认此点，恰反证"改权威源"被遵守）。属下游 routine，需 `opsx-project-init update` + 删旧 `openspec/tools/`（destructive，须确认）。

## ▶ 下一阶段建议

1. **dogfood 副本刷新**（优先，本仓自洽）：跑 `python3 opsx-project-init/scripts/init.py update --root .` 刷新本仓 `openspec/workflow/`（去 /clear 新骨架）+ 部署 `openspec/workflow/tools/` + `hack/checkpoint-commit.sh`；随后 `git rm -r openspec/tools/`（旧布局，走 destructive-commands 规则确认）。
2. **开 Phase B change**（`issues-pool-batch-mgmt` 暂名）：按 ROADMAP「Phase B 待迁」的 §5/§3.3/§8.2/§8.5 + 2 条 spec Requirement（批次注册表条**迁入时须改被动版**，去逾期催办）。可 dogfood 本 change 造的新流水线。
3. **开 Phase C change**（`cross-model-outside-voice` 暂名）：按 ROADMAP「Phase C 待迁」的 §6/§7.5-TG26/§8.3/§8.4 + 2 条 spec Requirement。
4. **下游消费仓采纳**（§9，各仓 routine）：`opsx-project-init update` 重拉新 bundle（含 hack/checkpoint-commit.sh、workflow/tools 归位）。Phase B 落地后再迁 issues 数据。
