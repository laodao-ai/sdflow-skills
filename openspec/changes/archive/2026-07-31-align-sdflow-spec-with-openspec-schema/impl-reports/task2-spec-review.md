# Task 2 Spec 轴审查 — project-local schema 下发与迁移

## 结论

**BLOCKED**

审查对象为 `tickets.md` 的 Task 2（`R-ID: SW-SCHEMA`）。本审查仅覆盖 Spec 轴，未修改生产代码或 `tickets.md`。

阻塞原因：Task 2 的两项关键验收没有可接受的反恒真证据：

1. 没有测试证明任一在途 change 的 schema 补写失败时，`config.yaml` 不会切换。
2. 没有测试覆盖 `openspec` 命令缺失分支；现有测试只模拟了非数字版本输出。

此外，相关测试套件 `pytest sdflow-init/tests -q` 在实现报告中记录为 120 秒无输出超时；本次复核重跑的定点命令通过，但不能替代未完成的全量证据。

## 审查输入

- `impl-reports/task2-brief.md`
- `impl-reports/task2-project-local-schema.md`
- `tickets.md` 的 Global Constraints 与 Task 2
- `design.md` 的迁移顺序、版本门、bundle 下发和配置窄 patch 约束
- `specs/spec-workflow/spec.md` 的 project-local schema 迁移要求
- `specs/spec-authoring/spec.md` 的相关 schema/CLI 载荷约束
- 实际代码 diff：
  - `sdflow-init/scripts/init.py`
  - `sdflow-init/assets/workflow/config.template.yaml`
  - `sdflow-init/tests/test_init.py`

## R-ID 与验收复选框核对

| 验收项 | 代码/测试证据 | 判定 |
|---|---|---|
| CLI 版本按 semver 数值元组判断；`<1.7.0`、命令缺失、非数字输出 fail-closed 并输出一行结论 | `init.py:383-402` 使用整数元组比较并处理 `OSError`、非零退出码和无法解析输出；`test_init.py:179-199` 覆盖 `<1.7.0` 与非数字输出，但没有命令缺失测试 | **BLOCKED：证据缺失** |
| 仅扫描含 `proposal.md` 的在途 change；缺绑定补写，已有绑定 no-op，归档和 stray 跳过 | `init.py:405-420` 明确跳过 `archive`、非目录、无 `proposal.md` 和已有 `.openspec.yaml`；`test_init.py:201-220` 覆盖补写、幂等和归档跳过 | **PASS** |
| 任一补写失败中止本次运行，配置不会切换；顺序有测试证据 | `init.py:933-940` 将迁移置于 config 处理前，异常会阻止后续切换；但没有注入补写失败并断言 config 未改变的测试 | **BLOCKED：关键验收无测试证据** |
| schema bundle 采用 rmtree-first 整删重拷，权威源删除文件不残留 | `init.py:211-219` 对 `openspec/schemas` 执行 `rmtree` 后 `copytree`；`test_init.py:212-219` 验证 orphan 清理 | **PASS** |
| 版本门通过时模板与消费仓配置指向 fork schema；update 只改 schema 行且其他内容 byte-identical | 模板改为 `sdflow-spec-driven`；`init.py:288-361` 只替换首个顶层 schema 行；`test_init.py:202-210` 验证窄 patch，`test_init.py:174-179` 验证 update 切换 | **PASS** |
| 版本门与迁移补写结论进入既有动作汇总 | `init.py:933-946` 将版本门和迁移结果追加到 `report`，最终由既有 run 输出 | **PASS** |

## 与批准设计的对照

- 迁移顺序实现为“先补写、后切 config”，符合 `design.md` 的迁移计划及 `spec-workflow` 要求。
- project-local schema 下发使用权威源 `sdflow-init/assets/schemas/`，并对消费仓 `openspec/schemas/` 做整删重拷，符合单一权威源和孤儿清理要求。
- 配置更新采用原子替换并只改顶层 `schema:` 行，符合设计中的窄 patch 约束。
- 版本解析使用数值元组，因此 `1.10.0` 不会按字符串比较错误；定点测试已验证该路径。
- 迁移函数的 docstring 声明“失败必须向上抛”，但验收所需的行为闭环没有对应回归测试。Spec 轴不能把实现意图当作验收证据。

## 验证结果

- `pytest sdflow-init/tests/test_init.py -q`：**50 passed, 1 skipped**。
- `pytest sdflow-init/tests -q`：实现报告记录为 **120 秒无输出超时**，未得到完整结果。
- 实现报告记录 `git diff --check`：通过。

## 修复前置条件

要将本 Task 2 审查结论改为 PASS，至少需要补齐并独立运行：

1. 模拟 `openspec --version` 命令缺失，断言保留内置 schema、未下发 project-local schema，并输出明确的一行原因。
2. 模拟第二个在途 change 的 `.openspec.yaml` 补写失败，断言本次运行失败、`config.yaml` 在运行前后 byte-identical，且不把失败误报为迁移完成。
3. 重新运行相关全量测试，给出退出码；若仍超时，报告未覆盖范围和判定依据，不能把全量验收标为通过。`n