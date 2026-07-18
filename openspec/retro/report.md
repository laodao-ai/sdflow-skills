# 全项目 change 成本×价值复盘（view-only 再生）

> 覆盖 40 change / 有真锚 22 / 边界不可解析 4
> 阶段墙钟为「阶段级 elapsed（含人读/拍板/生成时间）」口径（adr/0009），非纯 agent 耗时。

⚠️ 待复评: 以下镜出现轮数≥10、只提示不判断不自动砍——人读后自行决定保留/降采样/淘汰:
  - adversarial（layer=code-review host=claude runner=claude site=—，出现轮数 18）
  - broad（layer=code-review host=claude runner=claude site=—，出现轮数 14）
  - domain（layer=code-review host=claude runner=claude site=—，出现轮数 17）
  - history（layer=code-review host=claude runner=claude site=—，出现轮数 17）
  - outside-voice（layer=code-review host=claude runner=codex site=code-voice，出现轮数 19）
  - adversarial（layer=spec-review host=claude runner=claude site=—，出现轮数 14）
  - broad（layer=spec-review host=claude runner=claude site=—，出现轮数 14）
  - grounding（layer=spec-review host=claude runner=claude site=—，出现轮数 14）
  - outside-voice（layer=spec-review host=claude runner=codex site=design-voice，出现轮数 13）

## 一览

| 复盘 change | 总墙钟 | 有真锚 | 待复评镜 |
|---|---|---|---|
| 40 | ~331.1 hr | 22 | 9 |

本轮复盘覆盖 **40 个 change**，累计评审墙钟约 **331.1 hr**（其中 22 个带真实度量锚、可参与价值统计）。评审时间集中在 未归类 56%、写实现 17%（两者合计 73%）。单个 change 耗时最重的是 scoped-test-per-task（约 165.5 hr）、最轻的是 plan-mechanical-layer-hardening（0.2 min）。价值侧，出问题最多的是 代码审对抗镜（144 条，采纳率 78%）。另有 9 面镜达到待复评轮数阈值，详见下方 ⚠️ 待复评区块。

## per-change 明细

