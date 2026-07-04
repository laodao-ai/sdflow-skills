## Why

checkpoint 任务标签的格式约定（`checkpoint-commit.sh <change>:task<N>-<slug>`）当前**硬编码在三处独立维护**：`ship_gate.py` 的 `TAG_RE`（真正的解析权威）、`workflow.md`（bundle 权威文档）、`sdflow-ship/SKILL.md`（派发指令）。ship-gate-hardening-2 实证：把格式从裸 `task<N>-` 改成命名空间 `<change>:task<N>-` 时，需同步改多处而漏改了 SKILL.md 一处（spec-review G1 才抓到）。更危险的是 doc↔parser 漂移——文档写一种格式、gate 用 `TAG_RE` 解析另一种，会让标签**静默不计入完成集**（假✅家族），当前无任何守卫。本 change 用一条机械绑定测试焊死三站一致，止住漂移。

## What Changes

- **新增 contract 测试**（`sdflow-ship/tests/`）：从 `workflow.md` / `SKILL.md` 文档里出现的格式串构造一个 checkpoint subject，断言 `ship_gate.py` 的 `TAG_RE` **真能 match** 且捕获出正确的 `<change>` / `<N>`——把 **文档↔解析器** 双向钉死，任一站漂移即红。这是「单一真相源靠测试兜底」，取代「让 markdown 彼此 DRY」（跨运行时安装树无构建期 include，硬去重收益边际且添间接读依赖）。
- **`sdflow-ship/SKILL.md` 瘦身为引用而非独立复述**：RUN_PLAN 派发段不再自带完整格式文案，改为「按 workflow.md『step6 tag 契约』定义的命名空间格式派发」，把格式**字面**收敛到 workflow.md 单处；SKILL.md 只保留派发动作与语义要点。
- **`workflow.md` 明确为格式字面的权威文档源**（本就是 bundle 唯一权威源，本 change 在其 step6 处补一句「此格式字面为权威定义，消费方引用不复述」的自我声明，防后人再复制粘贴）。
- 不改 `TAG_RE` 本身的解析行为（格式语义逐字不变）；纯**防漂移加固**，无功能变更。

## Capabilities

### New Capabilities
<!-- 无新能力 -->

### Modified Capabilities
- `spec-workflow`: 新增需求——checkpoint 标签格式契约 MUST 有单一真相源（`TAG_RE` 为解析权威、`workflow.md` 为文档权威）且 MUST 有机械绑定测试防三站漂移；派发指令（SKILL.md）MUST 引用而非独立复述格式字面。

## Impact

- **文档**：`sdflow-init/assets/workflow/workflow.md`（step6 自我声明）、`sdflow-ship/SKILL.md`（派发段瘦身）。
- **测试**：`sdflow-ship/tests/`（新增 contract 测试；`test_workflow_authority.py` 既有断言可能顺带增强）。
- **代码**：`ship_gate.py` 不改行为（`TAG_RE` 作为被测锚点被引用）。
- **部署**：改 `assets/workflow/` 权威源后须 `sdflow-init update` 推下游；改 skill 后开发 checkout 跑 `setup.sh`。
- **无风险面**：无运行时行为变更，纯回归防护网；deferred T33/T35（新鲜度越 committed 边界）不在本 change scope。
