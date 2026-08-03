---
ship-gate:
  code_review: pass
  reviewed_sha: aee79fe00570148d1eb4b48081cd50fa2b54ef29
---

# code-review 报告 — fix-voice-quoting-and-mirror-vocab

## 命中范围

栈: Python 脚本 + Markdown SKILL/spec
清单: CR-01~09（base）
gstack/review: scope-drift 无（全部改动在 T164/T148 scope 内），计划完成度无缺口

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="TG-17" declared="TG-17,TG-18" evidence="T164 路径引号修复涉及 shell 命令注入面（TG-17）" -->

## 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history" -->

（本 change 无命中领域清单（无 DB/HTTP），领域镜 = 0。实际 fan-out：对抗镜 ×2 + 历史镜 ×1 + code-voice fallback ×1。）

## outside-voice

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="claude" reason_code="exec-error" findings="2" truncated="false" -->

code-voice 因 preflight 失败回落同族 fallback，2 条 findings（F1 中等→自动修、F2 低→已裁掉）。

<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->

HR-TG hit TG-17 但本轮未单开 hr-tg voice（F1 自动修范围仅 bookkeeping，无需领域专属第二意见）。

<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="none" reason_code="fallback-unavailable" findings="0" truncated="false" -->

## Findings（置信 ≥80）

### F1 [Important] T164/T148 todolist 未标 DONE + roadmap P2 未闭合

**命中镜**：对抗镜1（独家）
**置信度**：90

`openspec/issues/todolist/2026-07-todolist.md` T164(:52) 和 T148(:309) 仍 `"status":"OPEN"`。按项目惯例（[[completed-todo-mark-done-not-sweep]]），工作已落地的 todo 应当场标 DONE。

**处置**：已自动修 [impl-review-fix]——T164/T148 status 改 DONE，change 字段改 `fix-voice-quoting-and-mirror-vocab`。

### F2 [Minor] ADR-0023 仍写 3-token 词表

**命中镜**：对抗镜1
**置信度**：85

`openspec/adr/0023-fanout-capability-probe-mechanical-floor.md:26` 仍写 `lens ∈ {domain, adversarial, grounding}`（3 token），而 `_FANOUT_MIRRORS` 已扩至 4 token。ADR 非脚本消费，无运行时影响。

**处置**：defer → todolist（ADR 改动不在本 change scope，按通则③不加宽）。

### F3 [Minor] 引号改动 7 处仅 2 处有 golden 反漂移测试

**命中镜**：对抗镜2 + code-voice（2 镜收敛）
**置信度**：85

`hack/tests/test_async_branch_parity.py` 的 golden 常量只覆盖 dispatch + cleanup 两条命令行的引号形态，其余 5 处（mkdir、exec+sidecar、collect、await、reconcile/render-prompt）无 golden 锁。覆盖面缺口非本次引入（改前也无覆盖）。

**处置**：defer → todolist。

## 已裁掉（反静默压制）

- **X1**（对抗镜2）`<site>`/`<s>` 未加引号 → 裁掉。置信 60（<80）。理由：design.md 显式声明「`<T>` 和 `<site>` 不需要（clamped integer / controlled enum）」。
- **X2**（code-voice）分支含不相关 bookkeeping 提交 → 裁掉。置信 70（<80）。理由：7c0b904 是 base 提交，先于本 change 开始，非 scope drift。

## 修复 / defer 台账

- 自动修 1 项 [impl-review-fix]：T164/T148 todolist status → DONE
- defer 2 项 → todolist（F2 ADR 词表漂移 + F3 golden 测试覆盖面缺口）

## 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="3" 采纳="1" 裁掉="0" defer="2" 独立="1" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="claude" site="code-voice" findings="1" 采纳="0" 裁掉="0" defer="1" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="none" site="hr-tg" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->

> 本轮最高价值 = 对抗镜（3 findings，1 采纳 2 defer，独家发现 T164/T148 todolist 未标 DONE）。
> 历史镜 0 findings。code-voice 1 条与对抗镜收敛（golden 测试覆盖面缺口）。
> 保留信任边界声明：findings 数与合并池实收数的数值一致性是主 session 信任边界，非机械可验。

## 结论

☑ 建议进 /sdflow-done
☑ defer 残差已记录（F2/F3 待异步处理）