| change | 总墙钟(min) | spec-rev Δ | impl Δ | code-rev Δ | done Δ | #ckpt | spec_hr_tg | code_hr_tg | Σfindings | 采纳率 | 独立Σ | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| adaptive-workflow-routing | 111.1 | 83.8 | 10.1 | 3.0 | 0.5 | 7 | none | none | 28 | 0.96 | 19 | archived |
| add-codex-host-support | 2293.6 | 339.3 | 979.8 | 124.2 | 140.8 | 18 | TG-06,TG-08,TG-17 | TG-04,TG-06,TG-07,TG-08,TG-17 | 14 | 0.86 | 10 | archived |
| add-sdflow-architecture | 378.4 | 54.4 | 228.6 | 15.4 | — | 9 | TG-06,TG-08,TG-09 | TG-06,TG-08,TG-09 | 108 | 0.83 | 35 | archived |
| add-sdflow-devenv | 1808.5 | 298.6 | 466.5 | — | — | 18 | TG-08,TG-09,TG-17,TG-26 | — | 22 | 0.64 | 8 | archived |
| batch-triage-strategy | 107.4 | 41.9 | 50.0 | 10.8 | — | 8 | none | none | 29 | 0.9 | 11 | archived |
| checkpoint-tag-single-source | 753.8 | 678.1 | 68.7 | 7.0 | — | 6 | none | none | — | 无度量锚 | — | archived |
| cross-model-outside-voice | 229.7 | 71.6 | 76.0 | 24.6 | — | 12 | — | TG-08,TG-17 | — | 无度量锚 | — | archived |
| done-roadmap-writeback | 193.4 | 120.4 | 31.8 | 6.9 | — | 13 | none | none | 52 | 0.94 | 10 | archived |
| drop-per-dir-review-stub | 53.8 | — | 32.6 | — | — | 5 | — | none | — | 无度量锚 | — | archived |
| gate-anchor-line-scoped | 7.0 | — | — | 7.0 | — | 9 | none | none | — | 无度量锚 | — | archived |
| gate-checkpoint-hardening | 87.8 | 17.9 | 26.7 | 7.3 | — | 10 | none | none | — | 无度量锚 | — | archived |
| harden-hr-tg-anchor-consistency | 183.6 | — | 104.4 | 7.2 | — | 6 | none | none | 24 | 1.0 | 20 | archived |
| implement-mechanical-layer-hardening-p4-lens-metric-emit | 234.5 | 97.8 | 77.5 | 7.6 | — | 9 | TG-06 | TG-06 | 67 | 0.88 | 13 | archived |
| issues-pool-batch-mgmt | 0.0（边界不可解析） | — | — | — | — | 0 | — | — | — | 无度量锚 | — | archived |
| issues-pool-hardening | 206.3 | 40.5 | — | 8.8 | — | 10 | none | none | 28 | 0.86 | 9 | archived |
| matt-workflow-integration | 0.0（边界不可解析） | — | — | — | — | 1 | TG-06,TG-08 | TG-06,TG-08 | 70 | 0.79 | 21 | archived |
| minimize-repo-footprint | 136.5 | 21.4 | 103.9 | 11.2 | — | 10 | — | — | — | 无度量锚 | — | archived |
| mlh-p1-issues-sweep | 42.7 | 10.9 | 24.6 | 7.2 | — | 6 | none | none | 36 | 0.81 | 8 | archived |
| mlh-p2-anchor-lint | 90.2 | 5.4 | — | 7.2 | — | 6 | none | none | 38 | 0.82 | 18 | archived |
| mlh-p3-determ-guards | 166.8 | 91.4 | 64.5 | 10.9 | — | 5 | none | none | 37 | 0.86 | 10 | archived |
| mlh-p4-maintain-scan | 221.7 | 29.1 | 106.3 | — | — | 7 | none | none | 39 | 0.97 | 17 | archived |
| mlh-p4-reason-code-validators | 310.3 | 62.8 | 60.6 | 9.2 | — | 19 | TG-08 | none | 39 | 0.74 | 14 | archived |
| mlh-p5-gate-frontmatter | 161.6 | 32.1 | 37.3 | 8.2 | — | 6 | TG-04,TG-08 | TG-04,TG-08 | 49 | 0.86 | 18 | archived |
| mlh-p5-parser-cleanup | 145.9 | 57.8 | 45.1 | 7.7 | — | 7 | none | none | 16 | 0.69 | 8 | archived |
| mlh-p6-recorder-frontmatter | 0.0（边界不可解析） | — | — | — | — | 0 | — | — | — | 无度量锚 | — | archived |
| plan-mechanical-layer-hardening | 0.2 | — | — | — | — | 2 | — | — | — | 无度量锚 | — | archived |
| plan-workflow-cost-optimization | 23.8 | — | — | — | — | 3 | — | — | — | 无度量锚 | — | archived |
| rebuild-sdflow-roadmap-v2 | 534.9 | 170.4 | 38.8 | 10.6 | — | 11 | TG-06,TG-08 | TG-06,TG-08 | 99 | 0.78 | 27 | archived |
| review-tool-followups | 70.4 | 22.6 | 30.4 | 8.0 | — | 8 | none | none | — | 无度量锚 | — | archived |
| scoped-test-per-task | 9927.2 | — | — | — | — | 3 | none | — | — | 无度量锚 | — | archived |
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
| unknown | 11210.6 | 56% |
| impl | 3291.7 | 17% |
| spec-review | 2575.2 | 13% |
| ff | 1691.5 | 9% |
| code-review | 392.1 | 2% |
| grill | 345.4 | 2% |
| other | 216.5 | 1% |
| done | 141.2 | 1% |

## 聚合② 成本双峰（总墙钟 x / code-review 占比% y）

