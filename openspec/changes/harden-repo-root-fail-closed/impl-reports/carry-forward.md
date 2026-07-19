# Carry-forward — 双轴审裁定「不属当票、须由后续票承接」的发现

本文件是 tickets 管线内跨票传递的载体：某票双轴审报出的发现，若按 plan 的划分不属该票 scope，
**MUST NOT 静默丢弃**（反静默压制），登记于此并在承接票的 dispatch 中原文带上。

---

## CF-1 → Task 4：过宽 `subprocess.run` mock 是**面**，不是点

**来源**：Task 1 · Standards 轴 · Important
**发现者独立实测**（非采信自报）：全仓 **12 个同姿势站点**——
`sdflow-issues/tests/test_task4_rename_snapshot.py` 5 处 + `sdflow-issues/tests/test_issues.py` 7 处。

**内容**：这些用例整体替换 `issues_mod.subprocess.run`，会连带劫持被测函数之外的一切子进程调用，
其中就包括 `repo_root` 的 `git rev-parse`。当前后果是坏 JSON 被当仓根 `makedirs`（Task 1 实测的
再生链）；**Task 2 加固落地后，后果变成「凡走 `main()` 的用例都会撞进新的 fail-closed 分支」**——
不是一个用例，是十二个。

**为什么这条必须在 Task 4 被当面处理**：plan 的 Task 4 与 tasks.md 2.1 现在的口径都是
「修 `test_task4_rename_snapshot.py:149` 这一个用例」，是**点驱动**的。按 CLAUDE.md 基准 3
（面治优先于点补），正解是按 argv 分派做**面级**改造（只拦 recorder 那一次 scan 调用，
`git rev-parse` 透传真实行为），而非逐个补。

**⚠️ 反模式警告**：若 Task 4 只修 1 处、留 11 处，Task 2 的加固会以「11 个用例莫名变红」的形态
爆发在 Task 4 之后，且极易被误诊为「加固写错了」而去弱化 `repo_root` —— 那正是本 change 要防的
「拿现状反驳目标」。

---

## CF-2 → Task 6：R4 的达成锚在 Task 5，不在 Task 1

**来源**：Task 1 · Spec 轴 · Minor

**内容**：Task 1 的 `R-ID: R4` 标注过宽。R4「测试套件不得在当前工作目录留下副作用」的
Requirement 主体是**仓根单一份 `conftest.py` 的 autouse fixture 机械保证**，其三个 Scenario
（空目录跑套件条目数 0 / 全仓覆盖 / 泄漏被断言捕获）**无一被 Task 1 推进**——Task 1 清的是 R4
被违反后的历史产物，不是 R4 本身。

**Task 6 收口时的动作**：把 R4 的达成锚落在 **Task 5**；**MUST NOT** 因为 Task 1 的两个框已勾
就把 R4 读成已闭环。

---

## CF-3 → Task 6：`test_exec_claude_reverse_path_three_flags_golden` 的触发条件比记录的窄

**来源**：Task 1 · implementer 全量 pytest 观察

**内容**：该用例此前被记为「全量跑 FAILED / 单独跑 PASSED」的 order-dependent 缺陷
（proposal Non-Goals + tasks 4.5）。Task 1 的全量跑（1753 passed / 3 skipped / **0 failed**）
中它**没有失败** ⇒ 真实触发条件比「全量跑」更窄（可能与并发、机器负载或更早的某个用例相关）。

**Task 6 登记 buglist 时的动作**：如实写「触发条件未完全定位，已知一次全量跑未复现」，
**MUST NOT** 照抄「全量跑必红」这个已被证伪的描述。
