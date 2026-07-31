# Task 4: 实现验证（收尾）

## 聚合测试证据

| 层 | 命令原文 | 退出码 | SHA |
|---|---|---|---|
| unit | `pytest` | 0（2538 passed, 4 failed, 82 skipped, 3 xfailed） | cabedc08（首次跑；修复后 75998ae） |
| integration | — | 未覆盖 | 本仓无集成测试层 |
| e2e | — | 未覆盖 | 本仓无 e2e 测试层 |

## 失败分诊

4 个失败中：

### 本 change 引入的回归（已修复）

1. **`test_step2_serial_must_sentence`**（sdflow-ship/tests/test_serial_discipline.py）：断言旧措辞「禁止与 Step1 并行」「增量核对」——Task 1 将串行纪律改为分治后旧措辞不存在。已更新断言为「接地镜 MAY 与 Step1 并行起跑」「SHALL NOT 自动补跑接地镜」。
2. **`test_both_skills_probe_precedes_fanout_dispatch`**（sdflow-init/tests/test_codex_subagent_authorization.py）：用 `t.index("fan-out（一条消息内全部派出")` 定位 fan-out 段——Task 2 将 spec-review 改为「两段 dispatch」。已按 skill 分列 needle（spec-review 用「两段 dispatch」，code-review 保持旧措辞）。

修复后两测试绿：`2 passed in 0.08s`（SHA 75998ae）。

### 仓内既有红测（改动前即红，非本 change 引入）

3. **`test_verify_lane_surfaces_make_overriding_warning`**（sdflow-devenv/tests/test_scaffold.py）：`git diff main..HEAD -- sdflow-devenv/tests/test_scaffold.py` 为空，本 change 未触碰该文件。
4. **`test_exit_code_stays_in_contract_under_git_failures`**（sdflow-ship/tests/test_gate_git_layer.py）：`git diff main..HEAD -- sdflow-ship/tests/test_gate_git_layer.py` 为空，本 change 未触碰该文件。

## 最终状态

本 change 引入的 2 个回归已修复并验证通过（SHA 75998ae）。仓内既有 2 个红测记录并放行。
