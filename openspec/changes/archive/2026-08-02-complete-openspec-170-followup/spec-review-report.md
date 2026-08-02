---
ship-gate:
  design_approved: true
  reviewed_sha: 70a9d7e7c49be78de6d91ac8e7c8354dbbf291af
---

# Spec Review Report — complete-openspec-170-followup

## 评审概要

- **Change**: `openspec/changes/complete-openspec-170-followup/`
- **评审模式**: sdflow-spec-review 全流程（autoplan 原生 + 并行多镜 + outside-voice 同族降级）
- **命中 TG**: 无（纯 config/指令层改动）
- **镜头**: 对抗镜 ×2（sonnet）+ 接地镜 ×1（haiku）+ autoplan 广审（原生）+ design outside-voice 同族降级

<!-- sdflow:hr-tg v1 hit="none" declared="" evidence="" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="native" -->

---

## Findings

### F-SR1 [HIGH] Spec Scenario 2 承诺了 `sdflow-init update` 做不到的事

**问题**: `spec.md` 的 `archive-guidance-injection` Requirement Scenario 2 写道 "WHEN `sdflow-init update` runs on a downstream project THEN ... the downstream `openspec/config.yaml` SHALL be updated accordingly"。`proposal.md` Success Metric 同样声称 "下游项目 `sdflow-init update` 后获得 `operations` 段"。

但 `sdflow-init update` 的实际行为是**不动 config.yaml**（`init.py:574-578` 的 `handle_config` 在 `mode=="update"` 时只改 `schema:` 单键；`init.py:749-784` 的 `lint_config` 白名单不含 `operations`）。`SKILL.md:173` 也明确记载 "update 不动 config.yaml"。

template 里加 `operations` 段只对**新项目 init**（从模版生成全新 config）有效。已铺设项目的 `sdflow-init update` 产出的"下一步"提示是给人/AI 手动合并的，不是脚本自动行为。

**命中镜**: design-voice, 对抗镜 #1 (obs), 对抗镜 #2 — 三镜独立收敛
**置信度**: 高（init.py 源码实证）
**严重度**: 高（spec 承诺不可达 = 验收必假绿）
**建议**: Scenario 2 措辞改为 "WHEN a new project runs `sdflow-init` (init mode) THEN ..."；对已铺设项目补一句 "已有项目需按 `sdflow-init update` 打印的提示手动合并 `operations` 段"。Success Metric 同步修正。

---

### F-SR2 [HIGH] `fallback-ladder-slim` 目标文字不存在 → 恒真验收锚

**问题**: design.md 改动 5、tasks.md Task 2.2、spec.md `fallback-ladder-slim` Requirement 都要求从 `sdflow-done/SKILL.md:378-380` "去掉 REMOVED abort 的相关说明"。

但 `sdflow-done/SKILL.md` 通篇 **grep -ni "removed" → 零命中**。378-380 行只提中文遗留格式触发条件，从未提及 REMOVED abort。roadmap D2 描述的是 **CLI 行为**修复（"1.7.0 修掉了 REMOVED-abort"），不是 SKILL.md 文本中存在这段话。

Task 2.2 的验收标准 "读 fallback 段确认不再提及 REMOVED abort" 在当前文本上**恒真**——这是一个 vacuous anchor（参见 `恒真锚有两种成因.md`），实现者要么空转勾完、要么为了凑改动误删仍有效的 fallback 描述。

**命中镜**: 对抗镜 #1, 对抗镜 #2 — 两镜独立收敛
**置信度**: 高（grep 实证 + git log --follow 历史实证）
**严重度**: 高（vacuous anchor → verify 假绿或误删）
**建议**: 砍掉 Task 2.2 / `fallback-ladder-slim` Requirement。1.7.0 修复的是 CLI 行为，SKILL.md 无需改动。若要保留记录，改为陈述性说明 "确认现有 fallback 描述未提及 REMOVED-abort（已核实无需改动）"。

---

### F-SR3 [HIGH] `--json` 模式下成功/失败的 JSON schema 完全不同，design 只覆盖成功路径

**问题**: design.md 改动 4 只说 "改判断逻辑为读 JSON 输出的 `warnings` 数组"。但 CLI 1.7.0 源码实证：

- **成功路径**: `{"archive": {..., "warnings": [...]}, "root": {...}}` — exit 0
- **失败路径**（中文遗留格式 Validation error）: `{"archive": null, "status": [{"code": "archive_validation_failed", ...}]}` — exit 1，**无 `warnings` 字段**
- **成功无警告**: `{"archive": {...}, "root": {...}}` — 无 `warnings` 键（键缺省 vs 空数组）

旧判据（"archived as ..." 文本匹配）在 `--json` 模式下**不会出现在 stdout**（被 `if (!json)` 守卫）。design 未重写 SKILL.md:376-380 的成功/失败/fallback 判据为基于 JSON 结构的版本。

**命中镜**: 对抗镜 #1, 对抗镜 #2, design-voice — 三镜独立收敛
**置信度**: 高（CLI archive.js 源码实证 + 本机实测）
**严重度**: 高（fallback 触发判据失效 = 验证失败被静默当成功）
**建议**: design 改动 4 扩写为完整重写 376-380 判据：
- `archive` 非 null → 成功，读 `warnings[]`（如存在）展示
- `archive` 为 null 或 exit ≠ 0 → 走 fallback
- 显式列出两种 JSON 形状

---

