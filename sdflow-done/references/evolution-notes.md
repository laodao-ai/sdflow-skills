# 演进依据与历史取舍

> 仅在审计历史取舍时读取。本文不参与默认收尾执行。

## 1. v3 改进摘要（相对更早版本）

早期版本的归档步用手动 `mv` 搬迁 change 目录，漏掉了 delta 同步这一步，导致新能力永远进不了
`openspec/specs/`；也未做默认分支自动检测（容易误假设 `main`）、未强制 merge 缺省执行、未强制
verify 产出 `verify-report.md`、model 选择未按步骤性质区分档位。这些改进已直接固化进正文各步骤
（第三步「归档必须用 openspec archive CLI」、0.2 节默认分支检测、第五步 merge 缺省执行、第一步
verify-report.md 硬性可交付、模型选择章节按步定档位），此处仅作历史存档，不再是独立指令。

## 2. 首次执行踩坑速记

以下踩坑记录来自本 skill 首次实际执行时的复盘，条目均已提炼固化进正文对应步骤（手动归档漏 spec
同步 → 第三步「归档必须用 openspec archive CLI」；中文遗留主 spec → 第三步 fallback 「坑（手动同步
必看）」；复选框 stale → 0.3 节；blockquote 在 MUST 前 → 第三步「坑（手动同步必看）」；照搬旧 delta
→ 第三步 fallback b 步「以代码为准改写」；硬编码 main/--no-ff → 0.2 节 + 第五步），保留在此仅作历史
参考，正文不重复引用。
