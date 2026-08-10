# 全项目 change 成本×价值复盘（view-only 再生）

> 覆盖 69 change / 有真锚 50 / 边界不可解析 7
> 阶段墙钟为「阶段级 elapsed（含人读/拍板/生成时间）」口径（adr/0009），非纯 agent 耗时。

⚠️ 待复评: 以下镜出现轮数≥10、只提示不判断不自动砍——人读后自行决定保留/降采样/淘汰:
  - adversarial（layer=code-review host=claude runner=claude site=—，出现轮数 35）
  - broad（layer=code-review host=claude runner=claude site=—，出现轮数 31）
  - domain（layer=code-review host=claude runner=claude site=—，出现轮数 33）
  - history（layer=code-review host=claude runner=claude site=—，出现轮数 34）
  - outside-voice（layer=code-review host=claude runner=codex site=code-voice，出现轮数 31）
  - outside-voice（layer=code-review host=claude runner=codex site=hr-tg，出现轮数 16）
  - adversarial（layer=spec-review host=claude runner=claude site=—，出现轮数 39）
  - broad（layer=spec-review host=claude runner=claude site=—，出现轮数 39）
  - domain（layer=spec-review host=claude runner=claude site=—，出现轮数 17）
  - grounding（layer=spec-review host=claude runner=claude site=—，出现轮数 39）
  - outside-voice（layer=spec-review host=claude runner=claude site=design-voice，出现轮数 11）
  - outside-voice（layer=spec-review host=claude runner=codex site=design-voice，出现轮数 31）
  - outside-voice（layer=spec-review host=claude runner=codex site=hr-tg，出现轮数 12）

## 一览

| 复盘 change | 总墙钟 | 有真锚 | 待复评镜 |
|---|---|---|---|
| 69 | ~598.8 hr | 50 | 13 |

本轮复盘覆盖 **69 个 change**，累计评审墙钟约 **598.8 hr**（其中 50 个带真实度量锚、可参与价值统计）。评审时间集中在 收尾 27%、设计审 25%（两者合计 52%）。单个 change 耗时最重的是 scoped-test-per-task（约 165.5 hr）、最轻的是 plan-mechanical-layer-hardening（0.2 min）。价值侧，出问题最多的是 设计审广审镜（415 条，采纳率 87%）。另有 13 面镜达到待复评轮数阈值，详见下方 ⚠️ 待复评区块。

## per-change 明细

