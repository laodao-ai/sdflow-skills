# Planning decisions · sweep-pool-debt-2026-08（出票模式）

## 切分方案：默认采纳 design.md「切片建议」草图，无实质偏离

design.md 含「切片建议」节（4 张垂直切片，预算 3–6 内，票间无阻塞边），已过阶段二评审与设计
HARD-GATE。出票**默认采纳**该草图为切分方案，未增/删/合并票、未改切片边界。∴ 无实质偏离，
`T10-choice` 对抗镜复核三条件（无切片建议节 / 有实质偏离 / 草图与正文矛盾）均未命中，不派复核。

- 票 1（T292）= Task 1：ship_gate 内容锚（spec-workflow delta 全部 Requirement）
- 票 2（T294）= Task 2：归档面收敛 + CI
- 票 3（T290）= Task 3：切片偏离对账接线
- 票 4（T287）= Task 4：SKILL.md 下沉
- Task 5：强制「实现验证」收尾（skill 必产，不计入 3–6 预算，Blocked-by 全部功能票）

## 观察记录（非偏离）：票 1 ∩ 票 3 同文件 `sdflow-code-review/SKILL.md`

票 1（Task 1，impl-review 重锚协议段·新建）与票 3（Task 3，Step1 输入清单加偏离对账行）**同改
一个文件的不同节**。按并行安全约束五问评估：概率（真冲突）低——两节相隔；影响小且可恢复——
Claude 宿主各票独立 worktree，编排层按号序 `git merge --no-ff`，相隔两节 3-way 干净合并、真冲突
则 fail-loud（约束自带兜底）；完美成本高——串行化需触发必触发对抗镜复核。故**不加阻塞边、保留
草图无边拓扑**，依赖约束文档化的 worktree-merge 兜底。此为「不改同一模块的同一接口」判据下的
合规并行（同文件不同节 ≠ 同接口），非实质偏离，仅记录以告知执行期 merge 顺序 load-bearing。

## 自扫结论

全 ticket 语义一致性自扫（checkpoint 前）：无跨票矛盾、无与 Global Constraints 矛盾。Blocked-by
拓扑无环（功能票无边，收尾票依赖全部功能票号）。
