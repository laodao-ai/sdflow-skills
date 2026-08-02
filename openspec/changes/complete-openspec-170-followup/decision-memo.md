---
schema_version: 1
change: complete-openspec-170-followup
branch: feat/complete-openspec-170-followup
generated_at: 2026-08-02T07:00:00Z
decision_hash: fce7d8c2a12a
---

# 决策纪要 · complete-openspec-170-followup

## 目标态

openspec 1.7.0 跟进收尾：prevention 层扩到 apply/archive + archive 现代化 + amendment 双向 coherence。

## 拍板决策

- **D1 P2+P3+Q2 合为一个 change** — 依据：三块改文件集不相交（P2 触 config、P3 触 sdflow-done、Q2 触 sdflow-spec-review），同属 1.7.0 跟进收尾，改动量小；人 2026-08-02 明确指示
- **D2 Q2 采纳（amendment 双向 coherence）** — 依据：评审最常见 finding 根因在 proposal 而非 design/specs，当前措辞只许改 design/specs；人 2026-08-02 明确指示
- **D3 Q2 借 `/opsx:update` 原则但不直接调** — 依据：C1（`reviewed_sha` 时序冲突）；修法 = 把 `sdflow-spec-review/SKILL.md:298` 的措辞从「据此更新 design/specs」扩到四件套任意，标 `[spec-review-amendment]`，引用 `/opsx:update` 的双向原则
- **D4 archive guidance 写两条、apply guidance 暂不写** — 依据：roadmap B1 列出的两条硬约束都只关 archive 面，apply 面未识别到需要下沉的约束；不为对称而凑空条目
- **D5 C2 `## Purpose` 规则加到 `rules.specs`** — 依据：1.7.0 archive 抬 Purpose 进主 spec，缺则写占位符 + `validate --strict` 警告「too brief」（CHANGELOG #1431）
- **D6 D2 fallback 阶梯瘦身而非整删** — 依据：C3（中文遗留格式触发条件仍存在）；瘦身 = 去掉 REMOVED abort 相关 workaround 描述，保留核心 fallback 路径

## 承重约束

- **C1 Q2 不直接调 `/opsx:update`** — 验证方式：读 sdflow-spec-review/SKILL.md 的 ADR-7(b) 时序契约；**证据锚**：`sdflow-spec-review/SKILL.md:324-330`（二次修订必须先单独 checkpoint 再回写 `reviewed_sha`，`/opsx:update` 不知道此约束）
- **C2 `operations.{apply,archive}.guidance` 通道有效** — 验证方式：本仓 config.yaml 临时加 `operations` 段后实测 `openspec instructions archive|apply --json`；**证据锚**：`operationGuidance: ['TEST: archive guidance line 1']` 实际返回确认透传
- **C3 fallback 阶梯不能整删** — 验证方式：读 `sdflow-done/SKILL.md:378-379`，中文遗留格式导致的 Validation error 仍存在；1.7.0 只修了 REMOVED abort 这一个触发条件；**证据锚**：`sdflow-done/SKILL.md:378-379` + roadmap D2 原文

## 接受的边角

- apply guidance 暂空 — 概率/影响：apply 面走官方 `/opsx:apply` 时无约束注入，但当前 apply 面硬约束本就不在 sdflow-done 而在 sdflow-implement（与 config 通道无关）；完美成本：凑条目反而增加维护面；**接受**
- Q2 amendment 写回无机械门验证四件套 coherence — 概率：每次评审；影响：amendment 不 coherent 由设计门人工兜底（HARD-GATE 前人读全部四件套）；完美成本：实现 coherence checker 超出本 change scope；**接受**

## 三镜代价

本次无 TG-23 命中
