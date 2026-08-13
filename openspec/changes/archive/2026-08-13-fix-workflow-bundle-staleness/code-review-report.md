---
ship-gate:
  code_review: pass
  reviewed_sha: 2eb9b246b0bd5c0fe9d85c972942f31ec22b19d2
---

# code-review 报告 — fix-workflow-bundle-staleness

- **change**: `openspec/changes/fix-workflow-bundle-staleness/`（`skip_specs: true`）
- **日期**: 2026-08-13 · **host**: claude · **档位**: strong=opus / mid=sonnet / light=haiku · **effort**: high/medium/low
- **roster**: Step1 scope 审计（fresh 子代理）+ 领域镜（base CR-01~09，无命中域清单）+ 对抗镜 ×2（遗漏位点+引用断链 / init.py 安全性+测试覆盖）+ 历史镜（条件命中：rename）+ code-voice（codex gpt-5.6-sol）
- **TG 判定**: 命中 TG-28（devex）；HR-TG∩=∅

<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-28" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history,broad" -->

### 命中范围

栈: 无 backend/embedded/frontend（纯 Markdown + 1 处 Python）
清单: CR-01~09（base only，`code-checklists/domains/` 无命中栈）
Step1 scope 审计: 全部 tasks DONE（4.1/4.3/4.4 UNVERIFIABLE 因自报），2 条 SCOPE-CREEP（均裁掉，见下）

### 机械引用核

<!-- sdflow:ref-check v1 status="ran" pass="0" fail="2" uncheckable="0" -->

2 条 findings 均 `fail`（reason=quote-mismatch）——预期行为：findings 引用修复前的代码行，auto-fix 后行内容已变。两条 findings 已被采纳并修复，ref-check 在修复后盘面跑故 quote 不匹配。

### Findings（已采纳）

**[Important] F3 · _marker_schema 缺正向测试** | sdflow-init/scripts/init.py:636 | `"schema" not in data` 放宽校验后无"多键 marker 被接受"的正向测试用例 | 置信 85 | 命中镜: adversarial×2 + voice | **已修[impl-review-fix]**: 新增 `test_migration_accepts_marker_with_extra_keys` 测试用例

**[Important] F4 · fable5 TG 残留"26个"** | docs/sdflow-fable5/02-module-reference.md:173 | `26 个 TG 分七组` 且 D 组只列到 26，实际已有 TG-27/28 | 置信 90 | 命中镜: voice 独家 | **已修[impl-review-fix]**: 去数字 + D 组扩到 26-28

### 已裁掉（反静默压制）

- X1 · **SCOPE-CREEP-1** sdflow-guide.html 迁移超出声明范围 | Step1 scope 审计 | 裁掉理由：commit `85ccdbc` 是分支预提交（在 spec 生成前），非实现期越界；proposal/design 在此之后生成，未纳入声明是自然的
- X2 · **SCOPE-CREEP-2** init.py 校验放宽未回填文档 | Step1 scope 审计 | 裁掉理由：执行中 fold-in 的 bug fix（unblock 收尾门），已在 task4-verification.md 披露，文档回填属归档阶段责任
- X3 · F5 config.yaml 规则路径说明与 template 不一致 | voice | 裁掉理由：本仓是源仓，`openspec/workflow/` 确实存在（WORKFLOW-GUIDE.md），blurb 差异是给消费仓的提示，非本 change 范围
- X4 · F6 sdflow-guide.html Windows 路径不成立 | voice | 裁掉理由：proposal Non-Goals 明确不覆盖 Windows 路径，且 setup.sh Windows 逻辑非本 change 引入
- X5 · 领域镜 MEDIUM 旁注（init.py 调用点错误信息措辞）| domain | 裁掉理由：置信 40，纯旁注一致性，调用点逻辑未变
- X6 · 领域镜 LOW docstring 语气 | domain | 裁掉理由：置信 25，纯文档语气非功能缺陷
- X7 · 历史镜 LOW 记述改动歧义 | history | 裁掉理由：置信 1，改动是独立自举非交互失效

### 修复 / defer 台账

自动修 2 项[impl-review-fix]；自动选推荐 0 项；本轮新增待处理 0 项。

（无 defer 项——两条采纳均已当场修复。）

### 结论

- [x] 建议进 /sdflow-done
- [x] 本轮无新增待处理项

### 度量锚

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中2/低0" -->

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="code-voice" -->
