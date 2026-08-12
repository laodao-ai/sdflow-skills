# 演进依据与历史取舍

> 仅在审计历史取舍时读取。本文不参与默认阶段三执行。

## 1. 度量锚曾被系统性跳过的诊断（B25）

2026-08-07 ~ 08-12 六轮归档 `code-review-report.md`（`metrics.enabled=true` 全程未变）100% 缺
`sdflow:lens-metric` 锚。诊断（详见 `impl-reports/task5-skill-adaptation.md`）为「本步被系统性
跳过，而非 emitter 调用失败」：独立冒烟测试证实 `lens_metric_emit.py` 本身工作正常（合法输入
exit 0 正确产锚、非法输入 exit 1 正确拒收）；其中一份报告甚至已写出「### 度量锚」标题 +
「metrics.enabled=true」说明，却仍未真正调用脚本、也未运行锚行自检（若真跑过自检，脚本会因缺
lens-metric 锚判违规、阻塞该步——而报告照常归档说明自检同样被跳过）。

结论已固化进正文：`ship_gate.py` 加了 B25 锚存在门（外部机械兜底）；SKILL 正文把「度量锚落锚 +
锚行自检」拆成独立编号步骤，不再是「写报告」这句散文里可以顺带略过的细节。

## 2. 跨模型 finding 豁免条款随数值置信滤一并废止

旧版存在「被 `anchor_lint` 合法组合矩阵判定为『跨模型』的 finding，跳过数值置信滤直通对抗裁决」
的豁免条款。数值置信滤（旧版按 0-100 自报置信设门槛）本身已被机械引用核 + 二元裁决（DD4/adr/0041）
取代，门槛概念消失，「豁免于该门槛」这一说法随之失去意义。当前行为：跨模型 finding 与同族 finding
走同一条二元裁决，无特殊通道。`host-adaptive-execution` 单一源矩阵本身未删除，继续供 anchor 校验 /
declared-sites 完整性等其余用途引用。
