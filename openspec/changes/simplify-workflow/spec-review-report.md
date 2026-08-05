---
ship-gate:
  design_approved: true
  reviewed_sha: efba4a849658a4bd432727970f3e0b47cff89985
---

# Spec Review Report — simplify-workflow

评审层：spec-review | 宿主：claude | 镜头：autoplan(CEO+Eng) + grounding + adversarial×2 + outside-voice(design)

<!-- sdflow:step1-broad-review v1 mode="native" -->

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="none" declared="" evidence="无领域 TG 命中，无栈级/数据/接口/行为/规模/质量 TG" -->

---

## 一、Findings（按严重度排列，去重后）

### Critical

**C1 — Spec 跨能力一致性缺口：delta spec 未覆盖 spec-authoring 和 impl-orchestration**

delta spec 只修改 `spec-workflow`，但：
- `spec-authoring` SA-01（`spec.md:8`）明文要求 `skill SHALL 声明 disable-model-invocation: true`——Task 3 删除的正是这个声明
- `spec-authoring` SA-14（`spec.md:340-347`）以 `disable-model-invocation` 为前提定义四入口选择规则
- `impl-orchestration` spec（`spec.md:8/12`）明定"键缺失或值不识别 → superpowers"——Task 2 翻转的正是这个缺省

归档后这些主 spec 会继续断言被代码推翻的不变量。

- 置信度：高 | 命中镜：CEO Codex · Eng Claude · Eng Codex · Voice（4 个独立声音收敛）
- **建议**：specs/ 目录新增 `spec-authoring/` 和 `impl-orchestration/` 的 delta spec；Capabilities 段的 Modified Capabilities 把两者加进去

**C2 — 本地 pin `openspec/workflow/`（48 文件）未纳入任务，本仓自身简化不生效**

`resolve-workflow.sh` 检测到本地 `workflow.md` + `spec-checklists/` + `code-checklists/` 三者都在，判定本地 pin → 直接返回本地路径，不看全局 canonical。tasks.md Task 4/5/6 只改权威源 `sdflow-init/assets/workflow/`，从未提及 `openspec/workflow/`。proposal 的 Success Metrics（步骤表 10→6 行等）在本仓实际不生效。

- 置信度：高 | 命中镜：Eng Claude · Eng Codex（2 声收敛）
- **建议**：Task 4 补一步——要么删除 `openspec/workflow/` 下的规则文件（恢复全局解析），要么同步刷新

**C3 — 主 spec 未覆盖 Requirements 仍断言 RUN_SOP/embedded-test-sop 存在**

spec-workflow 主 spec 至少 2 条 Requirement 未被 delta 声明 MODIFIED/REMOVED：
- `spec.md:300-315`「skill 命名与品牌一致性」：把 `embedded-test-sop` 列为命名前缀豁免清单成员
- `spec.md:1399-1420`「判据 MUST 只在其保护的风险真实存在的阶段求值」：明文 MUST 要求 RUN_SOP 作为三个受保护分支之一有用例——删除 RUN_SOP 测试后此条 MUST 当场违反
- 另有 `spec.md:518/570`（阶段三 TG-02→SOP 条件步）：delta 以不同标题声明 MODIFIED，无法正确替换原 Requirement

- 置信度：高 | 命中镜：Voice · Adversarial 2（2 声收敛）
- **建议**：补全这些 Requirement 的 MODIFIED/REMOVED 声明

### High

**H1 — Sunset 治理机制被绕过，审计空白**

decision-memo D2 直接删除观察窗+三档阈值，未跑实测。sdflow-spec 上线后 10 天已有 15 个 change（93% 带 decision-memo），数据大概率支持删除，但从未检查。retro 报告未为这 15 个 change 生成记录。

- 置信度：高 | 命中镜：CEO Claude · CEO Codex（2 声收敛）
- **建议**：先跑一次 `sdflow-retro` 补齐数据，把结果写进 decision-memo

**H2 — 自动触发无机械门，副作用在 HARD-GATE 之前产生**

删除 `disable-model-invocation: true` 后，模型误判自然语言信号会创建真实 git 分支 + change 目录 + 草稿 memo。HARD-GATE 能挡"是否放行设计"，挡不住"是否应该一开始就建分支"。design.md Risks 段的"HARD-GATE 兜底"表述不准确。且通过 `claude-section.md` 会推给 15 个下游项目。

- 置信度：高 | 命中镜：CEO Claude · CEO Codex · Eng Claude（3 声收敛）
- 五问速算：概率低（需模型误读自然语言）、影响小（分支可删、目录可删）、完美成本高（与去摩擦目标冲突）→ **不阻断，但 Risks 措辞应修正为诚实边界描述**

**H3 — design.md/tasks.md 的 impl_route.py 路径错误**

`design.md:85` 和 `tasks.md:32` 写 `sdflow-ship/scripts/impl_route.py`，实际位于 `sdflow-implement/scripts/impl_route.py`。