| change | 总墙钟(min) | spec-rev Δ | impl Δ | code-rev Δ | done Δ | #ckpt | spec_hr_tg | code_hr_tg | Σfindings | 采纳率 | 独立Σ | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| absorb-gstack-autoplan | 356.5 | 148.3 | 32.4 | 12.1 | 21.3 | 22 | none | — | 49 | 0.76 | 7 | archived |
| absorb-gstack-review | 313.5 | 138.2 | 40.3 | 39.8 | 19.7 | 24 | none | TG-06,TG-08 | 51 | 0.71 | 18 | archived |
| adaptive-workflow-routing | 111.1 | 50.9 | 46.6 | 10.1 | 3.5 | 7 | none | none | 28 | 0.96 | 19 | archived |
| add-codex-host-support | 5026.3 | 260.3 | 190.3 | 1074.7 | 29.3 | 20 | TG-06,TG-08,TG-17 | TG-04,TG-06,TG-07,TG-08,TG-17 | 14 | 0.86 | 10 | archived |
| add-sdflow-architecture | 378.4 | 59.1 | 169.3 | 77.8 | 15.4 | 9 | TG-06,TG-08,TG-09 | TG-06,TG-08,TG-09 | 108 | 0.83 | 35 | archived |
| add-sdflow-devenv | 1808.5 | 158.2 | 1453.4 | — | 37.2 | 18 | TG-08,TG-09,TG-17,TG-26 | — | 22 | 0.64 | 8 | archived |
| add-sdflow-spec | 1139.2 | 168.2 | 48.3 | 66.6 | 20.8 | 40 | TG-08,TG-17 | TG-08,TG-17 | 77 | 0.94 | 19 | archived |
| align-sdflow-spec-with-openspec-schema | 698.7 | 450.6 | 110.3 | 62.4 | 12.6 | 23 | TG-06,TG-08 | — | 26 | 0.92 | 8 | archived |
| async-outside-voice | 411.5 | 189.2 | 14.7 | 25.4 | 10.5 | 29 | TG-09,TG-17,TG-26 | TG-06,TG-08,TG-09,TG-16,TG-17,TG-26 | 57 | 0.93 | 19 | archived |
| batch-triage-strategy | 107.4 | 37.0 | 9.6 | 53.5 | 7.3 | 8 | none | none | 29 | 0.9 | 11 | archived |
| checkpoint-tag-single-source | 753.8 | 55.4 | 681.3 | 10.1 | 7.0 | 6 | none | none | — | 无度量锚 | — | archived |
| complete-openspec-170-followup | 76.9 | 24.2 | 12.5 | 13.4 | 5.9 | 15 | none | none | 9 | 0.78 | 3 | archived |
| cross-model-outside-voice | 229.7 | 78.1 | 57.1 | 57.0 | 5.8 | 12 | — | TG-08,TG-17 | — | 无度量锚 | — | archived |
| curb-rework-loop-cost | 247.6 | 146.1 | 51.2 | 22.0 | 6.9 | 15 | none | none | 31 | 0.45 | 8 | archived |
| dedupe-issues-scripts-shared-layer | 1336.2 | 955.2 | 51.5 | 34.1 | 20.3 | 26 | TG-06 | TG-06,TG-26 | 38 | 0.89 | 7 | archived |
| done-roadmap-writeback | 193.4 | 118.2 | 11.6 | 31.8 | 6.9 | 13 | none | none | 52 | 0.94 | 10 | archived |
| drop-per-dir-review-stub | 53.8 | — | 36.9 | — | 12.8 | 5 | — | none | — | 无度量锚 | — | archived |
| drop-review-html-viewer | 0.0（边界不可解析） | — | — | — | — | 1 | — | — | — | 无度量锚 | — | archived |
| enable-codex-background-outside-voice | 0.0（边界不可解析） | — | — | — | — | 1 | TG-08,TG-09,TG-16,TG-17,TG-26 | TG-08,TG-09,TG-16,TG-17,TG-26 | 40 | 0.72 | 9 | archived |
| fix-b11-b12-tools-hardening | 0.0（边界不可解析） | — | — | — | — | 1 | — | — | — | 无度量锚 | — | archived |
| fix-design-gate-freshness-proxy | 447.5 | 227.7 | 28.6 | 23.0 | 10.5 | 26 | none | TG-17 | 46 | 0.83 | 22 | archived |
| fix-mechanical-layer-silent-failures | 999.7 | 52.8 | 98.0 | 532.8 | 38.5 | 19 | TG-08,TG-17 | TG-08,TG-09,TG-17,TG-26 | 42 | 0.83 | 27 | archived |
| fix-probe-scan-precision | 1174.0 | 719.5 | 22.3 | 9.8 | 22.0 | 23 | TG-07,TG-17 | none | 48 | 0.96 | 46 | archived |
| fix-voice-quoting-and-mirror-vocab | 316.7 | 239.8 | 17.6 | 9.7 | 11.6 | 18 | TG-17 | TG-17 | 21 | 0.86 | 6 | archived |
| fix-windows-encoding-crash | 875.6 | 769.6 | 26.3 | — | 6.5 | 34 | none | none | 48 | 0.94 | 13 | archived |
| gate-anchor-line-scoped | 7.0 | — | — | — | 7.0 | 9 | none | none | — | 无度量锚 | — | archived |
| gate-checkpoint-hardening | 87.8 | 27.6 | 17.1 | 13.8 | 7.3 | 10 | none | none | — | 无度量锚 | — | archived |
| harden-gate-git-layer | 617.0 | 253.9 | 52.3 | 10.1 | 13.4 | 36 | TG-17 | TG-17 | 54 | 0.8 | 37 | archived |
| harden-hr-tg-anchor-consistency | 183.6 | 55.3 | 16.7 | 104.4 | 7.2 | 6 | none | none | 24 | 1.0 | 20 | archived |
| harden-implement-review-loop | 1203.0 | 758.5 | 83.0 | 48.5 | 24.3 | 26 | none | none | 61 | 0.82 | 42 | archived |
| harden-issues-read-write | 148.2 | 94.1 | 9.2 | 12.0 | 7.3 | 17 | none | TG-06 | 25 | 0.8 | 4 | archived |
| harden-outside-voice-scripts | 119.6 | 47.7 | 12.3 | 10.3 | 7.4 | 16 | none | none | 21 | 0.62 | 2 | archived |
| harden-repo-root-fail-closed | 522.4 | 160.7 | 53.0 | 7.3 | 19.3 | 28 | TG-08 | TG-08 | 54 | 0.83 | 32 | archived |
| harden-sdflow-spec-followups | 353.4 | 85.3 | 18.4 | 20.9 | 17.6 | 34 | none | TG-08,TG-17 | 28 | 0.64 | 6 | archived |
| implement-mechanical-layer-hardening-p4-lens-metric-emit | 234.5 | 110.6 | 70.6 | 23.1 | 7.6 | 9 | TG-06 | TG-06 | 67 | 0.88 | 13 | archived |
| issues-pool-batch-mgmt | 0.0（边界不可解析） | — | — | — | — | 0 | — | — | — | 无度量锚 | — | archived |
| issues-pool-hardening | 206.3 | 37.8 | — | 116.8 | 8.8 | 10 | none | none | 28 | 0.86 | 9 | archived |
| issues-v2-single-file-model | 204.3 | 44.8 | 118.8 | 13.8 | 11.9 | 15 | TG-09 | none | 36 | 1.0 | 11 | archived |
| matt-workflow-integration | 0.0（边界不可解析） | — | — | — | — | 1 | TG-06,TG-08 | TG-06,TG-08 | 70 | 0.79 | 21 | archived |
| minimize-repo-footprint | 136.5 | 34.5 | 60.2 | 32.1 | 9.7 | 10 | — | — | — | 无度量锚 | — | archived |
| mlh-p1-issues-sweep | 42.7 | 2.6 | 15.6 | 17.4 | 7.2 | 6 | none | none | 36 | 0.81 | 8 | archived |
| mlh-p2-anchor-lint | 90.2 | 29.9 | — | 32.1 | 7.2 | 6 | none | none | 38 | 0.82 | 18 | archived |
| mlh-p3-determ-guards | 166.8 | 1.9 | 89.4 | 64.5 | 10.9 | 5 | none | none | 37 | 0.86 | 10 | archived |
| mlh-p4-maintain-scan | 221.7 | 38.8 | 14.3 | 106.3 | 8.4 | 7 | none | none | 39 | 0.97 | 17 | archived |
| mlh-p4-reason-code-validators | 310.3 | 98.3 | 15.7 | 6.6 | 9.2 | 19 | TG-08 | none | 39 | 0.74 | 14 | archived |
| mlh-p5-gate-frontmatter | 161.6 | 15.3 | 84.0 | 37.3 | 8.2 | 6 | TG-04,TG-08 | TG-04,TG-08 | 49 | 0.86 | 18 | archived |
| mlh-p5-parser-cleanup | 145.9 | 70.0 | 23.1 | 45.1 | 7.7 | 7 | none | none | 16 | 0.69 | 8 | archived |
| mlh-p6-recorder-frontmatter | 0.0（边界不可解析） | — | — | — | — | 1 | TG-06,TG-16,TG-26 | — | 34 | 0.85 | 16 | archived |
| parallelize-grounding-mirror | 142.4 | 39.7 | 43.1 | 12.6 | 10.5 | 16 | none | none | 17 | 1.0 | 4 | archived |
| plan-mechanical-layer-hardening | 0.2 | — | — | — | 0.2 | 2 | — | — | — | 无度量锚 | — | archived |
| plan-workflow-cost-optimization | 23.8 | — | — | — | 0.5 | 3 | — | — | — | 无度量锚 | — | archived |
| rebuild-sdflow-roadmap-v2 | 534.9 | 80.7 | 32.4 | 28.2 | 10.6 | 11 | TG-06,TG-08 | TG-06,TG-08 | 99 | 0.78 | 27 | archived |
| refactor-roadmap-internalize-deps | 296.1 | 92.7 | 36.0 | 27.8 | 20.5 | 34 | TG-08,TG-09 | TG-08,TG-09 | 73 | 0.85 | 42 | archived |
| review-tool-followups | 70.4 | 24.3 | 19.2 | 18.8 | 8.0 | 8 | none | none | — | 无度量锚 | — | archived |
| scoped-test-per-task | 9927.2 | 1043.3 | — | — | 8883.8 | 3 | none | — | — | 无度量锚 | — | archived |
| sdflow-init-hardening | 37.2 | — | — | 31.3 | 5.9 | 3 | — | TG-26 | 13 | 0.85 | 4 | archived |
| sdflow-init-readwrite-paths | 282.2 | 70.8 | 81.9 | 14.5 | 14.6 | 11 | none | none | 15 | 0.8 | 4 | archived |
| sdflow-rebrand | 253.0 | 29.4 | 170.3 | 43.8 | 9.5 | 14 | — | — | — | 无度量锚 | — | archived |
| sdflow-retro | 279.6 | 29.5 | 14.8 | 177.6 | 12.9 | 8 | none | none | 49 | 0.82 | 20 | archived |
| sdflow-retro-cleanup | 37.2 | — | 6.9 | 14.9 | 15.4 | 4 | — | none | 8 | 0.62 | 3 | archived |
| sdflow-ship | 290.8 | 44.8 | 94.3 | 34.7 | 8.4 | 10 | — | — | — | 无度量锚 | — | archived |
| shared-yaml-subset-parser | 626.8 | 65.6 | 107.0 | 112.8 | 40.0 | 26 | TG-08 | none | 23 | 0.78 | 14 | archived |
| ship-gate-hardening | 180.8 | 94.5 | — | 33.1 | 8.2 | 8 | TG-09 | TG-09 | — | 无度量锚 | — | archived |
| ship-gate-hardening-2 | 110.0 | 39.4 | 16.1 | 17.2 | 7.2 | 8 | none | none | — | 无度量锚 | — | archived |
| simplify-workflow | 231.3 | 61.1 | 17.8 | 3.8 | 20.3 | 25 | none | none | 23 | 0.87 | 12 | archived |
| streamline-workflow-automation | 0.0（边界不可解析） | — | — | — | — | 0 | — | — | — | 无度量锚 | — | archived |
| three-lens-decision-framework | 75.3 | 35.5 | 13.5 | 16.1 | 5.2 | 10 | none | none | — | 无度量锚 | — | archived |
| tickets-parallel-frontier | 188.4 | 135.0 | 8.4 | 10.9 | 7.8 | 15 | none | TG-04,TG-17 | 21 | 1.0 | 6 | archived |
| workflow-metrics-loop | 119.2 | 21.6 | 8.9 | 78.2 | 10.5 | 6 | none | none | 16 | 0.94 | 10 | archived |

