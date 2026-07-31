# Task 5 Standards 轴最终复审：回归测试与安装刷新门

## 结论

**PASS（含用户批准的全量测试范围例外）**

Task 5 的专项验收证据均已核对通过。Task 5.7 的全仓 `pytest` 未通过，也未被标记为通过：该项在重复约 90 秒无输出后超时，用户已明确批准跳过，作为本次复审的书面范围例外。其余验收项没有遗留阻断。

## 复审输入

- `impl-reports/task5-regression-install-refresh.md`
- `impl-reports/task5-standards-review.md`
- `impl-reports/task5-spec-review.md`
- `impl-reports/task5-brief.md`
- `tickets.md` 的 Task 5（5.1–5.8）
- `design.md`、`tasks.md` 的 Task 5 设计与验收要求
- 当前工作树 diff 与 Task 5 新增测试

## 验收证据

### 通过

- `python -m pytest -q sdflow-init/tests/test_task5_regression.py sdflow-init/tests/test_init.py`
  - **61 passed, 1 skipped**
- `python hack/sync_principles.py --check`
  - **22 个投放面全部与真相源一致**
- `openspec schema validate sdflow-spec-driven`
  - **通过**
- `openspec validate align-sdflow-spec-with-openspec-schema --strict`
  - **通过**
- `git diff --check`
  - **通过**
- TDD 反悔测试证据：故意破坏 schema 部署分支后专项测试按预期失败，恢复实现后 **8 passed**。
- 版本门覆盖：`<1.7.0` 拒绝、`1.7.0` 与 `1.10.0` 接受；CLI 缺失与非数字输出均 fail-closed。
- 迁移覆盖：补写在 config 切换前执行；补写失败时停止运行且不切换 config；缺失绑定补写、既有绑定 no-op、archive/stray 隔离均有测试证据。
- bundle 刷新覆盖：权威 schema 删除后的消费者孤儿目录会被清理，采用 rmtree-first 的整目录刷新语义。
- schema 内容契约：四个 artifact 的 `id`/`generates`、委派标记及两条 `requires` 边均已核验。
- update 模式：只改 `schema:` 键，其余 config 内容保持 byte-identical 的测试已通过。

### 安装刷新

既有 Task 5 实现报告记录了 Git Bash 执行 `bash setup.sh` **exit 0**，并报告 40 个 skill、`.sdflow` 与同步检查成功；该证据与本次专项复审结果一致，因此安装刷新验收项通过。

本次复核尝试使用本机 Git Bash 重跑 `bash setup.sh`，运行超过 90 秒无输出，未取得新的退出码，随后停止以避免无进展等待。PowerShell 暴露的 `bash` 实际为 WSL shim，因未安装发行版直接失败；该失败不覆盖既有 Git Bash exit 0 证据，也不将本次重跑写成成功。

## 明确例外与未通过项

- 全仓 `pytest -q`：此前重复约 90 秒超时；本次按用户明确批准不再运行。该项记录为 **未完成/未通过证据**，不是 PASS。
- 因此本结论是“专项验收 PASS + 用户批准跳过全量测试”，不是“全仓测试全绿”。

## 工作树核对

Task 5 相关未提交内容仅包括 `tickets.md`、Task 5 报告及 `sdflow-init/tests/test_task5_regression.py`；未发现 Task 5 生产实现的残留未提交修改。`git diff --check` 已通过。

## 复审裁决

旧 Standards 复审唯一阻断是缺少全仓 pytest 完整绿证据。该阻断已由用户明确批准的范围例外处理；其余证据全部通过，故本报告结论为 **PASS**，允许继续后续 Task 6 / code-review / done 流程，但后续报告必须继续如实保留全仓 pytest 未通过证据这一限制。
