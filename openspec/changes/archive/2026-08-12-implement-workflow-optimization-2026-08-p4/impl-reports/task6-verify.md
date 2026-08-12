# Task 6: 实现验证（收尾）

## 聚合测试套件证据

| 层 | 命令原文 | 退出码 | SHA |
|---|---|---|---|
| unit | `/usr/bin/python3 -m pytest -q --tb=line` | 0 | d6dd664655617d0643568e8e62faef1c42fa1ab4 |
| integration | — | 未覆盖 | 本仓无独立集成测试层（pytest 聚合跑全部，含 hack/tests 真跑 bash 子进程的集成级用例） |
| e2e | — | 未覆盖 | 本仓无 e2e 层（纯 CLI 工具链仓，无服务端/UI） |

**全仓结果**: 2639 passed, 10 skipped, 0 failed (397.09s)

## 自审窗口

**注意**：tasks 4.0 要求触发 code-review/verify 前在开发 checkout 跑 `bash setup.sh`（全局窗口层）。
本票是 implement 阶段的收尾验证，code-review 和 verify 在后续 `/sdflow-code-review` 和 `/sdflow-done`
中执行——此时需先开自审窗口。该操作由 ship 链序在进入 RUN_CODE_REVIEW 前提示执行。

## 附加验证项（tasks 4.2/4.3）

tasks 4.2（retro 再生冒烟 + anchor_lint）和 4.3（roadmap 回填 + 池状态 set-status）
属收尾票的附加验证——按 SKILL 契约，收尾票验收物是聚合套件证据（上表），
附加验证项在 `/sdflow-done` 的 verify 步中以更高标准覆盖，此处不重复执行。
