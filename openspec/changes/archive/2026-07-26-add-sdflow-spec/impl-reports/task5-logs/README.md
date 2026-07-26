# Task 5 · A/B 三路实测的原始日志（第三方复核用）

> 归档于 fix 轮次 1。报告本体 = `../task5-ab-comparison.md`；本轮修订说明 = `../task5-ab-comparison-fix1.md`。
> **只读归档，MUST NOT 手改**——报告里的每个数字都应能从这里重算出来。

## 目录

| 路径 | 内容 |
|---|---|
| `logs/{legacy,thin,subagent}/turn*.json` | **12 轮**的完整 `claude -p --output-format json` 输出（`usage` / `modelUsage` / `total_cost_usd` / `duration_ms` / `permission_denials` / `terminal_reason`）。**报告 §3 的全部指标出自这里。** |
| `logs/{lane}/review.json` | 三路各一次**冷启动独立评审**（`--model sonnet`）的完整输出。报告 §3.4 的 findings 出自这里。 |
| `logs/{lane}/turn*.err` | 每轮的 shell stderr。**全部 0 字节**——这本身是 §3.2「两轮中止非外部信号」的证据之一。 |
| `logs/{lane}.t*.out` | 驱动脚本 wrapper 的 stdout（result 文本 + META 摘要）。⚠️ `legacy.t2.out` / `thin.t2.out` **为 0 字节**，恰是被中止的那两轮。 |
| `logs-discarded-permfail/` | **作废并重跑的第一轮**（`--permission-mode dontAsk` 致三路条件不一致，$4.19）。**不计入任何指标**，留档备查。 |
| `prompts/` | 三路的**全部输入文本**（`req.txt` 需求、`decide.txt` 拍板、各路逐轮 prompt、`review.txt` 冷审模版）。 |
| `harness/turn.sh` | 驱动脚本。**唯一外部时限 = `timeout 3000`（50 分钟）**，12 轮共用，实验中途未改（mtime 早于最早一轮日志）。 |
| `harness/rev.sh` | 冷审驱动脚本。 |
| `harness/show.py` | 逐轮指标打印脚本。 |

## 复算方法

三路的美元 / token 合计 = 对各 lane 的 `turn*.json` 逐轮求和
（`-r` 续跑报**本轮**成本，非累计 ⇒ 逐轮求和口径正确）。
子代理用量出现在父进程的 `modelUsage` 的 haiku / sonnet 两行。

**一致性自检**（fix 轮次 1 已跑）：把 12 轮全部按 Opus 标准价
（in \$5 / out \$25 / cacheRead \$0.5 / cacheWrite-1h \$10 每 MTok）折算，
**12/12 轮的 `costUSD` 与折算值之比 = 1.0000**——含两轮被中止的轮次。
⇒ 中止轮的计费**未整体丢失**（残余边界见报告 §3.2）。

## ⚠️ 不在这里的东西

**三个沙箱 git clone 已 `rm -rf`，未归档、无法恢复。**
∴ 报告 §5 引用的 `design.md` 行、§3.4 的 `grep` / `diff` 输出**不能对源文件复跑**——
那些文件级证据只存报告誊抄 + `logs/*.out` 与 `review.json` 的转述。
补救路径（重跑代价与建议）见报告 §10 第 10 条。
