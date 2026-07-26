# 全项目 change 成本×价值复盘（view-only 再生）

> 覆盖 49 change / 有真锚 31 / 边界不可解析 6
> 阶段墙钟为「阶段级 elapsed（含人读/拍板/生成时间）」口径（adr/0009），非纯 agent 耗时。

⚠️ 待复评: 以下镜出现轮数≥10、只提示不判断不自动砍——人读后自行决定保留/降采样/淘汰:
  - adversarial（layer=code-review host=claude runner=claude site=—，出现轮数 25）
  - broad（layer=code-review host=claude runner=claude site=—，出现轮数 21）
  - domain（layer=code-review host=claude runner=claude site=—，出现轮数 24）
  - history（layer=code-review host=claude runner=claude site=—，出现轮数 24）
  - outside-voice（layer=code-review host=claude runner=codex site=code-voice，出现轮数 25）
  - outside-voice（layer=code-review host=claude runner=codex site=hr-tg，出现轮数 13）
  - adversarial（layer=spec-review host=claude runner=claude site=—，出现轮数 20）
  - broad（layer=spec-review host=claude runner=claude site=—，出现轮数 20）
  - domain（layer=spec-review host=claude runner=claude site=—，出现轮数 10）
  - grounding（layer=spec-review host=claude runner=claude site=—，出现轮数 20）
  - outside-voice（layer=spec-review host=claude runner=codex site=design-voice，出现轮数 19）

## 一览

| 复盘 change | 总墙钟 | 有真锚 | 待复评镜 |
|---|---|---|---|
| 49 | ~460.3 hr | 31 | 11 |

本轮复盘覆盖 **49 个 change**，累计评审墙钟约 **460.3 hr**（其中 31 个带真实度量锚、可参与价值统计）。评审时间集中在 设计审 49%、未归类 19%（两者合计 67%）。单个 change 耗时最重的是 scoped-test-per-task（约 165.5 hr）、最轻的是 plan-mechanical-layer-hardening（0.2 min）。价值侧，出问题最多的是 设计审对抗镜（198 条，采纳率 92%）。另有 11 面镜达到待复评轮数阈值，详见下方 ⚠️ 待复评区块。

## per-change 明细

