## Why

`sdflow-maintain` 的核心机械步——扫 `openspec/specs/`+`openspec/rules/` ↔ `INDEX.md` 表格行的 set-diff、CLAUDE.md 过时引用扫描、workflow bundle 陈旧遮蔽兜底扫描——目前全由 SKILL.md 的 prose 指令让模型**手做**（手扫、手比对、手判差异）。这正是 MLH roadmap §1.3 愿景点名要脚本化的「表↔文件 set-diff」确定性判据，也是 adr/0006 硬约束「凡机械 prose 协议 MUST 脚本化」的直接对象。手做 set-diff 有漂移风险（模型可能漏项、误判、或每次口径不一），且不可测。本 change 是 MLH 阶段4·4.B（★组，批次 `mlh-p4-target-state` T79），按目标态（非当下痛感）该做未做项。

## What Changes

- **新增** `sdflow-maintain/scripts/maintain_scan.py`：确定性只读差异报告脚本，把三类 set-diff 从模型手做下沉为脚本归约。
- **新增** `sdflow-maintain/tests/`：pytest 覆盖，含坏输入 fail-closed 断言（非零退出）。
- **`sdflow-maintain` 由纯 Markdown 编排类升为数据类**（首次拥有 `scripts/`+`tests/`，对齐 `sdflow-buglist`/`sdflow-todolist`/`sdflow-retro` 等数据类形态）。
- **修改** `sdflow-maintain/SKILL.md`：步骤 1-3（扫描/解析/对比生成报告）由 prose 手做改为「调 `maintain_scan.py` 出只读差异报告」；步骤 4（按报告修复 INDEX）、步骤 5（提示跑 retro）的**判断与编排保留给模型**（脚本不越权改 INDEX）。
- **判断权显式留人/模型**：新 spec 归哪个主题分组、是否修复 INDEX——脚本只出报告，不做这些判断。

## Capabilities

### New Capabilities
- `maintain-scan`: openspec 目录 ↔ INDEX.md 一致性的确定性 set-diff 只读报告能力——覆盖 ① specs/rules ↔ INDEX 表格行的双向 set-diff（新增未索引 / 已删未清理）② CLAUDE.md（根+子目录）过时 spec/rule 引用扫描 ③ workflow bundle 陈旧遮蔽兜底扫描；fail-closed、可观测、不改任何文件。

### Modified Capabilities
<!-- 无既有能力的 requirement 变更：本 change 是新增脚本能力，sdflow-maintain 现无 spec，判断/编排语义不变 -->

## Impact

- **代码**：新增 `sdflow-maintain/scripts/maintain_scan.py`（Python stdlib，无第三方依赖）+ `sdflow-maintain/tests/test_maintain_scan.py`；改 `sdflow-maintain/SKILL.md`（步骤 1-3 改为调脚本）。
- **技术栈（TG-01）**：纯 Python stdlib 脚本（对齐仓内既有数据类 skill 的 `scripts/` 取向）；不命中 backend·go / embedded / frontend 领域清单，仅适用 BASE 清单。
- **安装机制**：`sdflow-maintain` 走 skill symlink（改源即时生效），新增 `scripts/`/`tests/` 不改 `setup.sh` 逻辑；无 bundle 回灌链影响（非 `sdflow-init/assets/` 下）。
- **无外部服务 / 无 API / 无数据库变更**。

## Success Metrics

- 三类 set-diff 全部由 `maintain_scan.py` 产出，SKILL.md 步骤 1-3 无「手扫/手比对」prose。
- 坏输入（INDEX 缺失、表格畸形、目录不存在等）全部 fail-closed（非零退出 + 响亮报错），pytest 有对应负例断言。
- 判断部分（归组/是否修复）显式保留在 SKILL.md 步骤 4，脚本零写文件。
- 现有 maintain 的**保留行为**（会话末提示 retro、步骤 4 修复判断）不回归。〔spec-review-amendment M4：措辞收窄，见 Non-Goal「代码路径缺失退役」〕

## Non-Goals

- **不**让脚本自动修复 INDEX.md——修复仍由模型按报告判断执行（步骤 4 保留）。
- **不**把「新 spec 归哪主题分组」的判断下沉进脚本（内容判断留模型）。
- **不**动 4.D 小校验器组（4.D.1/2/4，另一次 change）与 ◐ 组（4.A/4.D.3，待 embedded 契约）。
- **不**改 `INDEX.md` 的生成/格式约定，也不触 `openspec/issues/INDEX.md`（那是 issues.py 的领地）。
- **代码路径缺失校验退役〔spec-review-amendment M4/D7〕**：现行 SKILL 步骤 2-3 有第三类差异「代码路径缺失」（代码路径速查表无映射）。本仓真实 INDEX 无此表（已废弃），故本 change **显式不下沉该校验**（YAGNI 退役），只保双向 set-diff 两类；不算「行为回归」，因该表在目标态已不存在。若未来消费仓有此需求再单开。

## Open Questions (TG-21)

- Q1（归组线）：脚本只报「新增未索引」的 spec/rule 名，还是也**建议**归入哪个主题分组？倾向前者（建议归组是内容判断，留模型），design 定。
- Q2（bundle 陈旧遮蔽扫描范围）：判定「残留规则文件本体」的清单从哪读——硬编码文件名 vs 从单一源读？倾向复用现有兜底扫描口径，design 明确。

## Assumptions (TG-22)

- `INDEX.md` 的表格行格式稳定可解析（markdown 表格）；若格式漂移，脚本应 fail-closed 报错而非静默误判（失效影响：误报差异 → 已被 fail-closed 红线覆盖）。
- `openspec/specs/` / `openspec/rules/` 目录结构稳定（spec.md / *.md 约定）；失效则扫描结果偏差，pytest 固定结构断言兜底。

## Compliance

N/A（本仓自建 skill 工具，无外部合规/隐私/许可约束；纯本地文件读取，不涉数据出境或第三方服务）。