| change | 总墙钟(min) | code-review 占比 |
|---|---|---|
| adaptive-workflow-routing | 111.1 | 3% |
| add-codex-host-support | 2293.6 | 5% |
| add-sdflow-architecture | 378.4 | 4% |
| add-sdflow-devenv | 1808.5 | 0% |
| batch-triage-strategy | 107.4 | 10% |
| checkpoint-tag-single-source | 753.8 | 1% |
| cross-model-outside-voice | 229.7 | 11% |
| done-roadmap-writeback | 193.4 | 4% |
| drop-per-dir-review-stub | 53.8 | 0% |
| gate-anchor-line-scoped | 7.0 | 100% |
| gate-checkpoint-hardening | 87.8 | 8% |
| harden-hr-tg-anchor-consistency | 183.6 | 4% |
| implement-mechanical-layer-hardening-p4-lens-metric-emit | 234.5 | 3% |
| issues-pool-batch-mgmt | 0.0 | — |
| issues-pool-hardening | 206.3 | 4% |
| matt-workflow-integration | 0.0 | — |
| minimize-repo-footprint | 136.5 | 8% |
| mlh-p1-issues-sweep | 42.7 | 17% |
| mlh-p2-anchor-lint | 90.2 | 8% |
| mlh-p3-determ-guards | 166.8 | 7% |
| mlh-p4-maintain-scan | 221.7 | 0% |
| mlh-p4-reason-code-validators | 310.3 | 3% |
| mlh-p5-gate-frontmatter | 161.6 | 5% |
| mlh-p5-parser-cleanup | 145.9 | 5% |
| mlh-p6-recorder-frontmatter | 0.0 | — |
| plan-mechanical-layer-hardening | 0.2 | 0% |
| plan-workflow-cost-optimization | 23.8 | 0% |
| rebuild-sdflow-roadmap-v2 | 534.9 | 2% |
| review-tool-followups | 70.4 | 11% |
| scoped-test-per-task | 9927.2 | 0% |
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

| layer | lens | host | runner | site | 出现轮数 | Σfindings | Σ采纳 | Σ裁掉 | Σdefer | Σ独立 | 采纳率 | 独立率 | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| code-review | adversarial | claude | claude | guard-bypass | 1 | 2 | 2 | 0 | 0 | 1 | 100% | 50% | — |
| code-review | adversarial | claude | claude | none | 1 | 5 | 3 | 1 | 1 | 1 | 60% | 20% | — |
| code-review | adversarial | claude | claude | parse-edge+blast-radius | 1 | 1 | 0 | 0 | 1 | 0 | 0% | 0% | — |
| code-review | adversarial | claude | claude | refactor-honesty | 1 | 3 | 1 | 0 | 2 | 0 | 33% | 0% | — |
| code-review | adversarial | claude | claude | — | 18 | 144 | 113 | 13 | 18 | 80 | 78% | 56% | ≥10待复评 |
| code-review | broad | claude | claude | native | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | broad | claude | claude | none | 1 | 1 | 1 | 0 | 0 | 1 | 100% | 100% | — |
| code-review | broad | claude | claude | step1 | 2 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | broad | claude | claude | — | 14 | 12 | 9 | 3 | 0 | 4 | 75% | 33% | ≥10待复评 |
| code-review | broad | claude | native | scope-drift | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | domain | claude | claude | backend | 1 | 4 | 3 | 0 | 1 | 2 | 75% | 50% | — |
| code-review | domain | claude | claude | checklist | 1 | 2 | 0 | 1 | 1 | 0 | 0% | 0% | — |
| code-review | domain | claude | claude | none | 1 | 3 | 3 | 0 | 0 | 2 | 100% | 67% | — |
| code-review | domain | claude | claude | — | 17 | 57 | 41 | 9 | 7 | 18 | 72% | 32% | ≥10待复评 |
| code-review | history | claude | claude | blame | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | history | claude | claude | git-blame | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | history | claude | claude | none | 1 | 2 | 1 | 1 | 0 | 0 | 50% | 0% | — |
| code-review | history | claude | claude | — | 17 | 13 | 8 | 4 | 1 | 3 | 62% | 23% | ≥10待复评 |
| code-review | outside-voice | claude | claude | code-voice | 1 | 4 | 2 | 1 | 1 | 1 | 50% | 25% | — |
| code-review | outside-voice | claude | codex | code-voice | 19 | 70 | 62 | 2 | 6 | 32 | 89% | 46% | ≥10待复评 |
| code-review | outside-voice | claude | codex | hr-tg | 6 | 21 | 20 | 0 | 1 | 7 | 95% | 33% | — |
| spec-review | adversarial | claude | claude | - | 1 | 8 | 8 | 0 | 0 | 4 | 100% | 50% | — |
| spec-review | adversarial | claude | claude | d1-t2 | 1 | 5 | 4 | 1 | 0 | 2 | 80% | 40% | — |
| spec-review | adversarial | claude | claude | d2-d3-scope | 1 | 4 | 4 | 0 | 0 | 2 | 100% | 50% | — |
| spec-review | adversarial | claude | claude | none | 2 | 30 | 28 | 2 | 0 | 9 | 93% | 30% | — |
| spec-review | adversarial | claude | claude | — | 14 | 139 | 128 | 6 | 5 | 63 | 92% | 45% | ≥10待复评 |
| spec-review | broad | claude | claude | - | 1 | 3 | 3 | 0 | 0 | 1 | 100% | 33% | — |
| spec-review | broad | claude | claude | autoplan-adapted | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | broad | claude | claude | none | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | broad | claude | claude | — | 14 | 106 | 91 | 10 | 5 | 21 | 86% | 20% | ≥10待复评 |
| spec-review | broad | claude | grill-substituted | design | 1 | 3 | 3 | 0 | 0 | 0 | 100% | 0% | — |
| spec-review | domain | claude | claude | backend | 1 | 5 | 5 | 0 | 0 | 1 | 100% | 20% | — |
| spec-review | domain | claude | claude | none | 2 | 12 | 12 | 0 | 0 | 3 | 100% | 25% | — |
| spec-review | domain | claude | claude | — | 6 | 31 | 31 | 0 | 0 | 16 | 100% | 52% | — |
| spec-review | grounding | claude | claude | - | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | grounding | claude | claude | code-facts | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | grounding | claude | claude | none | 2 | 3 | 3 | 0 | 0 | 0 | 100% | 0% | — |
| spec-review | grounding | claude | claude | — | 14 | 34 | 30 | 3 | 0 | 14 | 91% | 41% | ≥10待复评 |
| spec-review | outside-voice | claude | claude | design-voice | 4 | 25 | 23 | 0 | 2 | 5 | 92% | 20% | — |
| spec-review | outside-voice | claude | claude | hr-tg | 1 | 8 | 7 | 1 | 0 | 2 | 88% | 25% | — |
| spec-review | outside-voice | claude | codex | design-voice | 13 | 103 | 74 | 23 | 6 | 14 | 72% | 14% | ≥10待复评 |
| spec-review | outside-voice | claude | codex | hr-tg | 4 | 18 | 17 | 0 | 1 | 4 | 94% | 22% | — |

