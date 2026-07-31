# Task 2 Standards 轴审查

## 结论

BLOCKED

## 审查范围

- `impl-reports/task2-brief.md`
- `impl-reports/task2-project-local-schema.md`
- `tickets.md` 的 Task 2
- `design.md`
- `specs/spec-workflow/spec.md`、`specs/spec-authoring/spec.md`
- 当前 diff：`sdflow-init/scripts/init.py`、`sdflow-init/tests/test_init.py`、`sdflow-init/assets/workflow/config.template.yaml`

本审查为 Standards 轴，只读核验；未修改生产代码或 `tickets.md`。

## 逐项核验

### 1. CLI semver 版本门：部分通过

证据：`sdflow-init/scripts/init.py:386-402` 使用 `openspec --version`，将版本解析为整数三元组并与 `(1, 7, 0)` 比较；命令异常、非零退出和不可解析输出均返回 fail-closed 结果。`test_init.py:180-204` 覆盖 `1.6.9`、`1.10.0` 和非数字输出；定点测试通过。

结论：实现和已有测试满足该项；命令缺失的独立测试未出现，但代码的 `OSError` 分支已核对。

### 2. 在途 change 迁移范围与幂等：部分通过

证据：`init.py:405-423` 只遍历 `openspec/changes` 的目录，跳过名为 `archive` 的目录，只处理含 `proposal.md` 且没有 `.openspec.yaml` 的目录；已有绑定直接跳过。`test_init.py:221-236` 覆盖已有绑定的幂等性和 archive 隔离。

结论：主判据符合 ticket；但“stray 目录”没有独立、明确的 fixture 或机械判据。当前实现实际以“无 `proposal.md`”作为跳过条件，报告中“跳过 stray”的表述缺少对应证据，不能按完整通过计。

### 3. 补写失败必须中止且不得切换配置：未通过

证据：`run()` 在 `init.py:936-963` 中先调用 `migrate_changes()`，再调用 `copy_bundle()` 和 `handle_config()`；补写异常会离开主流程，理论上不会执行配置切换。`migrate_changes()` 的文件写入异常也没有被吞掉。

缺口：`test_init.py` 没有模拟任一补写失败，也没有断言 `.openspec.yaml`/`config.yaml` 的最终状态。Task 2 ticket 明确要求“任一补写失败会中止本次运行，配置不会切换；顺序有测试证据”，当前只有代码顺序，没有失败路径测试证据。该项是阻断项。

### 4. schema bundle rmtree-first 整删重拷：通过

证据：`copy_bundle()` 在 `init.py:253-260` 对 `openspec/schemas` 先 `shutil.rmtree()` 再 `shutil.copytree()`；`test_init.py:239-247` 覆盖消费仓孤儿文件被清除。Task 2 报告也记录了该定点验证。

### 5. 配置模板与 update 窄 patch：部分通过

证据：`config.template.yaml:17` 指向 `sdflow-spec-driven`。`init.py:321-385` 只匹配顶层 `schema:` 行，并通过临时文件原子替换；`test_init.py:226-238` 断言除 schema 行外内容保持字节一致。

结论：实现符合窄 patch 要求。当前 diff 没有 `openspec/config.yaml` 的源文件变更；其运行时切换由 `run()` 完成，但没有本仓 dogfood 的门通过运行证据。该点单独不足以阻断 Task 2，但需在后续集成/dogfood 验证中补齐。

### 6. 版本门与迁移结论进入动作汇总：通过

证据：`run()` 将 `_schema_gate()` 结果追加到 `report`，并分别追加迁移数量或“版本门未通过而跳过迁移”的结论（`init.py:933-942`）；`task2-project-local-schema.md` 记录了相关输出行为。

### 7. 测试与验证证据：部分通过

实际复跑：

- `pytest sdflow-init/tests/test_init.py -q`：`50 passed, 1 skipped`
- `git diff --check`：通过
- `pytest sdflow-init/tests -q`：此前运行在 120 秒内无结果输出并超时；实现报告未将其宣称为通过。

定点测试足以证明正常版本门、迁移幂等、archive 隔离、配置窄改和孤儿清理，但没有覆盖 Task 2 所要求的“补写失败后配置不切换”失败路径，因此不能作为完整 PASS 证据。

## Findings 台账

| ID | 严重级别 | 位置 | finding | 处置 |
|---|---|---|---|---|
| T2-S1 | BLOCKER | `sdflow-init/tests/test_init.py`；对应实现 `sdflow-init/scripts/init.py:936-963` | 缺少补写失败注入测试，未机械证明失败会中止且 `config.yaml` 不切换 | 补充失败路径测试后重新跑 Standards 轴 |
| T2-S2 | IMPORTANT | `sdflow-init/tests/test_init.py`、`init.py:405-423` | “stray 目录不受影响”没有独立测试或明确判据；当前仅通过无 `proposal.md` 间接跳过 | 明确 stray 定义并补测试；若定义就是无 proposal，则在测试中钉死该契约 |

## 最终判断

BLOCKED。Task 2 的正常路径已有可复现定点绿灯，但 ticket 明确要求的补写失败顺序证据缺失，且 stray 隔离声明没有独立机械锚点。补齐 T2-S1，并明确/覆盖 T2-S2 后，方可重新审查为 PASS。
