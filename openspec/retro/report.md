# 全项目 change 成本×价值复盘（view-only 再生）

> 覆盖 18 change / 有真锚 3 / 边界不可解析 2
> 阶段墙钟为「阶段级 elapsed（含人读/拍板/生成时间）」口径（adr/0009），非纯 agent 耗时。

⚠️ 待复评: 无（所有镜出现轮数<10）

## per-change 明细

| change | 总墙钟(min) | spec-rev Δ | impl Δ | code-rev Δ | done Δ | #ckpt | spec_hr_tg | code_hr_tg | Σfindings | 采纳率 | 独立Σ | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| adaptive-workflow-routing | 111.1 | 83.8 | 10.1 | 3.0 | 0.5 | 7 | none | none | 28 | 0.96 | 19 | archived |
| checkpoint-tag-single-source | 753.8 | 678.1 | 68.7 | 7.0 | — | 6 | none | none | — | 无度量锚 | — | archived |
| cross-model-outside-voice | 229.7 | 71.6 | 76.0 | 24.6 | — | 12 | — | TG-08,TG-17 | — | 无度量锚 | — | archived |
| drop-per-dir-review-stub | 53.8 | — | 32.6 | — | — | 5 | — | none | — | 无度量锚 | — | archived |
| gate-anchor-line-scoped | 7.0 | — | — | 7.0 | — | 9 | none | none | — | 无度量锚 | — | archived |
| gate-checkpoint-hardening | 87.8 | 17.9 | 26.7 | 7.3 | — | 10 | none | none | — | 无度量锚 | — | archived |
| issues-pool-batch-mgmt | 0.0（边界不可解析） | — | — | — | — | 0 | — | — | — | 无度量锚 | — | archived |
| minimize-repo-footprint | 136.5 | 21.4 | 103.9 | 11.2 | — | 10 | — | — | — | 无度量锚 | — | archived |
| plan-workflow-cost-optimization | 23.8 | — | — | — | — | 3 | — | — | — | 无度量锚 | — | archived |
| review-tool-followups | 70.4 | 22.6 | 30.4 | 8.0 | — | 8 | none | none | — | 无度量锚 | — | archived |
| sdflow-rebrand | 253.0 | 14.6 | 191.5 | 29.6 | — | 14 | — | — | — | 无度量锚 | — | archived |
| sdflow-retro | 89.1 | 40.3 | — | — | — | 6 | none | — | 32 | 0.88 | 15 | in-progress |
| sdflow-ship | 290.8 | 24.9 | 86.2 | 8.4 | — | 10 | — | — | — | 无度量锚 | — | archived |
| ship-gate-hardening | 180.8 | 79.6 | — | 8.2 | — | 8 | TG-09 | TG-09 | — | 无度量锚 | — | archived |
| ship-gate-hardening-2 | 110.0 | 25.2 | 25.2 | 7.2 | — | 8 | none | none | — | 无度量锚 | — | archived |
| streamline-workflow-automation | 0.0（边界不可解析） | — | — | — | — | 0 | — | — | — | 无度量锚 | — | archived |
| three-lens-decision-framework | 75.3 | 29.6 | 22.4 | 5.2 | — | 10 | none | none | — | 无度量锚 | — | archived |
| workflow-metrics-loop | 119.2 | 12.8 | 78.2 | 10.5 | — | 6 | none | none | 16 | 0.94 | 10 | archived |

## 聚合① 阶段占比

| 阶段 | 墙钟(min) | 占比 |
|---|---|---|
| spec-review | 1122.4 | 43% |
| impl | 751.8 | 29% |
| ff | 285.6 | 11% |
| grill | 155.2 | 6% |
| code-review | 137.4 | 5% |
| other | 99.7 | 4% |
| unknown | 39.3 | 2% |
| done | 0.5 | 0% |

## 聚合② 成本双峰（总墙钟 x / code-review 占比% y）

