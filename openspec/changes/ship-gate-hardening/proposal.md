# ship-gate-hardening — Proposal

## Why

`ship_gate.py` 是阶段三「盘面即状态」的确定性判官（adr/0006(b)）。首个全链实战 change（`cross-model-outside-voice`，2026-07-04）暴露其三个判定缺陷（B1/B2/B3，见 `openspec/issues/buglist/2026-07-04-buglist.md`），单轮 ship 制造 **3 次假 REFUSE_START/误报、3 次人工越权**（空 commit 补锚 ×1、拍板重申 ×2）——人工越权本应是例外通道，现已成常规操作，直接侵蚀「编排层无人值守可靠推进」的核心承诺。三缺陷同源同文件、活体复现记录俱在，趁证据新鲜一次清掉。

## What Changes

- **B1（P2）修复**：实现进度收集窗口改为**包含 plan 落地 commit 自身**——`plan_first_sha` 返回的 sha 目前作 `{sha}..HEAD` 排他起点（`ship_gate.py:231-232`），当 checkpoint 的 `add -A` 把 `superpowers-plan.md` 与 task1 锚打进同一 commit 时，task1 被漏数（已复现 11/12 误报）。
- **B2（P2）修复**：design 域新鲜度守卫（`is_stale` scope="design"，`ship_gate.py:88-93`）增加**阶段三合法尾流修订的豁免机制**——code-review 按工作流设计对 design.md/tasks.md 打 `[impl-review-fix]` 补丁并 `checkpoint(impl-review)` 提交，不应判「拍板失鲜」。豁免机制 ≥2 方案（commit subject 白名单 / 重申锚 / 监视面收窄），选型见 design.md 决策记录。
- **B3（P3）修复**：pre-flight 增加**归档终态识别**——change 目录已移入 `openspec/changes/archive/`（日期前缀锚死 glob 匹配 `YYYY-MM-DD-{change}`）且**该归档已落 base 树**（change 域可达，非全局分支态）时输出 SHIPPED，而非按 active 路径找不到 spec-review-report.md 就误报「未过设计门 REFUSE_START」（`ship_gate.py:199-205`；行 287-297 已有 SHIPPED 判定但归档后不可达）。glob 锚死日期前缀与 change 域判据两点选型见 design.md D3〔grill-amendment〕。
- **契约文档同步**：`ship_gate.py` 头注释契约表（窗口语义、新鲜度豁免、SHIPPED-after-archive）与 `sdflow-ship/SKILL.md` 相应提示语同步更新；`tests/` 补三缺陷的回归测试（`test_gate_impl_progress.py` / `test_gate_freshness.py` / 新终态用例）。
- 无 BREAKING：退出码语义、锚行字面集、JSON 输出字段均不变（B3 为新增可达路径，B1/B2 为误报收敛）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-workflow`：「阶段三编排台账确定性（ship_gate）」Requirement 三处行为修订——①完成判据窗口语义从 `<sha>..HEAD` 排他改为**含 plan 落地 commit 自身**（现 spec 原文把排他窗口写死在 Scenario「前置产物缺失点名」中，须随修）；②design-approved 新鲜度分域规则增加阶段三合法尾流修订豁免 Scenario；③新增归档后 SHIPPED 终态识别 Scenario。

## Impact

- **代码**：`sdflow-ship/scripts/ship_gate.py`（313 行单文件，三处判定函数）+ `sdflow-ship/tests/`（既有 9 个测试文件，B1/B2 落点 `test_gate_impl_progress.py` / `test_gate_freshness.py`，B3 新增用例）。
- **文档**：`sdflow-ship/SKILL.md`（链序段 REFUSE_START 提示语，如涉及）、`ship_gate.py` 头注释契约表。
- **技术栈**：纯 Python 编排脚本 + pytest，不命中 TG-01/02/03 任何领域清单（backend·go / embedded / frontend 均不适用）。
- **下游**：`/sdflow-ship` 编排 skill 的所有未来运行；无消费仓 bundle 内容变更（ship_gate.py 属 skill 本体，随 setup.sh symlink 即时生效，无需 sdflow-init update 推送）。

## Success Metrics

- **假 REFUSE_START / 误报次数** — 基准：单轮 ship 3 次（cross-model-outside-voice 实录）→ 目标：对同型盘面 0 次 — 度量方式：三缺陷各自的回归测试用真实复现盘面（task1 锚与 plan 同 commit / impl-review 补丁提交 / 归档后目录）断言正确 verdict；下一个真实 change 的 ship 全程人工越权计数。
- **回归零破坏** — 基准：sdflow-ship 测试套现有全绿 → 目标：修复后全绿且新增用例 ≥6（每缺陷 ≥2）— 度量方式：`pytest sdflow-ship/tests/` 通过数。

## 需求优先级（TG-19）

| 优先级 | 项 | 理由 |
|---|---|---|
| P0 | B1 窗口漏数、B2 失鲜误判 | 两者各在实战中直接触发人工越权，且每轮 ship 必经此判定路径 |
| P1 | B3 归档终态识别 | 只在归档后重跑 gate 时触发，误报但不阻塞主链（主链已完成） |
| P2 | 契约文档/SKILL 提示语同步 | 防文档与实现漂移，随修不独立成活 |

## 假设（TG-22）

- **checkpoint commit subject 约定稳定**：豁免/完成判据均信任 `~/.sdflow/hack/checkpoint-commit.sh` 产生的 `checkpoint(<tag>)` subject 前缀——此信任模型为 gate 既有先例（`done_task_ids` 即靠 `checkpoint(task<n>-` 判完成），伪造 subject 属已声明的接受项（人机同权、git 留痕可审计，见 `ship_gate.py` 头注释「已知不覆盖」）。若该假设失效（脚本改 subject 格式），完成判据与豁免同时失效，由契约测试 `test_anchor_contract.py` 同类机制兜底。

## Non-Goals（不在本次范围）

- **熔断重试计数脚本化（T26）**：gate 零副作用约束下的计数下沉是独立设计题，与本次三个误报修复无耦合——可证伪假设：若 T26 与 B1/B2/B3 有耦合，修复后 STEP_IN_PROGRESS 重试路径行为应发生变化；实际三修复均不触及该路径。
- **T28/T29（阶段提示 prompt / 时长度量）**：同批次但属「工作流信息显性化」族，归 workflow-metrics-loop 评估——可证伪假设：若它们必须随本 change，则 gate 修复的验收会依赖度量数据；实际验收仅依赖回归测试与下轮 ship 实录。
- **gate 对 rebase/--amend 历史改写的防伪**：既有已声明接受项，本次不扩大威胁模型。

## Compliance（合规声明）

- adr/0004（ship 窄编排红线）：不越 grill / 设计门两个人类点——本次仅修 gate 判定精度，不改人类门位置。遵守。
- adr/0006(b)（步序推进用确定性台账）：修复强化而非削弱该约束（减少确定性判定的误报、降低人工越权频次）。遵守。
- 其余（数据模型/schema 边界、外部依赖）：N/A。

## 开放问题（TG-21）

- B2 豁免机制选型（≥2 方案）→ 归 design.md 决策记录（TG-23），设计门拍板。负责人：本 change 设计阶段；截止：设计门。
