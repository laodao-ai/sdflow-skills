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

## 执行期修正（Task 1 merge 后）：撤销 task 1.9 的 64-hex 重锚，保留 40-hex

**问题**：task 1.9 要求把本 change 自身 `spec-review-report.md` 从 40-hex 重锚为 64-hex+manifest，
设计初衷是「防票2/3/4期间 gate 读旧锚自锁」——但该初衷假设**新门**在驱动 ship。

**实测证伪**：驱动本次 ship 的是**运行 checkout 的老门**（`~/.claude/skills/sdflow-ship` →
`~/.skills/sdflow-skills`，40-hex 格式），非本 dev checkout 的新门。老门读 64-hex 报告直接
判 `UNKNOWN(6)`（reviewed_sha out-of-domain，实测锚 `66d14ff…`）→ **真自锁**。

**根因**：dev/运行 checkout 分离下，改门的 change 在 ship 期间由**老门**驱动（CLAUDE.md 反向窗口
纪律）；新门只在 push→pull→`/sdflow-upgrade` 后才生效，那时本 change 早已归档。task 1.9 把方向
搞反了。

**修正**：merge Task 1 后，把 `spec-review-report.md` 锚恢复为原批准提交 40-hex
（`f28c1ffc0d880d728d66a9f6abf514271803d557`）、删 `reviewed_manifest`。老门恢复 CONTINUE_IMPL。

**为何 40-hex 是正确终态（非缩水，通则③）**：① ship 期间老门读 40-hex = fresh；② 归档后新门
（升级生效时）对**归档** change 不做失鲜复检，且 `FIELD_VALIDATORS` 语法接受 40-hex（DT-1 校验
分层）——两端皆安全。task 1.9 防的场景（新门读 live 40-hex 报告）在 dev/运行分离下**不可达**
（报告在新门生效前已归档）。spec Requirement「存量旧格式锚重跑写锚」是**能力**，不要求本报告在
归档件中必须 64-hex。

**代价（三镜）**：系统镜——零全局影响，外科式单行恢复；用户镜——无可感知行为差异；开发循环镜——
消除一次自锁死循环。**主次**：这是对一个在实际执行环境中失效的设计步的实现期纠正，已按通则③
显式留痕，交冷层 code-review 复核。
