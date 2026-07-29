# Windows 全量 pytest 修复清单

## 目标与验收口径

目标是在原生命令 `pytest` 下让 Windows 测试盘面真实全绿，不依赖调用者预设
`PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8`，也不把可修的编码问题整体 skip。

验收必须同时满足：

1. Windows 本机 Python 3.14：`pytest` 退出 0。
2. GitHub `windows-latest` 至少覆盖 Python 3.12 与 3.14，执行全量 `py -m pytest`。
3. POSIX-only 测试只按能力边界 skip；跨平台业务测试必须实际执行。
4. 测试辅助代码的文本子进程显式声明 `encoding="utf-8", errors="replace"`；不得靠全局 monkeypatch `subprocess` 或修改 locale 掩盖漏点。
5. 新增机械门覆盖生产代码与测试代码，防止以后新增 `text=True` 调用重新依赖 locale。

## 复现基线

记录日期：2026-07-29。

环境：Windows 11、CPython 3.14.3、`locale.getencoding() == "cp936"`、
`sys.getfilesystemencoding() == "utf-8"`、filesystem errors 为 `surrogatepass`。

命令：

```powershell
python -m pytest -q --continue-on-collection-errors
```

结果：

| tests | collection errors | failures | skipped |
|---:|---:|---:|---:|
| 1560 | 2 | 328 | 7 |

`--continue-on-collection-errors` 仅用于盘点；最终验收仍使用裸 `pytest`。

## 根因总表

