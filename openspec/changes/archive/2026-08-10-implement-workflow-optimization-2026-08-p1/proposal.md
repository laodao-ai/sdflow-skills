## Why

镜 roster 复评（roadmap 阶段 2）被卡在判据缺失上：13 面镜触发「待复评」阈值一年量级，但砍留所需的两个判据——per-镜实修率（T108）与 per-change token 维（T104）——数据采了、指标没建；同时 issues 池四条错关项（T98/T99/T101/T102）的重分诊被 recorder「终态不可再改」契约挡住，需要 `reopen` 命令解锁。本 change 是 `openspec/roadmaps/workflow-optimization-2026-08/` 阶段 1 的 1.B 四子任务（度量决策端补全），阶段 2 的复评拍板直接消费本 change 的产出；token 维只能从新 change 起累积，越晚开始盲区越长。

## What Changes

- **1.B.1 实修率指标**：retro 新增 per-镜实修率历史回算——以归档报告 finding 行的 `已修[impl-review-fix]` 精确标注为主信号（严格窄文法），修复 commit 存在性降为佐证 flag；解析不出的样本进未知桶，per-镜输出可判定/未知/覆盖率三数（decision-memo D2）。
- **1.B.2 token 维度量**：`checkpoint-commit.sh` 在 `git add -A` 前内联调 helper，读当前 session transcript 的 usage 字段，追加累计快照行到 `openspec/changes/<name>/token-log.jsonl`，随同一 checkpoint commit 入库；采集失败/Codex 宿主写「无锚」降级行，MUST NOT 挡 checkpoint 主功能（decision-memo D1）。
- **1.B.3 retro 报告模版增列**：per-change 表增 token 列、聚合③ per-镜价值表增实修率列 + 三数注记；缺数据显式「无锚」，不留空。
- **1.B.4 recorder reopen 命令**：`issues_v2.py reopen <ID> --reason <理由> [--to OPEN|PROPOSED]`——closed→open 原子迁移 + 终态字段清理（原 closed_reason 进历史行不丢）+ 自动 reindex，带契约测试（decision-memo D3）。

无 BREAKING：既有命令语法、lens-metric 锚契约、checkpoint 调用方式全部不变。

## Capabilities

### New Capabilities

- `token-snapshot-anchor`：checkpoint 级 token 快照锚——采集机制（transcript 定位 + usage 累加）、`token-log.jsonl` 行 schema、失败/异宿主降级契约（无锚行，不冒充机械锚，不挡 checkpoint）。

### Modified Capabilities

- `workflow-retro`：新增 requirement——per-镜实修率历史回算（窄文法提取 + 未知桶 + 三数输出 + 样本量闸门）与 per-change token 维 join（读 token-log.jsonl，缺锚显式标注）。
- `issues-scripts-shared-core`：新增 requirement——`reopen` 命令契约（守卫/状态/字段清理/原子序/自动 reindex + 往返与拒绝面契约测试）；既有「终态不可再改」语义收窄为「不可经 set-status 再改」，reopen 是唯一受控逆转换。

## Impact

- **代码**：`sdflow-retro/scripts/retro_report.py`（+实修率回算与两列渲染）、`sdflow-issues/scripts/issues_v2.py`（+reopen，内联复用其自身 M-2 mechanics——`sdflow_issues_core/` 已于 bad1f87 删除脱钩，MUST NOT 引用 [spec-review-amendment]）、`sdflow-init/assets/hack/checkpoint-commit.sh`（+token helper 调用；全局资产，真相源在 assets，改后须重跑 `setup.sh`）+ 新增 token helper 脚本。
- **测试**：`sdflow-retro/scripts/tests/`、`sdflow-issues/tests/`、`hack/tests/`（checkpoint 假 HOME 沙盒模式）同步扩展。
- **数据面**：新文件形态 `openspec/changes/<name>/token-log.jsonl` 从本 change 起出现在各 change 目录并随归档保留；归档报告只读不改写。
- **技术栈**：纯 Python/Bash + Markdown，不命中 TG-01/02/03 领域清单。

