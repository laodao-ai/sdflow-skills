# Task 5：实现验证

状态：DONE（V-1 已修复：Windows workflow 的临时 probe 先 `init` 铺设、再以 GBK `update`；全量红已在 base 复现；本 change 聚焦单元与 GBK 集成通过；仓内无本机 e2e 命令，按聚合套件发现契约记未覆盖）。

## 套件发现

`openspec/config.yaml` 未设置顶层 `test-suites`。依照聚合套件发现契约改查仓内约定：`README.md` 与 `CLAUDE.md` 均将 `pytest` 定义为全仓测试命令；`.github/workflows/mechanical-gates.yml` 在 Ubuntu/macOS 矩阵执行 `python -m pytest -q -rs`。`.github/workflows/windows-recorder-smoke.yml` 是本 change 所需的真实 Windows 编码冒烟工作流，但没有可在本机替代该远端 CI 结论的 e2e 命令。

## 证据

全量单元 | `python -m pytest -q -rs` | 2 | `dd21a121fd6f934d8976d3c6a193b8232aee0217`

全量收集在 Windows/Python 3.14 于两个既有跨平台缺口失败：`signal.SIGHUP` 不存在，以及 `os.fsdecode(b"br\\xffken")` 抛出 `UnicodeDecodeError`。用 base `3b4f838b99f2ccd3bf7a246e8ab675a9b6c40943` 复跑同一全量命令，得到相同两个收集错误；因此不是本 change 引入的回归。`sdflow-issues/tests/test_task5_delivery_contract.py` 的 Windows 路径失败亦在该 base SHA 复现（Git Bash 无法解释传入的绝对 Windows 路径）。

单元（本 change 覆盖） | `python -m pytest -q -rs hack/tests/test_encoding_hygiene.py hack/tests/test_subprocess_encoding_contract.py sdflow-issues/tests/test_task5_delivery_contract.py -k "not upgraded_install_known_consumer_smoke"` | 0 | `dd21a121fd6f934d8976d3c6a193b8232aee0217`

结果：18 passed，1 deselected（被排除的用例即上段已由 base 复现的既有 Windows/Git-Bash 路径失败）。

集成 | `bash -lc 'PYTHONIOENCODING=gbk bash setup.sh 2>&1'` | 0 | `dd21a121fd6f934d8976d3c6a193b8232aee0217`

该命令在本机 Windows + Git Bash 下完成安装，并通过 `sync_principles`、workflow guide、async parity、tier parity 与 encoding-hygiene 门；输出不含 `UnicodeEncodeError` 或 `Traceback`。

机械门 | `python hack/check_encoding_hygiene.py` | 0 | `dd21a121fd6f934d8976d3c6a193b8232aee0217`

变更校验 | `openspec validate fix-windows-encoding-crash --strict --type change` | 0 | `dd21a121fd6f934d8976d3c6a193b8232aee0217`

V-1 同构 probe | `git init "$probe" && python3 sdflow-init/scripts/init.py init --root "$probe" && PYTHONIOENCODING=gbk python3 sdflow-init/scripts/init.py update --root "$probe"` | 0 | `dd21a121fd6f934d8976d3c6a193b8232aee0217`

上述 probe 从空目录开始，顺序与 Windows workflow 相同；常驻的 `test_windows_smoke_workflow_is_persistent_and_branch_agnostic` 同时断言 workflow 中的 `init` 在 GBK `update` 之前。

e2e | — | 未覆盖 | 本仓无 `test-suites.e2e` 配置，也无 README/开发约定给出的本机 e2e 命令；唯一相关的 `.github/workflows/windows-recorder-smoke.yml` 尚未在本提交上远端执行。本机不得将该 Windows-only CI 记为通过。

## 分诊结论

- 全量 pytest 的 Windows 收集红与 Git-Bash 路径红均已在 base 复现，不是本 change 引入的回归。
- 本 change 相关 18 项单元测试、GBK `setup.sh` 集成、encoding-hygiene 机械门、严格 change 校验与 V-1 同构 probe 均在同一最终源码 SHA `dd21a121fd6f934d8976d3c6a193b8232aee0217` 通过。
- 仓内没有 `test-suites.e2e` 或本机 e2e 命令；Windows workflow 是远端平台验证，不把“工作流已定义”假报为“远端已通过”，也不把缺层升级成环境 blocker。
- 验证期间 `retro_report.py` 再生的 `openspec/retro/report.md` 属命令副作用，已从本 change 工作树清理，未纳入交付。
