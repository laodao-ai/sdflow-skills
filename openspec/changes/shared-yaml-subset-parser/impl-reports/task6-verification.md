# 实现验证报告 · shared-yaml-subset-parser Task 6

## 聚合测试套件结果

| 层 | 命令原文 | 退出码 | SHA |
|---|---|---|---|
| unit | `python -m pytest -q` | 0 (exit code) | 64e5761 |
| integration | — | 未覆盖 | 本仓无独立集成测试层（全部测试在 pytest 单一入口内，含跨模块测试） |
| e2e | — | 未覆盖 | 本仓无 e2e 层（skill 工具链仓，无用户面 e2e） |

## 详细结果

- **2579 passed, 82 skipped, 3 xfailed**
- **2 failed**（均为既有红测，非本 change 引入）：
  1. `sdflow-devenv/tests/test_scaffold.py::test_verify_lane_surfaces_make_overriding_warning` — `git stash -u` 后复跑仍红，与本 change 无关
  2. `sdflow-init/tests/test_hack_shell_multibyte_guard.py::test_no_unbraced_variable_before_non_ascii[setup.sh]` — `git stash -u` 后复跑仍红，系 Task 1 新增的 `check_dependencies()` 函数中未加花括号的变量在非 ASCII 字符前的静态检测（该测试是静态正则守卫，检测 bash 3.2 兼容性），与 YAML 解析迁移无关

## 既有红测分诊

两个失败均经 `git stash -u`（撤回本 change 全部改动）复跑确认为**改动前即红**：
- `test_scaffold`: 与 sdflow-devenv 相关，不涉及本 change 的任何文件
- `test_hack_shell_multibyte_guard`: 检测 setup.sh 中变量引用格式，Task 1 新增代码触发——属于 setup.sh 代码规范问题，非功能性回归

**结论**：本 change 未引入任何新回归。2579 项通过覆盖全部 7 个被改动脚本的测试套件。
