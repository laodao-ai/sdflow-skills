# 全项目 change 成本×价值复盘（view-only 再生）

> 覆盖 28 change / 有真锚 12 / 边界不可解析 2
> 阶段墙钟为「阶段级 elapsed（含人读/拍板/生成时间）」口径（adr/0009），非纯 agent 耗时。

⚠️ 待复评: 以下镜出现轮数≥10、只提示不判断不自动砍——人读后自行决定保留/降采样/淘汰:
  - outside-voice（layer=code-review runner=codex site=code-voice，出现轮数 10）

## per-change 明细

| change | 总墙钟(min) | spec-rev Δ | impl Δ | code-rev Δ | done Δ | #ckpt | spec_hr_tg | code_hr_tg | Σfindings | 采纳率 | 独立Σ | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| adaptive-workflow-routing | 111.1 | 83.8 | 10.1 | 3.0 | 0.5 | 7 | none | none | 28 | 0.96 | 19 | archived |
| batch-triage-strategy | 107.4 | 41.9 | 50.0 | 10.8 | — | 8 | none | none | 29 | 0.9 | 11 | archived |
| checkpoint-tag-single-source | 753.8 | 678.1 | 68.7 | 7.0 | — | 6 | none | none | — | 无度量锚 | — | archived |
| cross-model-outside-voice | 229.7 | 71.6 | 76.0 | 24.6 | — | 12 | — | TG-08,TG-17 | — | 无度量锚 | — | archived |
| drop-per-dir-review-stub | 53.8 | — | 32.6 | — | — | 5 | — | none | — | 无度量锚 | — | archived |
| gate-anchor-line-scoped | 7.0 | — | — | 7.0 | — | 9 | none | none | — | 无度量锚 | — | archived |
| gate-checkpoint-hardening | 87.8 | 17.9 | 26.7 | 7.3 | — | 10 | none | none | — | 无度量锚 | — | archived |
| issues-pool-batch-mgmt | 0.0（边界不可解析） | — | — | — | — | 0 | — | — | — | 无度量锚 | — | archived |
| issues-pool-hardening | 206.3 | 40.5 | — | 8.8 | — | 10 | none | none | 28 | 0.86 | 9 | archived |
| minimize-repo-footprint | 136.5 | 21.4 | 103.9 | 11.2 | — | 10 | — | — | — | 无度量锚 | — | archived |
| mlh-p1-issues-sweep | 42.7 | 10.9 | 24.6 | 7.2 | — | 6 | none | none | 36 | 0.81 | 8 | archived |
| mlh-p2-anchor-lint | 90.2 | 5.4 | — | 7.2 | — | 6 | none | none | 38 | 0.82 | 18 | archived |
| mlh-p3-determ-guards | 166.8 | 91.4 | 64.5 | 10.9 | — | 5 | none | none | 37 | 0.86 | 10 | archived |
| mlh-p5-gate-frontmatter | 161.6 | 32.1 | 37.3 | 8.2 | — | 6 | TG-04,TG-08 | TG-04,TG-08 | 49 | 0.86 | 18 | archived |
| mlh-p5-parser-cleanup | 145.9 | 57.8 | 45.1 | 7.7 | — | 7 | none | none | 16 | 0.69 | 8 | archived |
| plan-mechanical-layer-hardening | 0.2 | — | — | — | — | 2 | — | — | — | 无度量锚 | — | archived |
| plan-workflow-cost-optimization | 23.8 | — | — | — | — | 3 | — | — | — | 无度量锚 | — | archived |
| review-tool-followups | 70.4 | 22.6 | 30.4 | 8.0 | — | 8 | none | none | — | 无度量锚 | — | archived |
| sdflow-init-hardening | 37.2 | — | 31.3 | — | — | 3 | — | TG-26 | 13 | 0.85 | 4 | archived |
| sdflow-rebrand | 253.0 | 14.6 | 191.5 | 29.6 | — | 14 | — | — | — | 无度量锚 | — | archived |
| sdflow-retro | 279.6 | 40.3 | 177.6 | 12.9 | — | 8 | none | none | 49 | 0.82 | 20 | archived |
| sdflow-retro-cleanup | 37.2 | — | 14.9 | — | — | 4 | — | none | 8 | 0.62 | 3 | archived |
| sdflow-ship | 290.8 | 24.9 | 86.2 | 8.4 | — | 10 | — | — | — | 无度量锚 | — | archived |
| ship-gate-hardening | 180.8 | 79.6 | — | 8.2 | — | 8 | TG-09 | TG-09 | — | 无度量锚 | — | archived |
| ship-gate-hardening-2 | 110.0 | 25.2 | 25.2 | 7.2 | — | 8 | none | none | — | 无度量锚 | — | archived |
| streamline-workflow-automation | 0.0（边界不可解析） | — | — | — | — | 0 | — | — | — | 无度量锚 | — | archived |
| three-lens-decision-framework | 75.3 | 29.6 | 22.4 | 5.2 | — | 10 | none | none | — | 无度量锚 | — | archived |
| workflow-metrics-loop | 119.2 | 12.8 | 78.2 | 10.5 | — | 6 | none | none | 16 | 0.94 | 10 | archived |