| change | 总墙钟(min) | spec-rev Δ | impl Δ | code-rev Δ | done Δ | #ckpt | spec_hr_tg | code_hr_tg | Σfindings | 采纳率 | 独立Σ | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| adaptive-workflow-routing | 111.1 | 83.8 | 10.1 | 3.0 | 0.5 | 7 | none | none | 28 | 0.96 | 19 | archived |
| add-codex-host-support | 5026.3 | 433.6 | 979.8 | 124.2 | 140.8 | 20 | TG-06,TG-08,TG-17 | TG-04,TG-06,TG-07,TG-08,TG-17 | 14 | 0.86 | 10 | archived |
| add-sdflow-architecture | 378.4 | 54.4 | 228.6 | 15.4 | — | 9 | TG-06,TG-08,TG-09 | TG-06,TG-08,TG-09 | 108 | 0.83 | 35 | archived |
| add-sdflow-devenv | 1808.5 | 298.6 | 466.5 | — | — | 18 | TG-08,TG-09,TG-17,TG-26 | — | 22 | 0.64 | 8 | archived |
| add-sdflow-spec | 685.7 | 123.6 | 75.6 | — | — | 23 | TG-08,TG-17 | — | 69 | 0.94 | 12 | in-progress |
| async-outside-voice | 411.5 | 161.4 | 94.7 | 10.5 | — | 29 | TG-09,TG-17,TG-26 | TG-06,TG-08,TG-09,TG-16,TG-17,TG-26 | 57 | 0.93 | 19 | archived |
| batch-triage-strategy | 107.4 | 41.9 | 50.0 | 10.8 | — | 8 | none | none | 29 | 0.9 | 11 | archived |
| checkpoint-tag-single-source | 753.8 | 678.1 | 68.7 | 7.0 | — | 6 | none | none | — | 无度量锚 | — | archived |
| cross-model-outside-voice | 229.7 | 71.6 | 76.0 | 24.6 | — | 12 | — | TG-08,TG-17 | — | 无度量锚 | — | archived |
| dedupe-issues-scripts-shared-layer | 1336.2 | 975.3 | 178.5 | 37.5 | — | 26 | TG-06 | TG-06,TG-26 | 38 | 0.89 | 7 | archived |
| done-roadmap-writeback | 193.4 | 120.4 | 31.8 | 6.9 | — | 13 | none | none | 52 | 0.94 | 10 | archived |
| drop-per-dir-review-stub | 53.8 | — | 32.6 | — | — | 5 | — | none | — | 无度量锚 | — | archived |
| drop-review-html-viewer | 0.0（边界不可解析） | — | — | — | — | 1 | — | — | — | 无度量锚 | — | archived |
| enable-codex-background-outside-voice | 0.0（边界不可解析） | — | — | — | — | 1 | TG-08,TG-09,TG-16,TG-17,TG-26 | TG-08,TG-09,TG-16,TG-17,TG-26 | 40 | 0.72 | 9 | archived |
| fix-design-gate-freshness-proxy | 447.5 | 181.0 | 85.1 | 22.6 | — | 26 | none | TG-17 | 46 | 0.83 | 22 | archived |
| fix-mechanical-layer-silent-failures | 999.7 | 55.1 | 495.0 | 150.6 | — | 19 | TG-08,TG-17 | TG-08,TG-09,TG-17,TG-26 | 42 | 0.83 | 27 | archived |
| gate-anchor-line-scoped | 7.0 | — | — | 7.0 | — | 9 | none | none | — | 无度量锚 | — | archived |
| gate-checkpoint-hardening | 87.8 | 17.9 | 26.7 | 7.3 | — | 10 | none | none | — | 无度量锚 | — | archived |
| harden-gate-git-layer | 617.1 | 202.2 | 111.1 | 14.6 | — | 36 | TG-17 | TG-17 | 54 | 0.8 | 37 | archived |
| harden-hr-tg-anchor-consistency | 183.6 | 51.2 | 104.4 | 7.2 | — | 6 | none | none | 24 | 1.0 | 20 | archived |
| harden-repo-root-fail-closed | 522.4 | 142.2 | 123.5 | 19.3 | — | 28 | TG-08 | TG-08 | 54 | 0.83 | 32 | archived |
| implement-mechanical-layer-hardening-p4-lens-metric-emit | 234.5 | 97.8 | 77.5 | 7.6 | — | 9 | TG-06 | TG-06 | 67 | 0.88 | 13 | archived |
| issues-pool-batch-mgmt | 0.0（边界不可解析） | — | — | — | — | 0 | — | — | — | 无度量锚 | — | archived |
| issues-pool-hardening | 206.3 | 40.5 | — | 8.8 | — | 10 | none | none | 28 | 0.86 | 9 | archived |
| matt-workflow-integration | 0.0（边界不可解析） | — | — | — | — | 1 | TG-06,TG-08 | TG-06,TG-08 | 70 | 0.79 | 21 | archived |
| minimize-repo-footprint | 136.5 | 21.4 | 103.9 | 11.2 | — | 10 | — | — | — | 无度量锚 | — | archived |
| mlh-p1-issues-sweep | 42.7 | 10.9 | 24.6 | 7.2 | — | 6 | none | none | 36 | 0.81 | 8 | archived |
| mlh-p2-anchor-lint | 90.2 | 5.4 | — | 7.2 | — | 6 | none | none | 38 | 0.82 | 18 | archived |
| mlh-p3-determ-guards | 166.8 | 91.4 | 64.5 | 10.9 | — | 5 | none | none | 37 | 0.86 | 10 | archived |
| mlh-p4-maintain-scan | 221.7 | 29.1 | 106.3 | 8.4 | — | 7 | none | none | 39 | 0.97 | 17 | archived |
| mlh-p4-reason-code-validators | 310.3 | 62.8 | 60.6 | 9.2 | — | 19 | TG-08 | none | 39 | 0.74 | 14 | archived |
| mlh-p5-gate-frontmatter | 161.6 | 32.1 | 37.3 | 8.2 | — | 6 | TG-04,TG-08 | TG-04,TG-08 | 49 | 0.86 | 18 | archived |
| mlh-p5-parser-cleanup | 145.9 | 57.8 | 45.1 | 7.7 | — | 7 | none | none | 16 | 0.69 | 8 | archived |
| mlh-p6-recorder-frontmatter | 0.0（边界不可解析） | — | — | — | — | 1 | TG-06,TG-16,TG-26 | — | 34 | 0.85 | 16 | archived |
| plan-mechanical-layer-hardening | 0.2 | — | — | — | — | 2 | — | — | — | 无度量锚 | — | archived |
| plan-workflow-cost-optimization | 23.8 | — | — | — | — | 3 | — | — | — | 无度量锚 | — | archived |
| rebuild-sdflow-roadmap-v2 | 534.9 | 170.4 | 38.8 | 10.6 | — | 11 | TG-06,TG-08 | TG-06,TG-08 | 99 | 0.78 | 27 | archived |
| review-tool-followups | 70.4 | 22.6 | 30.4 | 8.0 | — | 8 | none | none | — | 无度量锚 | — | archived |
| scoped-test-per-task | 9927.2 | 8883.8 | — | — | — | 3 | none | — | — | 无度量锚 | — | archived |
| sdflow-init-hardening | 37.2 | — | 31.3 | 5.9 | — | 3 | — | TG-26 | 13 | 0.85 | 4 | archived |
| sdflow-rebrand | 253.0 | 14.6 | 191.5 | 29.6 | — | 14 | — | — | — | 无度量锚 | — | archived |
| sdflow-retro | 279.6 | 40.3 | 177.6 | 12.9 | — | 8 | none | none | 49 | 0.82 | 20 | archived |
| sdflow-retro-cleanup | 37.2 | — | 14.9 | 15.4 | — | 4 | — | none | 8 | 0.62 | 3 | archived |
| sdflow-ship | 290.8 | 24.9 | 86.2 | 8.4 | — | 10 | — | — | — | 无度量锚 | — | archived |
| ship-gate-hardening | 180.8 | 79.6 | — | 8.2 | — | 8 | TG-09 | TG-09 | — | 无度量锚 | — | archived |
| ship-gate-hardening-2 | 110.0 | 25.2 | 25.2 | 7.2 | — | 8 | none | none | — | 无度量锚 | — | archived |
| streamline-workflow-automation | 0.0（边界不可解析） | — | — | — | — | 0 | — | — | — | 无度量锚 | — | archived |
| three-lens-decision-framework | 75.3 | 29.6 | 22.4 | 5.2 | — | 10 | none | none | — | 无度量锚 | — | archived |
| workflow-metrics-loop | 119.2 | 12.8 | 78.2 | 10.5 | — | 6 | none | none | 16 | 0.94 | 10 | archived |