- 置信度：高 | 命中镜：Eng Claude · Eng Codex · Grounding（3 声收敛）
- **建议**：两处路径改为 `sdflow-implement/scripts/impl_route.py`

**H4 — `test_grill_handoff.py` 会红，任务未纳入**

4 个测试断言 `claude-section.md` 含 "ff 之后是 grill"、`prompts/step3-grill.md` 存在等——Task 4/5 删除这些内容后会红。

- 置信度：高 | 命中镜：Eng Claude · Eng Codex（2 声收敛）
- **建议**：Task 4 或新 Task 明确处置——整体删除（grill 不再是独立步骤）或改写为新规则守护

**H5 — WORKFLOW-GUIDE.md 是生成物，Task 4 指示手改**

由 `hack/gen_workflow_guide.py` 从 `workflow.md` + `prompts/step*.md` 机械拼装。`test_workflow_split.py` 3 个测试焊死一致性。`gen_workflow_guide.py:52-57` 的 `STEP_FILES` 字典硬编码旧步骤编号——删除 prompt 文件 + 重编号会击穿。

- 置信度：高 | 命中镜：Adversarial 1（已实跑验证基线 5 passed）
- **建议**：Task 4 改为"改 workflow.md + 更新 STEP_FILES 字典 → `python3 hack/gen_workflow_guide.py --write` 重新生成"

**H6 — 4 份 companion 文档未纳入 Impact/tasks**

`docs/workflow-map.md`（4 处 RUN_SOP）、`docs/workflow-overview.md`（6 处）、`docs/criteria-mechanization-tracker.md`、`docs/sdflow-fable5/02-module-reference.md`（5 处）——均自称"规则改动后需同步"。

- 置信度：高 | 命中镜：Adversarial 2
- **建议**：纳入 Task 4/6 的改动清单

**H7 — AGENTS.md 遗漏**

`AGENTS.md:125` 仍声明 sdflow-spec 只能人手触发，`:139-144` 保留旧三步例外，`:262-268` 强制 ff→grill。tasks.md Task 5 仅列 CLAUDE.md。

- 置信度：高 | 命中镜：Voice（独家）
- **建议**：AGENTS.md 纳入 Task 5

### Medium

**M1 — impl-pipeline 翻转实为 9 处硬编码 + 1 处对称显示逻辑**

`impl_route.py` 有 9 个 `return "superpowers"` 分散在 `read_config_pipeline`/`read_plan_marker`，加上 `_cmd_route:540` 的展示折叠逻辑需对称翻转。tasks.md 描述为"单点改动"。

- 置信度：高 | 命中镜：Eng Claude · Eng Codex
- **建议**：tasks.md 列全 9 个返回点 + 展示折叠逻辑

**M2 — impl-pipeline 单仓试点外推到 15 个下游项目**

试点全在本仓内（6 个 change），下游 15 个项目栈/约定未知。"15 个项目无在途 change"前提无核验痕迹。

- 置信度：中 | 命中镜：CEO Claude · CEO Codex · Adversarial 2
- **建议**：decision-memo D1 补核验证据锚；`sdflow-init update` 运行时输出里加一行回退说明

**M3 — config.template.yaml 旧注释**

`sdflow-init/assets/workflow/config.template.yaml:80` 仍写"缺省…一律 superpowers 旧管线"。新装的下游项目会被误导。

- 置信度：高 | 命中镜：Adversarial 1
- **建议**：Task 2 补更新两份 config.template.yaml 的注释

**M4 — Success Metric 数字不准确**

实测 `ship_gate.py` RUN_SOP+tg02_hit 合计 15 处（非 17）；测试命中 20 个函数（非 21）。

- 置信度：中 | 命中镜：Adversarial 2
- **建议**：数字改为"pytest 全绿"自证型指标，或实测修正

**M5 — 测试删除指令过粗，混入非 RUN_SOP 专属用例**

至少 4 个测试函数不是 RUN_SOP 专属——断言元组里把 RUN_SOP 列为"应排除的取值"之一。按字面"删除"执行会丢失"缺锚不放行"等安全相关回归覆盖。

- 置信度：中 | 命中镜：Adversarial 2 · Eng Codex
- **建议**：拆为"删除"（纯 RUN_SOP 测试）和"编辑保留"（附带提及的测试）两类

**M6 — config.yaml wayfinder 规则遗漏**

`openspec/config.yaml:38/48` 仍引用 `wayfinder→ff 衔接契约`。Task 6 grep 会命中但 tasks 未列入修改范围。

- 置信度：高 | 命中镜：Eng Codex · Voice
- **建议**：纳入 Task 4 或 Task 5 的改动清单

### Low

**L1** — ship_gate.py 三处"三个入口"计数需改成"两个"（Eng Claude）

**L2** — `ff-generation-constraints.md` impl-pipeline 触发条件措辞因缺省翻转语义变化（Adversarial 1）

---

## 二、决策登记区

### [自动决策] D1 — autoplan CEO premises

