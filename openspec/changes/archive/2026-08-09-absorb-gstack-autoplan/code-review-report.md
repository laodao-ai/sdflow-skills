---
ship-gate:
  code_review: pass
  reviewed_sha: 35cbe388b816f0e5bc37953c4f0b2066f7050e01
---

## code-review 报告 — absorb-gstack-autoplan

### 命中范围

栈: markdown workflow 资产 + Python 工具（无匹配 code-checklists/domains/ 领域清单）
清单: CR-01~09 (base only)
TG 命中: TG-18(test), TG-28(devex, 本 change 新增)
HR-TG: none（TG-28 不在 HR-TG 子集）
Step1 自持 scope 审计: 24/24 task DONE，零 scope-drift

<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history,broad" -->

trivial_shape: NOT_EXEMPT（logic-line:hack/sync_principles.py）→ 照常 fan-out

### Findings（置信 ≥80）

**[Important] F1 — 孤儿 spec 文件 outside-voice-reuse-guard** | `openspec/specs/outside-voice-reuse-guard/spec.md` | INDEX 已删行但 spec 目录未删,退役不完整 | 置信 90 | **已修[impl-review-fix]** 删除目录

**[Important] F2 — task-log-template 错误引用编排器** | `sdflow-roadmap/references/task-log-template.md:64` + 两个 fixture | 把 roadmap review 产出方描述为 `sdflow-spec-review 或 sdflow-code-review`，但 roadmap review 现为自持双镜 | 置信 85 | **已修[impl-review-fix]** 改为正确描述

**[Important] V2 — roadmap SKILL 裸 eval 缺清脏保护** | `sdflow-roadmap/SKILL.md:507` | 无 unset 步骤,可能复用上轮残留 SDFLOW_* 环境假绿 | 置信 80 | **defer→todolist**（既有债务,非本 change 引入,roadmap SKILL 的 tier-resolution 未被本 change 的 tasks.md 要求改写为完整保护版;roadmap 低频场景,risk 可控）

### 已裁掉（反静默压制）

| # | 来源 | 原始 | 理由 |
|---|---|---|---|
| X1 | 领域 F2 | 注释语义漂移 anchor_lint.py:556 | 置信 55 <80 |
| X2 | Voice V1 | host=unknown 路径自相矛盾 | 验证后不成立：tier-resolution 的 host=unknown → fail-loud 硬停在到达 fan-out 之前,SKILL.md:195 的"不会走到本段"是正确的 |
| X3 | Voice V3 | devex 未在 SKILL 显式枚举 | 不成立：领域镜派发由 TG→domains 映射驱动,不硬编码 |
| X4 | Voice V4 | sync_principles marker 缺失 fallback | implementer 已修(markers 在源文件中),测试验证幂等性 |
| X5 | Voice V5 | test order dependency | 成立但 Minor,defer→todolist |
| X6 | Voice V6 | criteria-mechanization-tracker.md 残留 | 成立 Minor,defer→todolist |

### 修复 / defer 台账

自动修 2 项[impl-review-fix]；defer 3 项 → todolist（V2 roadmap tier-resolution / V5 测试隔离 / V6 tracker 更新）

### outside-voice

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="6" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="code-voice" -->

code-voice 跨模型（runner=codex≠host=claude）6 条 findings：2 采信修复/defer,4 裁掉（验证不成立或 Minor）。

### 结论

- [x] 建议进 /sdflow-done
- [x] defer 残差已入 todolist（hand-off 会引用）
