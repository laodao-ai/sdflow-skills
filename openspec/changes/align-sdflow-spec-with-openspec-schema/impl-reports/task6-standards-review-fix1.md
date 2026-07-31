---
task: 6
axis: standards
verdict: BLOCKED
---

# Task 6 Standards 复审（fix1）

## 范围与判定口径

本次复审读取并核对了：

- `task6-documentation-boundaries.md`
- `task6-brief.md`
- `tickets.md` 的 Task 6
- 先前的 `task6-standards-review.md` 与 `task6-spec-review.md`
- 当前工作树 diff
- `CLAUDE.md`、`README.md`、roadmap、todolist/INDEX
- canonical `sdflow-init/assets/workflow/generation-process.md`
- dogfood `openspec/workflow/generation-process.md`

全量 `pytest` 按用户明确批准跳过，不作为本次阻断理由。

## 结论

**BLOCKED。** 先前复审指出的 dogfood 重复段落已经关闭，Task 6 的文档内容和 bundle 可观察产物也已核实；但阶段一人读侧同步的机械契约仍失败：`CLAUDE.md` 已加入 project-local schema 边界段，而 `AGENTS.md` 的对应“阶段一入口”小节没有同步该段，导致仓库既有测试失败。该缺口必须修复后才能放行 Task 6。

## 验收矩阵

| Task 6 验收项 | 结论 | 证据 |
|---|---|---|
| 阶段一入口文档说明 project-local schema 与提示层边界 | **BLOCKED** | `CLAUDE.md` 第 217 行起已说明 schema、委派提示层、版本门、迁移顺序与 fork 边界；但 `AGENTS.md` 同名人读段没有同一段，`hack/tests/test_canonical_entry_sync.py::test_two_human_carriers_are_verbatim_identical` 失败。 |
| roadmap P1 标记为已交付 | PASS | `openspec/roadmaps/openspec-1.7.0-followup/roadmap.md` 将 P1 标为“✅ 已交付（本 change）”，并明确全量 pytest 未作为放行证据。 |
| fork 漂移无机械门记录到 todolist，且本 change 不实现该能力 | PASS | T264 已写入 `openspec/issues/todolist/2026-07-todolist.md`，并出现在 `openspec/issues/INDEX.md`；roadmap 同步保留该边界。 |
| 文档中的 schema、委派、fallback 和迁移顺序与 ticket 语义一致 | PASS（待人读侧同步门关闭） | canonical 与 dogfood workflow 内容一致，均说明 schema 结构/依赖/委派提示、版本门失败回落内置 schema、先补写后切配置且补写失败不切换，并明确 fork 漂移不在本 change 范围。 |
| 修改 assets 后安装/bundle 刷新可证明消费侧不是旧版 | PASS（观察性证据；非 setup 成功） | `bash setup.sh` 本次 Git Bash 重跑无新成功退出码，最终超时 `exit 124`，因此不宣称 setup 成功；但既有 Task 5 证据记录过 `bash setup.sh` `exit 0`、安装 40 个 skill 与 `.sdflow`，本次又核实 canonical/dogfood `generation-process.md` 字节一致（均 9,166 bytes）且 dogfood bundle 共 54 个文件。该组合足以证明当前可观察 bundle 已刷新，但不能替代 setup 的成功结论。 |

## 实际验证

- `pytest -q hack/tests/test_canonical_entry_sync.py sdflow-init/tests/test_init.py`
  - **86 passed, 1 skipped, 1 failed**
  - 失败：`hack/tests/test_canonical_entry_sync.py::test_two_human_carriers_are_verbatim_identical`
  - 原因：`CLAUDE.md` 与 `AGENTS.md` 的“阶段一入口”小节不逐字一致；差异正是 project-local schema 边界段。
- canonical/dogfood 字节比较：`equal=True`，两者均为 9,166 bytes。
- dogfood `openspec/workflow/` 文件数：54。
- `git diff --check`：通过。
- 全量 `pytest`：按用户批准跳过；未标记为通过。
- setup 刷新：本次尝试 `exit 124`，未标记为成功；沿用既有 Task 5 的 `exit 0` 安装证据，并以本次可观察 bundle parity/file-count 作为消费侧刷新证据。

## 阻断与修复要求

1. 将 `CLAUDE.md` 阶段一入口新增的 project-local schema 边界段同步到 `AGENTS.md` 对应小节，或通过仓库规定的 canonical 生成/同步路径产生逐字一致结果。
2. 重新运行至少：
   `pytest -q hack/tests/test_canonical_entry_sync.py sdflow-init/tests/test_init.py`
3. 重新执行 `git diff --check`，并再次核对 canonical/dogfood 字节一致。

setup 本次 `exit 124` 不应被写成成功；若环境仍无法完成 setup，可继续记录该失败，但必须保留可验证的 bundle parity 与文件清单证据，并由后续门禁决定是否接受该降级。
