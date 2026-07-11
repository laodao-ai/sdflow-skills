# hand-off — harden-hr-tg-anchor-consistency

> verify **PASS**（2026-07-11，强档 opus·Do-Not-Trust·235 passed）后、archive 前产出。异步人类再入口 + 下阶段种子。

## ✅ 完成了什么（每条附机验锚点）

**hr-tg 锚一致性一次机械化到目标态、全 fail-closed、零妥协**（R1 出锚侧 + R2 校验侧）：

- **R1 出锚侧** `hr_tg_intersect.py`：M3 严格解析（空 cell/`TG-04x`/残留 fail-closed，commit `fb266b5`）· M-new catalog 全集存在性 + F8 边界（只取 `## 三` 段表行 fullmatch）+ F7 内部一致（HR-TG⊆全集，`cf8b0c1`）· 成员行严格抽取 + 段定位恰-1-fail-closed + fence-aware（冷层 fold `b9d229e`）。
- **R2 校验侧** `anchor_lint.py`：必需 `--trigger-catalog`（argparse `required=True`，缺→exit2 fail-closed 无 WARN，`b2bd30e`）· M1 declared 硬必填无 grace · M2 hit=declared∩HR-TG 重算逐元素 numeric 同序 · M4 evidence strip 非空 · M-new 双侧存在性 · F1 sentinel（declared=""空集/hit=none空 hit，`ebff04b`）· F2/M-parse 整行严格拒重复键/未闭合注释/未消费残留（`02fcc6b`+`b9d229e`）· F9 collect-not-raise 双侧独立错误收集（`ebff04b`+`b9d229e`）。
- **F3 跨文件一致性 golden** `test_hr_tg_cross_tool.py`：两份"非 import"重实现（adr/0002）的漂移由 golden 机械兜底（子集/全集逐字相等 + emit hit⟺lint 重算 + numeric 同序，`d927cd0`+`81dab6d`）。
- **bundle 回灌** `a095a16`：权威源 `sdflow-init/assets/workflow/tools/` + 下游副本 `openspec/workflow/tools/` 两工具 diff 空一致；两 SKILL anchor_lint 调用补 `--trigger-catalog`（`3d7d0b7`）。
- **诚实边界 S1**：M2 只堵内部一致性、declared 正确性留语义残余（模型 + evidence 人读 + git 审计），docstring 声明不冒充 tamper-proof；`test_m2_consistent_but_wrong_still_passes`（`test_anchor_lint.py:223`）钉死"一致但错→过"。
- **dogfood 回归核验**：真实 trigger-catalog（恰 1 个 `## 三、触发词目录`）+ 本 change 真实 spec-review-report.md 经收紧后 anchor_lint → **CLEAN**，收紧不误伤真实数据。

**质量层**：8 任务每任务双阶段冷审 + 冷全分支 sdflow-code-review（5 源）——后者揪出 **7 条热层每任务审漏的跨切片 parsing 面洞**（成员行/段边界/fence/锚边界/序/错误收集/doc），全 fold 修。冷层承重墙再实证。

## ⏳ 未完成 / 延后

- **defer = 0**：code-review 无 defer 项（sweep tagged 0，无新增 buglist/todolist）。
- **Minor（verify 判 PASS 可接受）**：F12 文档同步不完整——`docs/workflow-map.md` 与 `docs/workflow-skills/sdflow-spec-review.md` 部分 anchor_lint 为 prose 简写（`--layer spec-review`）未逐处补 `--trigger-catalog`；运行时真相源（两 SKILL.md + code-review.md 完整命令串）已含，view-only 文档简写不影响行为。
- **笔误（非缺口）**：tasks.md §4 三条目误编号 `3.1/3.2/3.3`（与 §3 重号），纯排版、与代码无关。

## ▶ 下一阶段建议

1. **adr/0019 升 Accepted**（本 change 即其首形态 dogfood）+ **adr/0018 补 Accepted 实证**（机械校验器输出诚实——本 change M2 诚实边界是其活样本）。
2. **criteria-mechanization-tracker.md 回填**：tracker 行 4.3/5d.3 此前标 `⏳pending harden-hr-tg-anchor-consistency` → 本 change ship 后翻实 🟢-deep（hr-tg 锚 M1/M2/M3/M4/M-new 全机械化 + file:line）；4.4 残余收窄注（S1 语义残余明确）。
3. **T139**（outside_voice_guard 双 step1 锚一致性）——本 change grill 时剥出的另一 capability，另开完整 change（todolist）。
4. **T141**（把 decomposition standard 融入 workflow 三处触发：roadmap / ff-change-spec / 执行发现）——hr-tg 收尾后单开（用户已定序）。
5. **T142 / workflow-map 广度刷新**：补 5 个 mlh-p4 后脚本（hr_tg_intersect/outside_voice_guard/review_disposition_check/lens_metric_emit/maintain_scan）+ hr-tg 3 字段 schema（本 change F12 已补 §3.2/§4 部分，broad 刷新另记）；顺带补齐上面 Minor 的 F12 doc 简写。
6. **Phase A tickets 样本 #2 仍未定**：本 change 按 merit 走 superpowers（~2 内聚片，非 tickets 样本）；样本另找"天生 3+ 独立切片 + 依赖拓扑"的单一能力工作。