> 无锚样本 30 份（旧格式,不纳入；份=报告文件数，每 change 常含 spec/code 两份，非 change 数；去重后 17 个 change）: 2026-07-02-issues-pool-batch-mgmt, 2026-07-02-issues-pool-batch-mgmt, 2026-07-02-streamline-workflow-automation, 2026-07-03-minimize-repo-footprint, 2026-07-03-minimize-repo-footprint, 2026-07-03-sdflow-rebrand, 2026-07-03-sdflow-rebrand, 2026-07-03-sdflow-ship, 2026-07-03-sdflow-ship, 2026-07-04-cross-model-outside-voice, 2026-07-04-cross-model-outside-voice, 2026-07-04-ship-gate-hardening, 2026-07-04-ship-gate-hardening, 2026-07-04-ship-gate-hardening-2, 2026-07-04-ship-gate-hardening-2, 2026-07-05-checkpoint-tag-single-source, 2026-07-05-checkpoint-tag-single-source, 2026-07-05-drop-per-dir-review-stub, 2026-07-05-drop-per-dir-review-stub, 2026-07-05-gate-anchor-line-scoped, 2026-07-05-gate-anchor-line-scoped, 2026-07-05-gate-checkpoint-hardening, 2026-07-05-gate-checkpoint-hardening, 2026-07-05-review-tool-followups, 2026-07-05-review-tool-followups, 2026-07-05-three-lens-decision-framework, 2026-07-05-three-lens-decision-framework, 2026-07-05-workflow-metrics-loop, 2026-07-16-add-codex-host-support, 2026-07-16-scoped-test-per-task
> 解析失败 0 份（编码/IO 错误，已跳过未计入聚合，不拖垮全局）: 无
> 独立率跨轮不保证同口径（dedup 合并尺度可能漂移），复评时校验最近几轮尺度一致。