### F-SR4 [MEDIUM] skip_specs 状态检测在 archive prompt 结构中位置未定

**问题**: design 改动 6 要求 archive 子代理 "先读 `openspec status --change ... --json`"，但未指定在 prompt 的什么位置插入、如何与现有 "先试 CLI → 走 fallback" 流程衔接。对 skipped 态 change，archive CLI 本身正常（CLI 已知 skip_specs），但现有 prompt 第 3 节核对要求报告 "同步了哪些主 specs"——skipped 态下无同步，子代理可能困惑。

**命中镜**: design-voice
**置信度**: 中
**严重度**: 中（可在实现期解决但 design 应给方向）
**建议**: design 建议在 prompt 里 `## 1. 先试 CLI` 之前加 `## 0. 前置检查` 段；skipped 态的最终报告写 "skip_specs: 无 delta 同步，正常"。

---

### F-SR5 [MEDIUM] Q2 amendment 扩到四件套后缺 termination 纪律

**问题**: `sdflow-spec-review/SKILL.md:298` 扩展后只有 "据此更新四件套中需要修订的产物...标 [spec-review-amendment]"。没有规定：做完一趟后是否需要检查其余产物是否因此产生新矛盾、"只做一趟" 还是 "迭代到不动点"。design 自己举的例子（"根因在 proposal 的 Non-Goals 划错了"）是高频场景。

**命中镜**: 对抗镜 #2
**置信度**: 中
**严重度**: 中（decision-memo 已接受此边角，但操作边界不清）
**建议**: 补一句 termination 纪律："amendment 只做一趟；一趟内发现新的跨产物矛盾记入决策登记区交人工二次评审，不在本轮自行迭代"。

---

### F-SR6 [MEDIUM] `--json` 输出稳定性假设未显式声明

**问题**: P3 从文本解析切到 `archive --json` 读 `warnings[]`。CLI 未声明该 JSON schema 是否为稳定 API。JSON 严格优于文本匹配，但应在 design 中注明所依赖的字段名，以便 CLI 升级时定位影响面。

**命中镜**: CEO review (autoplan)
**置信度**: 中
**严重度**: 中（文档缺口，不阻塞）
**建议**: design 改动 4 加一句注明依赖的 JSON 字段（`archive`, `warnings`, `status`）。

---

## 决策登记区

### 自动决策

- **[自动决策] D1**: autoplan scope 正确，P2+P3+Q2 不拆不合 — P1/P2 principle，CEO 双声 6/6 CONFIRMED
- **[自动决策] D2**: F-SR6 文档缺口不阻塞，补一句即可 — P6 principle
- **[自动决策] D3**: 中文遗留 fallback 无 sunset 声明 — 文档缺口，建议 Non-Goals 加一句迁移立场

### 需拍板

- **[需拍板] Q1**: F-SR1 — Spec Scenario 2 措辞修正 vs 扩展 `sdflow-init update` 机制支持 `operations` 键合并。**推荐**：修正措辞（代价低、目标态明确；扩展 update 机制超出本 change scope）
- **[需拍板] Q2**: F-SR2 — 砍掉 Task 2.2 / `fallback-ladder-slim` Requirement vs 改为陈述性确认。**推荐**：砍掉（恒真验收锚无实质价值，保留增加 verify 假绿风险）
- **[需拍板] Q3**: F-SR3 — design 改动 4 是否扩写为完整重写 376-380 判据。**推荐**：扩写（三镜收敛的核心 finding，不扩写 = fallback 触发判据在 JSON 模式下失效）
- **[需拍板] Q4**: F-SR4 — skip_specs 前置检查结构是否在 design 里给定方向。**推荐**：给方向（design 级指定位置，实现者不必猜）
- **[需拍板] Q5**: F-SR5 — Q2 amendment 是否补 termination 纪律。**推荐**：补一句（成本极低，防操作歧义）

### 已裁掉

- **[已裁掉] X1**: 对抗镜 #1 观察 "P2 guidance 对 sdflow-done 主路径是死重复" — 裁掉理由：proposal Why 已正确陈述目的是覆盖 `/opsx:archive` 路径，不是增强 sdflow-done 路径。这是预期行为，不是缺陷
- **[已裁掉] X2**: 对抗镜 #1 观察 "Task 1.3 diff 确认对齐含糊" — 裁掉理由：实现期自然会收窄比对范围到新增的 `operations` 段和 `## Purpose` 规则。措辞虽不精确但不会导致错误实现
- **[已裁掉] X3**: design-voice F2 "lint_config 不识别 operations 键" — 裁掉理由：当前 lint_config 不做顶层键白名单检测（不拒绝未知键），无即时失败风险；未来如加白名单是独立 change 的职责。超出本 change scope

---

## 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="1" sev="致0/高3/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="claude" site="design-voice" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="0" sev="致0/高2/中0/低0" -->

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="claude" reason_code="exec-error" findings="4" truncated="false" -->

<!-- sdflow:declared-sites v1 declared="design-voice" -->

---

## 收敛建议

F-SR1/F-SR2/F-SR3 是三个高置信高严重度 finding，均有多镜收敛 + 源码实证。建议设计门前**先做 amendment 修正这三条**，然后进 HARD-GATE 拍板。

是否建议进设计 HARD-GATE：**是**，修正三条高危 finding 后即可拍板。

## 拍板记录

设计门已拍板批准，日期 2026-08-02。Q1-Q5 全部接受推荐方案。