## 聚合① 阶段占比

| 阶段 | 墙钟(min) | 占比 |
|---|---|---|
| spec-review | 1402.4 | 37% |
| impl | 1197.3 | 32% |
| ff | 285.6 | 8% |
| unknown | 269.4 | 7% |
| other | 216.5 | 6% |
| code-review | 211.0 | 6% |
| grill | 195.2 | 5% |
| done | 0.5 | 0% |

## 聚合② 成本双峰（总墙钟 x / code-review 占比% y）

| change | 总墙钟(min) | code-review 占比 |
|---|---|---|
| adaptive-workflow-routing | 111.1 | 3% |
| batch-triage-strategy | 107.4 | 10% |
| checkpoint-tag-single-source | 753.8 | 1% |
| cross-model-outside-voice | 229.7 | 11% |
| drop-per-dir-review-stub | 53.8 | 0% |
| gate-anchor-line-scoped | 7.0 | 100% |
| gate-checkpoint-hardening | 87.8 | 8% |
| issues-pool-batch-mgmt | 0.0 | — |
| issues-pool-hardening | 206.3 | 4% |
| minimize-repo-footprint | 136.5 | 8% |
| mlh-p1-issues-sweep | 42.7 | 17% |
| mlh-p2-anchor-lint | 90.2 | 8% |
| mlh-p3-determ-guards | 166.8 | 7% |
| mlh-p5-gate-frontmatter | 161.6 | 5% |
| mlh-p5-parser-cleanup | 145.9 | 5% |
| plan-mechanical-layer-hardening | 0.2 | 0% |
| plan-workflow-cost-optimization | 23.8 | 0% |
| review-tool-followups | 70.4 | 11% |
| sdflow-init-hardening | 37.2 | 0% |
| sdflow-rebrand | 253.0 | 12% |
| sdflow-retro | 279.6 | 5% |
| sdflow-retro-cleanup | 37.2 | 0% |
| sdflow-ship | 290.8 | 3% |
| ship-gate-hardening | 180.8 | 5% |
| ship-gate-hardening-2 | 110.0 | 7% |
| streamline-workflow-automation | 0.0 | — |
| three-lens-decision-framework | 75.3 | 7% |
| workflow-metrics-loop | 119.2 | 9% |

## 聚合③ per-镜价值表（lens-metric 聚合，扫 archive）

