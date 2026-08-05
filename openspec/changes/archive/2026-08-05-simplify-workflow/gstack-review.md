<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- 侧信道佐证：autoplan 经 Skill 原生机制执行，CEO Phase 1 + Eng Phase 3 双相位完成，
     Claude subagent + Codex 双声道均真实调用（codex exec 前台阻塞返回） -->

# autoplan 广审结果 — simplify-workflow

## CEO Phase (Strategy & Scope)

### Claude subagent findings

1. **[严重] Sunset 治理机制被绕过** — decision-memo D2 直接删除观察窗，未跑三档实测（采用率/质量/成本）。sdflow-spec 上线后已有 15 个 change 落地（93% 带 decision-memo），数据大概率支持删除，但从未检查。审计空白。
2. **[高] 自动触发无机械门** — 删除 `disable-model-invocation: true` 后，模型误判自然语言信号会创建真实分支+change 目录，HARD-GATE 在副作用之后才出现。且会推给 15 个下游项目。
3. **[中] impl-pipeline 默认翻转外推** — 单仓试点（本仓 6 个 change）外推到 15 个未知下游项目，无逃生口发现机制。
4. **[中] embedded-test-sop 在途 RUN_SOP 未处置** — 合并时若有 change 卡在 RUN_SOP，无迁移路径。
5. **[低] 机会成本** — retro 报告显示 11 面镜已达"≥10 轮需复评"阈值未处理，是更大的成本中心。

### Codex findings

1. 不是"一条线性路径" — explore 仍条件性，Phase B 有人类决策，FF-0 可 halt。
2. 删除观察窗未生成证据 — `git revert` 恢复代码但无法撤消下游更新/默认值/用户习惯。
3. Wayfinder 覆盖是断言非证明 — explore 跨 session ≠ wayfinder 的持久化决策追踪。
4. tickets 默认翻转是无定价迁移 — 无滚动分组/通知/遥测/逃生口发现/成功指标。
5. "低频"不是嵌入式测试 SOP 的正确删除依据 — 罕见的嵌入式变更正是缺 SOP 代价最高的时候。
6. **[关键] 与自身治理契约冲突** — spec-authoring SA-01 要求 `disable-model-invocation: true`，SA-14 以此为前提定义四入口规则。delta spec 只修改 spec-workflow，未覆盖 spec-authoring。
7. 验证计划证明了删除而非结果 — 无端到端场景测试自然语言触发歧义、下游默认路由等。

### CEO Consensus Table

| 维度 | Claude | Codex | 共识 |
|------|--------|-------|------|
| 1. Sunset 机制应先评估？ | 严重 | 阻断 | **CONFIRMED** |
| 2. 自动触发风险？ | 高 | 高 | **CONFIRMED** |
| 3. impl-pipeline 翻转风险？ | 中 | 阻断 | **CONFIRMED** |
| 4. 嵌入式 SOP 删除合理？ | 中（在途处置缺） | 中（删除依据质疑） | **DISAGREE** |
| 5. Wayfinder 覆盖充分？ | 未单独审 | 断言非证明 | N/A（单声） |
| 6. Spec 契约一致性？ | 未单独审 | 阻断 | N/A（单声） |

## Eng Phase (Architecture & Code)

### Claude subagent findings

1. **[Critical] F1** — `openspec/workflow/` 本地 pin（48 文件）未被计划触及，本仓自身会继续用旧规则，简化对本仓不生效。
2. **[Critical] F2** — 删 `disable-model-invocation` 违反已生效的 `spec-authoring` SA-01/SA-14，delta spec 未覆盖。
3. **[High] F3** — `sdflow-init/tests/test_grill_handoff.py`（防 grill 被静默跳过的回归门）会红，计划未提及处置。
4. **[High] F4** — design.md/tasks.md 两处把 `impl_route.py` 路径写错（应为 `sdflow-implement/scripts/`）。
5. **[Medium] F5** — impl-pipeline 缺省翻转实为 9 处硬编码 + 1 处对称显示逻辑，描述为"单点改动"。
6. **[Medium] F6** — "HARD-GATE 兜底"表述不准确——副作用发生在 HARD-GATE 之前。
7. **[Low] F7** — ship_gate.py "三个入口"计数需同步改成"两个"。

### Codex findings

1. **[阻断]** delta spec 未覆盖 spec-authoring SA-01/SA-14/SA-11/SA-15。
2. **[阻断]** Task 2 指向不存在的路径 `sdflow-ship/scripts/impl_route.py`。
3. **[阻断]** impl_route.py 有 8 个字面 `return "superpowers"` 需分语义处理。
4. **[阻断]** config.yaml wayfinder 规则遗漏（L38/48）。
5. **[阻断]** 48 文件本地 pin 完全未纳入任务。
6. **[确认]** test_grill_handoff.py 会失败，任务未列出。
7. **[新增]** 受影响测试远多于任务所列（列出 10+ 个文件）。
8. **[新增]** Task 6 残留 grep 范围不可能通过（AGENTS.md/README/spec-authoring/config.yaml 等都会命中）。
9. **[新增]** RUN_SOP 删除后应补回归测试证明状态机无空洞。

### Eng Consensus Table

| 维度 | Claude | Codex | 共识 |
|------|--------|-------|------|
| 1. 架构完整（本地 pin）？ | Critical | 阻断 | **CONFIRMED** |
| 2. Spec 一致性？ | Critical | 阻断 | **CONFIRMED** |
| 3. 受影响测试完备？ | High | 阻断 | **CONFIRMED** |
| 4. 文件路径正确？ | High | 阻断 | **CONFIRMED** |
| 5. impl 翻转复杂度？ | Medium | 阻断 | **CONFIRMED** |
| 6. 残留扫描可行？ | 未单独审 | 新增 | N/A（单声） |

## Grounding Mirror (Code Fact Verification)

1. **[高] design.md:85** — `impl_route.py` 路径错误（`sdflow-ship/scripts/` → 实际 `sdflow-implement/scripts/`）
2. **[高] impl_route.py:177-206** — 缺省值尚未修改（仍为 'superpowers'）— 这是 pre-impl 状态，符合预期
3. **[中]** embedded-test-sop 目录空但仍存在（SKILL.md 已删）
4-6. **[信息]** 其余待做项（disable-model-invocation/RUN_SOP/prompt files）均已定位，代码事实核验通过

## autoplan 自动决策

[自动决策] D1 — autoplan CEO premises：前提（减认知负担 → 合并双轨）合理，但执行细节有缺口。按 P6(bias toward action) 接受前提。
[自动决策] D2 — 跳过 Design Review（无 UI scope）。
[自动决策] D3 — 跳过 DX Review（关键词为内部工具维护讨论，非面向外部开发者的 API/SDK）。

[gstack-amendment]
