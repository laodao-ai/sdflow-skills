# Task 4 实现报告 — 历史重放部署门

## 做了什么

对 5 份归档评审报告（4 份 code-review + 1 份 spec-review，覆盖 4 个不同 change）做历史重放，
验证新裁决协议（DD4 机械前置 + 强档二元裁决）部署门红线。

- 选取样本：`refactor-roadmap-internalize-deps`（多采纳+多裁掉）、`absorb-gstack-autoplan`（采纳+置信过滤裁掉）、
  `tickets-parallel-frontier`（全部为旧协议置信<80滤除项）、`fix-probe-scan-precision`（单条 finding）、
  `simplify-workflow` spec-review（18 采纳+3 裁掉的大样本）。
- 对每个 `reviewed_sha` 建 `git worktree`（detached，跑在 scratchpad，已清理），手工把 49 条 finding
  提取为结构化 JSON（真实按 DD4 契约处理：仅 2 条能定位到干净单一 `file:line` 且能核实出逐字引文，
  走 `{file,line,quote}` 三元组；其余 47 条按 brief 允许的做法标 `evidence_pack` → 机械层判
  `uncheckable`，直进强档二元裁决）。
- 真跑 `findings_ref_check.py --input <report>.json --root <worktree>`（脚本：
  `sdflow-init/assets/workflow/tools/findings_ref_check.py`，Task 1 交付）。机械层抓到 2 处真实
  引用漂移（r4 CR-06 行号 `:246`→实际 `:248`；r5 H3 缺 change 目录路径前缀），修正后两条均 `pass`。
- 对全部 49 条 finding 做独立强档二元重裁（读 worktree 真实代码核验，不依赖历史置信分数），
  与历史裁决逐条对表。

## 结果

- **49/49（100%）新旧裁决一致，0 mismatch**——无需触发「模型方差复裁一次」，也无需三类归因中的
  ③类判定过程（本来就是 0）。
- **③类（协议缺陷/真误杀）= 0 ✅ 满足红线**。
- ①类（历史误标/口径漂移）3 处，均发生在机械核验/JSON 构造阶段本身（我的引用转录误差 + 一处
  报告原文内部标签自相矛盾），已如实记录、剔除分母，不影响新旧裁决一致性判定。
- ②类（模型方差）0——首轮即 100% 一致。
- 噪声重入率（参考，非门禁）= 0/19 = 0%，但已在报告第五节写明 C4 语料限制：19 条历史裁掉项
  多数自带充分裁掉理由，样本对「新协议是否会比旧置信阈值更宽松放行噪声」的区分力有限，真正的
  压力测试需窗口期真实语料（tasks.md 5.3 已登记）。

## 产出物

- `impl-reports/replay/replay-report.md` — 完整重放报告（方法论 + 机械层结果 + 逐报告对表 + 三类
  归因 + 噪声重入率 + 诚实边界 + 结论）
- `impl-reports/replay/findings/*.json` — 5 份报告的结构化 finding 提取（含历史 disposition 标注）
- `impl-reports/replay/findings/*.refcheck.out.json` / `*.refcheck.log` — `findings_ref_check.py`
  真实运行输出（机械层证据，非叙述）
- `impl-reports/replay/run-replay.sh` — 可重跑的 harness 脚本（建 worktree + 跑机械核验），一次性、
  非常驻资产，未装进 bundle

## 未做 / 已知局限（如实报告）

- 未对 fail 路径做真实语料样本测试——旧语料里没有出现「有 quote 但内容对不上」的自然案例
  （2 处 fail 均是我自己转录引用时的错误，修正后变 pass，不是语料自带的 fail 样本）。fail 路径
  的正确性由 Task 1 的 pytest 单元测试独立覆盖，本重放不重复验证脚本单元正确性，只验证部署门
  （新旧裁决一致性）。
- 49 条样本 vs 全部历史轨迹（35-39 轮）是抽样，非全量重跑，按 DD5「3-5 份归档报告」范围执行，
  未超出也未缩水任务边界。

## MUST NOT 事项确认

- 未勾 `tasks.md` 复选框，未打 checkpoint 标签（按 brief 要求，留给执行模式在双轴审通过后处理）。

## 状态

DONE