| layer | lens | runner | site | 出现轮数 | Σfindings | Σ采纳 | Σ裁掉 | Σdefer | Σ独立 | 采纳率 | 独立率 | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| code-review | adversarial | claude | guard-bypass | 1 | 2 | 2 | 0 | 0 | 1 | 100% | 50% | — |
| code-review | adversarial | claude | none | 1 | 5 | 3 | 1 | 1 | 1 | 60% | 20% | — |
| code-review | adversarial | claude | parse-edge+blast-radius | 1 | 1 | 0 | 0 | 1 | 0 | 0% | 0% | — |
| code-review | adversarial | claude | refactor-honesty | 1 | 3 | 1 | 0 | 2 | 0 | 33% | 0% | — |
| code-review | adversarial | claude | — | 9 | 54 | 41 | 5 | 8 | 27 | 76% | 50% | — |
| code-review | broad | claude | native | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | broad | claude | none | 1 | 1 | 1 | 0 | 0 | 1 | 100% | 100% | — |
| code-review | broad | claude | step1 | 2 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | broad | claude | — | 5 | 6 | 6 | 0 | 0 | 3 | 100% | 50% | — |
| code-review | broad | native | scope-drift | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | domain | claude | backend | 1 | 4 | 3 | 0 | 1 | 2 | 75% | 50% | — |
| code-review | domain | claude | checklist | 1 | 2 | 0 | 1 | 1 | 0 | 0% | 0% | — |
| code-review | domain | claude | none | 1 | 3 | 3 | 0 | 0 | 2 | 100% | 67% | — |
| code-review | domain | claude | — | 8 | 26 | 19 | 4 | 3 | 9 | 73% | 35% | — |
| code-review | history | claude | blame | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | history | claude | git-blame | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | history | claude | none | 1 | 2 | 1 | 1 | 0 | 0 | 50% | 0% | — |
| code-review | history | claude | — | 8 | 4 | 2 | 2 | 0 | 0 | 50% | 0% | — |
| code-review | outside-voice | claude-fallback | code-voice | 1 | 4 | 2 | 1 | 1 | 1 | 50% | 25% | — |
| code-review | outside-voice | codex | code-voice | 10 | 32 | 27 | 2 | 3 | 12 | 84% | 38% | ≥10待复评 |
| code-review | outside-voice | codex | hr-tg | 2 | 3 | 3 | 0 | 0 | 2 | 100% | 67% | — |
| spec-review | adversarial | claude | - | 1 | 8 | 8 | 0 | 0 | 4 | 100% | 50% | — |
| spec-review | adversarial | claude | d1-t2 | 1 | 5 | 4 | 1 | 0 | 2 | 80% | 40% | — |
| spec-review | adversarial | claude | d2-d3-scope | 1 | 4 | 4 | 0 | 0 | 2 | 100% | 50% | — |
| spec-review | adversarial | claude | none | 2 | 30 | 28 | 2 | 0 | 9 | 93% | 30% | — |
| spec-review | adversarial | claude | — | 5 | 41 | 35 | 4 | 2 | 22 | 85% | 54% | — |
| spec-review | broad | claude | - | 1 | 3 | 3 | 0 | 0 | 1 | 100% | 33% | — |
| spec-review | broad | claude | autoplan-adapted | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | broad | claude | none | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | broad | claude | — | 5 | 13 | 13 | 0 | 0 | 6 | 100% | 46% | — |
| spec-review | broad | grill-substituted | design | 1 | 3 | 3 | 0 | 0 | 0 | 100% | 0% | — |
| spec-review | domain | claude | backend | 1 | 5 | 5 | 0 | 0 | 1 | 100% | 20% | — |
| spec-review | domain | claude | none | 2 | 12 | 12 | 0 | 0 | 3 | 100% | 25% | — |
| spec-review | domain | claude | — | 3 | 16 | 16 | 0 | 0 | 12 | 100% | 75% | — |
| spec-review | grounding | claude | - | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | grounding | claude | code-facts | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | grounding | claude | none | 2 | 3 | 3 | 0 | 0 | 0 | 100% | 0% | — |
| spec-review | grounding | claude | — | 5 | 18 | 14 | 3 | 0 | 7 | 82% | 39% | — |
| spec-review | outside-voice | claude-fallback | design-voice | 1 | 3 | 3 | 0 | 0 | 0 | 100% | 0% | — |
| spec-review | outside-voice | codex | design-voice | 7 | 28 | 25 | 2 | 1 | 7 | 89% | 25% | — |
| spec-review | outside-voice | codex | hr-tg | 1 | 3 | 3 | 0 | 0 | 1 | 100% | 33% | — |

> 无锚样本 28 份（旧格式,不纳入；份=报告文件数，每 change 常含 spec/code 两份，非 change 数；去重后 15 个 change）: 2026-07-02-issues-pool-batch-mgmt, 2026-07-02-issues-pool-batch-mgmt, 2026-07-02-streamline-workflow-automation, 2026-07-03-minimize-repo-footprint, 2026-07-03-minimize-repo-footprint, 2026-07-03-sdflow-rebrand, 2026-07-03-sdflow-rebrand, 2026-07-03-sdflow-ship, 2026-07-03-sdflow-ship, 2026-07-04-cross-model-outside-voice, 2026-07-04-cross-model-outside-voice, 2026-07-04-ship-gate-hardening, 2026-07-04-ship-gate-hardening, 2026-07-04-ship-gate-hardening-2, 2026-07-04-ship-gate-hardening-2, 2026-07-05-checkpoint-tag-single-source, 2026-07-05-checkpoint-tag-single-source, 2026-07-05-drop-per-dir-review-stub, 2026-07-05-drop-per-dir-review-stub, 2026-07-05-gate-anchor-line-scoped, 2026-07-05-gate-anchor-line-scoped, 2026-07-05-gate-checkpoint-hardening, 2026-07-05-gate-checkpoint-hardening, 2026-07-05-review-tool-followups, 2026-07-05-review-tool-followups, 2026-07-05-three-lens-decision-framework, 2026-07-05-three-lens-decision-framework, 2026-07-05-workflow-metrics-loop
> 解析失败 0 份（编码/IO 错误，已跳过未计入聚合，不拖垮全局）: 无
> 独立率跨轮不保证同口径（dedup 合并尺度可能漂移），复评时校验最近几轮尺度一致。