| ID | 根因 | 当前表现 | 正确修法 |
|---|---|---|---|
| W1 | 测试子进程 `text=True` 未声明编码 | GBK reader thread 抛 `UnicodeDecodeError`，`stdout/stderr` 变成 `None`，继发 300+ 个假失败 | 所有文本子进程显式 UTF-8 + replace；提取共享测试 helper 时仍保留调用点机械门 |
| W2 | POSIX 信号/进程组测试在 Windows 收集或执行 | `signal.SIGHUP` 不存在；`Popen.send_signal(SIGINT)` 不支持；`os.kill(pid, 0)` 语义不同 | `outside_voice_child_lifecycle` 在 Windows 模块级 skip；保留 Linux/macOS 全量执行 |
| W3 | 测试依赖 POSIX 文件名/权限/argv 字节形态 | executable bit、Tab 文件名、原始非 UTF-8 argv 在 Win32 不可构造 | 单元层使用跨平台可控输入；只有必须依赖 OS 形态的端到端格在 Windows skip |
| W4 | Windows 路径直接拼给 Bash | `D:\...` 被 Bash 吃掉反斜杠，变成 `D:project...`，退出 127 | 调 Bash 前统一用 `cygpath -u` 或 `Path.as_posix()` + `/d/...` 转换 helper；不得逐测试手拼 |
| W5 | 路径断言硬编码 `/` | 实际集合包含 `\`，字符串等值失败 | 所有仓内相对路径比较统一 `.as_posix()` |
| W6 | Unix-only API/权限假设 | `os.geteuid` 不存在；symlink 需要 Windows Developer Mode/特权 | 能力探针后 skip；不以 `os.name` 猜 symlink 能力 |
| W7 | shell 命令/CLI 查找假设 POSIX | `touch`、`/bin/bash`、POSIX quoting 或无 `.exe/.com` | 通过统一 shell fixture 解析 Git Bash；Windows 原生命令使用 `.com/.exe` 或 Python API |
| W8 | Windows CI 只跑定向 smoke | 远端绿不能证明全量 pytest 绿 | workflow 增加 Python 3.12/3.14 matrix 的全量 pytest job |

## P0：先解除两个 collection error

### 1. `sdflow-init/tests/test_outside_voice_child_lifecycle.py`

现状：模块级参数表直接引用 `signal.SIGHUP`（约第 199、333 行），Windows import 时即失败。

修改：

- 文件验证的是 POSIX signal、GNU timeout process group、负 PGID kill 和 orphan 行为，整体不具备 Windows 等价语义。
- 在 import 完成后、任何 POSIX 常量求值前执行 Windows 模块级 skip：

  ```python
  if os.name == "nt":
      pytest.skip(
          "requires POSIX signals and process-group semantics",
          allow_module_level=True,
      )
  ```

- Linux/macOS 必须继续覆盖 TERM/INT/HUP；不得简单删除 HUP 格。

### 2. `sdflow-ship/tests/test_gate_freshness.py`

现状：模块级 `os.fsdecode(b"br\xffken")` 在 Windows 的 `surrogatepass` 策略下抛
`UnicodeDecodeError`。

修改：

- 纯函数格用显式 `b"br\xffken".decode("utf-8", "surrogateescape")` 构造 lone surrogate，避免依赖宿主 filesystem codec。
- “原始非 UTF-8 argv 字节进入子进程”的端到端格仅 POSIX 可达，Windows 单独 skip；Windows argv 是 Unicode，没有同一输入通道。
- 同文件以下三格也必须按能力 skip，否则解除 collection 后仍红：
  - `test_mode_only_change_on_tasks_is_stale`：NTFS 不提供 POSIX executable-bit 变更。
  - `test_spec_path_with_tab_is_stale`：Win32 文件名不允许 Tab。
  - `test_ls_tree_keeps_tab_path_raw_and_unquoted`：同上。

## P0：文本子进程编码面修

机械扫描口径：测试文件内 `subprocess.run/Popen/check_output/check_call`，显式
`text=True` 或 `universal_newlines=True`，但没有 `encoding=`。当前共 **55 个文件、234 个直接站点**。

每个站点默认补：

```python
encoding="utf-8",
errors="replace",
```

若站点消费 JSON、结构化协议或严格等值，仍使用 replace 解码，但解析/断言必须 fail-closed；不得静默接受损坏 payload。

| 文件 | 站点数 | 当前行号 |
|---|---:|---|
| `hack/tests/test_decision_memo_gate.py` | 3 | 325, 548, 554 |
| `hack/tests/test_harden_sdflow_spec_followup_closure.py` | 1 | 59 |
| `hack/tests/test_install_agents.py` | 4 | 52, 250, 264, 370 |
| `hack/tests/test_sdflow_spec_agents.py` | 2 | 231, 275 |
| `hack/tests/test_sdflow_spec_failure_modes.py` | 7 | 145, 164, 222, 225, 496, 533, 544 |
| `hack/tests/test_sync_principles.py` | 1 | 198 |
| `sdflow-architecture/tests/test_sad_lint.py` | 3 | 9, 71, 92 |
| `sdflow-architecture/tests/test_sad_scaffold.py` | 3 | 9, 83, 384 |
| `sdflow-done/tests/test_roadmap_writeback_draft.py` | 1 | 336 |
| `sdflow-implement/tests/test_impl_route.py` | 13 | 234, 328, 330, 332, 334, 336, 384, 386, 388, 390, 392, 560, 726 |
| `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` | 1 | 432 |
| `sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py` | 1 | 329 |
| `sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py` | 5 | 284, 326, 328, 336, 462 |
| `sdflow-init/assets/workflow/tools/tests/test_outside_voice_guard.py` | 1 | 352 |
| `sdflow-init/assets/workflow/tools/tests/test_review_disposition_check.py` | 1 | 182 |
| `sdflow-init/tests/test_checkpoint_commit.py` | 2 | 11, 24 |
| `sdflow-init/tests/test_config_lint.py` | 5 | 30, 296, 313, 320, 326 |
| `sdflow-init/tests/test_ff0_branch_guard.py` | 2 | 27, 59 |
| `sdflow-init/tests/test_init_hardening.py` | 2 | 140, 163 |
| `sdflow-init/tests/test_outside_voice.py` | 4 | 18, 467, 547, 968 |
| `sdflow-init/tests/test_outside_voice_child_lifecycle.py` | 7 | 174, 360, 532, 637, 684, 770, 802 |
| `sdflow-init/tests/test_outside_voice_job.py` | 13 | 300, 1140, 1184, 2056, 3266, 3325, 3395, 3406, 3417, 3446, 3448, 3457, 3497 |
| `sdflow-init/tests/test_outside_voice_utf8.py` | 15 | 56, 194, 264, 469, 505, 519, 541, 562, 580, 620, 624, 626, 695, 696, 698 |
| `sdflow-init/tests/test_resolve_models.py` | 2 | 72, 91 |
| `sdflow-init/tests/test_resolve_workflow.py` | 2 | 12, 159 |
| `sdflow-init/tests/test_setup_failsafe.py` | 2 | 16, 35 |
| `sdflow-init/tests/test_setup_sdflow.py` | 8 | 17, 84, 95, 106, 182, 211, 234, 254 |
| `sdflow-issues/tests/test_batch_lint.py` | 1 | 30 |
| `sdflow-issues/tests/test_buglist.py` | 10 | 26, 200, 214, 245, 480, 492, 644, 777, 785, 800 |
| `sdflow-issues/tests/test_downstream_reference_guard.py` | 1 | 73 |
| `sdflow-issues/tests/test_frontmatter_dual_reader.py` | 1 | 30 |
| `sdflow-issues/tests/test_issues.py` | 19 | 276, 287, 321, 328, 340, 344, 459, 485, 505, 512, 531, 544, 555, 565, 573, 1728, 1804, 1873, 1900 |
| `sdflow-issues/tests/test_repo_root_identity_buglist.py` | 12 | 60, 161, 278, 319, 491, 557, 641, 730, 771, 898, 907, 972 |
| `sdflow-issues/tests/test_repo_root_identity_issues.py` | 12 | 60, 161, 278, 319, 491, 557, 641, 730, 771, 902, 911, 976 |
| `sdflow-issues/tests/test_repo_root_identity_todolist.py` | 12 | 60, 161, 278, 319, 491, 557, 641, 730, 771, 898, 907, 972 |
| `sdflow-issues/tests/test_task2_semantic_lock.py` | 14 | 102, 110, 186, 195, 296, 305, 316, 325, 335, 343, 350, 419, 473, 475 |
| `sdflow-issues/tests/test_task2_windows_local_fs_smoke.py` | 2 | 157, 219 |
| `sdflow-issues/tests/test_task3_frontmatter_writer.py` | 1 | 28 |
| `sdflow-issues/tests/test_task4_rename_snapshot.py` | 2 | 392, 656 |
| `sdflow-issues/tests/test_task5_delivery_contract.py` | 3 | 275, 378, 420 |
| `sdflow-issues/tests/test_task6_cli_equivalence_harness.py` | 1 | 40 |
| `sdflow-issues/tests/test_task6_coverage_gate.py` | 1 | 39 |
| `sdflow-issues/tests/test_todolist.py` | 10 | 25, 229, 243, 301, 510, 522, 656, 786, 794, 809 |
| `sdflow-retro/scripts/tests/test_retro_report.py` | 1 | 28 |
| `sdflow-ship/tests/test_frontmatter_archived.py` | 1 | 19 |
| `sdflow-ship/tests/test_gate_anchor_scope.py` | 2 | 22, 70 |
| `sdflow-ship/tests/test_gate_freshness.py` | 2 | 158, 1141 |
| `sdflow-ship/tests/test_gate_git_layer.py` | 1 | 94 |
| `sdflow-ship/tests/test_gate_impl_progress.py` | 6 | 87, 91, 93, 108, 112, 114 |
| `sdflow-ship/tests/test_gate_preflight.py` | 1 | 8 |
| `sdflow-ship/tests/test_gate_reviewed_sha.py` | 1 | 23 |
| `sdflow-ship/tests/test_gate_terminal.py` | 2 | 7, 96 |
| `sdflow-ship/tests/test_plan_resolver.py` | 1 | 155 |
| `sdflow-ship/tests/test_producer_parser_contract.py` | 2 | 29, 31 |
| `sdflow-ship/tests/test_superpowers_track_regression.py` | 1 | 57 |

### 共享 helper 优先级

先改以下高 fan-out helper，再复跑；它们一次修复会消掉大批继发失败：

1. `sdflow-init/tests/test_outside_voice_job.py::_run_job`。
2. `sdflow-ship/tests/test_gate_preflight.py::run_gate`。
3. `sdflow-ship/tests/conftest.py::_git`、`head_sha` 与 repo fixture 的 git init。
4. `sdflow-architecture/tests/test_sad_lint.py::run` / `test_sad_scaffold.py::run`。
5. `sdflow-implement/tests/test_impl_route.py` 的 route/CLI helper。
6. `sdflow-init/assets/workflow/tools/tests/` 下各工具的 CLI helper。

## P1：Windows shell 与路径修复

以下失败不是编码解码，而是 Windows 路径被 Bash 错误解释或依赖 Unix 命令：

| 文件/区域 | 现象 | 修改要求 |
|---|---|---|
| `sdflow-init/tests/test_outside_voice.py` | `/bin/bash: D:project...outside-voice.sh: No such file`、退出 127 | 所有传给 Bash 的 Windows path 先走统一 `bash_path()`；不得直接 `str(Path)` |
| `hack/tests/test_sdflow_spec_agents.py` | 同类 `D:project...` 路径损坏 | 复用同一个 Bash path helper |
| `hack/tests/test_install_agents.py` | `setup.sh` 路径损坏、退出 127 | 同上；setup runner 统一从 helper 构造 argv |
| `sdflow-init/tests/test_checkpoint_commit.py` | Bash 脚本退出 127 | 同上 |
| `hack/tests/test_decision_memo_gate.py`、`test_sdflow_spec_failure_modes.py` | 文档中抽出的 shell/hash 命令在 Windows 跑不起来 | 明确以 Git Bash 执行并转换路径；不能交给 PowerShell 默认解析 |
| `sdflow-init/tests/test_ff0_branch_guard.py` | 使用 `touch` 与 POSIX quoting，含 `; $() &` 的路径失败 | 用 Python `Path.touch()` 建哨兵；命令文本断言分别按 POSIX/Windows 表达，不执行拼接字符串 |
| `sdflow-init/tests/test_init_hardening.py` | PATH 夹具仅造 `python/python3` 无 `.exe/.cmd` 可执行面 | Windows 夹具生成 `.cmd` shim，POSIX 保留 executable script |

新增一个测试工具模块（建议 `tests/windows_compat.py` 或仓根 `test_support/windows.py`），只负责：

- `bash_path(Path) -> str`：Windows 转 `/c/...`，POSIX 原样。
- `bash_executable()`：解析 Git Bash，不硬编码 `/bin/bash`。
- `write_executable_shim()`：Windows 写 `.cmd`，POSIX 写 shebang + chmod。
- `can_create_symlink(tmp_path)`：真实探针，失败则给出明确 skip reason。

## P1：文件系统、权限与路径断言

| 文件 | 问题 | 修改要求 |
|---|---|---|
| `hack/tests/test_checkpoint_slug_coverage.py:103` | `str(path.relative_to(REPO))` 在 Windows 产生反斜杠 | 改为 `path.relative_to(REPO).as_posix()`；新增 Windows 风格回归 |
| `hack/tests/test_install_agents.py` | `os.geteuid` 不存在；创建 symlink 报 WinError 1314 | `getattr(os, "geteuid", None)`；symlink 用能力探针 skip，不按平台一刀切 |
| `sdflow-architecture/tests/test_sad_scaffold.py` | `os.geteuid` 不存在 | 同上；若测试只验证 POSIX owner/mode，Windows skip 该格 |
| `sdflow-devenv/tests/test_paths.py` | POSIX 路径/链接语义 | 路径比较 `.resolve()`/`.as_posix()`；链接格能力探针 |
| `sdflow-ship/tests/test_gate_freshness.py` | chmod、Tab filename、raw non-UTF-8 argv | 按 P0 所列三类能力边界拆分 |
| `sdflow-ship/tests/test_gate_git_layer.py` | 文件名/字节路径的 POSIX 假设 | 保留纯映射单测；真实 FS 格按能力 skip |

## P1：失败簇与责任文件

下面是本次完整运行的失败分布，用于复跑时核对是否按簇归零：

| 失败数 | 测试模块 | 主因 |
|---:|---|---|
| 103 | `sdflow-init/tests/test_outside_voice_job.py` | W1；少量 W4/W7 |
| 57 | `sdflow-init/tests/test_outside_voice.py` | W1、W4、W7 |
| 35 | `sdflow-architecture/tests/test_sad_scaffold.py` | W1、W6 |
| 22 | `sdflow-architecture/tests/test_sad_lint.py` | W1 |
| 13 | `hack/tests/test_harden_sdflow_spec_followup_closure.py` | W1 导致 JSON stdout=None |
| 10 | `sdflow-implement/tests/test_impl_route.py` | W1 |
| 10 | `hack/tests/test_sdflow_spec_agents.py` | W1/W4 |
| 9 | `hack/tests/test_install_agents.py` | W4/W6/W7 |
| 9 | `.../tools/tests/test_lens_metric_emit.py` | W1 |
| 8 | `hack/tests/test_sdflow_spec_failure_modes.py` | W1/W4 |
| 8 | `hack/tests/test_decision_memo_gate.py` | W1/W4/W7 |
| 6 | `sdflow-init/tests/test_checkpoint_commit.py` | W1/W4 |
| 5 | `sdflow-init/tests/test_config_lint.py::TestConfigLintModelTiersFleetKeyed` | W1 |
| 4 | `.../tools/tests/test_hr_tg_intersect.py` | W1 |
| 4 | `.../tools/tests/test_anchor_lint.py` | W1 |
| 3 | `sdflow-done/tests/test_roadmap_writeback_draft.py` | W1 |
| 2 | `sdflow-init/tests/test_ff0_branch_guard.py` | W7 |
| 2 | `sdflow-init/tests/test_init_hardening.py::TestT48SetupVersionCheck` | W7 |
| 2 | `sdflow-devenv/tests/test_paths.py` | W6/W7 |
| 2 | `hack/tests/test_sync_principles.py` | W1 |
| 2 | `.../tools/tests/test_review_disposition_check.py` | W1 |
| 其余 13 | config/init/scaffold/outside-voice-guard 等单项 | W1/W6/W7 |

## P0：扩展机械门

当前 `hack/tests/test_subprocess_encoding_contract.py` 主要守生产代码直接调用，未覆盖上述测试辅助面。

修改要求：

1. 扫描范围加入所有 `**/tests/**/*.py`、`hack/tests/**/*.py` 与 `sdflow-retro/scripts/tests/**/*.py`。
2. 同时识别：
   - `text=True`；
   - `universal_newlines=True`；
   - `kwargs = {"text": True}` 后 `subprocess.run(..., **kwargs)`；
   - wrapper 内部转发给 subprocess 的文本模式。
3. 白名单只能按“此调用不读取 stdout/stderr，且编码确实无关”的可机验条件建立；不得按文件整片排除。
4. 负向测试至少覆盖直接调用、动态 kwargs、共享 wrapper 三种漏法。

## P0：GitHub Actions 全量 Windows 门

修改 `.github/workflows/windows-recorder-smoke.yml`：

```yaml
strategy:
  matrix:
    python-version: ["3.12", "3.14"]

- uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}

- name: Run full pytest suite on Windows
  shell: bash
  run: py -m pytest
```

注意：现有定向 recorder/GBK/cp936 smoke 仍保留；全量 job 是新增终门，不替代定向诊断。

## 推荐实施顺序

1. P0 collection：两个收集错误 + `gate_freshness` 三个不可构造形态。
2. P0 shared helpers：优先修高 fan-out 的 6 个 helper。
3. P0 234 个显式编码站点机械清零，并扩展 AST 门。
4. P1 Bash path / executable shim / symlink capability helper。
5. P1 路径 `.as_posix()` 与 Unix-only API 清理。
6. 本机 `pytest` 全绿后，运行 `bash setup.sh`、编码门、`git diff --check`。
7. push 后必须观察 3.12/3.14 两档 `windows-latest` 全量 job 真实成功；不能以 workflow YAML 存在代替运行证据。

## 完成检查表

- [ ] 裸 `pytest` 在 Windows/Python 3.14 退出 0。
- [ ] collection errors = 0。
- [ ] failures = 0。
- [ ] skip 每一项都有不可构造的 OS 能力理由，不含编码问题。
- [ ] 55 个文件、234 个文本子进程漏点归零。
- [ ] 动态 kwargs / wrapper 机械门绿。
- [ ] Bash path helper 覆盖含空格、分号、`$()`、`&` 的路径。
- [ ] Windows symlink 能力探针在有/无 Developer Mode 两种环境行为明确。
- [ ] GitHub `windows-latest` Python 3.12 全量 pytest 成功。
- [ ] GitHub `windows-latest` Python 3.14 全量 pytest 成功。
- [ ] 现有 GBK/cp936 定向 smoke 继续成功。

## 边界

本清单不要求把 POSIX signal/process-group 行为移植到 Windows；那是不同操作系统能力。
它要求测试诚实地区分“业务跨平台契约”和“POSIX 专属契约”，并确保所有跨平台测试在 Windows
真实执行、真实全绿。临时设置 UTF-8 环境变量、全局 monkeypatch subprocess、或把整个失败目录
skip 都不算完成。
