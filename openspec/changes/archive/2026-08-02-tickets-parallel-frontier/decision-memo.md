---
schema_version: 1
change: tickets-parallel-frontier
branch: feat/tickets-parallel-frontier
generated_at: 2026-08-02T11:30:38+08:00
decision_hash: 4d69b0210011
---

# 决策纪要 · tickets-parallel-frontier

## 目标态

tickets 管线依赖图无阻塞边的 ticket 并行执行，缩短多票 change 的墙钟。

## 拍板决策

- **D4 [spec-review-amendment] per-ticket worktree 隔离（Claude 宿主）+ Codex 退化串行** — 依据：spec-review 6 镜收敛确认共享 `.git/index` 竞态是 critical 缺陷（CEO Claude 子代理实测复现），`git add <file>` 不构成事务边界；调研确认 `ship_gate.py:1478-1496` 的 `done_task_ids`（`git log --no-merges`，无 `--first-parent`）能穿透 merge commit 看到 worktree 分支上的 checkpoint 标签，gate 零改动；Claude Code `isolation: "worktree"` 是 harness 原生能力零脚本改动；Codex 无原生 worktree 且进程回收不兼容并行，退化串行（行为与改动前一致）；**砍掉的候选**：① 共享工作树 + flock 串行化 commit 关键区（闭合竞态但留语义层残余 + 需额外定义 commit 归属机制 + 需改 checkpoint-commit.sh 的 `git add -A`，三个补丁 vs worktree 一次性解决）② 共享工作树 + implementer 不提交（复杂度高，编排层需识别 uncommitted hunks 归属）
- **D3 [spec-review-amendment] review-package 用 merge commit 天然隔离** — 依据：worktree 方案下，merge 回主分支后 `merge_parent1..merge_commit` 天然只含该票改动，Commits/Stat/Diff 三段均自然收窄，无需文件过滤或 commit 归属机制；**砍掉的原候选**：PARALLEL_BASE + 文件范围隔离（commit 归属未定义，5 镜独立指出）
- ~~**D2 按文件名 `git add`**~~ [spec-review-amendment] 降为建议性最佳实践——worktree 隔离下每个 implementer 有独立 `.git/index`，不存在通配暂存带入别人改动的问题
- **D1 并行 implementer + 串行双轴审** — 依据不变：impl 是墙钟大头，双轴审并行 scope 大收益小

## 承重约束

- **C1 gate 完成窗口零改动** — 验证方式：读 `ship_gate.py:1478-1496` 的 `done_task_ids`（`git log sha..HEAD --no-merges`，无 `--first-parent`）确认穿透 merge commit + checkpoint 标签后置纪律；**证据锚**：`ship_gate.py:1478-1496`（遍历走进 merge 的所有父链，看到被 merge 进来的 worktree 分支上的 checkpoint 标签）、`SKILL.md:547`（标签由执行模式审后补打）；[spec-review-amendment] 穿透性由调研读码验证
- **C3 并行 implementer 异常处理 = 等全部返回后逐个处理** — 验证方式不变；BLOCKED 票的 worktree 直接丢弃（不 merge），无脏改动污染主分支；白跑成本 = 个别 implementer token；**补充**（领域镜 S10）：完成态票据正常走完审+checkpoint，不因兄弟票 BLOCKED 而搁置
- **C2 并行安全保证由 worktree 隔离结构性兜底** — [spec-review-amendment] 原 C2 的"出票语义约束 + git add fail-loud 兜底"已被 worktree 隔离替代——每个 implementer 有独立 `.git/index` 和工作树，即使出票判断失误（两票改同一文件），各自 commit 到独立分支，merge 时 git 正常冲突检测 fail-loud（真正的 merge conflict，非 index.lock 竞争）；**诚实边界**：出票语义约束仍在（减少 merge conflict 概率），但兜底从"不存在的 fail-loud"升级为"真正的 merge conflict 检测"

## 接受的边角

- 并行 implementer 中某个 BLOCKED 时其余已白跑 — 概率：低（pilot-log 5 票 0 BLOCKED）；影响：token 浪费（系统镜），BLOCKED 票的 worktree 直接丢弃不 merge（无脏改动污染）；完美成本：需 harness 支持取消正在运行的子代理（不存在该能力）；**为何接受**：成本天花板 = 2-3 个 implementer 的 token
- 并行 implementer 碰同一文件 → merge conflict — 概率：低（vertical-slice 设计 + 出票语义约束）；影响：`git merge --no-ff` 时 git 报 merge conflict、编排层需处理（fail-loud，非静默）；完美成本：需 ticket 声明文件路径（违反 SKILL.md:260 的设计取向）；**为何接受**：worktree 隔离下 merge conflict 是**真正的 fail-loud**（git merge 的原生冲突检测），比原方案的"不存在的 fail-loud"严格更强
- Codex 宿主无并行收益 — 概率：100%（Codex 无 worktree 原生能力）；影响：退化为串行（行为与改动前一致）；**为何接受**：④ 简化——不在无能力的宿主上强行造轮子

## 三镜代价

本次无 TG-23 命中。
