# Task 4 Spec 轴复审（fix1）

## 结论

**PASS**

本次为只读 Spec 轴复审，未修改生产代码或 `tickets.md`。复审对象为 Task 4（`SW-SCHEMA`、`SA-05`、`SA-17`）及 fix1 盘面；对照了 fix1 实现报告、旧报告、Task 4 brief、`tickets.md` 的 Task 4、`tasks.md` 的 4.1–4.4、`design.md` 的迁移计划与当前 diff。

## 输入与当前 diff

- `impl-reports/task4-dogfood-zero-regression-fix1.md`
- `impl-reports/task4-dogfood-zero-regression.md`
- `impl-reports/task4-brief.md`
- `tickets.md` 的 Task 4
- `tasks.md` 的 Task 4（4.1–4.4）
- `design.md` 的 Goals、Migration Plan 与迁移顺序约束
- 当前 diff：`sdflow-init/scripts/init.py`、`openspec/config.yaml`

当前 diff 将 Windows CLI 版本探测从固定裸命令改为优先使用 `shutil.which("openspec")`，再回退 `shutil.which("openspec.cmd")`，从而覆盖旧报告中 `[WinError 2]` 的实际阻断；`openspec/config.yaml` 指向 `sdflow-spec-driven`。

## 五项 Task 4 验收项逐项核对

| 验收项 | 实际报告证据 | 判定 |
|---|---|---|
| 1. 切换前为全部在途 change 保存 `openspec status --json` 快照 | fix1 报告明确记录 update 前仓内唯一在途 change 为 `align-sdflow-spec-with-openspec-schema`，并记录了 `openspec status --change ... --json` 的四个 artifact 快照：`proposal/specs/design/tasks` 均为 `done`，以及各自 `requires`。 | PASS |
| 2. 运行初始化/更新流程后，schema bundle 与 config 切到目标状态 | fix1 报告记录 `init.py update --dev --root .` 的实际输出：版本门通过（`openspec 1.7.0`）、铺设 project-local schema、bundle 以 54 文件刷新；并记录 `openspec/config.yaml` 首行为 `schema: sdflow-spec-driven`，schema bundle 存在。 | PASS |
| 3. 切换后逐 artifact 对比 status 快照且状态完全一致 | fix1 报告逐项对比 `proposal/specs/design/tasks`，四项均保持 `done`，artifact 路径未变化；既有 change 的 `schemaName` 保持 `spec-driven`，与切换前一致，符合既有 `.openspec.yaml` 绑定。 | PASS |
| 4. 一次性 change 验证新 dependencies 并删除 | fix1 报告记录实际 CLI 创建 `task4-dogfood-validation-20260731-fix1`；`instructions specs --json` 的 dependencies 含 `proposal`、`design`，`instructions tasks --json` 的 dependencies 含 `proposal`、`design`、`specs`；两份载荷均含成对 `sdflow:delegation` 标记与 `resolvedOutputPath`；最终 `Test-Path` 为 `False`。 | PASS |
| 5. 证据来自 CLI 实际输出而非静态配置推断 | fix1 报告分别记录了 update 实际输出、schema validate 实际结果、一次性 change 的 CLI 返回载荷，以及 status 与 instructions 的 JSON 结果；旧报告的版本门失败也被 fix1 的实际成功输出和当前 Windows 命令解析 diff 对应关闭。 | PASS |

## 旧报告阻断项复核

旧报告的唯一阻断是 Windows Python 子进程以裸 `openspec` 启动失败，导致版本门未通过、目标 schema 未切换。fix1 报告记录该问题消失，且当前 `init.py` diff 提供了对应的可审计修复路径。fix1 还记录了：

- `openspec schema validate sdflow-spec-driven` 通过；
- 定点回归：`58 passed, 1 skipped`；
- `openspec validate align-sdflow-spec-with-openspec-schema --strict` 通过；
- `git diff --check` 通过。

这些结果与 Task 4 的五项验收目标一致，未发现仍会阻断 Spec 轴放行的缺口。

## 最终裁决

Task 4 fix1 的 Spec 轴结论为 **PASS**。可解除 Task 4 的 Spec 轴阻断；本报告不勾选 `tickets.md`，也不替代后续实现管线的独立门禁。