| change | 总墙钟(min) | code-review 占比 |
|---|---|---|
| adaptive-workflow-routing | 111.1 | 3% |
| checkpoint-tag-single-source | 753.8 | 1% |
| cross-model-outside-voice | 229.7 | 11% |
| drop-per-dir-review-stub | 53.8 | 0% |
| gate-anchor-line-scoped | 7.0 | 100% |
| gate-checkpoint-hardening | 87.8 | 8% |
| issues-pool-batch-mgmt | 0.0 | — |
| minimize-repo-footprint | 136.5 | 8% |
| plan-workflow-cost-optimization | 23.8 | 0% |
| review-tool-followups | 70.4 | 11% |
| sdflow-rebrand | 253.0 | 12% |
| sdflow-retro | 89.1 | 0% |
| sdflow-ship | 290.8 | 3% |
| ship-gate-hardening | 180.8 | 5% |
| ship-gate-hardening-2 | 110.0 | 7% |
| streamline-workflow-automation | 0.0 | — |
| three-lens-decision-framework | 75.3 | 7% |
| workflow-metrics-loop | 119.2 | 9% |

## 聚合③ per-镜价值表（lens-metric 聚合，扫 archive）

| layer | lens | runner | site | 出现轮数 | Σfindings | Σ采纳 | Σ裁掉 | Σdefer | Σ独立 | 采纳率 | 独立率 | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| code-review | adversarial | claude | — | 2 | 13 | 12 | 1 | 0 | 11 | 92% | 85% | — |
| code-review | domain | claude | — | 1 | 6 | 6 | 0 | 0 | 4 | 100% | 67% | — |
| code-review | history | claude | — | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | outside-voice | codex | code-voice | 1 | 4 | 4 | 0 | 0 | 2 | 100% | 50% | — |
| spec-review | adversarial | claude | — | 1 | 12 | 11 | 0 | 1 | 7 | 92% | 58% | — |
| spec-review | broad | claude | — | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | grounding | claude | — | 1 | 4 | 4 | 0 | 0 | 3 | 100% | 75% | — |
| spec-review | outside-voice | codex | design-voice | 1 | 5 | 5 | 0 | 0 | 2 | 100% | 40% | — |

> 无锚样本 28 份（旧格式,不纳入；份=报告文件数，每 change 常含 spec/code 两份，非 change 数；去重后 15 个 change）: 2026-07-02-issues-pool-batch-mgmt, 2026-07-02-issues-pool-batch-mgmt, 2026-07-02-streamline-workflow-automation, 2026-07-03-minimize-repo-footprint, 2026-07-03-minimize-repo-footprint, 2026-07-03-sdflow-rebrand, 2026-07-03-sdflow-rebrand, 2026-07-03-sdflow-ship, 2026-07-03-sdflow-ship, 2026-07-04-cross-model-outside-voice, 2026-07-04-cross-model-outside-voice, 2026-07-04-ship-gate-hardening, 2026-07-04-ship-gate-hardening, 2026-07-04-ship-gate-hardening-2, 2026-07-04-ship-gate-hardening-2, 2026-07-05-checkpoint-tag-single-source, 2026-07-05-checkpoint-tag-single-source, 2026-07-05-drop-per-dir-review-stub, 2026-07-05-drop-per-dir-review-stub, 2026-07-05-gate-anchor-line-scoped, 2026-07-05-gate-anchor-line-scoped, 2026-07-05-gate-checkpoint-hardening, 2026-07-05-gate-checkpoint-hardening, 2026-07-05-review-tool-followups, 2026-07-05-review-tool-followups, 2026-07-05-three-lens-decision-framework, 2026-07-05-three-lens-decision-framework, 2026-07-05-workflow-metrics-loop
> 解析失败 0 份（编码/IO 错误，已跳过未计入聚合，不拖垮全局）: 无
> 独立率跨轮不保证同口径（dedup 合并尺度可能漂移），复评时校验最近几轮尺度一致。

