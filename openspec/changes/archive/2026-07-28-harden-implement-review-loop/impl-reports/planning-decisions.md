# 出票模式 `T10-choice` 仲裁审计落点

本文件是出票模式（`mode=tickets-plan`）粒度争议 / 全 ticket 语义一致性自扫遇矛盾时，`T10-choice`
仲裁记录的确定性审计落点〔spec-review-amendment M15；delta `impl-orchestration/spec.md`、
`spec-workflow/spec.md` 均 SHALL〕。行格式 = 「`T10-choice` 复核: <方案> | 对抗镜结论 <通过/证伪> |
<理由(三镜+主次)>」。
**①档分支**：有客观判据、未派对抗镜时，「对抗镜结论」字段记 `—` + 括注理由（如「①档：有客观
判据，自动选，未派对抗镜」），**不套用 <通过/证伪>**——该二值只对②档（派了对抗镜复核）成立。

> 首条为**回填**：本 change 自身出票时点（Task 2 之前）该规则尚未落地，此前无处可落，事后按本文件
> 确立的行格式补记；后续出票一律实时写入，不再回填。

---

`T10-choice` 复核: Task 1 的 Codex 实跑验收项加一条硬约束「该实跑 MUST NOT 以本 change 为目标（会
覆盖本 plan 文件 = 毁掉完成判据窗口锚）——用一次性 fixture change 或只走到档位解析步即止」 | 对抗镜
结论 — （①档：有客观判据，自动选，未派对抗镜） | 三镜：系统镜（主）——避免自锁与 ticket 重派：
`ship_gate.plan_first_sha()` 用 `git log --diff-filter=A -- <plan_rel>` 取完成判据窗口起点，覆盖/
重建 plan 文件即重置该窗口 ⇒ 已完成 ticket 被判未完成，这是脚本行为可判的事实，非偏好；用户镜——无
可感知行为变化；开发循环镜——多一行约束，心智成本近零。主次：系统镜为主。
