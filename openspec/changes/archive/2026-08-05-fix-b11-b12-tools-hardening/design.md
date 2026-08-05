## Context

issues-triage B11+B12 合批的 5 条待修 issue，均为工具层零碎加固（见 proposal.md）。
改动分散在 4 个文件 + 1 个新测试文件，彼此无耦合。

## Goals / Non-Goals

**Goals:**
- 逐条修复 T174/T139/T140/T56/T188，每条有明确 evidence 锚
- 全仓 pytest 绿

**Non-Goals:**
- 不重构 outside_voice_guard / anchor_lint 的整体架构
- 不改 outside-voice.sh 生产代码

## Decisions

### D1 · T174 fake-timeout 非整数 sec（测试桩）

**决定**：在 fake-timeout 桩脚本的 `lim=$(( sec * 10 ))` 前加 `sec="${sec%%.*}"`（截断小数部分取整）。

**理由**：生产 `--timeout` 只接受纯数字（`outside-voice.sh:913` 的 `*[!0-9]* → usage`），非整数进不来。
问题只在测试桩的 fake-timeout 里——有人直接传浮点 sec 时 bash 算术会炸。截断即可，比引入 bc 依赖简单。
改动在 `test_outside_voice.py` 和 `test_outside_voice_child_lifecycle.py` 两处 fake-timeout 桩。

**备选**：用 `printf '%.0f'` + bc 管道——引入外部依赖，测试桩不值得。

### D2 · T139 outside_voice_guard parse_mode 双锚（加固）

**决定**：`parse_mode` 从 `.search()` 改成 `_S1_RE.findall(_fence_outside_text(text))`，取所有 fence 外匹配。
数量 ≠ 1 → `EmitError`（多锚/缺锚均 fail-closed）。
数量 = 1 → 照旧取 mode 属性。

**理由**：issue 自述「构造性/低概率」，但 fail-closed 代价极低（几行改动），且与 `check_hr_tg` 的「多锚 violation」设计一致。

### D3 · T140 anchor_lint declared= 必填兼容性（WONTDO）

**决定**：标 **WONTDO**，不加 grace。

**理由**：
1. `anchor_lint` 只被 `sdflow-code-review` 和 `sdflow-spec-review` 在**当轮新产出的报告**上调用（`SKILL.md:351-352`），不重 lint 归档旧报告。
2. 所有新报告（v2 锚）都已有 declared=。旧格式锚只存在于已归档 change 的历史报告中，不会被重新 lint。
3. 消费仓若存在旧报告也不走 anchor_lint 路径——anchor_lint 由评审 SKILL 在生成报告后调用，不是通用 CI 门。
4. 加 grace（缺失降级 warning）会弱化 declared= 的必填语义，反而削弱 M1 字段校验的拦截力。

### D4 · T56 trivial_shape tests/ 排除扩展

**决定**：在 `in_tests` 的排除集中增加对 `tests/plugins/` 下文件的排除——`tests/plugins/` 下的 `.py` 文件视同 `conftest.py`（有 import 副作用），不判 trivial。

**修法**：在 `base not in ("conftest.py", "__init__.py")` 之外，追加 `and "tests/plugins/" not in path` 条件。

**理由**：pytest 插件注册在 `tests/plugins/` 里（`conftest.py` 的 `pytest_plugins` 列表引用），有 import 副作用、改动影响测试行为，不该免审。当前仓内无 `tests/plugins/` 目录，属预防性加固。

### D5 · T188 跨 skill 同 basename 测试守卫

**决定**：新建仓根守卫测试 `hack/tests/test_test_basename_uniqueness.py`，扫全仓（排除 `.claude/`）的 `test_*.py` basename，重复即 fail。

**理由**：issue 推荐方案②（唯一性守卫而非加 `__init__.py`）——成本低、fail-loud、不改包语义。
放 `hack/tests/` 与其他仓基础设施守卫同级（`test_install_agents.py` 等）。

## Risks / Trade-offs

- **D1 截断精度**：`sec="3.5"` 截断为 `sec="3"` → 看门狗提前 0.5s 触发。对测试桩来说提前 kill 比算术错好。
- **D3 WONTDO 残留**：若未来 anchor_lint 被用作 CI 通用门，旧报告会硬失败。当前架构下不会发生。
- **D5 守卫误判**：若不同 skill 的 tests/ 下恰好有同名但内容完全不同的测试文件，重命名是正确做法。

## Compliance

- 基准 1（机械化优先）：D5 用机械守卫拦同名冲突，不依赖「记得别取同名」。
- 基准 4（简化）：D3 选 WONTDO 而非加迁移 grace，因为旧报告实际不走重 lint 路径。
- 通则④（最简方案）：每条改动都是几行级别。
