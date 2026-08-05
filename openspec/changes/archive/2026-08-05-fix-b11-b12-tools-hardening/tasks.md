## 1. T174 fake-timeout 测试桩整数截断（D1）

- [x] 1.1 `sdflow-init/tests/test_outside_voice.py`：fake-timeout 桩在 `sec="$1"` 后加 `sec="${sec%%.*}"` 截断小数
- [x] 1.2 `sdflow-init/tests/test_outside_voice_child_lifecycle.py`：该文件的 fake-timeout 用 `shift 3; exec` 形式，无算术运算，不受 T174 影响——无需改动
- [x] 1.3 跑 `pytest sdflow-init/tests/test_outside_voice.py sdflow-init/tests/test_outside_voice_child_lifecycle.py` 验证绿（92 passed, 3 skipped）
- [x] 1.4 标 T174 DONE

## 2. T139 outside_voice_guard parse_mode 双锚校验（D2）

- [x] 2.1 `sdflow-init/assets/workflow/tools/outside_voice_guard.py`（权威源）+ 同步 `openspec/workflow/tools/`：parse_mode 从 `.search()` 改 `.findall()` + 数量校验
- [x] 2.2 补测试：`test_duplicate_step1_anchors_fail_closed` + `test_single_step1_anchor_returns_mode`
- [x] 2.3 跑 `pytest sdflow-init/assets/workflow/tools/tests/test_outside_voice_guard.py` 验证绿（44 passed）
- [x] 2.4 标 T139 DONE

## 3. T140 declared= 必填 WONTDO（D3）

- [x] 3.1 标 T140 WONTDO

## 4. T56 trivial_shape tests/plugins/ 排除（D4）

- [x] 4.1 `sdflow-init/assets/workflow/tools/trivial_shape.py`（权威源）+ 同步 `openspec/workflow/tools/`：排除条件追加 `"tests/plugins/" not in path`
- [x] 4.2 补测试：`test_new_tests_plugins_not_exempt` → NOT_EXEMPT
- [x] 4.3 跑 `pytest sdflow-init/assets/workflow/tools/tests/test_trivial_shape.py` 验证绿（35 passed）
- [x] 4.4 标 T56 DONE

## 5. T188 跨 skill 同 basename 测试守卫（D5）

- [x] 5.1 新建 `hack/tests/test_test_basename_uniqueness.py`：扫全仓（排除 `.claude/`）test_*.py basename，重复即 fail
- [x] 5.2 跑 `pytest hack/tests/test_test_basename_uniqueness.py` 验证绿（1 passed）
- [x] 5.3 标 T188 DONE

## 6. 收尾验证

- [x] 6.1 全仓 `pytest` 绿（2446 passed, 10 skipped；1 条预存 fail test_harden_sdflow_spec_followup_closure SA-14 锚断言不属本 change）
- [x] 6.2 更新 roadmap 批次状态（v10，85 条 open todo）
