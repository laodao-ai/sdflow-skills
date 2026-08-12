### Task 1: anchor_lint 拍板三问机验实现

**Blocked-by:** none
**R-ID:** GQ

在 `sdflow-init/assets/workflow/tools/anchor_lint.py` 实现 `sdflow:gate-questions` 锚的机验检查：

- `ANCHOR_PREFIXES` 字典登记 `"<!-- sdflow:gate-questions v1"` 前缀
- 新增 `check_gate_questions(report_text, layer, findings)` 函数：
  - MUST 接收 `layer` 参数，在函数体内按 layer 早返回（沿 `check_declared_sites` 的 layer-conditional 模式）
  - `layer=spec-review` 时 always-on 检查（不受 `metrics.enabled` 门控）
  - `layer=code-review` 时直接返回，不检查
  - 校验规则：fence 外存在性恒须、`q` 值逐字等于 `scope,deps,risk`（有序无增减）、缺 `q=` 属性同判违规、fence 外 ≥2 条判重复违规（fail-closed，沿 `duplicate-fanout-anchor` 先例）
  - MUST NOT 复用/扩展 `check_existence`/`MANDATORY` 列表（其 layer 参数是死参从不分流）

在 `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 新增七组契约测试：正例 / 缺锚负例 / q 值变异负例（缺项·增项·乱序·缺 `q=` 属性）/ 重复锚负例 / fence 内示范锚不算 / code-review layer 不查。

用 p4 归档报告**副本**做回放核验：原样 lint FAIL（缺新锚）→ 手工加段后 PASS（不改归档文件原件）。

- [ ] `ANCHOR_PREFIXES` 登记 + `check_gate_questions` 函数实现（layer 分治、q 值校验、重复锚 fail-closed、fence-aware）
- [ ] 七组契约测试全部通过（正例 / 缺锚 / q 变异四子项 / 重复锚 / fence 内 / code-review 不查）
- [ ] p4 归档报告副本回放：原样 FAIL → 加段后 PASS
- [ ] 既有 anchor_lint 测试无回归

