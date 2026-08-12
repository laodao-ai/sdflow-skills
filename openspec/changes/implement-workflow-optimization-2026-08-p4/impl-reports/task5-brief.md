### Task 5: 四编排 SKILL 全面适配 + B25 诊断修复 + bundle 同步

**Blocked-by:** 1,2,3,4
**R-ID:** SW-1, SW-2, SW-3, IO-2, HAE-1

B25 诊断定案：在归档报告数据上重放 `lens_metric_emit.py` 调用，判定「未调用 vs 调用失败未记录」，结论记入 impl-report。按结论修复 emitter 落盘直接成因。

四个编排 SKILL（sdflow-spec-review / sdflow-code-review / sdflow-implement / sdflow-done）全面适配：
(a) 派发条款接 effort——表格加 effort 档列，派发时构造 `subagent_type: sdflow-effort-$SDFLOW_EFFORT_<档位>`，空值回落不带 subagent_type；门禁步不低于 high。tier-resolution 托管块 unset 清脏清单扩含 `SDFLOW_EFFORT_*` 三变量。
(b) 两评审 SKILL 镜派发改三段组装序——段① = `render-review-prefix.sh` 输出原文一句引用；段②③ 界线显式化；SKILL 内与段①重复的散文契约收敛为引用。
(c) sdflow-code-review Step4 defer 改「当场 recorder add（显式 source_change）+ 返回 id 写台账」；台账改机读结构（表格行 + 专用 id 列）+ 聚合摘要句改写移出 gate 检测范围；Step3 引用核结果落 `sdflow:ref-check` 结构化锚；Step5 义务措辞与门对齐；recorder 失败 fail-loud。
(d) sdflow-done 三步子代理接 effort 档。

bundle 同步：config.template `effort-tiers` 段示例 + claude-section 说明 + `init.py lint_config` 扩 `effort-tiers` 结构/值域校验（与 resolver 同口径）+ scope-check 表全组复查。

- [ ] B25 诊断结论记入 impl-report（未调用 vs 调用失败，有确定性证据）
- [ ] B25 直接成因修复（SKILL/脚本改动，按诊断结论定）
- [ ] 四编排 SKILL 派发条款接 effort（subagent_type 构造 + 空值回落 + 门禁步 ≥ high + unset 扩面）
- [ ] 两评审 SKILL 镜派发改三段组装序（段① 脚本引用 + 段②③ 显式化 + 重复散文收敛）
- [ ] sdflow-code-review defer 当场入池（recorder add + id 台账 + ref-check 锚 + 聚合摘要改写）
- [ ] sdflow-done 三步子代理接 effort 档
- [ ] bundle 同步：config.template effort-tiers 段 + claude-section + init.py lint_config 扩面 + scope-check
- [ ] [e2e] 本 change 自身 code-review 报告含 lens-metric 锚 + ref-check 锚 + defer id 对账（dogfood 首证）

