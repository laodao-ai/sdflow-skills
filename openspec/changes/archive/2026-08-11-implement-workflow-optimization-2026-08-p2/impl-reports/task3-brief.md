### Task 3: 裁决协议重写 + 联动核查

**Blocked-by:** 1,2
**R-ID:** R-裁决, R-voice, R-全跑

重写两评审 SKILL 的 Step3 裁决段为「机械前置 + 二元裁决 + 置信降排序」，联动核查全仓消费点。

**A. sdflow-code-review Step3 重写**：
- 删除：<80 数值滤、置信封顶 ≤50、跨模型豁免矩阵条款
- 新增：接入 validator 机械前置（三态处理）+ 二元裁决（采纳/裁掉/defer + critique）+ 置信仅排序
- 「已裁掉」区新增 `[ref-check]` 来源标记
- frontmatter description Step3 括注改「机械引用核+二元裁决」（显式删「(<80 滤除)」）
- Step2 各镜 prompt 输出契约改为强制结构化字段（`{file, line, quote}` / `evidence_pack`）
- 合并池 > 100 条时分批裁决（每批 ≤50，批间携带已裁清单防重复采纳）

**B. sdflow-spec-review Step3 对齐**：
- 裁决动作层对齐同 A 的三层协议
- 保留「拿不准 → 决策登记区」路由并与置信数字脱钩
- Step2 输出契约同步改结构化字段

**C. spec-workflow 主 spec 联动核查**：
- grep 全仓「置信过滤 / <80 / 豁免」消费点，逐处改齐或确认不动

- [ ] sdflow-code-review Step3 不含 <80 数值滤/封顶 ≤50/跨模型豁免矩阵
- [ ] sdflow-code-review Step3 含 validator 接入 + 二元裁决 + [ref-check] 标记
- [ ] sdflow-code-review frontmatter description Step3 括注已更新
- [ ] sdflow-code-review Step2 各镜 prompt 要求结构化 findings 输出
- [ ] sdflow-spec-review Step3 裁决动作层与 code-review 三层协议对齐
- [ ] sdflow-spec-review 保留「拿不准→决策登记区」路由
- [ ] 全仓 grep「置信过滤/<80/豁免」无遗漏残余消费点

