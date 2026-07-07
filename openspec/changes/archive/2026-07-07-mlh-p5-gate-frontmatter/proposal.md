## Why

ship-gate 的状态锚（`design-approved` / `verify=PASS|FAIL` / `code-review=pass|blocked`）当前以 inline HTML 注释锚落在报告**正文**里，与人读的正文同处一个文本平面。B4 曾用「行级字面查找 + fence-aware」缓解正文对锚串的描述性提及被误判，但 B5 自认**非根治**：只要正文在非 fence 行原样写出锚字面（讨论、示范、对账清单），gate 仍会假命中。实测归档 88 个报告文件含 168 行 ship-gate 锚，其中 `ship-gate: X` / `ship-gate: --` / 空值等**噪声锚**正是正文讨论锚串处——这类假阳源持续存在。把状态迁到报告 **YAML frontmatter**，让「机器状态」与「人读正文」彻底分处两个平面，从根上消除子串/prose-inline 混淆（B4/B5 类 gate 假过·假红）。此为机械层固化 roadmap 阶段 5（Leg2 去字符串化家族①）；其 ROI 门经 P2 交付已过（GO 变体 a），且 `ship_gate.py` 经核实**只在 `sdflow-ship/scripts/`、走 skill symlink、非 bundle 回灌消费仓**，迁移爆炸半径大降——窗口已开。

## What Changes

- **新增报告 frontmatter 状态 schema**：`design_approved: bool` / `verify: PASS|FAIL` / `code_review: pass|blocked`，落在三类报告（spec-review / verify / code-review）的 YAML frontmatter。
- **三 producer SKILL 改写 frontmatter**：`sdflow-spec-review`（拍板回写）/ `sdflow-done`（verify 模板）/ `sdflow-code-review`（报告格式）产出 frontmatter 状态，**替代** inline 锚。**BREAKING**（对 live 报告格式）：新报告不再以 inline 注释锚承载结论；归档旧报告经 dual-read 兼容（见下）。
- **gate 消费侧 dual-read + fail-closed**：`ship_gate.py` 的 live 报告解析改读 frontmatter（**手写 stdlib，不 import yaml**——grill 已决 D3）；**归档报告 frontmatter + inline 双读**〔grill G2〕——迁移后新归档为 frontmatter、迁移前旧归档为 inline，`archived_verify_state` 须 frontmatter 优先→回退 inline（inline 读半场永久保留、非临时窗口）。LLM 写坏 frontmatter → **fail-closed**（判「无有效状态」→ gate 停下报告，绝不静默过门）。
- **解析机器退役仅 live 半场**：删 `_line_scoped_hits` 的 **live 报告解析半场**；`archived_verify_state` 的**归档读 `_line_scoped_hits` 永久保留**（订正「删整套」为「删 live、保留归档读」）。
- **契约测试迁移**：`test_anchor_contract.py` / `test_producer_parser_contract.py` + B5 聚合语料测试迁到 frontmatter；新增写坏 YAML fail-closed、归档 inline dual-read 兼容用例。

## Capabilities

### New Capabilities
<!-- 无新增能力：本变更改的是既有 ship-gate 锚契约的承载形态 -->

### Modified Capabilities
- `spec-workflow`：修改「阶段三编排台账确定性（ship_gate）」需求——机判锚点承载形态从**报告正文 inline 注释锚**改为**报告 YAML frontmatter 状态字段**（live 报告）；gate 解析改**手写 stdlib**（不 import yaml，保零依赖不变量）+ 写坏 fail-closed；归档 frontmatter+inline dual-read **永久保留识别**。锚字面与门禁语义（退出码、UNKNOWN 冲突判定、命名空间隔离）不变，仅换承载层。〔spec-review-amendment D7f：原「safe_load」订正为手写 stdlib〕

## Impact

- **`sdflow-ship/scripts/ship_gate.py`**（非 bundle、走 skill symlink → 爆炸半径小）：`anchors_in`/live 解析改读 frontmatter；`archived_verify_state` 归档读保留；`_line_scoped_hits` live 半场退役、归档读半场留存。
- **三 producer SKILL**：`sdflow-spec-review` / `sdflow-done` / `sdflow-code-review` 报告模板改写 frontmatter。
- **契约测试**：`sdflow-ship/tests/test_anchor_contract.py`、`test_producer_parser_contract.py` + B5 语料。
- **归档 88 文件 / 168 锚行**：不改动，由 dual-read 归档读路径继续识别。
- **依赖**：**无新增运行时依赖**——grill 已决手写 stdlib frontmatter 解析（不 import yaml），保持 `ship_gate.py` 零第三方依赖不变量（沿 anchor_lint / config_lint 惯例）。归档 88 文件为只读依赖（dual-read 语料）。