## 聚合① 阶段占比

| 阶段 | 墙钟(min) | 占比 |
|---|---|---|
| done | 9639.8 | 27% |
| spec-review | 8922.0 | 25% |
| unknown | 6568.9 | 18% |
| impl | 4634.7 | 13% |
| code-review | 3565.0 | 10% |
| grill | 1825.0 | 5% |
| other | 577.1 | 2% |
| ff | 192.7 | 1% |

## 聚合② 成本双峰（总墙钟 x / code-review 占比% y）

| change | 总墙钟(min) | code-review 占比 |
|---|---|---|
| absorb-gstack-autoplan | 356.5 | 3% |
| absorb-gstack-review | 313.5 | 13% |
| adaptive-workflow-routing | 111.1 | 9% |
| add-codex-host-support | 5026.3 | 21% |
| add-sdflow-architecture | 378.4 | 21% |
| add-sdflow-devenv | 1808.5 | 0% |
| add-sdflow-spec | 1139.2 | 6% |
| align-sdflow-spec-with-openspec-schema | 698.7 | 9% |
| async-outside-voice | 411.5 | 6% |
| batch-triage-strategy | 107.4 | 50% |
| checkpoint-tag-single-source | 753.8 | 1% |
| complete-openspec-170-followup | 76.9 | 17% |
| cross-model-outside-voice | 229.7 | 25% |
| curb-rework-loop-cost | 247.6 | 9% |
| dedupe-issues-scripts-shared-layer | 1336.2 | 3% |
| done-roadmap-writeback | 193.4 | 16% |
| drop-per-dir-review-stub | 53.8 | 0% |
| drop-review-html-viewer | 0.0 | — |
| enable-codex-background-outside-voice | 0.0 | — |
| fix-b11-b12-tools-hardening | 0.0 | — |
| fix-design-gate-freshness-proxy | 447.5 | 5% |
| fix-mechanical-layer-silent-failures | 999.7 | 53% |
| fix-probe-scan-precision | 1174.0 | 1% |
| fix-voice-quoting-and-mirror-vocab | 316.7 | 3% |
| fix-windows-encoding-crash | 875.6 | 0% |
| gate-anchor-line-scoped | 7.0 | 0% |
| gate-checkpoint-hardening | 87.8 | 16% |
| harden-gate-git-layer | 617.0 | 2% |
| harden-hr-tg-anchor-consistency | 183.6 | 57% |
| harden-implement-review-loop | 1203.0 | 4% |
| harden-issues-read-write | 148.2 | 8% |
| harden-outside-voice-scripts | 119.6 | 9% |
| harden-repo-root-fail-closed | 522.4 | 1% |
| harden-sdflow-spec-followups | 353.4 | 6% |
| implement-mechanical-layer-hardening-p4-lens-metric-emit | 234.5 | 10% |
| issues-pool-batch-mgmt | 0.0 | — |
| issues-pool-hardening | 206.3 | 57% |
| issues-v2-single-file-model | 204.3 | 7% |
| matt-workflow-integration | 0.0 | — |
| minimize-repo-footprint | 136.5 | 24% |
| mlh-p1-issues-sweep | 42.7 | 41% |
| mlh-p2-anchor-lint | 90.2 | 36% |
| mlh-p3-determ-guards | 166.8 | 39% |
| mlh-p4-maintain-scan | 221.7 | 48% |
| mlh-p4-reason-code-validators | 310.3 | 2% |
| mlh-p5-gate-frontmatter | 161.6 | 23% |
| mlh-p5-parser-cleanup | 145.9 | 31% |
| mlh-p6-recorder-frontmatter | 0.0 | — |
| parallelize-grounding-mirror | 142.4 | 9% |
| plan-mechanical-layer-hardening | 0.2 | 0% |
| plan-workflow-cost-optimization | 23.8 | 0% |
| rebuild-sdflow-roadmap-v2 | 534.9 | 5% |
| refactor-roadmap-internalize-deps | 296.1 | 9% |
| review-tool-followups | 70.4 | 27% |
| scoped-test-per-task | 9927.2 | 0% |
| sdflow-init-hardening | 37.2 | 84% |
| sdflow-init-readwrite-paths | 282.2 | 5% |
| sdflow-rebrand | 253.0 | 17% |
| sdflow-retro | 279.6 | 64% |
| sdflow-retro-cleanup | 37.2 | 40% |
| sdflow-ship | 290.8 | 12% |
| shared-yaml-subset-parser | 626.8 | 18% |
| ship-gate-hardening | 180.8 | 18% |
| ship-gate-hardening-2 | 110.0 | 16% |
| simplify-workflow | 231.3 | 2% |
| streamline-workflow-automation | 0.0 | — |
| three-lens-decision-framework | 75.3 | 21% |
| tickets-parallel-frontier | 188.4 | 6% |
| workflow-metrics-loop | 119.2 | 66% |

