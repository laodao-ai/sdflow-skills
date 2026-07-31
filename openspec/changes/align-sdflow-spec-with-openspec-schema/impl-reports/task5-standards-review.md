# Task 5 Standards 轴复审：回归测试与安装刷新门

## 结论

**BLOCKED**

Task 5 的定点回归、既有 `sdflow-init` 测试、schema/同步校验、突变测试证据和安装刷新证据均通过；但 Task 5 brief 与 ticket 5.7 要求安装刷新后全仓 `pytest` 通过。本轮全仓 `pytest -q` 长时间无最终结果，已停止，未取得通过证据，因此不能判定 PASS。

## 核验范围

- `impl-reports/task5-regression-install-refresh.md`
- `impl-reports/task5-brief.md`
- `tickets.md` Task 5
- `design.md`、`tasks.md` 的 Task 5 设计与验收要求
- 当前工作树状态及 Task 5 新增测试

## 已通过项

### 1. 回归测试

- `python -m pytest -q sdflow-init/tests/test_task5_regression.py`：**8 passed**。
- `python -m pytest -q sdflow-init/tests/test_init.py`：**53 passed, 1 skipped**。
- 覆盖项与 Task 5 对齐：
  - bundle 整删重拷及 schema 孤儿清理；
  - `<1.7.0`、`1.7.0`、`1.10.0` 数值 semver 门；
  - CLI 命令缺失/非数字输出的 fail-closed；
  - 迁移补写发生在 config 切换前；
  - schema `id`/`generates`、委派标记及 requires 约束。

### 2. 反恒真 / mutation red-green

实现报告记录了对 schema 部署分支的定点破坏：刷新后 stale schema 目录仍存在，新增测试按预期失败；恢复实现后新增套件 **8 passed**。当前生产实现没有残留修改，工作树中的实现相关新增物仅为 Task 5 测试与报告文件。

### 3. 安装刷新与同步证据

用户提供的安装证据为：显式 Git Bash 命令 `bash setup.sh` exit 0，安装 40 个 skills 至 Claude/Codex 与 `.sdflow`，同步检查全部通过；本复审未重跑 `setup.sh`。

本地复核结果：

- `sdflow-ship/SKILL.md` 在 `C:\Users\LENOVO\.claude\skills`、`C:\Users\LENOVO\.codex\skills` 与仓内源文件 SHA-256 一致；
- `python hack/sync_principles.py --check`：通过，22 个投放面一致；
- `openspec schema validate sdflow-spec-driven`：通过；
- `openspec validate align-sdflow-spec-with-openspec-schema --strict`：通过；
- `git diff --check`：通过；
- `openspec/config.yaml` 已指向 `sdflow-spec-driven`，本仓 fork schema 文件齐全。

## 阻塞项

`python -m pytest -q` 在本轮运行超过约两分钟仍无最终输出，已停止；没有 exit code、通过数或失败清单，不能将其视为 PASS。该证据缺口直接对应 Task 5 brief 的“完成安装刷新后全仓 pytest 通过”和 ticket 5.7 P0。

## 复审裁决

**BLOCKED：补充一次安装刷新后的全仓 `pytest` 完整结果（exit 0，或记录失败/超时及明确处置）后再复审。**

