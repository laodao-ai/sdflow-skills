### Task 3: ship_gate B25/B26 机械门

**Blocked-by:** none
**R-ID:** IO-1

在 ship_gate 既有 code-review 报告消费点新增两道机械门：① 锚存在门——`metrics.enabled=true` 时 code-review 报告 MUST 含 `sdflow:lens-metric layer="code-review"` 锚行与 `sdflow:ref-check` 结构化锚；缺任一 ⇒ STEP_IN_PROGRESS + 修复指引；config 缺省/false/文件不存在 = 放行，yq 非零 = fail-closed。② defer 对账门——台账行（表格数据行，id 取专用 id 列，单元格全内容=单 id）携 `T\d+|B\d+` id 且对应池文件文件系统存在且 `source_change` = 当前 change；不满足 ⇒ STEP_IN_PROGRESS。fence-aware 口径复用既有解析。spec-review 报告在 design 门加同款锚存在检查（含转换态指引）。

- [ ] 锚存在门：metrics 开启 + 报告缺锚 ⇒ 被拦（STEP_IN_PROGRESS + 修复指引）
- [ ] 锚存在门：metrics 缺省/false/config 文件不存在 ⇒ 放行
- [ ] 锚存在门：config 不可解析 ⇒ fail-closed 报 problem+cause+fix
- [ ] defer 对账门：台账行无 id / 池文件缺失 / source_change 属另一 change ⇒ 被拦
- [ ] defer 对账门：fence 内锚样例不触发判定（负例）
- [ ] defer 对账门：台账窄化——描述列旧票号不误抓 + 聚合摘要句不假阳（负例）
- [ ] spec-review 报告 design 门同款锚存在检查 + 转换态指引
- [ ] 测试矩阵：双向 config 态 × 缺锚/缺 ref-check/defer 无 id/池文件缺失/change 不符/窄化负例/fence 负例