## 聚合③ per-镜价值表（lens-metric 聚合，扫 archive）

| layer | lens | host | runner | site | 出现轮数 | Σfindings | Σ采纳 | Σ裁掉 | Σdefer | Σ独立 | 采纳率 | 独立率 | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| code-review | adversarial | claude | claude | guard-bypass | 1 | 2 | 2 | 0 | 0 | 1 | 100% | 50% | — |
| code-review | adversarial | claude | claude | none | 1 | 5 | 3 | 1 | 1 | 1 | 60% | 20% | — |
| code-review | adversarial | claude | claude | parse-edge+blast-radius | 1 | 1 | 0 | 0 | 1 | 0 | 0% | 0% | — |
| code-review | adversarial | claude | claude | refactor-honesty | 1 | 3 | 1 | 0 | 2 | 0 | 33% | 0% | — |
| code-review | adversarial | claude | claude | — | 35 | 191 | 140 | 16 | 35 | 100 | 73% | 52% | ≥10待复评 |
| code-review | adversarial | codex | codex | — | 2 | 2 | 2 | 0 | 0 | 0 | 100% | 0% | — |
| code-review | broad | claude | claude | native | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | broad | claude | claude | none | 1 | 1 | 1 | 0 | 0 | 1 | 100% | 100% | — |
| code-review | broad | claude | claude | step1 | 2 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | broad | claude | claude | — | 31 | 18 | 13 | 4 | 1 | 8 | 72% | 44% | ≥10待复评 |
| code-review | broad | claude | native | scope-drift | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | broad | codex | codex | — | 2 | 2 | 2 | 0 | 0 | 2 | 100% | 100% | — |
| code-review | domain | claude | claude | backend | 1 | 4 | 3 | 0 | 1 | 2 | 75% | 50% | — |
| code-review | domain | claude | claude | checklist | 1 | 2 | 0 | 1 | 1 | 0 | 0% | 0% | — |
| code-review | domain | claude | claude | none | 1 | 3 | 3 | 0 | 0 | 2 | 100% | 67% | — |
| code-review | domain | claude | claude | — | 33 | 77 | 54 | 14 | 9 | 25 | 70% | 32% | ≥10待复评 |
| code-review | domain | codex | codex | — | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | grounding | codex | codex | — | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | history | claude | claude | blame | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | history | claude | claude | git-blame | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | history | claude | claude | none | 1 | 2 | 1 | 1 | 0 | 0 | 50% | 0% | — |
| code-review | history | claude | claude | — | 34 | 21 | 12 | 8 | 1 | 6 | 57% | 29% | ≥10待复评 |
| code-review | history | codex | codex | — | 2 | 1 | 0 | 1 | 0 | 0 | 0% | 0% | — |
| code-review | outside-voice | claude | claude | code-voice | 5 | 7 | 4 | 1 | 2 | 3 | 57% | 43% | — |
| code-review | outside-voice | claude | claude | hr-tg | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | outside-voice | claude | codex | code-voice | 31 | 105 | 85 | 5 | 15 | 51 | 81% | 49% | ≥10待复评 |
| code-review | outside-voice | claude | codex | hr-tg | 16 | 54 | 41 | 4 | 10 | 23 | 75% | 43% | ≥10待复评 |
| code-review | outside-voice | claude | none | code-voice | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | outside-voice | claude | none | hr-tg | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| code-review | outside-voice | codex | claude | code-voice | 1 | 6 | 1 | 5 | 0 | 1 | 17% | 17% | — |
| code-review | outside-voice | codex | claude | hr-tg | 1 | 5 | 0 | 5 | 0 | 0 | 0% | 0% | — |
| code-review | outside-voice | codex | codex | code-voice | 1 | 2 | 2 | 0 | 0 | 0 | 100% | 0% | — |
| spec-review | adversarial | claude | claude | - | 1 | 8 | 8 | 0 | 0 | 4 | 100% | 50% | — |
| spec-review | adversarial | claude | claude | d1-t2 | 1 | 5 | 4 | 1 | 0 | 2 | 80% | 40% | — |
| spec-review | adversarial | claude | claude | d2-d3-scope | 1 | 4 | 4 | 0 | 0 | 2 | 100% | 50% | — |
| spec-review | adversarial | claude | claude | none | 2 | 30 | 28 | 2 | 0 | 9 | 93% | 30% | — |
| spec-review | adversarial | claude | claude | — | 39 | 378 | 350 | 20 | 8 | 176 | 93% | 47% | ≥10待复评 |
| spec-review | adversarial | codex | codex | — | 3 | 23 | 23 | 0 | 0 | 10 | 100% | 43% | — |
| spec-review | broad | claude | claude | - | 1 | 3 | 3 | 0 | 0 | 1 | 100% | 33% | — |
| spec-review | broad | claude | claude | autoplan-adapted | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | broad | claude | claude | none | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | broad | claude | claude | — | 39 | 415 | 361 | 35 | 19 | 172 | 87% | 41% | ≥10待复评 |
| spec-review | broad | claude | grill-substituted | design | 1 | 3 | 3 | 0 | 0 | 0 | 100% | 0% | — |
| spec-review | broad | codex | codex | — | 3 | 26 | 22 | 4 | 0 | 6 | 85% | 23% | — |
| spec-review | domain | claude | claude | backend | 1 | 5 | 5 | 0 | 0 | 1 | 100% | 20% | — |
| spec-review | domain | claude | claude | none | 2 | 12 | 12 | 0 | 0 | 3 | 100% | 25% | — |
| spec-review | domain | claude | claude | — | 17 | 82 | 79 | 1 | 2 | 35 | 96% | 43% | ≥10待复评 |
| spec-review | grounding | claude | claude | - | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | grounding | claude | claude | code-facts | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| spec-review | grounding | claude | claude | none | 2 | 3 | 3 | 0 | 0 | 0 | 100% | 0% | — |
| spec-review | grounding | claude | claude | — | 39 | 80 | 58 | 21 | 0 | 24 | 73% | 30% | ≥10待复评 |
| spec-review | grounding | codex | codex | — | 3 | 13 | 13 | 0 | 0 | 5 | 100% | 38% | — |
| spec-review | outside-voice | claude | claude | design-voice | 11 | 42 | 37 | 1 | 4 | 10 | 88% | 24% | ≥10待复评 |
| spec-review | outside-voice | claude | claude | hr-tg | 4 | 20 | 19 | 1 | 0 | 8 | 95% | 40% | — |
| spec-review | outside-voice | claude | codex | design-voice | 31 | 219 | 171 | 37 | 11 | 42 | 78% | 19% | ≥10待复评 |
| spec-review | outside-voice | claude | codex | hr-tg | 12 | 50 | 47 | 0 | 3 | 17 | 94% | 34% | ≥10待复评 |
| spec-review | outside-voice | codex | codex | design-voice | 2 | 6 | 4 | 2 | 0 | 2 | 67% | 33% | — |
| spec-review | outside-voice | codex | codex | hr-tg | 2 | 8 | 8 | 0 | 0 | 2 | 100% | 25% | — |
| spec-review | outside-voice | codex | none | design-voice | 1 | 0 | 0 | 0 | 0 | 0 | — | — | — |

