# hand-off — dedupe-issues-scripts-shared-layer

> 异步人类再入口 + 下个 change 种子。verify PASS 后 / archive 前产出。

## ✅ 完成了什么（每条附机验锚点）

**issues 台账三层重复全消，三 skill 合一为 `sdflow-issues`**（6 ticket，全套件 2143 passed / 0 failed）：

- **T1 core 骨架 + 封闭 POOL_SPEC schema**：`sdflow-issues/scripts/sdflow_issues_core/__init__.py`（唯一命名 package）；`validate_pool_spec` import 期 fail-closed（`__init__.py:198`）；守卫 `test_pool_spec_schema.py`（含 EXPECTED_CONTRACT + EXPECTED_ENUMS 外部字面锚）。tag `f8f03b2`。
- **T2 三层共享逻辑单一物理源 + 三薄入口迁入**：THREE_WAY(37)+TWO_WAY(24) helper 全上移 core、差异经 POOL_SPEC/PoolStrategy 注入、core 无 pool 值分支；三薄入口迁 `sdflow-issues/scripts/`（sys.path.insert + package import）；CLI 逐命令 byte-equivalent。tag `aba5edb`。
- **T3 SKILL.md 三合一 + 删旧目录**：`sdflow-issues/SKILL.md` 一份（骑墙判定 `:115` + 误判代价登记 `:140` + 一份 principles 块）；`sdflow-buglist/`·`sdflow-todolist/` 删除（`ls`→No such file）。tag `13763a8`。
- **T4 determinism-guards 守法切换**：镜像 AST 守退役（`test_mirror_consistency.py` 删）；AST 级无 pool 分支守（best-effort 诚实标）+ thinness 同一性守 + golden 降级接线守（`test_determinism_guards.py`）；`_legacy_block_range` 逐行重复 dedup 为 core 单一 `_scan_legacy_block_range`+`LegacyBlockError`。tag `c77e341`（含 fix1）。
- **T5 下游托管引用同步 + 机械引用守卫**：README/CLAUDE/AGENTS/CI/ship_gate/sdflow-done/retro/implement/init 全同步 3→1；`test_sync_principles` 17→15；机械引用守卫 `test_downstream_reference_guard.py`（非 vacuous 实证）。tag `02590cc`。
- **T6 行为等价留存测试 + 覆盖零回归门**：`test_task6_cli_equivalence_harness.py`（16 case 遍历 11 subcommand）+ `test_task6_coverage_gate.py`（逐 node 比对 baseline、钉死 count=2093+sha256、非魔数）；setup.sh temp-HOME 验证。tag `0e030b3`。
- **冷代码审（分支级独立层）**：3 镜收敛 + 2 次 cross-model voice 抓出 6 轮 per-ticket 双轴审全漏的 6 真发现，全采纳修复（F1 recorder token try/finally+conftest autouse·F3 baseline 钉死·F4 thinness 存在性·V2 validator fail-closed·V3 specific_values 单一源·F5 encoding），tag `5cc7748`/`5ce875a`/`2bb4c763`；报告 `code-review-report.md`（anchor_lint CLEAN）。

## ⏳ 未完成 / 延后

**批次 `dedupe-issues-scripts-shared-layer`**（见 `openspec/issues/batches.md` + `openspec/issues/INDEX.md`，5 项 T207-T211）：

- **T208〔AD-7〕**：`sdflow_issues_core` god-module 拆 cohesive 子模块（recorder/document/locking/ledger/policies）+ issues 内部消自调用子进程（subprocess→in-process import）。设计显式 defer。
- **T211〔冷审 V1·绑定 T208〕**：recorder 委派 token 改 ContextVar/显式 RecorderLockState 上下文栈隔离——F1 已修异常残留泄漏，但 in-process 多池并发/嵌套隔离须与 T208（in-process 化）同期做（今日全 CLI 独立进程不可达）。
- **T209〔AD-6〕**：`move --to-pool` 跨池搬运命令（误判落错池的机械恢复路径）。
- **T210〔冷审 F2〕**：CLI 等价 harness 升 frozen golden（stdout+落盘+exit 全字节对账）——等价性 T2 已 byte-identical 证过，此为前向 test 硬化。
- **T207〔T5 决策〕**：刷新 docs/ 下旧 skill 名到目标态（docs/** 整目录进机械守卫 allowlist，非承重点，显式后置）。

**Non-Goals（本 change 显式不做）**：不改数据模型/台账格式/CLI 语法；不做读取路径行为（= 后置 `harden-issues-read-path`）；不做 CLI 子命令树重整。

## ▶ 下一阶段建议

1. **`harden-issues-read-path`**（design 已点名的后置 change）——读取路径行为加固，与本次 dedup 是姊妹。优先级：中（本次已把共享逻辑单一源化，读取路径修复现在改一处即全池生效）。
2. **T208+T211 合并做**（god-module 拆分 + in-process 化 + token 上下文栈隔离）——三者强耦合（in-process 化才让 token 并发隔离成为真需求），一个 change 一起做。优先级：低（当前独立进程架构无暴露）。
3. **T210 harness golden 硬化**可随任一后续 issues change 顺手做（低成本、前向收益）。
4. T207/T209 为独立小项，按需另开。