## 需求优先级

- **P0**：1.B.4 reopen 命令（1.A.1 池对账的机械前置，阻塞面最宽）；1.B.1 实修率回算（阶段 2 拍板的主判据）。
- **P1**：1.B.2 token 快照锚（新 change 起累积，晚一天多一天盲区，但不阻塞阶段 2 起手——A1 闸门允许判据降级）。
- **P2**：1.B.3 报告增列中的 token 列渲染（依赖 1.B.2 落锚后才有数据可显）。

## 利益相关方与外部依赖

- **消费仓（下游项目）**：checkpoint-commit.sh 是 `~/.sdflow/hack/` 全局资产，所有用 checkpoint 的仓在 setup.sh 重跑后开始产 token-log.jsonl；降级路径保证无 transcript 环境（Codex 宿主/非 Claude 会话）只多一行无锚记录，行为无破坏。
- **sdflow-init bundle 同步面**：真相源 = `sdflow-init/assets/hack/`，MUST 先改 assets 再经 setup.sh 分发，禁止只改 `~/.sdflow/hack/` 副本。
- **外部依赖**：无新增第三方依赖；transcript JSONL 是 Claude Code 宿主的非公开格式（假设 A-3 覆盖其漂移风险）。

## 开放问题

- CONTEXT.md 词表是否收录「实修率」（与既有采纳率/独立率同族第三轴）——负责人：用户；截止：本 change 归档前（B.7 术语提议，未确认 MUST NOT 自动写入）。

## 假设

- **A-1 历史归档报告存在足量可判定样本**（承 roadmap 假设 A1）：失效 ⇒ 覆盖率三数如实呈现低值，该镜实修率标「参考」不入砍留依据；阶段 2 以独立率 + 人工复核为准。回算机制本身仍交付。
- **A-2 transcript usage 字段持续在场**（本机实测在场，含 input/output/cache 三类）：失效 ⇒ helper 写无锚降级行，checkpoint 主功能不受影响；token 列显式「无锚」。
- **A-3 transcript JSONL 格式为宿主非公开格式，可能随版本漂移**：失效形态同 A-2（解析不出 = 无锚行），不产生错数（宁缺毋假）。
- **A-4 reopen 扩展不破坏既有契约测试**（承 roadmap 假设 A3）：失效 ⇒ 修 reopen 实现适配既有不变量，MUST NOT 放宽既有守卫迁就新命令。

## Success Metrics

- retro 再生报告含实修率列 + 可判定/未知/覆盖率三数注记，13 面待复评镜在 **(layer, lens) 粒度**的实修率可读（达标或标「参考」）。[spec-review-amendment] 粒度诚实边界：历史 finding 行的镜归属信号只到 lens 级，五元组（host/runner/site）细分不可回算；真实语料试算显示可判定密度低，**大面积「参考」亦为合法产出**——「判据密度不足以支持砍留」本身就是诚实结论，不构成验收失败。
- 本 change 自身的 checkpoint 产出 token-log.jsonl 快照行（dogfood 即验收：跑一次真实 checkpoint 验证）。
- `reopen` 往返契约测试绿（add→终态→reopen→字段/目录/INDEX/CLOSED 全一致）+ 拒绝面测试绿。
- 全仓 pytest 绿。

## Non-Goals

- **1.A 池对账操作**（重开四条错关项、新增两条 todo、关 T119）——recorder 操作，非本 change 代码范围；1.A.1 在本 change 归档后执行。
- **逐镜 token 度量**——harness 无 per-子代理 token（wco P2 确认），MUST NOT 做机械承诺；token 维只到 per-change/checkpoint 级。
- **镜 roster 复评与裁决协议改造**——阶段 2（`implement-workflow-optimization-2026-08-p2`）。
- **lens-metric 锚契约变更**——实修率是纯读侧派生，不改锚 schema、不改 emitter。
- **set-status 自动 reindex 的存量不对称**——不加宽，保持现状。

## Compliance

N/A（无合规/隐私/许可证影响；token 快照只含计数与 session_id，不含对话内容）。