> 无锚样本 39 份（旧格式,不纳入；份=报告文件数，每 change 常含 spec/code 两份，非 change 数；去重后 26 个 change）: 2026-07-02-issues-pool-batch-mgmt, 2026-07-02-issues-pool-batch-mgmt, 2026-07-02-streamline-workflow-automation, 2026-07-03-minimize-repo-footprint, 2026-07-03-minimize-repo-footprint, 2026-07-03-sdflow-rebrand, 2026-07-03-sdflow-rebrand, 2026-07-03-sdflow-ship, 2026-07-03-sdflow-ship, 2026-07-04-cross-model-outside-voice, 2026-07-04-cross-model-outside-voice, 2026-07-04-ship-gate-hardening, 2026-07-04-ship-gate-hardening, 2026-07-04-ship-gate-hardening-2, 2026-07-04-ship-gate-hardening-2, 2026-07-05-checkpoint-tag-single-source, 2026-07-05-checkpoint-tag-single-source, 2026-07-05-drop-per-dir-review-stub, 2026-07-05-drop-per-dir-review-stub, 2026-07-05-gate-anchor-line-scoped, 2026-07-05-gate-anchor-line-scoped, 2026-07-05-gate-checkpoint-hardening, 2026-07-05-gate-checkpoint-hardening, 2026-07-05-review-tool-followups, 2026-07-05-review-tool-followups, 2026-07-05-three-lens-decision-framework, 2026-07-05-three-lens-decision-framework, 2026-07-05-workflow-metrics-loop, 2026-07-16-add-codex-host-support, 2026-07-16-scoped-test-per-task, 2026-07-19-fix-mechanical-layer-silent-failures, 2026-07-31-align-sdflow-spec-with-openspec-schema, 2026-07-31-curb-rework-loop-cost, 2026-08-01-parallelize-grounding-mirror, 2026-08-02-harden-issues-read-write, 2026-08-04-issues-v2-single-file-model, 2026-08-05-simplify-workflow, 2026-08-07-fix-probe-scan-precision, 2026-08-09-absorb-gstack-autoplan
> 解析失败 0 份（编码/IO 错误，已跳过未计入聚合，不拖垮全局）: 无
> 独立率跨轮不保证同口径（dedup 合并尺度可能漂移），复评时校验最近几轮尺度一致。