## 聚合① 阶段占比

| 阶段 | 墙钟(min) | 占比 |
|---|---|---|
| spec-review | 13445.6 | 49% |
| unknown | 5112.9 | 19% |
| impl | 4455.2 | 16% |
| ff | 2609.5 | 9% |
| grill | 682.9 | 2% |
| code-review | 676.9 | 2% |
| other | 492.4 | 2% |
| done | 141.2 | 1% |

## 聚合② 成本双峰（总墙钟 x / code-review 占比% y）

| change | 总墙钟(min) | code-review 占比 |
|---|---|---|
| adaptive-workflow-routing | 111.1 | 3% |
| add-codex-host-support | 5026.3 | 2% |
| add-sdflow-architecture | 378.4 | 4% |
| add-sdflow-devenv | 1808.5 | 0% |
| add-sdflow-spec | 685.7 | 0% |
| async-outside-voice | 411.5 | 3% |
| batch-triage-strategy | 107.4 | 10% |
| checkpoint-tag-single-source | 753.8 | 1% |
| cross-model-outside-voice | 229.7 | 11% |
| dedupe-issues-scripts-shared-layer | 1336.2 | 3% |
| done-roadmap-writeback | 193.4 | 4% |
| drop-per-dir-review-stub | 53.8 | 0% |
| drop-review-html-viewer | 0.0 | — |
| enable-codex-background-outside-voice | 0.0 | — |
| fix-design-gate-freshness-proxy | 447.5 | 5% |
| fix-mechanical-layer-silent-failures | 999.7 | 15% |
| gate-anchor-line-scoped | 7.0 | 100% |
| gate-checkpoint-hardening | 87.8 | 8% |
| harden-gate-git-layer | 617.1 | 2% |
| harden-hr-tg-anchor-consistency | 183.6 | 4% |
| harden-repo-root-fail-closed | 522.4 | 4% |
| implement-mechanical-layer-hardening-p4-lens-metric-emit | 234.5 | 3% |
| issues-pool-batch-mgmt | 0.0 | — |
| issues-pool-hardening | 206.3 | 4% |
| matt-workflow-integration | 0.0 | — |
| minimize-repo-footprint | 136.5 | 8% |
| mlh-p1-issues-sweep | 42.7 | 17% |
| mlh-p2-anchor-lint | 90.2 | 8% |
| mlh-p3-determ-guards | 166.8 | 7% |
| mlh-p4-maintain-scan | 221.7 | 4% |
| mlh-p4-reason-code-validators | 310.3 | 3% |
| mlh-p5-gate-frontmatter | 161.6 | 5% |
| mlh-p5-parser-cleanup | 145.9 | 5% |
| mlh-p6-recorder-frontmatter | 0.0 | — |
| plan-mechanical-layer-hardening | 0.2 | 0% |
| plan-workflow-cost-optimization | 23.8 | 0% |
| rebuild-sdflow-roadmap-v2 | 534.9 | 2% |
| review-tool-followups | 70.4 | 11% |
| scoped-test-per-task | 9927.2 | 0% |
| sdflow-init-hardening | 37.2 | 16% |
| sdflow-rebrand | 253.0 | 12% |
| sdflow-retro | 279.6 | 5% |
| sdflow-retro-cleanup | 37.2 | 41% |
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
| code-review | adversarial | claude | claude | — | 25 | 175 | 132 | 13 | 30 | 94 | 75% | 54% | ≥10待复评 |
| code-review | broad | claude | claude | native | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | broad | claude | claude | none | 1 | 1 | 1 | 0 | 0 | 1 | 100% | 100% | — |
| code-review | broad | claude | claude | step1 | 2 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | broad | claude | claude | — | 21 | 16 | 12 | 3 | 1 | 7 | 75% | 44% | ≥10待复评 |
| code-review | broad | claude | native | scope-drift | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | domain | claude | claude | backend | 1 | 4 | 3 | 0 | 1 | 2 | 75% | 50% | — |
| code-review | domain | claude | claude | checklist | 1 | 2 | 0 | 1 | 1 | 0 | 0% | 0% | — |
| code-review | domain | claude | claude | none | 1 | 3 | 3 | 0 | 0 | 2 | 100% | 67% | — |
| code-review | domain | claude | claude | — | 24 | 70 | 50 | 11 | 9 | 24 | 71% | 34% | ≥10待复评 |
| code-review | history | claude | claude | blame | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | history | claude | claude | git-blame | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | history | claude | claude | none | 1 | 2 | 1 | 1 | 0 | 0 | 50% | 0% | — |
| code-review | history | claude | claude | — | 24 | 17 | 12 | 4 | 1 | 6 | 71% | 35% | ≥10待复评 |
| code-review | outside-voice | claude | claude | code-voice | 2 | 5 | 3 | 1 | 1 | 2 | 60% | 40% | — |
| code-review | outside-voice | claude | codex | code-voice | 25 | 88 | 74 | 3 | 11 | 42 | 84% | 48% | ≥10待复评 |
| code-review | outside-voice | claude | codex | hr-tg | 13 | 46 | 35 | 2 | 10 | 19 | 74% | 41% | ≥10待复评 |
| spec-review | adversarial | claude | claude | - | 1 | 8 | 8 | 0 | 0 | 4 | 100% | 50% | — |
| spec-review | adversarial | claude | claude | d1-t2 | 1 | 5 | 4 | 1 | 0 | 2 | 80% | 40% | — |
| spec-review | adversarial | claude | claude | d2-d3-scope | 1 | 4 | 4 | 0 | 0 | 2 | 100% | 50% | — |
| spec-review | adversarial | claude | claude | none | 2 | 30 | 28 | 2 | 0 | 9 | 93% | 30% | — |
| spec-review | adversarial | claude | claude | — | 20 | 198 | 182 | 11 | 5 | 97 | 92% | 49% | ≥10待复评 |
| spec-review | adversarial | codex | codex | — | 2 | 17 | 17 | 0 | 0 | 9 | 100% | 53% | — |
| spec-review | broad | claude | claude | - | 1 | 3 | 3 | 0 | 0 | 1 | 100% | 33% | — |
| spec-review | broad | claude | claude | autoplan-adapted | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | broad | claude | claude | none | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | broad | claude | claude | — | 20 | 166 | 149 | 11 | 6 | 55 | 90% | 33% | ≥10待复评 |
| spec-review | broad | claude | grill-substituted | design | 1 | 3 | 3 | 0 | 0 | 0 | 100% | 0% | — |
| spec-review | broad | codex | codex | — | 2 | 20 | 16 | 4 | 0 | 5 | 80% | 25% | — |
| spec-review | domain | claude | claude | backend | 1 | 5 | 5 | 0 | 0 | 1 | 100% | 20% | — |
| spec-review | domain | claude | claude | none | 2 | 12 | 12 | 0 | 0 | 3 | 100% | 25% | — |
| spec-review | domain | claude | claude | — | 10 | 52 | 50 | 0 | 2 | 25 | 96% | 48% | ≥10待复评 |
| spec-review | grounding | claude | claude | - | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | grounding | claude | claude | code-facts | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | grounding | claude | claude | none | 2 | 3 | 3 | 0 | 0 | 0 | 100% | 0% | — |
| spec-review | grounding | claude | claude | — | 20 | 51 | 41 | 9 | 0 | 18 | 82% | 35% | ≥10待复评 |
| spec-review | grounding | codex | codex | — | 2 | 9 | 9 | 0 | 0 | 3 | 100% | 33% | — |
| spec-review | outside-voice | claude | claude | design-voice | 4 | 25 | 23 | 0 | 2 | 5 | 92% | 20% | — |
| spec-review | outside-voice | claude | claude | hr-tg | 1 | 8 | 7 | 1 | 0 | 2 | 88% | 25% | — |
| spec-review | outside-voice | claude | codex | design-voice | 19 | 135 | 103 | 23 | 9 | 24 | 76% | 18% | ≥10待复评 |
| spec-review | outside-voice | claude | codex | hr-tg | 9 | 38 | 35 | 0 | 3 | 12 | 92% | 32% | — |
| spec-review | outside-voice | codex | codex | design-voice | 2 | 6 | 4 | 2 | 0 | 2 | 67% | 33% | — |
| spec-review | outside-voice | codex | codex | hr-tg | 2 | 8 | 8 | 0 | 0 | 2 | 100% | 25% | — |

