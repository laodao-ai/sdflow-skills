# Verify Report — three-lens-decision-framework

- 日期：2026-07-05
- Change：`three-lens-decision-framework`（三镜决策框架焊进 workflow 源头，T46）
- 性质：纯 markdown workflow 规则 / skill 文本编辑 + spec delta（无代码 / 无 pytest）

## 结论：PASS

<!-- ship-gate: verify=PASS -->

六处落点措辞全部就位、跨落点口径一致（统一对齐 workflow.md G2「三面后果（系统/用户/开发循环）+ 主次判定」基准）、spec delta 与实现一致、`openspec validate` 通过。无核心缺口。

## 逐落点 / 逐需求核对表

| 需求 / 落点 | 代码出处（文件:行 / grep） | 状态 |
|---|---|---|
| ① BASE-12 三镜 + 主次 + TG-23 MUST | `spec-quality-base.md:31`：含「每个候选按三镜评估：系统镜…·用户镜…·开发循环镜…」+「理由（含一句主次判定…）」+「命中 TG-23（≥2 合理方案 / 非显然设计）时，三镜 + 主次判定 MUST 书面写入；琐碎决策…不强制（避样板税）」 | ✅ |
| ② G2 决策登记「三面后果 + 主次判定」，无残留「两方后果」 | `workflow.md:83`（G2）+ `:72`（设计门行）均为「选项+推荐+三面后果(系统/用户/开发循环)+主次判定」；`grep 两方后果` 全空 | ✅ |
| ③ code-review 记理由按三镜+主次；「有把握自动选」主动指令已清；T10 step① 含「按三镜+主次记理由」 | `SKILL.md:7/29/95` 记理由→按三镜+主次；`:95` T10 三级协议 ①「自动选并按三镜+主次记理由入报告」；`:142-143` 台账补「(三镜+主次)」；`grep 有把握` 仅剩 `:95` 元引用（「替换旧『有把握自动选』」）与 MUST NOT 反面钉子，无「≥2 方案有把握自动选」主动指令 | ✅ |
| ④ spec-review 三面后果+主次；事实核验 carve-out（不强制三镜）；无「两方后果/各自后果」 | `SKILL.md:8`「事实核验：待核验证据+风险+默认处理，不强制三镜」；`:77`（TENSION）+`:89`（ASCII 格式块 Q1）均为「三面后果+主次判定」；`grep 各自后果/两方后果` 全空 | ✅ |
| ⑤ ship 台账「理由(三镜+主次)」与 code-review 一致；T10 step① 含「按三镜+主次记理由」 | `SKILL.md:23` T10 三级 ①「自动选并按三镜+主次记理由」；台账行「T10复核: <方案> \| 对抗镜结论… \| <理由(三镜+主次)>」与 code-review:143 同串 | ✅ |
| ⑥ BASE-18 fold-vs-defer + 防吸积 AND 门（同 capability∧高耦合∧低增量），无「任一即fold」宽版 | `spec-quality-base.md:42`：「防吸积 AND 门 =「同 capability ∧ 高耦合 ∧ 低增量」三者皆满足才真 fold…任一不满足 → defer 另开」；两级判定 + 三镜/开发循环镜主导，与 BASE-10 YAGNI 不冲突（补充非推翻） | ✅ |
| spec delta：tension 无「有把握则自动裁决」残留、与 T10 一致 | `spec.md:27`：tension 需求用「T10 三级协议自动裁决（有客观判据自动裁 / 无则对抗镜复核 / 复核不过 defer）」并 MUST NOT 以「有把握」为唯一依据；与三处 skill 的 T10 一致（design.md 早期 F1 拟用中性词，实现按 impl-review-fix F1/CV2 对齐到 T10——符合 verify「与 T10 一致」判据） | ✅ |
| spec delta：「≥2 方案」与「事实核验」分列 | `spec.md:7`：书面三镜门覆盖命中 TG-23（≥2 合理方案）；「核验不了的事实」（Q2）明列「不属 TG-23，走待核验证据/风险/默认处理，不强制三镜」〔CV4〕 | ✅ |
| spec delta：fold-vs-defer scenario 与 BASE-18 AND 门一致 | `spec.md:21-23` scenario：「防吸积 AND 门（同 capability ∧ 高耦合 ∧ 低增量，三者皆满足）才 fold…任一不满足则 defer」与 BASE-18:42 同口径 | ✅ |
| `openspec validate three-lens-decision-framework` | 输出 `Change 'three-lens-decision-framework' is valid`，exit=0 | ✅ |

## 缺口清单

- 核心 FAIL：无。
- Minor / deferred（不阻断，PASS）：
  - F5 spec-review ASCII 决策框视觉细化 → 已 defer 至 T50（tasks.md 未列为本 change 动作，cosmetic）。
  - docs/ 可视化镜像刷新〔F3〕、trigger-catalog「≥2 方案」判例〔X2〕→ 已按 tasks.md 7.5 defer 入 todolist（非权威源 / 可选优化）。
  - 部署纪律（tasks 7.3 `setup.sh` 让全局 canonical 跟上）为运行时动作，非源文件措辞项，不影响本次源核验结论。

PASS