前提（减认知负担 → 合并双轨）合理。按 P6(bias toward action) 接受。

### [自动决策] D2 — 跳过 Design Review

无 UI scope。DX 关键词为内部工具维护讨论，非面向外部开发者 API/SDK。

### [需拍板] Q1 — Sunset 机制是否先跑评估？

数据大概率支持删除（93% 采用率远超 83% 门槛），但从未检查。两个选择：
- **A（推荐）**：先跑 `sdflow-retro` 补齐数据，结果写进 decision-memo（成本极低，换审计闭环）
- **B**：人明确拍板跳过评估，decision-memo 记录"人拍板跳过，理由 = ..."
- 三面后果：系统镜（A 增加 1 步不增加复杂度；B 留审计空白）· 用户镜（无可感知差异）· 开发循环镜（A ≈30min；B ≈0）
- 主次：开发循环成本极低，系统镜审计闭环价值明确 → 推荐 A

### [需拍板] Q2 — 自动触发是否加确认步？

- **A（推荐）**：按现有方案走（指令层约束 + HARD-GATE），但 Risks 措辞修正为诚实边界
- **B**：在相位 A/B 起手处加一个显式确认步（"检测到收敛信号，是否开 change？"）
- 三面后果：系统镜（A 无机械门但影响小可逆；B 增加一步但堵住分支创建）· 用户镜（A 更流畅；B 有一次确认摩擦）· 开发循环镜（B 需改 sdflow-spec 内部协议）
- 主次：五问速算判不阻断（概率低影响小可逆），推荐 A + 修正措辞

### [需拍板] Q3 — impl-pipeline 翻转策略？

- **A（推荐）**：按现方案翻转 + 补核验痕迹 + `sdflow-init update` 输出加回退说明
- **B**：只对新初始化项目默认 tickets，已有项目 pin 当前值
- 三面后果：系统镜（A 更简单统一；B 需在 sdflow-init 里加 pin 逻辑）· 用户镜（A 15 个项目静默切换；B 无感知）· 开发循环镜（B 增加维护面）
- 主次：tickets 是超集不退化 + 有 marker 锁定在途 change → 推荐 A

### 设计门拍板记录

设计门已拍板批准，日期 2026-08-05。Q1→A（跑 retro 补数据）、Q2→A（不加确认步 + 措辞已修正）、Q3→A（翻转 + 补核验痕迹）。

### [已裁掉] X1 — "低频不是嵌入式 SOP 正确删除依据"（Codex CEO）

裁掉理由：用户明确要求彻底删除（decision-memo D3）。嵌入式项目需要时可自建 SOP，不需要 workflow 自动化。

### [已裁掉] X2 — "不是一条线性路径"（Codex CEO）

裁掉理由：explore 条件前置、Phase B 人类决策、FF-0 halt 是流程正常行为，不是"非线性"的证据。"线性"指不再有分支 A/B 选择。

### [已裁掉] X3 — "机会成本——11 面镜待复评更优先"（Claude CEO）

裁掉理由：这是优先级建议，不是本 change 的设计缺陷。scope 由人定。

---

## 三、Outside Voice

<!-- sdflow:outside-voice v1 site="design-voice" guard="file-missing" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

Voice 3 条 findings 均进合并池（C1 关联 spec-authoring、C3 关联主 spec RUN_SOP requirement、H7 AGENTS.md 遗漏），无 tension（voice 与主审方向一致）。

**复用 autoplan outside voice**：guard reason_code=`file-missing`（gstack-review.md 在 guard 检查时尚未创建），回落自跑 design outside voice。仅补偿 outside-voice 切片，广审其余镜仍由 autoplan 原生执行覆盖。

<!-- sdflow:declared-sites v1 declared="design-voice" -->

---

## 五、Lens Metric（度量锚，pre-gate 草稿值）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="7" 采纳="7" 裁掉="0" defer="0" 独立="5" sev="致1/高2/中4/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="12" 采纳="9" 裁掉="3" defer="0" 独立="6" sev="致2/高4/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致2/高1/中0/低0" -->

---

## 四、收敛

**高收敛度**：17 条 findings 中 11 条由 ≥2 个独立声音收敛，6 条为单声独家（其中 Voice 独家 1 条、Adversarial 独家 3 条、Eng Claude 独家 2 条）。

**核心阻断项**（须在设计门前处理）：
- **C1**: 补 spec-authoring + impl-orchestration delta spec
- **C2**: 处理 openspec/workflow/ 本地 pin
- **C3**: 补全主 spec 未覆盖 Requirement 的 MODIFIED/REMOVED

**须修正但不阻断**：H3（路径错误）、H4（test_grill_handoff.py）、H5（WORKFLOW-GUIDE.md 生成物）、H6（companion 文档）、H7（AGENTS.md）

**建议进设计 HARD-GATE**：在处理完 C1/C2/C3 + 修正 H3-H7 后。当前四件套不满足直接放行条件。

[spec-review-amendment]