## Success Metrics

- 报告正文任意非 fence 行原样写出锚字面 → gate **不误判**（B4/B5 类根治：正文平面与状态平面分离，正文不再参与门禁解析）。
- LLM 写坏 frontmatter YAML → gate **fail-closed** 停下报告，零静默过门。
- 归档 88 文件旧 inline 锚 → dual-read **100% 仍正确识别**（SHIPPED/verify 判定不回归）。
- 产者↔gate 契约测试全绿；`_line_scoped_hits` live 半场删除后无 live 解析路径残留、归档读半场测试覆盖保留。

## Non-Goals

- **不迁家族②（recorder 索引 → frontmatter）**：那是 roadmap 阶段 6 north-star，不排期，本变更不碰。
- **不删归档读半场**：归档不可变，`archived_verify_state` 的 inline 锚读取永久保留，非本次退役范围。
- **不改门禁语义**：退出码、UNKNOWN 冲突判定、checkpoint 命名空间隔离、新鲜度分域等既有契约不变，仅换锚承载层。
- **不涉 bundle 回灌链**：`ship_gate.py` 非 bundle，本变更不触 `sdflow-init update` 下发流程（若实现中发现与此不符须停下核对，绝不 fold/sweep 行为面路径）。

## Compliance

- 遵 adr/0006 机械层固化硬约束：新解析路径 fail-closed + 可观测，pytest 覆盖坏输入（写坏 YAML）断言非零退出 / 判定不能；判断部分不新增，纯机械换层。
- 遵 workflow bundle 纪律：`ship_gate.py` 非 bundle 权威源、无下游回灌；三 producer SKILL 为本仓 skill，改动即生效（setup.sh symlink）。

## 需求优先级〔TG-19〕

- **P0**：frontmatter 状态 schema + 三 producer 迁移 + gate live 读 frontmatter + fail-closed + 归档 dual-read（核心闭环，缺一不可用）。
- **P1**：`_line_scoped_hits` live 半场退役（清理，依赖 P0 迁移完成）；契约测试全量迁移。
- **P2**：无（本变更不追加 nice-to-have）。

## 利益相关方与外部依赖〔TG-20〕

- **利益相关方**：`sdflow-ship` 编排器（消费 gate 判定）；三 producer SKILL 的使用者（本仓自身 dogfood + 未来任何跑此 workflow 的项目）。
- **外部依赖**：**无**——grill 已决手写 stdlib 解析，不引 PyYAML，保持 gate 零第三方依赖。归档 88 文件为只读依赖（dual-read 语料）。

## 开放问题〔TG-21〕

- ~~**Q1（frontmatter 解析实现）**~~ → **grill 已决：手写 stdlib**（不 import yaml；ship_gate 零依赖不变量 + 门禁不因缺库崩溃，见 design D3）。
- **Q2（frontmatter 与既有报告结构兼容）**：三类报告现有正文结构是否已有 frontmatter？迁入后 openspec validate / 现有工具是否受影响？负责人：design 起手核。
- **Q3（noise 锚清理）**：归档里的噪声锚（`ship-gate: X`/`--`/空）是历史正文示范，dual-read 只认 5 个合法锚字面即天然免疫——是否需额外处理？倾向否（合法锚白名单已隔离），design 确认。

## 假设〔TG-22〕

- **A1**：归档报告不可变（已并 base 的 archive/ 目录不会被回改）——若失效，归档 dual-read 语料范围会漂移。**当前成立**（归档纪律 + git 历史）。
- **A2**：`ship_gate.py` 仅在 `sdflow-ship/scripts/`、非 bundle 回灌（survey 实测）——若失效（未来被纳入 bundle tools/），迁移须走 `sdflow-init update` 回灌全流程、爆炸半径升级。**当前成立**，实现中若发现不符须停下核对。
- **A3**：live 报告与归档报告可由「路径」清晰区分（`openspec/changes/{change}/` = live；`archive/<date>-{change}/` = 归档）——gate 据此分流 frontmatter 读 vs inline 读。**当前成立**（gate 已有 active/archive 分流逻辑）。