> 无锚样本 31 份（旧格式,不纳入；份=报告文件数，每 change 常含 spec/code 两份，非 change 数；去重后 18 个 change）: 2026-07-02-issues-pool-batch-mgmt, 2026-07-02-issues-pool-batch-mgmt, 2026-07-02-streamline-workflow-automation, 2026-07-03-minimize-repo-footprint, 2026-07-03-minimize-repo-footprint, 2026-07-03-sdflow-rebrand, 2026-07-03-sdflow-rebrand, 2026-07-03-sdflow-ship, 2026-07-03-sdflow-ship, 2026-07-04-cross-model-outside-voice, 2026-07-04-cross-model-outside-voice, 2026-07-04-ship-gate-hardening, 2026-07-04-ship-gate-hardening, 2026-07-04-ship-gate-hardening-2, 2026-07-04-ship-gate-hardening-2, 2026-07-05-checkpoint-tag-single-source, 2026-07-05-checkpoint-tag-single-source, 2026-07-05-drop-per-dir-review-stub, 2026-07-05-drop-per-dir-review-stub, 2026-07-05-gate-anchor-line-scoped, 2026-07-05-gate-anchor-line-scoped, 2026-07-05-gate-checkpoint-hardening, 2026-07-05-gate-checkpoint-hardening, 2026-07-05-review-tool-followups, 2026-07-05-review-tool-followups, 2026-07-05-three-lens-decision-framework, 2026-07-05-three-lens-decision-framework, 2026-07-05-workflow-metrics-loop, 2026-07-16-add-codex-host-support, 2026-07-16-scoped-test-per-task, 2026-07-19-fix-mechanical-layer-silent-failures
> 解析失败 0 份（编码/IO 错误，已跳过未计入聚合，不拖垮全局）: 无
> 独立率跨轮不保证同口径（dedup 合并尺度可能漂移），复评时校验最近几轮尺度一致。

