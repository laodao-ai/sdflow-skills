# autoplan 广审报告 — tickets-parallel-frontier

<!-- sdflow:step1-broad-review v1 mode="native" -->

> 佐证：autoplan 原生执行，CEO 双声真实调用（Claude 子代理 + Codex exec），非模拟。

## CEO DUAL VOICES — CONSENSUS TABLE

| Dimension | Claude | Codex | Consensus |
|---|---|---|---|
| 1. 前提有效？ | `next_ready` 多返回 ✅；Phase A n=1 详细 | Phase A 未验并行假设 | CONFIRMED（代码前提成立）；Phase A 证据薄 |
| 2. 对的问题？ | 方向对，收益上限有限 | 墙钟收益写过满 | CONFIRMED |
| 3. Scope 校准？ | 精确 2 tasks 1 file | 同意 | CONFIRMED |
| 4. 替代方案？ | worktree 隔离"收益相同"是错误理由 | 拒绝机械隔离却承诺正确归因 | CONFIRMED |
| 5. 竞争/市场？ | N/A 内部工具 | N/A | CONFIRMED |
| 6. 6月轨迹？ | commit 归属损坏是最大后悔 | 同意 | CONFIRMED |

## Findings

### F1 [critical] 并行 implementer 共享 `.git/index` 竞态——两模型独立收敛

**两模型独立发现**：并行 `git add <file>` + `git commit` 在共享 `.git/index` 上竞态。
即使两个 implementer 修改完全不同的文件，`git add` + `git commit` 不是原子的——
一个的 `git commit` 可能把另一个已 `git add` 但还没 commit 的文件一起带走，
导致 commit 归属错误、review-package 隔离失效。

Claude 子代理实际复现了该竞态（两个并发进程，~150ms 差异，ticket A 的 commit 消失）。
Codex 从 git 内部机制推理得出相同结论。

**D2（`git add` 按文件名）只防通配误暂存，不是事务边界。**

证据：
- Claude: 实测复现，git log 只有 B 的 commit，A 的改动被吸进 B
- Codex: `.git/index` 共享 + `git add`/`commit` 非原子 = 竞态必然
- 既有 memory: `parallel-reviewers-mutate-same-worktree` 已记录同类问题

**修复方案**（按成本排序）：
1. **最小修复**：在 dispatch prompt 中要求 implementer 的 `git add` + `git commit` 用 `flock` 串行化（编辑/测试仍并行，只有提交关键区串行）
2. **中间方案**：implementer 不提交，留 working-tree diff，编排层收集后串行提交各票
3. **重新评估 Non-Goal**：per-ticket worktree 隔离（结构性消除竞态）

推荐方案 1（④ 最简方案 + 闭合竞态）。

### F2 [high] review-package commit 归属机制未指定

design.md 写"从 git log 识别其 commit"但未说明**如何**映射 commit 到 ticket。
implementer commit 没有 ticket 标签（`SKILL.md:547` 禁止），只在双轴审后由编排层补打。
审第 N 票时，编排层需要在交错的无标签 commit 里识别哪些属于 ticket N——当前设计无算法。

**修复**：要求 implementer 在报告文件里记录自己的 commit SHA 列表（已有报告文件契约，
只需加一个字段）。编排层据 SHA 列表隔离 diff，而非猜测。

### F3 [high] Non-Goal 2 驳回理由事实错误

"per-ticket worktree 隔离——gate 契约重写成本过高，**收益相同**"——
后半句不准确：worktree 隔离结构性消除 F1 的竞态，而当前方案不消除。
应改为"收益更高但成本过高"，或重新评估成本。

### F4 [medium] Phase A "判赢"证据薄且当日产出

tickets-pilot-log.md 详细记录 n=1（含 confounders），样本 2-6 只有名字列表。
判定与本 proposal 同一天（2026-08-02）产出，无间隔观察期。
墙钟判据明示"无回归信号"且被 `curb-rework-loop-cost` 同期变更混淆。

非阻塞（人已明确拍板），但建议在风险登记区如实记录。

### F5 [medium] proposal 墙钟公式过于乐观

proposal Success Metrics 写 `墙钟 ≈ T1 + max(T2,T3,T4) + T5`，
而 design.md 自己的公式是 `max(impl) + sum(审)`——review 串行仍是 sum。
proposal 应对齐 design 公式，避免误设期望。

## 自动决策

| # | 决策 | 原则 | 结果 |
|---|---|---|---|
| D1 | 前提确认 | P6 行动偏好 | 接受（代码前提已验证，Phase A 人已拍板） |
| D2 | Scope 扩展 | P3 务实 | 不扩展（2 tasks 精确） |
| D3 | DX scope | P1 完备 | 跳过（纯 prose 改动无 DX 面） |

## 标记

- [gstack-amendment] F1 F2 F3 需在 design/specs 修订中处理
