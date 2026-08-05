## Why

issues-triage roadmap B11+B12 合批中仍有 5 条低-中影响的工具脚本加固待修（T174/T139/T140/T56/T188）。
三条已在后续 change 中实质修复的（T176/T230/T68）已标 DONE 关闭。
本次统一处理剩余 5 条，消除工具层的潜在假阴/兼容性/基础设施面。

## What Changes

- **T174**（fake-timeout 测试桩）：看门狗 `$(( sec * 10 ))` 遇非整数 sec 抛算术错。生产已拦（`--timeout` 只接受纯数字），但测试桩的 fake-timeout 脚本无此防护。修法：截断为整数或改用兼容算术。
- **T139**（outside_voice_guard 双锚）：`parse_mode` 用 `.search()` 取首个 step1-broad-review 锚，native/simulated 双锚静默取前者。修法：`.findall()` + 数量校验，多锚 mode 冲突 fail-closed。
- **T140**（anchor_lint declared= 必填）：`check_hr_tg` 把 declared 列为 hr-tg 锚必填字段，旧格式锚（有 hit=/evidence= 无 declared=）重 lint 会 exit1。修法：确认旧报告实际不走重 lint 路径后标 WONTDO，或给 declared 加迁移 grace。
- **T56**（trivial_shape tests/ 排除）：tests/ 免多镜排除只覆盖 `conftest.py`/`__init__.py`，未覆盖 `tests/plugins/*` 等有 import 副作用的文件。修法：扩展排除集。
- **T188**（跨 skill 同 basename 测试文件）：不同 skill 下同名 `test_*.py` 会中断仓根 pytest 全局收集（import 冲突）。修法：加一条仓根机械守卫测试，扫 basename 唯一性。

## Capabilities

### New Capabilities

（无——纯工具加固）

### Modified Capabilities

（无——不涉及 spec 级行为变更）

## Impact

- `sdflow-init/tests/test_outside_voice.py`：fake-timeout 桩脚本
- `openspec/workflow/tools/outside_voice_guard.py`：parse_mode
- `openspec/workflow/tools/anchor_lint.py`：check_hr_tg declared= 校验
- `openspec/workflow/tools/trivial_shape.py`：tests/ 排除判据
- 新建仓根守卫测试文件

## Success Metrics

- 全仓 pytest 绿
- 5 条 issue 全部 DONE 或 WONTDO（有 evidence）

## Non-Goals

- 不改 outside-voice.sh 生产代码（T176/T230 已修）
- 不做 anchor_lint 的大规模重构
- 不做 pytest 收集机制的架构改动（如加 `__init__.py`）

## Compliance

N/A
